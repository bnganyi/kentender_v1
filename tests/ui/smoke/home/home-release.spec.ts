import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	AMINA, BRIAN, CHARLES, DANIEL, JOSPHAT, NAOMI, PASSWORD, PETER, flat, openHomeFromMenu, putWorldClock, region, root, rows,
} from "./helpers";

/**
 * HOME-CHG-001 v0.6 Phase 8 (rows HOME6-0805 and HOME6-0807): the keyboard, 200% zoom and every persona, from the menu.
 * Read-only, on the seed world at its clock (see helpers.ts). Run on the test site:
 *   scripts/test-site.sh run npx playwright test tests/ui/smoke/home/home-release.spec.ts --workers=1
 */
test.describe.configure({ mode: "serial", timeout: 240_000 });
test.beforeAll(() => putWorldClock());

const summary = async (page) => (await page.locator('[data-testid^="kt-home-summary-"]').allInnerTexts()).map((t) => t.replace(/\s+/g, " ").trim());

test.describe("type (Charles)", () => {
	test("the page sets in the board's own type: Inter, with none of Desk's letter spacing", async ({ page }) => {
		await openHomeFromMenu(page, CHARLES);
		const type = await page.evaluate(() => {
			const read = (sel: string) => {
				const style = getComputedStyle(document.querySelector(sel) as HTMLElement);
				return { family: style.fontFamily.split(",")[0].replace(/"/g, "").trim(), spacing: style.letterSpacing };
			};
			return { root: read(".kt-home"), sub: read(".kt-home header p"), row: read(".kt-home .kt-home-row-title"), rail: read(".kt-home .kt-home-rail-state") };
		});
		for (const [where, found] of Object.entries(type)) expect(found, where).toEqual({ family: "InterVariable", spacing: "normal" });
	});
});

test.describe("keyboard (Charles)", () => {
	test("Tab reaches every control in reading order, never traps focus, and every stop shows a focus ring", async ({ page }) => {
		await openHomeFromMenu(page, CHARLES);
		await page.locator('[data-testid="kt-home-title"]').evaluate((el) => {
			// start just before the first control inside Home: focus the heading's own position, then Tab onward
			const probe = document.createElement("span");
			probe.tabIndex = -1;
			el.parentElement!.insertBefore(probe, el);
			probe.focus();
		});
		const stops: { id: string; ring: boolean }[] = [];
		for (let i = 0; i < 60; i += 1) {
			await page.keyboard.press("Tab");
			const stop = await page.evaluate(() => {
				const el = document.activeElement as HTMLElement | null;
				const home = document.querySelector('[data-testid="kt-home-root"]');
				if (!el || !home || !home.contains(el)) return null;
				const style = getComputedStyle(el);
				const ring = el.matches(":focus-visible") && style.outlineStyle !== "none" && parseFloat(style.outlineWidth) > 0; // the design system's 1 px accent outline
				return { id: el.getAttribute("data-testid") || el.getAttribute("aria-label") || el.textContent!.trim().slice(0, 40), ring };
			});
			if (!stop) break; // focus has left Home: no trap
			stops.push(stop);
		}
		const ids = stops.map((s) => s.id);
		expect(ids.length, `stops: ${ids.join(" | ")}`).toBeGreaterThan(10);
		expect(ids.length).toBeLessThan(60); // left Home before the cap
		// reading order: the three summary columns, then My work's Continue buttons, then the rail
		const column = (name: string) => ids.findIndex((id) => id === `kt-home-summary-${name}` || id.startsWith(`kt-home-summary-${name}`));
		expect(column("my_work")).toBeGreaterThanOrEqual(0);
		expect(column("my_work")).toBeLessThan(column("waiting"));
		expect(column("waiting")).toBeLessThan(column("oversight"));
		const firstContinue = ids.findIndex((id) => id === "kt-home-continue" || id.startsWith("Continue:"));
		expect(firstContinue).toBeGreaterThan(column("oversight"));
		expect(stops.filter((s) => !s.ring).map((s) => s.id), "stops with no visible focus ring").toEqual([]);
	});

	test("a summary column moves focus to its region and Enter on Continue opens the owner's route", async ({ page }) => {
		await openHomeFromMenu(page, CHARLES);
		await page.locator('[data-testid="kt-home-summary-waiting"]').focus();
		await page.keyboard.press("Enter");
		await expect.poll(() => page.evaluate(() => (document.activeElement as HTMLElement | null)?.closest("#waiting") !== null)).toBe(true);
		await rows(page, "my-work").nth(4).locator('[data-testid="kt-home-continue"]').focus();
		await page.keyboard.press("Enter");
		await expect(page).toHaveURL(/\/desk\/tenders\/TND-MOH-2026-010\/evaluation\/secretary$/, { timeout: 60_000 });
	});

	test("Show more works from the keyboard and puts focus on the first appended row", async ({ page }) => {
		await openHomeFromMenu(page, CHARLES);
		await page.locator('#my-work [data-testid="kt-home-show-more"]').focus();
		await page.keyboard.press("Enter");
		await expect(rows(page, "my-work")).toHaveCount(10);
		const focused = await page.evaluate(() => (document.activeElement as HTMLElement | null)?.closest("[data-key]")?.getAttribute("data-key") || "");
		expect(focused).toBe(await rows(page, "my-work").nth(5).getAttribute("data-key"));
	});
});

test.describe("200% zoom (Charles)", () => {
	// A 1440 px window at 200% zoom is 720 CSS px wide; WCAG reflow is checked again at 400 px.
	for (const [width, height] of [[720, 512], [400, 600]]) {
		test(`at ${width} px the page reflows: no sideways scroll, the rail stacks under the main column, nothing is cut off`, async ({ page }) => {
			await page.setViewportSize({ width, height });
			await openHomeFromMenu(page, CHARLES);
			const metrics = await page.evaluate(() => {
				const sheet = document.querySelector(".kt-home-sheet") as HTMLElement;
				const main = document.querySelector('[data-testid="kt-home-main"]') as HTMLElement;
				const rail = document.querySelector('[data-testid="kt-home-rail"]') as HTMLElement;
				const box = sheet.getBoundingClientRect();
				const wide = Array.from(sheet.querySelectorAll<HTMLElement>("*")).filter((el) => {
					const r = el.getBoundingClientRect();
					return r.width > 0 && (r.right > box.right + 1 || r.left < box.left - 1);
				}).map((el) => el.getAttribute("data-testid") || el.className || el.tagName);
				return {
					docOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
					mainBottom: main.getBoundingClientRect().bottom,
					railTop: rail.getBoundingClientRect().top,
					railLeft: rail.getBoundingClientRect().left,
					mainLeft: main.getBoundingClientRect().left,
					wide,
				};
			});
			expect(metrics.docOverflow, "the page scrolls sideways").toBeLessThanOrEqual(1);
			expect(metrics.railTop, "the rail has not stacked under the main column").toBeGreaterThanOrEqual(metrics.mainBottom - 1);
			expect(Math.abs(metrics.railLeft - metrics.mainLeft)).toBeLessThanOrEqual(2);
			expect(metrics.wide, "elements wider than the sheet").toEqual([]);
			await region(page, "completed").scrollIntoViewIfNeeded();
			await expect(region(page, "completed").locator('[data-testid="kt-home-row"]').first()).toBeVisible();
		});
	}
});

test.describe("every persona, from the sidebar", () => {
	const PERSONAS = [
		{ user: CHARLES, name: "Charles", line: "Head of Procurement Function", columns: ["My work 10 actions for you", "Waiting on others 3 items you're waiting on", "Records you oversee 6 records with outstanding matters"] },
		{ user: AMINA, name: "Amina", line: "Accounting Officer", columns: ["My work 4 actions for you", "Waiting on others 2 items you're waiting on", "Records you oversee 6 records with outstanding matters"] },
		{ user: BRIAN, name: "Brian", line: "Procurement Officer", columns: ["My work 9 actions for you", "Waiting on others 1 item you're waiting on"] },
		{ user: PETER, name: "Peter", line: "Head of User Department", columns: ["My work 1 action for you", "Waiting on others 1 item you're waiting on", "Records you oversee 6 records with outstanding matters"] },
		{ user: NAOMI, name: "Naomi", line: "Auditor", columns: ["My work 0 actions for you", "Waiting on others 0 items you're waiting on", "Records you oversee 8 records with outstanding matters"] },
	];
	for (const persona of PERSONAS) {
		test(`${persona.name}: greeting, responsibility line, summary columns and no console errors`, async ({ page }) => {
			const errors = await openHomeFromMenu(page, persona.user);
			await expect(page.locator('[data-testid="kt-home-title"]')).toHaveText(new RegExp(`^Good (morning|afternoon|evening), ${persona.name}$`));
			expect(await flat(page.locator('[data-testid="kt-home-responsibilities"]'))).toContain(persona.line);
			expect(await summary(page)).toEqual(persona.columns);
			expect(errors.filter((e) => !/socket|favicon/i.test(e))).toEqual([]);
		});
	}

	test("Daniel (Technical Operator) sees the orientation and the search link, and no business action or count", async ({ page }) => {
		await openHomeFromMenu(page, DANIEL);
		await expect(page.locator('[data-testid="kt-home-technical-link"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-home-summary"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="kt-home-continue"]')).toHaveCount(0);
	});

	test("Josphat has nothing in his queues, so the empty state shows and no zeros do", async ({ page }) => {
		await openHomeFromMenu(page, JOSPHAT);
		await expect(page.locator('[data-testid="kt-home-empty"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-home-summary"]')).toHaveCount(0);
	});

	test("Jane (a public observer, a Website User) has no way into Home", async ({ page }) => {
		await login(page, "jane.wanjiku@observer.example", PASSWORD);
		await page.goto("/desk/home", { waitUntil: "domcontentloaded" });
		await expect(page.locator("body")).toContainText("not permitted", { ignoreCase: true, timeout: 30_000 });
		await expect(root(page)).toHaveCount(0);
	});
});
