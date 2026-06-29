"""OLTP 源管理 API"""
from fastapi import APIRouter, HTTPException
from app.database import get_meta_session
from app.models.oltp_source import OltpSource
from app.models.meta import ConnectionConfig
from app.schemas import OltpSourceCreate, OltpSourceUpdate, OltpSourceResponse

router = APIRouter(prefix="/api/oltp-sources", tags=["OLTP 源管理"])


@router.get("")
def list_oltp_sources() -> list[OltpSourceResponse]:
    session = get_meta_session()
    try:
        rows = session.query(OltpSource).all()
        result = []
        for r in rows:
            conn = session.query(ConnectionConfig).filter(ConnectionConfig.id == r.conn_id).first()
            result.append(OltpSourceResponse(
                id=r.id, record_src=r.record_src,
                conn_id=r.conn_id, database_name=r.database_name,
                connection_name=conn.name if conn else None,
                created_at=r.created_at,
            ))
        return result
    finally:
        session.close()


@router.post("")
def create_oltp_source(data: OltpSourceCreate) -> OltpSourceResponse:
    session = get_meta_session()
    try:
        existing = session.query(OltpSource).filter(OltpSource.record_src == data.record_src).first()
        if existing:
            raise HTTPException(400, f"record_src '{data.record_src}' 已存在")
        conn = session.query(ConnectionConfig).filter(ConnectionConfig.id == data.conn_id).first()
        if not conn:
            raise HTTPException(404, f"连接 (ID={data.conn_id}) 不存在")
        obj = OltpSource(record_src=data.record_src, conn_id=data.conn_id, database_name=data.database_name)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return OltpSourceResponse(
            id=obj.id, record_src=obj.record_src,
            conn_id=obj.conn_id, database_name=obj.database_name,
            connection_name=conn.name, created_at=obj.created_at,
        )
    finally:
        session.close()


@router.put("/{source_id}")
def update_oltp_source(source_id: int, data: OltpSourceUpdate) -> OltpSourceResponse:
    session = get_meta_session()
    try:
        obj = session.query(OltpSource).filter(OltpSource.id == source_id).first()
        if not obj:
            raise HTTPException(404, f"OLTP 源 (ID={source_id}) 不存在")
        if data.record_src is not None:
            dup = session.query(OltpSource).filter(
                OltpSource.record_src == data.record_src, OltpSource.id != source_id
            ).first()
            if dup:
                raise HTTPException(400, f"record_src '{data.record_src}' 已被使用")
            obj.record_src = data.record_src
        if data.conn_id is not None:
            conn = session.query(ConnectionConfig).filter(ConnectionConfig.id == data.conn_id).first()
            if not conn:
                raise HTTPException(404, f"连接 (ID={data.conn_id}) 不存在")
            obj.conn_id = data.conn_id
        if data.database_name is not None:
            obj.database_name = data.database_name
        session.commit()
        session.refresh(obj)
        conn = session.query(ConnectionConfig).filter(ConnectionConfig.id == obj.conn_id).first()
        return OltpSourceResponse(
            id=obj.id, record_src=obj.record_src,
            conn_id=obj.conn_id, database_name=obj.database_name,
            connection_name=conn.name if conn else None, created_at=obj.created_at,
        )
    finally:
        session.close()


@router.delete("/{source_id}")
def delete_oltp_source(source_id: int):
    session = get_meta_session()
    try:
        obj = session.query(OltpSource).filter(OltpSource.id == source_id).first()
        if not obj:
            raise HTTPException(404, f"OLTP 源 (ID={source_id}) 不存在")
        session.delete(obj)
        session.commit()
        return {"success": True, "message": "OLTP 源已删除"}
    finally:
        session.close()