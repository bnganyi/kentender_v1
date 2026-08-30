// Procurement Planning data adapter (PLN-CHG-001 v1.2 §8).
import { frappeCall } from "../../pln_shared/frappeCall.js";

const BASE = "kentender_procurement.procurement_planning.api";

export function newIdempotencyKey(action) {
	const rand =
		(crypto.randomUUID && crypto.randomUUID()) ||
		`${Date.now()}-${Math.random().toString(16).slice(2)}`;
	return `pln-${action}-${rand}`;
}

export function getPlanningWorkspace(args) {
	return frappeCall(`${BASE}.get_planning_workspace`, args || {});
}

export function selectPlanningContext(args) {
	return frappeCall(`${BASE}.select_planning_context`, args);
}

export function openDepartmentalPlan(args) {
	return frappeCall(`${BASE}.open_departmental_plan`, args);
}
