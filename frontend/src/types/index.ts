/* Data Vault Generator 前端类型定义 */

// 连接管理
export interface Connection {
  id: number
  name: string
  db_type: string
  host: string
  port: number
  database_name: string
  username: string
  is_meta: boolean
  is_source: boolean
  is_target: boolean
  created_at: string
}

export interface ConnectionCreate {
  name: string
  host: string
  port: number
  database_name: string
  username: string
  password: string
  is_meta: boolean
  is_source: boolean
  is_target: boolean
}

export interface ConnectionTestRequest {
  host: string
  port: number
  database_name?: string
  username: string
  password: string
}

// 元数据
export interface SourceTable {
  table_schema: string
  table_name: string
}

export interface SourceColumn {
  column_name: string
  data_type: string
  character_maximum_length: number | null
  numeric_precision: number | null
  numeric_scale: number | null
}

export interface Attribute {
  id: number
  table_catalog: string | null
  table_name: string
  column_name: string
  data_type: string | null
  character_maximum_length: number | null
  numeric_precision: number | null
  numeric_scale: number | null
  is_bk: boolean
  is_pk: boolean
  is_di: boolean
}

// 对象列表
export interface ObjectItem {
  id: number
  table_catalog: string | null
  table_name: string
  schema_name: string
  is_gen: boolean
  is_full_load: boolean
}

// 生成
export interface GenerateResult {
  stg: string
  cdc: string
  log: string
  v_mta: string
  v_current: string
  usp_stg: string
  usp_cdc: string
  usp_log: string
  execute_flow: string
  combined: string
}

// 部署
export interface DeployResult {
  success: boolean
  message: string
  executed_count: number
  error_at: number
}

export interface DatabaseStatus {
  success: boolean
  message?: string
  tables: string[]
  views: string[]
  procedures: string[]
}

// 日志
export interface LogEntry {
  id: number
  log_source: string | null
  log_type: string
  message: string | null
  created_at: string
}

// 配置
export interface AppConfig {
  psa_db_name: string
  hash_dummy: string
  core_db_name: string
}

// 数据库角色绑定
export interface DatabaseRoleItem {
  id: number
  role_name: string
  conn_id: number
  database_name: string
  created_at: string | null
}

export interface DatabaseRoleUpdate {
  conn_id: number
  database_name: string
}

export interface DatabaseRolesData {
  stage: DatabaseRoleItem | null
  core: DatabaseRoleItem | null
}

// OLTP 源管理
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

// API 通用响应
export interface ApiResponse<T> {
  success?: boolean
  message?: string
  data?: T
}