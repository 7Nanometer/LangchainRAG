<script setup>
/**
 * 管理后台框架：左侧管理菜单 + 内容区（仅管理员可见，路由守卫会拦截普通用户）
 * 窄屏（手机/平板）时菜单自动变为顶部横向排列
 */
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, DataAnalysis, Files } from '@element-plus/icons-vue'
import NanoLogo from '@/components/common/NanoLogo.vue'

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
        <NanoLogo :size="16" :name-size="12.5" />
      </div>
      <button class="back-link" type="button" @click="router.push('/chat')">
        <el-icon :size="13"><ArrowLeft /></el-icon>
        <span>返回问答</span>
      </button>
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
      <div class="admin-foot u-label">管理后台</div>
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
  background: var(--paper);
}
.admin-sidebar {
  width: 208px;
  flex-shrink: 0;
  background: var(--paper);
  border-right: 1px solid var(--rule);
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.admin-title {
  padding: 16px 16px 12px;
}
.back-link {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 12px 10px;
  padding: 6px 8px;
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: var(--fs-12);
  color: var(--ink-3);
  cursor: pointer;
  border-radius: var(--r-1);
  transition: color var(--dur-1) var(--ease), background var(--dur-1) var(--ease);
}
.back-link:hover {
  color: var(--ink);
  background: var(--tint);
}
.admin-menu {
  border-right: none;
  background: transparent;
  --el-menu-bg-color: transparent;
}
.admin-foot {
  margin-top: auto;
  padding: 14px 16px;
  border-top: 1px solid var(--rule-2);
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
  border-bottom: 1px solid var(--rule);
}
.admin-layout.mobile .admin-title {
  padding: 8px 8px 8px 14px;
  flex-shrink: 0;
}
.admin-layout.mobile .back-link {
  margin: 0 4px;
  flex-shrink: 0;
}
.admin-layout.mobile .admin-menu {
  flex: 1;
  min-width: 0;
  overflow-x: auto;
}
.admin-layout.mobile .admin-foot {
  display: none;
}
.admin-layout.mobile .admin-body {
  padding: 16px;
}
</style>
