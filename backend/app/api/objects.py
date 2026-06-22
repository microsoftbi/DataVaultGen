"""对象列表管理 API"""
from fastapi import APIRouter, HTTPException
from app.database import get_meta_session
from app.models.meta import GenList
from app.schemas import ObjectListItem, ObjectListUpdate, ObjectListBatchUpdate
from sqlalchemy import text

router = APIRouter(prefix="/api/objects", tags=["对象列表"])


@router.get("")
def list_objects():
    session = get_meta_session()
    rows = session.query(GenList).order_by(GenList.table_name).all()
    return [ObjectListItem.model_validate(r) for r in rows]


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