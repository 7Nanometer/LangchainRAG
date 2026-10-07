<script setup>
/** 管理后台框架：左侧管理菜单 + 内容区（仅管理员可见，路由守卫会拦截普通用户） */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, DataAnalysis, Files } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

// 当前高亮的菜单项（/admin/kb/3 这类子路径也要正确高亮「知识库管理」）
const activeMenu = computed(() => {
  if (route.path.startsWith('/admin/kb')) return '/admin/kb'
  return route.path
})
</script>

<template>
  <div class="admin-layout">
    <aside class="admin-sidebar">
      <div class="admin-title">
        <el-button text :icon="ArrowLeft" size="small" @click="router.push('/chat')">
          返回问答
        </el-button>
      </div>
      <el-menu :default-active="activeMenu" router class="admin-menu">
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
</style>
