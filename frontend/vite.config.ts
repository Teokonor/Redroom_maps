import process from 'node:process'
import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// Same prefixes nginx proxies in production.
const API_PREFIXES = ['/map', '/preview', '/country', '/video', '/tag', '/data', '/ping']

const backendUrl = process.env.REDROOM_BACKEND_URL?.replace(/\/+$/, '') || 'http://127.0.0.1:8652'

const apiProxy = Object.fromEntries(API_PREFIXES.map((prefix) => [prefix, backendUrl]))

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: apiProxy,
  },
  preview: {
    proxy: apiProxy,
  },
})
