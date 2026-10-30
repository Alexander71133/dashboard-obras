"""
Módulo de Procesamiento de Datos Financieros
Extrae, limpia y mapea la información del libro Excel hacia la estructura del Dashboard.
"""
from pathlib import Path
import re
import shutil
import unicodedata
from urllib.parse import quote

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_EXCEL = BASE_DIR / "Datos" / "Gestion Proyecto Fatima.xlsx"
RUTA_DOCUMENTOS = BASE_DIR / "documentos" / "obras"
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


def _slug_obra(nombre_obra):
    texto = unicodedata.normalize("NFKD", nombre_obra)
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def _copiar_archivos_obra(valor_carpeta, nombre_obra):
    if valor_carpeta is None or pd.isna(valor_carpeta) or not str(valor_carpeta).strip():
        return []

    carpeta_relativa = Path(*str(valor_carpeta).strip().replace("\\", "/").split("/"))
    if carpeta_relativa.is_absolute() or ".." in carpeta_relativa.parts:
        raise ValueError(
            f"La ruta de archivos de '{nombre_obra}' debe ser relativa a Dropbox."
        )

    raiz_dropbox = RUTA_CONTROL_OBRAS.parent.resolve()
    carpeta_origen = (raiz_dropbox / carpeta_relativa).resolve()
    try:
        carpeta_origen.relative_to(raiz_dropbox)
    except ValueError as error:
        raise ValueError(
            f"La ruta de archivos de '{nombre_obra}' está fuera de la carpeta de Dropbox."
        ) from error
    if not carpeta_origen.is_dir():
        raise FileNotFoundError(
            f"No existe la carpeta de archivos de '{nombre_obra}': {carpeta_origen}"
        )

    extensiones_admitidas = {
        ".csv", ".doc", ".docx", ".gif", ".jpeg", ".jpg",
        ".pdf", ".png", ".txt", ".webp", ".xls", ".xlsx",
    }
    destino_obra = RUTA_DOCUMENTOS / _slug_obra(nombre_obra)
    archivos = []
    for archivo in sorted(
        carpeta_origen.rglob("*"), key=lambda item: item.as_posix().casefold()
    ):
        if archivo.is_symlink():
            raise ValueError(f"No se admiten enlaces simbólicos en: {archivo}")
        if not archivo.is_file():
            continue
        if archivo.suffix.lower() not in extensiones_admitidas:
            raise ValueError(
                f"Tipo de archivo no admitido para '{nombre_obra}': {archivo.name}"
            )

        ruta_relativa = archivo.relative_to(carpeta_origen)
        destino = destino_obra / ruta_relativa
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(archivo, destino)
        ruta_web = quote(
            destino.relative_to(BASE_DIR).as_posix(),
            safe="/",
        )
        archivos.append(
            {
                "nombre": archivo.name,
                "ruta": ruta_web,
                "tipo": "imagen"
                if archivo.suffix.lower() in {".gif", ".jpeg", ".jpg", ".png", ".webp"}
                else "documento",
            }
        )

    return archivos


def _copiar_archivo_transaccion(valor_ruta, nombre_obra, raiz_origen):
    if valor_ruta is None or pd.isna(valor_ruta) or not str(valor_ruta).strip():
        return None

    ruta_relativa = Path(
        *str(valor_ruta).strip().replace("\\", "/").split("/")
    )
    if ruta_relativa.is_absolute() or ".." in ruta_relativa.parts:
        raise ValueError(
            f"La ruta de la factura de '{nombre_obra}' debe ser relativa a Dropbox."
        )

    raiz_origen = raiz_origen.resolve()
    ruta_candidata = raiz_origen
    for parte in ruta_relativa.parts:
        ruta_candidata /= parte
        if ruta_candidata.is_symlink():
            raise ValueError(f"No se admiten enlaces simbólicos en: {ruta_candidata}")

    archivo_origen = ruta_candidata.resolve()
    try:
        archivo_origen.relative_to(raiz_origen)
    except ValueError as error:
        raise ValueError(
            f"La factura de '{nombre_obra}' está fuera de la carpeta de Dropbox."
        ) from error
    if not archivo_origen.is_file():
        raise FileNotFoundError(
            f"No existe la factura de '{nombre_obra}': {archivo_origen}"
        )

    extensiones_admitidas = {
        ".csv", ".doc", ".docx", ".gif", ".jpeg", ".jpg",
        ".pdf", ".png", ".txt", ".webp", ".xls", ".xlsx",
    }
    if archivo_origen.suffix.lower() not in extensiones_admitidas:
        raise ValueError(
            f"Tipo de archivo no admitido para la factura de '{nombre_obra}': "
            f"{archivo_origen.name}"
        )

    destino = (
        BASE_DIR
        / "documentos"
        / "obras"
        / _slug_obra(nombre_obra)
        / ruta_relativa
    )
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(archivo_origen, destino)
    ruta_web = quote(
        destino.relative_to(BASE_DIR).as_posix(),
        safe="/",
    )
    return {
        "nombre": archivo_origen.name,
        "ruta": ruta_web,
        "tipo": "imagen"
        if archivo_origen.suffix.lower() in {".gif", ".jpeg", ".jpg", ".png", ".webp"}
        else "documento",
    }


def _estado_dashboard(valor, nombre_obra):
    if valor is None or pd.isna(valor):
        raise ValueError(f"La obra '{nombre_obra}' no tiene un estado en el Excel.")

    estado_fuente = str(valor).strip()
    estado_normalizado = _normalizar_encabezado(estado_fuente)
    estados = {
        "en curso": "ACTIVA",
        "activa": "ACTIVA",
        "culminado": "CULMINADA",
        "culminada": "CULMINADA",
    }
    if estado_normalizado not in estados:
        raise ValueError(
            f"Estado no reconocido para la obra '{nombre_obra}': '{estado_fuente}'."
        )
    return estado_fuente, estados[estado_normalizado]


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
            "estado": _buscar_columna(df.columns, ("Status",)),
            "monto_contrato": _buscar_columna(df.columns, ("Monto del Contrato",)),
            "estimado": _buscar_columna(df.columns, ("Total Ejecutado",)),
            "cobrado": _buscar_columna(df.columns, ("Total Ingresos",)),
            "flujo_caja": _buscar_columna(df.columns, ("Utilidad Actual",)),
            "egresos": None,
            "por_cobrar": None,
            "avance_cobrado": None,
            "archivos": _buscar_columna(df.columns, ("Archivos",)),
        }
    else:
        print(
            "AVISO: no se encontró Control Obras.xlsx en Dropbox; "
            "se usarán los datos guardados en el Excel del repositorio."
        )
        columnas = {
            "obra": _buscar_columna(df.columns, ("Obra",)),
            "estado": _buscar_columna(df.columns, ("Status", "Estado")),
            "monto_contrato": _buscar_columna(df.columns, ("Monto Contrato",)),
            "estimado": _buscar_columna(df.columns, ("Estimado Acumulado/Ejecutado", "Ejecutado")),
            "cobrado": _buscar_columna(df.columns, ("Cobrado Acumulado/Desembolsado", "Desembolsado")),
            "flujo_caja": _buscar_columna(df.columns, ("Flujo de Caja",)),
            "egresos": _buscar_columna(df.columns, ("Egresos Reales", "Egresos")),
            "por_cobrar": _buscar_columna(df.columns, ("Por cobrar",)),
            "avance_cobrado": _buscar_columna(df.columns, ("% Avance Cobrado",)),
            "archivos": _buscar_columna(df.columns, ("Archivos",)),
        }

    columnas_requeridas = ("obra", "estado", "monto_contrato", "estimado", "cobrado")
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

        estado_fuente, estado = _estado_dashboard(
            row.get(columnas["estado"]), nombre_obra
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

        fecha_cierre = None
        if estado == "CULMINADA" and nombre_obra.upper() == "FATIMA":
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
            "estado_fuente": estado_fuente,
            "fecha_cierre": fecha_cierre,
            "archivos": _copiar_archivos_obra(
                row.get(columnas["archivos"]) if columnas["archivos"] else None,
                nombre_obra,
            ),
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
            "estado": "CONSOLIDADO",
            "estado_fuente": "Consolidado",
            "fecha_cierre": None,
            "archivos": [],
        }

    return proyectos


def obtener_datos_transacciones():
    """Agrupa las entradas y salidas de Registro_Transacciones por obra."""
    usar_control_obras = RUTA_CONTROL_OBRAS.is_file()
    ruta_excel = RUTA_CONTROL_OBRAS if usar_control_obras else RUTA_EXCEL

    if not ruta_excel.is_file():
        raise FileNotFoundError(f"No se encontró el archivo Excel en: {ruta_excel}")

    hojas = pd.ExcelFile(ruta_excel).sheet_names
    if "Registro_Transacciones" not in hojas:
        if usar_control_obras:
            raise ValueError(
                f"No se encontró la hoja 'Registro_Transacciones' en: {ruta_excel}"
            )
        print(
            "AVISO: el Excel de respaldo no contiene la hoja "
            "'Registro_Transacciones'; el módulo se generará sin registros."
        )
        return []

    df = pd.read_excel(ruta_excel, sheet_name="Registro_Transacciones")
    columnas = {
        "obra": _buscar_columna(df.columns, ("Obra",)),
        "movimiento": _buscar_columna(df.columns, ("Tipo de movimiento",)),
        "categoria": _buscar_columna(df.columns, ("Categoria",)),
        "monto": _buscar_columna(df.columns, ("Monto",)),
        "factura": _buscar_columna(df.columns, ("Factura",)),
        "condicion": _buscar_columna(df.columns, ("Condicion",)),
    }
    faltantes = [nombre for nombre, columna in columnas.items() if columna is None]
    if faltantes:
        raise ValueError(
            "Faltan encabezados en 'Registro_Transacciones': "
            + ", ".join(faltantes)
        )

    obras = {}
    for indice, fila in df.iterrows():
        valor_obra = fila.get(columnas["obra"])
        if pd.isna(valor_obra) or not str(valor_obra).strip():
            continue

        obra = str(valor_obra).strip()
        movimiento = fila.get(columnas["movimiento"])
        if pd.isna(movimiento) or not str(movimiento).strip():
            raise ValueError(
                f"Falta el tipo de movimiento en la fila {indice + 2} "
                "de 'Registro_Transacciones'."
            )
        movimiento = str(movimiento).strip()
        movimiento_normalizado = _normalizar_encabezado(movimiento)
        if movimiento_normalizado not in {"entrada", "salida"}:
            raise ValueError(
                f"Tipo de movimiento no reconocido en la fila {indice + 2} "
                f"de 'Registro_Transacciones': '{movimiento}'."
            )

        condicion = fila.get(columnas["condicion"])
        if pd.isna(condicion) or not str(condicion).strip():
            raise ValueError(
                f"Falta la condición en la fila {indice + 2} "
                "de 'Registro_Transacciones'."
            )
        condicion_normalizada = _normalizar_encabezado(condicion)
        condiciones_validas = {
            "activa": "ACTIVA",
            "activas": "ACTIVA",
            "culminada": "CULMINADA",
            "culminadas": "CULMINADA",
        }
        if condicion_normalizada not in condiciones_validas:
            raise ValueError(
                f"Condición no reconocida en la fila {indice + 2} "
                f"de 'Registro_Transacciones': '{condicion}'."
            )
        estado_obra = condiciones_validas[condicion_normalizada]

        datos_obra = obras.setdefault(
            obra,
            {
                "obra": obra,
                "estado": estado_obra,
                "tipos_movimiento": set(),
                "categorias": set(),
                "total_entradas": 0.0,
                "total_salidas": 0.0,
                "facturas": {},
            },
        )
        if datos_obra["estado"] != estado_obra:
            raise ValueError(
                f"La obra '{obra}' tiene más de una condición en "
                "'Registro_Transacciones'."
            )
        datos_obra["tipos_movimiento"].add(movimiento)

        categoria = fila.get(columnas["categoria"])
        if pd.notna(categoria) and str(categoria).strip():
            datos_obra["categorias"].add(str(categoria).strip())

        monto = _numero(fila.get(columnas["monto"]))
        campo_total = (
            "total_entradas"
            if movimiento_normalizado == "entrada"
            else "total_salidas"
        )
        datos_obra[campo_total] += monto

        factura = _copiar_archivo_transaccion(
            fila.get(columnas["factura"]),
            obra,
            ruta_excel.parent,
        )
        if factura:
            datos_obra["facturas"][factura["ruta"]] = factura

    return [
        {
            "obra": obra,
            "estado": datos["estado"],
            "tipos_movimiento": sorted(datos["tipos_movimiento"]),
            "categorias": sorted(datos["categorias"]),
            "total_entradas": round(datos["total_entradas"], 2),
            "total_salidas": round(datos["total_salidas"], 2),
            "total": round(
                datos["total_entradas"] - datos["total_salidas"], 2
            ),
            "facturas": sorted(
                datos["facturas"].values(),
                key=lambda factura: factura["nombre"].casefold(),
            ),
        }
        for obra, datos in sorted(obras.items(), key=lambda item: item[0].casefold())
    ]


if __name__ == "__main__":
    datos = obtener_datos_obras()
    print("Datos procesados correctamente:")
    print(datos)