// Live data adapter for STR-UI-02 (Plan workspace) / STR-UI-03 (Structure editor).
import { frappeCall as call } from "../../strategy_shared/data/frappeCall.js";

export const getFinancialYears = () =>
	call("frappe.client.get_list", {
		doctype: "Financial Year",
		fields: ["name"],
		limit_page_length: 0,
		order_by: "name desc",
	}).then((rows) => (rows || []).map((row) => row.name));

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

export const activateVersion = (planVersionId) =>
	call("kentender_strategy.api.strategy_consumer_api.activate_strategy_version", {
		plan_version_id: planVersionId,
	});

export const createSuccessorVersion = (planId) =>
	call("kentender_strategy.api.strategy_consumer_api.create_strategy_successor_version", {
		plan_id: planId,
	});
