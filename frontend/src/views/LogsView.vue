<template>
  <div class="logs-view">
    <div class="page-header">
      <h2>{{ $t('logs.title') }}</h2>
      <div class="header-actions">
        <el-button @click="fetchLogs" :loading="loading">{{ $t('logs.refresh') }}</el-button>
        <el-button type="danger" @click="handleClear">{{ $t('logs.clear') }}</el-button>
      </div>
    </div>

    <!-- 统计栏 -->
    <el-card shadow="never" class="summary-card">
      <div class="summary-bar">
        <span class="summary-item">
          {{ $t('logs.total') }}：<strong>{{ summary.total }}</strong>
        </span>
        <el-divider direction="vertical" />
        <span class="summary-item summary-info">
          {{ $t('logs.info') }}：<strong>{{ summary.info }}</strong>
        </span>
        <el-divider direction="vertical" />
        <span class="summary-item summary-error">
          {{ $t('logs.error') }}：<strong>{{ summary.error }}</strong>
        </span>
        <el-divider direction="vertical" />
        <span class="summary-item summary-warning">
          {{ $t('logs.warning') }}：<strong>{{ summary.warning }}</strong>
        </span>
      </div>
    </el-card>

    <!-- 日志列表 -->
    <el-table
      :data="logs"
      v-loading="loading"
      border
      stripe
      style="width: 100%"
      max-height="620px"
      :default-sort="{ prop: 'created_at', order: 'descending' }"
    >
      <el-table-column prop="id" label="ID" width="70" sortable />
      <el-table-column prop="created_at" :label="$t('logs.time')" width="170" sortable />
      <el-table-column prop="log_source" :label="$t('logs.source')" min-width="120" />
      <el-table-column :label="$t('logs.logType')" width="90">
        <template #default="{ row }">
          <el-tag :type="logTypeTag(row.log_type)" size="small">
            {{ logTypeLabel(row.log_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="message" :label="$t('logs.message')" min-width="300" show-overflow-tooltip>
        <template #default="{ row }">
          <el-link type="primary" underline @click="showMessageDetail(row)">{{ row.message }}</el-link>
        </template>
      </el-table-column>
    </el-table>

    <!-- 消息详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      :title="$t('logs.detailTitle')"
      width="1050px"
      :close-on-click-modal="false"
      top="5vh"
    >
      <el-form v-if="detailRow" label-width="80px">
        <el-form-item :label="$t('logs.time')">
          <el-text>{{ detailRow.created_at }}</el-text>
        </el-form-item>
        <el-form-item :label="$t('logs.source')">
          <el-text>{{ detailRow.log_source || '-' }}</el-text>
        </el-form-item>
        <el-form-item :label="$t('logs.logType')">
          <el-tag :type="logTypeTag(detailRow.log_type)" size="small">
            {{ logTypeLabel(detailRow.log_type) }}
          </el-tag>
        </el-form-item>
        <el-form-item :label="$t('logs.message')">
          <el-input
            :model-value="detailRow.message || ''"
            type="textarea"
            :rows="18"
            readonly
            input-style="font-family: 'SF Mono', 'Fira Code', monospace; font-size: 13px; line-height: 1.6;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="detailVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { LogEntry } from '@/types'
import { listLogs, clearLogs } from '@/api'

const { t } = useI18n()

const logs = ref<LogEntry[]>([])
const loading = ref(false)
const detailVisible = ref(false)
const detailRow = ref<LogEntry | null>(null)

const summary = reactive({
  total: 0,
  info: 0,
  error: 0,
  warning: 0,
})

function logTypeTag(type: string) {
  if (type === 'N') return 'success'
  if (type === 'E') return 'danger'
  if (type === 'W') return 'warning'
  return 'info'
}

function logTypeLabel(type: string) {
  if (type === 'N') return t('logs.typeInfo')
  if (type === 'E') return t('logs.typeError')
  if (type === 'W') return t('logs.typeWarning')
  return type
}

function showMessageDetail(row: LogEntry) {
  detailRow.value = row
  detailVisible.value = true
}

function calcSummary() {
  let info = 0
  let error = 0
  let warning = 0
  for (const log of logs.value) {
    if (log.log_type === 'N') info++
    else if (log.log_type === 'E') error++
    else if (log.log_type === 'W') warning++
  }
  summary.total = logs.value.length
  summary.info = info
  summary.error = error
  summary.warning = warning
}

async function fetchLogs() {
  loading.value = true
  try {
    const res = await listLogs()
    logs.value = res.data
    calcSummary()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.message || t('logs.getLogsFailed'))
  } finally {
    loading.value = false
  }
}

async function handleClear() {
  try {
    await ElMessageBox.confirm(t('logs.clearConfirm'), t('logs.confirmClearTitle'), {
      confirmButtonText: t('logs.clearBtn'),
      cancelButtonText: t('common.cancel'),
      type: 'warning',
    })
    await clearLogs()
    ElMessage.success(t('logs.cleared'))
    logs.value = []
    calcSummary()
  } catch {
    // cancelled
  }
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.logs-view {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.summary-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.summary-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
}

.summary-item strong {
  font-weight: 600;
}

.summary-info {
  color: #67c23a;
}

.summary-error {
  color: #f56c6c;
}

.summary-warning {
  color: #e6a23c;
}
</style>
