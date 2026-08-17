"""
Módulo de Procesamiento de Datos Financieros
Extrae, limpia y mapea la información del libro Excel hacia la estructura del Dashboard.
"""
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_EXCEL = BASE_DIR / "Datos" / "Gestion Proyecto Fatima.xlsx"

def obtener_datos_obras():
    """
    Lee el archivo Excel y retorna un diccionario formateado con los datos
    organizados estrictamente según la secuencia analítica requerida.
    """
    if not RUTA_EXCEL.exists():
        raise FileNotFoundError(f"No se encontró el archivo Excel en: {RUTA_EXCEL}")

    df = pd.read_excel(RUTA_EXCEL, sheet_name="Resumen Financiero")
    df.columns = df.columns.str.strip()

    proyectos = {}

    for _, row in df.iterrows():
        nombre_obra = str(row.get('Obra', '')).strip()
        if not nombre_obra or pd.isna(row.get('Obra')):
            continue

        monto_contrato = float(row.get('Monto Contrato', 0) or 0)
        estimado = float(row.get('Estimado Acumulado/Ejecutado', 0) or 0)
        cobrado = float(row.get('Cobrado Acumulado/Desembolsado', 0) or 0)
        egresos = float(row.get('Egresos Reales', 0) or 0)
        por_cobrar = float(row.get('Por cobrar', 0) or 0)
        
        # Cálculo / Extracción del Avance Financiero %
        val_pct = row.get('% Avance Cobrado', None)
        if val_pct is not None and not pd.isna(val_pct):
            avance_financiero_pct = float(val_pct * 100) if float(val_pct) <= 1.0 else float(val_pct)
        else:
            avance_financiero_pct = (cobrado / monto_contrato * 100) if monto_contrato > 0 else 0.0

        flujo_caja = cobrado - egresos

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