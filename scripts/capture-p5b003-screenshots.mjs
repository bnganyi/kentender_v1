/**
 * One-off MCP screenshot capture for P5B-003 tracker evidence.
 * Run: node scripts/capture-p5b003-screenshots.mjs
 */
import { chromium } from 'playwright';
import * as dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.join(__dirname, '..', '.env.ui') });

const base = process.env.UI_BASE_URL || 'http://127.0.0.1:8000';
const user = process.env.UI_ADMIN_USER || 'Administrator';
const password = process.env.UI_ADMIN_PASSWORD || 'Sn00per56*';
const outDir = path.join(__dirname, '..');

const FIXTURE_ITEM = {
	id: 'pkg-moh-2026-001',
	title: 'District Hospital Renovation Works',
	subtitle: 'Works · Open Tender · 98,000,000 KES',
	status_label: 'Released',
	status_tone: 'success',
	blocker_count: 0,
};

async function login(page) {
	await page.goto(`${base}/login`, { waitUntil: 'domcontentloaded' });
	const email = page.locator('#login_email');
	try {
		await email.waitFor({ state: 'visible', timeout: 30_000 });
	} catch {
		await page.context().clearCookies();
		await page.goto(`${base}/login`, { waitUntil: 'domcontentloaded' });
		await email.waitFor({ state: 'visible', timeout: 30_000 });
	}
	await email.fill(user);
	await page.locator('#login_password').fill(password);
	await page.getByRole('button', { name: 'Login', exact: true }).click();
	await page.waitForFunction(() => !document.querySelector('#login_email'), { timeout: 60_000 });
}

const browser = await chromium.launch();
const page = await browser.newPage();
await login(page);
await page.goto(`${base}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('[data-testid="pp2-work-list"]', { timeout: 60_000 });
await page.evaluate((item) => {
	const host = document.querySelector('[data-testid="pp2-work-list"]');
	const api = window.kentender_procurement?.PlanningWorkList;
	if (!host || !api) throw new Error('PlanningWorkList unavailable');
	api.render(host, { items: [item], slug: 'packages' });
}, FIXTURE_ITEM);
await page.screenshot({ path: path.join(outDir, 'p5b003_packages_work_list_row_mcp.png'), fullPage: true });
console.log('saved p5b003_packages_work_list_row_mcp.png');
await browser.close();
console.log('done');
