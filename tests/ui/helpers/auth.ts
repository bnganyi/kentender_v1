import { Page } from '@playwright/test';

export async function login(page: Page, username: string, password: string) {
	await page.goto('/login', { waitUntil: 'domcontentloaded' });
	// Frappe login uses sr-only labels; prefer stable ids (see frappe/www/login.html).
	const email = page.locator('#login_email');
	try {
		await email.waitFor({ state: 'visible', timeout: 30_000 });
	} catch {
		// Stale session can land on Desk without the login form; reset cookies and retry.
		await page.context().clearCookies();
		await page.goto('/login', { waitUntil: 'domcontentloaded' });
		await email.waitFor({ state: 'visible', timeout: 30_000 });
	}
	await email.fill(username);
	await page.locator('#login_password').fill(password);
	// Exact "Login" — avoid matching Frappe's "Invalid Login. Try again." button (/login/i would match).
	await page.getByRole('button', { name: 'Login', exact: true }).click();

	const outcome = await Promise.race([
		page.getByText(/Invalid Login/i).waitFor({ state: 'visible', timeout: 60_000 }).then(() => 'invalid' as const),
		// Website/System Settings app_name is KenTender (was Frappe/ERPNext on older sites).
		page
			.getByRole('heading', { name: /Login to (KenTender|Frappe|ERPNext)/i })
			.waitFor({ state: 'hidden', timeout: 60_000 })
			.then(() => 'ok' as const),
		page.waitForURL(/\/desk(\/|$)/, { timeout: 60_000 }).then(() => 'ok' as const),
	]);

	if (outcome === 'invalid') {
		throw new Error(
			'Login failed (Invalid Login). Set UI_ADMIN_USER / UI_ADMIN_PASSWORD in apps/kentender_v1/.env.ui to match the target site.',
		);
	}

	await page.waitForLoadState('domcontentloaded');
}

/** Wave 0 smoke: use a user that exists on the target site (see `.env.ui`). */
export async function loginAsAdministrator(page: Page) {
	await login(
		page,
		process.env.UI_ADMIN_USER || 'Administrator',
		process.env.UI_ADMIN_PASSWORD || 'Sn00per56*',
	);
}

/** Default seeded KenTender v1 password (see kentender_core.seeds.constants.TEST_PASSWORD). */
const DEFAULT_SEED_PASSWORD = 'Test@123';

export async function loginAsStrategyManager(page: Page) {
	await login(
		page,
		process.env.UI_STRATEGY_USER || 'strategy.manager@moh.test',
		process.env.UI_STRATEGY_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** STR-SUP-005 — Strategy Viewer (see strategy_role_users seed). */
export async function loginAsStrategyViewer(page: Page) {
	await login(
		page,
		process.env.UI_STRATEGY_VIEWER_USER || 'strategy.viewer@moh.test',
		process.env.UI_STRATEGY_VIEWER_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** STR-SUP-005 — Strategy Officer (MOH). */
export async function loginAsStrategyOfficer(page: Page) {
	await login(
		page,
		process.env.UI_STRATEGY_OFFICER_USER || 'strategy.officer@moh.test',
		process.env.UI_STRATEGY_OFFICER_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** STR-SUP-005 — Strategy Viewer on OTHER PE (MOE). */
export async function loginAsStrategyViewerOtherPe(page: Page) {
	await login(
		page,
		process.env.UI_STRATEGY_VIEWER_OTHER_PE_USER || 'strategy.viewer@moe.test',
		process.env.UI_STRATEGY_VIEWER_OTHER_PE_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

export async function loginAsPlanningAuthority(page: Page) {
	await login(
		page,
		process.env.UI_PLANNING_USER || 'planning.authority@moh.test',
		process.env.UI_PLANNING_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

export async function loginAsRequisitioner(page: Page) {
	await login(
		page,
		process.env.UI_REQUISITIONER_USER || 'requisitioner@moh.test',
		process.env.UI_REQUISITIONER_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** Department Approver (HoD) — see `kentender_core.seeds.constants.SEED_USERS`. */
export async function loginAsHoDApprover(page: Page) {
	await login(
		page,
		process.env.UI_HOD_USER || 'hod.approver@moh.test',
		process.env.UI_HOD_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

export async function loginAsFinanceReviewer(page: Page) {
	await login(
		page,
		process.env.UI_FINANCE_USER || 'finance.reviewer@moh.test',
		process.env.UI_FINANCE_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

export async function loginAsProcurementPlanner(page: Page) {
	await login(
		page,
		process.env.UI_PLANNER_USER || 'planner@moh.test',
		process.env.UI_PLANNER_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

export async function loginAsPlanningReviewer(page: Page) {
	await login(
		page,
		process.env.UI_PLANNING_REVIEWER_USER || 'planning.reviewer@moh.test',
		process.env.UI_PLANNING_REVIEWER_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** Procurement Officer — `kentender_core.seeds.constants.SEED_USERS` (seed_core_minimal). */
export async function loginAsProcurementOfficer(page: Page) {
	await login(
		page,
		process.env.UI_PROCUREMENT_OFFICER_USER || 'procurement.officer@moh.test',
		process.env.UI_PROCUREMENT_OFFICER_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

export async function loginAsAuditor(page: Page) {
	await login(
		page,
		process.env.UI_AUDITOR_USER || 'auditor@moh.test',
		process.env.UI_AUDITOR_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** BUD-SUP-002 — Budget Viewer (PE-MOH). */
export async function loginAsBudgetViewer(page: Page) {
	await login(
		page,
		process.env.UI_BUDGET_VIEWER_USER || 'budget.viewer@moh.test',
		process.env.UI_BUDGET_VIEWER_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** BUD-SUP-002 — Budget Officer (PE-MOH). */
export async function loginAsBudgetOfficer(page: Page) {
	await login(
		page,
		process.env.UI_BUDGET_OFFICER_USER || 'budget.officer@moh.test',
		process.env.UI_BUDGET_OFFICER_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** BUD-SUP-002 — Budget Reviewer (PE-MOH). */
export async function loginAsBudgetReviewer(page: Page) {
	await login(
		page,
		process.env.UI_BUDGET_REVIEWER_USER || 'budget.reviewer@moh.test',
		process.env.UI_BUDGET_REVIEWER_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** BUD-SUP-002 — Budget Authority (PE-MOH). */
export async function loginAsBudgetAuthority(page: Page) {
	await login(
		page,
		process.env.UI_BUDGET_AUTHORITY_USER || 'budget.authority@moh.test',
		process.env.UI_BUDGET_AUTHORITY_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** BUD-SUP-002 — dual Officer+Authority for AC-018 SoD (PE-MOH). */
export async function loginAsBudgetOfficerAuthority(page: Page) {
	await login(
		page,
		process.env.UI_BUDGET_OFFICER_AUTHORITY_USER || 'budget.officer.authority@moh.test',
		process.env.UI_BUDGET_OFFICER_AUTHORITY_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** BUD-SUP-002 — Budget Officer scoped to PE-MOE (cross-entity denial vs PE-MOH). */
export async function loginAsBudgetOtherEntity(page: Page) {
	await login(
		page,
		process.env.UI_BUDGET_OTHER_ENTITY_USER || 'budget.officer@moe.test',
		process.env.UI_BUDGET_OTHER_ENTITY_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** Supplier portal (Phase O) — user must be linked to ``KTSM Supplier Profile.external_user``. */
export async function loginAsSupplierPortalUser(page: Page) {
	const user = process.env.UI_SUPPLIER_PORTAL_USER || '';
	const password = process.env.UI_SUPPLIER_PORTAL_PASSWORD || DEFAULT_SEED_PASSWORD;
	if (!user) {
		throw new Error('UI_SUPPLIER_PORTAL_USER is not set');
	}
	await login(page, user, password);
}
