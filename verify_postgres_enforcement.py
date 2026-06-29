import os
import sys

sys.path.insert(0, os.getcwd())

os.environ['DATABASE_URL'] = 'sqlite:///tmp/test.db'
from database import db

try:
    db._get_database_url()
except RuntimeError as exc:
    print(f'REJECTED_AS_EXPECTED: {exc}')
else:
    print('UNEXPECTED_SUCCESS')
