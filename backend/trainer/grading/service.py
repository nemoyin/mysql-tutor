from trainer.contracts import GradeResult
from trainer.query.policy import validate_query
from trainer.grading.compare import compare_results


def grade_submission(executor, problem: dict, sql: str) -> GradeResult:
    query = validate_query(sql)
    nodes = {type(node).__name__ for node in query.ast.walk()}
    for required in problem.get('required_constructs', []):
        if required not in nodes:
            return GradeResult('incorrect', '本题需要使用指定的知识点，请查看题目要求与提示。')
    actual = executor.execute_query(sql, 'grade')
    expected = executor.execute_query(problem['answer_sql'], 'grade')
    return compare_results(actual, expected, problem)
