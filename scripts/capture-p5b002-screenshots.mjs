/**
 * One-off MCP screenshot capture for P5B-002 tracker evidence.
 * Run: node scripts/capture-p5b002-screenshots.mjs
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

async function capture(page, route, filename) {
	await page.goto(`${base}${route}`, { waitUntil: 'domcontentloaded' });
	await page.waitForSelector('[data-testid="pp2-queue-tabs"]', { timeout: 60_000 });
	await page.screenshot({ path: path.join(outDir, filename), fullPage: true });
	console.log(`saved ${filename}`);
}

const browser = await chromium.launch();
const page = await browser.newPage();
await login(page);
await capture(page, '/desk/procurement-planning', 'p5b002_planning_home_queue_tabs_mcp.png');
await capture(page, '/desk/procurement-planning/packages', 'p5b002_packages_queue_tabs_mcp.png');
await browser.close();
console.log('done');
