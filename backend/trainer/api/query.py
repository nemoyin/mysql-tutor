from dataclasses import asdict
from fastapi import APIRouter
from pydantic import BaseModel, Field
from trainer.content.loader import load_problem,load_catalog
from trainer.contracts import QueryFailure
from trainer.grading.service import grade_submission
from trainer.query.executor import QueryExecutor
from trainer.query.policy import TABLES


class RunBody(BaseModel):
    profile_id:str
    scope:str='lab'
    sql:str=Field(max_length=20000)


def query_router(store,paths,manager):
    router=APIRouter(prefix='/api')
    executor=QueryExecutor(manager) if manager else None

    def require_ready():
        if executor is None or manager.state().phase!='ready':
            raise QueryFailure('not_ready','数据库未就绪','数据库正在准备或恢复，请稍后重试。')

    @router.get('/catalog')
    def catalog(): return load_catalog()

    @router.get('/catalog/{table}/sample')
    def sample(table:str):
        if table not in TABLES: raise ValueError('表不存在。')
        require_ready()
        return asdict(executor.execute_query(f'SELECT * FROM {table} LIMIT 10'))

    @router.post('/query/run')
    def run(body:RunBody):
        store.require_profile(body.profile_id)
        if body.scope!='lab': load_problem(paths.content,body.scope)
        require_ready()
        try:
            result=executor.execute_query(body.sql)
        except QueryFailure:
            store.add_history(body.profile_id,body.scope,body.sql,'error')
            raise
        store.add_history(body.profile_id,body.scope,body.sql,'ok')
        return asdict(result)

    @router.post('/problems/{problem_id}/submit')
    def submit(problem_id:str,body:RunBody):
        store.require_profile(body.profile_id)
        problem=load_problem(paths.content,problem_id)
        require_ready()
        result=grade_submission(executor,problem,body.sql)
        store.record_grade(body.profile_id,problem_id,result.status)
        store.add_history(body.profile_id,problem_id,body.sql,result.status)
        return asdict(result)

    return router
