import subprocess
import os

res = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
pids = set()
for line in res.stdout.splitlines():
    if ":5001 " in line and "LISTENING" in line:
        parts = line.strip().split()
        if len(parts) >= 5:
            pids.add(int(parts[-1]))

print("Found PIDs:", pids)
for pid in pids:
    try:
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True)
        print(f"Killed PID {pid}")
    except Exception as e:
        print(f"Error killing {pid}: {e}")

