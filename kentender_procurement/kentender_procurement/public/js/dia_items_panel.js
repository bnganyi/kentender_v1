frappe.provide("kentender_procurement.dia_items_panel");

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

	kentender_procurement.dia_items_panel = {
		mount(hostEl, ctx) {
			if (!hostEl || !ctx || !ctx.payload) {
				return;
			}
			const payload = ctx.payload;
			const cur = payload.currency || "KES";
			const dblock = payload.d || {};
			const c = payload.c || {};
			const rows = (dblock && dblock.rows) || [];
			const cnt = (dblock && dblock.line_count) || rows.length;
			const formatMoney = ctx.formatListMoney || function (v) {
				return String(v != null ? v : "—");
			};

			let itemsHtml = "";
			if (!rows.length) {
				itemsHtml =
					'<p class="text-muted small mb-0">' + esc(__("No line items on this demand.")) + "</p>";
			} else {
				itemsHtml =
					'<p class="small text-muted mb-1">' +
					esc(__("Lines")) +
					": " +
					esc(String(cnt)) +
					"</p>" +
					'<div class="table-responsive"><table class="table table-sm table-bordered kt-dia-detail-items mb-0">' +
					"<thead><tr>" +
					"<th>" +
					esc(__("Description")) +
					"</th><th>" +
					esc(__("Category")) +
					"</th><th>" +
					esc(__("UOM")) +
					'</th><th class="text-end">' +
					esc(__("Qty")) +
					'</th><th class="text-end">' +
					esc(__("Unit cost")) +
					'</th><th class="text-end">' +
					esc(__("Line total")) +
					"</th></tr></thead><tbody>";
				for (let i = 0; i < rows.length; i++) {
					const r = rows[i];
					itemsHtml +=
						"<tr><td>" +
						dash(r.item_description) +
						"</td><td>" +
						dash(r.category) +
						"</td><td>" +
						dash(r.uom) +
						'</td><td class="text-end">' +
						dash(r.quantity) +
						'</td><td class="text-end">' +
						esc(formatMoney(r.estimated_unit_cost, cur)) +
						'</td><td class="text-end">' +
						esc(formatMoney(r.line_total, cur)) +
						"</td></tr>";
				}
				itemsHtml += "</tbody></table></div>";
			}

			const amtStr = formatMoney(c.total_amount, cur);
			const snap =
				c.available_budget_at_check != null
					? esc(formatMoney(c.available_budget_at_check, cur))
					: "—";

			hostEl.innerHTML =
				'<div class="kt-dia-detail__section" data-testid="dia-items-panel">' +
				'<h4 class="kt-dia-detail__heading">' +
				esc(__("Financial summary")) +
				"</h4>" +
				'<dl class="kt-dia-detail__dl">' +
				dlRow(
					__("Total requested"),
					'<strong class="kt-dia-detail__amount" data-testid="dia-detail-total-amount">' +
						esc(amtStr) +
						"</strong>"
				) +
				dlRow(__("Available budget snapshot"), snap) +
				dlRow(__("Reservation ref"), dash(c.reservation_reference), "dia-detail-reservation-reference") +
				dlRow(__("Budget check time"), dash(c.budget_check_datetime)) +
				"</dl>" +
				'<h4 class="kt-dia-detail__heading mt-3">' +
				esc(__("Line items")) +
				"</h4>" +
				'<div data-testid="dia-detail-items-summary">' +
				itemsHtml +
				"</div></div>";
		},
	};
})();
