"""元数据导入 API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_meta_session
from app.models.meta import Attribute
from app.schemas import MetaImportRequest, AttributeResponse, AttributeUpdate, AttributeBatchUpdate
from app.services.meta_service import get_source_tables, get_source_columns, import_table_meta, ensure_gen_list

router = APIRouter(prefix="/api/meta", tags=["元数据导入"])


class BulkImportRequest(BaseModel):
    conn_id: int
    tables: list[dict]  # [{table_schema, table_name}]
    record_source: str = None


@router.get("/tables")
def list_source_tables(conn_id: int):
    """获取源库的所有表"""
    try:
        tables = get_source_tables(conn_id)
        return {"success": True, "tables": tables}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/columns")
def list_source_columns(conn_id: int, table_schema: str, table_name: str):
    """获取指定表的列信息"""
    try:
        columns = get_source_columns(conn_id, table_schema, table_name)
        return {"success": True, "columns": columns}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/import")
def import_meta(data: MetaImportRequest):
    """导入表元数据到 META 库（可指定 columns 筛选导入列）"""
    session = get_meta_session()
    try:
        count, skipped = import_table_meta(
            session=session,
            conn_id=data.conn_id,
            table_schema=data.table_schema,
            table_name=data.table_name,
            record_source=data.record_source,
            selected_columns=data.columns,
        )
        # 确保在对象列表中
        try:
            ensure_gen_list(session, table_name=data.table_name, schema_name=data.table_schema)
        except Exception as e:
            raise HTTPException(500, f"确保对象列表失败: {e}")
        return {"success": True, "imported": count, "skipped": skipped}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"导入元数据失败: {e}")


@router.post("/import-bulk")
def import_meta_bulk(data: BulkImportRequest):
    """批量导入多张表的元数据"""
    session = get_meta_session()
    total_imported = 0
    total_skipped = []
    results = []

    for tbl in data.tables:
        try:
            count, skipped = import_table_meta(
                session=session,
                conn_id=data.conn_id,
                table_schema=tbl["table_schema"],
                table_name=tbl["table_name"],
                record_source=data.record_source,
            )
            ensure_gen_list(session, table_name=tbl["table_name"], schema_name=tbl["table_schema"])
            total_imported += count
            total_skipped.extend(skipped)
            results.append({
                "table": f"{tbl['table_schema']}.{tbl['table_name']}",
                "imported": count,
            })
        except Exception as e:
            results.append({
                "table": f"{tbl['table_schema']}.{tbl['table_name']}",
                "imported": 0,
                "error": str(e),
            })

    return {
        "success": True,
        "total_imported": total_imported,
        "skipped": total_skipped,
        "results": results,
    }


@router.get("/attributes")
def list_attributes(table_name: str = None):
    """获取 META 中已导入的列属性"""
    session = get_meta_session()
    q = session.query(Attribute)
    if table_name:
        q = q.filter(Attribute.table_name == table_name)
    rows = q.order_by(Attribute.table_name, Attribute.id).all()
    return [AttributeResponse.model_validate(r) for r in rows]


@router.delete("/attributes/batch")
def batch_delete_attributes(data: AttributeBatchUpdate):
    """批量删除字段（从 META 表中移除）"""
    session = get_meta_session()
    ids = [upd.get("id") for upd in data.updates if upd.get("id")]
    if not ids:
        return {"success": True, "deleted": 0}
    deleted = session.query(Attribute).filter(Attribute.id.in_(ids)).delete(synchronize_session=False)
    session.commit()
    return {"success": True, "deleted": deleted}


@router.put("/attributes/batch")
def batch_update_attributes(data: AttributeBatchUpdate):
    """批量更新字段角色配置（必须放在 /{attr_id} 前面，避免路由冲突）"""
    session = get_meta_session()
    updated = 0
    for upd in data.updates:
        row = session.query(Attribute).filter(Attribute.id == upd.get("id")).first()
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


@router.put("/attributes/{attr_id}")
def update_attribute(attr_id: int, data: AttributeUpdate):
    """更新单个字段的角色配置"""
    session = get_meta_session()
    row = session.query(Attribute).filter(Attribute.id == attr_id).first()
    if not row:
        raise HTTPException(404, "Attribute not found")

    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(row, k, v)
    session.commit()
    return AttributeResponse.model_validate(row)