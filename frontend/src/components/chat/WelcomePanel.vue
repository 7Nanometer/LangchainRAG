<script setup>
/** 欢迎面板：新对话时显示 —— 一句话讲清机制 + 三个可直接点的示例问题 */
import NanoLogo from '@/components/common/NanoLogo.vue'

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
    <NanoLogo stacked :size="40" :name-size="21" />

    <h2 class="welcome-title">问一句，拿一张回执</h2>
    <p class="welcome-sub">
      先查商品资料再回答；每条回答下方都附一张回执面板——
      来源、相关度、耗时逐项列出，可随时展开核对原文。
    </p>

    <div class="examples">
      <div class="examples-label u-label">试试这样问</div>
      <button v-for="(q, i) in examples" :key="q" class="example-row" @click="emit('ask', q)">
        <span class="example-no num">{{ String(i + 1).padStart(2, '0') }}</span>
        <span class="example-q">{{ q }}</span>
        <span class="example-arrow">→</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.welcome {
  max-width: 460px;
  margin: 9vh auto 0;
  padding: 0 24px;
}
.welcome-title {
  font-size: var(--fs-26);
  font-weight: 800;
  letter-spacing: -0.01em;
  margin: 22px 0 10px;
}
.welcome-sub {
  color: var(--ink-2);
  font-size: var(--fs-13);
  line-height: 1.85;
  margin: 0 0 36px;
}
.examples-label {
  margin-bottom: 6px;
}
.example-row {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  border: none;
  border-top: 1px solid var(--rule);
  background: transparent;
  font-family: inherit;
  font-size: var(--fs-13);
  color: var(--ink-2);
  text-align: left;
  padding: 11px 4px;
  cursor: pointer;
  transition: background var(--dur-1) var(--ease);
}
.example-row:last-child {
  border-bottom: 1px solid var(--rule);
}
.example-row:hover {
  background: var(--tint);
  color: var(--ink);
}
.example-no {
  color: var(--ink-3);
  font-size: var(--fs-11);
}
.example-q {
  flex: 1;
}
.example-arrow {
  color: var(--ink-3);
  opacity: 0;
  transform: translateX(-4px);
  transition: opacity var(--dur-2) var(--ease), transform var(--dur-2) var(--ease);
}
.example-row:hover .example-arrow {
  opacity: 1;
  transform: translateX(0);
}
</style>
