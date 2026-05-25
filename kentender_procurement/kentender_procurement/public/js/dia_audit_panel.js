frappe.provide("kentender_procurement.dia_audit_panel");

(function () {
	let loadToken = 0;
	const cacheByDemand = Object.create(null);

	function esc(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function renderTimeline(timeline) {
		if (!timeline || !timeline.length) {
			return '<p class="text-muted small mb-0" data-testid="dia-audit-timeline-empty">' + esc(__("No workflow history yet.")) + "</p>";
		}
		let html = '<ul class="list-unstyled mb-0" data-testid="dia-audit-timeline">';
		for (let i = 0; i < timeline.length; i++) {
			const row = timeline[i];
			html +=
				'<li class="mb-1" data-testid="dia-audit-timeline-row">' +
				"<strong>" +
				esc(row.label) +
				"</strong>" +
				(row.detail ? " — " + esc(row.detail) : "") +
				(row.at ? '<span class="text-muted small"> · ' + esc(row.at) + "</span>" : "") +
				(row.note ? '<div class="small text-muted">' + esc(row.note) + "</div>" : "") +
				"</li>";
		}
		html += "</ul>";
		return html;
	}

	function renderDownstream(downstream) {
		const d = downstream || {};
		const lines = [
			[__("Reservation status"), d.reservation_status || "", "dia-audit-reservation-status"],
			[__("Reservation reference"), d.reservation_reference || "", "dia-audit-reservation-ref"],
			[__("Planning status"), d.planning_status || "", "dia-audit-planning-status"],
			[
				__("Linked procurement packages"),
				d.procurement_available === false ? __("Unavailable") : String(d.linked_packages != null ? d.linked_packages : 0),
				"dia-audit-packages",
			],
			[
				__("Linked procurement journeys"),
				d.procurement_available === false ? __("Unavailable") : String(d.linked_journeys != null ? d.linked_journeys : 0),
				"dia-audit-journeys",
			],
		];
		let html = '<dl class="kt-dia-detail__dl mt-2" data-testid="dia-audit-downstream">';
		for (let i = 0; i < lines.length; i++) {
			const val = lines[i][1];
			if (val === "" || val === "—" || val === "0" || val === 0) {
				continue;
			}
			html +=
				"<dt>" +
				esc(lines[i][0]) +
				'</dt><dd data-testid="' +
				esc(lines[i][2]) +
				'">' +
				esc(String(val)) +
				"</dd>";
		}
		html += "</dl>";
		if (html.indexOf("<dt>") < 0) {
			return '<p class="text-muted small mb-0" data-testid="dia-audit-downstream-empty">' + esc(__("No downstream usage recorded yet.")) + "</p>";
		}
		return html;
	}

	function render(hostEl, auditData) {
		hostEl.innerHTML =
			'<div class="kt-dia-detail__section" data-testid="dia-audit-panel">' +
			'<h4 class="kt-dia-detail__heading">' +
			esc(__("Workflow timeline")) +
			"</h4>" +
			renderTimeline((auditData && auditData.timeline) || []) +
			'<h4 class="kt-dia-detail__heading mt-3">' +
			esc(__("Downstream usage")) +
			"</h4>" +
			renderDownstream((auditData && auditData.downstream) || {}) +
			"</div>";
	}

	kentender_procurement.dia_audit_panel = {
		prefetch(nm) {
			if (!nm || cacheByDemand[nm]) {
				return;
			}
			frappe.call({
				method: "kentender_procurement.demand_intake.api.audit.get_demand_audit_data",
				args: { demand_name: nm },
				callback: function (r) {
					const data = (r && r.message) || null;
					if (data) {
						cacheByDemand[nm] = data;
					}
				},
			});
		},
		mount(hostEl, ctx) {
			if (!hostEl || !ctx || !ctx.payload) {
				return;
			}
			const nm = ctx.payload.name;
			if (!nm) {
				return;
			}
			if (cacheByDemand[nm]) {
				render(hostEl, cacheByDemand[nm]);
				return;
			}
			if (cacheByDemand[nm]) {
				render(hostEl, cacheByDemand[nm]);
				return;
			}
			const hasPanel = !!hostEl.querySelector('[data-testid="dia-audit-panel"]');
			if (hasPanel) {
				const token = ++loadToken;
				frappe.call({
					method: "kentender_procurement.demand_intake.api.audit.get_demand_audit_data",
					args: { demand_name: nm },
					callback: function (r) {
						if (token !== loadToken || !hostEl.isConnected) {
							return;
						}
						const data = (r && r.message) || null;
						if (data) {
							cacheByDemand[nm] = data;
						}
						render(hostEl, data);
					},
					error: function () {
						if (token !== loadToken || !hostEl.isConnected) {
							return;
						}
						if (!hostEl.querySelector('[data-testid="dia-audit-panel"]')) {
							hostEl.innerHTML =
								'<p class="text-danger small mb-0" data-testid="dia-audit-error">' +
								esc(__("Could not load audit data.")) +
								"</p>";
						}
					},
				});
				return;
			}
			const token = ++loadToken;
			hostEl.innerHTML =
				'<div class="text-muted small py-2" data-testid="dia-audit-loading">' + esc(__("Loading audit data…")) + "</div>";
			frappe.call({
				method: "kentender_procurement.demand_intake.api.audit.get_demand_audit_data",
				args: { demand_name: nm },
				callback: function (r) {
					if (token !== loadToken || !hostEl.isConnected) {
						return;
					}
					const data = (r && r.message) || null;
					if (data) {
						cacheByDemand[nm] = data;
					}
					render(hostEl, data);
				},
				error: function () {
					if (token !== loadToken || !hostEl.isConnected) {
						return;
					}
					hostEl.innerHTML =
						'<p class="text-danger small mb-0" data-testid="dia-audit-error">' +
						esc(__("Could not load audit data.")) +
						"</p>";
				},
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
