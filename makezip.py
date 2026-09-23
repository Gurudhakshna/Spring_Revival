import os, zipfile

ROOT = r'C:\jal-raksha'
OUT = os.path.join(os.path.expanduser('~'), 'Downloads', 'jal-raksha-ai.zip')
SKIP_DIRS = {'node_modules', '__pycache__', '.pytest_cache', '.git'}
SKIP_FILES = {'jal-raksha-ai.zip'}

if os.path.exists(OUT):
    os.remove(OUT)

count = 0
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn in SKIP_FILES or fn.endswith(('.log', '.err')):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.join('jal-raksha', os.path.relpath(full, ROOT))
            z.write(full, rel)
            count += 1

mb = os.path.getsize(OUT) / 1024 / 1024
print(f'ZIP OK: {OUT} | {mb:.1f} MB | {count} files')
