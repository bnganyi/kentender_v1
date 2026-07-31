import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const NATIVE_RAIL = ".body-sidebar";

test.describe("Procurement Home — functional Desk page", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1280, height: 900 });
		await loginAsAdministrator(page);
	});

	test("loads Stitch content order inside Procurement rail with Home active", async ({ page }) => {
		test.setTimeout(120_000);
		await page.goto("/desk/kt-procurement-home", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-ph-root")).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId("kt-ph-title")).toHaveText("Procurement Home");

		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator(`${NATIVE_RAIL} .sidebar-header .header-title`)).toHaveText(
			/^\s*Procurement\s*$/i
		);
		await expect(
			page.locator(`${NATIVE_RAIL} .sidebar-item-container[data-id="Home"] > .standard-sidebar-item`)
		).toHaveClass(/active-sidebar/, { timeout: 15_000 });

		// Home is Available — no Planned badge on the Home row.
		const homeText = await page
			.locator(`${NATIVE_RAIL} .sidebar-item-container[data-id="Home"]`)
			.innerText();
		expect(homeText).not.toMatch(/\bPlanned\b/);

		await expect(page.getByTestId("kt-ph-actions")).toBeVisible();
		await expect(page.getByTestId("kt-ph-pipeline")).toBeVisible();
		await expect(page.getByTestId("kt-ph-deadlines")).toBeVisible();

		// Browser tab title must be KenTender-branded (not bare Frappe).
		await expect.poll(async () => page.title()).toMatch(/^KenTender\b/);

		// Pipeline footer lifecycle link is not in Stitch main content.
		const rootText = await page.getByTestId("kt-ph-root").innerText();
		expect(rootText).not.toMatch(/VIEW PROCUREMENT LIFECYCLE/i);
		expect(rootText).not.toMatch(/View procurement lifecycle/i);

		const order = await page.evaluate(() => {
			const root = document.querySelector("#kt-ph-root");
			if (!root) return [];
			const ids = ["kt-ph-header", "kt-ph-actions", "kt-ph-pipeline", "kt-ph-split"];
			return ids.map((id) => {
				const el = root.querySelector(`[data-testid="${id}"], #${id}`);
				return el ? Math.round(el.getBoundingClientRect().top) : -1;
			});
		});
		expect(order[0]).toBeGreaterThanOrEqual(0);
		expect(order[1]).toBeGreaterThan(order[0]);
		expect(order[2]).toBeGreaterThan(order[1]);
		expect(order[3]).toBeGreaterThan(order[2]);

		// Stitch deadline rows: action Material icon + trailing chevron_right.
		const deadlineRows = page.getByTestId("kt-ph-deadline-row");
		const deadlineCount = await deadlineRows.count();
		if (deadlineCount > 0) {
			const first = deadlineRows.first();
			await expect(first.locator(".kt-ph-deadline__action .material-symbols-outlined")).toBeVisible();
			await expect(first.locator(".kt-ph-deadline__chevron")).toHaveText("chevron_right");
		}

		// No Approve/Reject state-changing actions on Home.
		expect(rootText).not.toMatch(/\bApprove\b/);
		expect(rootText).not.toMatch(/\bReject\b/);
	});
});
