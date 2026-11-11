#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT 384521 - Radar diario de noticias, eventos y normas del sector lechero argentino.
Sin inteligencia artificial: scraping + reglas fijas. Corre solo en GitHub Actions.
"""
import html as htmllib
import json
import random
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import config as C

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo(C.ZONA_HORARIA)
except Exception:  # pragma: no cover
    TZ = timezone(timedelta(hours=-3))

RAIZ = Path(__file__).resolve().parent
DIR_INFORMES = RAIZ / "informes"
DIR_ESTADO = RAIZ / "estado"
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
         "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
         "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8,
         "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12}


def log(msg):
    print(f"[{datetime.now(TZ):%H:%M:%S}] {msg}", flush=True)


# ------------------------------------------------------------------ texto
def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.lower()).strip()


def limpiar(s):
    return re.sub(r"\s+", " ", htmllib.unescape(s or "")).strip()


def quitar_html(s):
    return limpiar(BeautifulSoup(s or "", "lxml").get_text(" ", strip=True))


def compilar(terminos):
    ts = sorted({norm(t) for t in terminos.split("|") if t.strip()}, key=len, reverse=True)
    return re.compile(r"(?<![a-z0-9])(?:" + "|".join(re.escape(t) for t in ts) + r")(?![a-z0-9])")


RE_CAT = {k: compilar(v) for k, v in C.CATEGORIAS.items()}
RE_IMPACTO = [(re.compile("(?:" + "|".join(norm(x) for x in p.split("|")) + ")"), txt)
              for p, txt in C.IMPACTOS_NORMA]
CORE = [k for k in C.CATEGORIAS if k not in ("Eventos y capacitaciones", "Clima y tiempo", "Agro general")]


def clasificar(texto):
    """Devuelve (tags, seccion_principal) o ([], None) si no es relevante."""
    t = norm(texto)
    hits = {k: len(rx.findall(t)) for k, rx in RE_CAT.items()}
    tags = [k for k, v in hits.items() if v]
    if not any(hits[k] for k in CORE + ["Agro general"]):
        return [], None
    if hits["Eventos y capacitaciones"]:
        principal = "Eventos y capacitaciones"
    else:
        cand = [k for k in CORE if hits[k]]
        if cand:
            principal = max(cand, key=lambda k: (hits[k], -list(C.CATEGORIAS).index(k)))
        elif hits["Clima y tiempo"]:
            principal = "Clima y tiempo"
        else:
            principal = "Agro general"
    return tags, principal


# ------------------------------------------------------------------ fechas
def _tz(dt):
    return dt.replace(tzinfo=TZ) if dt.tzinfo is None else dt.astimezone(TZ)


def parse_fecha(texto):
    """Devuelve (datetime con zona, solo_dia) o (None, False)."""
    if not texto:
        return None, False
    s = limpiar(texto)
    m = re.search(r"hace\s+(\d+)\s*(minuto|min|hora|h\b|d[ií]a)", norm(s))
    if m:
        n, u = int(m.group(1)), m.group(2)
        delta = timedelta(minutes=n) if u.startswith("min") else timedelta(hours=n) if u.startswith("h") else timedelta(days=n)
        return datetime.now(TZ) - delta, False
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?\s*(Z|[+-]\d{2}:?\d{2})?)?", s)
    if m:
        y, mo, d, hh, mi, ss, z = m.groups()
        try:
            if hh is None:
                return datetime(int(y), int(mo), int(d), tzinfo=TZ), True
            dt = datetime(int(y), int(mo), int(d), int(hh), int(mi), int(ss or 0))
            if z:
                off = timezone.utc if z == "Z" else timezone(
                    (1 if z[0] == "+" else -1) * timedelta(hours=int(z[1:3]), minutes=int(z[-2:])))
                dt = dt.replace(tzinfo=off)
            return _tz(dt), False
        except ValueError:
            pass
    try:
        if re.search(r"\d{1,2}:\d{2}", s) and re.search(r"[A-Za-z]{3},", s):
            return _tz(parsedate_to_datetime(s)), False
    except Exception:
        pass
    m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})(?:\D+(\d{1,2}):(\d{2}))?", s)
    if m:
        d, mo, y, hh, mi = m.groups()
        try:
            if hh:
                return _tz(datetime(int(y), int(mo), int(d), int(hh), int(mi))), False
            return datetime(int(y), int(mo), int(d), tzinfo=TZ), True
        except ValueError:
            pass
    m = re.search(r"(\d{1,2})\s+(?:de\s+)?([a-záéíóú]{3,10})\.?,?\s+(?:de\s+)?(\d{4})", norm(s))
    if m and m.group(2) in MESES:
        try:
            return datetime(int(m.group(3)), MESES[m.group(2)], int(m.group(1)), tzinfo=TZ), True
        except ValueError:
            pass
    return None, False


def es_reciente(fecha, solo_dia, ahora):
    if fecha is None:
        return False
    if solo_dia:
        return fecha.date() == ahora.date()
    return timedelta(hours=-1) <= (ahora - fecha) <= timedelta(hours=C.VENTANA_HORAS)


def fmt_fecha(it):
    f = it.get("fecha")
    if f is None:
        return "fecha no informada"
    base = f"{DIAS[f.weekday()]} {f:%d/%m/%Y}"
    if it.get("fecha_inferida"):
        return base + " (detectada hoy; la fuente no informa fecha)"
    return base if it.get("solo_dia") else f"{base} {f:%H:%M}"


# ------------------------------------------------------------------ red (paciente y poco agresiva)
class Red:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(C.HEADERS)
        retry = Retry(total=C.REINTENTOS, connect=C.REINTENTOS, read=C.REINTENTOS,
                      backoff_factor=C.BACKOFF, status_forcelist=[429, 500, 502, 503, 504],
                      allowed_methods=["GET"], respect_retry_after_header=True, raise_on_status=False)
        ad = HTTPAdapter(max_retries=retry, pool_connections=2, pool_maxsize=2)
        self.s.mount("http://", ad)
        self.s.mount("https://", ad)
        self.ultimo, self.fallas, self.robots, self.problemas = {}, {}, {}, []

    @staticmethod
    def dominio(url):
        return urlparse(url).netloc.lower()

    def _esperar(self, dom):
        if dom in self.ultimo:
            falta = random.uniform(C.PAUSA_MIN_POR_DOMINIO, C.PAUSA_MAX_POR_DOMINIO) - (time.time() - self.ultimo[dom])
            if falta > 0:
                time.sleep(falta)

    def _robots(self, url):
        p = urlparse(url)
        dom = p.netloc.lower()
        if dom not in self.robots:
            rp = RobotFileParser()
            try:
                self._esperar(dom)
                r = self.s.get(f"{p.scheme}://{dom}/robots.txt", timeout=(C.TIMEOUT_CONEXION, 20))
                self.ultimo[dom] = time.time()
                if r.status_code == 200 and "html" not in r.headers.get("content-type", "").lower():
                    rp.parse(r.text.splitlines())
                else:
                    rp.parse([])
            except Exception:
                rp.parse([])
            self.robots[dom] = rp
        return self.robots[dom]

    def permitido(self, url):
        if not C.RESPETAR_ROBOTS:
            return True
        try:
            return self._robots(url).can_fetch(C.USER_AGENT, url)
        except Exception:
            return True

    def get(self, url, robots=True, referer=None):
        dom = self.dominio(url)
        if self.fallas.get(dom, 0) >= C.FALLAS_PARA_ABANDONAR_DOMINIO:
            return None
        if robots and not self.permitido(url):
            self.problemas.append(f"{url} -> bloqueado por robots.txt (omitido)")
            return None
        self._esperar(dom)
        hdr = {"Referer": referer} if referer else {}
        try:
            r = self.s.get(url, timeout=(C.TIMEOUT_CONEXION, C.TIMEOUT_LECTURA), headers=hdr)
            self.ultimo[dom] = time.time()
        except Exception as e:
            self.ultimo[dom] = time.time()
            self.fallas[dom] = self.fallas.get(dom, 0) + 1
            self.problemas.append(f"{url} -> {type(e).__name__}")
            return None
        if r.status_code >= 400:
            if r.status_code in (401, 403, 429) or r.status_code >= 500:
                self.fallas[dom] = self.fallas.get(dom, 0) + 1
            self.problemas.append(f"{url} -> HTTP {r.status_code}")
            return None
        self.fallas[dom] = 0
        return r


# ------------------------------------------------------------------ extracción
EXCLUIR = re.compile(r"/(tag|tags|categoria|categorias|category|autor|author|page|pagina|contacto|suscri\w*|login|"
                     r"search|buscar|wp-content|wp-json|feed|politica\w*|terminos\w*|quienes\w*|newsletter|"
                     r"publicidad|anunci\w*)(/|$)|\.(jpg|jpeg|png|gif|svg|webp|css|js)$")


def raiz_host(h):
    h = h.replace("www.", "")
    p = h.split(".")
    return ".".join(p[-3:]) if h.endswith((".com.ar", ".gob.ar", ".edu.ar", ".org.ar")) and len(p) >= 3 else ".".join(p[-2:])


def fecha_cercana(a):
    nodo = a
    for _ in range(4):
        nodo = nodo.parent
        if nodo is None:
            break
        t = nodo.find("time")
        if t:
            f, sd = parse_fecha(t.get("datetime") or t.get_text(" ", strip=True))
            if f:
                return f, sd
        txt = nodo.get_text(" ", strip=True)
        if len(txt) > 700:
            break
        f, sd = parse_fecha(txt)
        if f:
            return f, sd
    return None, False


def items_html(soup, base):
    out, raiz = {}, raiz_host(urlparse(base).netloc)
    for a in soup.find_all("a", href=True):
        href = urljoin(base, a["href"]).split("#")[0]
        p = urlparse(href)
        if p.scheme not in ("http", "https") or raiz_host(p.netloc) != raiz:
            continue
        path = p.path.lower()
        if EXCLUIR.search(path) or len(path.strip("/")) < 8 and not re.search(r"\d", path):
            continue
        if a.find_parent(["nav", "footer"]):
            continue
        texto = limpiar(a.get_text(" ", strip=True))
        if not texto:
            h = a.find(["h1", "h2", "h3", "h4"])
            texto = limpiar(h.get_text(" ", strip=True)) if h else ""
        if not (25 <= len(texto) <= 250) or len(texto.split()) < 4:
            continue
        if href.rstrip("/") == base.rstrip("/") or href in out:
            continue
        f, sd = fecha_cercana(a)
        out[href] = {"titulo": texto, "url": href, "fecha": f, "solo_dia": sd, "resumen": ""}
    return list(out.values())


def descubrir_feeds(soup, base):
    fs = []
    for l in soup.find_all("link", href=True):
        tipo = (l.get("type") or "").lower()
        if "alternate" in (l.get("rel") or []) and ("rss" in tipo or "atom" in tipo):
            fs.append(urljoin(base, l["href"]))
    return fs[:1]


def items_feed(contenido, fuente_nombre=None):
    soup = BeautifulSoup(contenido, "xml")
    out = []
    for it in soup.find_all(["item", "entry"]):
        t = it.find("title")
        if not t:
            continue
        l = it.find("link")
        url = (l.get("href") or l.get_text(strip=True)) if l else ""
        if not url:
            continue
        d = it.find(["pubDate", "published", "updated", "date"])
        f, sd = parse_fecha(d.get_text(strip=True)) if d else (None, False)
        desc = it.find(["description", "summary", "content"])
        src = it.find("source")
        titulo = limpiar(t.get_text())
        if src and titulo.endswith(" - " + limpiar(src.get_text())):
            titulo = titulo[: -len(" - " + limpiar(src.get_text()))]
        out.append({"titulo": titulo, "url": url.strip(), "fecha": f, "solo_dia": sd,
                    "resumen": quitar_html(desc.get_text()) [:320] if desc else "",
                    "fuente_real": limpiar(src.get_text()) if src else None})
    return out


def fecha_de_articulo(soup):
    for sel in [{"property": "article:published_time"}, {"property": "og:article:published_time"},
                {"itemprop": "datePublished"}, {"name": "date"}, {"name": "pubdate"}]:
        m = soup.find("meta", attrs=sel)
        if m and m.get("content"):
            f, sd = parse_fecha(m["content"])
            if f:
                return f, sd
    t = soup.find("time", attrs={"datetime": True})
    if t:
        f, sd = parse_fecha(t["datetime"])
        if f:
            return f, sd
    m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', str(soup))
    return parse_fecha(m.group(1)) if m else (None, False)


# ------------------------------------------------------------------ procesamiento de fuentes
def procesar_fuente(red, fuente, ahora, estado, primera):
    r = red.get(fuente["url"])
    if r is None:
        return []
    soup = BeautifulSoup(r.content, "lxml")
    items = []
    for fu in descubrir_feeds(soup, fuente["url"]):
        rf = red.get(fu, referer=fuente["url"])
        if rf is not None:
            try:
                items += items_feed(rf.content)
            except Exception as e:
                red.problemas.append(f"{fu} -> feed ilegible ({type(e).__name__})")
    items += items_html(soup, fuente["url"])
    unicos = {}
    for it in items:
        u = it["url"].rstrip("/")
        if u not in unicos or (unicos[u]["fecha"] is None and it["fecha"] is not None):
            unicos[u] = it
    items = list(unicos.values())[: C.MAX_ITEMS_POR_FUENTE * 2]

    resultado, abiertos = [], 0
    for it in items:
        tema_ok = fuente["tema"] == "lacteo"
        tags, principal = clasificar(it["titulo"] + " " + it["resumen"])
        if not tags and not tema_ok:
            if it["fecha"] is not None or abiertos >= C.MAX_ARTICULOS_A_ABRIR_POR_FUENTE:
                continue
        if it["fecha"] is None:
            if abiertos < C.MAX_ARTICULOS_A_ABRIR_POR_FUENTE:
                abiertos += 1
                ra = red.get(it["url"], referer=fuente["url"])
                if ra is not None:
                    sa = BeautifulSoup(ra.content, "lxml")
                    it["fecha"], it["solo_dia"] = fecha_de_articulo(sa)
                    if not it["resumen"]:
                        m = sa.find("meta", attrs={"property": "og:description"}) or sa.find("meta", attrs={"name": "description"})
                        it["resumen"] = limpiar(m.get("content", ""))[:320] if m else ""
                    tags, principal = clasificar(it["titulo"] + " " + it["resumen"])
            if it["fecha"] is None:
                u = it["url"]
                nuevo = u not in estado["urls"]
                estado["urls"].setdefault(u, ahora.isoformat())
                if primera or not nuevo or not (tags or tema_ok):
                    continue
                it["fecha"], it["solo_dia"], it["fecha_inferida"] = ahora, False, True
        if not es_reciente(it["fecha"], it.get("solo_dia", False), ahora):
            continue
        if not tags and not tema_ok:
            continue
        if not tags:
            tags, principal = ["Lechería y producción láctea"], "Lechería y producción láctea"
        it.update(tags=tags, seccion=principal, fuente=it.get("fuente_real") or fuente["nombre"])
        resultado.append(it)
    log(f"  {fuente['nombre']}: {len(resultado)} nota(s) de las últimas {C.VENTANA_HORAS} h")
    return resultado


def procesar_google_news(red, ahora):
    out = []
    for q in C.GOOGLE_NEWS_CONSULTAS:
        url = f"https://news.google.com/rss/search?q={quote_plus(q + ' when:1d')}&hl=es-419&gl=AR&ceid=AR:es-419"
        r = red.get(url, robots=False)
        if r is None:
            continue
        try:
            its = items_feed(r.content)
        except Exception:
            continue
        for it in its:
            if not es_reciente(it["fecha"], it.get("solo_dia", False), ahora):
                continue
            tags, principal = clasificar(it["titulo"])
            if not tags:
                continue
            it.update(tags=tags, seccion=principal, fuente=(it.get("fuente_real") or "Google Noticias"))
            out.append(it)
        time.sleep(random.uniform(*C.PAUSA_ENTRE_FUENTES))
    log(f"  Google Noticias (RSS): {len(out)} nota(s)")
    return out


# ------------------------------------------------------------------ Boletín Oficial
def resumen_norma(cuerpo):
    t = limpiar(cuerpo)
    m = re.search(r"ART[ÍI]CULO\s*1\s*[º°o]?\s*[\.\-–:]*", t, re.I)
    frag = t[m.end():] if m else t
    frag = re.split(r"ART[ÍI]CULO\s*2", frag, maxsplit=1)[0][:380]
    if len(frag) > 150 and "." in frag[150:]:
        frag = frag[: 150 + frag[150:].rfind(".") + 1]
    return frag.strip()


def impacto_norma(texto):
    t = norm(texto)
    frases = []
    for rx, txt in RE_IMPACTO:
        if rx.search(t) and txt not in frases:
            frases.append(txt)
    return frases[:3]


def procesar_boletin(red, ahora):
    r = red.get(C.BOLETIN_URL)
    if r is None:
        return []
    soup = BeautifulSoup(r.content, "lxml")
    avisos = {}
    for a in soup.find_all("a", href=True):
        if "/detalleAviso/primera/" in a["href"]:
            u = urljoin(C.BOLETIN_URL, a["href"]).split("#")[0]
            avisos.setdefault(u, limpiar(a.get_text(" ", strip=True)))
    log(f"  Boletín Oficial: {len(avisos)} aviso(s) en el listado; revisando detalle con pausas")
    out = []
    for i, (u, texto_lista) in enumerate(list(avisos.items())[: C.BOLETIN_MAX_AVISOS], 1):
        rd = red.get(u, referer=C.BOLETIN_URL)
        if rd is None:
            if red.fallas.get(red.dominio(u), 0) >= C.FALLAS_PARA_ABANDONAR_DOMINIO:
                break
            continue
        sd = BeautifulSoup(rd.content, "lxml")
        cuerpo_tag = sd.find(id="cuerpoDetalleAviso") or sd.find("main") or sd.body
        cuerpo = cuerpo_tag.get_text(" ", strip=True) if cuerpo_tag else ""
        h = sd.find(id="tituloDetalleAviso") or sd.find("h1")
        titulo = limpiar(h.get_text(" ", strip=True)) if h else ""
        titulo = (texto_lista if len(texto_lista) > len(titulo) else titulo)[:230] or "Aviso del Boletín Oficial"
        tags, _ = clasificar(titulo + " " + cuerpo[:6000])
        fuertes = [t for t in tags if t in CORE]
        if not fuertes and not (("Agro general" in tags) and len(RE_CAT["Agro general"].findall(norm(titulo + cuerpo[:6000]))) >= 2):
            continue
        m = re.search(r"/(\d{8})(?:/|$)", u)
        f, sdia = parse_fecha(f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}") if m else (ahora, True)
        res = resumen_norma(cuerpo)
        imp = impacto_norma(titulo + " " + cuerpo[:5000]) or [
            "Revisá el texto completo para verificar si alcanza a tu establecimiento o a la cadena láctea."]
        copy = (f"📢 Boletín Oficial: {titulo}. {res} Qué significa para el tambero: " + " ".join(imp)
                + " (Resumen automático: confirmá siempre en el texto oficial.)")
        out.append({"titulo": titulo, "url": u, "fecha": f, "solo_dia": sdia, "resumen": res,
                    "impacto": imp, "copy": copy, "tags": tags or ["Regulación y organismos"],
                    "seccion": "Boletín Oficial - Primera sección", "fuente": "Boletín Oficial"})
    log(f"  Boletín Oficial: {len(out)} norma(s) relevante(s)")
    return out


# ------------------------------------------------------------------ clima / ITH
def nivel_ith(v):
    if v < 72: return "sin estrés"
    if v < 79: return "estrés leve"
    if v < 89: return "estrés moderado"
    if v < 99: return "estrés severo"
    return "peligro de muerte"


def procesar_clima(red, ahora):
    out = []
    for nombre, lat, lon in C.ZONAS_CLIMA:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               "&hourly=temperature_2m,relative_humidity_2m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
               "&timezone=America%2FArgentina%2FBuenos_Aires&forecast_days=2")
        r = red.get(url, robots=False)
        if r is None:
            continue
        try:
            j = r.json()
            tmax, tmin = j["daily"]["temperature_2m_max"], j["daily"]["temperature_2m_min"]
            lluvia = j["daily"]["precipitation_sum"]
            temps, hums = j["hourly"]["temperature_2m"], j["hourly"]["relative_humidity_2m"]
            ith = []
            for dia in range(2):
                v = [(1.8 * t + 32) - (0.55 - 0.0055 * h) * (1.8 * t - 26)
                     for t, h in zip(temps[dia * 24:(dia + 1) * 24], hums[dia * 24:(dia + 1) * 24])
                     if t is not None and h is not None]
                ith.append(max(v) if v else 0)
        except Exception:
            red.problemas.append(f"{nombre}: respuesta de clima inesperada")
            continue
        manana = ahora + timedelta(days=1)
        titulo = (f"Pronóstico {nombre} - hoy: máx {tmax[0]:.0f}°/mín {tmin[0]:.0f}°, lluvia {lluvia[0]:.1f} mm, "
                  f"ITH máx {ith[0]:.0f} ({nivel_ith(ith[0])}) | mañana: máx {tmax[1]:.0f}°/mín {tmin[1]:.0f}°, "
                  f"lluvia {lluvia[1]:.1f} mm, ITH máx {ith[1]:.0f} ({nivel_ith(ith[1])})")
        out.append({"titulo": titulo, "url": f"https://open-meteo.com/en/docs#latitude={lat}&longitude={lon}",
                    "fecha": ahora, "solo_dia": True, "resumen": "", "tags": ["Clima y tiempo"],
                    "seccion": "Clima y estrés calórico", "fuente": "Open-Meteo"})
    log(f"  Clima: {len(out)} zona(s)")
    return out


# ------------------------------------------------------------------ salida
ORDEN = ["Boletín Oficial - Primera sección", "Clima y estrés calórico", "Eventos y capacitaciones",
         "Lechería y producción láctea", "Leche y productos lácteos", "Rodeo lechero y reproducción",
         "Sanidad y bienestar animal", "Alimentación, nutrición y forrajes", "Economía y comercialización",
         "Regulación y organismos", "Clima y tiempo", "Agro general"]


def agrupar(items):
    vistos_t, limpios = set(), []
    for it in sorted(items, key=lambda x: x["fecha"] or datetime.min.replace(tzinfo=TZ), reverse=True):
        k = norm(it["titulo"])[:90]
        if k in vistos_t:
            continue
        vistos_t.add(k)
        limpios.append(it)
    grupos = {}
    for it in limpios:
        grupos.setdefault(it["seccion"], []).append(it)
    return [(s, grupos[s]) for s in ORDEN if s in grupos] + [(s, v) for s, v in grupos.items() if s not in ORDEN]


def nombre_base(ahora):
    DIR_INFORMES.mkdir(exist_ok=True)
    base = f"{C.PREFIJO_ARCHIVOS}_{ahora:%d%m%y}"
    n, cand = 1, base
    while (DIR_INFORMES / f"{cand}.txt").exists() or (DIR_INFORMES / f"{cand}.html").exists():
        n += 1
        cand = f"{base}_{n}"
    return cand


def escribir_txt(path, grupos, ahora, problemas):
    L = [f"{C.BOT_NOMBRE} - Radar de noticias del sector lechero - {DIAS[ahora.weekday()]} {ahora:%d/%m/%Y %H:%M}", ""]
    total = sum(len(v) for _, v in grupos)
    L += [f"Total de ítems: {total}", ""]
    for sec, its in grupos:
        L += [f"===== {sec.upper()} =====", ""]
        for it in its:
            L += [f"{it['titulo']} | {fmt_fecha(it)}", it["url"]]
            if it.get("copy"):
                L += [f"COPY: {it['copy']}"]
            L.append("")
    if problemas:
        L += ["===== FUENTES CON PROBLEMAS (no son noticias) =====", *problemas, ""]
    path.write_text("\n".join(L), encoding="utf-8")


def escribir_html(path, grupos, ahora, problemas, resumen_fuentes):
    e = htmllib.escape
    total = sum(len(v) for _, v in grupos)
    h = [f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Radar de noticias · {C.BOT_NOMBRE} · {ahora:%d/%m/%Y}</title>
<style>
:root{{--bg:#f6f7f4;--fg:#1d2420;--card:#fff;--mut:#5d6a62;--acc:#1d6b45;--bd:#dfe5df;--tag:#e6f1ea}}
@media(prefers-color-scheme:dark){{:root{{--bg:#131715;--fg:#e8ede9;--card:#1b211e;--mut:#9aa89f;--acc:#6fcf9b;--bd:#2b3430;--tag:#24332b}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,Segoe UI,Roboto,sans-serif}}
main{{max-width:900px;margin:0 auto;padding:20px 16px 60px}}
h1{{font-size:1.5rem;margin:.2em 0}}h2{{font-size:1.1rem;margin:2em 0 .6em;color:var(--acc);text-transform:uppercase;letter-spacing:.04em;border-bottom:2px solid var(--bd);padding-bottom:.3em}}
.sub{{color:var(--mut)}}.card{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px 14px;margin:10px 0}}
.card a.t{{color:var(--fg);font-weight:600;text-decoration:none}}.card a.t:hover{{text-decoration:underline}}
.meta{{color:var(--mut);font-size:.85rem;margin-top:4px}}.tag{{display:inline-block;background:var(--tag);color:var(--acc);border-radius:99px;padding:1px 9px;font-size:.75rem;margin:4px 4px 0 0}}
.copy{{margin-top:8px;padding:8px 10px;border-left:3px solid var(--acc);background:var(--tag);font-size:.92rem}}
.url{{word-break:break-all;font-size:.8rem;color:var(--mut)}}details{{margin-top:2em;color:var(--mut)}}
</style></head><body><main>
<h1>Radar del sector lechero argentino</h1>
<p class="sub">{C.BOT_NOMBRE} · {DIAS[ahora.weekday()]} {ahora:%d/%m/%Y %H:%M} (GMT-3) · últimas {C.VENTANA_HORAS} h · {total} ítems</p>"""]
    for sec, its in grupos:
        h.append(f"<h2>{e(sec)} ({len(its)})</h2>")
        for it in its:
            h.append(f'<div class="card"><a class="t" href="{e(it["url"])}" target="_blank" rel="noopener noreferrer">{e(it["titulo"])}</a>'
                     f'<div class="meta">📅 {e(fmt_fecha(it))} · {e(it.get("fuente", ""))}</div>')
            if it.get("resumen") and not it.get("copy"):
                h.append(f'<div class="meta">{e(it["resumen"][:300])}</div>')
            if it.get("copy"):
                h.append(f'<div class="copy">{e(it["copy"])}</div>')
            h.append(f'<div class="url">{e(it["url"])}</div>')
            h.append("".join(f'<span class="tag">{e(t)}</span>' for t in it.get("tags", [])[:4]) + "</div>")
    if not grupos:
        h.append("<p>No se encontraron novedades en las últimas 24 horas.</p>")
    h.append(f"<details><summary>Estado de la corrida ({e(resumen_fuentes)})</summary><ul>"
             + "".join(f"<li>{e(p)}</li>" for p in problemas) + "</ul></details></main></body></html>")
    path.write_text("".join(h), encoding="utf-8")


# ------------------------------------------------------------------ main
def cargar_estado():
    f = DIR_ESTADO / "vistos.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8")), False
        except Exception:
            pass
    return {"urls": {}}, True


def guardar_estado(estado, ahora):
    DIR_ESTADO.mkdir(exist_ok=True)
    corte = ahora - timedelta(days=30)
    estado["urls"] = {u: t for u, t in estado["urls"].items() if datetime.fromisoformat(t) >= corte}
    (DIR_ESTADO / "vistos.json").write_text(json.dumps(estado, ensure_ascii=False, indent=0), encoding="utf-8")


def main():
    ahora = datetime.now(TZ)
    log(f"{C.BOT_NOMBRE} iniciando · {ahora:%d/%m/%Y %H:%M}")
    estado, primera = cargar_estado()
    red = Red()
    items, ok_fuentes = [], 0
    fuentes = list(C.FUENTES)
    random.shuffle(fuentes)
    for fu in fuentes:
        try:
            antes = len(red.problemas)
            its = procesar_fuente(red, fu, ahora, estado, primera)
            ok_fuentes += 1 if len(red.problemas) == antes or its else 0
            items += its
        except Exception as ex:
            red.problemas.append(f"{fu['nombre']} -> error inesperado: {type(ex).__name__}: {ex}")
        time.sleep(random.uniform(*C.PAUSA_ENTRE_FUENTES))
    for paso in (procesar_google_news, procesar_boletin, procesar_clima):
        try:
            items += paso(red, ahora)
        except Exception as ex:
            red.problemas.append(f"{paso.__name__} -> error inesperado: {type(ex).__name__}: {ex}")
    grupos = agrupar(items)
    base = nombre_base(ahora)
    resumen = f"{ok_fuentes}/{len(fuentes)} fuentes web respondieron"
    escribir_txt(DIR_INFORMES / f"{base}.txt", grupos, ahora, red.problemas)
    escribir_html(DIR_INFORMES / f"{base}.html", grupos, ahora, red.problemas, resumen)
    guardar_estado(estado, ahora)
    log(f"Listo: informes/{base}.txt y .html · {sum(len(v) for _, v in grupos)} ítems · {resumen}")
    if ok_fuentes == 0:
        log("ERROR: ninguna fuente respondió.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
