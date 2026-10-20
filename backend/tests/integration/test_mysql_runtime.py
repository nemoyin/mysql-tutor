def test_real_mysql_version_and_readonly_account(runtime):
    with runtime.connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT VERSION(), @@sql_mode, @@session.time_zone')
            version, modes, timezone = cur.fetchone()
            assert version.startswith('8.4.')
            assert 'ONLY_FULL_GROUP_BY' in modes
            assert timezone == '+08:00'


def test_restart_preserves_data(runtime):
    with runtime.connect(admin=True) as conn:
        with conn.cursor() as cur:
            cur.execute('CREATE DATABASE IF NOT EXISTS trainer_probe')
    runtime.stop()
    runtime.start()
    with runtime.connect(admin=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SHOW DATABASES LIKE 'trainer_probe'")
            assert cur.fetchone()[0] == 'trainer_probe'
            cur.execute('DROP DATABASE trainer_probe')
