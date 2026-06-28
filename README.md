# DWH-Generator

基于 Vue3 + FastAPI + SQLite/SQL Server 的 **PSA Type 2 + Data Vault 2.0** 数据仓库代码生成器。

## 快速启动

### 1. 后端（自动创建 META 库，无需手动部署）

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py                     # 热重载模式，http://localhost:8000
```

META 配置库使用 SQLite 自动创建于 `backend/data/meta.db`，无需单独部署数据库。

API 文档：`http://localhost:8000/docs`

### 2. 前端

```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

## 项目目录

```
dwh-generator/
├── backend/
│   ├── app/
│   │   ├── api/           # REST API 路由
│   │   ├── models/        # SQLAlchemy ORM 模型（SQLite）
│   │   ├── schemas/       # Pydantic 请求/响应模型
│   │   ├── services/      # 核心业务逻辑
│   │   └── templates/
│   │       ├── psa/         # PSA Type 2 Jinja2 模板（9个）
│   │       └── dv/          # Data Vault 2.0 Jinja2 模板（6个）
│   ├── data/              # SQLite META 数据库（自动创建）
│   ├── main.py            # 入口：python main.py（热重载）
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── views/         # 11 个页面
│   │   ├── api/           # API 调用封装
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── styles/        # 暗色主题 CSS
│   │   ├── i18n/          # 中文/英文国际化
│   │   ├── types/         # TypeScript 类型
│   │   └── router/        # 路由
│   ├── package.json
│   └── vite.config.ts
├── DESIGN.md
└── README.md
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Element Plus + Pinia + vue-i18n |
| 后端 | FastAPI + SQLAlchemy 2.0 + Jinja2 |
| 配置库 | SQLite（自动创建，无需部署） |
| 目标 DWH | SQL Server（用户配置的连接） |

## 功能

### 基础
- [x] 数据库连接管理（CRUD + 测试连接 + Fernet 密码加密）
- [x] 数据库角色绑定（OLTP 源 / STAGE 层 / CORE 层 分别映射）
- [x] 元数据导入（SQL Server INFORMATION_SCHEMA → META）
- [x] 字段角色配置（BK 业务键 / PK 主键 / DI 描述信息 / FK 外键）
- [x] 对象列表管理（生成开关 + 全量/增量标记）
- [x] 多语言支持（中文 + 英文）
- [x] 暗色主题（Claude Code 风格）

### PSA Type 2
- [x] PSA 全套 SQL 生成（STG → CDC → LOG → Views → USPs → 全流程）
- [x] 变更数据捕获（双源比对：V_LOG_CURRENT + V_MTA UNION ALL，LAG/LEAD HF 检测 I/U/D）
- [x] 渐进式加载类型（FULL / CDC 模式自动识别）
- [x] 每个 Tab 页的 Execute 按钮（直接部署到 STAGE 库）
- [x] FK 字段全链路透传（STG / CDC / LOG / Views / USPs）

### Data Vault 2.0
- [x] DV 自动配置（BK → HUB, DI → SAT, FK/PK → LINK 自动创建并绑定字段）
- [x] HUB 表 + USP_HUB 生成
- [x] SAT 表 + USP_SAT 生成（含 HD 变更指纹 + LAG 三重检测）
- [x] LINK 表 + USP_LINK 生成（含各 FK 独立 HK）
- [x] 每个 Tab 页的 Execute 按钮（直接部署到 CORE 库）

### 部署与运维
- [x] SQL 执行部署（GO 分割 + 事务 + 日志记录）
- [x] 运行时组件部署（EXECUTION_LOG 表 + USP_WRITELOG 存储过程）
- [x] 部署目标自动解析（PSA → STAGE 角色, DV → CORE 角色）
- [x] 数据预览（OLTP / STAGE / CORE 三层树导航 + 列结构 + 前 500 行）
- [x] 执行日志查看与清空
- [x] 自定义 SQL 执行