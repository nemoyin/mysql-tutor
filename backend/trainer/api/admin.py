from dataclasses import asdict
from fastapi import APIRouter
from pydantic import BaseModel
from trainer.contracts import RuntimeState
from trainer.runtime.bootstrap import restore_dataset


class ConfirmationBody(BaseModel):
    confirmation:str=''


def admin_router(store,manager,app):
    router=APIRouter(prefix='/api')

    @router.post('/admin/restore')
    def restore(body:ConfirmationBody):
        if body.confirmation!='restore-training': raise ValueError('请先确认恢复练习数据。')
        if manager is None: raise ValueError('数据库未就绪。')
        with manager.operation_lock:
            manager._state=RuntimeState('restoring',manager.port,'正在恢复练习数据…')
            marker=manager.paths.root/'data/restore-in-progress'
            marker.write_text('恢复中',encoding='utf-8')
            try:
                restore_dataset(manager)
                marker.unlink(missing_ok=True)
                manager._state=RuntimeState('ready',manager.port,'练习数据已恢复')
            except Exception:
                manager._state=RuntimeState('restore_failed',manager.port,'恢复未完成，请再次恢复练习数据。')
                raise
        return asdict(manager.state())

    @router.post('/profiles/{pid}/reset-progress')
    def reset(pid:str,body:ConfirmationBody):
        if body.confirmation!='reset-progress': raise ValueError('请先确认重置学习进度。')
        store.reset_progress(pid)
        return {'ok':True}

    @router.post('/admin/shutdown')
    def shutdown(body:ConfirmationBody):
        if body.confirmation!='shutdown': raise ValueError('请先确认退出工具。')
        callback=getattr(app.state,'shutdown_callback',None)
        if callback: callback()
        return {'ok':True,'message':'工具正在关闭，可关闭此页面。'}

    return router
