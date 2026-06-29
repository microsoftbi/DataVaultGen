# 多 OLTP 源接入 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Support multiple OLTP source databases, each with its own connection config and `record_src` alias, converging into the same PSA/DV target database through table name prefixing.

**Architecture:** New `OLTP_SOURCE` table replaces the single OLTP role in `DATABASE_ROLE`. `Attribute` table gains `record_src` column. PSA/DV generators filter by `record_src` and prefix table names. Frontend pages gain OLTP source management, selection, and display.

**Tech Stack:** SQLAlchemy ORM, FastAPI, Vue 3 + Element Plus, Jinja2 SQL templates

## Global Constraints

- All new backend files use SQLAlchemy ORM `Base` from `app.models.meta`
- Password encryption/decryption follows existing Fernet pattern in `app.config`
- Frontend table column `record_src` uses `el-tag` for display
- All UI strings must have corresponding i18n entries in both `zh-CN.ts` and `en.ts`
- Frontend API functions in `src/api/index.ts` use axios `http` instance
- PSA/DV table name prefix format: `{record_src}_{original_name}` (e.g. `erp_CUSTOMER`)

---

### Task 1: OltpSource Model + Attribute.record_src column

**Files:**
- Create: `backend/app/models/oltp_source.py`
- Modify: `backend/app/models/meta.py:34-42` (add `record_src` column to Attribute)

**Interfaces:**
- Consumes: `Base` from `sqlalchemy.orm.declarative_base` (inherited via `app.database.Base`)
- Produces: `OltpSource` model class, `Attribute.record_src` column

- [ ] **Step 1: Create OltpSource model**

Write `backend/app/models/oltp_source.py`:

```python
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
```

- [ ] **Step 2: Add `record_src` column to Attribute model**

Edit `backend/app/models/meta.py`, add `record_src` field after `is_fk`:

```python
# In Attribute class, after is_fk line:
is_fk = Column("IS_FK", Integer, default=0)
record_src = Column("RECORD_SRC", String(64), nullable=True)
```

- [ ] **Step 3: Add OltpSource to `__init__.py` for clean import**

Create `backend/app/models/__init__.py`:

```python
from .meta import (
    Attribute, ConnectionConfig, Configuration, DatabaseRole,
    DvHub, DvLink, DvSat, ExecutionLog, GenList, RecordSource,
)
from .oltp_source import OltpSource

__all__ = [
    "Attribute", "ConnectionConfig", "Configuration", "DatabaseRole",
    "DvHub", "DvLink", "DvSat", "ExecutionLog", "GenList", "RecordSource",
    "OltpSource",
]
```

---

### Task 2: Backend Pydantic Schemas

**Files:**
- Modify: `backend/app/schemas/__init__.py`

**Interfaces:**
- Consumes: `BaseModel` from pydantic
- Produces: `OltpSourceCreate`, `OltpSourceUpdate`, `OltpSourceResponse` schemas; modified `DatabaseRolesRequest` (remove oltp)

- [ ] **Step 1: Add OltpSource schemas**

Add to `backend/app/schemas/__init__.py`:

```python
class OltpSourceCreate(BaseModel):
    record_src: str = Field(..., max_length=64, description="源别名，同时也是 record_source")
    conn_id: int = Field(..., description="关联 ConnectionConfig.id")
    database_name: str = Field(..., max_length=128, description="数据库名")

class OltpSourceUpdate(BaseModel):
    record_src: Optional[str] = Field(None, max_length=64)
    conn_id: Optional[int] = None
    database_name: Optional[str] = Field(None, max_length=128)

class OltpSourceResponse(BaseModel):
    id: int
    record_src: str
    conn_id: int
    database_name: str
    connection_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Modify DatabaseRolesRequest — remove oltp**

Change `DatabaseRolesRequest` to:

```python
class DatabaseRolesRequest(BaseModel):
    """两个角色的绑定配置（OLTP 已移至 OLTP_SOURCE 表）"""
    stage: DatabaseRoleUpdate
    core: DatabaseRoleUpdate
```

Also update `DatabaseRolesData` response if it exists as a model — remove `oltp` field.

```python
class DatabaseRolesData(BaseModel):
    stage: Optional[DatabaseRoleResponse] = None
    core: Optional[DatabaseRoleResponse] = None
```

---

### Task 3: OLTP Source CRUD API

**Files:**
- Create: `backend/app/api/oltp_sources.py`

**Interfaces:**
- Consumes: `OltpSource`, `ConnectionConfig` models; `OltpSourceCreate`, `OltpSourceUpdate`, `OltpSourceResponse` schemas; `get_meta_session`
- Produces: GET/POST/PUT/DELETE endpoints at `/api/oltp-sources`
- Consumed by: Frontend OLTP source management in ConnectionView.vue

- [ ] **Step 1: Write the API file**

Create `backend/app/api/oltp_sources.py`:

```python
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
        # 检查 record_src 唯一
        existing = session.query(OltpSource).filter(OltpSource.record_src == data.record_src).first()
        if existing:
            raise HTTPException(400, f"record_src '{data.record_src}' 已存在")
        # 检查连接存在
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
```

- [ ] **Step 2: Register router in main.py**

Edit `backend/main.py` — add import and include_router for `oltp_sources`:

```python
from app.api.oltp_sources import router as oltp_sources_router
# ... in the create_app() or router includes section:
app.include_router(oltp_sources_router)
```

---

### Task 4: DB Roles API — Remove OLTP

**Files:**
- Modify: `backend/app/api/db_roles.py`

**Interfaces:**
- Consumes: `DatabaseRole` model, `DatabaseRolesRequest` (modified in Task 2)
- Produces: Simplified role response with only `stage` and `core`
- Consumed by: Frontend `getDbRoles` / `updateDbRoles`

- [ ] **Step 1: Update get_db_roles — remove oltp**

```python
@router.get("/db-roles")
def get_db_roles():
    session = get_meta_session()
    roles = session.query(DatabaseRole).all()
    result = {}
    for r in roles:
        result[r.role_name.lower()] = _role_to_dict(r)
    for name in ("stage", "core"):
        if name not in result:
            result[name] = None
    return {"success": True, "data": result}
```

- [ ] **Step 2: Update update_db_roles — remove oltp**

```python
@router.put("/db-roles")
def update_db_roles(data: DatabaseRolesRequest):
    session = get_meta_session()
    mappings = {"stage": "STAGE", "core": "CORE"}
    for key, role_cfg in [("stage", data.stage), ("core", data.core)]:
        role_name = mappings[key]
        existing = session.query(DatabaseRole).filter(DatabaseRole.role_name == role_name).first()
        if existing:
            existing.conn_id = role_cfg.conn_id
            existing.database_name = role_cfg.database_name
        else:
            session.add(DatabaseRole(role_name=role_name, conn_id=role_cfg.conn_id, database_name=role_cfg.database_name))
    session.commit()
    return get_db_roles()
```

---

### Task 5: Meta Import — Support record_src + return OLTP sources list

**Files:**
- Modify: `backend/app/api/meta_import.py`
- Modify: `backend/app/services/meta_service.py`

**Interfaces:**
- Consumes: `OltpSource` model, `record_src` parameter in import
- Produces: Updated `/api/meta/oltp-source` (returns list of sources), `/api/meta/import` (accepts record_src)

- [ ] **Step 1: Change `/api/meta/oltp-source` to return all OLTP sources**

In `backend/app/api/meta_import.py`, replace the existing `get_oltp_source()` endpoint:

```python
@router.get("/oltp-source")
def get_oltp_sources():
    """获取所有 OLTP 源列表"""
    session = get_meta_session()
    try:
        sources = session.query(OltpSource).all()
        result = []
        for src in sources:
            conn = session.query(ConnectionConfig).filter(ConnectionConfig.id == src.conn_id).first()
            result.append({
                "id": src.id,
                "record_src": src.record_src,
                "conn_id": src.conn_id,
                "database_name": src.database_name,
                "connection_name": conn.name if conn else None,
                "host": conn.host if conn else None,
            })
        return {"success": True, "sources": result}
    finally:
        session.close()
```

- [ ] **Step 2: Update `import_table_meta` in meta_service.py to accept and store `record_src`**

In `backend/app/services/meta_service.py`, modify `import_table_meta()` signature and implementation:

```python
def import_table_meta(
    session, conn_id: int, table_schema: str, table_name: str,
    columns: list[str] = None, record_src: str = None, database_name: str = None,
) -> dict:
    # ... existing logic to get columns from source ...
    # When creating Attribute rows, add record_src:
    for col_data in columns_data:
        attr = Attribute(
            table_catalog=database_name or conn_db_name,
            table_schema=table_schema,
            table_name=table_name,
            column_name=col_data["column_name"],
            data_type=col_data["data_type"],
            character_maximum_length=col_data.get("character_maximum_length"),
            numeric_precision=col_data.get("numeric_precision"),
            numeric_scale=col_data.get("numeric_scale"),
            is_bk=0, is_pk=0, is_di=0, is_fk=0,
            record_src=record_src,  # ← new field
        )
        session.add(attr)
    # ...
```

- [ ] **Step 3: Update import endpoint to pass record_src**

In `backend/app/api/meta_import.py`, update the import endpoint to accept and pass `record_src`:

```python
@router.post("/meta/import")
def import_meta(data: ImportRequest):
    # data now has optional record_src field
    session = get_meta_session()
    try:
        result = import_table_meta(
            session, data.conn_id, data.table_schema, data.table_name,
            columns=data.columns, record_src=data.record_src, database_name=data.database_name,
        )
        return {"success": True, **result}
    finally:
        session.close()
```

Update `ImportRequest` schema to add optional `record_src`:

```python
class ImportRequest(BaseModel):
    conn_id: int
    table_schema: str
    table_name: str
    record_source: Optional[str] = None  # matches frontend field name
    columns: Optional[list[str]] = None
    database_name: Optional[str] = None
```

---

### Task 6: Generator API — Accept `record_src` Parameter

**Files:**
- Modify: `backend/app/api/generator.py`

**Interfaces:**
- Consumes: `record_src` query parameter from request
- Produces: Updated `_get_psa()` and `_get_dv()` that accept `record_src`
- Consumed by: Frontend generation pages

- [ ] **Step 1: Update `_get_oltp_db` to query OltpSource table**

```python
def _get_oltp_db(session, record_src: str = None) -> str:
    """从 OLTP_SOURCE 表获取数据库名"""
    if record_src:
        source = session.query(OltpSource).filter(OltpSource.record_src == record_src).first()
        return source.database_name if source else None
    return None
```

- [ ] **Step 2: Update `_get_psa` and `_get_dv` to accept `record_src`**

```python
def _get_psa(session=None, record_src: str = None):
    if session is None:
        session = get_meta_session()
    psa_db, hash_d, _ = _get_config(session)
    oltp_db = _get_oltp_db(session, record_src)
    return PSAGenerator(session, psa_db, hash_d, oltp_db_name=oltp_db, record_src=record_src)


def _get_dv(session=None, record_src: str = None):
    if session is None:
        session = get_meta_session()
    psa_db, hash_d, core_db = _get_config(session)
    return DVGenerator(session, psa_db, core_db, hash_d, record_src=record_src)
```

- [ ] **Step 3: Add `record_src` query parameter to all generation endpoints**

Update all PSA endpoints:

```python
@router.post("/psa/stg")
def generate_stg(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_psa(record_src=record_src)
    return {"success": True, "sql": gen.generate_stg_table()}
```

Do the same for `/psa/cdc`, `/psa/log`, `/psa/views`, `/psa/usps`, `/psa/all`, `/psa/flow`.

Update all DV endpoints similarly:

```python
@router.post("/dv/hub")
def generate_dv_hub(record_src: str = Query(None, description="OLTP 源别名")):
    gen = _get_dv(record_src=record_src)
    return {"success": True, "sql": gen.generate_hub_table()}
```

Do the same for `/dv/sat`, `/dv/link`, `/dv/usp-hub`, `/dv/usp-sat`, `/dv/usp-link`, `/dv/all`, `/dv/flow`.

Add import:
```python
from fastapi import APIRouter, Query
from app.models.oltp_source import OltpSource
```

---

### Task 7: PSA Generator — Filter by record_src + Prefix Table Names

**Files:**
- Modify: `backend/app/services/generator_psa.py`

**Interfaces:**
- Consumes: `record_src` parameter in constructor
- Produces: PSA SQL with `{record_src}_` prefixed table names, filtered by record_src

- [ ] **Step 1: Update constructor to accept `record_src`**

```python
class PSAGenerator:
    def __init__(self, session: Session, psa_db_name: str, hash_dummy: str = "@IAMHUSKIES@",
                 oltp_db_name: str = None, record_src: str = None):
        self.session = session
        self.psa_db_name = psa_db_name
        self.hash_dummy = hash_dummy
        self.oltp_db_name = oltp_db_name
        self.record_src = record_src
        self.template = TemplateEngine()
```

- [ ] **Step 2: Update `_load_tables` to filter by `record_src` and add prefix**

```python
def _load_tables(self) -> list[dict]:
    query = self.session.query(Attribute).filter(
        Attribute.is_pk.is_(True) | Attribute.is_bk.is_(True) |
        Attribute.is_di.is_(True) | Attribute.is_fk.is_(True)
    )
    if self.record_src:
        query = query.filter(Attribute.record_src == self.record_src)
    rows = query.all()

    table_map: dict[str, dict] = {}
    for row in rows:
        key = row.table_name
        if key not in table_map:
            # Determine the object_name with prefix
            prefix = f"{self.record_src}_" if self.record_src else ""
            table_map[key] = {
                "object_name": f"{prefix}{row.table_name}",
                "schema_name": "dbo",
                "record_source": self.record_src or "dbo",
                "pk_fields": [],
                "bk_fields": [],
                "fk_fields": [],
                "di_fields": [],
            }
        field = {
            "field_name": row.column_name,
            "field_type": self._resolve_type(
                row.data_type, row.character_maximum_length,
                row.numeric_precision, row.numeric_scale,
            ),
        }
        if row.is_pk:
            table_map[key]["pk_fields"].append(field)
        elif row.is_bk:
            table_map[key]["bk_fields"].append(field)
        elif row.is_fk:
            table_map[key]["fk_fields"].append(field)
        elif row.is_di:
            table_map[key]["di_fields"].append(field)

    return list(table_map.values())
```

Update `record_source` field in `usp_stg` template context too — change `"oltp_db_name": self.oltp_db_name or self.psa_db_name` to use `self.record_src` for looking up the actual OLTP database name.

---

### Task 8: DV Generator — Filter by record_src + Prefix Table Names

**Files:**
- Modify: `backend/app/services/generator_dv.py`

**Interfaces:**
- Consumes: `record_src` parameter in constructor
- Produces: DV SQL with `{record_src}_` prefixed table names, filtered by record_src

- [ ] **Step 1: Update constructor**

```python
class DVGenerator:
    def __init__(self, session: Session, psa_db_name: str, core_db_name: str,
                 hash_tail: str, record_src: str = None):
        self.session = session
        self.psa_db_name = psa_db_name
        self.core_db_name = core_db_name
        self.hash_tail = hash_tail
        self.record_src = record_src
        self.template = TemplateEngine()
```

- [ ] **Step 2: Add record_src filter helper and prefix to all _load_* methods**

In `_load_hubs()`, `_load_sats()`, `_load_links()` — add filter by `self.record_src` on Attribute queries where applicable. For HUB/SAT/LINK definitions (DvHub/DvSat/DvLink rows), those are per-source objects so we filter Attributes by `record_src`.

Add a helper:
```python
def _prefix(self, name: str) -> str:
    return f"{self.record_src}_{name}" if self.record_src else name
```

Apply `_prefix()` to:
- `hub.table_name` → `self._prefix(hub.table_name)` in `_load_hubs`
- `sat.table_name` → `self._prefix(sat.table_name)` in `_load_sats`
- `link.table_name` → `self._prefix(link.table_name)` in `_load_links`
- `record_source` → `self.record_src` instead of `"dbo"`
- `psa_table_name` → `self._prefix(psa_table.table_name)`

---

### Task 9: Data Preview API — Show All OLTP Sources Flat

**Files:**
- Modify: `backend/app/api/data_preview.py`

**Interfaces:**
- Consumes: `OltpSource` model
- Produces: Updated `/api/preview/databases` — "oltp" returns source list; objects/data using `_build_role_engine_by_conn`

- [ ] **Step 1: Update `/api/preview/databases` — OLTP returns list**

```python
@router.get("/databases")
def get_databases():
    session = get_meta_session()
    try:
        result = {}
        # OLTP: return all sources
        sources = session.query(OltpSource).all()
        oltp_list = []
        for src in sources:
            conn = session.query(ConnectionConfig).filter(ConnectionConfig.id == src.conn_id).first()
            oltp_list.append({
                "conn_id": src.conn_id,
                "database_name": src.database_name,
                "connection_name": conn.name if conn else None,
                "record_src": src.record_src,
            })
        result["oltp"] = oltp_list

        # STAGE, CORE: unchanged
        for role_name in ("STAGE", "CORE"):
            role = session.query(DatabaseRole).filter(DatabaseRole.role_name == role_name).first()
            if role:
                conn = session.query(ConnectionConfig).filter(ConnectionConfig.id == role.conn_id).first()
                result[role_name.lower()] = {
                    "conn_id": role.conn_id,
                    "database_name": role.database_name,
                    "connection_name": conn.name if conn else None,
                }
            else:
                result[role_name.lower()] = None
        return {"success": True, "data": result}
    finally:
        session.close()
```

---

### Task 10: Frontend Types

**Files:**
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: Add OltpSource type**

```typescript
export interface OltpSource {
  id: number
  record_src: string
  conn_id: number
  database_name: string
  connection_name: string | null
  created_at: string | null
}

export interface OltpSourceCreate {
  record_src: string
  conn_id: number
  database_name: string
}

export interface OltpSourceUpdate {
  record_src?: string
  conn_id?: number
  database_name?: string
}
```

- [ ] **Step 2: Update DatabaseRolesData — remove oltp**

```typescript
export interface DatabaseRolesData {
  stage: DatabaseRoleItem | null
  core: DatabaseRoleItem | null
}
```

---

### Task 11: Frontend API Functions

**Files:**
- Modify: `frontend/src/api/index.ts`

- [ ] **Step 1: Add OLTP source API functions**

```typescript
// ── OLTP 源管理 ──────────────────────────────────────────

export function listOltpSources() {
  return http.get<{ success: boolean; sources: any[] }>('/oltp-sources')
}

export function createOltpSource(data: OltpSourceCreate) {
  return http.post<OltpSource>('/oltp-sources', data)
}

export function updateOltpSource(id: number, data: OltpSourceUpdate) {
  return http.put<OltpSource>(`/oltp-sources/${id}`, data)
}

export function deleteOltpSource(id: number) {
  return http.delete(`/oltp-sources/${id}`)
}
```

- [ ] **Step 2: Update `getOltpSource` to return list**

```typescript
export function getOltpSources() {
  return http.get<{ success: boolean; sources: any[] }>('/meta/oltp-source')
}
```

Add import:
```typescript
import type { OltpSource, OltpSourceCreate, OltpSourceUpdate } from '@/types'
```

- [ ] **Step 3: Update `getDbRoles` and `updateDbRoles` types**

```typescript
export function getDbRoles() {
  return http.get<{ success: boolean; data: any }>('/db-roles')
}

export function updateDbRoles(data: { stage: DatabaseRoleUpdate; core: DatabaseRoleUpdate }) {
  return http.put<{ success: boolean; data: any }>('/db-roles', data)
}
```

---

### Task 12: Frontend i18n

**Files:**
- Modify: `frontend/src/i18n/locales/zh-CN.ts`
- Modify: `frontend/src/i18n/locales/en.ts`

- [ ] **Step 1: Update zh-CN.ts**

Add to `connection` section:
```typescript
oltpSourceSection: 'OLTP 源管理',
addOltpSource: '新增 OLTP 源',
editOltpSource: '编辑 OLTP 源',
deleteOltpSourceConfirm: '确定要删除 OLTP 源 "{name}" 吗？',
recordSrc: 'Record Source',
recordSrcRequired: '请输入 Record Source',
recordSrcPlaceholder: '如 erp, crm',
selectOltpConn: '选择 OLTP 连接',
selectOltpConnRequired: '请选择连接',
dbNamePlaceholder: '数据库名称',
oltpConnColumn: '目标连接',
```

Remove `oltpLabel`, `oltpRole` if they exist.

Update `metaImport` section — change step 1 wording:
```typescript
step1Title: '选择 OLTP 源',
step1Desc: '选择 OLTP 源',
step1TitleLong: '步骤 1：选择 OLTP 源',
selectOltp: '请选择 OLTP 源',
emptyOltpSources: '暂无 OLTP 源',
emptyOltpHint: '请先在连接管理页面配置 OLTP 源。',
```

Add to `metaConfig` section:
```typescript
recordSrcColumn: '数据来源',
```

Add to `generate` section:
```typescript
selectOltpSource: '选择 OLTP 源',
selectOltpSourcePh: '请选择 OLTP 源',
```

- [ ] **Step 2: Update en.ts** (corresponding English translations)

```typescript
// connection section
oltpSourceSection: 'OLTP Sources',
addOltpSource: 'Add OLTP Source',
editOltpSource: 'Edit OLTP Source',
deleteOltpSourceConfirm: 'Delete OLTP source "{name}"?',
recordSrc: 'Record Source',
recordSrcRequired: 'Record Source is required',
recordSrcPlaceholder: 'e.g. erp, crm',
selectOltpConn: 'Select OLTP Connection',
selectOltpConnRequired: 'Please select a connection',
dbNamePlaceholder: 'Database name',
oltpConnColumn: 'Target Connection',
```

---

### Task 13: ConnectionView — Remove OLTP Role, Add OLTP Source Management

**Files:**
- Modify: `frontend/src/views/ConnectionView.vue`

- [ ] **Step 1: Remove OLTP role binding from template and script**

In template, remove the `el-form-item` for OLTP (lines 58-81 of original). Keep STAGE and CORE form items.

In script, update:
```typescript
const rolesForm = reactive<{
  stage: DatabaseRoleUpdate
  core: DatabaseRoleUpdate
}>({
  stage: { conn_id: 0, database_name: '' },
  core: { conn_id: 0, database_name: '' },
})
```

Update `fetchRoles()` — remove oltp handling.
Update `handleSaveRoles()` — remove oltp from request body.

- [ ] **Step 2: Add OLTP Source Management section after roles card**

Add a new card in template (after the `</el-card>` of roles binding):

```html
<!-- OLTP 源管理 -->
<el-card class="section-card" style="margin-top: 20px">
  <template #header>
    <div class="section-header">
      <span>{{ $t('connection.oltpSourceSection') }}</span>
      <el-button type="primary" size="small" @click="openAddOltpSource">
        {{ $t('connection.addOltpSource') }}
      </el-button>
    </div>
  </template>

  <el-table :data="oltpSources" v-loading="oltpLoading" border stripe size="small" style="width: 100%">
    <el-table-column prop="record_src" :label="$t('connection.recordSrc')" width="160" />
    <el-table-column :label="$t('connection.oltpConnColumn')" min-width="200">
      <template #default="{ row }">
        {{ row.connection_name || '-' }} (ID: {{ row.conn_id }})
      </template>
    </el-table-column>
    <el-table-column prop="database_name" :label="$t('connection.dbName')" width="180" />
    <el-table-column :label="$t('common.operation')" width="120" align="center">
      <template #default="{ row }">
        <el-button size="small" text @click="openEditOltpSource(row)">{{ $t('common.edit') }}</el-button>
        <el-button size="small" text type="danger" @click="handleDeleteOltpSource(row)">{{ $t('common.delete') }}</el-button>
      </template>
    </el-table-column>
  </el-table>
</el-card>
```

- [ ] **Step 3: Add OLTP source dialog**

```html
<el-dialog
  v-model="oltpDialogVisible"
  :title="isEditingOltp ? $t('connection.editOltpSource') : $t('connection.addOltpSource')"
  width="480px"
  :close-on-click-modal="false"
>
  <el-form ref="oltpFormRef" :model="oltpForm" :rules="oltpFormRules" label-width="140px">
    <el-form-item :label="$t('connection.recordSrc')" prop="record_src">
      <el-input v-model="oltpForm.record_src" :placeholder="$t('connection.recordSrcPlaceholder')" />
    </el-form-item>
    <el-form-item :label="$t('connection.selectOltpConn')" prop="conn_id"
      :rules="[{ required: true, message: t('connection.selectOltpConnRequired'), trigger: 'change' }]"
    >
      <el-select v-model="oltpForm.conn_id" :placeholder="$t('connection.selectConn')" style="width: 100%">
        <el-option v-for="c in connectionStore.connections" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
    </el-form-item>
    <el-form-item :label="$t('connection.dbName')" prop="database_name"
      :rules="[{ required: true, message: t('connection.inputDbNamePh'), trigger: 'blur' }]"
    >
      <el-input v-model="oltpForm.database_name" :placeholder="$t('connection.dbNamePlaceholder')" />
    </el-form-item>
  </el-form>
  <template #footer>
    <el-button @click="oltpDialogVisible = false">{{ $t('common.cancel') }}</el-button>
    <el-button type="primary" :loading="savingOltp" @click="handleSaveOltpSource">{{ $t('common.save') }}</el-button>
  </template>
</el-dialog>
```

- [ ] **Step 4: Add script logic for OLTP source management**

```typescript
// ── OLTP 源管理 ──────────────────────────────────────────

const oltpSources = ref<OltpSource[]>([])
const oltpLoading = ref(false)

async function fetchOltpSources() {
  oltpLoading.value = true
  try {
    const res = await api.listOltpSources()
    oltpSources.value = res.data
  } catch {
    // ignore
  } finally { oltpLoading.value = false }
}

const oltpDialogVisible = ref(false)
const isEditingOltp = ref(false)
const editingOltpId = ref<number | null>(null)
const savingOltp = ref(false)
const oltpFormRef = ref<any>(null)
const oltpForm = reactive<OltpSourceCreate>({
  record_src: '', conn_id: 0, database_name: '',
})
const oltpFormRules = {
  record_src: [{ required: true, message: t('connection.recordSrcRequired'), trigger: 'blur' }],
}

function openAddOltpSource() {
  isEditingOltp.value = false
  editingOltpId.value = null
  oltpForm.record_src = ''
  oltpForm.conn_id = 0
  oltpForm.database_name = ''
  oltpDialogVisible.value = true
}

function openEditOltpSource(row: OltpSource) {
  isEditingOltp.value = true
  editingOltpId.value = row.id
  oltpForm.record_src = row.record_src
  oltpForm.conn_id = row.conn_id
  oltpForm.database_name = row.database_name
  oltpDialogVisible.value = true
}

async function handleSaveOltpSource() {
  const valid = await oltpFormRef.value?.validate().catch(() => false)
  if (!valid) return
  savingOltp.value = true
  try {
    if (isEditingOltp.value && editingOltpId.value) {
      await api.updateOltpSource(editingOltpId.value, oltpForm)
    } else {
      await api.createOltpSource(oltpForm as OltpSourceCreate)
    }
    oltpDialogVisible.value = false
    ElMessage.success(t('common.success'))
    await fetchOltpSources()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e.message)
  } finally { savingOltp.value = false }
}

async function handleDeleteOltpSource(row: OltpSource) {
  try {
    await ElMessageBox.confirm(
      t('connection.deleteOltpSourceConfirm', { name: row.record_src }),
      t('connection.confirmDeleteTitle'),
      { confirmButtonText: t('common.delete'), cancelButtonText: t('common.cancel'), type: 'warning' },
    )
    await api.deleteOltpSource(row.id)
    ElMessage.success(t('common.success'))
    await fetchOltpSources()
  } catch { /* cancelled */ }
}
```

Add import: `import type { OltpSource, OltpSourceCreate } from '@/types'`

Call `fetchOltpSources()` in `onMounted()` alongside `fetchRoles()`.

---

### Task 14: MetaImportView — Select from OLTP Sources

**Files:**
- Modify: `frontend/src/views/MetaImportView.vue`

- [ ] **Step 1: Change Step 0 from connection selector to OLTP source selector**

Replace the connection loading logic with OLTP source loading. Remove `connections` direct usage and replace with `oltpSources`.

```typescript
// Replace:
// const connections = ref<Connection[]>([])
// const selectedConnId = ref<number | null>(null)
// const oltpDbName = ref('')
// const oltpRes = await api.getOltpSource()

// With:
const oltpSources = ref<any[]>([])
const selectedSourceId = ref<number | null>(null)
const selectedRecordSrc = ref('')
const selectedConnId = computed(() => {
  const src = oltpSources.value.find(s => s.id === selectedSourceId.value)
  return src?.conn_id || null
})
const selectedDbName = computed(() => {
  const src = oltpSources.value.find(s => s.id === selectedSourceId.value)
  return src?.database_name || ''
})

// In init():
const [connRes, srcRes] = await Promise.allSettled([
  api.listConnections(),
  api.getOltpSources(),
])
// ... populate connections for dropdown ...
if (srcRes.status === 'fulfilled') {
  const data = srcRes.value.data
  if (data.success) oltpSources.value = data.sources
}
```

Update the Step 0 template:

```html
<el-card v-show="activeStep === 0" shadow="never" class="step-card">
  <template #header><span class="step-title">{{ $t('metaImport.step1TitleLong') }}</span></template>
  <div v-if="loading" v-loading="loading" element-loading-text=" " style="height: 60px" />
  <div v-else-if="oltpSources.length === 0" class="empty-hint">
    <el-empty :description="$t('metaImport.emptyOltpSources')">
      <p>{{ $t('metaImport.emptyOltpHint') }}</p>
      <el-button type="primary" @click="goToConnections">{{ $t('metaImport.goToConnections') }}</el-button>
    </el-empty>
  </div>
  <div v-else>
    <el-form label-width="120px">
      <el-form-item :label="$t('metaImport.selectOltp')">
        <el-select v-model="selectedSourceId" :placeholder="$t('metaImport.selectOltp')" style="width: 420px" @change="resetTables">
          <el-option v-for="s in oltpSources" :key="s.id" :value="s.id">
            <span>{{ s.record_src }} — {{ s.connection_name }} / {{ s.database_name }}</span>
          </el-option>
        </el-select>
      </el-form-item>
    </el-form>
    <div class="step-actions">
      <el-button type="primary" :disabled="!selectedSourceId" @click="loadTables">{{ $t('common.next') }}</el-button>
    </div>
  </div>
</el-card>
```

- [ ] **Step 2: Pass `record_src` to import calls**

Update `loadAllColumns()` — when calling `api.importMeta()`, pass `selectedRecordSrc.value`:

```typescript
// At the top, track selected record_src:
watch(selectedSourceId, (id) => {
  const src = oltpSources.value.find(s => s.id === id)
  selectedRecordSrc.value = src?.record_src || ''
})

// In handleTransfer() and handleBatchImport():
// Replace: api.importMeta(selectedConnId.value!, cfg.tableSchema, cfg.tableName, undefined, keys, oltpDbName.value || undefined)
// With: api.importMeta(selectedConnId.value!, cfg.tableSchema, cfg.tableName, selectedRecordSrc.value, keys, selectedDbName.value || undefined)
```

---

### Task 15: MetaConfigView — Add record_src Column

**Files:**
- Modify: `frontend/src/views/MetaConfigView.vue`

- [ ] **Step 1: Add record_src column to objects table**

Between the `schema_name` column and `operation` column:

```html
<el-table-column :label="$t('metaConfig.recordSrcColumn')" width="120" align="center">
  <template #default="{ row }">
    <el-tag v-if="row.record_src" size="small">{{ row.record_src }}</el-tag>
    <span v-else class="empty-hint">-</span>
  </template>
</el-table-column>
```

Update the `ObjectItem` usage to include the new field. The backend `/api/objects` endpoint now needs to return `record_src` — this requires modifying the backend objects API to join with Attribute and get the distinct record_src values per table.

- [ ] **Step 2: Update backend objects endpoint**

In `backend/app/api/objects.py`, update the list endpoint to return `record_src`:

```python
@router.get("/objects")
def list_objects():
    session = get_meta_session()
    try:
        # Get all gen_list items with distinct table info
        from sqlalchemy import func
        sub = session.query(
            Attribute.table_name,
            Attribute.table_catalog,
            Attribute.record_src,
        ).distinct().subquery()

        rows = session.query(GenList, sub.c.record_src).outerjoin(
            sub, GenList.table_name == sub.c.table_name
        ).all()

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
    finally:
        session.close()
```

---

### Task 16: GeneratePsaView — Add record_src Selector

**Files:**
- Modify: `frontend/src/views/GeneratePsaView.vue`

- [ ] **Step 1: Add OLTP source selector above tabs**

In template, between card header and `el-tabs`:

```html
<div class="source-selector" style="margin-bottom: 16px; display: flex; align-items: center; gap: 12px;">
  <span style="font-weight: 500; font-size: 14px;">{{ $t('generate.selectOltpSource') }}:</span>
  <el-select v-model="selectedRecordSrc" :placeholder="$t('generate.selectOltpSourcePh')" style="width: 300px" @change="onSourceChange">
    <el-option v-for="src in oltpSources" :key="src.record_src" :label="`${src.record_src} — ${src.connection_name} / ${src.database_name}`" :value="src.record_src" />
  </el-select>
</div>
```

- [ ] **Step 2: Update script to load sources and pass to API**

```typescript
import { listOltpSources } from '@/api'

const oltpSources = ref<any[]>([])
const selectedRecordSrc = ref('')

async function loadOltpSources() {
  try {
    const res = await listOltpSources()
    oltpSources.value = res.data
    if (oltpSources.value.length > 0) {
      selectedRecordSrc.value = oltpSources.value[0].record_src
    }
  } catch { /* ignore */ }
}

function onSourceChange() {
  // Trigger regeneration of current tab
  onTabChange(activeTab.value)
}

// Update apiMap to pass record_src:
const apiMap: Record<string, (rs: string) => Promise<any>> = {
  stg: (rs) => generatePsaStg(rs),
  // ... etc
}
```

- [ ] **Step 3: Update the onTabChange to pass record_src**

```typescript
async function onTabChange(tabName: string | number) {
  if (!selectedRecordSrc.value) {
    ElMessage.warning(t('generate.selectOltpSourcePh'))
    return
  }
  const apiFn = apiMap[tabName as string]
  if (!apiFn) return
  generating.value = true
  sqlResult.value = ''
  try {
    const res = await apiFn(selectedRecordSrc.value)
    // ... rest unchanged
```

Call `loadOltpSources()` in `onMounted()`.

---

### Task 17: GenerateDvView — Add record_src Selector

**Files:**
- Modify: `frontend/src/views/GenerateDvView.vue`

- [ ] **Step 1: Add OLTP source selector above tabs**

Same pattern as GeneratePsaView — add a source selector div between card header and tabs.

- [ ] **Step 2: Update script with same pattern**

Load sources, update `apiMap` to pass `record_src`, update `onTabChange` to pass the selected source.

---

### Task 18: DataPreviewView — Show All OLTP Sources Flat

**Files:**
- Modify: `frontend/src/views/DataPreviewView.vue`

- [ ] **Step 1: Update tree building for OLTP node**

Find the tree-building logic. The OLTP node currently maps to a single `conn_id` + `database_name`. Change it to iterate over all OLTP sources and list tables from each.

The tree structure changes from:

```
oltp
  └─ table1, table2
```

To:

```
oltp
  └─ erp_CUSTOMER, erp_ORDERS, crm_PRODUCT
```

Internally, each leaf node needs `conn_id` and `database_name` for API calls. The `record_src` prefix is just display — the actual connection info is per-source.

The tree data for OLTP tables needs to:
1. For each source in `data.oltp` (now a list), build a temporary engine and list tables
2. For each table, prefix with `{record_src}_`
3. Each node stores `conn_id` and `database_name` for the source

- [ ] **Step 2: Update frontend buildTree function**

```typescript
async function buildTree() {
  // ...
  // OLTP: iterate over sources
  const oltpChildren: any[] = []
  for (const src of data.oltp) {
    try {
      const objRes = await api.getPreviewObjects(src.conn_id, src.database_name)
      // add tables with record_src prefix
      for (const t of objRes.data.tables) {
        // t is "schema.table" format
        oltpChildren.push({
          id: `oltp_${src.record_src}_${t}`,
          label: `${src.record_src}_${t.split('.')[1] || t}`,
          type: 'table',
          conn_id: src.conn_id,
          database_name: src.database_name,
          schema: t.split('.')[0],
          object: t.split('.')[1] || t,
          fullName: `${src.record_src}_${t.split('.')[1] || t}`,
        })
      }
    } catch { /* skip source if unreachable */ }
  }
  // ...
}
```

---

### Task 19: DeployView — No Change (Plan B)

**Files:**
- None (keep as-is)

Plan B means deploy all sources at once. The deploy endpoints (`/deploy/psa`, `/deploy/dv`) already work on all objects — no change needed.

---

### Task 20: main.py Lifecycle — Register OltpSource Engines

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: Update lifespan to also register OltpSource engines**

The current lifespan reads all `ConnectionConfig` rows to register engines. Add OltpSource loading so engines for OLTP sources are also registered:

```python
from app.models.oltp_source import OltpSource

# In lifespan startup, alongside existing connection registration:
sources = session.query(OltpSource).all()
for src in sources:
    conn = session.query(ConnectionConfig).filter(ConnectionConfig.id == src.conn_id).first()
    if conn:
        password = _decrypt_password(conn.password_encrypted)
        engine = build_engine(conn.host, conn.port, src.database_name, conn.username, password)
        register_engine(src.conn_id, engine)
```

Also remove the OLTP-specific role initialization from `_init_default_config` — only init STAGE and CORE now.