frappe.provide("kentender_procurement.dia_review_panel");

(function () {
	let loadToken = 0;
	const cacheByDemand = Object.create(null);
	const inFlightByDemand = Object.create(null);

	function esc(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	const WORKFLOW_ACTION_IDS = {
		submit_demand: true,
		approve_hod: true,
		approve_finance: true,
		return_from_hod: true,
		return_from_finance: true,
		reject_from_hod: true,
		reject_from_finance: true,
		cancel_demand: true,
	};

	const DIA_LANDING_ACTION_TESTID = {
		open_form: "dia-action-edit",
		submit_demand: "dia-action-submit",
		approve_hod: "dia-action-approve-hod",
		approve_finance: "dia-action-approve-finance",
		return_from_hod: "dia-action-return",
		return_from_finance: "dia-action-return",
		reject_from_hod: "dia-action-reject",
		reject_from_finance: "dia-action-reject",
		cancel_demand: "dia-action-cancel",
	};

	function readinessList(block, testId) {
		const checks = (block && block.checks) || [];
		if (!checks.length) {
			return '<p class="text-muted small mb-0">' + esc(__("No readiness checks.")) + "</p>";
		}
		let html = '<ul class="list-unstyled mb-0" data-testid="' + esc(testId) + '">';
		for (let i = 0; i < checks.length; i++) {
			const c = checks[i];
			html +=
				"<li>" +
				(c.ok ? "✓" : "✗") +
				" " +
				esc(c.label || "") +
				(c.required === false ? ' <span class="text-muted small">(' + esc(__("optional")) + ")</span>" : "") +
				"</li>";
		}
		html += "</ul>";
		return html;
	}

	function buildActionsHtml(actions, nm) {
		const workflow = (actions || []).filter(function (a) {
			return a && WORKFLOW_ACTION_IDS[a.id];
		});
		if (!workflow.length) {
			return '<p class="text-muted small mb-0" data-testid="dia-review-no-actions">' + esc(__("No workflow actions.")) + "</p>";
		}
		let h = '<div class="kt-dia-detail__actions btn-toolbar flex-wrap mb-2" data-testid="dia-review-actions">';
		for (let i = 0; i < workflow.length; i++) {
			const a = workflow[i];
			const base =
				"btn btn-sm " + (a.danger ? "btn-danger" : a.primary ? "btn-primary" : "btn-default");
			const tid = DIA_LANDING_ACTION_TESTID[a.id] || "dia-detail-action-" + esc(a.id);
			h +=
				'<button type="button" class="' +
				base +
				'" data-dia-detail-action="' +
				esc(a.id) +
				'" data-dia-detail-method="' +
				esc(a.method || "") +
				'" data-dia-detail-reason="' +
				esc(a.reason || "") +
				'" data-dia-detail-name="' +
				esc(nm) +
				'" data-testid="' +
				esc(tid) +
				'">' +
				esc(a.label || "") +
				"</button>";
		}
		h += "</div>";
		return h;
	}

	function fetchReviewData(nm, callback) {
		if (!nm) {
			callback(null);
			return;
		}
		if (cacheByDemand[nm]) {
			callback(cacheByDemand[nm]);
			return;
		}
		if (inFlightByDemand[nm]) {
			inFlightByDemand[nm].push(callback);
			return;
		}
		inFlightByDemand[nm] = [callback];
		frappe.call({
			method: "kentender_procurement.demand_intake.api.review.get_demand_review_data",
			args: { demand_name: nm },
			callback: function (r) {
				const data = (r && r.message) || null;
				if (data) {
					cacheByDemand[nm] = data;
				}
				const waiters = inFlightByDemand[nm] || [];
				delete inFlightByDemand[nm];
				for (let i = 0; i < waiters.length; i++) {
					waiters[i](data);
				}
			},
			error: function () {
				const waiters = inFlightByDemand[nm] || [];
				delete inFlightByDemand[nm];
				for (let i = 0; i < waiters.length; i++) {
					waiters[i](null);
				}
			},
		});
	}

	function paintReviewError(hostEl) {
		hostEl.innerHTML =
			'<p class="text-danger small mb-0" data-testid="dia-review-error">' +
			esc(__("Could not load review data.")) +
			"</p>";
	}

	function formatActor(label, at) {
		const parts = [];
		if (label) {
			parts.push(String(label));
		}
		if (at) {
			parts.push(String(at));
		}
		return parts.length ? parts.join(" · ") : "—";
	}

	function renderApprovalOutcome(payload, reviewData) {
		const e = (payload && payload.e) || {};
		const outcome = (reviewData && reviewData.approval_outcome) || {};
		const guidance = (reviewData && reviewData.planning_handoff_guidance) || {};
		let html =
			'<div data-testid="dia-review-approval-outcome">' +
			'<h4 class="kt-dia-detail__heading">' +
			esc(__("Approval outcome")) +
			"</h4>" +
			'<dl class="kt-dia-detail__dl">' +
			"<dt>" +
			esc(__("HoD approval")) +
			"</dt><dd>" +
			esc(formatActor(e.hod_approved_by_label || outcome.hod_approved_by, e.hod_approved_at || outcome.hod_approved_at)) +
			"</dd>" +
			"<dt>" +
			esc(__("Finance approval")) +
			"</dt><dd>" +
			esc(
				formatActor(
					e.finance_approved_by_label || outcome.finance_approved_by,
					e.finance_approved_at || outcome.finance_approved_at
				)
			) +
			"</dd></dl>" +
			'<details class="small mb-2"><summary class="text-muted">' +
			esc(__("Submission checks completed before approval")) +
			"</summary>" +
			readinessList(reviewData.submission_readiness, "dia-review-submission-checks-collapsed") +
			"</details>";
		if (guidance.message) {
			html +=
				'<p class="text-muted small mb-0" data-testid="dia-review-planning-guidance">' +
				esc(guidance.message) +
				"</p>";
		}
		html += "</div>";
		return html;
	}

	function renderPendingReview(reviewData) {
		const block = (reviewData && reviewData.review_action_readiness) || {};
		return (
			'<div data-testid="dia-review-pending-decision">' +
			'<h4 class="kt-dia-detail__heading">' +
			esc(__("Review readiness")) +
			"</h4>" +
			(block.ready
				? '<p class="small text-success mb-2">' + esc(__("Ready for your decision.")) + "</p>"
				: '<p class="small text-muted mb-2">' + esc(__("Resolve outstanding checks before approving.")) + "</p>") +
			readinessList(block, "dia-review-action-checks") +
			"</div>"
		);
	}

	function renderDraftRejected(reviewData) {
		const sub = (reviewData && reviewData.submission_readiness) || {};
		return (
			'<div data-testid="dia-review-submission-block">' +
			'<h4 class="kt-dia-detail__heading">' +
			esc(__("Submission readiness")) +
			"</h4>" +
			(sub.ready
				? '<p class="small text-success mb-2" data-testid="dia-review-submission-ready">' +
					esc(__("Ready to submit.")) +
					"</p>"
				: '<p class="small text-muted mb-2" data-testid="dia-review-submission-pending">' +
					esc(__("Complete required checks before submitting.")) +
					"</p>") +
			readinessList(sub, "dia-review-submission-checks") +
			"</div>"
		);
	}

	function renderTerminal(payload) {
		const e = (payload && payload.e) || {};
		return (
			'<div data-testid="dia-review-terminal">' +
			'<h4 class="kt-dia-detail__heading">' +
			esc(__("Closure")) +
			"</h4>" +
			'<p class="text-muted small mb-0">' +
			esc(e.cancellation_reason || __("This demand is cancelled.")) +
			"</p></div>"
		);
	}

	function render(hostEl, payload, reviewData) {
		const nm = payload.name || "";
		const actions = payload.actions || [];
		const view = (reviewData && reviewData.review_view) || "draft";
		let body = "";
		if (view === "pending_review") {
			body = renderPendingReview(reviewData);
		} else if (view === "approved_outcome") {
			body = renderApprovalOutcome(payload, reviewData);
		} else if (view === "terminal") {
			body = renderTerminal(payload);
		} else {
			body = renderDraftRejected(reviewData);
		}
		hostEl.innerHTML =
			'<div class="kt-dia-detail__section" data-testid="dia-review-panel">' +
			body +
			'<h4 class="kt-dia-detail__heading mt-3">' +
			esc(__("Workflow actions")) +
			"</h4>" +
			buildActionsHtml(actions, nm) +
			"</div>";
	}

	kentender_procurement.dia_review_panel = {
		prefetch(nm) {
			fetchReviewData(nm, function () {});
		},
		mount(hostEl, ctx) {
			if (!hostEl || !ctx || !ctx.payload) {
				return;
			}
			const payload = ctx.payload;
			const nm = payload.name;
			if (!nm) {
				return;
			}
			const token = ++loadToken;
			const cached = cacheByDemand[nm];
			const hasPanel = !!hostEl.querySelector('[data-testid="dia-review-panel"]');
			if (cached) {
				render(hostEl, payload, cached);
				return;
			}
			if (hasPanel) {
				fetchReviewData(nm, function (reviewData) {
					if (token !== loadToken || !hostEl.isConnected) {
						return;
					}
					if (reviewData) {
						render(hostEl, payload, reviewData);
					} else if (!hostEl.querySelector('[data-testid="dia-review-panel"]')) {
						paintReviewError(hostEl);
					}
				});
				return;
			}
			hostEl.innerHTML =
				'<div class="text-muted small py-2" data-testid="dia-review-loading">' +
				esc(__("Loading review data…")) +
				"</div>";
			fetchReviewData(nm, function (reviewData) {
				if (token !== loadToken || !hostEl.isConnected) {
					return;
				}
				if (reviewData) {
					render(hostEl, payload, reviewData);
				} else {
					paintReviewError(hostEl);
				}
			});
		},
		invalidate(demandName) {
			if (demandName) {
				delete cacheByDemand[demandName];
			} else {
				Object.keys(cacheByDemand).forEach(function (k) {
					delete cacheByDemand[k];
				});
			}
			loadToken += 1;
		},
	};
})();
