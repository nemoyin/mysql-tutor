import pytest
from pathlib import Path


@pytest.fixture(scope='session')
def runtime():
    from trainer.config import resolve_paths
    from trainer.runtime.manager import RuntimeManager
    manager = RuntimeManager(resolve_paths(Path(__file__).resolve().parents[2]))
    manager.start()
    yield manager
    manager.stop()
