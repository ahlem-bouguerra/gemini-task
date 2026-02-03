import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 3000,
    watch: { usePolling: true },
    proxy: {
      "/upload-batch": { target: "http://gemini-backend:8000", changeOrigin: true, secure: false },
      "/run-batch": { target: "http://gemini-backend:8000", changeOrigin: true, secure: false },
      "/job": { target: "http://gemini-backend:8000", changeOrigin: true, secure: false },
      "/downloads": { target: "http://gemini-backend:8000", changeOrigin: true, secure: false },
      "/jobs": { target: "http://gemini-backend:8000", changeOrigin: true, secure: false },
    },
  },
});
