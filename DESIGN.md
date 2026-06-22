# DWH-Generator 重构设计方案

## 基于 Vue3 + FastAPI + SQL Server（Phase 1：PSA Type 2 先行）

---

## 一、项目概述

### 1.1 原始项目功能

[DWH-Generator](https://github.com/microsoftbi/DWH-Generator) 是一个**数据仓库元数据驱动的自动代码生成工具**，遵循 **PSA（持久化临时区）+ Data Vault 2.0** 方法论。它通过读取源表的列元数据，自动生成全套 DWH 建表脚本、视图和存储过程。

> 原始技术栈：C# WinForms (.NET 4.5.2) + SQL Server + Handlebars.NET

### 1.2 重构目标

使用 **Vue3 + FastAPI + SQL Server** 重构，构建一个 **Web 版** DWH 生成器，功能与原始工具对等，并增加更好的用户体验。

### 1.3 实施策略

分阶段迭代，**Phase 1 仅实现 PSA Type 2 数据流**，DV (Data Vault 2.0) 部分根据后续需求再行扩展。

### 1.4 核心流程

```
Source OLTP → [ETL (用户自行处理)] → STAGE 首表 → 导入元数据 → 配置字段角色 (BK/PK/DI)
    → 生成 PSA Type 2 SQL 脚本 → (可选) 部署执行
```

---

## 二、整体架构

```
┌───────────────────────────────────────────────────────────────────┐
│                       Frontend (Vue3)                            │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐           │
│  │ 连接配置 │ │ 元数据导入 │ │ 字段配置  │ │ 生成与部署 │           │
│  └─────────┘ └──────────┘ └──────────┘ └───────────┘           │
│                               ┌──────────────┐ (后续扩展：DV)     │
│                               │ DV 配置 (预留) │                   │
│                               └──────────────┘                   │
└──────────────────────────┬────────────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼────────────────────────────────────────┐
│                      Backend (FastAPI)                            │
│  ┌──────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │ 连接管理  │ │ 元数据导入API │ │ 配置管理API  │ │ PSA 生成引擎 │ │
│  └──────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │
│  ┌──────────┐ ┌──────────────┐ ┌──────────────┐                  │
│  │ SQL执行器 │ │ 日志服务     │ │ 模板引擎     │                  │
│  └──────────┘ └──────────────┘ └──────────────┘                  │
└────────────┬──────────────────────────────┬───────────────────────┘
             │                              │
             ▼                              ▼
     ┌──────────────┐             ┌──────────────────┐
     │  META 数据库  │             │ 目标 DWH 数据库   │
     │  (SQL Server) │             │  (SQL Server)     │
     │  元数据配置    │             │  PSA / CORE 层    │
     └──────────────┘             └──────────────────┘
```

### 2.1 前端功能模块（Phase 1）

| 模块 | 功能 |
|------|------|
| 数据库连接管理 | 配置源数据库 / META 数据库 / 目标数据库连接信息 |
| 元数据导入 | 选择源表，导入列信息到 META 数据库 |
| 字段配置 | 标记字段角色：BK(业务键)、PK(主键)、DI(描述信息) |
| 对象列表管理 | 管理需要生成的表清单 |
| 代码生成 | 生成 PSA Type 2 全套 SQL 脚本（STG/CDC/LOG/Views/USPs） |
| 部署执行 | 在目标数据库上执行生成的 SQL |
| 日志查看 | 查看生成和执行日志 |

> **注**：DV 配置模块（HUB/SAT/LINK）在本阶段暂不实现，前端 UI 做占位预留。

### 2.2 后端服务模块（Phase 1）

| 模块 | 职责 |
|------|------|
| `api/connections` | 数据库连接 CRUD + 连接测试 |
| `api/meta_import` | 从源表导入列元数据到 META |
| `api/meta_config` | BK/PK/DI 字段角色配置 |
| `api/generator` | PSA 代码生成引擎 |
| `api/deploy` | SQL 执行器（部署到目标库） |
| `api/objects` | 对象列表管理 |
| `api/logs` | 生成/执行日志查询 |
| `services/template_engine` | Jinja2 模板渲染引擎 |
| `services/generator_psa` | PSA Type 2 全部组件生成逻辑 |
| `services/sql_executor` | SQL 批处理执行（按 `GO` 分割 + 事务） |
| `db/meta_models` | META 数据库 ORM 模型 |

> **注**：`api/dv_config`、`services/generator_dv` 等 DV 相关模块在后续迭代中添加。

---

## 三、数据库设计（SQL Server）

### 3.1 META 数据库（配置库）

```sql
-- 对象列表：需要生成的表
CREATE TABLE [dbo].[GEN_LIST] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [TABLE_CATALOG] NVARCHAR(128),
    [TABLE_NAME] NVARCHAR(128) NOT NULL,
    [SCHEMA_NAME] NVARCHAR(128) DEFAULT 'dbo',
    [IS_GEN] BIT DEFAULT 1,
    [IS_FULL_LOAD] BIT DEFAULT 0,
    [CREATED_AT] DATETIME DEFAULT GETDATE(),
    UNIQUE([TABLE_CATALOG], [TABLE_NAME])
);

-- 列属性元数据
CREATE TABLE [dbo].[ATTRIBUTE] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [TABLE_CATALOG] NVARCHAR(128),
    [TABLE_NAME] NVARCHAR(128) NOT NULL,
    [COLUMN_NAME] NVARCHAR(128) NOT NULL,
    [DATA_TYPE] NVARCHAR(128),
    [CHARACTER_MAXIMUM_LENGTH] INT,
    [NUMERIC_PRECISION] TINYINT,
    [NUMERIC_SCALE] INT,
    [IS_BK] BIT DEFAULT 0,           -- Business Key
    [IS_PK] BIT DEFAULT 0,           -- Primary Key (for PSA)
    [IS_DI] BIT DEFAULT 0,           -- Descriptive Info
    [CREATED_AT] DATETIME DEFAULT GETDATE()
);

-- 登记源表（RecordSource）
CREATE TABLE [dbo].[RECORD_SOURCE] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [DATABASE_NAME] NVARCHAR(128),
    [RECORD_SOURCE_NAME] NVARCHAR(128) NOT NULL
);

-- 数据库连接配置
CREATE TABLE [dbo].[CONNECTION_CONFIG] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [NAME] NVARCHAR(128) NOT NULL,
    [DB_TYPE] NVARCHAR(32) DEFAULT 'sqlserver',
    [HOST] NVARCHAR(255),
    [PORT] INT DEFAULT 1433,
    [DATABASE_NAME] NVARCHAR(128),
    [USERNAME] NVARCHAR(128),
    [PASSWORD_ENCRYPTED] NVARCHAR(MAX),
    -- 连接用途标记：同一物理库可承担多个角色
    [IS_META] BIT DEFAULT 0,         -- 是否为 META 库
    [IS_SOURCE] BIT DEFAULT 0,       -- 是否为源库
    [IS_TARGET] BIT DEFAULT 0,       -- 是否为目标 DWH 库
    [CREATED_AT] DATETIME DEFAULT GETDATE()
);

-- 配置参数表
CREATE TABLE [dbo].[CONFIGURATION] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [CONFIG_NAME] NVARCHAR(128) NOT NULL UNIQUE,
    [CONFIG_VALUE] NVARCHAR(MAX),
    [DESCRIPTION] NVARCHAR(500)
);

-- 执行日志
CREATE TABLE [dbo].[EXECUTION_LOG] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [LOG_SOURCE] NVARCHAR(255),
    [LOG_TYPE] CHAR(1) DEFAULT 'N',  -- N=Normal, E=Error, W=Warning
    [MESSAGE] NVARCHAR(MAX),
    [CREATED_AT] DATETIME DEFAULT GETDATE()
);
```

### 3.2 初始化数据

```sql
-- HASHDUMMY 配置（用于 HK 计算中的字段间分隔）
INSERT INTO [dbo].[CONFIGURATION] ([CONFIG_NAME], [CONFIG_VALUE], [DESCRIPTION])
VALUES ('HASHDUMMY', '@IAMHUSKIES@', 'Hash key 计算时字段间的填充串');

-- PSA 数据库名（默认值）
INSERT INTO [dbo].[CONFIGURATION] ([CONFIG_NAME], [CONFIG_VALUE], [DESCRIPTION])
VALUES ('PSA_DB', 'STAGE', 'PSA 层数据库名称');
```

---

## 四、PSA Type 2 数据流详解

### 4.1 数据流全貌

对于每个源表 `xxx`，生成以下数据库对象及数据流：

```
源表 (STAGE.dbo.xxx)
    │
    ▼  USP_xxx_STG  (全量刷新到 STG)
┌───────────────────┐
│  xxx_STG          │  ← 临时表：源数据 + 技术字段 (LOAD_DTS, REC_SRC, HK, 等)
│  (INSERT ONLY)    │
└───────┬───────────┘
        │
        ▼  USP_xxx_CDC  (变更数据捕获)
┌───────────────────┐
│  xxx_CDC          │  ← 变更表：通过 LAG/LEAD 比对标记 I/U/D
│  (CDC_OPERATION)  │
└───────┬───────────┘
        │
        ▼  USP_xxx_LOG (MERGE → LOG)
┌───────────────────┐
│  xxx_LOG          │  ← 历史全量表：SCD Type 2
│                    │    含 VALID_FROM, VALID_TO, IS_CURRENT
└───────┬───────────┘
        │
        ▼  Views
┌───────────────────┐
│ V_xxx_MTA         │  ← 带 Hash Key 的当前数据视图（从源表直接构建）
│ V_xxx_LOG_CURRENT │  ← LOG 表中的最新快照视图
└───────────────────┘
```

### 4.2 各组件功能说明

#### xxx_STG（临时表）

PSA 的第一层，将源表数据加载并附加技术字段：

| 字段 | 说明 |
|------|------|
| `LOAD_DTS` | 加载时间戳，默认 `GETDATE()` |
| `REC_SRC` | 登记源名称，默认 `'dbo'` |
| `REC_PATH` | 来源标识，默认 `'[schema].[table]'` |
| `TRANSFER_DTS` | 传输时间戳 |
| `HK` | Hash Key（所有业务字段的 MD5 拼接） |
| `... 业务字段 ...` | 源表所有 BK + DI 字段 |

#### xxx_CDC（变更数据捕获表）

通过与 LOG 表比对，标记每条记录的变更类型：

| 字段 | 说明 |
|------|------|
| `CDC_OPERATION_CODE` | `I`=新增, `U`=更新, `D`=删除 |
| 其他字段 | 与 STG 保持一致 + 各版本 Hash |

**CDC 判定逻辑**：

| 操作 | 条件 |
|------|------|
| **I (Insert)** | LAG 为 NULL，且数据来自 CDC（新增） |
| **U (Update)** | LAG_HF <> HF 且 LAG_HF 非 NULL（数据变更） |
| **D (Delete)** | LEAD 为 NULL，表示源已删除 |

#### xxx_LOG（历史全量表）

SCD Type 2 缓慢变化维处理，记录完整数据历史：

| 技术字段 | 说明 |
|---------|------|
| `HK` | Hash Key（业务键的 MD5） |
| `HF` | Hash Full（整行数据的 MD5，用于比对变化） |
| `LOAD_DTS` | 加载时间 |
| `VALID_FROM` | 生效起始时间 |
| `VALID_TO` | 生效结束时间（默认 `'2199-12-31'`） |
| `IS_CURRENT` | 是否当前版本（1/0） |

**MERGE 逻辑**：使用 `MERGE` 语句，将 CDC 变更合并到 LOG 表中，关闭旧版本，插入新版本。

#### 视图

| 视图 | 说明 |
|------|------|
| `V_xxx_MTA` | 从源表构建：源数据 + 计算 HK，用于后续 DV 层的数据入口 |
| `V_xxx_LOG_CURRENT` | 从 LOG 表取最新版本：`WHERE IS_CURRENT = 1` |

### 4.3 Hash Key 计算

```
HK = CONVERT(CHAR(32), HASHBYTES('MD5',
    ISNULL(TRIM(CONVERT(NVARCHAR(255), [BK_FIELD1])), N'') + N'@HASHDUMMY@'
    + ISNULL(TRIM(CONVERT(NVARCHAR(255), [BK_FIELD2])), N'') + N'@HASHDUMMY@'
), 2)
```

后端提供等价 Python 工具函数用于验证/测试：

```python
def compute_hash_key(*fields: str, hash_tail: str = "@IAMHUSKIES@") -> str:
    raw = ''.join(
        f"{str(field).strip()}{hash_tail}" if field is not None else hash_tail
        for field in fields
    )
    return hashlib.md5(raw.encode('utf-8')).hexdigest().upper()
```

---

## 五、代码生成引擎设计

### 5.1 模板架构（Jinja2）

沿用原始项目的模板思想，使用 Jinja2 作为模板引擎：

```
backend/app/templates/
└── psa/
    ├── stg_table.sql.j2       -- STG 建表
    ├── cdc_table.sql.j2       -- CDC 建表
    ├── log_table.sql.j2       -- LOG 建表
    ├── v_mta.sql.j2           -- MTA 视图
    ├── v_log_current.sql.j2   -- LOG_CURRENT 视图
    ├── usp_stg.sql.j2         -- STG 加载存储过程
    ├── usp_cdc.sql.j2         -- CDC 存储过程
    ├── usp_log.sql.j2         -- LOG 存储过程
    └── execute_flow.sql.j2    -- 全流程执行脚本
```

### 5.2 元数据模型

与原始项目的元数据类一一对应：

```python
class MetaTable:
    object_name: str        # 表名（如 CUSTOMER）
    schema_name: str        # 模式名（如 dbo）
    record_source: str      # 登记源
    is_full_load: bool      # 是否全量加载
    pk_fields: list[Field]  # Primary Key 字段
    bk_fields: list[Field]  # Business Key 字段（HK 计算依据）
    di_fields: list[Field]  # Descriptive Info 字段

class Field:
    field_name: str
    field_type: str         # SQL Server 类型字符串（如 NVARCHAR(255)）
```

### 5.3 生成器接口

```python
class PSAGenerator:
    """PSA Type 2 全套代码生成器"""

    def __init__(self, meta_tables: list[MetaTable],
                 psa_db_name: str, hash_tail: str):
        ...

    def generate_stg_table(self) -> str  # CREATE TABLE xxx_STG
    def generate_cdc_table(self) -> str  # CREATE TABLE xxx_CDC
    def generate_log_table(self) -> str  # CREATE TABLE xxx_LOG
    def generate_v_mta(self) -> str      # CREATE VIEW V_xxx_MTA
    def generate_v_current(self) -> str  # CREATE VIEW V_xxx_LOG_CURRENT
    def generate_usp_stg(self) -> str    # CREATE PROCEDURE USP_xxx_STG
    def generate_usp_cdc(self) -> str    # CREATE PROCEDURE USP_xxx_CDC
    def generate_usp_log(self) -> str    # CREATE PROCEDURE USP_xxx_LOG
    def generate_execute_flow(self) -> str  # 全流程执行脚本
```

### 5.4 模板示例（STG 表）

```jinja2
USE [{{ psa_db_name }}]
GO

{% for table in tables %}
CREATE TABLE [{{ table.schema_name }}].[{{ table.object_name }}_STG](
    [LOAD_DTS] DATETIME NOT NULL DEFAULT GETDATE(),
    [REC_SRC] NVARCHAR(15) NOT NULL DEFAULT '{{ table.record_source }}',
    [REC_PATH] NVARCHAR(256) NULL DEFAULT '{{ table.schema_name }}.{{ table.object_name }}',
    [TRANSFER_DTS] DATETIME NULL DEFAULT GETDATE(),
    [HK] CHAR(32) NULL,
    {% for f in table.pk_fields %}
    [{{ f.field_name }}] {{ f.field_type }} NULL,
    {% endfor %}
    {% for f in table.bk_fields %}
    [{{ f.field_name }}] {{ f.field_type }} NULL,
    {% endfor %}
    {% for f in table.di_fields %}
    [{{ f.field_name }}] {{ f.field_type }} NULL{% if not loop.last %},{% endif %}
    {% endfor %}
) ON [PRIMARY]
GO

{% endfor %}
```

---

## 六、项目目录结构

dwh-generator/
├── frontend/                          # Vue3 前端
│   ├── src/
│   │   ├── api/                       # API 调用封装
│   │   │   ├── connections.ts
│   │   │   ├── meta.ts
│   │   │   ├── config.ts
│   │   │   ├── generator.ts
│   │   │   └── deploy.ts
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AppSidebar.vue
│   │   │   │   └── AppHeader.vue
│   │   │   ├── connection/
│   │   │   │   ├── ConnectionForm.vue
│   │   │   │   └── ConnectionList.vue
│   │   │   ├── meta/
│   │   │   │   ├── MetaImport.vue
│   │   │   │   ├── FieldConfig.vue
│   │   │   │   └── FieldTable.vue
│   │   │   ├── generator/
│   │   │   │   ├── GeneratePanel.vue
│   │   │   │   └── ScriptPreview.vue
│   │   │   ├── deploy/
│   │   │   │   ├── DeployPanel.vue
│   │   │   │   └── ExecutionLog.vue
│   │   │   └── dv/                    # (预留) DV 配置组件
│   │   ├── views/
│   │   │   ├── DashboardView.vue
│   │   │   ├── ConnectionView.vue
│   │   │   ├── MetaImportView.vue
│   │   │   ├── MetaConfigView.vue
│   │   │   ├── GenerateView.vue
│   │   │   └── DeployView.vue
│   │   ├── stores/                    # Pinia 状态管理
│   │   │   ├── connection.ts
│   │   │   ├── meta.ts
│   │   │   └── generator.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── router/
│   │   │   └── index.ts
│   │   └── App.vue
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                           # FastAPI 后端
│   ├── main.py                         # 入口：python main.py
│   ├── app/
│   │   ├── config.py
│   │   ├── database.py                # SQLAlchemy + pymssql/pyodbc
│   │   ├── models/
│   │   │   ├── meta.py                # META 表 ORM 模型
│   │   │   ├── connection.py
│   │   │   └── log.py
│   │   ├── schemas/                   # Pydantic 请求/响应模型
│   │   │   ├── connection.py
│   │   │   ├── meta.py
│   │   │   └── generator.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── connections.py
│   │   │   ├── meta_import.py
│   │   │   ├── meta_config.py
│   │   │   ├── generator.py
│   │   │   ├── deploy.py
│   │   │   └── logs.py
│   │   ├── services/
│   │   │   ├── meta_service.py
│   │   │   ├── template_engine.py     # Jinja2 模板引擎
│   │   │   ├── generator_psa.py       # PSA Type 2 生成逻辑
│   │   │   ├── sql_executor.py        # SQL 执行器（GO 分割 + 事务）
│   │   │   └── hash_utils.py          # MD5 Hash Key 工具
│   │   └── templates/
│   │       └── psa/                   # Jinja2 模板文件
│   ├── main.py                         # 入口：python main.py
│   ├── meta_deploy.sql                # META 数据库初始化脚本（一键执行）
│   ├── requirements.txt
│   └── .env                           # 数据库配置
│
├── DESIGN.md
└── README.md
```

---

## 七、API 设计

### 7.1 连接管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/connections` | 获取所有连接配置 |
| POST | `/api/connections` | 创建连接配置 |
| PUT | `/api/connections/{id}` | 更新连接配置 |
| DELETE | `/api/connections/{id}` | 删除连接配置 |
| POST | `/api/connections/{id}/test` | 测试数据库连接 |

### 7.2 元数据导入

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/meta/tables?conn_id={id}` | 获取源库所有表 |
| GET | `/api/meta/columns?conn_id={id}&table={t}` | 获取指定表列信息（INFORMATION_SCHEMA） |
| POST | `/api/meta/import` | 导入表元数据到 META.ATTRIBUTE |
| GET | `/api/meta/attributes` | 获取 META 中已导入的列属性 |
| PUT | `/api/meta/attributes/{id}` | 更新字段角色配置 (BK/PK/DI) |
| PUT | `/api/meta/attributes/batch` | 批量更新字段角色配置 |

### 7.3 对象列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/objects` | 获取对象列表（含生成开关） |
| POST | `/api/objects/init` | 初始化对象列表（全量导入未配置的表） |
| PUT | `/api/objects/{id}` | 更新单个对象生成开关 |
| PUT | `/api/objects/batch` | 批量更新对象配置（IS_GEN / IS_FULL_LOAD） |

### 7.4 代码生成（PSA Type 2）

| 方法 | 路径 | 返回 |
|------|------|------|
| POST | `/api/generate/psa/stg` | STG 建表 SQL |
| POST | `/api/generate/psa/cdc` | CDC 建表 SQL |
| POST | `/api/generate/psa/log` | LOG 建表 SQL |
| POST | `/api/generate/psa/views` | MTA + LOG_CURRENT 视图 SQL |
| POST | `/api/generate/psa/usps` | USP_STG + USP_CDC + USP_LOG 存储过程 SQL |
| POST | `/api/generate/psa/all` | 上述全部 SQL（按依赖顺序拼接） |
| POST | `/api/generate/psa/flow` | 全流程执行脚本 |

### 7.5 部署

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/deploy/psa` | 部署全套 PSA 对象到目标库 |
| POST | `/api/deploy/sql` | 执行自定义 SQL（传递 SQL 文本） |
| GET | `/api/deploy/status` | 检查目标库中已部署的表/视图/存储过程状态 |

### 7.6 配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/config` | 获取所有配置参数（如 HASHDUMMY, PSA_DB 等） |
| PUT | `/api/config` | 更新配置参数 |

### 7.7 日志

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/logs` | 获取执行日志（分页） |
| DELETE | `/api/logs` | 清空日志 |

---

## 八、用户操作流程

```
┌────────────────────────────────────────────────────────────────────┐
│  1. 配置数据库连接                                                     │
│     ├─ 连接 META 数据库（新建 SQL Server 数据库）                        │
│     ├─ 连接源数据库（读取表的列结构）                                     │
│     └─ 连接目标 DWH 数据库（部署生成的 PSA 脚本）                         │
├────────────────────────────────────────────────────────────────────┤
│  2. 导入元数据                                                        │
│     ├─ 选择源数据库 → 浏览表 → 选择首张 PSA 表                           │
│     ├─ 系统自动读取该表的列信息（从 INFORMATION_SCHEMA）                   │
│     ├─ 校验技术字段是否齐全                                             │
│     └─ 导入到 META 数据库的 ATTRIBUTE 表                                │
├────────────────────────────────────────────────────────────────────┤
│  3. 配置字段角色                                                       │
│     ├─ 表格显示所有已导入的列                                           │
│     ├─ 标记 BK（Business Key → 用于 HK 计算）                           │
│     ├─ 标记 PK（Primary Key → PSA 主键）                               │
│     ├─ 标记 DI（Descriptive Info → 常规业务字段）                        │
│     ├─ 支持批量操作：清除所有 / 全选 BK / 智能推荐                        │
│     └─ 点击"保存"写入 META 库                                          │
├────────────────────────────────────────────────────────────────────┤
│  4. 管理对象列表                                                       │
│     ├─ 初始化对象列表（将已导入元数据的表纳入生成清单）                      │
│     ├─ 配置每张表的加载方式（全量/增量）                                  │
│     └─ 选择需要生成代码的对象                                            │
├────────────────────────────────────────────────────────────────────┤
│  5. 生成代码                                                          │
│     ├─ 选择要生成的组件（STG / CDC / LOG / Views / USPs）              │
│     ├─ 或一键生成全部                                                  │
│     ├─ 预览生成的 SQL（Monaco Editor 语法高亮 + 复制）                   │
│     └─ 下载 SQL 脚本文件                                               │
├────────────────────────────────────────────────────────────────────┤
│  6. 部署执行                                                          │
│     ├─ 选择目标数据库 → 点击部署                                        │
│     ├─ 按顺序执行：表 → 视图 → 存储过程                                  │
│     ├─ SQL 以 GO 分割，逐批在事务中执行                                  │
│     ├─ 实时查看执行进度与日志                                            │
│     └─ 部署失败时高亮错误 SQL 并显示详细错误信息                          │
└────────────────────────────────────────────────────────────────────┘
```

---

## 九、关键技术点

### 9.1 多数据库连接管理

```python
# FastAPI 中使用 SQLAlchemy 动态连接 SQL Server
# 每个连接配置对应一个独立的 Engine 实例
DATABASE_URL_TEMPLATE = "mssql+pymssql://{user}:{password}@{host}:{port}/{dbname}"
```

- 用户配置多个数据库连接（源库 / META 库 / 目标库）
- 后端根据连接 ID 动态创建 Engine 并缓存
- 连接测试通过 `SELECT 1` 验证连通性

### 9.2 SQL 批处理执行

```python
def execute_sql_batch(sql: str, connection_id: int):
    """按 GO 分割 SQL，逐批在事务中执行"""

    statements = re.split(r'\bGO\b', sql, flags=re.IGNORECASE)
    engine = get_engine(connection_id)

    with engine.begin() as conn:   # 自动事务
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
```

### 9.3 源表结构读取

```python
# 从 SQL Server INFORMATION_SCHEMA 读取列元数据
SELECT
    COLUMN_NAME, DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table
ORDER BY ORDINAL_POSITION
```

### 9.4 密码安全

数据库密码使用 `cryptography.fernet` 对称加密后存储，密钥从环境变量 `META_SECRET_KEY` 读取。

### 9.5 模板引擎封装

使用 Jinja2 的 `Environment` + `FileSystemLoader` 加载模板目录，缓存已编译模板：

```python
class TemplateEngine:
    def __init__(self, template_dir: str):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            keep_trailing_newline=True
        )

    def render(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return template.render(**context)
```

---

## 十、开发路线图

| 阶段 | 内容 | 预估工日 |
|------|------|----------|
| **Phase 1** | 项目初始化、META 数据库 DDL、后端基础框架 | 2 天 |
| **Phase 2** | 数据库连接管理（CRUD + 连接测试） | 1 天 |
| **Phase 3** | 元数据导入（读取 INFORMATION_SCHEMA → 写入 META） | 2 天 |
| **Phase 4** | 字段配置 UI + 对象列表管理 | 1.5 天 |
| **Phase 5** | PSA Type 2 模板开发 + 代码生成引擎 | 3 天 |
| **Phase 6** | SQL 执行器 + 部署功能 | 2 天 |
| **Phase 7** | 前端界面开发（Dashboard / 连接 / 导入 / 配置 / 生成 / 部署） | 4 天 |
| **Phase 8** | 集成测试 + 完善日志 + 文档 | 1.5 天 |
| **总计** | | **约 17 天** |

### 后续迭代

| 版本 | 内容 |
|------|------|
| **v2.0** | Data Vault 2.0 支持（HUB / SAT / LINK 生成与部署） |
| **v2.1** | 多用户支持（如有需要） |
| **v2.2** | 生成结果的版本对比与回滚 |

---

## 十一、环境与依赖

### 后端

```
Python 3.11+
FastAPI
SQLAlchemy 2.0
pymssql / pyodbc        # SQL Server 连接驱动
Jinja2                   # 模板引擎
Pydantic v2
Alembic                  # 数据库迁移
cryptography             # 密码加密
python-multipart
uvicorn
```

### 前端

```
Vue 3 + TypeScript
Vite
Pinia                    # 状态管理
Vue Router
Element Plus             # UI 组件库
Monaco Editor            # SQL 编辑器（语法高亮）
Axios                    # HTTP 客户端
```

### 部署

```
Node.js 18+ (前端构建)
SQL Server 2019+ (META 库 + 目标 DWH 库)
```