# 多 OLTP 源接入设计方案

## 概述

当前系统仅支持单一的 OLTP 源数据库（通过 `DATABASE_ROLE` 表中 `role_name = 'OLTP'` 的行绑定）。本设计将其扩展为支持任意多个 OLTP 源，每个源拥有独立的连接配置和别名（作为 `record_source`），多源数据通过表名前缀汇聚到同一套 PSA/DV 目标库中。

## 数据模型变更

### 新增表 `OLTP_SOURCE`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK, autoincrement | |
| `record_src` | String(64), UNIQUE, NOT NULL | 源别名，同时也是 record_source 标识，用作表名前缀 |
| `conn_id` | Integer, NOT NULL | 引用 ConnectionConfig.id |
| `database_name` | String(128), NOT NULL | 对应的数据库名 |
| `created_at` | DateTime | 创建时间 |

### Attribute 表新增字段

| 新字段 | 类型 | 说明 |
|--------|------|------|
| `record_src` | String(64), nullable | 该字段所属的 OLTP 源 |

### DATABASE_ROLE 表变更

删除 `role_name = 'OLTP'` 的行，仅保留 STAGE 和 CORE 两行。所有通过 `role_name = 'OLTP'` 查找的地方改为查询 `OLTP_SOURCE` 表。

### 约束

- `record_src` 必须全局唯一
- 删除 `ConnectionConfig` 前需检查是否有 `OLTP_SOURCE` 或 `DATABASE_ROLE` 引用该 `conn_id`

## 后端 API 变更

### 新增 API（OLTP 源 CRUD）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/oltp-sources` | 列出所有 OLTP 源 |
| POST | `/api/oltp-sources` | 新增 OLTP 源（record_src, conn_id, database_name） |
| PUT | `/api/oltp-sources/{id}` | 编辑 OLTP 源 |
| DELETE | `/api/oltp-sources/{id}` | 删除 OLTP 源 |

### 修改的 API

| 路径 | 改动 |
|------|------|
| `GET /api/db-roles` | 返回结果去掉 `oltp` 键，仅保留 `stage` 和 `core` |
| `PUT /api/db-roles` | 请求体去掉 `oltp` 字段 |
| `GET /api/meta/oltp-source` | 改为列出所有 OLTP 源（返回列表而非单个） |
| `POST /api/meta/import` | 增加 `record_src` 参数，写入 Attribute 表时赋值 |
| `GET /api/generator/psa/*` | 增加 `record_src` 参数，按源过滤生成 |
| `GET /api/generator/dv/*` | 增加 `record_src` 参数，按源过滤生成 |
| `GET /api/preview/databases` | OLTP 节点返回所有 OLTP 源的表（合并展示） |
| `GET /api/objects` | 返回结果增加 `record_src` 信息 |

### 后端 Pydantic Schema 变更

新增 `OltpSourceCreate` / `OltpSourceUpdate` schema。`DatabaseRolesRequest` 去掉 `oltp` 字段。

## 生成器逻辑变更

### PSA Generator

构造函数增加 `record_src` 参数。生成 SQL 时：
- 表名前缀使用 `{record_src}_`（如 `stg_erp_customer`）
- `oltp_db_name` 从 `OLTP_SOURCE` 表按 `record_src` 查询
- 仅在 `Attribute.record_src == record_src` 的字段上生成

### DV Generator

构造函数增加 `record_src` 参数。生成 SQL 时：
- HUB/SAT/LINK 表名使用 `h_{record_src}_{table}`、`s_{record_src}_{table}`、`l_{record_src}_{table}`
- 仅在 `Attribute.record_src == record_src` 的字段上生成

### 生成 API 端点

所有 PSA/DV 生成端点增加可选 `record_src` 查询参数。如果未指定 `record_src`，返回提示请选择源。生成配置（PSA_DB、CORE_DB、HASH_DUMMY）保持不变。

## 前端 UI 变更

### 页面 1：连接管理（ConnectionView.vue）

- **角色绑定区域**：去掉 OLTP 那一行，仅保留 STAGE 和 CORE
- **新增 OLTP 源管理卡片**：表格展示所有 OLTP 源（record_src / 连接名 / 数据库名 / 操作）
- **新增对话框**："新增 OLTP 源"和"编辑 OLTP 源"对话框（record_src / 连接选择 / 数据库名）

### 页面 2：元数据导入（MetaImportView.vue）

Step 0 选择器改为展示 OLTP 源列表，格式：`{record_src} — {连接名} / {数据库名}`。导入时自动携带 `record_src`。

### 页面 3：字段配置（MetaConfigView.vue）

对象列表表格增加"数据来源（record_src）"列，展示标签样式。

### 页面 4：生成 PSA（GeneratePsaView.vue）

顶部新增 OLTP 源下拉选择器。选择源后生成的 SQL 只包含该源的 PSA 对象。切换源时重新生成。

### 页面 5：生成 DV（GenerateDvView.vue）

顶部新增 OLTP 源下拉选择器。选择源后生成的 DV 对象使用 `{record_src}_` 前缀。

### 页面 6：数据预览（DataPreviewView.vue）

树中 OLTP 节点下直接展示所有源的表（不以 record_src 分组），表名显示为 `{record_src}_{table_name}`。

### 页面 7：部署执行（DeployView.vue）

"部署 PSA"和"部署 DV"按钮不做选择器，点击后一次性部署所有源的对象（全量部署）。

## 数据流图

```
[OLTP 源 A] ──→ 导入元数据 ──→ ATTRIBUTE (record_src='erp')
[OLTP 源 B] ──→ 导入元数据 ──→ ATTRIBUTE (record_src='crm')
                                     │
                ┌────────────────────┴────────────────────┐
                │                                         │
         生成 PSA(erp)                              生成 PSA(crm)
         生成 DV(erp)                               生成 DV(crm)
                │                                         │
                └─────────── 部署 → 同一目标库 ───────────┘
```

## 未涉及的部分

- 部署差异对比（Deploy Diff）：当前逻辑只对比目标库中存在/缺失的对象，不区分源，保持不动
- 运行时组件部署：不涉及 OLTP 源，保持不动
- 系统配置（PSA_DB / CORE_DB / HASH_DUMMY）：全局共享，保持不动
- 执行日志：不涉及 OLTP 源，保持不动