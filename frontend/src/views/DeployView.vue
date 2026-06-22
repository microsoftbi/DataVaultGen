<template>
  <div class="deploy-container">
    <!-- 顶部区域：目标连接选择 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="section-header">
          <el-icon :size="20"><Connection /></el-icon>
          <span>目标连接</span>
        </div>
      </template>

      <div class="conn-select-row">
        <el-select
          v-model="selectedConnId"
          placeholder="请选择目标连接"
          size="large"
          style="width: 360px"
          @change="onConnChange"
        >
          <el-option
            v-for="c in targetConnections"
            :key="c.id"
            :label="`${c.name} (${c.db_type}@${c.host}:${c.port}/${c.database_name})`"
            :value="c.id"
          />
        </el-select>

        <el-button
          type="default"
          :disabled="!selectedConnId"
          :loading="statusLoading"
          @click="fetchStatus"
        >
          查看状态
        </el-button>
      </div>

      <!-- 差异对比 -->
      <div v-if="deployDiff" style="margin-top: 12px;">
        <el-divider />
        <div class="section-header">
          <span style="font-weight: 600; font-size: 14px;">部署差异对比</span>
          <el-button size="small" :loading="diffLoading" @click="fetchDiff">刷新对比</el-button>
        </div>
        <div class="diff-summary">
          <el-tag>{{ diffSummary.total }} 个对象</el-tag>
          <el-tag type="success">{{ diffSummary.existing }} 已部署</el-tag>
          <el-tag type="danger">{{ diffSummary.missing }} 待部署</el-tag>
        </div>
        <el-table :data="deployDiff" border stripe size="small" style="width: 100%; margin-top: 8px;" max-height="300">
          <el-table-column prop="name" label="对象名" min-width="240" />
          <el-table-column prop="type" label="类型" width="120">
            <template #default="{ row }">
              <el-tag :type="row.type === 'TABLE' ? '' : row.type === 'VIEW' ? 'success' : 'warning'" size="small">
                {{ row.type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'EXISTS' ? 'success' : 'danger'" size="small">
                {{ row.status === 'EXISTS' ? '已部署' : '待部署' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 状态展示 -->
      <template v-if="deployStatus">
        <el-divider />

        <div class="status-cards">
          <el-card shadow="hover" class="status-card card-tables">
            <div class="status-card-inner">
              <span class="status-card-value">{{ deployStatus.tables.length }}</span>
              <span class="status-card-label">表 (Tables)</span>
              <el-button v-if="deployStatus.tables.length" text type="primary" size="small" @click="showTableList = !showTableList">
                {{ showTableList ? '收起' : '查看列表' }}
              </el-button>
            </div>
          </el-card>
          <el-card shadow="hover" class="status-card card-views">
            <div class="status-card-inner">
              <span class="status-card-value">{{ deployStatus.views.length }}</span>
              <span class="status-card-label">视图 (Views)</span>
              <el-button v-if="deployStatus.views.length" text type="primary" size="small" @click="showViewList = !showViewList">
                {{ showViewList ? '收起' : '查看列表' }}
              </el-button>
            </div>
          </el-card>
          <el-card shadow="hover" class="status-card card-procs">
            <div class="status-card-inner">
              <span class="status-card-value">{{ deployStatus.procedures.length }}</span>
              <span class="status-card-label">存储过程 (Procedures)</span>
              <el-button v-if="deployStatus.procedures.length" text type="primary" size="small" @click="showProcList = !showProcList">
                {{ showProcList ? '收起' : '查看列表' }}
              </el-button>
            </div>
          </el-card>
        </div>

        <el-collapse v-model="activeCollapse" class="status-collapse">
          <el-collapse-item v-if="showTableList && deployStatus.tables.length" title="表列表" name="tables">
            <div class="item-list">
              <el-tag
                v-for="t in deployStatus.tables"
                :key="t"
                class="item-tag"
              >{{ t }}</el-tag>
              <span v-if="!deployStatus.tables.length" class="empty-hint">暂无</span>
            </div>
          </el-collapse-item>
          <el-collapse-item v-if="showViewList && deployStatus.views.length" title="视图列表" name="views">
            <div class="item-list">
              <el-tag
                v-for="v in deployStatus.views"
                :key="v"
                class="item-tag"
                type="success"
              >{{ v }}</el-tag>
              <span v-if="!deployStatus.views.length" class="empty-hint">暂无</span>
            </div>
          </el-collapse-item>
          <el-collapse-item v-if="showProcList && deployStatus.procedures.length" title="存储过程列表" name="procs">
            <div class="item-list">
              <el-tag
                v-for="p in deployStatus.procedures"
                :key="p"
                class="item-tag"
                type="warning"
              >{{ p }}</el-tag>
              <span v-if="!deployStatus.procedures.length" class="empty-hint">暂无</span>
            </div>
          </el-collapse-item>
        </el-collapse>
      </template>
    </el-card>

    <!-- 中部区域：部署操作 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="section-header">
          <el-icon :size="20"><Upload /></el-icon>
          <span>部署操作</span>
        </div>
      </template>

      <div class="deploy-actions">
        <div class="action-item">
          <div class="action-info">
            <strong>部署运行时组件</strong>
            <p>在目标库创建 EXECUTION_LOG 表、USP_WRITELOG 存储过程及配置默认值。<br>生成的 PSA/DV 存储过程依赖此组件写入日志。</p>
          </div>
          <el-button
            size="large"
            :disabled="!selectedConnId"
            :loading="deployRuntimeLoading"
            @click="handleDeployRuntime"
          >
            部署运行时
          </el-button>
        </div>

        <el-divider />

        <div class="action-item">
          <div class="action-info">
            <strong>部署 PSA</strong>
            <p>将生成的 PSA 分层 SQL 脚本部署到目标数据库执行。</p>
          </div>
          <el-button
            type="primary"
            size="large"
            :disabled="!selectedConnId"
            :loading="deployPsaLoading"
            @click="handleDeployPsa"
          >
            部署 PSA
          </el-button>
        </div>

        <div class="action-item">
          <div class="action-info">
            <strong>部署 DV</strong>
            <p>将生成的 Data Vault 2.0 分层 SQL 脚本部署到目标数据库执行。</p>
          </div>
          <el-button
            type="success"
            size="large"
            :disabled="!selectedConnId"
            :loading="deployDvLoading"
            @click="handleDeployDv"
          >
            部署 DV
          </el-button>
        </div>

        <el-divider />

        <div class="action-item">
          <div class="action-info">
            <strong>部署自定义 SQL</strong>
            <p>手动输入 SQL 语句，直接部署到目标数据库执行。</p>
          </div>
          <el-button
            type="default"
            size="large"
            :disabled="!selectedConnId"
            @click="sqlDialogVisible = true"
          >
            部署自定义 SQL
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 自定义 SQL 对话框 -->
    <el-dialog
      v-model="sqlDialogVisible"
      title="部署自定义 SQL"
      width="680px"
      :close-on-click-modal="false"
    >
      <el-input
        v-model="customSql"
        type="textarea"
        :rows="12"
        placeholder="请输入要执行的 SQL 语句..."
        class="sql-editor"
      />
      <p class="sql-tip">注意：多条 SQL 语句请以分号 (;) 分隔。</p>
      <template #footer>
        <el-button @click="sqlDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="deploySqlLoading"
          :disabled="!customSql.trim()"
          @click="handleDeploySql"
        >
          执行部署
        </el-button>
      </template>
    </el-dialog>

    <!-- 底部区域：部署日志 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="section-header">
          <el-icon :size="20"><Document /></el-icon>
          <span>部署日志</span>
          <el-tag size="small" type="info" class="log-count">最近 {{ logs.length }} 条</el-tag>
        </div>
      </template>

      <el-table
        :data="logs"
        stripe
        style="width: 100%"
        max-height="420"
        size="small"
        v-loading="logLoading"
      >
        <el-table-column
          prop="created_at"
          label="时间"
          width="170"
          :formatter="(row: LogEntry) => row.created_at ? new Date(row.created_at).toLocaleString() : '-'"
        />
        <el-table-column
          prop="log_source"
          label="来源"
          width="120"
        >
          <template #default="{ row }">
            <span>{{ row.log_source || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="log_type"
          label="类型"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            <el-tag
              :type="logTypeTag(row.log_type)"
              size="small"
              effect="dark"
            >
              {{ row.log_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="message"
          label="消息"
          min-width="300"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <span class="log-message">{{ row.message || '-' }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Connection, Document, Upload } from '@element-plus/icons-vue'
import {
  listConnections,
  getDeployStatus,
  deployPsa,
  deployDv,
  deployRuntime,
  deploySql,
  listLogs,
  getDeployDiff,
} from '@/api'
import type { Connection as ConnectionType, DatabaseStatus, LogEntry } from '@/types'

// ── 目标连接 ──

const allConnections = ref<ConnectionType[]>([])
const selectedConnId = ref<number | null>(null)

const targetConnections = computed(() =>
  allConnections.value.filter((c) => c.is_target),
)
const deployDiff = ref<any[] | null>(null)
const diffLoading = ref(false)
const diffSummary = computed(() => {
  if (!deployDiff.value) return { total: 0, existing: 0, missing: 0 }
  const existing = deployDiff.value.filter(d => d.status === 'EXISTS').length
  const missing = deployDiff.value.filter(d => d.status === 'MISSING').length
  return { total: deployDiff.value.length, existing, missing }
})

async function loadConnections() {
  try {
    const res = await listConnections()
    allConnections.value = res.data
    // 自动选中第一个目标连接
    if (!selectedConnId.value && targetConnections.value.length) {
      selectedConnId.value = targetConnections.value[0].id
    }
  } catch {
    ElMessage.error('加载连接列表失败')
  }
}

function onConnChange() {
  deployStatus.value = null
  showTableList.value = false
  showViewList.value = false
  showProcList.value = false
}

// ── 差异对比 ──
async function fetchDiff() {
  if (!selectedConnId.value) return
  diffLoading.value = true
  try {
    const res = await getDeployDiff(selectedConnId.value)
    const data = res.data as any
    if (data.success) {
      deployDiff.value = data.diffs
    } else {
      ElMessage.warning(data.message || '获取差异失败')
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e.message)
  } finally { diffLoading.value = false }
}

// ── 状态查看 ──

const statusLoading = ref(false)
const deployStatus = ref<DatabaseStatus | null>(null)
const showTableList = ref(false)
const showViewList = ref(false)
const showProcList = ref(false)
const activeCollapse = ref<string[]>([])

async function fetchStatus() {
  if (!selectedConnId.value) return
  statusLoading.value = true
  deployStatus.value = null
  try {
    const res = await getDeployStatus(selectedConnId.value)
    deployStatus.value = res.data
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '获取部署状态失败')
  } finally {
    statusLoading.value = false
  }
}

// ── 部署 PSA ──

const deployPsaLoading = ref(false)

async function handleDeployPsa() {
  if (!selectedConnId.value) return
  deployPsaLoading.value = true
  try {
    const res = await deployPsa(selectedConnId.value)
    const result = res.data
    if (result.success) {
      ElMessage.success(`部署成功，共执行 ${result.executed_count} 条语句`)
    } else {
      const extra = result.error_at > 0 ? `，在第 ${result.error_at} 条出错` : ''
      ElMessage.warning(result.message || `部署完成${extra}`)
    }
    await refreshLogs()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '部署 PSA 失败')
  } finally {
    deployPsaLoading.value = false
  }
}

// ── 部署 DV ──

const deployDvLoading = ref(false)

async function handleDeployDv() {
  if (!selectedConnId.value) return
  deployDvLoading.value = true
  try {
    const res = await deployDv(selectedConnId.value)
    const result = res.data
    if (result.success) {
      ElMessage.success(`DV 部署成功，共执行 ${result.executed_count} 条语句`)
    } else {
      const extra = result.error_at > 0 ? `，在第 ${result.error_at} 条出错` : ''
      ElMessage.warning(result.message || `DV 部署完成${extra}`)
    }
    await refreshLogs()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '部署 DV 失败')
  } finally {
    deployDvLoading.value = false
  }
}

// ── 部署运行时组件 ──

const deployRuntimeLoading = ref(false)

async function handleDeployRuntime() {
  if (!selectedConnId.value) return
  deployRuntimeLoading.value = true
  try {
    const res = await deployRuntime(selectedConnId.value)
    const result = res.data
    if (result.success) {
      ElMessage.success(`运行时组件部署成功，${result.executed_count} 条语句已执行`)
    } else {
      ElMessage.warning(result.message || '运行时部署失败')
    }
    await refreshLogs()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '部署运行时失败')
  } finally {
    deployRuntimeLoading.value = false
  }
}

// ── 自定义 SQL ──

const sqlDialogVisible = ref(false)
const customSql = ref('')
const deploySqlLoading = ref(false)

async function handleDeploySql() {
  if (!selectedConnId.value || !customSql.value.trim()) return
  deploySqlLoading.value = true
  try {
    const res = await deploySql(selectedConnId.value, customSql.value)
    const result = res.data
    if (result.success) {
      ElMessage.success(`自定义 SQL 部署成功，共执行 ${result.executed_count} 条语句`)
    } else {
      const extra = result.error_at > 0 ? `，在第 ${result.error_at} 条出错` : ''
      ElMessage.warning(result.message || `自定义 SQL 部署完成${extra}`)
    }
    sqlDialogVisible.value = false
    customSql.value = ''
    await refreshLogs()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '部署自定义 SQL 失败')
  } finally {
    deploySqlLoading.value = false
  }
}

// ── 日志 ──

const logs = ref<LogEntry[]>([])
const logLoading = ref(false)

async function refreshLogs() {
  logLoading.value = true
  try {
    const res = await listLogs(100)
    logs.value = res.data
  } catch {
    // 静默处理
  } finally {
    logLoading.value = false
  }
}

function logTypeTag(type: string): string {
  switch (type) {
    case 'N':
      return 'success'
    case 'E':
      return 'danger'
    case 'W':
      return 'warning'
    default:
      return 'info'
  }
}

// ── 初始化 ──

onMounted(async () => {
  await loadConnections()
  await refreshLogs()
})
</script>

<style scoped>
.deploy-container {
  padding: 0;
}

/* ── 各区卡片 ── */

.section-card {
  margin-bottom: 20px;
  border-radius: 12px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.log-count {
  margin-left: auto;
  font-weight: 400;
}

/* ── 连接选择 ── */

.conn-select-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* ── 状态卡片 ── */

.status-cards {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.status-card {
  flex: 1;
  min-width: 180px;
  border-radius: 10px;
}

.status-card-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 0;
}

.status-card-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1.2;
}

.status-card-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.card-tables {
  border-top: 3px solid #409eff;
}

.card-views {
  border-top: 3px solid #67c23a;
}

.card-procs {
  border-top: 3px solid #e6a23c;
}

/* ── 折叠列表 ── */

.status-collapse {
  margin-top: 12px;
}

.item-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.item-tag {
  font-size: 12px;
}

.empty-hint {
  color: var(--el-text-color-placeholder);
  font-size: 13px;
}

/* ── 部署操作 ── */

.deploy-actions {
  padding: 4px 0;
}

.action-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.action-info strong {
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.action-info p {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}

/* ── SQL 编辑 ── */

.sql-editor {
  font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.sql-tip {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

/* ── 日志 ── */

.log-message {
  white-space: pre-wrap;
  word-break: break-all;
}
</style>