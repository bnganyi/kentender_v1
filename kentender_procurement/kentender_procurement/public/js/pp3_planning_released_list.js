/**
 * P7-001 — Released to Tender follow-up list (v3).
 */
(function () {
	frappe.provide("kentender_procurement");

	const RELEASED_LIST_API =
		"kentender_procurement.procurement_planning.api.released_to_tender.get_pp_released_to_tender";
	const renderTokens = new WeakMap();

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function packageCode(row) {
		const pkg = (row && row.package) || {};
		return String(pkg.code || pkg.id || "").trim();
	}

	function rowStatusLabel(row) {
		const consumption = (row && row.consumption) || {};
		const tender = (row && row.tender) || {};
		const consStatus = String(consumption.status || "").trim();
		if (consStatus === "Consumed" || String(tender.code || "").trim()) {
			return __("Released · Tender created");
		}
		return __("Released");
	}

	function rowHtml(row, selectedCode) {
		const pkg = (row && row.package) || {};
		const code = packageCode(row);
		const active = code && code === selectedCode;
		return (
			'<button type="button" class="pp3-released-list__row' +
			(active ? " is-active" : "") +
			'" data-testid="pp3-released-row" data-pp3-package-code="' +
			esc(code) +
			'" aria-selected="' +
			(active ? "true" : "false") +
			'">' +
			'<div class="pp3-released-list__title">' +
			esc(pkg.name || code) +
			"</div>" +
			'<div class="pp3-released-list__meta text-muted small" data-testid="pp3-released-row-status">' +
			esc(rowStatusLabel(row)) +
			"</div>" +
			"</button>"
		);
	}

	function listHtml(rows, selectedCode) {
		const items = Array.isArray(rows) ? rows : [];
		if (!items.length) {
			return (
				'<div class="pp3-released-list__empty text-muted small">' +
				esc(__("No released packages match this search.")) +
				"</div>"
			);
		}
		let html = "";
		for (let i = 0; i < items.length; i += 1) {
			html += rowHtml(items[i], selectedCode);
		}
		return html;
	}

	function summaryIdleHtml() {
		return (
			kentender_procurement &&
			kentender_procurement.PlanningReleasedSummary &&
			typeof kentender_procurement.PlanningReleasedSummary.idleHtml === "function"
				? kentender_procurement.PlanningReleasedSummary.idleHtml()
				: '<div class="pp3-release-summary pp3-release-summary--idle" data-testid="pp3-release-summary">' +
					'<p class="text-muted small mb-0">' +
					esc(__("Select a released package to view follow-up actions.")) +
					"</p></div>"
		);
	}

	function fetchReleased(searchText) {
		return frappe
			.call({
				method: RELEASED_LIST_API,
				type: "GET",
				args: { search_text: String(searchText || "").trim() },
				freeze: false,
			})
			.then(function (r) {
				const msg = (r && r.message) || {};
				if (!msg.ok) {
					throw new Error(msg.message || __("Released packages could not be loaded."));
				}
				return msg;
			});
	}

	function bindSearch(searchInput, onSearch) {
		if (!searchInput || searchInput.getAttribute("data-bound") === "1") return;
		searchInput.setAttribute("data-bound", "1");
		let timer = null;
		searchInput.addEventListener("input", function () {
			if (timer) clearTimeout(timer);
			timer = setTimeout(function () {
				onSearch(String(searchInput.value || "").trim());
			}, 250);
		});
	}

	function renderSummary(summaryHost, row, options) {
		if (!summaryHost) return;
		const code = packageCode(row);
		const summaryApi =
			kentender_procurement &&
			kentender_procurement.PlanningReleasedSummary &&
			typeof kentender_procurement.PlanningReleasedSummary.render === "function"
				? kentender_procurement.PlanningReleasedSummary
				: null;
		if (summaryApi && code) {
			summaryApi.render(summaryHost, {
				packageCode: code,
				onViewEvidence: options && options.onViewEvidence,
			});
			return;
		}
		summaryHost.innerHTML = row ? "" : summaryIdleHtml();
	}

	function render(host, opts) {
		if (!host) return;
		const options = opts || {};
		const token = (renderTokens.get(host) || 0) + 1;
		renderTokens.set(host, token);
		const selectedCode = String(options.selectedPackageCode || "").trim();
		const searchText = String(options.searchText || "").trim();

		host.innerHTML =
			'<div class="pp3-released-to-tender-layout">' +
			'<div class="pp3-released-to-tender-layout__search mb-2">' +
			'<label class="small text-muted d-block mb-1">' +
			esc(__("Search")) +
			"</label>" +
			'<input type="search" class="form-control form-control-sm" data-testid="pp3-released-search" ' +
			'placeholder="' +
			esc(__("Search released packages")) +
			'" value="' +
			esc(searchText) +
			'">' +
			"</div>" +
			'<div class="pp3-released-to-tender-layout__body">' +
			'<div class="pp3-released-to-tender-layout__list">' +
			'<div class="pp3-released-list" data-testid="pp3-released-list">' +
			'<div class="pp3-released-list__loading text-muted small">' +
			esc(__("Loading released packages…")) +
			"</div></div></div>" +
			'<div class="pp3-released-to-tender-layout__summary" data-testid="pp3-released-summary-host"></div>' +
			"</div></div>";

		const listHost = host.querySelector('[data-testid="pp3-released-list"]');
		const summaryHost = host.querySelector('[data-testid="pp3-released-summary-host"]');
		const searchInput = host.querySelector('[data-testid="pp3-released-search"]');
		renderSummary(summaryHost, null, options);

		function paintRows(rows) {
			if (!listHost) return;
			listHost.innerHTML = listHtml(rows, selectedCode);
			listHost.querySelectorAll('[data-testid="pp3-released-row"]').forEach(function (btn) {
				btn.addEventListener("click", function () {
					const code = String(btn.getAttribute("data-pp3-package-code") || "").trim();
					const match = rows.find(function (row) {
						return packageCode(row) === code;
					});
					if (typeof options.onSelect === "function" && match) {
						options.onSelect(match);
					}
				});
			});
		}

		function load(search) {
			fetchReleased(search)
				.then(function (payload) {
					if (renderTokens.get(host) !== token) return;
					const rows = payload.rows || [];
					paintRows(rows);
					if (typeof options.onLoaded === "function") {
						options.onLoaded(payload, rows);
					}
					if (!selectedCode && rows.length && typeof options.onSelect === "function") {
						options.onSelect(rows[0]);
					} else if (selectedCode) {
						const match = rows.find(function (row) {
							return packageCode(row) === selectedCode;
						});
						if (match) {
							renderSummary(summaryHost, match, options);
						}
					}
				})
				.catch(function (err) {
					if (renderTokens.get(host) !== token) return;
					if (listHost) {
						listHost.innerHTML =
							'<div class="pp3-released-list__error text-danger small">' +
							esc((err && err.message) || __("Released packages could not be loaded.")) +
							"</div>";
					}
				});
		}

		bindSearch(searchInput, function (value) {
			load(value);
		});
		load(searchText);
	}

	kentender_procurement.PlanningReleasedList = {
		render: render,
		summaryIdleHtml: summaryIdleHtml,
		rowStatusLabel: rowStatusLabel,
		packageCode: packageCode,
	};
})();
