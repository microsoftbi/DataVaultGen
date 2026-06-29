"""数据预览 API — 浏览 OLTP/STAGE/CORE 三个库的对象和数据"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.database import get_meta_session, get_meta_engine, build_engine
from app.models.meta import DatabaseRole, ConnectionConfig
from app.models.oltp_source import OltpSource
from app.config import settings

router = APIRouter(prefix="/api/preview", tags=["数据预览"])


# ── 密码解密 + 临时引擎（与 deploy.py 一致） ──────────────────────
import base64
import hashlib
from cryptography.fernet import Fernet

_key = base64.urlsafe_b64encode(
    hashlib.sha256(settings.secret_key.encode()).digest()
)
_cipher = Fernet(_key)


def _decrypt_password(encrypted: str) -> str:
    return _cipher.decrypt(encrypted.encode()).decode()


def _build_role_engine(role_name: str):
    """根据角色绑定构建带数据库名的临时引擎"""
    session = get_meta_session()
    try:
        role = session.query(DatabaseRole).filter(DatabaseRole.role_name == role_name).first()
        if not role:
            return None, None, f"{role_name} 角色未配置"
        conn = session.query(ConnectionConfig).filter(ConnectionConfig.id == role.conn_id).first()
        if not conn:
            return None, None, f"连接 (ID={role.conn_id}) 不存在"
        password = _decrypt_password(conn.password_encrypted)
        engine = build_engine(conn.host, conn.port, role.database_name, conn.username, password)
        return engine, role.database_name, None
    finally:
        session.close()


@router.get("/databases")
def get_databases():
    """返回 OLTP/STAGE/CORE 的数据库信息（OLTP 返回所有源列表）"""
    session = get_meta_session()
    try:
        result = {}
        # OLTP: 返回所有 OLTP 源
        sources = session.query(OltpSource).all()
        oltp_list = []
        for src in sources:
            conn = session.query(ConnectionConfig).filter(ConnectionConfig.id == src.conn_id).first()
            oltp_list.append({
                "conn_id": src.conn_id,
                "database_name": src.database_name,
                "connection_name": conn.name if conn else None,
                "record_src": src.record_src,
            })
        result["oltp"] = oltp_list

        # STAGE, CORE: unchanged
        for role_name in ("STAGE", "CORE"):
            role = session.query(DatabaseRole).filter(DatabaseRole.role_name == role_name).first()
            if role:
                conn = session.query(ConnectionConfig).filter(ConnectionConfig.id == role.conn_id).first()
                result[role_name.lower()] = {
                    "conn_id": role.conn_id,
                    "database_name": role.database_name,
                    "connection_name": conn.name if conn else None,
                }
            else:
                result[role_name.lower()] = None
        return {"success": True, "data": result}
    finally:
        session.close()


@router.get("/objects")
def get_objects(conn_id: int, database_name: str):
    """获取指定库的对象列表（表/视图/存储过程）"""
    engine, db_name, err = _build_role_engine_by_conn(conn_id, database_name)
    if err:
        raise HTTPException(400, err)

    result = {"tables": [], "views": [], "procedures": []}

    with engine.connect() as conn:
        # 表
        rows = conn.execute(text("""
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)).fetchall()
        result["tables"] = [f"{r[0]}.{r[1]}" for r in rows]

        # 视图
        rows = conn.execute(text("""
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM INFORMATION_SCHEMA.VIEWS
            ORDER BY TABLE_NAME
        """)).fetchall()
        result["views"] = [f"{r[0]}.{r[1]}" for r in rows]

        # 存储过程
        rows = conn.execute(text("""
            SELECT SPECIFIC_SCHEMA, SPECIFIC_NAME
            FROM INFORMATION_SCHEMA.ROUTINES
            WHERE ROUTINE_TYPE = 'PROCEDURE'
            ORDER BY SPECIFIC_NAME
        """)).fetchall()
        result["procedures"] = [f"{r[0]}.{r[1]}" for r in rows]

    engine.dispose()
    return {"success": True, **result}


@router.get("/columns")
def get_columns(conn_id: int, database_name: str, schema: str, object: str):
    """获取指定表/视图的列结构"""
    engine, db_name, err = _build_role_engine_by_conn(conn_id, database_name)
    if err:
        raise HTTPException(400, err)

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :object
            ORDER BY ORDINAL_POSITION
        """), {"schema": schema, "object": object}).fetchall()

        columns = []
        for r in rows:
            col = {
                "column_name": r[0],
                "data_type": r[1],
                "max_length": r[2],
                "precision": r[3],
                "scale": r[4],
                "is_nullable": r[5],
            }
            # 补充友好的类型显示
            t = r[1].upper() if r[1] else "NVARCHAR"
            if t in ("NVARCHAR", "VARCHAR", "NCHAR", "CHAR") and r[2]:
                col["display_type"] = f"{r[1]}({r[2]})"
            elif t == "DECIMAL" and r[3]:
                col["display_type"] = f"DECIMAL({r[3]},{r[4]})"
            elif t == "NUMERIC" and r[3]:
                col["display_type"] = f"NUMERIC({r[3]})"
            else:
                col["display_type"] = r[1] or ""
            columns.append(col)

    engine.dispose()
    return {"success": True, "columns": columns}


@router.get("/data")
def get_data(conn_id: int, database_name: str, schema: str, object: str, limit: int = 500):
    """获取指定表/视图的前 N 行数据"""
    engine, db_name, err = _build_role_engine_by_conn(conn_id, database_name)
    if err:
        raise HTTPException(400, err)

    with engine.connect() as conn:
        rows = conn.execute(text(
            f"SELECT TOP {limit} * FROM [{schema}].[{object}]"
        )).fetchall()

        # 列名
        col_names = list(rows[0]._fields) if rows else []
        # 数据行（转为列表）
        data_rows = [list(r) for r in rows]
        # 时间类型转字符串
        for row in data_rows:
            for i, val in enumerate(row):
                if hasattr(val, 'isoformat'):
                    row[i] = val.isoformat()

    engine.dispose()
    return {"success": True, "columns": col_names, "rows": data_rows, "total": len(data_rows)}


# ── META 库预览 ──────────────────────────────────────────────
_EXCLUDED_META_TABLES = {"sqlite_sequence", "sqlite_master"}


@router.get("/meta/tables")
def get_meta_tables():
    """获取 META 库 (SQLite) 的所有用户表"""
    engine = get_meta_engine()
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )).fetchall()
    tables = [r[0] for r in rows if r[0] not in _EXCLUDED_META_TABLES]
    return {"success": True, "tables": tables}


@router.get("/meta/columns")
def get_meta_columns(table: str):
    """获取 META 库指定表的列结构"""
    engine = get_meta_engine()
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info(\"{table}\")")).fetchall()
    columns = []
    for r in rows:
        columns.append({
            "column_name": r[1],
            "data_type": r[2],
            "is_nullable": "YES" if r[3] else "NO",
            "display_type": r[2] or "",
        })
    return {"success": True, "columns": columns}


@router.get("/meta/data")
def get_meta_data(table: str, limit: int = 500):
    """获取 META 库指定表的前 N 行数据"""
    engine = get_meta_engine()
    with engine.connect() as conn:
        rows = conn.execute(text(
            f"SELECT * FROM \"{table}\" LIMIT :limit"
        ), {"limit": limit}).fetchall()
        col_names = list(rows[0]._fields) if rows else []
        data_rows = []
        for r in rows:
            row = []
            for val in list(r):
                if hasattr(val, 'isoformat'):
                    row.append(val.isoformat())
                else:
                    row.append(val)
            data_rows.append(row)
    return {"success": True, "columns": col_names, "rows": data_rows, "total": len(data_rows)}


def _build_role_engine_by_conn(conn_id: int, database_name: str):
    """根据连接 ID + 数据库名构建临时引擎"""
    session = get_meta_session()
    try:
        conn = session.query(ConnectionConfig).filter(ConnectionConfig.id == conn_id).first()
        if not conn:
            return None, None, f"Connection {conn_id} not found"
        password = _decrypt_password(conn.password_encrypted)
        engine = build_engine(conn.host, conn.port, database_name, conn.username, password)
        return engine, database_name, None
    finally:
        session.close()