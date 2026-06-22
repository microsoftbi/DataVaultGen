<template>
  <div class="dashboard-container">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <h1 class="welcome-title">DWH-Generator 管理中心</h1>
      <p class="welcome-desc">
        数据仓库自动化生成平台，帮助您快速完成从数据源接入到目标部署的全流程。
      </p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-inner">
            <div class="stat-icon icon-connections">
              <el-icon :size="36"><Connection /></el-icon>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ stats.connections }}</span>
              <span class="stat-label">已配置连接</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-inner">
            <div class="stat-icon icon-fields">
              <el-icon :size="36"><List /></el-icon>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ stats.fields }}</span>
              <span class="stat-label">已导入字段</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-inner">
            <div class="stat-icon icon-pending">
              <el-icon :size="36"><Files /></el-icon>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ stats.pending }}</span>
              <span class="stat-label">待生成对象</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-inner">
            <div class="stat-icon icon-status">
              <el-icon :size="36"><Monitor /></el-icon>
            </div>
            <div class="stat-info">
              <span class="stat-label">系统状态</span>
              <el-tag
                :type="systemStatus === '正常运行' ? 'success' : 'danger'"
                size="large"
                class="status-tag"
              >
                {{ systemStatus }}
              </el-tag>
              <span v-if="healthInfo" class="stat-sub">
                {{ healthInfo.app }} v{{ healthInfo.version }}
              </span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快速入门指南 -->
    <el-card shadow="never" class="guide-card">
      <template #header>
        <div class="guide-header">
          <el-icon :size="22"><Guide /></el-icon>
          <span>快速入门指南</span>
        </div>
      </template>

      <el-steps :active="-1" direction="vertical" class="guide-steps">
        <el-step
          v-for="(step, index) in steps"
          :key="index"
          :title="step.title"
          :description="step.desc"
          :status="index === 0 ? 'process' : 'wait'"
          class="guide-step"
        />
      </el-steps>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { Connection, List, Files, Monitor, Guide } from '@element-plus/icons-vue'
import {
  listConnections,
  listAttributes,
  listObjects,
  healthCheck,
} from '@/api'

interface Stats {
  connections: number
  fields: number
  pending: number
}

interface HealthInfo {
  status: string
  app: string
  version: string
}

interface Step {
  title: string
  desc: string
}

const stats = reactive<Stats>({
  connections: 0,
  fields: 0,
  pending: 0,
})

const systemStatus = ref<string>('加载中...')
const healthInfo = ref<HealthInfo | null>(null)

const steps: Step[] = [
  {
    title: '配置数据源连接',
    desc: '添加源数据库和元数据库的连接信息，支持多种数据库类型。',
  },
  {
    title: '导入元数据',
    desc: '选择源数据表，将表结构及字段信息导入到元数据库中。',
  },
  {
    title: '标记字段属性',
    desc: '为字段标记业务主键 (BK)、物理主键 (PK) 和脱敏字段 (DI)。',
  },
  {
    title: '配置生成对象',
    desc: '选择需要生成代码的数据对象，并配置全量加载或增量同步。',
  },
  {
    title: '生成代码',
    desc: '一键生成 PSA 分层所需的存储过程、视图和执行流脚本。',
  },
  {
    title: '部署执行',
    desc: '将生成的 SQL 脚本部署到目标数据库中执行，完成数据同步。',
  },
]

onMounted(async () => {
  try {
    const [connRes, attrRes, objRes, healthRes] = await Promise.all([
      listConnections(),
      listAttributes(),
      listObjects(),
      healthCheck(),
    ])

    stats.connections = connRes.data.length
    stats.fields = attrRes.data.length
    stats.pending = objRes.data.filter((o) => o.is_gen).length

    const h = healthRes.data
    systemStatus.value = h.status === 'ok' ? '正常运行' : '异常'
    healthInfo.value = { status: h.status, app: h.app, version: h.version }
  } catch {
    systemStatus.value = '无法连接'
    healthInfo.value = null
  }
})
</script>

<style scoped>
.dashboard-container {
  padding: 0;
}

.welcome-section {
  margin-bottom: 28px;
}

.welcome-title {
  margin: 0 0 8px;
  font-size: 26px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.welcome-desc {
  margin: 0;
  font-size: 15px;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}

/* ── 统计卡片 ── */

.stats-row {
  margin-bottom: 28px;
}

.stat-card {
  border-radius: 12px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-inner {
  display: flex;
  align-items: center;
  gap: 18px;
}

.stat-icon {
  flex-shrink: 0;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.icon-connections {
  background: linear-gradient(135deg, #ecf5ff 0%, #d9ecff 100%);
  color: #409eff;
}

.icon-fields {
  background: linear-gradient(135deg, #f0f9eb 0%, #e1f3d8 100%);
  color: #67c23a;
}

.icon-pending {
  background: linear-gradient(135deg, #fdf6ec 0%, #faecd8 100%);
  color: #e6a23c;
}

.icon-status {
  background: linear-gradient(135deg, #f0f0f0 0%, #e8e8e8 100%);
  color: #909399;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 30px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--el-text-color-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 2px;
}

.stat-sub {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-top: 2px;
}

.status-tag {
  margin-top: 4px;
  align-self: flex-start;
}

/* ── 快速入门指南 ── */

.guide-card {
  border-radius: 12px;
}

.guide-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.guide-steps {
  padding: 8px 0;
}

.guide-step {
  margin-bottom: 4px;
}

.guide-step :deep(.el-step__title) {
  font-size: 15px;
}

.guide-step :deep(.el-step__description) {
  font-size: 13px;
  line-height: 1.5;
  padding-right: 20px;
}
</style>