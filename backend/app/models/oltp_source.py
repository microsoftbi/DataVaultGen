"""OLTP 源配置模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base


class OltpSource(Base):
    """OLTP 源表 — 每行一个独立的 OLTP 源"""
    __tablename__ = "OLTP_SOURCE"

    id = Column("ID", Integer, primary_key=True, autoincrement=True)
    record_src = Column("RECORD_SRC", String(64), nullable=False, unique=True)
    conn_id = Column("CONN_ID", Integer, nullable=False)
    database_name = Column("DATABASE_NAME", String(128), nullable=False)
    created_at = Column("CREATED_AT", DateTime, default=datetime.now)