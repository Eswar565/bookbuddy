import subprocess
res = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
for line in res.stdout.splitlines():
    if "5001" in line:
        print(line)
