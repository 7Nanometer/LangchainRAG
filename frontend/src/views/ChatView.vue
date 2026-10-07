<script setup>
/**
 * 聊天主页：左侧会话列表 + 中间消息区 + 底部输入框
 * 支持流式打字机效果、引用展示、历史会话找回
 */
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import ConversationSidebar from '@/components/chat/ConversationSidebar.vue'
import MessageItem from '@/components/chat/MessageItem.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import WelcomePanel from '@/components/chat/WelcomePanel.vue'

const route = useRoute()
const router = useRouter()
const chat = useChatStore()
const scrollRef = ref()

// 生成中的"虚拟消息"：复用 MessageItem 渲染打字机效果
const streamingMessage = computed(() => ({
  id: 'streaming',
  role: 'assistant',
  content: chat.streamText,
  citations: chat.streamCitations,
  is_fallback: chat.streamFallback,
}))

onMounted(async () => {
  await chat.loadConversations()
  const id = route.params.id
  if (id) await chat.openConversation(Number(id))
  else chat.newChat()
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
    <ConversationSidebar />

    <div class="chat-main">
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
  max-width: 900px;
  margin: 0 auto;
  padding: 20px 20px 8px;
}
</style>
