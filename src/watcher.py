import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from generar_html import generar_dashboard

BASE_DIR = Path(__file__).resolve().parent.parent
RUTAS_EXCEL = {
    (BASE_DIR / "Datos" / "Gestion Proyecto Fatima.xlsx").resolve(),
    (
        Path.home()
        / "Dropbox"
        / "Macroandes"
        / "Inversora Macroandes"
        / "Control Obras.xlsx"
    ).resolve(),
}

class ExcelHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if Path(event.src_path).resolve() in RUTAS_EXCEL:
            print("\n[DETECTADO] Cambio en Excel. Actualizando Dashboard...")
            generar_dashboard()

if __name__ == "__main__":
    event_handler = ExcelHandler()
    observer = Observer()
    carpetas_excel = {ruta.parent for ruta in RUTAS_EXCEL if ruta.parent.is_dir()}
    for carpeta in carpetas_excel:
        observer.schedule(event_handler, path=str(carpeta), recursive=False)
    observer.start()
    print("=== MONITOR ACTIVO: Modifica un libro de datos y se actualizará el dashboard. (Ctrl+C para salir) ===")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()