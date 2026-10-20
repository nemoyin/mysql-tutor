def test_seed_is_deterministic_and_relations_valid(runtime):
    from trainer.runtime.bootstrap import seed_dataset
    from trainer.content.loader import load_catalog
    with runtime.connect(admin=True) as conn:
        seed_dataset(conn)
        with conn.cursor() as cur:
            for table, count in [('customers',30),('categories',6),('products',40),('orders',120),('order_items',300)]:
                cur.execute(f'SELECT COUNT(*) FROM training.{table}')
                assert cur.fetchone()[0] == count
            cur.execute('SELECT COUNT(*) FROM training.customers c LEFT JOIN training.orders o ON c.customer_id=o.customer_id WHERE o.order_id IS NULL')
            assert cur.fetchone()[0] == 6
            cur.execute('SELECT COUNT(*) FROM training.products p LEFT JOIN training.order_items i ON p.product_id=i.product_id WHERE i.order_id IS NULL')
            assert cur.fetchone()[0] == 4
            cur.execute('SELECT SUM(quantity*unit_price) FROM training.order_items WHERE order_id=1')
            assert str(cur.fetchone()[0]) == '79.80'
        seed_dataset(conn)  # Repeat seeding must not duplicate rows.
    assert len(load_catalog()) == 5
