// Live data adapter for STR-UI-02 (Plan workspace) / STR-UI-03 (Structure editor).
import { frappeCall as call } from "../../strategy_shared/data/frappeCall.js";

// Performance Target.financial_year_id links to ERPNext's own "Fiscal Year"
// (CU-305 repointed the field's Link options there), not the KenTender
// "Financial Year" doctype STR-CHG-001 v1.6 §1.1 disposes of — the original
// version of this queried the latter, populating the select with names
// ("FY-2027-2028") the Link target doesn't recognise ("Could not find
// Financial Year: FY-2027-2028"; real values look like "2027-2028").
// Querying "Fiscal Year" directly via frappe.client.get_list is *also*
// wrong: ERPNext scopes its read permission to accounting roles a Strategy
// Author doesn't hold (403 Insufficient Permission). Go through Strategy's
// own read contract instead — §3 assigns Strategy read access to the
// catalogue, not raw table permission on it.
export const getFinancialYears = () => call("kentender_strategy.api.strategy_ui_api.list_available_fiscal_years", {});

// Performance Indicator.unit is a plain Data field (STR-CHG-001 v1.6 §4.4
// names no catalogue), so this offers the distinct values already in use
// across every plan as select options — letting an author pick a
// consistent existing unit or type a genuinely new one, rather than
// retyping "Percentage"/"percent"/"%" by hand each time.
const COMMON_UNITS = ["Percentage", "Count", "Rate per 100,000 population", "Rate per 1,000 population", "Days", "Ratio"];
export const getIndicatorUnits = () =>
	call("frappe.client.get_list", {
		doctype: "Performance Indicator",
		fields: ["unit"],
		group_by: "unit",
		filters: { unit: ["not in", ["", null]] },
		limit_page_length: 0,
		order_by: "unit asc",
	}).then((rows) => {
		const used = (rows || []).map((row) => row.unit).filter(Boolean);
		return [...new Set([...COMMON_UNITS, ...used])].sort((a, b) => a.localeCompare(b));
	});

export const getPlanWorkspace = (planId) =>
	call("kentender_strategy.api.strategy_ui_api.get_plan_workspace", { plan_id: planId });

export const getPlanHistory = (planId) =>
	call("kentender_strategy.api.strategy_ui_api.get_plan_history", { plan_id: planId });

export const getVersionHistory = (planVersionId) =>
	call("kentender_strategy.api.strategy_ui_api.get_version_history", { plan_version_id: planVersionId });

export const getStrategyTree = (planVersionId) =>
	call("kentender_strategy.api.strategy_ui_api.get_strategy_tree", { plan_version_id: planVersionId });

export const saveStructureDraft = (planVersionId, { nodes, indicators, targets, deletes, expectedVersion }) =>
	call("kentender_strategy.api.strategy_consumer_api.save_strategy_structure_draft", {
		plan_version_id: planVersionId,
		nodes: nodes || [],
		indicators: indicators || [],
		targets: targets || [],
		deletes: deletes || [],
		expected_version: expectedVersion || null,
	});

export const submitVersion = (planVersionId) =>
	call("kentender_strategy.api.strategy_consumer_api.submit_strategy_version", {
		plan_version_id: planVersionId,
	});

export const createSuccessorVersion = (planId) =>
	call("kentender_strategy.api.strategy_consumer_api.create_strategy_successor_version", {
		plan_id: planId,
	});
