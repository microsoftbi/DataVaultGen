# DWH-Generator

基于 Vue3 + FastAPI + SQLite/SQL Server 的 PSA Type 2 数据仓库生成器。

## 快速启动

### 1. 后端（自动创建 META 库，无需手动部署）

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py                     # 热重载模式，http://localhost:8000
```

META 配置库使用 SQLite 自动创建于 `backend/meta.db`，无需单独部署数据库。

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
│   │   └── templates/psa/ # Jinja2 模板
│   ├── target_meta_deploy.sql  # 目标 SQL Server META 运行时组件
│   ├── main.py            # 入口：python main.py（热重载）
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── views/         # 7 个页面
│   │   ├── api/           # API 调用封装
│   │   ├── stores/        # Pinia 状态管理
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
| 前端 | Vue 3 + TypeScript + Element Plus + Pinia |
| 后端 | FastAPI + SQLAlchemy 2.0 + Jinja2 |
| 配置库 | SQLite（自动创建，无需部署） |
| 目标 DWH | SQL Server（用户配置的连接） |

## 功能

- [x] 数据库连接管理（CRUD + 测试连接）
- [x] 元数据导入（SQL Server INFORMATION_SCHEMA → META）
- [x] 字段角色配置（BK 业务键 / PK 主键 / DI 描述信息）
- [x] 对象列表管理
- [x] PSA Type 2 代码生成（STG / CDC / LOG / Views / USPs）
- [x] SQL 执行部署（GO 分割 + 事务）
- [ ] Data Vault 2.0（后续迭代）