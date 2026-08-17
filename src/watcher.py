import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from generar_html import generar_dashboard

BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_EXCEL = BASE_DIR / "Datos" / "Gestion Proyecto Fatima.xlsx"

class ExcelHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if Path(event.src_path).resolve() == RUTA_EXCEL.resolve():
            print("\n[DETECTADO] Cambio en Excel. Actualizando Dashboard...")
            generar_dashboard()

if __name__ == "__main__":
    event_handler = ExcelHandler()
    observer = Observer()
    observer.schedule(event_handler, path=str(RUTA_EXCEL.parent), recursive=False)
    observer.start()
    print("=== MONITOR ACTIVO: Modifica tu Excel y se actualizará solo. (Ctrl+C para salir) ===")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()