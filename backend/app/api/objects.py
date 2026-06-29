"""对象列表管理 API"""
from fastapi import APIRouter, HTTPException
from app.database import get_meta_session
from app.models.meta import GenList, Attribute
from app.schemas import ObjectListItem, ObjectListUpdate, ObjectListBatchUpdate
from sqlalchemy import text

router = APIRouter(prefix="/api/objects", tags=["对象列表"])


@router.get("")
def list_objects():
    session = get_meta_session()
    # 关联 Attribute 获取 record_src
    sub = session.query(
        Attribute.table_name,
        Attribute.record_src,
    ).distinct().subquery()

    rows = session.query(GenList, sub.c.record_src).outerjoin(
        sub, GenList.table_name == sub.c.table_name
    ).order_by(GenList.table_name).all()

    result = []
    for gen, record_src in rows:
        result.append({
            "id": gen.id,
            "table_catalog": gen.table_catalog,
            "table_name": gen.table_name,
            "schema_name": gen.schema_name,
            "is_gen": gen.is_gen,
            "is_full_load": gen.is_full_load,
            "record_src": record_src,
        })
    return result


@router.post("/init")
def init_object_list():
    """初始化对象列表 — 将所有已导入元数据的表纳入列表"""
    session = get_meta_session()
    session.execute(text("""
        INSERT OR IGNORE INTO GEN_LIST (TABLE_CATALOG, TABLE_NAME, SCHEMA_NAME)
        SELECT DISTINCT NULL, TABLE_NAME, 'dbo'
        FROM ATTRIBUTE
    """))
    session.commit()
    return {"success": True, "message": "Object list initialized"}


@router.put("/batch/update")
def batch_update_objects(data: ObjectListBatchUpdate):
    """批量更新对象（必须放在 /{obj_id} 前面）"""
    session = get_meta_session()
    updated = 0
    for upd in data.updates:
        row = session.query(GenList).filter(GenList.id == upd.get("id")).first()
        if not row:
            continue
        for k, v in upd.items():
            if k == "id":
                continue
            if hasattr(row, k):
                setattr(row, k, v)
        updated += 1
    session.commit()
    return {"success": True, "updated": updated}


@router.put("/{obj_id}")
def update_object(obj_id: int, data: ObjectListUpdate):
    session = get_meta_session()
    row = session.query(GenList).filter(GenList.id == obj_id).first()
    if not row:
        raise HTTPException(404, "Object not found")
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(row, k, v)
    session.commit()
    return ObjectListItem.model_validate(row)