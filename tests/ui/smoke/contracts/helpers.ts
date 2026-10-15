import fs from 'node:fs';
import { expect, type Browser, type Page } from '@playwright/test';
import { login } from '../../helpers/auth';

// Shared by the Contract Management browser specs (plan Phase 4 and 5): the world the builder wrote, one session per person, the menu path to a contract, and a button press that waits for the server.
// Run `make cm-ui-world` first (the people, the ERPNext world and the received Award packages); `make cm-ui-gate` does both and cleans up.
export const WORLD = process.env.CM_UI_WORLD || 'artifacts/cm-ui-world.json';
export const world = fs.existsSync(WORLD) ? JSON.parse(fs.readFileSync(WORLD, 'utf8')) : null;
export const today = new Date().toISOString().slice(0, 10);

export const board = (page: Page, id: string) => page.getByTestId(`cm-board-${id}`);
export const attr = (name: string) => `[data-testid="${name}"]`;

export async function as<T>(browser: Browser, persona: string, run: (page: Page) => Promise<T>): Promise<T> {
	const context = await browser.newContext();
	const page = await context.newPage();
	const problems: string[] = [];
	page.on('pageerror', (error) => problems.push(error.message));
	page.on('framenavigated', (frame) => {
		if (frame === page.mainFrame() && /\/app\/(contract-|purchase-|payment-)/.test(frame.url())) problems.push(`sent to a Desk form: ${frame.url()}`);
	});
	try {
		await login(page, world.people[persona], world.password);
		const result = await run(page);
		expect(problems, `${persona}: no page error and no Desk form`).toEqual([]);
		return result;
	} finally {
		await context.close();
	}
}

/** From the menu, never by URL: Home, the "Contract Management" item, then the contract. */
export async function openContract(page: Page, contract: string, view: 'My work' | 'All contracts' = 'All contracts') {
	await page.goto('/app/home');
	await page.locator('.body-sidebar').getByText('Contract Management', { exact: true }).click();
	await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'workspace');
	if (view === 'All contracts') await page.getByTestId('cm-view-1').click(); // the list opens on My work, as the board draws it
	await expect(page.getByTestId(`cm-row-${contract}`)).toBeVisible();
	await page.getByTestId(`cm-row-${contract}`).getByRole('link', { name: contract }).click();
	await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'board');
}

/** The supplier's side is the supplier portal, from its own header: sign in, the "Contracts" item, the contract. */
export async function openAsSupplier(page: Page, contract: string) {
	await page.goto('/account');
	await page.locator('[data-kt-portal-nav="contracts"]').click();
	await expect(page).toHaveURL(/\/supplier\/contracts/);
	await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'workspace');
	await page.getByTestId(`cm-row-${contract}`).getByRole('link', { name: contract }).click();
	await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'board');
}

export const tab = async (page: Page, name: string) => {
	await page.getByTestId(`cm-tab-${name.toLowerCase()}`).click();
	await expect(page.getByTestId('cm-root')).toHaveAttribute('data-refreshing', 'false');
};
/** Click a button that runs commands and wait until the server has answered all of them and the screen has drawn the outcome (a refusal would stay on the page). */
export const press = async (page: Page, testid = 'cm-primary', commands = 1) => {
	let answered = 0;
	const count = (response: { url(): string }) => {
		if (response.url().includes('run_contract_command')) answered++;
	};
	page.on('response', count);
	await page.getByTestId(testid).click();
	await expect.poll(() => answered, { timeout: 30_000 }).toBeGreaterThanOrEqual(commands);
	page.off('response', count);
	await expect(page.getByTestId('cm-root')).toHaveAttribute('data-busy', 'false');
	await expect(page.getByTestId('cm-root')).toHaveAttribute('data-refreshing', 'false');
	expect(await page.getByTestId('cm-refusal').allInnerTexts(), 'the server accepted the command').toEqual([]);
};
export const nextStep = (page: Page) => page.getByTestId('cm-next-step');

/** A small valid PDF (a labelled one-page document), the signed copy or the guarantee a person uploads. */
export function pdf(label: string): { name: string; mimeType: string; buffer: Buffer } {
	const text = `KenTender evidence for a browser walk: ${label}`.replace(/[()]/g, '[');
	const stream = `BT /F1 12 Tf 72 720 Td (${text}) Tj ET`;
	const objects = [
		'<< /Type /Catalog /Pages 2 0 R >>',
		'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
		'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
		`<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`,
		'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
	];
	let out = '%PDF-1.4\n';
	const offsets: number[] = [];
	objects.forEach((body, i) => {
		offsets.push(out.length);
		out += `${i + 1} 0 obj\n${body}\nendobj\n`;
	});
	const xref = out.length;
	out += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n` + offsets.map((o) => `${String(o).padStart(10, '0')} 00000 n \n`).join('');
	out += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
	return { name: `cm-ui-${label.replace(/\W+/g, '-')}.pdf`, mimeType: 'application/pdf', buffer: Buffer.from(out, 'latin1') };
}
