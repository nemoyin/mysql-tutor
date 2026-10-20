from pathlib import Path
import pytest
from fastapi.testclient import TestClient


def test_health_and_paths(tmp_path):
    from trainer.config import resolve_paths
    from trainer.api.app import create_app
    paths = resolve_paths(tmp_path)
    assert paths.mysql_data == tmp_path / 'data' / 'mysql'
    assert paths.learning_db == tmp_path / 'data' / 'learning.sqlite3'
    with TestClient(create_app(paths)) as client:
        assert client.get('/api/health').json()['status'] == 'ok'


def test_root_must_be_directory(tmp_path):
    from trainer.config import resolve_paths
    file = tmp_path / 'file'
    file.write_text('x')
    with pytest.raises(ValueError):
        resolve_paths(file)
