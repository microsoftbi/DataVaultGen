"""数据库连接管理 API"""
import base64
import hashlib
from fastapi import APIRouter, HTTPException
from cryptography.fernet import Fernet
from app.database import (
    get_meta_session, register_engine, remove_engine, build_engine, test_connection,
)
from app.models.meta import ConnectionConfig
from app.schemas import (
    ConnectionCreate, ConnectionUpdate, ConnectionResponse, ConnectionTestRequest,
)
from app.config import settings

router = APIRouter(prefix="/api/connections", tags=["连接管理"])

# 从 secret_key 派生 32 字节的 Fernet 密钥（确保重启后可解密）
_key = base64.urlsafe_b64encode(
    hashlib.sha256(settings.secret_key.encode()).digest()
)
_cipher = Fernet(_key)


def _encrypt(password: str) -> str:
    return _cipher.encrypt(password.encode()).decode()


def _decrypt(encrypted: str) -> str:
    return _cipher.decrypt(encrypted.encode()).decode()


@router.get("")
def list_connections():
    session = get_meta_session()
    rows = session.query(ConnectionConfig).all()
    return [ConnectionResponse.model_validate(r) for r in rows]


@router.get("/{conn_id}")
def get_connection(conn_id: int):
    session = get_meta_session()
    row = session.query(ConnectionConfig).filter(ConnectionConfig.id == conn_id).first()
    if not row:
        raise HTTPException(404, "Connection not found")
    return ConnectionResponse.model_validate(row)


@router.post("", status_code=201)
def create_connection(data: ConnectionCreate):
    session = get_meta_session()
    row = ConnectionConfig(
        name=data.name,
        host=data.host,
        port=data.port,
        database_name=data.database_name,
        username=data.username,
        password_encrypted=_encrypt(data.password),
        is_meta=data.is_meta,
        is_source=data.is_source,
        is_target=data.is_target,
    )
    session.add(row)
    session.commit()
    session.refresh(row)

    # 注册动态引擎
    engine = build_engine(data.host, data.port, data.database_name, data.username, data.password)
    register_engine(row.id, engine)

    return ConnectionResponse.model_validate(row)


@router.put("/{conn_id}")
def update_connection(conn_id: int, data: ConnectionUpdate):
    session = get_meta_session()
    row = session.query(ConnectionConfig).filter(ConnectionConfig.id == conn_id).first()
    if not row:
        raise HTTPException(404, "Connection not found")

    update_data = data.model_dump(exclude_unset=True, exclude={"password"})
    for k, v in update_data.items():
        setattr(row, k, v)

    if data.password is not None:
        row.password_encrypted = _encrypt(data.password)

    session.commit()

    # 重新注册引擎
    remove_engine(conn_id)
    password = _decrypt(row.password_encrypted)
    engine = build_engine(row.host, row.port, row.database_name, row.username, password)
    register_engine(conn_id, engine)

    return ConnectionResponse.model_validate(row)


@router.delete("/{conn_id}")
def delete_connection(conn_id: int):
    session = get_meta_session()
    row = session.query(ConnectionConfig).filter(ConnectionConfig.id == conn_id).first()
    if not row:
        raise HTTPException(404, "Connection not found")
    session.delete(row)
    session.commit()
    remove_engine(conn_id)
    return {"message": "Deleted"}


@router.post("/test")
def test_conn(data: ConnectionTestRequest):
    ok, detail = test_connection(data.host, data.port, data.database_name, data.username, data.password)
    return {"success": ok, "message": "Connection successful" if ok else detail}


@router.post("/{conn_id}/test")
def test_saved_connection(conn_id: int):
    session = get_meta_session()
    row = session.query(ConnectionConfig).filter(ConnectionConfig.id == conn_id).first()
    if not row:
        raise HTTPException(404, "Connection not found")
    password = _decrypt(row.password_encrypted)
    ok, detail = test_connection(row.host, row.port, row.database_name, row.username, password)
    return {"success": ok, "message": "Connection successful" if ok else detail}