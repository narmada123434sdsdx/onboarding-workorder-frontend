import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',       // allow LAN / mobile access
    port: 5173,            // fixed port
    strictPort: true,      // do NOT change port
    cors: true,
    allowedHosts: [
      '.ngrok-free.dev',
      '.ngrok.io',
      '.trycloudflare.com'
    ]
  }
})
