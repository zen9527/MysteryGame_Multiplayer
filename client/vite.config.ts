import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
        secure: false
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        secure: false
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('vue/dist') || id.includes('vue-router') || id.includes('pinia')) {
              return 'vendor';
            }
          }
          if (id.includes('/components/game/') || id.includes('/components/GamePage.vue')) {
            return 'game';
          }
        },
      },
    },
    chunkSizeWarningLimit: 500,
  },
})
