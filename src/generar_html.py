"""
Módulo Generador de Dashboard HTML
Genera la interfaz estática interactiva con los indicadores reordenados y el gráfico Waterfall.
"""
from datetime import datetime
from html import escape
import json
from pathlib import Path
from procesar_datos import obtener_datos_obras, obtener_datos_transacciones

BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_OUTPUT = BASE_DIR / "output" / "dashboard_obras.html"
RUTA_INDEX = BASE_DIR / "index.html"
RUTA_REPORTE = BASE_DIR / "reporte_obras.html"


def _formatear_monto(valor):
    return f"${float(valor or 0):,.2f}"


def _generar_reporte_html(datos_obras):
    obras_en_curso = sorted(
        (
            (obra, datos)
            for obra, datos in datos_obras.items()
            if datos["estado"] == "ACTIVA"
        ),
        key=lambda item: item[0].casefold(),
    )
    totales = {
        campo: sum(float(datos.get(campo_datos, 0) or 0) for _, datos in obras_en_curso)
        for campo, campo_datos in (
            ("contratos", "monto_contrato"),
            ("ejecutado", "estimado_ejecutado"),
            ("desembolsado", "cobrado_desembolsado"),
            ("por_cobrar", "por_cobrar"),
            ("flujo", "flujo_caja"),
        )
    }
    porcentaje_ejecutado = (
        totales["ejecutado"] / totales["contratos"] * 100
        if totales["contratos"] > 0
        else 0
    )
    porcentaje_desembolsado = (
        totales["desembolsado"] / totales["contratos"] * 100
        if totales["contratos"] > 0
        else 0
    )
    fichas = []
    for obra, datos in obras_en_curso:
        contrato = float(datos["monto_contrato"] or 0)
        ejecutado = float(datos["estimado_ejecutado"] or 0)
        porcentaje_cobrado = max(
            0, min(100, float(datos["avance_financiero_pct"] or 0))
        )
        porcentaje_ejecutado_obra = (
            max(0, min(100, ejecutado / contrato * 100)) if contrato > 0 else 0
        )
        fichas.append(
            f"""<article class="project">
                <header class="project-heading">
                    <div><p class="project-kicker">Obra en curso</p><h2>{escape(obra)}</h2></div>
                    <span class="status">En Curso</span>
                </header>
                <div class="progress-block">
                    <div class="progress-heading"><span>Avance financiero cobrado</span><strong>{porcentaje_cobrado:.2f}%</strong></div>
                    <div class="progress-track"><span style="width:{porcentaje_cobrado}%"></span></div>
                    <p>Ejecutado: {_formatear_monto(ejecutado)} ({porcentaje_ejecutado_obra:.2f}% del contrato).</p>
                </div>
                <div class="project-metrics">
                    <div><span>Monto del contrato</span><strong>{_formatear_monto(contrato)}</strong></div>
                    <div><span>Monto ejecutado</span><strong>{_formatear_monto(ejecutado)}</strong></div>
                    <div><span>Total desembolsado</span><strong>{_formatear_monto(datos['cobrado_desembolsado'])}</strong></div>
                    <div><span>Saldo por cobrar</span><strong>{_formatear_monto(datos['por_cobrar'])}</strong></div>
                    <div><span>Flujo de caja</span><strong>{_formatear_monto(datos['flujo_caja'])}</strong></div>
                    <div><span>Estado</span><strong>En Curso</strong></div>
                </div>
            </article>"""
        )

    fecha = datetime.now().strftime("%d/%m/%Y")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte ejecutivo, gerencial y financiero | Inversora Macroandes</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ max-width: 980px; margin: 0 auto; padding: 28px 32px; color: #27332d; background: #fff; font: 14px/1.5 Arial, sans-serif; }}
        .report-actions {{ display: flex; justify-content: flex-end; margin-bottom: 18px; }}
        .print-button {{ padding: 9px 14px; border: 1px solid #176b4d; border-radius: 5px; color: #fff; background: #176b4d; cursor: pointer; font: inherit; font-weight: 700; }}
        .report-header {{ display: flex; align-items: center; gap: 18px; margin-bottom: 22px; padding-bottom: 16px; border-bottom: 3px solid #176b4d; }}
        .logo {{ width: 66px; height: 74px; flex: 0 0 66px; object-fit: contain; }}
        .company {{ margin: 0 0 5px; color: #176b4d; font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
        h1 {{ margin: 0; color: #202923; font-size: 25px; line-height: 1.2; }}
        .report-subtitle {{ margin: 6px 0 0; color: #68756c; font-size: 12px; }}
        .scope {{ margin: 0 0 18px; padding: 10px 12px; border-left: 3px solid #176b4d; color: #405047; background: #f1f6f2; }}
        .section-title {{ margin: 20px 0 10px; color: #2b3830; font-size: 17px; }}
        .summary {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 9px; }}
        .metric {{ min-height: 76px; padding: 11px 12px; border: 1px solid #dfe6df; border-radius: 5px; }}
        .metric span, .project-metrics span {{ display: block; color: #59665d; font-size: 11px; font-weight: 600; }}
        .metric strong {{ display: block; margin-top: 5px; color: #176b4d; font-size: 18px; overflow-wrap: anywhere; }}
        .management-summary {{ margin: 12px 0 18px; color: #405047; }}
        .project {{ margin-top: 12px; padding: 13px; border: 1px solid #dfe6df; border-radius: 5px; break-inside: avoid; page-break-inside: avoid; }}
        .project-heading {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; padding-bottom: 9px; border-bottom: 1px solid #e8ede8; }}
        .project-kicker {{ margin: 0 0 3px; color: #68756c; font-size: 10px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }}
        .project h2 {{ margin: 0; color: #202923; font-size: 17px; line-height: 1.35; }}
        .status {{ flex: 0 0 auto; padding: 4px 8px; border-radius: 3px; color: #176b4d; background: #e8f3ed; font-size: 11px; font-weight: 700; }}
        .progress-block {{ margin: 11px 0; }}
        .progress-heading {{ display: flex; justify-content: space-between; gap: 12px; color: #445148; font-size: 12px; }}
        .progress-track {{ height: 7px; margin-top: 5px; overflow: hidden; border-radius: 5px; background: #e8ede8; }}
        .progress-track span {{ display: block; height: 100%; border-top: 7px solid #4a9b70; background: #4a9b70; }}
        .progress-block p {{ margin: 5px 0 0; color: #68756c; font-size: 11px; }}
        .project-metrics {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 7px; }}
        .project-metrics > div {{ padding: 8px; background: #f8faf8; }}
        .project-metrics strong {{ display: block; margin-top: 3px; color: #29372d; font-size: 13px; overflow-wrap: anywhere; }}
        .empty {{ padding: 20px; border: 1px dashed #cfd9d0; color: #66736a; text-align: center; }}
        .footer {{ margin-top: 20px; padding-top: 9px; border-top: 1px solid #dfe6df; color: #68756c; font-size: 10px; }}
        @page {{ size: portrait; margin: 15mm; }}
        @media (max-width: 620px) {{ body {{ padding: 18px 14px; }} .summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} .project-metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
        @media print {{
            * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            body {{ max-width: none; padding: 0; font-size: 12pt; line-height: 1.45; }}
            .report-actions {{ display: none; }}
            .report-header {{ gap: 6mm; margin-bottom: 7mm; padding-bottom: 5mm; }}
            .logo {{ width: 24mm; height: 27mm; flex-basis: 24mm; }}
            .company {{ margin-bottom: 2mm; font-size: 11pt; }}
            h1 {{ font-size: 25pt; line-height: 1.2; }}
            .report-subtitle {{ margin-top: 2mm; font-size: 11pt; }}
            .scope {{ margin-bottom: 5mm; padding: 3mm 4mm; font-size: 11pt; }}
            .section-title {{ margin: 6mm 0 3mm; font-size: 17pt; line-height: 1.25; break-after: avoid; page-break-after: avoid; }}
            .summary {{ gap: 3mm; }}
            .metric {{ min-height: 20mm; padding: 3mm; }}
            .metric span, .project-metrics span {{ font-size: 10.5pt; line-height: 1.3; }}
            .metric strong {{ margin-top: 1.5mm; font-size: 15pt; line-height: 1.25; }}
            .management-summary {{ margin: 4mm 0 6mm; font-size: 11.5pt; line-height: 1.45; }}
            .project {{ margin-top: 4mm; padding: 4mm; }}
            .project-heading {{ padding-bottom: 3mm; }}
            .project-kicker {{ margin-bottom: 1mm; font-size: 9.5pt; }}
            .project h2 {{ font-size: 16pt; line-height: 1.3; }}
            .status {{ padding: 1mm 2mm; font-size: 10.5pt; }}
            .progress-block {{ margin: 3mm 0; }}
            .progress-heading {{ font-size: 11.5pt; }}
            .progress-track {{ height: 2mm; margin-top: 1.5mm; }}
            .progress-track span {{ border-top-width: 2mm; }}
            .progress-block p {{ margin-top: 1.5mm; font-size: 10.5pt; }}
            .project-metrics {{ gap: 2mm; }}
            .project-metrics > div {{ padding: 2.5mm; }}
            .project-metrics strong {{ margin-top: 1mm; font-size: 12pt; line-height: 1.3; }}
            .footer {{ margin-top: 6mm; padding-top: 2.5mm; font-size: 10pt; line-height: 1.4; }}
            .progress-track span {{ border-top-color: #4a9b70; }}
        }}
    </style>
</head>
<body>
    <div class="report-actions"><button class="print-button" type="button" onclick="window.print()">Imprimir / Guardar como PDF</button></div>
    <header class="report-header">
        <img class="logo" src="src/assets/Logo.svg" alt="Logo de Inversora Macroandes">
        <div><p class="company">Inversora Macroandes</p><h1>Reporte ejecutivo, gerencial y financiero</h1><p class="report-subtitle">Tablero de obras · Fecha de emisión: {fecha}</p></div>
    </header>
    <p class="scope"><strong>Alcance:</strong> este reporte presenta exclusivamente las obras con estado “En Curso” registrado en el tablero.</p>
    <h2 class="section-title">Resumen ejecutivo del portafolio activo</h2>
    <section class="summary" aria-label="Indicadores consolidados de obras en curso">
        <div class="metric"><span>Obras en curso</span><strong>{len(obras_en_curso)}</strong></div>
        <div class="metric"><span>Monto total de contratos</span><strong>{_formatear_monto(totales['contratos'])}</strong></div>
        <div class="metric"><span>Monto ejecutado</span><strong>{_formatear_monto(totales['ejecutado'])}</strong></div>
        <div class="metric"><span>Total desembolsado</span><strong>{_formatear_monto(totales['desembolsado'])}</strong></div>
        <div class="metric"><span>Saldo por cobrar</span><strong>{_formatear_monto(totales['por_cobrar'])}</strong></div>
        <div class="metric"><span>Flujo de caja</span><strong>{_formatear_monto(totales['flujo'])}</strong></div>
    </section>
    <p class="management-summary">Las obras activas registran una ejecución acumulada equivalente al {porcentaje_ejecutado:.2f}% del monto contratado y desembolsos por el {porcentaje_desembolsado:.2f}%. El saldo consolidado pendiente por cobrar es de {_formatear_monto(totales['por_cobrar'])}.</p>
    <h2 class="section-title">Detalle gerencial y financiero por obra</h2>
    {''.join(fichas) or '<div class="empty">No hay obras en curso para incluir en este reporte.</div>'}
    <footer class="footer">Fuente: tablero de control de obras de Inversora Macroandes. Los montos corresponden a los valores registrados para cada proyecto activo.</footer>
</body>
</html>
"""

def generar_dashboard():
    datos_obras = obtener_datos_obras()
    datos_json = json.dumps(datos_obras, ensure_ascii=False)
    transacciones = obtener_datos_transacciones()
    transacciones_json = json.dumps(transacciones, ensure_ascii=False)
    ruta_base_archivos = ""

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inversora Macroandes </title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        :root {{ font-family: 'Inter', sans-serif; color: #323338; background: #f7f8fa; font-synthesis: none; }}
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; min-height: 100vh; background: #f7f8fa; color: #323338; }}
        button, input, select {{ font: inherit; }}
        .app-layout {{ min-height: 100vh; display: grid; grid-template-columns: 248px minmax(0, 1fr); }}
        .sidebar {{ position: sticky; top: 0; height: 100vh; display: flex; flex-direction: column; padding: 22px 14px 16px; background: #fff; border-right: 1px solid #e6e9ef; }}
        .brand {{ display: flex; align-items: center; gap: 10px; padding: 0 9px 28px; color: #323338; }}
        .brand-logo {{ width: 40px; height: 52px; flex: 0 0 auto; object-fit: contain; filter: brightness(0) saturate(100%) invert(27%) sepia(46%) saturate(740%) hue-rotate(111deg) brightness(94%) contrast(91%); }}
        .brand-name {{ font-size: 15px; font-weight: 750; letter-spacing: -.4px; }}
        .brand-caption {{ margin-top: 2px; color: #9699a6; font-size: 10px; }}
        .workspace-label {{ padding: 0 10px 8px; color: #9699a6; font-size: 10px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
        .nav-item {{ min-height: 39px; display: flex; align-items: center; gap: 11px; padding: 0 11px; border-radius: 6px; color: #676879; text-decoration: none; font-size: 12px; }}
        .nav-item.active {{ color: #4b4bd8; background: #f0f0ff; font-weight: 650; }}
        .nav-item i {{ width: 16px; text-align: center; }}
        .sidebar-footer {{ margin-top: auto; padding: 13px 10px 0; border-top: 1px solid #eceef2; color: #9699a6; font-size: 10px; line-height: 1.6; }}
        .main-shell {{ min-width: 0; }}
        .topbar {{ height: 61px; display: flex; align-items: center; justify-content: space-between; padding: 0 32px; border-bottom: 1px solid #e6e9ef; background: #fff; }}
        .breadcrumbs {{ color: #9699a6; font-size: 11px; }}
        .breadcrumbs strong {{ color: #454650; font-weight: 600; }}
        .topbar-right {{ display: flex; align-items: center; gap: 16px; color: #676879; font-size: 11px; }}
        .avatar {{ width: 29px; height: 29px; display: grid; place-items: center; border-radius: 50%; color: #514fd4; background: #edecff; font-size: 10px; font-weight: 700; }}
        .content {{ max-width: 1500px; margin: 0 auto; padding: 28px 32px 44px; }}
        .page-heading {{ display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; margin-bottom: 22px; }}
        .report-button {{ min-height: 36px; display: inline-flex; align-items: center; gap: 8px; padding: 0 12px; border: 1px solid #4b4bd8; border-radius: 5px; color: #fff; background: #4b4bd8; cursor: pointer; font-size: 11px; font-weight: 650; text-decoration: none; white-space: nowrap; }}
        .report-button:hover {{ border-color: #3c3cb6; background: #3c3cb6; }}
        .eyebrow {{ margin: 0 0 7px; color: #9699a6; font-size: 10px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
        h1 {{ margin: 0; color: #323338; font-size: 26px; letter-spacing: -.8px; }}
        .subtitle {{ margin: 7px 0 0; color: #676879; font-size: 12px; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-bottom: 20px; }}
        .kpi-card {{ min-width: 0; padding: 16px 17px; border: 1px solid #e6e9ef; border-radius: 8px; background: #fff; box-shadow: 0 1px 3px rgba(20,20,40,.035); transition: border-color .2s, box-shadow .2s; }}
        .kpi-card.obra-culminada {{ border-style: dashed; background: #fafbfc; }}
        .kpi-label {{ display: flex; align-items: center; gap: 8px; color: #676879; font-size: 11px; font-weight: 550; }}
        .kpi-icon {{ width: 25px; height: 25px; display: grid; place-items: center; border-radius: 6px; color: #6161ff; background: #f0f0ff; }}
        .kpi-value {{ margin-top: 12px; color: #323338; font-size: 22px; font-weight: 700; letter-spacing: -.4px; overflow-wrap: anywhere; }}
        .kpi-note {{ margin-top: 4px; color: #9699a6; font-size: 10px; }}
        .badge-obra-estado {{ display: none; }}
        .badge-obra-estado.visible {{ display: inline-flex; margin-top: 8px; padding: 3px 7px; border-radius: 9999px; color: #166534; background: #dcfce7; font-size: 9px; font-weight: 700; letter-spacing: .06em; }}
        .board-card, .detail-card {{ overflow: hidden; border: 1px solid #e6e9ef; border-radius: 8px; background: #fff; box-shadow: 0 1px 3px rgba(20,20,40,.035); }}
        .board-head {{ display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 17px 19px 13px; }}
        .board-title {{ display: flex; align-items: center; gap: 9px; margin: 0; font-size: 15px; font-weight: 700; }}
        .board-count {{ padding: 3px 7px; border-radius: 10px; color: #676879; background: #f0f1f4; font-size: 10px; font-weight: 600; }}
        .board-description {{ margin: 4px 0 0; color: #9699a6; font-size: 10px; }}
        .board-controls {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 0 19px 14px; }}
        .view-tabs {{ display: flex; align-items: center; gap: 3px; }}
        .view-tab {{ padding: 7px 10px; border: 0; border-radius: 5px; color: #676879; background: transparent; cursor: pointer; font-size: 10px; }}
        .view-tab.active {{ color: #4b4bd8; background: #f0f0ff; font-weight: 650; }}
        .board-search {{ width: min(250px, 42vw); height: 32px; padding: 0 10px; border: 1px solid #d5d7df; border-radius: 5px; outline: none; font-size: 10px; }}
        .board-search:focus {{ border-color: #8585ff; box-shadow: 0 0 0 2px #f0f0ff; }}
        .table-scroll {{ overflow-x: auto; }}
        .project-table {{ width: 100%; min-width: 1040px; border-collapse: collapse; text-align: left; }}
        .transaction-table {{ width: 100%; min-width: 850px; border-collapse: collapse; text-align: left; }}
        .project-table th {{ height: 36px; padding: 0 12px; border-top: 1px solid #eceef2; border-bottom: 1px solid #eceef2; color: #9699a6; background: #fbfbfc; font-size: 9px; font-weight: 650; letter-spacing: .04em; text-transform: uppercase; white-space: nowrap; }}
        .project-table td {{ height: 53px; padding: 8px 12px; border-bottom: 1px solid #f0f1f4; color: #454650; font-size: 10px; white-space: nowrap; }}
        .transaction-table th {{ height: 36px; padding: 0 12px; border-top: 1px solid #eceef2; border-bottom: 1px solid #eceef2; color: #9699a6; background: #fbfbfc; font-size: 9px; font-weight: 650; letter-spacing: .04em; text-transform: uppercase; white-space: nowrap; }}
        .transaction-table td {{ padding: 10px 12px; border-bottom: 1px solid #f0f1f4; color: #454650; font-size: 10px; }}
        .transaction-table tbody tr:hover {{ background: #fbfbff; }}
        .transaction-table tbody tr:last-child td {{ border-bottom: 0; }}
        .transaction-total {{ font-weight: 700; white-space: nowrap; }}
        .transaction-total.positive {{ color: #147d52; }}
        .transaction-total.negative {{ color: #c2414b; }}
        .transaction-total.neutral {{ color: #676879; }}
        .transactions-card {{ margin-top: 18px; }}
        .transactions-note {{ padding: 0 19px 12px; }}
        .project-table tbody tr {{ cursor: pointer; transition: background .15s; }}
        .project-table tbody tr:hover {{ background: #f7f8ff; }}
        .project-table tbody tr.selected {{ background: #f0f0ff; box-shadow: inset 3px 0 #6161ff; }}
        .project-table tbody tr:last-child td {{ border-bottom: 0; }}
        .project-name {{ max-width: 290px; overflow: hidden; color: #323338; font-weight: 600; text-overflow: ellipsis; }}
        .project-subname {{ margin-top: 3px; color: #9699a6; font-size: 9px; }}
        .status-pill {{ display: inline-flex; align-items: center; gap: 5px; min-height: 22px; padding: 0 8px; border-radius: 4px; color: #147d52; background: #dff5e9; font-size: 9px; font-weight: 650; }}
        .status-pill.completed {{ color: #676879; background: #eceef2; }}
        .status-pill::before {{ width: 5px; height: 5px; border-radius: 50%; background: currentColor; content: ''; }}
        .table-progress {{ width: 105px; height: 6px; overflow: hidden; border-radius: 5px; background: #eceef2; }}
        .table-progress span {{ height: 100%; display: block; border-radius: inherit; background: #6161ff; }}
        .progress-value {{ margin-left: 7px; color: #676879; font-size: 9px; }}
        .empty-row {{ padding: 24px !important; color: #9699a6 !important; text-align: center; }}
        .files-button {{ padding: 6px 9px; border: 1px solid #e1e3e9; border-radius: 5px; color: #4b4bd8; background: #fff; cursor: pointer; font-size: 10px; font-weight: 600; white-space: nowrap; }}
        .files-button:hover {{ border-color: #b7b7ff; background: #f7f7ff; }}
        .files-empty {{ color: #9699a6; font-size: 10px; }}
        .files-dialog {{ position: fixed; inset: 0 0 0 auto; width: min(560px, 100%); height: 100vh; height: 100dvh; max-height: 100vh; max-height: 100dvh; margin: 0; padding: 0 20px 28px; overflow-y: auto; border: 0; border-left: 1px solid #e6e9ef; border-radius: 0; color: #323338; background: #fff; box-shadow: -16px 0 45px rgba(28,43,33,.12); }}
        .files-dialog::backdrop {{ background: rgba(26, 28, 38, .42); }}
        .files-dialog-header {{ position: sticky; top: 0; z-index: 1; display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin: 0 -20px; padding: 24px 20px 18px; border-bottom: 1px solid #eceef2; background: #fff; }}
        .files-dialog-header p {{ margin: 0 0 8px; color: #4b4bd8; font-size: 10px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }}
        .files-dialog-header h2 {{ margin: 0; font-size: 18px; }}
        .files-dialog-header small {{ display: block; margin-top: 6px; color: #9699a6; font-size: 10px; }}
        .files-dialog-close {{ width: 32px; height: 32px; flex: 0 0 32px; border: 1px solid #e1e3e9; border-radius: 5px; color: #676879; background: #fff; cursor: pointer; }}
        .files-section-title {{ display: flex; align-items: center; justify-content: space-between; margin: 22px 0 11px; font-size: 12px; font-weight: 700; }}
        .files-section-title small {{ color: #9699a6; font-size: 10px; font-weight: 400; }}
        .files-document-list {{ display: grid; gap: 8px; }}
        .files-document {{ display: flex; align-items: center; gap: 11px; min-width: 0; padding: 10px; border: 1px solid #e6e9ef; border-radius: 5px; color: #454650; text-decoration: none; }}
        .files-document:hover {{ border-color: #b7d2c0; background: #fbfdfb; }}
        .files-document-icon {{ width: 30px; height: 34px; flex: 0 0 30px; display: grid; place-items: center; border-radius: 4px; color: #a64d4d; background: #faeeee; font-size: 9px; font-weight: 800; text-transform: uppercase; }}
        .files-document-name {{ min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 10px; }}
        .files-document-open {{ margin-left: auto; color: #87938a; font-size: 10px; }}
        .files-photo-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 7px; margin-top: 9px; }}
        .files-photo {{ aspect-ratio: 1.25; overflow: hidden; border: 1px solid #e6e9ef; border-radius: 4px; background: #f4f6f4; }}
        .files-photo img {{ width: 100%; height: 100%; display: block; object-fit: cover; transition: transform .2s ease; }}
        .files-photo:hover img {{ transform: scale(1.04); }}
        .files-empty-preview {{ padding: 18px; border: 1px dashed #dfe6df; border-radius: 5px; color: #849087; text-align: center; font-size: 11px; }}
        @media (max-width: 420px) {{ .files-photo-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
        .detail-card {{ margin-top: 18px; padding: 18px 20px 10px; }}
        .detail-heading {{ display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 8px; }}
        .detail-heading h2 {{ margin: 0; font-size: 14px; font-weight: 700; }}
        .detail-heading p {{ margin: 4px 0 0; color: #9699a6; font-size: 10px; }}
        .detail-caption {{ padding: 4px 8px; border-radius: 4px; color: #676879; background: #f0f1f4; font-size: 9px; }}
        #waterfallChart {{ width: 100%; height: 340px; }}
        @media (max-width: 1020px) {{ .app-layout {{ grid-template-columns: 205px minmax(0, 1fr); }} .sidebar {{ padding-right: 10px; padding-left: 10px; }} .content {{ padding-right: 20px; padding-left: 20px; }} }}
        @media (max-width: 760px) {{ .app-layout {{ display: block; }} .sidebar {{ position: static; height: auto; padding: 12px 15px; border-right: 0; border-bottom: 1px solid #e6e9ef; }} .brand {{ padding: 0; }} .workspace-label, .sidebar nav, .sidebar-footer {{ display: none; }} .topbar {{ height: 48px; padding: 0 16px; }} .topbar-right span {{ display: none; }} .content {{ padding: 20px 14px 32px; }} .page-heading {{ align-items: flex-start; flex-direction: column; }} .kpi-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }} .kpi-card {{ padding: 12px; }} .kpi-value {{ font-size: 18px; }} .board-head, .board-controls {{ align-items: flex-start; flex-direction: column; }} .board-controls {{ gap: 10px; }} .board-search {{ width: 100%; }} }}
        @media (max-width: 420px) {{ .kpi-grid {{ grid-template-columns: 1fr; }} .view-tabs {{ width: 100%; }} .view-tab {{ flex: 1; padding-right: 5px; padding-left: 5px; }} }}
    </style>
</head>
<body>
    <div class="app-layout">
        <aside class="sidebar" aria-label="Navegación principal">
            <div class="brand"><img class="brand-logo" src="src/assets/Logo.svg" alt="Logo de Inversora Macroandes"><div><div class="brand-name">Inversora Macroandes</div><div class="brand-caption">Gestión de proyectos</div></div></div>
            <div class="workspace-label">Espacio de trabajo</div>
            <nav aria-label="Secciones del tablero">
                <a class="nav-item" href="#resumen"><i class="fa-solid fa-house"></i> Inicio</a>
                <a class="nav-item active" href="#tablero"><i class="fa-solid fa-table-cells-large"></i> Tablero de obras</a>
                <a class="nav-item" href="#conciliacion"><i class="fa-solid fa-chart-column"></i> Finanzas</a>
                <a class="nav-item" href="#registro-transacciones"><i class="fa-solid fa-money-bill-transfer"></i> Registro de Transacciones</a>
            </nav>
            <div class="sidebar-footer">Inversora Macroandes<br>Panel interno de seguimiento</div>
        </aside>
        <div class="main-shell">
            <header class="topbar">
                <div class="breadcrumbs">Espacio de trabajo <span aria-hidden="true">/</span> <strong>Tablero de obras</strong></div>
                <div class="topbar-right"><span><i class="fa-regular fa-circle-question"></i> Centro de ayuda</span><div class="avatar" aria-label="Inversora Macroandes">IM</div></div>
            </header>
            <main class="content" id="resumen">
                <section class="page-heading">
                    <div><p class="eyebrow">Inversora Macroandes · Portafolio</p><h1>Control de obras</h1><p class="subtitle">Seguimiento financiero y estado de los proyectos.</p></div>
                    <a class="report-button" id="generate-report" href="reporte_obras.html" target="_blank" rel="noopener"><i class="fa-solid fa-file-pdf" aria-hidden="true"></i> Generar reporte PDF</a>
                </section>
                <section class="kpi-grid" aria-label="Indicadores financieros de los proyectos filtrados">
                    <article class="kpi-card"><div class="kpi-label"><span class="kpi-icon"><i class="fa-solid fa-file-invoice-dollar"></i></span>Monto de contrato</div><div id="badge-obra-estado" class="badge-obra-estado">OBRA CULMINADA</div><div class="kpi-value" id="kpi-monto">$0,00</div><div class="kpi-note">Valor contractual acordado</div></article>
                    <article class="kpi-card"><div class="kpi-label"><span class="kpi-icon"><i class="fa-solid fa-helmet-safety"></i></span>Ejecutado</div><div class="kpi-value" id="kpi-estimado">$0,00</div><div class="kpi-note">Monto de avance financiero ejecutado</div></article>
                    <article class="kpi-card"><div class="kpi-label"><span class="kpi-icon"><i class="fa-solid fa-money-bill-transfer"></i></span>Desembolsado</div><div class="kpi-value" id="kpi-cobrado">$0,00</div><div class="kpi-note">Total recaudado efectivamente</div></article>
                    <article class="kpi-card"><div class="kpi-label"><span class="kpi-icon"><i class="fa-solid fa-arrow-trend-up"></i></span>Flujo de caja</div><div class="kpi-value" id="kpi-flujo-caja">$0,00</div><div class="kpi-note">Desembolsado menos ejecutado</div></article>
                    <article class="kpi-card"><div class="kpi-label"><span class="kpi-icon"><i class="fa-solid fa-hourglass-half"></i></span>Por cobrar</div><div class="kpi-value" id="kpi-por-cobrar">$0,00</div><div class="kpi-note">Saldo pendiente por cobrar</div></article>
                    <article class="kpi-card"><div class="kpi-label"><span class="kpi-icon"><i class="fa-solid fa-chart-pie"></i></span>Avance financiero</div><div class="kpi-value" id="kpi-avance-pct">0,00%</div><div class="kpi-note">Porcentaje cobrado sobre el contrato</div></article>
                </section>
                <section class="board-card" id="tablero" aria-label="Tablero de proyectos">
                    <div class="board-head"><div><h2 class="board-title">Proyectos <span class="board-count" id="project-count">0</span></h2><p class="board-description">Selecciona una fila para consultar sus indicadores financieros.</p></div></div>
                    <div class="board-controls">
                        <div class="view-tabs" role="tablist" aria-label="Filtrar proyectos">
                            <button class="view-tab active" type="button" data-view="TODAS">Todas las obras</button>
                            <button class="view-tab" type="button" data-view="ACTIVA">Activas</button>
                            <button class="view-tab" type="button" data-view="CULMINADA">Culminadas</button>
                        </div>
                        <input class="board-search" id="project-search" type="search" placeholder="Buscar proyecto..." aria-label="Buscar proyecto">
                    </div>
                    <div class="table-scroll">
                        <table class="project-table">
                            <thead><tr><th>Proyecto</th><th>Estado</th><th>Monto contrato</th><th>Ejecutado</th><th>Desembolsado</th><th>Por cobrar</th><th>Avance financiero</th><th>Flujo de caja</th><th>Archivos</th></tr></thead>
                            <tbody id="project-rows"></tbody>
                        </table>
                    </div>
                </section>
                <section class="detail-card" id="conciliacion" aria-label="Conciliación financiera">
                    <div class="detail-heading"><div><h2>Conciliación de flujo de caja</h2><p id="chart-project-name">Detalle del proyecto seleccionado</p></div><span class="detail-caption">USD</span></div>
                    <div id="waterfallChart"></div>
                </section>
                <section id="registro-transacciones" class="board-card transactions-card" aria-label="Registro de transacciones por obra">
                    <div class="board-head"><div><h2 class="board-title">Registro de Transacciones <span class="board-count" id="transaction-count">0</span></h2><p class="board-description">Entradas y salidas agrupadas por obra, con su saldo neto.</p></div></div>
                    <div class="board-controls">
                        <div class="view-tabs" role="group" aria-label="Filtrar transacciones por condición">
                            <button class="view-tab active" type="button" data-transaction-view="TODAS">Todas las obras</button>
                            <button class="view-tab" type="button" data-transaction-view="ACTIVA">Activas</button>
                            <button class="view-tab" type="button" data-transaction-view="CULMINADA">Culminadas</button>
                        </div>
                        <input class="board-search" id="transaction-search" type="search" placeholder="Buscar obra..." aria-label="Buscar obra en transacciones">
                    </div>
                    <p class="board-description transactions-note">Total neto = entradas menos salidas</p>
                    <div class="table-scroll">
                        <table class="transaction-table">
                            <thead><tr><th>Obra</th><th>Entradas</th><th>Salidas</th><th>Total neto</th><th>Facturas de compra</th></tr></thead>
                            <tbody id="transaction-rows"></tbody>
                        </table>
                    </div>
                </section>
                <dialog class="files-dialog" id="files-dialog" aria-labelledby="files-dialog-title">
                    <div class="files-dialog-header"><div><p id="files-dialog-type">Documentos y fotos</p><h2 id="files-dialog-title">Archivos del proyecto</h2><small id="files-dialog-count"></small></div><button class="files-dialog-close" id="files-dialog-close" type="button" aria-label="Cerrar"><i class="fa-solid fa-xmark"></i></button></div>
                    <div id="files-preview"></div>
                </dialog>
            </main>
        </div>
    </div>
    <script>
        const datosProyectos = {datos_json};
        const datosTransacciones = {transacciones_json};
        const estadoSelector = {{ vista: 'TODAS' }};
        const busquedaObras = document.getElementById('project-search');
        const filasObras = document.getElementById('project-rows');
        const busquedaTransacciones = document.getElementById('transaction-search');
        const filasTransacciones = document.getElementById('transaction-rows');
        const estadoTransacciones = {{ vista: 'TODAS' }};
        const dialogArchivos = document.getElementById('files-dialog');
        const rutaBaseArchivos = "{ruta_base_archivos}";
        let proyectoSeleccionado = null;
        let mostrarProyectoSeleccionado = false;

        function formatearUSD(valor) {{
            return new Intl.NumberFormat('en-US', {{ style: 'currency', currency: 'USD', minimumFractionDigits: 2 }}).format(valor);
        }}

        function formatearFecha(fecha) {{
            if (!fecha) return '';
            const [anio, mes, dia] = fecha.split('-');
            return `${{dia}}/${{mes}}/${{anio}}`;
        }}

        function escaparHTML(valor) {{
            return String(valor).replace(/[&<>"']/g, (caracter) => ({{
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
            }})[caracter]);
        }}

        function renderizarTransacciones() {{
            const consulta = busquedaTransacciones.value.trim().toLocaleLowerCase('es');
            const obras = datosTransacciones.filter((datos) => {{
                const texto = datos.obra.toLocaleLowerCase('es');
                const coincideEstado = estadoTransacciones.vista === 'TODAS'
                    || datos.estado === estadoTransacciones.vista;
                return coincideEstado && (!consulta || texto.includes(consulta));
            }});

            document.getElementById('transaction-count').textContent = obras.length;
            filasTransacciones.innerHTML = obras.map((datos) => {{
                const claseTotal = datos.total > 0
                    ? 'positive'
                    : datos.total < 0
                        ? 'negative'
                        : 'neutral';

                return `<tr>
                    <td><div class="project-name">${{escaparHTML(datos.obra)}}</div></td>
                    <td>${{formatearUSD(datos.total_entradas)}}</td>
                    <td>${{formatearUSD(datos.total_salidas)}}</td>
                    <td class="transaction-total ${{claseTotal}}">${{formatearUSD(datos.total)}}</td>
                    <td>${{datos.facturas.length
                        ? `<button class="files-button" type="button" data-invoices-project="${{escaparHTML(datos.obra)}}" aria-label="Ver facturas de compra de ${{escaparHTML(datos.obra)}}"><i class="fa-solid fa-paperclip" aria-hidden="true"></i> Ver ${{datos.facturas.length}}</button>`
                        : '<span class="files-empty">Sin facturas</span>'}}</td>
                </tr>`;
            }}).join('') || '<tr><td class="empty-row" colspan="5">No hay transacciones para mostrar.</td></tr>';
            filasTransacciones.querySelectorAll('[data-invoices-project]').forEach((boton) => {{
                boton.addEventListener('click', () => {{
                    const obra = boton.dataset.invoicesProject;
                    const datos = datosTransacciones.find((fila) => fila.obra === obra);
                    mostrarArchivos(obra, datos.facturas, 'Facturas de compra');
                }});
            }});
        }}

        function mostrarArchivos(obra, archivos, tipo) {{
            document.getElementById('files-dialog-type').textContent = tipo;
            document.getElementById('files-dialog-title').textContent = `${{tipo}} · ${{obra}}`;
            document.getElementById('files-dialog-count').textContent = `${{archivos.length}} archivos vinculados a esta obra`;
            const imagenes = archivos.filter((archivo) => archivo.tipo === 'imagen');
            const documentos = archivos.filter((archivo) => archivo.tipo !== 'imagen');
            const vistaDocumentos = documentos.map((archivo) => {{
                const extension = archivo.nombre.split('.').pop() || 'archivo';
                return `<a class="files-document" href="${{escaparHTML(rutaBaseArchivos + archivo.ruta)}}" target="_blank" rel="noopener noreferrer">
                    <span class="files-document-icon">${{escaparHTML(extension)}}</span>
                    <span class="files-document-name">${{escaparHTML(archivo.nombre)}}</span>
                    <span class="files-document-open" aria-hidden="true"><i class="fa-solid fa-arrow-up-right-from-square"></i></span>
                </a>`;
            }}).join('');
            const vistaImagenes = imagenes.map((archivo) => {{
                const url = escaparHTML(rutaBaseArchivos + archivo.ruta);
                return `<a class="files-photo" href="${{url}}" target="_blank" rel="noopener noreferrer" aria-label="Abrir foto: ${{escaparHTML(archivo.nombre)}}">
                    <img src="${{url}}" alt="${{escaparHTML(archivo.nombre)}}" loading="lazy">
                </a>`;
            }}).join('');
            document.getElementById('files-preview').innerHTML = archivos.length
                ? `${{documentos.length ? `<section aria-label="Documentos"><div class="files-section-title">Documentos <small>${{documentos.length}} archivos</small></div><div class="files-document-list">${{vistaDocumentos}}</div></section>` : ''}}
                    ${{imagenes.length ? `<section aria-label="Fotos"><div class="files-section-title">Fotos <small>${{imagenes.length}} imágenes</small></div><div class="files-photo-grid">${{vistaImagenes}}</div></section>` : ''}}`
                : '<div class="files-empty-preview">No hay archivos vinculados a esta obra.</div>';
            dialogArchivos.showModal();
        }}

        function obtenerEtiquetaObra(obra, data) {{
            if (data && data.estado === 'CULMINADA') {{
                return `${{obra}} - CULMINADA ${{formatearFecha(data.fecha_cierre)}}`;
            }}
            return obra;
        }}

        function renderizarTablero() {{
            const consulta = busquedaObras.value.trim().toLocaleLowerCase('es');
            const proyectos = Object.entries(datosProyectos).filter(([obra, data]) => {{
                if (obra === 'CONSOLIDADO OBRAS') return false;
                const coincideVista = estadoSelector.vista === 'TODAS' || data.estado === estadoSelector.vista;
                const textoProyecto = `${{obra}} ${{data.estado_fuente}}`.toLocaleLowerCase('es');
                const coincideBusqueda = !consulta || textoProyecto.includes(consulta);
                return coincideVista && coincideBusqueda;
            }});
            if (!proyectos.some(([obra]) => obra === proyectoSeleccionado)) {{
                proyectoSeleccionado = proyectos[0]?.[0] || null;
            }}

            const totales = proyectos.reduce((sum, [, data]) => ({{
                monto: sum.monto + (Number(data.monto_contrato) || 0),
                ejecutado: sum.ejecutado + (Number(data.estimado_ejecutado) || 0),
                desembolsado: sum.desembolsado + (Number(data.cobrado_desembolsado) || 0),
                flujo: sum.flujo + (Number(data.flujo_caja) || 0),
                porCobrar: sum.porCobrar + (Number(data.por_cobrar) || 0),
            }}), {{ monto: 0, ejecutado: 0, desembolsado: 0, flujo: 0, porCobrar: 0 }});
            const datosObraSeleccionada = mostrarProyectoSeleccionado
                ? proyectos.find(([obra]) => obra === proyectoSeleccionado)?.[1]
                : null;
            const indicadores = datosObraSeleccionada || totales;
            const avanceFinanciero = datosObraSeleccionada
                ? Number(datosObraSeleccionada.avance_financiero_pct) || 0
                : totales.monto > 0
                    ? (totales.desembolsado / totales.monto) * 100
                : 0;
            document.getElementById('kpi-monto').textContent = formatearUSD(indicadores.monto_contrato ?? indicadores.monto);
            document.getElementById('kpi-estimado').textContent = formatearUSD(indicadores.estimado_ejecutado ?? indicadores.ejecutado);
            document.getElementById('kpi-cobrado').textContent = formatearUSD(indicadores.cobrado_desembolsado ?? indicadores.desembolsado);
            document.getElementById('kpi-flujo-caja').textContent = formatearUSD(indicadores.flujo_caja ?? indicadores.flujo);
            document.getElementById('kpi-por-cobrar').textContent = formatearUSD(indicadores.por_cobrar ?? indicadores.porCobrar);
            document.getElementById('kpi-avance-pct').textContent = `${{avanceFinanciero.toFixed(2)}}%`;

            const obrasCulminadas = datosObraSeleccionada
                ? datosObraSeleccionada.estado === 'CULMINADA'
                : proyectos.length > 0 && proyectos.every(([, data]) => data.estado === 'CULMINADA');
            document.querySelectorAll('.kpi-card').forEach((card) => {{
                card.classList.toggle('obra-culminada', obrasCulminadas);
            }});
            const badge = document.getElementById('badge-obra-estado');
            badge.classList.toggle('visible', obrasCulminadas);
            badge.textContent = datosObraSeleccionada ? 'OBRA CULMINADA' : 'OBRAS CULMINADAS';

            document.getElementById('project-count').textContent = proyectos.length;
            filasObras.innerHTML = proyectos.map(([obra, data]) => {{
                const avance = Math.max(0, Math.min(100, Number(data.avance_financiero_pct) || 0));
                const culminada = data.estado === 'CULMINADA';
                const selected = proyectoSeleccionado === obra;
                const detalle = culminada && data.fecha_cierre
                    ? `Culminada el ${{formatearFecha(data.fecha_cierre)}}`
                    : 'Proyecto de inversión';
                return `<tr class="${{selected ? 'selected' : ''}}" data-project="${{escaparHTML(obra)}}">
                    <td><div class="project-name">${{escaparHTML(obra)}}</div><div class="project-subname">${{detalle}}</div></td>
                    <td><span class="status-pill ${{culminada ? 'completed' : ''}}">${{escaparHTML(data.estado_fuente)}}</span></td>
                    <td>${{formatearUSD(data.monto_contrato)}}</td>
                    <td>${{formatearUSD(data.estimado_ejecutado)}}</td>
                    <td>${{formatearUSD(data.cobrado_desembolsado)}}</td>
                    <td>${{formatearUSD(data.por_cobrar)}}</td>
                    <td><div style="display:flex;align-items:center"><div class="table-progress"><span style="width:${{avance}}%"></span></div><span class="progress-value">${{avance.toFixed(1)}}%</span></div></td>
                    <td>${{formatearUSD(data.flujo_caja)}}</td>
                    <td>${{data.archivos.length
                        ? `<button class="files-button" type="button" data-files-project="${{escaparHTML(obra)}}" aria-label="Ver archivos de ${{escaparHTML(obra)}}"><i class="fa-solid fa-paperclip" aria-hidden="true"></i> Ver ${{data.archivos.length}}</button>`
                        : '<span class="files-empty">Sin archivos</span>'}}</td>
                </tr>`;
            }}).join('') || '<tr><td class="empty-row" colspan="9">No hay proyectos que coincidan con esta vista.</td></tr>';

            filasObras.querySelectorAll('[data-project]').forEach((fila) => {{
                fila.addEventListener('click', () => {{
                    actualizarDashboard(fila.dataset.project);
                }});
            }});
            filasObras.querySelectorAll('[data-files-project]').forEach((boton) => {{
                boton.addEventListener('click', (evento) => {{
                    evento.stopPropagation();
                    const obra = boton.dataset.filesProject;
                    mostrarArchivos(obra, datosProyectos[obra].archivos, 'Documentos y fotos');
                }});
            }});

            const dataSeleccionada = datosProyectos[proyectoSeleccionado];
            if (dataSeleccionada) {{
                document.getElementById('chart-project-name').textContent = obtenerEtiquetaObra(proyectoSeleccionado, dataSeleccionada);
                renderizarWaterfall(dataSeleccionada.cobrado_desembolsado, dataSeleccionada.egresos_reales, dataSeleccionada.flujo_caja);
            }} else {{
                document.getElementById('chart-project-name').textContent = 'No hay proyectos en esta vista';
                Plotly.purge('waterfallChart');
            }}
        }}

        function actualizarDashboard(obra) {{
            if (!datosProyectos[obra] || obra === 'CONSOLIDADO OBRAS') return;
            proyectoSeleccionado = obra;
            mostrarProyectoSeleccionado = true;
            renderizarTablero();
        }}

        function renderizarWaterfall(cobrado, egresos, flujoCaja) {{
            const trace = {{
                type: "waterfall",
                orientation: "v",
                measure: ["relative", "relative", "total"],
                x: ["Desembolsado", "Ejecutado", "Flujo de Caja"],
                y: [cobrado, -egresos, flujoCaja],
                connector: {{ line: {{ color: "#cbd5e1", width: 1, dash: "dot" }} }},
                decreasing: {{ marker: {{ color: "#f43f5e" }} }},
                increasing: {{ marker: {{ color: "#10b981" }} }},
                totals: {{ marker: {{ color: "#3b82f6" }} }},
                textposition: "outside",
                text: [formatearUSD(cobrado), formatearUSD(-egresos), formatearUSD(flujoCaja)],
                hoverinfo: "x+text"
            }};

            const layout = {{
                paper_bgcolor: '#ffffff',
                plot_bgcolor: '#ffffff',
                font: {{ color: '#676879', family: 'Inter' }},
                xaxis: {{ tickfont: {{ color: '#676879', size: 11 }}, linecolor: '#e6e9ef' }},
                yaxis: {{ title: 'Monto (USD)', gridcolor: '#f0f1f4', zerolinecolor: '#c9cbd3' }},
                margin: {{ t: 30, b: 40, l: 60, r: 20 }},
                autosize: true
            }};

            Plotly.newPlot('waterfallChart', [trace], layout, {{ responsive: true, displayModeBar: false }});
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            document.getElementById('files-dialog-close').addEventListener('click', () => dialogArchivos.close());
            document.querySelectorAll('[data-view]').forEach((boton) => {{
                boton.addEventListener('click', () => {{
                    estadoSelector.vista = boton.dataset.view;
                    mostrarProyectoSeleccionado = false;
                    document.querySelectorAll('[data-view]').forEach((tab) => tab.classList.toggle('active', tab === boton));
                    renderizarTablero();
                }});
            }});
            busquedaObras.addEventListener('input', () => {{
                mostrarProyectoSeleccionado = false;
                renderizarTablero();
            }});
            busquedaTransacciones.addEventListener('input', renderizarTransacciones);
            document.querySelectorAll('[data-transaction-view]').forEach((boton) => {{
                boton.addEventListener('click', () => {{
                    estadoTransacciones.vista = boton.dataset.transactionView;
                    document.querySelectorAll('[data-transaction-view]').forEach((tab) => {{
                        tab.classList.toggle('active', tab === boton);
                    }});
                    renderizarTransacciones();
                }});
            }});
            renderizarTablero();
            renderizarTransacciones();
        }});
    </script>
</body>
</html>
"""

    # Crear directorio si no existe y guardar
    RUTA_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    RUTA_REPORTE.write_text(_generar_reporte_html(datos_obras), encoding="utf-8")
    with open(RUTA_OUTPUT, "w", encoding="utf-8") as f:
        html_output = html_content.replace(
            'src="src/assets/Logo.svg"', 'src="../src/assets/Logo.svg"'
        ).replace(
            'const rutaBaseArchivos = "";',
            'const rutaBaseArchivos = "../";',
        ).replace(
            'href="reporte_obras.html"',
            'href="../reporte_obras.html"',
        )
        f.write(html_output)

    with open(RUTA_INDEX, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(
        f"¡ÉXITO! Dashboards generados correctamente en: "
        f"{RUTA_OUTPUT}, {RUTA_INDEX} y {RUTA_REPORTE}"
    )

if __name__ == "__main__":
    generar_dashboard()