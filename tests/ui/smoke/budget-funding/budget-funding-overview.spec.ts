import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

/**
 * BUD-UI-03 Budget Overview — live canvas + workspace tabs (Pack Phase 3).
 */

test.describe.configure({ mode: "serial" });

test.describe("Budget Funding overview (BUD-UI-03)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("open from portfolio shows live Overview regions and totals", async ({ page }) => {
		await page.goto("/desk/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 45_000,
		});

		const row = page.locator('tr[data-budget-code="MOH-BUD-2027-2028"]');
		await expect(row).toBeVisible({ timeout: 20_000 });
		await row.getByRole("button", { name: /Open/i }).click();
		await page.waitForURL(/\/desk\/budget-overview\/MOH-BUD-2027-2028/, { timeout: 20_000 });

		const root = page.locator('[data-testid="kt-bud-overview"][data-kt-bud-live="1"]');
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId("kt-bud-workspace-chrome")).toBeVisible();
		await expect(page.getByTestId("kt-bud-workspace-tabs")).toBeVisible();
		await expect(page.getByTestId("kt-bud-overview-identity")).toBeVisible();
		await expect(page.getByTestId("kt-bud-overview-funding")).toBeVisible();
		await expect(page.getByTestId("kt-bud-overview-kpis")).toBeVisible();
		await expect(page.getByTestId("kt-bud-overview-bar")).toBeVisible();
		await expect(page.getByTestId("kt-bud-overview-strategy")).toBeVisible();
		await expect(page.getByTestId("kt-bud-overview-definition")).toBeVisible();
		await expect(page.getByTestId("kt-bud-overview-attention")).toBeVisible();

		await expect(
			page.locator('[data-testid="kt-bud-workspace-chrome"] span[data-kt-bud-budget-code]'),
		).toHaveText("MOH-BUD-2027-2028");
		await expect(page.locator('[data-kt-bud-ov="approved"]')).toHaveText("KES 560M");
		await expect(page.locator('[data-kt-bud-ov="available"]')).toHaveText("KES 105M");
		await expect(page.locator('[data-kt-bud-ov="actual"]')).toHaveText("KES 180M");
		await expect(page.locator('[data-kt-bud-ov="source"]')).toHaveText("Direct capture");

		await assertStitchDeskChrome(page, {
			rootTestId: "kt-bud-overview",
			primaryCtaTestId: "kt-bud-overview-primary",
			secondaryCtaTestId: "kt-bud-view-performance",
			headlineSelector: "[data-kt-bud-budget-title]",
		});
	});

	test("tabs navigate without flash and round-trip keeps shell", async ({ page }) => {
		await page.goto("/desk/budget-overview/MOH-BUD-2027-2028", { waitUntil: "domcontentloaded" });
		const root = page.locator('[data-testid="kt-bud-overview"][data-kt-bud-live="1"]');
		await expect(root).toBeVisible({ timeout: 45_000 });

		await expect(page.locator("body")).toHaveClass(/kt-cl-shell/);

		const first = await root.evaluate((el) => ({
			key: el.getAttribute("data-kt-bud-mount-key") || "",
			gen: el.getAttribute("data-kt-bud-mount-gen") || "",
			live: el.getAttribute("data-kt-bud-live") || "",
		}));
		expect(first.key).toContain("budget-overview");
		expect(Number(first.gen)).toBeGreaterThanOrEqual(1);
		expect(first.live).toBe("1");

		await page
			.locator('[data-testid="kt-bud-tab-budget-lines"]')
			.filter({ visible: true })
			.click();
		await page.waitForURL(/\/desk\/budget-lines\/MOH-BUD-2027-2028/, { timeout: 20_000 });
		const linesPage = page
			.locator('[data-testid="kt-bud-lines"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(linesPage).toBeVisible({ timeout: 45_000 });
		await expect(linesPage.getByTestId("kt-bud-workspace-chrome")).toBeVisible();
		await expect(linesPage.getByTestId("kt-bud-lines-table")).toBeVisible();
		await expect(page.locator("body")).toHaveClass(/kt-cl-shell/);
		await expect(linesPage.locator("[data-kt-bud-budget-title]")).not.toHaveText("—");

		await linesPage.getByTestId("kt-bud-tab-budget-overview").click();
		await page.waitForURL(/\/desk\/budget-overview\/MOH-BUD-2027-2028/, { timeout: 20_000 });
		const overview = page
			.locator('[data-testid="kt-bud-overview"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(overview).toBeVisible({ timeout: 45_000 });
		await expect(page.locator("body")).toHaveClass(/kt-cl-shell/);
		await expect(overview.locator('[data-kt-bud-ov="approved"]')).toHaveText("KES 560M");

		const again = await overview.evaluate((el) => ({
			key: el.getAttribute("data-kt-bud-mount-key") || "",
			gen: el.getAttribute("data-kt-bud-mount-gen") || "",
			live: el.getAttribute("data-kt-bud-live") || "",
		}));
		expect(again.key).toBe(first.key);
		expect(again.gen).toBe(first.gen);
		expect(again.live).toBe("1");
	});

	test("budget tab hop never flashes empty chrome title placeholders", async ({ page }) => {
		await page.goto("/desk/budget-overview/MOH-BUD-2027-2028", { waitUntil: "domcontentloaded" });
		const overview = page
			.locator('[data-testid="kt-bud-overview"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(overview).toBeVisible({ timeout: 45_000 });
		const seedTitle = (
			await overview.locator("[data-kt-bud-budget-title]").first().textContent()
		)?.trim();
		expect(seedTitle && seedTitle !== "—").toBeTruthy();

		const titles = await page.evaluate(async () => {
			const samples: string[] = [];
			const push = () => {
				const visible = [...document.querySelectorAll('[data-testid="kt-bud-workspace-chrome"]')].find(
					(node) => {
						const pc = node.closest(".page-container");
						if (!pc) return false;
						return getComputedStyle(pc).display !== "none";
					},
				);
				const title = (
					(visible &&
						(visible.querySelector("[data-kt-bud-budget-title]") as HTMLElement | null)
							?.textContent) ||
					""
				).trim();
				samples.push(title);
			};
			const tab = document.querySelector(
				'[data-testid="kt-bud-overview"]:not([style*="display: none"]) [data-kt-bud-tab="budget-lines"]',
			);
			if (!tab) return { samples, err: "no-tab" };
			(tab as HTMLElement).click();
			push();
			await new Promise((r) => requestAnimationFrame(() => r(null)));
			push();
			for (let i = 0; i < 8; i++) {
				await new Promise((r) => setTimeout(r, 40));
				push();
			}
			return { samples, err: null };
		});

		expect(titles.err).toBeNull();
		expect(titles.samples.length).toBeGreaterThan(3);
		const afterSwap = titles.samples.slice(1);
		expect(afterSwap.some((t) => t && t !== "—")).toBe(true);
		expect(afterSwap.every((t) => !t || t !== "—")).toBe(true);
	});

	test("Active primary CTA routes to revision create page", async ({ page }) => {
		await page.goto("/desk/budget-overview/MOH-BUD-2027-2028", { waitUntil: "domcontentloaded" });
		const overview = page
			.locator('[data-testid="kt-bud-overview"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(overview).toBeVisible({ timeout: 45_000 });
		await expect(overview.getByTestId("kt-bud-overview-primary")).toHaveText(/Request revision/i);
		await overview.getByTestId("kt-bud-overview-primary").click();
		await page.waitForURL(/\/desk\/budget-revision-create\/MOH-BUD-2027-2028/, { timeout: 20_000 });
		await expect(
			page
				.locator('[data-testid="kt-bud-revision-create"][data-kt-bud-live="1"]')
				.filter({ visible: true }),
		).toBeVisible({ timeout: 45_000 });
	});
});
