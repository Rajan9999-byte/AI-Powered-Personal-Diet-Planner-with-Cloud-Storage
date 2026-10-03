import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  root: fileURLToPath(new URL('./frontend', import.meta.url)),
  publicDir: fileURLToPath(new URL('./public', import.meta.url)),
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': 'http://127.0.0.1:5000'
    }
  },
  build: {
    outDir: fileURLToPath(new URL('./frontend/dist', import.meta.url)),
    emptyOutDir: true,
    sourcemap: true
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.js']
  }
});
