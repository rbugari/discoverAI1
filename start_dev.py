import subprocess
import sys
import os
import time
import shutil
from dotenv import load_dotenv

# Cargar variables
load_dotenv()

def find_venv(root_dir):
    """Busca el entorno virtual en ubicaciones comunes."""
    candidates = [
        os.path.join(root_dir, ".venv"),
        os.path.join(root_dir, "apps", "api", ".venv"),
        os.path.join(root_dir, "venv"),
    ]
    
    for venv in candidates:
        if os.path.exists(venv):
            python_exe = os.path.join(venv, "Scripts", "python.exe")
            if os.path.exists(python_exe):
                return python_exe
    return None

def main():
    print("🚀 Iniciando DiscoverAI Dev Environment (v2.1)...")
    print("-----------------------------------------------")

    root_dir = os.getcwd()
    api_dir = os.path.join(root_dir, "apps", "api")
    web_dir = os.path.join(root_dir, "apps", "web")

    # 1. Encontrar Python del entorno virtual
    python_exe = find_venv(root_dir)
    
    # Si no encuentra venv, intenta usar el python del sistema (riesgoso pero fallback)
    if not python_exe:
        print("⚠️  No se encontró .venv en root ni en apps/api.")
        print("    Intentando usar 'python' del sistema...")
        python_exe = "python"
    else:
        print(f"✅ Usando entorno virtual: {python_exe}")

    # 2. Comandos
    # Usamos python -m uvicorn y python -m celery para asegurar el entorno
    
    # API: Se ejecuta desde apps/api
    # start "Title" /D "WorkDir" cmd /k "command"
    cmd_api = f'start "DiscoverAI API" /D "{api_dir}" cmd /k ""{python_exe}" -m uvicorn app.main:app --reload --port 8000"'
    
    # Worker: Se ejecuta desde apps/api
    # Usamos el script custom worker.py (Polling Loop)
    cmd_worker = f'start "DiscoverAI Worker" /D "{api_dir}" cmd /k ""{python_exe}" -m app.worker"'

    # Web: Se ejecuta desde apps/web
    # Asumimos que npm está en el PATH global
    cmd_web = f'start "DiscoverAI Web" /D "{web_dir}" cmd /k "npm run dev"'

    print("\nIniciando servicios...")
    
    try:
        # API
        print(f"1. API [Backend] -> Lanzando...")
        subprocess.Popen(cmd_api, shell=True)
        time.sleep(2) 

        # Worker
        print(f"2. Worker [Celery] -> Lanzando...")
        subprocess.Popen(cmd_worker, shell=True)
        time.sleep(2)

        # Web
        print(f"3. Web [Frontend] -> Lanzando...")
        subprocess.Popen(cmd_web, shell=True)
        
        print("\n✅ Servicios iniciados.")
        print("   - API Docs: http://localhost:8000/docs")
        print("   - Dashboard: http://localhost:3000")
        print("\nℹ️  Si ves errores de 'Acceso denegado', ejecuta la terminal como Administrador.")
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
