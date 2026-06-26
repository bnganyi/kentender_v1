/** P5C-013 — Approved Demand Include-in-Plan modal. */
(function () {
	frappe.provide("kentender_procurement");

	const INCLUDE_DEMAND_API =
		"kentender_procurement.procurement_planning.api.approved_demands.include_pp_demand_in_procurement_plan";
	const PLAN_SEARCH_QUERY =
		"kentender_procurement.procurement_planning.api.reference_search.search_procurement_plan";

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function normalizeCodes(rawCodes) {
		if (!Array.isArray(rawCodes)) return [];
		const out = [];
		for (let i = 0; i < rawCodes.length; i += 1) {
			const code = String(rawCodes[i] || "").trim();
			if (!code) continue;
			out.push(code);
		}
		return out;
	}

	function blockedMessage(opts) {
		const o = opts || {};
		const label = String(o.blocker_message || "").trim();
		if (label) return label;
		return __("Resolve blockers before including this demand in a procurement plan.");
	}

	function hasTechnicalLeakage(message) {
		const value = String(message || "").trim();
		if (!value) return false;
		return /PLANINCL-|PKGREL-|PKGCONSUME-|source object|target object|technical refs|source_object_code|target_object_code|technical_refs_json|locked_summary_json|passed_forward_summary_json|audit_event_ref/i.test(
			value
		);
	}

	function safeIncludeFailureMessage(rawMessage) {
		const value = String(rawMessage || "").trim();
		if (!value || hasTechnicalLeakage(value)) {
			return __("The demand could not be included in the selected plan.");
		}
		return value;
	}

	function businessContextHtml(opts) {
		const o = opts || {};
		const demandLabel = String(o.demand_name || o.demand_code || "").trim() || "—";
		const valueLabel = String(o.value_label || "").trim() || "—";
		const fundingLabel = String(o.funding_label || "").trim() || "—";
		const activePlanLabel = String(o.target_plan_name || o.target_plan_label || "").trim();
		let html =
			'<div class="pp2-include-plan-modal__context" data-testid="pp2-include-plan-modal">' +
			'<div class="pp2-include-plan-modal__context-row"><span class="text-muted small">' +
			esc(__("Demand")) +
			'</span><div class="small" data-testid="pp2-include-plan-demand">' +
			esc(demandLabel) +
			"</div></div>" +
			'<div class="pp2-include-plan-modal__context-row"><span class="text-muted small">' +
			esc(__("Value")) +
			'</span><div class="small" data-testid="pp2-include-plan-value">' +
			esc(valueLabel) +
			"</div></div>" +
			'<div class="pp2-include-plan-modal__context-row"><span class="text-muted small">' +
			esc(__("Funding")) +
			'</span><div class="small" data-testid="pp2-include-plan-funding">' +
			esc(fundingLabel) +
			"</div></div>";
		if (activePlanLabel) {
			html +=
				'<div class="pp2-include-plan-modal__context-row"><span class="text-muted small">' +
				esc(__("Active plan")) +
				'</span><div class="small" data-testid="pp2-include-plan-active-plan">' +
				esc(activePlanLabel) +
				"</div></div>";
		}
		html += "</div>";
		return html;
	}

	function buildIncludePlanDialogFields(opts) {
		const o = opts || {};
		const locked = o.target_plan_locked === true;
		const fields = [
			{
				fieldtype: "HTML",
				fieldname: "context",
				options: businessContextHtml(o),
			},
		];
		if (!locked) {
			fields.push({
				fieldtype: "Link",
				fieldname: "target_plan",
				label: __("Target plan"),
				options: "Procurement Plan",
				reqd: 0,
				get_query: function () {
					return {
						query: PLAN_SEARCH_QUERY,
					};
				},
			});
		}
		fields.push({
			fieldtype: "Data",
			fieldname: "target_plan_fallback",
			hidden: 1,
			default: String(o.target_plan_code || "").trim(),
		});
		return fields;
	}

	function tagTargetPlanField(dialog) {
		if (!dialog || !dialog.fields_dict || !dialog.fields_dict.target_plan) return;
		const targetField = dialog.fields_dict.target_plan;
		const wrapper = targetField.$wrapper;
		if (!wrapper || !wrapper.attr) return;
		wrapper.attr("data-testid", "pp2-target-plan-select");
		if (targetField.$input && typeof targetField.$input.attr === "function") {
			targetField.$input.attr("data-testid", "pp2-target-plan-select-input");
		}
	}

	function open(opts) {
		const o = opts || {};
		if (!o.include_allowed) {
			if (typeof o.onBlocked === "function") {
				o.onBlocked(blockedMessage(o));
			}
			return { opened: false };
		}
		const demandCode = String(o.demand_code || "").trim();
		if (!demandCode) {
			frappe.show_alert({
				indicator: "orange",
				message: __("Demand code is missing for include action."),
			});
			return { opened: false };
		}
		const demandItemCodes = normalizeCodes(o.demand_item_codes);
		const locked = o.target_plan_locked === true;
		const dialog = new frappe.ui.Dialog({
			title: locked ? __("Add to Active Plan") : __("Add to Active Plan"),
			fields: buildIncludePlanDialogFields(o),
			primary_action_label: __("Add to Active Plan"),
			primary_action: function (values) {
				let targetPlan = String((values && values.target_plan) || "").trim();
				if (!targetPlan && dialog.fields_dict && dialog.fields_dict.target_plan) {
					const targetField = dialog.fields_dict.target_plan;
					if (typeof targetField.get_value === "function") {
						targetPlan = String(targetField.get_value() || "").trim();
					}
					if (targetField.$input && typeof targetField.$input.val === "function") {
						targetPlan = String(targetField.$input.val() || "").trim();
					}
				}
				if (!targetPlan) {
					targetPlan = String((values && values.target_plan_fallback) || "").trim();
				}
				if (!targetPlan) {
					targetPlan = String(o.target_plan_code || "").trim();
				}
				if (!targetPlan) {
					frappe.show_alert({
						indicator: "orange",
						message: __("Select a target procurement plan."),
					});
					return;
				}
				dialog.hide();
				dialog.set_primary_action(__("Including..."), function () {});
				frappe.call({
					method: INCLUDE_DEMAND_API,
					args: {
						demand_code: demandCode,
						procurement_plan_code: targetPlan,
						demand_item_codes: JSON.stringify(demandItemCodes),
					},
					callback: function (response) {
						const message = response && response.message ? response.message : {};
						if (!message || !message.ok) {
							frappe.msgprint({
								title: __("Unable to include demand"),
								message: safeIncludeFailureMessage(message && message.message),
								indicator: "orange",
							});
							dialog.set_primary_action(__("Add to Active Plan"), dialog.primary_action);
							return;
						}
						frappe.show_alert({
							indicator: "green",
							message: __("Demand added to procurement plan."),
						});
						if (typeof o.onSuccess === "function") {
							o.onSuccess(message);
						}
					},
					error: function () {
						dialog.set_primary_action(__("Add to Active Plan"), dialog.primary_action);
					},
				});
			},
		});
		dialog.show();
		if (!locked) {
			tagTargetPlanField(dialog);
		}
		const defaultPlanCode = String(o.target_plan_code || "").trim();
		if (defaultPlanCode && !locked) {
			dialog.set_value("target_plan", defaultPlanCode);
		}
		const primaryBtn = dialog.get_primary_btn ? dialog.get_primary_btn() : null;
		if (primaryBtn && primaryBtn.attr) {
			primaryBtn.attr("data-testid", "pp2-confirm-include-plan");
		}
		return { opened: true, dialog: dialog };
	}

	kentender_procurement.PlanningIncludePlanModal = {
		open: open,
	};
})();
