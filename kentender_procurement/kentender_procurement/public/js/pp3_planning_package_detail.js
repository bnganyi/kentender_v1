/**
 * P6-001+ — Contextual Package Detail surface (PP3 wireframe §14–19).
 */
(function () {
	frappe.provide("kentender_procurement");

	const PACKAGE_DETAIL_API =
		"kentender_procurement.procurement_planning.api.package_detail.get_pp3_package_detail";
	const RUN_READINESS_API =
		"kentender_procurement.procurement_planning.api.package_readiness.run_pp_package_readiness_checks";
	const SUBMIT_PACKAGE_API =
		"kentender_procurement.procurement_planning.api.workflow.submit_package";
	const APPROVE_PACKAGE_API =
		"kentender_procurement.procurement_planning.api.workflow.approve_package";
	const RETURN_PACKAGE_API =
		"kentender_procurement.procurement_planning.api.workflow.return_package";
	const RELEASE_PACKAGE_API =
		"kentender_procurement.procurement_planning.api.package_release.release_pp_package_to_tender";
	const WORKBENCH_ROOT = "/desk/procurement-planning";

	const TAB_CONFIG = [
		{ id: "overview", label: __("Overview"), testId: "pp3-package-overview-tab" },
		{ id: "lines_funding", label: __("Lines & Funding"), testId: "pp3-package-lines-funding-tab" },
		{ id: "readiness", label: __("Readiness"), testId: "pp3-package-readiness-tab" },
		{ id: "review", label: __("Review"), testId: "pp3-package-review-tab" },
		{ id: "release", label: __("Release"), testId: "pp3-package-release-tab" },
	];

	const renderTokens = new WeakMap();
	const activeTabs = new WeakMap();

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function readMessage(response) {
		if (!response) return {};
		if (response.message && typeof response.message === "object") {
			return response.message;
		}
		return response;
	}

	function formatPlainCurrency(value, currency) {
		if (value == null || !currency) return "";
		const html = frappe.format(value, { fieldtype: "Currency", options: currency });
		const el = document.createElement("div");
		el.innerHTML = html;
		return (el.textContent || el.innerText || "").trim();
	}

	function loadingHtml() {
		return (
			'<article class="pp3-package-detail" data-testid="pp3-package-detail">' +
			'<p class="text-muted small mb-0">' +
			esc(__("Loading package…")) +
			"</p></article>"
		);
	}

	function errorHtml(message) {
		return (
			'<article class="pp3-package-detail" data-testid="pp3-package-detail">' +
			'<p class="text-danger small mb-2" data-testid="pp3-package-detail-error">' +
			esc(message || __("Package detail is unavailable.")) +
			"</p>" +
			'<button type="button" class="btn btn-default btn-sm" data-testid="pp3-back-to-workbench">' +
			esc(__("Back to Workbench")) +
			"</button></article>"
		);
	}

	function fieldRow(label, value, testId) {
		const text = String(value == null ? "" : value).trim() || "—";
		return (
			'<div class="pp3-package-detail__field mb-2">' +
			'<div class="small text-muted">' +
			esc(label) +
			"</div>" +
			'<div class="small"' +
			(testId ? ' data-testid="' + esc(testId) + '"' : "") +
			">" +
			esc(text) +
			"</div></div>"
		);
	}

	function headerHtml(detail) {
		const h = (detail && detail.header) || {};
		const primary = (detail && detail.primary_action) || {};
		return (
			'<header class="pp3-package-detail__header" data-testid="pp3-package-header">' +
			'<h3 class="h6 mb-1" data-testid="pp3-package-title">' +
			esc(h.title || detail.package_name || "") +
			"</h3>" +
			(h.meta_line
				? '<p class="text-muted small mb-1" data-testid="pp3-package-meta">' +
					esc(h.meta_line) +
					"</p>"
				: "") +
			fieldRow(__("Active plan"), h.active_plan_label, "pp3-package-active-plan") +
			fieldRow(__("Status"), h.status_label, "pp3-package-status") +
			fieldRow(__("Funding"), h.funding_label, "pp3-package-funding") +
			fieldRow(__("Blockers"), h.blockers_label, "pp3-package-blockers") +
			fieldRow(__("Next action"), h.next_action_label, "pp3-package-next-action") +
			(primary.visible && primary.label
				? '<div class="mt-2"><button type="button" class="btn btn-primary btn-sm" data-testid="pp3-package-primary-action" data-action="' +
					esc(primary.key || "") +
					'">' +
					esc(primary.label) +
					"</button></div>"
				: "") +
			"</header>"
		);
	}

	function tabsNavHtml(activeTab) {
		let html =
			'<nav class="pp3-package-detail__tabs nav nav-tabs mb-3" data-testid="pp3-package-tabs">';
		for (let i = 0; i < TAB_CONFIG.length; i += 1) {
			const tab = TAB_CONFIG[i];
			const active = tab.id === activeTab ? " active" : "";
			html +=
				'<button type="button" class="nav-link pp3-package-detail__tab' +
				active +
				'" data-testid="' +
				esc(tab.testId) +
				'" data-tab="' +
				esc(tab.id) +
				'">' +
				esc(tab.label) +
				"</button>";
		}
		return html + "</nav>";
	}

	function overviewTabHtml(tab) {
		const t = tab || {};
		return (
			'<section class="pp3-package-detail__tab-panel" data-testid="pp3-package-overview-panel">' +
			fieldRow(__("Source demand"), t.source_demand_label, "pp3-package-overview-source-demand") +
			fieldRow(__("Package purpose"), t.package_purpose, "pp3-package-overview-purpose") +
			fieldRow(__("Current status"), t.status_label, "pp3-package-overview-status") +
			fieldRow(__("Funding"), t.funding_label, "pp3-package-overview-funding") +
			fieldRow(__("Blockers"), t.blockers_label, "pp3-package-overview-blockers") +
			fieldRow(__("Next action"), t.next_action_label, "pp3-package-overview-next-action") +
			"</section>"
		);
	}

	function linesFundingTabHtml(tab) {
		const t = tab || {};
		const lines = Array.isArray(t.lines) ? t.lines : [];
		let table =
			'<table class="table table-sm small mb-2" data-testid="pp3-package-lines-table">' +
			"<thead><tr><th>" +
			esc(__("Demand item")) +
			"</th><th>" +
			esc(__("Package line")) +
			"</th><th>" +
			esc(__("Value")) +
			"</th></tr></thead><tbody>";
		if (!lines.length) {
			table +=
				'<tr><td colspan="3" class="text-muted">' +
				esc(__("No package lines yet.")) +
				"</td></tr>";
		} else {
			for (let i = 0; i < lines.length; i += 1) {
				const row = lines[i] || {};
				table +=
					"<tr><td>" +
					esc(row.demand_item_label || "—") +
					"</td><td>" +
					esc(row.package_line_label || "—") +
					"</td><td>" +
					esc(row.value_label || "—") +
					"</td></tr>";
			}
		}
		table += "</tbody></table>";
		return (
			'<section class="pp3-package-detail__tab-panel" data-testid="pp3-package-lines-funding-panel">' +
			fieldRow(__("Package total"), t.package_total_label, "pp3-package-lines-total") +
			fieldRow(__("Funding"), t.funding_label, "pp3-package-lines-funding") +
			fieldRow(__("Difference"), t.difference_label, "pp3-package-lines-difference") +
			table +
			"</section>"
		);
	}

	function readinessTabHtml(tab) {
		const t = tab || {};
		const checks = Array.isArray(t.checks) ? t.checks : [];
		let list = '<ul class="list-unstyled small mb-2" data-testid="pp3-package-readiness-checks">';
		for (let i = 0; i < checks.length; i += 1) {
			const c = checks[i] || {};
			const mark = c.ok ? "✓" : "✗";
			list +=
				"<li>" +
				esc(mark + " " + (c.label || "")) +
				"</li>";
		}
		list += "</ul>";
		const blockers = Array.isArray(t.blockers) ? t.blockers : [];
		let blockersHtml = "";
		if (blockers.length) {
			blockersHtml =
				'<div class="mb-2" data-testid="pp3-package-readiness-blockers">' +
				'<div class="small text-muted">' +
				esc(__("Blockers")) +
				"</div><ul class=\"small mb-0\">";
			for (let b = 0; b < blockers.length; b += 1) {
				blockersHtml += "<li>" + esc(blockers[b]) + "</li>";
			}
			blockersHtml += "</ul></div>";
		}
		const actions =
			'<div class="pp3-package-readiness-actions">' +
			(t.failed
				? '<button type="button" class="btn btn-default btn-sm me-2" data-testid="pp3-package-readiness-resolve" data-action="resolve_blockers">' +
					esc(__("Resolve Blockers")) +
					"</button>"
				: "") +
			(t.may_run
				? '<button type="button" class="btn btn-primary btn-sm" data-testid="pp3-package-readiness-run" data-action="run_readiness">' +
					esc(t.failed ? __("Run Checks Again") : __("Run Checks")) +
					"</button>"
				: "") +
			"</div>";
		return (
			'<section class="pp3-package-detail__tab-panel" data-testid="pp3-package-readiness-panel">' +
			fieldRow(__("Current readiness"), t.summary_label, "pp3-package-readiness-summary") +
			blockersHtml +
			list +
			actions +
			"</section>"
		);
	}

	function reviewTabHtml(tab) {
		const t = tab || {};
		let actions = "";
		if (t.may_submit) {
			actions +=
				'<button type="button" class="btn btn-primary btn-sm" data-testid="pp3-package-review-submit" data-action="submit_for_review">' +
				esc(__("Submit for Review")) +
				"</button>";
		}
		if (t.may_approve) {
			actions +=
				'<button type="button" class="btn btn-primary btn-sm me-2" data-testid="pp3-package-review-approve" data-action="approve">' +
				esc(__("Approve")) +
				"</button>";
		}
		if (t.may_return) {
			actions +=
				'<button type="button" class="btn btn-default btn-sm" data-testid="pp3-package-review-return" data-action="return">' +
				esc(__("Return")) +
				"</button>";
		}
		return (
			'<section class="pp3-package-detail__tab-panel" data-testid="pp3-package-review-panel">' +
			fieldRow(__("Review status"), t.status_label, "pp3-package-review-status") +
			(t.reviewer_note
				? fieldRow(__("Reviewer note"), t.reviewer_note, "pp3-package-review-note")
				: "") +
			(!t.may_approve && !t.may_return
				? '<p class="text-muted small mb-2" data-testid="pp3-package-review-guidance">' +
					esc(t.guidance || "") +
					"</p>"
				: "") +
			(t.next_action_label && t.status_label === __("Approved")
				? fieldRow(__("Next action"), t.next_action_label, "pp3-package-review-next-action")
				: "") +
			(actions ? '<div class="mt-2">' + actions + "</div>" : "") +
			"</section>"
		);
	}

	function releaseTabHtml(tab) {
		const t = tab || {};
		if (t.released) {
			let actions =
				'<div class="mt-2">' +
				(t.tender_open_route
					? '<a class="btn btn-primary btn-sm me-2" data-testid="pp3-package-release-open-tender" href="' +
						esc(t.tender_open_route) +
						'">' +
						esc(__("Open Tender")) +
						"</a>"
					: "") +
				'<button type="button" class="btn btn-default btn-sm" data-testid="pp3-package-view-evidence">' +
				esc(__("View Evidence")) +
				"</button></div>";
			return (
				'<section class="pp3-package-detail__tab-panel" data-testid="pp3-package-release-panel">' +
				'<p class="small mb-1" data-testid="pp3-package-release-headline">' +
				esc(t.headline || "") +
				"</p>" +
				'<p class="small mb-2" data-testid="pp3-package-release-subheadline">' +
				esc(t.subheadline || "") +
				"</p>" +
				fieldRow(__("Next action"), t.next_action_label, "pp3-package-release-next-action") +
				actions +
				"</section>"
			);
		}
		const blockers = Array.isArray(t.blockers) ? t.blockers : [];
		let blockersHtml = "";
		if (blockers.length) {
			blockersHtml =
				'<div class="mb-2" data-testid="pp3-package-release-blockers">' +
				'<div class="small text-muted">' +
				esc(__("Blockers")) +
				"</div><ol class=\"small mb-0\">";
			for (let i = 0; i < blockers.length; i += 1) {
				blockersHtml += "<li>" + esc(blockers[i]) + "</li>";
			}
			blockersHtml += "</ol></div>";
		}
		function bulletList(title, items, testId) {
			const rows = Array.isArray(items) ? items : [];
			if (!rows.length) return "";
			let html =
				'<div class="mb-2" data-testid="' +
				esc(testId) +
				'"><div class="small text-muted">' +
				esc(title) +
				"</div><ul class=\"small mb-0\">";
			for (let i = 0; i < rows.length; i += 1) {
				html += "<li>" + esc(rows[i]) + "</li>";
			}
			return html + "</ul></div>";
		}
		let actions = "";
		if (t.ready_label === __("No") && blockers.length) {
			actions =
				'<div class="mt-2">' +
				'<button type="button" class="btn btn-default btn-sm me-2" data-testid="pp3-package-release-go-readiness" data-action="go_readiness">' +
				esc(__("Go to Readiness")) +
				"</button>" +
				'<button type="button" class="btn btn-default btn-sm" data-testid="pp3-package-release-go-review" data-action="go_review">' +
				esc(__("Go to Review")) +
				"</button></div>";
		} else if (t.may_release) {
			actions =
				'<div class="mt-2"><button type="button" class="btn btn-primary btn-sm" data-testid="pp3-package-release-action" data-action="release_to_tender">' +
				esc(__("Release to Tender Management")) +
				"</button></div>";
		}
		return (
			'<section class="pp3-package-detail__tab-panel" data-testid="pp3-package-release-panel">' +
			fieldRow(__("Ready to release"), t.ready_label, "pp3-package-release-ready") +
			blockersHtml +
			bulletList(
				__("After release, these will be protected:"),
				t.protected_values,
				"pp3-package-release-protected",
			) +
			bulletList(
				__("Sent to Tender Management:"),
				t.sent_values,
				"pp3-package-release-sent",
			) +
			(t.warning
				? '<div class="alert alert-warning small py-2" data-testid="pp3-package-release-warning">' +
					esc(t.warning) +
					"</div>"
				: "") +
			actions +
			"</section>"
		);
	}

	function tabPanelHtml(activeTab, tabs) {
		const data = tabs || {};
		switch (activeTab) {
			case "lines_funding":
				return linesFundingTabHtml(data.lines_funding);
			case "readiness":
				return readinessTabHtml(data.readiness);
			case "review":
				return reviewTabHtml(data.review);
			case "release":
				return releaseTabHtml(data.release);
			default:
				return overviewTabHtml(data.overview);
		}
	}

	function shellHtml(detail, activeTab) {
		const d = detail || {};
		const tab = activeTab || "overview";
		return (
			'<article class="pp3-package-detail" data-testid="pp3-package-detail">' +
			headerHtml(d) +
			'<div class="pp3-package-detail__actions mt-3">' +
			'<button type="button" class="btn btn-default btn-sm" data-testid="pp3-back-to-workbench">' +
			esc(__("Back to Workbench")) +
			"</button>" +
			(d.show_view_evidence !== false
				? '<button type="button" class="btn btn-default btn-sm ms-2" data-testid="pp3-package-view-evidence">' +
					esc(__("View Evidence")) +
					"</button>"
				: "") +
			"</div>" +
			'<div class="pp3-package-detail__body mt-3" data-testid="pp3-package-detail-body">' +
			tabsNavHtml(tab) +
			'<div class="pp3-package-detail__tab-host" data-testid="pp3-package-tab-host">' +
			tabPanelHtml(tab, d.tabs) +
			"</div></div></article>"
		);
	}

	function setActiveTab(host, tabId) {
		if (host) activeTabs.set(host, tabId || "overview");
	}

	function getActiveTab(host) {
		return activeTabs.get(host) || "overview";
	}

	function openEvidence(packageCode) {
		if (
			kentender_procurement.PlanningEvidenceDrawer &&
			typeof kentender_procurement.PlanningEvidenceDrawer.openForPackage === "function"
		) {
			kentender_procurement.PlanningEvidenceDrawer.openForPackage({
				package_code: String(packageCode || "").trim(),
			});
		}
	}

	function callMethod(method, args) {
		return new Promise(function (resolve, reject) {
			frappe.call({
				method: method,
				args: args || {},
				callback: function (response) {
					resolve(readMessage(response));
				},
				error: function () {
					reject(new Error(__("Planning information could not be loaded. Try again.")));
				},
			});
		});
	}

	function runAction(action, opts) {
		const o = opts || {};
		const packageCode = String(o.packageCode || "").trim();
		const packageId = String(o.packageId || packageCode).trim();
		if (!packageCode) return Promise.resolve();
		if (action === "run_readiness") {
			return callMethod(RUN_READINESS_API, { package_code: packageCode });
		}
		if (action === "submit_for_review") {
			return callMethod(SUBMIT_PACKAGE_API, { package_id: packageId });
		}
		if (action === "approve") {
			return callMethod(APPROVE_PACKAGE_API, { package_id: packageId });
		}
		if (action === "return") {
			const reason = window.prompt(__("Enter return reason"));
			if (!reason || !String(reason).trim()) {
				return Promise.resolve({ cancelled: true });
			}
			return callMethod(RETURN_PACKAGE_API, {
				package_id: packageId,
				reason: String(reason).trim(),
			});
		}
		if (action === "release_to_tender") {
			return callMethod(RELEASE_PACKAGE_API, { package_code: packageCode });
		}
		return Promise.resolve();
	}

	function bindActions(host, opts, detail) {
		if (!host) return;
		const o = opts || {};
		const packageCode = String(o.packageCode || "").trim();

		host.querySelectorAll('[data-testid="pp3-back-to-workbench"]').forEach(function (btn) {
			if (btn.getAttribute("data-bound") === "1") return;
			btn.setAttribute("data-bound", "1");
			btn.addEventListener("click", function () {
				window.location.href = WORKBENCH_ROOT;
			});
		});

		host.querySelectorAll('[data-testid="pp3-package-view-evidence"]').forEach(function (btn) {
			if (btn.getAttribute("data-bound") === "1") return;
			btn.setAttribute("data-bound", "1");
			btn.addEventListener("click", function () {
				openEvidence(packageCode);
			});
		});

		host.querySelectorAll(".pp3-package-detail__tab").forEach(function (btn) {
			if (btn.getAttribute("data-bound") === "1") return;
			btn.setAttribute("data-bound", "1");
			btn.addEventListener("click", function () {
				const tabId = String(btn.getAttribute("data-tab") || "overview").trim();
				setActiveTab(host, tabId);
				host.innerHTML = shellHtml(detail, tabId);
				bindActions(host, o, detail);
			});
		});

		host.querySelectorAll("[data-action]").forEach(function (btn) {
			if (btn.getAttribute("data-bound") === "1") return;
			btn.setAttribute("data-bound", "1");
			btn.addEventListener("click", function () {
				const action = String(btn.getAttribute("data-action") || "").trim();
				if (action === "go_readiness") {
					setActiveTab(host, "readiness");
					host.innerHTML = shellHtml(detail, "readiness");
					bindActions(host, o, detail);
					return;
				}
				if (action === "go_review") {
					setActiveTab(host, "review");
					host.innerHTML = shellHtml(detail, "review");
					bindActions(host, o, detail);
					return;
				}
				if (action === "resolve_blockers") {
					setActiveTab(host, "lines_funding");
					host.innerHTML = shellHtml(detail, "lines_funding");
					bindActions(host, o, detail);
					return;
				}
				runAction(action, o).then(function () {
					render(host, o);
				});
			});
		});

		const primary = host.querySelector('[data-testid="pp3-package-primary-action"]');
		if (primary && primary.getAttribute("data-bound") !== "1") {
			primary.setAttribute("data-bound", "1");
			primary.addEventListener("click", function () {
				const action = String(primary.getAttribute("data-action") || "").trim();
				if (action === "open_tender") {
					const route = String(
						((detail.tabs || {}).release || {}).tender_open_route || "",
					).trim();
					if (route) window.location.href = route;
					return;
				}
				runAction(action, o).then(function () {
					render(host, o);
				});
			});
		}
	}

	function render(host, opts) {
		const target = host && host.nodeType === 1 ? host : null;
		if (!target) return Promise.resolve();
		const o = opts || {};
		const packageCode = String(o.packageCode || "").trim();
		if (!packageCode) {
			target.innerHTML = errorHtml(__("Package code is missing."));
			bindActions(target, o, null);
			return Promise.resolve();
		}
		const token = (renderTokens.get(target) || 0) + 1;
		renderTokens.set(target, token);
		target.innerHTML = loadingHtml();
		return new Promise(function (resolve) {
			frappe.call({
				method: PACKAGE_DETAIL_API,
				args: { package: packageCode },
				callback: function (response) {
					if (token !== renderTokens.get(target)) return resolve();
					const payload = readMessage(response);
					if (!payload || !payload.ok) {
						target.innerHTML = errorHtml(
							String((payload && payload.message) || "").trim() ||
								__("Package detail is unavailable."),
						);
						bindActions(target, o, null);
						return resolve();
					}
					const activeTab = getActiveTab(target);
					target.innerHTML = shellHtml(payload, activeTab);
					bindActions(
						target,
						{ packageCode: packageCode, packageId: payload.package_code || packageCode },
						payload,
					);
					resolve();
				},
				error: function () {
					if (token !== renderTokens.get(target)) return resolve();
					target.innerHTML = errorHtml(__("Planning information could not be loaded. Try again."));
					bindActions(target, o, null);
					resolve();
				},
			});
		});
	}

	kentender_procurement.PlanningPackageDetail = {
		render: render,
		TAB_CONFIG: TAB_CONFIG,
	};
})();
