import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,  // Explicitly set to 5174
    host: true,
    strictPort: true, // Don't try other ports if 5174 is taken
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})