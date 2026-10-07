<script setup>
/** 欢迎面板：新对话时显示，提供几个示例问题方便快速体验 */
const emit = defineEmits(['ask'])

const examples = [
  'W1 耳机续航多久？',
  '手表可以戴着游泳吗？',
  '退货运费由谁承担？',
  '三款商品的价格分别是多少？',
]
</script>

<template>
  <div class="welcome">
    <div class="welcome-icon">💬</div>
    <h2 class="welcome-title">你好，我是知识库智能客服</h2>
    <p class="welcome-sub">
      我会先查找商品知识库资料，再回答你的问题，并标注答案的出处
    </p>

    <div class="examples">
      <div class="examples-label">试试这样问我：</div>
      <div class="example-list">
        <button v-for="q in examples" :key="q" class="example-btn" @click="emit('ask', q)">
          {{ q }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.welcome {
  max-width: 560px;
  margin: 60px auto 0;
  text-align: center;
  padding: 0 20px;
}
.welcome-icon {
  font-size: 52px;
}
.welcome-title {
  font-size: 21px;
  margin: 14px 0 8px;
}
.welcome-sub {
  color: var(--text-second);
  font-size: 13.5px;
  margin: 0 0 30px;
}
.examples-label {
  font-size: 12.5px;
  color: var(--text-second);
  margin-bottom: 10px;
}
.example-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}
.example-btn {
  border: 1px solid var(--border-color);
  background: var(--panel-bg);
  color: var(--text-main);
  border-radius: 20px;
  padding: 8px 16px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.example-btn:hover {
  border-color: var(--brand);
  color: var(--brand);
  transform: translateY(-1px);
}
</style>
