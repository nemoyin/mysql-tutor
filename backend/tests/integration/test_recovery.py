import subprocess
from dataclasses import replace
from pathlib import Path
import pytest
import json
import os
import socket
import sys
import time
from trainer.config import resolve_paths
from trainer.runtime.manager import RuntimeManager


def test_second_manager_cannot_take_ownership(runtime):
    other=RuntimeManager(runtime.paths)
    with pytest.raises(RuntimeError,match='运行'): other.start()
    other.stop()
    with runtime.connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT 1');assert cur.fetchone()[0]==1


def test_interrupted_initialization_recovers(tmp_path,runtime):
    root=tmp_path/'中文 空格'
    root.mkdir()
    subprocess.run(['cmd.exe','/c','mklink','/J',str(root/'runtime'),str(runtime.paths.root/'runtime')],capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    staging=root/'data/mysql-initializing'
    staging.mkdir(parents=True);(staging/'partial').write_text('incomplete')
    manager=RuntimeManager(resolve_paths(root))
    try:
        manager.start()
        assert manager.state().phase=='ready'
        assert len(list((root/'data').glob('mysql-interrupted-*')))==1
    finally: manager.stop()


def test_unknown_error_preserves_original():
    from trainer.query.errors import mysql_failure
    error=mysql_failure(Exception(9999,'original diagnostic'))
    assert 'original diagnostic' in error.original
    assert error.mysql_errno==9999


def test_abrupt_launcher_exit_leaves_database_restartable(tmp_path,runtime):
    root=tmp_path/'abrupt-exit'
    root.mkdir()
    subprocess.run(['cmd.exe','/c','mklink','/J',str(root/'runtime'),str(runtime.paths.root/'runtime')],capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    source=Path(__file__).resolve().parents[3]
    script='''import sys,time
from pathlib import Path
from trainer.config import resolve_paths
from trainer.runtime.manager import RuntimeManager
m=RuntimeManager(resolve_paths(Path(sys.argv[1])))
m.start()
print(m.port,flush=True)
time.sleep(120)
'''
    env={**os.environ,'PYTHONPATH':str(source/'backend')}
    parent=subprocess.Popen([sys.executable,'-u','-c',script,str(root)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
    port=None
    restarted=RuntimeManager(resolve_paths(root))
    try:
        port=int(parent.stdout.readline().strip())
        parent.terminate();parent.wait(timeout=10)
        deadline=time.monotonic()+10
        alive=True
        while time.monotonic()<deadline:
            try:
                with socket.create_connection(('127.0.0.1',port),timeout=.2): pass
            except OSError:
                alive=False;break
            time.sleep(.1)
        assert not alive, 'MySQL must not survive an abruptly terminated launcher'
        restarted.start()
        assert restarted.state().phase=='ready'
    finally:
        if parent.poll() is None: parent.terminate();parent.wait(timeout=10)
        restarted.stop()
        if port:
            # RED cleanup: authenticated shutdown of this test's known instance only.
            try:
                import pymysql
                config=json.loads((root/'data/instance.json').read_text(encoding='utf-8'))
                with pymysql.connect(host='127.0.0.1',port=port,user='root',password=config['admin_password'],connect_timeout=1,autocommit=True) as conn:
                    with conn.cursor() as cur: cur.execute('SHUTDOWN')
            except pymysql.MySQLError: pass
