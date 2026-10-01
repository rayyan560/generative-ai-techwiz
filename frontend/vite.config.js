import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendRoot = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: resolve(frontendRoot, "../static/react"),
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(frontendRoot, "src/main.jsx"),
      output: {
        entryFileNames: "complaint-tracker.js",
        assetFileNames: "complaint-tracker.[ext]",
      },
    },
  },
});
