<template>
  <div class="generate-config-view">
    <div class="page-header">
      <h2>配置摘要</h2>
    </div>

    <el-card shadow="never" class="config-card">
      <template #header>
        <div class="card-header">
          <span class="section-title">系统配置</span>
          <el-button size="small" @click="openConfigDialog">编辑配置</el-button>
        </div>
      </template>

      <div v-if="configLoading" class="loading-placeholder">
        <el-skeleton :rows="2" animated />
      </div>
      <el-descriptions v-else :column="2" border size="small">
        <el-descriptions-item label="PSA 数据库名">
          {{ config.psa_db_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="HASHDUMMY">
          {{ config.hash_dummy || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="CORE 数据库（DV）">
          {{ config.core_db_name || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 编辑配置对话框 -->
    <el-dialog
      v-model="configDialogVisible"
      title="编辑配置"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form ref="configFormRef" :model="configForm" label-width="140px" :rules="configRules">
        <el-form-item label="PSA 数据库名" prop="psa_db_name">
          <el-input v-model="configForm.psa_db_name" placeholder="请输入 PSA 数据库名" />
        </el-form-item>
        <el-form-item label="HASHDUMMY" prop="hash_dummy">
          <el-input v-model="configForm.hash_dummy" placeholder="请输入 HASHDUMMY 值" />
        </el-form-item>
        <el-form-item label="CORE 库名 (DV)" prop="core_db_name">
          <el-input v-model="configForm.core_db_name" placeholder="请输入 CORE 数据库名" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="configDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingConfig" @click="saveConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getConfig, updateConfig } from '@/api'
import type { AppConfig } from '@/types'

const config = reactive<AppConfig>({ psa_db_name: '', hash_dummy: '', core_db_name: '' })
const configLoading = ref(false)

onMounted(loadConfig)
async function loadConfig() {
  configLoading.value = true
  try {
    const res = await getConfig()
    Object.assign(config, res.data)
  } catch (e: any) {
    ElMessage.error('获取配置失败: ' + (e?.response?.data?.message || e.message))
  } finally { configLoading.value = false }
}

const configDialogVisible = ref(false)
const configForm = reactive<AppConfig>({ psa_db_name: '', hash_dummy: '', core_db_name: '' })
const savingConfig = ref(false)
const configFormRef = ref<any>(null)

const configRules = {
  psa_db_name: [{ required: true, message: '请输入 PSA 数据库名', trigger: 'blur' }],
  hash_dummy: [{ required: true, message: '请输入 HASHDUMMY 值', trigger: 'blur' }],
  core_db_name: [{ required: true, message: '请输入 CORE 数据库名', trigger: 'blur' }],
}

function openConfigDialog() {
  configForm.psa_db_name = config.psa_db_name
  configForm.hash_dummy = config.hash_dummy
  configForm.core_db_name = config.core_db_name
  configDialogVisible.value = true
}

async function saveConfig() {
  if (!configFormRef.value) return
  try { await configFormRef.value.validate() } catch { return }
  savingConfig.value = true
  try {
    await updateConfig({
      psa_db_name: configForm.psa_db_name,
      hash_dummy: configForm.hash_dummy,
      core_db_name: configForm.core_db_name,
    })
    Object.assign(config, configForm)
    configDialogVisible.value = false
    ElMessage.success('配置已更新')
  } catch (e: any) {
    ElMessage.error('保存配置失败: ' + (e?.response?.data?.message || e.message))
  } finally { savingConfig.value = false }
}
</script>

<style scoped>
.generate-config-view { max-width: 1200px; margin: 0 auto; }
.page-header h2 { margin: 0 0 16px 0; font-size: 20px; }
.config-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.section-title { font-weight: 600; font-size: 15px; }
.loading-placeholder { padding: 8px 0; }
</style>