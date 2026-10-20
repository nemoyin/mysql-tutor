# 离线 MySQL 培训工具 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 本项目建议使用 executing-plans，由当前会话顺序实施。

**Goal:** 交付 Windows 单机离线培训工具，使零基础学员在真实 MySQL 上完成 8 章约 40 题的查询学习，并保存进度。

**Architecture:** 浏览器前端由本地应用服务提供，应用服务管理课程、学员记录和判题。工具专用 MySQL 实例仅执行练习数据查询；学习记录保存在独立 SQLite 文件。启动器负责进程生命周期，所有运行组件随便携包交付。

**Tech Stack:** Python 3.12 x64、FastAPI/Uvicorn、PyMySQL（含 caching_sha2_password 所需依赖）、SQLGlot；React/TypeScript、Vite、CodeMirror 6；SQLite；MySQL Community Server 8.4 LTS Windows x64 ZIP；PyInstaller onedir；pytest、Vitest、Playwright。

**Spec:** `docs/superpowers/specs/2026-10-20-mysql-training-design.md`（用户已确认）。

## Global Constraints

- 单机独立使用，第一版只做 MySQL，Hive 留待后续。
- 本地学员档案仅输入姓名或昵称进入，不设置密码。
- 第一版面向 Windows 10/11 64 位电脑，采用本地服务加浏览器页面。
- 分发包包含 MySQL 和工具运行所需组件；首次使用不联网下载依赖。
- 查询分析优先，不做建库建表、插入、更新和删除的教学。
- 自由实验室只开放查询；恢复练习数据和重置学习进度分别处理。
- 不提供在线 AI 辅导。讲解、提示和常见错误说明预先内置，断网时全部可用。
- 课程推荐按顺序学习，允许自由选择，不强制解锁。
- 第一版不包含窗口函数、存储过程、数据库运维及复杂性能优化。
- 所有产品代码任务先写有意义的失败测试，再实现并验证；布局与文案用人工视觉验收，不编写只复述样式的测试。

## Review Focus

1. 中文、空格路径下启动和再次启动应正常；Task 2 和 Task 10 覆盖。
2. 快速切题、慢保存请求和切换学员时，草稿不得串题或串人；Task 6、Task 8 覆盖。
3. 金额精度、NULL、重复行及并列排序不得误判；Task 5 覆盖。
4. 初始化中断、端口被抢占、进程编号被复用，不得破坏数据或关闭其他实例；Task 2、Task 9 覆盖。
5. 预览截断、查询超时和断开浏览器后重新进入不得产生假通过或卡死；Task 4、Task 5、Task 8 覆盖。

## 技术决定与交付规则

MySQL 选择 8.4 LTS 系列，首次构建时从官方发行源选择一个仍可取得的具体补丁版，写入 `runtime/manifest.json` 并核对 SHA-256。后续构建只使用这个固定发行文件；改变版本必须重跑全部题库与离线验证。构建时锁定 Python 和前端依赖，记录确切版本及校验信息；不在学员启动时选择或下载版本。

Python 与前端构建工具只供开发使用，交付包包含可执行程序和编译后的静态文件。CodeMirror、字体、图标及帮助内容均随包提供，不引用 CDN。PyInstaller 使用目录模式，便于保留 MySQL 的独立目录及可写数据目录。

MySQL 官方参考：[Windows 安装包](https://dev.mysql.com/doc/refman/8.4/en/windows-choosing-package.html)。SQL 解析使用 [SQLGlot 的 MySQL 方言](https://sqlglot.com/)，解析只作支持范围检查，实际权限由 MySQL 限制。[PyInstaller 目录打包说明](https://pyinstaller.org/en/stable/operating-mode.html)作为构建参考。

当前不是 Git 仓库。Task 1 在当前目录初始化仓库作为本地版本记录，不连接远程、不推送；每个任务通过验收后提交相关源码，运行数据、密钥和发行包不入库。

## 文件结构及公共约定

```text
backend/trainer/
  main.py, config.py, contracts.py
  runtime/manager.py, runtime/bootstrap.py
  dataset/schema.sql, dataset/seed.sql, dataset/catalog.json
  query/policy.py, query/executor.py, query/errors.py
  grading/compare.py, grading/service.py
  learning/store.py, learning/service.py
  content/models.py, content/loader.py
  api/app.py, api/learning.py, api/query.py, api/admin.py
backend/tests/{unit,integration}/
content/chapters/{01..08}.json
frontend/src/{app,components,features,api}/
frontend/tests/
tests/e2e/
scripts/{fetch_runtime.py,build.ps1,verify_content.py,offline_acceptance.ps1}
packaging/trainer.spec
runtime/manifest.json
docs/{user-guide.md,acceptance.md}
pyproject.toml, requirements.lock, frontend/package.json, frontend/package-lock.json
```

分发目录：`MySQL学习工具.exe`、`_internal/`、`runtime/mysql/`、`content/`、`web/`、`data/`。`data/` 细分 `mysql/`、`learning.sqlite3`、`config/`、`logs/`。数据库及日志不打进源码提交；初始分发包不含学员数据。

公共类型由 Task 1 定义：

- `RuntimePaths(root: Path, mysql_bin: Path, mysql_data: Path, learning_db: Path, content: Path, web: Path)`。
- `RuntimeState(phase: str, mysql_port: int | None, message: str, recoverable: bool)`。
- `QueryResult(columns: list[ColumnMeta], rows: list[list[Cell]], total_rows: int | None, truncated: bool, elapsed_ms: int)`。
- `ColumnMeta(name: str, kind: str)`；`Cell` 使用 JSON 标量或 NULL，DECIMAL 在传输层保留十进制字符串，按列类型解释；日期时间使用固定 ISO 表达。
- `QueryFailure(code: str, mysql_errno: int | None, original: str, explanation: str)`。
- `GradeResult(status: Literal['passed','incorrect','ungraded'], reason: str)`。
- `Problem(id, chapter_id, title, lesson, example_sql, starter_sql, prompt, hints, answer_sql, output_columns, compare_order, check_aliases, decimal_places, required_constructs)`；参考答案与未打开提示不随普通题目接口返回。
- `Profile(id: str, nickname: str)`；`Draft(profile_id, scope, sql, revision)`；`scope` 为题目 ID 或 `lab`。
- `TableInfo(name: str, label: str, description: str, columns: list[FieldInfo], relations: list[RelationInfo])`；`FieldInfo(name: str, mysql_type: str, nullable: bool, description: str)`；`RelationInfo(column: str, target_table: str, target_column: str)`，由 Task 1 定义、Task 3 填充。
- `ValidatedQuery(sql: str, ast: sqlglot.Expression, referenced_tables: set[str])` 由 Task 4 在 query/policy.py 定义，仅供后端使用。

API 使用统一错误结构 `{code,message,details}`，常见 SQL 错误不作为应用崩溃处理。服务仅绑定 127.0.0.1，验证 Host/Origin，所有修改接口验证本地会话令牌；前端不持有数据库凭据。静态资源与 API 同源。

## Task 1：建立工程与可运行的本地服务

**Files:** 创建 `pyproject.toml`、`backend/trainer/{main,config,contracts}.py`、`backend/trainer/api/app.py`、`frontend/package.json`、`frontend/src/app/App.tsx`、`frontend/src/api/client.ts`、`.gitignore`；测试 `backend/tests/unit/test_app.py`。

**Interfaces:** 产生 `create_app(paths: RuntimePaths) -> FastAPI`、`resolve_paths(root: Path) -> RuntimePaths` 和上述公共类型；提供 `GET /api/health -> {status,version}`。

- [ ] 建立隔离开发环境、依赖锁和 Git 本地记录；不安装产品到系统服务，不更改已有 MySQL。
- [ ] 写失败测试 `test_health_and_paths`，断言健康接口返回 `status == 'ok'`，所有可写路径在指定 root/data 内，非法配置路径被拒绝。
- [ ] 执行 `python -m pytest backend/tests/unit/test_app.py -q`，确认因接口尚未实现而失败。
- [ ] 实现路径与服务工厂、中文首页框架、前端 API 错误封装；开发阶段静态页面由本地服务提供。
- [ ] 重跑上述测试及前端 `npm run build`（在 frontend 目录），要求通过；提交工程骨架。

## Task 2：真实 MySQL 的独立启动与初始化

**Files:** 创建 `backend/trainer/runtime/{manager,bootstrap}.py`、`scripts/fetch_runtime.py`、`runtime/manifest.json`；测试 `backend/tests/unit/test_runtime.py`、`backend/tests/integration/test_mysql_runtime.py`。

**Interfaces:** 消费 RuntimePaths；产生 `RuntimeManager.start() -> RuntimeState`、`stop() -> None`、`state() -> RuntimeState`、`bootstrap_instance(paths: RuntimePaths, port: int) -> None`。连接凭据仅由内部接口提供给后端组件。

- [ ] 写失败测试：`test_paths_with_chinese_and_spaces`、`test_occupied_port_uses_another_port`、`test_restart_preserves_data`、`test_stale_pid_never_kills_foreign_process`、`test_interrupted_initialization_recovers`、`test_readonly_directory_has_actionable_error`。
- [ ] 执行 `python -m pytest backend/tests/unit/test_runtime.py -q`，确认失败；在固定 MySQL 发行文件可用后启用集成测试，缺少运行文件必须明确失败，不能报告验收成功。
- [ ] 实现官方发行文件下载、校验、清单记录；隐藏窗口启动 MySQL，禁用 X Plugin 额外监听，传统协议仅绑定本机；优先 13306，冲突时选择可用端口，处理检查后被占用的重试。
- [ ] 使用仅属于本工具的临时初始化目录及完成标记；中断后只处理已验证位于本工具根目录中的未完成目录，不删除已有成功实例。管理凭据随机生成且不进入日志。
- [ ] 固定 utf8mb4、排序规则、SQL mode（包含 ONLY_FULL_GROUP_BY、STRICT_TRANS_TABLES）、会话时区 +08:00；初始化专用只读账号。停止前核对实例路径及所属进程，禁止全局结束 mysqld。
- [ ] 执行 `python -m pytest backend/tests/unit/test_runtime.py backend/tests/integration/test_mysql_runtime.py -q`，全部通过后提交。

## Task 3：电商固定数据与数据参考接口

**Files:** 创建 `backend/trainer/dataset/{schema.sql,seed.sql,catalog.json}`、`backend/trainer/content/models.py`；测试 `backend/tests/integration/test_dataset.py`。

**Interfaces:** 产生 `seed_dataset(connection) -> None`（放在 runtime/bootstrap.py）、`load_catalog() -> list[TableInfo]`（放在 content/loader.py）；表名固定为 `customers`、`categories`、`products`、`orders`、`order_items`。

- [ ] 写失败测试 `test_seed_is_deterministic_and_relations_valid`，验证主外键、DECIMAL 金额，以及未下单客户、未售商品、NULL、同名客户、取消订单确实存在。
- [ ] 执行 `python -m pytest backend/tests/integration/test_dataset.py -q`，确认失败。
- [ ] 建立 30 客户、6 分类、40 商品、120 订单、300 明细的固定种子数据，日期固定为 2026-01-01 至 2026-06-30；价格与折扣有稳定的人工可核对案例。禁止启动时随机生成。
- [ ] 实现中文表说明、字段类型与关联信息，样例接口每表最多 10 行；仅对固定目录中的五张表提供结构及样例。
- [ ] 重跑数据测试，人工核算一个客户的订单数及销售额，与 SQL 结果一致；提交数据与参考内容。

## Task 4：受控查询执行与中文报错

**Files:** 创建 `backend/trainer/query/{policy,executor,errors}.py`、`backend/trainer/api/query.py`；测试 `backend/tests/unit/test_query_policy.py`、`backend/tests/integration/test_query_execution.py`。

**Interfaces:** `validate_query(sql: str) -> ValidatedQuery`；`execute_query(sql: str, purpose: Literal['preview','grade']) -> QueryResult`，失败抛出携带 QueryFailure 的领域异常。`POST /api/query/run {profile_id,scope,sql}` 返回结果或结构化错误。

- [ ] 写失败测试，覆盖带注释的合法 SELECT、子查询、字符串内分号，以及 UPDATE、多语句、INTO OUTFILE、LOAD_FILE、SLEEP/BENCHMARK、锁定查询、系统库访问被拒绝。
- [ ] 执行 `python -m pytest backend/tests/unit/test_query_policy.py -q`，确认失败。
- [ ] 使用 SQLGlot MySQL 方言解析整段输入，确认只有一个查询 AST；只允许课程需要的查询结构、函数和练习表。限制引用的 schema，禁用用户变量赋值和任意函数调用；不靠字符串前缀检查。
- [ ] 仅用 SELECT 权限账号执行，限制查询 5 秒；结合服务器执行时间限制、连接超时和取消清理，超时后下一次查询仍可使用。预览最多 200 行、判题最多 10000 行，分别多取一行判断是否超限。列值大小及响应体同样设限，超限不静默修改 SQL。
- [ ] 写并执行集成测试 `test_readonly_account_cannot_write`、`test_timeout_then_next_query_works`、`test_preview_is_marked_truncated`、`test_unknown_error_preserves_original`；映射常见 1054、1064、1146、1055 报错到中文。
- [ ] 运行本任务全部测试并提交。实际数据库若表现与解析器不一致，返回真实报错，不改写学员 SQL 以掩盖差异。

## Task 5：课程模型与结果判题

**Files:** 创建 `backend/trainer/content/loader.py`、`backend/trainer/grading/{compare,service}.py`；测试 `backend/tests/unit/test_grading.py`、`backend/tests/integration/test_grading.py`；先创建两道临时正式课程题（后由 Task 7 扩充）。

**Interfaces:** `load_problem(problem_id: str) -> Problem`；`compare_results(actual: QueryResult, expected: QueryResult, problem: Problem) -> GradeResult`；`grade_submission(problem_id: str, sql: str) -> GradeResult`。`POST /api/problems/{id}/submit` 执行后判题，禁止客户端提供参考结果或判题规则。

- [ ] 写失败测试 `test_unordered_rows_keep_duplicate_counts`、`test_null_differs_from_empty_string`、`test_decimal_scale_normalized`、`test_ordered_rows_and_tie_breaker`、`test_different_valid_sql_passes`、`test_truncated_grade_is_ungraded`、`test_ast_construct_not_keyword_in_comment`。
- [ ] 执行 `python -m pytest backend/tests/unit/test_grading.py -q`，确认失败。
- [ ] 按列元数据规范化数值与日期；金额依题目指定精度按 ROUND_HALF_UP 量化，NULL 保持独立。默认将每行规范化为元组后用计数多重集合比较，排序题逐行比较。
- [ ] 先比列数、必要别名与结果行数，再比值及顺序；要求指定语法的题使用 AST 节点检查。返回差异类别而不泄露完整答案；超时、资源超限为 ungraded。
- [ ] 运行 `python -m pytest backend/tests/unit/test_grading.py backend/tests/integration/test_grading.py -q`，验证参考结果由真实 MySQL 产生且不会被浏览器直接索取；提交。

## Task 6：学员、草稿、进度与查询记录

**Files:** 创建 `backend/trainer/learning/{store,service}.py`、`backend/trainer/api/learning.py`；测试 `backend/tests/unit/test_learning.py`、`backend/tests/integration/test_learning_api.py`。

**Interfaces:** `create_profile(nickname: str) -> Profile`；`save_draft(profile_id: str, scope: str, sql: str, revision: int) -> Draft`；`reveal_answer(profile_id: str, problem_id: str) -> str`；`record_grade(profile_id: str, problem_id: str, result: GradeResult) -> None`。

- [ ] 写失败测试：去除昵称首尾空白、空昵称拒绝、规范化后同名返回冲突而不合并；学员 A/B 及题目之间隔离；较旧 revision 不覆盖较新草稿；重开 SQLite 后进度仍在。
- [ ] 增加 `test_answer_reveal_survives_restart`，断言查看答案后通过保留首次完成方式，再练记录不会抹去查看事实。学习记录不声称能检测学员是否从外部取得答案。
- [ ] 执行 `python -m pytest backend/tests/unit/test_learning.py -q`，确认失败。
- [ ] 使用参数化 SQLite 操作、事务和 schema 版本；昵称限制 1–30 字符，profile 为 UUID；学习草稿、查看答案事件、提交结果、最后位置和命名保存 SQL 分表记录。
- [ ] 保存草稿仅接受比已有值更新的 revision；相同 revision 与相同内容可幂等重试，相同 revision 不同内容返回冲突，前端刷新最新版本后提供恢复选择。
- [ ] 提供档案列表/创建、课程状态、草稿读写、分层提示/参考答案、历史分页、保存 SQL、重置当前学员进度接口；查询历史每人保留最近 1000 条，草稿和命名保存不跟随历史淘汰。
- [ ] 执行本任务全部测试，验证会话令牌与 Host/Origin 校验；提交。

## Task 7：完成 8 章 40 题及离线讲解

**Files:** 创建或补全 `content/chapters/01.json` 至 `08.json`、`scripts/verify_content.py`、`backend/tests/integration/test_all_content.py`。

**Interfaces:** 使用 Task 5 的 Problem 模型与 `grade_submission`；章节题量固定为 3、5、8、4、6、6、4、4，总计 40 题。

- [ ] 写内容验收测试：8 章、40 个唯一题号、每题有中文讲解与示例、至少两层提示和答案、输出规则完备、所有链接为本地或纯帮助文本。
- [ ] 执行 `python -m pytest backend/tests/integration/test_all_content.py -q`，确认因缺少内容失败。
- [ ] 编写课程与练习，覆盖设计文档全部知识点；别名、日期区间、取消订单、舍入及并列规则在题干明确。第一章通过观察表与简单 SELECT 认识结构，不要求执行管理命令。
- [ ] 为每题准备参考正确写法与一条有针对性的错误写法；其中至少 10 题另备等价正确写法。参考和错误案例都在真实 MySQL 上执行，错误案例必须未通过，避免空结果或数据巧合使题目失效。
- [ ] 执行 `python scripts/verify_content.py` 及上述测试，要求全部答案通过、全部针对性错误未通过；逐题人工核对题干与结果，提交题库。

## Task 8：首页、学习工作台、自由实验室与学习记录

**Files:** 创建 `frontend/src/features/{profiles,home,workspace,lab,records}/`、`frontend/src/components/{SqlEditor,ResultTable,SchemaPanel,FeedbackPanel}.tsx`、`frontend/tests/workspace.test.tsx`、`tests/e2e/learning.spec.ts`。

**Interfaces:** 使用 Task 4–6 的 API；`SqlEditor({value,onChange,onRun})`、`ResultTable({result})`；前端题目只接收公开内容。样例运行独立于题目草稿。

- [ ] 写失败交互测试：运行不自动判题；查看普通提示不标记看过答案；切题保留草稿；慢保存与切学员不会覆盖他人内容；示例不覆盖编辑内容。
- [ ] 在 frontend 执行 `npm run test -- --run`，确认相关用例失败。
- [ ] 实现中文学习界面，首页突出继续学习，工作台三栏布局，右侧数据参考可折叠；1280×720 无关键按钮遮挡，较窄窗口堆叠或折叠侧栏，结果表单独横向滚动。
- [ ] 实现编辑 600ms 后自动保存；切换前等待保存或提示失败并保留本机恢复副本，恢复副本按学员及 scope 隔离。关闭前使用 keepalive 保存，页面重开时结合 revision 恢复，显示保存状态。
- [ ] 实现显式运行/提交、原始错误与中文提示、分层提示、下一题、草稿恢复、历史分页与命名 SQL。切换和运行期间处理请求竞态，旧请求不能更新新题画面。
- [ ] 使用 Playwright 跑完整流程：建档 → 做题 → 提示 → 通过 → 切题 → 实验室 → 关闭页面 → 重开 → 检查进度；另测服务重启后恢复。执行 `npm run build` 并人工查看桌面和小屏截图，修复后提交。

## Task 9：数据恢复、关闭与异常恢复

**Files:** 创建 `backend/trainer/api/admin.py`；补全 runtime/manager.py、learning/service.py；创建前端设置对话框；测试 `backend/tests/integration/test_recovery.py`、`tests/e2e/recovery.spec.ts`。

**Interfaces:** `restore_dataset() -> RuntimeState`（runtime/bootstrap.py）；`reset_progress(profile_id: str) -> None`（learning/service.py）；`POST /api/admin/restore`、`POST /api/profiles/{id}/reset-progress`、`POST /api/admin/shutdown`。

- [ ] 写失败测试：恢复数据保留所有档案、草稿及历史；重置进度只清当前学员的通过记录、答案查看记录和继续学习位置，保留草稿/历史/命名 SQL；恢复中禁止新查询并给出可重试状态。
- [ ] 写故障注入测试：恢复中断后显示状态并允许安全重试；启动阶段不会仅因完成标记存在就跳过实际健康检查；关闭接口不会停止另一个 MySQL 实例。
- [ ] 执行 `python -m pytest backend/tests/integration/test_recovery.py -q`，确认失败。
- [ ] 实现管理操作互斥和查询排空；恢复仅作用于固定练习 schema，使用进行中标记保证中断后可识别并幂等重试。重建练习数据不触及 learning.sqlite3。
- [ ] 确认框写明准确影响范围；实现退出工具、数据库优雅关闭及异常日志。退出后返回可理解的页面状态，不把正常退出展示为 SQL 报错。
- [ ] 运行本任务后端与端到端测试，确认无实例干扰后提交。

## Task 10：便携打包与离线验收交付

**Files:** 创建 `scripts/{build.ps1,offline_acceptance.ps1}`、`packaging/trainer.spec`、`docs/{user-guide.md,acceptance.md}`；补全 README 和依赖锁文件。

**Interfaces:** `scripts/build.ps1` 产生 `dist/MySQL学习工具/` 及 ZIP；包内启动器消费同一 RuntimePaths，无开发环境路径依赖；`scripts/offline_acceptance.ps1 -Root <包路径>` 输出机器可读检查结果与人工验证清单。

- [ ] 写打包冒烟检查：没有 Python/Node/MySQL 的 PATH，且网络请求被阻止时，发行包仍能启动、执行 SELECT、完成一题并在重启后保留档案。
- [ ] 先对缺少运行组件的构建运行检查，确认具体指出缺失组件，而不是静默改用已安装的 MySQL。
- [ ] 以 PyInstaller onedir 打包 Python 服务与启动器，将前端静态文件、课程、MySQL 发行目录及必要运行库一起组装。核对官方 Windows 运行库要求，处理可合法随包分发的运行依赖；不能把“请联网安装”当成完成免安装目标。
- [ ] 验证开发过程下载的资源有固定校验清单，发行包保留适用的许可证/NOTICE；不包括开发依赖、密钥、测试学员档案和日志。
- [ ] 在干净 Windows 10/11 x64 环境断网验收，覆盖中文空格路径、首次初始化、非管理员启动、重启、已有 MySQL、端口冲突、恢复数据及 40 题校验；记录环境、结果、包大小与启动时间。拿不到干净环境时明确记录未验证项，不宣称全部验收通过。
- [ ] 执行 `python -m pytest backend/tests -q`、frontend 的 `npm run test -- --run` 与 `npm run build`、端到端 `npx playwright test`、`python scripts/verify_content.py`，确认通过。
- [ ] 交付 ZIP、使用说明、验收记录；最后提交源码与文档，不提交发行包和用户数据。

## 计划自检与执行交接

已覆盖设计文档中的启动、单机档案、课程与页面、查询约束、判题、学习记录、恢复、异常和离线交付；没有产品实现代码。本计划的 5 个 Review Focus 均落实到任务测试。

建议当前会话顺序执行：任务之间的运行管理、查询和判题接口联系紧密，连续实施更方便及时做真实 MySQL 集成验证。每个任务通过后更新复选框并形成提交，最后进行整体检查。

执行前请用户审阅本计划并选择：当前会话顺序实施，或按任务分工给子代理实施。用户选择后读取对应执行技能，再开始 Task 1。
