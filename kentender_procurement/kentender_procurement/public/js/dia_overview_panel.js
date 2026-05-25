frappe.provide("kentender_procurement.dia_overview_panel");

(function () {
	function esc(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function dash(v) {
		if (v === null || v === undefined || v === "") {
			return "—";
		}
		return esc(String(v));
	}

	function dlRow(label, valueHtml, ddTestId) {
		const tid = ddTestId ? ' data-testid="' + esc(ddTestId) + '"' : "";
		return "<dt>" + esc(label) + "</dt><dd" + tid + ">" + valueHtml + "</dd>";
	}

	function justificationSummary(e) {
		if (!e) {
			return '<p class="text-muted small mb-0">' + esc(__("No additional justification recorded.")) + "</p>";
		}
		const parts = [];
		if (e.return_reason) {
			parts.push(
				'<p class="small mb-1"><strong>' +
					esc(__("Return to draft")) +
					"</strong> — " +
					dash(e.return_reason) +
					"</p>"
			);
		}
		if (e.rejection_reason) {
			parts.push(
				'<p class="small mb-1"><strong>' +
					esc(__("Rejection")) +
					"</strong> — " +
					dash(e.rejection_reason) +
					"</p>"
			);
		}
		if (e.cancellation_reason) {
			parts.push(
				'<p class="small mb-1"><strong>' +
					esc(__("Cancellation")) +
					"</strong> — " +
					dash(e.cancellation_reason) +
					"</p>"
			);
		}
		if (e.is_exception) {
			parts.push(
				'<p class="small mb-0 kt-dia-detail__exception"><strong>' +
					esc(__("Exception demand")) +
					"</strong></p>"
			);
		}
		if (!parts.length) {
			return '<p class="text-muted small mb-0">' + esc(__("No additional justification recorded.")) + "</p>";
		}
		return '<div data-testid="dia-overview-justification">' + parts.join("") + "</div>";
	}

	kentender_procurement.dia_overview_panel = {
		mount(hostEl, ctx) {
			if (!hostEl || !ctx || !ctx.payload) {
				return;
			}
			const payload = ctx.payload;
			const a = payload.a || {};
			const e = payload.e || {};
			hostEl.innerHTML =
				'<div class="kt-dia-detail__section" data-testid="dia-overview-panel">' +
				'<h4 class="kt-dia-detail__heading">' +
				esc(__("Identity")) +
				"</h4>" +
				'<dl class="kt-dia-detail__dl">' +
				dlRow(__("Demand ID"), '<span class="font-monospace">' + dash(a.demand_id) + "</span>") +
				dlRow(__("Department"), dash(a.requesting_department_label || a.requesting_department)) +
				dlRow(__("Requester"), dash(a.requested_by_label || a.requested_by)) +
				dlRow(__("Entity"), dash(a.procuring_entity_label || a.procuring_entity)) +
				dlRow(__("Demand category"), dash(a.requisition_type)) +
				dlRow(__("Request date"), dash(a.request_date)) +
				dlRow(__("Required by"), dash(a.required_by_date)) +
				dlRow(__("Current stage"), dash(e.current_stage), "dia-detail-current-stage") +
				"</dl>" +
				'<h4 class="kt-dia-detail__heading mt-3">' +
				esc(__("Justification summary")) +
				"</h4>" +
				justificationSummary(e) +
				"</div>";
		},
	};
})();
