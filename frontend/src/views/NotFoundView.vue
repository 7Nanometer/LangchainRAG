<script setup>
/** 404 页面：访问了不存在的地址 */
import { useRouter } from 'vue-router'
import NanoLogo from '@/components/common/NanoLogo.vue'

const router = useRouter()
</script>

<template>
  <div class="notfound-page">
    <div class="nf-inner">
      <NanoLogo :size="24" :name-size="16" />
      <div class="nf-code num">404</div>
      <div class="nf-rule" />
      <p class="nf-text">这张回执不存在——页面可能已被移除，或地址有笔误。</p>
      <el-button type="primary" @click="router.push('/chat')">回到问答</el-button>
    </div>
  </div>
</template>

<style scoped>
.notfound-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--paper);
}
.nf-inner {
  text-align: center;
  max-width: 380px;
}
.nf-code {
  font-size: 72px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.03em;
  margin: 26px 0 0;
}
.nf-rule {
  width: 56px;
  height: 2px;
  background: var(--ink);
  margin: 18px auto;
}
.nf-text {
  font-size: var(--fs-13);
  color: var(--ink-2);
  line-height: 1.8;
  margin: 0 0 26px;
}
</style>
