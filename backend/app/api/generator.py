"""PSA + DV 代码生成 API"""
from fastapi import APIRouter
from app.database import get_meta_session
from app.models.meta import Configuration, DatabaseRole
from app.services.generator_psa import PSAGenerator
from app.services.generator_dv import DVGenerator

router = APIRouter(prefix="/api/generate", tags=["代码生成"])


def _get_config(session) -> tuple[str, str, str]:
    psa_db = session.query(Configuration).filter(
        Configuration.config_name == "PSA_DB"
    ).first()
    hash_d = session.query(Configuration).filter(
        Configuration.config_name == "HASHDUMMY"
    ).first()
    core_db = session.query(Configuration).filter(
        Configuration.config_name == "CORE_DB"
    ).first()
    return (
        psa_db.config_value if psa_db else "STAGE",
        hash_d.config_value if hash_d else "@IAMHUSKIES@",
        core_db.config_value if core_db else "CORE",
    )


def _get_oltp_db(session) -> str:
    """从角色绑定获取 OLTP 数据库名"""
    role = session.query(DatabaseRole).filter(DatabaseRole.role_name == "OLTP").first()
    return role.database_name if role else None


def _get_psa(session=None):
    if session is None:
        session = get_meta_session()
    psa_db, hash_d, _ = _get_config(session)
    oltp_db = _get_oltp_db(session)
    return PSAGenerator(session, psa_db, hash_d, oltp_db_name=oltp_db)


def _get_dv(session=None):
    if session is None:
        session = get_meta_session()
    psa_db, hash_d, core_db = _get_config(session)
    return DVGenerator(session, psa_db, core_db, hash_d)


# ── PSA ──────────────────────────────────────────────────────

@router.post("/psa/stg")
def generate_stg():
    gen = _get_psa()
    return {"success": True, "sql": gen.generate_stg_table()}


@router.post("/psa/cdc")
def generate_cdc():
    gen = _get_psa()
    return {"success": True, "sql": gen.generate_cdc_table()}


@router.post("/psa/log")
def generate_log():
    gen = _get_psa()
    return {"success": True, "sql": gen.generate_log_table()}


@router.post("/psa/views")
def generate_views():
    gen = _get_psa()
    return {"success": True, "sql": gen.generate_v_mta() + "\n\n" + gen.generate_v_current()}


@router.post("/psa/usps")
def generate_usps():
    gen = _get_psa()
    return {
        "success": True,
        "sql": gen.generate_usp_stg() + "\n\n" + gen.generate_usp_cdc() + "\n\n" + gen.generate_usp_log(),
    }


@router.post("/psa/all")
def generate_psa_all():
    gen = _get_psa()
    return {"success": True, "sql": gen.generate_combined()}


@router.post("/psa/flow")
def generate_flow():
    gen = _get_psa()
    return {"success": True, "sql": gen.generate_execute_flow()}


# ── DV ───────────────────────────────────────────────────────

@router.post("/dv/hub")
def generate_dv_hub():
    gen = _get_dv()
    return {"success": True, "sql": gen.generate_hub_table()}


@router.post("/dv/sat")
def generate_dv_sat():
    gen = _get_dv()
    return {"success": True, "sql": gen.generate_sat_table()}


@router.post("/dv/link")
def generate_dv_link():
    gen = _get_dv()
    return {"success": True, "sql": gen.generate_link_table()}


@router.post("/dv/usp-hub")
def generate_dv_usp_hub():
    gen = _get_dv()
    return {"success": True, "sql": gen.generate_usp_hub()}


@router.post("/dv/usp-sat")
def generate_dv_usp_sat():
    gen = _get_dv()
    return {"success": True, "sql": gen.generate_usp_sat()}


@router.post("/dv/usp-link")
def generate_dv_usp_link():
    gen = _get_dv()
    return {"success": True, "sql": gen.generate_usp_link()}


@router.post("/dv/all")
def generate_dv_all():
    gen = _get_dv()
    return {"success": True, "sql": gen.generate_combined()}


@router.post("/dv/flow")
def generate_dv_flow():
    gen = _get_dv()
    return {"success": True, "sql": gen.generate_execute_flow()}