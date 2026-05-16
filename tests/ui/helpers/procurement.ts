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

/** R4-002 — Needs My Action panel (pack §11.1). */
export async function expectProcurementHomeNeedsActionPanel(page: Page) {
	const panel = page.locator('.plc-procurement-home-needs-action');
	await expect(panel).toBeVisible({ timeout: 45_000 });
	await expect(panel.getByRole('heading', { name: /Needs My Action/i })).toBeVisible();
	return panel;
}

/** R4-003 — Blocked Journeys panel (pack §11.1). */
export async function expectProcurementHomeBlockedPanel(page: Page) {
	const panel = page.locator('.plc-procurement-home-blocked-journeys');
	await expect(panel).toBeVisible({ timeout: 45_000 });
	await expect(panel.getByRole('heading', { name: /Blocked Journeys/i })).toBeVisible();
	return panel;
}

/** R4-004 — Ready for Handoff panel (pack §11.1). */
export async function expectProcurementHomeReadyForHandoffPanel(page: Page) {
	const panel = page.locator('.plc-procurement-home-ready-for-handoff');
	await expect(panel).toBeVisible({ timeout: 45_000 });
	await expect(panel.getByRole('heading', { name: /Ready for Handoff/i })).toBeVisible();
	return panel;
}

export function needsActionJourneyCard(page: Page, journeyTitle: string) {
	return page
		.locator('.plc-procurement-home-needs-action')
		.locator('.kt-ph-journey-card')
		.filter({ hasText: journeyTitle });
}

export function blockedJourneyCard(page: Page, journeyTitle: string) {
	return page
		.locator('.plc-procurement-home-blocked-journeys')
		.locator('.kt-ph-journey-card')
		.filter({ hasText: journeyTitle });
}

export function readyForHandoffJourneyCard(page: Page, journeyTitle: string) {
	return page
		.locator('.plc-procurement-home-ready-for-handoff')
		.locator('.kt-ph-journey-card')
		.filter({ hasText: journeyTitle });
}

/** R4-005 / R4-006 — Desk Page `plc-procurement-journey` with path or query `journey_code` (header loads async). */
export async function expectProcurementJourneyPageShell(page: Page, journeyCode: string) {
	await expect(page.getByTestId('plc-journey-page')).toBeVisible({ timeout: 45_000 });
	await expect(page.getByTestId('plc-journey-route-code')).toContainText(journeyCode, {
		timeout: 45_000,
	});
	await expect(page.getByTestId('plc-journey-header-loading')).toHaveCount(0, { timeout: 45_000 });
	await expect(page.getByTestId('plc-journey-header')).toBeVisible({ timeout: 45_000 });
}

/** R4-006 — WORKS master journey header (requires seed `JRN-MOH-2026-001`). */
export async function expectWorksMasterJourneyHeader(page: Page) {
	await expect(page.getByTestId('plc-journey-header')).toBeVisible({ timeout: 45_000 });
	await expect(page.getByTestId('plc-journey-title')).toContainText('District Hospital Renovation Works', {
		timeout: 45_000,
	});
	await expect(page.getByTestId('plc-journey-entity')).toContainText('PE-MOH');
	await expect(page.getByTestId('plc-journey-category')).toContainText('Works');
	await expect(page.getByTestId('plc-journey-method')).toContainText('Open Tender');
	await expect(page.getByTestId('plc-journey-current-stage')).toContainText('Tender Published');
	await expect(page.getByTestId('plc-journey-next-action')).toContainText(/tender|closing|opening|readiness/i);
}

/** WORKS seed §15 — base checkpoint `step_key` order (must match `works_seed_step_contract.py`). */
export const WORKS_JOURNEY_TIMELINE_STEP_KEYS_IN_ORDER: readonly string[] = [
	'strategy',
	'budget',
	'demand',
	'planning_inclusion',
	'package_release',
	'std_readiness',
	'tender_publication',
	'tender_closing',
	'opening_readiness',
	'bid_opening',
	'evaluation_award',
	'contract',
];

/** R4-007 — Lifecycle spine (`plc-journey-timeline`, rectification `plc-journey-step-*` pillars). */
export async function expectWorksJourneyTimelineSpine(page: Page) {
	const timeline = page.getByTestId('plc-journey-timeline');
	await expect(timeline).toBeVisible({ timeout: 45_000 });
	await expect(page.getByTestId('plc-journey-timeline-title')).toContainText(/Lifecycle spine/i);

	const nodes = timeline.locator('.plc-journey-timeline-node');
	await expect(nodes).toHaveCount(WORKS_JOURNEY_TIMELINE_STEP_KEYS_IN_ORDER.length);

	const keys: string[] = [];
	for (let i = 0; i < WORKS_JOURNEY_TIMELINE_STEP_KEYS_IN_ORDER.length; i += 1) {
		const k = await nodes.nth(i).getAttribute('data-step-key');
		keys.push(String(k || '').trim());
	}
	expect(keys).toEqual(WORKS_JOURNEY_TIMELINE_STEP_KEYS_IN_ORDER);

	await expect(timeline.locator('.plc-journey-step-pill.plc-journey-step-tender')).toHaveCount(2);
	await expect(timeline.locator('.plc-journey-step-pill.plc-journey-step-planning')).toHaveCount(2);
	await expect(timeline.locator('.plc-journey-step-pill.plc-journey-step-opening')).toHaveCount(2);

	const evalAward = timeline.locator('[data-step-key="evaluation_award"] .plc-journey-step-pill').first();
	await expect(evalAward).toHaveClass(/plc-journey-step-evaluation/);
	await expect(evalAward).toHaveClass(/plc-journey-step-award/);

	// TENDER_PUBLISHED seed: rows 1–7 done (incl. Handed Off); 8–12 not started.
	for (let i = 0; i < 7; i += 1) {
		await expect(nodes.nth(i).locator('.plc-journey-step-pill')).toHaveClass(/plc-journey-step--done/);
	}
	for (let i = 7; i < WORKS_JOURNEY_TIMELINE_STEP_KEYS_IN_ORDER.length; i += 1) {
		await expect(nodes.nth(i).locator('.plc-journey-step-pill')).toHaveClass(/plc-journey-step--not-started/);
	}
}

/** R4-008 — Step detail cards (blocker badge, `plc-open-current-module` when route present). */
export async function expectWorksJourneyStepCardsSection(page: Page) {
	const section = page.getByTestId('plc-journey-step-cards');
	await expect(section).toBeVisible({ timeout: 45_000 });
	await expect(page.getByTestId('plc-journey-step-cards-title')).toContainText(/Step details/i);

	const cards = section.getByTestId('plc-journey-step-card');
	await expect(cards).toHaveCount(WORKS_JOURNEY_TIMELINE_STEP_KEYS_IN_ORDER.length);

	for (let i = 0; i < WORKS_JOURNEY_TIMELINE_STEP_KEYS_IN_ORDER.length; i += 1) {
		const key = WORKS_JOURNEY_TIMELINE_STEP_KEYS_IN_ORDER[i];
		const card = section.locator(`[data-step-key="${key}"]`).first();
		await expect(card).toBeVisible();
		await expect(card.getByTestId('plc-journey-step-blocker-badge')).toHaveCount(0);
	}

	const tenderPub = section.locator('[data-step-key="tender_publication"]').first();
	await expect(tenderPub.getByTestId('plc-open-current-module')).toBeVisible();
	await expect(tenderPub.getByTestId('plc-open-current-module')).toContainText(/Open module/i);
}

/** R4-009 — Current focus panel (`plc-current-focus`) and blocker summary. */
export async function expectWorksJourneyCurrentFocusPanel(page: Page) {
	const panel = page.getByTestId('plc-current-focus');
	await expect(panel).toBeVisible({ timeout: 45_000 });
	await expect(page.getByTestId('plc-current-focus-title')).toContainText(/Current focus/i);

	// First non-completed WORKS step @ TENDER_PUBLISHED: tender_closing ("Tender Closed").
	const milestone = panel.locator('.plc-current-focus-milestone').first();
	await expect(milestone).toHaveAttribute('data-step-key', 'tender_closing');
	await expect(page.getByTestId('plc-current-focus-step-label')).toContainText(/Tender Closed/i);
	await expect(page.getByTestId('plc-current-focus-step-status')).toContainText(/Not Started/i);

	await expect(page.getByTestId('plc-current-focus-next-action')).toContainText(
		/Await tender closing|prepare bid opening|opening readiness/i,
	);

	await expect(page.getByTestId('plc-current-focus-owner')).toContainText(/Tender Management/i);
	await expect(page.getByTestId('plc-current-focus-journey-status')).toContainText(/Completed/i);

	const blockers = page.getByTestId('plc-current-focus-blockers');
	await expect(blockers).toBeVisible();
	await expect(page.getByTestId('plc-current-focus-blocker-total')).toHaveAttribute('data-count', '0');
	await expect(page.getByTestId('plc-current-focus-blocker-critical')).toHaveAttribute('data-count', '0');
	await expect(page.getByTestId('plc-current-focus-blockers-empty')).toBeVisible();
}

/** WORKS TENDER_PUBLISHED base handoff codes (must match `works_master_handoff_payloads.BASE_HANDOFF_CODES`). */
export const WORKS_BASE_HANDOFF_CODES: readonly string[] = [
	'STRATREF-MOH-2026-001',
	'BUDCONF-MOH-2026-001',
	'DEMAPP-MOH-2026-001',
	'PLANINCL-MOH-2026-001',
	'PKGREL-MOH-2026-001',
	'STDREADY-TND-MOH-2026-001',
	'PUBCERT-TND-MOH-2026-001',
];

/** R4-010 — Handoff evidence panel (`plc-handoff-panel`). */
export async function expectWorksJourneyHandoffPanel(page: Page) {
	const panel = page.getByTestId('plc-handoff-panel');
	await expect(panel).toBeVisible({ timeout: 45_000 });
	await expect(page.getByTestId('plc-handoff-panel-title')).toContainText(/Handoffs & evidence/i);

	const cards = panel.getByTestId('plc-handoff-card');
	await expect(cards).toHaveCount(WORKS_BASE_HANDOFF_CODES.length);

	const strat = panel.locator('[data-handoff-code="STRATREF-MOH-2026-001"]');
	await expect(strat.getByTestId('plc-handoff-card-title')).toContainText(/Strategy Alignment Reference/i);
	await expect(strat.getByTestId('plc-handoff-card-status')).toContainText(/Consumed/i);
	await expect(strat.getByTestId('plc-handoff-card-route')).toContainText(/Strategy.*→.*Budget/i);

	const pub = panel.locator('[data-handoff-code="PUBCERT-TND-MOH-2026-001"]');
	await expect(pub.getByTestId('plc-handoff-card-title')).toContainText(/Tender Publication Certificate/i);
	await expect(pub.getByTestId('plc-handoff-card-source')).toContainText(/TM2 Tender · TND-MOH-2026-001/i);
	await expect(pub.getByTestId('plc-handoff-card-status')).toContainText(/Handed Off/i);

	// R4-013 — one “Technical details” control per seeded handoff (non-empty technical_refs).
	await expect(panel.getByTestId('plc-open-evidence')).toHaveCount(WORKS_BASE_HANDOFF_CODES.length);
}

/** R4-011 — Evidence timeline (`plc-evidence-timeline`, `get_journey.evidence_summary` §9.5). */
export async function expectWorksJourneyEvidenceTimeline(page: Page) {
	const section = page.getByTestId('plc-evidence-timeline');
	await expect(section).toBeVisible({ timeout: 45_000 });
	await expect(page.getByTestId('plc-evidence-timeline-title')).toContainText(/Evidence timeline/i);

	const events = section.getByTestId('plc-evidence-timeline-event');
	await expect(events).toHaveCount(WORKS_BASE_HANDOFF_CODES.length);

	const strat = section.locator('[data-handoff-code="STRATREF-MOH-2026-001"]').first();
	await expect(strat.getByTestId('plc-evidence-timeline-module')).toContainText(/Strategy/i);
	await expect(strat.getByTestId('plc-evidence-timeline-event-title')).toContainText(/Strategy Alignment Reference/i);

	const pub = section.locator('[data-handoff-code="PUBCERT-TND-MOH-2026-001"]').first();
	await expect(pub.getByTestId('plc-evidence-timeline-event-title')).toContainText(/Tender Publication Certificate/i);
	await expect(pub.getByTestId('plc-evidence-timeline-object')).toContainText(/TM2 Tender · TND-MOH-2026-001/i);
	await expect(pub.getByTestId('plc-evidence-timeline-handoff-code')).toContainText(/PUBCERT-TND-MOH-2026-001/);
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
