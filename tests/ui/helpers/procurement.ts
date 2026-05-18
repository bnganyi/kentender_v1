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

/** R4-001 / R8-006 / PLC-SMOKE-UI-001 — Active Procurement Journeys panel on Procurement Home. */
export async function expectProcurementHomeActiveJourneysPanel(page: Page) {
	const panel = page.getByTestId('plc-procurement-home-active-journeys');
	await expect(panel).toBeVisible({ timeout: 45_000 });
	await expect(panel.getByRole('heading', { name: /Active Procurement Journeys/i })).toBeVisible();
	return panel;
}

/** Locator for a journey card by title within the active journeys panel. */
export function activeJourneyCard(page: Page, journeyTitle: string) {
	return page
		.getByTestId('plc-procurement-home-active-journeys')
		.locator('.kt-ph-journey-card')
		.filter({ hasText: journeyTitle });
}

/** §14 G9-003 — Procurement Home usable: active journeys list with stage, substantive next action, blockers, Open Journey. */
export async function expectG9ProcurementHomeUsable(page: Page, journeyTitle: string) {
	await expectProcurementHomeShell(page);
	const panel = await expectProcurementHomeActiveJourneysPanel(page);
	const host = panel.locator('#kt-ph-active-journeys-host');
	await expect(host.locator('.kt-ph-journey-card').first()).toBeVisible({ timeout: 45_000 });

	const card = activeJourneyCard(page, journeyTitle);
	await expect(card).toBeVisible({ timeout: 45_000 });

	const meta = card.locator('.kt-ph-journey-card-meta');
	await expect(meta.locator('div').filter({ hasText: /Current stage/i }).first()).toBeVisible();
	await expect(meta.locator('div').filter({ hasText: /Next action/i }).first()).toBeVisible();
	const nextRow = meta.locator('div').filter({ hasText: /Next action/i }).first();
	await expect(nextRow).not.toHaveText(/Next action:\s*[—\-]\s*$/);

	await expect(meta.locator('div').filter({ hasText: /Blockers/i }).first()).toBeVisible();
	await expect(card.getByTestId('plc-home-open-journey')).toBeVisible();
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

/** Cursor pack §15.2 PLC-SMOKE-UI-002 — spine pillar **class** hooks on timeline pills (`procurement_journey_page.js`). */
export const PLC_SMOKE_UI_002_SPINE_PILLAR_CLASSES: readonly string[] = [
	'plc-journey-step-strategy',
	'plc-journey-step-budget',
	'plc-journey-step-demand',
	'plc-journey-step-planning',
	'plc-journey-step-std-readiness',
	'plc-journey-step-tender',
	'plc-journey-step-opening',
];

/** R8-007 / PLC-SMOKE-UI-002 — `plc-journey-page` + spine pillars visible; statuses via {@link expectWorksJourneyTimelineSpine}. */
export async function expectPlcSmokeUi002JourneyFullSpine(page: Page) {
	await expect(page.getByTestId('plc-journey-page')).toBeVisible({ timeout: 45_000 });
	await expectWorksJourneyTimelineSpine(page);
	const timeline = page.getByTestId('plc-journey-timeline');
	for (const cls of PLC_SMOKE_UI_002_SPINE_PILLAR_CLASSES) {
		const pill = timeline.locator(`.plc-journey-step-pill.${cls}`).first();
		await expect(pill).toBeVisible({ timeout: 45_000 });
		await expect(pill.locator('.plc-journey-step-status')).not.toHaveText(/^\s*$/);
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

/** §14 G9-002 — Base checkpoint handoff cards with locked/passed-forward preview, evidence line, and journey-level next action. */
const G9_BASE_HANDOFF_CARD_EXPECTATIONS: ReadonlyArray<{
	code: string;
	titlePattern: RegExp;
	statusPattern: RegExp;
}> = [
	{
		code: 'STRATREF-MOH-2026-001',
		titlePattern: /Strategy Alignment Reference/i,
		statusPattern: /Consumed/i,
	},
	{
		code: 'BUDCONF-MOH-2026-001',
		titlePattern: /Budget Funding Confirmation/i,
		statusPattern: /Consumed/i,
	},
	{
		code: 'DEMAPP-MOH-2026-001',
		titlePattern: /Demand Approval Certificate/i,
		statusPattern: /Consumed/i,
	},
	{
		code: 'PLANINCL-MOH-2026-001',
		titlePattern: /Planning Inclusion Record/i,
		statusPattern: /Consumed/i,
	},
	{
		code: 'PKGREL-MOH-2026-001',
		titlePattern: /Planning Release Package/i,
		statusPattern: /Consumed/i,
	},
	{
		code: 'STDREADY-TND-MOH-2026-001',
		titlePattern: /Tender Document Readiness Certificate/i,
		statusPattern: /Consumed/i,
	},
	{
		code: 'PUBCERT-TND-MOH-2026-001',
		titlePattern: /Tender Publication Certificate/i,
		statusPattern: /Handed Off/i,
	},
];

export async function expectG9BaseHandoffCardsDetail(page: Page) {
	await expectWorksJourneyHandoffPanel(page);

	const panel = page.getByTestId('plc-handoff-panel');
	for (const row of G9_BASE_HANDOFF_CARD_EXPECTATIONS) {
		const card = panel.locator(`[data-handoff-code="${row.code}"]`);
		await expect(card).toBeVisible({ timeout: 45_000 });
		await expect(card.getByTestId('plc-handoff-card-title')).toContainText(row.titlePattern);
		await expect(card.getByTestId('plc-handoff-card-status')).toContainText(row.statusPattern);
		await expect(card.getByTestId('plc-handoff-card-route')).not.toHaveText(/^\s*$/);

		const preview = card.getByTestId('plc-handoff-card-preview');
		await expect(preview).toBeVisible();
		await expect(preview).not.toHaveText(/^\s*$/);

		const evidence = card.getByTestId('plc-handoff-card-evidence');
		await expect(evidence).toBeVisible();
		await expect(evidence).not.toHaveText(/^\s*$/);

		await expect(card.getByTestId('plc-open-evidence')).toBeVisible();
		await expect(card.getByTestId('plc-handoff-card-stale')).toHaveCount(0);
	}

	await expect(page.getByTestId('plc-current-focus-next-action')).toBeVisible({ timeout: 45_000 });
	await expect(page.getByTestId('plc-current-focus-next-action')).not.toHaveText(/^\s*$/);
}

/** True when both CLOSECERT and OPENREADY WORKS master cards exist (`OPENING_READY` checkpoint seed). Caller must be logged in; loads `/desk` so `frappe.call` is available. */
export async function plcOpeningCheckpointHandoffsSeeded(page: Page): Promise<boolean> {
	await page.goto('/desk', { waitUntil: 'domcontentloaded' });
	return page.evaluate(async () => {
		return new Promise<boolean>((resolve, reject) => {
			// @ts-ignore desk global
			frappe.call({
				method: 'frappe.client.get_list',
				args: {
					doctype: 'Procurement Handoff Card',
					filters: [
						[
							'handoff_code',
							'in',
							['CLOSECERT-TND-MOH-2026-001', 'OPENREADY-TND-MOH-2026-001'],
						],
					],
					fields: ['handoff_code'],
					limit_page_length: 2,
				},
				callback: (r: { message?: { handoff_code?: string }[] }) => {
					const codes = new Set((r.message || []).map((row) => row.handoff_code));
					resolve(
						codes.has('CLOSECERT-TND-MOH-2026-001') &&
							codes.has('OPENREADY-TND-MOH-2026-001'),
					);
				},
				error: reject,
			});
		});
	});
}

/** §14 G9-002A — Optional opening checkpoint: CLOSECERT + OPENREADY on journey handoff panel (requires OPENING_READY seed). */
export async function expectG9OpeningCheckpointHandoffCards(page: Page) {
	const panel = page.getByTestId('plc-handoff-panel');
	await expect(panel).toBeVisible({ timeout: 45_000 });

	const closing = panel.locator('[data-handoff-code="CLOSECERT-TND-MOH-2026-001"]');
	await expect(closing).toBeVisible({ timeout: 45_000 });
	await expect(closing.getByTestId('plc-handoff-card-title')).toContainText(/Tender Closing Certificate/i);
	await expect(closing.getByTestId('plc-handoff-card-status')).toContainText(/Consumed/i);
	await expect(closing.getByTestId('plc-handoff-card-route')).not.toHaveText(/^\s*$/);
	await expect(closing.getByTestId('plc-handoff-card-preview')).toBeVisible();
	await expect(closing.getByTestId('plc-handoff-card-preview')).not.toHaveText(/^\s*$/);
	await expect(closing.getByTestId('plc-handoff-card-evidence')).toBeVisible();
	await expect(closing.getByTestId('plc-handoff-card-evidence')).not.toHaveText(/^\s*$/);
	await expect(closing.getByTestId('plc-open-evidence')).toBeVisible();
	await expect(closing.getByTestId('plc-handoff-card-stale')).toHaveCount(0);

	const opening = panel.locator('[data-handoff-code="OPENREADY-TND-MOH-2026-001"]');
	await expect(opening).toBeVisible({ timeout: 45_000 });
	await expect(opening.getByTestId('plc-handoff-card-title')).toContainText(/Opening Readiness Record/i);
	await expect(opening.getByTestId('plc-handoff-card-status')).toContainText(/Handed Off/i);
	await expect(opening.getByTestId('plc-handoff-card-route')).not.toHaveText(/^\s*$/);
	await expect(opening.getByTestId('plc-handoff-card-preview')).toBeVisible();
	await expect(opening.getByTestId('plc-handoff-card-preview')).not.toHaveText(/^\s*$/);
	await expect(opening.getByTestId('plc-handoff-card-evidence')).toBeVisible();
	await expect(opening.getByTestId('plc-handoff-card-evidence')).not.toHaveText(/^\s*$/);
	await expect(opening.getByTestId('plc-open-evidence')).toBeVisible();
	await expect(opening.getByTestId('plc-handoff-card-stale')).toHaveCount(0);
}

/**
 * R8-008 / PLC-SMOKE-UI-003 — Planning Release Package handoff (`plc-handoff-card` for PKGREL).
 * Pack §15.2: source/target, locked + passed-forward preview, technical details drawer.
 */
export async function expectPlcSmokeUi003PlanningReleaseHandoffCard(page: Page) {
	const panel = page.getByTestId('plc-handoff-panel');
	await expect(panel).toBeVisible({ timeout: 45_000 });

	const card = panel.locator('[data-handoff-code="PKGREL-MOH-2026-001"]');
	await expect(card).toBeVisible({ timeout: 45_000 });
	await expect(card).toHaveAttribute('data-testid', 'plc-handoff-card');

	await expect(card.getByTestId('plc-handoff-card-title')).toContainText(/Planning Release Package/i);
	await expect(card.getByTestId('plc-handoff-card-status')).toContainText(/Consumed/i);
	await expect(card.getByTestId('plc-handoff-card-route')).toContainText(/Procurement Planning/i);
	await expect(card.getByTestId('plc-handoff-card-route')).toContainText(/Tender Management/i);
	await expect(card.getByTestId('plc-handoff-card-source')).toContainText(/Procurement Package/i);
	await expect(card.getByTestId('plc-handoff-card-source')).toContainText(/PKG-MOH-2026-001/);
	await expect(card.getByTestId('plc-handoff-card-target')).toContainText(/TM2 Tender/i);
	await expect(card.getByTestId('plc-handoff-card-target')).toContainText(/TND-MOH-2026-001/);

	// passed_forward_summary preview (first string keys → blurb lines in `procurement_journey_page.js`).
	await expect(card.getByTestId('plc-handoff-card-preview')).toContainText(/Required Std Category/i);
	await expect(card.getByTestId('plc-handoff-card-preview')).toContainText(/Works/i);
	await expect(card.getByTestId('plc-handoff-card-preview')).toContainText(/District Hospital/i);
	await expect(card.getByTestId('plc-handoff-card-evidence')).toContainText(/PKG-MOH-2026-001/);

	const techBtn = card.getByTestId('plc-open-evidence');
	await expect(techBtn).toBeVisible();
	await techBtn.click();
	await expect(page.getByTestId('plc-technical-evidence-drawer')).toBeVisible({ timeout: 15_000 });
	await expect(page.getByTestId('plc-technical-evidence-handoff-code')).toContainText('PKGREL-MOH-2026-001');
	const body = page.getByTestId('plc-technical-evidence-body');
	await expect(body).toContainText('tm2_tender_code');
	await expect(body).toContainText('TND-MOH-2026-001');
	await page.keyboard.press('Escape');
	await expect(page.getByTestId('plc-technical-evidence-drawer')).toBeHidden({ timeout: 15_000 });
}

/** Pack §15.2 PLC-SMOKE-UI-004 / R3-016 BRS-003 — exact business label strings. */
export const PLC_SMOKE_UI_004_BUSINESS_LABELS: readonly string[] = [
	'Tender document package ready',
	'Supplier submission checklist ready',
	'Opening register rules ready',
	'Evaluation rules ready',
	'Contract carry-forward terms ready',
];

/**
 * R8-009 / PLC-SMOKE-UI-004 — TM2 Tender Desk form (`tm2-tender-business-readiness-host`): business labels
 * first; technical output codes only after expanding `plc-br-technical-collapsed`.
 * Precondition: caller has opened `/app/tm2-tender/{code}` and the form layout is visible.
 */
export async function expectPlcSmokeUi004Tm2TenderFormBusinessReadiness(page: Page) {
	const host = page.getByTestId('tm2-tender-business-readiness-host');
	await expect(host).toBeVisible({ timeout: 45_000 });

	const summary = page.getByTestId('plc-business-readiness-summary');
	await expect(summary).toBeVisible({ timeout: 90_000 });
	await expect(host.getByTestId('plc-br-loading')).toHaveCount(0);

	await expect(summary.getByTestId('plc-br-summary-label')).toContainText(/Tender document readiness/i);

	for (const label of PLC_SMOKE_UI_004_BUSINESS_LABELS) {
		await expect(
			summary.getByTestId('plc-br-business-label').filter({ hasText: label }).first(),
		).toBeVisible({ timeout: 15_000 });
	}

	await expect(summary.getByTestId('plc-br-technical-restricted')).toHaveCount(0);

	const checksRoot = summary.getByTestId('plc-br-business-checks');
	await expect(checksRoot).toBeVisible();

	const details = summary.getByTestId('plc-br-technical-collapsed');
	await expect(details).toBeVisible();
	await expect(details).not.toHaveAttribute('open');

	const body = summary.getByTestId('plc-technical-evidence-body');
	await expect(body).not.toBeVisible();

	await summary.getByTestId('plc-br-technical-summary').click({ timeout: 15_000 });
	await expect(details).toHaveAttribute('open', '');
	await expect(body).toBeVisible({ timeout: 15_000 });

	const codes = body.locator('.plc-technical-output-code');
	await expect(codes.first()).toBeVisible();
	await expect(codes.first()).toContainText(/GB-TND-MOH-2026-001-V2/);

	await summary.getByTestId('plc-br-technical-summary').click();
	await expect(details).not.toHaveAttribute('open');
	await expect(body).not.toBeVisible();
}

/** PLC-SMOKE-UI-005 / R3-016 / PLC-SMOKE-BE-004 — canonical STD outputs + snapshot (pack §15.2). */
export const PLC_SMOKE_UI_005_TECH_AND_SNAPSHOT_EXPECTATIONS: readonly string[] = [
	'GB-TND-MOH-2026-001-V2',
	'DSM-TND-MOH-2026-001-V2',
	'DOM-TND-MOH-2026-001-V2',
	'DEM-TND-MOH-2026-001-V2',
	'DCM-TND-MOH-2026-001-V2',
	'PUBSNAP-TND-MOH-2026-001-V2',
];

/**
 * R8-010 / PLC-SMOKE-UI-005 — TM2 Tender form: **`plc-technical-evidence-body`** (inside
 * **`plc-br-technical-collapsed`**) exposes every pack STD/ref token after expansion.
 *
 * Uses the shared `plc-technical-evidence-body` test-id as **`business_readiness_summary.js`**;
 * Bootstrap **`plc-technical-evidence-drawer`** remains handoff‑card JSON (**R4-013**) but is not mounted on this route.
 *
 * Preconditions: **`/app/tm2-tender/TND-MOH-2026-001`** opened; **`plc-business-readiness-summary`** hydrated.
 */
export async function expectPlcSmokeUi005Tm2ReadinessTechnicalBodyStdout(page: Page) {
	const summary = page.getByTestId('plc-business-readiness-summary');
	await expect(summary).toBeVisible({ timeout: 90_000 });

	const details = summary.getByTestId('plc-br-technical-collapsed');
	const body = summary.getByTestId('plc-technical-evidence-body');

	if (!(await body.isVisible().catch(() => false))) {
		await summary.getByTestId('plc-br-technical-summary').click({ timeout: 15_000 });
	}

	await expect(details).toHaveAttribute('open', '');
	await expect(body).toBeVisible({ timeout: 15_000 });

	for (const token of PLC_SMOKE_UI_005_TECH_AND_SNAPSHOT_EXPECTATIONS) {
		await expect(body).toContainText(token);
	}

	await summary.getByTestId('plc-br-technical-summary').click();
	await expect(details).not.toHaveAttribute('open');
	await expect(body).not.toBeVisible();
}

/**
 * R8-011 / PLC-SMOKE-UI-006 — TM2 Tender Desk form **`tm2-tender-module-journey-context`** hosts the
 * shared **`plc-module-journey-context-header`** (District Hospital Renovation WORKS journey baseline).
 *
 * Depends on **LV-R5-010-01** wiring in `tm2_tender.js`; adds stage + procuring entity checks for §15.2 wording.
 */
export async function expectPlcSmokeUi006Tm2ModuleJourneyContextHeader(page: Page) {
	const shell = page.getByTestId('tm2-tender-module-journey-context');
	await expect(shell).toBeVisible({ timeout: 45_000 });

	const header = shell.getByTestId('plc-module-journey-context-header');
	await expect(header).toBeVisible({ timeout: 45_000 });

	await expect(shell.getByTestId('plc-module-journey-context-title')).toContainText(
		/District Hospital Renovation Works/i,
		{ timeout: 45_000 },
	);
	await expect(shell.getByTestId('plc-module-journey-context-code')).toContainText('JRN-MOH-2026-001');
	await expect(shell.getByTestId('plc-module-journey-context-entity')).toContainText('PE-MOH');
	await expect(shell.getByTestId('plc-module-journey-context-stage')).toContainText(/Tender Published/i);
	await expect(shell.getByTestId('plc-module-journey-context-open')).toBeVisible();
}

/** R4-011 — Evidence timeline (`plc-evidence-timeline`, `get_journey.evidence_summary` §9.5). */
export async function expectWorksJourneyEvidenceTimeline(page: Page) {
	const section = page.getByTestId('plc-evidence-timeline');
	await expect(section).toBeVisible({ timeout: 45_000 });
	await expect(page.getByTestId('plc-evidence-timeline-title')).toContainText(/Evidence timeline/i);

	// Exclude addendum-only / TM2 audit rows (handoffs keep non-empty ``data-handoff-code`` — **R7-003**)
	const events = section.locator(
		`.plc-evidence-timeline-event[data-handoff-code]:not([data-handoff-code=""])`,
	);
	await expect(events).toHaveCount(WORKS_BASE_HANDOFF_CODES.length);

	const strat = section.locator('[data-handoff-code="STRATREF-MOH-2026-001"]').first();
	await expect(strat.getByTestId('plc-evidence-timeline-module')).toContainText(/Strategy/i);
	// ``event_type`` follows journey step label (R3-015); ``business_label`` carries handoff_title.
	await expect(strat.getByTestId('plc-evidence-timeline-event-title')).toContainText(/Strategy Priority/i);
	await expect(strat.getByTestId('plc-evidence-timeline-business-label')).toContainText(/Strategy Alignment Reference/i);

	const pub = section.locator('[data-handoff-code="PUBCERT-TND-MOH-2026-001"]').first();
	await expect(pub.getByTestId('plc-evidence-timeline-event-title')).toContainText(/Tender Published/i);
	await expect(pub.getByTestId('plc-evidence-timeline-business-label')).toContainText(/Tender Publication Certificate/i);
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
