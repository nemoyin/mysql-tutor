# SQL 学习工坊

Windows 单机离线 MySQL 查询培训工具。真实 MySQL 8.4、8 章 40 道题、电商固定数据、引导式学习、自由实验室、本地学员及进度。

产品使用请读 [使用说明](docs/user-guide.md)，开发范围见 [设计](docs/superpowers/specs/2026-10-20-mysql-training-design.md) 和 [实施计划](docs/superpowers/plans/2026-10-20-mysql-training-implementation.md)。

## 开发启动

Python 3.12 x64、Node.js 22。先建立 `.venv`，安装 `requirements.lock`；在 `frontend` 中运行 `npm ci` 和 `npm run build`；运行 `python scripts/fetch_runtime.py` 校验并准备固定 MySQL ZIP。

PowerShell：

```powershell
$env:PYTHONPATH='backend'
.venv/Scripts/python.exe -m trainer.main
```

工具仅监听本机，不修改系统 MySQL。浏览器关闭后后台仍运行，请使用工具设置中的退出入口。

## 测试与构建

```powershell
.venv/Scripts/python.exe -m pytest -q
npm --prefix frontend run test -- --run
npm --prefix frontend run build
$env:NODE_PATH=(Resolve-Path frontend/node_modules).Path
frontend/node_modules/.bin/playwright.cmd test --config frontend/playwright.config.ts
.venv/Scripts/python.exe scripts/verify_content.py
.venv/Scripts/python.exe scripts/build_distribution.py
```

浏览器测试需先启动工具；默认使用本机 Chrome。测试数据库使用单独临时目录，独立于开发预览数据。发布包输出在 `dist/`，不带开发环境和测试学员数据。

严格按测试先行推进，过程及决策见 [开发记录](docs/implementation-ledger.md)。跨干净系统的未验证项目见 [验收记录](docs/acceptance.md)。
