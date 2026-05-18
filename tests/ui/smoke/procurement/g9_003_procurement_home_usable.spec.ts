/**
 * §14 G9-003 — Procurement Home shows active journeys with current stage, next action, blockers,
 * and primary navigation (**Open Journey**).
 *
 * Depends on WORKS master seed (`JRN-MOH-2026-001`) so **`list_journeys`** returns at least one active row.
 */
import { test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	expectG9ProcurementHomeUsable,
	openProcurementWorkspaceFromModule,
	procurementHomeWorkspace,
} from '../../helpers/procurement';

const WORKS_JOURNEY_TITLE = 'District Hospital Renovation Works';

test.describe('G9-003 Procurement Home usability', () => {
	test('G9-003: Active Procurement Journeys panel lists journeys with next actions', async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expectG9ProcurementHomeUsable(page, WORKS_JOURNEY_TITLE);
	});
});
