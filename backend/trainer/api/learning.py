from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from trainer.content.loader import load_problem, public_problem


class NicknameBody(BaseModel):
    nickname: str = Field(max_length=100)


class ProfileBody(BaseModel):
    profile_id: str


class DraftBody(BaseModel):
    sql: str = Field(max_length=20000)
    revision: int = Field(ge=1)


class SavedBody(BaseModel):
    name: str = Field(max_length=60)
    sql: str = Field(max_length=20000)


class HintBody(ProfileBody):
    level: int = Field(ge=0,le=1)


def learning_router(store,paths):
    router=APIRouter(prefix='/api')

    @router.post('/profiles')
    def create_profile(body:NicknameBody):
        profile=store.create_profile(body.nickname)
        store.select_profile(profile['id'])
        return profile

    @router.post('/profiles/{pid}/select')
    def select_profile(pid:str):
        store.select_profile(pid)
        return {'ok':True}

    @router.get('/profiles/{pid}/progress')
    def progress(pid:str): return store.progress(pid)

    def check_scope(scope):
        if scope!='lab': load_problem(paths.content,scope)

    @router.get('/profiles/{pid}/drafts/{scope}')
    def draft(pid:str,scope:str):
        check_scope(scope)
        return store.get_draft(pid,scope)

    @router.put('/profiles/{pid}/drafts/{scope}')
    def save_draft(pid:str,scope:str,body:DraftBody):
        check_scope(scope)
        return store.save_draft(pid,scope,body.sql,body.revision)

    @router.get('/problems/{problem_id}')
    def problem(problem_id:str): return public_problem(load_problem(paths.content,problem_id))

    @router.post('/problems/{problem_id}/hint')
    def hint(problem_id:str,body:HintBody):
        store.require_profile(body.profile_id)
        return {'hint':load_problem(paths.content,problem_id)['hints'][body.level]}

    @router.post('/problems/{problem_id}/answer')
    def answer(problem_id:str,body:ProfileBody):
        problem=load_problem(paths.content,problem_id)
        store.reveal_answer(body.profile_id,problem_id)
        return {'sql':problem['answer_sql']}

    @router.get('/profiles/{pid}/history')
    def history(pid:str,offset:int=0): return store.history(pid,offset)

    @router.get('/profiles/{pid}/saved')
    def saved(pid:str): return store.saved_queries(pid)

    @router.post('/profiles/{pid}/saved')
    def save_query(pid:str,body:SavedBody): return store.save_query(pid,body.name,body.sql)

    return router
