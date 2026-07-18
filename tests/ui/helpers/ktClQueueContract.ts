import { expect, type Page } from "@playwright/test";

/** Outline-variant token used on filter controls (`#c4c6cf`). */
export const KT_CL_OUTLINE_VARIANT_RGB = "rgb(196, 198, 207)";

export type KtClToolbarChromeOptions = {
	/** Last crumb text (module/parent), bold SPAN — not a link */
	currentCrumb: string | RegExp;
	/** Leaf H1 under page header */
	pageTitle: string | RegExp;
	/** Optional ancestor link that must remain clickable */
	ancestorLink?: string | RegExp;
	/** When false, skip avatar size / margin metrics (default true) */
	assertUserClusterMetrics?: boolean;
};

/**
 * Top toolbar + page header contract (C1-M1): context trail left, user cluster right, no search.
 */
export async function expectKtClToolbarChrome(page: Page, opts: KtClToolbarChromeOptions) {
	const toolbar = page.getByTestId("kt-cl-toolbar");
	await expect(toolbar).toBeVisible();
	await expect(toolbar.getByTestId("kt-cl-toolbar-search")).toHaveCount(0);
	await expect(toolbar.getByTestId("kt-cl-toolbar-title-sep")).toHaveCount(0);
	await expect(toolbar.getByTestId("kt-cl-toolbar-page-title")).toHaveCount(0);

	const trail = toolbar.getByTestId("kt-cl-breadcrumbs");
	await expect(trail).toBeVisible();
	const current = trail.getByTestId("kt-cl-breadcrumb-current");
	await expect(current).toHaveText(opts.currentCrumb);
	await expect(current).toHaveJSProperty("tagName", "SPAN");
	await expect(trail.getByRole("link", { name: opts.currentCrumb })).toHaveCount(0);
	if (opts.ancestorLink) {
		await expect(trail.getByRole("link", { name: opts.ancestorLink })).toBeVisible();
	}

	await expect(page.locator('[data-testid="kt-cl-page-header"] [data-testid="kt-cl-breadcrumbs"]')).toHaveCount(
		0
	);
	await expect(page.getByTestId("kt-cl-page-title")).toHaveText(opts.pageTitle);

	await expect(toolbar.getByTestId("kt-cl-toolbar-notifications")).toBeVisible();
	await expect(toolbar.getByTestId("kt-cl-toolbar-help")).toBeVisible();
	await expect(toolbar.getByTestId("kt-cl-toolbar-user-name")).not.toBeEmpty();
	await expect(toolbar.getByTestId("kt-cl-toolbar-user-role")).toBeVisible();
	const avatar = toolbar.getByTestId("kt-cl-toolbar-avatar");
	await expect(avatar).toBeVisible();

	if (opts.assertUserClusterMetrics !== false) {
		const clusterMetrics = await toolbar.evaluate((el) => {
			const name = el.querySelector('[data-testid="kt-cl-toolbar-user-name"]');
			const av = el.querySelector('[data-testid="kt-cl-toolbar-avatar"]');
			const sep = el.querySelector('[data-testid="kt-cl-toolbar-user-sep"]');
			const nCs = name ? getComputedStyle(name) : null;
			const aCs = av ? getComputedStyle(av) : null;
			return {
				nameMargin: nCs && nCs.marginBottom,
				avatarW: av && Math.round(av.getBoundingClientRect().width),
				avatarH: av && Math.round(av.getBoundingClientRect().height),
				avatarRadius: aCs && aCs.borderRadius,
				sepH: sep && Math.round(sep.getBoundingClientRect().height),
			};
		});
		expect(clusterMetrics.nameMargin).toBe("0px");
		expect(clusterMetrics.avatarW).toBe(32);
		expect(clusterMetrics.avatarH).toBe(32);
		expect(clusterMetrics.sepH).toBe(24);
		expect(Number.parseFloat(String(clusterMetrics.avatarRadius))).toBeGreaterThanOrEqual(16);

		const notifBorder = await toolbar
			.getByTestId("kt-cl-toolbar-notifications")
			.evaluate((el) => getComputedStyle(el).borderStyle);
		expect(notifBorder === "none" || notifBorder === "").toBeTruthy();
	}
}

export type KtClFilterBarLayoutOptions = {
	/** A non-search filter key used to measure compact field width (default std_family) */
	sampleFilterKey?: string;
	/** When set, assert this filter shares the same row (top) as sampleFilterKey */
	sameRowFilterKey?: string;
};

/**
 * Filter bar: `|` separator, outline-variant borders, search fills leftover space.
 */
export async function expectKtClFilterBarLayout(page: Page, opts: KtClFilterBarLayoutOptions = {}) {
	const sampleKey = opts.sampleFilterKey || "std_family";
	const bar = page.getByTestId("kt-cl-filter-bar");
	await expect(bar).toBeVisible();
	await expect(bar.getByTestId("kt-cl-filter-sep")).toHaveText("|");

	const search = bar.locator('[data-filter="search"]');
	const sample = bar.locator(`[data-filter="${sampleKey}"]`);
	await expect(search).toBeVisible();
	await expect(sample).toBeVisible();

	const metrics = await bar.evaluate(
		(el, keys: { sampleKey: string; sameRowKey: string | null }) => {
			const s = el.querySelector('[data-filter="search"]') as HTMLElement | null;
			const f = el.querySelector(`[data-filter="${keys.sampleKey}"]`) as HTMLElement | null;
			const same = keys.sameRowKey
				? (el.querySelector(`[data-filter="${keys.sameRowKey}"]`) as HTMLElement | null)
				: null;
			const fields = el.querySelector(".kt-cl-filter-fields") as HTMLElement | null;
			if (!s || !f || !fields) return null;
			const sc = getComputedStyle(s);
			const fc = getComputedStyle(f);
			const barBox = el.getBoundingClientRect();
			const searchBox = s.getBoundingClientRect();
			const fieldsBox = fields.getBoundingClientRect();
			return {
				searchW: Math.round(searchBox.width),
				familyW: Math.round(f.getBoundingClientRect().width),
				rightGap: Math.round(barBox.right - fieldsBox.right),
				barW: Math.round(barBox.width),
				sampleTop: Math.round(f.getBoundingClientRect().top),
				sameTop: same ? Math.round(same.getBoundingClientRect().top) : null,
				searchBorderColor: sc.borderTopColor,
				familyBorderColor: fc.borderTopColor,
				searchBorderW: sc.borderTopWidth,
			};
		},
		{ sampleKey, sameRowKey: opts.sameRowFilterKey || null }
	);

	expect(metrics).not.toBeNull();
	expect(metrics!.searchW).toBeGreaterThan(metrics!.familyW * 1.5);
	expect(metrics!.searchW).toBeGreaterThan(metrics!.barW * 0.35);
	expect(metrics!.rightGap).toBeLessThan(40);
	expect(metrics!.searchBorderW).toBe("1px");
	expect(metrics!.searchBorderColor).toBe(KT_CL_OUTLINE_VARIANT_RGB);
	expect(metrics!.familyBorderColor).toBe(KT_CL_OUTLINE_VARIANT_RGB);
	if (opts.sameRowFilterKey && metrics!.sameTop != null) {
		expect(metrics!.sameTop).toBe(metrics!.sampleTop);
	}
}

export type KtClQueueTableFooterOptions = {
	/** Default page size shown in the select (default "20") */
	defaultPageSize?: string;
	/** When false, skip asserting pager presence (empty / single-page edge cases) */
	requirePager?: boolean;
};

/**
 * Queue table footer: Rows per page control left of the page counter.
 */
export async function expectKtClQueueTableFooter(page: Page, opts: KtClQueueTableFooterOptions = {}) {
	const defaultSize = opts.defaultPageSize ?? "20";
	const requirePager = opts.requirePager !== false;

	await expect(page.getByTestId("kt-cl-ui00-table")).toBeVisible({ timeout: 15_000 });
	const pageSize = page.getByTestId("kt-cl-ui00-page-size");
	const pager = page.getByTestId("kt-cl-ui00-pager");

	await expect(page.getByTestId("kt-cl-ui00-page-size-wrap")).toContainText(/Rows per page/i);
	await expect(pageSize).toHaveValue(defaultSize);
	if (requirePager) {
		await expect(pager).toBeVisible();
		const order = await page.evaluate(() => {
			const size = document.querySelector('[data-testid="kt-cl-ui00-page-size"]');
			const pg = document.querySelector('[data-testid="kt-cl-ui00-pager"]');
			if (!size || !pg) return null;
			return size.getBoundingClientRect().left < pg.getBoundingClientRect().left;
		});
		expect(order).toBe(true);
	} else {
		const order = await page.evaluate(() => {
			const wrap = document.querySelector('[data-testid="kt-cl-ui00-footer-right"]');
			const size = document.querySelector('[data-testid="kt-cl-ui00-page-size"]');
			if (!wrap || !size) return null;
			const children = Array.from(wrap.children);
			const sizeIdx = children.findIndex((c) => c.contains(size) || c === size);
			return sizeIdx === 0 || sizeIdx >= 0;
		});
		expect(order).toBe(true);
	}
}

/**
 * Changing Rows per page must call the dashboard method with the new page_size and keep the select in sync.
 */
export async function expectKtClPageSizeWired(
	page: Page,
	opts: {
		methodIncludes: string;
		selectValue?: string;
		windowFlag?: string;
	}
) {
	const selectValue = opts.selectValue ?? "10";
	const flag = opts.windowFlag ?? "__ktClLastPageSize";
	const methodIncludes = opts.methodIncludes;

	await page.evaluate(
		({ flagName, methodNeedle }) => {
			const w = window as unknown as Record<string, unknown> & {
				frappe: { call: (opts: { method?: string; args?: { page_size?: number } }) => unknown };
			};
			w[flagName] = null;
			const orig = w.frappe.call.bind(w.frappe);
			w.frappe.call = function (callOpts) {
				if (String((callOpts && callOpts.method) || "").includes(methodNeedle)) {
					w[flagName] = callOpts.args && callOpts.args.page_size;
				}
				return orig(callOpts);
			};
		},
		{ flagName: flag, methodNeedle: methodIncludes }
	);

	await page.getByTestId("kt-cl-ui00-page-size").selectOption(selectValue);
	await expect
		.poll(async () => page.evaluate((flagName) => (window as unknown as Record<string, unknown>)[flagName], flag), {
			timeout: 15_000,
		})
		.toBe(Number(selectValue));
	await expect(page.getByTestId("kt-cl-ui00-page-size")).toHaveValue(selectValue);
}
