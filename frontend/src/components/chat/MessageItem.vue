<script setup>
/** 单条消息：用户气泡 / AI 回答（Markdown + 引用 + 赞踩 + 复制） */
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument, Service } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { renderMarkdown } from '@/utils/markdown'
import CitationList from './CitationList.vue'

const props = defineProps({
  message: { type: Object, required: true },
  streaming: { type: Boolean, default: false },
})

const chat = useChatStore()
const isUser = computed(() => props.message.role === 'user')
const html = computed(() => renderMarkdown(props.message.content))

async function onCopy() {
  try {
    await navigator.clipboard.writeText(props.message.content)
    ElMessage.success('已复制回答')
  } catch {
    ElMessage.warning('复制失败，请手动选择文字复制')
  }
}

function onLike() {
  if (props.streaming || typeof props.message.id !== 'number') return
  chat.feedback(props.message.id, 'like')
}
function onDislike() {
  if (props.streaming || typeof props.message.id !== 'number') return
  chat.feedback(props.message.id, 'dislike')
}
</script>

<template>
  <div class="msg-row" :class="isUser ? 'is-user' : 'is-ai'">
    <div v-if="!isUser" class="ai-avatar">
      <el-icon :size="16"><Service /></el-icon>
    </div>

    <div class="msg-body">
      <!-- 用户消息：纯文本气泡 -->
      <div v-if="isUser" class="bubble user-bubble">{{ message.content }}</div>

      <!-- AI 消息：Markdown 渲染 -->
      <div v-else class="bubble ai-bubble">
        <div v-if="message.from_cache" class="cache-badge">⚡ 来自缓存（秒回）</div>
        <div v-if="!message.content" class="thinking">
          <span class="dot" /><span class="dot" /><span class="dot" /> 正在查找资料…
        </div>
        <div v-else class="md-body" v-html="html" />
        <span v-if="streaming && message.content" class="cursor">▍</span>

        <div v-if="!streaming && message.is_fallback" class="fallback-tip">
          （本次回答为兜底回答：知识库中未找到相关资料）
        </div>

        <CitationList v-if="!streaming" :citations="message.citations || []" />

        <!-- 操作条（流式生成时隐藏） -->
        <div v-if="!streaming && message.content" class="msg-ops">
          <el-button
            text
            size="small"
            :type="message.feedback === 'like' ? 'primary' : ''"
            @click="onLike"
          >
            👍 有用
          </el-button>
          <el-button
            text
            size="small"
            :type="message.feedback === 'dislike' ? 'danger' : ''"
            @click="onDislike"
          >
            👎 没用
          </el-button>
          <el-button text size="small" :icon="CopyDocument" @click="onCopy">复制</el-button>
          <span v-if="message.latency_ms" class="latency">
            {{ (message.latency_ms / 1000).toFixed(1) }}s
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.msg-row {
  display: flex;
  gap: 10px;
  margin-bottom: 18px;
}
.msg-row.is-user {
  justify-content: flex-end;
}
.ai-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--brand);
  color: #fff;
}
.msg-body {
  max-width: min(760px, 82%);
}
.bubble {
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.75;
  word-break: break-word;
}
.user-bubble {
  background: var(--brand);
  color: #fff;
  border-top-right-radius: 4px;
  white-space: pre-wrap;
}
.ai-bubble {
  background: var(--panel-bg);
  border: 1px solid var(--border-color);
  border-top-left-radius: 4px;
}
.md-body :deep(p) {
  margin: 0 0 8px;
}
.md-body :deep(p:last-child) {
  margin-bottom: 0;
}
.md-body :deep(ul),
.md-body :deep(ol) {
  margin: 4px 0 8px;
  padding-left: 22px;
}
.md-body :deep(code) {
  background: rgba(128, 128, 128, 0.12);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 13px;
}
.md-body :deep(pre) {
  background: rgba(0, 0, 0, 0.06);
  padding: 10px;
  border-radius: 8px;
  overflow-x: auto;
}
.cache-badge {
  display: inline-block;
  font-size: 11.5px;
  color: #d97706;
  background: rgba(217, 119, 6, 0.12);
  padding: 2px 8px;
  border-radius: 6px;
  margin-bottom: 8px;
}
.md-body :deep(.cite-ref) {
  display: inline-block;
  min-width: 16px;
  height: 16px;
  line-height: 16px;
  text-align: center;
  font-size: 10.5px;
  color: #fff;
  background: var(--brand);
  border-radius: 4px;
  padding: 0 3px;
  margin: 0 2px;
  vertical-align: super;
  font-weight: 600;
}
.thinking {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-second);
  font-size: 13px;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-second);
  animation: blink 1.2s infinite;
}
.dot:nth-child(2) {
  animation-delay: 0.2s;
}
.dot:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes blink {
  0%, 80%, 100% { opacity: 0.25; }
  40% { opacity: 1; }
}
.cursor {
  animation: blink 1s infinite;
  color: var(--brand);
}
.fallback-tip {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-second);
}
.msg-ops {
  display: flex;
  align-items: center;
  margin-top: 8px;
  border-top: 1px dashed var(--border-color);
  padding-top: 6px;
}
.latency {
  margin-left: auto;
  font-size: 11.5px;
  color: var(--text-second);
}
</style>
