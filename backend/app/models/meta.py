"""META 数据库 ORM 模型（SQLite 兼容）"""
import logging
from sqlalchemy import Column, Integer, String, DateTime, Text, inspect, UniqueConstraint
from sqlalchemy import text as sa_text
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


# 已知的列变更：{表名: [(列名, SQL 类型定义)]}
_MIGRATIONS: dict[str, list[tuple[str, str]]] = {
    "ATTRIBUTE": [
        ("IS_FK", "INTEGER DEFAULT 0"),
        ("DV_COLUMN_NAME", "VARCHAR(50)"),
        ("DV_SAT_ID", "INTEGER"),
        ("DV_HUB_ID", "INTEGER"),
        ("DV_LINK_ID", "INTEGER"),
        ("RECORD_SRC", "VARCHAR(64)"),
        ("TABLE_SCHEMA", "VARCHAR(128) DEFAULT 'dbo'"),
    ],
    "EXECUTION_LOG": [],
    "CONNECTION_CONFIG": [],
    "DATABASE_ROLE": [],
}


def init_meta_db(engine):
    """自动创建 META 库所有表（幂等）+ 增量迁移"""
    Base.metadata.create_all(engine)
    # 尝试添加缺失列
    inspector = inspect(engine)
    for table_name, columns in _MIGRATIONS.items():
        existing = {c["name"] for c in inspector.get_columns(table_name)} if inspector.has_table(table_name) else set()
        with engine.connect() as conn:
            for col_name, col_type in columns:
                if col_name not in existing:
                    try:
                        conn.execute(sa_text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                        logger.info(f"Migrated: added {col_name} to {table_name}")
                    except Exception:
                        conn.rollback()


class GenList(Base):
    __tablename__ = "GEN_LIST"

    id = Column("ID", Integer, primary_key=True, autoincrement=True)
    table_catalog = Column("TABLE_CATALOG", String(128))
    table_name = Column("TABLE_NAME", String(128), nullable=False)
    schema_name = Column("SCHEMA_NAME", String(128), default="dbo")
    is_gen = Column("IS_GEN", Integer, default=1)       # SQLite 无 Boolean，用 0/1
    is_full_load = Column("IS_FULL_LOAD", Integer, default=0)
    created_at = Column("CREATED_AT", DateTime, default=datetime.now)


class Attribute(Base):
    __tablename__ = "ATTRIBUTE"

    id = Column("ID", Integer, primary_key=True, autoincrement=True)
    table_catalog = Column("TABLE_CATALOG", String(128))
    table_name = Column("TABLE_NAME", String(128), nullable=False)
    column_name = Column("COLUMN_NAME", String(128), nullable=False)
    data_type = Column("DATA_TYPE", String(128))
    character_maximum_length = Column("CHARACTER_MAXIMUM_LENGTH", Integer)
    numeric_precision = Column("NUMERIC_PRECISION", Integer)
    numeric_scale = Column("NUMERIC_SCALE", Integer)
    is_bk = Column("IS_BK", Integer, default=0)
    is_pk = Column("IS_PK", Integer, default=0)
    is_di = Column("IS_DI", Integer, default=0)
    is_fk = Column("IS_FK", Integer, default=0)          # Foreign Key (for LINK)
    dv_column_name = Column("DV_COLUMN_NAME", String(50)) # DV 中的列名别名
    dv_sat_id = Column("DV_SAT_ID", Integer, default=None)
    dv_hub_id = Column("DV_HUB_ID", Integer, default=None)
    dv_link_id = Column("DV_LINK_ID", Integer, default=None)
    record_src = Column("RECORD_SRC", String(64), nullable=True)
    table_schema = Column("TABLE_SCHEMA", String(128), default="dbo")
    created_at = Column("CREATED_AT", DateTime, default=datetime.now)


class DvHub(Base):
    __tablename__ = "DV_HUB"

    id = Column("ID", Integer, primary_key=True, autoincrement=True)
    table_name = Column("TABLE_NAME", String(128), nullable=False)
    created_at = Column("CREATED_AT", DateTime, default=datetime.now)


class DvSat(Base):
    __tablename__ = "DV_SAT"

    id = Column("ID", Integer, primary_key=True, autoincrement=True)
    table_name = Column("TABLE_NAME", String(128), nullable=False)
    created_at = Column("CREATED_AT", DateTime, default=datetime.now)


class DvLink(Base):
    __tablename__ = "DV_LINK"

    id = Column("ID", Integer, primary_key=True, autoincrement=True)
    table_name = Column("TABLE_NAME", String(128), nullable=False)
    created_at = Column("CREATED_AT", DateTime, default=datetime.now)


class RecordSource(Base):
    __tablename__ = "RECORD_SOURCE"

    id = Column("ID", Integer, primary_key=True, autoincrement=True)
    database_name = Column("DATABASE_NAME", String(128))
    record_source_name = Column("RECORD_SOURCE_NAME", String(128), nullable=False)


class ConnectionConfig(Base):
    __tablename__ = "CONNECTION_CONFIG"

    id = Column("ID", Integer, primary_key=True, autoincrement=True)
    name = Column("NAME", String(128), nullable=False)
    db_type = Column("DB_TYPE", String(32), default="sqlserver")
    host = Column("HOST", String(255))
    port = Column("PORT", Integer, default=1433)
    database_name = Column("DATABASE_NAME", String(128))
    username = Column("USERNAME", String(128))
    password_encrypted = Column("PASSWORD_ENCRYPTED", Text)
    is_meta = Column("IS_META", Integer, default=0)
    is_source = Column("IS_SOURCE", Integer, default=0)
    is_target = Column("IS_TARGET", Integer, default=0)
    created_at = Column("CREATED_AT", DateTime, default=datetime.now)


class DatabaseRole(Base):
    """数据库角色绑定：OLTP / STAGE / CORE 分别绑定到哪个连接的哪个数据库"""
    __tablename__ = "DATABASE_ROLE"
    __table_args__ = (UniqueConstraint("ROLE_NAME"),)

    id = Column("ID", Integer, primary_key=True, autoincrement=True)
    role_name = Column("ROLE_NAME", String(32), nullable=False)   # OLTP / STAGE / CORE
    conn_id = Column("CONN_ID", Integer, nullable=False)          # 关联 ConnectionConfig.id
    database_name = Column("DATABASE_NAME", String(128), nullable=False)
    created_at = Column("CREATED_AT", DateTime, default=datetime.now)


class Configuration(Base):
    __tablename__ = "CONFIGURATION"

    id = Column("ID", Integer, primary_key=True, autoincrement=True)
    config_name = Column("CONFIG_NAME", String(128), nullable=False, unique=True)
    config_value = Column("CONFIG_VALUE", Text)
    description = Column("DESCRIPTION", String(500))


class ExecutionLog(Base):
    __tablename__ = "EXECUTION_LOG"

    id = Column("ID", Integer, primary_key=True, autoincrement=True)
    log_source = Column("LOG_SOURCE", String(255))
    log_type = Column("LOG_TYPE", String(1), default="N")  # SQLite 无 CHAR
    message = Column("MESSAGE", Text)
    created_at = Column("CREATED_AT", DateTime, default=datetime.now)