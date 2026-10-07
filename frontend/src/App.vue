<script setup>
// 应用根组件：只负责初始化主题 + 显示当前路由页面
import { onMounted } from 'vue'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()
onMounted(() => themeStore.applyTheme())
</script>

<template>
  <router-view />
</template>
