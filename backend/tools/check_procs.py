import subprocess

p = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-NetTCPConnection -LocalPort 5001 -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, OwningProcess, State"], capture_output=True, text=True)
print(p.stdout)
