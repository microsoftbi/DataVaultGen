<template>
  <div class="dv-config-view">
    <div class="page-header">
      <h2>Data Vault 配置</h2>
    </div>

    <div class="auto-toolbar">
      <span class="toolbar-desc">基于字段标记自动创建 HUB/SAT/LINK 表并完成映射：</span>
      <el-select v-model="autoTableName" placeholder="选择源表" size="small" style="width: 200px">
        <el-option v-for="t in tableNames" :key="t" :label="t" :value="t" />
      </el-select>
      <el-button size="small" type="primary" :loading="autoConfiguring" @click="handleAutoConfig">
        一键自动配置
      </el-button>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- ========== HUB ========== -->
      <el-tab-pane label="HUB 配置" name="hub">
        <div class="tab-toolbar">
          <el-button size="small" type="primary" @click="openCreateDialog('hub')">新建 HUB</el-button>
        </div>
        <el-table :data="hubs" border stripe size="small" style="width: 100%">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="table_name" label="HUB 表名" min-width="200" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" type="danger" link @click="deleteHub(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="!hubs.length" class="empty-hint">暂无 HUB 配置，请先新建。</div>

        <el-divider />
        <h4>字段映射（BK 字段 → HUB）</h4>
        <el-table :data="hubAttributes" border stripe size="small" style="width: 100%" max-height="300">
          <el-table-column prop="table_name" label="源表" width="140" />
          <el-table-column prop="column_name" label="字段名" width="140" />
          <el-table-column prop="data_type" label="类型" width="100" />
          <el-table-column label="目标 HUB" width="200">
            <template #default="{ row }">
              <el-select v-model="row.dv_hub_id" placeholder="选择 HUB" size="small" @change="(v:any) => updateAttr(row, 'dv_hub_id', v)">
                <el-option v-for="h in hubs" :key="h.id" :label="h.table_name" :value="h.id" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="DV 列名" width="150">
            <template #default="{ row }">
              <el-input v-model="row.dv_column_name" size="small" placeholder="默认同源" @blur="updateAttr(row, 'dv_column_name', row.dv_column_name)" />
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ========== SAT ========== -->
      <el-tab-pane label="SAT 配置" name="sat">
        <div class="tab-toolbar">
          <el-button size="small" type="primary" @click="openCreateDialog('sat')">新建 SAT</el-button>
        </div>
        <el-table :data="sats" border stripe size="small" style="width: 100%">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="table_name" label="SAT 表名" min-width="200" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" type="danger" link @click="deleteSat(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="!sats.length" class="empty-hint">暂无 SAT 配置，请先新建。</div>

        <el-divider />
        <h4>字段映射（DI 字段 → SAT）</h4>
        <el-table :data="satAttributes" border stripe size="small" style="width: 100%" max-height="300">
          <el-table-column prop="table_name" label="源表" width="140" />
          <el-table-column prop="column_name" label="字段名" width="140" />
          <el-table-column prop="data_type" label="类型" width="100" />
          <el-table-column label="目标 SAT" width="200">
            <template #default="{ row }">
              <el-select v-model="row.dv_sat_id" placeholder="选择 SAT" size="small" @change="(v:any) => updateAttr(row, 'dv_sat_id', v)">
                <el-option v-for="s in sats" :key="s.id" :label="s.table_name" :value="s.id" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="DV 列名" width="150">
            <template #default="{ row }">
              <el-input v-model="row.dv_column_name" size="small" placeholder="默认同源" @blur="updateAttr(row, 'dv_column_name', row.dv_column_name)" />
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ========== LINK ========== -->
      <el-tab-pane label="LINK 配置" name="link">
        <div class="tab-toolbar">
          <el-button size="small" type="primary" @click="openCreateDialog('link')">新建 LINK</el-button>
        </div>
        <el-table :data="links" border stripe size="small" style="width: 100%">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="table_name" label="LINK 表名" min-width="200" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" type="danger" link @click="deleteLink(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="!links.length" class="empty-hint">暂无 LINK 配置，请先新建。</div>

        <el-divider />
        <h4>字段映射（FK 字段 → LINK）</h4>
        <el-table :data="linkAttributes" border stripe size="small" style="width: 100%" max-height="300">
          <el-table-column prop="table_name" label="源表" width="140" />
          <el-table-column prop="column_name" label="字段名" width="140" />
          <el-table-column prop="data_type" label="类型" width="100" />
          <el-table-column label="目标 LINK" width="200">
            <template #default="{ row }">
              <el-select v-model="row.dv_link_id" placeholder="选择 LINK" size="small" @change="(v:any) => updateAttr(row, 'dv_link_id', v)">
                <el-option v-for="l in links" :key="l.id" :label="l.table_name" :value="l.id" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="DV 列名" width="150">
            <template #default="{ row }">
              <el-input v-model="row.dv_column_name" size="small" placeholder="默认同源" @blur="updateAttr(row, 'dv_column_name', row.dv_column_name)" />
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 新建 DV 表对话框 -->
    <el-dialog v-model="createDialogVisible" :title="createDialogTitle" width="400px">
      <el-form @submit.prevent="handleCreate">
        <el-form-item label="表名">
          <el-input v-model="newTableName" placeholder="请输入表名（如 HUB_CUSTOMER）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as api from '@/api'

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
  return `新建 ${m[createDialogType.value]} 表`
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
  if (!newTableName.value) { ElMessage.warning('请输入表名'); return }
  creating.value = true
  try {
    const apiMap: Record<string, Function> = {
      hub: (n: string) => api.createDvHub(n),
      sat: (n: string) => api.createDvSat(n),
      link: (n: string) => api.createDvLink(n),
    }
    await apiMap[createDialogType.value](newTableName.value)
    ElMessage.success('创建成功')
    createDialogVisible.value = false
    await loadAll()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e.message)
  } finally { creating.value = false }
}

async function deleteHub(row: any) {
  try { await ElMessageBox.confirm('确定删除？') } catch { return }
  await api.deleteDvHub(row.id)
  ElMessage.success('已删除')
  await loadAll()
}

async function deleteSat(row: any) {
  try { await ElMessageBox.confirm('确定删除？') } catch { return }
  await api.deleteDvSat(row.id)
  ElMessage.success('已删除')
  await loadAll()
}

async function deleteLink(row: any) {
  try { await ElMessageBox.confirm('确定删除？') } catch { return }
  await api.deleteDvLink(row.id)
  ElMessage.success('已删除')
  await loadAll()
}

async function handleAutoConfig() {
  if (!autoTableName.value) { ElMessage.warning('请先选择源表'); return }
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
      ElMessage.success(`自动配置完成：${msg}`)
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
    ElMessage.error('更新失败: ' + (e?.response?.data?.message || e.message))
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