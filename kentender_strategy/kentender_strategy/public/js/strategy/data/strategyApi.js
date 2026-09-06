// Live data adapter for the Strategy Alignment page — STR-UI-01..04 read
// contracts (kentender_strategy.api.strategy_ui_api) and the §8 command
// contracts (kentender_strategy.api.strategy_consumer_api).
import { frappeCall as call } from "../../strategy_shared/data/frappeCall.js";

// --- STR-UI-01 Portfolio -----------------------------------------------------

export const fetchPortfolio = (filters) =>
	call("kentender_strategy.api.strategy_ui_api.get_strategy_portfolio", {
		search: (filters && filters.search) || "",
		plan_role: (filters && filters.plan_role) || "",
		status: (filters && filters.status) || "",
	});

export const saveNewPlanDraft = (payload) =>
	call("kentender_strategy.api.strategy_consumer_api.save_strategy_plan_draft", { payload });

// --- STR-UI-02 / STR-UI-03 Plan workspace + structure editor -----------------

export const getPlanWorkspace = (planId) =>
	call("kentender_strategy.api.strategy_ui_api.get_plan_workspace", { plan_id: planId });

export const savePlanDraft = (payload, expectedVersion) =>
	call("kentender_strategy.api.strategy_consumer_api.save_strategy_plan_draft", {
		payload,
		expected_version: expectedVersion || null,
	});

export const getVersionHistory = (planVersionId) =>
	call("kentender_strategy.api.strategy_ui_api.get_version_history", { plan_version_id: planVersionId });

export const getStrategyTree = (planVersionId) =>
	call("kentender_strategy.api.strategy_ui_api.get_strategy_tree", { plan_version_id: planVersionId });

// §12.3 — only ERPNext Fiscal Years overlapping the plan period are offered.
export const getFiscalYears = (planId) =>
	call("kentender_strategy.api.strategy_ui_api.list_available_fiscal_years", { plan_id: planId });

// Performance Indicator.unit is a plain Data field (STR-CHG-001 §4.4 names no
// catalogue), so this offers the distinct values already in use across every
// plan as suggestions — an author picks a consistent existing unit or types a
// genuinely new one.
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

export const saveStructureDraft = (planVersionId, { nodes, indicators, targets, deletes, expectedVersion }) =>
	call("kentender_strategy.api.strategy_consumer_api.save_strategy_structure_draft", {
		plan_version_id: planVersionId,
		nodes: nodes || [],
		indicators: indicators || [],
		targets: targets || [],
		deletes: deletes || [],
		expected_version: expectedVersion || null,
	});

export const submitVersion = (planVersionId, expectedVersion) =>
	call("kentender_strategy.api.strategy_consumer_api.submit_strategy_version", {
		plan_version_id: planVersionId,
		expected_version: expectedVersion || null,
	});

export const createSuccessorVersion = (planId) =>
	call("kentender_strategy.api.strategy_consumer_api.create_strategy_successor_version", {
		plan_id: planId,
	});

// --- STR-UI-04 Approval task -------------------------------------------------

export const getVersionReviewOverview = (planVersionId) =>
	call("kentender_strategy.api.strategy_ui_api.get_version_review_overview", { plan_version_id: planVersionId });

export const diffStrategyVersions = (compareVersionId, baseVersionId) =>
	call("kentender_strategy.api.strategy_ui_api.diff_strategy_versions", {
		compare_version_id: compareVersionId,
		base_version_id: baseVersionId || null,
	});

export const returnVersion = (planVersionId, reason, expectedVersion) =>
	call("kentender_strategy.api.strategy_consumer_api.return_strategy_version", {
		plan_version_id: planVersionId,
		reason,
		expected_version: expectedVersion || null,
	});

export const approveVersion = (planVersionId, expectedVersion) =>
	call("kentender_strategy.api.strategy_consumer_api.approve_strategy_version", {
		plan_version_id: planVersionId,
		expected_version: expectedVersion || null,
	});
