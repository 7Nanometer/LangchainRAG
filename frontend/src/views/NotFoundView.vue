<script setup>
/** 404 页面：访问了不存在的地址 */
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="notfound-page">
    <el-result icon="warning" title="404" sub-title="页面不存在或已被移除">
      <template #extra>
        <el-button type="primary" @click="router.push('/chat')">回到首页</el-button>
      </template>
    </el-result>
  </div>
</template>

<style scoped>
.notfound-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
