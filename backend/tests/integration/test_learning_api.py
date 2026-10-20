from dataclasses import replace
from fastapi.testclient import TestClient


def test_learning_api_does_not_leak_answers_and_records_progress(tmp_path,runtime):
    from trainer.api.app import create_app
    paths=replace(runtime.paths,learning_db=tmp_path/'learning.db')
    with TestClient(create_app(paths,manager=runtime),base_url='http://127.0.0.1') as client:
        bootstrap=client.get('/api/bootstrap').json()
        headers={'X-Local-Token':bootstrap['token']}
        assert client.post('/api/profiles',json={'nickname':'甲'}).status_code==403
        profile=client.post('/api/profiles',json={'nickname':'甲'},headers=headers).json()
        pid=profile['id']
        problem=client.get('/api/problems/01-01').json()
        assert 'answer_sql' not in problem and 'hints' not in problem
        assert client.post('/api/problems/01-01/submit',json={'profile_id':pid,'sql':'SELECT * FROM customers'},headers=headers).json()['status']=='passed'
        assert client.get(f'/api/profiles/{pid}/progress').json()['01-01']['mode']=='independent'
        assert client.post('/api/query/run',json={'profile_id':pid,'scope':'lab','sql':"UPDATE customers SET city='北京'"},headers=headers).status_code==400


def test_restore_and_reset_have_distinct_effects(tmp_path,runtime):
    from trainer.api.app import create_app
    paths=replace(runtime.paths,learning_db=tmp_path/'learning.db')
    with TestClient(create_app(paths,manager=runtime),base_url='http://127.0.0.1') as client:
        headers={'X-Local-Token':client.get('/api/bootstrap').json()['token']}
        pid=client.post('/api/profiles',json={'nickname':'甲'},headers=headers).json()['id']
        client.put(f'/api/profiles/{pid}/drafts/01-01',json={'sql':'SELECT * FROM customers','revision':1},headers=headers)
        client.post('/api/problems/01-01/answer',json={'profile_id':pid},headers=headers)
        client.post('/api/problems/01-01/submit',json={'profile_id':pid,'sql':'SELECT * FROM customers'},headers=headers)
        assert client.post('/api/admin/restore',json={},headers=headers).status_code==400
        assert client.post('/api/admin/restore',json={'confirmation':'restore-training'},headers=headers).status_code==200
        assert client.get(f'/api/profiles/{pid}/progress').json()['01-01']['mode']=='assisted'
        client.post(f'/api/profiles/{pid}/reset-progress',json={'confirmation':'reset-progress'},headers=headers)
        assert client.get(f'/api/profiles/{pid}/progress').json()=={}
        assert client.get(f'/api/profiles/{pid}/drafts/01-01').json()['sql']=='SELECT * FROM customers'
