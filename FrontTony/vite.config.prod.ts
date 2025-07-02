import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Configuración para producción con dominio real
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  base: '/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
  server: {
    host: '0.0.0.0',
    port: 80,
  },
  preview: {
    host: '0.0.0.0',
    port: 80,
  },
}); 