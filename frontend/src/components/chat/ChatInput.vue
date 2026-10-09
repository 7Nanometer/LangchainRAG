<script setup>
/** 输入区：Enter 发送 / Shift+Enter 换行；生成中变为"停止" */
import { ref } from 'vue'
import { Promotion } from '@element-plus/icons-vue'

const props = defineProps({
  streaming: { type: Boolean, default: false },
})
const emit = defineEmits(['send', 'stop'])

const text = ref('')

function onSend() {
  if (props.streaming) {
    emit('stop')
    return
  }
  const value = text.value.trim()
  if (!value) return
  emit('send', value)
  text.value = ''
}

function onKeydown(e) {
  // 中文输入法组词（isComposing）时不要触发发送
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    onSend()
  }
}
</script>

<template>
  <div class="input-area">
    <div class="input-box">
      <el-input
        v-model="text"
        type="textarea"
        :autosize="{ minRows: 1, maxRows: 6 }"
        resize="none"
        placeholder="写下你的问题，回车发送（Shift＋回车换行）"
        @keydown="onKeydown"
      />
      <el-button
        v-if="!streaming"
        class="send-btn"
        type="primary"
        :disabled="!text.trim()"
        @click="onSend"
      >
        发送
      </el-button>
      <el-button v-else class="send-btn stop-btn" @click="onSend">停止生成</el-button>
    </div>
    <div class="input-tip">
      回答由 AI 依据知识库资料生成 · 引用与指标可在回答下方的回执面板中逐项核对
    </div>
  </div>
</template>

<style scoped>
.input-area {
  padding: 12px 24px 14px;
  border-top: 1px solid var(--rule);
  background: var(--paper);
}
.input-box {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  max-width: 820px;
  margin: 0 auto;
}
.input-box :deep(.el-textarea__inner) {
  padding: 9px 12px;
  font-size: var(--fs-14);
  line-height: 1.65;
}
.send-btn {
  height: 38px;
  flex-shrink: 0;
  padding: 0 20px;
}
.stop-btn {
  color: var(--ink-2);
  border-color: var(--rule);
}
.stop-btn:hover {
  color: var(--ink);
  border-color: var(--ink);
  background: var(--tint);
}
.input-tip {
  max-width: 820px;
  margin: 7px auto 0;
  font-size: var(--fs-11);
  color: var(--ink-3);
}
</style>
