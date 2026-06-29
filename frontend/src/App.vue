<template>
  <el-config-provider :locale="elementLocale">
    <el-container style="min-height: 100vh">
      <el-aside :width="collapsed ? '64px' : '220px'" class="app-sidebar">
        <div class="sidebar-header">
          <div v-if="!collapsed" class="logo-text">Data Vault Generator</div>
          <div v-else class="logo-mini">DG</div>
          <el-button
            :icon="collapsed ? Expand : Fold"
            text
            @click="collapsed = !collapsed"
            class="collapse-btn"
          />
        </div>
        <el-menu
          :default-active="route.path"
          :collapse="collapsed"
          router
          class="sidebar-menu"
        >
          <el-menu-item index="/">
            <el-icon><Monitor /></el-icon>
            <template #title>{{ $t('menu.dashboard') }}</template>
          </el-menu-item>
          <el-menu-item index="/connections">
            <el-icon><Connection /></el-icon>
            <template #title>{{ $t('menu.connections') }}</template>
          </el-menu-item>
          <el-menu-item index="/meta-import">
            <el-icon><Upload /></el-icon>
            <template #title>{{ $t('menu.metaImport') }}</template>
          </el-menu-item>
          <el-menu-item index="/meta-config">
            <el-icon><Setting /></el-icon>
            <template #title>{{ $t('menu.metaConfig') }}</template>
          </el-menu-item>
          <el-menu-item index="/dv-config">
            <el-icon><Coin /></el-icon>
            <template #title>{{ $t('menu.dvConfig') }}</template>
          </el-menu-item>
          <el-sub-menu index="/generate">
            <template #title>
              <el-icon><MagicStick /></el-icon>
              <span>{{ $t('menu.generate') }}</span>
            </template>
            <el-menu-item index="/generate/config">{{ $t('menu.generateConfig') }}</el-menu-item>
            <el-menu-item index="/generate/psa">{{ $t('menu.generatePsa') }}</el-menu-item>
            <el-menu-item index="/generate/dv">{{ $t('menu.generateDv') }}</el-menu-item>
          </el-sub-menu>
          <el-menu-item index="/deploy">
            <el-icon><Promotion /></el-icon>
            <template #title>{{ $t('menu.deploy') }}</template>
          </el-menu-item>
          <el-menu-item index="/data-preview">
            <el-icon><Search /></el-icon>
            <template #title>{{ $t('menu.dataPreview') }}</template>
          </el-menu-item>
          <el-menu-item index="/logs">
            <el-icon><Document /></el-icon>
            <template #title>{{ $t('menu.logs') }}</template>
          </el-menu-item>
        </el-menu>
        <div class="sidebar-spacer" />
        <el-menu
          :default-active="route.path"
          :collapse="collapsed"
          router
          class="sidebar-menu sidebar-bottom"
        >
          <el-menu-item index="/intro">
            <el-icon><InfoFilled /></el-icon>
            <template #title>{{ $t('menu.intro') }}</template>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-container>
        <el-header class="app-header">
          <span class="header-title">{{ $t('app.title') }}</span>
          <div class="header-right">
            <span class="header-version">{{ $t('app.version') }}</span>
            <el-dropdown @command="changeLocale" trigger="click">
              <el-button text class="lang-btn">
                🌐 {{ currentLangLabel }}
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="zh-CN">🇨🇳 中文</el-dropdown-item>
                  <el-dropdown-item command="en">🇺🇸 English</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button
              :icon="isDark ? Moon : Sunny"
              text
              @click="toggleTheme"
              class="theme-btn"
            />
          </div>
        </el-header>
        <el-main class="app-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </el-config-provider>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { setLocale } from '@/i18n'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import en from 'element-plus/es/locale/lang/en'
import {
  Monitor, Connection, Upload, Setting,
  MagicStick, Promotion, Document, Search,
  Expand, Fold, Coin, InfoFilled,
  Sunny, Moon,
} from '@element-plus/icons-vue'

const route = useRoute()
const collapsed = ref(false)

// ── 主题切换 ──────────────────────────────────────────────────
const isDark = ref(document.documentElement.classList.contains('dark'))

function toggleTheme() {
  const dark = !isDark.value
  isDark.value = dark
  document.documentElement.classList.toggle('dark', dark)
  localStorage.setItem('theme', dark ? 'dark' : 'light')
}

// ── 语言切换 ──────────────────────────────────────────────────
const { locale } = useI18n()

const elementLocale = computed(() => locale.value === 'zh-CN' ? zhCn : en)
const currentLangLabel = computed(() => locale.value === 'zh-CN' ? '中文' : 'English')

function changeLocale(lang: string) {
  setLocale(lang)
}
</script>

<style scoped>
.app-sidebar {
  background-color: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  transition: width 0.3s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 12px;
  border-bottom: 1px solid var(--el-border-color-light);
  gap: 8px;
}
.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--el-color-primary);
  white-space: nowrap;
}
.logo-mini {
  font-size: 18px;
  font-weight: 700;
  color: var(--el-color-primary);
}
.collapse-btn {
  flex-shrink: 0;
}
.sidebar-menu {
  border-right: none;
}
.sidebar-menu .el-menu-item {
  height: 36px;
  line-height: 36px;
}
.sidebar-menu .el-sub-menu .el-sub-menu__title {
  height: 36px;
  line-height: 36px;
}
.sidebar-spacer {
  flex: 1;
}
.sidebar-bottom {
  border-top: 1px solid var(--el-border-color-light);
}
.app-header {
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.header-title {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-version {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
.theme-btn {
  font-size: 18px;
}
.lang-btn {
  font-size: 13px;
}
.app-main {
  background-color: var(--el-bg-color-page);
  min-height: calc(100vh - 60px);
}
</style>
