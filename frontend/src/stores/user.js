/**
 * 用户状态：登录通行证、当前用户信息
 *
 * 只负责"记住状态"，不负责发请求（发请求的代码在 src/api/ 里）——
 * 这样拆分可以避免模块之间绕圈依赖。
 */
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('rag-token') || '',
    user: JSON.parse(localStorage.getItem('rag-user') || 'null'),
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
    username: (state) => state.user?.username || '',
  },
  actions: {
    /** 登录成功后保存通行证和用户信息 */
    setLogin(token, user) {
      this.token = token
      this.user = user
      localStorage.setItem('rag-token', token)
      localStorage.setItem('rag-user', JSON.stringify(user))
    },
    /** 更新用户信息（比如改完密码后刷新） */
    setUser(user) {
      this.user = user
      localStorage.setItem('rag-user', JSON.stringify(user))
    },
    /** 退出登录：清空本地登录状态 */
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('rag-token')
      localStorage.removeItem('rag-user')
      // 同时清空聊天相关的本地缓存（防止换账号后看到上一个人的内容）
      localStorage.removeItem('rag-chat-draft')
    },
  },
})
