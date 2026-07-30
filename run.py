import os
import subprocess
import sys
import time
import threading

def run_backend():
    print("[SYSTEM] Starting Flask Backend on http://localhost:5000 ...")
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    env = os.environ.copy()
    # Add root folder to pythonpath to resolve relative imports
    import site
    user_site = site.getusersitepackages()
    root_dir = os.path.dirname(os.path.abspath(__file__))
    env["PYTHONPATH"] = f"{root_dir}{os.pathsep}{user_site}"
    
    cmd = [sys.executable, "-m", "backend.app"]
    p = subprocess.Popen(cmd, cwd=root_dir, env=env)
    p.wait()

def run_frontend():
    print("[SYSTEM] Starting Vite Frontend on http://localhost:5173 ...")
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    
    # Run npm run dev inside frontend
    p = subprocess.Popen(["npm", "run", "dev"], cwd=frontend_dir, shell=True)
    p.wait()

if __name__ == "__main__":
    t1 = threading.Thread(target=run_backend, daemon=True)
    t2 = threading.Thread(target=run_frontend, daemon=True)
    
    t1.start()
    time.sleep(2)  # Give backend a moment to initialize database
    t2.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SYSTEM] Shutting down FinIntel SME servers...")
        sys.exit(0)
