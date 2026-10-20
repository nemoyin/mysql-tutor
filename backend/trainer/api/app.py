import secrets
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from trainer.config import RuntimePaths
from trainer.contracts import QueryFailure
from trainer.learning.store import LearningStore
from trainer.content.loader import load_chapters
from trainer.api.learning import learning_router
from trainer.api.query import query_router
from trainer.api.admin import admin_router


def create_app(paths: RuntimePaths, manager=None) -> FastAPI:
    app = FastAPI(title='SQL 学习工坊', docs_url=None, redoc_url=None)
    app.state.paths = paths
    token=secrets.token_urlsafe(32)
    store=LearningStore(paths.learning_db)

    @app.middleware('http')
    async def local_only(request:Request,call_next):
        host=request.headers.get('host','').split(':')[0]
        if host not in ('127.0.0.1','localhost','testserver'):
            return JSONResponse({'message':'仅支持本机访问'},status_code=403)
        if request.method not in ('GET','HEAD','OPTIONS'):
            origin=request.headers.get('origin')
            if (origin and origin != f'http://{request.headers.get("host")}') or request.headers.get('x-local-token')!=token:
                return JSONResponse({'message':'本地会话已失效，请刷新页面重试。'},status_code=403)
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Cache-Control']='no-store' if request.url.path.startswith('/api') else 'no-cache'
        return response

    @app.exception_handler(ValueError)
    async def bad_value(request,error):
        return JSONResponse({'code':'invalid_input','message':str(error)},status_code=400)

    @app.exception_handler(QueryFailure)
    async def query_failure(request,error):
        return JSONResponse({'code':error.code,'message':error.explanation,'details':error.payload()},status_code=400)

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'version': '0.1.0'}

    @app.get('/api/bootstrap')
    def bootstrap():
        chapters=load_chapters(paths.content)
        return dict(token=token,profiles=store.profiles(),last_profile=store.last_profile(),
                    chapters=[{**{k:v for k,v in c.items() if k!='problems'},'problems':[dict(id=p['id'],title=p['title']) for p in c['problems']]} for c in chapters],
                    runtime=manager.state().__dict__ if manager else {'phase':'stopped'})

    app.include_router(learning_router(store,paths))
    app.include_router(query_router(store,paths,manager))
    app.include_router(admin_router(store,manager,app))
    web=paths.web if paths.web.is_dir() else paths.root/'frontend/dist'
    if (web/'assets').is_dir(): app.mount('/assets',StaticFiles(directory=web/'assets'),name='assets')

    @app.get('/')
    def index():
        if (web/'index.html').exists(): return FileResponse(web/'index.html')
        return JSONResponse({'message':'学习页面尚未构建，请先构建前端。'})

    return app
