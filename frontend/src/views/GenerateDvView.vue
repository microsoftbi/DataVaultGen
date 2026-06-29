<template>
  <div class="generate-dv-view">
    <div class="page-header">
      <h2>{{ $t('generate.dvTitle') }}</h2>
    </div>

    <el-card shadow="never" class="preview-card">
      <template #header>
        <div class="card-header">
          <span class="section-title">{{ $t('generate.selectType') }}</span>
          <div class="preview-actions">
            <el-tag v-if="sqlResult" size="small" type="info" class="line-count">
              {{ lineCount }} {{ $t('generate.lines') }}
            </el-tag>
            <el-button v-if="sqlResult" size="small" @click="copySql">
              {{ copySuccess ? $t('common.copied') : $t('generate.copySql') }}
            </el-button>
            <el-button v-if="sqlResult" size="small" @click="downloadSql">
              {{ $t('generate.downloadSql') }}
            </el-button>
            <el-button v-if="sqlResult" size="small" type="primary"
                       :loading="executing" @click="executeCurrentSql">
              {{ $t('generate.executeSql') }}
            </el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab" type="card" @tab-change="onTabChange">
        <el-tab-pane :label="$t('generate.dvTabs.hub')" name="dv_hub" />
        <el-tab-pane :label="$t('generate.dvTabs.sat')" name="dv_sat" />
        <el-tab-pane :label="$t('generate.dvTabs.link')" name="dv_link" />
        <el-tab-pane :label="$t('generate.dvTabs.uspHub')" name="dv_usp_hub" />
        <el-tab-pane :label="$t('generate.dvTabs.uspSat')" name="dv_usp_sat" />
        <el-tab-pane :label="$t('generate.dvTabs.uspLink')" name="dv_usp_link" />
        <el-tab-pane :label="$t('generate.dvTabs.all')" name="dv_all" />
        <el-tab-pane :label="$t('generate.dvTabs.flow')" name="dv_flow" />
      </el-tabs>

      <div v-if="!sqlResult && !generating" class="placeholder-text">
        {{ $t('generate.placeholderText') }}
      </div>
      <div v-loading="generating" class="sql-wrapper">
        <pre v-if="sqlResult" class="sql-code"><code ref="codeRef" class="language-sql">{{ sqlResult }}</code></pre>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import {
  generateDvHub, generateDvSat, generateDvLink,
  generateDvUspHub, generateDvUspSat, generateDvUspLink, generateDvAll,
  generateDvFlow,
  executeSql,
} from '@/api'

const { t } = useI18n()

const codeRef = ref<HTMLElement | null>(null)
const sqlResult = ref('')
const generating = ref(false)
const executing = ref(false)
const copySuccess = ref(false)
const activeTab = ref('dv_hub')

const lineCount = computed(() => {
  const c = sqlResult.value; return c ? c.split('\n').length : 0
})

const apiMap: Record<string, () => Promise<any>> = {
  dv_hub: generateDvHub, dv_sat: generateDvSat, dv_link: generateDvLink,
  dv_usp_hub: generateDvUspHub, dv_usp_sat: generateDvUspSat,
  dv_usp_link: generateDvUspLink, dv_all: generateDvAll,
  dv_flow: generateDvFlow,
}

watch(sqlResult, async () => {
  await nextTick()
  if (codeRef.value) hljs.highlightElement(codeRef.value)
})

async function onTabChange(tabName: string | number) {
  const apiFn = apiMap[tabName as string]
  if (!apiFn) return
  generating.value = true
  sqlResult.value = ''
  try {
    const res = await apiFn()
    const sql = res.data?.sql || ''
    sqlResult.value = sql
    if (!sql) ElMessage.warning(t('generate.generateEmpty'))
  } catch (e: any) {
    ElMessage.error(t('generate.generateFailed') + ': ' + (e?.response?.data?.message || e.message))
  } finally { generating.value = false }
}

function downloadSql() {
  if (!sqlResult.value) { ElMessage.warning(t('generate.noDownloadable')); return }
  const blob = new Blob([sqlResult.value], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `dv_${activeTab.value}_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}.sql`
  a.click(); URL.revokeObjectURL(url)
}

async function copySql() {
  if (!sqlResult.value) return
  try {
    await navigator.clipboard.writeText(sqlResult.value)
    copySuccess.value = true; ElMessage.success(t('generate.copied'))
    setTimeout(() => { copySuccess.value = false }, 2000)
  } catch { ElMessage.error(t('generate.copyFailed')) }
}

async function executeCurrentSql() {
  if (!sqlResult.value) return
  try {
    await ElMessageBox.confirm(
      t('deploy.confirmDeploy', { name: 'CORE · ' + t('generate.dvTabs.' + activeTab.value.replace('dv_', '')) }),
      t('common.pleaseConfirm'),
      { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' }
    )
  } catch { return }

  executing.value = true
  try {
    const res = await executeSql(sqlResult.value, 'CORE')
    if (res.data?.success) {
      ElMessage.success(t('deploy.deploySuccess'))
    } else {
      ElMessage.error(t('deploy.deployFailed') + ': ' + (res.data?.message || ''))
    }
  } catch (e: any) {
    ElMessage.error(t('deploy.deployFailed') + ': ' + (e?.response?.data?.message || e.message))
  } finally {
    executing.value = false
  }
}

onMounted(() => { onTabChange('dv_hub') })
</script>

<style scoped>
.generate-dv-view { max-width: 1200px; margin: 0 auto; }
.page-header h2 { margin: 0 0 16px 0; font-size: 20px; }
.preview-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.section-title { font-weight: 600; font-size: 15px; }
.preview-actions { display: flex; align-items: center; gap: 8px; }
.line-count { font-family: monospace; }
.placeholder-text {
  padding: 40px 0; text-align: center; color: var(--el-text-color-placeholder); font-size: 14px;
}
.sql-wrapper { min-height: 100px; }
.sql-code {
  margin: 16px 0 0; padding: 16px; border-radius: 4px; background: var(--el-fill-color);
  overflow-x: auto; max-height: 600px; overflow-y: auto;
  font-size: 13px; line-height: 1.6;
}
.sql-code code { font-family: 'SF Mono', 'Fira Code', 'Courier New', monospace; background: none; padding: 0; }
</style>
