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

async function loginPlanning(page: Page, email: string, passwordEnv?: string) {
	await login(page, email, passwordEnv || DEFAULT_SEED_PASSWORD);
}

export async function loginAsMohPlanningOfficer(page: Page) {
	await loginPlanning(page, PLANNING_USERS.planner, process.env.UI_PLN_PLANNER_PASSWORD);
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

/** Dual-PE Procurement Planner (created by prepare_planning_gate03_ui). */
export async function loginAsPlanningMultiPlanner(page: Page) {
	await loginPlanning(
		page,
		PLANNING_USERS.multiPlanner,
		process.env.UI_PLN_MULTI_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}
