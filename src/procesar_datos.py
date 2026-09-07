"""
Módulo de Procesamiento de Datos Financieros
Extrae, limpia y mapea la información del libro Excel hacia la estructura del Dashboard.
"""
from pathlib import Path
import unicodedata
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_EXCEL = BASE_DIR / "Datos" / "Gestion Proyecto Fatima.xlsx"


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
    Lee el archivo Excel y retorna un diccionario formateado con los datos
    organizados estrictamente según la secuencia analítica requerida.
    """
    if not RUTA_EXCEL.exists():
        raise FileNotFoundError(f"No se encontró el archivo Excel en: {RUTA_EXCEL}")

    df = pd.read_excel(RUTA_EXCEL, sheet_name="Resumen Financiero")

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

    columnas_requeridas = ("obra", "monto_contrato", "estimado", "cobrado", "por_cobrar")
    faltantes = [nombre for nombre in columnas_requeridas if columnas[nombre] is None]
    if faltantes:
        raise ValueError(f"Faltan encabezados en 'Resumen Financiero': {', '.join(faltantes)}")

    proyectos = {}

    for _, row in df.iterrows():
        valor_obra = row.get(columnas["obra"])
        nombre_obra = str(valor_obra).strip()
        if not nombre_obra or pd.isna(valor_obra):
            continue

        monto_contrato = _numero(row.get(columnas["monto_contrato"]))
        estimado = _numero(row.get(columnas["estimado"]))
        cobrado = _numero(row.get(columnas["cobrado"]))
        por_cobrar = _numero(row.get(columnas["por_cobrar"]))

        if columnas["flujo_caja"]:
            flujo_caja = _numero(row.get(columnas["flujo_caja"]))
        else:
            flujo_caja = cobrado - _numero(row.get(columnas["egresos"]))

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

        proyectos[nombre_obra] = {
            "monto_contrato": monto_contrato,
            "estimado_ejecutado": estimado,
            "cobrado_desembolsado": cobrado,
            "egresos_reales": egresos,
            "por_cobrar": por_cobrar,
            "avance_financiero_pct": round(avance_financiero_pct, 2),
            "flujo_caja": flujo_caja
        }

    return proyectos

if __name__ == "__main__":
    datos = obtener_datos_obras()
    print("Datos procesados correctamente:")
    print(datos)