import os
import subprocess
import sys
import time
import threading
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
child_exit_code = 0
child_exit_lock = threading.Lock()
child_exit_event = threading.Event()


def _record_child_exit(exit_code, child_name):
    global child_exit_code
    if exit_code:
        with child_exit_lock:
            if child_exit_code == 0:
                child_exit_code = exit_code
        logger.error("%s exited with non-zero code %s.", child_name, exit_code)
        child_exit_event.set()

def run_backend():
    logger.info("Starting Flask Backend on http://localhost:5000 ...")
    env = os.environ.copy()
    # Add root folder to pythonpath to resolve relative imports
    import site
    user_site = site.getusersitepackages()
    root_dir = os.path.dirname(os.path.abspath(__file__))
    env["PYTHONPATH"] = f"{root_dir}{os.pathsep}{user_site}"
    
    cmd = [sys.executable, "-m", "backend.app"]
    p = subprocess.Popen(cmd, cwd=root_dir, env=env)
    exit_code = p.wait()
    _record_child_exit(exit_code, "Flask backend")

def run_frontend():
    logger.info("Starting Vite Frontend on http://localhost:5173 ...")
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    
    # Run npm run dev inside frontend
    p = subprocess.Popen(["npm", "run", "dev"], cwd=frontend_dir, shell=True)
    exit_code = p.wait()
    _record_child_exit(exit_code, "Vite frontend")

if __name__ == "__main__":
    t1 = threading.Thread(target=run_backend, daemon=True)
    t2 = threading.Thread(target=run_frontend, daemon=True)
    
    t1.start()
    time.sleep(2)  # Give backend a moment to initialize database
    t2.start()
    
    try:
        while not child_exit_event.wait(1):
            pass
        with child_exit_lock:
            exit_code = child_exit_code
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Shutting down FinIntel SME servers...")
        sys.exit(0)
