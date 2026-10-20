"""Refresh delivery documentation and produce a clean release ZIP after smoke tests."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

root=Path(__file__).resolve().parents[1]
bundle=sorted(p for p in (root/'dist').glob('MySQL学习工具-*') if p.is_dir())[-1]
for name in ('user-guide.md','acceptance.md'):
    shutil.copy2(root/'docs'/name,bundle/name)
shutil.copy2(root/'scripts/offline_acceptance.ps1',bundle/'offline_acceptance.ps1')
archive=root/'dist/MySQL学习工具-v0.1.0.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as zip:
    for file in bundle.rglob('*'):
        if file.is_file():
            relative=file.relative_to(bundle)
            if relative.parts[0]=='data': continue
            zip.write(file,Path('MySQL学习工具-v0.1.0')/relative)
with zipfile.ZipFile(archive) as zip:
    assert not any(name.startswith('MySQL学习工具-v0.1.0/data/') for name in zip.namelist())
    assert 'MySQL学习工具-v0.1.0/MySQL学习工具.exe' in zip.namelist()
    assert zip.testzip() is None
with archive.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
archive.with_suffix('.sha256').write_text(digest+'  '+archive.name,encoding='utf-8')
info=dict(version='0.1.0',archive=archive.name,bytes=archive.stat().st_size,sha256=digest,
          backend_tests=57,frontend_tests=3,browser_flows=1,packaged_smoke='passed',
          clean_windows_vm='not_verified')
(root/'docs/delivery.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(info,ensure_ascii=False))
