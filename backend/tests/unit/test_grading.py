from trainer.contracts import QueryResult, ColumnMeta
import pytest


def result(rows, kind='integer', truncated=False):
    return QueryResult([ColumnMeta('n',kind)],rows,len(rows),truncated)


@pytest.mark.parametrize('actual,expected,ordered,status,kind',[
    ([[2],[1]],[[1],[2]],False,'passed','integer'),
    ([[1],[1]],[[1],[2]],False,'incorrect','integer'),
    ([[2],[1]],[[1],[2]],True,'incorrect','integer'),
    ([[None]],[['']],False,'incorrect','text'),
])
def test_rows_null_duplicates_and_order(actual,expected,ordered,status,kind):
    from trainer.grading.compare import compare_results
    assert compare_results(result(actual,kind),result(expected,kind),{'compare_order':ordered}).status == status


def test_decimal_scale_normalized():
    from trainer.grading.compare import compare_results
    assert compare_results(result([['10.0']],'decimal'),result([['10.00']],'decimal'),{}).status == 'passed'


def test_truncated_grade_is_ungraded():
    from trainer.grading.compare import compare_results
    assert compare_results(result([[1]],truncated=True),result([[1]]),{}).status == 'ungraded'


def test_numeric_value_not_same_as_text():
    from trainer.grading.compare import compare_results
    assert compare_results(result([['1']],'text'),result([[1]]),{}).status == 'incorrect'
