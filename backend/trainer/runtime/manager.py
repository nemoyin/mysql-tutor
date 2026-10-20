import json
import os
import secrets
import socket
import subprocess
import time
import threading
import hashlib
import tempfile
from pathlib import Path

import pymysql
from trainer.config import RuntimePaths
from trainer.contracts import RuntimeState

HIDDEN = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
SQL_MODE = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'


def mysql_compatible_root(root: Path) -> Path:
    """MySQL's Windows argument parser requires an ASCII alias for Unicode paths."""
    if os.name != 'nt' or str(root).isascii():
        return root
    parent = Path(tempfile.gettempdir()) / 'mysql-training-paths'
    if not str(parent).isascii():
        raise RuntimeError('系统临时目录包含中文，请将工具解压到纯英文目录。')
    parent.mkdir(exist_ok=True)
    alias = parent / hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:20]
    if alias.exists():
        if alias.resolve() != root.resolve():
            raise RuntimeError('数据库路径映射冲突，请联系维护人员。')
    else:
        result = subprocess.run(['cmd.exe', '/c', 'mklink', '/J', str(alias), str(root)],
                                capture_output=True, creationflags=HIDDEN)
        if result.returncode:
            raise RuntimeError('无法创建中文目录兼容映射，请将工具解压到纯英文目录。')
    return alias


def choose_port(preferred: int) -> int:
    with socket.socket() as sock:
        try:
            sock.bind(('127.0.0.1', preferred))
        except OSError:
            sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def ensure_writable(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / f'.write-{secrets.token_hex(4)}'
        probe.write_text('ok')
        probe.unlink()
    except OSError as error:
        raise RuntimeError('此目录无法写入，请将工具解压到有写入权限的文件夹。') from error


class RuntimeManager:
    def __init__(self, paths: RuntimePaths):
        self.paths = paths
        self.process = None
        self.port = None
        self._log = None
        self._lock_file = None
        self._state = RuntimeState('stopped')
        self.operation_lock = threading.RLock()
        self.config = {}

    def state(self):
        return self._state

    def _acquire(self):
        if os.name == 'nt':
            import msvcrt
            self._lock_file = open(self.paths.root / 'data/instance.lock', 'a+b')
            self._lock_file.seek(0)
            if not self._lock_file.read(1):
                self._lock_file.write(b'0')
                self._lock_file.flush()
            self._lock_file.seek(0)
            try:
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                self._lock_file.close()
                self._lock_file = None
                raise RuntimeError('工具已在运行，请使用已打开的学习页面。')

    def _release(self):
        if self._lock_file:
            import msvcrt
            self._lock_file.seek(0)
            msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            self._lock_file.close()
            self._lock_file = None

    def connect(self, admin=False, database=None):
        return pymysql.connect(host='127.0.0.1', port=self.port,
            user='root' if admin else 'learner',
            password=self.config['admin_password' if admin else 'reader_password'],
            database=database, charset='utf8mb4', autocommit=True,
            connect_timeout=3, read_timeout=8, write_timeout=8,
            init_command="SET time_zone = '+08:00'")

    def start(self) -> RuntimeState:
        if self.process and self.process.poll() is None:
            return self._state
        if not self.paths.mysql_bin.is_file():
            raise RuntimeError('缺少随包携带的 MySQL 运行文件，请重新解压完整工具包。')
        ensure_writable(self.paths.root / 'data')
        self._acquire()
        try:
            self._start_owned()
        except Exception:
            self.stop()
            raise
        return self._state

    def _start_owned(self):
        data = self.paths.root / 'data'
        alias = mysql_compatible_root(self.paths.root)
        mysql_bin = alias / 'runtime/mysql/bin/mysqld.exe'
        (data / 'logs').mkdir(exist_ok=True)
        config_file = data / 'instance.json'
        if config_file.exists():
            self.config = json.loads(config_file.read_text(encoding='utf-8'))
        else:
            self.config = dict(admin_password=secrets.token_hex(24), reader_password=secrets.token_hex(24), initialized=False)
            config_file.write_text(json.dumps(self.config), encoding='utf-8')
        initialized = (self.paths.mysql_data / 'auto.cnf').exists()
        if not initialized:
            self._state = RuntimeState('initializing', message='首次使用，正在准备数据库…')
            staging = data / 'mysql-initializing'
            if staging.exists():
                staging.rename(data / f'mysql-interrupted-{time.time_ns()}')
            args = [str(mysql_bin), '--no-defaults', '--initialize-insecure',
                    f'--basedir={alias / "runtime/mysql"}', f'--datadir={alias / "data/mysql-initializing"}']
            result = subprocess.run(args, capture_output=True, creationflags=HIDDEN, timeout=120)
            if result.returncode:
                (data / 'logs/initialize.log').write_bytes(result.stderr)
                raise RuntimeError('MySQL 初始化失败，请检查 data/logs/initialize.log。')
            if self.paths.mysql_data.exists():
                raise RuntimeError('数据目录不完整，请保留目录并联系维护人员。')
            staging.rename(self.paths.mysql_data)
        self.port = choose_port(13306)
        self._log = open(data / 'logs/mysql.log', 'ab')
        args = [str(mysql_bin), '--no-defaults',
            f'--basedir={alias / "runtime/mysql"}', f'--datadir={alias / "data/mysql"}',
            '--bind-address=127.0.0.1', f'--port={self.port}', '--mysqlx=OFF',
            '--character-set-server=utf8mb4', '--collation-server=utf8mb4_0900_ai_ci',
            f'--sql-mode={SQL_MODE}', '--default-time-zone=+08:00',
            '--innodb-buffer-pool-size=64M', '--max-connections=20', '--local-infile=OFF',
            '--secure-file-priv=NULL', '--skip-log-bin', '--console']
        self.process = subprocess.Popen(args, stdout=self._log, stderr=self._log, creationflags=HIDDEN)
        deadline = time.monotonic() + 60
        connection = None
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError('MySQL 启动失败，请检查 data/logs/mysql.log。')
            try:
                try:
                    connection = self.connect(admin=True)
                except pymysql.err.OperationalError as error:
                    if error.args[0] == 1045 and not self.config['initialized']:
                        connection = pymysql.connect(host='127.0.0.1', port=self.port, user='root', password='', autocommit=True)
                    else:
                        raise
                break
            except pymysql.err.OperationalError:
                time.sleep(.2)
        if connection is None:
            raise RuntimeError('等待数据库启动超时，可退出工具后重试。')
        with connection as conn:
            with conn.cursor() as cur:
                cur.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s", (self.config['admin_password'],))
                cur.execute("CREATE USER IF NOT EXISTS 'learner'@'127.0.0.1' IDENTIFIED BY %s", (self.config['reader_password'],))
                cur.execute("GRANT SELECT ON training.* TO 'learner'@'127.0.0.1'")
        self.config['initialized'] = True
        config_file.write_text(json.dumps(self.config), encoding='utf-8')
        self._state = RuntimeState('ready', self.port, '数据库已就绪')

    def stop(self):
        if self.process and self.process.poll() is None:
            try:
                with self.connect(admin=True) as conn:
                    with conn.cursor() as cur:
                        cur.execute('SHUTDOWN')
                self.process.wait(timeout=15)
            except Exception:
                # Only this object's live child handle can be terminated, never a PID read from disk.
                self.process.terminate()
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
        self.process = None
        if self._log:
            self._log.close()
            self._log = None
        self._release()
        self._state = RuntimeState('stopped')
