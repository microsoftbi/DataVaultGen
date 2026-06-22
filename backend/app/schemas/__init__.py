"""Pydantic 请求/响应模型"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── 连接管理 ──────────────────────────────────────────────────

class ConnectionCreate(BaseModel):
    name: str
    host: str = "localhost"
    port: int = 1433
    database_name: Optional[str] = None
    username: str = "sa"
    password: str
    is_meta: bool = False
    is_source: bool = False
    is_target: bool = False


class ConnectionUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_meta: Optional[bool] = None
    is_source: Optional[bool] = None
    is_target: Optional[bool] = None


class ConnectionResponse(BaseModel):
    id: int
    name: str
    db_type: str
    host: str
    port: int
    database_name: str
    username: str
    is_meta: bool
    is_source: bool
    is_target: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ConnectionTestRequest(BaseModel):
    host: str
    port: int = 1433
    database_name: Optional[str] = None
    username: str
    password: str


# ── 元数据导入 ────────────────────────────────────────────────

class SourceTable(BaseModel):
    table_schema: str
    table_name: str


class SourceColumn(BaseModel):
    column_name: str
    data_type: str
    character_maximum_length: Optional[int] = None
    numeric_precision: Optional[int] = None
    numeric_scale: Optional[int] = None


class MetaImportRequest(BaseModel):
    conn_id: int
    table_schema: str
    table_name: str
    record_source: Optional[str] = None
    columns: Optional[list[str]] = None  # 指定要导入的列名，不传则全部导入


class AttributeUpdate(BaseModel):
    is_bk: Optional[bool] = None
    is_pk: Optional[bool] = None
    is_di: Optional[bool] = None
    is_fk: Optional[bool] = None
    dv_column_name: Optional[str] = None
    dv_sat_id: Optional[int] = None
    dv_hub_id: Optional[int] = None
    dv_link_id: Optional[int] = None


class AttributeBatchUpdate(BaseModel):
    updates: list[dict]


class AttributeResponse(BaseModel):
    id: int
    table_catalog: Optional[str]
    table_name: str
    column_name: str
    data_type: Optional[str]
    character_maximum_length: Optional[int]
    numeric_precision: Optional[int]
    numeric_scale: Optional[int]
    is_bk: bool
    is_pk: bool
    is_di: bool
    is_fk: bool
    dv_column_name: Optional[str]
    dv_sat_id: Optional[int]
    dv_hub_id: Optional[int]
    dv_link_id: Optional[int]

    class Config:
        from_attributes = True


# ── DV 配置 ──────────────────────────────────────────────────

class DvTableCreate(BaseModel):
    table_name: str


class DvTableResponse(BaseModel):
    id: int
    table_name: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── 对象列表 ──────────────────────────────────────────────────

class ObjectListItem(BaseModel):
    id: int
    table_catalog: Optional[str]
    table_name: str
    schema_name: str
    is_gen: bool
    is_full_load: bool

    class Config:
        from_attributes = True


class ObjectListUpdate(BaseModel):
    is_gen: Optional[bool] = None
    is_full_load: Optional[bool] = None


class ObjectListBatchUpdate(BaseModel):
    updates: list[dict]  # [{id: int, is_gen: bool, is_full_load: bool}]


# ── 代码生成 ──────────────────────────────────────────────────

class GenerateResult(BaseModel):
    stg: str = ""
    cdc: str = ""
    log: str = ""
    v_mta: str = ""
    v_current: str = ""
    usp_stg: str = ""
    usp_cdc: str = ""
    usp_log: str = ""
    dv_hub: str = ""
    dv_sat: str = ""
    dv_link: str = ""
    dv_usp_hub: str = ""
    dv_usp_sat: str = ""
    dv_usp_link: str = ""
    execute_flow: str = ""
    combined: str = ""


class DeployRequest(BaseModel):
    conn_id: int
    sql: str
    object_type: Optional[str] = "all"  # all | tables | views | procs


# ── 配置 ──────────────────────────────────────────────────────

class ConfigUpdate(BaseModel):
    psa_db_name: Optional[str] = None
    hash_dummy: Optional[str] = None
    core_db_name: Optional[str] = None


class ConfigResponse(BaseModel):
    psa_db_name: str
    hash_dummy: str
    core_db_name: str


# ── 数据库角色绑定 ────────────────────────────────────────────

class DatabaseRoleUpdate(BaseModel):
    """单个角色的绑定配置"""
    conn_id: int
    database_name: str


class DatabaseRolesRequest(BaseModel):
    """三个角色的绑定配置"""
    oltp: DatabaseRoleUpdate
    stage: DatabaseRoleUpdate
    core: DatabaseRoleUpdate


class DatabaseRoleResponse(BaseModel):
    id: int
    role_name: str
    conn_id: int
    database_name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── 日志 ──────────────────────────────────────────────────────

class LogResponse(BaseModel):
    id: int
    log_source: Optional[str]
    log_type: str
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True