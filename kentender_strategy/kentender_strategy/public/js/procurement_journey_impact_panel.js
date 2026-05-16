// R5-002 / LV-R5-002-01 — Procurement Journey Impact panel on Strategy Objective / Strategy Target.
(function () {
	function esc(s) {
		const t = String(s == null ? "" : s);
		return frappe.utils.escape_html ? frappe.utils.escape_html(t) : t;
	}

	function renderPanel(frm) {
		const $page = $(frm.wrapper).find(".form-layout .form-page").first();
		$page.find(".kt-plc-strategy-procurement-journey-impact-root").remove();

		if (frm.is_new() || !frm.doc || !frm.doc.name) {
			return;
		}

		const $root = $(`<div class="kt-plc-strategy-procurement-journey-impact-root border rounded mb-3" data-testid="plc-strategy-procurement-journey-impact">
			<div class="px-3 py-2 border-bottom bg-light">
				<strong>${__("Procurement journey impact")}</strong>
				<div class="small text-muted" data-testid="plc-strategy-procurement-journey-impact-subtitle"></div>
			</div>
			<div class="px-3 py-2" data-testid="plc-strategy-procurement-journey-impact-body">
				<p class="text-muted small mb-0" data-testid="plc-strategy-procurement-journey-impact-loading">${__(
					"Loading…",
				)}</p>
			</div>
		</div>`);

		$page.prepend($root);

		frappe.call({
			method:
				"kentender_procurement.procurement_lifecycle.api.journey_api.get_procurement_journeys_for_strategy_node",
			args: {
				strategy_node_doctype: frm.doctype,
				name: frm.doc.name,
			},
			callback: function (r) {
				const $body = $root.find('[data-testid="plc-strategy-procurement-journey-impact-body"]');
				const $sub = $root.find('[data-testid="plc-strategy-procurement-journey-impact-subtitle"]');
				if (r.exc) {
					$body.empty().append(
						`<p class="text-danger small mb-0" data-testid="plc-strategy-procurement-journey-impact-error">${esc(
							r.exc,
						)}</p>`,
					);
					return;
				}
				const d = r.message;
				if (!d || !d.ok) {
					const msg = (d && d.message) || __("Unable to load procurement links.");
					$body.empty().append(
						`<p class="text-muted small mb-0" data-testid="plc-strategy-procurement-journey-impact-empty">${esc(
							msg,
						)}</p>`,
					);
					return;
				}

				const bc = esc(d.business_code || "");
				const bt = esc(d.business_title || "");
				$sub.text(bc && bt ? `${bt} (${bc})` : bc || bt || "");

				const journeys = d.journeys || [];
				const lines = d.budget_lines || [];

				if (!journeys.length && !lines.length) {
					$body.empty().append(
						`<p class="text-muted small mb-0" data-testid="plc-strategy-procurement-journey-impact-none">${__(
							"No linked procurement journeys or budget lines.",
						)}</p>`,
					);
					return;
				}

				const $wrap = $('<div class="kt-plc-strategy-impact-content"></div>');
				if (journeys.length) {
					const $j = $('<div class="mb-2" data-testid="plc-strategy-procurement-journey-impact-journeys"></div>');
					$j.append(`<div class="small font-weight-bold mb-1">${ __("Linked procurement journeys") }</div>`);
					const $ul = $('<ul class="list-unstyled mb-0 pl-0"></ul>');
					journeys.forEach(function (j) {
						const title = esc(j.journey_title || j.journey_code || "");
						const code = esc(j.journey_code || "");
						const stage = esc(j.current_stage_label || "");
						const href = esc(j.open_route || "#");
						$ul.append(
							`<li class="mb-1" data-testid="plc-strategy-procurement-journey-impact-journey-row"><a href="${href}"><span data-testid="plc-strategy-procurement-journey-impact-journey-title">${title}</span></a> <span class="text-muted small">(${code})</span>${stage ? `<span class="text-muted small"> — ${stage}</span>` : ""}</li>`,
						);
					});
					$j.append($ul);
					$wrap.append($j);
				}
				if (lines.length) {
					const $b = $('<div data-testid="plc-strategy-procurement-journey-impact-budget-lines"></div>');
					$b.append(`<div class="small font-weight-bold mb-1">${ __("Linked budget lines") }</div>`);
					const $ul = $('<ul class="list-unstyled mb-0 pl-0"></ul>');
					lines.forEach(function (line) {
						const nm = esc(line.name || "");
						const code = esc(line.code || "");
						const href = esc(line.list_route || "#");
						$ul.append(
							`<li class="mb-1" data-testid="plc-strategy-procurement-journey-impact-budget-row"><a href="${href}"><span data-testid="plc-strategy-procurement-journey-impact-budget-name">${nm}</span></a> <span class="text-muted small">(${code})</span></li>`,
						);
					});
					$b.append($ul);
					$wrap.append($b);
				}

				$body.empty().append($wrap);
			},
			error: function (err) {
				const $body = $root.find('[data-testid="plc-strategy-procurement-journey-impact-body"]');
				$body.empty().append(
					`<p class="text-danger small mb-0" data-testid="plc-strategy-procurement-journey-impact-error">${esc(
						err && err.message,
					)}</p>`,
				);
			},
		});
	}

	frappe.ui.form.on("Strategy Objective", {
		refresh: renderPanel,
	});

	frappe.ui.form.on("Strategy Target", {
		refresh: renderPanel,
	});
})();
