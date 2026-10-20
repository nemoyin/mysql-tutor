from pathlib import Path
import json


DATASET = Path(__file__).resolve().parents[1] / 'dataset'


def seed_dataset(connection, force=False):
    with connection.cursor() as cur:
        if force:
            cur.execute('DROP DATABASE IF EXISTS training')
        cur.execute('CREATE DATABASE IF NOT EXISTS training CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci')
        cur.execute('USE training')
        cur.execute("SHOW TABLES LIKE 'dataset_version'")
        if cur.fetchone():
            return
        for file in ('schema.sql', 'seed.sql'):
            for statement in (DATASET / file).read_text(encoding='utf-8').split(';'):
                if statement.strip():
                    cur.execute(statement)
        cur.execute('CREATE TABLE dataset_version (version INT NOT NULL)')
        cur.execute('INSERT INTO dataset_version VALUES (1)')


def restore_dataset(manager):
    with manager.operation_lock:
        with manager.connect(admin=True) as conn:
            seed_dataset(conn, force=True)
    return manager.state()
