<template>
  <div class="generate-psa-view">
    <div class="page-header">
      <h2>PSA Type 2 代码生成</h2>
    </div>

    <el-card shadow="never" class="actions-card">
      <template #header>
        <span class="section-title">生成按钮</span>
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

    <!-- SQL 预览 -->
    <el-card shadow="never" class="preview-card">
      <template #header>
        <div class="card-header">
          <span class="section-title">SQL 预览</span>
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

      <div v-if="!sqlResult" class="placeholder-text">
        点击上方按钮生成 PSA SQL 代码...
      </div>
      <pre v-else class="sql-code"><code ref="codeRef" class="language-sql">{{ sqlResult }}</code></pre>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import {
  generatePsaStg, generatePsaCdc, generatePsaLog,
  generatePsaViews, generatePsaUsps, generatePsaAll, generatePsaFlow,
} from '@/api'

const codeRef = ref<HTMLElement | null>(null)
const sqlResult = ref('')
const loadingMap = reactive<Record<string, boolean>>({})
const copySuccess = ref(false)

interface GenerateButton { key: string; label: string; type?: string }

const psaButtons: GenerateButton[] = [
  { key: 'stg', label: 'STG' },
  { key: 'cdc', label: 'CDC' },
  { key: 'log', label: 'LOG' },
  { key: 'views', label: '视图' },
  { key: 'usps', label: '存储过程' },
  { key: 'all', label: 'PSA 全部', type: 'primary' },
  { key: 'flow', label: 'PSA 流程' },
]

const loadingAny = computed(() => psaButtons.some((b) => loadingMap[b.key]))

const lineCount = computed(() => {
  const c = sqlResult.value; return c ? c.split('\n').length : 0
})

const apiMap: Record<string, () => Promise<any>> = {
  stg: generatePsaStg, cdc: generatePsaCdc, log: generatePsaLog,
  views: generatePsaViews, usps: generatePsaUsps,
  all: generatePsaAll, flow: generatePsaFlow,
}

watch(sqlResult, async () => {
  await nextTick()
  if (codeRef.value) hljs.highlightElement(codeRef.value)
})

async function handleGenerate(key: string) {
  const apiFn = apiMap[key]
  if (!apiFn) return

  loadingMap[key] = true
  try {
    const res = await apiFn()
    const sql = res.data?.sql || ''
    sqlResult.value = sql
    if (sql) ElMessage.success('生成成功')
    else ElMessage.warning('生成结果为空')
  } catch (e: any) {
    ElMessage.error('生成失败: ' + (e?.response?.data?.message || e.message))
  } finally { loadingMap[key] = false }
}

function downloadSql() {
  if (!sqlResult.value) { ElMessage.warning('没有可下载的 SQL 内容'); return }
  const blob = new Blob([sqlResult.value], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `psa_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}.sql`
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

onMounted(() => { /* no config needed here */ })
</script>

<style scoped>
.generate-psa-view { max-width: 1200px; margin: 0 auto; }
.page-header h2 { margin: 0 0 16px 0; font-size: 20px; }
.actions-card, .preview-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.section-title { font-weight: 600; font-size: 15px; }
.preview-actions { display: flex; align-items: center; gap: 8px; }
.line-count { font-family: monospace; }
.placeholder-text {
  padding: 40px 0; text-align: center; color: var(--el-text-color-placeholder); font-size: 14px;
}
.sql-code {
  margin: 0; padding: 16px; border-radius: 4px; background: #f6f8fa;
  overflow-x: auto; max-height: 600px; overflow-y: auto;
  font-size: 13px; line-height: 1.6;
}
.sql-code code { font-family: 'SF Mono', 'Fira Code', 'Courier New', monospace; background: none; padding: 0; }
</style>