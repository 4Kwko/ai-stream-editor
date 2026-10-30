import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

const BACKEND = process.env.AI_STREAM_BACKEND ?? 'http://127.0.0.1:8765'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    // O navegador fala só com o Vite; /api vai para o backend local, sem CORS.
    // changeOrigin troca o Host para 127.0.0.1:8765; o Origin continua 127.0.0.1:5173.
    proxy: { '/api': { target: BACKEND, changeOrigin: true } },
  },
  preview: {
    host: '127.0.0.1',
    port: 4173,
    strictPort: true,
    proxy: { '/api': { target: BACKEND, changeOrigin: true } },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    restoreMocks: true,
  },
})
