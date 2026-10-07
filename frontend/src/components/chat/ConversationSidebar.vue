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
    <el-button class="new-btn" type="primary" :icon="Plus" @click="goNew">新建对话</el-button>

    <div class="conv-list">
      <div
        v-for="conv in chat.conversations"
        :key="conv.id"
        class="conv-item"
        :class="{ active: chat.currentId === conv.id }"
        @click="open(conv.id)"
      >
        <div class="conv-main">
          <div class="conv-title">{{ conv.title }}</div>
          <div class="conv-time">{{ formatTime(conv.updated_at) }}</div>
        </div>
        <div class="conv-ops" @click.stop>
          <el-button text size="small" :icon="Edit" title="重命名" @click="onRename(conv)" />
          <el-button
            text
            size="small"
            type="danger"
            :icon="Delete"
            title="删除"
            @click="onDelete(conv)"
          />
        </div>
      </div>

      <div v-if="!chat.conversations.length" class="conv-empty">
        还没有历史对话<br />问一个问题就开始吧
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.new-btn {
  margin: 12px;
}
.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 12px;
}
.conv-item {
  display: flex;
  align-items: center;
  padding: 10px 10px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 2px;
}
.conv-item:hover {
  background: rgba(128, 128, 128, 0.1);
}
.conv-item.active {
  background: rgba(37, 99, 235, 0.12);
}
.conv-main {
  flex: 1;
  min-width: 0;
}
.conv-title {
  font-size: 13.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.conv-time {
  font-size: 11px;
  color: var(--text-second);
  margin-top: 2px;
}
.conv-ops {
  display: none;
  flex-shrink: 0;
}
.conv-item:hover .conv-ops {
  display: block;
}
.conv-empty {
  text-align: center;
  color: var(--text-second);
  font-size: 12.5px;
  margin-top: 40px;
  line-height: 1.8;
}
</style>
