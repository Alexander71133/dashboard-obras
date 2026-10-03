"""
Módulo de Procesamiento de Datos Financieros
Extrae, limpia y mapea la información del libro Excel hacia la estructura del Dashboard.
"""
from pathlib import Path
import unicodedata
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_EXCEL = BASE_DIR / "Datos" / "Gestion Proyecto Fatima.xlsx"
RUTA_CONTROL_OBRAS = (
    Path.home()
    / "Dropbox"
    / "Macroandes"
    / "Inversora Macroandes"
    / "Control Obras.xlsx"
)


def _normalizar_encabezado(valor):
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    return " ".join(texto.strip().lower().split())


def _buscar_columna(columnas, aliases):
    aliases_normalizados = {_normalizar_encabezado(alias) for alias in aliases}
    for columna in columnas:
        if _normalizar_encabezado(columna) in aliases_normalizados:
            return columna
    return None


def _numero(valor):
    if valor is None or pd.isna(valor):
        return 0.0
    return float(valor)

def obtener_datos_obras():
    """
    Lee el libro fuente de Dropbox cuando está disponible; en caso contrario,
    usa la copia de Resumen Financiero guardada en el repositorio.
    """
    usar_control_obras = RUTA_CONTROL_OBRAS.is_file()
    ruta_excel = RUTA_CONTROL_OBRAS if usar_control_obras else RUTA_EXCEL
    hoja = "Panel_de_Control" if usar_control_obras else "Resumen Financiero"

    if not ruta_excel.is_file():
        raise FileNotFoundError(f"No se encontró el archivo Excel en: {ruta_excel}")

    print(f"Fuente de datos utilizada: {ruta_excel}")
    df = pd.read_excel(ruta_excel, sheet_name=hoja)

    if usar_control_obras:
        columnas = {
            "obra": _buscar_columna(df.columns, ("Nombre de la Obra / Proyecto",)),
            "monto_contrato": _buscar_columna(df.columns, ("Monto del Contrato",)),
            "estimado": _buscar_columna(df.columns, ("Total Ejecutado",)),
            "cobrado": _buscar_columna(df.columns, ("Total Ingresos",)),
            "flujo_caja": _buscar_columna(df.columns, ("Utilidad Actual",)),
            "egresos": None,
            "por_cobrar": None,
            "avance_cobrado": None,
        }
    else:
        print(
            "AVISO: no se encontró Control Obras.xlsx en Dropbox; "
            "se usarán los datos guardados en el Excel del repositorio."
        )
        columnas = {
            "obra": _buscar_columna(df.columns, ("Obra",)),
            "monto_contrato": _buscar_columna(df.columns, ("Monto Contrato",)),
            "estimado": _buscar_columna(df.columns, ("Estimado Acumulado/Ejecutado", "Ejecutado")),
            "cobrado": _buscar_columna(df.columns, ("Cobrado Acumulado/Desembolsado", "Desembolsado")),
            "flujo_caja": _buscar_columna(df.columns, ("Flujo de Caja",)),
            "egresos": _buscar_columna(df.columns, ("Egresos Reales", "Egresos")),
            "por_cobrar": _buscar_columna(df.columns, ("Por cobrar",)),
            "avance_cobrado": _buscar_columna(df.columns, ("% Avance Cobrado",)),
        }

    columnas_requeridas = ("obra", "monto_contrato", "estimado", "cobrado")
    if not usar_control_obras:
        columnas_requeridas += ("por_cobrar",)
    faltantes = [nombre for nombre in columnas_requeridas if columnas[nombre] is None]
    if faltantes:
        raise ValueError(f"Faltan encabezados en '{hoja}': {', '.join(faltantes)}")

    proyectos = {}
    nombres_dashboard = {
        "cacute cafe": "CACUTE SUELOS CAFÉ",
        "cacute galpon": "CACUTE SUELOS GALPON",
    }

    for _, row in df.iterrows():
        valor_obra = row.get(columnas["obra"])
        if pd.isna(valor_obra):
            continue
        nombre_obra = str(valor_obra).strip()
        if not nombre_obra:
            continue
        if usar_control_obras:
            nombre_obra = nombres_dashboard.get(
                _normalizar_encabezado(nombre_obra), nombre_obra
            )

        monto_contrato = _numero(row.get(columnas["monto_contrato"]))
        estimado = _numero(row.get(columnas["estimado"]))
        cobrado = _numero(row.get(columnas["cobrado"]))

        if columnas["flujo_caja"]:
            flujo_caja = _numero(row.get(columnas["flujo_caja"]))
        else:
            flujo_caja = cobrado - _numero(row.get(columnas["egresos"]))

        if usar_control_obras:
            egresos = estimado
            por_cobrar = monto_contrato - cobrado
        else:
            por_cobrar = _numero(row.get(columnas["por_cobrar"]))
            if columnas["egresos"]:
                egresos = _numero(row.get(columnas["egresos"]))
            else:
                egresos = cobrado - flujo_caja

        # Cálculo / Extracción del Avance Financiero %
        val_pct = row.get(columnas["avance_cobrado"]) if columnas["avance_cobrado"] else None
        if val_pct is not None and not pd.isna(val_pct):
            avance_financiero_pct = float(val_pct * 100) if float(val_pct) <= 1.0 else float(val_pct)
        else:
            avance_financiero_pct = (cobrado / monto_contrato * 100) if monto_contrato > 0 else 0.0

        estado = "ACTIVA"
        fecha_cierre = None
        if nombre_obra.upper() == "FATIMA":
            estado = "CULMINADA"
            fecha_cierre = "2026-09-15"

        proyectos[nombre_obra] = {
            "monto_contrato": monto_contrato,
            "estimado_ejecutado": estimado,
            "cobrado_desembolsado": cobrado,
            "egresos_reales": egresos,
            "por_cobrar": por_cobrar,
            "avance_financiero_pct": round(avance_financiero_pct, 2),
            "flujo_caja": flujo_caja,
            "estado": estado,
            "fecha_cierre": fecha_cierre
        }

    if usar_control_obras:
        filas = list(proyectos.values())
        monto_contrato = round(sum(fila["monto_contrato"] for fila in filas), 2)
        estimado = round(sum(fila["estimado_ejecutado"] for fila in filas), 2)
        cobrado = round(sum(fila["cobrado_desembolsado"] for fila in filas), 2)
        flujo_caja = round(cobrado - estimado, 2)
        proyectos["CONSOLIDADO OBRAS"] = {
            "monto_contrato": monto_contrato,
            "estimado_ejecutado": estimado,
            "cobrado_desembolsado": cobrado,
            "egresos_reales": estimado,
            "por_cobrar": round(monto_contrato - cobrado, 2),
            "avance_financiero_pct": round(cobrado / monto_contrato * 100, 2)
            if monto_contrato > 0
            else 0.0,
            "flujo_caja": flujo_caja,
            "estado": "ACTIVA",
            "fecha_cierre": None,
        }

    return proyectos

if __name__ == "__main__":
    datos = obtener_datos_obras()
    print("Datos procesados correctamente:")
    print(datos)