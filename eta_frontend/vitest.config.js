import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
    css: true,
    include: ['src/unit/**/*.test.{js,jsx,ts,tsx}', 'src/integration/**/*.test.{js,jsx,ts,tsx}'],
  },
});
