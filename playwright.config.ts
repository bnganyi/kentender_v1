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
  /**
   * Refuses to start on a background queue Frappe will reject enqueues from.
   * Every fixture reset deletes documents, each deletion enqueues a job, and
   * nothing consumes them without a worker — so the suite breaks mid-run in
   * ways that read as product defects. See tests/ui/helpers/benchQueue.ts.
   */
  globalSetup: './tests/ui/globalSetup.ts',
  /** PLN-CHG-001 v1.12 D13 — puts the Planning fixtures' intake flags back. */
  globalTeardown: './tests/ui/globalTeardown.ts',
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
    /**
     * A click on a control that never becomes actionable — a disabled button
     * a spec forgot to satisfy the precondition for — otherwise waits out the
     * whole test timeout with no output, which reads as a hung suite rather
     * than a failing test. Bound it well under the per-test budget.
     */
    actionTimeout: 15_000,
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
