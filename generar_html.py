"""Convierte el informe Markdown validado en un HTML autocontenido.

Dependencia: pip install mistune
Ejecutar desde cualquier carpeta: python generar_html.py
"""

import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import mistune

BASE = Path(__file__).resolve().parent
ORIGEN = BASE / "informes" / "informe_vulnerabilidades.md"
DESTINO = BASE / "informes" / "informe_vulnerabilidades.html"

INDICADORES = [
    ("Evaluaciones realizadas", "Evaluaciones", "neutral"),
    ("Afectaciones confirmadas según inventario", "Confirmadas", "danger"),
    ("Posibles afectaciones", "Posibles", "warning"),
    ("No aplicables", "No aplicables", "success"),
    ("Prioridad alta", "Prioridad alta", "danger"),
    ("Prioridad media", "Prioridad media", "warning"),
]

ESTILOS = """
:root { --ink:#14263c; --muted:#617186; --line:#dce5ed; --bg:#f3f6fa;
        --paper:#fff; --navy:#10263f; --teal:#117b83; }
* { box-sizing:border-box; }
html { scroll-behavior:smooth; }
body { margin:0; background:var(--bg); color:var(--ink);
       font-family:Inter,Segoe UI,Arial,sans-serif; font-size:14px; line-height:1.62; }
.hero { background:linear-gradient(115deg,#0e233c,#173d57 72%,#126c70);
        color:#fff; padding:48px max(24px,calc((100vw - 1120px)/2)); }
.hero .eyebrow { text-transform:uppercase; letter-spacing:.12em;
                  font-weight:750; font-size:11px; color:#abd8d8; }
.hero h1 { margin:10px 0 6px; font-size:clamp(28px,4vw,42px);
           line-height:1.15; letter-spacing:-.03em; }
.hero p { color:#d7e4ec; margin:0; font-size:15px; }
.hero .flag { display:inline-block; border:1px solid #8ab9bb; border-radius:40px;
              margin-top:18px; padding:5px 12px; font-size:11px; color:#d3f4f1; }
.wrapper { max-width:1168px; margin:0 auto; padding:26px 24px 60px; }
.kpis { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }
.kpi { background:#fff; border:1px solid var(--line); border-radius:13px;
       padding:20px 22px; box-shadow:0 3px 15px #172c4210; border-top:3px solid #7492a7; }
.kpi.danger { border-top-color:#c54c51; }
.kpi.warning { border-top-color:#d19b34; }
.kpi.success { border-top-color:#228a74; }
.kpi .value { display:block; font-size:31px; font-weight:790; line-height:1.2; }
.kpi .label { color:var(--muted); font-size:12px; font-weight:600; }
.notice { margin-top:20px; background:#e8f1f3; color:#285766;
          padding:13px 16px; border-left:3px solid #30848b; border-radius:7px; font-size:13px; }
.document { margin-top:22px; padding:28px 36px 42px; background:var(--paper);
            border:1px solid var(--line); border-radius:14px;
            box-shadow:0 6px 28px #172c420e; }
.document h1 { font-size:24px; margin:0 0 12px; }
.document h2 { font-size:20px; margin:34px 0 16px; padding:0 0 10px;
               border-bottom:1px solid var(--line); letter-spacing:-.015em; }
.document h3 { font-size:15px; margin:22px 0 8px; color:var(--teal); }
.document p { margin:8px 0 14px; }
.document li { margin:5px 0; }
.document ul,.document ol { padding-left:23px; }
.document a { color:#087d8b; overflow-wrap:anywhere; text-decoration-thickness:1px; }
.document a:hover { color:#044e62; }
.document table { border-collapse:collapse; width:100%; margin:16px 0 23px;
                  font-size:12px; }
.document table th { background:#183550; color:white; font-weight:650;
                     padding:11px 10px; text-align:left; }
.document table td { padding:10px; border-bottom:1px solid #e4eaf0; vertical-align:top; }
.document table tbody tr:nth-child(even) { background:#f5f8fb; }
.document table tbody tr:hover { background:#edf5f6; }

.document table td:nth-child(1) { white-space:nowrap; }
.document table td:nth-child(5) { overflow-wrap:anywhere; }

.table-scroll { overflow-x:auto; }
.pill { display:inline-block; padding:3px 8px; border-radius:16px;
        font-size:11px; font-weight:700; white-space:nowrap; }
.pill-confirmada,.pill-alta { background:#fce7e7; color:#a82e36; }
.pill-posible,.pill-media { background:#fff0d5; color:#916018; }
.pill-no_aplicable,.pill-sin_prioridad { background:#e5f2ed; color:#28735d; }
.footer { color:var(--muted); text-align:center; padding:24px 0 4px; font-size:12px; }
@media(max-width:760px) {
  .kpis { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .hero { padding:35px 22px; }
  .wrapper { padding:18px 12px 35px; }
  .document { padding:20px 16px; }
  .document table { min-width:740px; }
}
@media print {
  @page { size:A4 landscape; margin:13mm; }
  body { background:white; color:#111; font-size:11px; }
  .hero { padding:15px 20px; print-color-adjust:exact; -webkit-print-color-adjust:exact; }
  .hero h1 { font-size:25px; }
  .wrapper { padding:12px 0; }
  .kpi { padding:10px 14px; box-shadow:none; break-inside:avoid; }
  .kpi .value { font-size:23px; }
  .document { box-shadow:none; border:0; padding:10px 0; }
  .document h2,.document h3 { break-after:avoid; }
  .document tr { break-inside:avoid; }
  .document table { font-size:10px; }
  .document table th { print-color-adjust:exact; -webkit-print-color-adjust:exact; }
  a { color:#111; }
}
"""


def obtener_numero(texto: str, etiqueta: str) -> int:
    patron = rf"(?m)^- {re.escape(etiqueta)}:\s*\*\*(\d+)\*\*\s*$"
    encontrado = re.search(patron, texto)
    if not encontrado:
        raise ValueError(f"Falta el indicador en el Markdown: {etiqueta}")
    return int(encontrado.group(1))


def generar_html() -> Path:
    texto = ORIGEN.read_text(encoding="utf-8-sig")
    kpis = "\n".join(
        f'<div class="kpi {clase}"><span class="value">{obtener_numero(texto, etiqueta)}</span>'
        f'<span class="label">{escape(nombre)}</span></div>'
        for etiqueta, nombre, clase in INDICADORES
    )

    renderer = mistune.create_markdown(plugins=["table", "url"])
    cuerpo = renderer(texto)

    # El HTML se alimenta de los números y hallazgos del Markdown validado.
    # Solo decoramos las etiquetas de estado y prioridad ya existentes.
    etiquetas = {
        "confirmada": "Confirmada", "posible": "Posible",
        "no_aplicable": "No aplicable", "alta": "Alta",
        "media": "Media", "sin_prioridad": "Sin prioridad",
    }
    cuerpo = re.sub(
        r"<td>(confirmada|posible|no_aplicable|alta|media|sin_prioridad)</td>",
        lambda m: (
            f'<td><span class="pill pill-{m.group(1)}">'
            f'{etiquetas[m.group(1)]}</span></td>'
        ),
        cuerpo,
    )
    # Para tablas anchas, habilitamos desplazamiento horizontal en móviles.
    cuerpo = cuerpo.replace('<table>', '<div class="table-scroll"><table>')
    cuerpo = cuerpo.replace('</table>', '</table></div>')

    fecha_html = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pagina = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Informe de vulnerabilidades IT/OT | Entrepinares</title>
<style>{ESTILOS}</style>
</head>
<body>
<header class="hero">
  <div class="eyebrow">Entrepinares · Demostración formativa</div>
  <h1>Vulnerabilidades IT/OT</h1>
  <p>Informe de análisis basado en CISA KEV e inventario ficticio</p>
  <span class="flag">ANÁLISIS BAJO DEMANDA · CATÁLOGO GUARDADO</span>
</header>
<main class="wrapper">
  <section class="kpis" aria-label="Indicadores principales">{kpis}</section>
  <div class="notice">Este informe combina reglas específicas de correlación,
  el cribado completo de CISA KEV y un piloto de evaluación NVD.
  No constituye un escaneo de infraestructura real.</div>
  <article class="document">{cuerpo}</article>
  <footer class="footer">Documento generado a partir del informe Markdown validado · {fecha_html}</footer>
</main>
</body>
</html>
"""
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(pagina, encoding="utf-8")
    return DESTINO


if __name__ == "__main__":
    ruta = generar_html()
    print("INFORME HTML GENERADO CORRECTAMENTE")
    print(f"Archivo: {ruta}")
