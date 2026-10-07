/**
 * 路由表 + 门卫（导航守卫）
 *
 * 门卫规则：
 *  1. 没登录 → 一律送到登录页
 *  2. 登录了但不是管理员 → 进不了 /admin 管理页面（会被弹回聊天页）
 *  3. 后端每个管理接口还有独立检查（双保险，绕过前端也没用）
 */
import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      { path: '', redirect: '/chat' },
      {
        path: 'chat/:id?',
        name: 'chat',
        component: () => import('@/views/ChatView.vue'),
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/ProfileView.vue'),
      },
      {
        path: 'admin',
        component: () => import('@/layouts/AdminLayout.vue'),
        meta: { admin: true },
        children: [
          { path: '', redirect: '/admin/dashboard' },
          {
            path: 'dashboard',
            name: 'admin-dashboard',
            component: () => import('@/views/admin/DashboardView.vue'),
          },
          {
            path: 'kb',
            name: 'admin-kb',
            component: () => import('@/views/admin/KnowledgeBaseView.vue'),
          },
          {
            path: 'kb/:id',
            name: 'admin-kb-documents',
            component: () => import('@/views/admin/DocumentsView.vue'),
          },
        ],
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { public: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const userStore = useUserStore()

  if (to.meta.public) return true

  if (!userStore.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  if (to.meta.admin && !userStore.isAdmin) {
    ElMessage.warning('没有权限访问管理后台（仅管理员可用）')
    return { path: '/chat' }
  }

  return true
})

export default router
