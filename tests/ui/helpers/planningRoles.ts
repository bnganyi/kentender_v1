/**
 * Contract v2.4 §4.6 Planning personas — login helpers for Gate 03+ UI.
 * Service tests are the Done gate for PLN-PERM; these unblock Stitch Playwright.
 */
import { Page } from '@playwright/test';
import { login } from './auth';

/** Shared seed password — see kentender_core.seeds.constants.TEST_PASSWORD. */
const DEFAULT_SEED_PASSWORD = process.env.UI_SEED_PASSWORD || 'Test@123';

export const PLANNING_USERS = {
	planner: process.env.UI_PLN_PLANNER_USER || 'moh.planning.officer@example.test',
	reviewer: process.env.UI_PLN_REVIEWER_USER || 'moh.planning.reviewer@example.test',
	accountingOfficer:
		process.env.UI_PLN_AO_USER || 'moh.accounting.officer@example.test',
	designatedApprover:
		process.env.UI_PLN_APPROVER_USER || 'moh.plan.approver@example.test',
	tenderInitiator:
		process.env.UI_PLN_TENDER_INITIATOR_USER || 'moh.tender.initiator@example.test',
	countyPlanner:
		process.env.UI_PLN_COUNTY_PLANNER_USER || 'kisumu.planning.officer@example.test',
	systemAdminNoScope:
		process.env.UI_PLN_SYSADMIN_USER || 'kentender.system.admin@example.test',
	/** Ensured by prepare_planning_gate03_ui — dual PE Planning USA. */
	multiPlanner: process.env.UI_PLN_MULTI_USER || 'pln.ui.multi@example.test',
	viewer: process.env.UI_PLN_VIEWER_USER || 'pln.ui.viewer@example.test',
} as const;

export type PlanningGate03Prep = {
	ok?: boolean;
	empty_draft_plan?: string;
	empty_draft_fy?: string;
	builder_route?: string;
	multi_planner?: string;
	create_fy?: string;
	pe_moh?: string;
};

/** Admin-only prepare for Gate 03 Playwright fixtures. */
export async function preparePlanningGate03(
	page: Page,
): Promise<PlanningGate03Prep> {
	await page.goto('/desk', { waitUntil: 'domcontentloaded' });
	const message = await page.evaluate(async () => {
		const r = await (
			window as unknown as {
				frappe: {
					call: (o: { method: string }) => Promise<{ message?: PlanningGate03Prep }>;
				};
			}
		).frappe.call({
			method: 'kentender_procurement.procurement_planning.api.prepare_planning_gate03_ui',
		});
		return r.message || {};
	});
	return message;
}

export type PlanningGate04Prep = PlanningGate03Prep & {
	eligible_demand?: string;
	eligible_demand_code?: string;
	need_item_count?: number;
	plan_item?: string;
	editor_route?: string;
	plan_item_code?: string;
};

export type PlanningGate05Prep = PlanningGate04Prep & {
	hod_user?: string;
	ready_for_submit?: boolean;
};

export type PlanningGate05ApprovalPrep = PlanningGate05Prep & {
	reviewer_user?: string;
	approver_user?: string;
	version?: string;
	review_route?: string;
	ready_for_approval?: boolean;
};

/** Admin-only prepare for Gate 04 Playwright fixtures. */
export async function preparePlanningGate04(
	page: Page,
	opts?: { withPlanItem?: boolean; needItemCount?: number },
): Promise<PlanningGate04Prep> {
	await page.goto('/desk', { waitUntil: 'domcontentloaded' });
	const withPlanItem = opts?.withPlanItem ? 1 : 0;
	const needItemCount = Math.max(1, opts?.needItemCount ?? 1);
	const message = await page.evaluate(
		async ({ withItem, needCount }: { withItem: number; needCount: number }) => {
			const r = await (
				window as unknown as {
					frappe: {
						call: (o: {
							method: string;
							args?: Record<string, unknown>;
						}) => Promise<{ message?: PlanningGate04Prep }>;
					};
				}
			).frappe.call({
				method: 'kentender_procurement.procurement_planning.api.prepare_planning_gate04_ui',
				args: { with_plan_item: withItem, need_item_count: needCount },
			});
			return r.message || {};
		},
		{ withItem: withPlanItem, needCount: needItemCount },
	);
	return message;
}

/** Admin-only prepare for Ready Plan Item (C02: no contribution). */
export async function preparePlanningGate05(page: Page): Promise<PlanningGate05Prep> {
	await page.goto('/desk', { waitUntil: 'domcontentloaded' });
	const message = await page.evaluate(async () => {
		const r = await (
			window as unknown as {
				frappe: {
					call: (o: { method: string }) => Promise<{ message?: PlanningGate05Prep }>;
				};
			}
		).frappe.call({
			method: 'kentender_procurement.procurement_planning.api.prepare_planning_gate05_ui',
		});
		return r.message || {};
	});
	return message;
}

/** Admin-only prepare for PLN-UI-08 review/approval (In review + recommended). */
export async function preparePlanningGate05Approval(
	page: Page,
): Promise<PlanningGate05ApprovalPrep> {
	await page.goto('/desk', { waitUntil: 'domcontentloaded' });
	const message = await page.evaluate(async () => {
		const r = await (
			window as unknown as {
				frappe: {
					call: (o: {
						method: string;
					}) => Promise<{ message?: PlanningGate05ApprovalPrep }>;
				};
			}
		).frappe.call({
			method:
				'kentender_procurement.procurement_planning.api.prepare_planning_gate05_approval_ui',
		});
		return r.message || {};
	});
	return message;
}

async function loginPlanning(page: Page, email: string, passwordEnv?: string) {
	await login(page, email, passwordEnv || DEFAULT_SEED_PASSWORD);
}

export async function loginAsMohPlanningOfficer(page: Page) {
	await loginPlanning(page, PLANNING_USERS.planner, process.env.UI_PLN_PLANNER_PASSWORD);
}

export async function loginAsMohHod(page: Page, hodEmail?: string) {
	await loginPlanning(
		page,
		hodEmail || process.env.UI_PLN_HOD_USER || 'moh.hod.dhp@example.test',
		process.env.UI_PLN_HOD_PASSWORD,
	);
}

export async function loginAsMohPlanningReviewer(page: Page) {
	await loginPlanning(page, PLANNING_USERS.reviewer, process.env.UI_PLN_REVIEWER_PASSWORD);
}

export async function loginAsMohAccountingOfficer(page: Page) {
	await loginPlanning(
		page,
		PLANNING_USERS.accountingOfficer,
		process.env.UI_PLN_AO_PASSWORD,
	);
}

export async function loginAsMohPlanApprover(page: Page) {
	await loginPlanning(
		page,
		PLANNING_USERS.designatedApprover,
		process.env.UI_PLN_APPROVER_PASSWORD,
	);
}

export async function loginAsMohTenderInitiator(page: Page) {
	await loginPlanning(
		page,
		PLANNING_USERS.tenderInitiator,
		process.env.UI_PLN_TENDER_INITIATOR_PASSWORD,
	);
}

export async function loginAsCountyPlanningOfficer(page: Page) {
	await loginPlanning(
		page,
		PLANNING_USERS.countyPlanner,
		process.env.UI_PLN_COUNTY_PLANNER_PASSWORD,
	);
}

/** Admin without Planning operational USA — PLN-AC-019 / PLN-PERM-004. */
export async function loginAsPlanningSystemAdminNoScope(page: Page) {
	await loginPlanning(
		page,
		PLANNING_USERS.systemAdminNoScope,
		process.env.UI_PLN_SYSADMIN_PASSWORD,
	);
}

/** Planning Viewer (record visibility; no review task) — ensured by Gate 05 approval prep. */
export async function loginAsMohPlanningViewer(page: Page) {
	await loginPlanning(
		page,
		PLANNING_USERS.viewer,
		process.env.UI_PLN_VIEWER_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** Dual-PE Procurement Planner (created by prepare_planning_gate03_ui). */
export async function loginAsPlanningMultiPlanner(page: Page) {
	await loginPlanning(
		page,
		PLANNING_USERS.multiPlanner,
		process.env.UI_PLN_MULTI_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}
