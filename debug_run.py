from pathlib import Path
Path('debug_output.txt').write_text('hello from python', encoding='utf-8')
print('done')
