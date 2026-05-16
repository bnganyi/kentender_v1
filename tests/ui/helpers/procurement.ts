import { expect, type Locator, type Page } from '@playwright/test';

import { openWorkspaceFromDeskLauncher } from './routes';
import { procurementModule } from './selectors';

export const procurementHomeWorkspace = {
	heading: 'Procurement Home',
	routePattern: /\/(app|desk)\/procurement-home/,
};

export const procurementPlanningWorkspace = {
	heading: 'Procurement Planning',
	routePattern: /\/(app|desk)(\/procurement-planning|\/Workspaces\/Procurement%20Planning)/,
};

export const supplierRegistryWorkspace = {
	heading: 'KTSM Supplier Registry',
	routePattern: /\/(app|desk)(\/ktsm-supplier-registry|\/Workspaces\/KTSM%20Supplier%20Registry)/,
};

export async function openProcurementWorkspaceFromModule(page: Page, workspaceLabel: string) {
	await openWorkspaceFromDeskLauncher(page, procurementModule, workspaceLabel);
}

export async function expectProcurementHomeShell(page: Page) {
	await expect(page.getByTestId('ph-landing-page')).toBeVisible({ timeout: 45_000 });
}

/** R4-001 / PLC-SMOKE-UI-001 — Active Procurement Journeys panel on Procurement Home. */
export async function expectProcurementHomeActiveJourneysPanel(page: Page) {
	const panel = page.locator('.plc-procurement-home-active-journeys');
	await expect(panel).toBeVisible({ timeout: 45_000 });
	await expect(panel.getByRole('heading', { name: /Active Procurement Journeys/i })).toBeVisible();
	return panel;
}

/** Locator for a journey card by title within the active journeys panel. */
export function activeJourneyCard(page: Page, journeyTitle: string) {
	return page
		.locator('.plc-procurement-home-active-journeys')
		.locator('.kt-ph-journey-card')
		.filter({ hasText: journeyTitle });
}

export async function expectProcurementPlanningShell(page: Page) {
	await expect(page.getByTestId('pp-page-title')).toContainText(procurementPlanningWorkspace.heading, {
		timeout: 45_000,
	});
	await expect(page.getByTestId('pp-current-plan-bar')).toBeVisible();
	await expect(page.getByTestId('pp-control-bar')).toBeVisible();
}

export async function expectKtsmSupplierRegistryWorkbenchShell(page: Page) {
	await expect(page.getByTestId('ktsm-workbench-root')).toBeVisible({ timeout: 45_000 });
	await expect(page.getByTestId('ktsm-header')).toBeVisible();
}

/** G0-012 / LV-G0-017-02 — lifecycle spine order in the Procurement left rail. */
const G012_PRIMARY_SPECS: readonly (string | RegExp)[] = [
	'Procurement Home',
	'Procurement Journeys',
	'My Work',
	'Strategy Alignment',
	'Budget & Funding',
	/Demand Intake/i,
	'Procurement Planning',
	'Tender Document Readiness',
	'Tender Management',
	'Bid Opening',
	/Evaluation\s*&\s*Award|Evaluation and Award/i,
	'Contract Management',
	'Supplier Management',
	'Evidence & Audit',
];

export type ExpectProcurementSidebarSpineG012Options = {
	/**
	 * When true, skip **My Work** in ordering assertions. The **My Work** workspace uses
	 * `module: Kentender Procurement`; Desk hides the sidebar row when that module is not in
	 * the user `allow_modules` (common for spine-only general roles). Administrator / full
	 * module sets still use the default full spine.
	 */
	omitMyWork?: boolean;
	/**
	 * When true, only assert **among links that appear** for this user (workspace `roles` /
	 * module gate may hide most spine rows). Still requires **Procurement Home** and
	 * **Procurement Journeys**, then checks vertical order for every other visible spine label
	 * in G0-012 order. **Configuration** is asserted only if that heading is present.
	 */
	onlyVisibleSpineLinks?: boolean;
};

export async function expectProcurementSidebarSpineG012(
	page: Page,
	opts?: ExpectProcurementSidebarSpineG012Options,
) {
	const specs: readonly (string | RegExp)[] = opts?.omitMyWork
		? G012_PRIMARY_SPECS.filter((s) => s !== 'My Work')
		: G012_PRIMARY_SPECS;
	const sb = page.locator('.body-sidebar');

	if (opts?.onlyVisibleSpineLinks) {
		await expect(sb.getByRole('link', { name: 'Procurement Home', exact: true }).first()).toBeVisible({
			timeout: 45_000,
		});
		await expect(sb.getByRole('link', { name: 'Procurement Journeys', exact: true }).first()).toBeVisible({
			timeout: 45_000,
		});
		const visibleLocs: Locator[] = [];
		for (const spec of specs) {
			const loc =
				typeof spec === 'string'
					? sb.getByRole('link', { name: spec, exact: true }).first()
					: sb.getByRole('link', { name: spec }).first();
			try {
				await loc.waitFor({ state: 'visible', timeout: 2500 });
			} catch {
				continue;
			}
			await loc.scrollIntoViewIfNeeded().catch(() => {});
			visibleLocs.push(loc);
		}
		expect(visibleLocs.length).toBeGreaterThanOrEqual(2);
		const boxes: ({ y: number } | null)[] = [];
		for (const loc of visibleLocs) {
			boxes.push(await loc.boundingBox());
		}
		for (let i = 0; i < boxes.length - 1; i += 1) {
			const a = boxes[i];
			const b = boxes[i + 1];
			expect(a).not.toBeNull();
			expect(b).not.toBeNull();
			if (a && b) {
				expect(a.y).toBeLessThanOrEqual(b.y + 4);
			}
		}
		const cfg = sb.getByText('Configuration', { exact: true }).first();
		if (await cfg.isVisible({ timeout: 3000 }).catch(() => false)) {
			await expect(cfg).toBeVisible();
		}
		return;
	}

	const locs = specs.map((spec) =>
		typeof spec === 'string'
			? sb.getByRole('link', { name: spec, exact: true }).first()
			: sb.getByRole('link', { name: spec }).first(),
	);
	for (const loc of locs) {
		await loc.waitFor({ state: 'visible', timeout: 45_000 });
		await loc.scrollIntoViewIfNeeded().catch(() => {});
	}
	await expect(sb.getByText('Configuration', { exact: true }).first()).toBeVisible();

	const boxes: ({ y: number } | null)[] = [];
	for (const loc of locs) {
		boxes.push(await loc.boundingBox());
	}
	for (let i = 0; i < boxes.length - 1; i += 1) {
		const a = boxes[i];
		const b = boxes[i + 1];
		expect(a).not.toBeNull();
		expect(b).not.toBeNull();
		if (a && b) {
			expect(a.y).toBeLessThanOrEqual(b.y + 4);
		}
	}
}

/** @deprecated Prefer {@link expectProcurementSidebarSpineG012} — kept for older spec imports. */
export const expectSidebarProcurementHomeFirst = expectProcurementSidebarSpineG012;

export async function clickSidebarLink(page: Page, label: string | RegExp): Promise<Locator> {
	const link = page.getByRole('link', { name: label }).first();
	await link.waitFor({ state: 'visible', timeout: 45_000 });
	await link.click();
	await page.waitForLoadState('domcontentloaded');
	return link;
}
