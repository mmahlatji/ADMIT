import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  build: {
    rollupOptions: {
      output: {
        // Pages are split by route already. These three change far less often
        // than our own code, so giving them their own chunks means a deploy
        // only invalidates the app chunk rather than the whole bundle.
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          mantine: [
            "@mantine/core",
            "@mantine/hooks",
            "@mantine/form",
            "@mantine/notifications",
            "@mantine/modals",
            "@mantine/dropzone",
          ],
          supabase: ["@supabase/supabase-js"],
        },
      },
    },
  },
});
