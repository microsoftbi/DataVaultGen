"""数据库角色绑定 API：配置 STAGE / CORE 分别使用哪个连接的哪个数据库（OLTP 已移至 OLTP_SOURCE 表）"""
from fastapi import APIRouter, HTTPException
from app.database import get_meta_session, build_engine
from app.models.meta import DatabaseRole, ConnectionConfig
from app.schemas import DatabaseRolesRequest, DatabaseRoleUpdate, DatabaseRoleResponse
from sqlalchemy import text
import base64
import hashlib
from cryptography.fernet import Fernet
from app.config import settings

router = APIRouter(prefix="/api", tags=["数据库角色绑定"])

# 解密密钥（与 connections.py 一致）
_key = base64.urlsafe_b64encode(
    hashlib.sha256(settings.secret_key.encode()).digest()
)
_cipher = Fernet(_key)


def _decrypt_password(encrypted: str) -> str:
    return _cipher.decrypt(encrypted.encode()).decode()


def _role_to_dict(role: DatabaseRole) -> dict:
    return {
        "id": role.id,
        "role_name": role.role_name,
        "conn_id": role.conn_id,
        "database_name": role.database_name,
        "created_at": role.created_at,
    }


@router.get("/db-roles")
def get_db_roles():
    """获取两个角色的绑定配置"""
    session = get_meta_session()
    roles = session.query(DatabaseRole).all()
    result = {}
    for r in roles:
        result[r.role_name.lower()] = _role_to_dict(r)
    for name in ("stage", "core"):
        if name not in result:
            result[name] = None
    return {"success": True, "data": result}


@router.put("/db-roles")
def update_db_roles(data: DatabaseRolesRequest):
    """保存两个角色的绑定配置"""
    session = get_meta_session()
    mappings = {"stage": "STAGE", "core": "CORE"}

    for key, role_cfg in [("stage", data.stage), ("core", data.core)]:
        role_name = mappings[key]
        existing = session.query(DatabaseRole).filter(DatabaseRole.role_name == role_name).first()
        if existing:
            existing.conn_id = role_cfg.conn_id
            existing.database_name = role_cfg.database_name
        else:
            session.add(DatabaseRole(
                role_name=role_name,
                conn_id=role_cfg.conn_id,
                database_name=role_cfg.database_name,
            ))

    session.commit()
    return get_db_roles()


@router.post("/db-roles/{role_name}/create-database")
def create_database(role_name: str):
    """重建指定角色（stage/core）的数据库（DROP + CREATE）"""
    if role_name.lower() not in ("stage", "core"):
        raise HTTPException(400, "role_name must be 'stage' or 'core'")

    session = get_meta_session()
    role = session.query(DatabaseRole).filter(
        DatabaseRole.role_name == role_name.upper()
    ).first()
    if not role:
        raise HTTPException(400, f"{role_name.upper()} 角色未配置，请先绑定连接和数据库名")

    db_name = role.database_name
    if not db_name:
        raise HTTPException(400, f"{role_name.upper()} 未指定数据库名")

    conn = session.query(ConnectionConfig).filter(
        ConnectionConfig.id == role.conn_id
    ).first()
    if not conn:
        raise HTTPException(400, f"连接 (ID={role.conn_id}) 不存在")

    password = _decrypt_password(conn.password_encrypted)

    # 以 master 为目标构建引擎（不能连接到即将被 DROP 的数据库）
    engine = build_engine(conn.host, conn.port, "master", conn.username, password)
    try:
        with engine.connect() as conn_exec:
            conn_exec.execution_options(isolation_level="AUTOCOMMIT")
            conn_exec.execute(text(f"DROP DATABASE IF EXISTS [{db_name}]"))
            conn_exec.execute(text(f"CREATE DATABASE [{db_name}]"))
        return {"success": True, "message": f"数据库 [{db_name}] 已重建"}
    except Exception as e:
        raise HTTPException(500, f"创建数据库失败: {str(e)}")
    finally:
        engine.dispose()