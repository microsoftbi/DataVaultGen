"""PSA + DV 代码生成 API"""
from fastapi import APIRouter, Query
from app.database import get_meta_session
from app.models.meta import Configuration
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


def _get_psa(session=None, record_src: str = None):
    if session is None:
        session = get_meta_session()
    psa_db, hash_d, _ = _get_config(session)
    return PSAGenerator(session, psa_db, hash_d, record_src=record_src)


def _get_dv(session=None, record_src: str = None):
    if session is None:
        session = get_meta_session()
    psa_db, hash_d, core_db = _get_config(session)
    return DVGenerator(session, psa_db, core_db, hash_d, record_src=record_src)


# ── PSA ──────────────────────────────────────────────────────

@router.post("/psa/stg")
def generate_stg(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_psa(record_src=record_src)
    return {"success": True, "sql": gen.generate_stg_table()}


@router.post("/psa/cdc")
def generate_cdc(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_psa(record_src=record_src)
    return {"success": True, "sql": gen.generate_cdc_table()}


@router.post("/psa/log")
def generate_log(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_psa(record_src=record_src)
    return {"success": True, "sql": gen.generate_log_table()}


@router.post("/psa/views")
def generate_views(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_psa(record_src=record_src)
    return {"success": True, "sql": gen.generate_v_mta() + "\n\n" + gen.generate_v_current()}


@router.post("/psa/usps")
def generate_usps(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_psa(record_src=record_src)
    return {
        "success": True,
        "sql": gen.generate_usp_stg() + "\n\n" + gen.generate_usp_cdc() + "\n\n" + gen.generate_usp_log(),
    }


@router.post("/psa/usp-stg")
def generate_usp_stg(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_psa(record_src=record_src)
    return {"success": True, "sql": gen.generate_usp_stg()}


@router.post("/psa/usp-cdc")
def generate_usp_cdc(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_psa(record_src=record_src)
    return {"success": True, "sql": gen.generate_usp_cdc()}


@router.post("/psa/usp-log")
def generate_usp_log(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_psa(record_src=record_src)
    return {"success": True, "sql": gen.generate_usp_log()}


@router.post("/psa/all")
def generate_psa_all(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_psa(record_src=record_src)
    return {"success": True, "sql": gen.generate_combined()}


@router.post("/psa/flow")
def generate_flow(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_psa(record_src=record_src)
    return {"success": True, "sql": gen.generate_execute_flow()}


# ── DV ───────────────────────────────────────────────────────

@router.post("/dv/hub")
def generate_dv_hub(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_dv(record_src=record_src)
    return {"success": True, "sql": gen.generate_hub_table()}


@router.post("/dv/sat")
def generate_dv_sat(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_dv(record_src=record_src)
    return {"success": True, "sql": gen.generate_sat_table()}


@router.post("/dv/link")
def generate_dv_link(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_dv(record_src=record_src)
    return {"success": True, "sql": gen.generate_link_table()}


@router.post("/dv/usp-hub")
def generate_dv_usp_hub(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_dv(record_src=record_src)
    return {"success": True, "sql": gen.generate_usp_hub()}


@router.post("/dv/usp-sat")
def generate_dv_usp_sat(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_dv(record_src=record_src)
    return {"success": True, "sql": gen.generate_usp_sat()}


@router.post("/dv/usp-link")
def generate_dv_usp_link(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_dv(record_src=record_src)
    return {"success": True, "sql": gen.generate_usp_link()}


@router.post("/dv/all")
def generate_dv_all(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_dv(record_src=record_src)
    return {"success": True, "sql": gen.generate_combined()}


@router.post("/dv/flow")
def generate_dv_flow(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_dv(record_src=record_src)
    return {"success": True, "sql": gen.generate_execute_flow()}