# Data Vault Generator 重构设计方案

## 基于 Vue3 + FastAPI + SQL Server（PSA Type 2 + Data Vault 2.0）

---

## 一、项目概述

### 1.1 原始项目功能

本系统基于 [DWH-Generator](https://github.com/microsoftbi/DWH-Generator) 重构，是一个**数据仓库元数据驱动的自动代码生成工具**，遵循 **PSA（持久化临时区）+ Data Vault 2.0** 方法论。它通过读取源表的列元数据，自动生成全套 DWH 建表脚本、视图和存储过程。

> 原始技术栈：C# WinForms (.NET 4.5.2) + SQL Server + Handlebars.NET

### 1.2 重构目标

使用 **Vue3 + FastAPI + SQL Server** 重构，构建一个 **Web 版** DWH 生成器，功能与原始工具对等，并增加更好的用户体验（暗色主题、多语言、数据预览等）。

### 1.3 核心流程

```
Source OLTP → 导入元数据 → 配置字段角色 (BK/PK/DI/FK)
    → DV 自动配置（可选） → 生成 PSA Type 2 / DV 2.0 SQL 脚本
    → 预览 → (可选) 部署执行到目标库
```

---

## 二、整体架构

```
┌───────────────────────────────────────────────────────────────────┐
│                       Frontend (Vue3)                            │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐           │
│  │ 连接配置 │ │ 元数据导入 │ │ 字段配置  │ │ DV 配置   │           │
│  └─────────┘ └──────────┘ └──────────┘ └───────────┘           │
│  ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐          │
│  │ PSA 生成  │ │ DV 生成  │ │ 部署执行  │ │ 数据预览  │          │
│  └───────────┘ └──────────┘ └──────────┘ └───────────┘          │
│  ┌───────────┐ ┌──────────┐                                      │
│  │ 执行日志  │ │ 系统概览  │                                      │
│  └───────────┘ └──────────┘                                      │
└──────────────────────────┬────────────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼────────────────────────────────────────┐
│                      Backend (FastAPI)                            │
│  ┌──────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │ 连接管理  │ │ 元数据导入API │ │ 配置管理API  │ │ PSA 生成引擎 │ │
│  └──────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │
│  ┌──────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │ DV 生成  │ │ SQL执行器    │ │ 日志服务     │ │ 模板引擎     │ │
│  └──────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │
│  ┌──────────┐ ┌──────────────┐                                    │
│  │ 角色绑定 │ │ 数据预览     │                                    │
│  └──────────┘ └──────────────┘                                    │
└────────────┬──────────────────────────────┬───────────────────────┘
             │                              │
             ▼                              ▼
     ┌──────────────┐             ┌──────────────────┐
     │  META 数据库  │             │ 目标 DWH 数据库   │
     │  (SQLite)     │             │  (SQL Server)     │
     │  元数据配置    │             │ PSA(STAGE) /     │
     │  自动创建      │             │ CORE / OLTP(源)  │
     └──────────────┘             └──────────────────┘
```

### 2.1 前端功能模块

| 模块 | 功能 |
|------|------|
| 数据库连接管理 | 配置数据库连接信息（CRUD + 测试连接） |
| 数据库角色绑定 | 将连接映射到 OLTP / STAGE / CORE 三种角色 |
| 元数据导入 | 选择源表，导入列信息到 META 数据库（分步向导） |
| 字段配置 | 标记字段角色：BK(业务键)、PK(主键)、DI(描述信息)、FK(外键) |
| DV 配置 | 手动/自动创建 HUB / SAT / LINK 表并绑定字段 |
| 代码生成（PSA） | 生成 PSA Type 2 全套 SQL（STG/CDC/LOG/Views/USPs/Flow） |
| 代码生成（DV） | 生成 Data Vault 2.0 SQL（HUB/SAT/LINK 表 + USP） |
| 部署执行 | 自动解析目标库，执行 SQL |
| 数据预览 | 三层（OLTP/STAGE/CORE）树导航，查表结构和前 500 行 |
| 执行日志 | 查看生成和执行日志 |
| 系统概览 | Dashboard 快速指引和状态概览 |

### 2.2 后端服务模块

| 模块 | 职责 |
|------|------|
| `api/connections` | 数据库连接 CRUD + 连接测试 |
| `api/meta_import` | 从源表导入列元数据到 META |
| `api/db_roles` | 数据库角色绑定（OLTP/STAGE/CORE） |
| `api/objects` | 对象列表管理 |
| `api/dv_config` | DV 自动/手动配置（HUB/SAT/LINK） |
| `api/generator` | PSA + DV 代码生成引擎入口 |
| `api/deploy` | SQL 执行器 + 配置管理 + 日志 |
| `api/data_preview` | 数据库对象浏览和数据预览 |
| `services/generator_psa` | PSA Type 2 生成逻辑 |
| `services/generator_dv` | Data Vault 2.0 生成逻辑 |
| `services/template_engine` | Jinja2 模板渲染引擎 |
| `services/sql_executor` | SQL 批处理执行（按 GO 分割 + 事务） |

---

## 三、数据库设计（SQLite）

### 3.1 META 数据库（配置库，SQLite）

使用 SQLite 本地文件，路径 `backend/data/meta.db`，启动时自动创建。

#### ATTRIBUTE — 列属性元数据

```sql
CREATE TABLE [ATTRIBUTE] (
    [ID] INTEGER PRIMARY KEY AUTOINCREMENT,
    [TABLE_CATALOG] VARCHAR(128),
    [TABLE_NAME] VARCHAR(128) NOT NULL,
    [COLUMN_NAME] VARCHAR(128) NOT NULL,
    [DATA_TYPE] VARCHAR(128),
    [CHARACTER_MAXIMUM_LENGTH] INTEGER,
    [NUMERIC_PRECISION] INTEGER,
    [NUMERIC_SCALE] INTEGER,
    [IS_BK] INTEGER DEFAULT 0,           -- Business Key（用于 HUB）
    [IS_PK] INTEGER DEFAULT 0,           -- Primary Key（PSA 主键 + LINK）
    [IS_DI] INTEGER DEFAULT 0,           -- Descriptive Info（用于 SAT）
    [IS_FK] INTEGER DEFAULT 0,           -- Foreign Key（用于 LINK）
    [DV_COLUMN_NAME] VARCHAR(50),        -- DV 中的列名别名
    [DV_HUB_ID] INTEGER,                 -- 关联的 HUB 表 ID
    [DV_SAT_ID] INTEGER,                 -- 关联的 SAT 表 ID
    [DV_LINK_ID] INTEGER,                -- 关联的 LINK 表 ID
    [RECORD_SRC] VARCHAR(64),              -- 来源标识（如 erp, crm）
    [CREATED_AT] DATETIME
);
```

#### OLTP_SOURCE — OLTP 源配置（多源支持）

```sql
CREATE TABLE [OLTP_SOURCE] (
    [ID] INTEGER PRIMARY KEY AUTOINCREMENT,
    [RECORD_SRC] VARCHAR(64) NOT NULL UNIQUE,  -- 来源别名（如 erp, crm）
    [CONN_ID] INTEGER NOT NULL,                -- 关联 CONNECTION_CONFIG.ID
    [DATABASE_NAME] VARCHAR(128) NOT NULL,     -- 源数据库名
    [CREATED_AT] DATETIME
);
```

#### DV_HUB / DV_SAT / DV_LINK — DV 对象表

```sql
CREATE TABLE [DV_HUB] (
    [ID] INTEGER PRIMARY KEY AUTOINCREMENT,
    [TABLE_NAME] VARCHAR(128) NOT NULL,
    [CREATED_AT] DATETIME
);
CREATE TABLE [DV_SAT] (
    [ID] INTEGER PRIMARY KEY AUTOINCREMENT,
    [TABLE_NAME] VARCHAR(128) NOT NULL,
    [CREATED_AT] DATETIME
);
CREATE TABLE [DV_LINK] (
    [ID] INTEGER PRIMARY KEY AUTOINCREMENT,
    [TABLE_NAME] VARCHAR(128) NOT NULL,
    [CREATED_AT] DATETIME
);
```

#### CONNECTION_CONFIG — 数据库连接配置

```sql
CREATE TABLE [CONNECTION_CONFIG] (
    [ID] INTEGER PRIMARY KEY AUTOINCREMENT,
    [NAME] VARCHAR(128) NOT NULL,
    [DB_TYPE] VARCHAR(32) DEFAULT 'sqlserver',
    [HOST] VARCHAR(255),
    [PORT] INTEGER DEFAULT 1433,
    [DATABASE_NAME] VARCHAR(128),
    [USERNAME] VARCHAR(128),
    [PASSWORD_ENCRYPTED] TEXT,          -- Fernet 加密
    [IS_META] INTEGER DEFAULT 0,
    [IS_SOURCE] INTEGER DEFAULT 0,
    [IS_TARGET] INTEGER DEFAULT 0,
    [CREATED_AT] DATETIME
);
```

#### DATABASE_ROLE — 角色绑定

```sql
CREATE TABLE [DATABASE_ROLE] (
    [ID] INTEGER PRIMARY KEY AUTOINCREMENT,
    [ROLE_NAME] VARCHAR(50) NOT NULL,  -- OLTP / STAGE / CORE
    [CONN_ID] INTEGER NOT NULL,        -- 关联 CONNECTION_CONFIG.ID
    [DATABASE_NAME] VARCHAR(128),      -- 该角色下的数据库名
    [CREATED_AT] DATETIME
);
```

#### GEN_LIST — 对象列表

```sql
CREATE TABLE [GEN_LIST] (
    [ID] INTEGER PRIMARY KEY AUTOINCREMENT,
    [TABLE_CATALOG] VARCHAR(128),
    [TABLE_NAME] VARCHAR(128) NOT NULL,
    [SCHEMA_NAME] VARCHAR(128) DEFAULT 'dbo',
    [IS_GEN] INTEGER DEFAULT 1,
    [IS_FULL_LOAD] INTEGER DEFAULT 0,
    [CREATED_AT] DATETIME
);
```

#### CONFIGURATION — 系统配置

```sql
CREATE TABLE [CONFIGURATION] (
    [ID] INTEGER PRIMARY KEY AUTOINCREMENT,
    [CONFIG_NAME] VARCHAR(128) NOT NULL UNIQUE,
    [CONFIG_VALUE] TEXT,
    [DESCRIPTION] VARCHAR(500)
);
INSERT INTO [CONFIGURATION] VALUES (NULL, 'PSA_DB', 'STAGE', 'PSA 层数据库名称');
INSERT INTO [CONFIGURATION] VALUES (NULL, 'CORE_DB', 'CORE', 'DV 层数据库名称');
INSERT INTO [CONFIGURATION] VALUES (NULL, 'HASHDUMMY', '@IAMHUSKIES@', 'Hash key 计算时字段间的填充串');
```

#### EXECUTION_LOG — 执行日志

```sql
CREATE TABLE [EXECUTION_LOG] (
    [ID] INTEGER PRIMARY KEY AUTOINCREMENT,
    [LOG_SOURCE] VARCHAR(255),
    [LOG_TYPE] CHAR(1) DEFAULT 'N',
    [MESSAGE] TEXT,
    [CREATED_AT] DATETIME
);
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
│  xxx_STG          │  ← 临时表：源数据 + 技术字段
│  (TRUNCATE+INSERT)│
└───────┬───────────┘
        │
        ▼  USP_xxx_CDC  (变更数据捕获)
┌───────────────────┐
│  xxx_CDC          │  ← 变更表：通过 LAG/LEAD 比对标记 I/U/D
│  (CDC_OPERATION)  │     双源比对（V_LOG_CURRENT + V_MTA）
└───────┬───────────┘
        │
        ▼  USP_xxx_LOG (INSERT FROM CDC)
┌───────────────────┐
│  xxx_LOG          │  ← 历史全量表（渐进式加载）
│                    │    无 IS_CURRENT / VALID_FROM / VALID_TO
│                    │    通过 MAX(LOAD_DTS) 取最新版本
└───────┬───────────┘
        │
        ▼  Views
┌───────────────────┐
│ V_xxx_MTA         │  ← 从 STG 构建：带 HK/HD/HF 的 MTA 视图
│ V_xxx_LOG_CURRENT │  ← LOG 表中每个 HK 最新版本视图（MAX(LOAD_DTS) 子查询）
└───────────────────┘
```

### 4.2 各组件功能说明

#### xxx_STG（临时表）

将源表数据加载并附加技术字段，使用 `TRUNCATE + INSERT` 全量刷新。

| 字段 | 说明 |
|------|------|
| `HK` | Hash Key（PK+BK 字段的 MD5 拼接） |
| `PK / BK / FK / DI` 字段 | 源表所有字段透传 |

#### xxx_CDC（变更数据捕获表）

双源比对：`V_LOG_CURRENT`（历史最新快照） + `V_MTA`（当前 STG 数据）= `UNION ALL`，通过 LAG/LEAD 分析 HF 变化检测 I/U/D。

**CDC 判定逻辑**：

| 操作 | 条件 |
|------|------|
| **I (Insert)** | LAG_HF 为 NULL，且 SOURCE_ENTITY = 'CDC' |
| **U (Update)** | LAG_HF <> HF 且 LAG_HF 非 NULL，且 SOURCE = 'CDC' |
| **D (Delete)** | LEAD_HF 为 NULL 且 SOURCE = 'HDA' 且 LOAD_TYPE = 'FULL' |

#### xxx_LOG（历史全量表）

渐进式历史表，无需 SCD Type 2 版本管理。通过 `MAX(LOAD_DTS)` 子查询获取每个 HK 的最新行。

| 字段 | 说明 |
|------|------|
| `LOAD_DTS` | 加载时间戳（DATETIMEOFFSET） |
| `SEQUENCE_NO` | 序号 |
| `CDC_OPERATION_CODE` | 变更类型（I/U/D） |
| `HK` / `HD` / `HF` | Hash Key / Data Hash / Full Hash |
| `PK / BK / FK / DI` 字段 | 源表所有字段 |

#### 视图

| 视图 | 说明 |
|------|------|
| `V_xxx_MTA` | 从 STG 构建：带 HK/HD/HF/SEQUENCE_NO 计算 |
| `V_xxx_LOG_CURRENT` | 从 LOG 表取每个 HK 最新版本：`MAX(LOAD_DTS) GROUP BY HK` |

### 4.3 Hash Key 计算

```
HK = CONVERT(CHAR(32), HASHBYTES('MD5',
    ISNULL(TRIM(CONVERT(NVARCHAR(255), [BK_FIELD1])), N'') + N'HASHDUMMY'
    + ISNULL(TRIM(CONVERT(NVARCHAR(255), [BK_FIELD2])), N'') + N'HASHDUMMY'
), 2)

HF = CONVERT(CHAR(32), HASHBYTES('MD5',
    + ISNULL(TRIM(CONVERT(NVARCHAR(255), [PK/BK_FIELD])), N'') + N'HASHDUMMY'
    + ISNULL(TRIM(CONVERT(NVARCHAR(255), [DI_FIELD])), N'') + N'HASHDUMMY'
), 2)  -- PK + BK + DI 全量指纹

HD = CONVERT(CHAR(32), HASHBYTES('MD5',
    + ISNULL(TRIM(CONVERT(NVARCHAR(255), [DI_FIELD1])), N'') + N'HASHDUMMY'
), 2)  -- 仅 DI 字段，用于变更检测
```

---

## 五、代码生成引擎设计

### 5.1 模板架构（Jinja2）

```
backend/app/templates/
├── psa/
│   ├── stg_table.sql.j2       -- STG 建表（含 PK/BK/FK/DI）
│   ├── cdc_table.sql.j2       -- CDC 建表（含 PK/BK/FK/DI）
│   ├── log_table.sql.j2       -- LOG 建表（含 PK/BK/FK/DI）
│   ├── v_mta.sql.j2           -- MTA 视图（HK/HF/HD 计算）
│   ├── v_log_current.sql.j2   -- LOG_CURRENT 视图
│   ├── usp_stg.sql.j2         -- STG 加载（TRUNCATE+INSERT 全量）
│   ├── usp_cdc.sql.j2         -- CDC 存储过程（LAG/LEAD 变更检测）
│   ├── usp_log.sql.j2         -- LOG 存储过程（INSERT FROM CDC）
│   └── execute_flow.sql.j2    -- 全流程执行脚本
└── dv/
    ├── hub_table.sql.j2       -- HUB 建表（DROP+CREATE）
    ├── sat_table.sql.j2       -- SAT 建表（含 HD 列）
    ├── link_table.sql.j2      -- LINK 建表（含 FK_HK）
    ├── usp_hub.sql.j2         -- HUB 加载（ROW_NUMBER + PK 拼接 JOIN）
    ├── usp_sat.sql.j2         -- SAT 加载（LAG HD 变更检测）
    └── usp_link.sql.j2        -- LINK 加载（含各 FK 独立 HK）
```

### 5.2 元数据模型

```python
class MetaTable:
    object_name: str        # 表名（如 CUSTOMER）
    schema_name: str        # 模式名（如 dbo）
    record_source: str      # 登记源
    is_full_load: bool      # 是否全量加载
    pk_fields: list[Field]  # Primary Key 字段
    bk_fields: list[Field]  # Business Key 字段（HK 计算依据）
    fk_fields: list[Field]  # Foreign Key 字段（PSA 透传 + LINK）
    di_fields: list[Field]  # Descriptive Info 字段（SAT + HD 计算）

class Field:
    field_name: str         # DV 目标列名（或源列名）
    psa_field_name: str     # PSA 源列名
    field_type: str         # SQL Server 类型字符串
```

### 5.3 生成器接口

```python
class PSAGenerator:
    def __init__(self, session, psa_db_name, hash_dummy, oltp_db_name=None): ...
    def generate_stg_table(self) -> str
    def generate_cdc_table(self) -> str
    def generate_log_table(self) -> str
    def generate_v_mta(self) -> str
    def generate_v_current(self) -> str
    def generate_usp_stg(self) -> str  # 带 oltp_db_name 三部分引用
    def generate_usp_cdc(self) -> str
    def generate_usp_log(self) -> str
    def generate_execute_flow(self) -> str

class DVGenerator:
    def __init__(self, session, psa_db_name, core_db_name, hash_tail): ...
    def generate_hub_table(self) -> str
    def generate_sat_table(self) -> str
    def generate_link_table(self) -> str
    def generate_usp_hub(self) -> str
    def generate_usp_sat(self) -> str
    def generate_usp_link(self) -> str
```

---

## 六、项目目录结构

```
dwh-generator/
├── frontend/
│   ├── src/
│   │   ├── api/                   # API 调用封装
│   │   ├── components/            # 公用组件
│   │   ├── views/                 # 12 个页面（DataPreviewView 支持 3 种模式）
│   │   │   ├── DashboardView.vue
│   │   │   ├── ConnectionView.vue
│   │   │   ├── MetaImportView.vue
│   │   │   ├── MetaConfigView.vue
│   │   │   ├── DvConfigView.vue
│   │   │   ├── GenerateConfigView.vue
│   │   │   ├── GeneratePsaView.vue
│   │   │   ├── GenerateDvView.vue
│   │   │   ├── DataPreviewView.vue
│   │   │   ├── DeployView.vue
│   │   │   └── LogsView.vue
│   │   ├── stores/                # Pinia 状态管理
│   │   ├── styles/                # 暗色主题 CSS
│   │   ├── i18n/                  # en / zh-CN
│   │   ├── types/                 # TypeScript 类型
│   │   └── router/index.ts
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── main.py                    # 入口：python main.py
│   ├── app/
│   │   ├── config.py
│   │   ├── database.py            # SQLite(SQLAlchemy) + SQL Server(pyodbc)
│   │   ├── models/meta.py         # ORM 模型（Attribute, DatabaseRole 等）
│   │   ├── models/oltp_source.py # OltpSource 多 OLTP 源模型
│   │   ├── schemas/__init__.py    # Pydantic 模型
│   │   ├── api/
│   │   │   ├── connections.py
│   │   │   ├── meta_import.py
│   │   │   ├── objects.py
│   │   │   ├── dv_config.py
│   │   │   ├── generator.py
│   │   │   ├── deploy.py
│   │   │   ├── data_preview.py
│   │   │   ├── db_roles.py
│   │   │   └── oltp_sources.py
│   │   ├── services/
│   │   │   ├── generator_psa.py
│   │   │   ├── generator_dv.py
│   │   │   ├── template_engine.py
│   │   │   ├── meta_service.py
│   │   │   ├── sql_executor.py
│   │   │   └── runtime_sql.py
│   │   └── templates/
│   │       ├── psa/               # 9 个模板
│   │       └── dv/                # 6 个模板
│   ├── data/                      # SQLite META 数据库
│   ├── requirements.txt
│   └── .env
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
| POST | `/api/connections` | 创建（密码 Fernet 加密） |
| PUT | `/api/connections/{id}` | 更新 |
| DELETE | `/api/connections/{id}` | 删除 |
| POST | `/api/connections/test` | 测试连接（未保存） |
| POST | `/api/connections/{id}/test` | 测试已保存连接 |

### 7.2 角色绑定

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/db-roles` | 获取 OLTP/STAGE/CORE 角色绑定 |
| PUT | `/api/db-roles` | 更新角色绑定 |

### 7.3 元数据导入

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/meta/oltp-source` | 获取 OLTP 角色绑定的连接信息 |
| GET | `/api/meta/tables` | 获取源库表列表 |
| GET | `/api/meta/columns` | 获取表列信息 |
| POST | `/api/meta/import` | 导入单表元数据 |
| POST | `/api/meta/import-bulk` | 批量导入多表 |
| GET | `/api/meta/attributes` | 获取已导入字段 |
| PUT | `/api/meta/attributes/{id}` | 更新字段角色 |
| PUT | `/api/meta/attributes/batch` | 批量更新 |

### 7.4 DV 配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/dv/hubs` | 获取 HUB 列表 |
| POST | `/api/dv/hubs` | 新建 HUB |
| DELETE | `/api/dv/hubs/{id}` | 删除 HUB |
| GET | `/api/dv/sats` | 获取 SAT 列表 |
| POST | `/api/dv/sats` | 新建 SAT |
| DELETE | `/api/dv/sats/{id}` | 删除 SAT |
| GET | `/api/dv/links` | 获取 LINK 列表 |
| POST | `/api/dv/links` | 新建 LINK |
| DELETE | `/api/dv/links/{id}` | 删除 LINK |
| POST | `/api/dv/auto-configure` | 自动创建 HUB/SAT/LINK 并绑定字段 |

### 7.5 代码生成

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/generate/psa/*` | 7 个端点：stg/cdc/log/views/usps/all/flow |
| POST | `/api/generate/dv/*` | 7 个端点：hub/sat/link/usp-hub/usp-sat/usp-link/all |

### 7.6 部署

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/deploy/runtime` | 部署运行时组件到 STAGE |
| POST | `/api/deploy/psa` | 生成+部署全套 PSA 到 STAGE |
| POST | `/api/deploy/dv` | 生成+部署全套 DV 到 CORE |
| POST | `/api/deploy/sql` | 执行自定义 SQL |
| POST | `/api/deploy/execute` | 执行 SQL 到指定角色库 |
| GET | `/api/deploy/status` | 检查目标库对象状态 |

### 7.7 OLTP 源管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/oltp-sources` | 获取所有 OLTP 源 |
| POST | `/api/oltp-sources` | 新增 OLTP 源 |
| PUT | `/api/oltp-sources/{id}` | 更新 OLTP 源 |
| DELETE | `/api/oltp-sources/{id}` | 删除 OLTP 源 |

### 7.8 数据预览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/preview/databases` | 获取 OLTP/STAGE/CORE 库信息 |
| GET | `/api/preview/objects` | 获取库下表/视图/存储过程 |
| GET | `/api/preview/columns` | 获取列结构 |
| GET | `/api/preview/data` | 获取前 500 行数据 |
| GET | `/api/preview/meta/tables` | 获取 META 配置库表列表 |
| GET | `/api/preview/meta/columns` | 获取 META 配置库列结构 |
| GET | `/api/preview/meta/data` | 获取 META 配置库前 500 行数据 |

### 7.9 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/config` | 获取系统配置 |
| PUT | `/api/config` | 更新配置 |
| GET | `/api/objects` | 对象列表 |
| POST | `/api/objects/init` | 初始化对象列表 |
| GET | `/api/logs` | 执行日志 |
| DELETE | `/api/logs` | 清空日志 |
| GET | `/api/health` | 健康检查 |

---

## 八、用户操作流程

```
 1. 配置数据库连接
    ├─ 添加源库 / STAGE 库 / CORE 库 连接信息
    ├─ 在角色绑定页面将连接映射到 STAGE / CORE 角色
    └─ 在 OLTP 源管理中配置源数据库（record_src + 连接 + 数据库名）

 2. 导入元数据
    ├─ 选择 OLTP 源库 → 浏览表 → 选择要导入的表
    ├─ 选择导入哪些列（左→右导入，右→左移除）
    └─ 确认导入

 3. 配置字段角色
    ├─ 标记 BK（Business Key → HUB HK 计算）
    ├─ 标记 PK（Primary Key → PSA 主键 + LINK 关联）
    ├─ 标记 DI（Descriptive Info → SAT 属性 + HD 计算）
    └─ 标记 FK（Foreign Key → LINK 关联）

 4. DV 配置（可选）
    ├─ 点击"自动配置"根据字段标记自动创建 HUB/SAT/LINK
    └─ 在字段映射中手动调整绑定关系

 5. 生成代码
    ├─ PSA Type 2：选择组件预览 / 一键全部生成
    ├─ Data Vault 2.0：选择组件预览 / 一键全部生成
    ├─ 支持复制、下载
    └─ 支持直接 Execute 到目标库

 6. 部署执行
    ├─ 自动解析 PSA→STAGE、DV→CORE 目标连接
    ├─ 支持全部部署 / 运行时组件部署 / 自定义 SQL
    └─ 实时查看部署日志

 7. 数据预览
    ├─ **OLTP 库**：浏览所有 OLTP 源的表数据
    ├─ **数据仓库**：STAGE / CORE 层树导航
    ├─ **配置库**：META 数据库 SQLite 表结构 + 数据浏览
    └─ 查看表结构和前 500 行数据
```

---

## 九、关键技术点

### 9.1 数据库连接管理

- 连接配置存储在 SQLite META 库
- 密码使用 `cryptography.fernet` 对称加密（密钥从 `SECRET_KEY` 派生）
- 成功测试的连接在内存中缓存 Engine
- 角色绑定（DATABASE_ROLE）将连接映射为 OLTP/STAGE/CORE 三种逻辑角色

### 9.2 SQL 批处理执行

```python
# 按 GO 分割，逐批在事务中执行
statements = re.split(r'\bGO\b', sql, flags=re.IGNORECASE)
with engine.begin() as conn:
    for stmt in statements:
        if stmt.strip():
            conn.execute(text(stmt))
```

### 9.3 CDC 双源比对

USP_CDC 使用 `V_LOG_CURRENT` + `V_MTA` 的 UNION ALL 作为输入：
- `V_LOG_CURRENT`（HK 的最新版本）→ 标记为 `HDA`（历史数据）
- `V_MTA`（当前 STG 的全量数据）→ 标记为 `CDC`（当前数据）
- 通过 `LAG(HF) / LEAD(HF) OVER (PARTITION BY HK ORDER BY ...)` 检测变更

### 9.4 USP_SAT 三重变更检测

- `VALUE_CHANGE_INDICATOR`：LAG(HD) 比对，检测 DI 字段是否变化
- `CDC_CHANGE_INDICATOR`：CDC_OPERATION_CODE 是否变化
- `TIME_CHANGE_INDICATOR`：下一行 LOAD_DTS 是否存在

### 9.5 USP_LINK FK_HK 计算

每个 FK 字段除了原始值，还独立计算 `[field_name]_HK`（使用 `@|@` 分隔符），作为对各 HUB 的引用键。

---

## 十、开发环境

### 后端

```
Python 3.11+
FastAPI 0.115
SQLAlchemy 2.0
pyodbc 5.1              # SQL Server 连接驱动
Jinja2 3.1               # 模板引擎
Pydantic v2 + settings
cryptography             # 密码加密
uvicorn
```

### 前端

```
Vue 3 + TypeScript + Vite
Pinia                    # 状态管理
Vue Router
Element Plus             # UI 组件库
vue-i18n@9               # 国际化
Axios                    # HTTP 客户端
highlight.js             # SQL 语法高亮
```

### 部署

```
Node.js 18+ (前端构建)
SQL Server 2019+ (目标 DWH 库)
SQLite (META 配置库，自动管理)
```