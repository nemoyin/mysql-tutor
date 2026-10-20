"""Exercise the frozen executable with only Windows system tools on PATH."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import urllib.request

parser=argparse.ArgumentParser()
parser.add_argument('root',type=Path)
args=parser.parse_args()
root=args.root.resolve()
exe=root/'MySQL学习工具.exe'
assert exe.is_file(), 'Packaged executable missing'
with socket.socket() as sock:
    sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
base=f'http://127.0.0.1:{port}'
environment=os.environ.copy()
environment['PATH']=str(Path(os.environ['SystemRoot'])/'System32')
environment.pop('PYTHONPATH',None)
token=''
def request(path,body=None,method=None):
    payload=None if body is None else json.dumps(body).encode()
    req=urllib.request.Request(base+'/api'+path,data=payload,method=method,
        headers={'Content-Type':'application/json','X-Local-Token':token})
    with urllib.request.urlopen(req,timeout=15) as response: return json.load(response)

def launch():
    process=subprocess.Popen([str(exe),'--no-browser','--port',str(port)],cwd=root,env=environment,creationflags=subprocess.CREATE_NO_WINDOW)
    deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        if process.poll() is not None: raise RuntimeError('Packaged application exited before ready')
        try:
            data=request('/bootstrap')
            if data['runtime']['phase']=='ready': return process,data
            if data['runtime']['phase']=='failed': raise RuntimeError(data['runtime']['message'])
        except (OSError,TimeoutError): pass
        time.sleep(.3)
    process.terminate();raise RuntimeError('Packaged startup timed out')

process=None
start=time.monotonic()
try:
    process,boot=launch();token=boot['token']
    startup=round(time.monotonic()-start,2)
    nickname='离线发行验收'
    existing=next((p for p in boot['profiles'] if p['nickname']==nickname),None)
    profile=existing or request('/profiles',{'nickname':nickname})
    pid=profile['id']
    current=request(f'/profiles/{pid}/drafts/01-01')
    request(f'/profiles/{pid}/drafts/01-01',{'sql':'SELECT * FROM customers','revision':current['revision']+1},method='PUT')
    assert len(request('/query/run',{'profile_id':pid,'scope':'01-01','sql':'SELECT * FROM customers'})['rows'])==30
    assert request('/problems/01-01/submit',{'profile_id':pid,'sql':'SELECT * FROM customers'})['status']=='passed'
    request('/admin/shutdown',{'confirmation':'shutdown'});process.wait(timeout=30)
    process,boot=launch();token=boot['token']
    assert any(p['id']==pid for p in boot['profiles'])
    assert request(f'/profiles/{pid}/drafts/01-01')['sql']=='SELECT * FROM customers'
    assert request(f'/profiles/{pid}/progress')['01-01']['mode']=='independent'
    # The frozen executable must also release its database when terminated abruptly.
    process.terminate();process.wait(timeout=15)
    time.sleep(.3)
    process,boot=launch();token=boot['token']
    assert request(f'/profiles/{pid}/progress')['01-01']['mode']=='independent'
    request('/admin/shutdown',{'confirmation':'shutdown'});process.wait(timeout=30)
    print(json.dumps(dict(status='passed',startup_seconds=startup,restricted_path=True,restart_persistence=True,abrupt_restart=True,port=port),ensure_ascii=False))
finally:
    if process and process.poll() is None:
        try:
            request('/admin/shutdown',{'confirmation':'shutdown'});process.wait(timeout=30)
        except Exception:
            process.terminate();process.wait(timeout=15)
