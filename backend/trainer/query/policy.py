from dataclasses import dataclass
import sqlglot
from sqlglot import exp
from trainer.contracts import QueryFailure

TABLES = {'customers', 'categories', 'products', 'orders', 'order_items'}
FUNCTIONS = {'COUNT','SUM','AVG','MAX','MIN','ROUND','ABS','COALESCE','IFNULL','NULLIF',
             'CONCAT','CONCAT_WS','LOWER','UPPER','LENGTH','CHAR_LENGTH','SUBSTRING','TRIM',
             'DATE','DATE_FORMAT','YEAR','MONTH','DAY','DAYOFMONTH','DATEDIFF','CAST',
             'CASE','IF','CEIL','CEILING','FLOOR','ISNULL'}


@dataclass
class ValidatedQuery:
    sql: str
    ast: exp.Expression
    referenced_tables: set[str]


def validate_query(sql: str) -> ValidatedQuery:
    def reject(message):
        raise QueryFailure('unsupported_query', message, message)
    if not sql.strip(): reject('请先输入一条 SQL 查询。')
    if len(sql) > 20000: reject('SQL 太长，请将查询控制在 20000 字符以内。')
    try:
        statements = [s for s in sqlglot.parse(sql, read='mysql') if s is not None]
    except sqlglot.errors.ParseError as error:
        raise QueryFailure('syntax_error', str(error), 'SQL 结构无法识别，请检查语法、括号和引号。') from error
    if len(statements) != 1 or not isinstance(statements[0], (exp.Select, exp.Union)):
        reject('第一版仅支持单条 SELECT 查询。')
    tree = statements[0]
    ctes = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    tables = set()
    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        if table.catalog or table.db.lower() not in ('', 'training') or name not in TABLES | ctes:
            reject('仅能查询右侧数据参考中的五张练习表。')
        tables.add(name)
    blocked = {'Into','Lock','Parameter','SessionParameter','PropertyEQ','Assignment',
               'Update','Delete','Insert','Create','Drop','Command','Set','Execute'}
    for node in tree.walk():
        if type(node).__name__ in blocked:
            reject('该操作超出只读练习范围，请使用普通查询。')
        if isinstance(node, exp.Func):
            name = node.name.upper() if isinstance(node, exp.Anonymous) else node.sql_name()
            if name not in FUNCTIONS:
                reject(f'第一版暂不支持函数 {name}。')
    return ValidatedQuery(sql, tree, tables)
