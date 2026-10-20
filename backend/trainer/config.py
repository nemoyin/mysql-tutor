from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    mysql_bin: Path
    mysql_data: Path
    learning_db: Path
    content: Path
    web: Path


def resolve_paths(root: Path) -> RuntimePaths:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError('工具目录不存在或不是文件夹')
    return RuntimePaths(root, root / 'runtime/mysql/bin/mysqld.exe',
                        root / 'data/mysql', root / 'data/learning.sqlite3',
                        root / 'content', root / 'web')
