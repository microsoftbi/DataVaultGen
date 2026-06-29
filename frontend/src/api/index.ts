/* API 客户端封装 */
import axios from 'axios'
import type {
  Connection, ConnectionCreate, ConnectionTestRequest,
  SourceTable, SourceColumn, Attribute,
  ObjectItem, GenerateResult, DeployResult,
  DatabaseStatus, LogEntry, AppConfig,
  DatabaseRolesData, DatabaseRoleUpdate,
  OltpSource, OltpSourceCreate, OltpSourceUpdate,
} from '@/types'

const http = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// ── 连接管理 ──────────────────────────────────────────────────

export function listConnections() {
  return http.get<Connection[]>('/connections')
}

export function getConnection(id: number) {
  return http.get<Connection>(`/connections/${id}`)
}

export function createConnection(data: ConnectionCreate) {
  return http.post<Connection>('/connections', data)
}

export function updateConnection(id: number, data: Partial<ConnectionCreate>) {
  return http.put<Connection>(`/connections/${id}`, data)
}

export function deleteConnection(id: number) {
  return http.delete(`/connections/${id}`)
}

export function testConnection(data: ConnectionTestRequest) {
  return http.post<{ success: boolean; message: string }>('/connections/test', data)
}

export function testSavedConnection(id: number) {
  return http.post<{ success: boolean; message: string }>(`/connections/${id}/test`)
}

// ── 元数据导入 ────────────────────────────────────────────────

export function getOltpSources() {
  return http.get<{ success: boolean; sources: any[] }>('/meta/oltp-source')
}

export function listSourceTables(connId: number, databaseName?: string) {
  return http.get<{ success: boolean; tables: SourceTable[] }>('/meta/tables', {
    params: { conn_id: connId, database_name: databaseName || undefined },
  })
}

export function listSourceColumns(connId: number, tableSchema: string, tableName: string, databaseName?: string) {
  return http.get<{ success: boolean; columns: SourceColumn[] }>('/meta/columns', {
    params: { conn_id: connId, table_schema: tableSchema, table_name: tableName, database_name: databaseName || undefined },
  })
}

export function importMeta(connId: number, tableSchema: string, tableName: string, recordSource?: string, columns?: string[], databaseName?: string) {
  return http.post('/meta/import', {
    conn_id: connId,
    table_schema: tableSchema,
    table_name: tableName,
    record_source: recordSource,
    columns,
    database_name: databaseName,
  })
}

export function importMetaBulk(connId: number, tables: { table_schema: string; table_name: string }[], databaseName?: string) {
  return http.post('/meta/import-bulk', {
    conn_id: connId,
    tables,
    database_name: databaseName,
  })
}

export function listAttributes(tableName?: string) {
  return http.get('/meta/attributes', {
    params: tableName ? { table_name: tableName } : {},
  })
}

export function batchDeleteAttributes(updates: { id: number }[]) {
  return http.delete('/meta/attributes/batch', { data: { updates } })
}

export function updateAttribute(id: number, data: { is_bk?: boolean; is_pk?: boolean; is_di?: boolean }) {
  return http.put<Attribute>(`/meta/attributes/${id}`, data)
}

export function batchUpdateAttributes(updates: any[]) {
  return http.put('/meta/attributes/batch', { updates })
}

// ── 对象列表 ──────────────────────────────────────────────────

export function listObjects() {
  return http.get<ObjectItem[]>('/objects')
}

export function initObjectList() {
  return http.post('/objects/init')
}

export function updateObject(id: number, data: { is_gen?: boolean; is_full_load?: boolean }) {
  return http.put<ObjectItem>(`/objects/${id}`, data)
}

export function batchUpdateObjects(updates: any[]) {
  return http.put('/objects/batch/update', { updates })
}

// ── 代码生成 ──────────────────────────────────────────────────

export function generatePsaAll(recordSrc?: string) {
  return http.post<{ success: boolean; sql: string }>('/generate/psa/all', null, { params: { record_src: recordSrc } })
}

export function generatePsaStg(recordSrc?: string) {
  return http.post<{ success: boolean; sql: string }>('/generate/psa/stg', null, { params: { record_src: recordSrc } })
}

export function generatePsaCdc(recordSrc?: string) {
  return http.post<{ success: boolean; sql: string }>('/generate/psa/cdc', null, { params: { record_src: recordSrc } })
}

export function generatePsaLog(recordSrc?: string) {
  return http.post<{ success: boolean; sql: string }>('/generate/psa/log', null, { params: { record_src: recordSrc } })
}

export function generatePsaViews(recordSrc?: string) {
  return http.post<{ success: boolean; sql: string }>('/generate/psa/views', null, { params: { record_src: recordSrc } })
}

export function generatePsaUsps(recordSrc?: string) {
  return http.post<{ success: boolean; sql: string }>('/generate/psa/usps', null, { params: { record_src: recordSrc } })
}

export function generatePsaFlow(recordSrc?: string) {
  return http.post<{ success: boolean; sql: string }>('/generate/psa/flow', null, { params: { record_src: recordSrc } })
}

// ── 部署 ──────────────────────────────────────────────────────

export function deployRuntime(connId?: number) {
  return http.post('/deploy/runtime', null, { params: { conn_id: connId } })
}

export function deployDv(connId?: number) {
  return http.post('/deploy/dv', null, { params: { conn_id: connId } })
}

export function deployPsa(connId?: number) {
  return http.post<DeployResult>('/deploy/psa', null, { params: { conn_id: connId } })
}

export function deploySql(connId: number, sql: string, objectType = 'all') {
  return http.post<DeployResult>('/deploy/sql', {
    conn_id: connId,
    sql,
    object_type: objectType,
  })
}

export function executeSql(sql: string, role = 'STAGE') {
  return http.post<DeployResult>('/deploy/execute', { sql, role })
}

export function exportMetaConfig() {
  return http.get('/meta/export')
}

export function importMetaConfig(data: any) {
  return http.post('/meta/import', data)
}

// ── DV 配置 ──────────────────────────────────────────────────────

export function listDvHubs() { return http.get('/dv/hubs') }
export function createDvHub(name: string) { return http.post('/dv/hubs', { table_name: name }) }
export function deleteDvHub(id: number) { return http.delete(`/dv/hubs/${id}`) }

export function listDvSats() { return http.get('/dv/sats') }
export function createDvSat(name: string) { return http.post('/dv/sats', { table_name: name }) }
export function deleteDvSat(id: number) { return http.delete(`/dv/sats/${id}`) }

export function listDvLinks() { return http.get('/dv/links') }
export function createDvLink(name: string) { return http.post('/dv/links', { table_name: name }) }
export function deleteDvLink(id: number) { return http.delete(`/dv/links/${id}`) }

export function autoConfigureDv(tableName: string) {
  return http.post('/dv/auto-configure', { table_name: tableName })
}

// ── DV 生成 ──────────────────────────────────────────────────────

export function generateDvHub(recordSrc?: string) { return http.post('/generate/dv/hub', null, { params: { record_src: recordSrc } }) }
export function generateDvSat(recordSrc?: string) { return http.post('/generate/dv/sat', null, { params: { record_src: recordSrc } }) }
export function generateDvLink(recordSrc?: string) { return http.post('/generate/dv/link', null, { params: { record_src: recordSrc } }) }
export function generateDvUspHub(recordSrc?: string) { return http.post('/generate/dv/usp-hub', null, { params: { record_src: recordSrc } }) }
export function generateDvUspSat(recordSrc?: string) { return http.post('/generate/dv/usp-sat', null, { params: { record_src: recordSrc } }) }
export function generateDvUspLink(recordSrc?: string) { return http.post('/generate/dv/usp-link', null, { params: { record_src: recordSrc } }) }
export function generateDvAll(recordSrc?: string) { return http.post('/generate/dv/all', null, { params: { record_src: recordSrc } }) }
export function generateDvFlow(recordSrc?: string) { return http.post('/generate/dv/flow', null, { params: { record_src: recordSrc } }) }

export function getDeployDiff(connId: number) {
  return http.get('/deploy/diff', { params: { conn_id: connId } })
}

export function getDeployStatus(connId: number) {
  return http.get<DatabaseStatus>('/deploy/status', { params: { conn_id: connId } })
}

// ── 配置 ──────────────────────────────────────────────────────

export function getConfig() {
  return http.get<AppConfig>('/config')
}

export function updateConfig(data: { psa_db_name?: string; hash_dummy?: string }) {
  return http.put<AppConfig>('/config', data)
}

// ── 数据预览 ──────────────────────────────────────────────────

export function getPreviewDatabases() {
  return http.get<{ success: boolean; data: any }>('/preview/databases')
}

export function getPreviewObjects(connId: number, databaseName: string) {
  return http.get('/preview/objects', {
    params: { conn_id: connId, database_name: databaseName },
  })
}

export function getPreviewColumns(connId: number, databaseName: string, schema: string, object: string) {
  return http.get('/preview/columns', {
    params: { conn_id: connId, database_name: databaseName, schema, object },
  })
}

export function getPreviewData(connId: number, databaseName: string, schema: string, object: string, limit = 500) {
  return http.get('/preview/data', {
    params: { conn_id: connId, database_name: databaseName, schema, object, limit },
  })
}

// ── META 库预览 ──────────────────────────────────────────────

export function getMetaPreviewTables() {
  return http.get<{ success: boolean; tables: string[] }>('/preview/meta/tables')
}

export function getMetaPreviewColumns(table: string) {
  return http.get<{ success: boolean; columns: any[] }>('/preview/meta/columns', {
    params: { table },
  })
}

export function getMetaPreviewData(table: string, limit = 500) {
  return http.get<{ success: boolean; columns: string[]; rows: any[][]; total: number }>('/preview/meta/data', {
    params: { table, limit },
  })
}

// ── 日志 ──────────────────────────────────────────────────────

export function listLogs(limit = 100, offset = 0) {
  return http.get<LogEntry[]>('/logs', { params: { limit, offset } })
}

export function clearLogs() {
  return http.delete('/logs')
}

// ── 数据库角色绑定 ────────────────────────────────────────────

export function getDbRoles() {
  return http.get<{ success: boolean; data: any }>('/db-roles')
}

export function updateDbRoles(data: { stage: DatabaseRoleUpdate; core: DatabaseRoleUpdate }) {
  return http.put<{ success: boolean; data: any }>('/db-roles', data)
}

// ── OLTP 源管理 ──────────────────────────────────────────────

export function listOltpSources() {
  return http.get<OltpSource[]>('/oltp-sources')
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

// ── 健康检查 ──────────────────────────────────────────────────

export function healthCheck() {
  return http.get<{ status: string; app: string; version: string }>('/health')
}

export default http