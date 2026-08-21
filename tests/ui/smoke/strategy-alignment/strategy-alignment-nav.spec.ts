import { execSync } from "node:child_process";
import path from "node:path";

import { test, expect, type Page } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * Strategy Alignment MVP-1 — Stitch Desk shells + live API binders.
 * Requires MOH-SP-2026-2030 seed (works_master_strategy_hierarchy).
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const PLAN = "MOH-SP-2026-2030";
const REVIEW_BLOCKERS_PLAN = "MOH-SP-9001";
const REVIEW_TX_PLAN = "MOH-SP-9002";
const TARGET = "MOH-TGT-AVAIL-2028";

function seedStrategyDownstreamFixtures(): void {
	try {
		execSync("redis-cli -p 11000 FLUSHDB", { stdio: "pipe" });
	} catch {
		/* ignore */
	}
	let lastErr: unknown;
	for (let attempt = 1; attempt <= 3; attempt += 1) {
		try {
			execSync(
				`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ` +
					"kentender_strategy.seeds.works_master_strategy_hierarchy.upsert_works_master_strategy_hierarchy",
				{ stdio: "pipe", timeout: 180_000 },
			);
			execSync(
				`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ` +
					"kentender_strategy.seeds.moh_downstream_usage.seed_moh_downstream_usage_refs",
				{ stdio: "pipe", timeout: 180_000 },
			);
			return;
		} catch (e) {
			lastErr = e;
			execSync("sleep 2");
		}
	}
	throw lastErr;
}

test.describe.configure({ mode: "serial" });

test.describe("Strategy Alignment UI shell", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("Strategy Performance management view loads (STR-UI-15)", async ({ page }) => {
		await page.goto("/desk/strategy-performance", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-performance"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.getByTestId("kt-str-perf-header")).toBeVisible();
		await expect(page.getByTestId("kt-str-perf-strip")).toBeVisible();
		await expect(page.getByTestId("kt-str-perf-exceptions")).toBeVisible();
		await expect(page.getByTestId("kt-str-perf-outcomes")).toBeVisible();
		await expect(page.getByTestId("kt-str-perf-procurement")).toBeVisible();
		await expect(page.getByTestId("kt-str-perf-commitments")).toBeVisible();
		await expect(page.getByTestId("kt-str-perf-export")).toBeVisible();
		// Stitch regions / column contract (not title-only).
		await expect(page.getByRole("heading", { name: "Exceptions Requiring Intervention" })).toBeVisible();
		await expect(page.getByRole("heading", { name: /Outcome Performance/ })).toBeVisible();
		await expect(page.getByText("Funding Snapshot", { exact: true })).toBeVisible();
		await expect(page.getByRole("heading", { name: "Aligned Procurement Pipeline" })).toBeVisible();
		await expect(page.getByRole("heading", { name: "Strategy Value Commitments" })).toBeVisible();
		await expect(page.getByRole("columnheader", { name: /FUNDING TREATMENT/i })).toBeVisible();
		await expect(page.getByRole("columnheader", { name: /DOWNSTREAM ADOPTION/i })).toBeVisible();
		// Context filter grid is 4 columns at desktop (not stacked full-width cards).
		const filterGeom = await page.getByTestId("kt-str-perf-filters").evaluate((el) => {
			const grid = el.querySelector(":scope > .grid") as HTMLElement | null;
			if (!grid) return { ok: false };
			const kids = Array.from(grid.children) as HTMLElement[];
			if (kids.length < 3) return { ok: false, n: kids.length };
			const tops = kids.map((k) => k.getBoundingClientRect().top);
			const sameRow = Math.abs(tops[0] - tops[1]) < 8 && Math.abs(tops[0] - tops[2]) < 8;
			const widths = kids.slice(0, 3).map((k) => k.getBoundingClientRect().width);
			return { ok: sameRow && widths.every((w) => w > 80 && w < 520), sameRow, widths };
		});
		expect(filterGeom.ok).toBeTruthy();
		// On-track strip tile keeps Stitch green surface (not plain white).
		const onTrackBg = await page
			.locator('[data-testid="kt-str-perf-strip"] .bg-\\[\\#f0fdf4\\]')
			.evaluate((el) => getComputedStyle(el).backgroundColor);
		expect(onTrackBg).toMatch(/rgb\(\s*240,\s*253,\s*244\s*\)/);
		// Filter selects must keep a chevron glyph (Tailwind Forms stand-in or Material sibling).
		const selectGlyph = await page.locator("#kt-str-perf-programme").evaluate((el) => {
			const cs = getComputedStyle(el);
			const bg = cs.backgroundImage || "";
			const sib = el.nextElementSibling;
			const material =
				!!sib &&
				sib.classList.contains("material-symbols-outlined") &&
				(sib.textContent || "").trim() === "expand_more";
			return {
				hasSvgChevron: bg.includes("svg") || bg.includes("data:image"),
				material,
				paddingRight: parseFloat(cs.paddingRight || "0"),
			};
		});
		expect(selectGlyph.hasSvgChevron || selectGlyph.material).toBeTruthy();
		expect(selectGlyph.paddingRight).toBeGreaterThanOrEqual(24);
		// Not a Plan workspace tab surface — no seven-tab chrome.
		await expect(page.getByTestId("kt-str-plan-tabs")).toHaveCount(0);
		// No create/maintenance controls on Performance.
		await expect(page.getByTestId("kt-str-create-plan")).toHaveCount(0);
		await expect(page.getByRole("heading", { name: "Strategy Performance" })).toBeVisible();
		await expect(page.locator('[data-kt-str-strip="active_targets"]')).not.toHaveText("—");
	});

	test("Strategy Performance shows Planning stage and PVC adoption depth (XMOD-STR-007)", async ({
		page,
	}) => {
		test.setTimeout(240_000);
		try {
			execSync("redis-cli -p 11000 FLUSHDB", { stdio: "pipe" });
		} catch {
			/* ignore */
		}
		execSync(
			`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ` +
				"kentender_strategy.seeds.works_master_strategy_hierarchy.upsert_works_master_strategy_hierarchy",
			{ stdio: "pipe", timeout: 180_000 },
		);
		execSync(
			`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ` +
				"kentender_strategy.seeds.moh_downstream_usage.seed_moh_performance_contribution_depth",
			{ stdio: "pipe", timeout: 180_000 },
		);
		await page.goto("/desk/strategy-performance", { waitUntil: "domcontentloaded" });
		const root = page.locator('[data-testid="kt-str-performance"][data-kt-str-live="1"]');
		await expect(root).toBeVisible({ timeout: 30_000 });

		const planningRow = root.locator('[data-kt-str-perf-stage="procurement-plan"]');
		await expect(planningRow).toBeVisible({ timeout: 15_000 });
		const planningCount = Number(
			(await planningRow.getAttribute("data-kt-str-perf-stage-count")) || "0",
		);
		expect(planningCount).toBeGreaterThan(0);
		await expect(planningRow.locator("[data-kt-str-perf-stage-value]")).not.toHaveText("—");

		const adoption = root.locator('[data-kt-str-perf-adoption="MOH-PVC-EFT-01"]').first();
		await expect(adoption).toBeVisible({ timeout: 15_000 });
		await expect(adoption).toContainText(/aligned Value Cases addressed/i);
		await expect(adoption).not.toHaveText(/^0 of /);
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
		await expect(page.getByTestId("kt-str-open-performance")).toBeVisible();
		// Seed Active plan row (Draft successors share the same plan_code).
		const mohRow = page.locator(
			'[data-testid="kt-str-plans-table"] tr[data-plan-code="MOH-SP-2026-2030"][data-plan-status="Active"]'
		);
		await expect(mohRow).toBeVisible({ timeout: 15_000 });
		await expect(mohRow.getByText("MOH-SP-2026-2030", { exact: true })).toBeVisible();
		// Period stacks start/end so Plan/Status get horizontal room.
		const periodCell = mohRow.locator(".kt-str-plans-col-period");
		await expect(periodCell.locator(".kt-str-period-start")).toHaveText(
			/^\d{2}-[A-Z][a-z]{2}-\d{4}$/
		);
		await expect(periodCell.locator(".kt-str-period-end")).toHaveText(
			/^\d{2}-[A-Z][a-z]{2}-\d{4}$/
		);
		const colGeom = await mohRow.evaluate((row) => {
			const plan = row.querySelector(".kt-str-plans-col-plan") as HTMLElement | null;
			const period = row.querySelector(".kt-str-plans-col-period") as HTMLElement | null;
			const start = period?.querySelector(".kt-str-period-start") as HTMLElement | null;
			const end = period?.querySelector(".kt-str-period-end") as HTMLElement | null;
			const startR = start?.getBoundingClientRect();
			const endR = end?.getBoundingClientRect();
			return {
				planW: plan ? plan.getBoundingClientRect().width : 0,
				periodW: period ? period.getBoundingClientRect().width : 0,
				stacked: !!(startR && endR && endR.top > startR.bottom - 2),
				// Each date must stay on one line (no mid-token wrap like "01-Jul-" / "2026").
				startSingleLine: !!(startR && startR.height > 0 && startR.height <= 22),
				endSingleLine: !!(endR && endR.height > 0 && endR.height <= 22),
			};
		});
		expect(colGeom.planW).toBeGreaterThanOrEqual(220);
		expect(colGeom.planW).toBeGreaterThan(colGeom.periodW);
		expect(colGeom.periodW).toBeGreaterThanOrEqual(100);
		expect(colGeom.periodW).toBeLessThan(160);
		expect(colGeom.stacked).toBe(true);
		expect(colGeom.startSingleLine).toBe(true);
		expect(colGeom.endSingleLine).toBe(true);
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
		// DS primary #003d9b
		expect(geometry.btnBg).toBe("rgb(0, 61, 155)");

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
		await search.fill("MOH-SP-2026-2030");
		// Same plan_code may appear as Active + Draft successor versions.
		await expect(
			page.locator(
				'[data-testid="kt-str-plans-table"] tr[data-plan-code="MOH-SP-2026-2030"][data-plan-status="Active"]'
			)
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

		// Module focus lock: light blue on create fields (not navy primary / 2px ring).
		const createRoot = page.getByTestId("kt-str-create-plan");
		const titleField = createRoot.locator('[data-kt-str-field="title"]');
		await titleField.focus();
		const createFocus = await titleField.evaluate((el) => {
			const cs = getComputedStyle(el);
			const m = (cs.borderColor || "").match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
			return {
				borderColor: cs.borderColor,
				boxShadow: cs.boxShadow,
				r: m ? Number(m[1]) : -1,
				g: m ? Number(m[2]) : -1,
				b: m ? Number(m[3]) : -1,
			};
		});
		expect(createFocus.r).toBeGreaterThan(100);
		expect(createFocus.b).toBeGreaterThan(createFocus.r);
		expect(createFocus.r).not.toBe(0);
		expect(createFocus.g).not.toBe(31);
		expect(createFocus.boxShadow).not.toMatch(/0,\s*31,\s*72|#001f48/i);
		expect(createFocus.boxShadow.toLowerCase()).not.toBe("none");
		const peField = createRoot.locator('select[data-kt-str-field="procuring_entity_select"]');
		await peField.focus();
		const peFocus = await peField.evaluate((el) => {
			const c = getComputedStyle(el).borderColor || "";
			const s = getComputedStyle(el).boxShadow || "";
			return { c, s, navy: /0,\s*31,\s*72|#001f48/i.test(c + s) };
		});
		expect(peFocus.navy).toBe(false);
		expect(peFocus.c.toLowerCase()).not.toBe("rgb(0, 31, 72)");

		// Inline validation keeps the form open (title required — not plan_code).
		await page.getByTestId("kt-str-create-plan-submit").click();
		await expect(page.locator('[data-kt-str-error="title"]')).toBeVisible();
		await expect(page).toHaveURL(/strategy-plan-create/);
		await expect(page.getByTestId("kt-str-create-plan-reference")).toBeVisible();
		await expect(page.getByText("Generated automatically on save")).toBeVisible();

		const suffix = Date.now().toString().slice(-6);
		// Stitch regions from create_plan/code.html
		await expect(page.getByTestId("kt-str-create-bento")).toBeVisible();
		await expect(page.getByText("Basic Information")).toBeVisible();
		await expect(page.getByTestId("kt-str-create-plan-context")).toBeVisible();
		await expect(page.getByTestId("kt-str-create-quote")).toHaveCount(0);
		await expect(page.getByTestId("kt-str-create-actions")).toBeVisible();
		// Stitch/Tailwind Forms select chevron (SVG background) + date calendar glyphs.
		await expect(createRoot.locator(".material-symbols-outlined", { hasText: "calendar_today" })).toHaveCount(2);
		const selectGlyphs = await createRoot.locator("select:visible").evaluateAll((els) =>
			els.map((el) => {
				const cs = getComputedStyle(el);
				return {
					hasChevron: /url\(|data:image\/svg/.test(cs.backgroundImage),
					padRight: parseFloat(cs.paddingRight),
				};
			})
		);
		// Visible by default: plan type + procuring entity (subordinate parent/scope stay hidden for ESP).
		expect(selectGlyphs.length).toBe(2);
		for (const g of selectGlyphs) {
			expect(g.hasChevron).toBe(true);
			expect(g.padRight).toBeGreaterThanOrEqual(32);
		}
		await expect(createRoot.locator("[data-kt-str-create-subordinate]")).toBeHidden();
		await expect(createRoot.locator('[data-kt-str-field="plan_type"] option', { hasText: "Thematic Plan" })).toHaveCount(1);
		await expect(createRoot.locator('[data-kt-str-field="plan_type"] option', { hasText: "Sector Strategy" })).toHaveCount(0);

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
		await expect(page).toHaveURL(/strategy-plan-overview\/[A-Z0-9]+-SP-\d{4}/, { timeout: 20_000 });
		const overviewUrl = page.url();
		const refMatch = overviewUrl.match(/strategy-plan-overview\/([A-Z0-9]+-SP-\d{4})/);
		expect(refMatch?.[1]).toBeTruthy();
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
		const cancelTitle = `Cancel ${suffix}`;
		await page.goto("/desk/strategy-plan-create", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-create-plan"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});
		await expect(page.locator('[data-kt-str-field="plan_code"]')).toHaveCount(0);
		await page.locator('[data-kt-str-field="title"]').fill(cancelTitle);
		await page.getByTestId("kt-str-create-plan-cancel").click();
		await expect(page).toHaveURL(/strategy-alignment/, { timeout: 15_000 });
		await expect(page.locator('[data-testid="kt-str-portfolio"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});
		const search = page.getByTestId("kt-str-pf-filters").getByLabel("Search plans");
		await search.fill(cancelTitle);
		await expect(page.locator('[data-testid="kt-str-plans-table"] [data-kt-str-empty="1"]')).toBeVisible({
			timeout: 10_000,
		});
	});

	test("Create Programme Strategy requires parent and distinct scope (STR-FR-005)", async ({ page }) => {
		const suffix = Date.now().toString().slice(-6);
		await page.goto("/desk/strategy-plan-create", { waitUntil: "domcontentloaded" });
		const createRoot = page.locator('[data-testid="kt-str-create-plan"][data-kt-str-live="1"]');
		await expect(createRoot).toBeVisible({ timeout: 20_000 });
		const peSelect = page.locator('[data-kt-str-field="procuring_entity_select"]');
		await expect(peSelect).toBeVisible();
		if (!(await peSelect.isDisabled())) {
			const options = await peSelect.locator("option").allTextContents();
			const moh = options.find((t) => /MOH|Health|PE-MOH/i.test(t));
			if (moh) {
				await peSelect.selectOption({ label: moh.trim() });
			} else {
				await peSelect.selectOption({ index: 1 });
			}
		}
		await page.locator('[data-kt-str-field="plan_type"]').selectOption("programme");
		await expect(createRoot.locator("[data-kt-str-create-subordinate]")).toBeVisible();
		await page.locator('[data-kt-str-field="title"]').fill(`Programme Strategy ${suffix}`);
		await page.getByTestId("kt-str-create-plan-submit").click();
		await expect(page.locator('[data-kt-str-error="parent_plan"]')).toBeVisible();
		const parentSelect = page.locator('[data-kt-str-field="parent_plan"]');
		await expect(parentSelect.locator("option")).not.toHaveCount(1, { timeout: 10_000 });
		const parentValue = await parentSelect.locator("option").nth(1).getAttribute("value");
		expect(parentValue).toBeTruthy();
		await parentSelect.selectOption(parentValue!);
		await page.locator('[data-kt-str-field="scope_type"]').selectOption("Programme");
		await page.locator('[data-kt-str-field="scope_id"]').fill(`MOH-PROG-UI-${suffix}`);
		await page.locator('[data-kt-str-field="start_date"]').fill("2026-07-01");
		await page.locator('[data-kt-str-field="end_date"]').fill("2028-06-30");
		await page.getByTestId("kt-str-create-plan-submit").click();
		await expect(page).toHaveURL(/strategy-plan-overview\/[A-Z0-9]+-SP-\d{4}/, { timeout: 20_000 });
		await expect(page.getByTestId("kt-str-overview")).toBeVisible({ timeout: 30_000 });
	});

	test("View navigates to plan overview with refresh-safe plan code", async ({ page }) => {
		await page.goto("/desk/strategy-alignment", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-str-portfolio")).toBeVisible({ timeout: 30_000 });
		await expect(
			page.locator(
				`[data-testid="kt-str-plans-table"] tr[data-plan-code="${PLAN}"][data-plan-status="Active"]`
			)
		).toBeVisible({ timeout: 20_000 });
		await page
			.locator(
				`[data-testid="kt-str-plans-table"] tr[data-plan-code="${PLAN}"][data-plan-status="Active"] button[data-kt-str-action="open-plan"]`
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

	test("strategy typography resists Desk Espresso weight/tracking", async ({ page }) => {
		await page.goto(`/desk/strategy-plan-overview/${PLAN}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-overview"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		const typo = await page.evaluate(() => {
			const title = document.querySelector(
				'[data-testid="kt-str-plan-chrome"] h1'
			) as HTMLElement | null;
			const meta = document.querySelector(
				'[data-testid="kt-str-plan-chrome"] [data-kt-str-chrome-meta] p'
			) as HTMLElement | null;
			const section = document.querySelector(
				'.kt-str-root h2.font-headline-sm'
			) as HTMLElement | null;
			const t = title ? getComputedStyle(title) : null;
			const m = meta ? getComputedStyle(meta) : null;
			const s = section ? getComputedStyle(section) : null;
			return {
				titleFamily: t?.fontFamily || "",
				titleSize: t?.fontSize || "",
				titleWeight: t?.fontWeight || "",
				titleTracking: t?.letterSpacing || "",
				metaFamily: m?.fontFamily || "",
				metaSize: m?.fontSize || "",
				metaWeight: m?.fontWeight || "",
				metaTracking: m?.letterSpacing || "",
				metaLine: m?.lineHeight || "",
				sectionTracking: s?.letterSpacing || "",
				sectionWeight: s?.fontWeight || "",
			};
		});
		expect(typo.titleFamily).toMatch(/Manrope/i);
		expect(typo.titleSize).toBe("30px");
		expect(typo.titleWeight).toBe("700");
		// DS headline-lg 30px × −0.02em → −0.6px
		expect(typo.titleTracking).toBe("-0.6px");
		expect(typo.metaFamily).toMatch(/Inter/i);
		expect(typo.metaSize).toBe("14px");
		expect(typo.metaWeight).toBe("400");
		expect(typo.metaTracking).toBe("normal");
		expect(typo.metaLine).toBe("20px");
		expect(typo.sectionWeight).toBe("600");
		expect(typo.sectionTracking).toBe("normal");
	});

	test("VC and Measurements section titles share headline-md density", async ({ page }) => {
		const samples: { path: string; live: string; title: string }[] = [
			{
				path: `/desk/strategy-value-commitments/${PLAN}`,
				live: '[data-testid="kt-str-value-commitments"][data-kt-str-live="1"]',
				title: "Plan value commitments",
			},
			{
				path: `/desk/strategy-plan-measurements/${PLAN}`,
				live: '[data-testid="kt-str-measurements"][data-kt-str-live="1"]',
				title: "Performance measurements",
			},
		];
		const measured: { size: string; weight: string; family: string; gap: number }[] = [];
		for (const { path, live, title } of samples) {
			await page.goto(path, { waitUntil: "domcontentloaded" });
			await expect(page.locator(live).first()).toBeVisible({ timeout: 30_000 });
			const info = await page.evaluate((heading) => {
				const root = document.querySelector(".kt-str-root") as HTMLElement | null;
				const tabs = root?.querySelector('[data-testid="kt-str-plan-tabs"]') as HTMLElement | null;
				const h = [...(root?.querySelectorAll("h1,h2,h3") || [])].find((el) =>
					(el.textContent || "").includes(heading)
				) as HTMLElement | undefined;
				if (!h || !tabs) {
					return null;
				}
				const hs = getComputedStyle(h);
				return {
					size: hs.fontSize,
					weight: hs.fontWeight,
					family: hs.fontFamily,
					gap: Math.round(h.getBoundingClientRect().top - tabs.getBoundingClientRect().bottom),
					tag: h.tagName,
					color: hs.color,
				};
			}, title);
			expect(info).toBeTruthy();
			expect(info!.family).toMatch(/Manrope/i);
			expect(info!.size).toBe("22px");
			expect(info!.weight).toBe("600");
			expect(info!.tag).toBe("H3");
			/* Tabs → section title: tightened from pt-6 (24px) to pt-4 (16px). */
			expect(info!.gap).toBeLessThanOrEqual(20);
			expect(info!.gap).toBeGreaterThanOrEqual(12);
			measured.push({ size: info!.size, weight: info!.weight, family: info!.family, gap: info!.gap });
		}
		expect(measured[0].size).toBe(measured[1].size);
		expect(measured[0].weight).toBe(measured[1].weight);
	});

	async function assertVisiblePlanChrome(page: Page, live: string) {
		const $live = page.locator(live).first();
		await expect($live).toBeVisible({ timeout: 30_000 });
		const $chrome = $live.locator('[data-testid="kt-str-plan-chrome"]');
		await expect($chrome).toHaveCount(1);
		await expect($live.locator('[data-testid="kt-str-plan-tabs"]')).toHaveCount(1);
		const chrome = await $chrome.evaluate((el) => {
			const codeRow = el.querySelector("[data-kt-str-chrome-code-row]");
			const code = codeRow?.querySelector("[data-kt-str-plan-code]");
			const pill = codeRow?.querySelector("[data-kt-str-plan-status-pill]");
			const meta = el.querySelector("[data-kt-str-chrome-meta]");
			const statusInMeta = !!meta?.querySelector("[data-kt-str-plan-status-pill], [data-kt-str-plan-status]");
			const period = (meta?.querySelector("[data-kt-str-plan-period]")?.textContent || "").trim();
			const version = (meta?.querySelector("[data-kt-str-plan-version]")?.textContent || "").trim();
			let statusAfterCode = false;
			if (code && pill && codeRow) {
				const kids = [...codeRow.children];
				statusAfterCode = kids.indexOf(pill) === kids.indexOf(code) + 1;
			}
			return {
				code: (code?.textContent || "").trim(),
				status: (pill?.querySelector("[data-kt-str-plan-status]")?.textContent || "").trim(),
				statusAfterCode,
				statusInMeta,
				period,
				version,
				pillTone: pill?.className || "",
				sticky: getComputedStyle(el).position === "sticky",
				tabCount: el.querySelectorAll("[data-kt-str-tab]").length,
				injected: el.classList.contains("kt-str-injected-plan-chrome"),
			};
		});
		expect(chrome.injected).toBe(true);
		expect(chrome.code).toBe(PLAN);
		expect(chrome.status).toMatch(/^(Active|Draft|Submitted|Returned|Approved)$/);
		expect(chrome.statusAfterCode).toBe(true);
		expect(chrome.statusInMeta).toBe(false);
		/* Regression: Downstream once painted compact "v1" beside the calendar — forbid that. */
		expect(chrome.period).toMatch(/^Effective \d{2}-[A-Z][a-z]{2}-\d{4} - \d{2}-[A-Z][a-z]{2}-\d{4}$/);
		expect(chrome.version).toMatch(/^Version \d+$/);
		expect(chrome.version).not.toMatch(/^v\d+$/i);
		expect(chrome.period).not.toMatch(/^v\d+$/i);
		expect(chrome.sticky).toBe(false);
		expect(chrome.tabCount).toBe(7);
		if (chrome.status === "Active" || chrome.status === "Approved") {
			expect(chrome.pillTone).toMatch(/status-available/);
		}
		return chrome;
	}

	test("shared plan chrome is identical across plan tabs", async ({ page }) => {
		const routes = [
			{ path: `/desk/strategy-plan-overview/${PLAN}`, live: '[data-testid="kt-str-overview"][data-kt-str-live="1"]' },
			{ path: `/desk/strategy-plan-structure/${PLAN}`, live: '[data-testid="kt-str-structure"][data-kt-str-live="1"]' },
			{
				path: `/desk/strategy-value-commitments/${PLAN}`,
				live: '[data-testid="kt-str-value-commitments"][data-kt-str-live="1"]',
			},
			{
				path: `/desk/strategy-plan-measurements/${PLAN}`,
				live: '[data-testid="kt-str-measurements"][data-kt-str-live="1"]',
			},
			{
				path: `/desk/strategy-plan-downstream-usage/${PLAN}`,
				live: '[data-testid="kt-str-downstream"][data-kt-str-live="1"]',
			},
			{ path: `/desk/strategy-plan-review/${PLAN}`, live: '[data-testid^="kt-str-review-"][data-kt-str-live="1"]' },
			{ path: `/desk/strategy-plan-audit/${PLAN}`, live: '[data-testid="kt-str-audit"][data-kt-str-live="1"]' },
		];
		for (const { path, live } of routes) {
			await page.goto(path, { waitUntil: "domcontentloaded" });
			await assertVisiblePlanChrome(page, live);
		}
	});

	test("plan tab soft-nav reuses mounted DOM without remount flash", async ({ page }) => {
		await page.goto(`/desk/strategy-plan-overview/${PLAN}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-overview"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		const first = await page.locator('[data-testid="kt-str-overview"]').evaluate((el) => ({
			key: el.getAttribute("data-kt-str-mount-key") || "",
			gen: el.getAttribute("data-kt-str-mount-gen") || "",
			live: el.getAttribute("data-kt-str-live") || "",
		}));
		expect(first.key).toContain("strategy-plan-overview");
		expect(Number(first.gen)).toBeGreaterThanOrEqual(1);
		expect(first.live).toBe("1");

		await page.locator('[data-testid="kt-str-overview"] [data-kt-str-tab="strategy-plan-measurements"]').click();
		await expect(page.locator('[data-testid="kt-str-measurements"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await page
			.locator('[data-testid="kt-str-measurements"] [data-kt-str-tab="strategy-plan-overview"]')
			.click();
		await expect(page.locator('[data-testid="kt-str-overview"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		const again = await page.locator('[data-testid="kt-str-overview"]').evaluate((el) => ({
			key: el.getAttribute("data-kt-str-mount-key") || "",
			gen: el.getAttribute("data-kt-str-mount-gen") || "",
			live: el.getAttribute("data-kt-str-live") || "",
		}));
		expect(again.key).toBe(first.key);
		expect(again.gen).toBe(first.gen);
		expect(again.live).toBe("1");
	});

	test("plan tab hop never flashes empty plan chrome placeholders", async ({ page }) => {
		await page.goto(`/desk/strategy-plan-overview/${PLAN}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-overview"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		const seedTitle = (
			await page
				.locator(
					'[data-testid="kt-str-overview"]:visible [data-testid="kt-str-plan-chrome"] [data-kt-str-plan-title]'
				)
				.textContent()
		)?.trim();
		expect(seedTitle && seedTitle !== "—").toBeTruthy();

		const titles = await page.evaluate(async (tabSlug) => {
			const samples = [];
			const push = () => {
				const visible = [...document.querySelectorAll('[data-testid="kt-str-plan-chrome"]')].find(
					(node) => {
						const pc = node.closest(".page-container");
						if (!pc) return false;
						return getComputedStyle(pc).display !== "none";
					}
				);
				const title = (
					(visible && visible.querySelector("[data-kt-str-plan-title]")?.textContent) ||
					""
				).trim();
				samples.push(title);
			};
			const tab = document.querySelector(
				`[data-testid="kt-str-overview"]:not([style*="display: none"]) [data-kt-str-tab="${tabSlug}"]`
			);
			if (!tab) return { samples, err: "no-tab" };
			tab.click();
			push();
			await new Promise((r) => requestAnimationFrame(() => r(null)));
			push();
			for (let i = 0; i < 8; i++) {
				await new Promise((r) => setTimeout(r, 40));
				push();
			}
			return { samples, err: null };
		}, "strategy-plan-structure");

		expect(titles.err).toBeNull();
		expect(titles.samples.length).toBeGreaterThan(3);
		// After the destination page is shown, title must stay hydrated (never "—").
		const afterSwap = titles.samples.slice(1);
		expect(afterSwap.some((t) => t && t !== "—")).toBe(true);
		expect(afterSwap.every((t) => !t || t !== "—")).toBe(true);
		await expect(
			page.locator(
				'[data-testid="kt-str-structure"]:visible [data-testid="kt-str-plan-chrome"] [data-kt-str-plan-title]'
			)
		).not.toHaveText("—");
		await expect(
			page.locator(
				'[data-testid="kt-str-structure"]:visible [data-testid="kt-str-plan-chrome"] [data-kt-str-plan-title]'
			)
		).toHaveText(seedTitle!);
	});

	test("shared plan chrome survives soft tab navigation", async ({ page }) => {
		const hops: { slug: string; live: string }[] = [
			{ slug: "strategy-plan-downstream-usage", live: '[data-testid="kt-str-downstream"][data-kt-str-live="1"]' },
			{ slug: "strategy-plan-structure", live: '[data-testid="kt-str-structure"][data-kt-str-live="1"]' },
			{
				slug: "strategy-value-commitments",
				live: '[data-testid="kt-str-value-commitments"][data-kt-str-live="1"]',
			},
			{ slug: "strategy-plan-measurements", live: '[data-testid="kt-str-measurements"][data-kt-str-live="1"]' },
			{ slug: "strategy-plan-review", live: '[data-testid^="kt-str-review-"][data-kt-str-live="1"]' },
			{ slug: "strategy-plan-audit", live: '[data-testid="kt-str-audit"][data-kt-str-live="1"]' },
			{ slug: "strategy-plan-overview", live: '[data-testid="kt-str-overview"][data-kt-str-live="1"]' },
		];
		await page.goto(`/desk/strategy-plan-overview/${PLAN}`, { waitUntil: "domcontentloaded" });
		await assertVisiblePlanChrome(page, '[data-testid="kt-str-overview"][data-kt-str-live="1"]');
		for (const { slug, live } of hops) {
			await page.locator(`[data-testid="kt-str-plan-chrome"]:visible [data-kt-str-tab="${slug}"]`).click();
			await assertVisiblePlanChrome(page, live);
		}
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
		await page.goto(`/desk/strategy-value-commitments/${PLAN}`, {
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
		// Seed commitments (not fixture-only MOH-PVC-SUS-02).
		await expect(vc.locator('[data-kt-str-vc-code="MOH-PVC-EFT-01"]')).toBeVisible();
		await expect(vc.locator('[data-kt-str-vc-code="MOH-PVC-ECO-01"]')).toBeVisible();
		await expect(vc.getByRole("button", { name: /Add commitment/i })).toHaveCount(0);

		// Under shared plan chrome: tight gap after tabs; Stitch VC canvas title is headline-lg.
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
		expect(vcDensity.planPx).toBeGreaterThanOrEqual(28);
		expect(vcDensity.titlePx).toBeLessThanOrEqual(vcDensity.planPx);

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
		// Successor Draft inherits structure + existing commitments; add a new commitment directly.
		// Serial suite may already have an open successor — reuse it when Create is hidden.
		await page.goto(`/desk/strategy-plan-overview/${PLAN}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-overview"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});
		let draftId: string | null = null;
		const createBtn = page.getByTestId("kt-str-create-successor");
		if (await createBtn.isVisible()) {
			await createBtn.click();
			const modal = page.getByTestId("kt-str-successor-modal");
			await expect(modal).toBeVisible();
			await page.getByTestId("kt-str-confirm-successor").click();
			await expect(page).toHaveURL(/strategy-plan-overview\/[a-z0-9]{10,}/i, { timeout: 20_000 });
			draftId = await page.locator('[data-testid="kt-str-overview"]').getAttribute("data-kt-str-plan-id");
		} else {
			draftId = await page.evaluate(async (planCode) => {
				const r = await (window as unknown as { frappe: { call: (o: unknown) => Promise<{ message?: { name: string }[] }> } }).frappe.call({
					method: "frappe.client.get_list",
					args: {
						doctype: "Strategic Plan",
						filters: {
							plan_code: planCode,
							status: ["in", ["Draft", "Returned", "Submitted"]],
							version_number: [">", 1],
						},
						fields: ["name"],
						limit_page_length: 1,
						order_by: "version_number desc",
					},
				});
				return r.message?.[0]?.name ?? null;
			}, PLAN);
		}
		expect(draftId).toBeTruthy();

		await page.goto(`/desk/strategy-value-commitments/${draftId}`, {
			waitUntil: "domcontentloaded",
		});
		const vc = page.locator(
			'[data-testid="kt-str-value-commitments"][data-kt-str-live="1"]:visible'
		);
		await expect(vc).toBeVisible({ timeout: 20_000 });
		await expect(vc).toHaveAttribute("data-kt-str-vc-editable", "1");
		await expect(vc.locator('[data-kt-str-vc-code="MOH-PVC-EFT-01"]')).toBeVisible();

		// Add commitment sits beside the title (row), not stacked under it.
		const vcHeaderLayout = await vc.getByTestId("kt-str-vc-header").evaluate((el) => {
			const title = el.querySelector("h3, h2, h1") as HTMLElement | null;
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

		const rationaleText = `UI07 live wire rationale ${Date.now()}`;
		await drawer.locator("[data-kt-str-vc-drawer-rationale]").fill(rationaleText);
		await drawer.locator("[data-kt-str-vc-drawer-owner]").fill("Director, Digital Health");
		await drawer.locator("[data-kt-str-vc-drawer-links] input[type='checkbox']").first().check();
		await drawer.getByRole("button", { name: /Save Commitment/i }).click();
		await expect(drawer).toHaveClass(/translate-x-full/, { timeout: 15_000 });
		await expect(vc.getByText(rationaleText)).toBeVisible({
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
				slug: "strategy-value-commitments",
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
			{ label: "Review", slug: "strategy-plan-review", testid: "kt-str-review-ready" },
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
		await expect(page.getByText("MOH-PROG-0001").first()).toBeVisible({ timeout: 15_000 });
		await expect(page.getByText("MOH-OUT-0001").first()).toBeVisible();
		await expect(page.locator('[data-testid="kt-str-structure"][data-kt-str-structure-editable="0"]')).toBeVisible();
		await expect(page.getByRole("button", { name: /Add Structure Item/i })).toHaveCount(0);
		await expect(page.getByRole("button", { name: /Add Programme/i })).toHaveCount(0);
		// Never show a warning banner for zero issues (flex must not defeat .hidden).
		await expect(page.locator("[data-kt-str-structure-issues]")).toBeHidden();
		await expect(page.getByText(/0 structure issues/i)).toHaveCount(0);

		const split = await page.getByTestId("kt-str-structure-split").evaluate((el) => {
			const tree = el.querySelector("[data-testid='kt-str-structure-tree']") as HTMLElement;
			const detail = el.querySelector("[data-testid='kt-str-structure-detail']") as HTMLElement;
			const detailCard = detail.querySelector(".rounded-xl, [class*='rounded-xl']") as HTMLElement;
			const cs = getComputedStyle(el);
			const tcs = getComputedStyle(tree);
			const treeTop = tree.getBoundingClientRect().top;
			const cardTop = (detailCard || detail).getBoundingClientRect().top;
			return {
				display: cs.display,
				paddingTop: cs.paddingTop,
				gap: cs.gap,
				treeW: tree.getBoundingClientRect().width,
				detailW: detail.getBoundingClientRect().width,
				total: el.getBoundingClientRect().width,
				treeRadius: tcs.borderRadius,
				treeBorder: tcs.borderTopWidth,
				topDelta: Math.abs(treeTop - cardTop),
			};
		});
		expect(split.display).toBe("flex");
		expect(split.paddingTop).toBe("24px");
		expect(parseFloat(split.gap)).toBeGreaterThanOrEqual(12);
		expect(split.treeW).toBeGreaterThan(split.total * 0.3);
		expect(split.detailW).toBeGreaterThan(split.total * 0.45);
		expect(split.treeRadius).toMatch(/12px|0\.75rem/);
		expect(parseFloat(split.treeBorder)).toBeGreaterThanOrEqual(1);
		expect(split.topDelta).toBeLessThanOrEqual(4);

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
		await page.locator('[data-node-code="MOH-OUT-0001"]').first().click();
		await expect(page.getByTestId("kt-str-structure-detail").getByText("MOH-OUT-0001").first()).toBeVisible();
		await expect(
			page
				.getByTestId("kt-str-structure-detail")
				.getByRole("heading", { name: /Reliable and accessible digital clinical/i })
		).toBeVisible();
	});

	test("plan structure Draft empty can add Programme via drawer", async ({ page }) => {
		const suffix = Date.now().toString().slice(-6);
		await page.goto("/desk/strategy-plan-create", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-create-plan"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 20_000,
		});
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
		await expect(page).toHaveURL(/strategy-plan-overview\/[A-Z0-9]+-SP-\d{4}/, { timeout: 20_000 });
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
		await expect(panel.getByTestId("kt-str-structure-reference")).toBeVisible();
		await expect(panel.getByText("Generated automatically on save")).toBeVisible();
		await expect(panel.locator('input[name="code"]')).toHaveCount(0);
		// Focus chrome: light blue, not near-black primary (title field — code is system-assigned).
		const focusChrome = await panel.locator('input[name="title"]').evaluate((el) => {
			el.focus();
			const cs = getComputedStyle(el);
			return { border: cs.borderColor, outline: cs.outlineColor, shadow: cs.boxShadow };
		});
		expect(focusChrome.border).toMatch(/123,\s*190,\s*255|123 190 255|#7bbeff/i);
		expect(focusChrome.border).not.toMatch(/0,\s*31,\s*72|0 31 72|#001f48/i);
		await overlay.evaluate((el) => el.dispatchEvent(new MouseEvent("click", { bubbles: true })));
		await expect(overlay).toBeVisible();
		await panel.locator('input[name="title"]').fill("Digital Services Programme");
		await panel.locator('input[name="responsible_function"]').fill("ICT");
		await panel.getByRole("button", { name: /^Save$/i }).click();
		await expect(overlay).toHaveCount(0, { timeout: 15_000 });
		await expect(page.getByText(/^[A-Z0-9]+-PROG-\d{4}$/).first()).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("kt-str-structure-detail").getByText("Digital Services Programme")).toBeVisible();

		// Cancel closes without save on a second open.
		await page.getByRole("button", { name: /Add Structure Item/i }).click();
		await expect(page.getByTestId("kt-str-structure-drawer-overlay")).toBeVisible({ timeout: 10_000 });
		await page.getByTestId("kt-str-structure-drawer-panel").getByRole("button", { name: "Cancel" }).click();
		await expect(page.getByTestId("kt-str-structure-drawer-overlay")).toHaveCount(0);
	});

	test("structure target save shows inline Benefit Owner error (no Message dialog)", async ({
		page,
	}) => {
		await page.goto(`/desk/strategy-plan-structure/${REVIEW_TX_PLAN}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator('[data-testid="kt-str-structure"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await page.locator('[data-node-code="REV-IND-01"]').first().click();
		await page.getByRole("button", { name: /Add Performance Target/i }).click();
		const panel = page.getByTestId("kt-str-structure-drawer-panel");
		await expect(panel).toBeVisible({ timeout: 15_000 });
		await panel.locator('textarea[name="title"]').fill("Inline error target");
		await panel.locator('select[name="comparison_direction"]').selectOption("At least");
		await panel.locator('input[name="target_numeric"]').fill("99.9");
		await panel.locator('input[name="period_start"]').fill("2027-07-01");
		await panel.locator('input[name="period_end"]').fill("2028-06-30");
		await panel.locator('input[name="benefit_owner"]').fill("");
		await panel.locator('input[name="measurement_verifier"]').fill("Administrator");
		await panel.getByRole("button", { name: /Save target/i }).click();
		const ownerErr = panel.locator('[data-kt-str-error="benefit_owner"]');
		await expect(ownerErr).toBeVisible({ timeout: 10_000 });
		await expect(ownerErr).toContainText(/required/i);
		await expect(page.getByText(/Value missing for Performance Target/i)).toHaveCount(0);
		await expect(page.locator(".msgprint, .modal-dialog").filter({ hasText: /^Message$/ })).toHaveCount(0);
		await expect(panel).toBeVisible();
	});

	test("review live binds ready canvas for Active plan", async ({ page }) => {
		await page.goto(`/desk/strategy-plan-review/${PLAN}`, { waitUntil: "domcontentloaded" });
		const ready = page.locator('[data-testid="kt-str-review-ready"][data-kt-str-live="1"]');
		await expect(ready).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-str-review-ready-card")).toBeVisible();
		await expect(ready.locator("[data-kt-str-plan-code]").first()).toContainText(PLAN, {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-str-review-state-toggle")).toBeHidden();
		await expect(ready.locator("[data-kt-str-plan-status]").first()).toContainText(/Active/i);
		await expect(ready.locator('[data-kt-str-action="submit-for-review"]')).toBeHidden();
	});

	test("review live binds blockers canvas with Resolve navigation", async ({ page }) => {
		await page.goto(`/desk/strategy-plan-review/${REVIEW_BLOCKERS_PLAN}`, {
			waitUntil: "domcontentloaded",
		});
		const blockers = page.locator('[data-testid="kt-str-review-blockers"][data-kt-str-live="1"]');
		await expect(blockers).toBeVisible({ timeout: 30_000 });
		await expect(blockers.locator("[data-kt-str-blocker-count-label]")).toContainText(/Blocker/i);
		await expect(blockers.locator('[data-kt-str-review-group="Structure"]')).toBeVisible();
		await expect(blockers.locator("[data-kt-str-resolve]").first()).toBeVisible();
		await expect(blockers.locator('[data-kt-str-action="submit-for-review"]')).toBeDisabled();
		await blockers.locator('[data-kt-str-action="run-readiness"]').click();
		await expect(blockers).toHaveAttribute("data-kt-str-live", "1", { timeout: 15_000 });
		await blockers.locator("[data-kt-str-resolve]").first().click();
		await expect(page).toHaveURL(/strategy-plan-structure|strategy-plan-overview/, {
			timeout: 15_000,
		});
	});

	test("review submit hides Submit and shows governance CTAs", async ({ page }) => {
		// Seed resets REVIEW_TX to a ready Draft before each evidence run (see Makefile/bench execute).
		await page.goto(`/desk/strategy-plan-review/${REVIEW_TX_PLAN}`, {
			waitUntil: "domcontentloaded",
		});
		const ready = page.locator('[data-testid="kt-str-review-ready"][data-kt-str-live="1"]');
		await expect(ready).toBeVisible({ timeout: 30_000 });
		await expect(ready.locator("[data-kt-str-plan-status]").first()).toContainText(/Draft/i);
		const submit = ready.locator('[data-kt-str-action="submit-for-review"]');
		await expect(submit).toBeVisible({ timeout: 15_000 });
		await expect(submit).toBeEnabled();
		await submit.click();
		await expect(ready.locator("[data-kt-str-review-ready-title]")).toContainText(/Awaiting review/i, {
			timeout: 20_000,
		});
		await expect(ready.locator("[data-kt-str-plan-status]").first()).toContainText(/Submitted/i);
		await expect(submit).toBeHidden();
		await expect(ready.locator('[data-kt-str-action="return-for-correction"]')).toBeVisible();
		await expect(ready.locator('[data-kt-str-action="approve-plan"]')).toBeVisible();
		await expect(page).toHaveURL(new RegExp(`strategy-plan-review/${REVIEW_TX_PLAN}`));
	});

	test("satellite surfaces open", async ({ page }) => {
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
	});

	test("measurements register is live for Active plan", async ({ page }) => {
		await page.goto(`/desk/strategy-plan-measurements/${PLAN}`, {
			waitUntil: "domcontentloaded",
		});
		const meas = page.locator('[data-testid="kt-str-measurements"][data-kt-str-live="1"]:visible');
		await expect(meas).toBeVisible({ timeout: 30_000 });
		await expect(meas.getByTestId("kt-str-measurements-table")).toBeVisible();
		await expect(meas.getByRole("heading", { name: "Performance measurements" })).toBeVisible();
		const measFilters = meas.locator("[data-kt-str-meas-filters]");
		await expect(
			measFilters.locator(".material-symbols-outlined", { hasText: "expand_more" })
		).toHaveCount(3);
		// Seed truth: two Verified MOH-TGT-AVAIL-2028 rows — not fixture-only TGT-02/03.
		await expect(
			meas.locator('[data-kt-str-meas-tbody] tr[data-kt-str-target-code="MOH-TGT-AVAIL-2028"]')
		).toHaveCount(2, { timeout: 15_000 });
		await expect(meas.getByText("MOH-TGT-02")).toHaveCount(0);
		await expect(meas.getByText("MOH-TGT-03")).toHaveCount(0);
		await expect(meas.locator('[data-kt-str-meas-count="verified"]')).toHaveText(/^[2-9]\d*$/);
		await expect(meas.locator('[data-kt-str-meas-count="due"]')).toHaveText("0");
		await expect(page.getByText(/UI fixture — no backend yet/i)).toHaveCount(0);

		await meas.getByRole("button", { name: /Submit measurement/i }).first().click();
		await expect(page).toHaveURL(
			new RegExp(`strategy-measurement-submit/${PLAN}/MOH-TGT-AVAIL-2028`),
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-str-measurement-submit")).toBeVisible({ timeout: 30_000 });
	});

	test("submit measurement uses date fields and live derived result", async ({ page }) => {
		await page.goto(`/desk/strategy-measurement-submit/${PLAN}/${TARGET}`, {
			waitUntil: "domcontentloaded",
		});
		const root = page.locator('[data-testid="kt-str-measurement-submit"][data-kt-str-live="1"]');
		await expect(root).toBeVisible({ timeout: 30_000 });
		await expect(root.locator('[data-kt-str-meas-period-start]')).toHaveAttribute("type", "date");
		await expect(root.locator('[data-kt-str-meas-period-end]')).toHaveAttribute("type", "date");
		await expect(root.locator('[data-kt-str-meas-date]')).toHaveAttribute("type", "date");

		const actual = root.locator("[data-kt-str-actual]");
		await actual.fill("99.82");
		await expect(root.locator("[data-kt-str-result]")).toHaveText(/AT RISK/i, { timeout: 5_000 });
		await expect(root.locator("[data-kt-str-meas-derived]")).toHaveAttribute(
			"data-kt-str-meas-tone",
			"at-risk"
		);

		await actual.fill("99.96");
		await expect(root.locator("[data-kt-str-result]")).toHaveText(/ON TRACK/i, { timeout: 5_000 });
		await expect(root.locator("[data-kt-str-meas-derived]")).toHaveAttribute(
			"data-kt-str-meas-tone",
			"on-track"
		);
	});

	test("verify measurement hydrates and stays on page after Verify", async ({ page }) => {
		const stamp = Date.now().toString().slice(-6);
		const day = String((Number(stamp) % 27) + 1).padStart(2, "0");
		const periodStart = `2027-03-${day}`;
		const periodEnd = `2027-03-${day}`;

		await page.goto(`/desk/strategy-measurement-submit/${PLAN}/${TARGET}`, {
			waitUntil: "domcontentloaded",
		});
		const submitRoot = page.locator(
			'[data-testid="kt-str-measurement-submit"][data-kt-str-live="1"]'
		);
		await expect(submitRoot).toBeVisible({ timeout: 30_000 });
		await submitRoot.locator("[data-kt-str-meas-period-start]").fill(periodStart);
		await submitRoot.locator("[data-kt-str-meas-period-end]").fill(periodEnd);
		await submitRoot.locator("[data-kt-str-meas-date]").fill(periodEnd);
		await submitRoot.locator("[data-kt-str-actual]").fill("99.85");
		await submitRoot.locator("[data-kt-str-meas-evidence-source]").fill("PW verify evidence");
		await submitRoot.getByRole("button", { name: /Submit measurement/i }).click();
		await expect(submitRoot).toHaveAttribute("data-kt-str-workflow-status", "Submitted", {
			timeout: 20_000,
		});

		const verifyUrl = `/desk/strategy-measurement-verify/${PLAN}/${TARGET}`;
		await page.goto(verifyUrl, { waitUntil: "domcontentloaded" });
		const root = page.locator('[data-testid="kt-str-measurement-verify"][data-kt-str-live="1"]');
		await expect(root).toBeVisible({ timeout: 30_000 });
		await expect(root.getByTestId("kt-str-meas-verify-compare")).toBeVisible();
		await expect(root.getByTestId("kt-str-meas-verify-decision")).toBeVisible();
		await expect(root.locator("[data-kt-str-target-code]")).toContainText(TARGET);
		await expect(root.locator("[data-kt-str-meas-workflow-label]")).toHaveText(/SUBMITTED/i);
		await expect(root.getByRole("button", { name: /Back to measurements/i })).toBeVisible();
		await expect(page.getByText(/Back to Contract/i)).toHaveCount(0);

		// Status pill icons share a vertical mid-line with their labels.
		const pillAlign = await root.locator("[data-kt-str-meas-workflow-pill]").evaluate((el) => {
			const icon = el.querySelector(".material-symbols-outlined") as HTMLElement | null;
			const label = el.querySelector("[data-kt-str-meas-workflow-label]") as HTMLElement | null;
			if (!icon || !label) {
				return { ok: false, delta: 99 };
			}
			const ir = icon.getBoundingClientRect();
			const lr = label.getBoundingClientRect();
			return { ok: true, delta: Math.abs(ir.top + ir.height / 2 - (lr.top + lr.height / 2)) };
		});
		expect(pillAlign.ok).toBe(true);
		expect(pillAlign.delta).toBeLessThanOrEqual(2);

		const before = page.url();
		await root.getByRole("button", { name: /Verify Measurement/i }).click();
		await expect(root).toHaveAttribute("data-kt-str-workflow-status", "Verified", {
			timeout: 20_000,
		});
		await expect(root.locator("[data-kt-str-meas-workflow-label]")).toHaveText(/VERIFIED/i);
		await expect(root.locator("[data-kt-str-meas-workflow-icon]")).toHaveText("verified");
		expect(page.url().split("?")[0]).toBe(before.split("?")[0]);
		await expect(page).toHaveURL(new RegExp(`strategy-measurement-verify/${PLAN}/${TARGET}`));
	});

	test("verify measurement requires comments for Return", async ({ page }) => {
		const stamp = `r${Date.now().toString().slice(-5)}`;
		const day = String((Number(Date.now()) % 27) + 1).padStart(2, "0");
		const periodStart = `2027-04-${day}`;
		const periodEnd = `2027-04-${day}`;

		await page.goto(`/desk/strategy-measurement-submit/${PLAN}/${TARGET}`, {
			waitUntil: "domcontentloaded",
		});
		const submitRoot = page.locator(
			'[data-testid="kt-str-measurement-submit"][data-kt-str-live="1"]'
		);
		await expect(submitRoot).toBeVisible({ timeout: 30_000 });
		await submitRoot.locator("[data-kt-str-meas-period-start]").fill(periodStart);
		await submitRoot.locator("[data-kt-str-meas-period-end]").fill(periodEnd);
		await submitRoot.locator("[data-kt-str-meas-date]").fill(periodEnd);
		await submitRoot.locator("[data-kt-str-actual]").fill("99.9");
		await submitRoot
			.locator("[data-kt-str-meas-evidence-source]")
			.fill(`PW return ${stamp}`);
		await submitRoot.getByRole("button", { name: /Submit measurement/i }).click();
		await expect(submitRoot).toHaveAttribute("data-kt-str-workflow-status", "Submitted", {
			timeout: 20_000,
		});

		await page.goto(`/desk/strategy-measurement-verify/${PLAN}/${TARGET}`, {
			waitUntil: "domcontentloaded",
		});
		const root = page.locator('[data-testid="kt-str-measurement-verify"][data-kt-str-live="1"]');
		await expect(root).toBeVisible({ timeout: 30_000 });
		await root.locator("[data-kt-str-meas-verify-comments]").fill("");
		const before = page.url();
		await root.getByRole("button", { name: /Return for correction/i }).click();
		await expect(root).toHaveAttribute("data-kt-str-workflow-status", "Submitted", {
			timeout: 5_000,
		});
		expect(page.url().split("?")[0]).toBe(before.split("?")[0]);
		await expect(root.getByRole("button", { name: /Verify Measurement/i })).toBeEnabled();
	});

	test("submit measurement stays on the same page like save draft", async ({ page }) => {
		const submitUrl = `/desk/strategy-measurement-submit/${PLAN}/${TARGET}`;
		await page.goto(submitUrl, { waitUntil: "domcontentloaded" });
		const root = page.locator('[data-testid="kt-str-measurement-submit"][data-kt-str-live="1"]');
		await expect(root).toBeVisible({ timeout: 30_000 });

		// Unique period inside target window so seed Verified rows do not collide.
		const stamp = Date.now().toString().slice(-6);
		const day = String((Number(stamp) % 27) + 1).padStart(2, "0");
		await root.locator("[data-kt-str-meas-period-start]").fill(`2026-11-${day}`);
		await root.locator("[data-kt-str-meas-period-end]").fill(`2026-11-${day}`);
		await root.locator("[data-kt-str-meas-date]").fill(`2026-11-${day}`);
		await root.locator("[data-kt-str-actual]").fill("99.95");
		await root.locator("[data-kt-str-meas-evidence-source]").fill("UI stay-on-page evidence");

		const before = page.url();
		await root.getByRole("button", { name: /Submit measurement/i }).click();
		await expect(root).toHaveAttribute("data-kt-str-workflow-status", "Submitted", {
			timeout: 20_000,
		});
		await expect(page).toHaveURL(new RegExp(`strategy-measurement-submit/${PLAN}/${TARGET}`));
		expect(page.url()).toContain("strategy-measurement-submit");
		await expect(root).toBeVisible();
		// Same surface — did not bounce to register / overview.
		expect(page.url().split("?")[0]).toBe(before.split("?")[0]);
	});

	test("downstream usage is live with derived Budget, Demand, and Planning rows", async ({
		page,
	}) => {
		test.setTimeout(240_000);
		seedStrategyDownstreamFixtures();
		await page.goto(`/desk/strategy-plan-downstream-usage/${PLAN}`, {
			waitUntil: "domcontentloaded",
		});
		const down = page.locator('[data-testid="kt-str-downstream"][data-kt-str-live="1"]');
		await expect(down).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-str-downstream-table")).toBeVisible();
		await expect(down.locator('[data-kt-str-down-count="Demand"]')).not.toHaveText("0", {
			timeout: 15_000,
		});
		await expect(down.locator('[data-kt-str-down-count="Budget"]')).not.toHaveText("0");
		await expect(down.locator('[data-kt-str-down-count="Planning"]')).not.toHaveText("0", {
			timeout: 15_000,
		});
		await expect(down.locator("[data-kt-str-down-tbody] [data-kt-str-down-row]")).not.toHaveCount(0);
		await expect(down.getByText("PKG-MOH-2026-001")).toBeVisible();
		await expect(down.getByText("DEM-MOH-2027-014")).toHaveCount(0);
		await expect(down.locator("[data-kt-str-plan-code]")).toContainText(PLAN);

		const filters = down.locator("[data-kt-str-down-filters]");
		await expect(
			filters.locator(".material-symbols-outlined", { hasText: "expand_more" })
		).toHaveCount(4);

		const beforeCount = await down.locator("[data-kt-str-down-tbody] [data-kt-str-down-row]").count();
		const demandCount = Number(
			await down.locator('[data-kt-str-down-count="Demand"]').innerText()
		);
		await down.locator("[data-kt-str-down-filter-module]").selectOption("Demand");
		await expect(down.locator("[data-kt-str-down-tbody] [data-kt-str-down-row]")).toHaveCount(
			demandCount,
			{ timeout: 5_000 }
		);
		await down.getByRole("button", { name: /Clear filters/i }).click();
		await expect(down.locator("[data-kt-str-down-tbody] [data-kt-str-down-row]")).toHaveCount(
			beforeCount
		);
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

	test("audit table exposes a visible horizontal scrollbar when overflowing", async ({ page }) => {
		await page.setViewportSize({ width: 1100, height: 900 });
		await page.goto(`/desk/strategy-plan-audit/${PLAN}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-audit"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		const scroll = page.getByTestId("kt-str-audit-scroll");
		await expect(scroll).toBeVisible();
		const metrics = await scroll.evaluate((el) => {
			const cs = getComputedStyle(el);
			return {
				overflowX: cs.overflowX,
				scrollbarWidth: cs.scrollbarWidth,
				scrollWidth: el.scrollWidth,
				clientWidth: el.clientWidth,
				hasHideClass: el.classList.contains("scrollbar-hide"),
			};
		});
		expect(metrics.hasHideClass).toBe(false);
		expect(metrics.overflowX).toMatch(/auto|scroll/);
		expect(metrics.scrollbarWidth).not.toBe("none");
		// Wide columns may still fit on some viewports; only assert scroll when overflowing.
		if (metrics.scrollWidth > metrics.clientWidth) {
			await scroll.evaluate((el) => {
				el.scrollLeft = el.scrollWidth;
			});
			await expect
				.poll(async () => scroll.evaluate((el) => el.scrollLeft))
				.toBeGreaterThan(0);
		}
	});

	test("shared table footer paginates Audit and appears on Portfolio", async ({ page }) => {
		await page.goto(`/desk/strategy-plan-audit/${PLAN}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-audit"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		const auditFooter = page
			.locator('[data-testid="kt-str-audit"] [data-testid="kt-str-table-footer"]')
			.first();
		await expect(auditFooter).toBeVisible();
		await expect(auditFooter.locator("[data-kt-str-footer-range]")).toHaveText(
			/Showing (\d+(-\d+)? of \d+|0 of 0)/
		);
		await expect(auditFooter.getByText("Rows per page")).toBeVisible();
		await expect(auditFooter.locator(".kt-str-footer-page-size-glyph")).toBeVisible();
		await expect(auditFooter.locator("[data-kt-str-footer-page-size]")).toHaveValue("20");
		const sizeOpts = await auditFooter
			.locator("[data-kt-str-footer-page-size] option")
			.evaluateAll((els) => els.map((el) => (el as HTMLOptionElement).value));
		expect(sizeOpts).toEqual(["10", "20", "50", "100"]);

		const page1 = auditFooter.locator('[data-kt-str-footer-page-num="1"]');
		await expect(page1).toBeVisible();
		await expect(page1).toHaveClass(/is-active/);

		const countAttr = await page
			.locator('[data-testid="kt-str-audit"]')
			.getAttribute("data-kt-str-audit-count");
		const total = Number(countAttr || "0");
		if (total > 20) {
			const next = auditFooter.locator("[data-kt-str-footer-next]");
			await expect(next).toBeEnabled();
			await next.click();
			await expect(auditFooter.locator('[data-kt-str-footer-page-num="2"]')).toHaveClass(
				/is-active/
			);
			await expect(auditFooter.locator("[data-kt-str-footer-range]")).toHaveText(
				/Showing 21-\d+ of \d+/
			);
			await auditFooter.locator('[data-kt-str-footer-page-num="1"]').click();
			await expect(page1).toHaveClass(/is-active/);
		}

		// Force multi-page chrome when possible: page size 10.
		if (total > 10) {
			await auditFooter.locator("[data-kt-str-footer-page-size]").selectOption("10");
			await expect(auditFooter.locator('[data-kt-str-footer-page-num="1"]')).toHaveClass(
				/is-active/
			);
			await expect(auditFooter.locator("[data-kt-str-footer-next]")).toBeEnabled();
			const pageNums = await auditFooter
				.locator("[data-kt-str-footer-page-num]")
				.evaluateAll((els) => els.map((el) => el.getAttribute("data-kt-str-footer-page-num")));
			expect(pageNums.length).toBeGreaterThanOrEqual(2);
			expect(pageNums[0]).toBe("1");
		}

		await page.goto("/desk/strategy-alignment", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-str-portfolio"][data-kt-str-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		const pfFooter = page
			.locator('[data-testid="kt-str-portfolio"] [data-testid="kt-str-table-footer"]')
			.first();
		await expect(pfFooter).toBeVisible();
		await expect(pfFooter.locator("[data-kt-str-footer-range]")).toHaveText(
			/Showing (\d+(-\d+)? of \d+|0 of 0)/
		);
		await expect(pfFooter.getByText("Rows per page")).toBeVisible();
		await expect(pfFooter.locator("[data-kt-str-footer-page-size]")).toHaveValue("20");
		await expect(pfFooter.locator('[data-kt-str-footer-page-num="1"]')).toHaveClass(/is-active/);
	});
});
