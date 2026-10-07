<script setup>
/**
 * 文档管理页（仅管理员）
 * 功能：拖拽批量上传商品资料 → 实时看处理进度 → 失败重试 / 重建索引 / 删除
 *
 * 处理进度通过"轮询"实现：只要有文件还在排队/处理中，
 * 页面就每 2.5 秒自动刷新一次状态（处理完自动停止）。
 */
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Delete, Refresh, UploadFilled } from '@element-plus/icons-vue'
import { deleteDocument, listDocuments, reindexDocument, uploadDocuments } from '@/api/admin'
import { formatSize, formatTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const kbId = Number(route.params.id)

const loading = ref(false)
const uploading = ref(false)
const docs = ref([])
const pendingFiles = ref([])
const uploadRef = ref()
let pollTimer = null

const statusMap = {
  pending: { text: '排队中', type: 'info' },
  processing: { text: '处理中', type: 'primary' },
  ready: { text: '已完成', type: 'success' },
  failed: { text: '失败', type: 'danger' },
}

async function load() {
  loading.value = true
  try {
    docs.value = await listDocuments(kbId)
    updatePolling()
  } finally {
    loading.value = false
  }
}

async function loadQuiet() {
  try {
    docs.value = await listDocuments(kbId)
    updatePolling()
  } catch {
    /* 轮询失败静默处理，下次重试 */
  }
}

function updatePolling() {
  const hasActive = docs.value.some((d) => ['pending', 'processing'].includes(d.status))
  if (hasActive && !pollTimer) {
    pollTimer = setInterval(loadQuiet, 2500)
  } else if (!hasActive && pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// ---------- 上传 ----------
function onFileChange(_file, fileList) {
  pendingFiles.value = fileList
}
function onFileRemove(_file, fileList) {
  pendingFiles.value = fileList
}

async function startUpload() {
  if (!pendingFiles.value.length) {
    ElMessage.warning('请先选择要上传的文件')
    return
  }
  const fd = new FormData()
  for (const f of pendingFiles.value) {
    fd.append('files', f.raw)
  }
  uploading.value = true
  try {
    const res = await uploadDocuments(kbId, fd)
    if (res.saved.length) {
      ElMessage.success(`已接收 ${res.saved.length} 份文件，后台正在自动处理`)
    }
    for (const err of res.errors) {
      ElMessage.error(err)
    }
    pendingFiles.value = []
    uploadRef.value?.clearFiles()
    load()
  } catch {
    /* 错误提示已统一处理 */
  } finally {
    uploading.value = false
  }
}

// ---------- 行操作 ----------
async function onReindex(doc) {
  await reindexDocument(doc.id)
  ElMessage.success(`「${doc.filename}」已加入重建队列`)
  load()
}

async function onDelete(doc) {
  try {
    await ElMessageBox.confirm(
      `确定删除「${doc.filename}」吗？该文件及其全部知识片段会被清除，不可恢复。`,
      '删除确认',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }
  await deleteDocument(doc.id)
  ElMessage.success('已删除')
  load()
}

function progressPercent(doc) {
  if (!doc.chunk_count) return 0
  return Math.min(100, Math.round((doc.processed_chunks / doc.chunk_count) * 100))
}

onMounted(load)
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div>
    <div class="page-head">
      <div class="head-left">
        <el-button text :icon="ArrowLeft" @click="router.push('/admin/kb')">返回</el-button>
        <h2 class="page-title">知识库资料管理</h2>
      </div>
      <el-button :icon="Refresh" @click="load">刷新状态</el-button>
    </div>

    <!-- 上传区 -->
    <div class="upload-card">
      <el-upload
        ref="uploadRef"
        drag
        multiple
        :auto-upload="false"
        accept=".pdf,.docx,.xlsx,.csv,.txt,.md"
        :on-change="onFileChange"
        :on-remove="onFileRemove"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">
          把商品资料拖到这里，或 <em>点击选择文件</em>
        </div>
        <div class="upload-hint">
          支持 PDF / Word / Excel / CSV / TXT / Markdown，可一次选多个文件（单个不超过 50MB）
        </div>
      </el-upload>
      <div class="upload-actions">
        <span class="upload-count">
          {{ pendingFiles.length ? `已选择 ${pendingFiles.length} 个文件` : '尚未选择文件' }}
        </span>
        <el-button
          type="primary"
          :disabled="!pendingFiles.length"
          :loading="uploading"
          @click="startUpload"
        >
          开始上传并处理
        </el-button>
      </div>
    </div>

    <!-- 文档列表 -->
    <el-table v-loading="loading" :data="docs" style="width: 100%" row-key="id">
      <el-table-column prop="filename" label="文件名" min-width="220" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="doc-name">{{ row.filename }}</span>
          <el-tag size="small" effect="plain" class="type-tag">{{ row.file_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="大小" width="90">
        <template #default="{ row }">{{ formatSize(row.size_bytes) }}</template>
      </el-table-column>
      <el-table-column label="处理状态" width="230">
        <template #default="{ row }">
          <el-tooltip
            :content="row.error_msg || '处理完成'"
            :disabled="row.status !== 'failed'"
            placement="top"
          >
            <el-tag :type="statusMap[row.status]?.type || 'info'" effect="light">
              {{ statusMap[row.status]?.text || row.status }}
            </el-tag>
          </el-tooltip>
          <el-progress
            v-if="row.status === 'processing'"
            :percentage="progressPercent(row)"
            :stroke-width="6"
            style="margin-top: 6px; max-width: 180px"
          />
        </template>
      </el-table-column>
      <el-table-column label="知识片段" width="100">
        <template #default="{ row }">
          <span v-if="row.status === 'ready'">{{ row.chunk_count }} 段</span>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column label="上传时间" width="150">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <el-button
            size="small"
            text
            :icon="Refresh"
            :disabled="['pending', 'processing'].includes(row.status)"
            @click="onReindex(row)"
          >
            重建
          </el-button>
          <el-button
            size="small"
            text
            type="danger"
            :icon="Delete"
            :disabled="['processing'].includes(row.status)"
            @click="onDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="还没有资料，把商品文档拖到上方上传框即可" />
      </template>
    </el-table>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.head-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.page-title {
  margin: 0;
  font-size: 18px;
}
.upload-card {
  background: var(--panel-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}
.upload-icon {
  font-size: 42px;
  color: var(--brand);
}
.upload-text {
  font-size: 14px;
  margin-top: 6px;
}
.upload-text em {
  color: var(--brand);
  font-style: normal;
}
.upload-hint {
  font-size: 12px;
  color: var(--text-second);
  margin-top: 4px;
}
.upload-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}
.upload-count {
  font-size: 13px;
  color: var(--text-second);
}
.doc-name {
  margin-right: 6px;
}
.type-tag {
  text-transform: uppercase;
}
.muted {
  color: var(--text-second);
}
</style>
