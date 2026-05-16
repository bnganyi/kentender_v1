/**
 * Desk module tile labels (`Desktop Icon` name / `data-id`) and workspace routes
 * for launcher + sidebar navigation helpers.
 */
import { workspaceAppPath } from './routes';

export const procurementModule = 'Procurement';
export const budgetModule = 'Budget';
export const strategyModule = 'Strategy';

export const strategyWorkspace = {
	heading: 'Strategy Management',
	route: workspaceAppPath('Strategy Management'),
	/** Visible copy on the Strategy workspace shell (see workspace-shell / workspace-clickability specs). */
	placeholderBlurb: 'Strategic Plan',
};

export const budgetWorkspace = {
	heading: 'Budget Management',
	route: workspaceAppPath('Budget Management'),
};

export const procurementWorkspace = {
	heading: 'Procurement Home',
	route: workspaceAppPath('Procurement Home'),
};

/** DIA injected workbench (see `Demand Intake and Approval` workspace). */
export const diaWorkspace = {
	heading: 'Demand Intake and Approval',
	route: workspaceAppPath('Demand Intake and Approval'),
};
