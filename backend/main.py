"""DWH-Generator 后端入口 — python main.py"""
import sys
from pathlib import Path

# 确保 backend/ 目录在 Python 路径中，使得 from app.xxx 导入生效
sys.path.insert(0, str(Path(__file__).parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.config import settings
from app.api import connections, meta_import, objects, generator, deploy, dv_config
from app.models.meta import ConnectionConfig, init_meta_db
from app.database import get_meta_engine, get_meta_session, build_engine, register_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时自动初始化 META 表 + 恢复连接引擎"""
    # 1. 自动创建 META 表（幂等）
    engine = get_meta_engine()
    init_meta_db(engine)

    # 2. 恢复之前保存的数据库连接引擎
    try:
        session = get_meta_session()
        rows = session.query(ConnectionConfig).all()
        for row in rows:
            try:
                password = connections._decrypt(row.password_encrypted)
                engine = build_engine(row.host, row.port, row.database_name, row.username, password)
                register_engine(row.id, engine)
            except Exception:
                pass  # 跳过无法恢复的连接
        session.close()
    except Exception:
        pass
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — 允许前端开发服务器
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 防浏览器缓存中间件
@app.middleware("http")
async def no_cache(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# 注册路由
app.include_router(connections.router)
app.include_router(meta_import.router)
app.include_router(objects.router)
app.include_router(generator.router)
app.include_router(deploy.router)
app.include_router(dv_config.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,            # 热重载
        reload_dirs=[str(Path(__file__).parent)],
    )