import pytest
from pathlib import Path
from dataclasses import replace
import subprocess


@pytest.fixture(scope='session')
def runtime(tmp_path_factory):
    from trainer.config import resolve_paths
    from trainer.runtime.manager import RuntimeManager
    source=Path(__file__).resolve().parents[2]
    test_root=tmp_path_factory.mktemp('mysql-training')
    subprocess.run(['cmd.exe','/c','mklink','/J',str(test_root/'runtime'),str(source/'runtime')],capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    manager = RuntimeManager(replace(resolve_paths(test_root),content=source/'content'))
    manager.start()
    from trainer.runtime.bootstrap import seed_dataset
    with manager.connect(admin=True) as conn: seed_dataset(conn)
    yield manager
    manager.stop()
