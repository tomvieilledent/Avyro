import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// SPA à page unique : react-router-dom gère toutes les routes côté client
// depuis index.html. Le backend Flask sert index.html en fallback pour toute
// route non-API (voir _register_frontend dans backend/app/__init__.py).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Le frontend appelle des chemins relatifs "/api/..." (voir src/lib/api.js).
      // En dev, on les relaie vers le backend Flask lancé via run-local.sh (port 8080).
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  build: {
    target: 'es2020',
  },
})
