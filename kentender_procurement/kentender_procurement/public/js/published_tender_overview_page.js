// BW-A1 — Published Tender Overview (bidder workspace).
// Route: /desk/published-tender-overview/<publication_ref>
(function () {
	"use strict";

	var SURFACE_ID = "BW-A1";
	var PAGE_SLUG = "published-tender-overview";
	var GET_API = "kentender_procurement.tender_configurations.get_published_tender_overview";
	var START_API = "kentender_procurement.tender_configurations.start_or_get_bid_workspace";
	var PDF_API =
		"kentender_procurement.tender_configurations.download_tender_configuration_document_preview_pdf";
	var STORAGE_KEY = "kt_cl_bw_a1_publication_ref";

	var state = {
		payload: null,
		publicationRef: null,
		mounting: false,
		busy: false,
	};

	function surface() {
		var reg = kentender_core.cl_surface_registry;
		return reg && typeof reg.get === "function" ? reg.get(SURFACE_ID) : null;
	}

	function esc(v) {
		return frappe.utils.escape_html(v == null ? "" : String(v));
	}

	function publicationRef() {
		var route = frappe.get_route() || [];
		if (route.length > 1 && route[1]) {
			return String(route[1]).trim();
		}
		if (frappe.route_options && frappe.route_options.publication_ref) {
			return String(frappe.route_options.publication_ref).trim();
		}
		try {
			var params = new URLSearchParams(window.location.search || "");
			if (params.get("publication_ref")) {
				return String(params.get("publication_ref")).trim();
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

	function formatDate(raw) {
		if (!raw) return "—";
		try {
			return frappe.datetime.str_to_user(String(raw).replace("T", " ").slice(0, 19));
		} catch (e) {
			return String(raw);
		}
	}

	function statusChip(chip) {
		var s = String(chip || "Open");
		var tone = "approved";
		if (s === "Closed") tone = "error";
		if (s === "Unavailable") tone = "pending";
		return (
			'<span class="kt-cl-bw-a1-status kt-cl-bw-a1-status--' +
			tone +
			'" data-testid="kt-cl-bw-a1-status-chip">' +
			'<span class="kt-cl-bw-a1-status-dot"></span>' +
			esc(s) +
			"</span>"
		);
	}

	function ctaIcon(action) {
		if (action === "Continue Bid") return "play_arrow";
		if (action === "View Submitted Bid") return "receipt_long";
		if (action === "Closed") return "lock";
		if (action === "Unavailable") return "block";
		return "play_arrow";
	}

	function primaryCta(data) {
		var action = data.primary_action || "Unavailable";
		var enabled = !!data.primary_action_enabled;
		var cls =
			"kt-cl-bw-a1-cta" + (enabled ? " kt-cl-bw-a1-cta--primary" : " kt-cl-bw-a1-cta--disabled");
		return (
			'<button type="button" class="' +
			cls +
			'" data-action="primary-cta" data-testid="kt-cl-bw-a1-primary-cta"' +
			(enabled ? "" : " disabled") +
			">" +
			'<span class="material-symbols-outlined">' +
			ctaIcon(action) +
			"</span><span data-testid=\"kt-cl-bw-a1-primary-cta-label\">" +
			esc(action) +
			"</span></button>"
		);
	}

	function documentsTable(docs) {
		var rows = (docs || [])
			.map(function (d, idx) {
				var actions = "";
				if (d.can_view || d.can_download) {
					actions =
						'<div class="kt-cl-bw-a1-doc-actions">' +
						(d.can_view
							? '<button type="button" class="kt-cl-bw-a1-link" data-action="view-pdf" data-testid="kt-cl-bw-a1-doc-view-' +
								idx +
								'">' +
								__("View") +
								"</button>"
							: "") +
						(d.can_download
							? '<button type="button" class="kt-cl-bw-a1-link" data-action="download-pdf" data-testid="kt-cl-bw-a1-doc-download-' +
								idx +
								'">' +
								__("Download") +
								"</button>"
							: "") +
						"</div>";
				} else {
					actions = '<span class="text-muted">—</span>';
				}
				return (
					'<tr data-testid="kt-cl-bw-a1-doc-row" data-doc-key="' +
					esc(d.document_key || "") +
					'">' +
					'<td><span class="material-symbols-outlined kt-cl-bw-a1-doc-icon">' +
					esc(d.icon || "description") +
					"</span> " +
					esc(d.name || "") +
					"</td>" +
					"<td>" +
					esc(d.type || "") +
					"</td>" +
					"<td>" +
					esc(d.size || "—") +
					"</td>" +
					'<td class="kt-cl-bw-a1-td-right">' +
					actions +
					"</td></tr>"
				);
			})
			.join("");
		if (!rows) {
			rows =
				'<tr><td colspan="4" class="text-muted">' +
				__("No package documents available.") +
				"</td></tr>";
		}
		return (
			'<section class="kt-cl-bw-a1-card" data-testid="kt-cl-bw-a1-documents">' +
			'<h2 class="kt-cl-bw-a1-section-title"><span class="material-symbols-outlined">folder</span>' +
			__("Tender Documents") +
			"</h2>" +
			'<div class="kt-cl-bw-a1-table-wrap"><table class="kt-cl-bw-a1-table">' +
			"<thead><tr><th>" +
			__("Document Name") +
			"</th><th>" +
			__("Type") +
			"</th><th>" +
			__("Size") +
			"</th><th class=\"kt-cl-bw-a1-td-right\">" +
			__("Action") +
			"</th></tr></thead><tbody>" +
			rows +
			"</tbody></table></div></section>"
		);
	}

	function clarificationsBlock(data) {
		var items = data.clarifications || [];
		var askEnabled = !!data.ask_question_enabled;
		var list =
			items.length === 0
				? '<p class="kt-cl-bw-a1-muted" data-testid="kt-cl-bw-a1-clarifications-empty">' +
					__("No clarifications published yet.") +
					"</p>"
				: items
						.map(function (q) {
							return (
								'<div class="kt-cl-bw-a1-qa">' +
								'<p class="kt-cl-bw-a1-q">Q: ' +
								esc(q.question || "") +
								"</p>" +
								'<p class="kt-cl-bw-a1-a">A: ' +
								esc(q.answer || "") +
								"</p></div>"
							);
						})
						.join("");
		var askHint = data.clarification_deadline_passed
			? '<span class="kt-cl-bw-a1-ask-hint" data-testid="kt-cl-bw-a1-ask-hint">' +
				__("Clarification deadline has passed") +
				"</span>"
			: "";
		return (
			'<section class="kt-cl-bw-a1-card" data-testid="kt-cl-bw-a1-clarifications">' +
			'<div class="kt-cl-bw-a1-clarif-head">' +
			'<h2 class="kt-cl-bw-a1-section-title"><span class="material-symbols-outlined">forum</span>' +
			__("Clarifications") +
			"</h2>" +
			'<div class="kt-cl-bw-a1-ask-wrap">' +
			'<button type="button" class="kt-cl-bw-a1-ask" data-testid="kt-cl-bw-a1-ask-question" disabled' +
			(askEnabled ? "" : "") +
			">" +
			__("Ask Question") +
			"</button>" +
			askHint +
			"</div></div>" +
			list +
			"</section>"
		);
	}

	function keyDates(dates, pastDeadline) {
		var d = dates || {};
		return (
			'<section class="kt-cl-bw-a1-card" data-testid="kt-cl-bw-a1-key-dates">' +
			'<h2 class="kt-cl-bw-a1-section-title">' +
			__("Key Dates") +
			"</h2>" +
			'<div class="kt-cl-bw-a1-timeline">' +
			'<div class="kt-cl-bw-a1-tl-item"><span class="kt-cl-bw-a1-tl-dot kt-cl-bw-a1-tl-dot--done"></span>' +
			'<p class="kt-cl-bw-a1-tl-label">' +
			__("Published Date") +
			"</p><p class=\"kt-cl-bw-a1-tl-value\" data-testid=\"kt-cl-bw-a1-date-published\">" +
			esc(formatDate(d.published_at)) +
			"</p></div>" +
			'<div class="kt-cl-bw-a1-tl-item"><span class="kt-cl-bw-a1-tl-dot"></span>' +
			'<p class="kt-cl-bw-a1-tl-label">' +
			__("Clarification Deadline") +
			"</p><p class=\"kt-cl-bw-a1-tl-value\" data-testid=\"kt-cl-bw-a1-date-clarification\">" +
			esc(formatDate(d.clarification_deadline)) +
			"</p></div>" +
			'<div class="kt-cl-bw-a1-tl-item"><span class="kt-cl-bw-a1-tl-dot"></span>' +
			'<p class="kt-cl-bw-a1-tl-label">' +
			__("Submission Deadline") +
			'</p><p class="kt-cl-bw-a1-tl-value' +
			(pastDeadline ? " is-alert" : "") +
			'" data-testid="kt-cl-bw-a1-date-submission">' +
			esc(formatDate(d.submission_deadline)) +
			"</p></div>" +
			'<div class="kt-cl-bw-a1-tl-item"><span class="kt-cl-bw-a1-tl-dot"></span>' +
			'<p class="kt-cl-bw-a1-tl-label">' +
			__("Opening Date/Time") +
			"</p><p class=\"kt-cl-bw-a1-tl-value\" data-testid=\"kt-cl-bw-a1-date-opening\">" +
			esc(formatDate(d.opening_datetime)) +
			"</p></div></div></section>"
		);
	}

	function submitChecklist(sections) {
		var rows = (sections || [])
			.map(function (s) {
				var req = !!s.required;
				return (
					'<tr data-testid="kt-cl-bw-a1-section-row">' +
					"<td>" +
					esc(s.title || s.section_key || "") +
					'</td><td class="kt-cl-bw-a1-td-right' +
					(req ? " is-required" : "") +
					'">' +
					esc(s.required_label || (req ? "Required" : "Optional")) +
					"</td></tr>"
				);
			})
			.join("");
		if (!rows) {
			rows =
				'<tr><td colspan="2" class="text-muted">' +
				__("Submission sections will appear from the tender schema.") +
				"</td></tr>";
		}
		return (
			'<section class="kt-cl-bw-a1-card" data-testid="kt-cl-bw-a1-submit-checklist">' +
			'<h3 class="kt-cl-bw-a1-card-eyebrow">' +
			__("What you will submit") +
			"</h3>" +
			'<table class="kt-cl-bw-a1-mini-table"><tbody>' +
			rows +
			"</tbody></table></section>"
		);
	}

	function tenderInfo(rows) {
		var body = (rows || [])
			.map(function (r) {
				return (
					'<div class="kt-cl-bw-a1-info-row" data-testid="kt-cl-bw-a1-info-row" data-info-key="' +
					esc(r.key || "") +
					'">' +
					"<dt>" +
					esc(r.label || "") +
					"</dt><dd>" +
					esc(r.value || "") +
					"</dd></div>"
				);
			})
			.join("");
		if (!body) {
			body =
				'<p class="kt-cl-bw-a1-muted">' +
				__("No tender info fields configured for this STD instance.") +
				"</p>";
		}
		return (
			'<section class="kt-cl-bw-a1-card" data-testid="kt-cl-bw-a1-tender-info">' +
			'<h2 class="kt-cl-bw-a1-section-title">' +
			__("Tender Info") +
			"</h2>" +
			'<dl class="kt-cl-bw-a1-info-list">' +
			body +
			"</dl></section>"
		);
	}

	function render(data) {
		var refLine =
			__("Ref:") +
			" " +
			esc(data.published_tender_ref || "") +
			(data.procuring_entity ? " • " + esc(data.procuring_entity) : "");
		return (
			'<div class="kt-cl-bw-a1-root" data-testid="kt-cl-bw-a1-root">' +
			'<div class="kt-cl-bw-a1-layout" data-testid="kt-cl-bw-a1-layout">' +
			'<div class="kt-cl-bw-a1-main">' +
			'<section class="kt-cl-bw-a1-card" data-testid="kt-cl-bw-a1-header">' +
			'<div class="kt-cl-bw-a1-header-row">' +
			"<div>" +
			statusChip(data.status_chip) +
			'<h1 class="kt-cl-bw-a1-title" data-testid="kt-cl-bw-a1-title">' +
			esc(data.tender_title || "") +
			"</h1>" +
			'<p class="kt-cl-bw-a1-ref" data-testid="kt-cl-bw-a1-ref">' +
			refLine +
			"</p></div>" +
			primaryCta(data) +
			"</div>" +
			'<div class="kt-cl-bw-a1-scope" data-testid="kt-cl-bw-a1-scope">' +
			'<h2 class="kt-cl-bw-a1-card-eyebrow">' +
			__("Scope Summary") +
			"</h2>" +
			"<p>" +
			esc(data.scope_summary || "—") +
			"</p></div></section>" +
			documentsTable(data.documents) +
			clarificationsBlock(data) +
			"</div>" +
			'<aside class="kt-cl-bw-a1-rail">' +
			keyDates(data.dates, !!data.past_submission_deadline) +
			submitChecklist(data.submission_sections) +
			tenderInfo(data.tender_info) +
			"</aside></div></div>"
		);
	}

	function emptyHtml(msg) {
		return (
			'<div class="kt-cl-bw-a1-root" data-testid="kt-cl-bw-a1-root">' +
			'<div class="kt-cl-bw-a1-empty" data-testid="kt-cl-bw-a1-empty"><p>' +
			esc(msg || __("Select a published tender to view the overview.")) +
			"</p></div></div>"
		);
	}

	function call(method, args) {
		return new Promise(function (resolve, reject) {
			frappe.call({
				method: method,
				args: args || {},
				callback: function (r) {
					if (r.exc) reject(r.exc);
					else resolve(r.message);
				},
				error: reject,
			});
		});
	}

	function downloadPdf(configurationId) {
		if (!configurationId) return;
		window.open(
			"/api/method/" +
				PDF_API +
				"?configuration_id=" +
				encodeURIComponent(configurationId),
			"_blank"
		);
	}

	function bind($root) {
		$root.off("click.bwa1");
		$root.on("click.bwa1", "[data-action='primary-cta']", function () {
			if (state.busy || !state.payload) return;
			var action = state.payload.primary_action;
			if (!state.payload.primary_action_enabled) return;
			state.busy = true;
			function goBidderWorkspace(route) {
				var next = String(route || "");
				if (!next) return;
				if (next.indexOf("/tenders/") === 0 || next.indexOf("http") === 0) {
					window.location.href = next;
					return;
				}
				if (next.indexOf("/app/") === 0) {
					window.location.href = next;
					return;
				}
				frappe.set_route(next.split("/"));
			}
			if (action === "View Submitted Bid") {
				var route = state.payload.bidder_workspace_route;
				state.busy = false;
				if (route) goBidderWorkspace(route);
				return;
			}
			call(START_API, {
				published_tender_ref: state.publicationRef,
				bidder_label: "Desk Bidder",
			})
				.then(function (res) {
					state.busy = false;
					var next = (res && res.bidder_workspace_route) || state.payload.bidder_workspace_route;
					if (next) {
						goBidderWorkspace(next);
					} else {
						frappe.msgprint(__("Bid workspace opened."));
						load();
					}
				})
				.catch(function () {
					state.busy = false;
					frappe.msgprint({
						title: __("Bidding unavailable"),
						indicator: "red",
						message: __("Could not start or continue the bid for this tender."),
					});
				});
		});
		$root.on("click.bwa1", "[data-action='view-pdf'], [data-action='download-pdf']", function () {
			if (!state.payload) return;
			downloadPdf(state.payload.configuration_id);
		});
	}

	function mount(wrapper, html) {
		var page = wrapper.page;
		var $main = $(page.main);
		$main.html(html);
		bind($main);
	}

	function load() {
		var wrapper = state.wrapper;
		if (!wrapper || state.mounting) return;
		enterSurface();
		var ref = publicationRef();
		state.publicationRef = ref;
		if (!ref) {
			mount(wrapper, emptyHtml());
			return;
		}
		try {
			window.sessionStorage.setItem(STORAGE_KEY, ref);
		} catch (e) {
			/* ignore */
		}
		state.mounting = true;
		mount(
			wrapper,
			'<div class="kt-cl-bw-a1-root" data-testid="kt-cl-bw-a1-root"><p class="kt-cl-bw-a1-muted" style="padding:1rem">' +
				__("Loading published tender…") +
				"</p></div>"
		);
		call(GET_API, { published_tender_ref: ref })
			.then(function (data) {
				state.payload = data || {};
				state.mounting = false;
				mount(wrapper, render(state.payload));
			})
			.catch(function () {
				state.mounting = false;
				mount(
					wrapper,
					emptyHtml(__("Could not load published tender overview for {0}.", [ref]))
				);
			});
	}

	frappe.pages[PAGE_SLUG] = frappe.pages[PAGE_SLUG] || {};

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Published Tender Overview"),
			single_column: true,
		});
		wrapper.page = page;
		state.wrapper = wrapper;
		page.main.html('<div data-testid="kt-cl-bw-a1-root"></div>');
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		state.wrapper = wrapper;
		load();
	};
})();
