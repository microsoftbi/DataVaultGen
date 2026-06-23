<template>
  <div class="generate-dv-view">
    <div class="page-header">
      <h2>Data Vault 2.0 代码生成</h2>
    </div>

    <el-card shadow="never" class="preview-card">
      <template #header>
        <div class="card-header">
          <span class="section-title">选择生成类型</span>
          <div class="preview-actions">
            <el-tag v-if="sqlResult" size="small" type="info" class="line-count">
              {{ lineCount }} lines
            </el-tag>
            <el-button v-if="sqlResult" size="small" @click="copySql">
              {{ copySuccess ? '已复制' : '复制 SQL' }}
            </el-button>
            <el-button v-if="sqlResult" size="small" @click="downloadSql">
              下载 SQL
            </el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab" type="card" @tab-change="onTabChange">
        <el-tab-pane label="HUB 表" name="dv_hub" />
        <el-tab-pane label="SAT 表" name="dv_sat" />
        <el-tab-pane label="LINK 表" name="dv_link" />
        <el-tab-pane label="USP_HUB" name="dv_usp_hub" />
        <el-tab-pane label="USP_SAT" name="dv_usp_sat" />
        <el-tab-pane label="USP_LINK" name="dv_usp_link" />
        <el-tab-pane label="DV 全部" name="dv_all" />
      </el-tabs>

      <div v-if="!sqlResult && !generating" class="placeholder-text">
        选择上方标签自动生成对应 SQL 代码...
      </div>
      <div v-loading="generating" class="sql-wrapper">
        <pre v-if="sqlResult" class="sql-code"><code ref="codeRef" class="language-sql">{{ sqlResult }}</code></pre>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import {
  generateDvHub, generateDvSat, generateDvLink,
  generateDvUspHub, generateDvUspSat, generateDvUspLink, generateDvAll,
} from '@/api'

const codeRef = ref<HTMLElement | null>(null)
const sqlResult = ref('')
const generating = ref(false)
const copySuccess = ref(false)
const activeTab = ref('dv_hub')

const lineCount = computed(() => {
  const c = sqlResult.value; return c ? c.split('\n').length : 0
})

const apiMap: Record<string, () => Promise<any>> = {
  dv_hub: generateDvHub, dv_sat: generateDvSat, dv_link: generateDvLink,
  dv_usp_hub: generateDvUspHub, dv_usp_sat: generateDvUspSat,
  dv_usp_link: generateDvUspLink, dv_all: generateDvAll,
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
    if (!sql) ElMessage.warning('生成结果为空')
  } catch (e: any) {
    ElMessage.error('生成失败: ' + (e?.response?.data?.message || e.message))
  } finally { generating.value = false }
}

function downloadSql() {
  if (!sqlResult.value) { ElMessage.warning('没有可下载的 SQL 内容'); return }
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
    copySuccess.value = true; ElMessage.success('已复制到剪贴板')
    setTimeout(() => { copySuccess.value = false }, 2000)
  } catch { ElMessage.error('复制失败') }
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
  margin: 16px 0 0; padding: 16px; border-radius: 4px; background: #f6f8fa;
  overflow-x: auto; max-height: 600px; overflow-y: auto;
  font-size: 13px; line-height: 1.6;
}
.sql-code code { font-family: 'SF Mono', 'Fira Code', 'Courier New', monospace; background: none; padding: 0; }
</style>