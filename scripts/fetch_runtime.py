"""Download the pinned upstream ZIP only during development/build."""
from pathlib import Path
import hashlib
import json
import urllib.request
import zipfile

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'runtime/manifest.json').read_text(encoding='utf-8'))
archive=root/'runtime/downloads'/manifest['url'].split('/')[-1]
archive.parent.mkdir(parents=True,exist_ok=True)
if not archive.exists(): urllib.request.urlretrieve(manifest['url'],archive)
with archive.open('rb') as stream:
    actual=hashlib.file_digest(stream,'sha256').hexdigest()
if actual!=manifest['sha256']: raise SystemExit('MySQL ZIP checksum mismatch; refusing extraction')
target=root/'runtime/mysql'
if not target.exists():
    with zipfile.ZipFile(archive) as zip:
        extraction=root/'runtime/downloads/extracted'
        for entry in zip.infolist():
            destination=(extraction/entry.filename).resolve()
            if not destination.is_relative_to(extraction.resolve()): raise SystemExit('Unsafe archive member')
        zip.extractall(extraction)
    (extraction/f"mysql-{manifest['version']}-winx64").rename(target)
print('MySQL runtime verified:',manifest['version'],actual)
