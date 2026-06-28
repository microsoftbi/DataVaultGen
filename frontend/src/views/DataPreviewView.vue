<template>
  <div class="data-preview">
    <div class="preview-body">
      <!-- 左侧树 -->
      <div class="tree-panel">
        <div class="tree-header">
          <strong>{{ $t('menu.dataPreview') }}</strong>
        </div>
        <el-tree
          ref="treeRef"
          :data="treeData"
          :props="treeProps"
          node-key="id"
          highlight-current
          :expand-on-click-node="true"
          :filter-node-method="filterNode"
          @node-click="onNodeClick"
          class="preview-tree"
        >
          <template #default="{ node, data }">
            <span class="tree-node-label">
              <el-icon v-if="data.type === 'database'" style="margin-right: 4px; color: var(--el-color-primary);">
                <FolderOpened />
              </el-icon>
              <el-icon v-else-if="data.type === 'category'" style="margin-right: 4px; color: var(--el-text-color-secondary);">
                <Folder />
              </el-icon>
              <el-icon v-else-if="data.type === 'table'" style="margin-right: 4px; color: #409eff;">
                <Grid />
              </el-icon>
              <el-icon v-else-if="data.type === 'view'" style="margin-right: 4px; color: #67c23a;">
                <View />
              </el-icon>
              <el-icon v-else-if="data.type === 'procedure'" style="margin-right: 4px; color: #e6a23c;">
                <Monitor />
              </el-icon>
              <span>{{ data.label }}</span>
            </span>
          </template>
        </el-tree>
      </div>

      <!-- 右侧内容 -->
      <div class="content-panel">
        <div v-if="!selectedObject" class="empty-hint">
          <el-empty :description="$t('dataPreview.selectHint')" />
        </div>

        <template v-else-if="selectedObject.type === 'table' || selectedObject.type === 'view'">
          <!-- 结构 -->
          <el-card shadow="never" class="preview-card">
            <template #header>
              <span class="card-title">{{ $t('dataPreview.structure') }}: {{ selectedObject.fullName }}</span>
            </template>
            <el-table
              :data="structureData"
              v-loading="structureLoading"
              border
              stripe
              size="small"
              max-height="260"
              style="width: 100%"
            >
              <el-table-column prop="column_name" :label="$t('dataPreview.columnName')" min-width="160" />
              <el-table-column prop="display_type" :label="$t('dataPreview.dataType')" width="160" />
              <el-table-column prop="is_nullable" :label="$t('dataPreview.nullable')" width="80" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.is_nullable === 'YES' ? 'info' : 'danger'" size="small">
                    {{ row.is_nullable === 'YES' ? 'YES' : 'NO' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <!-- 数据 -->
          <el-card shadow="never" class="preview-card">
            <template #header>
              <div class="card-header">
                <span class="card-title">{{ $t('dataPreview.dataPreview') }}: {{ selectedObject.fullName }} ({{ $t('dataPreview.topN', { n: dataTotal }) }})</span>
                <el-button size="small" :loading="dataLoading" @click="loadData">{{ $t('dataPreview.refresh') }}</el-button>
              </div>
            </template>
            <el-table
              :data="dataRows"
              v-loading="dataLoading"
              border
              stripe
              size="small"
              max-height="420"
              style="width: 100%"
              :scrollbar-always-on="true"
            >
              <el-table-column
                v-for="col in dataColumns"
                :key="col"
                :prop="col"
                :label="col"
                min-width="120"
                show-overflow-tooltip
              />
            </el-table>
          </el-card>
        </template>

        <div v-else-if="selectedObject.type === 'procedure'" class="empty-hint">
          <el-empty :description="$t('dataPreview.procedureHint')" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { FolderOpened, Folder, Grid, View, Monitor } from '@element-plus/icons-vue'
import * as api from '@/api'

const { t } = useI18n()

// ── 树 ──────────────────────────────────────────────────────────
const treeRef = ref<any>(null)
const treeData = ref<any[]>([])
const treeProps = {
  children: 'children',
  label: 'label',
}

interface TreeNode {
  id: string
  label: string
  type: 'database' | 'category' | 'table' | 'view' | 'procedure'
  children?: TreeNode[]
  fullName?: string
  connId?: number
  dbName?: string
  schema?: string
  objectName?: string
}

// ── 选中对象 ────────────────────────────────────────────────────
const selectedObject = ref<TreeNode | null>(null)

// ── 结构 ────────────────────────────────────────────────────────
const structureLoading = ref(false)
const structureData = ref<any[]>([])

// ── 数据 ────────────────────────────────────────────────────────
const dataLoading = ref(false)
const dataColumns = ref<string[]>([])
const dataRows = ref<any[][]>([])
const dataTotal = ref(0)

// ── 初始化 ──────────────────────────────────────────────────────
onMounted(() => loadTree())

async function loadTree() {
  try {
    // 1. 获取数据库信息
    const dbRes = await api.getPreviewDatabases()
    const dbData = (dbRes.data as any).data
    if (!dbData) return

    // 2. 并行获取每个库的对象列表
    const nodes: TreeNode[] = []
    for (const [key, label] of [['oltp', 'OLTP'], ['stage', 'STAGE'], ['core', 'CORE']]) {
      const info = dbData[key]
      if (!info) {
        nodes.push({ id: key, label, type: 'database', children: [
          { id: `${key}-empty`, label: t('dataPreview.notConfigured'), type: 'category' as const },
        ]})
        continue
      }

      const objRes: any = await api.getPreviewObjects(info.conn_id, info.database_name)
      const objs = objRes.data || {}

      const dbNode: TreeNode = {
        id: key,
        label: `${label} (${info.database_name})`,
        type: 'database',
        children: [],
        connId: info.conn_id,
        dbName: info.database_name,
      }

      // Tables
      if (objs.tables?.length) {
        const tableChildren: TreeNode[] = objs.tables.map((t: string) => {
          const parts = t.split('.')
          return {
            id: `${key}-tbl-${t}`,
            label: t,
            type: 'table',
            fullName: t,
            connId: info.conn_id,
            dbName: info.database_name,
            schema: parts[0],
            objectName: parts[1],
          }
        })
        dbNode.children!.push({ id: `${key}-tables`, label: `Tables (${tableChildren.length})`, type: 'category', children: tableChildren })
      }

      // Views
      if (objs.views?.length) {
        const viewChildren: TreeNode[] = objs.views.map((t: string) => {
          const parts = t.split('.')
          return {
            id: `${key}-vw-${t}`,
            label: t,
            type: 'view',
            fullName: t,
            connId: info.conn_id,
            dbName: info.database_name,
            schema: parts[0],
            objectName: parts[1],
          }
        })
        dbNode.children!.push({ id: `${key}-views`, label: `Views (${viewChildren.length})`, type: 'category', children: viewChildren })
      }

      // Procedures
      if (objs.procedures?.length) {
        const procChildren: TreeNode[] = objs.procedures.map((t: string) => {
          const parts = t.split('.')
          return {
            id: `${key}-usp-${t}`,
            label: t,
            type: 'procedure',
            fullName: t,
            connId: info.conn_id,
            dbName: info.database_name,
            schema: parts[0],
            objectName: parts[1],
          }
        })
        dbNode.children!.push({ id: `${key}-procs`, label: `Procedures (${procChildren.length})`, type: 'category', children: procChildren })
      }

      nodes.push(dbNode)
    }

    treeData.value = nodes
  } catch (e: any) {
    ElMessage.error(t('dataPreview.loadFailed'))
  }
}

function filterNode(value: string, data: any) {
  if (!value) return true
  return data.label?.toLowerCase().includes(value.toLowerCase())
}

// ── 节点点击 ──────────────────────────────────────────────────
async function onNodeClick(data: TreeNode) {
  if (data.type === 'table' || data.type === 'view') {
    selectedObject.value = data
    await Promise.all([
      loadStructure(data),
      loadData(data),
    ])
  } else if (data.type === 'procedure') {
    selectedObject.value = data
    structureData.value = []
    dataColumns.value = []
    dataRows.value = []
  }
}

async function loadStructure(node: TreeNode) {
  structureLoading.value = true
  try {
    const res = await api.getPreviewColumns(node.connId!, node.dbName!, node.schema!, node.objectName!)
    const data = res.data as any
    structureData.value = data.columns || []
  } catch (e: any) {
    ElMessage.error(t('dataPreview.loadStructFailed'))
    structureData.value = []
  } finally {
    structureLoading.value = false
  }
}

async function loadData(node?: TreeNode) {
  const n = node || selectedObject.value
  if (!n || (n.type !== 'table' && n.type !== 'view')) return
  dataLoading.value = true
  try {
    const res = await api.getPreviewData(n.connId!, n.dbName!, n.schema!, n.objectName!)
    const data = res.data as any
    dataColumns.value = data.columns || []
    dataRows.value = data.rows || []
    dataTotal.value = data.total || 0
  } catch (e: any) {
    ElMessage.error(t('dataPreview.loadDataFailed'))
    dataColumns.value = []
    dataRows.value = []
    dataTotal.value = 0
  } finally {
    dataLoading.value = false
  }
}
</script>

<style scoped>
.data-preview {
  padding: 0;
  height: calc(100vh - 60px - 32px);
}
.preview-body {
  display: flex;
  height: 100%;
  gap: 16px;
}
.tree-panel {
  width: 280px;
  flex-shrink: 0;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--el-bg-color);
  overflow-y: auto;
}
.tree-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-light);
  font-size: 14px;
}
.preview-tree {
  padding: 8px 0;
}
.tree-node-label {
  display: flex;
  align-items: center;
  font-size: 13px;
}
.content-panel {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.empty-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
.preview-card {
  border-radius: 8px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title {
  font-size: 14px;
  font-weight: 600;
}
</style>