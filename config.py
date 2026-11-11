# -*- coding: utf-8 -*-
"""Configuración del BOT 384521. Todo lo editable está acá."""

BOT_NOMBRE = "BOT 384521"
ZONA_HORARIA = "America/Argentina/Buenos_Aires"   # GMT-3
VENTANA_HORAS = 24
PREFIJO_ARCHIVOS = "noticiasinta"                  # -> noticiasinta_101126.txt / .html

# ---------------------------------------------------------------- Cortesía de red
RESPETAR_ROBOTS = True            # si un sitio lo prohíbe, se saltea y queda en el log
PAUSA_MIN_POR_DOMINIO = 3.0       # segundos mínimos entre pedidos al MISMO dominio
PAUSA_MAX_POR_DOMINIO = 7.0
PAUSA_ENTRE_FUENTES = (1.5, 4.0)
TIMEOUT_CONEXION = 15
TIMEOUT_LECTURA = 60              # tolera servidores lentos
REINTENTOS = 4
BACKOFF = 4                       # espera 4s, 8s, 16s... entre reintentos
FALLAS_PARA_ABANDONAR_DOMINIO = 2 # corta de raíz si el sitio insiste en rechazar
MAX_ARTICULOS_A_ABRIR_POR_FUENTE = 8   # para leer fecha cuando el listado no la trae
MAX_ITEMS_POR_FUENTE = 60
BOLETIN_MAX_AVISOS = 250          # avisos de la 1ª sección a revisar en detalle

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.5",
    "Connection": "keep-alive",
}

# ---------------------------------------------------------------- Fuentes web
# tema: "lacteo" -> todo lo que publica es relevante | "general" -> se filtra por palabras clave
FUENTES = [
    {"nombre": "Argentina.gob.ar - Noticias", "url": "https://www.argentina.gob.ar/noticias", "tema": "general"},
    {"nombre": "Noticias institucionales (intainforma)", "url": "https://intainforma.inta.gob.ar/noticias/", "tema": "general"},
    {"nombre": "SENASA", "url": "https://www.argentina.gob.ar/senasa", "tema": "general"},
    {"nombre": "Todo Lechería", "url": "https://www.todolecheria.com.ar/noticias/", "tema": "lacteo"},
    {"nombre": "Agrofy News - Lechería", "url": "https://news.agrofy.com.ar/lecheria", "tema": "lacteo"},
    {"nombre": "Agrofy News", "url": "https://news.agrofy.com.ar/", "tema": "general"},
    {"nombre": "Bichos de Campo", "url": "https://bichosdecampo.com/", "tema": "general"},
    {"nombre": "Agrolink", "url": "https://agrolink.com.ar/ultimas-noticias/", "tema": "general"},
    {"nombre": "Clarín Rural", "url": "https://www.clarin.com/rural/", "tema": "general"},
    {"nombre": "Agroverdad", "url": "https://agroverdad.com.ar/todas-las-noticias", "tema": "general"},
    {"nombre": "Mundo Agro Córdoba", "url": "https://mundoagrocba.com.ar/", "tema": "general"},
    {"nombre": "Agritotal", "url": "https://www.agritotal.com/", "tema": "general"},
    {"nombre": "Revista Chacra (Infobae)", "url": "https://www.infobae.com/revista-chacra/", "tema": "general"},
    {"nombre": "La Nación - Campo", "url": "https://www.lanacion.com.ar/economia/campo/", "tema": "general"},
    {"nombre": "UNL - Noticias", "url": "https://www.unl.edu.ar/noticias/", "tema": "general"},
    {"nombre": "Infocampo", "url": "https://www.infocampo.com.ar/", "tema": "general"},
    {"nombre": "Agroempresario", "url": "https://agroempresario.com/", "tema": "general"},
    {"nombre": "Portal Lechero", "url": "https://portalechero.com/", "tema": "lacteo"},
    {"nombre": "OCLA", "url": "https://www.ocla.org.ar/", "tema": "lacteo"},
    {"nombre": "FCV UNL - Eventos", "url": "https://www.fcv.unl.edu.ar/eventos/", "tema": "general"},
    {"nombre": "CMVER", "url": "https://cmver.com.ar/", "tema": "general"},
    {"nombre": "Mundo Rural", "url": "https://mundorural.com.ar/", "tema": "general"},
    {"nombre": "Infoláctea", "url": "https://www.infolactea.com.ar/", "tema": "lacteo"},
]

# Reemplaza al scraping de la página de resultados de Google (que bloquea bots):
# Google Noticias publica un feed RSS oficial, ya filtrado a las últimas 24 h.
GOOGLE_NEWS_CONSULTAS = [
    '"INTA Lechero" OR "INTA Rafaela" OR "INTA Paraná"',
    'lechería OR tambo OR "leche cruda" OR "industria láctea"',
    '"precio de la leche" OR "productores tamberos" OR "cuenca lechera"',
    'bovinos OR vacas OR leucosis OR ganadería OR "sanidad animal"',
    'SENASA OR "buenas prácticas agrarias" OR veterinaria',
    'agro OR agronegocio OR "campo argentino" OR agropecuaria',
    'helada OR sequía OR "estrés calórico" OR "pronóstico" campo',
    'jornada OR capacitación OR congreso OR remate tambo OR lechería',
]

# Pronóstico + ITH (estrés calórico) vía Open-Meteo (API pública, sin clave)
ZONAS_CLIMA = [
    ("Rafaela (Santa Fe)", -31.25, -61.49),
    ("Paraná (Entre Ríos)", -31.73, -60.53),
    ("Villa María (Córdoba)", -32.41, -63.24),
    ("Trenque Lauquen (Buenos Aires)", -35.97, -62.73),
]

BOLETIN_URL = "https://www.boletinoficial.gob.ar/seccion/primera"

# No se scrapean (ver README): requieren login o prohíben el acceso automatizado.
FUENTES_NO_SOPORTADAS = ["instagram.com/*", "x.com/*"]

# ---------------------------------------------------------------- Palabras clave
CATEGORIAS = {
    "Lechería y producción láctea": """lechería|vacas|ganado|ganadería|sector lechero|actividad lechera|producción lechera|producción de leche|producción láctea|cadena láctea|cadena de valor láctea|industria láctea|industria lechera|tambo|tambos|establecimiento lechero|establecimientos lecheros|establecimiento tambero|establecimientos tamberos|productor lechero|productores lecheros|productor tambero|productores tamberos|tamberos|tambera|cuenca lechera|cuencas lecheras|sistemas de producción de leche|sistemas lecheros|sistemas pastoriles|tambo pastoril|tambo estabulado|tambo robotizado|tambo automatizado|ordeño|ordeño mecánico|ordeño robotizado|sala de ordeño|equipos de ordeño|máquinas de ordeño|instalaciones de ordeño|rutina de ordeño|eficiencia de ordeño|gestión del tambo|gestión lechera|administración de tambos|manejo del rodeo lechero|eficiencia productiva|productividad lechera|inta lechero|inta rafaela|inta paraná|inta parana|lechero|lechera|lecheros|lecheras""",
    "Leche y productos lácteos": """leche|leche cruda|leche bovina|leche fluida|leche refrigerada|leche pasteurizada|leche ultrapasteurizada|leche en polvo|leche concentrada|leche en sachet|productos lácteos|productos derivados de la leche|derivados lácteos|lácteos|lácteo|quesos|queso|yogur|manteca|crema de leche|dulce de leche|suero lácteo|lactosuero|proteínas lácteas|grasa láctea|sólidos lácteos|composición de la leche|calidad de leche|calidad higiénico-sanitaria de la leche|inocuidad de productos lácteos|análisis de leche|recuento de células somáticas|recuento bacteriano|células somáticas|residuos de antibióticos en leche|adulteración de leche|contaminantes en leche|refrigeración de leche|conservación de leche|transporte de leche|recepción de leche|leche de calidad""",
    "Rodeo lechero y reproducción": """rodeo lechero|vacas lecheras|vacas en producción|vacas en ordeño|vacas secas|vacas de descarte|descarte de vacas|vaquillonas|vaquillonas lecheras|reposición de vientres|reposición de vaquillonas|terneros de tambo|terneras de tambo|crianza artificial de terneros|crianza de terneras|recría de vaquillonas|reproducción bovina|reproducción en rodeos lecheros|eficiencia reproductiva|inseminación artificial|inseminación artificial a tiempo fijo|iatf|transferencia embrionaria|genética lechera|mejoramiento genético bovino|selección genética|biotecnología reproductiva|fertilidad|índices reproductivos|período de transición|período seco|lactancia|curva de lactancia|producción individual|control lechero|control de producción de leche|rodeo|terneros|terneras""",
    "Sanidad y bienestar animal": """sanidad del rodeo lechero|salud del rodeo|sanidad bovina|sanidad animal|mastitis|mastitis bovina|mastitis ambiental|mastitis contagiosa|leucosis|leucosis bovina|brucelosis|brucelosis bovina|tuberculosis bovina|queratoconjuntivitis|enfermedades del ganado lechero|enfermedades de los terneros|salud de terneros|bienestar animal|bienestar de vacas lecheras|estrés calórico|estrés térmico|índice de temperatura y humedad|ith|mortalidad de terneros|mortalidad en rodeos lecheros|vacunación bovina|vacunación|productos veterinarios|medicamentos veterinarios|antibióticos veterinarios|residuos de medicamentos en leche|trazabilidad animal|identificación animal|identificación electrónica|veterinaria|veterinario|veterinarios|aftosa|fiebre aftosa|garrapata|bovinos|bovino|bovina|vacuna|vacunas|senasa""",
    "Alimentación, nutrición y forrajes": """alimentación de vacas lecheras|nutrición de vacas lecheras|nutrición bovina|alimentación del rodeo lechero|dieta de vacas lecheras|ración para vacas lecheras|balanceado para vacas lecheras|suplementación|suplementación alimenticia|concentrados|forrajes|forraje|reservas forrajeras|heno|pasturas|pasturas implantadas|pasturas megatérmicas|alfalfa|verdeos|verdeo|maíz para silo|silaje|silo|sorgo forrajero|calidad de forrajes|calidad nutricional|balance nutricional|eficiencia alimenticia|conversión alimenticia|agua para consumo animal|bebederos|comederos|alimentación de terneros|sustitutos lácteos|reemplazantes lácteos|calostro|nutrición animal|alimentación animal""",
    "Economía y comercialización": """economía lechera|economía del tambo|costos de producción de leche|costos de producción lechera|costo por litro de leche|precio de la leche|precio al productor|precio de leche cruda|mercado lácteo|mercado de la leche|comercialización de leche|comercialización de productos lácteos|industria procesadora de leche|exportación de productos lácteos|exportaciones lácteas|importación de productos lácteos|retenciones|derechos de exportación|rentabilidad del tambo|financiamiento|créditos para productores|emergencia agropecuaria|emergencia y/o desastre agropecuario|desastre agropecuario|precio del ganado|mercado de hacienda|liniers|cañuelas|hacienda|commodities|dólar agro|tipo de cambio agro""",
    "Regulación y organismos": """secretaría de agricultura|secretaría de bioeconomía|registro de establecimientos lácteos|habilitación de establecimientos lácteos|habilitación de tambos|habilitación de plantas lácteas|transporte de productos lácteos|buenas prácticas lecheras|buenas prácticas de ordeño|buenas prácticas de manufactura|buenas prácticas agrarias|inocuidad alimentaria|higiene del tambo|higiene de la leche|fiscalización de productos lácteos|regulación de productos lácteos|rotulado de productos lácteos|código alimentario argentino|inta|inase""",
    "Clima y tiempo": """clima|pronóstico|helada|heladas|sequía|lluvias|precipitaciones|inundación|inundaciones|ola de calor|el niño|la niña|niño|niña|servicio meteorológico|smn|temperatura|anegamiento|granizo|tormenta""",
    "Eventos y capacitaciones": """jornada|jornadas|curso|cursos|capacitación|capacitaciones|congreso|congresos|expo|exposición|remate|remates|charla|charlas|taller|talleres|webinar|seminario|simposio|día de campo|encuentro|workshop|feria|agroactiva|expoagro|ciclo de charlas|inscripción""",
    "Agro general": """agro|agronegocio|agronegocios|campo argentino|agropecuaria|agropecuario|agricultura|rural|gado|cosecha|siembra|soja|maíz|trigo|girasol|productores|productor agropecuario|cooperativa|cooperativas|biotecnología|agroindustria""",
}

# Qué implica una norma para el tambero (reglas fijas, sin IA)
IMPACTOS_NORMA = [
    ("derechos de exportación|retenciones|alícuota", "Puede modificar el precio que recibe la industria por sus exportaciones y, por arrastre, el precio de la leche al productor."),
    ("senasa|sanitari|vacunación|brucelosis|tuberculosis|leucosis|aftosa|trazabilidad|identificación", "Afecta requisitos sanitarios, de vacunación o de trazabilidad del rodeo: conviene revisar plazos y obligaciones del establecimiento."),
    ("crédito|financiamiento|banco nación|línea de|tasa|prórroga|refinanciación", "Puede abrir o cambiar condiciones de financiamiento para inversiones o capital de trabajo del tambo."),
    ("emergencia agropecuaria|desastre agropecuario|zona de emergencia", "Habilita beneficios (prórrogas impositivas, asistencia) para productores de zonas afectadas: verificar si el departamento del tambo está incluido."),
    ("leche|lácte|tambo|lechería|lechero", "Alcanza de manera directa a la cadena láctea; revisar si cambia requisitos de habilitación, calidad o comercialización."),
    ("impuesto|iva|ganancias|monotributo|arca|afip|facturación|retención", "Tiene impacto impositivo o administrativo: consultar con el contador cómo se aplica al tambo."),
    ("importación|arancel|mercosur|exportación", "Modifica condiciones de comercio exterior que influyen en la competitividad y en los precios del sector."),
    ("medicamento|veterinari|producto fitosanitario|agroquímic|antibiótico", "Regula insumos de uso veterinario/agrícola: puede cambiar qué productos se pueden usar o comprar."),
    ("inta|inase|investigación|convenio|capacitación", "Vinculado a investigación, transferencia o capacitación disponible para el sector."),
]
