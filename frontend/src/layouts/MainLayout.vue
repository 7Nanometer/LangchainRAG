<script setup>
/** 主框架：顶部导航栏 + 内容区（所有登录后的页面都套在这个框架里） */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Moon, Sunny } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'

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
        <span class="brand-icon">💬</span>
        <span class="brand-name">知识库智能问答</span>
      </div>

      <div class="topbar-right">
        <el-tooltip :content="themeStore.isDark ? '切换浅色模式' : '切换深色模式'">
          <el-button circle text class="theme-btn" @click="toggleTheme">
            <el-icon :size="18"><Moon v-if="!themeStore.isDark" /><Sunny v-else /></el-icon>
          </el-button>
        </el-tooltip>

        <el-dropdown trigger="click" @command="onUserCommand">
          <span class="user-chip">
            <el-avatar :size="28" class="user-avatar">{{ userInitial }}</el-avatar>
            <span class="user-name">{{ userStore.username }}</span>
            <el-tag v-if="userStore.isAdmin" size="small" type="warning" effect="plain">
              管理员
            </el-tag>
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
  height: 56px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: var(--panel-bg);
  border-bottom: 1px solid var(--border-color);
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}
.brand-icon {
  font-size: 20px;
}
.brand-name {
  font-size: 16px;
  font-weight: 700;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  outline: none;
}
.user-chip:hover {
  background: rgba(128, 128, 128, 0.1);
}
.user-avatar {
  background: var(--brand);
  font-weight: 600;
}
.user-name {
  font-size: 14px;
}
.page-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
