import { test, expect } from "@playwright/test";
import { login, loginAsAdministrator } from "../../helpers/auth";
import { assertStitchSectionTableChrome } from "../../helpers/stitchDeskChrome";

/**
 * DEM-UI-06 — Routine Budget confirmation on shared demand-review.
 * Section heads: app-wide primary-fixed. Recommendation body: Stitch DEM-UI-06.html.
 * Route: /desk/demand-review/<name>
 */

const ROOT = '[data-testid="kt-dem-ui04-root"]';
const DEFAULT_SEED_PASSWORD = "Test@123";

async function prepareBudgetDemand(page: import("@playwright/test").Page): Promise<{
	demand: string;
	budgetOfficer: string;
}> {
	await loginAsAdministrator(page);
	await page.goto("/desk", { waitUntil: "domcontentloaded" });
	const prepared = await page.evaluate(async () => {
		const r = await (
			window as unknown as {
				frappe: {
					call: (o: { method: string }) => Promise<{
						message?: {
							demand?: string;
							ok?: boolean;
							budget_officer?: string;
							current_stage?: string;
						};
					}>;
				};
			}
		).frappe.call({
			method: "kentender_procurement.demands.api.prepare_budget_confirmation_ui06",
		});
		return {
			demand: r.message?.demand || "",
			budgetOfficer: r.message?.budget_officer || "",
			stage: r.message?.current_stage || "",
		};
	});
	expect(prepared.demand).toBeTruthy();
	expect(prepared.budgetOfficer).toBeTruthy();
	expect(prepared.stage).toBe("Budget Confirmation");
	return { demand: prepared.demand, budgetOfficer: prepared.budgetOfficer };
}

test.describe("DEM-UI-06 Routine Budget confirmation", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("Stitch regions, checkbox gates Confirm, confirm → Final Approval", async ({
		page,
	}) => {
		const { demand, budgetOfficer } = await prepareBudgetDemand(page);
		await page.context().clearCookies();
		await login(
			page,
			budgetOfficer,
			process.env.UI_BUDGET_OFFICER_PASSWORD || DEFAULT_SEED_PASSWORD,
		);
		await page.goto(`/desk/demand-review/${demand}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator(ROOT)).toHaveAttribute(
			"data-kt-dem-review-stage",
			"Budget Confirmation",
		);
		await expect(page.getByTestId("kt-dem-record-header")).toBeVisible();
		await expect(page.getByTestId("kt-dem-stage")).toContainText(/Budget confirmation/i);
		await expect(page.getByTestId("kt-dem-stage")).toContainText(/Current/i);
		await expect(page.getByTestId("kt-dem-business-host")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui05-root")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui06-root")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui06-summary")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui06-condition")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui06-strategy-check")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui06-recommendation")).toBeVisible();

		// Left column: Strategy fully visible (not clipped); Summary must not eat 100% height.
		const leftColLayout = await page.evaluate(() => {
			const col = document.querySelector(".kt-dem-budget-col-left") as HTMLElement | null;
			const summary = document.querySelector(
				'[data-testid="kt-dem-ui06-summary"]',
			) as HTMLElement | null;
			const strategy = document.querySelector(
				'[data-testid="kt-dem-ui06-strategy-check"]',
			) as HTMLElement | null;
			const lineTarget = document.querySelector(
				'[data-kt-dem-label="funding_budget_line_target"]',
			) as HTMLElement | null;
			const aligned = document.querySelector(
				'[data-testid="kt-dem-ui06-strategy-result"]',
			) as HTMLElement | null;
			const condition = document.querySelector(
				'[data-testid="kt-dem-ui06-condition"]',
			) as HTMLElement | null;
			const rows = document.querySelector(".kt-dem-ui06-summary-rows") as HTMLElement | null;
			if (!col || !summary || !strategy || !lineTarget || !aligned || !condition || !rows) {
				return null;
			}
			const cr = col.getBoundingClientRect();
			const sr = summary.getBoundingClientRect();
			const tr = strategy.getBoundingClientRect();
			const lr = lineTarget.getBoundingClientRect();
			const ar = aligned.getBoundingClientRect();
			const lastRow = rows.lastElementChild as HTMLElement | null;
			const lastRowBottom = lastRow ? lastRow.getBoundingClientRect().bottom : 0;
			const condTop = condition.getBoundingClientRect().top;
			return {
				strategyBottomInsideCol: tr.bottom <= cr.bottom + 2,
				alignedBottomInsideStrategy: ar.bottom <= tr.bottom + 2,
				lineTargetBottomInsideStrategy: lr.bottom <= tr.bottom + 2,
				lineTargetHeight: lr.height,
				alignedVisible: ar.height > 8,
				strategyNaturalHeight: tr.height > 120,
				// Only Stitch mt-6 (~24px) between last row and condition — no flex cavern.
				spacerPx: Math.max(0, condTop - lastRowBottom),
			};
		});
		expect(leftColLayout).toBeTruthy();
		expect(leftColLayout!.strategyBottomInsideCol).toBe(true);
		expect(leftColLayout!.alignedBottomInsideStrategy).toBe(true);
		expect(leftColLayout!.lineTargetBottomInsideStrategy).toBe(true);
		expect(leftColLayout!.lineTargetHeight).toBeGreaterThan(12);
		expect(leftColLayout!.alignedVisible).toBe(true);
		expect(leftColLayout!.strategyNaturalHeight).toBe(true);
		expect(leftColLayout!.spacerPx).toBeLessThanOrEqual(40);
		await expect(page.getByTestId("kt-dem-ui06-progress")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui06-signoff")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui06-confirm-checkbox")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui06-no-reserve-note")).toContainText(
			/does not reserve/i,
		);
		await expect(page.getByTestId("kt-dem-ui06-footer")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui06-return")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui06-adjust")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui06-confirm")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui06-adjust-panel")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui06-adjust-line")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui06-apply-adjust")).toBeVisible();

		// View Details → Stitch read-only drawer (Business / Classify / Items / Strategy / PVC).
		await expect(page.getByTestId("kt-dem-view-details")).toBeVisible();
		await page.getByTestId("kt-dem-view-details").click();
		await expect(page.getByTestId("kt-dem-details-drawer")).toBeVisible();
		await expect(page.getByTestId("kt-dem-details-business")).toContainText(
			/Summary of need/i,
		);
		await expect(page.getByTestId("kt-dem-details-classify")).toContainText(
			/Classification/i,
		);
		await expect(page.getByTestId("kt-dem-details-items")).toBeVisible();
		await expect(page.getByTestId("kt-dem-details-items-list").locator("li")).toHaveCount(2, {
			timeout: 10_000,
		});
		await expect(page.getByTestId("kt-dem-details-strategy")).toBeVisible();
		await expect(page.getByTestId("kt-dem-details-pvc")).toBeVisible();
		// Drawer body must scroll (not clip section content); icon must not inherit underline.
		const drawerUx = await page.evaluate(() => {
			const body = document.querySelector(
				".kt-dem-details-drawer-body",
			) as HTMLElement | null;
			const pvc = document.querySelector(
				'[data-testid="kt-dem-details-pvc"]',
			) as HTMLElement | null;
			const link = document.querySelector(
				'[data-testid="kt-dem-view-details"]',
			) as HTMLElement | null;
			const icon = link?.querySelector(
				".material-symbols-outlined",
			) as HTMLElement | null;
			const bcs = body ? getComputedStyle(body) : null;
			if (link) {
				link.dispatchEvent(new Event("mouseover", { bubbles: true }));
			}
			const iconDeco = icon ? getComputedStyle(icon).textDecorationLine : "";
			return {
				overflowY: bcs?.overflowY || "",
				canScroll: !!(body && body.scrollHeight > body.clientHeight + 8),
				pvcFullyInBody: !!(
					body &&
					pvc &&
					pvc.getBoundingClientRect().bottom <=
						body.getBoundingClientRect().bottom + body.scrollHeight
				),
				pvcHeight: pvc ? pvc.getBoundingClientRect().height : 0,
				iconNoUnderline: !iconDeco.includes("underline"),
			};
		});
		expect(drawerUx.overflowY).toMatch(/auto|scroll/);
		expect(drawerUx.canScroll || drawerUx.pvcHeight > 24).toBe(true);
		expect(drawerUx.pvcHeight).toBeGreaterThan(24);
		expect(drawerUx.iconNoUnderline).toBe(true);
		await page.getByTestId("kt-dem-details-close").click();
		await expect(page.getByTestId("kt-dem-details-drawer")).toBeHidden();

		// App-wide chrome: Summary + Strategy + Recommendation + Adjust primary-fixed + square cards.
		await assertStitchSectionTableChrome(page, {
			sectionTestId: "kt-dem-ui06-summary",
			roundedControlTestId: "kt-dem-ui06-adjust",
		});
		await assertStitchSectionTableChrome(page, {
			sectionTestId: "kt-dem-ui06-strategy-check",
		});
		await assertStitchSectionTableChrome(page, {
			sectionTestId: "kt-dem-ui06-recommendation",
		});
		await assertStitchSectionTableChrome(page, {
			sectionTestId: "kt-dem-ui06-adjust-panel",
		});

		// Adjust is a sibling section under the budget stack (not nested under recommendation).
		const adjustLayout = await page.evaluate(() => {
			const stack = document.querySelector(
				'[data-testid="kt-dem-ui06-main"]',
			) as HTMLElement | null;
			const rec = document.querySelector(
				'[data-testid="kt-dem-ui06-recommendation"]',
			) as HTMLElement | null;
			const adj = document.querySelector(
				'[data-testid="kt-dem-ui06-adjust-panel"]',
			) as HTMLElement | null;
			const badge = document.querySelector(
				"[data-kt-dem-funding-alloc-badge]",
			) as HTMLElement | null;
			return {
				sibling: !!(
					stack &&
					rec &&
					adj &&
					stack.contains(rec) &&
					stack.contains(adj) &&
					!rec.contains(adj)
				),
				badgeText: (badge?.textContent || "").trim(),
				badgeActive: !!badge?.classList.contains("is-active"),
			};
		});
		expect(adjustLayout.sibling).toBe(true);
		expect(adjustLayout.badgeText).toMatch(/^Active$/i);
		expect(adjustLayout.badgeActive).toBe(true);

		// Recommend head same height as Summary; Stitch body tiles + visible progress bar.
		const recommendChrome = await page.evaluate(() => {
			const sumHead = document.querySelector(
				'[data-testid="kt-dem-ui06-summary"] > .bg-surface-container-low',
			) as HTMLElement | null;
			const recHead = document.querySelector(
				".kt-dem-ui06-recommend-head",
			) as HTMLElement | null;
			const tiles = document.querySelector(
				'[data-testid="kt-dem-ui06-money-tiles"]',
			) as HTMLElement | null;
			const tile = document.querySelector(
				".kt-dem-ui06-money-tile",
			) as HTMLElement | null;
			const track = document.querySelector(
				".kt-dem-ui06-progress-track",
			) as HTMLElement | null;
			const stack = document.querySelector(
				".kt-dem-ui06-rec-stack",
			) as HTMLElement | null;
			const bars = [
				...document.querySelectorAll("[data-kt-dem-funding-bar]"),
			] as HTMLElement[];
			const sh = sumHead ? getComputedStyle(sumHead) : null;
			const rh = recHead ? getComputedStyle(recHead) : null;
			const tcs = tile ? getComputedStyle(tile) : null;
			const trackCs = track ? getComputedStyle(track) : null;
			const stackCs = stack ? getComputedStyle(stack) : null;
			const tilesCs = tiles ? getComputedStyle(tiles) : null;
			return {
				sumBg: sh?.backgroundColor || "",
				recBg: rh?.backgroundColor || "",
				sumPadY: sh ? parseFloat(sh.paddingTop) + parseFloat(sh.paddingBottom) : 0,
				recPadY: rh ? parseFloat(rh.paddingTop) + parseFloat(rh.paddingBottom) : 0,
				recInset: (rh?.boxShadow || "").includes("inset"),
				tileCols: tilesCs
					? tilesCs.gridTemplateColumns.split(" ").filter(Boolean).length
					: 0,
				tileGapPx: tilesCs ? parseFloat(tilesCs.gap || tilesCs.columnGap || "0") : 0,
				tilePadPx: tcs ? parseFloat(tcs.paddingTop) : 0,
				tileRadiusPx: tcs ? parseFloat(tcs.borderTopLeftRadius) : 0,
				tileBorderTop: tcs?.borderTopWidth || "",
				stackGapPx: stackCs ? parseFloat(stackCs.gap || "0") : 0,
				trackHeightPx: track ? parseFloat(trackCs?.height || "0") : 0,
				barHeightsPx: bars.map((b) => parseFloat(getComputedStyle(b).height || "0")),
				barWidths: bars.map((b) => b.style.width || ""),
			};
		});
		expect(recommendChrome.recBg).toBe("rgb(215, 226, 255)");
		expect(recommendChrome.sumBg).toBe("rgb(215, 226, 255)");
		expect(recommendChrome.recInset).toBe(true);
		// Same vertical padding band as Funding Summary (py-3 + py-3).
		expect(Math.abs(recommendChrome.recPadY - recommendChrome.sumPadY)).toBeLessThanOrEqual(2);
		expect(recommendChrome.tileCols).toBe(4);
		expect(recommendChrome.tileGapPx).toBeGreaterThanOrEqual(8);
		expect(recommendChrome.tilePadPx).toBeGreaterThanOrEqual(12);
		expect(recommendChrome.tileRadiusPx).toBeGreaterThanOrEqual(6);
		expect(recommendChrome.tileBorderTop).toBe("2px");
		expect(recommendChrome.stackGapPx).toBeGreaterThanOrEqual(20);
		expect(recommendChrome.trackHeightPx).toBeGreaterThanOrEqual(10);
		expect(recommendChrome.barHeightsPx.every((h) => h >= 10)).toBe(true);
		expect(recommendChrome.barWidths.some((w) => parseFloat(w) > 0)).toBe(true);

		// Actions inside sign-off card.
		const actionsLayout = await page.getByTestId("kt-dem-ui06-signoff").evaluate((signoff) => {
			const actions = signoff.querySelector(
				'[data-testid="kt-dem-ui06-footer"]',
			) as HTMLElement | null;
			const ret = signoff.querySelector(
				'[data-testid="kt-dem-ui06-return"]',
			) as HTMLElement | null;
			const adjust = signoff.querySelector(
				'[data-testid="kt-dem-ui06-adjust"]',
			) as HTMLElement | null;
			const confirm = signoff.querySelector(
				'[data-testid="kt-dem-ui06-confirm"]',
			) as HTMLElement | null;
			if (!actions || !ret || !adjust || !confirm) {
				return null;
			}
			const sr = signoff.getBoundingClientRect();
			const rr = ret.getBoundingClientRect();
			const ar = adjust.getBoundingClientRect();
			const cr = confirm.getBoundingClientRect();
			const acs = getComputedStyle(adjust);
			const ccs = getComputedStyle(confirm);
			return {
				actionsInsideSignoff: actions.parentElement === signoff,
				footerNotFixed: getComputedStyle(actions).position !== "fixed",
				returnInsideCard: rr.left >= sr.left - 1 && rr.right <= sr.right + 1,
				returnLeftOfAdjust: rr.right <= ar.left + 1,
				adjustLeftOfConfirm: ar.right <= cr.left + 1,
				adjustBg: acs.backgroundColor,
				adjustBorderColor: acs.borderTopColor,
				confirmBg: ccs.backgroundColor,
			};
		});
		expect(actionsLayout).toBeTruthy();
		expect(actionsLayout!.actionsInsideSignoff).toBe(true);
		expect(actionsLayout!.footerNotFixed).toBe(true);
		expect(actionsLayout!.returnInsideCard).toBe(true);
		expect(actionsLayout!.returnLeftOfAdjust).toBe(true);
		expect(actionsLayout!.adjustLeftOfConfirm).toBe(true);
		expect(actionsLayout!.adjustBg).toMatch(/rgb\(255,\s*255,\s*255\)/);
		expect(actionsLayout!.adjustBorderColor).toBe("rgb(115, 119, 129)");
		expect(actionsLayout!.confirmBg).toBe("rgb(0, 31, 72)");

		// Funding Summary: full thousands. Recommendation tiles: compact M.
		await expect(page.getByTestId("kt-dem-ui06-summary")).toContainText(
			/KES\s+455,000,000/,
		);
		await expect(page.getByTestId("kt-dem-ui06-condition")).toContainText(/Sufficient/i);
		await expect(page.getByTestId("kt-dem-ui06-recommendation")).toContainText(
			/Digital clinical systems infrastructure/i,
		);
		await expect(page.getByTestId("kt-dem-ui06-recommendation")).toContainText(/Active/i);
		await expect(page.getByTestId("kt-dem-ui06-money-tiles")).toContainText(/KES\s+\d+M/);
		await expect(page.getByTestId("kt-dem-ui06-progress")).toBeVisible();

		const confirm = page.getByTestId("kt-dem-ui06-confirm");
		await expect(confirm).toBeDisabled();
		await page.getByTestId("kt-dem-ui06-confirm-checkbox").check();
		await expect(confirm).toBeEnabled();
		// Checked mark must be visible (Desk focus must not force white fill over navy).
		const checkChrome = await page.getByTestId("kt-dem-ui06-confirm-checkbox").evaluate((el) => {
			const input = el as HTMLInputElement;
			const mark = input.nextElementSibling as HTMLElement | null;
			const ics = getComputedStyle(input);
			const mcs = mark ? getComputedStyle(mark) : null;
			return {
				checked: input.checked,
				bg: ics.backgroundColor,
				markOpacity: mcs?.opacity || "",
				markColor: mcs?.color || "",
			};
		});
		expect(checkChrome.checked).toBe(true);
		expect(checkChrome.bg).toMatch(/rgb\(0,\s*31,\s*72\)/);
		expect(parseFloat(checkChrome.markOpacity || "0")).toBeGreaterThanOrEqual(1);
		expect(checkChrome.markColor).toMatch(/rgb\(255,\s*255,\s*255\)/);

		await confirm.click();
		await expect(page.locator(ROOT)).toHaveAttribute(
			"data-kt-dem-review-stage",
			"Final Approval",
			{ timeout: 30_000 },
		);
		const rsvCount = await page.evaluate(async (demandName) => {
			const r = await (
				window as unknown as {
					frappe: {
						call: (o: {
							method: string;
							args?: Record<string, unknown>;
						}) => Promise<{ message?: unknown }>;
					};
				}
			).frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Demand Funding Allocation",
					filters: { demand: demandName },
					fields: ["funding_reservation", "bo_confirmation_status"],
				},
			});
			const rows = (r.message as Array<{
				funding_reservation?: string;
				bo_confirmation_status?: string;
			}>) || [];
			return {
				confirmed: rows.every((x) => x.bo_confirmation_status === "Confirmed"),
				reserved: rows.some((x) => !!x.funding_reservation),
			};
		}, demand);
		expect(rsvCount.confirmed).toBe(true);
		expect(rsvCount.reserved).toBe(false);
	});
});
