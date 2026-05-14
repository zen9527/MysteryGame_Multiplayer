import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  plugins: [vue()],
  test: {
    include: ['tests/unit/**/*.spec.ts', 'tests/integration/**/*.spec.ts', 'tests/components/**/*.spec.ts'],
    exclude: ['tests/e2e/**', '**/node_modules/**'],
    environment: 'jsdom',
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
});
