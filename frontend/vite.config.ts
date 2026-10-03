import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  root: fileURLToPath(new URL('.', import.meta.url)),
  plugins: [react()],
  clearScreen: false,
  server: { host: '127.0.0.1', port: 1420, strictPort: true },
  preview: { host: '127.0.0.1', port: 1421, strictPort: true },
  build: { outDir: '../dist', emptyOutDir: true },
  test: { environment: 'jsdom', setupFiles: ['./src/test/setup.ts'], css: false },
});
