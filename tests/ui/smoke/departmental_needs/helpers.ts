import { execSync } from "node:child_process";
import path from "node:path";

import { expect, Page } from "@playwright/test";

/**
 * Shared plumbing for the NDS-CHG-001 v1.6 §10 browser smoke specs.
 *
 * Fixtures come from `departmental_needs.seeds.playwright_ui_fixtures`, which
 * owns records under a dedicated **Organisation Unit**
 * ("Playwright — Departmental Needs") — never the §14.3 demo Needs. These
 * specs decide real tasks and overwrite the Needs-submission state, so
 * pointing them at the demo seed left it changed and the Python suite red
 * (DEBT-07).
 *
 * AUTH-ADR-001 v1.6 §1.1 makes the site exactly one implicit Procuring
 * Entity, so the old PE-CGKIS isolation trick (a dedicated Procuring Entity
 * with its own `need_reference` counter) no longer exists as a mechanism.
 * Isolation is now by Organisation Unit plus `fixture_namespace` only — and
 * because CFG-BR-010 keeps at most one Fiscal Year Open at a time, every
 * fixture here necessarily shares the *same* open Fiscal Year, and therefore
 * the *same* `need_reference` counter, as the §14.3 default profile and any
 * other fixture family (see FOLLOW_UPS.md FU-16/FU-17). A spec must never
 * hardcode an expected reference — always read it back from the fixture
 * command's own JSON return value via `resetFixture()`.
 *
 * Each fixture resets and rebuilds through the real §8.2 commands, so a spec
 * starts from the documented state no matter what ran before it.
 *
 * **Run these with one worker** — `npm run test:ui:smoke:nds` (FOLLOW_UPS.md
 * FU-01). Every fixture rebuilds the same Organisation Unit's Need(s), so two
 * spec *files* running concurrently (playwright.config.ts allows 2 workers,
 * and `fullyParallel: false` only serialises within a file) reset each
 * other's fixture mid-test — observed as a review task screen resolving to
 * the withdrawal route, a plausible-looking wrong page rather than a crash.
 * The alternative is a separate fixture entity per spec file, as
 * `kentender_budget` does; one worker is the cheaper answer for a suite this
 * size.
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

/**
 * Rebuild one Playwright fixture. Safe to call from any prior state.
 *
 * Every fixture builder in `playwright_ui_fixtures.py` returns a plain dict
 * (e.g. `{"need": "NDS-MOH-2027-0005", "reference": "NDS-MOH-2027-0005",
 * "task": "NDT-..."}`), which `bench execute` prints to stdout as one JSON
 * line. A spec must read the real reference/task ids from this return value —
 * never hardcode one (see the module doc comment above).
 */
export function resetFixture<T = Record<string, unknown>>(fn: string): T {
	const output = bench(`execute ${FIXTURES}.${fn}`).trim();
	try {
		return JSON.parse(output) as T;
	} catch (error) {
		throw new Error(`resetFixture(${fn}): could not parse bench execute output as JSON:\n${output}`);
	}
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
	// A revisited screen renders its last payload at once and revalidates in
	// place; wait for that refresh too so assertions read the fresh rows.
	await expect(shell).toHaveAttribute("data-refreshing", "false", { timeout: 30_000 });
}

/**
 * §12.1 — a caller authorised in several departments must choose one before
 * any row is fetched.
 *
 * Live-verified 2026-09-04 (not assumed): every current fixture actor
 * (`AUTHOR`/`REVIEWER`, each granted exactly one Organisation Unit via
 * `_actor(..., scoped=True)`) never sees this picker at all — the workspace's
 * `data-screen` resolves straight to `"workspace"` with zero
 * `[data-testid="nds-context-picker"]` elements rendered, because
 * `kentender_core.services.working_context`'s single-option auto-resolve
 * (mirrored by `DepartmentalNeeds.vue`'s own `selectionRequired`) never shows
 * a picker for a one-option scope, and the site carries exactly one Open
 * Fiscal Year at a time (CFG-BR-010), so `financialYears.length` is never
 * greater than one either. There is therefore no stable identifier for a
 * caller to supply today — the old hardcoded Organisation Unit argument is
 * gone.
 *
 * This helper stays deliberately defensive rather than being deleted: it
 * remains a no-op whenever the shell is not on `"context-selection"` (every
 * call today), and picks the first selectable option in each control when it
 * is — so a future fixture actor granted more than one Organisation Unit, or
 * a second concurrently-open Fiscal Year, does not silently strand every
 * calling spec at an unhandled picker.
 */
export async function selectContext(page: Page): Promise<void> {
	const shell = page.locator('[data-testid="nds-shell"]');
	const settle = async () => {
		await expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
		await expect(shell).toHaveAttribute("data-refreshing", "false", { timeout: 30_000 });
	};
	await settle();

	if ((await shell.getAttribute("data-screen")) !== "context-selection") return;

	// The year goes first: choosing a department reloads and re-renders the
	// picker, so grabbing the year select before that settles races the
	// re-render.
	const years = page.locator('[data-testid="nds-fy-select"]');
	if (await years.isVisible().catch(() => false)) {
		const value = await years.locator("option:not([disabled])").first().getAttribute("value");
		expect(value, "no selectable Financial Year option").not.toBeNull();
		await years.selectOption(value as string);
		await settle();
	}

	// ContextPicker.vue's option value is the bare `organisation_unit` id
	// (no Procuring Entity component any more).
	const picker = page.locator('[data-testid="nds-context-select"]');
	if (await picker.isVisible().catch(() => false)) {
		const value = await picker.locator("option:not([disabled])").first().getAttribute("value");
		expect(value, "no selectable department option").not.toBeNull();
		await picker.selectOption(value as string);
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
		// "Failed to load resource" alone is undiagnosable — name the URL.
		const url = message.location()?.url;
		// Known phantom, not ours: frappe's sidebar app-switcher builds a
		// DETACHED jQuery fragment whose one icon-less item renders
		// <img src="undefined">; the browser fetches /undefined (404) on every
		// Desk load though nothing enters the DOM (traced 2026-08-30 via CDP:
		// parser-initiated Image request, no matching element in any frame).
		// It surfaced only intermittently, poisoning unrelated specs.
		if (url && /\/undefined$/.test(url)) return;
		if (message.type() === "error") errors.push(url ? `${message.text()} (${url})` : message.text());
	});
	page.on("pageerror", (error) => errors.push(String(error)));
	return errors;
}
