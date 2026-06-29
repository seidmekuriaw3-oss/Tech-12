import importlib.util
import traceback

spec = importlib.util.spec_from_file_location('app_mod', 'app.py')
module = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(module)
    print('loaded')
except Exception:
    traceback.print_exc()
