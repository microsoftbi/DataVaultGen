<template>
  <div class="deploy-container">
    <!-- 顶部区域：目标连接选择 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="section-header">
          <el-icon :size="20"><Connection /></el-icon>
          <span>{{ $t('deploy.targetConn') }}</span>
        </div>
      </template>

      <div class="conn-select-row">
        <el-select
          v-model="selectedConnId"
          :placeholder="$t('deploy.selectTargetPh')"
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
          {{ $t('deploy.checkStatus') }}
        </el-button>
      </div>

      <!-- 差异对比 -->
      <div v-if="deployDiff" style="margin-top: 12px;">
        <el-divider />
        <div class="section-header">
          <span style="font-weight: 600; font-size: 14px;">{{ $t('deploy.deployDiffSection') }}</span>
          <el-button size="small" :loading="diffLoading" @click="fetchDiff">{{ $t('deploy.refreshDiff') }}</el-button>
        </div>
        <div class="diff-summary">
          <el-tag>{{ $t('deploy.objectsCount', { n: diffSummary.total }) }}</el-tag>
          <el-tag type="success">{{ diffSummary.existing }} {{ $t('deploy.deployed') }}</el-tag>
          <el-tag type="danger">{{ diffSummary.missing }} {{ $t('deploy.pending') }}</el-tag>
        </div>
        <el-table :data="deployDiff" border stripe size="small" style="width: 100%; margin-top: 8px;" max-height="300">
          <el-table-column prop="name" :label="$t('deploy.objectName')" min-width="240" />
          <el-table-column prop="type" :label="$t('deploy.objectType')" width="120">
            <template #default="{ row }">
              <el-tag :type="row.type === 'TABLE' ? '' : row.type === 'VIEW' ? 'success' : 'warning'" size="small">
                {{ row.type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" :label="$t('deploy.objectStatus')" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'EXISTS' ? 'success' : 'danger'" size="small">
                {{ row.status === 'EXISTS' ? $t('deploy.deployed') : $t('deploy.pending') }}
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
              <span class="status-card-label">{{ $t('deploy.tablesLabel') }}</span>
              <el-button v-if="deployStatus.tables.length" text type="primary" size="small" @click="showTableList = !showTableList">
                {{ showTableList ? $t('deploy.collapse') : $t('deploy.viewList') }}
              </el-button>
            </div>
          </el-card>
          <el-card shadow="hover" class="status-card card-views">
            <div class="status-card-inner">
              <span class="status-card-value">{{ deployStatus.views.length }}</span>
              <span class="status-card-label">{{ $t('deploy.viewsLabel') }}</span>
              <el-button v-if="deployStatus.views.length" text type="primary" size="small" @click="showViewList = !showViewList">
                {{ showViewList ? $t('deploy.collapse') : $t('deploy.viewList') }}
              </el-button>
            </div>
          </el-card>
          <el-card shadow="hover" class="status-card card-procs">
            <div class="status-card-inner">
              <span class="status-card-value">{{ deployStatus.procedures.length }}</span>
              <span class="status-card-label">{{ $t('deploy.proceduresLabel') }}</span>
              <el-button v-if="deployStatus.procedures.length" text type="primary" size="small" @click="showProcList = !showProcList">
                {{ showProcList ? $t('deploy.collapse') : $t('deploy.viewList') }}
              </el-button>
            </div>
          </el-card>
        </div>

        <el-collapse v-model="activeCollapse" class="status-collapse">
          <el-collapse-item v-if="showTableList && deployStatus.tables.length" :title="$t('deploy.tablesList')" name="tables">
            <div class="item-list">
              <el-tag
                v-for="t in deployStatus.tables"
                :key="t"
                class="item-tag"
              >{{ t }}</el-tag>
              <span v-if="!deployStatus.tables.length" class="empty-hint">{{ $t('deploy.empty') }}</span>
            </div>
          </el-collapse-item>
          <el-collapse-item v-if="showViewList && deployStatus.views.length" :title="$t('deploy.viewsList')" name="views">
            <div class="item-list">
              <el-tag
                v-for="v in deployStatus.views"
                :key="v"
                class="item-tag"
                type="success"
              >{{ v }}</el-tag>
              <span v-if="!deployStatus.views.length" class="empty-hint">{{ $t('deploy.empty') }}</span>
            </div>
          </el-collapse-item>
          <el-collapse-item v-if="showProcList && deployStatus.procedures.length" :title="$t('deploy.proceduresList')" name="procs">
            <div class="item-list">
              <el-tag
                v-for="p in deployStatus.procedures"
                :key="p"
                class="item-tag"
                type="warning"
              >{{ p }}</el-tag>
              <span v-if="!deployStatus.procedures.length" class="empty-hint">{{ $t('deploy.empty') }}</span>
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
          <span>{{ $t('deploy.deployActionsSection') }}</span>
        </div>
      </template>

      <div class="deploy-actions">
        <div class="action-item">
          <div class="action-info">
            <strong>{{ $t('deploy.runtimeActionTitle') }}</strong>
            <p>{{ $t('deploy.runtimeActionDesc1') }}<br>{{ $t('deploy.runtimeActionDesc2') }}</p>
          </div>
          <el-button
            size="large"
            :disabled="!selectedConnId"
            :loading="deployRuntimeLoading"
            @click="handleDeployRuntime"
          >
            {{ $t('deploy.deployRuntime') }}
          </el-button>
        </div>

        <el-divider />

        <div class="action-item">
          <div class="action-info">
            <strong>{{ $t('deploy.psaActionTitle') }}</strong>
            <p>{{ $t('deploy.psaActionDesc') }}</p>
          </div>
          <el-button
            type="primary"
            size="large"
            :disabled="!selectedConnId"
            :loading="deployPsaLoading"
            @click="handleDeployPsa"
          >
            {{ $t('deploy.deployPsa') }}
          </el-button>
        </div>

        <div class="action-item">
          <div class="action-info">
            <strong>{{ $t('deploy.dvActionTitle') }}</strong>
            <p>{{ $t('deploy.dvActionDesc') }}</p>
          </div>
          <el-button
            type="success"
            size="large"
            :disabled="!selectedConnId"
            :loading="deployDvLoading"
            @click="handleDeployDv"
          >
            {{ $t('deploy.deployDv') }}
          </el-button>
        </div>

        <el-divider />

        <div class="action-item">
          <div class="action-info">
            <strong>{{ $t('deploy.customSqlActionTitle') }}</strong>
            <p>{{ $t('deploy.customSqlActionDesc') }}</p>
          </div>
          <el-button
            type="default"
            size="large"
            :disabled="!selectedConnId"
            @click="sqlDialogVisible = true"
          >
            {{ $t('deploy.customSqlActionTitle') }}
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 自定义 SQL 对话框 -->
    <el-dialog
      v-model="sqlDialogVisible"
      :title="$t('deploy.customSqlDialogTitle')"
      width="680px"
      :close-on-click-modal="false"
    >
      <el-input
        v-model="customSql"
        type="textarea"
        :rows="12"
        :placeholder="$t('deploy.customSqlInputPh')"
        class="sql-editor"
      />
      <p class="sql-tip">{{ $t('deploy.customSqlTip') }}</p>
      <template #footer>
        <el-button @click="sqlDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button
          type="primary"
          :loading="deploySqlLoading"
          :disabled="!customSql.trim()"
          @click="handleDeploySql"
        >
          {{ $t('deploy.executeDeploy') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 底部区域：部署日志 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="section-header">
          <el-icon :size="20"><Document /></el-icon>
          <span>{{ $t('deploy.deployLog') }}</span>
          <el-tag size="small" type="info" class="log-count">{{ $t('deploy.recentNLogs', { n: logs.length }) }}</el-tag>
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
          :label="$t('deploy.timeColumn')"
          width="170"
          :formatter="(row: LogEntry) => row.created_at ? new Date(row.created_at).toLocaleString() : '-'"
        />
        <el-table-column
          prop="log_source"
          :label="$t('deploy.sourceColumn')"
          width="120"
        >
          <template #default="{ row }">
            <span>{{ row.log_source || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="log_type"
          :label="$t('deploy.typeColumn')"
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
          :label="$t('deploy.messageColumn')"
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
import { useI18n } from 'vue-i18n'
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

const { t } = useI18n()

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
    ElMessage.error(t('deploy.loadConnFailed'))
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
      ElMessage.warning(data.message || t('deploy.getDiffFailed'))
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
    ElMessage.error(e?.response?.data?.message || t('deploy.getStatusFailed'))
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
      ElMessage.success(t('deploy.deploySuccessMsg', { n: result.executed_count }))
    } else {
      const extra = result.error_at > 0 ? t('deploy.errorAt', { n: result.error_at }) : ''
      ElMessage.warning(result.message || t('deploy.deployCompleteMsg', { extra }))
    }
    await refreshLogs()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || t('deploy.deployPsaFailed'))
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
      ElMessage.success(t('deploy.deployDvSuccessMsg', { n: result.executed_count }))
    } else {
      const extra = result.error_at > 0 ? t('deploy.errorAt', { n: result.error_at }) : ''
      ElMessage.warning(result.message || t('deploy.deployDvCompleteMsg', { extra }))
    }
    await refreshLogs()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || t('deploy.deployDvFailed'))
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
      ElMessage.success(t('deploy.runtimeSuccessMsg', { n: result.executed_count }))
    } else {
      ElMessage.warning(result.message || t('deploy.runtimeFailedMsg'))
    }
    await refreshLogs()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || t('deploy.runtimeDeployFailed'))
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
      ElMessage.success(t('deploy.customSqlSuccessMsg', { n: result.executed_count }))
    } else {
      const extra = result.error_at > 0 ? t('deploy.errorAt', { n: result.error_at }) : ''
      ElMessage.warning(result.message || t('deploy.customSqlCompleteMsg', { extra }))
    }
    sqlDialogVisible.value = false
    customSql.value = ''
    await refreshLogs()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || t('deploy.customSqlFailed'))
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
