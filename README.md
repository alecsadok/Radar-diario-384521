# Radar 384521

Recopila cada día (23:00, GMT-3) noticias, eventos, normas del Boletín Oficial y pronóstico/ITH
relevantes para la lechería argentina. **No usa inteligencia artificial**: es un script de Python
que corre solo en GitHub Actions y guarda dos archivos por día en `informes/`:

- `noticiasinta_ddmmaa.txt` → título | día y fecha, y en la línea de abajo el link.
- `noticiasinta_ddmmaa.html` → versión para leer, agrupada por tema.

Si se ejecuta dos veces el mismo día no se pisa nada: crea `_2`, `_3`, etc.

## Estructura
| Archivo | Para qué sirve |
|---|---|
| `radar.py` | El programa |
| `config.py` | **Lo único que normalmente tocás**: fuentes, palabras clave, pausas, zonas de clima |
| `.github/workflows/radar.yml` | Programación diaria y guardado de resultados |
| `informes/` | Resultados diarios |
| `estado/vistos.json` | Memoria de enlaces (para detectar novedades en sitios sin fecha) |
| `tests/test_offline.py` | Prueba automática sin internet |

## Puesta en marcha (una sola vez)
1. Subí todo el contenido de esta carpeta al repo (Add file → Upload files; respetá la carpeta `.github/workflows/`).
2. Pestaña **Settings → Actions → General → Workflow permissions** → elegí **Read and write permissions** → Save.
3. Pestaña **Actions** → "Radar diario 384521" → **Run workflow** para probar.
4. A los pocos minutos aparecen los archivos en `informes/`.

## Mantenimiento para que funcione siempre
1. **Revisá la pestaña Actions una vez por semana.** Un tilde verde = anduvo. Una cruz roja = abrí la corrida y leé el error.
2. **Pausa de GitHub a los 60 días:** GitHub desactiva las programaciones de repos sin actividad. Como el bot guarda un informe por día, el repo siempre tiene actividad. Si alguna vez ves el aviso "workflow disabled", pulsá *Enable workflow*.
3. **Demoras normales:** GitHub puede arrancar la corrida unos minutos (a veces más de 30) tarde en horas de mucha carga. Es esperable.
4. **Un sitio dejó de traer notas:** abrí el HTML del día, sección "Estado de la corrida": lista qué fuentes dieron error. Causas típicas: cambió la web, el sitio bloquea a servidores de GitHub, o la nota no cumple el filtro de 24 h.
   - Si un sitio ofrece RSS, agregá su URL como fuente: los feeds son lo más estable.
   - Si un sitio bloquea siempre, sacalo de `FUENTES` en `config.py` o pedile al medio un RSS.
5. **Agregar o quitar palabras clave:** editá `CATEGORIAS` en `config.py` (términos separados por `|`, sin importar tildes ni mayúsculas).
6. **Cambiar la hora:** en `radar.yml`, `cron: "0 2 * * *"` es hora UTC (02:00 UTC = 23:00 Argentina). Para las 20:00 Argentina serían las `0 23 * * *`.
7. **Límites de cortesía:** si algún sitio te da errores 429/403, subí `PAUSA_MIN_POR_DOMINIO` y `PAUSA_MAX_POR_DOMINIO` en `config.py`.
8. **Si cambia el Boletín Oficial:** el programa busca enlaces `/detalleAviso/primera/...`. Si renuevan la web, hay que ajustar la función `procesar_boletin`.
9. **Probar en tu computadora:** `pip install -r requirements.txt` y `python radar.py`.

## Qué NO hace (y por qué)
- **Instagram y X** no se leen: exigen iniciar sesión y prohíben el acceso automatizado; además bloquean las IP de GitHub.
- **Búsqueda de Google:** reemplazada por el feed RSS oficial de Google Noticias (mismas búsquedas, ya limitadas a 24 h).
- **Eludir bloqueos:** el bot es paciente (pausas de 3–7 s por sitio, reintentos con espera creciente, abandona un dominio que lo rechaza) y respeta `robots.txt`, pero no usa proxies rotativos ni evade captchas. Si un sitio no quiere tráfico automático, se omite.
- **Resumen de normas:** no es IA, son reglas fijas (palabras clave → frases de impacto). Sirve de orientación; siempre confirmar en el texto oficial.
