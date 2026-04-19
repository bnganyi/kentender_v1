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
	route: '/app/budget-management',
	appPath: '/app/budget-management',
};

export const procurementWorkspace = {
	heading: 'Procurement',
	route: '/app/procurement',
	appPath: '/app/procurement',
};