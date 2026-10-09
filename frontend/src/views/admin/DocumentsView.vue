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
import { ArrowLeft, Refresh } from '@element-plus/icons-vue'
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
  pending: { text: '排队中' },
  processing: { text: '处理中' },
  ready: { text: '已完成' },
  failed: { text: '失败' },
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
        <button class="back-link" type="button" @click="router.push('/admin/kb')">
          <el-icon :size="13"><ArrowLeft /></el-icon>
          <span>知识库</span>
        </button>
        <div>
          <h2 class="page-title">资料管理</h2>
          <p class="page-sub">上传 → 解析 → 分块 → 建立索引，全流程可追踪</p>
        </div>
      </div>
      <el-button :icon="Refresh" @click="load">刷新状态</el-button>
    </div>

    <!-- 上传区 -->
    <div class="upload-panel">
      <el-upload
        ref="uploadRef"
        drag
        multiple
        :auto-upload="false"
        accept=".pdf,.docx,.xlsx,.csv,.txt,.md"
        :on-change="onFileChange"
        :on-remove="onFileRemove"
      >
        <svg
          class="upload-icon"
          width="30"
          height="30"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M12 3v10" />
          <path d="M8 9l4 4 4-4" />
          <path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
        </svg>
        <div class="upload-text">把商品资料拖到这里，或 <em>点击选择文件</em></div>
        <div class="upload-hint">
          支持 PDF / Word / Excel / CSV / TXT / Markdown，可一次选多个文件（单个不超过 50MB）
        </div>
      </el-upload>
      <div class="upload-actions">
        <span class="upload-count num">
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
          <span class="type-chip num">{{ row.file_type }}</span>
        </template>
      </el-table-column>
      <el-table-column label="大小" width="90">
        <template #default="{ row }">
          <span class="num">{{ formatSize(row.size_bytes) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="处理状态" width="230">
        <template #default="{ row }">
          <el-tooltip
            :content="row.error_msg || '处理完成'"
            :disabled="row.status !== 'failed'"
            placement="top"
          >
            <span class="st" :class="row.status">
              <i class="st-block" />
              {{ statusMap[row.status]?.text || row.status }}
            </span>
          </el-tooltip>
          <el-progress
            v-if="row.status === 'processing'"
            :percentage="progressPercent(row)"
            :stroke-width="2"
            :show-text="false"
            style="margin-top: 7px; max-width: 170px"
          />
        </template>
      </el-table-column>
      <el-table-column label="知识片段" width="100">
        <template #default="{ row }">
          <span v-if="row.status === 'ready'" class="num">{{ row.chunk_count }} 段</span>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column label="上传时间" width="150">
        <template #default="{ row }">
          <span class="num time-cell">{{ formatTime(row.created_at) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <button
            class="row-op"
            type="button"
            :disabled="['pending', 'processing'].includes(row.status)"
            @click="onReindex(row)"
          >
            重建
          </button>
          <button
            class="row-op danger"
            type="button"
            :disabled="row.status === 'processing'"
            @click="onDelete(row)"
          >
            删除
          </button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="还没有资料，把商品文档拖到上方上传框即可" />
      </template>
    </el-table>
  </div>
</template>

<style scoped>
.head-left {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}
.back-link {
  display: flex;
  align-items: center;
  gap: 5px;
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: var(--fs-12);
  color: var(--ink-3);
  cursor: pointer;
  padding: 4px 8px;
  margin-top: 3px;
  border-radius: var(--r-1);
  transition: color var(--dur-1) var(--ease), background var(--dur-1) var(--ease);
}
.back-link:hover {
  color: var(--ink);
  background: var(--tint);
}

.upload-panel {
  background: var(--panel);
  border: 1px solid var(--rule);
  border-radius: var(--r-1);
  padding: 14px;
  margin-bottom: var(--sp-4);
}
.upload-icon {
  color: var(--ink-3);
}
.upload-text {
  font-size: var(--fs-13);
  margin-top: 8px;
  color: var(--ink);
}
.upload-text em {
  color: var(--ink);
  font-style: normal;
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-thickness: 1px;
}
.upload-hint {
  font-size: var(--fs-12);
  color: var(--ink-3);
  margin-top: 4px;
}
.upload-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid var(--rule-2);
  padding-top: 12px;
  margin-top: 6px;
}
.upload-count {
  font-size: var(--fs-12);
  color: var(--ink-3);
}

.doc-name {
  margin-right: 8px;
}
.type-chip {
  font-size: var(--fs-11);
  color: var(--ink-3);
  border: 1px solid var(--rule);
  border-radius: var(--r-2);
  padding: 0 5px;
}

/* 状态：小方块 + 文字（方块颜色=状态语言） */
.st {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-12);
  color: var(--ink-2);
}
.st-block {
  width: 7px;
  height: 7px;
  border-radius: 1px;
  background: var(--ink-3);
}
.st.pending .st-block {
  background: transparent;
  border: 1px solid var(--ink-3);
}
.st.processing .st-block {
  background: var(--ink);
  animation: pulse-ink 1.1s ease-in-out infinite;
}
.st.ready .st-block {
  background: var(--ok);
}
.st.failed .st-block {
  background: var(--stamp);
}
.st.failed {
  color: var(--stamp);
}

.time-cell {
  font-size: var(--fs-12);
  color: var(--ink-2);
}

.row-op {
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: var(--fs-12);
  color: var(--ink-3);
  padding: 3px 8px;
  border-radius: var(--r-2);
  cursor: pointer;
  transition: color var(--dur-1) var(--ease), background var(--dur-1) var(--ease);
}
.row-op:hover:not(:disabled) {
  color: var(--ink);
  background: var(--tint);
}
.row-op.danger:hover:not(:disabled) {
  color: var(--stamp);
}
.row-op:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
