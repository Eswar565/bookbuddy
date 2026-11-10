import subprocess

res = subprocess.run(['wmic', 'process', 'where', 'name="python.exe"', 'get', 'processid,commandline,creationdate'], capture_output=True, text=True)
for line in res.stdout.splitlines():
    if 'run.py' in line:
        print(line)

