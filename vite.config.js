import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

// Toolforge serves wmfr-search.toolforge.org from the root. Override with VITE_BASE for a sub-path (GitHub Pages).
export default defineConfig({
  base: process.env.VITE_BASE || '/',
  plugins: [vue()],
  resolve: {
    // Group views share lingua-deck's `@/components/...` imports: src/components provides standalone versions
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
})
