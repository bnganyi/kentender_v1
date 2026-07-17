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
		await page.goto("/desk/procurement-home");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });

		// The custom replacement rail must be gone entirely.
		await expect(page.locator("#kt-cl-sidenav")).toHaveCount(0);

		// Specified top-level entries + the two spec groups are present.
		const railText = await page.locator(NATIVE_RAIL).innerText();
		for (const label of [
			"Procurement Home",
			"Analytics",
			"Strategy Alignment",
			"Budget & Funding",
			"Demand Intake & Approval",
			"Tender Management",
			"Contract Management",
			"Supplier Management",
			"STD Administration",
		]) {
			expect(railText).toContain(label);
		}
	});

	test("applies the Civic Ledger tokens (256px rail, navy active right-border + tint, Material icons)", async ({ page }) => {
		await page.goto("/desk/procurement-home");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });

		const styles = await page.evaluate(() => {
			const rail = document.querySelector(".body-sidebar") as HTMLElement;
			const active = document.querySelector(
				".body-sidebar .standard-sidebar-item.active-sidebar"
			) as HTMLElement | null;
			const cs = active ? getComputedStyle(active) : null;
			const icon = document.querySelector(
				'.body-sidebar .sidebar-item-container[data-id="Procurement Home"] .sidebar-item-icon'
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
		expect(styles.railBg).toBe("rgb(242, 244, 246)"); // surface-container-low
		expect(styles.activeBorderRight).toBe("4px solid rgb(0, 11, 29)"); // primary right-border
		expect(styles.activeBg).toBe("rgba(173, 200, 243, 0.2)"); // primary-fixed-dim / 20
		expect(styles.iconContent).toContain("home"); // Material Symbol ligature swap
		expect(styles.iconFont).toContain("Material Symbols Outlined");
	});

	test("Tender Management is a two-level group that collapses and expands natively", async ({ page }) => {
		await page.goto("/desk/procurement-home");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });

		const result = await page.evaluate(() => {
			const sec = document.querySelector('.body-sidebar .section-item[data-id="Tender Management"]');
			const nested = sec?.querySelector(".nested-container") as HTMLElement;
			const header = sec?.querySelector(".standard-sidebar-item") as HTMLElement;
			const childrenCount = nested.querySelectorAll(":scope > .sidebar-item-container").length;
			const hiddenInitially = nested.classList.contains("hidden");
			header.click();
			const hiddenAfterClick = nested.classList.contains("hidden");
			header.click();
			const hiddenAfterReopen = nested.classList.contains("hidden");
			const cs = getComputedStyle(nested);
			return {
				childrenCount,
				hiddenInitially,
				hiddenAfterClick,
				hiddenAfterReopen,
				connector: `${cs.borderLeftWidth} ${cs.borderLeftStyle}`,
			};
		});

		expect(result.childrenCount).toBe(7);
		expect(result.hiddenInitially).toBe(false);
		expect(result.hiddenAfterClick).toBe(true);
		expect(result.hiddenAfterReopen).toBe(false);
		expect(result.connector).toBe("1px solid"); // outline-variant connector rail
	});

	test("the native rail persists across navigation and tracks the active workspace", async ({ page }) => {
		await page.goto("/desk/procurement-home");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });

		await page.goto("/desk/contract-management");
		await expect(page.locator(NATIVE_RAIL)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator("#kt-cl-sidenav")).toHaveCount(0);

		const state = await page.evaluate(() => {
			const rail = document.querySelector(".body-sidebar") as HTMLElement;
			const active = document.querySelector(
				".body-sidebar .standard-sidebar-item.active-sidebar"
			) as HTMLElement | null;
			return {
				railWidth: rail && getComputedStyle(rail).width,
				topCount: document.querySelectorAll(".body-sidebar .sidebar-items > .sidebar-item-container").length,
				activeLabel: active ? active.textContent?.trim() : null,
			};
		});

		expect(state.railWidth).toBe("256px");
		expect(state.topCount).toBe(12);
		expect(state.activeLabel).toContain("Contract Management");
	});
});
