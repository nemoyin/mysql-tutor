# SDD ledger — plan: docs/superpowers/plans/2026-10-20-mysql-training-implementation.md

执行方式：当前会话顺序实施，TDD。用户已授权。

Ruling: 当前目录是只有设计文档的新项目，按已批准计划在原目录建立 feature/offline-mysql-training 分支，不创建额外工作树 — 没有需要保护的现有产品代码，保持交付位置一致。

Ruling: 默认沙箱在 Git 初始化后出现 helper_unknown_error，连 Get-Location 也失败；使用经自动审批的终端执行，在原项目目录建立隔离环境，不更改系统 MySQL。

Ruling: 技能辅助脚本是 shell 脚本；Windows 下使用本文件和原生操作记录等价的任务、测试和决策，不引入第二套 shell 运行依赖。

Pre-flight: Task 1→2 路径对象一致；2→3 初始化接口需要在数据库创建后再播种；3→4 表名固定；4→5 预览与判题限额分离；5→6 完成状态由服务端判题写入；6→8 草稿 revision 冲突由 API 明确返回；2/3→9 恢复仅重建练习 schema；1–9→10 发行包根路径不能依赖源码位置。

Task 1: in progress — 先验证健康接口及目录约束。

Task 1: complete — 2 tests RED→GREEN，frontend build PASS。使用本地分支，已提交基础代码。
Task 2: 核心启动/重启已验证 — 4 单元测试及 2 真实 MySQL 测试通过；Windows 中文命令行导致初始启动失败，新增兼容路径测试 RED→GREEN 后修复。其他故障注入测试继续补齐。
Ruling: Windows MySQL 8.4.11 在中文命令行参数中截断路径；使用系统临时目录的 ASCII junction 指向原工具目录，所有实际数据仍在原目录。临时目录也含非 ASCII 时明确提示英文解压路径；不修改既有 MySQL。
Ruling: Git 的沙箱创建者与提升后执行身份不同，使用每次命令级 safe.directory，不修改全局 Git 配置。初次提交为开发中快照，并不代表当时数据库测试通过；后续 9/9 测试已经转绿。
Task 3: complete — 固定数据 30/6/40/120/300，订单 1 金额 79.80 手工期望验证，6 位未下单客户与 4 件未售出商品，9 tests PASS。
