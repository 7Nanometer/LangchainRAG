<script setup>
/** 会话侧栏：新建对话 + 历史会话列表（点击切换 / 改名 / 删除） */
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Delete, Edit, Plus } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { formatTime } from '@/utils/format'

const chat = useChatStore()
const router = useRouter()
// 手机端在抽屉里使用时，选中后通知父组件关闭抽屉
const emit = defineEmits(['navigate'])

function goNew() {
  chat.newChat()
  router.push('/chat')
  emit('navigate')
}

function open(id) {
  if (chat.currentId !== id) router.push(`/chat/${id}`)
  emit('navigate')
}

async function onRename(conv) {
  try {
    const { value } = await ElMessageBox.prompt('输入新的会话名称', '重命名会话', {
      inputValue: conv.title,
      inputPattern: /\S/,
      inputErrorMessage: '名称不能为空',
      confirmButtonText: '保存',
      cancelButtonText: '取消',
    })
    await chat.rename(conv.id, value.trim())
  } catch {
    /* 取消 */
  }
}

async function onDelete(conv) {
  try {
    await ElMessageBox.confirm(`确定删除会话「${conv.title}」吗？删除后不再显示。`, '删除会话', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  await chat.remove(conv.id)
}
</script>

<template>
  <aside class="sidebar">
    <div class="side-head">
      <span class="u-label">会话</span>
      <span class="side-count num">{{ chat.conversations.length }}</span>
      <el-button class="new-btn" size="small" :icon="Plus" @click="goNew">新建</el-button>
    </div>

    <div class="conv-list">
      <div
        v-for="conv in chat.conversations"
        :key="conv.id"
        class="conv-item"
        :class="{ active: chat.currentId === conv.id }"
        @click="open(conv.id)"
      >
        <span class="conv-mark" aria-hidden="true" />
        <div class="conv-main">
          <div class="conv-title">{{ conv.title }}</div>
          <div class="conv-time num">{{ formatTime(conv.updated_at) }}</div>
        </div>
        <div class="conv-ops" @click.stop>
          <button class="conv-op" type="button" title="重命名" @click="onRename(conv)">
            <el-icon :size="13"><Edit /></el-icon>
          </button>
          <button class="conv-op danger" type="button" title="删除" @click="onDelete(conv)">
            <el-icon :size="13"><Delete /></el-icon>
          </button>
        </div>
      </div>

      <div v-if="!chat.conversations.length" class="conv-empty">
        还没有历史会话<br />问一个问题，第一张回执就出现在这里
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 252px;
  flex-shrink: 0;
  background: var(--paper);
  border-right: 1px solid var(--rule);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 工具行：会话计数 + 新建 */
.side-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 12px 10px 16px;
  border-bottom: 1px solid var(--rule);
}
.side-count {
  font-size: var(--fs-11);
  color: var(--ink-3);
}
.new-btn {
  margin-left: auto;
}

.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px 0 12px;
}
.conv-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 9px 12px 9px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--rule-2);
  transition: background var(--dur-1) var(--ease);
}
.conv-item:hover {
  background: var(--tint);
}
.conv-item.active {
  background: var(--tint-2);
}
/* 选中标记：一枚小墨块 */
.conv-mark {
  width: 5px;
  height: 5px;
  background: transparent;
  flex-shrink: 0;
  transition: background var(--dur-1) var(--ease);
}
.conv-item.active .conv-mark {
  background: var(--ink);
}
.conv-main {
  flex: 1;
  min-width: 0;
}
.conv-title {
  font-size: var(--fs-13);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--ink-2);
}
.conv-item.active .conv-title,
.conv-item:hover .conv-title {
  color: var(--ink);
}
.conv-item.active .conv-title {
  font-weight: 600;
}
.conv-time {
  font-size: var(--fs-11);
  color: var(--ink-3);
  margin-top: 1px;
}
.conv-ops {
  display: none;
  flex-shrink: 0;
  gap: 2px;
}
.conv-item:hover .conv-ops,
.conv-item.active .conv-ops {
  display: flex;
}
.conv-op {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: none;
  background: transparent;
  border-radius: var(--r-2);
  color: var(--ink-3);
  cursor: pointer;
}
.conv-op:hover {
  background: var(--tint);
  color: var(--ink);
}
.conv-op.danger:hover {
  color: var(--stamp);
}
.conv-empty {
  text-align: center;
  color: var(--ink-3);
  font-size: var(--fs-12);
  margin-top: 48px;
  line-height: 1.9;
}
</style>
