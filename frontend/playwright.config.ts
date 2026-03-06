import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E configuration for USERinator.
 *
 * These tests run against live services through the Caddy gateway (:8080).
 * Start all services before running:
 *   - AUTHinator  :8001
 *   - RMAinator   :8002
 *   - FULFILinator :8003
 *   - USERinator  :8004
 *   - Caddy       :8080
 *   - Vite        :5173
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'html',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:8080',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
