<script setup>
/**
 * 单条消息
 *   - 用户消息：一张"提交单"（发丝框，右对齐）
 *   - AI 回答：署名行（签发方）+ 正文（Markdown，[n] 角标可点）+ 答案回执 + 操作行
 */
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useChatStore } from '@/stores/chat'
import { renderMarkdown } from '@/utils/markdown'
import NanoLogo from '@/components/common/NanoLogo.vue'
import ReceiptPanel from './ReceiptPanel.vue'

const props = defineProps({
  message: { type: Object, required: true },
  streaming: { type: Boolean, default: false },
})

const chat = useChatStore()
const isUser = computed(() => props.message.role === 'user')
const html = computed(() => renderMarkdown(props.message.content))
const panelRef = ref()

/** 点正文里的 [n] 角标 → 展开回执并定位到该条来源 */
function onBodyClick(e) {
  const el = e.target.closest?.('.cite-ref')
  if (!el) return
  const n = Number(el.textContent)
  if (n) panelRef.value?.openAt(n)
}

/** 键盘操作角标（Enter / 空格），与鼠标点击等效 */
function onBodyKey(e) {
  if (e.key !== 'Enter' && e.key !== ' ') return
  const el = e.target.closest?.('.cite-ref')
  if (!el) return
  e.preventDefault()
  const n = Number(el.textContent)
  if (n) panelRef.value?.openAt(n)
}

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
    <!-- 用户消息：提交单 -->
    <div v-if="isUser" class="ask-box">{{ message.content }}</div>

    <!-- AI 回答 -->
    <div v-else class="answer">
      <div class="issuer">
        <NanoLogo :size="13" :name-size="11.5" />
        <span class="issuer-time" />
      </div>

      <div
        v-if="message.content"
        class="md-body"
        @click="onBodyClick"
        @keydown="onBodyKey"
        v-html="html"
      />
      <span v-if="streaming && message.content" class="caret" aria-hidden="true" />

      <div v-if="!message.content" class="retrieving">
        <span class="retrieving-mark" />
        <span>正在检索资料</span>
        <span class="tick">…</span>
      </div>

      <!-- 答案回执（签名动作） -->
      <ReceiptPanel
        v-if="!isUser && (message.citations?.length || message.retrieval || !streaming)"
        ref="panelRef"
        :message="message"
        :streaming="streaming"
      />

      <!-- 操作行 -->
      <div v-if="!streaming && message.content" class="ops">
        <button
          class="op"
          :class="{ on: message.feedback === 'like' }"
          type="button"
          @click="onLike"
        >
          有用
        </button>
        <button
          class="op"
          :class="{ on: message.feedback === 'dislike' }"
          type="button"
          @click="onDislike"
        >
          没用
        </button>
        <button class="op" type="button" @click="onCopy">复制</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.msg-row {
  margin-bottom: 26px;
}
.msg-row.is-user {
  display: flex;
  justify-content: flex-end;
}

/* ---- 用户"提交单" ---- */
.ask-box {
  max-width: 78%;
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: var(--r-1);
  padding: 9px 13px;
  font-size: var(--fs-14);
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

/* ---- AI 回答 ---- */
.answer {
  max-width: 100%;
}
.issuer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 7px;
  color: var(--ink-3);
}
.retrieving {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: var(--fs-13);
  color: var(--ink-2);
  padding: 2px 0;
}
.retrieving-mark {
  width: 3px;
  height: 13px;
  background: var(--ink);
  animation: pulse-ink 1.1s ease-in-out infinite;
}
.tick {
  animation: caret-blink 1s steps(1) infinite;
  color: var(--ink-3);
}
.caret {
  display: inline-block;
  width: 8px;
  height: 15px;
  background: var(--ink);
  vertical-align: -2px;
  margin-left: 2px;
  animation: caret-blink 1.06s steps(1) infinite;
}

/* ---- 操作行 ---- */
.ops {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-top: 8px;
}
.op {
  font-family: inherit;
  font-size: var(--fs-11);
  letter-spacing: 0.04em;
  color: var(--ink-3);
  background: transparent;
  border: none;
  border-radius: var(--r-2);
  padding: 3px 8px;
  cursor: pointer;
  transition: color var(--dur-1) var(--ease), background var(--dur-1) var(--ease);
}
.op:hover {
  color: var(--ink);
  background: var(--tint);
}
.op.on {
  color: var(--ink);
  font-weight: 700;
}
.op.on::before {
  content: '';
  display: inline-block;
  width: 5px;
  height: 5px;
  background: var(--ink);
  margin-right: 5px;
  vertical-align: 1px;
}
</style>
