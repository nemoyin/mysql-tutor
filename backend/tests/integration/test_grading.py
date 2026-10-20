def test_different_valid_sql_passes(runtime):
    from trainer.grading.service import grade_submission
    from trainer.query.executor import QueryExecutor
    problem = dict(answer_sql='SELECT customer_id FROM customers WHERE city=\'北京\'', compare_order=False)
    result = grade_submission(QueryExecutor(runtime), problem, 'SELECT customer_id FROM customers WHERE city IN (\'北京\')')
    assert result.status == 'passed'


def test_ast_construct_not_keyword_in_comment(runtime):
    from trainer.grading.service import grade_submission
    from trainer.query.executor import QueryExecutor
    problem = dict(answer_sql='SELECT customer_id FROM customers ORDER BY customer_id', required_constructs=['Order'])
    assert grade_submission(QueryExecutor(runtime),problem,'SELECT customer_id FROM customers /* ORDER BY */').status == 'incorrect'
