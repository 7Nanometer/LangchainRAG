<script setup>
/**
 * 品牌标志 —— Nano回执
 * 图形：一枚"回"字面板（细线外框 + 偏右下的墨块答件），自成一体、单色可用。
 * 字标：Nano（常规）＋ 回执（加粗），贴紧排列。
 */
defineProps({
  size: { type: Number, default: 22 }, // 图形边长（px）
  nameSize: { type: Number, default: 15 }, // 字标字号（px）
  stacked: { type: Boolean, default: false }, // 图形在上、字在下（登录大标志用）
})
</script>

<template>
  <span class="logo" :class="{ stacked }">
    <svg
      class="logo-mark"
      :width="size"
      :height="size"
      viewBox="0 0 32 32"
      aria-hidden="true"
    >
      <rect
        x="3"
        y="3"
        width="26"
        height="26"
        rx="4"
        fill="none"
        stroke="currentColor"
        stroke-width="2.6"
      />
      <rect x="13.5" y="13.5" width="9" height="9" fill="currentColor" />
    </svg>
    <span class="logo-name" :style="{ fontSize: nameSize + 'px' }">
      <span class="latin">Nano</span><span class="hanzi">回执</span>
    </span>
  </span>
</template>

<style scoped>
.logo {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--ink);
  user-select: none;
}
.logo.stacked {
  flex-direction: column;
  gap: 12px;
}
.logo-mark {
  flex-shrink: 0;
  display: block;
}
.logo-name {
  line-height: 1;
  letter-spacing: 0.005em;
  white-space: nowrap;
}
.latin {
  font-weight: 600;
}
.hanzi {
  font-weight: 800;
}
</style>
