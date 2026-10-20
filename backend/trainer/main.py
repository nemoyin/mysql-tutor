import argparse
import logging
from pathlib import Path
import sys
import threading
import webbrowser

import uvicorn
from trainer.config import resolve_paths
from trainer.contracts import RuntimeState
from trainer.runtime.manager import RuntimeManager, choose_port
from trainer.runtime.bootstrap import seed_dataset
from trainer.api.app import create_app


def main():
    parser=argparse.ArgumentParser(description='SQL 学习工坊 — 离线 MySQL 培训')
    default=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[2]
    parser.add_argument('--root',type=Path,default=default)
    parser.add_argument('--port',type=int,default=18765)
    parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args()
    paths=resolve_paths(args.root)
    (paths.root/'data/logs').mkdir(parents=True,exist_ok=True)
    logging.basicConfig(filename=paths.root/'data/logs/app.log',encoding='utf-8',level=logging.INFO)
    manager=RuntimeManager(paths)
    app=create_app(paths,manager)
    port=choose_port(args.port)
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning',log_config=None))
    app.state.shutdown_callback=lambda:setattr(server,'should_exit',True)

    def prepare():
        try:
            manager.start()
            manager._state=RuntimeState('seeding',manager.port,'正在准备课程数据…')
            marker=paths.root/'data/restore-in-progress'
            with manager.connect(admin=True) as conn: seed_dataset(conn,force=marker.exists())
            marker.unlink(missing_ok=True)
            manager._state=RuntimeState('ready',manager.port,'数据库已就绪')
        except Exception as error:
            logging.exception('Database preparation failed')
            manager._state=RuntimeState('failed',manager.port,str(error))

    worker=threading.Thread(target=prepare,daemon=True)
    worker.start()
    if not args.no_browser:
        threading.Timer(1,lambda:webbrowser.open(f'http://127.0.0.1:{port}')).start()
    try:
        server.run()
    finally:
        worker.join(timeout=130)
        manager.stop()


if __name__=='__main__': main()
