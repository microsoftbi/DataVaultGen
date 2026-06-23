<template>
  <div class="dv-config-view">
    <div class="page-header">
      <h2>{{ $t('dvConfig.title') }}</h2>
    </div>

    <div class="auto-toolbar">
      <span class="toolbar-desc">{{ $t('dvConfig.autoToolbarDesc') }}</span>
      <el-select v-model="autoTableName" :placeholder="$t('dvConfig.selectSourceTable')" size="small" style="width: 200px">
        <el-option v-for="t in tableNames" :key="t" :label="t" :value="t" />
      </el-select>
      <el-button size="small" type="primary" :loading="autoConfiguring" @click="handleAutoConfig">
        {{ $t('dvConfig.autoConfig') }}
      </el-button>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- ========== HUB ========== -->
      <el-tab-pane :label="$t('dvConfig.hubsTab')" name="hub">
        <div class="tab-toolbar">
          <el-button size="small" type="primary" @click="openCreateDialog('hub')">{{ $t('dvConfig.addHub') }}</el-button>
        </div>
        <el-table :data="hubs" border stripe size="small" style="width: 100%">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="table_name" :label="$t('dvConfig.hubTableName')" min-width="200" />
          <el-table-column :label="$t('common.operation')" width="100">
            <template #default="{ row }">
              <el-button size="small" type="danger" link @click="deleteHub(row)">{{ $t('common.delete') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="!hubs.length" class="empty-hint">{{ $t('dvConfig.emptyHubs') }}</div>

        <el-divider />
        <h4>{{ $t('dvConfig.fieldMapHub') }}</h4>
        <el-table :data="hubAttributes" border stripe size="small" style="width: 100%" max-height="300">
          <el-table-column prop="table_name" :label="$t('dvConfig.sourceTable')" width="140" />
          <el-table-column prop="column_name" :label="$t('dvConfig.columnName')" width="140" />
          <el-table-column prop="data_type" :label="$t('dvConfig.dataType')" width="100" />
          <el-table-column :label="$t('dvConfig.targetHub')" width="200">
            <template #default="{ row }">
              <el-select v-model="row.dv_hub_id" :placeholder="$t('dvConfig.selectHub')" size="small" @change="(v:any) => updateAttr(row, 'dv_hub_id', v)">
                <el-option v-for="h in hubs" :key="h.id" :label="h.table_name" :value="h.id" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column :label="$t('dvConfig.dvColumn')" width="150">
            <template #default="{ row }">
              <el-input v-model="row.dv_column_name" size="small" :placeholder="$t('dvConfig.defaultSameAsSrc')" @blur="updateAttr(row, 'dv_column_name', row.dv_column_name)" />
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ========== SAT ========== -->
      <el-tab-pane :label="$t('dvConfig.satsTab')" name="sat">
        <div class="tab-toolbar">
          <el-button size="small" type="primary" @click="openCreateDialog('sat')">{{ $t('dvConfig.addSat') }}</el-button>
        </div>
        <el-table :data="sats" border stripe size="small" style="width: 100%">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="table_name" :label="$t('dvConfig.satTableName')" min-width="200" />
          <el-table-column :label="$t('common.operation')" width="100">
            <template #default="{ row }">
              <el-button size="small" type="danger" link @click="deleteSat(row)">{{ $t('common.delete') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="!sats.length" class="empty-hint">{{ $t('dvConfig.emptySats') }}</div>

        <el-divider />
        <h4>{{ $t('dvConfig.fieldMapSat') }}</h4>
        <el-table :data="satAttributes" border stripe size="small" style="width: 100%" max-height="300">
          <el-table-column prop="table_name" :label="$t('dvConfig.sourceTable')" width="140" />
          <el-table-column prop="column_name" :label="$t('dvConfig.columnName')" width="140" />
          <el-table-column prop="data_type" :label="$t('dvConfig.dataType')" width="100" />
          <el-table-column :label="$t('dvConfig.targetSat')" width="200">
            <template #default="{ row }">
              <el-select v-model="row.dv_sat_id" :placeholder="$t('dvConfig.selectSat')" size="small" @change="(v:any) => updateAttr(row, 'dv_sat_id', v)">
                <el-option v-for="s in sats" :key="s.id" :label="s.table_name" :value="s.id" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column :label="$t('dvConfig.dvColumn')" width="150">
            <template #default="{ row }">
              <el-input v-model="row.dv_column_name" size="small" :placeholder="$t('dvConfig.defaultSameAsSrc')" @blur="updateAttr(row, 'dv_column_name', row.dv_column_name)" />
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ========== LINK ========== -->
      <el-tab-pane :label="$t('dvConfig.linksTab')" name="link">
        <div class="tab-toolbar">
          <el-button size="small" type="primary" @click="openCreateDialog('link')">{{ $t('dvConfig.addLink') }}</el-button>
        </div>
        <el-table :data="links" border stripe size="small" style="width: 100%">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="table_name" :label="$t('dvConfig.linkTableName')" min-width="200" />
          <el-table-column :label="$t('common.operation')" width="100">
            <template #default="{ row }">
              <el-button size="small" type="danger" link @click="deleteLink(row)">{{ $t('common.delete') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="!links.length" class="empty-hint">{{ $t('dvConfig.emptyLinks') }}</div>

        <el-divider />
        <h4>{{ $t('dvConfig.fieldMapLink') }}</h4>
        <el-table :data="linkAttributes" border stripe size="small" style="width: 100%" max-height="300">
          <el-table-column prop="table_name" :label="$t('dvConfig.sourceTable')" width="140" />
          <el-table-column prop="column_name" :label="$t('dvConfig.columnName')" width="140" />
          <el-table-column prop="data_type" :label="$t('dvConfig.dataType')" width="100" />
          <el-table-column :label="$t('dvConfig.targetLink')" width="200">
            <template #default="{ row }">
              <el-select v-model="row.dv_link_id" :placeholder="$t('dvConfig.selectLink')" size="small" @change="(v:any) => updateAttr(row, 'dv_link_id', v)">
                <el-option v-for="l in links" :key="l.id" :label="l.table_name" :value="l.id" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column :label="$t('dvConfig.dvColumn')" width="150">
            <template #default="{ row }">
              <el-input v-model="row.dv_column_name" size="small" :placeholder="$t('dvConfig.defaultSameAsSrc')" @blur="updateAttr(row, 'dv_column_name', row.dv_column_name)" />
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 新建 DV 表对话框 -->
    <el-dialog v-model="createDialogVisible" :title="createDialogTitle" width="400px">
      <el-form @submit.prevent="handleCreate">
        <el-form-item :label="$t('dvConfig.tableNameLabel')">
          <el-input v-model="newTableName" :placeholder="$t('dvConfig.inputTableNamePh')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">{{ $t('common.create') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as api from '@/api'

const { t } = useI18n()

const activeTab = ref('hub')
const hubs = ref<any[]>([])
const sats = ref<any[]>([])
const links = ref<any[]>([])
const attributes = ref<any[]>([])
const creating = ref(false)
const createDialogVisible = ref(false)
const createDialogType = ref('hub')
const newTableName = ref('')
const autoTableName = ref('')
const autoConfiguring = ref(false)

const tableNames = computed(() => {
  const names = new Set(attributes.value.map((a: any) => a.table_name))
  return Array.from(names).sort()
})

const createDialogTitle = computed(() => {
  const m: Record<string, string> = { hub: 'HUB', sat: 'SAT', link: 'LINK' }
  return t('dvConfig.newTableDialogTitle', { type: m[createDialogType.value] })
})

const hubAttributes = computed(() => attributes.value.filter(a => a.is_bk))
const satAttributes = computed(() => attributes.value.filter(a => a.is_di))
const linkAttributes = computed(() => attributes.value.filter(a => a.is_fk))

async function loadAll() {
  const [h, s, l, a] = await Promise.all([
    api.listDvHubs(),
    api.listDvSats(),
    api.listDvLinks(),
    api.listAttributes(),
  ])
  hubs.value = h.data
  sats.value = s.data
  links.value = l.data
  attributes.value = a.data
}

function openCreateDialog(type: string) {
  createDialogType.value = type
  newTableName.value = ''
  createDialogVisible.value = true
}

async function handleCreate() {
  if (!newTableName.value) { ElMessage.warning(t('dvConfig.inputTableNameWarn')); return }
  creating.value = true
  try {
    const apiMap: Record<string, Function> = {
      hub: (n: string) => api.createDvHub(n),
      sat: (n: string) => api.createDvSat(n),
      link: (n: string) => api.createDvLink(n),
    }
    await apiMap[createDialogType.value](newTableName.value)
    ElMessage.success(t('dvConfig.createSuccess'))
    createDialogVisible.value = false
    await loadAll()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e.message)
  } finally { creating.value = false }
}

async function deleteHub(row: any) {
  try { await ElMessageBox.confirm(t('dvConfig.confirmDelete')) } catch { return }
  await api.deleteDvHub(row.id)
  ElMessage.success(t('dvConfig.deleted'))
  await loadAll()
}

async function deleteSat(row: any) {
  try { await ElMessageBox.confirm(t('dvConfig.confirmDelete')) } catch { return }
  await api.deleteDvSat(row.id)
  ElMessage.success(t('dvConfig.deleted'))
  await loadAll()
}

async function deleteLink(row: any) {
  try { await ElMessageBox.confirm(t('dvConfig.confirmDelete')) } catch { return }
  await api.deleteDvLink(row.id)
  ElMessage.success(t('dvConfig.deleted'))
  await loadAll()
}

async function handleAutoConfig() {
  if (!autoTableName.value) { ElMessage.warning(t('dvConfig.selectSourceTableWarn')); return }
  autoConfiguring.value = true
  try {
    const res = await api.autoConfigureDv(autoTableName.value)
    const data = res.data as any
    if (data.success) {
      let msg = ''
      const r = data.results
      if (r.hub) msg += `HUB: ${r.hub.table_name} (${r.hub.fields.length} fields)  `
      if (r.sat) msg += `SAT: ${r.sat.table_name} (${r.sat.fields.length} fields)  `
      if (r.link) msg += `LINK: ${r.link.table_name} (${r.link.fields.length} fields)`
      ElMessage.success(t('dvConfig.autoConfigDone', { msg }))
      await loadAll()
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e.message)
  } finally { autoConfiguring.value = false }
}

async function updateAttr(row: any, field: string, value: any) {
  try {
    await api.updateAttribute(row.id, { [field]: value })
  } catch (e: any) {
    ElMessage.error(t('dvConfig.updateFailed') + ': ' + (e?.response?.data?.message || e.message))
  }
}

onMounted(() => loadAll())
</script>

<style scoped>
.dv-config-view { padding: 20px; }
.page-header h2 { margin: 0 0 16px; font-size: 18px; font-weight: 600; }
.auto-toolbar {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 16px; background: var(--el-fill-color-light);
  border-radius: 6px; margin-bottom: 16px;
}
.toolbar-desc { font-size: 13px; color: var(--el-text-color-secondary); }
.tab-toolbar { margin-bottom: 12px; }
.empty-hint { padding: 20px; text-align: center; color: var(--el-text-color-placeholder); }
h4 { margin: 12px 0; font-size: 14px; }
</style>
