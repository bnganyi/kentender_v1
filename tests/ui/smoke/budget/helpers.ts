import { execSync } from "node:child_process";
import path from "node:path";

import { expect, Page } from "@playwright/test";

/**
 * Shared plumbing for the BUD-CHG-001 v1.9 §16 browser journeys.
 *
 * Fixtures come from `kentender_budget.seeds.playwright_ui_fixtures`, which
 * puts the §15.3 Ministry of Health budget back into a documented state
 * before each spec and guarantees the §15.1 actors can log in: Josphat Mwangi
 * (Budget Officer + Finance Confirmation Officer), Beatrice Kamau (Budget
 * Approver), Naomi Chebet (Auditor) and Samuel Otieno (no Budget
 * responsibility, the Forbidden fixture actor) — the canonical register's
 * own, never a module-owned duplicate.
 *
 * Every spec mutates the one canonical budget, so the suite runs with one
 * worker and each spec file resets its own starting state.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_budget.seeds.playwright_ui_fixtures";

export const PASSWORD = "Test@123";
export const OFFICER = "josphat.mwangi@moh.example.test";
export const APPROVER = "beatrice.kamau@moh.example.test";
export const AUDITOR = "naomi.chebet@moh.example.test";
export const NOBODY = "samuel.otieno@moh.example.test";
export const ADMIN = "Administrator";
export const CANONICAL_FY = "2027-2028";
export const CANONICAL_BUDGET = "MOH-BUD-2027-001";
export const RETURN_REASON = "Attach the signed transfer instrument; the uploaded file is the September baseline approval, not the March transfer.";

export function bench(command: string): string {
	try {
		return execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} ${command}`, { stdio: "pipe", timeout: 300_000, encoding: "utf-8" });
	} catch (error: any) {
		const stderr = (error?.stderr || "").toString().trim();
		const stdout = (error?.stdout || "").toString().trim();
		throw new Error(`bench ${command} failed\n${stderr || stdout || error?.message}`);
	}
}

function parseResult<T>(fn: string, output: string): T {
	const line = output.trim().split("\n").pop() || "";
	try {
		return JSON.parse(line) as T;
	} catch (error) {
		throw new Error(`${fn}: could not parse bench execute output:\n${output}`);
	}
}

export interface DefaultFixture {
	budget: string;
	budget_code: string;
	fiscal_year: string;
	version: string;
	version_code: string;
	dhi_line: string;
	dhi_code: string;
	hwd_line: string;
	hwd_code: string;
}
export interface IsolatedBudget extends DefaultFixture {
	version_number: number;
}
export interface PendingFixture extends DefaultFixture {
	pending: IsolatedBudget;
	return_reason?: string;
}
export interface SuccessorFixture extends DefaultFixture {
	v2: string;
	v2_code: string;
	v2_number: number;
	reservation: string;
	return_reason?: string;
	shortfall?: number;
}
export interface ClosureFixture extends DefaultFixture {
	closure: IsolatedBudget;
	remaining_total?: number;
	active_commitments_total?: number;
}
export interface ConversionFixture extends DefaultFixture {
	conversion: IsolatedBudget;
	reservation: string;
	requires_review?: boolean;
}
export interface EmptyYearFixture extends DefaultFixture {
	empty_fiscal_year: string;
}

/** Rebuild one fixture and return its ids — never hardcode a reference. */
export function resetFixture<T = DefaultFixture>(fn: string): T {
	return parseResult<T>(fn, bench(`execute ${FIXTURES}.${fn}`));
}

export async function login(page: Page, user: string, password?: string): Promise<void> {
	// Administrator keeps the site's own password (.env.ui); every fixture actor
	// uses the standard test password. The request context shares the page's
	// cookies, so no login/logout probe ever reaches the page console.
	const pwd = password || (user === ADMIN ? process.env.UI_ADMIN_PASSWORD || PASSWORD : PASSWORD);
	await page.request.get("/api/method/logout", { failOnStatusCode: false });
	const response = await page.request.post("/api/method/login", { data: { usr: user, pwd }, failOnStatusCode: false });
	expect(response.status(), `login as ${user}`).toBe(200);
}

/** Pick the financial year the screen should show (the filter is local, never a gate). */
export async function selectYear(page: Page, fy: string): Promise<void> {
	await page.evaluate((year) => window.localStorage.setItem("kt-budget-fiscal-year", year), fy);
}

export async function gotoBudget(page: Page, route = ""): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto(`/app/budget-funding${route}`, { waitUntil: "domcontentloaded" });
}

/**
 * Wait for the page-ready hook, never for networkidle (AGENTS.md §6.7). The
 * root shell exposes `data-screen`; each screen exposes `data-loading`
 * (skeleton, only when it has nothing to show yet) and `data-refreshing`.
 */
export async function expectScreen(page: Page, screen: "workspace" | "register" | "editor" | "detail" | "closure" | "review" | "line"): Promise<void> {
	await expect(page.locator('[data-testid="bud-shell"]')).toHaveAttribute("data-screen", screen, { timeout: 30_000 });
	const testid = { workspace: "bud-ws", register: "bud-reg", editor: "bud-editor", detail: "bud-detail", closure: "bud-close", review: "bud-task", line: "bud-line" }[screen];
	const el = page.locator(`[data-testid="${testid}"]`);
	await expect(el).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
	await expect(el).toHaveAttribute("data-refreshing", "false", { timeout: 30_000 });
}

/** KT-STD-001 §3A.2 — a page-load denial is never a modal. */
export async function expectNoFrappeModal(page: Page): Promise<void> {
	await expect(page.locator(".modal.show")).toHaveCount(0);
	await expect(page.locator("text=Not permitted")).toHaveCount(0);
}

/**
 * Zero page console errors is release evidence. Frappe's dev server echoes
 * socket.io polling 404s and a sidebar divider `<img src=undefined>` on every
 * Desk page; both are framework noise, not page defects.
 */
export function collectConsoleErrors(page: Page): string[] {
	const errors: string[] = [];
	page.on("console", (msg) => {
		if (msg.type() !== "error") return;
		const url = (msg.location && msg.location().url) || "";
		const text = `${msg.text()} @ ${url}`;
		if (/socket\.io|xhr poll error|src=undefined|\/undefined\b/.test(text)) return;
		errors.push(text);
	});
	page.on("pageerror", (err) => errors.push(`pageerror: ${err.message}`));
	return errors;
}

/** A structurally valid one-page PDF — Frappe validates uploaded PDFs with pypdf. */
const MINIMAL_PDF_BASE64 = "JVBERi0xLjQKMSAwIG9iago8PC9UeXBlL0NhdGFsb2cvUGFnZXMgMiAwIFI+PgplbmRvYmoKMiAwIG9iago8PC9UeXBlL1BhZ2VzL0tpZHNbMyAwIFJdL0NvdW50IDE+PgplbmRvYmoKMyAwIG9iago8PC9UeXBlL1BhZ2UvUGFyZW50IDIgMCBSL01lZGlhQm94WzAgMCA1OTUgODQyXS9Db250ZW50cyA0IDAgUi9SZXNvdXJjZXM8PC9Gb250PDwvRjEgNSAwIFI+Pj4+Pj4KZW5kb2JqCjQgMCBvYmoKPDwvTGVuZ3RoIDk2Pj5zdHJlYW0KQlQgL0YxIDE0IFRmIDYwIDc2MCBUZCAoS2VuVGVuZGVyIGRlbW8gYXBwcm92YWwgZG9jdW1lbnQgLSBmaXh0dXJlLCBub3QgYSByZWFsIGluc3RydW1lbnQpIFRqIEVUCmVuZHN0cmVhbQplbmRvYmoKNSAwIG9iago8PC9UeXBlL0ZvbnQvU3VidHlwZS9UeXBlMS9CYXNlRm9udC9IZWx2ZXRpY2E+PgplbmRvYmoKeHJlZgowIDYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDA5IDAwMDAwIG4gCjAwMDAwMDAwNTQgMDAwMDAgbiAKMDAwMDAwMDEwNSAwMDAwMCBuIAowMDAwMDAwMjE3IDAwMDAwIG4gCjAwMDAwMDAzNjAgMDAwMDAgbiAKdHJhaWxlcjw8L1NpemUgNi9Sb290IDEgMCBSPj4Kc3RhcnR4cmVmCjQyMwolJUVPRgo=";

/** Attach the approval document through Frappe's own uploader dialog. */
export async function attachDocument(page: Page, triggerTestId: string, fileName = "approval.pdf"): Promise<void> {
	await page.getByTestId(triggerTestId).click();
	const dialog = page.locator(".modal.show");
	await dialog.waitFor({ state: "visible", timeout: 15_000 });
	await dialog.locator("input[type=file]").first().setInputFiles({ name: fileName, mimeType: "application/pdf", buffer: Buffer.from(MINIMAL_PDF_BASE64, "base64") });
	const upload = dialog.locator("button:has-text('Upload')").first();
	await upload.waitFor({ state: "visible", timeout: 15_000 });
	await upload.click();
	await expect(dialog).toHaveCount(0, { timeout: 30_000 });
}
