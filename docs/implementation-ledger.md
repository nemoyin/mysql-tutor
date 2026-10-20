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

Task 4: complete — SQL 支持范围与真实执行测试 RED→GREEN；只读账号不能写、预览截断、MySQL 中文反馈、超时后下一查询成功。
Ruling: COUNT 笛卡尔积被 MySQL 优化为快速计数，超时测试改用依赖每一行的 SUM 表达式，保证实际触发执行时间限制。
Task 5: complete — 结果比较、重复行、NULL、精度、排序、截断与 AST 语法要求测试 RED→GREEN；等价查询可通过。
Task 6: complete — 档案、草稿隔离、保存版本、查看答案记录及 API 测试 RED→GREEN。学习数据保存在独立 SQLite，真实 SQL 仍由 MySQL 执行。
Task 7: complete — 8 章 40 题全部正确/错误/至少 10 个等价 SQL 在真实 MySQL 中验证。SQLGlot 将 AND 和 DATE_FORMAT 规范化为内部函数节点；新增回归测试确认失败后修正函数映射。
Task 8: complete — 3 个草稿并发/失败恢复测试 RED→GREEN；浏览器学习流程从缺少欢迎页的失败到整条通过。实际浏览器发现实验室编辑区溢出遮挡按钮，使用同一失败测试修复编辑器高度后通过。完成桌面截图检查。
Task 9: complete — 恢复数据与重置进度接口测试、初始化中断、中文空格路径、双启动隔离及未知报错通过。双启动在读取已锁定文件时抛出 PermissionError，先观察测试失败，再统一转换为可理解的运行中提示。
Task 10: in progress — 发行组装测试 RED→GREEN；已生成真实便携包并以仅含 Windows System32 的 PATH 验证启动、查询、判题、退出及重启持久化，PASS，首次初始化约 5.42 秒（仅当前主机）。
Ruling: 后端测试使用临时独立实例，避免与开发预览的学习记录和后台数据库冲突。发行包测试产生的 data 不会放入交付 ZIP。
Ruling: 执行技能要求最终 fresh-context reviewer；只委托一次只读整体验证，不委托开发任务，保持用户选择的顺序开发。
Ruling: 当前没有干净 Windows 10/11 虚拟机；不能声称跨干净系统验收完成，在验收文档中明确保留此项。
