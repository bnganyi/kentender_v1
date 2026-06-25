/**
 * P7-003+ — Released package follow-up summary panel.
 */
(function () {
	frappe.provide("kentender_procurement");

	const SUMMARY_API =
		"kentender_procurement.procurement_planning.api.released_to_tender.get_pp_released_package_summary";
	const renderTokens = new WeakMap();

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function fieldRow(label, value, testId) {
		if (!value) return "";
		return (
			'<div class="pp3-release-summary__field" data-testid="' +
			esc(testId) +
			'">' +
			'<div class="small text-muted">' +
			esc(label) +
			"</div>" +
			'<div class="small">' +
			esc(value) +
			"</div></div>"
		);
	}

	function idleHtml() {
		return (
			'<div class="pp3-release-summary pp3-release-summary--idle" data-testid="pp3-release-summary">' +
			'<p class="text-muted small mb-0">' +
			esc(__("Select a released package to view follow-up actions.")) +
			"</p></div>"
		);
	}

	function summaryHtml(payload) {
		const p = payload || {};
		const pkg = p.package || {};
		const tender = p.tender || {};
		const tenderLabel = String(tender.code || tender.name || "").trim();
		let actions = '<div class="pp3-release-summary__actions mt-3">';
		if (p.may_open_tender && tender.open_route) {
			actions +=
				'<a class="btn btn-primary btn-sm me-2" data-testid="pp3-open-tender-button" href="' +
				esc(tender.open_route) +
				'">' +
				esc(__("Open Tender")) +
				"</a>";
		}
		if (p.may_open_package && pkg.open_route) {
			actions +=
				'<a class="btn btn-default btn-sm me-2" data-testid="pp3-open-package-button" href="' +
				esc(pkg.open_route) +
				'">' +
				esc(__("Open Package")) +
				"</a>";
		}
		if (p.may_view_evidence && pkg.code) {
			actions +=
				'<button type="button" class="btn btn-default btn-sm" data-testid="pp3-view-release-evidence" data-pp3-package-code="' +
				esc(pkg.code) +
				'">' +
				esc(__("View Evidence")) +
				"</button>";
		}
		actions += "</div>";
		return (
			'<div class="pp3-release-summary" data-testid="pp3-release-summary">' +
			'<h3 class="h6 mb-2">' +
			esc(pkg.name || pkg.code || "") +
			"</h3>" +
			'<p class="text-muted small mb-2" data-testid="pp3-release-summary-headline">' +
			esc(p.headline || __("Released to Tender Management")) +
			"</p>" +
			fieldRow(__("Tender"), tenderLabel, "pp3-release-summary-tender") +
			fieldRow(__("Status"), p.status_label || "", "pp3-release-summary-status") +
			fieldRow(__("Next"), p.next_action_label || "", "pp3-release-summary-next-action") +
			actions +
			"</div>"
		);
	}

	function fetchSummary(packageCode) {
		return frappe
			.call({
				method: SUMMARY_API,
				type: "GET",
				args: { package_code: String(packageCode || "").trim() },
				freeze: false,
			})
			.then(function (r) {
				const msg = (r && r.message) || {};
				if (!msg.ok) {
					throw new Error(msg.message || __("Release summary could not be loaded."));
				}
				return msg;
			});
	}

	function bindActions(host, payload, opts) {
		if (!host) return;
		const evidenceBtn = host.querySelector('[data-testid="pp3-view-release-evidence"]');
		if (evidenceBtn && evidenceBtn.getAttribute("data-bound") !== "1") {
			evidenceBtn.setAttribute("data-bound", "1");
			evidenceBtn.addEventListener("click", function (event) {
				if (event && typeof event.preventDefault === "function") event.preventDefault();
				const pkg = (payload && payload.package) || {};
				if (typeof opts.onViewEvidence === "function") {
					opts.onViewEvidence({
						title: pkg.name || pkg.code || "",
						package_code: pkg.code || "",
					});
				}
			});
		}
	}

	function render(host, opts) {
		if (!host) return;
		const options = opts || {};
		const packageCode = String(options.packageCode || "").trim();
		const token = (renderTokens.get(host) || 0) + 1;
		renderTokens.set(host, token);

		if (!packageCode) {
			host.innerHTML = idleHtml();
			return;
		}

		host.innerHTML =
			'<div class="pp3-release-summary pp3-release-summary--loading" data-testid="pp3-release-summary">' +
			'<p class="text-muted small mb-0">' +
			esc(__("Loading release summary…")) +
			"</p></div>";

		fetchSummary(packageCode)
			.then(function (payload) {
				if (renderTokens.get(host) !== token) return;
				host.innerHTML = summaryHtml(payload);
				bindActions(host, payload, options);
				if (typeof options.onLoaded === "function") {
					options.onLoaded(payload);
				}
			})
			.catch(function (err) {
				if (renderTokens.get(host) !== token) return;
				host.innerHTML =
					'<div class="pp3-release-summary pp3-release-summary--error" data-testid="pp3-release-summary">' +
					'<p class="text-danger small mb-0">' +
					esc((err && err.message) || __("Release summary could not be loaded.")) +
					"</p></div>";
			});
	}

	kentender_procurement.PlanningReleasedSummary = {
		render: render,
		idleHtml: idleHtml,
		summaryHtml: summaryHtml,
	};
})();
