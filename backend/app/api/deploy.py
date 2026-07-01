"""部署与 SQL 执行 API"""
import base64
import hashlib
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from cryptography.fernet import Fernet
from app.config import settings
from app.database import get_meta_session, get_engine, build_engine
from app.models.meta import Configuration, ExecutionLog, DatabaseRole, ConnectionConfig, Attribute, GenList, RecordSource
from app.schemas import DeployRequest, ExecuteSqlRequest, ConfigResponse, ConfigUpdate
from app.services.sql_executor import execute_batch, check_database_status
from app.services.runtime_sql import RUNTIME_SQL
from app.services.generator_psa import PSAGenerator
from datetime import datetime

# 解密密钥（与 connections.py 一致）
_key = base64.urlsafe_b64encode(
    hashlib.sha256(settings.secret_key.encode()).digest()
)
_cipher = Fernet(_key)


def _decrypt_password(encrypted: str) -> str:
    return _cipher.decrypt(encrypted.encode()).decode()


def _build_role_engine(role_name: str, session=None):
    """根据角色绑定构建带数据库名的临时引擎"""
    close_session = False
    if session is None:
        session = get_meta_session()
        close_session = True
    try:
        role = session.query(DatabaseRole).filter(DatabaseRole.role_name == role_name).first()
        if not role:
            return None, f"{role_name} 角色未配置，请先在 数据源连接 页面完成数据库角色绑定"

        conn = session.query(ConnectionConfig).filter(ConnectionConfig.id == role.conn_id).first()
        if not conn:
            return None, f"{role_name} 角色绑定的连接 (ID={role.conn_id}) 不存在"

        password = _decrypt_password(conn.password_encrypted)
        engine = build_engine(conn.host, conn.port, role.database_name, conn.username, password)
        return engine, None
    finally:
        if close_session:
            session.close()

router = APIRouter(prefix="/api", tags=["部署与配置"])

# ── 配置 ──────────────────────────────────────────────────────

@router.get("/config")
def get_config():
    session = get_meta_session()
    psa = session.query(Configuration).filter(Configuration.config_name == "PSA_DB").first()
    hash_d = session.query(Configuration).filter(Configuration.config_name == "HASHDUMMY").first()
    core = session.query(Configuration).filter(Configuration.config_name == "CORE_DB").first()
    return ConfigResponse(
        psa_db_name=psa.config_value if psa else "STAGE",
        hash_dummy=hash_d.config_value if hash_d else "@IAMHUSKIES@",
        core_db_name=core.config_value if core else "CORE",
    )


@router.put("/config")
def update_config(data: ConfigUpdate):
    session = get_meta_session()
    if data.psa_db_name is not None:
        row = session.query(Configuration).filter(Configuration.config_name == "PSA_DB").first()
        if row:
            row.config_value = data.psa_db_name
        else:
            session.add(Configuration(config_name="PSA_DB", config_value=data.psa_db_name))
    if data.hash_dummy is not None:
        row = session.query(Configuration).filter(Configuration.config_name == "HASHDUMMY").first()
        if row:
            row.config_value = data.hash_dummy
        else:
            session.add(Configuration(config_name="HASHDUMMY", config_value=data.hash_dummy))
    if data.core_db_name is not None:
        row = session.query(Configuration).filter(Configuration.config_name == "CORE_DB").first()
        if row:
            row.config_value = data.core_db_name
        else:
            session.add(Configuration(config_name="CORE_DB", config_value=data.core_db_name))
    session.commit()
    return get_config()

# ── 部署 ──────────────────────────────────────────────────────

@router.post("/deploy/psa")
def deploy_psa(conn_id: int = None):
    """生成并部署全套 PSA 对象到 STAGE 库（自动从角色绑定获取目标+数据库）"""
    session = get_meta_session()

    # 从角色绑定构建带数据库名的引擎
    engine, err = _build_role_engine("STAGE", session)
    if err:
        raise HTTPException(400, err)

    # 生成全部 SQL
    psa_db = session.query(Configuration).filter(Configuration.config_name == "PSA_DB").first()
    hash_d = session.query(Configuration).filter(Configuration.config_name == "HASHDUMMY").first()
    gen = PSAGenerator(session, psa_db.config_value if psa_db else "STAGE",
                       hash_d.config_value if hash_d else "@IAMHUSKIES@")

    sql = gen.generate_combined()

    # 写入日志
    log = ExecutionLog(log_source="deploy/psa", log_type="N",
                       message="Starting PSA deploy to STAGE (auto-resolved)")
    session.add(log)
    session.commit()

    # 执行（传入临时引擎，绕过缓存）
    result = execute_batch(0, sql, engine=engine)

    # 记录结果
    log2 = ExecutionLog(
        log_source="deploy/psa",
        log_type="E" if not result["success"] else "N",
        message=result["message"],
    )
    session.add(log2)
    session.commit()

    return result


@router.post("/deploy/dv")
def deploy_dv(conn_id: int = None):
    """生成并部署全套 DV 对象到 CORE 库（自动从角色绑定获取目标+数据库）"""
    session = get_meta_session()

    # 从角色绑定构建带数据库名的引擎
    engine, err = _build_role_engine("CORE", session)
    if err:
        raise HTTPException(400, err)

    psa_db = session.query(Configuration).filter(Configuration.config_name == "PSA_DB").first()
    hash_d = session.query(Configuration).filter(Configuration.config_name == "HASHDUMMY").first()
    core_db = session.query(Configuration).filter(Configuration.config_name == "CORE_DB").first()

    from app.services.generator_dv import DVGenerator
    gen = DVGenerator(
        session,
        psa_db.config_value if psa_db else "STAGE",
        core_db.config_value if core_db else "CORE",
        hash_d.config_value if hash_d else "@IAMHUSKIES@",
    )
    sql = gen.generate_combined()

    log = ExecutionLog(log_source="deploy/dv", log_type="N",
                       message="Starting DV deploy to CORE (auto-resolved)")
    session.add(log)
    session.commit()

    result = execute_batch(0, sql, engine=engine)

    log2 = ExecutionLog(
        log_source="deploy/dv",
        log_type="E" if not result["success"] else "N",
        message=result["message"],
    )
    session.add(log2)
    session.commit()
    return result


@router.post("/deploy/runtime")
def deploy_runtime(conn_id: int = None):
    """部署运行时组件到 STAGE 库（自动从角色绑定获取目标+数据库）"""
    session = get_meta_session()

    engine, err = _build_role_engine("STAGE", session)
    if err:
        raise HTTPException(400, err)

    log = ExecutionLog(log_source="deploy/runtime", log_type="N",
                       message="Deploying runtime components to STAGE (auto-resolved)")
    session.add(log)
    session.commit()

    result = execute_batch(0, RUNTIME_SQL, engine=engine)

    log2 = ExecutionLog(
        log_source="deploy/runtime",
        log_type="E" if not result["success"] else "N",
        message=result["message"],
    )
    session.add(log2)
    session.commit()
    return result


@router.post("/deploy/sql")
def deploy_sql(data: DeployRequest):
    """执行自定义 SQL"""
    engine = get_engine(data.conn_id)
    if not engine:
        raise HTTPException(400, "Connection not found or not initialized")

    session = get_meta_session()
    log = ExecutionLog(log_source=f"deploy/sql/{data.object_type}", log_type="N",
                       message=f"Executing SQL on connection {data.conn_id}")
    session.add(log)
    session.commit()

    result = execute_batch(data.conn_id, data.sql)

    log2 = ExecutionLog(
        log_source=f"deploy/sql/{data.object_type}",
        log_type="E" if not result["success"] else "N",
        message=result["message"],
    )
    session.add(log2)
    session.commit()

    return result


@router.post("/deploy/execute")
def execute_sql(data: ExecuteSqlRequest):
    """执行自定义 SQL 到指定角色绑定的数据库（STAGE / CORE），自动解析目标连接"""
    session = get_meta_session()

    engine, err = _build_role_engine(data.role, session)
    if err:
        raise HTTPException(400, err)

    log = ExecutionLog(log_source=f"execute/{data.role}", log_type="N",
                       message=f"Executing SQL on {data.role} database")
    session.add(log)
    session.commit()

    result = execute_batch(0, data.sql, engine=engine)

    log2 = ExecutionLog(
        log_source=f"execute/{data.role}",
        log_type="E" if not result["success"] else "N",
        message=result["message"],
    )
    session.add(log2)
    session.commit()
    return result


@router.get("/deploy/status")
def deploy_status(conn_id: int):
    """检查目标数据库中的对象状态"""
    return check_database_status(conn_id)


@router.get("/deploy/diff")
def deploy_diff(conn_id: int):
    """对比目标库中 PSA 对象的部署状态"""
    from app.models.meta import Attribute, GenList
    session = get_meta_session()

    # 1. 获取 META 中配置的表
    tables = session.query(Attribute).filter(
        Attribute.is_pk.is_(True) | Attribute.is_bk.is_(True) | Attribute.is_di.is_(True)
    ).all()
    table_names = list(set(t.table_name for t in tables))

    # 2. 构建期望的对象列表
    expected = []
    for tn in table_names:
        expected.append({"name": f"dbo.{tn}_STG", "type": "TABLE"})
        expected.append({"name": f"dbo.{tn}_CDC", "type": "TABLE"})
        expected.append({"name": f"dbo.{tn}_LOG", "type": "TABLE"})
        expected.append({"name": f"dbo.V_{tn}_MTA", "type": "VIEW"})
        expected.append({"name": f"dbo.V_{tn}_LOG_CURRENT", "type": "VIEW"})
        expected.append({"name": f"dbo.USP_{tn}_STG", "type": "PROCEDURE"})
        expected.append({"name": f"dbo.USP_{tn}_CDC", "type": "PROCEDURE"})
        expected.append({"name": f"dbo.USP_{tn}_LOG", "type": "PROCEDURE"})

    # 3. 获取目标库现有对象
    actual = check_database_status(conn_id)
    if not actual.get("success"):
        return {"success": False, "message": actual.get("message", "Cannot check target database")}

    actual_set = set(actual.get("tables", []) + actual.get("views", []) + actual.get("procedures", []))

    # 4. 做对比
    diffs = []
    for obj in expected:
        status = "EXISTS" if obj["name"] in actual_set else "MISSING"
        diffs.append({**obj, "status": status})

    missing_count = sum(1 for d in diffs if d["status"] == "MISSING")
    return {
        "success": True,
        "diffs": diffs,
        "summary": {
            "total": len(diffs),
            "existing": len(diffs) - missing_count,
            "missing": missing_count,
        },
    }


# ── 导出 / 导入 META 配置 ──────────────────────────────────────

class MetaExportData(BaseModel):
    attributes: list
    gen_list: list
    configurations: list
    record_sources: list


@router.get("/meta/export")
def export_meta_config():
    """导出 META 配置为 JSON"""
    session = get_meta_session()
    attrs = session.query(Attribute).all()
    gens = session.query(GenList).all()
    configs = session.query(Configuration).all()
    rss = session.query(RecordSource).all()

    def row_to_dict(r):
        d = {c.name: getattr(r, c.name) for c in r.__table__.columns}
        d.pop("id", None)
        d.pop("CREATED_AT", None)
        return d

    return {
        "success": True,
        "data": MetaExportData(
            attributes=[row_to_dict(a) for a in attrs],
            gen_list=[row_to_dict(g) for g in gens],
            configurations=[
                {"CONFIG_NAME": c.config_name, "CONFIG_VALUE": c.config_value, "DESCRIPTION": c.description}
                for c in configs
            ],
            record_sources=[row_to_dict(r) for r in rss],
        ).model_dump(),
    }


@router.post("/meta/import")
def import_meta_config(data: MetaExportData):
    """从 JSON 导入 META 配置"""
    session = get_meta_session()

    # 清空现有数据
    session.query(ExecutionLog).delete()
    session.query(Attribute).delete()
    session.query(GenList).delete()
    session.query(RecordSource).delete()
    session.query(Configuration).delete()

    # 导入 ATTRIBUTE
    for a in data.attributes:
        session.add(Attribute(**a))
    # 导入 GEN_LIST
    for g in data.gen_list:
        session.add(GenList(**g))
    # 导入 CONFIGURATION
    for c in data.configurations:
        session.add(Configuration(**c))
    # 导入 RECORD_SOURCE
    for r in data.record_sources:
        session.add(RecordSource(**r))

    session.commit()
    return {"success": True, "message": f"Imported {len(data.attributes)} attributes, {len(data.gen_list)} gen_list items, {len(data.configurations)} configs"}


# ── 日志 ──────────────────────────────────────────────────────

@router.get("/logs")
def list_logs(limit: int = 100, offset: int = 0):
    session = get_meta_session()
    rows = (
        session.query(ExecutionLog)
        .order_by(ExecutionLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    from app.schemas import LogResponse
    return [LogResponse.model_validate(r) for r in rows]


@router.delete("/logs")
def clear_logs():
    session = get_meta_session()
    session.query(ExecutionLog).delete()
    session.commit()
    return {"success": True, "message": "Logs cleared"}