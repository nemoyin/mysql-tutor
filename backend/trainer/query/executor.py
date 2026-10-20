from datetime import date, datetime, timedelta
from decimal import Decimal
import time
import pymysql
from pymysql.constants import FIELD_TYPE
from trainer.contracts import QueryResult, ColumnMeta, QueryFailure
from trainer.query.policy import validate_query
from trainer.query.errors import mysql_failure


def column_kind(code):
    if code in (FIELD_TYPE.DECIMAL,FIELD_TYPE.NEWDECIMAL): return 'decimal'
    if code in (FIELD_TYPE.TINY,FIELD_TYPE.SHORT,FIELD_TYPE.LONG,FIELD_TYPE.LONGLONG,FIELD_TYPE.INT24): return 'integer'
    if code in (FIELD_TYPE.FLOAT,FIELD_TYPE.DOUBLE): return 'float'
    if code in (FIELD_TYPE.DATE,FIELD_TYPE.DATETIME,FIELD_TYPE.TIMESTAMP,FIELD_TYPE.TIME): return 'date'
    return 'text'


def wire_value(value):
    if isinstance(value, Decimal): return str(value)
    if isinstance(value, (date,datetime)): return value.isoformat()
    if isinstance(value, timedelta): return str(value)
    if isinstance(value, bytes): return value.decode('utf-8', errors='replace')
    return value


class QueryExecutor:
    def __init__(self, manager, timeout_ms=5000):
        self.manager = manager
        self.timeout_ms = timeout_ms

    def execute_query(self, sql: str, purpose='preview') -> QueryResult:
        validate_query(sql)
        limit = 10000 if purpose == 'grade' else 200
        start = time.monotonic()
        with self.manager.operation_lock:
            try:
                with self.manager.connect(database='training') as conn:
                    with conn.cursor(pymysql.cursors.SSCursor) as cur:
                        cur.execute('SET SESSION MAX_EXECUTION_TIME=%s', (self.timeout_ms,))
                        cur.execute(sql)
                        columns = [ColumnMeta(d[0], column_kind(d[1])) for d in cur.description]
                        rows = []
                        size = 0
                        for _ in range(limit + 1):
                            row = cur.fetchone()
                            if row is None: break
                            values = [wire_value(v) for v in row]
                            size += sum(len(str(v)) for v in values)
                            if size > 2_000_000:
                                raise QueryFailure('result_too_large', '结果过大', '结果超过展示限制，请减少字段或使用筛选条件。')
                            rows.append(values)
                        truncated = len(rows) > limit
                        # Closing an unbuffered cursor drains remaining results; server timeout bounds it.
                        return QueryResult(columns, rows[:limit], None if truncated else len(rows), truncated, int((time.monotonic()-start)*1000))
            except pymysql.MySQLError as error:
                raise mysql_failure(error) from error
