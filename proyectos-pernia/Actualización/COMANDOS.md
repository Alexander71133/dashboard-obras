# Actualizar Proyectos Pernia

El dashboard no se actualiza automáticamente cuando cambia el Excel. Ejecuta estos comandos después de sincronizar en Dropbox el libro y los documentos del proyecto.

```powershell
# Regenerar el dashboard y copiar los adjuntos desde Dropbox
Set-Location "$HOME\Documents\Dashboard_Obras\proyectos-pernia"
python .\generar_dashboard.py

# Publicar el proyecto en GitHub desde la carpeta raíz del repositorio
Set-Location ..
git status
git add .\proyectos-pernia
git diff --cached --stat
git commit -m "Actualizar dashboard Proyectos Pernia"
git push origin main
```

Revisa la salida de `git status` y `git diff --cached --stat` antes de confirmar. Si `git commit` indica que no hay cambios, no hay nada nuevo que publicar.

El dashboard y los archivos de `documentos/` serán públicos si GitHub Pages está habilitado para el repositorio. No publiques archivos privados.