<template>
  <div class="connection-view">
    <!-- ── 第一部分：服务器连接管理 ── -->
    <el-card class="section-card">
      <template #header>
        <div class="section-header">
          <span>{{ $t('connection.serverSectionTitle') }}</span>
          <el-button type="primary" size="small" @click="openCreateDialog">
            {{ $t('connection.new') }}
          </el-button>
        </div>
      </template>

      <el-table
        :data="connectionStore.connections"
        v-loading="connectionStore.loading"
        border
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" :label="$t('connection.nameColumn')" min-width="120" />
        <el-table-column prop="host" :label="$t('connection.host')" min-width="130" />
        <el-table-column prop="port" :label="$t('connection.port')" width="80" />
        <el-table-column prop="username" :label="$t('connection.username')" width="100" />
        <el-table-column prop="created_at" :label="$t('common.createdAt')" width="170" />
        <el-table-column :label="$t('common.operation')" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openEditDialog(row)">{{ $t('common.edit') }}</el-button>
            <el-button size="small" type="success" link @click="handleTest(row)">{{ $t('connection.testConn') }}</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ── 第二部分：数据库角色绑定 ── -->
    <el-card class="section-card" style="margin-top: 20px">
      <template #header>
        <div class="section-header">
          <span>{{ $t('connection.roleBindSectionTitle') }}</span>
          <el-button
            type="primary"
            size="small"
            @click="handleSaveRoles"
            :loading="savingRoles"
          >
            {{ $t('connection.saveRoles') }}
          </el-button>
        </div>
      </template>

      <el-form
        ref="rolesFormRef"
        :model="rolesForm"
        label-width="180px"
        style="max-width: 880px"
      >
        <el-form-item
          :label="$t('connection.stageLabel')"
          prop="stage.conn_id"
          :rules="[{ required: true, message: t('connection.selectConnRequired'), trigger: 'change' }]"
        >
          <el-select
            v-model="rolesForm.stage.conn_id"
            :placeholder="$t('connection.selectConn')"
            style="width: 250px; margin-right: 12px"
          >
            <el-option
              v-for="c in connectionStore.connections"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
          <el-input
            v-model="rolesForm.stage.database_name"
            :placeholder="$t('connection.inputDbNamePh')"
            style="width: 200px; margin-right: 12px"
          />
          <el-button
            size="small"
            type="danger"
            :loading="creatingDb === 'stage'"
            @click="handleCreateDatabase('stage')"
          >
            {{ $t('connection.createDb') }}
          </el-button>
        </el-form-item>

        <el-form-item
          :label="$t('connection.coreLabel')"
          prop="core.conn_id"
          :rules="[{ required: true, message: t('connection.selectConnRequired'), trigger: 'change' }]"
        >
          <el-select
            v-model="rolesForm.core.conn_id"
            :placeholder="$t('connection.selectConn')"
            style="width: 250px; margin-right: 12px"
          >
            <el-option
              v-for="c in connectionStore.connections"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
          <el-input
            v-model="rolesForm.core.database_name"
            :placeholder="$t('connection.inputDbNamePh')"
            style="width: 200px; margin-right: 12px"
          />
          <el-button
            size="small"
            type="danger"
            :loading="creatingDb === 'core'"
            @click="handleCreateDatabase('core')"
          >
            {{ $t('connection.createDb') }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ── 第三部分：OLTP 源管理 ── -->
    <el-card class="section-card" style="margin-top: 20px">
      <template #header>
        <div class="section-header">
          <span>{{ $t('connection.oltpSourceSection') }}</span>
          <el-button type="primary" size="small" @click="openAddOltpSource">
            {{ $t('connection.addOltpSource') }}
          </el-button>
        </div>
      </template>

      <el-table :data="oltpSources" v-loading="oltpLoading" border stripe size="small" style="width: 100%">
        <el-table-column prop="record_src" :label="$t('connection.recordSrc')" width="140" />
        <el-table-column :label="$t('connection.oltpConnColumn')" min-width="140">
          <template #default="{ row }">
            {{ row.connection_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="database_name" :label="$t('connection.dbName')" width="210" />
        <el-table-column :label="$t('common.operation')" width="210" align="center">
          <template #default="{ row }">
            <el-button size="small" text @click="openEditOltpSource(row)">{{ $t('common.edit') }}</el-button>
            <el-button size="small" text type="danger" @click="handleDeleteOltpSource(row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- OLTP 源新增/编辑 对话框 -->
    <el-dialog
      v-model="oltpDialogVisible"
      :title="isEditingOltp ? $t('connection.editOltpSource') : $t('connection.addOltpSource')"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form ref="oltpFormRef" :model="oltpForm" :rules="oltpFormRules" label-width="140px">
        <el-form-item :label="$t('connection.recordSrc')" prop="record_src">
          <el-input v-model="oltpForm.record_src" :placeholder="$t('connection.recordSrcPlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('connection.selectOltpConn')" prop="conn_id"
          :rules="[{ required: true, message: t('connection.selectOltpConnRequired'), trigger: 'change' }]"
        >
          <el-select v-model="oltpForm.conn_id" :placeholder="$t('connection.selectConn')" style="width: 100%">
            <el-option v-for="c in connectionStore.connections" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('connection.dbName')" prop="database_name"
          :rules="[{ required: true, message: t('connection.inputDbNamePh'), trigger: 'blur' }]"
        >
          <el-input v-model="oltpForm.database_name" :placeholder="$t('connection.dbNamePlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="oltpDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="savingOltp" @click="handleSaveOltpSource">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 新建 / 编辑 对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? t('connection.editConn') : t('connection.new')"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="90px"
        style="padding-right: 20px"
      >
        <el-form-item :label="$t('connection.name')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('connection.nameRequired')" />
        </el-form-item>
        <el-form-item :label="$t('connection.host')" prop="host">
          <el-input v-model="form.host" :placeholder="$t('connection.hostRequired')" />
        </el-form-item>
        <el-form-item :label="$t('connection.port')" prop="port">
          <el-input-number
            v-model="form.port"
            :min="1"
            :max="65535"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="$t('connection.username')" prop="username">
          <el-input v-model="form.username" :placeholder="$t('connection.usernameRequired')" />
        </el-form-item>
        <el-form-item :label="$t('connection.password')" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="isEditing ? t('connection.passwordHint') : t('connection.passwordRequired')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleTestInDialog" :loading="testingInDialog">
          {{ $t('connection.testConn') }}
        </el-button>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          {{ $t('common.save') }}
        </el-button>
      </template>

      <!-- 测试连接失败时的详细错误信息 -->
      <el-input
        v-if="testError"
        v-model="testError"
        type="textarea"
        :rows="3"
        readonly
        style="margin-top: 12px"
        input-style="font-family: monospace; font-size: 12px; color: var(--el-color-danger)"
      />
    </el-dialog>

    <!-- 重建数据库 对话框 -->
    <el-dialog
      v-model="createDbDialogVisible"
      :title="t('connection.createDb')"
      width="620px"
      :close-on-click-modal="false"
      top="30vh"
    >
      <div style="margin-bottom: 12px; color: var(--el-color-danger); font-size: 14px; font-weight: 500;">
        ⚠ {{ t('connection.createDbConfirm', { dbName: createDbDbName }) }}
      </div>
      <el-input
        v-model="createDbSql"
        type="textarea"
        :rows="4"
        style="font-family: 'SF Mono', 'Fira Code', 'Courier New', monospace; font-size: 13px;"
      />
      <template #footer>
        <el-button @click="createDbDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="danger" :loading="creatingDb !== null" @click="handleCreateDatabaseConfirm">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import type { Connection } from '@/types'
import type { DatabaseRoleUpdate, OltpSource, OltpSourceCreate } from '@/types'
import * as api from '@/api'
import { useConnectionStore } from '@/stores/connection'

const { t } = useI18n()
const connectionStore = useConnectionStore()

// ── 连接列表 ──────────────────────────────────────────────────────

onMounted(() => {
  connectionStore.fetchAll()
  fetchRoles()
  fetchOltpSources()
})

// ── 对话框状态 ────────────────────────────────────────────────────

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const testingInDialog = ref(false)
const testError = ref('')

const formRef = ref<FormInstance>()

const defaultForm = () => ({
  name: 'TEST',
  host: '192.168.0.116',
  port: 1433,
  username: 'sa',
  password: 'Passw0rd',
})

const form = reactive(defaultForm())

const formRules: FormRules = {
  name: [{ required: true, message: t('connection.nameRequired'), trigger: 'blur' }],
  host: [{ required: true, message: t('connection.hostRequired'), trigger: 'blur' }],
  port: [{ required: true, message: t('connection.portRequired'), trigger: 'blur' }],
  username: [{ required: true, message: t('connection.usernameRequired'), trigger: 'blur' }],
  password: [
    {
      required: true,
      validator: (_rule: any, value: string, callback: Function) => {
        if (!isEditing.value && !value) {
          callback(new Error(t('connection.passwordRequired')))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

function resetForm() {
  Object.assign(form, defaultForm())
  editingId.value = null
  isEditing.value = false
  testError.value = ''
}

function openCreateDialog() {
  resetForm()
  dialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

function openEditDialog(row: Connection) {
  isEditing.value = true
  editingId.value = row.id
  form.name = row.name
  form.host = row.host
  form.port = row.port
  form.username = row.username
  form.password = ''
  dialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

// ── 保存连接 ──────────────────────────────────────────────────────

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (isEditing.value && editingId.value !== null) {
      const payload: any = {
        name: form.name,
        host: form.host,
        port: form.port,
        username: form.username,
      }
      if (form.password) payload.password = form.password
      await connectionStore.update(editingId.value, payload)
      ElMessage.success(t('connection.updated'))
    } else {
      await connectionStore.create({ ...form })
      ElMessage.success(t('connection.created'))
    }
    dialogVisible.value = false
    connectionStore.fetchAll()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.message || t('connection.operationFailed'))
  } finally {
    saving.value = false
  }
}

// ── 重建数据库 ──────────────────────────────────────────────────────

const createDbDialogVisible = ref(false)
const createDbSql = ref('')
const createDbDbName = ref('')
const createDbRoleName = ref('')
const creatingDb = ref<string | null>(null)

function handleCreateDatabase(roleName: string) {
  const dbName = roleName === 'stage' ? rolesForm.stage.database_name : rolesForm.core.database_name
  if (!dbName) {
    ElMessage.warning(t('connection.inputDbNamePh'))
    return
  }
  createDbRoleName.value = roleName
  createDbDbName.value = dbName
  createDbSql.value = `DROP DATABASE IF EXISTS [${dbName}]\nCREATE DATABASE [${dbName}]`
  createDbDialogVisible.value = true
}

async function handleCreateDatabaseConfirm() {
  const roleName = createDbRoleName.value
  creatingDb.value = roleName
  try {
    const res = await api.createDatabase(roleName)
    const data = res.data as any
    if (data.success) {
      ElMessage.success(data.message || t('common.success'))
      createDbDialogVisible.value = false
    } else {
      ElMessage.error(data.message || t('connection.operationFailed'))
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.message || t('connection.operationFailed'))
  } finally {
    creatingDb.value = null
  }
}

// ── 测试连接 ──────────────────────────────────────────────────────

async function handleTest(row: Connection) {
  try {
    const res = await api.testSavedConnection(row.id)
    const data = res.data
    if (data.success) {
      ElMessage.success(data.message || t('connection.testSuccess'))
    } else {
      ElMessage.warning(data.message || t('connection.testFail'))
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.message || t('connection.testFailed'))
  }
}

async function handleTestInDialog() {
  testingInDialog.value = true
  testError.value = ''
  try {
    const res = await api.testConnection({
      host: form.host,
      port: form.port,
      database_name: '',
      username: form.username,
      password: form.password,
    })
    const data = res.data
    if (data.success) {
      ElMessage.success(data.message || t('connection.testSuccess'))
    } else {
      testError.value = data.message || 'Connection failed'
    }
  } catch (e: any) {
    testError.value = e?.response?.data?.message || e?.message || t('connection.testFailed')
  } finally {
    testingInDialog.value = false
  }
}

// ── 删除连接 ──────────────────────────────────────────────────────

async function handleDelete(row: Connection) {
  try {
    await ElMessageBox.confirm(
      t('connection.deleteConfirm', { name: row.name }),
      t('connection.confirmDeleteTitle'),
      { confirmButtonText: t('common.delete'), cancelButtonText: t('common.cancel'), type: 'warning' },
    )
    await connectionStore.remove(row.id)
    ElMessage.success(t('connection.deleted'))
    connectionStore.fetchAll()
    fetchRoles() // 可能影响了角色绑定中的选择
  } catch {
    // cancelled
  }
}

// ── 数据库角色绑定 ────────────────────────────────────────────────

const rolesFormRef = ref<FormInstance>()
const savingRoles = ref(false)
const rolesForm = reactive<{
  stage: DatabaseRoleUpdate
  core: DatabaseRoleUpdate
}>({
  stage: { conn_id: 0, database_name: '' },
  core: { conn_id: 0, database_name: '' },
})

async function fetchRoles() {
  try {
    const res = await api.getDbRoles()
    const data = res.data.data
    if (data) {
      if (data.stage) {
        rolesForm.stage.conn_id = data.stage.conn_id
        rolesForm.stage.database_name = data.stage.database_name
      }
      if (data.core) {
        rolesForm.core.conn_id = data.core.conn_id
        rolesForm.core.database_name = data.core.database_name
      }
    }
  } catch {
    // ignore
  }
}

async function handleSaveRoles() {
  const valid = await rolesFormRef.value?.validate().catch(() => false)
  if (!valid) return

  savingRoles.value = true
  try {
    await api.updateDbRoles({
      stage: rolesForm.stage,
      core: rolesForm.core,
    })
    ElMessage.success(t('connection.saveRolesSuccess'))
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.message || t('connection.saveFailed'))
  } finally {
    savingRoles.value = false
  }
}

// ── OLTP 源管理 ──────────────────────────────────────────────

const oltpSources = ref<OltpSource[]>([])
const oltpLoading = ref(false)

async function fetchOltpSources() {
  oltpLoading.value = true
  try {
    const res = await api.listOltpSources()
    oltpSources.value = res.data
  } catch {
    // ignore
  } finally { oltpLoading.value = false }
}

const oltpDialogVisible = ref(false)
const isEditingOltp = ref(false)
const editingOltpId = ref<number | null>(null)
const savingOltp = ref(false)
const oltpFormRef = ref<any>(null)
const oltpForm = reactive<OltpSourceCreate>({
  record_src: '', conn_id: 0, database_name: '',
})
const oltpFormRules = {
  record_src: [{ required: true, message: t('connection.recordSrcRequired'), trigger: 'blur' }],
}

function openAddOltpSource() {
  isEditingOltp.value = false
  editingOltpId.value = null
  oltpForm.record_src = ''
  oltpForm.conn_id = 0
  oltpForm.database_name = ''
  oltpDialogVisible.value = true
}

function openEditOltpSource(row: OltpSource) {
  isEditingOltp.value = true
  editingOltpId.value = row.id
  oltpForm.record_src = row.record_src
  oltpForm.conn_id = row.conn_id
  oltpForm.database_name = row.database_name
  oltpDialogVisible.value = true
}

async function handleSaveOltpSource() {
  const valid = await oltpFormRef.value?.validate().catch(() => false)
  if (!valid) return
  savingOltp.value = true
  try {
    if (isEditingOltp.value && editingOltpId.value) {
      await api.updateOltpSource(editingOltpId.value, oltpForm)
    } else {
      await api.createOltpSource(oltpForm as OltpSourceCreate)
    }
    oltpDialogVisible.value = false
    ElMessage.success(t('common.success'))
    await fetchOltpSources()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e.message)
  } finally { savingOltp.value = false }
}

async function handleDeleteOltpSource(row: OltpSource) {
  try {
    await ElMessageBox.confirm(
      t('connection.deleteOltpSourceConfirm', { name: row.record_src }),
      t('connection.confirmDeleteTitle'),
      { confirmButtonText: t('common.delete'), cancelButtonText: t('common.cancel'), type: 'warning' },
    )
    await api.deleteOltpSource(row.id)
    ElMessage.success(t('common.success'))
    await fetchOltpSources()
  } catch { /* cancelled */ }
}
</script>

<style scoped>
.connection-view {
  padding: 20px;
}

.section-card :deep(.el-card__header) {
  padding: 12px 20px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 15px;
  font-weight: 600;
}
</style>
