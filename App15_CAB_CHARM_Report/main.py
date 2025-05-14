import subprocess
import os
import time
import webbrowser
import psutil
import sys
import tempfile
import shutil
import openpyxl

def kill_existing_bokeh():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline') or []
            if isinstance(cmdline, list) and 'bokeh' in ' '.join(cmdline):
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

# Use MEIPASS if frozen, otherwise __file__ location
if getattr(sys, 'frozen', False):
    app_path = sys._MEIPASS
else:
    app_path = os.path.dirname(os.path.abspath(__file__))

# Ensure export file exists
if not (os.path.exists("export.xlsx") or os.path.exists("export.csv")):
    import pandas as pd
    dummy_data = pd.DataFrame(columns=[
        "Change ID", "Status", "Description", "UAT Coordinator", "Cycle Description",
        "Cycle ID", "CAB Meeting Date", "Implementation Date", "Category",
        "Change Impact", "Change Complexity"
    ])
    dummy_data.to_excel("export.xlsx", index=False)

# Kill existing bokeh
kill_existing_bokeh()

# Copy dashboard.py to a real temp path
dashboard_source = os.path.join(app_path, "dashboard.py")
dashboard_temp_path = os.path.join(tempfile.gettempdir(), "dashboard.py")
shutil.copyfile(dashboard_source, dashboard_temp_path)

# Run Bokeh with that path
subprocess.Popen([
    "bokeh", "serve", dashboard_temp_path,
    "--allow-websocket-origin=localhost:5006"
], shell=True)

time.sleep(2)
webbrowser.open("http://localhost:5006/dashboard")

#to create installer, run the following cmd in bash: pyinstaller --onefile --add-data "dashboard.py;." --hidden-import openpyxl --icon=sap_sre_icon.ico main.py

