import subprocess
import sys

cmd = [sys.executable, '-m', 'pytest', 'tests/test_database_postgres_only.py']
result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)
print(result.stderr)
raise SystemExit(result.returncode)
