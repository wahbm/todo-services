# Todo API 接口文档

## 1. 服务信息

这是一个基于 FastAPI + SQLite 的 Todo 服务，提供 Todo 的增删改查、完成/重新打开、批量删除和统计能力。

- 服务名称：`Todo API Service`
- 当前版本：`1.0.0`
- 默认服务地址：`http://127.0.0.1:8000`
- 默认数据库：项目根目录下的 `todo.db`
- Swagger UI：[`/docs`](http://127.0.0.1:8000/docs)
- ReDoc：[`/redoc`](http://127.0.0.1:8000/redoc)
- OpenAPI JSON：[`/openapi.json`](http://127.0.0.1:8000/openapi.json)

除 `204 No Content` 接口外，接口默认使用 JSON 请求体和 JSON 响应。

## 2. 启动服务

```bash
uvicorn app.main:app --reload
```

如需指定数据库文件：

```bash
TODO_DB_PATH=/path/to/todo.db uvicorn app.main:app --reload
```

如果部署在反向代理的子路径下，可通过 `ROOT_PATH` 配置外部根路径：

```bash
ROOT_PATH=/api uvicorn app.main:app --reload
```

## 3. 接口总览

| 方法 | 路径 | 说明 | 成功状态码 |
| --- | --- | --- | --- |
| `GET` | `/health` | 健康检查 | `200` |
| `POST` | `/todos` | 创建 Todo | `201` |
| `GET` | `/todos` | 分页查询 Todo | `200` |
| `GET` | `/todos/stats/summary` | 获取 Todo 统计 | `200` |
| `DELETE` | `/todos` | 按 ID 批量删除 Todo | `200` |
| `GET` | `/todos/{todo_id}` | 获取单个 Todo | `200` |
| `PATCH` | `/todos/{todo_id}` | 部分更新 Todo | `200` |
| `DELETE` | `/todos/{todo_id}` | 删除单个 Todo | `204` |
| `PATCH` | `/todos/{todo_id}/complete` | 标记为已完成 | `200` |
| `PATCH` | `/todos/{todo_id}/reopen` | 重新打开 Todo | `200` |

## 4. 数据模型

### 4.1 Todo 对象 `TodoResponse`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `integer` | 是 | Todo ID，自增 |
| `title` | `string` | 是 | 标题，长度 1～200；创建和更新时会去除首尾空格 |
| `description` | `string \| null` | 是 | 描述，最大长度 1000；可以为空 |
| `completed` | `boolean` | 是 | 是否已完成，默认 `false` |
| `created_at` | `string (date-time)` | 是 | 创建时间 |
| `updated_at` | `string (date-time)` | 是 | 最后更新时间 |

示例：

```json
{
  "id": 1,
  "title": "Buy groceries",
  "description": "Pick up fruit, milk, and bread.",
  "completed": false,
  "created_at": "2026-09-14T08:00:00",
  "updated_at": "2026-09-14T08:00:00"
}
```

### 4.2 创建请求 `TodoCreate`

| 字段 | 类型 | 必填 | 默认值 | 约束 |
| --- | --- | --- | --- | --- |
| `title` | `string` | 是 | - | 1～200 个字符，不能全为空格 |
| `description` | `string \| null` | 否 | `null` | 最大长度 1000 |

### 4.3 更新请求 `TodoUpdate`

所有字段均为可选，未传入的字段保持原值。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `title` | `string \| null` | 否 | 传入时长度 1～200，不能全为空格 |
| `description` | `string \| null` | 否 | 最大长度 1000；显式传 `null` 可清空描述 |
| `completed` | `boolean \| null` | 否 | 更新完成状态 |

### 4.4 Todo 列表响应 `TodoListResponse`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `items` | `TodoResponse[]` | 当前页数据 |
| `total` | `integer` | 符合筛选条件的总数量 |
| `page` | `integer` | 当前页码 |
| `page_size` | `integer` | 当前分页大小 |

### 4.5 批量删除请求/响应

请求模型 `TodoBulkDeleteRequest`：

```json
{
  "ids": [1, 2, 3]
}
```

`ids` 至少包含一个整数 ID。

响应模型 `TodoBulkDeleteResponse`：

```json
{
  "deleted": 2
}
```

`deleted` 表示实际删除的记录数，不存在的 ID 会被忽略。

## 5. 接口详情

### 5.1 健康检查

#### `GET /health`

返回服务是否正常运行。

响应 `200 OK`：

```json
{
  "status": "ok"
}
```

示例：

```bash
curl http://127.0.0.1:8000/health
```

### 5.2 创建 Todo

#### `POST /todos`

请求头：`Content-Type: application/json`

请求体：

```json
{
  "title": "Buy groceries",
  "description": "Pick up fruit, milk, and bread."
}
```

响应 `201 Created`：返回创建后的 `TodoResponse`。

示例：

```bash
curl -X POST http://127.0.0.1:8000/todos \
  -H 'Content-Type: application/json' \
  -d '{"title":"Buy groceries","description":"Pick up fruit, milk, and bread."}'
```

### 5.3 分页查询 Todo

#### `GET /todos`

查询参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `page` | `integer` | 否 | `1` | 页码，最小值 `1` |
| `page_size` | `integer` | 否 | `20` | 每页数量，范围 `1～100` |
| `completed` | `boolean` | 否 | 不筛选 | `true` 查询已完成，`false` 查询未完成 |
| `keyword` | `string` | 否 | 不筛选 | 在 `title` 或 `description` 中进行包含匹配，至少 1 个字符 |

查询结果按 `id` 倒序排列，最新创建的 Todo 在前。

响应 `200 OK`：

```json
{
  "items": [
    {
      "id": 2,
      "title": "Write report",
      "description": null,
      "completed": true,
      "created_at": "2026-09-14T08:02:00",
      "updated_at": "2026-09-14T08:03:00"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20
}
```

示例：

```bash
# 查询第 1 页，每页 20 条
curl 'http://127.0.0.1:8000/todos?page=1&page_size=20'

# 查询未完成且标题/描述包含 buy 的 Todo
curl 'http://127.0.0.1:8000/todos?completed=false&keyword=buy'
```

### 5.4 获取 Todo 统计

#### `GET /todos/stats/summary`

响应 `200 OK`：

```json
{
  "total": 10,
  "completed": 4,
  "active": 6
}
```

字段说明：

- `total`：Todo 总数
- `completed`：已完成数量
- `active`：未完成数量

示例：

```bash
curl http://127.0.0.1:8000/todos/stats/summary
```

### 5.5 批量删除 Todo

#### `DELETE /todos`

请求头：`Content-Type: application/json`

请求体：

```json
{
  "ids": [1, 2, 3]
}
```

响应 `200 OK`：

```json
{
  "deleted": 2
}
```

示例：

```bash
curl -X DELETE http://127.0.0.1:8000/todos \
  -H 'Content-Type: application/json' \
  -d '{"ids":[1,2,3]}'
```

### 5.6 获取单个 Todo

#### `GET /todos/{todo_id}`

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `todo_id` | `integer` | Todo ID |

响应 `200 OK`：返回 `TodoResponse`。

示例：

```bash
curl http://127.0.0.1:8000/todos/1
```

### 5.7 部分更新 Todo

#### `PATCH /todos/{todo_id}`

请求头：`Content-Type: application/json`

请求体示例：

```json
{
  "title": "Buy groceries today",
  "description": "Fruit and milk",
  "completed": true
}
```

只传需要修改的字段即可：

```json
{
  "completed": true
}
```

响应 `200 OK`：返回更新后的 `TodoResponse`。

说明：

- 空对象 `{}` 会执行空更新并返回当前 Todo。
- `description` 显式传 `null` 时会清空描述；省略该字段则保留原描述。
- 更新成功后，`updated_at` 由数据库触发器自动更新。

示例：

```bash
curl -X PATCH http://127.0.0.1:8000/todos/1 \
  -H 'Content-Type: application/json' \
  -d '{"completed":true}'
```

### 5.8 删除单个 Todo

#### `DELETE /todos/{todo_id}`

响应 `204 No Content`，响应体为空。

示例：

```bash
curl -i -X DELETE http://127.0.0.1:8000/todos/1
```

### 5.9 标记为已完成

#### `PATCH /todos/{todo_id}/complete`

无需请求体，将指定 Todo 的 `completed` 设置为 `true`。

响应 `200 OK`：返回更新后的 `TodoResponse`。

示例：

```bash
curl -X PATCH http://127.0.0.1:8000/todos/1/complete
```

### 5.10 重新打开 Todo

#### `PATCH /todos/{todo_id}/reopen`

无需请求体，将指定 Todo 的 `completed` 设置为 `false`。

响应 `200 OK`：返回更新后的 `TodoResponse`。

示例：

```bash
curl -X PATCH http://127.0.0.1:8000/todos/1/reopen
```

## 6. 错误响应

### 6.1 资源不存在：`404 Not Found`

获取、更新、删除或改变不存在的 Todo 时返回：

```json
{
  "detail": "Todo 999 not found"
}
```

### 6.2 参数校验失败：`422 Unprocessable Entity`

请求体或查询参数不符合约束时，由 FastAPI 返回标准校验错误，例如标题为空：

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "title"],
      "msg": "Value error, title must not be blank",
      "input": "   "
    }
  ]
}
```

常见触发场景：

- 创建 Todo 时缺少 `title`。
- `title` 为空或全是空格，或超过 200 个字符。
- `description` 超过 1000 个字符。
- `page` 小于 1，或 `page_size` 不在 1～100 范围内。
- `keyword` 为空字符串。
- 批量删除时 `ids` 为空数组。

## 7. OpenAPI 与测试

接口定义由 FastAPI 自动生成，也可以通过启动服务后访问以下地址查看：

- Swagger UI：`http://127.0.0.1:8000/docs`
- OpenAPI JSON：`http://127.0.0.1:8000/openapi.json`

运行测试：

```bash
pytest
```
