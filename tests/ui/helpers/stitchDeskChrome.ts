import { expect, type Page } from "@playwright/test";

/**
 * Runtime Stitch Desk chrome contract — Desk/Bootstrap bleed defeat + DS tokens.
 *
 * Authority: docs/mvp-1/00_common/design_system_refactor/
 * Visibility-only smoke is insufficient. Call this from every Stitch Desk
 * portfolio/shell Playwright gate before claiming UI Done.
 *
 * Primary CTA must be DS primary #003d9b (not Win98 outset black).
 * Selects must keep a chevron (SVG Forms stand-in or Material expand_more).
 */

export type StitchDeskChromeOptions = {
	/** Root locator that is already live / visible (optional). */
	rootTestId?: string;
	/** Primary CTA test id (bg-primary button). */
	primaryCtaTestId: string;
	/**
	 * filled = DS primary (default).
	 * bordered = secondary header action (Audit Export — white + border).
	 */
	primaryCtaStyle?: "filled" | "bordered";
	/** Optional secondary bordered CTA test id. */
	secondaryCtaTestId?: string;
	/** CSS selector for a filter <select> inside the canvas. Omit/empty when the surface has no select. */
	selectSelector?: string;
	/** Optional headline selector (defaults to canvas h1). */
	headlineSelector?: string;
	/** Expect Manrope 30/700 on headline (default true). */
	assertHeadline?: boolean;
	/**
	 * Hover filled primary and require white label on lifted primary-container (#0052cc).
	 * Opt-in — wire for Budget Lines + Strategy portfolio (and later modules).
	 */
	assertPrimaryHover?: boolean;
	/**
	 * Assert enabled text inputs / textareas use white fill (not surface gray).
	 * Opt-in for data-entry forms (revision create, register, strategy create).
	 */
	assertEditableInputs?: boolean;
};

/** DS muted table/toolbar head stand-ins (#f7f8f9, #f8f8fa) or surface-low (#f3f4f6). */
const MUTED_HEAD_RGB =
	/^rgb\(\s*(243|247|248),\s*(244|248),\s*(246|249|250)\s*\)$/;
/** outline-variant #c3c6d6 (DS) or legacy #c3c6d1 */
const CARD_BORDER_OK = /rgb\(\s*195,\s*198,\s*(209|214)\s*\)/;

/**
 * Section headers + table theads use DS muted surface; rounded-xl cards stay rounded.
 * Inputs/buttons stay lightly rounded (0.5rem).
 */
export async function assertStitchSectionTableChrome(
	page: Page,
	opts: {
		/** Section card with .rounded-xl (e.g. Need). */
		sectionTestId?: string;
		/** Table card wrapper with .rounded-xl. */
		tableWrapTestId?: string;
		/** Soft-round control that must stay ~0.5rem (not squared). */
		roundedControlTestId?: string;
	},
) {
	if (opts.sectionTestId) {
		const section = page.getByTestId(opts.sectionTestId).filter({ visible: true }).first();
		await expect(section).toBeVisible({ timeout: 15_000 });
		const styles = await section.evaluate((el) => {
			const cs = getComputedStyle(el);
			const header = el.querySelector(
				".kt-ds-section-title, .bg-surface-container-low, .kt-ds-toolbar-band",
			) as HTMLElement | null;
			const hcs = header ? getComputedStyle(header) : null;
			return {
				cardRadius: cs.borderRadius,
				borderColor: cs.borderColor,
				borderWidth: cs.borderWidth,
				headerBg: hcs?.backgroundColor || "",
			};
		});
		const radiusPx = parseFloat(styles.cardRadius);
		expect(radiusPx, "section card must be rounded (DS)").toBeGreaterThanOrEqual(6);
		expect(radiusPx, "section card must not be fully squared").toBeLessThanOrEqual(14);
		if (styles.headerBg && styles.headerBg !== "rgba(0, 0, 0, 0)") {
			// Transparent section titles (kt-ds-section-title) are OK; bands must be muted.
			const isTransparent =
				styles.headerBg === "rgba(0, 0, 0, 0)" || styles.headerBg === "transparent";
			if (!isTransparent) {
				expect(
					styles.headerBg,
					"section header band must be muted DS (not primary-fixed)",
				).toMatch(MUTED_HEAD_RGB);
			}
		}
		if (parseFloat(styles.borderWidth) > 0) {
			expect(styles.borderColor, "section card border must be outline-variant").toMatch(
				CARD_BORDER_OK,
			);
		}
	}

	if (opts.tableWrapTestId) {
		const wrap = page.getByTestId(opts.tableWrapTestId).filter({ visible: true }).first();
		await expect(wrap).toBeVisible({ timeout: 15_000 });
		const styles = await wrap.evaluate((el) => {
			const cs = getComputedStyle(el);
			const headerRow =
				(el.querySelector("thead tr.kt-ds-table-head") as HTMLElement | null) ||
				(el.querySelector("thead tr.bg-surface-container-low") as HTMLElement | null) ||
				(el.querySelector("thead.bg-surface-container-low") as HTMLElement | null) ||
				(el.querySelector("thead tr") as HTMLElement | null);
			const hcs = headerRow ? getComputedStyle(headerRow) : null;
			return {
				cardRadius: cs.borderRadius,
				borderColor: cs.borderColor,
				borderWidth: cs.borderWidth,
				headerBg: hcs?.backgroundColor || "",
			};
		});
		const radiusPx = parseFloat(styles.cardRadius);
		expect(radiusPx, "table card must be rounded (DS)").toBeGreaterThanOrEqual(6);
		expect(radiusPx, "table card must not be fully squared").toBeLessThanOrEqual(14);
		expect(styles.headerBg, "table thead must be muted DS (not primary-fixed)").toMatch(
			MUTED_HEAD_RGB,
		);
		if (parseFloat(styles.borderWidth) > 0) {
			expect(styles.borderColor, "table card border must be outline-variant").toMatch(
				CARD_BORDER_OK,
			);
		}
	}

	if (opts.roundedControlTestId) {
		const control = page.getByTestId(opts.roundedControlTestId).filter({ visible: true }).first();
		await expect(control).toBeVisible({ timeout: 15_000 });
		const radius = await control.evaluate((el) => getComputedStyle(el).borderRadius);
		const px = parseFloat(radius);
		expect(px, "inputs/buttons stay lightly rounded").toBeGreaterThanOrEqual(6);
		expect(px, "inputs/buttons must not be fully squared").toBeLessThanOrEqual(10);
	}
}

/** Editable form controls must look active — white fill, never surface gray. */
export async function assertEditableInputs(page: Page, rootTestId?: string) {
	const scope = rootTestId
		? page.getByTestId(rootTestId).filter({ visible: true }).first()
		: page.locator(".kt-stitch-canvas").filter({ visible: true }).first();
	await expect(scope).toBeVisible({ timeout: 30_000 });
	const control = scope
		.locator(
			'input[type="text"]:not([disabled]):not([readonly]), textarea:not([disabled]):not([readonly])',
		)
		.filter({ visible: true })
		.first();
	await expect(control).toBeVisible({ timeout: 15_000 });
	const bg = await control.evaluate((el) => getComputedStyle(el).backgroundColor);
	expect(bg, "editable control must be white (not surface gray)").toBe("rgb(255, 255, 255)");
}

/** Filled primary hover contract — white on primary-container, never inky on-primary-container. */
export async function assertFilledPrimaryCtaHover(page: Page, primaryCtaTestId: string) {
	const primary = page.getByTestId(primaryCtaTestId).filter({ visible: true }).first();
	await expect(primary).toBeVisible({ timeout: 15_000 });
	await primary.hover();
	await expect
		.poll(
			async () =>
				primary.evaluate((el) => {
					const cs = getComputedStyle(el);
					return `${cs.color}|${cs.backgroundColor}`;
				}),
			{ timeout: 5_000 },
		)
		.toBe("rgb(255, 255, 255)|rgb(0, 82, 204)");
}

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
			const glyph = sib ? (sib.textContent || "").trim() : "";
			const materialChevron =
				!!sib &&
				sib.classList.contains("material-symbols-outlined") &&
				(glyph === "expand_more" || glyph === "arrow_drop_down");
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
		// Primary CTA = DS #003d9b, never Desk Win98 outset black.
		expect(chrome.primaryBg).toBe("rgb(0, 61, 155)");
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
		expect(chrome.titleSize).toBe("30px");
	}

	if (opts.assertPrimaryHover && opts.primaryCtaStyle !== "bordered") {
		await assertFilledPrimaryCtaHover(page, opts.primaryCtaTestId);
	}

	if (opts.assertEditableInputs) {
		await assertEditableInputs(page, opts.rootTestId);
	}
}
