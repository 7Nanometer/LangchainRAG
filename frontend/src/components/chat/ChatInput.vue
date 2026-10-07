<script setup>
/** 输入框：Enter 发送 / Shift+Enter 换行；生成中变为"停止"按钮 */
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
        placeholder="输入你的问题，回车发送（Shift+回车换行）"
        @keydown="onKeydown"
      />
      <el-button
        v-if="!streaming"
        class="send-btn"
        type="primary"
        :icon="Promotion"
        :disabled="!text.trim()"
        @click="onSend"
      >
        发送
      </el-button>
      <el-button v-else class="send-btn" type="danger" plain @click="onSend">停止生成</el-button>
    </div>
    <div class="input-tip">回答由 AI 根据知识库资料生成，请注意甄别 · 引用片段可在回答下方展开查看</div>
  </div>
</template>

<style scoped>
.input-area {
  padding: 10px 20px 14px;
  border-top: 1px solid var(--border-color);
  background: var(--panel-bg);
}
.input-box {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}
.input-box :deep(.el-textarea__inner) {
  box-shadow: none;
  background: var(--app-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 14px;
}
.send-btn {
  height: 40px;
  flex-shrink: 0;
}
.input-tip {
  margin-top: 6px;
  font-size: 11.5px;
  color: var(--text-second);
  text-align: center;
}
</style>
