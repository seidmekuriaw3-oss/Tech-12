import subprocess
import sys
from pathlib import Path

cmd = [r'C:\Users\USER\AppData\Local\Python\pythoncore-3.14-64\python.exe', '-m', 'pytest', '-q', 'tests/test_admin_routes.py']
res = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).resolve().parent, timeout=600)
print(res.stdout, end='')
print(res.stderr, end='')
raise SystemExit(res.returncode)
