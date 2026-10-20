from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from trainer.contracts import GradeResult, QueryResult


def compare_results(actual: QueryResult, expected: QueryResult, problem: dict) -> GradeResult:
    if actual.truncated or expected.truncated:
        return GradeResult('ungraded', '结果超过判题限制，请缩小查询范围后再提交。')
    if len(actual.columns) != len(expected.columns):
        return GradeResult('incorrect', '输出字段数量不符合要求，请检查 SELECT 后的字段。')
    if problem.get('check_aliases') and [c.name for c in actual.columns] != [c.name for c in expected.columns]:
        return GradeResult('incorrect', '请按题目要求设置输出字段的别名及顺序。')
    if len(actual.rows) != len(expected.rows):
        return GradeResult('incorrect', f'结果行数不符合要求；当前返回 {len(actual.rows)} 行，请检查筛选或关联条件。')

    def normalize(result):
        def cell(value, kind):
            if value is None: return ('null', None)
            if kind in ('integer','decimal','float'):
                number = Decimal(str(value))
                if 'decimal_places' in problem and problem['decimal_places'] is not None:
                    number = number.quantize(Decimal(1).scaleb(-problem['decimal_places']), rounding=ROUND_HALF_UP)
                return ('number', number)
            return (kind, value)
        return [tuple(cell(v,c.kind) for v,c in zip(row,result.columns)) for row in result.rows]

    left, right = normalize(actual), normalize(expected)
    if problem.get('compare_order'):
        if left != right:
            if Counter(left) == Counter(right):
                return GradeResult('incorrect', '数据正确，但排列顺序不符合要求，请检查 ORDER BY。')
            return GradeResult('incorrect', '结果值或排列顺序不符合要求，请检查查询条件。')
    elif Counter(left) != Counter(right):
        return GradeResult('incorrect', '结果值不符合要求，请检查条件、计算口径或重复行。')
    return GradeResult('passed', '回答正确！可以继续下一道练习。')
