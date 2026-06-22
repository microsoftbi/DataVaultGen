<template>
  <div class="generate-view">
    <div class="page-header">
      <h2>代码生成 (PSA + DV)</h2>
    </div>

    <!-- 配置摘要 -->
    <el-card shadow="never" class="config-card">
      <template #header>
        <div class="card-header">
          <span class="section-title">配置摘要</span>
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

    <!-- PSA 生成按钮 -->
    <el-card shadow="never" class="actions-card">
      <template #header>
        <span class="section-title">PSA Type 2</span>
      </template>
      <el-row :gutter="16">
        <el-col v-for="btn in psaButtons" :key="btn.key" :span="3">
          <el-button :type="btn.type || 'default'"
            :loading="loadingMap[btn.key]" :disabled="loadingAny"
            style="width: 100%" @click="handleGenerate(btn.key)">
            {{ btn.label }}
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- DV 生成按钮 -->
    <el-card shadow="never" class="actions-card">
      <template #header>
        <span class="section-title">Data Vault 2.0</span>
      </template>
      <el-row :gutter="16">
        <el-col v-for="btn in dvButtons" :key="btn.key" :span="3">
          <el-button :type="btn.type || 'default'"
            :loading="loadingMap[btn.key]" :disabled="loadingAny"
            style="width: 100%" @click="handleGenerate(btn.key)">
            {{ btn.label }}
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- SQL 预览（语法高亮） -->
    <el-card shadow="never" class="preview-card">
      <template #header>
        <div class="card-header">
          <span class="section-title">SQL 预览</span>
          <div class="preview-actions">
            <el-tag v-if="sqlResult" size="small" type="info" class="line-count">
              {{ lineCount }} lines
            </el-tag>
            <el-button
              v-if="sqlResult"
              size="small"
              @click="copySql"
            >
              {{ copySuccess ? '已复制' : '复制 SQL' }}
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="!sqlResult" class="placeholder-text">
        点击上方按钮生成 SQL 代码...
      </div>
      <pre v-else class="sql-code"><code ref="codeRef" class="language-sql">{{ sqlResult }}</code></pre>
    </el-card>

    <!-- 编辑配置对话框 -->
    <el-dialog
      v-model="configDialogVisible"
      title="编辑配置"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="configFormRef"
        :model="configForm"
        label-width="140px"
        :rules="configRules"
      >
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
        <el-button type="primary" :loading="savingConfig" @click="saveConfig">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import {
  getConfig, updateConfig,
  generatePsaStg, generatePsaCdc, generatePsaLog,
  generatePsaViews, generatePsaUsps, generatePsaAll, generatePsaFlow,
  generateDvHub, generateDvSat, generateDvLink,
  generateDvUspHub, generateDvUspSat, generateDvUspLink, generateDvAll,
} from '@/api'
import type { AppConfig } from '@/types'

const codeRef = ref<HTMLElement | null>(null)

// ── 配置 ────────────────────────────────────────────────────────

const config = reactive<AppConfig>({ psa_db_name: '', hash_dummy: '', core_db_name: '' })
const configLoading = ref(false)

async function loadConfig() {
  configLoading.value = true
  try {
    const res = await getConfig()
    Object.assign(config, res.data)
  } catch (e: any) {
    ElMessage.error('获取配置失败: ' + (e?.response?.data?.message || e.message))
  } finally {
    configLoading.value = false
  }
}

// 配置编辑对话框
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

// ── 按钮定义 ────────────────────────────────────────────────────

interface GenerateButton { key: string; label: string; type?: string }

const psaButtons: GenerateButton[] = [
  { key: 'stg', label: 'STG' },
  { key: 'cdc', label: 'CDC' },
  { key: 'log', label: 'LOG' },
  { key: 'views', label: '视图' },
  { key: 'usps', label: '存储过程' },
  { key: 'all', label: 'PSA 全部', type: 'primary' },
  { key: 'flow', label: 'PSA 流程' },
  { key: 'download', label: '下载 SQL' },
]

const dvButtons: GenerateButton[] = [
  { key: 'dv_hub', label: 'HUB 表' },
  { key: 'dv_sat', label: 'SAT 表' },
  { key: 'dv_link', label: 'LINK 表' },
  { key: 'dv_usp_hub', label: 'USP_HUB' },
  { key: 'dv_usp_sat', label: 'USP_SAT' },
  { key: 'dv_usp_link', label: 'USP_LINK' },
  { key: 'dv_all', label: 'DV 全部', type: 'primary' },
]

// ── 生成逻辑 ────────────────────────────────────────────────────

const sqlResult = ref('')
const loadingMap = reactive<Record<string, boolean>>({})
const copySuccess = ref(false)

const lastGeneratedKey = ref('')

const labelMap: Record<string, string> = {
  stg: 'STG', cdc: 'CDC', log: 'LOG',
  views: 'VIEWS', usps: 'USPS',
  all: 'PSA', flow: 'FLOW',
  dv_hub: 'DV_HUB', dv_sat: 'DV_SAT', dv_link: 'DV_LINK',
  dv_usp_hub: 'DV_USP_HUB', dv_usp_sat: 'DV_USP_SAT', dv_usp_link: 'DV_USP_LINK',
  dv_all: 'DV',
}
const labelName = computed(() => labelMap[lastGeneratedKey.value] || 'ALL')

const lineCount = computed(() => {
  const c = sqlResult.value
  return c ? c.split('\n').length : 0
})

const allButtons = computed(() => [...psaButtons, ...dvButtons])

const loadingAny = computed(() =>
  allButtons.value.some((b) => loadingMap[b.key])
)

const apiMap: Record<string, () => Promise<any>> = {
  stg: generatePsaStg,
  cdc: generatePsaCdc,
  log: generatePsaLog,
  views: generatePsaViews,
  usps: generatePsaUsps,
  all: generatePsaAll,
  flow: generatePsaFlow,
  dv_hub: generateDvHub,
  dv_sat: generateDvSat,
  dv_link: generateDvLink,
  dv_usp_hub: generateDvUspHub,
  dv_usp_sat: generateDvUspSat,
  dv_usp_link: generateDvUspLink,
  dv_all: generateDvAll,
}

// SQL 更新后自动执行语法高亮
watch(sqlResult, async () => {
  await nextTick()
  if (codeRef.value) {
    hljs.highlightElement(codeRef.value)
  }
})

async function handleGenerate(key: string) {
  if (key === 'download') { downloadSql(); return }

  const apiFn = apiMap[key]
  if (!apiFn) return

  loadingMap[key] = true
  try {
    const res = await apiFn()
    const sql = res.data?.sql || ''
    sqlResult.value = sql
    lastGeneratedKey.value = key
    if (sql) ElMessage.success('生成成功')
    else ElMessage.warning('生成结果为空')
  } catch (e: any) {
    ElMessage.error('生成失败: ' + (e?.response?.data?.message || e.message))
  } finally { loadingMap[key] = false }
}

// ── 下载 ────────────────────────────────────────────────────────

function downloadSql() {
  if (!sqlResult.value) {
    ElMessage.warning('没有可下载的 SQL 内容')
    return
  }
  const blob = new Blob([sqlResult.value], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  a.href = url
  a.download = `psa_${labelName.value}_${today}.sql`
  a.click()
  URL.revokeObjectURL(url)
}

// ── 复制 ────────────────────────────────────────────────────────

async function copySql() {
  if (!sqlResult.value) return
  try {
    await navigator.clipboard.writeText(sqlResult.value)
    copySuccess.value = true
    ElMessage.success('已复制到剪贴板')
    setTimeout(() => { copySuccess.value = false }, 2000)
  } catch {
    ElMessage.error('复制失败，请手动选择复制')
  }
}

// ── 初始化 ──────────────────────────────────────────────────────

onMounted(() => { loadConfig() })
</script>

<style scoped>
.generate-view {
  max-width: 1200px;
  margin: 0 auto;
}
.page-header h2 {
  margin: 0 0 16px 0;
  font-size: 20px;
}
.config-card, .actions-card, .preview-card {
  margin-bottom: 16px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.section-title {
  font-weight: 600;
  font-size: 15px;
}
.loading-placeholder {
  padding: 8px 0;
}
.preview-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.line-count {
  font-family: monospace;
}
.placeholder-text {
  padding: 40px 0;
  text-align: center;
  color: var(--el-text-color-placeholder);
  font-size: 14px;
}
.sql-code {
  margin: 0;
  padding: 16px;
  border-radius: 4px;
  background: #f6f8fa;
  overflow-x: auto;
  max-height: 600px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.6;
}
.sql-code code {
  font-family: 'SF Mono', 'Fira Code', 'Courier New', monospace;
  background: none;
  padding: 0;
}
</style>