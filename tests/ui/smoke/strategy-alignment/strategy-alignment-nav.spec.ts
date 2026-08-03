import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * Strategy Alignment MVP-1 — Stitch Desk shells + live API binders.
 * Requires MOH-SP-2026-2030 seed (works_master_strategy_hierarchy).
 */

const PLAN = "MOH-SP-2026-2030";
const TARGET = "MOH-TGT-01";

test.describe.configure({ mode: "serial" });

test.describe("Strategy Alignment UI shell", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("portfolio opens from Desk route with Stitch regions", async ({ page }) => {
		await page.goto("/desk/strategy-alignment", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-str-portfolio")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-str-summary-strip")).toBeVisible();
		await expect(page.getByTestId("kt-str-bento")).toBeVisible();
		await expect(page.getByTestId("kt-str-plans-table")).toBeVisible();
		// Live API binder marks the root after get_strategy_portfolio succeeds.
		await expect(page.locator('[data-testid="kt-str-portfolio"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});
		// Seed plan row is rendered from API (not fixture hardcode).
		await expect(
			page.locator('[data-testid="kt-str-plans-table"] tr[data-plan-code="MOH-SP-2026-2030"]')
		).toBeVisible({ timeout: 15_000 });
		await expect(page.getByText("MOH-SP-2026-2030")).toBeVisible();
		// Summary strip maps Active / Awaiting review / Measurements due / Needs attention.
		const strip = page.getByTestId("kt-str-summary-strip");
		await expect(strip.locator('[data-kt-str-count="active"]')).not.toHaveText("—");
		await expect(strip.locator('[data-kt-str-count="submitted"]')).toBeVisible();
		await expect(strip.locator('[data-kt-str-count="measurements_due"]')).toBeVisible();
		await expect(strip.locator('[data-kt-str-count="measurement_attention"]')).not.toHaveText("—");

		// Stitch code.html contract: 12-col bento, lg 9/3, primary CTA from Stitch classes.
		await expect(page.locator(".kt-str-root")).toBeVisible();
		await expect(page.locator("button.bg-primary")).toContainText("Create strategic plan");
		await expect(page.getByTestId("kt-str-pf-my-work")).toBeVisible();
		const geometry = await page.locator('[data-testid="kt-str-bento"]').evaluate((el) => {
			const style = getComputedStyle(el);
			const main = el.querySelector("[data-kt-str-bento-main]") as HTMLElement | null;
			const aside = el.querySelector("[data-kt-str-bento-aside]") as HTMLElement | null;
			const btn = document.querySelector(".kt-str-root button.bg-primary") as HTMLElement | null;
			const btnCs = btn ? getComputedStyle(btn) : null;
			return {
				display: style.display,
				columns: style.gridTemplateColumns,
				mainWidth: main ? main.getBoundingClientRect().width : 0,
				asideWidth: aside ? aside.getBoundingClientRect().width : 0,
				bentoWidth: el.getBoundingClientRect().width,
				btnBg: btnCs ? btnCs.backgroundColor : "",
			};
		});
		expect(geometry.display).toBe("grid");
		expect(geometry.columns.split(" ").length).toBeGreaterThanOrEqual(12);
		expect(geometry.mainWidth).toBeGreaterThan(geometry.bentoWidth * 0.55);
		expect(geometry.asideWidth).toBeGreaterThan(180);
		expect(geometry.asideWidth).toBeLessThan(geometry.bentoWidth * 0.4);
		// Stitch primary #001f48
		expect(geometry.btnBg).toBe("rgb(0, 31, 72)");

		// Search lives in the filter panel, left of dropdowns, separated by "|".
		const filters = page.getByTestId("kt-str-pf-filters");
		await expect(filters).toBeVisible();
		await expect(filters.getByPlaceholder("Search by plan code or title...")).toBeVisible();
		await expect(page.getByTestId("kt-str-pf-filter-sep")).toHaveText("|");
		// Filters are dropdowns with visible chevrons (not plain text inputs).
		await expect(filters.locator("select")).toHaveCount(4);
		await expect(filters.locator(".material-symbols-outlined", { hasText: "expand_more" })).toHaveCount(4);
		const order = await filters.evaluate((el) => {
			const kids = [...el.children];
			const searchIdx = kids.findIndex(
				(c) => c.querySelector?.("input[type='text']") || (c as HTMLElement).matches?.("input")
			);
			const sepIdx = kids.findIndex((c) => c.getAttribute("data-testid") === "kt-str-pf-filter-sep");
			// Selects are wrapped in .relative for chevron affordance.
			const selectIdx = kids.findIndex(
				(c) => c.tagName === "SELECT" || !!c.querySelector?.("select")
			);
			return { searchIdx, sepIdx, selectIdx };
		});
		expect(order.searchIdx).toBeGreaterThanOrEqual(0);
		expect(order.sepIdx).toBeGreaterThan(order.searchIdx);
		expect(order.selectIdx).toBeGreaterThan(order.sepIdx);

		// Focus chrome: light blue on fields, not near-black primary.
		const planType = filters.getByLabel("Plan type");
		await planType.focus();
		const focusChrome = await planType.evaluate((el) => {
			const cs = getComputedStyle(el);
			return { borderColor: cs.borderColor, boxShadow: cs.boxShadow };
		});
		expect(focusChrome.borderColor).toMatch(/123,\s*190,\s*255/);
		expect(focusChrome.boxShadow).not.toMatch(/0,\s*31,\s*72/);

		// Text actions must not show Desk/Bootstrap black button boxes at rest.
		const textActions = await page.evaluate(() => {
			const root = document.querySelector(".kt-str-root");
			if (!root) return [];
			const labels = ["Clear filters", "View"];
			return labels.map((label) => {
				const btn = [...root.querySelectorAll("button")].find(
					(b) => (b.textContent || "").trim() === label
				) as HTMLElement | undefined;
				if (!btn) return { label, found: false };
				const cs = getComputedStyle(btn);
				return {
					label,
					found: true,
					borderStyle: cs.borderStyle,
					borderWidth: cs.borderWidth,
					borderColor: cs.borderColor,
				};
			});
		});
		for (const row of textActions) {
			expect(row.found).toBe(true);
			expect(row.borderStyle === "none" || row.borderWidth === "0px").toBeTruthy();
		}

		// Live My Work (seed has verified At-risk measurement).
		const myWork = page.getByTestId("kt-str-pf-my-work");
		await expect(myWork.locator("[data-kt-str-action]").first()).toBeVisible();
	});

	test("portfolio search filters live plan rows", async ({ page }) => {
		await page.goto("/desk/strategy-alignment", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-portfolio"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		const search = page.getByTestId("kt-str-pf-filters").getByLabel("Search plans");
		await search.fill("NO-SUCH-PLAN-ZZZ");
		await expect(page.locator('[data-testid="kt-str-plans-table"] [data-kt-str-empty="1"]')).toBeVisible({
			timeout: 10_000,
		});
		await search.fill("MOH-SP-2026");
		await expect(
			page.locator('[data-testid="kt-str-plans-table"] tr[data-plan-code="MOH-SP-2026-2030"]')
		).toBeVisible({ timeout: 10_000 });
	});

	test("Create strategic plan focused page validates, creates, and opens overview", async ({ page }) => {
		await page.goto("/desk/strategy-alignment", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-portfolio"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await page.getByTestId("kt-str-create-plan").click();
		await expect(page).toHaveURL(/strategy-plan-create/, { timeout: 15_000 });
		await expect(page.locator('[data-testid="kt-str-create-plan"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});

		// Inline validation keeps the form open.
		await page.getByTestId("kt-str-create-plan-submit").click();
		await expect(page.locator('[data-kt-str-error="plan_code"]')).toBeVisible();
		await expect(page).toHaveURL(/strategy-plan-create/);

		const suffix = Date.now().toString().slice(-6);
		const code = `UI01-PW-${suffix}`;
		// Stitch regions from create_plan/code.html
		await expect(page.getByTestId("kt-str-create-bento")).toBeVisible();
		await expect(page.getByText("Basic Information")).toBeVisible();
		await expect(page.getByTestId("kt-str-create-plan-context")).toBeVisible();
		await expect(page.getByTestId("kt-str-create-quote")).toBeVisible();
		await expect(page.getByTestId("kt-str-create-actions")).toBeVisible();
		// Stitch/Tailwind Forms select chevron (SVG background) + date calendar glyphs.
		const createRoot = page.getByTestId("kt-str-create-plan");
		await expect(createRoot.locator(".material-symbols-outlined", { hasText: "calendar_today" })).toHaveCount(2);
		const selectGlyphs = await createRoot.locator("select").evaluateAll((els) =>
			els.map((el) => {
				const cs = getComputedStyle(el);
				return {
					hasChevron: /url\(|data:image\/svg/.test(cs.backgroundImage),
					padRight: parseFloat(cs.paddingRight),
				};
			})
		);
		expect(selectGlyphs.length).toBe(2);
		for (const g of selectGlyphs) {
			expect(g.hasChevron).toBe(true);
			expect(g.padRight).toBeGreaterThanOrEqual(32);
		}
		// Quote architecture icon must stay large + primary-fixed (not forced to 20px gray).
		const arch = await createRoot
			.locator('[data-testid="kt-str-create-quote"] .material-symbols-outlined')
			.evaluate((el) => {
				const cs = getComputedStyle(el);
				return { size: parseFloat(cs.fontSize), color: cs.color };
			});
		expect(arch.size).toBeGreaterThanOrEqual(32);
		expect(arch.color).toMatch(/215,\s*226,\s*255/);

		// Basic Information icon must share vertical center with the title (no Desk h2 margin drift).
		const headerAlign = await createRoot.locator("section h2").evaluate((title) => {
			const icon = title.parentElement?.querySelector(".material-symbols-outlined") as HTMLElement;
			const ir = icon.getBoundingClientRect();
			const tr = title.getBoundingClientRect();
			return {
				midDelta: Math.abs(ir.top + ir.height / 2 - (tr.top + tr.height / 2)),
				h2MarginBottom: parseFloat(getComputedStyle(title).marginBottom),
			};
		});
		expect(headerAlign.h2MarginBottom).toBe(0);
		expect(headerAlign.midDelta).toBeLessThan(2);

		// Stitch action bar: helper left + Cancel/Create right (sm:flex-row), not stacked full-width.
		await page.setViewportSize({ width: 1280, height: 900 });
		const actionLayout = await createRoot.locator('[data-testid="kt-str-create-actions"]').evaluate((el) => {
			const cs = getComputedStyle(el);
			const cancel = el.querySelector('[data-testid="kt-str-create-plan-cancel"]') as HTMLElement;
			const submit = el.querySelector('[data-testid="kt-str-create-plan-submit"]') as HTMLElement;
			const helper = el.querySelector("p") as HTMLElement;
			return {
				flexDir: cs.flexDirection,
				cancelW: cancel.getBoundingClientRect().width,
				submitW: submit.getBoundingClientRect().width,
				helperTop: helper.getBoundingClientRect().top,
				cancelTop: cancel.getBoundingClientRect().top,
				barW: el.getBoundingClientRect().width,
			};
		});
		expect(actionLayout.flexDir).toBe("row");
		expect(Math.abs(actionLayout.helperTop - actionLayout.cancelTop)).toBeLessThan(24);
		expect(actionLayout.cancelW).toBeLessThan(actionLayout.barW * 0.45);
		expect(actionLayout.submitW).toBeLessThan(actionLayout.barW * 0.45);

		await page.locator('[data-kt-str-field="plan_code"]').fill(code);
		await page.locator('[data-kt-str-field="title"]').fill(`Playwright Create ${suffix}`);
		await page.locator('[data-kt-str-field="plan_type"]').selectOption("entity");
		const peSelect = page.locator('[data-kt-str-field="procuring_entity_select"]');
		await expect(peSelect).toBeVisible();
		const peDisabled = await peSelect.isDisabled();
		if (!peDisabled) {
			const options = await peSelect.locator("option").allTextContents();
			const moh = options.find((t) => /MOH|Health|PE-MOH/i.test(t));
			if (moh) {
				await peSelect.selectOption({ label: moh.trim() });
			} else {
				await peSelect.selectOption({ index: 1 });
			}
		}
		await page.locator('[data-kt-str-field="start_date"]').fill("2026-07-01");
		await page.locator('[data-kt-str-field="end_date"]').fill("2027-06-30");
		await page.getByTestId("kt-str-create-plan-submit").click();
		await expect(page).toHaveURL(new RegExp(`strategy-plan-overview/${code}`), { timeout: 20_000 });
		await expect(page.getByTestId("kt-str-overview")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-str-plan-tabs")).toBeVisible();
		for (const tab of [
			"Overview",
			"Structure",
			"Value Commitments",
			"Measurement",
			"Downstream Usage",
			"Review",
			"Audit",
		]) {
			await expect(page.getByTestId("kt-str-plan-tabs").getByRole("button", { name: tab })).toBeVisible();
		}
		await expect(page.getByTestId("kt-str-start-plan-structure")).toBeVisible({ timeout: 15_000 });
	});

	test("Create strategic plan Cancel returns to portfolio without creating", async ({ page }) => {
		const suffix = Date.now().toString().slice(-6);
		const code = `UI01-CANCEL-${suffix}`;
		await page.goto("/desk/strategy-plan-create", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-create-plan"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});
		await page.locator('[data-kt-str-field="plan_code"]').fill(code);
		await page.locator('[data-kt-str-field="title"]').fill(`Cancel ${suffix}`);
		await page.getByTestId("kt-str-create-plan-cancel").click();
		await expect(page).toHaveURL(/strategy-alignment/, { timeout: 15_000 });
		await expect(page.locator('[data-testid="kt-str-portfolio"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});
		const search = page.getByTestId("kt-str-pf-filters").getByLabel("Search plans");
		await search.fill(code);
		await expect(page.locator('[data-testid="kt-str-plans-table"] [data-kt-str-empty="1"]')).toBeVisible({
			timeout: 10_000,
		});
	});

	test("View navigates to plan overview with refresh-safe plan code", async ({ page }) => {
		await page.goto("/desk/strategy-alignment", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-str-portfolio")).toBeVisible({ timeout: 30_000 });
		await expect(
			page.locator(`[data-testid="kt-str-plans-table"] tr[data-plan-code="${PLAN}"]`)
		).toBeVisible({ timeout: 20_000 });
		await page
			.locator(
				`[data-testid="kt-str-plans-table"] tr[data-plan-code="${PLAN}"] button[data-kt-str-action="open-plan"]`
			)
			.click();
		await expect(page).toHaveURL(new RegExp(`strategy-plan-overview/${PLAN}`), {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-str-overview")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-str-plan-tabs")).toBeVisible();
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-str-overview")).toBeVisible({ timeout: 30_000 });
		await expect(page).toHaveURL(new RegExp(`strategy-plan-overview/${PLAN}`));
	});

	test("plan overview mounts Stitch code.html regions", async ({ page }) => {
		await page.goto(`/desk/strategy-plan-overview/${PLAN}`, { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-str-overview")).toBeVisible({ timeout: 30_000 });
		await expect(page.locator('[data-testid="kt-str-overview"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});
		await expect(page.getByTestId("kt-str-plan-chrome")).toBeVisible();
		await expect(page.getByTestId("kt-str-plan-tabs")).toBeVisible();
		await expect(page.getByText("Plan Details")).toBeVisible();
		await expect(page.getByText("Performance Attention")).toBeVisible();
		await expect(page.getByText("Plan Structure")).toBeVisible();
		await expect(page.getByText("Public-value Commitments")).toBeVisible();
		await expect(page.getByRole("button", { name: "Export Plan" })).toBeVisible();
		await expect(page.getByRole("button", { name: "Create successor version" })).toBeVisible();
		// Live Plan Details — PE name, not raw id; MOH seed type.
		await expect(page.locator('[data-kt-str-detail="plan_type"]')).toHaveText(/Entity Strategic Plan/i);
		await expect(page.locator('[data-kt-str-detail="procuring_entity"]')).toHaveText(/Health|MOH/i);
		await expect(page.locator('[data-testid="kt-str-plan-chrome"] [data-kt-str-plan-code]')).toHaveText(PLAN);
		// Attention table is API-driven (no hardcoded MOH-TGT-02 fixture row required).
		const attentionCodes = await page
			.locator("[data-kt-str-attention-tbody] [data-target-code]")
			.evaluateAll((els) => els.map((el) => el.getAttribute("data-target-code") || ""));
		expect(attentionCodes.every((c) => c && !c.startsWith("mfm") && c.length < 40)).toBeTruthy();
		await expect(page.locator("[data-kt-str-lock-footer]")).toBeVisible();
		// CTA sits in the plan header action cluster (right of Export Plan), not the footer.
		const headerActions = await page.getByTestId("kt-str-plan-chrome").evaluate((el) => {
			const cluster = el.querySelector(".flex.gap-3, .flex.flex-wrap.items-center.gap-3");
			if (!cluster) return { ok: false };
			const labels = [...cluster.querySelectorAll("button")].map((b) =>
				(b.textContent || "").replace(/\s+/g, " ").trim()
			);
			return {
				ok: true,
				labels,
				exportIdx: labels.findIndex((t) => t.includes("Export Plan")),
				ctaIdx: labels.findIndex((t) => t.includes("Create successor version")),
			};
		});
		expect(headerActions.ok).toBe(true);
		expect(headerActions.exportIdx).toBeGreaterThanOrEqual(0);
		expect(headerActions.ctaIdx).toBeGreaterThan(headerActions.exportIdx);

		// Header CTAs must sit beside the title (row), not stacked under it.
		const headerLayout = await page.getByTestId("kt-str-plan-chrome").evaluate((el) => {
			const row = el.querySelector(":scope > .flex") as HTMLElement | null;
			if (!row) return { ok: false };
			const title = row.querySelector("h1") as HTMLElement | null;
			const actions = [...row.querySelectorAll("button")].find((b) =>
				(b.textContent || "").includes("Create successor")
			) as HTMLElement | undefined;
			if (!title || !actions) return { ok: false };
			const t = title.getBoundingClientRect();
			const a = actions.getBoundingClientRect();
			return {
				ok: true,
				flexDirection: getComputedStyle(row).flexDirection,
				ctaRightOfTitle: a.left > t.right - 40,
				ctaNotFarBelowTitle: a.top < t.bottom + 80,
			};
		});
		expect(headerLayout.ok).toBe(true);
		expect(headerLayout.flexDirection).toBe("row");
		expect(headerLayout.ctaRightOfTitle).toBe(true);
		expect(headerLayout.ctaNotFarBelowTitle).toBe(true);

		const geometry = await page.getByTestId("kt-str-overview-bento").evaluate((el) => {
			const main = el.querySelector("[data-kt-str-overview-main]") as HTMLElement | null;
			const aside = el.querySelector("[data-kt-str-overview-aside]") as HTMLElement | null;
			const cs = getComputedStyle(el);
			return {
				display: cs.display,
				tracks: cs.gridTemplateColumns.split(" ").filter(Boolean).length,
				mainW: main ? main.getBoundingClientRect().width : 0,
				asideW: aside ? aside.getBoundingClientRect().width : 0,
				bentoW: el.getBoundingClientRect().width,
			};
		});
		expect(geometry.display).toBe("grid");
		expect(geometry.tracks).toBeGreaterThanOrEqual(12);
		expect(geometry.mainW).toBeGreaterThan(geometry.bentoW * 0.55);
		expect(geometry.asideW).toBeGreaterThan(180);

		// Text link stays borderless; Export keeps outline border.
		const chrome = await page.evaluate(() => {
			const root = document.querySelector(".kt-str-root");
			if (!root) return { found: false };
			const norm = (el: Element) => (el.textContent || "").replace(/\s+/g, " ").trim();
			const viewStruct = [...root.querySelectorAll("button")].find(
				(b) => norm(b) === "View structure"
			);
			const exportBtn = [...root.querySelectorAll("button")].find((b) =>
				norm(b).includes("Export Plan")
			);
			if (!viewStruct || !exportBtn) {
				return { found: false, buttons: [...root.querySelectorAll("button")].map(norm) };
			}
			return {
				found: true,
				viewBorder: getComputedStyle(viewStruct).borderWidth,
				exportBorder: getComputedStyle(exportBtn).borderStyle,
			};
		});
		expect(chrome.found).toBe(true);
		expect(chrome.viewBorder === "0px").toBeTruthy();
		expect(chrome.exportBorder).not.toBe("none");

		const modal = page.getByTestId("kt-str-successor-modal");
		await page.getByRole("button", { name: "Create successor version" }).click();
		await expect(modal).toBeVisible();
		await expect(modal.getByRole("heading", { name: "Create Successor Version" })).toBeVisible();
		await modal.getByRole("button", { name: "Cancel" }).click();
		await expect(modal).toBeHidden();
	});

	test("plan overview create successor opens Draft version Overview", async ({ page }) => {
		await page.goto(`/desk/strategy-plan-overview/${PLAN}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-overview"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});
		await expect(page.getByTestId("kt-str-create-successor")).toBeVisible({ timeout: 10_000 });
		await page.getByTestId("kt-str-create-successor").click();
		const modal = page.getByTestId("kt-str-successor-modal");
		await expect(modal).toBeVisible();
		await page.getByTestId("kt-str-confirm-successor").click();
		await expect(page).toHaveURL(/strategy-plan-overview\/[a-z0-9]{10,}/i, { timeout: 20_000 });
		await expect(page.locator('[data-testid="kt-str-overview"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});
		await expect(page.locator('[data-testid="kt-str-plan-chrome"] [data-kt-str-plan-status]')).toHaveText(
			/Draft/i
		);
		await expect(page.locator('[data-testid="kt-str-plan-chrome"] [data-kt-str-plan-version]')).toHaveText(
			/Version\s*[2-9]/i
		);
		const draftId = await page.locator('[data-testid="kt-str-overview"]').getAttribute("data-kt-str-plan-id");
		expect(draftId).toBeTruthy();
		// Active source still reachable by plan_code
		await page.goto(`/desk/strategy-plan-overview/${PLAN}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-overview"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});
		await expect(page.locator('[data-testid="kt-str-plan-chrome"] [data-kt-str-plan-status]')).toHaveText(
			/Active/i
		);
		await expect(page.locator('[data-testid="kt-str-plan-chrome"] [data-kt-str-plan-code]')).toHaveText(PLAN);
	});

	test("value commitments Active plan is live and read-only", async ({ page }) => {
		await page.goto(`/desk/strategy-plan-value-commitments/${PLAN}`, {
			waitUntil: "domcontentloaded",
		});
		const vc = page.locator(
			'[data-testid="kt-str-value-commitments"][data-kt-str-live="1"]:visible'
		);
		await expect(vc).toBeVisible({ timeout: 30_000 });
		await expect(vc).toHaveAttribute("data-kt-str-vc-editable", "0");
		await expect(page.locator('[data-testid="kt-str-plan-tabs"]:visible')).toBeVisible();
		await expect(vc.getByTestId("kt-str-vc-table")).toBeVisible();
		await expect(vc.getByText("Plan value commitments")).toBeVisible();
		// Seed commitments (not fixture-only PVO-SUS-02).
		await expect(vc.locator('[data-kt-str-vc-code="PVO-EFT-01"]')).toBeVisible();
		await expect(vc.locator('[data-kt-str-vc-code="PVO-ECO-01"]')).toBeVisible();
		await expect(vc.getByRole("button", { name: /Add commitment/i })).toHaveCount(0);

		// Under shared plan chrome: section title smaller than plan h1; tight gap after tabs.
		const vcDensity = await page.evaluate(() => {
			const tabs = document.querySelector('[data-testid="kt-str-plan-tabs"]:not([style*="display: none"])');
			const root = document.querySelector(
				'[data-testid="kt-str-value-commitments"][data-kt-str-live="1"]'
			);
			const header = root && root.querySelector('[data-testid="kt-str-vc-header"]');
			const title = header && (header.querySelector("h2, h1") as HTMLElement | null);
			const planH1 = document.querySelector(
				'[data-testid="kt-str-plan-chrome"] h1'
			) as HTMLElement | null;
			if (!tabs || !header || !title || !planH1) return { ok: false };
			const gap = header.getBoundingClientRect().top - tabs.getBoundingClientRect().bottom;
			const titlePx = parseFloat(getComputedStyle(title).fontSize);
			const planPx = parseFloat(getComputedStyle(planH1).fontSize);
			return { ok: true, gap, titlePx, planPx };
		});
		expect(vcDensity.ok).toBe(true);
		expect(vcDensity.gap).toBeLessThanOrEqual(32);
		expect(vcDensity.titlePx).toBeLessThanOrEqual(22);
		expect(vcDensity.titlePx).toBeLessThan(vcDensity.planPx);

		const drawer = vc.getByTestId("kt-str-vc-drawer");
		await expect(drawer).toHaveClass(/translate-x-full/);
		// Row action (not the plan "Review" tab).
		await vc.locator('button[data-kt-str-action="review-vc"]').first().click();
		await expect(drawer).toHaveClass(/is-open/);
		await expect(drawer.getByText(/Review Commitment/i)).toBeVisible();
		await expect(drawer.locator("[data-kt-str-vc-drawer-save]")).toBeHidden();
		await drawer.getByRole("button", { name: "Cancel" }).click();
		await expect(drawer).toHaveClass(/translate-x-full/);
	});

	test("value commitments Draft can add commitment via drawer", async ({ page }) => {
		// Successor Draft inherits structure + existing commitments; add an unused Active PVO.
		await page.goto(`/desk/strategy-plan-overview/${PLAN}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-overview"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});
		await page.getByTestId("kt-str-create-successor").click();
		const modal = page.getByTestId("kt-str-successor-modal");
		await expect(modal).toBeVisible();
		await page.getByTestId("kt-str-confirm-successor").click();
		await expect(page).toHaveURL(/strategy-plan-overview\/[a-z0-9]{10,}/i, { timeout: 20_000 });
		const draftId = await page.locator('[data-testid="kt-str-overview"]').getAttribute("data-kt-str-plan-id");
		expect(draftId).toBeTruthy();

		await page.goto(`/desk/strategy-plan-value-commitments/${draftId}`, {
			waitUntil: "domcontentloaded",
		});
		const vc = page.locator(
			'[data-testid="kt-str-value-commitments"][data-kt-str-live="1"]:visible'
		);
		await expect(vc).toBeVisible({ timeout: 20_000 });
		await expect(vc).toHaveAttribute("data-kt-str-vc-editable", "1");
		await expect(vc.locator('[data-kt-str-vc-code="PVO-EFT-01"]')).toBeVisible();

		// Add commitment sits beside the title (row), not stacked under it.
		const vcHeaderLayout = await vc.getByTestId("kt-str-vc-header").evaluate((el) => {
			const title = el.querySelector("h2, h1") as HTMLElement | null;
			const btn = [...el.querySelectorAll("button")].find((b) =>
				(b.textContent || "").includes("Add commitment")
			) as HTMLElement | undefined;
			if (!title || !btn) return { ok: false };
			const t = title.getBoundingClientRect();
			const a = btn.getBoundingClientRect();
			return {
				ok: true,
				flexDirection: getComputedStyle(el).flexDirection,
				ctaRightOfTitle: a.left > t.right - 40,
				sameRow: Math.abs(a.top - t.top) < 48,
			};
		});
		expect(vcHeaderLayout.ok).toBe(true);
		expect(vcHeaderLayout.flexDirection).toBe("row");
		expect(vcHeaderLayout.ctaRightOfTitle).toBe(true);
		expect(vcHeaderLayout.sameRow).toBe(true);

		const drawer = vc.getByTestId("kt-str-vc-drawer");
		await vc.getByRole("button", { name: /Add commitment/i }).click();
		await expect(drawer).toHaveClass(/is-open/);
		await expect(drawer.getByText("Add Commitment")).toBeVisible();

		const pvoBtn = drawer.locator("[data-kt-str-action='select-pvo']").filter({ hasText: "PVO-LOC-01" });
		await expect(pvoBtn).toBeVisible({ timeout: 15_000 });
		await pvoBtn.click();
		await drawer.locator("[data-kt-str-vc-drawer-rationale]").fill("UI07 live wire rationale");
		await drawer.locator("[data-kt-str-vc-drawer-owner]").fill("Director, Digital Health");
		await drawer.locator("[data-kt-str-vc-drawer-links] input[type='checkbox']").first().check();
		await drawer.getByRole("button", { name: /Save Commitment/i }).click();
		await expect(drawer).toHaveClass(/translate-x-full/, { timeout: 15_000 });
		await expect(vc.locator('[data-kt-str-vc-code="PVO-LOC-01"]')).toBeVisible({
			timeout: 15_000,
		});
		await expect(page.getByText(/Commitment saved \(UI fixture\)/i)).toHaveCount(0);

		await vc.getByRole("button", { name: /Add commitment/i }).click();
		await expect(drawer).toHaveClass(/is-open/);
		await drawer.getByRole("button", { name: "Cancel" }).click();
		await expect(drawer).toHaveClass(/translate-x-full/);
	});

	test("plan tabs navigate across Stitch surfaces", async ({ page }) => {
		const tabs: { label: string; slug: string; testid: string }[] = [
			{ label: "Structure", slug: "strategy-plan-structure", testid: "kt-str-structure" },
			{
				label: "Value Commitments",
				slug: "strategy-plan-value-commitments",
				testid: "kt-str-value-commitments",
			},
			{
				label: "Measurement",
				slug: "strategy-plan-measurements",
				testid: "kt-str-measurements",
			},
			{
				label: "Downstream Usage",
				slug: "strategy-plan-downstream-usage",
				testid: "kt-str-downstream",
			},
			{ label: "Review", slug: "strategy-plan-review", testid: "kt-str-review-blockers" },
			{ label: "Audit", slug: "strategy-plan-audit", testid: "kt-str-audit" },
		];

		await page.goto(`/desk/strategy-plan-overview/${PLAN}`, { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-str-overview")).toBeVisible({ timeout: 30_000 });

		for (const tab of tabs) {
			// Desk keeps prior Page hosts in DOM; scope to the visible canvas only.
			const visibleTabs = page.locator('[data-testid="kt-str-plan-tabs"]:visible');
			await visibleTabs.locator(`[data-kt-str-tab="${tab.slug}"]`).click({ force: true });
			await expect(page).toHaveURL(new RegExp(`${tab.slug}/${PLAN}`), { timeout: 15_000 });
			await expect(page.getByTestId(tab.testid)).toBeVisible({ timeout: 30_000 });
			await expect(page.locator('[data-testid="kt-str-plan-tabs"]:visible')).toHaveCount(1);
		}
	});

	test("plan structure mounts live tree for Active plan (read-only)", async ({ page }) => {
		await page.goto(`/desk/strategy-plan-structure/${PLAN}`, { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-str-structure")).toBeVisible({ timeout: 30_000 });
		await expect(page.locator('[data-testid="kt-str-structure"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});
		await expect(page.getByTestId("kt-str-structure-tree")).toBeVisible();
		await expect(page.getByTestId("kt-str-structure-detail")).toBeVisible();
		await expect(page.getByText("Structure Hierarchy")).toBeVisible();
		await expect(page.getByText("MOH-PROG-DH").first()).toBeVisible({ timeout: 15_000 });
		await expect(page.getByText("MOH-OUT-01").first()).toBeVisible();
		await expect(page.locator('[data-testid="kt-str-structure"][data-kt-str-structure-editable="0"]')).toBeVisible();
		await expect(page.getByRole("button", { name: /Add Structure Item/i })).toHaveCount(0);
		await expect(page.getByRole("button", { name: /Add Programme/i })).toHaveCount(0);
		// Never show a warning banner for zero issues (flex must not defeat .hidden).
		await expect(page.locator("[data-kt-str-structure-issues]")).toBeHidden();
		await expect(page.getByText(/0 structure issues/i)).toHaveCount(0);

		const split = await page.getByTestId("kt-str-structure-split").evaluate((el) => {
			const tree = el.querySelector("[data-testid='kt-str-structure-tree']") as HTMLElement;
			const detail = el.querySelector("[data-testid='kt-str-structure-detail']") as HTMLElement;
			const cs = getComputedStyle(el);
			return {
				display: cs.display,
				treeW: tree.getBoundingClientRect().width,
				detailW: detail.getBoundingClientRect().width,
				total: el.getBoundingClientRect().width,
			};
		});
		expect(split.display).toBe("flex");
		expect(split.treeW).toBeGreaterThan(split.total * 0.3);
		expect(split.detailW).toBeGreaterThan(split.total * 0.45);

		// Hierarchy indents must survive later .p-2 { padding } !important sheets.
		const treeIndent = await page.getByTestId("kt-str-structure-tree").evaluate((tree) => {
			const scroll = tree.querySelector("[data-kt-str-structure-tree-host]") || tree.querySelector(".overflow-y-auto");
			if (!scroll) return { ok: false };
			const items = [...scroll.children].filter((el) =>
				el.classList.contains("flex")
			) as HTMLElement[];
			const pl = (el: HTMLElement) => parseFloat(getComputedStyle(el).paddingLeft);
			const by = (token: string) =>
				items.find((el) => el.classList.contains(token));
			const prog = items[0];
			const sub = by("pl-8");
			const out = by("pl-14");
			const ind = by("pl-20");
			const tgt = by("pl-28");
			if (!prog || !sub || !out || !ind || !tgt) {
				return {
					ok: false,
					counts: items.length,
					classes: items.map((el) => el.className),
				};
			}
			return {
				ok: true,
				prog: pl(prog),
				sub: pl(sub),
				out: pl(out),
				ind: pl(ind),
				tgt: pl(tgt),
			};
		});
		expect(treeIndent.ok).toBe(true);
		expect(treeIndent.sub).toBeGreaterThan(treeIndent.prog + 8);
		expect(treeIndent.out).toBeGreaterThan(treeIndent.sub + 8);
		expect(treeIndent.ind).toBeGreaterThan(treeIndent.out + 8);
		expect(treeIndent.tgt).toBeGreaterThan(treeIndent.ind + 8);
		expect(treeIndent.tgt).toBeGreaterThanOrEqual(100); // pl-28 ≈ 7rem

		// Selecting Outcome updates detail panel from live DTO.
		await page.locator('[data-node-code="MOH-OUT-01"]').first().click();
		await expect(page.getByTestId("kt-str-structure-detail").getByText("MOH-OUT-01").first()).toBeVisible();
		await expect(
			page
				.getByTestId("kt-str-structure-detail")
				.getByRole("heading", { name: /Reliable and accessible digital clinical/i })
		).toBeVisible();
	});

	test("plan structure Draft empty can add Programme via drawer", async ({ page }) => {
		const suffix = Date.now().toString().slice(-6);
		const code = `UI03-STR-${suffix}`;
		await page.goto("/desk/strategy-plan-create", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-create-plan"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});
		await page.locator('[data-kt-str-field="plan_code"]').fill(code);
		await page.locator('[data-kt-str-field="title"]').fill(`Structure live ${suffix}`);
		await page.locator('[data-kt-str-field="plan_type"]').selectOption("entity");
		const peSelect = page.locator('[data-kt-str-field="procuring_entity_select"]');
		if (!(await peSelect.isDisabled())) {
			const options = await peSelect.locator("option").allTextContents();
			const moh = options.find((t) => /MOH|Health|PE-MOH/i.test(t));
			if (moh) {
				await peSelect.selectOption({ label: moh.trim() });
			} else {
				await peSelect.selectOption({ index: 1 });
			}
		}
		await page.locator('[data-kt-str-field="start_date"]').fill("2026-07-01");
		await page.locator('[data-kt-str-field="end_date"]').fill("2030-06-30");
		await page.getByTestId("kt-str-create-plan-submit").click();
		await expect(page).toHaveURL(new RegExp(`strategy-plan-overview/${code}`), { timeout: 20_000 });
		await page.getByTestId("kt-str-start-plan-structure").click();
		await expect(page).toHaveURL(/strategy-plan-structure/, { timeout: 15_000 });
		await expect(page.locator('[data-testid="kt-str-structure"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});
		await expect(page.locator('[data-testid="kt-str-structure"][data-kt-str-structure-editable="1"]')).toBeVisible();
		await expect(page.getByText(/No structure yet/i)).toBeVisible();
		await page.getByRole("button", { name: /Add Programme/i }).click();
		// Wrapper carries kt-str-root so token/focus CSS applies; overlay is the visible surface.
		const drawerRoot = page.getByTestId("kt-str-structure-drawer");
		await expect(drawerRoot).toHaveCount(1);
		await expect(drawerRoot).toHaveClass(/kt-str-root/);
		const overlay = page.getByTestId("kt-str-structure-drawer-overlay");
		await expect(overlay).toBeVisible({ timeout: 15_000 });
		const panel = page.getByTestId("kt-str-structure-drawer-panel");
		await expect(panel.getByRole("heading", { name: /Add Programme/i })).toBeVisible();
		await expect(overlay).toHaveAttribute("data-dismiss", "explicit-only");
		// Focus chrome: light blue, not near-black primary.
		const focusChrome = await panel.locator('input[name="code"]').evaluate((el) => {
			el.focus();
			const cs = getComputedStyle(el);
			return { border: cs.borderColor, outline: cs.outlineColor, shadow: cs.boxShadow };
		});
		expect(focusChrome.border).toMatch(/123,\s*190,\s*255|123 190 255|#7bbeff/i);
		expect(focusChrome.border).not.toMatch(/0,\s*31,\s*72|0 31 72|#001f48/i);
		await overlay.evaluate((el) => el.dispatchEvent(new MouseEvent("click", { bubbles: true })));
		await expect(overlay).toBeVisible();
		await panel.locator('input[name="code"]').fill(`${code}-PROG`);
		await panel.locator('input[name="title"]').fill("Digital Services Programme");
		await panel.locator('input[name="responsible_function"]').fill("ICT");
		await panel.getByRole("button", { name: /^Save$/i }).click();
		await expect(overlay).toHaveCount(0, { timeout: 15_000 });
		await expect(page.getByText(`${code}-PROG`).first()).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("kt-str-structure-detail").getByText("Digital Services Programme")).toBeVisible();

		// Cancel closes without save on a second open.
		await page.getByRole("button", { name: /Add Structure Item/i }).click();
		await expect(page.getByTestId("kt-str-structure-drawer-overlay")).toBeVisible({ timeout: 10_000 });
		await page.getByTestId("kt-str-structure-drawer-panel").getByRole("button", { name: "Cancel" }).click();
		await expect(page.getByTestId("kt-str-structure-drawer-overlay")).toHaveCount(0);
	});

	test("review state toggle switches blocker and ready fixtures", async ({ page }) => {
		await page.goto(`/desk/strategy-plan-review/${PLAN}`, { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-str-review-state-toggle")).toBeVisible({ timeout: 30_000 });
		await page
			.getByTestId("kt-str-review-state-toggle")
			.getByRole("button", { name: "Show ready for submission" })
			.click({ force: true });
		await expect(page.getByTestId("kt-str-review-ready")).toBeVisible({ timeout: 30_000 });
		await page
			.getByTestId("kt-str-review-state-toggle")
			.getByRole("button", { name: "Show blockers" })
			.click({ force: true });
		await expect(page.getByTestId("kt-str-review-blockers")).toBeVisible({ timeout: 30_000 });
	});

	test("satellite surfaces open", async ({ page }) => {
		await page.goto("/desk/strategy-pvo-catalogue", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-str-pvo-catalogue")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByRole("button", { name: /Create objective/i })).toBeVisible();

		await page.goto("/desk/strategy-pvo-editor", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-str-pvo-editor")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByRole("button", { name: /Save objective/i })).toBeVisible();

		await page.goto(`/desk/strategy-measurement-submit/${TARGET}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.getByTestId("kt-str-measurement-submit")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByRole("button", { name: /Submit measurement/i })).toBeVisible();

		await page.goto(`/desk/strategy-measurement-verify/${TARGET}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.getByTestId("kt-str-measurement-verify")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByRole("button", { name: /Verify Measurement/i })).toBeVisible();

		await page.goto("/desk/strategy-corrective-actions", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-str-corrective-actions")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByRole("button", { name: /Create corrective action/i })).toBeVisible();
	});

	test("measurements register is live for Active plan", async ({ page }) => {
		await page.goto(`/desk/strategy-plan-measurements/${PLAN}`, {
			waitUntil: "domcontentloaded",
		});
		const meas = page.locator('[data-testid="kt-str-measurements"][data-kt-str-live="1"]:visible');
		await expect(meas).toBeVisible({ timeout: 30_000 });
		await expect(meas.getByTestId("kt-str-measurements-table")).toBeVisible();
		await expect(meas.getByRole("heading", { name: "Performance measurements" })).toBeVisible();
		// Seed truth: two Verified MOH-TGT-01 rows — not fixture-only TGT-02/03.
		await expect(
			meas.locator('[data-kt-str-meas-tbody] tr[data-kt-str-target-code="MOH-TGT-01"]')
		).toHaveCount(2, { timeout: 15_000 });
		await expect(meas.getByText("MOH-TGT-02")).toHaveCount(0);
		await expect(meas.getByText("MOH-TGT-03")).toHaveCount(0);
		await expect(meas.locator('[data-kt-str-meas-count="verified"]')).toHaveText(/^[2-9]\d*$/);
		await expect(meas.locator('[data-kt-str-meas-count="due"]')).toHaveText("0");
		await expect(page.getByText(/UI fixture — no backend yet/i)).toHaveCount(0);

		await meas.getByRole("button", { name: /Submit measurement/i }).first().click();
		await expect(page).toHaveURL(
			new RegExp(`strategy-measurement-submit/${PLAN}/MOH-TGT-01`),
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-str-measurement-submit")).toBeVisible({ timeout: 30_000 });
	});

	test("downstream and audit mount Stitch tables", async ({ page }) => {
		await page.goto(`/desk/strategy-plan-downstream-usage/${PLAN}`, {
			waitUntil: "domcontentloaded",
		});
		const down = page.getByTestId("kt-str-downstream");
		await expect(down).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-str-downstream-table")).toBeVisible();

		await page.goto(`/desk/strategy-plan-audit/${PLAN}`, { waitUntil: "domcontentloaded" });
		const audit = page.getByTestId("kt-str-audit");
		await expect(audit).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-str-audit-table")).toBeVisible();
		await expect(audit.getByRole("heading", { name: "Audit history" })).toBeVisible();
	});
});
