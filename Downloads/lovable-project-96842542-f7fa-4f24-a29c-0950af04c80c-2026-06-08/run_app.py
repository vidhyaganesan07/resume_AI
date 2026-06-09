import subprocess
import threading
import sys
import os
 
def run_backend():
    print("[Python Backend] Starting server...")
    # Runs your backend on port 8000
    subprocess.run([sys.executable, "backend/main.py"])
 
def run_frontend():
    print("[Lovable Frontend] Starting server...")
    # Automatically handles Windows vs Mac terminal environments
    use_shell = True if os.name == 'nt' else False
    subprocess.run("npm run dev", shell=use_shell)
 
if __name__ == "__main__":
    # Start both servers on separate threads at the same time
    t1 = threading.Thread(target=run_backend)
    t2 = threading.Thread(target=run_frontend)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
