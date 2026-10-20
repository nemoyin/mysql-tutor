from trainer.contracts import QueryFailure

EXPLANATIONS = {
    1054: '找不到这个字段，请对照右侧表结构检查字段名或表别名。',
    1064: 'SQL 语法有误，请检查关键字、逗号、括号和引号。',
    1146: '找不到这张表，请检查表名。',
    1055: '分组查询中，非聚合字段需要与 GROUP BY 的分组规则一致。',
    1052: '字段名不明确，请加上表名或表别名。',
    1142: '练习区仅允许读取电商数据，不能修改数据。',
    3024: '查询超过时间限制，请检查关联条件或减少参与计算的数据。',
    2013: '查询连接中断，请检查查询规模后重试。',
}


def mysql_failure(error):
    number = error.args[0] if error.args and isinstance(error.args[0], int) else None
    return QueryFailure('mysql_error', str(error), EXPLANATIONS.get(number, 'MySQL 返回错误，请参考下方原始信息。'), number)
