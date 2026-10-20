from fastapi import FastAPI
from trainer.config import RuntimePaths


def create_app(paths: RuntimePaths) -> FastAPI:
    app = FastAPI(title='SQL 学习工坊', docs_url=None, redoc_url=None)
    app.state.paths = paths

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'version': '0.1.0'}

    return app
