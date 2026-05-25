import { expect, type Locator, type Page } from '@playwright/test';

export async function expectListSelectionPreservesScroll(
	page: Page,
	list: Locator,
	rows: Locator,
	targetIndex: number,
) {
	const rowCount = await rows.count();
	expect(rowCount).toBeGreaterThan(targetIndex);

	await list.evaluate((el) => {
		el.scrollTop = el.scrollHeight;
	});
	const before = await list.evaluate((el) => el.scrollTop);
	await rows.nth(targetIndex).click({ force: true });
	const after = await list.evaluate((el) => el.scrollTop);

	expect(Math.abs(after - before)).toBeLessThanOrEqual(2);
}

export async function expectNoLoadingFlash(
	panel: Locator,
	loadingText: Locator,
	timeoutMs = 1500,
) {
	await expect(panel).toBeVisible({ timeout: 30000 });
	await expect(loadingText).toHaveCount(0, { timeout: timeoutMs });
}

export async function expectNoLoadingTestIds(
	page: Page,
	loadingTestIds: string[],
	timeoutMs = 1500,
) {
	for (const testId of loadingTestIds) {
		await expect(page.getByTestId(testId)).toHaveCount(0, { timeout: timeoutMs });
	}
}

export async function expectDetailTabCycleNoLoadingFlash(
	page: Page,
	tabs: Array<{ tabTestId: string; panelTestId: string }>,
	loadingTestIds: string[],
) {
	for (const tab of tabs) {
		await page.getByTestId(tab.tabTestId).click();
		await expect(page.getByTestId(tab.panelTestId)).toBeVisible({ timeout: 30000 });
		await expectNoLoadingTestIds(page, loadingTestIds);
	}
}

export async function expectRowSwitchKeepsDetailShell(
	page: Page,
	options: {
		rowSelector: string;
		detailRootSelector: string;
		detailPanelSelector: string;
		stableNodeSelector?: string;
		loadingSelectors?: string[];
		switchToIndex?: number;
		waitMs?: number;
	},
) {
	const rowSelector = options.rowSelector;
	const detailRootSelector = options.detailRootSelector;
	const detailPanelSelector = options.detailPanelSelector;
	const stableNodeSelector = options.stableNodeSelector || '';
	const loadingSelectors = options.loadingSelectors || [];
	const switchToIndex = options.switchToIndex ?? 1;
	const waitMs = options.waitMs ?? 350;

	const rows = page.locator(rowSelector);
	const count = await rows.count();
	expect(count).toBeGreaterThan(switchToIndex);
	await rows.first().click({ force: true });
	await expect(page.locator(detailPanelSelector)).toBeVisible({ timeout: 30_000 });

	await page.evaluate(
		({ rootSel, panelSel, stableSel, loadingSels }) => {
			const root = document.querySelector(rootSel);
			const probe = { loadingSeen: false, panelReplaced: 0, stableNodeReplaced: 0 };
			const state = window as Window & {
				__workspaceProbe?: { loadingSeen: boolean; panelReplaced: number; stableNodeReplaced: number };
				__workspaceProbeStop?: () => void;
			};
			state.__workspaceProbe = probe;
			let currentPanel = root?.querySelector(panelSel) || null;
			let stableNode = stableSel ? root?.querySelector(stableSel) || null : null;
			const obs = new MutationObserver(() => {
				for (const sel of loadingSels) {
					if (document.querySelector(sel)) {
						probe.loadingSeen = true;
					}
				}
				const next = root?.querySelector(panelSel) || null;
				if (currentPanel && next && next !== currentPanel) {
					probe.panelReplaced += 1;
					currentPanel = next;
				}
				if (stableSel) {
					const stableNext = root?.querySelector(stableSel) || null;
					if (stableNode && stableNext && stableNext !== stableNode) {
						probe.stableNodeReplaced += 1;
						stableNode = stableNext;
					}
				}
			});
			if (root) {
				obs.observe(root, { childList: true, subtree: true });
			}
			state.__workspaceProbeStop = () => obs.disconnect();
		},
		{
			rootSel: detailRootSelector,
			panelSel: detailPanelSelector,
			stableSel: stableNodeSelector,
			loadingSels: loadingSelectors,
		},
	);

	await rows.nth(switchToIndex).click({ force: true });
	await page.waitForTimeout(waitMs);
	const probe = await page.evaluate(() => {
		const state = window as Window & {
			__workspaceProbe?: { loadingSeen: boolean; panelReplaced: number; stableNodeReplaced: number };
			__workspaceProbeStop?: () => void;
		};
		const out = state.__workspaceProbe || { loadingSeen: false, panelReplaced: -1, stableNodeReplaced: -1 };
		if (state.__workspaceProbeStop) {
			state.__workspaceProbeStop();
		}
		return out;
	});
	expect(probe.loadingSeen).toBeFalsy();
	expect(probe.panelReplaced).toBe(0);
	if (stableNodeSelector) {
		expect(probe.stableNodeReplaced).toBe(0);
	}
}

export async function expectSearchKeepsFocusWhileTyping(search: Locator, text: string) {
	await search.click();
	let typed = '';
	for (const ch of text.split('')) {
		typed += ch;
		await search.type(ch);
		await expect(search).toBeFocused();
	}
	await expect(search).toHaveValue(typed);
}

export async function expectDetailTabSwitchPreservesListScroll(
	list: Locator,
	tabButton: Locator,
	tabPanel: Locator,
) {
	await expect(list).toBeVisible();
	await list.evaluate((el) => {
		el.scrollTop = el.scrollHeight;
	});
	const before = await list.evaluate((el) => el.scrollTop);
	expect(before).toBeGreaterThan(0);

	await tabButton.click();
	await expect(tabPanel).toBeVisible();

	const after = await list.evaluate((el) => el.scrollTop);
	expect(Math.abs(after - before)).toBeLessThanOrEqual(2);
}

export async function expectPrimarySidebarItemHighlighted(
	page: Page,
	primaryItemText: string,
	duplicateItemText?: string,
) {
	const state = await page.evaluate(
		([primaryText, duplicateText]) => {
			const normalize = (s: string) => String(s || '').trim().toLowerCase();
			const items = Array.from(document.querySelectorAll('.standard-sidebar-item')).map((el) => ({
				label: normalize(el.textContent || ''),
				active: el.classList.contains('active-sidebar'),
			}));
			const primary = items.find((item) => item.label === normalize(primaryText));
			const duplicate = duplicateText
				? items.find((item) => item.label === normalize(duplicateText))
				: null;
			return {
				primaryFound: !!primary,
				primaryActive: !!(primary && primary.active),
				duplicateFound: !!duplicate,
				duplicateActive: !!(duplicate && duplicate.active),
			};
		},
		[primaryItemText, duplicateItemText || ''],
	);

	expect(state.primaryFound).toBeTruthy();
	expect(state.primaryActive).toBeTruthy();
	if (duplicateItemText && state.duplicateFound) {
		expect(state.duplicateActive).toBeFalsy();
	}
}

export async function expectStatusFiltersUseHierarchyContract(
	container: Locator,
	options?: { allTestId?: string; sampleZeroTestId?: string },
) {
	const allFilter = container.getByTestId(options?.allTestId || 'strategy-status-all');
	await expect(allFilter).toHaveClass(/kt-status-filter/);
	await expect(allFilter).not.toHaveClass(/btn-primary/);

	const zeroFilter = container.getByTestId(options?.sampleZeroTestId || 'strategy-status-submitted');
	const countText = ((await zeroFilter.textContent()) || '').replace(/\s+/g, ' ').trim();
	const isZeroCount = /\b0$/.test(countText);
	if (isZeroCount) {
		await expect(zeroFilter).toHaveClass(/is-zero/);
	}
}

export async function expectPrimaryTabsUseHierarchyContract(
	page: Page,
	options?: { tabPrefix?: string },
) {
	const prefix = options?.tabPrefix || 'strategy-tab-';
	const activePrimaryTab = page.locator(`[data-testid^="${prefix}"][aria-selected="true"]`).last();
	await expect(activePrimaryTab).toHaveClass(/kt-primary-tab/);
	await expect(activePrimaryTab).not.toHaveClass(/btn-primary/);
}

export async function expectSecondaryTabsUseHierarchyContract(page: Page) {
	const activeSecondaryTab = page.locator('.kt-strategy-structure-subtab[aria-selected="true"]').last();
	await expect(activeSecondaryTab).toHaveClass(/kt-secondary-tab/);
	await expect(activeSecondaryTab).not.toHaveClass(/btn-primary/);
}

export async function expectContextActionUsesHierarchyContract(page: Page) {
	const addTarget = page.locator('[data-testid="structure-add-target"]').last();
	await expect(addTarget).toHaveClass(/kt-context-action/);
	await expect(addTarget).not.toHaveClass(/btn-primary/);
}

export async function expectRowActionUsesHierarchyContract(page: Page) {
	const rowEdit = page.locator('[data-testid^="structure-edit-"]').last();
	await expect(rowEdit).toHaveClass(/kt-row-action/);
	await expect(rowEdit).not.toHaveClass(/btn-default/);
}

export async function expectReviewStatusMatchesWorkspace(page: Page) {
	const readStatus = () =>
		page.evaluate(() => {
			const normalize = (s: string | null) => String(s || '').trim().toLowerCase();
			const review = document.querySelector('[data-testid="strategy-review-status"]');
			const selected = document.querySelector('[data-testid="selected-plan-status"]');
			const listActive = document.querySelector('.kt-strategy-plan-row.is-active .kt-strategy-inline-status');
			const reviewText = normalize(review ? review.textContent : '');
			const reviewState = normalize(reviewText.replace(/^current state:\s*/i, ''));
			return {
				review: reviewState,
				selected: normalize(selected ? selected.textContent : ''),
				list: normalize(listActive ? listActive.textContent : ''),
			};
		});

	const first = await readStatus();
	await expect
		.poll(async () => {
			const now = await readStatus();
			return {
				review: now.review,
				selected: now.selected,
				list: now.list,
				synced: !!now.review && now.review === now.selected && now.review === now.list,
			};
		}, { timeout: 30_000 })
		.toMatchObject({ synced: true });

	const submit = page.getByTestId('strategy-submit-plan');
	const submitCount = await submit.count();
	if (submitCount > 0 && (await submit.isEnabled())) {
		await Promise.all([
			page.waitForResponse(
				(r) => r.url().includes('kentender_strategy.api.strategy_workflow.submit_plan') && r.ok(),
				{ timeout: 60_000 },
			),
			submit.click(),
		]);
		await expect(page.getByTestId('strategy-review-status')).toContainText(/Submitted/i, { timeout: 30_000 });
		const after = await readStatus();
		expect(after.review).toBe('submitted');
		expect(after.review).toBe(after.selected);
		expect(after.review).toBe(after.list);
	}
}

export async function expectStructureOverviewTypographyHierarchy(page: Page) {
	await page.getByTestId('strategy-tab-structure').click();
	await expect(page.getByTestId('strategy-tab-panel-structure')).toBeVisible();
	const overview = page.getByTestId('structure-overview');
	await expect(overview).toBeVisible({ timeout: 30_000 });

	const firstProgram = page.locator('.kt-strategy-outline-row--program').first();
	const firstTarget = page.locator('.kt-strategy-outline-row--target').first();
	await expect(firstProgram).toBeVisible();
	await expect(firstTarget).toBeVisible();

	const [programWeight, targetWeight] = await Promise.all([
		firstProgram
			.locator('.kt-strategy-outline-title')
			.first()
			.evaluate((el) => getComputedStyle(el).fontWeight),
		firstTarget
			.locator('.kt-strategy-outline-title')
			.first()
			.evaluate((el) => getComputedStyle(el).fontWeight),
	]);
	expect(Number(programWeight)).toBeGreaterThan(Number(targetWeight));

	const code = page.locator('.kt-strategy-outline-code').first();
	if ((await code.count()) > 0) {
		await expect(code).toBeVisible();
	}
	const token = page.locator('.kt-strategy-type-token').first();
	await expect(token).toBeVisible();
}
