import subprocess
from dataclasses import replace
from pathlib import Path
import pytest
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
