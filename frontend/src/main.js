/**
 * 前端入口 —— 浏览器打开网页后，第一个跑起来的就是这里
 * 负责把各个积木拼装到一起：路由、状态管理、UI 组件库
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn' // 组件库的中文语言包
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css' // 深色主题支持

import App from './App.vue'
import router from './router'
import './styles/index.css'

const app = createApp(App)
app.use(createPinia()) // 状态管理（记住登录状态等）
app.use(router) // 路由（页面跳转）
app.use(ElementPlus, { locale: zhCn }) // UI 组件库（全中文）
app.mount('#app')
