<template>
  <div class="logs-view">
    <div class="page-header">
      <h2>执行日志</h2>
      <div class="header-actions">
        <el-button @click="fetchLogs" :loading="loading">刷新</el-button>
        <el-button type="danger" @click="handleClear">清空日志</el-button>
      </div>
    </div>

    <!-- 统计栏 -->
    <el-card shadow="never" class="summary-card">
      <div class="summary-bar">
        <span class="summary-item">
          总计：<strong>{{ summary.total }}</strong>
        </span>
        <el-divider direction="vertical" />
        <span class="summary-item summary-info">
          信息：<strong>{{ summary.info }}</strong>
        </span>
        <el-divider direction="vertical" />
        <span class="summary-item summary-error">
          错误：<strong>{{ summary.error }}</strong>
        </span>
        <el-divider direction="vertical" />
        <span class="summary-item summary-warning">
          警告：<strong>{{ summary.warning }}</strong>
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
      <el-table-column prop="created_at" label="时间" width="170" sortable />
      <el-table-column prop="log_source" label="来源" min-width="120" />
      <el-table-column label="类型" width="90">
        <template #default="{ row }">
          <el-tag :type="logTypeTag(row.log_type)" size="small">
            {{ logTypeLabel(row.log_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="message" label="消息" min-width="300" show-overflow-tooltip>
        <template #default="{ row }">
          <el-link type="primary" underline @click="showMessageDetail(row)">{{ row.message }}</el-link>
        </template>
      </el-table-column>
    </el-table>

    <!-- 消息详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="消息详情"
      width="1050px"
      :close-on-click-modal="false"
      top="5vh"
    >
      <el-form v-if="detailRow" label-width="80px">
        <el-form-item label="时间">
          <el-text>{{ detailRow.created_at }}</el-text>
        </el-form-item>
        <el-form-item label="来源">
          <el-text>{{ detailRow.log_source || '-' }}</el-text>
        </el-form-item>
        <el-form-item label="类型">
          <el-tag :type="logTypeTag(detailRow.log_type)" size="small">
            {{ logTypeLabel(detailRow.log_type) }}
          </el-tag>
        </el-form-item>
        <el-form-item label="消息">
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
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { LogEntry } from '@/types'
import { listLogs, clearLogs } from '@/api'

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
  if (type === 'N') return '信息'
  if (type === 'E') return '错误'
  if (type === 'W') return '警告'
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
    ElMessage.error(e?.response?.data?.message || e?.message || '获取日志失败')
  } finally {
    loading.value = false
  }
}

async function handleClear() {
  try {
    await ElMessageBox.confirm('确定要清空所有执行日志吗？此操作不可恢复。', '确认清空', {
      confirmButtonText: '清空',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await clearLogs()
    ElMessage.success('日志已清空')
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