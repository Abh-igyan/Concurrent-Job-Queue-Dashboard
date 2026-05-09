import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": process.env.VITE_PROXY_TARGET ?? "http://localhost:8000",
      "/ws": {
        target: process.env.VITE_WS_PROXY_TARGET ?? "ws://localhost:8000",
        ws: true
      }
    }
  }
});
