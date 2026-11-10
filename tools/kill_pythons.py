import os, signal, subprocess

current_pid = os.getpid()
p = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Process python* | Select-Object -ExpandProperty Id"], capture_output=True, text=True)
pids = [int(x.strip()) for x in p.stdout.split() if x.strip()]
print('Found pids:', pids)
for pid in pids:
    if pid != current_pid:
        try:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)])
            print('Killed', pid)
        except Exception as e:
            print('Error killing', pid, e)

