/**
 * One-off MCP screenshot capture for P5B-004 tracker evidence.
 * Run: node scripts/capture-p5b004-screenshots.mjs
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
	funding_label: 'Budget linked',
	blocker_count: 0,
	next_action_label: 'Open Tender',
	primary_action: { label: 'Open Tender', action: 'open_tender' },
	secondary_actions: [{ label: 'Open Package', action: 'open_package' }],
	show_evidence_action: true,
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
await page.addInitScript(() => window.localStorage.removeItem('kt-pp2-right-panel-collapsed'));
await page.goto(`${base}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('[data-testid="pp2-primary-workspace-shell"]', { timeout: 60_000 });
const shell = page.getByTestId('pp2-primary-workspace-shell');
if ((await shell.getAttribute('data-right-panel-collapsed')) === '1') {
	await page.getByTestId('pp2-primary-right-panel-toggle').click();
}
await page.evaluate((item) => {
	const workListHost = document.querySelector('[data-testid="pp2-primary-work-list-host"]');
	const summaryHost = document.querySelector('[data-testid="pp2-primary-summary-host"]');
	const wl = window.kentender_procurement?.PlanningWorkList;
	const sp = window.kentender_procurement?.PlanningSelectedSummaryPanel;
	if (!workListHost || !summaryHost || !wl || !sp) throw new Error('Planning APIs unavailable');
	wl.render(workListHost, {
		items: [item],
		slug: 'packages',
		onSelect: (_id, it) => {
			sp.render(summaryHost, { summary: sp.summaryFromWorkItem(it) });
		},
	});
}, FIXTURE_ITEM);
await page.getByTestId('pp2-work-list-row').click();
await page.waitForSelector('[data-testid="pp2-selected-summary-title"]', { timeout: 30_000 });
await page.screenshot({
	path: path.join(outDir, 'p5b004_packages_selected_summary_mcp.png'),
	fullPage: true,
});
console.log('saved p5b004_packages_selected_summary_mcp.png');
await browser.close();
console.log('done');
