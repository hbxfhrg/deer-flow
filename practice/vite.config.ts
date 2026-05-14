import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api/threads': {
        target: 'http://localhost:2024',
        changeOrigin: true,
        secure: false,
      },
      '/api/langgraph': {
        target: 'http://localhost:2024',
        changeOrigin: true,
        secure: false,
      },
      // 其他 API 请求仍然使用 Gateway (8001)
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})