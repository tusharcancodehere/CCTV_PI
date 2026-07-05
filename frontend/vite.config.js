import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/static/',
  plugins: [react()],
  server: {
    proxy: {
      // Backend API routes
      '/api': {
        target: 'http://127.0.0.1:8888',
        changeOrigin: true,
      },
      // Legacy stream alias
      '/video_feed': {
        target: 'http://127.0.0.1:8888',
        changeOrigin: true,
      },
      // Snapshot endpoint
      '/snapshot': {
        target: 'http://127.0.0.1:8888',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Deterministic filenames — prevents stale 404 after rebuild
        entryFileNames: 'index.js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name?.endsWith('.css')) return 'index.css'
          return '[name]-[hash][extname]'
        },
      },
    },
  },
})
