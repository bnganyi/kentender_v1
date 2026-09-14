// Live data adapter for the Strategy Alignment page — STR-UI-01..04 read
// contracts (kentender_strategy.api.strategy_ui_api) and the §8 command
// contracts (kentender_strategy.api.strategy_consumer_api). Every write
// carries the attempt's idempotency key (§8.2, plan D6).
import { frappeCall as call } from "../../strategy_shared/data/frappeCall.js";

// --- STR-UI-01 Strategic plans ---------------------------------------------

export const fetchPortfolio = (filters) =>
	call("kentender_strategy.api.strategy_ui_api.get_strategy_portfolio", {
		search: (filters && filters.search) || "",
		plan_role: (filters && filters.plan_role) || "",
		status: (filters && filters.status) || "",
	});

// --- STR-UI-02 / STR-UI-03 Plan workspace + structure editor ---------------

export const getPlanWorkspace = (planId, versionNumber) =>
	call("kentender_strategy.api.strategy_ui_api.get_plan_workspace", {
		plan_id: planId,
		version_number: versionNumber || null,
	});

export const savePlanDraft = (payload, expectedVersion, idempotencyKey) =>
	call("kentender_strategy.api.strategy_consumer_api.save_strategy_plan_draft", {
		payload,
		expected_version: expectedVersion || null,
		idempotency_key: idempotencyKey || null,
	});

export const getVersionHistory = (planVersionId) =>
	call("kentender_strategy.api.strategy_ui_api.get_version_history", { plan_version_id: planVersionId });

export const getStrategyTree = (planVersionId) =>
	call("kentender_strategy.api.strategy_ui_api.get_strategy_tree", { plan_version_id: planVersionId });

// §12.3 — only ERPNext Fiscal Years overlapping the plan period are offered.
export const getFiscalYears = (planId) =>
	call("kentender_strategy.api.strategy_ui_api.list_available_fiscal_years", { plan_id: planId });

// Performance Indicator.unit is a plain Data field (STR-CHG-001 §4.4 names no
// catalogue, and §4.7 does not assume the UOM catalogue carries Percentage),
// so this offers the distinct values already in use as suggestions.
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

export const saveStructureDraft = (planVersionId, { nodes, indicators, targets, deletes, expectedVersion }, idempotencyKey) =>
	call("kentender_strategy.api.strategy_consumer_api.save_strategy_structure_draft", {
		plan_version_id: planVersionId,
		nodes: nodes || [],
		indicators: indicators || [],
		targets: targets || [],
		deletes: deletes || [],
		expected_version: expectedVersion || null,
		idempotency_key: idempotencyKey || null,
	});

export const submitVersion = (planVersionId, expectedVersion, idempotencyKey) =>
	call("kentender_strategy.api.strategy_consumer_api.submit_strategy_version", {
		plan_version_id: planVersionId,
		expected_version: expectedVersion || null,
		idempotency_key: idempotencyKey || null,
	});

export const createSuccessorVersion = (planId, idempotencyKey) =>
	call("kentender_strategy.api.strategy_consumer_api.create_strategy_successor_version", {
		plan_id: planId,
		idempotency_key: idempotencyKey || null,
	});

// --- STR-UI-04 Approval task -------------------------------------------------

export const getVersionReviewOverview = (planVersionId) =>
	call("kentender_strategy.api.strategy_ui_api.get_version_review_overview", { plan_version_id: planVersionId });

export const diffStrategyVersions = (compareVersionId, baseVersionId) =>
	call("kentender_strategy.api.strategy_ui_api.diff_strategy_versions", {
		compare_version_id: compareVersionId,
		base_version_id: baseVersionId || null,
	});

export const returnVersion = (planVersionId, reason, expectedVersion, idempotencyKey) =>
	call("kentender_strategy.api.strategy_consumer_api.return_strategy_version", {
		plan_version_id: planVersionId,
		reason,
		expected_version: expectedVersion || null,
		idempotency_key: idempotencyKey || null,
	});

export const approveVersion = (planVersionId, expectedVersion, idempotencyKey) =>
	call("kentender_strategy.api.strategy_consumer_api.approve_strategy_version", {
		plan_version_id: planVersionId,
		expected_version: expectedVersion || null,
		idempotency_key: idempotencyKey || null,
	});
