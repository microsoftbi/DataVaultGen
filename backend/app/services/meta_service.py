"""元数据服务 — 从源表读取 INFORMATION_SCHEMA 并写入 META"""
import base64
import hashlib
import re
from sqlalchemy import text
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from app.database import get_engine, build_engine
from app.models.meta import Attribute, RecordSource, GenList, ConnectionConfig
from app.config import settings

# ── 密码解密 + 临时引擎（用于按角色绑定的数据库名查询） ──────
_key = base64.urlsafe_b64encode(
    hashlib.sha256(settings.secret_key.encode()).digest()
)
_cipher = Fernet(_key)


def _decrypt_password(encrypted: str) -> str:
    return _cipher.decrypt(encrypted.encode()).decode()


def _build_temp_engine(conn_id: int, database_name: str):
    """根据连接凭据 + 指定数据库名构建临时引擎（不缓存）"""
    from app.database import get_meta_session as _get_ms
    s = _get_ms()
    try:
        row = s.query(ConnectionConfig).filter(ConnectionConfig.id == conn_id).first()
        if not row:
            return None
        password = _decrypt_password(row.password_encrypted)
        return build_engine(row.host, row.port, database_name, row.username, password)
    finally:
        s.close()


# DWH 技术字段列表 — 导入时自动跳过
TECHNICAL_FIELDS = {
    "LOAD_DTS", "LOAD_DT",
    "REC_SRC", "REC_PATH",
    "TRANSFER_DTS", "FILE_TRANSFER_DTS",
    "HK", "HF", "HD",
    "INSERT_TIME", "INSERTTIME",
    "CDC_OPERATION_CODE",
    "VALID_FROM", "VALID_TO", "IS_CURRENT",
    "SEQUENCE_NO", "SESSION_DTS",
    "FULLY_QUALIFIED_FILE_NAME",
}

# 业务键智能匹配模式 — 符合这些模式的字段自动标记为 BK
BK_PATTERNS = [
    re.compile(r'^ID$', re.IGNORECASE),
    re.compile(r'.*_ID$', re.IGNORECASE),
    re.compile(r'.*_CODE$', re.IGNORECASE),
    re.compile(r'.*_KEY$', re.IGNORECASE),
    re.compile(r'.*_NO$', re.IGNORECASE),
    re.compile(r'^CODE$', re.IGNORECASE),
    re.compile(r'^KEY$', re.IGNORECASE),
]


def _is_technical_field(name: str) -> bool:
    """判断是否为 DWH 技术字段"""
    return name.upper() in TECHNICAL_FIELDS or name.upper().startswith("_")


def _suggest_bk(name: str) -> bool:
    """根据字段名智能推荐是否为业务键"""
    return any(p.match(name) for p in BK_PATTERNS)


def get_source_columns(conn_id: int, table_schema: str, table_name: str, database_name: str = None) -> list[dict]:
    """从源数据库读取指定表的列信息"""
    if database_name:
        engine = _build_temp_engine(conn_id, database_name)
        if not engine:
            raise ValueError(f"Connection {conn_id} not found or invalid")
    else:
        engine = get_engine(conn_id)
        if not engine:
            raise ValueError(f"Connection {conn_id} not found")

    sql = text("""
        SELECT
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION,
            NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table
        ORDER BY ORDINAL_POSITION
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql, {"schema": table_schema, "table": table_name}).fetchall()
        return [
            {
                "column_name": row[0],
                "data_type": row[1],
                "character_maximum_length": row[2],
                "numeric_precision": row[3],
                "numeric_scale": row[4],
            }
            for row in rows
        ]


def get_source_tables(conn_id: int, database_name: str = None) -> list[dict]:
    """获取源库的所有用户表"""
    if database_name:
        engine = _build_temp_engine(conn_id, database_name)
        if not engine:
            raise ValueError(f"Connection {conn_id} not found or invalid")
    else:
        engine = get_engine(conn_id)
        if not engine:
            raise ValueError(f"Connection {conn_id} not found")

    sql = text("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql).fetchall()
        return [{"table_schema": r[0], "table_name": r[1]} for r in rows]


def import_table_meta(
    session: Session,
    conn_id: int,
    table_schema: str,
    table_name: str,
    record_source: str = None,
    selected_columns: list[str] = None,
    database_name: str = None,
) -> tuple[int, list[str]]:
    """
    将源表列信息导入 META.ATTRIBUTE
    - selected_columns: 用户指定的导入列名列表，不传则全部导入
    - 自动跳过 DWH 技术字段（LOAD_DTS, HK, HF 等）
    - 根据字段名智能推荐 BK（ID, *_ID, *_CODE 等）
    - 其余字段默认标记为 DI
    """
    columns = get_source_columns(conn_id, table_schema, table_name, database_name=database_name)
    imported = 0
    skipped = []

    if record_source is None:
        record_source = table_schema

    for col in columns:
        col_name = col["column_name"]

        # 用户指定了导入列 → 只导入选中的
        if selected_columns is not None and col_name not in selected_columns:
            continue

        # 自动跳过技术字段
        if _is_technical_field(col_name):
            skipped.append(col_name)
            continue

        exists = session.query(Attribute).filter(
            Attribute.table_name == table_name,
            Attribute.column_name == col_name,
        ).first()
        if exists:
            continue

        is_bk = _suggest_bk(col_name)

        attr = Attribute(
            table_catalog=None,
            table_name=table_name,
            column_name=col_name,
            table_schema=table_schema,
            data_type=col["data_type"],
            character_maximum_length=col["character_maximum_length"],
            numeric_precision=col["numeric_precision"],
            numeric_scale=col["numeric_scale"],
            is_bk=is_bk,
            is_pk=is_bk,      # BK 默认也设置为 PK
            is_di=not is_bk,  # BK 不是 DI，其余字段默认 DI
            record_src=record_source,  # 记录来源 OLTP 源
        )
        session.add(attr)
        imported += 1

    session.commit()
    return imported, skipped


def ensure_gen_list(session: Session, table_name: str, table_catalog: str = None, schema_name: str = "dbo"):
    """确保表存在于对象列表中"""
    exists = session.query(GenList).filter(
        GenList.table_name == table_name
    ).first()
    if not exists:
        gl = GenList(
            table_catalog=table_catalog,
            table_name=table_name,
            schema_name=schema_name,
            is_gen=True,
            is_full_load=False,
        )
        session.add(gl)
        session.commit()