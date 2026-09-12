import { test, expect, Page } from "@playwright/test";
import { login, loginAsAdministrator } from "../../helpers/auth";
import { collectConsoleErrors } from "../planning/helpers";

/**
 * AUTH-ADR-001 §10/§12 — Technical record search, plus a sweep confirming
 * every module workspace a technical user (Administrator/System Manager)
 * opens renders its own content rather than a Forbidden/Not-found panel.
 *
 * (a) is a smoke sweep, not a per-module fidelity check: each app owns its
 * own workspace's design-fidelity/AC coverage elsewhere. This only guards
 * the specific regression this change could introduce — a technical user
 * newly refused something they could already reach.
 *
 * Real record references below were read from the live dev site
 * (`bench --site kentender.midas.com execute frappe.get_all ...`), not
 * invented, per the task's read-only lookup requirement. Route assertions
 * were cross-checked against the actual resolvers each module registered
 * (`kentender_procurement.{departmental_needs,procurement_planning,
 * procurement_requisitions,tender_preparation}.services.technical_read`) —
 * in particular, Procurement Requisition and Prepared Tender resolve the
 * doc name to its own business reference before building the route
 * (`_requisition_route`/`_tender_route`), so the URL segment is
 * `requisition_reference`/`tender_reference`, not the PRQ-#####/TPR-#####
 * doc name. Still flagged for reconciliation in the task report, since this
 * spec was written without running it.
 */

const WORKSPACES = [
	"/app/strategy",
	"/app/budget-funding",
	"/app/departmental-needs",
	"/app/procurement-planning",
	"/app/procurement-requisitions",
	"/app/tender-preparation",
	"/app/system-setup",
];

/** No hard per-app readiness contract is assumed here (each module owns its
 *  own shell testid) — settle on domcontentloaded plus a fixed window long
 *  enough for a Vue-in-Desk screen's own async load to resolve and paint
 *  whatever verdict it reached, then assert none of it is a refusal. */
async function assertNotForbidden(page: Page): Promise<void> {
	await page.waitForTimeout(3000);
	await expect(page.locator('[data-testid$="-forbidden"]')).toHaveCount(0);
	await expect(page.getByText(/isn't available to you/i)).toHaveCount(0);
	await expect(page.getByText(/not found/i)).toHaveCount(0);
	await expect(page.locator(".modal.show")).toHaveCount(0);
}

async function gotoTechnicalSearch(page: Page): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto("/app/technical-search", { waitUntil: "domcontentloaded" });
}

async function runSearch(page: Page, query: string): Promise<void> {
	await page.locator('[data-testid="kt-ts-input"]').fill(query);
	await page.locator('[data-testid="kt-ts-search"]').click();
}

test.describe.serial("Technical record search + technical-user access sweep", () => {
	test("Administrator sees no Forbidden/Not-found panel on any module workspace", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsAdministrator(page);

		for (const workspace of WORKSPACES) {
			await page.goto(workspace, { waitUntil: "domcontentloaded" });
			await assertNotForbidden(page);
		}

		expect(errors, `console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Administrator: Technical record search Empty state, then finds records by reference across modules", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsAdministrator(page);

		await gotoTechnicalSearch(page);
		await expect(page.locator('[data-testid="kt-ts-empty"]')).toBeVisible({ timeout: 20_000 });
		expect(page.url()).toMatch(/\/technical-search$/);

		// Departmental Need — NDS-MOH-2027-0001 (confirmed live: current_state
		// "Accepted for planning"). Route: departmental-needs/<need_reference>
		// (kentender_procurement.departmental_needs.services.technical_read._need_route).
		await runSearch(page, "NDS-MOH-2027-0001");
		const ndsRow = page.locator('[data-testid="kt-ts-row"]', { hasText: "NDS-MOH-2027-0001" });
		await expect(ndsRow).toBeVisible({ timeout: 20_000 });
		await ndsRow.locator('[data-testid="kt-ts-open"]').click();
		await expect(page).toHaveURL(/\/departmental-needs\/NDS-MOH-2027-0001$/, { timeout: 20_000 });
		// AUTH-ADR-001 §8 — technical read grants no business action: no
		// approval/submission control renders for this Administrator session.
		await expect(
			page.locator(
				'[data-testid$="-submit"], [data-testid$="-approve"], [data-testid$="-accept"], [data-testid$="-return"], [data-testid$="-withdraw"], [data-testid$="-reject"], [data-testid$="-revoke"], [data-testid$="-decline"]'
			)
		).toHaveCount(0);

		// Departmental Plan (DPP) — DPP-MOH-00188-2027-001. Route:
		// departmental-procurement-plan/<dpp_reference> (._dpp_route).
		await gotoTechnicalSearch(page);
		await runSearch(page, "DPP-MOH-00188-2027-001");
		const dppRow = page.locator('[data-testid="kt-ts-row"]', { hasText: "DPP-MOH-00188-2027-001" });
		await expect(dppRow).toBeVisible({ timeout: 20_000 });
		await dppRow.locator('[data-testid="kt-ts-open"]').click();
		await expect(page).toHaveURL(/\/departmental-procurement-plan\/DPP-MOH-00188-2027-001$/, {
			timeout: 20_000,
		});

		// Annual Plan — PLN-MOH-2027-001 ("Ministry of Health Annual Procurement
		// Plan 2027/28"). Route: annual-procurement-plan/<plan_reference> (._plan_route).
		await gotoTechnicalSearch(page);
		await runSearch(page, "PLN-MOH-2027-001");
		const planRow = page.locator('[data-testid="kt-ts-row"]', { hasText: "PLN-MOH-2027-001" });
		await expect(planRow).toBeVisible({ timeout: 20_000 });
		await planRow.locator('[data-testid="kt-ts-open"]').click();
		await expect(page).toHaveURL(/\/annual-procurement-plan\/PLN-MOH-2027-001$/, { timeout: 20_000 });

		// Procurement Requisition — business reference REQ-MOH-2027-002-001,
		// doc name PRQ-22169. Route: procurement-requisitions/<requisition_reference>
		// (kentender_procurement.procurement_requisitions.services.technical_read
		// ._requisition_route resolves the doc name to its business reference).
		await gotoTechnicalSearch(page);
		await runSearch(page, "REQ-MOH-2027-002-001");
		const reqRow = page.locator('[data-testid="kt-ts-row"]', { hasText: "REQ-MOH-2027-002-001" });
		await expect(reqRow).toBeVisible({ timeout: 20_000 });
		await reqRow.locator('[data-testid="kt-ts-open"]').click();
		await expect(page).toHaveURL(/\/procurement-requisitions\/REQ-MOH-2027-002-001$/, { timeout: 20_000 });

		// Prepared Tender — business reference TND-MOH-2027-002, doc name
		// TPR-22181. Route: tender-preparation/<tender_reference> (same
		// resolve-to-business-reference pattern as Procurement Requisition
		// above, in kentender_procurement.tender_preparation.services.technical_read).
		await gotoTechnicalSearch(page);
		await runSearch(page, "TND-MOH-2027-002");
		const tprRow = page.locator('[data-testid="kt-ts-row"]', { hasText: "TND-MOH-2027-002" });
		await expect(tprRow).toBeVisible({ timeout: 20_000 });
		await tprRow.locator('[data-testid="kt-ts-open"]').click();
		await expect(page).toHaveURL(/\/tender-preparation\/TND-MOH-2027-002$/, { timeout: 20_000 });

		expect(errors, `console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Administrator: a query with no match shows No match, never an empty success", async ({ page }) => {
		await loginAsAdministrator(page);
		await gotoTechnicalSearch(page);
		await runSearch(page, "NOTHING-MATCHES-THIS-QUERY-0000");
		const nomatch = page.locator('[data-testid="kt-ts-nomatch"]');
		await expect(nomatch).toBeVisible({ timeout: 20_000 });
		await expect(nomatch).toContainText('No record matches "NOTHING-MATCHES-THIS-QUERY-0000"');
		await expect(page.locator('[data-testid="kt-ts-row"]')).toHaveCount(0);
	});

	test("a non-technical user (Grace Wanjiku) gets the Forbidden panel", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(
			page,
			process.env.UI_PLN_AUTHOR_USER || "grace.wanjiku@moh.example.test",
			process.env.UI_PLN_AUTHOR_PASSWORD || "Test@123"
		);
		await gotoTechnicalSearch(page);
		await expect(page.locator('[data-testid="kt-ts-forbidden"]')).toBeVisible({ timeout: 20_000 });
		await expect(page.locator('[data-testid="kt-ts-forbidden"]')).toContainText(
			"You do not have access to Technical record search"
		);
		expect(errors, `console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
