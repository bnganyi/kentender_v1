// PUB-A1 — Electronic Tender Package Review (v7).
// Route: /desk/it-tender-package-review/<configuration_id>
(function () {
	"use strict";

	var SURFACE_ID = "PUB-A1";
	var PAGE_SLUG = "it-tender-package-review";
	var GET_API = "kentender_procurement.tender_configurations.get_package_review_summary";
	var CONFIRM_API = "kentender_procurement.tender_configurations.confirm_tender_package";
	var RETURN_PREVIEW_API =
		"kentender_procurement.tender_configurations.return_tender_configuration_preview_for_correction";
	var RETURN_PUB_API =
		"kentender_procurement.tender_configurations.return_publication_for_correction";
	var STORAGE_KEY = "kt_cl_pub_a1_configuration_id";
	var BACK_ROUTE = "it-tender-configuration-overview";

	var state = {
		payload: null,
		configurationId: null,
		mounting: false,
		busy: false,
	};

	function surface() {
		var reg = kentender_core.cl_surface_registry;
		return reg && typeof reg.get === "function" ? reg.get(SURFACE_ID) : null;
	}

	function c() {
		return kentender_core.cl_components || kentender_core.cl.components;
	}

	function esc(v) {
		return frappe.utils.escape_html(v == null ? "" : String(v));
	}

	function configurationId() {
		var route = frappe.get_route() || [];
		if (route.length > 1 && route[1]) {
			return String(route[1]).trim();
		}
		if (frappe.route_options && frappe.route_options.configuration_id) {
			return String(frappe.route_options.configuration_id).trim();
		}
		try {
			var params = new URLSearchParams(window.location.search || "");
			if (params.get("configuration_id")) {
				return String(params.get("configuration_id")).trim();
			}
		} catch (e) {
			/* ignore */
		}
		try {
			var stored = window.sessionStorage.getItem(STORAGE_KEY);
			if (stored) {
				return stored;
			}
		} catch (e2) {
			/* ignore */
		}
		return null;
	}

	function enterSurface() {
		var sh = kentender_core.cl_shell;
		var surf = surface();
		if (!sh || typeof sh.enterNative !== "function" || !surf) {
			return;
		}
		sh.enterNative({
			sidebarWorkspaceKey: surf.sidebarWorkspaceKey || "procurement",
			toolbar: (surf.chrome && surf.chrome.toolbar) || {},
			chrome: surf.chrome,
		});
	}

	function emptyHtml() {
		return (
			'<div class="kt-cl-pub-a1-empty" data-testid="kt-cl-pub-a1-root">' +
			"<p>" +
			__("Select a tender configuration to review the electronic package.") +
			"</p>" +
			'<button type="button" class="kt-cl-pub-a3-btn kt-cl-pub-a3-btn--secondary" data-action="back-home">' +
			__("Back to Configuration Home") +
			"</button></div>"
		);
	}

	function statusPill(status) {
		var s = String(status || "").toLowerCase();
		var cls = "kt-cl-pub-a1-pill";
		if (s.indexOf("available") >= 0 || s.indexOf("pass") >= 0) {
			cls += " kt-cl-pub-a1-pill--warn";
		} else if (s.indexOf("block") >= 0 || s.indexOf("fail") >= 0 || s.indexOf("attention") >= 0) {
			cls += " kt-cl-pub-a1-pill--warn";
		}
		return '<span class="' + cls + '">' + esc(status || "—") + "</span>";
	}

	function packageStrip(data) {
		var ctx = data.context || {};
		var blockers = !!(data.has_blockers);
		var statusLabel = blockers
			? __("BLOCKERS FOUND")
			: data.package_confirmed
				? __("PACKAGE CONFIRMED")
				: data.package_status || __("IN REVIEW");
		var cells = [
			{
				key: "config-ref",
				label: __("Tender Config Ref"),
				value: data.configuration_ref || ctx.configuration_ref || data.configuration_id || "—",
			},
			{
				key: "pkg-ref",
				label: __("Package Ref"),
				value: data.procurement_package_ref || ctx.procurement_package_ref || "—",
			},
			{
				key: "title",
				label: __("Tender Title"),
				value: data.tender_title || ctx.procurement_title || "—",
			},
			{
				key: "pe",
				label: __("Procuring Entity"),
				value: data.procuring_entity || ctx.procuring_entity_name || "—",
			},
			{
				key: "method",
				label: __("Method"),
				value: data.procurement_method || ctx.procurement_method_label || "—",
			},
			{
				key: "std",
				label: __("STD"),
				value: data.standard_tender_document || ctx.standard_tender_document_label || "—",
			},
			{ key: "status", label: __("Status"), value: statusLabel, alert: blockers },
		];
		var html = cells
			.map(function (cell) {
				return (
					'<div class="kt-cl-pub-a3-strip-cell" data-testid="kt-cl-pub-a1-strip-' +
					esc(cell.key) +
					'">' +
					'<p class="kt-cl-pub-a3-strip-label">' +
					esc(cell.label) +
					"</p>" +
					'<p class="kt-cl-pub-a3-strip-value' +
					(cell.alert ? " is-alert" : "") +
					'">' +
					esc(cell.value) +
					"</p></div>"
				);
			})
			.join("");
		return (
			'<section class="kt-cl-pub-a3-strip" data-testid="kt-cl-pub-a1-context-strip">' +
			'<div class="kt-cl-pub-a3-strip-grid" style="grid-template-columns:repeat(auto-fit,minmax(120px,1fr))">' +
			html +
			"</div></section>"
		);
	}

	function readinessTable(rows) {
		var body = (rows || [])
			.map(function (row, idx) {
				return (
					'<tr data-testid="kt-cl-pub-a1-readiness-row-' +
					esc(String(idx)) +
					'">' +
					"<td><strong>" +
					esc(row.area || "") +
					"</strong></td>" +
					"<td>" +
					statusPill(row.status || "—") +
					"</td>" +
					"<td>" +
					esc(row.summary || "") +
					"</td></tr>"
				);
			})
			.join("");
		return (
			'<section data-testid="kt-cl-pub-a1-readiness">' +
			'<div class="kt-cl-pub-a1-section-head">' +
			"<h2><span class=\"material-symbols-outlined\">inventory_2</span>" +
			__("Package Readiness Summary") +
			"</h2>" +
			'<button type="button" class="kt-cl-pub-a3-btn kt-cl-pub-a3-btn--primary" data-action="open-full-config" data-testid="kt-cl-pub-a1-open-config">' +
			__("Open Full Configuration") +
			"</button></div>" +
			'<div class="overflow-x-auto"><table class="kt-cl-pub-a1-table">' +
			"<thead><tr><th>" +
			__("Package Area") +
			"</th><th>" +
			__("Status") +
			"</th><th>" +
			__("Summary") +
			"</th></tr></thead><tbody>" +
			body +
			"</tbody></table></div></section>"
		);
	}

	function bidderTable(rows) {
		var body = (rows || [])
			.map(function (row) {
				return (
					"<tr><td><strong>" +
					esc(row.area || "") +
					"</strong></td><td>" +
					statusPill(row.status || "—") +
					"</td><td>" +
					esc(row.summary || "") +
					"</td></tr>"
				);
			})
			.join("");
		return (
			'<section data-testid="kt-cl-pub-a1-bidder">' +
			'<div class="kt-cl-pub-a1-section-head">' +
			"<h2><span class=\"material-symbols-outlined\">person_check</span>" +
			__("Bidder Experience Summary") +
			"</h2>" +
			'<button type="button" class="kt-cl-pub-a3-btn kt-cl-pub-a3-btn--outline" data-action="preview-workspace" data-testid="kt-cl-pub-a1-preview-workspace">' +
			__("Preview Bidder Workspace") +
			"</button></div>" +
			'<div class="overflow-x-auto"><table class="kt-cl-pub-a1-table">' +
			"<thead><tr><th>" +
			__("Bidder Workspace Area") +
			"</th><th>" +
			__("Status") +
			"</th><th>" +
			__("Summary") +
			"</th></tr></thead><tbody>" +
			body +
			"</tbody></table></div></section>"
		);
	}

	function documentSection(doc) {
		doc = doc || {};
		var available = doc.has_preview ? __("Available") : doc.preview_status || __("Pending");
		var renderOk = !(doc.render_issue_count > 0);
		return (
			'<section data-testid="kt-cl-pub-a1-document">' +
			'<div class="kt-cl-pub-a1-section-head">' +
			"<h2><span class=\"material-symbols-outlined\">description</span>" +
			__("Tender Document Output") +
			"</h2></div>" +
			'<div class="overflow-x-auto"><table class="kt-cl-pub-a1-table">' +
			"<thead><tr><th>" +
			__("Output") +
			"</th><th>" +
			__("Action") +
			"</th></tr></thead><tbody>" +
			"<tr><td><strong>" +
			__("Generated Tender Document") +
			"</strong><div>" +
			statusPill(available) +
			'</div></td><td><button type="button" class="kt-cl-pub-a1-link" data-action="open-document">' +
			'<span class="material-symbols-outlined">visibility</span> ' +
			__("View") +
			"</button></td></tr>" +
			"<tr><td><strong>" +
			__("Render Validation") +
			"</strong><div>" +
			statusPill(renderOk ? __("Passed") : __("Issues")) +
			"</div></td><td><span class=\"kt-cl-pub-a3-helper\">" +
			__("Automatic") +
			"</span></td></tr>" +
			"<tr><td><strong>" +
			__("Preview PDF") +
			"</strong><div>" +
			statusPill(doc.has_preview || doc.has_confirmed_pdf ? __("Available") : __("Pending")) +
			'</div></td><td><button type="button" class="kt-cl-pub-a1-link" data-action="open-document">' +
			'<span class="material-symbols-outlined">download</span> ' +
			esc(doc.download_label || __("Download")) +
			"</button></td></tr>" +
			"</tbody></table></div></section>"
		);
	}

	function issuesSection(issues) {
		var rows = issues || [];
		var body = rows.length
			? rows
					.map(function (issue) {
						var sev = String(issue.severity || "");
						var sevCls =
							sev.toLowerCase().indexOf("block") >= 0
								? "kt-cl-pub-a1-sev kt-cl-pub-a1-sev--blocker"
								: "kt-cl-pub-a1-sev kt-cl-pub-a1-sev--warn";
						return (
							"<tr><td><span class=\"" +
							sevCls +
							'">' +
							esc(sev || "—") +
							"</span></td><td>" +
							esc(issue.issue || "") +
							"</td><td>" +
							esc(issue.impact || issue.area || "") +
							'</td><td><button type="button" class="kt-cl-pub-a1-link" data-action="open-full-config">' +
							esc(issue.fix_action || __("Fix Area")) +
							"</button></td></tr>"
						);
					})
					.join("")
			: '<tr><td colspan="4">' + __("No package blockers or warnings.") + "</td></tr>";
		return (
			'<section data-testid="kt-cl-pub-a1-issues">' +
			'<div class="kt-cl-pub-a1-section-head">' +
			'<span class="material-symbols-outlined" style="color:#ba1a1a">report</span>' +
			"<h3>" +
			__("Package Blockers & Warnings") +
			"</h3></div>" +
			'<div class="overflow-x-auto"><table class="kt-cl-pub-a1-table">' +
			"<thead><tr><th>" +
			__("Severity") +
			"</th><th>" +
			__("Issue") +
			"</th><th>" +
			__("Area") +
			"</th><th>" +
			__("Action") +
			"</th></tr></thead><tbody>" +
			body +
			"</tbody></table></div></section>"
		);
	}

	function confirmedBanner(data) {
		if (!data.package_confirmed && !(data.publication_id && data.in_publication_setup)) {
			return "";
		}
		var pubId = data.publication_id || "";
		return (
			'<section class="kt-cl-pub-a1-confirmed" data-testid="kt-cl-pub-a1-confirmed">' +
			"<p><strong>" +
			__("Tender package confirmed.") +
			"</strong></p>" +
			"<p>" +
			__("The tender is ready for publication setup.") +
			"</p>" +
			'<button type="button" class="kt-cl-pub-a3-btn kt-cl-pub-a3-btn--primary" data-action="continue-setup" data-publication-id="' +
			esc(pubId) +
			'" data-testid="kt-cl-pub-a1-continue-setup"' +
			(pubId ? "" : " disabled") +
			">" +
			__("Continue to Publication Setup") +
			"</button></section>"
		);
	}

	function footerHtml(data) {
		var canConfirm = !!(data && data.can_confirm_package) && !state.busy;
		var canReturn = !!(data && data.can_return_for_correction) && !state.busy;
		var confirmed = !!(data && data.package_confirmed);
		return (
			'<div class="kt-cl-pub-a3-footer" data-testid="kt-cl-pub-a1-footer">' +
			'<button type="button" class="kt-cl-pub-a3-btn kt-cl-pub-a3-btn--secondary" data-action="back-home" data-testid="kt-cl-pub-a1-back">' +
			'<span class="material-symbols-outlined">arrow_back</span> ' +
			__("Back to Configuration") +
			"</button>" +
			'<div class="kt-cl-pub-a3-footer-end">' +
			'<button type="button" class="kt-cl-pub-a3-btn kt-cl-pub-a3-btn--outline" data-action="return-correction" data-testid="kt-cl-pub-a1-return"' +
			(canReturn ? "" : " disabled") +
			">" +
			__("Return for Correction") +
			"</button>" +
			(confirmed
				? '<button type="button" class="kt-cl-pub-a3-btn kt-cl-pub-a3-btn--primary" data-action="continue-setup" data-publication-id="' +
					esc(data.publication_id || "") +
					'" data-testid="kt-cl-pub-a1-continue-setup-footer">' +
					__("Continue to Publication Setup") +
					"</button>"
				: '<button type="button" class="kt-cl-pub-a3-btn kt-cl-pub-a3-btn--primary" data-action="confirm-package" data-testid="kt-cl-pub-a1-confirm"' +
					(canConfirm ? "" : " disabled") +
					">" +
					__("Confirm Tender Package") +
					' <span class="material-symbols-outlined">task_alt</span></button>') +
			"</div></div>"
		);
	}

	function pageHtml(data) {
		return (
			'<div data-testid="kt-cl-pub-a1-root" data-configuration-id="' +
			esc(data.configuration_id || "") +
			'">' +
			packageStrip(data) +
			confirmedBanner(data) +
			'<div class="kt-cl-pub-a1-layout" data-testid="kt-cl-pub-a1-layout">' +
			readinessTable(data.package_readiness) +
			bidderTable(data.bidder_experience) +
			documentSection(data.document_output) +
			issuesSection(data.issues) +
			"</div>" +
			footerHtml(data) +
			"</div>"
		);
	}

	function continueToSetup(publicationId) {
		var id = publicationId || (state.payload && state.payload.publication_id) || "";
		if (!id) {
			frappe.set_route("publications");
			return;
		}
		frappe.set_route("publication-setup", id);
	}

	function confirmPackage(page) {
		if (state.busy || !state.configurationId) {
			return;
		}
		kentender_core.cl.confirm({
			title: __("Confirm Tender Package?"),
			message: __(
				"This confirms that the electronic tender package is ready for publication setup. " +
					"The package includes bidder submission requirements, forms and evidence, price schedule, evaluation setup, generated tender document, and audit record. " +
					"After confirmation, the tender will move to Publication Setup. " +
					"This action does not publish the tender, notify bidders, open bid submission, evaluate bids, approve an award, or create a contract."
			),
			confirmLabel: __("Confirm Tender Package"),
			cancelLabel: __("Cancel"),
			onConfirm: function () {
				state.busy = true;
				remount(page);
				frappe.call({
					method: CONFIRM_API,
					args: {
						configuration_id: state.configurationId,
						payload: { confirm_ready_for_handoff: 1 },
					},
					callback: function (r) {
						state.busy = false;
						state.payload = r.message || state.payload;
						remount(page);
						frappe.show_alert(
							{
								message: __("Tender package confirmed. Ready for publication setup."),
								indicator: "green",
							},
							5
						);
					},
					error: function () {
						state.busy = false;
						remount(page);
					},
				});
			},
		});
	}

	function returnForCorrection(page) {
		if (state.busy || !state.configurationId) {
			return;
		}
		var reason = "";
		kentender_core.cl.confirm({
			title: __("Return for Correction?"),
			message: __(
				"This will return the tender to Tender Configurations for correction. " +
					"A new readiness check, review approval, electronic tender package review, and package confirmation will be required before publication."
			),
			confirmLabel: __("Return for Correction"),
			cancelLabel: __("Cancel"),
			onConfirm: function () {
				reason = window.prompt(__("Reason for return"), "") || "";
				if (!reason.trim()) {
					frappe.msgprint(__("A reason for return is required."));
					return;
				}
				state.busy = true;
				remount(page);
				var pubId = (state.payload && state.payload.publication_id) || "";
				if (pubId) {
					frappe.call({
						method: RETURN_PUB_API,
						args: { publication_id: pubId, payload: { reason: reason } },
						callback: function () {
							state.busy = false;
							frappe.show_alert({ message: __("Returned for correction"), indicator: "orange" }, 5);
							frappe.set_route(BACK_ROUTE, state.configurationId);
						},
						error: function () {
							state.busy = false;
							remount(page);
						},
					});
				} else {
					frappe.call({
						method: RETURN_PREVIEW_API,
						args: {
							configuration_id: state.configurationId,
							payload: {
								affected_section: "Electronic Tender Package",
								reason: reason,
								severity: "High",
							},
						},
						callback: function () {
							state.busy = false;
							frappe.show_alert({ message: __("Returned for correction"), indicator: "orange" }, 5);
							frappe.set_route(BACK_ROUTE, state.configurationId);
						},
						error: function () {
							state.busy = false;
							remount(page);
						},
					});
				}
			},
		});
	}

	function bind($root, page) {
		$root.off(".puba1");
		$root.on("click.puba1", "[data-action='back-home']", function (e) {
			e.preventDefault();
			frappe.set_route(BACK_ROUTE, state.configurationId || undefined);
		});
		$root.on("click.puba1", "[data-action='open-full-config']", function (e) {
			e.preventDefault();
			frappe.set_route(BACK_ROUTE, state.configurationId);
		});
		$root.on("click.puba1", "[data-action='open-document']", function (e) {
			e.preventDefault();
			frappe.set_route("it-tender-configuration-render-preview", state.configurationId);
		});
		$root.on("click.puba1", "[data-action='preview-workspace']", function (e) {
			e.preventDefault();
			frappe.set_route("it-tender-configuration-overview", state.configurationId);
		});
		$root.on("click.puba1", "[data-action='confirm-package']", function (e) {
			e.preventDefault();
			confirmPackage(page);
		});
		$root.on("click.puba1", "[data-action='return-correction']", function (e) {
			e.preventDefault();
			returnForCorrection(page);
		});
		$root.on("click.puba1", "[data-action='continue-setup']", function (e) {
			e.preventDefault();
			continueToSetup($(this).attr("data-publication-id"));
		});
	}

	function remount(page) {
		var sh = kentender_core.cl_shell;
		var surf = surface();
		var pageHeader =
			(surf && surf.chrome && surf.chrome.pageHeader) || {
				title: __("Electronic Tender Package Review"),
				hideBreadcrumbs: true,
			};
		enterSurface();
		if (surf && surf.chrome && surf.chrome.toolbar && typeof sh.updateChrome === "function") {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}
		sh.mountContent(page.main, {
			pageHeader: pageHeader,
			mainHtml: state.payload ? pageHtml(state.payload) : emptyHtml(),
		});
		bind($(page.main), page);
	}

	function mount(page) {
		if (state.mounting) {
			return;
		}
		var sh = kentender_core.cl_shell;
		if (!sh || typeof sh.mountContent !== "function") {
			page.main.html(
				'<div class="p-4 text-danger">' + __("Civic Ledger shell is not loaded.") + "</div>"
			);
			return;
		}
		enterSurface();
		var id = configurationId();
		state.configurationId = id;
		if (!id) {
			state.payload = null;
			remount(page);
			return;
		}
		var route = frappe.get_route() || [];
		if (!(route[0] === PAGE_SLUG && route[1] === id)) {
			state.mounting = true;
			frappe.set_route(PAGE_SLUG, id);
			setTimeout(function () {
				state.mounting = false;
			}, 0);
			return;
		}
		try {
			window.sessionStorage.setItem(STORAGE_KEY, id);
		} catch (e) {
			/* ignore */
		}
		frappe.call({
			method: GET_API,
			args: { configuration_id: id },
			callback: function (r) {
				state.payload = r.message || null;
				remount(page);
			},
			error: function () {
				state.payload = null;
				remount(page);
			},
		});
	}

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Electronic Tender Package Review"),
			single_column: true,
		});
		wrapper.page = page;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (wrapper && wrapper.page) {
			mount(wrapper.page);
		}
	};
})();
