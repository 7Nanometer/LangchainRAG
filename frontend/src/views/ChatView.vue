<script setup>
/** 聊天主页（M1 阶段为占位页，完整问答功能在 M3 里程碑实现） */
</script>

<template>
  <div class="chat-placeholder">
    <div class="placeholder-inner">
      <div class="placeholder-icon">💬</div>
      <h2>知识库问答</h2>
      <p>问答功能正在按计划开发中，将在下个里程碑开放。</p>
      <p class="hint">
        届时你可以在这里提问商品相关问题，AI 会先查资料再回答，并标注引用出处。
      </p>
    </div>
  </div>
</template>

<style scoped>
.chat-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.placeholder-inner {
  text-align: center;
  color: var(--text-second);
  padding: 24px;
}
.placeholder-icon {
  font-size: 48px;
  margin-bottom: 12px;
}
.placeholder-inner h2 {
  margin: 0 0 8px;
  color: var(--text-main);
}
.placeholder-inner p {
  margin: 6px 0;
  font-size: 14px;
}
.hint {
  font-size: 13px !important;
  opacity: 0.8;
}
</style>
