/**
 * Officer Bid Submissions — Desk Frappe Page (docs/bids Stitch screens 1–6).
 * Routes: bid-submissions | bid-submissions/<publication_id> |
 *         bid-submissions/<publication_id>/bid/<bid_id> |
 *         bid-submissions/<publication_id>/bid/<bid_id>/section/<section_key>
 *
 * Sub-routes stay on the same Frappe Page, so on_page_show often does not
 * re-fire; bind frappe.router "change" and remount from the active page.
 */
var ktBsActivePage = null;
var ktBsRouteToken = 0;

frappe.pages["bid-submissions"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Bid Submissions"),
		single_column: true,
	});
	wrapper.page = page;
	ktBsActivePage = page;
	$(wrapper).addClass("page-bid-submissions");
	ensureCss();
	page.main.html('<div class="kt-bs-page" data-testid="kt-bid-submissions-root"></div>');
	bindRouterRemount();
	mount(page);
};

frappe.pages["bid-submissions"].on_page_show = function (wrapper) {
	var page =
		(wrapper && wrapper.page) ||
		(cur_page && cur_page.page) ||
		ktBsActivePage ||
		null;
	if (page && page.main) {
		ktBsActivePage = page;
		ensureCss();
		mount(page);
	}
};

function bindRouterRemount() {
	if (window.__ktBsRouterBound) {
		return;
	}
	window.__ktBsRouterBound = true;
	if (!(frappe.router && typeof frappe.router.on === "function")) {
		return;
	}
	frappe.router.on("change", function () {
		var route = frappe.get_route() || [];
		if (route[0] !== "bid-submissions" || !ktBsActivePage) {
			return;
		}
		mount(ktBsActivePage);
	});
}

function ensureCss() {
	if (!document.getElementById("kt-bs-fonts")) {
		var fonts = document.createElement("link");
		fonts.id = "kt-bs-fonts";
		fonts.rel = "stylesheet";
		fonts.href =
			"https://fonts.googleapis.com/css2?family=Manrope:wght@600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap";
		document.head.appendChild(fonts);
	}
	// Stylesheet is also on app_include_css; link only if missing (e.g. cold cache).
	if (
		!document.querySelector(
			'link[href*="bid_submissions_page.css"], style[data-kt-bs]'
		)
	) {
		var link = document.createElement("link");
		link.id = "kt-bs-page-css";
		link.rel = "stylesheet";
		link.href = "/assets/kentender_procurement/css/bid_submissions_page.css";
		document.head.appendChild(link);
	}
	// Desk may keep .page-head with higher-order styles; force-hide for this route.
	$(".page-bid-submissions > .page-head, .page-bid-submissions .page-head").hide();
}

function esc(v) {
	return frappe.utils.escape_html(v == null ? "" : String(v));
}

function icon(name, extraClass) {
	return (
		'<span class="material-symbols-outlined' +
		(extraClass ? " " + extraClass : "") +
		'" aria-hidden="true">' +
		esc(name) +
		"</span>"
	);
}

function routeParts() {
	var route = frappe.get_route() || [];
	var parts = route.slice(1);
	return {
		publicationId: parts[0] || "",
		bidId: parts[1] === "bid" ? parts[2] || "" : "",
		sectionKey: parts[3] === "section" ? parts[4] || "" : "",
		viewOpeningRecord: parts[1] === "opening-record",
		viewReceipt: parts[1] === "bid" && parts[3] === "receipt",
	};
}

function go() {
	var args = Array.prototype.slice.call(arguments);
	var next = ["bid-submissions"].concat(args);
	var done = function () {
		if (ktBsActivePage) {
			mount(ktBsActivePage);
		}
	};
	var ret = frappe.set_route.apply(frappe, next);
	if (ret && typeof ret.then === "function") {
		ret.then(done);
	} else {
		// set_route may update history sync but defer page show; remount next tick.
		setTimeout(done, 0);
	}
}

function pillClass(stage) {
	var s = String(stage || "");
	if (s.indexOf("Receiving") === 0) {
		return "kt-bs-pill--receiving";
	}
	if (s.indexOf("Closed") === 0) {
		return "kt-bs-pill--sealed";
	}
	if (s.indexOf("Opening") === 0) {
		return "kt-bs-pill--opening";
	}
	if (s.indexOf("Released") === 0) {
		return "kt-bs-pill--released";
	}
	return "kt-bs-pill--opened kt-bs-pill--solid";
}

function statusPill(stage, opts) {
	opts = opts || {};
	var label = stage || "";
	var cls = pillClass(label);
	var lock =
		opts.withLock && String(label).indexOf("Closed") === 0
			? icon("lock")
			: '<span class="kt-bs-pill__dot" aria-hidden="true"></span>';
	return (
		'<span class="kt-bs-pill ' +
		cls +
		'">' +
		lock +
		esc(label) +
		"</span>"
	);
}

function fmtDt(v) {
	if (!v) {
		return "—";
	}
	var d = frappe.datetime.str_to_obj(v);
	if (!d || isNaN(d.getTime())) {
		return String(v).replace("T", " ").slice(0, 16);
	}
	var months = [
		"Jan",
		"Feb",
		"Mar",
		"Apr",
		"May",
		"Jun",
		"Jul",
		"Aug",
		"Sep",
		"Oct",
		"Nov",
		"Dec",
	];
	var h = d.getHours();
	var m = d.getMinutes();
	var ampm = h >= 12 ? "p.m." : "a.m.";
	var h12 = h % 12;
	if (h12 === 0) {
		h12 = 12;
	}
	var mm = m < 10 ? "0" + m : String(m);
	return (
		d.getDate() +
		" " +
		months[d.getMonth()] +
		" " +
		d.getFullYear() +
		", " +
		h12 +
		":" +
		mm +
		" " +
		ampm
	);
}

function sectionIcon(key, label) {
	var k = String(key || "").toLowerCase();
	var l = String(label || "").toLowerCase();
	var blob = k + " " + l;
	if (blob.indexOf("form_of_tender") >= 0 || blob.indexOf("form of tender") >= 0) {
		return "contract";
	}
	if (blob.indexOf("price") >= 0 || blob.indexOf("schedule") >= 0) {
		return "payments";
	}
	if (blob.indexOf("security") >= 0) {
		return "shield";
	}
	if (blob.indexOf("questionnaire") >= 0 || blob.indexOf("cbq") >= 0) {
		return "corporate_fare";
	}
	if (blob.indexOf("statutory") >= 0 || blob.indexOf("declaration") >= 0) {
		return "rule";
	}
	if (blob.indexOf("preliminary") >= 0 || blob.indexOf("evidence") >= 0) {
		return "fact_check";
	}
	if (blob.indexOf("technical") >= 0) {
		return "engineering";
	}
	if (blob.indexOf("addenda") >= 0 || blob.indexOf("document") >= 0) {
		return "folder_open";
	}
	return "description";
}

function backBtn(action, label) {
	return (
		'<button type="button" class="kt-bs-back" data-action="' +
		esc(action) +
		'">' +
		icon("arrow_back") +
		esc(label || __("Back to Bid Submissions")) +
		"</button>"
	);
}

function rootEl(page) {
	return page.main.find("[data-testid='kt-bid-submissions-root']");
}

function mount(page) {
	var $root = rootEl(page);
	if (!$root.length) {
		return;
	}
	ktBsActivePage = page;
	var token = ++ktBsRouteToken;
	var r = routeParts();
	if (r.sectionKey && r.bidId && r.publicationId) {
		loadSection($root, r.publicationId, r.bidId, r.sectionKey, token);
		return;
	}
	if (r.viewReceipt && r.bidId && r.publicationId) {
		loadReceipt($root, r.publicationId, r.bidId, token);
		return;
	}
	if (r.bidId && r.publicationId) {
		loadBidOverview($root, r.publicationId, r.bidId, token);
		return;
	}
	if (r.viewOpeningRecord && r.publicationId) {
		loadOpeningRecord($root, r.publicationId, token);
		return;
	}
	if (r.publicationId) {
		loadPublicationView($root, r.publicationId, token);
		return;
	}
	loadLanding($root, token);
}

function stillCurrent(token) {
	return token === ktBsRouteToken;
}

function loadLanding($root, token) {
	$root.html('<div class="kt-bs-empty">' + esc(__("Loading…")) + "</div>");
	var search = "";
	var stage = "";
	function refresh() {
		var callToken = ktBsRouteToken;
		frappe.call({
			method: "kentender_procurement.tender_configurations.list_bid_submission_tenders",
			args: { search: search, stage: stage || null, page: 1, page_size: 50 },
			callback: function (r) {
				if (!stillCurrent(token) || !stillCurrent(callToken)) {
					return;
				}
				if (r.exc) {
					$root.html(
						'<div class="kt-bs-empty" data-testid="kt-bs-error">' +
							esc(__("Unable to load Bid Submissions.")) +
							"</div>"
					);
					return;
				}
				renderLanding(
					$root,
					r.message || {},
					refresh,
					function (s) {
						search = s;
					},
					function (st) {
						stage = st;
					},
					search,
					stage
				);
			},
		});
	}
	refresh();
}

function renderLanding($root, data, refresh, setSearch, setStage, search, stage) {
	var rows = data.rows || [];
	var stages = data.stages || [];
	var total = data.total != null ? data.total : rows.length;
	var opts =
		'<option value="">' +
		esc(__("All")) +
		"</option>" +
		stages
			.map(function (s) {
				return (
					'<option value="' +
					esc(s) +
					'"' +
					(s === stage ? " selected" : "") +
					">" +
					esc(s) +
					"</option>"
				);
			})
			.join("");
	var body =
		rows.length === 0
			? '<tr><td colspan="6"><div class="kt-bs-empty" data-testid="kt-bs-empty-landing">' +
			  esc(__("No permitted tenders in the submission lifecycle.")) +
			  "</div></td></tr>"
			: rows
					.map(function (row) {
						return (
							"<tr data-testid='kt-bs-landing-row' data-publication-id='" +
							esc(row.publication_id) +
							"'>" +
							"<td><span class='kt-bs-ref'>" +
							esc(row.publication_ref || row.configuration_ref) +
							"</span><span class='kt-bs-title'>" +
							esc(row.tender_title) +
							"</span></td>" +
							"<td>" +
							esc(row.procuring_entity || "—") +
							"</td>" +
							"<td><span class='kt-bs-date'>" +
							esc(fmtDt(row.submission_deadline)) +
							"</span></td>" +
							"<td><span class='kt-bs-date'>" +
							esc(fmtDt(row.opening_datetime)) +
							"</span></td>" +
							"<td>" +
							statusPill(row.submission_stage) +
							"</td>" +
							"<td class='kt-bs-td-right'><button type='button' class='kt-bs-link' data-action='open-row' data-publication-id='" +
							esc(row.publication_id) +
							"'>" +
							esc((row.action && row.action.label) || __("View")) +
							"</button></td></tr>"
						);
					})
					.join("");

	$root.html(
		'<div class="kt-bs-canvas--wide" data-testid="kt-bs-landing">' +
			'<div class="kt-bs-header-block">' +
			'<nav class="kt-bs-crumb" aria-label="Breadcrumb">' +
			"<span>" +
			esc(__("Portal")) +
			"</span>" +
			icon("chevron_right") +
			"<span>" +
			esc(__("Tendering")) +
			"</span>" +
			icon("chevron_right") +
			'<span class="kt-bs-crumb__current">' +
			esc(__("Bid Submissions")) +
			"</span></nav>" +
			'<h2 class="kt-bs-headline">' +
			esc(__("Bid Submissions")) +
			"</h2>" +
			'<p class="kt-bs-lead">' +
			esc(
				__(
					"View tenders receiving submissions and access bids after authorised opening."
				)
			) +
			"</p></div>" +
			'<div class="kt-bs-filters">' +
			'<div class="kt-bs-filters__search">' +
			icon("search") +
			'<input type="search" data-testid="kt-bs-search" placeholder="' +
			esc(__("Search by tender reference or title")) +
			'" value="' +
			esc(search || "") +
			'"/></div>' +
			'<div class="kt-bs-filters__stage">' +
			'<label class="kt-bs-label-caps" for="kt-bs-stage-filter">' +
			esc(__("Stage:")) +
			"</label>" +
			'<select id="kt-bs-stage-filter" data-testid="kt-bs-stage-filter">' +
			opts +
			"</select></div>" +
			'<button type="button" class="kt-bs-filters__icon-btn" data-action="refresh" title="' +
			esc(__("Apply filters")) +
			'" aria-label="' +
			esc(__("Apply filters")) +
			'">' +
			icon("filter_list") +
			"</button></div>" +
			'<div class="kt-bs-table-card">' +
			'<div class="kt-bs-table-card__scroll"><table class="kt-bs-table"><thead><tr>' +
			"<th>" +
			esc(__("Tender Information")) +
			"</th><th>" +
			esc(__("Procuring Entity")) +
			"</th><th>" +
			esc(__("Submission Deadline")) +
			"</th><th>" +
			esc(__("Opening Date")) +
			"</th><th>" +
			esc(__("Submission Stage")) +
			"</th><th class='kt-bs-th-right'>" +
			esc(__("Actions")) +
			"</th></tr></thead><tbody>" +
			body +
			"</tbody></table></div>" +
			'<div class="kt-bs-pager"><p>' +
			esc(__("Showing")) +
			" <strong>" +
			esc(String(rows.length)) +
			"</strong> " +
			esc(__("of")) +
			" <strong>" +
			esc(String(total)) +
			"</strong> " +
			esc(__("tenders")) +
			"</p></div></div>" +
			'<div class="kt-bs-info-banner">' +
			icon("info") +
			"<div><h4>" +
			esc(__("Confidentiality Protocol")) +
			"</h4><p>" +
			esc(
				__(
					"Bidder identities and financial details remain sealed until authorised opening. The Opening Register is available only after bids are opened."
				)
			) +
			"</p></div></div></div>"
	);

	function applyFilters() {
		setSearch($root.find("[data-testid='kt-bs-search']").val() || "");
		setStage($root.find("[data-testid='kt-bs-stage-filter']").val() || "");
		refresh();
	}
	$root.find("[data-action='refresh']").on("click", applyFilters);
	$root.find("[data-testid='kt-bs-search']").on("keydown", function (e) {
		if (e.key === "Enter") {
			e.preventDefault();
			applyFilters();
		}
	});
	$root.find("[data-testid='kt-bs-stage-filter']").on("change", applyFilters);
	$root.find("[data-action='open-row']").on("click", function (e) {
		e.preventDefault();
		e.stopPropagation();
		var pubId = $(this).attr("data-publication-id");
		if (pubId) {
			go(pubId);
		}
	});
}

function loadPublicationView($root, publicationId, token) {
	$root.html('<div class="kt-bs-empty">' + esc(__("Loading…")) + "</div>");
	frappe.call({
		method: "kentender_procurement.tender_configurations.list_bid_submission_tenders",
		args: { page: 1, page_size: 100 },
		callback: function (lr) {
			if (!stillCurrent(token)) {
				return;
			}
			var row = ((lr.message && lr.message.rows) || []).find(function (r) {
				return r.publication_id === publicationId;
			});
			var stage = (row && row.submission_stage) || "";
			if (stage === "Opened" || stage === "Released to evaluation") {
				loadRegister($root, publicationId, token);
				return;
			}
			if (stage === "Receiving submissions") {
				renderReceiving($root, row || { publication_id: publicationId });
				return;
			}
			loadSealed($root, publicationId, token);
		},
	});
}

function detailHeader(opts) {
	return (
		'<header class="kt-bs-detail-header">' +
		'<div class="kt-bs-detail-header__main">' +
		'<div class="kt-bs-detail-header__badges">' +
		'<span class="kt-bs-ref-badge">' +
		esc(opts.ref || "—") +
		"</span>" +
		statusPill(opts.stage, { withLock: !!opts.lockPill }) +
		"</div>" +
		'<h1 class="kt-bs-headline" style="color:var(--kt-bs-on-surface)">' +
		esc(opts.title || __("Tender")) +
		"</h1>" +
		'<p class="kt-bs-pe">' +
		icon("corporate_fare") +
		esc(opts.pe || "—") +
		"</p></div>" +
		'<div class="kt-bs-detail-header__meta">' +
		'<div class="kt-bs-meta-field"><span class="kt-bs-label-caps">' +
		esc(__("Submission Deadline")) +
		'</span><div class="kt-bs-meta-field__value">' +
		icon("calendar_today") +
		"<span>" +
		esc(fmtDt(opts.deadline)) +
		"</span></div></div>" +
		'<div class="kt-bs-meta-field"><span class="kt-bs-label-caps">' +
		esc(__("Scheduled Opening")) +
		'</span><div class="kt-bs-meta-field__value">' +
		icon("schedule") +
		"<span>" +
		esc(fmtDt(opts.opening)) +
		"</span></div></div></div></header>"
	);
}

function renderReceiving($root, row) {
	$root.html(
		'<div class="kt-bs-canvas" data-testid="kt-bs-receiving">' +
			backBtn("back") +
			detailHeader({
				ref: (row && (row.publication_ref || row.configuration_ref)) || "—",
				stage: __("Receiving submissions"),
				title: (row && row.tender_title) || __("Tender"),
				pe: (row && row.procuring_entity) || "—",
				deadline: row && row.submission_deadline,
				opening: row && row.opening_datetime,
			}) +
			'<div class="kt-bs-vault-card"><div class="kt-bs-vault" data-testid="kt-bs-receiving-vault">' +
			'<div class="kt-bs-vault__icon-wrap"><div class="kt-bs-vault__glow"></div>' +
			'<div class="kt-bs-vault__icon">' +
			icon("lock_clock") +
			"</div></div>" +
			"<div><h3>" +
			esc(__("Receiving submissions")) +
			"</h3><p>" +
			esc(
				__(
					"This tender is still receiving submissions. Bids remain sealed until after the deadline and authorised opening."
				)
			) +
			"</p></div></div></div></div>"
	);
	$root.find("[data-action='back']").on("click", function () {
		go();
	});
}

function loadSealed($root, publicationId, token) {
	frappe.call({
		method: "kentender_procurement.tender_configurations.get_bid_submission_sealed_status",
		args: { publication_id: publicationId },
		callback: function (r) {
			if (!stillCurrent(token)) {
				return;
			}
			if (r.exc) {
				$root.html(
					'<div class="kt-bs-empty">' + esc(__("Unable to load sealed status.")) + "</div>"
				);
				return;
			}
			renderSealed($root, r.message || {});
		},
	});
}

function renderSealed($root, data) {
	var canOpen = !!data.can_open_submitted_bids;
	var cta = canOpen
		? '<button type="button" class="kt-bs-btn kt-bs-btn--primary" data-action="open-confirm" data-testid="kt-bs-open-bids">' +
		  icon("lock_open") +
		  esc(__("Open submitted bids")) +
		  "</button>"
		: '<div data-testid="kt-bs-waiting" class="kt-bs-pill kt-bs-pill--opening" style="padding:12px 20px">' +
		  icon("schedule") +
		  "<span>" +
		  esc(__("Waiting for authorised bid opening…")) +
		  "</span></div>";

	$root.html(
		'<div class="kt-bs-canvas" data-testid="kt-bs-sealed">' +
			backBtn("back") +
			detailHeader({
				ref: data.publication_ref || data.configuration_ref || "—",
				stage: data.status_label || __("Closed and sealed"),
				lockPill: true,
				title: data.tender_title || __("Tender"),
				pe: data.procuring_entity || "—",
				deadline: data.submission_deadline,
				opening: data.opening_datetime,
			}) +
			'<div class="kt-bs-vault-card">' +
			'<div class="kt-bs-vault" data-testid="kt-bs-vault">' +
			'<div class="kt-bs-vault__icon-wrap"><div class="kt-bs-vault__glow"></div>' +
			'<div class="kt-bs-vault__icon">' +
			icon("encrypted") +
			"</div></div>" +
			"<div><h3>" +
			esc(__("Bids remain sealed")) +
			"</h3><p>" +
			esc(
				__(
					"Submitted bids cannot be viewed until the authorised bid-opening process is completed."
				)
			) +
			"</p></div>" +
			'<div class="kt-bs-vault__actions">' +
			cta +
			"</div></div>" +
			'<div class="kt-bs-vault-foot">' +
			'<div class="kt-bs-vault-foot__items">' +
			'<span class="kt-bs-vault-foot__item">' +
			icon("visibility_off") +
			esc(__("Identities occluded until open")) +
			"</span>" +
			'<span class="kt-bs-vault-foot__item">' +
			icon("verified_user") +
			esc(__("Opening actions audited")) +
			"</span></div></div></div>" +
			'<div class="kt-bs-supplement">' +
			'<div class="kt-bs-supplement__card"><h3>' +
			icon("visibility_off") +
			esc(__("Privacy Protocol")) +
			"</h3><p>" +
			esc(
				__(
					"Bidder identity and financial information stay hidden until the electronic seal is officially broken."
				)
			) +
			"</p></div>" +
			'<div class="kt-bs-supplement__card"><h3>' +
			icon("history") +
			esc(__("Audit Trail")) +
			"</h3><p>" +
			esc(
				__(
					"Authorised opening creates an immutable opening record and submission register for this tender."
				)
			) +
			"</p></div></div></div>"
	);
	$root.find("[data-action='back']").on("click", function () {
		go();
	});
	$root.find("[data-action='open-confirm']").on("click", function () {
		showOpenDialog($root, data);
	});
}

function showOpenDialog($root, data) {
	var $backdrop = $(
		'<div class="kt-bs-dialog-backdrop" data-testid="kt-bs-open-dialog">' +
			'<div class="kt-bs-dialog" role="dialog" aria-modal="true">' +
			'<div class="kt-bs-dialog__body">' +
			"<h3>" +
			esc(__("Open submitted bids?")) +
			"</h3>" +
			'<div class="kt-bs-dialog__panel">' +
			'<div class="kt-bs-dialog__field"><span class="kt-bs-label-caps">' +
			esc(__("Tender Reference")) +
			'</span><span class="kt-bs-mono" style="color:var(--kt-bs-primary)">' +
			esc(data.publication_ref || "") +
			"</span></div>" +
			'<div class="kt-bs-dialog__field"><span class="kt-bs-label-caps">' +
			esc(__("Tender Title")) +
			"</span><span>" +
			esc(data.tender_title || "") +
			"</span></div>" +
			'<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;padding-top:8px">' +
			'<div class="kt-bs-dialog__field"><span class="kt-bs-label-caps">' +
			esc(__("Submission Deadline")) +
			'</span><span class="kt-bs-mono" style="font-size:12px">' +
			esc(fmtDt(data.submission_deadline)) +
			"</span></div>" +
			'<div class="kt-bs-dialog__field"><span class="kt-bs-label-caps">' +
			esc(__("Scheduled Opening")) +
			'</span><span class="kt-bs-mono" style="font-size:12px">' +
			esc(fmtDt(data.opening_datetime)) +
			"</span></div></div></div>" +
			'<p class="kt-bs-dialog__warn">' +
			esc(
				__(
					"Opening will make the submitted bids visible to authorised users and create the official submission register. This action will be recorded."
				)
			) +
			"</p></div>" +
			'<div class="kt-bs-dialog-actions">' +
			'<button type="button" class="kt-bs-btn kt-bs-btn--muted" data-action="cancel">' +
			esc(__("Cancel")) +
			"</button>" +
			'<button type="button" class="kt-bs-btn kt-bs-btn--dark" data-action="confirm-open" data-testid="kt-bs-confirm-open">' +
			esc(__("Open bids")) +
			"</button></div></div></div>"
	);
	$("body").append($backdrop);
	$backdrop.on("click", "[data-action='cancel']", function () {
		$backdrop.remove();
	});
	$backdrop.on("click", function (e) {
		if (e.target === $backdrop[0]) {
			$backdrop.remove();
		}
	});
	$backdrop.on("click", "[data-action='confirm-open']", function () {
		var $btn = $(this);
		$btn.prop("disabled", true);
		frappe.call({
			method: "kentender_procurement.tender_configurations.open_submitted_bids",
			args: { publication_id: data.publication_id },
			callback: function (r) {
				$backdrop.remove();
				if (r.exc) {
					return;
				}
				frappe.show_alert({ message: __("Bids opened"), indicator: "green" }, 4);
				go(data.publication_id);
			},
			error: function () {
				$btn.prop("disabled", false);
			},
		});
	});
}

function loadRegister($root, publicationId, token) {
	$root.html('<div class="kt-bs-empty">' + esc(__("Loading…")) + "</div>");
	frappe.call({
		method: "kentender_procurement.tender_configurations.get_opening_register",
		args: { publication_id: publicationId },
		callback: function (r) {
			if (!stillCurrent(token)) {
				return;
			}
			if (r.exc) {
				$root.html(
					'<div class="kt-bs-empty">' + esc(__("Unable to load register.")) + "</div>"
				);
				return;
			}
			renderRegister($root, r.message || {});
		},
	});
}

function renderRegister($root, data) {
	var rows = data.rows || [];
	var body;
	if (data.empty) {
		body =
			'<div class="kt-bs-empty" data-testid="kt-bs-no-bids"><h3>' +
			esc(data.empty_title || __("No bids were received")) +
			"</h3><p>" +
			esc(
				data.empty_message ||
					__("No active bid submissions were recorded for this tender.")
			) +
			"</p></div>";
	} else {
		body =
			'<div class="kt-bs-table-card"><div class="kt-bs-table-card__scroll">' +
			'<table class="kt-bs-table" data-testid="kt-bs-register-table"><thead><tr>' +
			"<th>" +
			esc(__("Tenderer")) +
			"</th><th>" +
			esc(__("Submission Receipt")) +
			"</th><th>" +
			esc(__("Submitted At")) +
			"</th><th>" +
			esc(__("Lots")) +
			"</th><th>" +
			esc(__("Offer Type")) +
			"</th><th>" +
			esc(__("Status")) +
			"</th><th class='kt-bs-th-right'>" +
			esc(__("Actions")) +
			"</th></tr></thead><tbody>" +
			rows
				.map(function (row) {
					var lots = (row.lots || []).join(", ") || "—";
					var offer =
						row.offer_type === "Alternative"
							? __("Alternative offer")
							: __("Main offer");
					return (
						"<tr data-testid='kt-bs-register-row'>" +
						"<td><div style='font-weight:700'>" +
						esc(row.tenderer) +
						"</div></td>" +
						"<td><span class='kt-bs-date'>" +
						esc(row.receipt_code) +
						"</span></td>" +
						"<td><span class='kt-bs-date'>" +
						esc(fmtDt(row.submitted_at)) +
						"</span></td>" +
						"<td>" +
						esc(lots) +
						"</td><td>" +
						esc(offer) +
						"</td><td>" +
						'<span class="kt-bs-status-inline"><span class="kt-bs-status-inline__dot"></span>' +
						esc(row.status || __("Opened")) +
						"</span></td>" +
						"<td class='kt-bs-td-right'><div class='kt-bs-btn-row'>" +
						"<button type='button' class='kt-bs-btn kt-bs-btn--solid-sm' data-action='view-bid' data-bid-id='" +
						esc(row.bid_id) +
						"'>" +
						esc(__("View bid")) +
						"</button>" +
						"<button type='button' class='kt-bs-btn kt-bs-btn--outline' data-action='view-receipt' data-bid-id='" +
						esc(row.bid_id) +
						"'>" +
						esc(__("View receipt")) +
						"</button></div></td></tr>"
					);
				})
				.join("") +
			"</tbody></table></div></div>";
	}

	var activeN = data.active_bids_opened != null ? data.active_bids_opened : rows.length;

	$root.html(
		'<div class="kt-bs-canvas" data-testid="kt-bs-register">' +
			backBtn("back") +
			'<div class="kt-bs-register-head">' +
			'<div class="kt-bs-register-head__ref">' +
			esc(data.publication_ref || data.configuration_ref || "") +
			"</div>" +
			'<div class="kt-bs-register-head__title-row">' +
			'<h1 class="kt-bs-headline">' +
			esc(data.tender_title || __("Submission Register")) +
			"</h1>" +
			statusPill(__("Opened")) +
			"</div>" +
			'<p class="kt-bs-register-head__pe">' +
			esc(__("Procuring Entity:")) +
			" <strong>" +
			esc(data.procuring_entity || "—") +
			"</strong></p>" +
			'<div class="kt-bs-register-head__meta">' +
			'<div class="kt-bs-register-head__meta-item">' +
			icon("event_available") +
			esc(__("Opened date and time:")) +
			" <strong>" +
			esc(fmtDt(data.opened_at)) +
			"</strong></div>" +
			'<div class="kt-bs-register-head__divider"></div>' +
			'<div class="kt-bs-register-head__meta-item kt-bs-register-head__meta-item--accent">' +
			icon("how_to_reg") +
			"<strong>" +
			esc(__("{0} active bids opened", [String(activeN)])) +
			"</strong></div></div></div>" +
			body +
			'<footer class="kt-bs-register-foot">' +
			'<div class="kt-bs-register-foot__links">' +
			'<button type="button" class="kt-bs-foot-link" data-action="opening-record">' +
			icon("description") +
			esc(__("View opening record")) +
			"</button></div>" +
			'<div class="kt-bs-register-foot__end">' +
			esc(__("End of Register")) +
			"</div></footer></div>"
	);
	$root.find("[data-action='back']").on("click", function () {
		go();
	});
	$root.find("[data-action='opening-record']").on("click", function () {
		go(data.publication_id, "opening-record");
	});
	$root.find("[data-action='view-bid']").on("click", function () {
		go(data.publication_id, "bid", $(this).attr("data-bid-id"));
	});
	$root.find("[data-action='view-receipt']").on("click", function () {
		go(data.publication_id, "bid", $(this).attr("data-bid-id"), "receipt");
	});
}

function loadBidOverview($root, publicationId, bidId, token) {
	$root.html('<div class="kt-bs-empty">' + esc(__("Loading…")) + "</div>");
	frappe.call({
		method: "kentender_procurement.tender_configurations.get_submitted_bid_overview",
		args: { publication_id: publicationId, bid_id: bidId },
		callback: function (r) {
			if (!stillCurrent(token)) {
				return;
			}
			if (r.exc) {
				$root.html('<div class="kt-bs-empty">' + esc(__("Unable to load bid.")) + "</div>");
				return;
			}
			renderBidOverview($root, r.message || {});
		},
	});
}

function renderBidOverview($root, data) {
	var sections = data.sections || [];
	var lots = (data.lots || []).join(", ") || "—";
	var body =
		'<div class="kt-bs-table-card">' +
		'<div class="kt-bs-panel-head">' +
		'<h3 class="kt-bs-headline-sm">' +
		esc(__("Submission Package Details")) +
		"</h3></div>" +
		'<div class="kt-bs-table-card__scroll">' +
		'<table class="kt-bs-table" data-testid="kt-bs-bid-sections"><thead><tr>' +
		"<th>" +
		esc(__("Bid Section")) +
		"</th><th>" +
		esc(__("Submission Status")) +
		"</th><th class='kt-bs-th-right'>" +
		esc(__("Action")) +
		"</th></tr></thead><tbody>" +
		sections
			.map(function (s) {
				var ic = sectionIcon(s.section_key, s.label);
				var submitted =
					String(s.submission_status || "").toLowerCase().indexOf("submit") >= 0;
				return (
					"<tr><td><div class='kt-bs-section-cell'>" +
					icon(ic) +
					'<span class="kt-bs-section-cell__label">' +
					esc(s.label) +
					"</span></div></td><td>" +
					(submitted
						? '<span class="kt-bs-submitted">' +
						  icon("check_circle") +
						  esc(s.submission_status || __("Submitted")) +
						  "</span>"
						: esc(s.submission_status || "—")) +
					"</td><td class='kt-bs-td-right'><button type='button' class='kt-bs-link kt-bs-link--secondary' data-action='review' data-section='" +
					esc(s.section_key) +
					"'>" +
					esc(__("Review")) +
					"</button></td></tr>"
				);
			})
			.join("") +
		"</tbody></table></div></div>";

	$root.html(
		'<div class="kt-bs-canvas" data-testid="kt-bs-bid-overview">' +
			backBtn("back-reg", __("Back to Submission Register")) +
			'<section class="kt-bs-overview-head">' +
			"<div>" +
			'<div class="kt-bs-badge-row">' +
			'<span class="kt-bs-badge kt-bs-badge--primary">' +
			esc(data.read_only_label || __("Read-only submitted bid")) +
			"</span>" +
			'<span class="kt-bs-badge kt-bs-badge--ok">' +
			esc(data.status || __("Opened")) +
			"</span></div>" +
			'<h2 class="kt-bs-headline">' +
			esc(data.tenderer || __("Submitted bid")) +
			"</h2>" +
			'<div class="kt-bs-overview-sub">' +
			icon("description") +
			"<span>" +
			esc(data.publication_ref || "") +
			" | " +
			esc(data.tender_title || "") +
			"</span></div></div>" +
			'<div class="kt-bs-overview-meta">' +
			"<div><span class='kt-bs-label-caps'>" +
			esc(__("Submission Receipt")) +
			"</span><p class='kt-bs-mono'>" +
			esc(data.receipt_code) +
			"</p></div>" +
			"<div><span class='kt-bs-label-caps'>" +
			esc(__("Submitted Date")) +
			"</span><p>" +
			esc(fmtDt(data.submitted_at)) +
			"</p></div>" +
			"<div><span class='kt-bs-label-caps'>" +
			esc(__("Applicable Lots")) +
			"</span><p>" +
			esc(lots) +
			"</p></div>" +
			"<div><span class='kt-bs-label-caps'>" +
			esc(__("Offer Type")) +
			"</span><p>" +
			esc(data.offer_type || "—") +
			"</p></div></div></section>" +
			body +
			"</div>"
	);
	$root.find("[data-action='back-reg']").on("click", function () {
		go(data.publication_id);
	});
	$root.find("[data-action='review']").on("click", function () {
		go(data.publication_id, "bid", data.bid_id, "section", $(this).attr("data-section"));
	});
}

function loadSection($root, publicationId, bidId, sectionKey, token) {
	$root.html('<div class="kt-bs-empty">' + esc(__("Loading…")) + "</div>");
	frappe.call({
		method: "kentender_procurement.tender_configurations.get_submitted_section_response",
		args: {
			publication_id: publicationId,
			bid_id: bidId,
			section_key: sectionKey,
		},
		callback: function (r) {
			if (!stillCurrent(token)) {
				return;
			}
			if (r.exc) {
				$root.html(
					'<div class="kt-bs-empty">' + esc(__("Unable to load section.")) + "</div>"
				);
				return;
			}
			renderSection($root, r.message || {});
		},
	});
}

function renderSection($root, data) {
	var payload = data.payload || {};
	var pretty = JSON.stringify(payload, null, 2);
	$root.html(
		'<div class="kt-bs-canvas" data-testid="kt-bs-section-review">' +
			backBtn("back-bid", __("Back to Submitted Bid")) +
			'<div class="kt-bs-section-badge">' +
			esc(__("Submitted response — read only")) +
			"</div>" +
			'<h1 class="kt-bs-headline">' +
			esc(data.section_label || data.section_key) +
			"</h1>" +
			'<div class="kt-bs-section-meta-row">' +
			"<span><span class='kt-bs-label-caps'>" +
			esc(__("Tenderer:")) +
			"</span><strong>" +
			esc(data.tenderer) +
			"</strong></span>" +
			"<span><span class='kt-bs-label-caps'>" +
			esc(__("Ref:")) +
			'</span><span class="kt-bs-mono">' +
			esc(data.publication_ref) +
			"</span></span>" +
			"<span><span class='kt-bs-label-caps'>" +
			esc(__("Receipt:")) +
			'</span><span class="kt-bs-mono">' +
			esc(data.receipt_code) +
			"</span></span></div>" +
			'<div class="kt-bs-section-block" style="margin-top:24px">' +
			'<div class="kt-bs-section-block__inner">' +
			'<h2 class="kt-bs-section-block__title">' +
			esc(__("Submitted content")) +
			"</h2>" +
			'<div class="kt-bs-section-payload" data-testid="kt-bs-section-payload">' +
			esc(pretty) +
			"</div></div></div>" +
			'<div class="kt-bs-nav-row">' +
			(data.previous_section_key
				? '<button type="button" class="kt-bs-btn kt-bs-btn--muted" data-action="prev" data-section="' +
				  esc(data.previous_section_key) +
				  '">' +
				  esc(__("Previous section")) +
				  "</button>"
				: "<span></span>") +
			(data.next_section_key
				? '<button type="button" class="kt-bs-btn kt-bs-btn--dark" data-action="next" data-section="' +
				  esc(data.next_section_key) +
				  '">' +
				  esc(__("Next section")) +
				  "</button>"
				: "<span></span>") +
			"</div></div>"
	);
	$root.find("[data-action='back-bid']").on("click", function () {
		go(data.publication_id, "bid", data.bid_id);
	});
	$root.find("[data-action='prev'],[data-action='next']").on("click", function () {
		go(data.publication_id, "bid", data.bid_id, "section", $(this).attr("data-section"));
	});
}

function loadReceipt($root, publicationId, bidId, token) {
	frappe.call({
		method: "kentender_procurement.tender_configurations.get_submission_receipt_view",
		args: { publication_id: publicationId, bid_id: bidId },
		callback: function (r) {
			if (!stillCurrent(token)) {
				return;
			}
			if (r.exc) {
				$root.html('<div class="kt-bs-empty">' + esc(__("Unable to load receipt.")) + "</div>");
				return;
			}
			var d = r.message || {};
			$root.html(
				'<div class="kt-bs-canvas" data-testid="kt-bs-receipt">' +
					backBtn("back", __("Back to Submitted Bid")) +
					'<h2 class="kt-bs-headline">' +
					esc(__("Submission receipt")) +
					"</h2>" +
					'<div class="kt-bs-table-card" style="margin-top:24px;padding:20px">' +
					'<div class="kt-bs-overview-meta" style="border:none;padding:0;grid-template-columns:1fr 1fr">' +
					"<div><span class='kt-bs-label-caps'>" +
					esc(__("Tender")) +
					"</span><p>" +
					esc(d.publication_ref) +
					" — " +
					esc(d.tender_title) +
					"</p></div>" +
					"<div><span class='kt-bs-label-caps'>" +
					esc(__("Tenderer")) +
					"</span><p style='font-weight:700'>" +
					esc(d.tenderer) +
					"</p></div>" +
					"<div><span class='kt-bs-label-caps'>" +
					esc(__("Receipt")) +
					"</span><p class='kt-bs-mono'>" +
					esc(d.receipt_code) +
					"</p></div>" +
					"<div><span class='kt-bs-label-caps'>" +
					esc(__("Submitted")) +
					"</span><p>" +
					esc(fmtDt(d.submitted_at)) +
					"</p></div>" +
					"<div><span class='kt-bs-label-caps'>" +
					esc(__("Offer type")) +
					"</span><p>" +
					esc(d.offer_type) +
					"</p></div>" +
					"<div><span class='kt-bs-label-caps'>" +
					esc(__("Status")) +
					"</span><p>" +
					esc(d.status) +
					"</p></div></div></div></div>"
			);
			$root.find("[data-action='back']").on("click", function () {
				go(publicationId, "bid", bidId);
			});
		},
	});
}

function loadOpeningRecord($root, publicationId, token) {
	frappe.call({
		method: "kentender_procurement.tender_configurations.get_opening_record_view",
		args: { publication_id: publicationId },
		callback: function (r) {
			if (!stillCurrent(token)) {
				return;
			}
			if (r.exc) {
				$root.html(
					'<div class="kt-bs-empty">' + esc(__("Unable to load opening record.")) + "</div>"
				);
				return;
			}
			var d = r.message || {};
			var receipts = (d.receipt_refs || []).join(", ") || "—";
			$root.html(
				'<div class="kt-bs-canvas" data-testid="kt-bs-opening-record">' +
					backBtn("back") +
					'<h2 class="kt-bs-headline">' +
					esc(__("Opening record")) +
					"</h2>" +
					'<div class="kt-bs-table-card" style="margin-top:24px;padding:20px">' +
					'<div class="kt-bs-overview-meta" style="border:none;padding:0;grid-template-columns:1fr 1fr">' +
					"<div><span class='kt-bs-label-caps'>" +
					esc(__("Tender")) +
					"</span><p>" +
					esc(d.publication_ref) +
					" — " +
					esc(d.tender_title) +
					"</p></div>" +
					"<div><span class='kt-bs-label-caps'>" +
					esc(__("Scheduled opening")) +
					"</span><p class='kt-bs-mono'>" +
					esc(fmtDt(d.scheduled_opening_datetime)) +
					"</p></div>" +
					"<div><span class='kt-bs-label-caps'>" +
					esc(__("Actual opening")) +
					"</span><p class='kt-bs-mono'>" +
					esc(fmtDt(d.opened_at)) +
					"</p></div>" +
					"<div><span class='kt-bs-label-caps'>" +
					esc(__("Opened by")) +
					"</span><p>" +
					esc(d.opened_by || "—") +
					"</p></div>" +
					"<div><span class='kt-bs-label-caps'>" +
					esc(__("Active bids opened")) +
					"</span><p>" +
					esc(d.active_bids_opened != null ? String(d.active_bids_opened) : "—") +
					"</p></div>" +
					"<div><span class='kt-bs-label-caps'>" +
					esc(__("Receipts")) +
					"</span><p class='kt-bs-mono'>" +
					esc(receipts) +
					"</p></div>" +
					"<div><span class='kt-bs-label-caps'>" +
					esc(__("Opening status")) +
					"</span><p>" +
					esc(d.opening_status || "—") +
					"</p></div></div></div></div>"
			);
			$root.find("[data-action='back']").on("click", function () {
				go(publicationId);
			});
		},
	});
}
