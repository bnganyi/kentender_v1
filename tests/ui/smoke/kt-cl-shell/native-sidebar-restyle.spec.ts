import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * Step 1 — Restore + restyle the NATIVE Frappe Workspace Sidebar (`.body-sidebar`).
 *
 * The custom `#kt-cl-sidenav` replacement is retired as navigation; the native
 * rail is the source of truth (routing/collapse/persistence) and only the visual
 * language is overridden by `kt_native_sidebar_civic.css` (Civic Ledger tokens).
 */

const NATIVE_RAIL = ".body-sidebar";

test.describe("Civic Ledger — native Workspace Sidebar restyle", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1280, height: 800 });
		await loginAsAdministrator(page);
	});

	test("renders the native rail (not the custom #kt-cl-sidenav) with the Civic Ledger IA", async ({ page }) => {
		await page.goto("/desk/coming-soon?feature=Home");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });

		await expect(page.locator("#kt-cl-sidenav")).toHaveCount(0);

		const railText = await page.locator(NATIVE_RAIL).innerText();
		for (const label of [
			"Home",
			"Analytics",
			"Strategy Alignment",
			"Budget & Funding",
			"Demands",
			"Procurement Plans",
			"Tender Management",
			"Contract Management",
			"Supplier Management",
			"STD Administration",
		]) {
			expect(railText).toContain(label);
		}
		expect(railText).not.toContain("Procurement Journeys");
		expect(railText).not.toContain("Tender Management Hub");
		// Exact section — do not use substring (collides with "Tender Configurations").
		await expect(page.locator(`${NATIVE_RAIL} .section-item[data-id="Configuration"]`)).toHaveCount(0);
		expect(railText).toContain("Planned");
	});

	test("shows Procurement / KenTender header with colored icon", async ({ page }) => {
		await page.goto("/desk/coming-soon?feature=Home");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });

		const header = page.locator(`${NATIVE_RAIL} .sidebar-header`);
		await expect(header.locator(".header-title")).toHaveText(/^\s*Procurement\s*$/i);
		await expect(header.locator(".header-subtitle")).toContainText("KenTender");

		// ERPNext pattern: rounded tile is drawn in the solid SVG; outer shell must not
		// paint a sharp CSS plate (that leaked blue at the four corners).
		const icon = await header.locator(".sidebar-item-icon").evaluate((el) => {
			const img = el.querySelector("img") as HTMLImageElement | null;
			const cs = getComputedStyle(el);
			const canvas = document.createElement("canvas");
			canvas.width = 32;
			canvas.height = 32;
			const ctx = canvas.getContext("2d");
			let cornerRgb: number[] | null = null;
			if (ctx && img) {
				ctx.drawImage(img, 0, 0, 32, 32);
				const px = ctx.getImageData(0, 0, 1, 1).data;
				cornerRgb = [px[0], px[1], px[2], px[3]];
			}
			return {
				bg: cs.backgroundColor,
				hasSolidImg: !!(img && /desktop_icons\/solid\/procurement\.svg/.test(img.src)),
				cornerRgb,
			};
		});
		expect(icon.bg === "rgba(0, 0, 0, 0)" || icon.bg === "transparent").toBe(true);
		expect(icon.hasSolidImg).toBe(true);
		// SVG corner pixel must be transparent (alpha 0), not an opaque blue plate.
		expect(icon.cornerRgb).not.toBeNull();
		expect(icon.cornerRgb![3]).toBe(0);
	});

	test("applies the Civic Ledger tokens (256px rail, navy active right-border + tint, Material icons)", async ({ page }) => {
		await page.goto("/desk/coming-soon?feature=Home");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });

		const styles = await page.evaluate(() => {
			const rail = document.querySelector(".body-sidebar") as HTMLElement;
			const home = document.querySelector(
				'.body-sidebar .sidebar-item-container[data-id="Home"] .standard-sidebar-item'
			) as HTMLElement | null;
			home?.click();
			const active = document.querySelector(
				".body-sidebar .standard-sidebar-item.active-sidebar"
			) as HTMLElement | null;
			const cs = active ? getComputedStyle(active) : null;
			const icon = document.querySelector(
				'.body-sidebar .sidebar-item-container[data-id="Home"] .sidebar-item-icon'
			);
			const iconBefore = icon ? getComputedStyle(icon, "::before") : null;
			return {
				railWidth: rail && getComputedStyle(rail).width,
				railBg: rail && getComputedStyle(rail).backgroundColor,
				activeBorderRight: cs && `${cs.borderRightWidth} ${cs.borderRightStyle} ${cs.borderRightColor}`,
				activeBg: cs && cs.backgroundColor,
				iconContent: iconBefore && iconBefore.content,
				iconFont: iconBefore && iconBefore.fontFamily,
			};
		});

		expect(styles.railWidth).toBe("256px");
		expect(styles.railBg).toBe("rgb(242, 244, 246)");
		expect(styles.activeBorderRight).toBe("4px solid rgb(0, 11, 29)");
		expect(styles.activeBg).toBe("rgba(173, 200, 243, 0.2)");
		expect(styles.iconContent).toContain("home");
		expect(styles.iconFont).toContain("Material Symbols Outlined");
	});

	test("top-level icon columns align and section expanders stay chrome-free", async ({ page }) => {
		await page.goto("/desk/coming-soon?feature=Home");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });

		const layout = await page.evaluate(() => {
			function labelLeft(id: string) {
				const el = document.querySelector(
					`.body-sidebar [data-id="${id}"] > .standard-sidebar-item .sidebar-item-label`
				) as HTMLElement | null;
				return el ? Math.round(el.getBoundingClientRect().left) : null;
			}
			function dropChrome(id: string) {
				const drop = document.querySelector(
					`.body-sidebar [data-id="${id}"] > .standard-sidebar-item .drop-icon`
				) as HTMLElement | null;
				if (!drop) return null;
				const cs = getComputedStyle(drop);
				return {
					width: cs.width,
					border: cs.border,
					outlineStyle: cs.outlineStyle,
					boxShadow: cs.boxShadow,
					bg: cs.backgroundColor,
				};
			}
			const stdBefore = getComputedStyle(
				document.querySelector(
					'.body-sidebar [data-id="STD Administration"] > .standard-sidebar-item .item-anchor'
				) as Element,
				"::before"
			);
			return {
				homeLabel: labelLeft("Home"),
				plansLabel: labelLeft("Procurement Plans"),
				tmLabel: labelLeft("Tender Management"),
				cmLabel: labelLeft("Contract Management"),
				stdLabel: labelLeft("STD Administration"),
				stdGlyph: stdBefore.content,
				tmDrop: dropChrome("Tender Management"),
				stdDrop: dropChrome("STD Administration"),
			};
		});

		expect(layout.homeLabel).not.toBeNull();
		expect(layout.tmLabel).toBe(layout.homeLabel);
		expect(layout.stdLabel).toBe(layout.homeLabel);
		expect(layout.cmLabel).toBe(layout.homeLabel);
		expect(layout.plansLabel).toBe(layout.homeLabel);
		expect(layout.stdGlyph).toContain("menu_book");
		for (const drop of [layout.tmDrop, layout.stdDrop]) {
			expect(drop).not.toBeNull();
			expect(drop!.width).toBe("20px");
			expect(drop!.border).toMatch(/none|0px/);
			expect(drop!.outlineStyle).toBe("none");
			expect(drop!.boxShadow).toBe("none");
		}
	});

	test("Tender Management is a two-level group that collapses and expands natively", async ({ page }) => {
		await page.goto("/desk/coming-soon?feature=Home");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });

		const result = await page.evaluate(() => {
			const sec = document.querySelector('.body-sidebar .section-item[data-id="Tender Management"]');
			const nested = sec?.querySelector(".nested-container") as HTMLElement;
			const header = sec?.querySelector(".standard-sidebar-item") as HTMLElement;
			const childrenCount = nested.querySelectorAll(":scope > .sidebar-item-container").length;
			const childLabels = Array.from(nested.querySelectorAll(":scope > .sidebar-item-container")).map(
				(el) => (el as HTMLElement).dataset.id || ""
			);
			const hiddenInitially = nested.classList.contains("hidden");
			header.click();
			const hiddenAfterClick = nested.classList.contains("hidden");
			header.click();
			const hiddenAfterReopen = nested.classList.contains("hidden");
			const cs = getComputedStyle(nested);
			return {
				childrenCount,
				childLabels,
				hiddenInitially,
				hiddenAfterClick,
				hiddenAfterReopen,
				connector: `${cs.borderLeftWidth} ${cs.borderLeftStyle}`,
			};
		});

		expect(result.childrenCount).toBe(5);
		expect(result.childLabels).toEqual([
			"Tender Configurations",
			"Tenders",
			"Bid Submissions",
			"Evaluation",
			"Awards",
		]);
		expect(result.hiddenInitially).toBe(false);
		expect(result.hiddenAfterClick).toBe(true);
		expect(result.hiddenAfterReopen).toBe(false);
		expect(result.connector).toBe("1px solid");
	});

	test("Planned Home opens the named capability overview", async ({ page }) => {
		await page.goto("/desk/coming-soon?feature=Home");
		await expect(page.getByTestId("kt-coming-soon")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-coming-soon-title")).toHaveText("Home");
	});

	test("Planned items select only their own feature (not STD Versions)", async ({ page }) => {
		await page.goto("/desk/coming-soon?feature=Home");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });

		const home = page.locator(
			`${NATIVE_RAIL} .sidebar-item-container[data-id="Home"] > .standard-sidebar-item`
		);
		const stdVersions = page.locator(
			`${NATIVE_RAIL} .sidebar-item-container[data-id="STD Versions"] > .standard-sidebar-item`
		);
		await expect(home).toHaveClass(/active-sidebar/);
		await expect(stdVersions).not.toHaveClass(/active-sidebar/);

		await page.goto("/desk/coming-soon?feature=Analytics");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });
		await expect(
			page.locator(`${NATIVE_RAIL} .sidebar-item-container[data-id="Analytics"] > .standard-sidebar-item`)
		).toHaveClass(/active-sidebar/);
		await expect(stdVersions).not.toHaveClass(/active-sidebar/);
	});

	test("hub routes mark Demands / Plans / Budget active consistently", async ({ page }) => {
		test.setTimeout(120_000);
		await page.goto("/desk/demand-hub", { waitUntil: "domcontentloaded" });
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });
		// Hub pages restore Procurement via deferred sidebar.setup — wait for the spine.
		await expect(
			page.locator(`${NATIVE_RAIL} .sidebar-item-container[data-id="Demands"]`)
		).toBeVisible({ timeout: 15_000 });
		await expect(page.locator(`${NATIVE_RAIL} .sidebar-header .header-title`)).toHaveText(
			/^\s*Procurement\s*$/i
		);
		await expect(
			page.locator(`${NATIVE_RAIL} .sidebar-item-container[data-id="Demands"] > .standard-sidebar-item`)
		).toHaveClass(/active-sidebar/, { timeout: 15_000 });

		await page.goto("/desk/planning-hub");
		await expect(
			page.locator(`${NATIVE_RAIL} .sidebar-item-container[data-id="Procurement Plans"]`)
		).toBeVisible({ timeout: 15_000 });
		await expect(
			page.locator(
				`${NATIVE_RAIL} .sidebar-item-container[data-id="Procurement Plans"] > .standard-sidebar-item`
			)
		).toHaveClass(/active-sidebar/, { timeout: 15_000 });

		await page.goto("/desk/budget-hub");
		await expect(
			page.locator(`${NATIVE_RAIL} .sidebar-item-container[data-id="Budget & Funding"]`)
		).toBeVisible({ timeout: 15_000 });
		await expect(
			page.locator(
				`${NATIVE_RAIL} .sidebar-item-container[data-id="Budget & Funding"] > .standard-sidebar-item`
			)
		).toHaveClass(/active-sidebar/, { timeout: 15_000 });

		await page.goto("/desk/strategy-management");
		await expect(
			page.locator(
				`${NATIVE_RAIL} .sidebar-item-container[data-id="Strategy Alignment"] > .standard-sidebar-item`
			)
		).toHaveClass(/active-sidebar/, { timeout: 15_000 });
	});

	test("section parents are bold only when a child is active", async ({ page }) => {
		await page.goto("/desk/coming-soon?feature=Home");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });

		const weightsQuiet = await page.evaluate(() => {
			const tm = document.querySelector(
				'.body-sidebar [data-id="Tender Management"] > .standard-sidebar-item .sidebar-item-label'
			) as HTMLElement;
			const std = document.querySelector(
				'.body-sidebar [data-id="STD Administration"] > .standard-sidebar-item .sidebar-item-label'
			) as HTMLElement;
			return {
				tm: tm ? getComputedStyle(tm).fontWeight : null,
				std: std ? getComputedStyle(std).fontWeight : null,
			};
		});
		expect(["400", "500"].includes(weightsQuiet.tm || "")).toBe(true);
		expect(["400", "500"].includes(weightsQuiet.std || "")).toBe(true);

		await page.goto("/desk/it-tender-configuration-dashboard");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });
		await expect(
			page.locator(
				`${NATIVE_RAIL} .sidebar-item-container[data-id="Tender Configurations"] > .standard-sidebar-item`
			)
		).toHaveClass(/active-sidebar/);

		const weightsActive = await page.evaluate(() => {
			const tm = document.querySelector(
				'.body-sidebar [data-id="Tender Management"] > .standard-sidebar-item .sidebar-item-label'
			) as HTMLElement;
			const std = document.querySelector(
				'.body-sidebar [data-id="STD Administration"] > .standard-sidebar-item .sidebar-item-label'
			) as HTMLElement;
			return {
				tm: tm ? getComputedStyle(tm).fontWeight : null,
				std: std ? getComputedStyle(std).fontWeight : null,
			};
		});
		expect(["600", "700", "bold"].includes(weightsActive.tm || "")).toBe(true);
		expect(["400", "500"].includes(weightsActive.std || "")).toBe(true);
	});

	test("the native rail persists across navigation", async ({ page }) => {
		await page.goto("/desk/coming-soon?feature=Home");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });

		await page.goto("/desk/planning-hub");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator("#kt-cl-sidenav")).toHaveCount(0);

		const state = await page.evaluate(() => {
			const rail = document.querySelector(".body-sidebar") as HTMLElement;
			return {
				railWidth: rail && getComputedStyle(rail).width,
				topCount: document.querySelectorAll(".body-sidebar .sidebar-items > .sidebar-item-container")
					.length,
				hasPlans: !!document.querySelector(
					'.body-sidebar .sidebar-item-container[data-id="Procurement Plans"]'
				),
			};
		});

		expect(state.railWidth).toBe("256px");
		expect(state.topCount).toBe(10);
		expect(state.hasPlans).toBe(true);
	});
});
