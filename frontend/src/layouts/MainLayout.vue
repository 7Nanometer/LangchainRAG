<script setup>
/** 主框架：顶部导航栏 + 内容区（所有登录后的页面都套在这个框架里） */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Moon, Sunny } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import NanoLogo from '@/components/common/NanoLogo.vue'

const router = useRouter()
const userStore = useUserStore()
const themeStore = useThemeStore()

const userInitial = computed(() => userStore.username.slice(0, 1).toUpperCase())

function toggleTheme() {
  themeStore.setMode(themeStore.isDark ? 'light' : 'dark')
}

async function onUserCommand(command) {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'admin') {
    router.push('/admin/dashboard')
  } else if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '退出',
        cancelButtonText: '取消',
        type: 'warning',
      })
    } catch {
      return
    }
    userStore.logout()
    router.push('/login')
  }
}
</script>

<template>
  <div class="main-layout">
    <header class="topbar">
      <div class="brand" @click="router.push('/chat')">
        <NanoLogo :size="19" :name-size="14.5" />
      </div>

      <div class="topbar-right">
        <el-tooltip :content="themeStore.isDark ? '切换浅色模式' : '切换深色模式'">
          <el-button circle text class="theme-btn" @click="toggleTheme">
            <el-icon :size="16"><Moon v-if="!themeStore.isDark" /><Sunny v-else /></el-icon>
          </el-button>
        </el-tooltip>

        <span class="topbar-divider" aria-hidden="true" />

        <el-dropdown trigger="click" @command="onUserCommand">
          <span class="user-chip">
            <el-avatar :size="24" class="user-avatar">{{ userInitial }}</el-avatar>
            <span class="user-name">{{ userStore.username }}</span>
            <el-tag v-if="userStore.isAdmin" size="small">管理员</el-tag>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人设置</el-dropdown-item>
              <el-dropdown-item v-if="userStore.isAdmin" command="admin">
                管理后台
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <main class="page-body">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.main-layout {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.topbar {
  height: 54px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: var(--paper);
  border-bottom: 1px solid var(--rule);
}
.brand {
  cursor: pointer;
  user-select: none;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.topbar-divider {
  width: 1px;
  height: 18px;
  background: var(--rule);
}
.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--r-1);
  outline: none;
  transition: background var(--dur-1) var(--ease);
}
.user-chip:hover {
  background: var(--tint);
}
.user-avatar {
  background: var(--ink);
  color: var(--paper);
  font-weight: 600;
  font-size: 12px;
}
.user-name {
  font-size: var(--fs-13);
  color: var(--ink);
}
.page-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
