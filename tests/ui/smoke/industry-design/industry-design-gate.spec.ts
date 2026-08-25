import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * Industry design gate — cross-module computed-style parity (AGENTS.md §6.6).
 *
 * kentender_core.tests.test_industry_design_gate is the static half (every
 * page-level Vue root wraps class="kt-industry", no app forks a competing
 * token file). This is the runtime half: it proves two independently-owned
 * pages that both claim ".kt-industry" are actually rendering with the same
 * CSS custom properties, not just a same-named class each has redefined —
 * exactly the failure mode this gate exists to catch (Strategy's Structure
 * screen looked plausible for several iterations while silently rendering
 * its own forked token file, discovered only by a live getComputedStyle diff
 * against Reference Data).
 *
 * Keep in sync with kentender_core.tests.test_industry_design_gate.LEGACY_BUNDLE_ALLOWLIST —
 * add a page here only once it is off that allowlist.
 */

const PAGES = ["/desk/reference-data", "/desk/strategy-portfolio"];

test.describe("Industry design gate — computed style parity", () => {
	test("every Industry page renders the same accent, button and card tokens", async ({ page }) => {
		await loginAsAdministrator(page);

		const samples: Record<string, Record<string, string>> = {};

		for (const route of PAGES) {
			await page.goto(route);
			const root = page.locator(".kt-industry").first();
			await expect(root).toBeVisible();

			samples[route] = await root.evaluate((el) => {
				const cs = getComputedStyle(el as HTMLElement);
				return {
					accent: cs.getPropertyValue("--kt-color-accent").trim(),
					accent800: cs.getPropertyValue("--kt-color-accent-800").trim(),
					divider: cs.getPropertyValue("--kt-color-divider").trim(),
					radiusMd: cs.getPropertyValue("--kt-radius-md").trim(),
					fontHeading: cs.getPropertyValue("--kt-font-heading").trim(),
					fontBody: cs.getPropertyValue("--kt-font-body").trim(),
				};
			});
		}

		const [firstRoute, ...restRoutes] = PAGES;
		for (const route of restRoutes) {
			expect(samples[route], `${route} vs ${firstRoute}`).toEqual(samples[firstRoute]);
		}
	});

	test("the page rail is the same shared component on every Industry page", async ({ page }) => {
		await loginAsAdministrator(page);

		for (const route of PAGES) {
			await page.goto(route);
			const rail = page.locator(".kt-rail").first();
			await expect(rail).toBeVisible();
			const height = await rail.evaluate((el) => getComputedStyle(el as HTMLElement).height);
			expect(height, route).toBe("64px");
			// A scoped-CSS attribute must be present — its absence is exactly how
			// this session caught a component silently crossing a bundle boundary
			// and losing its Vue-internal wiring (see kt_industry_page_rail.bundle.js).
			const hasScopeAttr = await rail.evaluate((el) =>
				Array.from((el as HTMLElement).attributes).some((a) => a.name.startsWith("data-v-"))
			);
			expect(hasScopeAttr, route).toBe(true);
		}
	});
});
