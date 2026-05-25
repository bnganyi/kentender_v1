frappe.provide("kentender_procurement.dia_planning_panel");

(function () {
	let handoffToken = 0;
	let readinessToken = 0;
	const cacheByDemand = Object.create(null);

	function esc(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function dash(v) {
		if (v === null || v === undefined || v === "") {
			return "—";
		}
		return esc(String(v));
	}

	function dlRow(label, valueHtml, ddTestId, hideIfEmpty) {
		if (hideIfEmpty && (valueHtml === "—" || !valueHtml)) {
			return "";
		}
		const tid = ddTestId ? ' data-testid="' + esc(ddTestId) + '"' : "";
		return "<dt>" + esc(label) + "</dt><dd" + tid + ">" + valueHtml + "</dd>";
	}

	const READINESS_LABELS = {
		budget_line: __("Budget line linked"),
		funding_source: __("Funding source resolved"),
		reservation_status: __("Budget reserved"),
		strategy_linkage: __("Strategy linkage complete"),
		delivery_location: __("Delivery location provided"),
		budget_availability: __("Sufficient budget available"),
		handoff_artefact: __("Planning handoff available"),
	};

	function checkById(checks, id) {
		for (let i = 0; i < (checks || []).length; i++) {
			if (checks[i] && checks[i].id === id) {
				return checks[i];
			}
		}
		return null;
	}

	function buildPanelChecks(readiness, handoffReadiness, linkage, handoffPayload) {
		const serverChecks = (readiness && readiness.checks) || [];
		const handoffChecks = (handoffReadiness && handoffReadiness.checks) || [];
		const out = [];

		out.push(
			checkById(serverChecks, "budget_line") || {
				id: "budget_line",
				label: READINESS_LABELS.budget_line,
				ok: !!(linkage && (linkage.budget_line_label || linkage.budget_line)),
				required: true,
			}
		);

		const fundingOk = !!(linkage && (linkage.funding_source_label || linkage.funding_source));
		out.push({
			id: "funding_source",
			label: READINESS_LABELS.funding_source,
			ok: fundingOk,
			required: true,
		});

		const reservation = checkById(serverChecks, "reservation_status");
		out.push(
			reservation
				? Object.assign({}, reservation, { label: READINESS_LABELS.reservation_status })
				: {
						id: "reservation_status",
						label: READINESS_LABELS.reservation_status,
						ok: false,
						required: true,
					}
		);

		const strategy = checkById(serverChecks, "strategy_linkage");
		out.push(
			strategy
				? Object.assign({}, strategy, { label: READINESS_LABELS.strategy_linkage })
				: {
						id: "strategy_linkage",
						label: READINESS_LABELS.strategy_linkage,
						ok: !!(linkage && (linkage.strategic_plan_label || linkage.strategic_plan)),
						required: true,
					}
		);

		const delivery = checkById(handoffChecks, "delivery_location");
		out.push(
			delivery
				? Object.assign({}, delivery, { label: READINESS_LABELS.delivery_location })
				: {
						id: "delivery_location",
						label: READINESS_LABELS.delivery_location,
						ok: false,
						required: true,
					}
		);

		const artefactOk = !!(
			handoffPayload &&
			handoffPayload.ok &&
			((handoffPayload.demand_approval_certificate &&
				handoffPayload.demand_approval_certificate.handoff_code) ||
				(handoffPayload.planning_inclusion && handoffPayload.planning_inclusion.handoff_code) ||
				handoffPayload.journey)
		);
		out.push({
			id: "handoff_artefact",
			label: READINESS_LABELS.handoff_artefact,
			ok: artefactOk,
			required: false,
		});

		return out;
	}

	function buildPlanningChecksTable(panelChecks, actions, nm, integrityBlocked) {
		const checks = (panelChecks && panelChecks.checks) || [];
		if (!checks.length) {
			return "";
		}
		let html =
			'<div class="table-responsive mb-2" data-testid="dia-planning-blocker-table">' +
			'<table class="table table-sm table-bordered mb-0">' +
			"<thead><tr><th>" +
			esc(__("Requirement")) +
			"</th><th>" +
			esc(__("Status")) +
			"</th><th>" +
			esc(__("Owner")) +
			"</th><th>" +
			esc(__("Action")) +
			"</th></tr></thead><tbody>";
		for (let i = 0; i < checks.length; i++) {
			const row = checks[i];
			let actionCell = "—";
			if (row.action_id === "return_approved_to_finance") {
				const act = (actions || []).find(function (a) {
					return a && a.id === "return_approved_to_finance";
				});
				if (act) {
					actionCell =
						'<button type="button" class="btn btn-default btn-xs" data-dia-detail-action="return_approved_to_finance" data-dia-detail-method="' +
						esc(act.method || "") +
						'" data-dia-detail-reason="' +
						esc(act.reason || "return") +
						'" data-dia-detail-name="' +
						esc(nm) +
						'" data-testid="dia-action-return-to-finance">' +
						esc(row.action_label || act.label || __("Send back to Finance")) +
						"</button>";
				}
			}
			html +=
				"<tr data-testid=\"dia-planning-check-row-" +
				esc(row.id) +
				'"><td>' +
				esc(row.requirement || "") +
				"</td><td>" +
				esc(row.status_label || "") +
				"</td><td>" +
				esc(row.owner || "") +
				"</td><td>" +
				actionCell +
				"</td></tr>";
		}
		html += "</tbody></table></div>";
		if (integrityBlocked) {
			html =
				'<div class="alert alert-warning small py-2 mb-2" data-testid="dia-planning-integrity-blocked">' +
				esc(__("Planning is blocked until finance resolves budget reservation integrity.")) +
				"</div>" +
				html;
		}
		return html;
	}

	function buildPlanningReadinessHtml(reviewData, linkage, handoffPayload, status, actions, nm) {
		const st = String(status || "").trim();
		if (st !== "Approved" && st !== "Planning Ready") {
			return "";
		}
		if (st === "Planning Ready") {
			return (
				'<div class="kt-dia-planning-readiness mb-3" data-testid="dia-planning-readiness">' +
				'<h4 class="kt-dia-detail__heading">' +
				esc(__("Planning readiness")) +
				"</h4>" +
				'<p class="text-muted small mb-0" data-testid="dia-planning-readiness-ready">' +
				esc(__("Planning ready — this demand can be included in procurement planning.")) +
				"</p></div>"
			);
		}

		const panelChecks = (reviewData && reviewData.planning_panel_checks) || {};
		const planningReadiness = (reviewData && reviewData.planning_readiness) || {};
		const integrityBlocked = !!(reviewData && reviewData.integrity_blocked);
		const gateReady = !!(planningReadiness.ready) && !integrityBlocked;

		let html =
			'<div class="kt-dia-planning-readiness mb-3" data-testid="dia-planning-readiness">' +
			'<h4 class="kt-dia-detail__heading">' +
			esc(__("Planning readiness")) +
			"</h4>" +
			'<p class="text-muted small mb-2" data-testid="dia-planning-readiness-intro">' +
			esc(
				gateReady
					? __("Planning check passed — ready for procurement planning intake.")
					: __(
							"Finance reserves budget on approval; procurement confirms Planning Ready when checks pass."
						)
			) +
			"</p>";
		html += buildPlanningChecksTable(panelChecks, actions, nm, integrityBlocked);
		html +=
			'<button type="button" class="btn btn-default btn-sm mb-0" data-dia-planning-refresh="1" data-testid="dia-planning-run-check">' +
			esc(__("Run Planning Readiness Check")) +
			"</button>";
		if (gateReady) {
			html +=
				'<p class="text-success small mt-2 mb-0" data-testid="dia-planning-readiness-ready">' +
				esc(__("All required planning checks passed.")) +
				"</p>";
		}
		html += "</div>";
		return html;
	}

	function buildLinkageSummaryHtml(b, e, status, payload) {
		const st = String(status || e.status || "Draft");
		const hasBudget = !!(b && (b.budget_line_label || b.budget_line));
		if (st === "Draft" && !hasBudget) {
			return (
				'<p class="text-muted small mb-2" data-testid="dia-detail-planning-draft-placeholder">' +
				esc(
					__(
						"Budget and strategy linkages are optional while this demand is in draft. A planner can complete them before planning handoff."
					)
				) +
				"</p>"
			);
		}
		let h = '<dl class="kt-dia-detail__dl">';
		h += dlRow(__("Budget line"), dash(b.budget_line_label || b.budget_line), "dia-detail-budget-line", true);
		h += dlRow(__("Budget"), dash(b.budget_label || b.budget), null, true);
		h += dlRow(__("Funding source"), dash(b.funding_source_label || b.funding_source), null, true);
		h += dlRow(__("Reservation status"), dash(b.reservation_status), "dia-detail-reservation-status", false);
		if (payload && payload.c && payload.c.reservation_reference) {
			h += dlRow(
				__("Reservation reference"),
				dash(payload.c.reservation_reference),
				"dia-detail-reservation-reference",
				false
			);
		}
		h += dlRow(__("Strategic plan"), dash(b.strategic_plan_label || b.strategic_plan), "dia-detail-strategy", true);
		h += dlRow(__("Program"), dash(b.program_label || b.program), null, true);
		h += dlRow(__("Sub-program"), dash(b.sub_program_label || b.sub_program), null, true);
		h += dlRow(__("Output indicator"), dash(b.output_indicator_label || b.output_indicator), null, true);
		h += dlRow(__("Performance target"), dash(b.performance_target_label || b.performance_target), null, true);
		h += dlRow(__("Planning status"), dash(e.planning_status), "dia-detail-planning-status", false);
		h += "</dl>";
		return h;
	}

	function buildPlanningHandoffContentHtml(d) {
		if (!d) {
			return (
				'<p class="text-muted small mb-0" data-testid="dia-detail-planning-handoff-empty">' +
				dash(__("Unable to load planning handoff data.")) +
				"</p>"
			);
		}
		if (!d.ok) {
			const msg =
				d && d.message !== undefined && d.message !== null && String(d.message).trim()
					? String(d.message)
					: __("Unable to load planning handoff data.");
			return (
				'<p class="text-muted small mb-0" data-testid="dia-detail-planning-handoff-empty">' +
				dash(msg) +
				"</p>"
			);
		}

		let h = "";
		if (d.hint) {
			h +=
				'<p class="text-muted small mb-2" data-testid="dia-detail-planning-handoff-hint">' +
				esc(String(d.hint)) +
				"</p>";
		}

		h += '<dl class="kt-dia-detail__dl">';
		if (d.journey) {
			const j = d.journey;
			const title = String(j.journey_title || "").trim();
			const href = esc(String(j.open_route || "#"));
			const primary = esc(title || String(j.journey_code || ""));
			const jourVal =
				'<a href="' +
				href +
				'" data-testid="dia-detail-planning-handoff-journey-link"><span data-testid="dia-detail-planning-handoff-journey-title">' +
				primary +
				"</span></a>";
			h += dlRow(
				__("Linked procurement journey"),
				'<span data-testid="dia-detail-planning-handoff-journey">' + jourVal + "</span>"
			);
		}
		h += "</dl>";

		const cert = d.demand_approval_certificate;
		if (cert && cert.handoff_code) {
			const certHref = esc(String(cert.demand_approval_record_route || "#"));
			const certLabelEsc = esc(String(cert.demand_approval_record_label || __("Demand Approval Record")));
			const linkHtml =
				'<a href="' +
				certHref +
				'" data-testid="dia-detail-planning-handoff-certificate-link">' +
				certLabelEsc +
				"</a>";
			h +=
				'<div class="border-top mt-3 pt-2" data-testid="dia-detail-planning-handoff-certificate">' +
				'<p class="small font-weight-bold mb-1">' +
				esc(__("Demand Approval Certificate")) +
				"</p>" +
				'<dl class="kt-dia-detail__dl">' +
				dlRow(__("Record"), linkHtml) +
				"</dl></div>";
		}

		const incl = d.planning_inclusion;
		if (incl && incl.handoff_code) {
			const pcode = incl.target_object_code || incl.plan_code_hint || "";
			const pcodeTxt = pcode ? esc(String(pcode)) : "";
			h +=
				'<div class="border-top mt-3 pt-2" data-testid="dia-detail-planning-handoff-planning-inclusion">' +
				'<p class="small font-weight-bold mb-1">' +
				esc(__("Planning inclusion")) +
				"</p>" +
				'<dl class="kt-dia-detail__dl">' +
				(pcodeTxt
					? dlRow(
							__("Procurement plan"),
							'<span data-testid="dia-detail-planning-handoff-plan-code">' + pcodeTxt + "</span>"
						)
					: "") +
				"</dl></div>";
		}

		return h;
	}

	function buildPlanningActionsHtml(actions, nm, reviewData) {
		const planning = (actions || []).filter(function (a) {
			return a && a.id === "mark_planning_ready";
		});
		if (!planning.length) {
			return "";
		}
		const readiness = (reviewData && reviewData.planning_readiness) || {};
		const integrityBlocked = !!(reviewData && reviewData.integrity_blocked);
		if (!(readiness && readiness.ready) || integrityBlocked) {
			return (
				'<p class="text-muted small mb-2" data-testid="dia-planning-confirm-blocked">' +
				esc(__("Confirm Planning Ready is available when all required checks above pass.")) +
				"</p>"
			);
		}
		let h = '<div class="kt-dia-detail__actions btn-toolbar flex-wrap mb-2" data-testid="dia-planning-actions">';
		for (let i = 0; i < planning.length; i++) {
			const a = planning[i];
			h +=
				'<button type="button" class="btn btn-sm btn-primary" data-dia-detail-action="mark_planning_ready" data-dia-detail-method="' +
				esc(a.method || "") +
				'" data-dia-detail-reason="' +
				esc(a.reason || "") +
				'" data-dia-detail-name="' +
				esc(nm) +
				'" data-testid="dia-action-mark-planning-ready">' +
				esc(a.label || __("Confirm Planning Ready")) +
				"</button>";
		}
		h += "</div>";
		return h;
	}

	function paintPlanningPanel(hostEl, ctx, handoffPayload, reviewData) {
		const payload = ctx.payload || {};
		const b = payload.b || {};
		const e = payload.e || {};
		const a = payload.a || {};
		const roleKey = payload.role_key || ctx.roleKey || "";
		const nm = payload.name || "";

		hostEl.innerHTML =
			'<div class="kt-dia-detail__section" data-testid="dia-planning-panel">' +
			'<h4 class="kt-dia-detail__heading">' +
			esc(__("Budget and strategy context")) +
			"</h4>" +
			buildLinkageSummaryHtml(b, e, a.status, payload) +
			(roleKey === "auditor"
				? '<p class="text-muted small mb-2">' + esc(__("Read-only planning context for audit review.")) + "</p>"
				: "") +
			'<div data-testid="dia-planning-readiness-host">' +
			buildPlanningReadinessHtml(reviewData, b, handoffPayload, a.status, payload.actions || [], nm) +
			"</div>" +
			'<div data-testid="dia-planning-actions-host">' +
			buildPlanningActionsHtml(payload.actions || [], nm, reviewData) +
			"</div>" +
			'<h4 class="kt-dia-detail__heading mt-3">' +
			esc(__("Procurement planning handoff")) +
			"</h4>" +
			(a.demand_id
				? '<p class="text-muted small mb-2" data-testid="dia-detail-planning-handoff-subtitle">' +
					esc(String(a.demand_id)) +
					(a.status ? " · " + esc(String(a.status)) : "") +
					"</p>"
				: "") +
			'<div id="kt-dia-planning-handoff-body-inner" data-testid="dia-detail-planning-handoff-body">' +
			buildPlanningHandoffContentHtml(handoffPayload) +
			"</div></div>";

		hostEl.onclick = function (ev) {
			const btn = ev.target.closest("[data-dia-planning-refresh]");
			if (!btn || !hostEl.contains(btn)) {
				return;
			}
			ev.preventDefault();
			const handoffInner = hostEl.querySelector("#kt-dia-planning-handoff-body-inner");
			if (handoffInner) {
				handoffInner.innerHTML =
					'<p class="text-muted small mb-0" data-testid="dia-detail-planning-handoff-loading">' +
					esc(__("Loading procurement planning context…")) +
					"</p>";
			}
			const token = ++handoffToken;
			readinessToken += 1;
			loadHandoff(hostEl, ctx, token, true);
		};
	}

	function storePlanningCache(nm, handoffPayload, reviewData) {
		if (!nm) {
			return;
		}
		cacheByDemand[nm] = {
			handoff: handoffPayload,
			review: reviewData,
		};
	}

	function paintReadinessBlock(hostEl, ctx, reviewData, handoffPayload) {
		const payload = ctx.payload || {};
		const b = payload.b || {};
		const a = payload.a || {};
		const readinessHost = hostEl.querySelector('[data-testid="dia-planning-readiness-host"]');
		const actionsHost = hostEl.querySelector('[data-testid="dia-planning-actions-host"]');
		if (!readinessHost) {
			return;
		}
		readinessHost.innerHTML = buildPlanningReadinessHtml(
			reviewData,
			b,
			handoffPayload,
			a.status,
			payload.actions || [],
			payload.name || ""
		);
		if (actionsHost) {
			actionsHost.innerHTML = buildPlanningActionsHtml(
				payload.actions || [],
				payload.name || "",
				reviewData
			);
		}
		storePlanningCache(payload.name || "", handoffPayload, reviewData);
	}

	function loadReadiness(hostEl, ctx, token, handoffPayload) {
		const nm = (ctx.payload && ctx.payload.name) || "";
		if (!nm) {
			paintReadinessBlock(hostEl, ctx, null, handoffPayload);
			return;
		}
		frappe.call({
			method: "kentender_procurement.demand_intake.api.review.get_demand_review_data",
			args: { demand_name: nm },
			callback: function (r) {
				if (token !== readinessToken || !hostEl.isConnected) {
					return;
				}
				paintReadinessBlock(hostEl, ctx, r && r.message, handoffPayload);
			},
			error: function () {
				if (token !== readinessToken || !hostEl.isConnected) {
					return;
				}
				paintReadinessBlock(hostEl, ctx, null, handoffPayload);
			},
		});
	}

	function loadHandoff(hostEl, ctx, token, forceRefresh) {
		const nm = (ctx.payload && ctx.payload.name) || "";
		const hostInner = hostEl.querySelector("#kt-dia-planning-handoff-body-inner");
		if (!hostInner || !nm) {
			loadReadiness(hostEl, ctx, token, null);
			return;
		}
		if (!forceRefresh && cacheByDemand[nm] && cacheByDemand[nm].handoff !== undefined) {
			hostInner.innerHTML = buildPlanningHandoffContentHtml(cacheByDemand[nm].handoff);
			loadReadiness(hostEl, ctx, token, cacheByDemand[nm].handoff);
			return;
		}
		frappe.call({
			method: "kentender_procurement.procurement_lifecycle.api.journey_api.get_demand_planning_status",
			args: { demand_name: nm },
			callback: function (r) {
				if (token !== handoffToken || !hostEl.isConnected) {
					return;
				}
				const payload = r && r.message;
				hostInner.innerHTML = buildPlanningHandoffContentHtml(payload);
				loadReadiness(hostEl, ctx, readinessToken, payload);
			},
			error: function (err) {
				if (token !== handoffToken || !hostEl.isConnected) {
					return;
				}
				const m =
					err && err.message !== undefined ? String(err.message) : __("Unable to load planning context.");
				hostInner.innerHTML =
					'<p class="text-danger small mb-0" data-testid="dia-detail-planning-handoff-error">' +
					esc(m) +
					"</p>";
				loadReadiness(hostEl, ctx, readinessToken, null);
			},
		});
	}

	kentender_procurement.dia_planning_panel = {
		prefetch(nm, payload) {
			if (!nm || cacheByDemand[nm]) {
				return;
			}
			const ctx = { payload: payload || { name: nm } };
			frappe.call({
				method: "kentender_procurement.procurement_lifecycle.api.journey_api.get_demand_planning_status",
				args: { demand_name: nm },
				callback: function (r) {
					const handoffPayload = (r && r.message) || null;
					frappe.call({
						method: "kentender_procurement.demand_intake.api.review.get_demand_review_data",
						args: { demand_name: nm },
						callback: function (rr) {
							storePlanningCache(nm, handoffPayload, (rr && rr.message) || null);
						},
					});
				},
			});
		},
		mount(hostEl, ctx) {
			if (!hostEl || !ctx || !ctx.payload) {
				return;
			}
			const payload = ctx.payload;
			const nm = payload.name || "";
			const cached = nm ? cacheByDemand[nm] : null;
			const hasPanel = !!hostEl.querySelector('[data-testid="dia-planning-panel"]');
			if (cached) {
				paintPlanningPanel(hostEl, ctx, cached.handoff, cached.review);
				return;
			}
			if (hasPanel) {
				const token = ++handoffToken;
				readinessToken += 1;
				loadHandoff(hostEl, ctx, token, true);
				return;
			}
			const b = payload.b || {};
			const e = payload.e || {};
			const a = payload.a || {};
			const roleKey = payload.role_key || ctx.roleKey || "";

			hostEl.innerHTML =
				'<div class="kt-dia-detail__section" data-testid="dia-planning-panel">' +
				'<h4 class="kt-dia-detail__heading">' +
				esc(__("Budget and strategy context")) +
				"</h4>" +
				buildLinkageSummaryHtml(b, e, a.status, payload) +
				(roleKey === "auditor"
					? '<p class="text-muted small mb-2">' + esc(__("Read-only planning context for audit review.")) + "</p>"
					: "") +
				'<div data-testid="dia-planning-readiness-host"></div>' +
				'<div data-testid="dia-planning-actions-host"></div>' +
				'<h4 class="kt-dia-detail__heading mt-3">' +
				esc(__("Procurement planning handoff")) +
				"</h4>" +
				(a.demand_id
					? '<p class="text-muted small mb-2" data-testid="dia-detail-planning-handoff-subtitle">' +
						esc(String(a.demand_id)) +
						(a.status ? " · " + esc(String(a.status)) : "") +
						"</p>"
					: "") +
				'<div id="kt-dia-planning-handoff-body-inner" data-testid="dia-detail-planning-handoff-body"><p class="text-muted small mb-0" data-testid="dia-detail-planning-handoff-loading">' +
				esc(__("Loading procurement planning context…")) +
				"</p></div></div>";

			hostEl.onclick = function (ev) {
				const btn = ev.target.closest("[data-dia-planning-refresh]");
				if (!btn || !hostEl.contains(btn)) {
					return;
				}
				ev.preventDefault();
				const handoffInner = hostEl.querySelector("#kt-dia-planning-handoff-body-inner");
				if (handoffInner) {
					handoffInner.innerHTML =
						'<p class="text-muted small mb-0" data-testid="dia-detail-planning-handoff-loading">' +
						esc(__("Loading procurement planning context…")) +
						"</p>";
				}
				const token = ++handoffToken;
				readinessToken += 1;
				loadHandoff(hostEl, ctx, token, true);
			};

			const token = ++handoffToken;
			readinessToken += 1;
			loadHandoff(hostEl, ctx, token, false);
		},
		invalidate(demandName) {
			if (demandName) {
				delete cacheByDemand[demandName];
			} else {
				Object.keys(cacheByDemand).forEach(function (k) {
					delete cacheByDemand[k];
				});
			}
			handoffToken += 1;
			readinessToken += 1;
		},
	};
})();
