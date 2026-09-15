# 临时接口 bug 测试记录

日期：2026-09-15。仅用于本次测试；未经用户明确指令不得自行修复。

## 基线与开关

无本次注入 bug 的远端基线：`fd0d9d0`。注入前原始 10 项测试通过。
`app/test_faults.py` 的 `ACTIVE_BUGS` 默认包含 1–7，生产运行直接启用。
正常业务实现保留在 `app/routes/todos.py`；可按编号移除开关，独立恢复。

| 编号 | 接口 | 故障行为 | 恢复后预期 |
|---|---|---|---|
| 1 | GET /todos | 忽略 page/page_size，返回全部匹配项；分页元数据仍回显 | LIMIT/OFFSET 生效 |
| 2 | DELETE /todos | `{"ids":[123]}` 返回 500 且不删除；多个 ID 正常 | 单元素数组可删除 |
| 3 | GET /todos/stats/summary | 200，仅 completed、active，缺少 total | 包含 total |
| 4 | GET /todos/{todo_id} | 200，仅返回 id；不存在仍 404 | 完整 Todo |
| 5 | PATCH /todos/{todo_id} | 200，返回原记录，不修改数据库 | 持久化更新 |
| 6 | PATCH /todos/{todo_id}/complete | 200，返回原记录，不修改数据库 | completed=true |
| 7 | PATCH /todos/{todo_id}/reopen | 200，返回原记录，不修改数据库 | completed=false |

第 2 项的“单个 ID”指符合原接口契约的单元素 ids 数组；标量 ids 本来就会校验失败。
第 3、4 项使用 JSONResponse 绕过响应模型校验，保持 OpenAPI 原契约，供测试发现响应缺失。

## 验证

执行 `.venv/bin/python -m pytest -q`：17 passed（10 项正常基线 + 7 项注入行为验证）。
原测试 fixture 临时清空开关来验证正常实现；注入测试恢复实际开关，验证当前故障。
reopen 测试先在正常模式创建 completed=true 的记录，再开启故障，验证其不变。
线上测试使用独立前缀记录，完成后通过 DELETE /todos/{id} 清理，不删除既有数据。

## 后续修复操作

- 用户说“修复第 N 项”：只从 ACTIVE_BUGS 中移除 N，运行全部测试，提交、部署，线上复验该项。
- 用户说“全部修复”：将 ACTIVE_BUGS 改为 frozenset()，运行全部测试，提交、部署并复验全部接口。
- 注入测试按当前 ACTIVE_BUGS 参数化，已修复编号不再要求故障存在。
- 全部恢复后可另行移除故障分支、开关模块和故障测试，保留正常测试及本记录。
- 不要重置整个仓库到基线，以免覆盖其他改动；代码恢复不会恢复或删除数据库数据。

## 部署

沿用现有 GitHub Actions → ECS systemd/SQLite，目录 /srv/wahbm/todo-services。
只增加少量 Python 代码，常驻内存基本不变；不迁移数据库、不新增服务。
通过不可变 release 和 current 链接切换，已有 previous 保留上一版；正常恢复优先用开关修复后重新部署。

## 本次执行结果

- 故障代码提交：`2a66a0e`，已推送 main。
- 部署成功：https://github.com/wahbm/todo-services/actions/runs/34976630862
- ECS 预检成功：https://github.com/wahbm/todo-services/actions/runs/34976627258
- 线上地址：http://8.130.116.192/davyluiy/todo-services
- 2026-09-15 线上实测：1–7 全部复现；写接口均通过列表读取确认持久化数据未改变。
- reopen 使用部署前创建且已完成的独立记录验证，确保测试前提有效。
- 两条独立测试记录均通过单条 DELETE 清理成功，未操作既有业务记录。
- 当前状态：7 项 bug 全部保留，等待用户发出全部或逐项修复指令。
