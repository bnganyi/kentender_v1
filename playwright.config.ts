import { defineConfig, devices } from '@playwright/test';
import * as dotenv from 'dotenv';

dotenv.config({ path: '.env.ui' });

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  expect: {
    timeout: 5_000,
  },
  fullyParallel: false,
  /** Fewer parallel browsers reduces flaky `/login` when many tests log in as the same user. */
  workers: process.env.CI ? 2 : 2,
  retries: process.env.CI ? 2 : 1,
  reporter: [['html', { open: 'never' }]],
  use: {
    /**
     * Same Frappe site as `bench --site kentender.midas.com`: use local gunicorn when
     * `default_site` is set (see `sites/common_site_config.json`). Override with
     * `UI_BASE_URL=https://kentender.midas.com` only where that host resolves (VPN / DNS).
     */
    baseURL: process.env.UI_BASE_URL || 'http://127.0.0.1:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    headless: true,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
