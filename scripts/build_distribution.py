from pathlib import Path
from datetime import datetime
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import zipfile

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'backend'))
from trainer.distribution import assemble_distribution

def run(args,**kwargs): subprocess.run(args,cwd=root,check=True,**kwargs)
run([sys.executable,str(root/'scripts/fetch_runtime.py')])
subprocess.run(['npm.cmd','run','build'],cwd=root/'frontend',check=True)
run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--noconsole',
     '--name','SQLStudio','--paths',str(root/'backend'),
     '--collect-all','sqlglot','--collect-all','pymysql','--collect-all','cryptography',
     '--add-data',f'{root / "backend/trainer/dataset"}{os.pathsep}trainer/dataset',
     str(root/'backend/trainer/main.py')])
output=root/'dist'/('MySQL学习工具-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
assemble_distribution(root,root/'dist/SQLStudio',output)
for name in ['msvcp140.dll','msvcp140_1.dll','msvcp140_2.dll','msvcp140_atomic_wait.dll','vcruntime140.dll','vcruntime140_1.dll','concrt140.dll']:
    dll=Path(os.environ['SystemRoot'])/'System32'/name
    if not dll.exists(): raise RuntimeError(f'Missing app-local runtime dependency: {name}')
    shutil.copy2(dll,output/'runtime/mysql/bin'/name)
licenses=output/'licenses'
licenses.mkdir()
for dist in importlib.metadata.distributions():
    for item in dist.files or []:
        if item.name.lower().startswith(('license','copying','notice')):
            file=dist.locate_file(item)
            if file.is_file():
                directory=licenses/dist.metadata['Name']
                directory.mkdir(exist_ok=True)
                shutil.copy2(file,directory/item.name)
for name in ['user-guide.md','acceptance.md']:
    file=root/'docs'/name
    if file.exists(): shutil.copy2(file,output/name)
(output/'THIRD-PARTY-NOTICES.txt').write_text('MySQL Community Server: see runtime/mysql/LICENSE.\nMicrosoft Visual C++ Runtime: app-local Microsoft runtime DLLs; https://visualstudio.microsoft.com/license-terms/\nPython and Python packages: see licenses/ and _internal/.\nFrontend dependency license metadata: frontend-licenses.json.\n',encoding='utf-8')
frontend={}
for package in (root/'frontend/node_modules').glob('**/package.json'):
    try:
        data=json.loads(package.read_text(encoding='utf-8'))
        if data.get('name') and data.get('license'): frontend[data['name']]=dict(version=data.get('version'),license=data['license'])
    except (ValueError,OSError): pass
(output/'frontend-licenses.json').write_text(json.dumps(frontend,ensure_ascii=False,indent=2),encoding='utf-8')
for file in (root/'frontend/node_modules').rglob('*'):
    if file.is_file() and file.name.lower().startswith(('license','copying','notice')):
        target=licenses/'frontend'/file.relative_to(root/'frontend/node_modules')
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(file,target)
archive=output.with_suffix('.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as zip:
    for file in output.rglob('*'):
        if file.is_file(): zip.write(file,Path(output.name)/file.relative_to(output))
with archive.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
archive.with_suffix('.sha256').write_text(digest+'  '+archive.name,encoding='utf-8')
print(json.dumps(dict(directory=str(output),archive=str(archive),bytes=archive.stat().st_size,sha256=digest),ensure_ascii=False))
