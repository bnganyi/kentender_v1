frappe.provide("kentender_budget.budget_review_panel");

(function () {
	function esc(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function row(ok, label) {
		return "<li>" + (ok ? "✓" : "✗") + " " + esc(label) + "</li>";
	}

	function emitWorkflowChanged(budgetName) {
		document.dispatchEvent(
			new CustomEvent("kt-budget-workflow-changed", {
				detail: { budget_name: budgetName || "" },
			}),
		);
	}

	function bindReviewActions($host, selected, checksPass, ctx) {
		const budgetName = selected.name;
		const st = String(selected.status || "Draft").trim();

		$host.find("[data-testid='budget-submit-approval']").on("click", function () {
			if (!checksPass) return;
			frappe.confirm(__("Submit this budget for approval?"), function () {
				frappe.call({
					method: "kentender_budget.api.approval.submit_budget",
					args: { budget_name: budgetName },
					callback: function () {
						frappe.show_alert({ message: __("Submitted for approval"), indicator: "green" });
						emitWorkflowChanged(budgetName);
					},
				});
			});
		});

		$host.find("[data-testid='budget-approve']").on("click", function () {
			frappe.confirm(__("Approve this budget?"), function () {
				frappe.call({
					method: "kentender_budget.api.approval.approve_budget",
					args: { budget_name: budgetName },
					callback: function () {
						frappe.show_alert({ message: __("Budget approved"), indicator: "green" });
						emitWorkflowChanged(budgetName);
					},
				});
			});
		});

		$host.find("[data-testid='budget-reject']").on("click", function () {
			const d = new frappe.ui.Dialog({
				title: __("Reject budget"),
				fields: [
					{
						fieldname: "rejection_reason",
						label: __("Reason for rejection"),
						fieldtype: "Small Text",
						reqd: 1,
					},
				],
				primary_action_label: __("Reject"),
				primary_action: function (values) {
					const reason = (values.rejection_reason || "").trim();
					if (!reason) return;
					frappe.call({
						method: "kentender_budget.api.approval.reject_budget",
						args: { budget_name: budgetName, rejection_reason: reason },
						callback: function () {
							d.hide();
							frappe.show_alert({ message: __("Budget rejected"), indicator: "orange" });
							emitWorkflowChanged(budgetName);
						},
					});
				},
			});
			d.$wrapper.attr("data-testid", "budget-reject-modal");
			d.fields_dict.rejection_reason.$wrapper
				.find("textarea")
				.attr("data-testid", "budget-reject-reason-input");
			d.show();
		});

		if (st === "Submitted" && !ctx.canApproveBudget) {
			$host.find("[data-testid='budget-approver-banner']").show();
		}
	}

	function renderActionsHtml(selected, checksPass, ctx) {
		const st = String(selected.status || "Draft").trim();
		let html = '<div class="kt-budget-review-actions mt-3" data-testid="budget-review-actions">';
		if (st === "Draft" || st === "Rejected") {
			if (ctx.canSubmitBudget) {
				html +=
					'<button type="button" class="btn btn-primary btn-sm" data-testid="budget-submit-approval"' +
					(checksPass ? "" : " disabled") +
					">" +
					esc(__("Submit for Approval")) +
					"</button>";
			}
		} else if (st === "Submitted") {
			if (ctx.canApproveBudget) {
				html +=
					'<button type="button" class="btn btn-primary btn-sm" data-testid="budget-approve">' +
					esc(__("Approve")) +
					"</button> " +
					'<button type="button" class="btn btn-default btn-sm" data-testid="budget-reject">' +
					esc(__("Reject")) +
					"</button>";
			}
		}
		html += "</div>";
		return html;
	}

	kentender_budget.budget_review_panel = {
		mount(hostEl, ctx) {
			if (!hostEl || !ctx || !ctx.selected) return;
			const selected = ctx.selected;
			const payload = ctx.reviewPayload || {};
			const totals = payload.totals || {};
			const lines = payload.budget_lines || [];
			if (!ctx.reviewPayload) {
				hostEl.innerHTML =
					'<div class="text-muted small py-2" data-testid="budget-review-loading">' +
					esc(__("Loading readiness…")) +
					"</div>";
				return;
			}
			const checks = [
				{ ok: !!selected.budget_name, label: __("Budget name provided") },
				{ ok: !!selected.strategic_plan, label: __("Strategic plan selected") },
				{ ok: !!selected.fiscal_year, label: __("Fiscal year provided") },
				{ ok: Number(selected.total_budget_amount || 0) > 0, label: __("Total amount provided") },
				{ ok: lines.length > 0, label: __("At least one allocation exists") },
				{
					ok:
						Number(totals.allocated_sum || selected.allocated_amount || 0) <=
						Number(selected.total_budget_amount || 0),
					label: __("Allocated amount does not exceed total"),
				},
			];
			const checksPass = checks.every(function (c) {
				return c.ok;
			});
			const st = String(selected.status || "Draft").trim();
			let approverContext = "";
			if (st === "Submitted") {
				approverContext =
					'<p class="small text-muted mb-2" data-testid="budget-approver-banner">' +
					esc(__("Awaiting approval by Planning Authority / Budget Approver.")) +
					"</p>";
			} else if (st === "Approved" && (selected.approved_by || selected.approved_at)) {
				approverContext =
					'<p class="small text-muted mb-2">' +
					esc(__("Approved by:")) +
					" " +
					esc(selected.approved_by_label || selected.approved_by || "—") +
					(selected.approved_at ? " · " + esc(String(selected.approved_at)) : "") +
					"</p>";
			}

			hostEl.innerHTML =
				'<div class="kt-budget-section kt-surface" data-testid="budget-review-panel">' +
				"<h6>" +
				esc(__("Review")) +
				"</h6>" +
				approverContext +
				'<ul class="list-unstyled mb-3" data-testid="budget-readiness-checklist">' +
				checks.map(function (check) {
					return row(check.ok, check.label);
				}).join("") +
				"</ul>" +
				'<div class="small text-muted mb-1">' +
				esc(__("Current state:")) +
				" " +
				esc(st) +
				"</div>" +
				'<div class="small text-muted mb-2">' +
				esc(ctx.nextStepLabel(st)) +
				"</div>" +
				renderActionsHtml(selected, checksPass, ctx) +
				"</div>";

			bindReviewActions($(hostEl), selected, checksPass, ctx);
		},
	};
})();
