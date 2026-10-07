/**
 * Vite 构建配置 —— 前端工程的"施工图纸"
 *
 * 两个关键点：
 *  1. @ 符号代表 src 目录（import 时不用写一长串相对路径）
 *  2. 开发模式下把 /api 开头的请求自动转给后端 8000 端口（免跨域配置）
 */
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 1500,
  },
})
