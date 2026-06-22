"""DV 配置管理 API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_meta_session
from app.models.meta import DvHub, DvSat, DvLink, Attribute
from app.schemas import DvTableCreate, DvTableResponse

router = APIRouter(prefix="/api/dv", tags=["DV 配置"])


class AutoConfigureRequest(BaseModel):
    table_name: str


@router.post("/auto-configure")
def auto_configure_dv(data: AutoConfigureRequest):
    """
    根据字段标记自动创建 HUB/SAT/LINK 并完成字段映射。
    - BK 字段 → HUB_{table_name}
    - DI 字段 → SAT_{table_name}
    - FK 字段 → LINK_{table_name}
    """
    session = get_meta_session()
    results = {}

    attrs = session.query(Attribute).filter(
        Attribute.table_name == data.table_name
    ).all()
    if not attrs:
        raise HTTPException(404, f"Table '{data.table_name}' not found in attributes")

    bk_fields = [a for a in attrs if a.is_bk]
    di_fields = [a for a in attrs if a.is_di]
    fk_fields = [a for a in attrs if a.is_fk]

    # ── HUB ──────────────────────────────────────────────
    if bk_fields:
        hub_name = f"HUB_{data.table_name}"
        existing_hub = session.query(DvHub).filter(DvHub.table_name == hub_name).first()
        if not existing_hub:
            existing_hub = DvHub(table_name=hub_name)
            session.add(existing_hub)
            session.flush()
        for a in bk_fields:
            a.dv_hub_id = existing_hub.id
        results["hub"] = {"table_name": hub_name, "id": existing_hub.id, "fields": [a.column_name for a in bk_fields]}

    # ── SAT ──────────────────────────────────────────────
    if di_fields:
        sat_name = f"SAT_{data.table_name}"
        existing_sat = session.query(DvSat).filter(DvSat.table_name == sat_name).first()
        if not existing_sat:
            existing_sat = DvSat(table_name=sat_name)
            session.add(existing_sat)
            session.flush()
        for a in di_fields:
            a.dv_sat_id = existing_sat.id
        results["sat"] = {"table_name": sat_name, "id": existing_sat.id, "fields": [a.column_name for a in di_fields]}

    # ── LINK ─────────────────────────────────────────────
    if fk_fields:
        link_name = f"LINK_{data.table_name}"
        existing_link = session.query(DvLink).filter(DvLink.table_name == link_name).first()
        if not existing_link:
            existing_link = DvLink(table_name=link_name)
            session.add(existing_link)
            session.flush()
        for a in fk_fields:
            a.dv_link_id = existing_link.id
        results["link"] = {"table_name": link_name, "id": existing_link.id, "fields": [a.column_name for a in fk_fields]}

    session.commit()
    return {"success": True, "results": results}


# ── HUB ──────────────────────────────────────────────────────

@router.get("/hubs")
def list_hubs():
    session = get_meta_session()
    rows = session.query(DvHub).all()
    return [DvTableResponse.model_validate(r) for r in rows]


@router.post("/hubs", status_code=201)
def create_hub(data: DvTableCreate):
    session = get_meta_session()
    row = DvHub(table_name=data.table_name)
    session.add(row)
    session.commit()
    session.refresh(row)
    return DvTableResponse.model_validate(row)


@router.delete("/hubs/{hub_id}")
def delete_hub(hub_id: int):
    session = get_meta_session()
    row = session.query(DvHub).filter(DvHub.id == hub_id).first()
    if not row:
        raise HTTPException(404, "HUB not found")
    # 清除关联字段的 DV_HUB_ID
    session.query(Attribute).filter(Attribute.dv_hub_id == hub_id).update({"dv_hub_id": None})
    session.delete(row)
    session.commit()
    return {"message": "Deleted"}


# ── SAT ──────────────────────────────────────────────────────

@router.get("/sats")
def list_sats():
    session = get_meta_session()
    rows = session.query(DvSat).all()
    return [DvTableResponse.model_validate(r) for r in rows]


@router.post("/sats", status_code=201)
def create_sat(data: DvTableCreate):
    session = get_meta_session()
    row = DvSat(table_name=data.table_name)
    session.add(row)
    session.commit()
    session.refresh(row)
    return DvTableResponse.model_validate(row)


@router.delete("/sats/{sat_id}")
def delete_sat(sat_id: int):
    session = get_meta_session()
    row = session.query(DvSat).filter(DvSat.id == sat_id).first()
    if not row:
        raise HTTPException(404, "SAT not found")
    session.query(Attribute).filter(Attribute.dv_sat_id == sat_id).update({"dv_sat_id": None})
    session.delete(row)
    session.commit()
    return {"message": "Deleted"}


# ── LINK ─────────────────────────────────────────────────────

@router.get("/links")
def list_links():
    session = get_meta_session()
    rows = session.query(DvLink).all()
    return [DvTableResponse.model_validate(r) for r in rows]


@router.post("/links", status_code=201)
def create_link(data: DvTableCreate):
    session = get_meta_session()
    row = DvLink(table_name=data.table_name)
    session.add(row)
    session.commit()
    session.refresh(row)
    return DvTableResponse.model_validate(row)


@router.delete("/links/{link_id}")
def delete_link(link_id: int):
    session = get_meta_session()
    row = session.query(DvLink).filter(DvLink.id == link_id).first()
    if not row:
        raise HTTPException(404, "LINK not found")
    session.query(Attribute).filter(Attribute.dv_link_id == link_id).update({"dv_link_id": None})
    session.delete(row)
    session.commit()
    return {"message": "Deleted"}