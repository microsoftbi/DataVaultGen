<template>
  <el-container style="min-height: 100vh">
    <el-aside :width="collapsed ? '64px' : '220px'" class="app-sidebar">
      <div class="sidebar-header">
        <div v-if="!collapsed" class="logo-text">DWH Generator</div>
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
          <template #title>仪表盘</template>
        </el-menu-item>
        <el-menu-item index="/connections">
          <el-icon><Connection /></el-icon>
          <template #title>数据库连接</template>
        </el-menu-item>
        <el-menu-item index="/meta-import">
          <el-icon><Upload /></el-icon>
          <template #title>元数据导入</template>
        </el-menu-item>
        <el-menu-item index="/meta-config">
          <el-icon><Setting /></el-icon>
          <template #title>字段配置</template>
        </el-menu-item>
        <el-menu-item index="/dv-config">
          <el-icon><Coin /></el-icon>
          <template #title>DV 配置</template>
        </el-menu-item>
        <el-sub-menu index="/generate">
          <template #title>
            <el-icon><MagicStick /></el-icon>
            <span>代码生成</span>
          </template>
          <el-menu-item index="/generate/config">配置摘要</el-menu-item>
          <el-menu-item index="/generate/psa">PSA Type 2</el-menu-item>
          <el-menu-item index="/generate/dv">Data Vault 2.0</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/deploy">
          <el-icon><Promotion /></el-icon>
          <template #title>部署执行</template>
        </el-menu-item>
        <el-menu-item index="/logs">
          <el-icon><Document /></el-icon>
          <template #title>执行日志</template>
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
          <template #title>系统介绍</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <span class="header-title">DWH-Generator · PSA + Data Vault 2.0</span>
        <div class="header-right">
          <span class="header-version">v1.0</span>
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
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  Monitor, Connection, Upload, Setting,
  MagicStick, Promotion, Document,
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
.app-main {
  background-color: var(--el-bg-color-page);
  min-height: calc(100vh - 60px);
}
</style>