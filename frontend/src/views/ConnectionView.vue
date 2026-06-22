<template>
  <div class="connection-view">
    <div class="page-header">
      <h2>数据库连接管理</h2>
      <el-button type="primary" @click="openCreateDialog">
        新建连接
      </el-button>
    </div>

    <el-table
      :data="connectionStore.connections"
      v-loading="connectionStore.loading"
      border
      stripe
      style="width: 100%"
    >
      <el-table-column prop="name" label="名称" min-width="140" />
      <el-table-column prop="host" label="主机" min-width="130" />
      <el-table-column prop="port" label="端口" width="80" />
      <el-table-column prop="database_name" label="数据库" min-width="140" />
      <el-table-column label="类型标签" width="200">
        <template #default="{ row }">
          <el-tag v-if="row.is_meta" type="primary" size="small" style="margin-right: 4px">元数据</el-tag>
          <el-tag v-if="row.is_source" type="success" size="small" style="margin-right: 4px">源库</el-tag>
          <el-tag v-if="row.is_target" type="warning" size="small">目标库</el-tag>
          <span v-if="!row.is_meta && !row.is_source && !row.is_target" class="no-tag">--</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" link @click="openEditDialog(row)">编辑</el-button>
          <el-button size="small" type="success" link @click="handleTest(row)">测试连接</el-button>
          <el-button size="small" type="danger" link @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建 / 编辑 对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑连接' : '新建连接'"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        style="padding-right: 20px"
      >
        <el-form-item label="连接名称" prop="name">
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
        <el-form-item label="数据库名" prop="database_name">
          <el-input v-model="form.database_name" placeholder="请输入数据库名" />
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
        <el-form-item label="用途">
          <el-checkbox v-model="form.is_meta">元数据</el-checkbox>
          <el-checkbox v-model="form.is_source">源库</el-checkbox>
          <el-checkbox v-model="form.is_target">目标库</el-checkbox>
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
        placeholder=""
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import type { Connection, ConnectionCreate } from '@/types'
import * as api from '@/api'
import { useConnectionStore } from '@/stores/connection'

const connectionStore = useConnectionStore()

// ── 列表 ──────────────────────────────────────────────────────────

onMounted(() => {
  connectionStore.fetchAll()
})

// ── 对话框状态 ────────────────────────────────────────────────────

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const testingInDialog = ref(false)
const testError = ref('')

const formRef = ref<FormInstance>()

const defaultForm = (): ConnectionCreate => ({
  name: 'TEST',
  host: '192.168.0.116',
  port: 1433,
  database_name: 'TEST_STORE',
  username: 'sa',
  password: 'Passw0rd',
  is_meta: false,
  is_source: true,
  is_target: false,
})

const form = reactive<ConnectionCreate>(defaultForm())

const formRules: FormRules = {
  name: [{ required: true, message: '请输入连接名称', trigger: 'blur' }],
  host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口', trigger: 'blur' }],
  database_name: [{ required: true, message: '请输入数据库名', trigger: 'blur' }],
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

// ── 打开新建/编辑 ────────────────────────────────────────────────

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
  form.database_name = row.database_name
  form.username = row.username
  form.password = ''
  form.is_meta = row.is_meta
  form.is_source = row.is_source
  form.is_target = row.is_target
  dialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

// ── 保存 ──────────────────────────────────────────────────────────

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (isEditing.value && editingId.value !== null) {
      const payload: Partial<ConnectionCreate> = {
        name: form.name,
        host: form.host,
        port: form.port,
        database_name: form.database_name,
        username: form.username,
        is_meta: form.is_meta,
        is_source: form.is_source,
        is_target: form.is_target,
      }
      if (form.password) {
        payload.password = form.password
      }
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

// ── 测试连接（列表行中） ────────────────────────────────────────

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

// ── 测试连接（对话框中） ────────────────────────────────────────

async function handleTestInDialog() {
  testingInDialog.value = true
  testError.value = ''
  try {
    const res = await api.testConnection({
      host: form.host,
      port: form.port,
      database_name: form.database_name,
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

// ── 删除 ──────────────────────────────────────────────────────────

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
  } catch {
    // cancelled
  }
}
</script>

<style scoped>
.connection-view {
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

.no-tag {
  color: var(--el-text-color-placeholder);
}
</style>