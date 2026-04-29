import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"
import path from "path"

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000"

// Hosts permitidos: configurar en docker-compose.override.yml via VITE_ALLOWED_HOSTS
// Ejemplo: VITE_ALLOWED_HOSTS=mi-servidor.ejemplo.com,otro-host.ejemplo.com
const allowedHosts = process.env.VITE_ALLOWED_HOSTS
  ? process.env.VITE_ALLOWED_HOSTS.split(",").map((h) => h.trim()).filter(Boolean)
  : []

export default defineConfig({
  base: 'aiuda/',
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    allowedHosts,
    proxy: {
      "/api": apiProxyTarget,
      "/aiuda/api": {
        target: apiProxyTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/aiuda\/api/, "/api"),
      },
    },
  },
})
