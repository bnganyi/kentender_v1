/** Shared Desk module / workspace selectors for Playwright smoke tests. */

export type ModuleSelector = {
	label: string;
};

export type WorkspaceSelector = {
	route: string;
	heading: string;
};

export const strategyModule: ModuleSelector = { label: 'Strategy' };
export const budgetModule: ModuleSelector = { label: 'Budget' };
export const procurementModule: ModuleSelector = { label: 'Procurement' };

export const strategyWorkspace: WorkspaceSelector = {
	route: '/app/strategy-management',
	heading: 'Strategy Management',
};

export const budgetWorkspace: WorkspaceSelector = {
	route: '/app/budget-management',
	heading: 'Budget Management',
};

export const procurementWorkspace: WorkspaceSelector = {
	route: '/app/procurement-home',
	heading: 'Procurement Home',
};

export const diaWorkspace: WorkspaceSelector = {
	route: '/app/demand-intake-and-approval',
	heading: 'Demand Intake and Approval',
};
