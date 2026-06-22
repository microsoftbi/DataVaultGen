"""数据库引擎管理 — SQLite (META) + SQL Server (用户连接)"""
from typing import Optional
from urllib.parse import quote_plus
from pathlib import Path
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session as SASession
from sqlalchemy.engine import Engine
from app.config import settings

# ── ODBC 辅助（用于用户管理的 SQL Server 连接） ────────────────
ODBC_DRIVER = "ODBC Driver 18 for SQL Server"


def _odbc_url(user: str, password: str, host: str, port: int, db_name: str) -> str:
    """构建 mssql+pyodbc 连接 URL"""
    params = quote_plus(
        f"DRIVER={{{ODBC_DRIVER}}};SERVER={host},{port};DATABASE={db_name};"
        f"UID={user};PWD={password};TrustServerCertificate=yes"
    )
    return f"mssql+pyodbc:///?odbc_connect={params}"


# ── META 库（SQLite） ────────────────────────────────────────
_meta_engine: Optional[Engine] = None
_meta_session_factory: Optional[sessionmaker] = None


def get_meta_engine() -> Engine:
    """获取 META 库数据库引擎 (SQLite)"""
    global _meta_engine, _meta_session_factory
    if _meta_engine is None:
        db_path = Path(settings.meta_db_path).resolve()
        conn_str = f"sqlite:///{db_path}"
        _meta_engine = create_engine(conn_str, echo=settings.debug)

        # 启用 WAL 模式 + 外键
        @event.listens_for(_meta_engine, "connect")
        def _set_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        _meta_session_factory = sessionmaker(bind=_meta_engine)
    return _meta_engine


def get_meta_session() -> SASession:
    """获取 META 库会话"""
    get_meta_engine()
    return _meta_session_factory()


# ── 用户管理的 SQL Server 动态连接池 ──────────────────────────
_connection_cache: dict[int, Engine] = {}


def build_engine(host: str, port: int, db_name: str, user: str, password: str) -> Engine:
    conn_str = _odbc_url(user, password, host, port, db_name)
    return create_engine(conn_str, pool_pre_ping=True, pool_recycle=3600)


def get_engine(conn_id: int) -> Optional[Engine]:
    return _connection_cache.get(conn_id)


def register_engine(conn_id: int, engine: Engine):
    _connection_cache[conn_id] = engine


def remove_engine(conn_id: int):
    engine = _connection_cache.pop(conn_id, None)
    if engine:
        engine.dispose()


def test_connection(host: str, port: int, db_name: str, user: str, password: str) -> tuple[bool, str]:
    """测试数据库连接是否可用，返回 (成功与否, 详情)"""
    try:
        # 如果没有指定数据库名，用 master 测试服务器连通性
        actual_db = db_name if db_name else "master"
        engine = build_engine(host, port, actual_db, user, password)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True, "Connection successful"
    except Exception as e:
        return False, str(e)