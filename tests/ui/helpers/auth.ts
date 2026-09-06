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

/**
 * NDS-CHG-001 v1.1 §14.2 — the seeded Departmental Needs actors.
 *
 * All four are created by `departmental_needs.seeds.kentender_mvp_r1._user`,
 * which sets DEFAULT_SEED_PASSWORD on every run, so a reseed cannot silently
 * lock these specs out.
 *
 * Logging in per role is the whole point: it is the only way to exercise the
 * reviewer, withdrawal and intake screens, whose audiences never overlap. An
 * interactive browser session cannot switch between them on this site (the
 * logout endpoints return 403 and the session cookie is httpOnly), which is
 * exactly why those screens went unverified until these specs existed —
 * DEBT-06 in the Departmental Needs tracker.
 */

/** §14.2 — Departmental Author, scoped to two MoH departments (Grace Wanjiku). */
export async function loginAsDepartmentalNeedsRequester(page: Page) {
	await login(
		page,
		process.env.UI_NDS_REQUESTER_USER || 'grace.wanjiku@moh.example.test',
		process.env.UI_NDS_REQUESTER_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** §14.2 — Head of User Department (Dr Peter Kimani), the departmental checker. */
export async function loginAsDepartmentalNeedsReviewer(page: Page) {
	await login(
		page,
		process.env.UI_NDS_REVIEWER_USER || 'peter.kimani@moh.example.test',
		process.env.UI_NDS_REVIEWER_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** §14.2 / NDS-AC-042 — acting HoD (Julia Njeri): same role, narrower scope. */
export async function loginAsDepartmentalNeedsActingReviewer(page: Page) {
	await login(
		page,
		process.env.UI_NDS_ACTING_USER || 'julia.njeri@moh.example.test',
		process.env.UI_NDS_ACTING_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** §14.2 / NDS-AC-043 — Procurement Planner (Amina Hassan): intake window only. */
export async function loginAsDepartmentalNeedsPlanner(page: Page) {
	await login(
		page,
		process.env.UI_NDS_PLANNER_USER || 'amina.hassan@moh.example.test',
		process.env.UI_NDS_PLANNER_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/**
 * Playwright-owned Departmental Needs actors (DEBT-07).
 *
 * Scoped to PE-CGKIS, whose Needs the UI suite may freely decide and withdraw
 * — unlike the §14.3 demo actors above, whose fixtures the Python suite
 * asserts. Created by `departmental_needs.seeds.playwright_ui_fixtures`, which
 * sets DEFAULT_SEED_PASSWORD on every fixture rebuild.
 *
 * Each holds exactly one department (the Planner, one Procuring Entity), so
 * they resolve a single context and never meet the §12.1 picker.
 */

/** Departmental Author for the Playwright fixture entity. */
export async function loginAsNdsFixtureAuthor(page: Page) {
	await login(
		page,
		process.env.UI_NDS_PW_AUTHOR || 'nds.pw.author@example.test',
		process.env.UI_NDS_PW_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** Head of User Department for the Playwright fixture entity. */
export async function loginAsNdsFixtureReviewer(page: Page) {
	await login(
		page,
		process.env.UI_NDS_PW_REVIEWER || 'nds.pw.reviewer@example.test',
		process.env.UI_NDS_PW_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** Procurement Planner for the Playwright fixture entity. */
export async function loginAsNdsFixturePlanner(page: Page) {
	await login(
		page,
		process.env.UI_NDS_PW_PLANNER || 'nds.pw.planner@example.test',
		process.env.UI_NDS_PW_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** Contract v2.2 §7.5 — single-scope Demand Requester (Dr Miriam Njeri). */
export async function loginAsDemandRequester(page: Page) {
	await login(
		page,
		process.env.UI_DEMAND_REQUESTER_USER || 'moh.medicalservices.officer@example.test',
		process.env.UI_DEMAND_REQUESTER_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** Contract v2.2 §7.5 — multi-scope System Manager + two Requester pairs. */
export async function loginAsDemandMultiscopeAdmin(page: Page) {
	await login(
		page,
		process.env.UI_DEMAND_MULTISCOPE_USER || 'kentender.multiscope.admin@example.test',
		process.env.UI_DEMAND_MULTISCOPE_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** Contract v2.2 §7.5 — System Manager with no Demand Requester assignment. */
export async function loginAsDemandNoScopeAdmin(page: Page) {
	await login(
		page,
		process.env.UI_DEMAND_NOSCOPE_USER || 'kentender.system.admin@example.test',
		process.env.UI_DEMAND_NOSCOPE_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** Contract v2.2 §7.1 — Business Approver (James Mwangi). */
export async function loginAsBusinessApprover(page: Page) {
	await login(
		page,
		process.env.UI_BUSINESS_USER || 'moh.business.approver@example.test',
		process.env.UI_BUSINESS_PASSWORD || DEFAULT_SEED_PASSWORD,
	);
}

/** DEM-UI-05 — Procurement Approval Authority (Amina Otieno). */
export async function loginAsProcurementApprover(page: Page) {
	await login(
		page,
		process.env.UI_PROCUREMENT_APPROVER_USER || 'moh.procurement.approver@example.test',
		process.env.UI_PROCUREMENT_APPROVER_PASSWORD || DEFAULT_SEED_PASSWORD,
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

/** Supplier portal (Phase O) — user must be linked to ``KTSM Supplier Profile.external_user``. */
export async function loginAsSupplierPortalUser(page: Page) {
	const user = process.env.UI_SUPPLIER_PORTAL_USER || '';
	const password = process.env.UI_SUPPLIER_PORTAL_PASSWORD || DEFAULT_SEED_PASSWORD;
	if (!user) {
		throw new Error('UI_SUPPLIER_PORTAL_USER is not set');
	}
	await login(page, user, password);
}
