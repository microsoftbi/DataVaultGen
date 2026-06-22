<template>
  <div class="connection-view">
    <!-- ── 第一部分：服务器连接管理 ── -->
    <el-card class="section-card">
      <template #header>
        <div class="section-header">
          <span>服务器连接管理</span>
          <el-button type="primary" size="small" @click="openCreateDialog">
            新建连接
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
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="host" label="主机" min-width="130" />
        <el-table-column prop="port" label="端口" width="80" />
        <el-table-column prop="username" label="用户名" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" type="success" link @click="handleTest(row)">测试连接</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ── 第二部分：数据库角色绑定 ── -->
    <el-card class="section-card" style="margin-top: 20px">
      <template #header>
        <div class="section-header">
          <span>数据库角色绑定</span>
          <el-button
            type="primary"
            size="small"
            @click="handleSaveRoles"
            :loading="savingRoles"
          >
            保存角色配置
          </el-button>
        </div>
      </template>

      <el-form
        ref="rolesFormRef"
        :model="rolesForm"
        label-width="120px"
        style="max-width: 700px"
      >
        <el-form-item
          label="OLTP（源系统）"
          prop="oltp.conn_id"
          :rules="[{ required: true, message: '请选择连接', trigger: 'change' }]"
        >
          <el-select
            v-model="rolesForm.oltp.conn_id"
            placeholder="选择连接"
            style="width: 250px; margin-right: 12px"
            @change="rolesForm.oltp.conn_id = $event"
          >
            <el-option
              v-for="c in connectionStore.connections"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
          <el-input
            v-model="rolesForm.oltp.database_name"
            placeholder="输入数据库名"
            style="width: 200px"
          />
        </el-form-item>

        <el-form-item
          label="STAGE（PSA 层）"
          prop="stage.conn_id"
          :rules="[{ required: true, message: '请选择连接', trigger: 'change' }]"
        >
          <el-select
            v-model="rolesForm.stage.conn_id"
            placeholder="选择连接"
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
            placeholder="输入数据库名"
            style="width: 200px"
          />
        </el-form-item>

        <el-form-item
          label="CORE（DV 层）"
          prop="core.conn_id"
          :rules="[{ required: true, message: '请选择连接', trigger: 'change' }]"
        >
          <el-select
            v-model="rolesForm.core.conn_id"
            placeholder="选择连接"
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
            placeholder="输入数据库名"
            style="width: 200px"
          />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 新建 / 编辑 对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑连接' : '新建连接'"
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
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入连接名称" />
        </el-form-item>
        <el-form-item label="主机" prop="host">
          <el-input v-model="form.host" placeholder="请输入主机地址" />
        </el-form-item>
        <el-form-item label="端口" prop="port">
          <el-input-number
            v-model="form.port"
            :min="1"
            :max="65535"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="isEditing ? '留空则不修改密码' : '请输入密码'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleTestInDialog" :loading="testingInDialog">
          测试连接
        </el-button>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          保存
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import type { Connection } from '@/types'
import type { DatabaseRoleUpdate } from '@/types'
import * as api from '@/api'
import { useConnectionStore } from '@/stores/connection'

const connectionStore = useConnectionStore()

// ── 连接列表 ──────────────────────────────────────────────────────

onMounted(() => {
  connectionStore.fetchAll()
  fetchRoles()
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
  name: [{ required: true, message: '请输入连接名称', trigger: 'blur' }],
  host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口', trigger: 'blur' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    {
      required: true,
      validator: (_rule: any, value: string, callback: Function) => {
        if (!isEditing.value && !value) {
          callback(new Error('请输入密码'))
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
      ElMessage.success('连接已更新')
    } else {
      await connectionStore.create({ ...form })
      ElMessage.success('连接已创建')
    }
    dialogVisible.value = false
    connectionStore.fetchAll()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.message || '操作失败')
  } finally {
    saving.value = false
  }
}

// ── 测试连接 ──────────────────────────────────────────────────────

async function handleTest(row: Connection) {
  try {
    const res = await api.testSavedConnection(row.id)
    const data = res.data
    if (data.success) {
      ElMessage.success(data.message || '连接成功')
    } else {
      ElMessage.warning(data.message || '连接失败')
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.message || '测试连接失败')
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
      ElMessage.success(data.message || '连接成功')
    } else {
      testError.value = data.message || 'Connection failed'
    }
  } catch (e: any) {
    testError.value = e?.response?.data?.message || e?.message || '测试连接失败'
  } finally {
    testingInDialog.value = false
  }
}

// ── 删除连接 ──────────────────────────────────────────────────────

async function handleDelete(row: Connection) {
  try {
    await ElMessageBox.confirm(
      `确定要删除连接「${row.name}」吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    await connectionStore.remove(row.id)
    ElMessage.success('连接已删除')
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
  oltp: DatabaseRoleUpdate
  stage: DatabaseRoleUpdate
  core: DatabaseRoleUpdate
}>({
  oltp: { conn_id: 0, database_name: '' },
  stage: { conn_id: 0, database_name: '' },
  core: { conn_id: 0, database_name: '' },
})

async function fetchRoles() {
  try {
    const res = await api.getDbRoles()
    const data = res.data.data
    if (data) {
      if (data.oltp) {
        rolesForm.oltp.conn_id = data.oltp.conn_id
        rolesForm.oltp.database_name = data.oltp.database_name
      }
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
      oltp: rolesForm.oltp,
      stage: rolesForm.stage,
      core: rolesForm.core,
    })
    ElMessage.success('角色配置已保存')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.message || '保存失败')
  } finally {
    savingRoles.value = false
  }
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