// R5-003 / LV-R5-003-01 — Procurement Use panel on Budget Line form.
(function () {
	function esc(s) {
		const t = String(s == null ? "" : s);
		return frappe.utils.escape_html ? frappe.utils.escape_html(t) : t;
	}

	function fmtAmount(val, currency) {
		if (val == null || val === "") return "—";
		const num = parseFloat(val);
		if (isNaN(num)) return "—";
		const cur = esc(currency || "");
		return cur ? `${cur} ${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
	}

	function renderPanel(frm) {
		const $page = $(frm.wrapper).find(".form-layout .form-page").first();
		$page.find(".kt-plc-budget-procurement-use-root").remove();

		if (frm.is_new() || !frm.doc || !frm.doc.name) {
			return;
		}

		const $root = $(`<div class="kt-plc-budget-procurement-use-root border rounded mb-3" data-testid="plc-budget-procurement-use">
			<div class="px-3 py-2 border-bottom bg-light">
				<strong>${__("Procurement use")}</strong>
				<div class="small text-muted" data-testid="plc-budget-procurement-use-subtitle"></div>
			</div>
			<div class="px-3 py-2" data-testid="plc-budget-procurement-use-body">
				<p class="text-muted small mb-0" data-testid="plc-budget-procurement-use-loading">${__(
					"Loading…",
				)}</p>
			</div>
		</div>`);

		$page.prepend($root);

		frappe.call({
			method:
				"kentender_procurement.procurement_lifecycle.api.journey_api.get_procurement_use_for_budget_line",
			args: {
				budget_line_name: frm.doc.name,
			},
			callback: function (r) {
				const $body = $root.find('[data-testid="plc-budget-procurement-use-body"]');
				const $sub = $root.find('[data-testid="plc-budget-procurement-use-subtitle"]');
				if (r.exc) {
					$body.empty().append(
						`<p class="text-danger small mb-0" data-testid="plc-budget-procurement-use-error">${esc(
							r.exc,
						)}</p>`,
					);
					return;
				}
				const d = r.message;
				if (!d || !d.ok) {
					const msg = (d && d.message) || __("Unable to load procurement use data.");
					$body.empty().append(
						`<p class="text-muted small mb-0" data-testid="plc-budget-procurement-use-empty">${esc(
							msg,
						)}</p>`,
					);
					return;
				}

				const blCode = esc(d.budget_line_code || "");
				const blName = esc(d.budget_line_display_name || "");
				$sub.text(blCode && blName ? `${blName} (${blCode})` : blCode || blName || "");

				const $wrap = $('<div class="kt-plc-budget-use-content"></div>');

				// --- Funding confirmation ---
				const hasBudget = d.budget_name || d.fiscal_year || d.budget_status;
				const hasFunding = hasBudget || d.amount_allocated != null;
				if (hasFunding) {
					const cur = esc(d.currency || "");
					const statusBadge = d.budget_status
						? `<span class="badge badge-${d.budget_status === "Approved" ? "success" : "secondary"} ml-1">${esc(d.budget_status)}</span>`
						: "";
					const budgetLine = hasBudget
						? `<div class="small mb-1"><span class="font-weight-bold">${esc(d.budget_name || "")}${d.fiscal_year ? ` (${esc(String(d.fiscal_year))})` : ""}</span>${statusBadge}</div>`
						: "";
					const amountRow = `<div class="row g-1 small">
						<div class="col-4"><span class="text-muted">${__("Allocated")}</span><br><span data-testid="plc-budget-procurement-use-amount-allocated">${fmtAmount(d.amount_allocated, cur)}</span></div>
						<div class="col-4"><span class="text-muted">${__("Reserved")}</span><br><span data-testid="plc-budget-procurement-use-amount-reserved">${fmtAmount(d.amount_reserved, cur)}</span></div>
						<div class="col-4"><span class="text-muted">${__("Available")}</span><br><span data-testid="plc-budget-procurement-use-amount-available">${fmtAmount(d.amount_available, cur)}</span></div>
					</div>`;
					const $funding = $(`<div class="mb-2 pb-2 border-bottom" data-testid="plc-budget-procurement-use-funding">
						<div class="small font-weight-bold mb-1">${__("Funding confirmation")}</div>
						${budgetLine}
						${amountRow}
					</div>`);
					$wrap.append($funding);
				}

				const journeys = d.journeys || [];
				const demands = d.demands || [];
				const packages = d.packages || [];

				if (!journeys.length && !demands.length && !packages.length) {
					const $none = $(`<p class="text-muted small mb-0" data-testid="plc-budget-procurement-use-none">${__(
						"No linked procurement journeys, demands, or packages.",
					)}</p>`);
					$wrap.append($none);
					$body.empty().append($wrap);
					return;
				}

				// --- Journeys ---
				if (journeys.length) {
					const $j = $(
						'<div class="mb-2" data-testid="plc-budget-procurement-use-journeys"></div>',
					);
					$j.append(
						`<div class="small font-weight-bold mb-1">${__("Linked procurement journeys")}</div>`,
					);
					const $ul = $('<ul class="list-unstyled mb-0 pl-0"></ul>');
					journeys.forEach(function (j) {
						const title = esc(j.journey_title || j.journey_code || "");
						const code = esc(j.journey_code || "");
						const stage = esc(j.current_stage_label || "");
						const href = esc(j.open_route || "#");
						$ul.append(
							`<li class="mb-1" data-testid="plc-budget-procurement-use-journey-row"><a href="${href}"><span data-testid="plc-budget-procurement-use-journey-title">${title}</span></a> <span class="text-muted small">(${code})</span>${stage ? `<span class="text-muted small"> — ${stage}</span>` : ""}</li>`,
						);
					});
					$j.append($ul);
					$wrap.append($j);
				}

				// --- Demands ---
				if (demands.length) {
					const $d = $(
						'<div class="mb-2" data-testid="plc-budget-procurement-use-demands"></div>',
					);
					$d.append(
						`<div class="small font-weight-bold mb-1">${__("Linked demands")}</div>`,
					);
					const $ul = $('<ul class="list-unstyled mb-0 pl-0"></ul>');
					demands.forEach(function (dem) {
						const title = esc(dem.title || dem.demand_id || "");
						const code = esc(dem.demand_id || "");
						const status = esc(dem.status || "");
						const href = esc(dem.list_route || "#");
						$ul.append(
							`<li class="mb-1" data-testid="plc-budget-procurement-use-demand-row"><a href="${href}"><span data-testid="plc-budget-procurement-use-demand-title">${title}</span></a> <span class="text-muted small">(${code})</span>${status ? `<span class="text-muted small"> — ${status}</span>` : ""}</li>`,
						);
					});
					$d.append($ul);
					$wrap.append($d);
				}

				// --- Packages ---
				if (packages.length) {
					const $p = $(
						'<div data-testid="plc-budget-procurement-use-packages"></div>',
					);
					$p.append(
						`<div class="small font-weight-bold mb-1">${__("Linked procurement packages")}</div>`,
					);
					const $ul = $('<ul class="list-unstyled mb-0 pl-0"></ul>');
					packages.forEach(function (pkg) {
						const title = esc(pkg.name || pkg.code || "");
						const code = esc(pkg.code || "");
						const status = esc(pkg.status || "");
						const href = esc(pkg.list_route || "#");
						$ul.append(
							`<li class="mb-1" data-testid="plc-budget-procurement-use-package-row"><a href="${href}"><span data-testid="plc-budget-procurement-use-package-name">${title}</span></a> <span class="text-muted small">(${code})</span>${status ? `<span class="text-muted small"> — ${status}</span>` : ""}</li>`,
						);
					});
					$p.append($ul);
					$wrap.append($p);
				}

				$body.empty().append($wrap);
			},
			error: function (err) {
				const $body = $root.find('[data-testid="plc-budget-procurement-use-body"]');
				$body.empty().append(
					`<p class="text-danger small mb-0" data-testid="plc-budget-procurement-use-error">${esc(
						err && err.message,
					)}</p>`,
				);
			},
		});
	}

	frappe.ui.form.on("Budget Line", {
		refresh: renderPanel,
	});
})();
