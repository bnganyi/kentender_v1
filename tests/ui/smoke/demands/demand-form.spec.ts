import { test, expect } from "@playwright/test";
import {
	loginAsAdministrator,
	loginAsDemandMultiscopeAdmin,
	loginAsDemandNoScopeAdmin,
	loginAsDemandRequester,
} from "../../helpers/auth";
import {
	assertStitchDeskChrome,
	assertStitchSectionTableChrome,
} from "../../helpers/stitchDeskChrome";

/**
 * DEM-UI-02 Create/Edit Demand — Stitch Desk canvas + live bind.
 * Route: /desk/demand-form
 * Creation-scope: Contract v2.2 §7.5 (single / multi / blocked).
 */

const ROOT = '[data-testid="kt-dem-ui02-root"]';

test.describe("DEM-UI-02 Demand Form", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsDemandRequester(page);
	});

	test("Stitch regions, sections, footer, and live bind render", async ({ page }) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator(`${ROOT}.kt-stitch-canvas`)).toBeVisible();
		await expect(page.getByRole("heading", { name: "Create demand" })).toBeVisible();
		await expect(page.getByTestId("kt-dem-create-lead")).toBeVisible();
		await expect(page.getByTestId("kt-dem-create-lead")).toContainText(
			/Describe what is needed/i,
		);
		// Single-scope: PE lives under shared title (not the old top context row).
		await expect(page.getByTestId("kt-dem-ui02-context")).toBeHidden();
		await expect(page.getByTestId("kt-dem-record-header")).toBeVisible();
		// Create: no demand code / status / route row until the Demand exists.
		await expect(page.getByTestId("kt-dem-record-meta-top")).toBeHidden();
		await expect(page.getByTestId("kt-dem-code")).toBeHidden();
		await expect(page.getByTestId("kt-dem-status-pill")).toBeHidden();
		await expect(page.getByTestId("kt-dem-route-pill")).toBeHidden();
		await expect(page.getByTestId("kt-dem-record-pe")).toBeVisible();
		await expect(page.getByTestId("kt-dem-record-pe")).toContainText(/Ministry of Health/i);
		await expect(page.getByTestId("kt-dem-stage")).toBeVisible();
		await expect(page.getByTestId("kt-dem-stage")).toContainText(/Request preparation/i);
		await expect(page.getByTestId("kt-dem-stage")).toContainText(/Current/i);
		// Stage labels stay sentence case (not SCREAMING CAPS).
		const stageText = await page.getByTestId("kt-dem-stage").innerText();
		expect(stageText).not.toMatch(/REQUEST PREPARATION/);
		await expect(page.getByText(/Current stage:/i)).toHaveCount(0);
		await expect(page.getByTestId("kt-dem-ui02-section-need")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-section-delivery")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-section-items")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-section-estimate")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-what")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-why")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-add-item")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-footer")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-save")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-submit")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-docs-dropzone")).toBeVisible();
		await expect(page.locator("cdn.tailwindcss.com")).toHaveCount(0);
		// Returned banner hidden on create.
		await expect(page.getByTestId("kt-dem-ui02-return-notice")).toBeHidden();
		// Single-scope: read-only PE · OU context (no pair select).
		await expect(page.getByTestId("kt-dem-ui02-scope-pair")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui02-scope-blocked")).toBeHidden();
		await expect(page.locator(`${ROOT}`)).toHaveAttribute(
			"data-kt-dem-selection-mode",
			"single_readonly",
		);
		// Form Stitch places PE/OU context above the H1 — measure to header top (not H1).
		const gap = await page.evaluate(() => {
			const header = document.querySelector('[data-testid="kt-dem-ui02-header"]');
			const toolbar = document.querySelector('[data-testid="kt-cl-toolbar"]');
			if (!header || !toolbar) return null;
			return Math.round(
				header.getBoundingClientRect().top - toolbar.getBoundingClientRect().bottom,
			);
		});
		expect(gap, "toolbar-to-form-header gap").not.toBeNull();
		expect(gap as number).toBeLessThanOrEqual(28);
		expect(gap as number).toBeGreaterThanOrEqual(0);
	});

	test("Stitch chrome resists Desk button/select bleed", async ({ page }) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-dem-ui02-root",
			primaryCtaTestId: "kt-dem-ui02-submit",
			selectSelector: '[data-kt-dem-field="demand_route"]',
		});
	});

	test("Section headers are primary-fixed blue; cards square; inputs stay rounded", async ({
		page,
	}) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		await assertStitchSectionTableChrome(page, {
			sectionTestId: "kt-dem-ui02-section-need",
			roundedControlTestId: "kt-dem-ui02-title",
		});
		// Items section embeds a table — thead must match section header chrome.
		const itemsTheadBg = await page
			.getByTestId("kt-dem-ui02-section-items")
			.evaluate((el) => {
				const row = el.querySelector("thead tr") as HTMLElement | null;
				return row ? getComputedStyle(row).backgroundColor : "";
			});
		expect(itemsTheadBg).toBe("rgb(215, 226, 255)");
	});

	test("Focused inputs use Strategy/Budget soft #7bbeff lock, not navy/black", async ({ page }) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		const title = page.getByTestId("kt-dem-ui02-title");
		await title.focus();
		await expect
			.poll(async () => {
				return title.evaluate((el) => {
					const cs = getComputedStyle(el);
					return {
						borderColor: cs.borderColor,
						boxShadow: cs.boxShadow,
						outlineStyle: cs.outlineStyle,
					};
				});
			})
			.toMatchObject({
				outlineStyle: "none",
				borderColor: "rgb(123, 190, 255)",
			});
		const focusChrome = await title.evaluate((el) => {
			const cs = getComputedStyle(el);
			return { borderColor: cs.borderColor, boxShadow: cs.boxShadow };
		});
		// App-wide lock: #7bbeff border + 1px soft halo (Budget/Strategy).
		expect(focusChrome.borderColor).toBe("rgb(123, 190, 255)");
		expect(focusChrome.boxShadow).toMatch(/0px 0px 0px 1px/);
		expect(focusChrome.boxShadow).not.toMatch(/0px 0px 0px [2-9]px/);
		expect(focusChrome.boxShadow).toMatch(/123,\s*190,\s*255/);
		// Reject Civic Ledger near-black and navy primary slabs.
		expect(focusChrome.boxShadow).not.toMatch(/0,\s*11,\s*29/);
		expect(focusChrome.borderColor).not.toBe("rgb(0, 31, 72)");
	});

	test("Stitch surface layout: shared record chrome on surface canvas", async ({ page }) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		const layout = await page.evaluate(() => {
			const root = document.querySelector('[data-testid="kt-dem-ui02-root"]') as HTMLElement;
			const chrome = document.querySelector(
				'[data-testid="kt-dem-record-chrome"]',
			) as HTMLElement;
			const stage = document.querySelector('[data-testid="kt-dem-stage"]') as HTMLElement;
			const canvas = document.querySelector(
				'[data-testid="kt-dem-ui02-form-canvas"]',
			) as HTMLElement;
			if (!root || !chrome || !stage || !canvas) return null;
			return {
				rootBg: getComputedStyle(root).backgroundColor,
				canvasBg: getComputedStyle(canvas).backgroundColor,
				stageBorder: getComputedStyle(stage).borderColor,
				hasHeader: !!document.querySelector('[data-testid="kt-dem-record-header"]'),
			};
		});
		expect(layout).not.toBeNull();
		expect(layout!.rootBg).toBe("rgb(249, 249, 254)");
		expect(layout!.canvasBg).toBe("rgb(249, 249, 254)");
		expect(layout!.hasHeader).toBe(true);
		expect(layout!.stageBorder).toBe("rgb(195, 198, 209)");
	});

	test("Required-by date shows one Material calendar (native date is invisible overlay)", async ({
		page,
	}) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		const wrap = page.getByTestId("kt-dem-ui02-date-wrap");
		await expect(wrap.locator("[data-kt-dem-date-icon]")).toHaveCount(1);
		await expect(wrap.locator(".material-symbols-outlined")).toHaveCount(1);
		await expect(page.getByTestId("kt-dem-ui02-required-by")).toHaveAttribute("type", "text");
		const native = page.getByTestId("kt-dem-ui02-required-by-native");
		await expect(native).toHaveAttribute("type", "date");
		const nativeOpacity = await native.evaluate((el) => getComputedStyle(el).opacity);
		expect(Number(nativeOpacity)).toBe(0);
		// Visible display field must not be a second date control with its own glyph.
		await expect(wrap.locator('input[type="date"]')).toHaveCount(1);
	});

	test("Estimate amount uses 28px mono; labels stay sentence case", async ({ page }) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		// Seed a visible total via item amount.
		await page.locator('[data-kt-dem-item="description"]').first().fill("Compute lot");
		await page.locator('[data-kt-dem-item="requester_estimate"]').first().fill("455000000");
		await page.locator('[data-kt-dem-item="requester_estimate"]').first().blur();
		const est = await page.getByTestId("kt-dem-ui02-estimate-total").evaluate((el) => {
			const cs = getComputedStyle(el);
			return {
				text: (el.textContent || "").trim(),
				fontSize: cs.fontSize,
				fontFamily: cs.fontFamily,
				fontWeight: cs.fontWeight,
			};
		});
		expect(est.text.replace(/,/g, "")).toMatch(/455000000/);
		expect(est.fontSize).toBe("28px");
		expect(est.fontFamily).toMatch(/JetBrains Mono/i);
		expect(["700", "bold"]).toContain(est.fontWeight);
		const labelTransform = await page
			.locator('[data-testid="kt-dem-ui02-section-estimate"] label')
			.first()
			.evaluate((el) => getComputedStyle(el).textTransform);
		expect(labelTransform).toBe("none");
		await expect(
			page.locator('[data-testid="kt-dem-ui02-section-estimate"] label').first(),
		).toHaveText(/Requester estimate/i);
		await expect(page.getByTestId("kt-dem-ui02-confidence")).toBeVisible();
	});

	test("Add item row and cancel returns to workspace", async ({ page }) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		const rowsBefore = await page.locator("[data-kt-dem-item-row]").count();
		await page.getByTestId("kt-dem-ui02-add-item").click();
		await expect(page.locator("[data-kt-dem-item-row]")).toHaveCount(rowsBefore + 1);
		await page.getByTestId("kt-dem-ui02-cancel").click();
		await expect(page).toHaveURL(/demands-workspace/, { timeout: 15_000 });
	});
});

test.describe("DEM-UI-02 creation-scope states", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("Multi-scope: no silent PE/OU; pair select enables save", async ({ page }) => {
		await loginAsDemandMultiscopeAdmin(page);
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator(ROOT)).toHaveAttribute(
			"data-kt-dem-selection-mode",
			"multi_required",
		);
		await expect(page.getByTestId("kt-dem-ui02-scope-pair")).toBeVisible();
		const selected = await page.getByTestId("kt-dem-ui02-scope-pair").inputValue();
		expect(selected).toBe("");
		await expect(page.getByTestId("kt-dem-ui02-save")).toBeDisabled();
		await page.getByTestId("kt-dem-ui02-scope-pair").selectOption({ index: 1 });
		await expect(page.getByTestId("kt-dem-ui02-save")).toBeEnabled({ timeout: 5_000 });
	});

	test("No-scope admin: creation blocked with no PE fallback", async ({ page }) => {
		await loginAsDemandNoScopeAdmin(page);
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator(ROOT)).toHaveAttribute("data-kt-dem-selection-mode", "blocked");
		await expect(page.getByTestId("kt-dem-ui02-scope-blocked")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-scope-blocked")).toContainText(/Requester/i);
		await expect(page.getByTestId("kt-dem-ui02-save")).toBeDisabled();
		await expect(page.getByTestId("kt-dem-ui02-submit")).toBeDisabled();
	});
});

test.describe("DEM-UI-03 Returned correction state", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("Return notice, correction list, highlights, funding, footer actions", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		const demandName = await page.evaluate(async () => {
			const r = await (window as unknown as {
				frappe: {
					call: (o: {
						method: string;
					}) => Promise<{ message?: { demand?: string; ok?: boolean } }>;
				};
			}).frappe.call({
				method: "kentender_procurement.demands.api.prepare_returned_demand_ui03",
			});
			return r.message?.demand || "";
		});
		expect(demandName).toBeTruthy();

		await loginAsDemandRequester(page);
		await page.goto(`/desk/demand-form/${demandName}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator(ROOT)).toHaveClass(/kt-dem-form-returned/);
		await expect(page.getByTestId("kt-dem-status-pill")).toBeVisible();
		await expect(page.getByTestId("kt-dem-status-pill")).toHaveText(/Returned/i);
		await expect(page.getByTestId("kt-dem-record-header")).toBeVisible();
		await expect(page.getByTestId("kt-dem-stage")).toBeVisible();
		await expect(page.getByTestId("kt-dem-stage")).toContainText(/Request preparation/i);
		await expect(page.getByTestId("kt-dem-stage")).toContainText(/Current/i);
		await expect(page.getByText(/Current stage:/i)).toHaveCount(0);
		// Return notice stays below the shared stage indicator.
		const stackOrder = await page.evaluate(() => {
			const stage = document.querySelector('[data-testid="kt-dem-stage"]');
			const notice = document.querySelector('[data-testid="kt-dem-ui02-return-notice"]');
			if (!stage || !notice) return null;
			return stage.compareDocumentPosition(notice) & Node.DOCUMENT_POSITION_FOLLOWING;
		});
		expect(stackOrder).toBeTruthy();
		await expect(page.getByTestId("kt-dem-ui02-return-notice")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-return-notice")).toContainText(
			/Business Approver|Procurement Approval Authority/i,
		);
		await expect(page.getByTestId("kt-dem-ui02-return-notice")).toContainText(/15,000,000/);
		// Contained card — same column width as Need section, not a full-bleed band.
		const noticeWidths = await page.evaluate(() => {
			const notice = document.querySelector('[data-testid="kt-dem-ui02-return-notice"]');
			const section = document.querySelector('[data-testid="kt-dem-ui02-section-need"]');
			const root = document.querySelector('[data-testid="kt-dem-ui02-root"]');
			return {
				notice: notice?.getBoundingClientRect().width || 0,
				section: section?.getBoundingClientRect().width || 0,
				root: root?.getBoundingClientRect().width || 0,
			};
		});
		expect(Math.abs(noticeWidths.notice - noticeWidths.section)).toBeLessThan(4);
		expect(noticeWidths.notice).toBeLessThan(noticeWidths.root * 0.85);
		await expect(page.getByTestId("kt-dem-ui02-correction-list")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-correction-list")).toContainText(
			/Need items and participant quantities/i,
		);
		await expect(page.getByTestId("kt-dem-ui02-correction-list")).toContainText(
			/Expected outcome for the revised scope/i,
		);
		await expect(page.getByTestId("kt-dem-ui02-correction-list")).toContainText(
			/Requester estimate/i,
		);
		await expect(page.getByTestId("kt-dem-ui02-available-funding")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-available-funding")).toContainText(
			/80,000,000/,
		);
		await expect(page.getByTestId("kt-dem-ui02-section-items")).toHaveClass(
			/kt-dem-correction-highlight/,
		);
		await expect(page.getByTestId("kt-dem-ui02-outcome")).toHaveClass(
			/kt-dem-correction-highlight/,
		);
		await expect(page.getByTestId("kt-dem-ui02-section-estimate")).toHaveClass(
			/kt-dem-correction-highlight/,
		);
		await expect(page.getByTestId("kt-dem-ui02-section-need")).not.toHaveClass(
			/kt-dem-correction-highlight/,
		);
		await expect(page.getByTestId("kt-dem-ui02-cancel")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui02-cancel-demand")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-save")).toHaveText(/Save changes/i);
		await expect(page.getByTestId("kt-dem-ui02-submit")).toContainText(/Resubmit/i);

		// Cancel demand uses Stitch reason modal — never frappe.prompt / Desk dialog.
		const cancelModal = page.getByTestId("kt-dem-ui02-cancel-modal");
		await expect(cancelModal).toBeAttached();
		await expect(cancelModal).toBeHidden();
		await page.getByTestId("kt-dem-ui02-cancel-demand").click();
		await expect(cancelModal).toBeVisible({ timeout: 10_000 });
		await expect(cancelModal).not.toHaveAttribute("hidden", "");
		await expect(page.getByTestId("kt-dem-ui02-cancel-modal-comment")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-cancel-modal-confirm")).toBeVisible();
		await expect(page.locator(".frappe-dialog:visible, .modal-dialog:visible")).toHaveCount(0);
		const modalBorder = await cancelModal
			.locator(".kt-dem-reason-modal-card")
			.evaluate((el) => getComputedStyle(el).borderColor);
		expect(modalBorder).toBe("rgb(195, 198, 209)");
		await page.getByTestId("kt-dem-ui02-cancel-modal-confirm").click();
		await expect(page.getByTestId("kt-dem-ui02-cancel-modal-error")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-cancel-modal-error")).toContainText(/required/i);
		await page.getByTestId("kt-dem-ui02-cancel-modal-dismiss").click();
		await expect(cancelModal).toBeHidden();
	});
});

test.describe("DEM-UI-02 supporting documents persistence", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsDemandRequester(page);
	});

	test("Upload persists after reload", async ({ page }) => {
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });

		await page.getByTestId("kt-dem-ui02-title").fill("DEM-UI-02 docs persistence");
		await page.getByTestId("kt-dem-ui02-what").fill("Need for document upload proof");
		await page.locator('[data-kt-dem-field="need_rationale"]').fill("Rationale for docs");
		await page.locator('[data-kt-dem-field="expected_outcome"]').fill("Outcome");
		await page.locator('[data-kt-dem-field="beneficiaries"]').fill("Beneficiaries");
		await page.locator('[data-kt-dem-field="delivery_location"]').fill("Nairobi");
		await page.locator('[data-kt-dem-field="required_by_date"]').fill("2027-12-31");
		await page.locator('[data-kt-dem-item="description"]').first().fill("Lot A");
		await page.locator('[data-kt-dem-item="requester_estimate"]').first().fill("100000");

		await page.getByTestId("kt-dem-ui02-save").click();
		await expect(page).toHaveURL(/demand-form\/.+/, { timeout: 30_000 });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });

		const demandName = page.url().split("/demand-form/")[1]?.split("?")[0] || "";
		expect(demandName).toBeTruthy();

		await page.getByTestId("kt-dem-ui02-docs-file").setInputFiles({
			name: "dem-ui02-support.txt",
			mimeType: "text/plain",
			buffer: Buffer.from("dem-ui02 playwright supporting document"),
		});
		await expect(page.getByTestId("kt-dem-ui02-doc-chip")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-dem-ui02-doc-chip")).toContainText(/dem-ui02-support\.txt/i);

		await page.goto(`/desk/demand-form/${demandName}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-dem-ui02-docs-list")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-doc-chip")).toContainText(/dem-ui02-support\.txt/i);
	});
});
