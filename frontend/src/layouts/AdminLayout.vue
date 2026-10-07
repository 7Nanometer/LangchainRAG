<script setup>
/**
 * 管理后台框架：左侧管理菜单 + 内容区（仅管理员可见，路由守卫会拦截普通用户）
 * 窄屏（手机/平板）时菜单自动变为顶部横向排列
 */
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, DataAnalysis, Files } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

// 当前高亮的菜单项（/admin/kb/3 这类子路径也要正确高亮「知识库管理」）
const activeMenu = computed(() => {
  if (route.path.startsWith('/admin/kb')) return '/admin/kb'
  return route.path
})

// 窄屏适配
const isMobile = ref(window.innerWidth < 900)
function onResize() {
  isMobile.value = window.innerWidth < 900
}
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))
</script>

<template>
  <div class="admin-layout" :class="{ mobile: isMobile }">
    <aside class="admin-sidebar">
      <div class="admin-title">
        <el-button text :icon="ArrowLeft" size="small" @click="router.push('/chat')">
          返回问答
        </el-button>
      </div>
      <el-menu
        :default-active="activeMenu"
        :mode="isMobile ? 'horizontal' : 'vertical'"
        router
        class="admin-menu"
      >
        <el-menu-item index="/admin/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据看板</span>
        </el-menu-item>
        <el-menu-item index="/admin/kb">
          <el-icon><Files /></el-icon>
          <span>知识库管理</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <section class="admin-body">
      <router-view />
    </section>
  </div>
</template>

<style scoped>
.admin-layout {
  height: 100%;
  display: flex;
}
.admin-sidebar {
  width: 210px;
  flex-shrink: 0;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}
.admin-title {
  padding: 12px 16px 8px;
}
.admin-menu {
  border-right: none;
  background: transparent;
}
.admin-body {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: 20px 24px;
}

/* 窄屏：菜单移到顶部横向排列 */
.admin-layout.mobile {
  flex-direction: column;
}
.admin-layout.mobile .admin-sidebar {
  width: 100%;
  flex-direction: row;
  align-items: center;
  border-right: none;
  border-bottom: 1px solid var(--border-color);
}
.admin-layout.mobile .admin-title {
  padding: 8px 8px 8px 14px;
  flex-shrink: 0;
}
.admin-layout.mobile .admin-menu {
  flex: 1;
  min-width: 0;
  overflow-x: auto;
}
.admin-layout.mobile .admin-body {
  padding: 14px;
}
</style>
