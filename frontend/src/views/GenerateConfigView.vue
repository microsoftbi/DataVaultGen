<template>
  <div class="generate-config-view">
    <div class="page-header">
      <h2>{{ $t('generate.configSummary') }}</h2>
    </div>

    <el-card shadow="never" class="config-card">
      <template #header>
        <div class="card-header">
          <span class="section-title">{{ $t('generate.sysConfig') }}</span>
          <el-button size="small" @click="openConfigDialog">{{ $t('generate.editConfig') }}</el-button>
        </div>
      </template>

      <div v-if="configLoading" class="loading-placeholder">
        <el-skeleton :rows="2" animated />
      </div>
      <el-descriptions v-else :column="2" border size="small">
        <el-descriptions-item :label="$t('generate.psaDbName')">
          {{ config.psa_db_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('generate.hashDummy')">
          {{ config.hash_dummy || '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('generate.coreDbName')">
          {{ config.core_db_name || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 编辑配置对话框 -->
    <el-dialog
      v-model="configDialogVisible"
      :title="$t('generate.editConfig')"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form ref="configFormRef" :model="configForm" label-width="140px" :rules="configRules">
        <el-form-item :label="$t('generate.psaDbName')" prop="psa_db_name">
          <el-input v-model="configForm.psa_db_name" :placeholder="$t('generate.inputPsaDbPh')" />
        </el-form-item>
        <el-form-item :label="$t('generate.hashDummy')" prop="hash_dummy">
          <el-input v-model="configForm.hash_dummy" :placeholder="$t('generate.inputHashDummyPh')" />
        </el-form-item>
        <el-form-item :label="$t('generate.coreDbLabel')" prop="core_db_name">
          <el-input v-model="configForm.core_db_name" :placeholder="$t('generate.inputCoreDbPh')" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="configDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="savingConfig" @click="saveConfig">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getConfig, updateConfig } from '@/api'
import type { AppConfig } from '@/types'

const { t } = useI18n()

const config = reactive<AppConfig>({ psa_db_name: '', hash_dummy: '', core_db_name: '' })
const configLoading = ref(false)

onMounted(loadConfig)
async function loadConfig() {
  configLoading.value = true
  try {
    const res = await getConfig()
    Object.assign(config, res.data)
  } catch (e: any) {
    ElMessage.error(t('generate.getConfigFailed') + ': ' + (e?.response?.data?.message || e.message))
  } finally { configLoading.value = false }
}

const configDialogVisible = ref(false)
const configForm = reactive<AppConfig>({ psa_db_name: '', hash_dummy: '', core_db_name: '' })
const savingConfig = ref(false)
const configFormRef = ref<any>(null)

const configRules = {
  psa_db_name: [{ required: true, message: t('generate.inputPsaDbPh'), trigger: 'blur' }],
  hash_dummy: [{ required: true, message: t('generate.inputHashDummyPh'), trigger: 'blur' }],
  core_db_name: [{ required: true, message: t('generate.inputCoreDbPh'), trigger: 'blur' }],
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
    ElMessage.success(t('generate.configSaved'))
  } catch (e: any) {
    ElMessage.error(t('generate.saveConfigFailed') + ': ' + (e?.response?.data?.message || e.message))
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
