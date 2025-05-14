import webbrowser
import subprocess
import os
import signal
import psutil
import time

# Optional: kill any existing bokeh serve process
def kill_existing_bokeh():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] and 'bokeh' in proc.info['name'].lower():
            try:
                proc.kill()
                print(f"Killed existing Bokeh process: PID {proc.pid}")
            except Exception:
                pass

kill_existing_bokeh()
time.sleep(1)  # give it a second to clear out

# Launch Bokeh server with updated script
subprocess.Popen(["bokeh", "serve", "--show", "dashboard.py"], shell=True)

# Optional: open browser manually if "--show" fails
# webbrowser.open("http://localhost:5006/dashboard")