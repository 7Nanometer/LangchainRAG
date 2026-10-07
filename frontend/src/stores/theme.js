/**
 * 主题状态：浅色 / 深色 / 跟随系统
 * 选择结果存在浏览器 localStorage 里，换页面、重启浏览器都记得
 */
import { defineStore } from 'pinia'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    mode: localStorage.getItem('theme-mode') || 'light', // light / dark / system
  }),
  getters: {
    isDark(state) {
      if (state.mode === 'system') {
        return window.matchMedia('(prefers-color-scheme: dark)').matches
      }
      return state.mode === 'dark'
    },
  },
  actions: {
    setMode(mode) {
      this.mode = mode
      localStorage.setItem('theme-mode', mode)
      this.applyTheme()
    },
    applyTheme() {
      // Element Plus 官方深色模式：给 html 加上 dark 类即可整体切换
      document.documentElement.classList.toggle('dark', this.isDark)
    },
  },
})
