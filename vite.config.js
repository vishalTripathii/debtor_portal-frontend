import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Load env file based on mode
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],

    // Build configuration for production/S3
    build: {
      outDir: 'dist',
      sourcemap: mode !== 'production',
      // Optimize chunk size for CloudFront
      rollupOptions: {
        output: {
          manualChunks: {
            // Separate vendor chunks for better caching
            vendor: ['react', 'react-dom', 'react-router-dom'],
            mui: ['@mui/material', '@mui/icons-material'],
          },
        },
      },
      // Optimize for production
      minify: mode === 'production' ? 'esbuild' : false,
      // Set chunk size warning limit
      chunkSizeWarningLimit: 1000,
    },

    // Define environment variables
    define: {
      // Make env variables available in the app
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
    },

    // Server configuration for development
    server: {
      port: 5173,
      host: true,
      // Proxy API requests in development
      proxy: env.VITE_API_BASE_URL ? undefined : {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },

    // Preview server (for testing production build locally)
    preview: {
      port: 4173,
      host: true,
    },

    // Base URL for assets (important for S3/CloudFront)
    // Set to '/' for root-level deployment
    // Or set VITE_BASE_URL env variable for custom path
    base: env.VITE_BASE_URL || '/',
  }
})
