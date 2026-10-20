import pytest
from trainer.contracts import QueryFailure


def test_preview_is_marked_truncated(runtime):
    from trainer.query.executor import QueryExecutor
    result = QueryExecutor(runtime).execute_query('SELECT * FROM order_items', 'preview')
    assert len(result.rows) == 200
    assert result.truncated
    assert result.total_rows is None


def test_readonly_account_cannot_write(runtime):
    import pymysql
    with runtime.connect(database='training') as conn:
        with conn.cursor() as cur:
            with pytest.raises(pymysql.MySQLError):
                cur.execute("UPDATE customers SET city='北京' WHERE customer_id=1")


def test_mysql_error_includes_chinese_explanation(runtime):
    from trainer.query.executor import QueryExecutor
    with pytest.raises(QueryFailure) as failure:
        QueryExecutor(runtime).execute_query('SELECT unknown_column FROM customers')
    assert failure.value.mysql_errno == 1054
    assert '字段' in failure.value.explanation


def test_timeout_then_next_query_works(runtime):
    from trainer.query.executor import QueryExecutor
    executor = QueryExecutor(runtime, timeout_ms=20)
    with pytest.raises(QueryFailure):
        executor.execute_query('SELECT SUM(a.quantity+b.quantity+c.quantity+d.quantity) FROM order_items a CROSS JOIN order_items b CROSS JOIN order_items c CROSS JOIN order_items d')
    assert executor.execute_query('SELECT 1').rows == [[1]]
