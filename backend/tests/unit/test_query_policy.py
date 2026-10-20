import pytest


@pytest.mark.parametrize('sql',[
    'SELECT * FROM customers',
    "/*练习*/ SELECT customer_name FROM customers WHERE city='上;海';",
    'SELECT * FROM customers WHERE customer_id IN (SELECT customer_id FROM orders)',
    'SELECT COUNT(*), ROUND(AVG(price),2) FROM products',
])
def test_allows_teaching_queries(sql):
    from trainer.query.policy import validate_query
    assert validate_query(sql).sql == sql


@pytest.mark.parametrize('sql',[
    'UPDATE customers SET city="北京"', 'SELECT 1; SELECT 2',
    "SELECT * INTO OUTFILE 'a.txt' FROM customers", "SELECT LOAD_FILE('a')",
    'SELECT SLEEP(10)', 'SELECT BENCHMARK(1000000,1+1)',
    'SELECT * FROM customers FOR UPDATE','SELECT * FROM mysql.user',
    'SELECT @@version','SELECT @a:=1','SELECT GET_LOCK("x",5)',
    'SELECT * FROM training.customers JOIN information_schema.tables',
])
def test_rejects_outside_supported_readonly_queries(sql):
    from trainer.query.policy import validate_query
    from trainer.contracts import QueryFailure
    with pytest.raises(QueryFailure):
        validate_query(sql)
