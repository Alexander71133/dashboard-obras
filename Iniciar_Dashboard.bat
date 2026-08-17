@echo off
title Lanzador Dashboard de Obras
echo Activar entorno virtual y compilando datos...
cd /d "%~dp0"
call venv\Scripts\activate
python src\generar_html.py
start "" "output\dashboard_obras.html"
python src\watcher.py
pause