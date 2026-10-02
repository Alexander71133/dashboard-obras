"""Genera los datos y adjuntos estáticos del tablero de Proyectos Pernia."""

import json
import shutil
from pathlib import Path
from urllib.parse import quote

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = (
    Path.home()
    / "Dropbox"
    / "Macroandes"
    / "Inversora Macroandes"
    / "Informes de obras"
    / "Proyectos Pernia"
)
EXCEL_PATH = SOURCE_DIR / "Tablero Control Pernia.xlsx"
ASSET_DIR = BASE_DIR / "documentos"
OUTPUT_PATH = BASE_DIR / "proyectos.js"

FOLDER_BY_ARCHIVE = {
    "Suelos Café": "Estudios Suelo Café",
    "Suelos Galpón": "Estudios Suelos Galpon",
}


def porcentaje(valor):
    if pd.isna(valor):
        return 0.0
    numero = float(valor)
    return round(numero * 100 if 0 <= numero <= 1 else numero, 1)


def generar():
    if not EXCEL_PATH.is_file():
        raise FileNotFoundError(f"No se encontró el tablero fuente: {EXCEL_PATH}")

    tabla = pd.read_excel(EXCEL_PATH, sheet_name="Tabla de Control")
    requeridas = {
        "Proyecto",
        "Archivos",
        "Estado",
        "Presupuesto",
        "Cronograma",
        "% Ejecución fisica",
        "% Ejecución financiera",
        "Monto desembolso",
        "Monto por pagar",
    }
    faltantes = requeridas.difference(tabla.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas en 'Tabla de Control': {', '.join(sorted(faltantes))}")

    proyectos = []
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    for _, fila in tabla.iterrows():
        carpeta_archivos = str(fila["Archivos"]).strip()
        carpeta_origen = FOLDER_BY_ARCHIVE.get(carpeta_archivos, carpeta_archivos)
        origen = SOURCE_DIR / carpeta_origen
        if not origen.is_dir():
            raise FileNotFoundError(f"No existe la carpeta de adjuntos: {origen}")

        carpeta_salida = ASSET_DIR / carpeta_archivos
        carpeta_salida.mkdir(parents=True, exist_ok=True)
        adjuntos = []

        for archivo in sorted(origen.iterdir(), key=lambda item: item.name.casefold()):
            if not archivo.is_file() or archivo.suffix.lower() not in {".pdf", ".jpg", ".jpeg", ".png"}:
                continue
            destino = carpeta_salida / archivo.name
            shutil.copy2(archivo, destino)
            ruta_web = quote(destino.relative_to(BASE_DIR).as_posix(), safe="/")
            adjuntos.append(
                {
                    "name": archivo.name,
                    "url": ruta_web,
                    "type": "image" if archivo.suffix.lower() in {".jpg", ".jpeg", ".png"} else "pdf",
                }
            )

        proyectos.append(
            {
                "name": str(fila["Proyecto"]).strip(),
                "folder": carpeta_archivos,
                "status": str(fila["Estado"]).strip(),
                "schedule": str(fila["Cronograma"]).strip(),
                "physical": porcentaje(fila["% Ejecución fisica"]),
                "financial": porcentaje(fila["% Ejecución financiera"]),
                "budget": float(fila["Presupuesto"]),
                "paid": float(fila["Monto desembolso"]),
                "due": float(fila["Monto por pagar"]),
                "files": adjuntos,
            }
        )

    OUTPUT_PATH.write_text(
        "window.MACROANDES_PROJECTS = "
        + json.dumps(proyectos, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    print(f"Tablero generado: {len(proyectos)} proyectos, {sum(len(p['files']) for p in proyectos)} adjuntos")


if __name__ == "__main__":
    generar()