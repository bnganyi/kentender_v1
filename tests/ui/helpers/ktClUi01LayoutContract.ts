import { expect, type Page } from "@playwright/test";
import { expectConfigurationContextStrip } from "./ktClConfigContext";
import { expectKtClToolbarChrome } from "./ktClQueueContract";

/**
 * UI-01 Tender Configuration Home — structural layout contract (C1-M3).
 * Catches Bootstrap/Tailwind collisions before they ship (CTA wrap, crumb, handoff icon).
 */

export async function expectUi01StructuralLayout(page: Page) {
	await expectKtClToolbarChrome(page, {
		currentCrumb: /Tender Configuration Home/i,
		pageTitle: /Tender Configuration Home/i,
		ancestorLink: /Tender Configurations/i,
	});
	await expect(page.getByTestId("kt-cl-breadcrumb-current")).toHaveJSProperty("tagName", "SPAN");

	await expectConfigurationContextStrip(page);

	const nextLayout = await page.evaluate(() => {
		const panel = document.querySelector('[data-testid="kt-cl-ui01-next-action"]') as HTMLElement | null;
		const btn = document.querySelector('[data-testid="kt-cl-ui01-next-btn"]') as HTMLElement | null;
		const body = document.querySelector(".kt-cl-ui01-next-body") as HTMLElement | null;
		if (!panel || !btn || !body) return null;
		const p = panel.getBoundingClientRect();
		const b = btn.getBoundingClientRect();
		const c = body.getBoundingClientRect();
		const cs = getComputedStyle(panel);
		const btnCs = getComputedStyle(btn);
		return {
			sameRow: Math.abs(b.top + b.height / 2 - (c.top + c.height / 2)) < 28,
			btnRightOfCopy: b.left >= c.right - 4,
			noWrap: p.height < 160,
			flexDirection: cs.flexDirection,
			flexWrap: cs.flexWrap,
			btnWhiteSpace: btnCs.whiteSpace,
			titleWhite: (() => {
				const t = panel.querySelector('[data-testid="kt-cl-ui01-next-label"]') as HTMLElement | null;
				return t ? getComputedStyle(t).color : "";
			})(),
			bg: cs.backgroundColor,
		};
	});
	expect(nextLayout).not.toBeNull();
	expect(nextLayout!.flexDirection).toBe("row");
	expect(nextLayout!.flexWrap).toBe("nowrap");
	expect(nextLayout!.btnWhiteSpace).toBe("nowrap");
	expect(nextLayout!.sameRow).toBe(true);
	expect(nextLayout!.btnRightOfCopy).toBe(true);
	expect(nextLayout!.noWrap).toBe(true);
	expect(nextLayout!.bg).toMatch(/rgb\(0,\s*34,\s*68\)/);
	expect(nextLayout!.titleWhite).toMatch(/rgb\(255,\s*255,\s*255\)/);

	const handoffHeader = await page.evaluate(() => {
		const hdr = document.querySelector('[data-testid="kt-cl-ui01-handoff-header"]') as HTMLElement | null;
		const title = hdr?.querySelector(".kt-cl-ui01-handoff-title") as HTMLElement | null;
		const icon = hdr?.querySelector(".kt-cl-ui01-handoff-header-icon") as HTMLElement | null;
		if (!hdr || !title || !icon) return null;
		const h = hdr.getBoundingClientRect();
		const t = title.getBoundingClientRect();
		const i = icon.getBoundingClientRect();
		return {
			aligned: Math.abs(t.top + t.height / 2 - (i.top + i.height / 2)) < 6,
			iconRight: i.left > t.right,
			iconInside: i.top >= h.top - 1 && i.bottom <= h.bottom + 1,
			headerH: Math.round(h.height),
		};
	});
	expect(handoffHeader).not.toBeNull();
	expect(handoffHeader!.aligned).toBe(true);
	expect(handoffHeader!.iconRight).toBe(true);
	expect(handoffHeader!.iconInside).toBe(true);
	expect(handoffHeader!.headerH).toBeGreaterThanOrEqual(44);

	const layout = await page.evaluate(() => {
		const side = document.querySelector('[data-testid="kt-cl-ui01-side"]') as HTMLElement | null;
		const main = document.querySelector('[data-testid="kt-cl-ui01-main"]') as HTMLElement | null;
		if (!side || !main) return null;
		const s = side.getBoundingClientRect();
		const m = main.getBoundingClientRect();
		return {
			sideRightOfMain: s.left >= m.right - 8,
			sideWide: s.width > 200,
		};
	});
	expect(layout).not.toBeNull();
	expect(layout!.sideRightOfMain).toBe(true);
	expect(layout!.sideWide).toBe(true);

	await expect(page.getByTestId("kt-cl-ui01-progress")).toBeVisible();
	await expect(page.getByTestId("kt-cl-ui01-resources")).toBeVisible();

	const handoffAction = page.getByTestId("kt-cl-ui01-handoff-action-readiness_check");
	if ((await handoffAction.count()) > 0) {
		const chrome = await handoffAction.evaluate((el) => {
			const cs = getComputedStyle(el);
			return {
				borderStyle: cs.borderStyle,
				borderWidth: cs.borderWidth,
				bg: cs.backgroundColor,
			};
		});
		expect(chrome.borderStyle === "none" || chrome.borderWidth === "0px").toBeTruthy();
		expect(chrome.bg === "rgba(0, 0, 0, 0)" || chrome.bg === "transparent").toBeTruthy();
	}

	const body = await page.getByTestId("kt-cl-ui01-root").innerText();
	expect(body.toLowerCase()).not.toContain("finalize configuration");
	expect(body.toLowerCase()).not.toContain("publish tender");
	expect(body.toLowerCase()).not.toContain("complete configuration");
	expect(body).not.toMatch(/\bLocked\b/);
}

export async function expectUi01NineCards(page: Page, titles: string[]) {
	await expect(page.getByTestId("kt-cl-ui01-steps")).toBeVisible();
	for (let i = 1; i <= 9; i++) {
		const id = `CFG-0${i}`;
		await expect(page.getByTestId(`kt-cl-ui01-step-${id}`)).toBeVisible();
		await expect(page.getByTestId(`kt-cl-ui01-step-${id}`)).toContainText(titles[i - 1]);
		await expect(page.getByTestId(`kt-cl-ui01-step-badge-${id}`)).toBeVisible();
	}
}
