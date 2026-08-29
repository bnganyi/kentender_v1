import { execSync } from "node:child_process";
import path from "node:path";

import { expect, Page } from "@playwright/test";

/**
 * Shared plumbing for the NDS-CHG-001 v1.1 §10 browser smoke specs.
 *
 * Fixtures come from `departmental_needs.seeds.playwright_ui_fixtures`, which
 * owns records under **PE-CGKIS** — never the §14.3 demo Needs. These specs
 * decide real tasks and overwrite an intake window, and pointing them at the
 * demo seed left it changed and the Python suite red (DEBT-07). Isolation is by
 * Procuring Entity rather than namespace alone, because `need_reference` is
 * generated per PE and financial year and the §14 seed asserts its own
 * sequence.
 *
 * Each fixture resets and rebuilds through the real §8.2 commands, so a spec
 * starts from the documented state no matter what ran before it.
 *
 * **Run these with one worker** — `npm run test:ui:smoke:nds`. Every fixture
 * rebuilds the same PE-CGKIS Need, so two spec *files* running concurrently
 * (playwright.config.ts allows 2 workers, and `fullyParallel: false` only
 * serialises within a file) reset each other mid-test: observed as a review
 * task screen resolving to the withdrawal route. The alternative is a separate
 * fixture entity per spec file, as kentender_budget does; one worker is the
 * cheaper answer for a suite this size.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.departmental_needs.seeds.playwright_ui_fixtures";

function bench(command: string): string {
	try {
		return execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} ${command}`, {
			stdio: "pipe",
			timeout: 300_000,
			encoding: "utf-8",
		});
	} catch (error: any) {
		// execSync's own message is just the command line; the useful part is
		// the traceback bench printed. Without this a fixture failure looks
		// identical to a product failure in the report.
		const stderr = (error?.stderr || "").toString().trim();
		const stdout = (error?.stdout || "").toString().trim();
		throw new Error(`bench ${command} failed\n${stderr || stdout || error?.message}`);
	}
}

/** Rebuild one Playwright fixture. Safe to call from any prior state. */
export function resetFixture(fn: string): void {
	bench(`execute ${FIXTURES}.${fn}`);
}

/** Remove every Playwright-owned row, leaving the §14 seed untouched. */
export function clearFixtures(): void {
	bench(`execute ${FIXTURES}.reset_all --kwargs "{'commit': True}"`);
}

/** The §10 canonical route. `/app` is rewritten to `/desk` by Frappe itself. */
export async function gotoNeeds(page: Page, route = ""): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto(`/app/departmental-needs${route}`, { waitUntil: "domcontentloaded" });
}

/**
 * Wait for the page-ready hook rather than a visual class (§16.1).
 *
 * `data-screen` is set by the root component from the resolved route, so this
 * also asserts the router picked the screen the spec means to test — a wrong
 * route otherwise shows up much later as a confusing missing-element failure.
 */
export async function expectScreen(page: Page, screen: string): Promise<void> {
	const shell = page.locator('[data-testid="nds-shell"]');
	await expect(shell).toHaveAttribute("data-screen", screen, { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
}

/**
 * §12.1 — a user authorised in several departments must choose one before any
 * row is fetched. The picker is skipped silently when only one context exists,
 * so specs can call this unconditionally.
 */
export async function selectContext(
	page: Page,
	organisationUnit: string,
	financialYear = "FY-2027-2028",
): Promise<void> {
	const shell = page.locator('[data-testid="nds-shell"]');
	const settle = () =>
		expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
	await settle();

	if ((await shell.getAttribute("data-screen")) !== "context-selection") return;

	// §12.1 — the context is PE/OU *and* Financial Year, and choosing either
	// one re-requests the workspace. The year goes first: choosing a context
	// reloads and re-renders the picker, so grabbing the year select before
	// that settles races the re-render.
	const years = page.locator('[data-testid="nds-fy-select"]');
	if (await years.isVisible().catch(() => false)) {
		await years.selectOption(financialYear);
		await settle();
	}

	const picker = page.locator('[data-testid="nds-context-select"]');
	if (await picker.isVisible().catch(() => false)) {
		// The option value is `${procuring_entity}::${organisation_unit}` — the
		// identifiers, not the display labels, so this does not break when a
		// Procuring Entity or unit is renamed.
		const value = await picker
			.locator("option")
			.evaluateAll(
				(options, unit) =>
					(options as HTMLOptionElement[]).find((option) =>
						option.value.endsWith(`::${unit}`),
					)?.value ?? "",
				organisationUnit,
			);
		expect(value, `no context option for ${organisationUnit}`).not.toEqual("");
		await picker.selectOption(value);
		await settle();
	}

	await expect(shell).not.toHaveAttribute("data-screen", "context-selection", {
		timeout: 30_000,
	});
}

/** §16.3 — zero page console errors is part of the release evidence. */
export function collectConsoleErrors(page: Page): string[] {
	const errors: string[] = [];
	page.on("console", (message) => {
		if (message.type() === "error") errors.push(message.text());
	});
	page.on("pageerror", (error) => errors.push(String(error)));
	return errors;
}
