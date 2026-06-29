<template>
  <div class="meta-config-view">
    <!-- 对象列表 -->
    <div class="section">
      <div class="section-header">
        <h3>{{ $t('metaConfig.objectList') }}</h3>
      </div>

      <el-table :data="objects" v-loading="objectsLoading" border stripe style="width:100%">
        <el-table-column prop="table_name" :label="$t('metaConfig.tableName')" min-width="200" />
        <el-table-column prop="schema_name" :label="$t('common.schema')" width="100" />
        <el-table-column :label="$t('metaConfig.operation')" width="120" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openFieldConfig(row)">{{ $t('metaConfig.fieldConfig') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 字段配置对话框 -->
    <el-dialog v-model="dialogVisible" :title="t('metaConfig.fieldConfigTitle', { table: dialogTableName })"
      :width="fullscreen ? '98%' : '800px'" :fullscreen="fullscreen"
      :close-on-click-modal="false" @closed="onDialogClosed">
      <template #header="{ close, titleId, titleClass }">
        <div class="dialog-header">
          <span :id="titleId" :class="titleClass">{{ $t('metaConfig.fieldConfigTitle', { table: dialogTableName }) }}</span>
          <el-button :icon="fullscreen ? FullScreen : FullScreen" size="small" circle
            @click="fullscreen = !fullscreen" />
        </div>
      </template>
      <div class="dialog-field-actions">
        <el-button size="small" @click="handleSetAllDi">{{ $t('metaConfig.setAllDi') }}</el-button>
        <el-button size="small" @click="handleClearAll">{{ $t('metaConfig.clearAllMark') }}</el-button>
        <el-button type="primary" size="small" :loading="saving"
          :disabled="modifiedRows.length === 0" @click="handleSave">
          {{ $t('metaConfig.saveChanges') }} <span v-if="modifiedRows.length > 0">({{ modifiedRows.length }})</span>
        </el-button>
      </div>

      <el-table :data="attributes" v-loading="attributesLoading" border stripe style="width:100%" max-height="450" row-key="id">
        <el-table-column prop="column_name" :label="$t('metaConfig.columnName')" min-width="160" />
        <el-table-column prop="data_type" :label="$t('metaConfig.dataType')" width="140" />
        <el-table-column :label="$t('metaConfig.isBkPk')" width="120" align="center">
          <template #default="{ row }">
            <el-checkbox :model-value="row.is_bk || row.is_pk"
              @change="(v:any) => handleBkPkChange(row, v as boolean)" />
          </template>
        </el-table-column>
        <el-table-column :label="$t('metaConfig.isDi')" width="80" align="center">
          <template #default="{ row }">
            <el-checkbox :model-value="row.is_di"
              @change="(v:any) => handleDiChange(row, v as boolean)" />
          </template>
        </el-table-column>
        <el-table-column :label="$t('metaConfig.isFk')" width="80" align="center">
          <template #default="{ row }">
            <el-checkbox :model-value="row.is_fk"
              @change="(v:any) => handleFkChange(row, v as boolean)" />
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { FullScreen } from '@element-plus/icons-vue'
import type { ObjectItem, Attribute } from '@/types'
import * as api from '@/api'

const { t } = useI18n()

// ── 对象列表 ─────────────────────────────────────────────────────

const objects = ref<ObjectItem[]>([])
const objectsLoading = ref(false)

async function loadObjects() {
  objectsLoading.value = true
  try {
    const res = await api.listObjects()
    objects.value = res.data
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.message || t('metaConfig.loadObjectsFailed'))
  } finally { objectsLoading.value = false }
}

// ── 字段配置对话框 ───────────────────────────────────────────────

const dialogVisible = ref(false)
const dialogTableName = ref('')
const fullscreen = ref(false)
const attributes = ref<Attribute[]>([])
const attributesLoading = ref(false)
const saving = ref(false)
const modifiedRows = ref<Attribute[]>([])

function takeSnapshot() {
  modifiedRows.value = []
}

function markModified(row: Attribute) {
  const idx = modifiedRows.value.findIndex(r => r.id === row.id)
  if (idx >= 0) modifiedRows.value[idx] = { ...row }
  else modifiedRows.value.push({ ...row })
}

async function openFieldConfig(row: ObjectItem) {
  dialogTableName.value = row.table_name
  dialogVisible.value = true

  attributesLoading.value = true
  try {
    const res = await api.listAttributes(row.table_name)
    const list: Attribute[] = res.data
    for (const attr of list) {
      // 没有任何标记时默认 DI
      if (!attr.is_bk && !attr.is_pk && !attr.is_di && !attr.is_fk) attr.is_di = true
      // 加载后同步：如果 is_bk 或 is_pk 任一为 true，两个都设为 true
      if (attr.is_bk || attr.is_pk) { attr.is_bk = true; attr.is_pk = true }
    }
    attributes.value = list
    takeSnapshot()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.message || t('metaConfig.loadFailed'))
    attributes.value = []
  } finally { attributesLoading.value = false }
}

function onDialogClosed() {
  attributes.value = []
  modifiedRows.value = []
}

function handleBkPkChange(row: Attribute, val: boolean) {
  if (!val) { row.is_bk = false; row.is_pk = false; markModified(row); return }
  row.is_bk = true; row.is_pk = true; row.is_di = false; row.is_fk = false
  markModified(row)
}
function handleDiChange(row: Attribute, val: boolean) {
  if (!val) { row.is_di = false; markModified(row); return }
  row.is_di = true; row.is_bk = false; row.is_pk = false; row.is_fk = false
  markModified(row)
}
function handleFkChange(row: Attribute, val: boolean) {
  if (!val) { row.is_fk = false; markModified(row); return }
  row.is_fk = true; row.is_bk = false; row.is_pk = false; row.is_di = false
  markModified(row)
}

function handleSetAllDi() {
  for (const attr of attributes.value) {
    attr.is_bk = false; attr.is_pk = false; attr.is_di = true; markModified(attr)
  }
}
function handleClearAll() {
  for (const attr of attributes.value) {
    attr.is_bk = false; attr.is_pk = false; attr.is_di = false; markModified(attr)
  }
}

async function handleSave() {
  if (modifiedRows.value.length === 0) { ElMessage.info(t('metaConfig.noChanges')); return }
  saving.value = true
  try {
    await api.batchUpdateAttributes(modifiedRows.value.map(r => ({
      id: r.id, is_bk: r.is_bk, is_pk: r.is_pk, is_di: r.is_di, is_fk: r.is_fk,
    })))
    ElMessage.success(t('metaConfig.savedCount', { n: modifiedRows.value.length }))
    takeSnapshot()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || e?.message || t('metaConfig.saveFailed')) }
  finally { saving.value = false }
}

// ── 生命周期 ─────────────────────────────────────────────────────

onMounted(() => loadObjects())
</script>

<style scoped>
.meta-config-view { padding: 20px; }
.section { background: var(--el-bg-color); border-radius: 6px; border: 1px solid var(--el-border-color-light); padding: 16px; margin-bottom: 20px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.section-header h3 { margin: 0; font-size: 15px; font-weight: 600; }
.header-actions { display: flex; gap: 8px; }
.dialog-field-actions { display: flex; gap: 8px; margin-bottom: 12px; }
.dialog-header { display: flex; align-items: center; justify-content: space-between; width: 100%; }
</style>
