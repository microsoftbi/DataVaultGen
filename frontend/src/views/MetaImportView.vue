<template>
  <div class="meta-import-view">
    <div class="page-header">
      <h2>{{ $t('metaImport.pageTitle') }}</h2>
    </div>

    <!-- 步骤条 -->
    <el-steps :active="activeStep" finish-status="success" class="import-steps">
      <el-step :title="$t('metaImport.step1Title')" :description="$t('metaImport.step1Desc')" />
      <el-step :title="$t('metaImport.step2Title')" :description="$t('metaImport.step2Desc')" />
      <el-step :title="$t('metaImport.step3Title')" :description="$t('metaImport.step3Desc')" />
      <el-step :title="$t('metaImport.step4Title')" :description="$t('metaImport.step4Desc')" />
      <el-step :title="$t('metaImport.step5Title')" :description="$t('metaImport.step5Desc')" />
    </el-steps>

    <!-- ==================== Step 0: 选择源连接 ==================== -->
    <el-card v-show="activeStep === 0" shadow="never" class="step-card">
      <template #header><span class="step-title">{{ $t('metaImport.step1TitleLong') }}</span></template>
      <div v-if="!connectionsLoading && sourceConnections.length === 0" class="empty-hint">
        <el-empty :description="$t('metaImport.emptyConn')">
          <p>{{ $t('metaImport.emptyHint') }}</p>
          <el-button type="primary" @click="goToConnections">{{ $t('metaImport.goToConnections') }}</el-button>
        </el-empty>
      </div>
      <div v-else>
        <el-form label-width="120px">
          <el-form-item :label="$t('metaImport.oltpLabel')">
            <el-select v-model="selectedConnId" :placeholder="$t('metaImport.selectOltp')" style="width: 360px" :loading="connectionsLoading" @change="onConnChange">
              <el-option v-for="c in sourceConnections" :key="c.id" :label="c.name" :value="c.id">
                <span>{{ c.name }}</span>
                <span class="conn-detail">({{ c.host }} / {{ c.database_name || '?' }})</span>
              </el-option>
            </el-select>
          </el-form-item>
        </el-form>
        <div class="step-actions">
          <el-button type="primary" :disabled="!selectedConnId" @click="loadTables">{{ $t('common.next') }}</el-button>
        </div>
      </div>
    </el-card>

    <!-- ==================== Step 1: 选择数据表 ==================== -->
    <el-card v-show="activeStep === 1" shadow="never" class="step-card">
      <template #header><span class="step-title">{{ $t('metaImport.step2TitleLong') }}</span></template>

      <el-table :data="tables" v-loading="tablesLoading" border stripe style="width: 100%"
        @selection-change="onSelectionChange" ref="tableRef">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="table_schema" :label="$t('metaImport.tableSchema')" min-width="160" />
        <el-table-column prop="table_name" :label="$t('metaImport.tableName')" min-width="200" />
      </el-table>

      <div class="step-actions">
        <el-button @click="activeStep = 0">{{ $t('common.prev') }}</el-button>
        <el-button type="primary" :disabled="selectedTables.length === 0" :loading="loadingColumns" @click="loadAllColumns">
          {{ $t('metaImport.nextConfigCols', { count: selectedTables.length }) }}
        </el-button>
      </div>
    </el-card>

    <!-- ==================== Step 2: 配置导入列（每表一个标签页） ==================== -->
    <el-card v-show="activeStep === 2" shadow="never" class="step-card">
      <template #header>
        <div class="step2-header">
          <span class="step-title">{{ $t('metaImport.step3TitleLong') }}</span>
        </div>
      </template>

      <el-tabs v-model="activeTableKey" type="border-card">
        <el-tab-pane v-for="cfg in tableConfigs" :key="cfg.key" :name="cfg.key" :label="cfg.tableName">
          <template #label>
            <span>{{ cfg.tableName }}</span>
            <el-tag size="small" type="info" style="margin-left: 6px">{{ (selectedKeysMap[cfg.key] || []).length }}/{{ cfg.totalCount }}</el-tag>
          </template>
          <div style="display: flex; justify-content: center; padding: 12px 0; width: 100%;">
            <el-transfer
              v-model="selectedKeysMap[cfg.key]"
              :data="cfg.transferData"
              :titles="[t('metaImport.leftListTitle'), t('metaImport.rightListTitle')]"
              @change="(value: any, direction: any, keys: any) => handleTransfer(cfg, direction, keys)"
              style="height: 400px; width: 100%;"
            />
          </div>
        </el-tab-pane>
      </el-tabs>

      <div class="step-actions">
        <el-button @click="activeStep = 1">{{ $t('common.prev') }}</el-button>
        <el-button type="primary" @click="goToConfirm">
          {{ $t('metaImport.importBtn', { count: selectedTables.length }) }}
        </el-button>
      </div>
    </el-card>

    <!-- ==================== Step 3: 确认导入 ==================== -->
    <el-card v-show="activeStep === 3" shadow="never" class="step-card">
      <template #header><span class="step-title">{{ $t('metaImport.step4TitleLong') }}</span></template>

      <el-table :data="confirmSummary" border stripe size="small" style="width: 100%">
        <el-table-column prop="tableName" :label="$t('metaImport.importTableHeader')" min-width="180" />
        <el-table-column prop="selectedCount" :label="$t('metaImport.importedCols')" width="100">
          <template #default="{ row }"><el-tag type="success">{{ row.selectedCount }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="skippedCount" :label="$t('metaImport.skippedCols')" width="150">
          <template #default="{ row }"><el-tag v-if="row.skippedCount" type="warning">{{ row.skippedCount }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="columns" :label="$t('metaImport.columns')" min-width="300">
          <template #default="{ row }"><el-text size="small" type="info">{{ row.columns.join(', ') }}</el-text></template>
        </el-table-column>
      </el-table>

      <div class="step-actions">
        <el-button :disabled="importing" @click="activeStep = 2">{{ $t('common.prev') }}</el-button>
        <el-button type="primary" :loading="importing" @click="handleBatchImport">
          {{ $t('metaImport.importBtn', { count: selectedTables.length }) }}
        </el-button>
      </div>
    </el-card>

    <!-- ==================== Step 4: 导入结果 ==================== -->
    <el-card v-show="activeStep === 4" shadow="never" class="step-card">
      <template #header><span class="step-title">{{ $t('metaImport.step5TitleLong') }}</span></template>
      <el-result icon="success" :title="$t('metaImport.importComplete')"
        :sub-title="t('metaImport.importSummary', { tables: importResults.length, fields: totalImported })">
        <template #extra>
          <el-table :data="importResults" border stripe size="small" style="width: 100%; margin-bottom: 16px">
            <el-table-column prop="table" :label="$t('metaImport.importTableHeader')" min-width="180" />
            <el-table-column prop="imported" :label="$t('metaImport.importedField')" width="100">
              <template #default="{ row }"><el-tag :type="row.error ? 'danger' : 'success'">{{ row.imported || 0 }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="error" :label="$t('metaImport.result')" min-width="300">
              <template #default="{ row }">
                <el-text v-if="row.error" type="danger" size="small">{{ row.error }}</el-text>
                <el-text v-else type="success" size="small">{{ $t('metaImport.rowSuccess') }}</el-text>
              </template>
            </el-table-column>
          </el-table>
          <el-button type="primary" @click="goToMetaConfig">{{ $t('metaImport.goToMetaConfig') }}</el-button>
          <el-button @click="resetAll">{{ $t('metaImport.continueImport') }}</el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { Connection, SourceTable } from '@/types'
import * as api from '@/api'

const router = useRouter()
const { t } = useI18n()

// ── 技术 / BK 判定 ──────────────────────────────────────────────
const TECHNICAL_FIELDS = new Set([
  'LOAD_DTS', 'LOAD_DT', 'REC_SRC', 'REC_PATH',
  'TRANSFER_DTS', 'FILE_TRANSFER_DTS',
  'HK', 'HF', 'HD', 'INSERT_TIME', 'INSERTTIME',
  'CDC_OPERATION_CODE', 'VALID_FROM', 'VALID_TO', 'IS_CURRENT',
  'SEQUENCE_NO', 'SESSION_DTS', 'FULLY_QUALIFIED_FILE_NAME',
])
const BK_PATTERNS = [/^ID$/i, /.*_ID$/i, /.*_CODE$/i, /.*_KEY$/i, /.*_NO$/i, /^CODE$/i, /^KEY$/i]
function isTechnical(name: string) { return TECHNICAL_FIELDS.has(name.toUpperCase()) }
function isBkRecommended(name: string) { return BK_PATTERNS.some(p => p.test(name)) }

// ── 状态 ──────────────────────────────────────────────────────────
const activeStep = ref(0)
const connectionsLoading = ref(false)
const connections = ref<Connection[]>([])
const selectedConnId = ref<number | null>(null)
const sourceConnections = computed(() => connections.value)

const tablesLoading = ref(false)
const tables = ref<SourceTable[]>([])
const selectedTables = ref<SourceTable[]>([])
const tableRef = ref<any>(null)

const loadingColumns = ref(false)
const tableConfigs = ref<TableConfig[]>([])
const activeTableKey = ref('')

interface TableConfig {
  key: string
  tableName: string
  tableSchema: string
  transferData: { key: string; label: string; disabled: boolean }[]
  totalCount: number
}

const selectedKeysMap = ref<Record<string, string[]>>({})

const importing = ref(false)
const importResults = ref<any[]>([])
const totalImported = ref(0)

const totalSelectedCount = computed(() =>
  Object.values(selectedKeysMap.value).reduce((s, arr) => s + arr.filter(k => !isTechnical(k)).length, 0)
)

const confirmSummary = computed(() =>
  tableConfigs.value.map(c => {
    const keys = selectedKeysMap.value[c.key] || []
    const nonTech = keys.filter(k => !isTechnical(k))
    return {
      tableName: c.tableName,
      selectedCount: nonTech.length,
      skippedCount: c.totalCount - nonTech.length,
      columns: nonTech,
    }
  })
)

// ── 生命周期 ──────────────────────────────────────────────────────
onMounted(() => fetchConnections())
function goToConnections() { router.push('/connections') }

// ── 连接 ──────────────────────────────────────────────────────────
async function fetchConnections() {
  connectionsLoading.value = true
  try {
    const res = await api.listConnections()
    connections.value = res.data
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || e?.message || t('metaImport.fetchConnFailed')) }
  finally { connectionsLoading.value = false }
}

function onConnChange() {
  selectedTables.value = []
  tables.value = []
  tableConfigs.value = []
  selectedKeysMap.value = {}
}

// ── 表 ───────────────────────────────────────────────────────────
async function loadTables() {
  if (!selectedConnId.value) return
  tablesLoading.value = true
  activeStep.value = 1
  try {
    const res = await api.listSourceTables(selectedConnId.value)
    if (res.data.success) tables.value = res.data.tables
    else { ElMessage.warning((res.data as any).message || t('metaImport.fetchTablesFailed')); tables.value = [] }
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || e?.message || t('metaImport.fetchTablesFailed')); tables.value = [] }
  finally { tablesLoading.value = false }
}

function onSelectionChange(rows: SourceTable[]) { selectedTables.value = rows }

// ── 加载所有表的列配置（源表列 + 已有 META 列） ────────────────
async function loadAllColumns() {
  if (!selectedConnId.value || selectedTables.value.length === 0) return
  loadingColumns.value = true
  const configs: TableConfig[] = []
  const keyMap: Record<string, string[]> = {}

  for (const tbl of selectedTables.value) {
    const key = `${tbl.table_schema}.${tbl.table_name}`
    try {
      // 读取源表列
      const srcRes = await api.listSourceColumns(selectedConnId.value, tbl.table_schema, tbl.table_name)
      const srcCols = (srcRes.data as any).columns || []

      // 读取 META 中已有的列
      const metaRes = await api.listAttributes(tbl.table_name)
      const metaCols = (metaRes.data || []).map((a: any) => a.column_name)

      // 构造 transfer data（显示: 字段名(类型)）
      const transferData = srcCols.map((c: any) => ({
        key: c.column_name,
        label: `${c.column_name} (${c.data_type || '?'})`,
        disabled: isTechnical(c.column_name),
      }))

      // 右侧：已经在 META 中的列 + 非技术字段
      keyMap[key] = metaCols

      configs.push({ key, tableName: tbl.table_name, tableSchema: tbl.table_schema, transferData, totalCount: srcCols.length })
    } catch (e: any) {
      ElMessage.error(t('metaImport.fetchColumnsFailed', { table: tbl.table_name }))
    }
  }

  tableConfigs.value = configs
  selectedKeysMap.value = keyMap
  if (configs.length > 0) activeTableKey.value = configs[0].key
  activeStep.value = 2
  loadingColumns.value = false
}

// ── 传输列处理（实时导入/删除） ──────────────────────────────────
async function handleTransfer(cfg: TableConfig, direction: string, keys: string[]) {
  if (direction === 'right') {
    // 左→右：导入到 META
    try {
      await api.importMeta(selectedConnId.value!, cfg.tableSchema, cfg.tableName, undefined, keys)
      ElMessage.success(t('metaImport.transferImported', { table: cfg.tableName, n: keys.length }))
    } catch (e: any) {
      ElMessage.error(t('metaImport.importColumnsFailed', { msg: e?.response?.data?.detail || e?.message }))
      // 回退：从右侧移除
      selectedKeysMap.value[cfg.key] = (selectedKeysMap.value[cfg.key] || []).filter(k => !keys.includes(k))
    }
  } else {
    // 右→左：从 META 删除
    try {
      // 先查出这些列名的 attribute ID
      const metaRes = await api.listAttributes(cfg.tableName)
      const toDelete = (metaRes.data || []).filter((a: any) => keys.includes(a.column_name)).map((a: any) => ({ id: a.id }))
      if (toDelete.length > 0) {
        await api.batchDeleteAttributes(toDelete)
        ElMessage.success(t('metaImport.transferRemoved', { table: cfg.tableName, n: toDelete.length }))
      }
    } catch (e: any) {
      ElMessage.error(t('metaImport.removeColumnsFailed', { msg: e?.response?.data?.detail || e?.message }))
      // 回退
      selectedKeysMap.value[cfg.key] = [...(selectedKeysMap.value[cfg.key] || []), ...keys]
    }
  }
}

// ── 确认 ──────────────────────────────────────────────────────────
function goToConfirm() { activeStep.value = 3 }

// ── 批量导入 ──────────────────────────────────────────────────────
async function handleBatchImport() {
  if (!selectedConnId.value || tableConfigs.value.length === 0) return
  importing.value = true
  importResults.value = []
  totalImported.value = 0

  for (const cfg of tableConfigs.value) {
    const cols = (selectedKeysMap.value[cfg.key] || []).filter(k => !isTechnical(k))
    try {
      const res = await api.importMeta(selectedConnId.value!, cfg.tableSchema, cfg.tableName, undefined, cols)
      const data = res.data as any
      importResults.value.push({
        table: cfg.tableName,
        imported: data.imported || 0,
        error: null,
      })
      totalImported.value += data.imported || 0
    } catch (e: any) {
      const msg = e?.response?.data?.detail || e?.response?.data?.message || e?.message || t('metaImport.importFailed')
      console.error(`Import ${cfg.tableName} failed:`, msg)
      importResults.value.push({
        table: cfg.tableName,
        imported: 0,
        error: msg,
      })
    }
  }

  activeStep.value = 4
  importing.value = false
  ElMessage.success(t('metaImport.importDoneSummary', { tables: tableConfigs.value.length, fields: totalImported.value }))
}

function goToMetaConfig() { router.push('/meta-config') }

function resetAll() {
  activeStep.value = 0
  selectedTables.value = []
  tables.value = []
  tableConfigs.value = []
  selectedKeysMap.value = {}
  importResults.value = []
  totalImported.value = 0
}
</script>

<style scoped>
.meta-import-view { padding: 20px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.page-header h2 { margin: 0; font-size: 18px; font-weight: 600; }
.import-steps { margin-bottom: 28px; }
.step-card { border-radius: 8px; }
.step-title { font-size: 15px; font-weight: 600; }
.step2-header { display: flex; align-items: center; justify-content: space-between; }
.step2-actions { display: flex; gap: 8px; }
.empty-hint p { margin: 16px 0; color: var(--el-text-color-secondary); }
.conn-detail { color: var(--el-text-color-placeholder); font-size: 12px; margin-left: 8px; }
.tech-field { color: var(--el-text-color-placeholder); text-decoration: line-through; }
.tab-actions { margin-top: 10px; display: flex; gap: 8px; }
.step-actions { margin-top: 20px; display: flex; gap: 10px; justify-content: flex-end; }
</style>

<style>
/* 全局生效：将 el-transfer 面板宽度增加 80%（默认 200px → 360px） */
.el-transfer-panel { width: 360px !important; }
</style>
