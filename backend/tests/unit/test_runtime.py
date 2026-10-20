from pathlib import Path
import socket
import pytest


def test_occupied_port_uses_another_port():
    from trainer.runtime.manager import choose_port
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
        assert choose_port(port) != port


def test_missing_runtime_has_actionable_error(tmp_path):
    from trainer.config import resolve_paths
    from trainer.runtime.manager import RuntimeManager
    manager = RuntimeManager(resolve_paths(tmp_path))
    with pytest.raises(RuntimeError, match='MySQL'):
        manager.start()
    manager.stop()  # No process owned, must not stop any other database.


def test_readonly_directory_has_actionable_error(tmp_path):
    from trainer.runtime.manager import ensure_writable
    file = tmp_path / 'file'
    file.write_text('x')
    with pytest.raises(RuntimeError, match='写入'):
        ensure_writable(file)
