/**
 * 网络请求统一封装（基于 axios）
 *
 * 干三件事：
 *  1. 自动带上登录通行证（Authorization 请求头）
 *  2. 后端返回的错误自动弹出中文提示（不用每个页面各写一遍）
 *  3. 通行证过期（401）自动清理登录状态并跳回登录页
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// 请求出发前：自动带上通行证
request.interceptors.request.use((config) => {
  const userStore = useUserStore()
  if (userStore.token) {
    config.headers.Authorization = `Bearer ${userStore.token}`
  }
  return config
})

// 收到响应后：统一的错误处理
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const message =
      error.response?.data?.message || '网络异常，请确认后端服务已启动（4-启动系统.bat）'

    if (status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    }
    ElMessage.error(message)
    return Promise.reject(error)
  },
)

export default request
