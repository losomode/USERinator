import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const deployDomain = env.VITE_DEPLOY_DOMAIN;

  // When VITE_DEPLOY_DOMAIN is set, allow that host in addition to localhost.
  // Keeps local dev (localhost:8080) and remote deployment working simultaneously.
  const allowedHosts: string[] | undefined = deployDomain
    ? ['localhost', '127.0.0.1', deployDomain, `www.${deployDomain}`]
    : undefined;

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@inator/shared': path.resolve(__dirname, '../../shared/frontend/src'),
      },
      dedupe: ['react', 'react-dom', 'react-router-dom'],
    },
    server: {
      port: 3004,
      strictPort: true,
      open: false,
      ...(allowedHosts ? { allowedHosts } : {}),
    },
    base: '/users/',
    build: {
      outDir: 'dist',
    },
  };
});
