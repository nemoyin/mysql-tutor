from contextlib import contextmanager
from pathlib import Path
import sqlite3
import unicodedata
import uuid


class LearningStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.db() as conn:
            conn.executescript('''
            CREATE TABLE IF NOT EXISTS profiles(id TEXT PRIMARY KEY,nickname TEXT NOT NULL,nickname_key TEXT UNIQUE NOT NULL,last_scope TEXT);
            CREATE TABLE IF NOT EXISTS drafts(profile_id TEXT,scope TEXT,sql TEXT NOT NULL,revision INTEGER NOT NULL,PRIMARY KEY(profile_id,scope));
            CREATE TABLE IF NOT EXISTS progress(profile_id TEXT,problem_id TEXT,answer_seen INTEGER NOT NULL DEFAULT 0,mode TEXT,attempts INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(profile_id,problem_id));
            CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY AUTOINCREMENT,profile_id TEXT,scope TEXT,sql TEXT,status TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS saved_queries(id TEXT PRIMARY KEY,profile_id TEXT,name TEXT,sql TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
            PRAGMA user_version=1;
            ''')

    @contextmanager
    def db(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def require_profile(self, profile_id):
        with self.db() as conn:
            if not conn.execute('SELECT 1 FROM profiles WHERE id=?',(profile_id,)).fetchone():
                raise ValueError('学员档案不存在，请重新选择。')

    def profiles(self):
        with self.db() as conn:
            return [dict(row) for row in conn.execute('SELECT id,nickname,last_scope FROM profiles ORDER BY rowid')]

    def create_profile(self, nickname):
        nickname = unicodedata.normalize('NFKC', nickname).strip()
        if not 1 <= len(nickname) <= 30:
            raise ValueError('请输入 1–30 个字符的姓名或昵称。')
        profile = dict(id=str(uuid.uuid4()), nickname=nickname)
        try:
            with self.db() as conn:
                conn.execute('INSERT INTO profiles(id,nickname,nickname_key) VALUES (?,?,?)',
                             (profile['id'],nickname,nickname.casefold()))
        except sqlite3.IntegrityError as error:
            raise ValueError('这个昵称已有档案，请选择已有档案或换一个昵称。') from error
        return profile

    def select_profile(self, profile_id):
        self.require_profile(profile_id)
        with self.db() as conn:
            conn.execute("INSERT INTO settings VALUES ('last_profile',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(profile_id,))

    def last_profile(self):
        with self.db() as conn:
            row=conn.execute("SELECT value FROM settings WHERE key='last_profile'").fetchone()
            return row[0] if row else None

    def get_draft(self, profile_id, scope):
        self.require_profile(profile_id)
        with self.db() as conn:
            row=conn.execute('SELECT sql,revision FROM drafts WHERE profile_id=? AND scope=?',(profile_id,scope)).fetchone()
            return dict(row) if row else dict(sql='',revision=0)

    def save_draft(self, profile_id, scope, sql, revision):
        self.require_profile(profile_id)
        if len(sql)>20000 or revision<1: raise ValueError('草稿内容过长或版本无效。')
        with self.db() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row=conn.execute('SELECT sql,revision FROM drafts WHERE profile_id=? AND scope=?',(profile_id,scope)).fetchone()
            if row and (revision < row['revision'] or (revision==row['revision'] and sql!=row['sql'])):
                raise ValueError('草稿已有更新版本，请重新加载后恢复编辑。')
            conn.execute('INSERT INTO drafts VALUES (?,?,?,?) ON CONFLICT(profile_id,scope) DO UPDATE SET sql=excluded.sql,revision=excluded.revision',(profile_id,scope,sql,revision))
            conn.execute('UPDATE profiles SET last_scope=? WHERE id=?',(scope,profile_id))
        return dict(sql=sql,revision=revision)

    def reveal_answer(self, profile_id, problem_id):
        self.require_profile(profile_id)
        with self.db() as conn:
            conn.execute('INSERT INTO progress(profile_id,problem_id,answer_seen) VALUES (?,?,1) ON CONFLICT(profile_id,problem_id) DO UPDATE SET answer_seen=1',(profile_id,problem_id))

    def record_grade(self, profile_id, problem_id, status):
        self.require_profile(profile_id)
        with self.db() as conn:
            conn.execute('INSERT OR IGNORE INTO progress(profile_id,problem_id) VALUES (?,?)',(profile_id,problem_id))
            conn.execute('UPDATE progress SET attempts=attempts+1 WHERE profile_id=? AND problem_id=?',(profile_id,problem_id))
            if status=='passed':
                conn.execute("UPDATE progress SET mode=COALESCE(mode,CASE WHEN answer_seen=1 THEN 'assisted' ELSE 'independent' END) WHERE profile_id=? AND problem_id=?",(profile_id,problem_id))

    def progress(self, profile_id):
        self.require_profile(profile_id)
        with self.db() as conn:
            return {row['problem_id']:dict(row) for row in conn.execute('SELECT problem_id,answer_seen,mode,attempts FROM progress WHERE profile_id=?',(profile_id,))}

    def add_history(self, profile_id, scope, sql, status):
        self.require_profile(profile_id)
        with self.db() as conn:
            conn.execute('INSERT INTO history(profile_id,scope,sql,status) VALUES (?,?,?,?)',(profile_id,scope,sql,status))
            conn.execute('DELETE FROM history WHERE profile_id=? AND id NOT IN (SELECT id FROM history WHERE profile_id=? ORDER BY id DESC LIMIT 1000)',(profile_id,profile_id))

    def history(self, profile_id, offset=0):
        self.require_profile(profile_id)
        with self.db() as conn:
            return [dict(row) for row in conn.execute('SELECT id,scope,sql,status,created_at FROM history WHERE profile_id=? ORDER BY id DESC LIMIT 30 OFFSET ?',(profile_id,max(0,offset)))]

    def save_query(self, profile_id, name, sql):
        self.require_profile(profile_id)
        if not name.strip() or len(name)>60 or len(sql)>20000: raise ValueError('请填写不超过 60 字的名称，并检查 SQL 长度。')
        item=dict(id=str(uuid.uuid4()),name=name.strip(),sql=sql)
        with self.db() as conn:
            conn.execute('INSERT INTO saved_queries(id,profile_id,name,sql) VALUES (?,?,?,?)',(item['id'],profile_id,item['name'],sql))
        return item

    def saved_queries(self, profile_id):
        self.require_profile(profile_id)
        with self.db() as conn:
            return [dict(row) for row in conn.execute('SELECT id,name,sql,created_at FROM saved_queries WHERE profile_id=? ORDER BY rowid DESC',(profile_id,))]

    def reset_progress(self, profile_id):
        self.require_profile(profile_id)
        with self.db() as conn:
            conn.execute('DELETE FROM progress WHERE profile_id=?',(profile_id,))
            conn.execute('UPDATE profiles SET last_scope=NULL WHERE id=?',(profile_id,))
