<template>
  <div class="intro-container">
    <div v-loading="loading" class="markdown-body" v-html="renderedHtml"></div>
    <el-empty v-if="!loading && !renderedHtml" :description="$t('intro.empty')" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'

const { locale } = useI18n()

// 配置 marked 使用 highlight.js
marked.setOptions({
  highlight(code: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
})

const loading = ref(true)
const renderedHtml = ref('')

async function loadIntro() {
  loading.value = true
  try {
    const res = await fetch(`/api/intro?lang=${encodeURIComponent(locale.value)}`)
    const data = await res.json()
    if (data.success && data.content) {
      renderedHtml.value = await marked.parse(data.content)
    } else {
      renderedHtml.value = ''
    }
  } catch (e) {
    console.error('Failed to load intro', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadIntro)
watch(locale, loadIntro)
</script>

<style scoped>
.intro-container {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.markdown-body {
  line-height: 1.8;
  color: var(--el-text-color-primary);
}

.markdown-body h1 {
  font-size: 24px;
  border-bottom: 1px solid var(--el-border-color-light);
  padding-bottom: 12px;
  margin-bottom: 20px;
}

.markdown-body h2 {
  font-size: 20px;
  margin-top: 28px;
  margin-bottom: 12px;
}

.markdown-body h3 {
  font-size: 16px;
  margin-top: 20px;
  margin-bottom: 8px;
}

.markdown-body p {
  margin-bottom: 12px;
}

.markdown-body ul,
.markdown-body ol {
  padding-left: 24px;
  margin-bottom: 12px;
}

.markdown-body li {
  margin-bottom: 4px;
}

.markdown-body code {
  background-color: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.markdown-body pre {
  background-color: var(--el-fill-color);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin-bottom: 16px;
}

.markdown-body pre code {
  background: none;
  padding: 0;
}

.markdown-body a {
  color: var(--el-color-primary);
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.markdown-body blockquote {
  border-left: 4px solid var(--el-color-primary);
  padding-left: 16px;
  margin-left: 0;
  color: var(--el-text-color-secondary);
}

.markdown-body table {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 16px;
}

.markdown-body th,
.markdown-body td {
  border: 1px solid var(--el-border-color-light);
  padding: 8px 12px;
  text-align: left;
}

.markdown-body th {
  background-color: var(--el-fill-color-light);
  font-weight: 600;
}
</style>