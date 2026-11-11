"""Prueba sin internet: simula las respuestas de los sitios. Ejecutar: python tests/test_offline.py"""
import json, sys, tempfile, shutil
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as C, radar as R

ahora = datetime.now(R.TZ)
hoy_iso = ahora.strftime("%Y-%m-%dT%H:%M:%S-03:00")
ayer_iso = (ahora - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S-03:00")
rss_fecha = (ahora - timedelta(hours=2)).strftime("%a, %d %b %Y %H:%M:%S -0300")

class Resp:
    def __init__(s, body, status=200): s.content = body.encode(); s.text = body; s.status_code = status
    def json(s): return json.loads(s.text)

HTML_LAC = f"""<html><head><link rel="alternate" type="application/rss+xml" href="/feed"></head><body>
<nav><a href="/menu/institucional-largo-texto-del-menu">Menú institucional largo texto de menú</a></nav>
<article><a href="/noticias/mastitis-ambiental-nuevas-estrategias-de-control">Mastitis ambiental: nuevas estrategias de control en tambos</a><time datetime="{hoy_iso}"></time></article>
<article><a href="/noticias/nota-vieja-sobre-vacas-lecheras-de-hace-dias">Nota vieja sobre vacas lecheras de hace días atrás</a><time datetime="{ayer_iso}"></time></article>
<article><a href="/noticias/jornada-de-capacitacion-en-tambo-rafaela">Jornada de capacitación en tambo robotizado en Rafaela</a><span>Publicado hace 3 horas</span></article>
<article><a href="/noticias/torneo-de-futbol-del-club-del-pueblo-final">Torneo de fútbol del club del pueblo llega a la final</a><span>hace 1 hora</span></article>
</body></html>"""
RSS = f"""<?xml version="1.0"?><rss><channel><item><title>Precio de la leche al productor sube en noviembre</title>
<link>https://ejemplo.com.ar/precio-leche</link><pubDate>{rss_fecha}</pubDate><description>&lt;p&gt;El valor del litro&lt;/p&gt;</description></item></channel></rss>"""
GN = f"""<?xml version="1.0"?><rss><channel><item><title>SENASA actualiza vacunación contra brucelosis - Infobae</title>
<link>https://news.google.com/rss/articles/abc</link><pubDate>{rss_fecha}</pubDate><source url="https://infobae.com">Infobae</source></item></channel></rss>"""
BO_LIST = """<html><body><a href="/detalleAviso/primera/300001/20261110">SENASA Resolución 100/2026</a>
<a href="/detalleAviso/primera/300002/20261110">MINISTERIO DE SALUD Resolución 5/2026</a></body></html>"""
BO_1 = "<html><body><h1 id='tituloDetalleAviso'>Resolución 100/2026</h1><div id='cuerpoDetalleAviso'>VISTO el expediente... ARTÍCULO 1º.- Establécese la vacunación obligatoria contra la brucelosis bovina en tambos y reduce los derechos de exportación de lácteos. ARTÍCULO 2º.- Comuníquese.</div></body></html>"
BO_2 = "<html><body><div id='cuerpoDetalleAviso'>ARTÍCULO 1º.- Apruébase el protocolo hospitalario.</div></body></html>"
METEO = json.dumps({"daily": {"temperature_2m_max": [33, 30], "temperature_2m_min": [20, 18], "precipitation_sum": [0, 5]},
                    "hourly": {"temperature_2m": [30] * 48, "relative_humidity_2m": [60] * 48}})

def fake_get(self, url, robots=True, referer=None):
    if "open-meteo" in url: return Resp(METEO)
    if "news.google.com" in url: return Resp(GN)
    if url.endswith("/feed"): return Resp(RSS)
    if "boletinoficial" in url and "seccion" in url: return Resp(BO_LIST)
    if "300001" in url: return Resp(BO_1)
    if "300002" in url: return Resp(BO_2)
    if "todolecheria" in url and url.endswith("/noticias/"): return Resp(HTML_LAC)
    if "/noticias/" in url:  # artículo individual
        return Resp(f"<html><head><meta property='article:published_time' content='{hoy_iso}'></head></html>")
    return None

R.Red.get = fake_get
R.time.sleep = lambda *_: None
tmp = Path(tempfile.mkdtemp())
R.DIR_INFORMES, R.DIR_ESTADO = tmp / "informes", tmp / "estado"
C.FUENTES = [{"nombre": "Fuente lácteo", "url": "https://www.todolecheria.com.ar/noticias/", "tema": "lacteo"},
             {"nombre": "Fuente caída", "url": "https://caida.com/", "tema": "general"}]
# primera ejecución, luego segunda el mismo día (no debe sobrescribir)
assert R.main() == 0
assert R.main() == 0
archivos = sorted(p.name for p in R.DIR_INFORMES.iterdir())
print(archivos)
txt = (R.DIR_INFORMES / archivos[1]).read_text(encoding="utf-8")
print(txt[:2500])
assert len(archivos) == 4 and archivos[0].startswith("noticiasinta_") and f"{ahora:%d%m%y}" in archivos[0]
assert "Mastitis ambiental" in txt and "Nota vieja" not in txt
assert "Precio de la leche" in txt and "brucelosis" in txt.lower() and "protocolo hospitalario" not in txt
assert "COPY:" in txt and "Pronóstico Rafaela" in txt
assert "inta lechero" not in txt.lower()
html = (R.DIR_INFORMES / archivos[0]).read_text(encoding="utf-8")
assert "384521" in html and "intalechero" not in html.lower()
print("OK - todas las pruebas pasaron")
shutil.rmtree(tmp)
