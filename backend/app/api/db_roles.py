"""数据库角色绑定 API：配置 STAGE / CORE 分别使用哪个连接的哪个数据库（OLTP 已移至 OLTP_SOURCE 表）"""
from fastapi import APIRouter, HTTPException
from app.database import get_meta_session
from app.models.meta import DatabaseRole
from app.schemas import DatabaseRolesRequest, DatabaseRoleUpdate, DatabaseRoleResponse

router = APIRouter(prefix="/api", tags=["数据库角色绑定"])


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