<script setup>
/**
 * 聊天主页：左侧会话列表 + 中间消息区 + 底部输入框
 * 桌面端侧栏常显；手机端（<768px）侧栏收进抽屉，由顶部按钮唤出
 */
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Menu as MenuIcon } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import ConversationSidebar from '@/components/chat/ConversationSidebar.vue'
import MessageItem from '@/components/chat/MessageItem.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import WelcomePanel from '@/components/chat/WelcomePanel.vue'
import NanoLogo from '@/components/common/NanoLogo.vue'

const route = useRoute()
const router = useRouter()
const chat = useChatStore()
const scrollRef = ref()

// ---------- 手机端适配 ----------
const isMobile = ref(window.innerWidth < 768)
const drawerVisible = ref(false)

function onResize() {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) drawerVisible.value = false
}

// 生成中的"虚拟消息"：复用 MessageItem 渲染打字机效果
const streamingMessage = computed(() => ({
  id: 'streaming',
  role: 'assistant',
  content: chat.streamText,
  citations: chat.streamCitations,
  is_fallback: chat.streamFallback,
  from_cache: chat.streamFromCache,
  retrieval: chat.streamRetrieval,
}))

onMounted(async () => {
  window.addEventListener('resize', onResize)
  await chat.loadConversations()
  const id = route.params.id
  if (id) await chat.openConversation(Number(id))
  else chat.newChat()
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})

// URL → 状态（用户在侧栏点会话、或直接输网址时）
watch(
  () => route.params.id,
  async (id) => {
    const numId = id ? Number(id) : null
    if (numId !== chat.currentId) {
      if (numId) await chat.openConversation(numId)
      else chat.newChat()
    }
  },
)

// 状态 → URL（首次提问自动建会话后，地址栏跟上）
watch(
  () => chat.currentId,
  (id) => {
    const target = id ? `/chat/${id}` : '/chat'
    if (route.name === 'chat' && route.path !== target) router.replace(target)
  },
)

// 自动滚动到底部
function scrollToBottom() {
  nextTick(() => {
    const el = scrollRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}
watch(() => chat.messages.length, scrollToBottom)
watch(() => chat.streamText, scrollToBottom)
</script>

<template>
  <div class="chat-page">
    <!-- 桌面端：侧栏常显 -->
    <ConversationSidebar v-if="!isMobile" />

    <!-- 手机端：侧栏放进抽屉 -->
    <el-drawer
      v-if="isMobile"
      v-model="drawerVisible"
      direction="ltr"
      size="272px"
      :with-header="false"
      class="conv-drawer"
    >
      <ConversationSidebar @navigate="drawerVisible = false" />
    </el-drawer>

    <div class="chat-main">
      <!-- 手机端顶部细栏 -->
      <div v-if="isMobile" class="mobile-bar">
        <el-button text :icon="MenuIcon" @click="drawerVisible = true">会话</el-button>
        <NanoLogo :size="15" :name-size="12.5" />
        <span class="mobile-spacer" />
      </div>

      <div ref="scrollRef" class="messages-area">
        <WelcomePanel v-if="chat.isEmpty" @ask="chat.send" />
        <div v-else class="messages-inner">
          <MessageItem v-for="m in chat.messages" :key="m.id" :message="m" />
          <MessageItem v-if="chat.streaming" :message="streamingMessage" streaming />
        </div>
      </div>

      <ChatInput :streaming="chat.streaming" @send="chat.send" @stop="chat.stop" />
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  height: 100%;
  display: flex;
  min-height: 0;
  background: var(--paper);
}
.chat-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.messages-area {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}
.messages-inner {
  max-width: 820px;
  margin: 0 auto;
  padding: 26px 28px 16px;
}
.mobile-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-bottom: 1px solid var(--rule);
  background: var(--paper);
  flex-shrink: 0;
}
.mobile-spacer {
  flex: 1;
}
</style>

<style>
/* 抽屉里的侧栏撑满（el-drawer 渲染到 body，需全局样式） */
.conv-drawer .el-drawer__body {
  padding: 0;
}
.conv-drawer .sidebar {
  width: 100%;
  border-right: none;
}
</style>
