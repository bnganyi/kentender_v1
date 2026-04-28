/** Module / Desktop Icon label (opens Workspace Sidebar). */
export const strategyModule = 'Strategy';
export const budgetModule = 'Budget';
export const procurementModule = 'Procurement';

export const strategyWorkspace = {
	heading: 'Strategy Management',
	/** Frappe Desk resolves workspaces under `/desk/<slug>` (pathname must include `strategy-management` for client binding). */
	route: '/desk/strategy-management',
	/** Matches workspace intro paragraph (Wave 1 shell). */
	placeholderBlurb: 'Create and manage strategic plans',
	appPath: '/desk/strategy-management',
};

export const budgetWorkspace = {
	heading: 'Budget Management',
	/** Desk resolves workspaces under `/desk/<slug>` or `/app/<slug>` depending on build. */
	route: '/desk/budget-management',
	placeholderBlurb: 'Create and manage budget allocations aligned to strategic plans.',
	appPath: '/desk/budget-management',
};

/** Default workspace under the Procurement module tile (see `procurement_home` Workspace). */
export const procurementWorkspace = {
	heading: 'Procurement Home',
	route: '/desk/procurement-home',
	appPath: '/desk/procurement-home',
};

/**
 * Demand Intake and Approval (DIA). Do not `page.goto` a path for this screen — Frappe can treat
 * `/app/...` or `/desk/...` as a legacy `Page` and 404. Use `openDIALanding` / `navigateToDiaWorkspace`.
 */
export const diaWorkspace = {
	heading: 'Demand Intake and Approval',
	introSnippet: 'Capture, approve, and prepare procurement demand',
};