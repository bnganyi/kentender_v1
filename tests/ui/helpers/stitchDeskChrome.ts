import { expect, type Page } from "@playwright/test";

/**
 * Runtime Stitch Desk chrome contract — Desk/Bootstrap bleed defeat.
 *
 * Visibility-only smoke is insufficient. Call this from every Stitch Desk
 * portfolio/shell Playwright gate before claiming UI Done.
 *
 * Primary CTA must be Stitch navy #001f48 (not Win98 outset black).
 * Selects must keep a chevron (SVG Forms stand-in or Material expand_more).
 */

export type StitchDeskChromeOptions = {
	/** Root locator that is already live / visible (optional). */
	rootTestId?: string;
	/** Primary CTA test id (bg-primary button). */
	primaryCtaTestId: string;
	/**
	 * filled = Stitch navy primary (default).
	 * bordered = Stitch secondary header action (Audit Export — white + border).
	 */
	primaryCtaStyle?: "filled" | "bordered";
	/** Optional secondary bordered CTA test id. */
	secondaryCtaTestId?: string;
	/** CSS selector for a filter <select> inside the canvas. Omit/empty when the surface has no select. */
	selectSelector?: string;
	/** Optional headline selector (defaults to canvas h1). */
	headlineSelector?: string;
	/** Expect Manrope 28/700 on headline (default true). */
	assertHeadline?: boolean;
};

export async function assertStitchDeskChrome(page: Page, opts: StitchDeskChromeOptions) {
	if (opts.rootTestId) {
		await expect(page.getByTestId(opts.rootTestId)).toBeVisible({ timeout: 30_000 });
	}

	const chrome = await page.evaluate(
		({ primaryCtaTestId, secondaryCtaTestId, selectSelector, headlineSelector }) => {
			const primary = document.querySelector(
				`[data-testid="${primaryCtaTestId}"]`,
			) as HTMLElement | null;
			const secondary = secondaryCtaTestId
				? (document.querySelector(`[data-testid="${secondaryCtaTestId}"]`) as HTMLElement | null)
				: null;
			const select = document.querySelector(selectSelector) as HTMLElement | null;
			const h1 = document.querySelector(headlineSelector || ".kt-stitch-canvas h1") as HTMLElement | null;
			const pcs = primary ? getComputedStyle(primary) : null;
			const scs = secondary ? getComputedStyle(secondary) : null;
			const sel = select ? getComputedStyle(select) : null;
			const h1cs = h1 ? getComputedStyle(h1) : null;
			const sib = select?.nextElementSibling;
			const materialChevron =
				!!sib &&
				sib.classList.contains("material-symbols-outlined") &&
				(sib.textContent || "").trim() === "expand_more";
			return {
				hasPrimary: !!primary,
				hasSelect: !!select,
				primaryBg: pcs?.backgroundColor || "",
				primaryBorder: pcs?.border || "",
				primaryRadius: pcs?.borderRadius || "",
				secondaryBg: scs?.backgroundColor || "",
				secondaryBorder: scs?.border || "",
				selectBgImage: sel?.backgroundImage || "",
				selectPaddingRight: parseFloat(sel?.paddingRight || "0"),
				materialChevron,
				titleFamily: h1cs?.fontFamily || "",
				titleWeight: h1cs?.fontWeight || "",
				titleSize: h1cs?.fontSize || "",
				canvasClass: !!document.querySelector(".kt-stitch-canvas"),
			};
		},
		{
			primaryCtaTestId: opts.primaryCtaTestId,
			secondaryCtaTestId: opts.secondaryCtaTestId || "",
			selectSelector: opts.selectSelector,
			headlineSelector: opts.headlineSelector || ".kt-stitch-canvas h1",
		},
	);

	expect(chrome.canvasClass, "root must opt into .kt-stitch-canvas").toBeTruthy();
	expect(chrome.hasPrimary, `missing primary CTA ${opts.primaryCtaTestId}`).toBeTruthy();

	expect(chrome.primaryBorder.toLowerCase()).not.toContain("outset");
	expect(parseFloat(chrome.primaryRadius)).toBeGreaterThanOrEqual(6);
	if (opts.primaryCtaStyle === "bordered") {
		// Audit Stitch header Export — white fill + outline, not navy primary.
		expect(chrome.primaryBg).toMatch(/rgb\(\s*255,\s*255,\s*255\s*\)/);
		expect(chrome.primaryBorder).toMatch(/1px/);
	} else {
		// Primary CTA = Stitch navy, never Desk Win98 outset black.
		expect(chrome.primaryBg).toBe("rgb(0, 31, 72)");
	}

	if (opts.secondaryCtaTestId) {
		expect(chrome.secondaryBg).toMatch(/rgb\(\s*255,\s*255,\s*255\s*\)/);
		expect(chrome.secondaryBorder).toMatch(/1px/);
	}

	if (opts.selectSelector) {
		expect(chrome.hasSelect, `missing select ${opts.selectSelector}`).toBeTruthy();
		const hasChevron =
			/svg|data:image/i.test(chrome.selectBgImage) || chrome.materialChevron;
		expect(hasChevron, "filter select must show chevron glyph").toBeTruthy();
		expect(chrome.selectPaddingRight).toBeGreaterThanOrEqual(24);

		// Permanent: never stack SVG Forms chevron + Material expand_more (garbled "~").
		if (chrome.materialChevron) {
			expect(
				chrome.selectBgImage === "none" || chrome.selectBgImage === "",
				"Material expand_more sibling requires select background-image: none",
			).toBeTruthy();
		}
	}

	if (opts.assertHeadline !== false) {
		expect(chrome.titleFamily).toMatch(/Manrope/i);
		expect(chrome.titleWeight).toBe("700");
		expect(chrome.titleSize).toBe("28px");
	}
}
