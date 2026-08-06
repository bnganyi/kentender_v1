/* global frappe */
/* Procurement Home — dedicated Desk page (Stitch main content, section updates). */
(function () {
	"use strict";

	var _state = {
		mounted: false,
		loading: false,
		requestId: 0,
		context: null,
		visibility: null,
		actions: null,
		pipeline: null,
		deadlines: null,
		portfolio: null,
	};

	function _esc(s) {
		if (s == null) return "";
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function _ensureFonts() {
		if (document.getElementById("kt-ph-fonts")) return;
		var link = document.createElement("link");
		link.id = "kt-ph-fonts";
		link.rel = "stylesheet";
		link.href =
			"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@600;700;800&family=JetBrains+Mono:wght@500;600&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap";
		document.head.appendChild(link);
	}

	function _host(wrapper) {
		return (
			wrapper.querySelector(".layout-main-section") ||
			wrapper.querySelector(".page-body") ||
			wrapper
		);
	}

	function _mountShell(host) {
		if (host.querySelector("#kt-ph-root")) {
			_state.mounted = true;
			return;
		}
		host.innerHTML =
			'<div class="kt-ph-root" id="kt-ph-root" data-testid="kt-ph-root">' +
			'  <header class="kt-ph-header" data-testid="kt-ph-header">' +
			'    <div><h1 class="kt-ph-title" data-testid="kt-ph-title">Procurement Home</h1>' +
			'    <p class="kt-ph-subtitle">Review your procurement work, deadlines and portfolio.</p></div>' +
			'    <div class="kt-ph-context" data-testid="kt-ph-context"></div>' +
			"  </header>" +
			'  <section class="kt-ph-section" data-testid="kt-ph-actions-section">' +
			'    <div class="kt-ph-card" id="kt-ph-actions" data-testid="kt-ph-actions"><div class="kt-ph-loading">Loading actions…</div></div>' +
			"  </section>" +
			'  <section class="kt-ph-section" data-testid="kt-ph-pipeline-section">' +
			'    <div class="kt-ph-card kt-ph-pipeline-body" id="kt-ph-pipeline" data-testid="kt-ph-pipeline"><div class="kt-ph-loading">Loading pipeline…</div></div>' +
			"  </section>" +
			'  <div class="kt-ph-split" id="kt-ph-split" data-testid="kt-ph-split">' +
			'    <section class="kt-ph-deadlines" id="kt-ph-deadlines-wrap"><div class="kt-ph-card" id="kt-ph-deadlines" data-testid="kt-ph-deadlines"><div class="kt-ph-loading">Loading deadlines…</div></div></section>' +
			'    <section class="kt-ph-portfolio" id="kt-ph-portfolio-wrap"><div class="kt-ph-card" id="kt-ph-portfolio" data-testid="kt-ph-portfolio"><div class="kt-ph-loading">Loading portfolio…</div></div></section>' +
			"  </div>" +
			"</div>";
		_state.mounted = true;
		_bindContextHandlers(host);
	}

	function _bindContextHandlers(host) {
		var root = host.querySelector("#kt-ph-root");
		if (!root || root.__ktPhBound) return;
		root.__ktPhBound = true;
		root.addEventListener("change", function (e) {
			var t = e.target;
			if (!t || !t.getAttribute) return;
			if (t.getAttribute("data-testid") === "kt-ph-entity" || t.getAttribute("data-testid") === "kt-ph-fy") {
				_loadHome();
			}
		});
		root.addEventListener("click", function (e) {
			var btn = e.target.closest("[data-kt-ph-nav]");
			if (!btn) return;
			e.preventDefault();
			var url = btn.getAttribute("data-kt-ph-nav");
			if (!url) return;
			if (url.indexOf("/desk/") === 0) {
				var path = url.replace(/^\/desk\//, "");
				frappe.set_route.apply(frappe, path.split("/"));
			} else {
				window.location.href = url;
			}
		});
	}

	function _selectedContextArgs() {
		var peEl = document.querySelector('[data-testid="kt-ph-entity"]');
		var fyEl = document.querySelector('[data-testid="kt-ph-fy"]');
		var args = {};
		if (peEl && peEl.tagName === "SELECT") args.procuring_entity = peEl.value;
		else if (_state.context && _state.context.procuring_entity) args.procuring_entity = _state.context.procuring_entity.id;
		if (fyEl && fyEl.tagName === "SELECT") args.fiscal_year = fyEl.value;
		else if (_state.context) args.fiscal_year = _state.context.fiscal_year;
		return args;
	}

	function _renderContext(ctx) {
		var el = document.querySelector('[data-testid="kt-ph-context"]');
		if (!el || !ctx) return;
		var pe = ctx.procuring_entity || {};
		var peHtml;
		if (ctx.show_entity_selector && (ctx.available_entities || []).length > 1) {
			peHtml =
				'<select data-testid="kt-ph-entity">' +
				(ctx.available_entities || [])
					.map(function (e) {
						var sel = e.id === pe.id ? " selected" : "";
						return (
							'<option value="' +
							_esc(e.id) +
							'"' +
							sel +
							">" +
							_esc(e.name) +
							(e.code ? " (" + _esc(e.code) + ")" : "") +
							"</option>"
						);
					})
					.join("") +
				"</select>";
		} else {
			peHtml =
				'<p class="kt-ph-context__value" data-testid="kt-ph-entity">' +
				_esc(pe.name || pe.code || "") +
				(pe.code && pe.name !== pe.code ? " (" + _esc(pe.code) + ")" : "") +
				"</p>";
		}
		var fyHtml;
		if (ctx.show_fiscal_year_selector && (ctx.available_fiscal_years || []).length > 1) {
			fyHtml =
				'<select data-testid="kt-ph-fy">' +
				(ctx.available_fiscal_years || [])
					.map(function (y) {
						var sel = String(y) === String(ctx.fiscal_year) ? " selected" : "";
						return '<option value="' + _esc(y) + '"' + sel + ">" + _esc(y) + "</option>";
					})
					.join("") +
				"</select>";
		} else {
			fyHtml =
				'<p class="kt-ph-context__value" data-testid="kt-ph-fy">' +
				_esc(ctx.fiscal_year) +
				"</p>";
		}
		el.innerHTML =
			"<div><p class=\"kt-ph-context__label\">Procuring Entity</p>" +
			peHtml +
			"</div><div><p class=\"kt-ph-context__label\">Financial Year</p>" +
			fyHtml +
			"</div>";
	}

	function _urgencyClass(u) {
		var key = String(u || "").toLowerCase().replace(/\s+/g, "-");
		if (key === "overdue" || key === "blocked") return "kt-ph-urgency--overdue";
		if (key === "due-soon" || key === "returned") return "kt-ph-urgency--due-soon";
		return "";
	}

	function _renderActions(section) {
		var el = document.getElementById("kt-ph-actions");
		if (!el) return;
		if (!section || section.error) {
			el.innerHTML =
				'<div class="kt-ph-unavailable" data-testid="kt-ph-actions-unavailable">This section is temporarily unavailable.</div>';
			return;
		}
		var items = section.items || [];
		if (section.empty || !items.length) {
			el.innerHTML =
				'<div class="kt-ph-card__head"><h3 class="kt-ph-card__title"><span class="material-symbols-outlined" style="color:var(--kt-ph-error,#ba1a1a)">hub</span>Requires Your Action</h3>' +
				'<span class="kt-ph-badge">0 Pending</span></div>' +
				'<div class="kt-ph-empty" data-testid="kt-ph-actions-empty">' +
				'<p class="kt-ph-empty__title">No actions require your attention</p>' +
				"<p>New approvals, returned work and other assigned actions will appear here.</p></div>";
			return;
		}
		var rows = items
			.map(function (item) {
				return (
					'<tr data-kt-ph-nav="' +
					_esc(item.target_url) +
					'">' +
					'<td><div class="kt-ph-table__title">' +
					_esc(item.title) +
					'</div><div class="kt-ph-table__ref">' +
					_esc(item.reference) +
					"</div></td>" +
					"<td>" +
					_esc(item.stage) +
					"</td>" +
					"<td><div class=\"kt-ph-urgency " +
					_urgencyClass(item.urgency) +
					'"><span class="kt-ph-urgency__dot"></span>' +
					_esc(item.urgency) +
					"</div><div>" +
					_esc(item.action_required) +
					"</div></td>" +
					'<td class="kt-ph-mono">' +
					_esc(item.due_date || "—") +
					"</td>" +
					'<td style="text-align:right"><button type="button" class="kt-ph-link-btn" data-kt-ph-nav="' +
					_esc(item.target_url) +
					'">' +
					_esc(item.action_label) +
					"</button></td></tr>"
				);
			})
			.join("");
		el.innerHTML =
			'<div class="kt-ph-card__head"><h3 class="kt-ph-card__title"><span class="material-symbols-outlined" style="color:var(--kt-ph-error,#ba1a1a)">hub</span>Requires Your Action</h3>' +
			'<span class="kt-ph-badge">' +
			_esc(section.pending_count || items.length) +
			" Pending</span></div>" +
			'<div class="overflow-x-auto"><table class="kt-ph-table"><thead><tr>' +
			"<th>Work item</th><th>Procurement stage</th><th>Action required</th><th>Due date</th><th style=\"text-align:right\">Action</th>" +
			"</tr></thead><tbody>" +
			rows +
			"</tbody></table></div>" +
			'<div class="kt-ph-footer-link"><button type="button" class="kt-ph-link-btn" data-kt-ph-nav="' +
			_esc(section.view_all_url || "/desk/demand-hub") +
			'">View all work <span class="material-symbols-outlined" style="font-size:16px;vertical-align:middle">arrow_forward</span></button></div>';
	}

	function _renderPipeline(section) {
		var el = document.getElementById("kt-ph-pipeline");
		if (!el) return;
		if (!section || section.error) {
			el.innerHTML =
				'<div class="kt-ph-unavailable" data-testid="kt-ph-pipeline-unavailable">This section is temporarily unavailable.</div>';
			return;
		}
		var stages = section.stages || [];
		var nodes = stages
			.map(function (s) {
				return (
					'<button type="button" class="kt-ph-pipe" data-kt-ph-nav="' +
					_esc(s.url) +
					'"><span class="kt-ph-pipe__count">' +
					_esc(s.count) +
					'</span><span class="kt-ph-pipe__label">' +
					_esc(s.label) +
					"</span></button>"
				);
			})
			.join("");
		el.innerHTML =
			'<h3 class="kt-ph-card__title" style="margin-bottom:8px"><span class="material-symbols-outlined">hub</span>Procurement Pipeline</h3>' +
			'<div class="kt-ph-pipeline-grid">' +
			nodes +
			"</div>";
	}

	function _deadlineActionIcon(item) {
		if (item && item.action_icon) return String(item.action_icon);
		var label = String((item && item.action_label) || "").toLowerCase();
		if (label.indexOf("review") >= 0) return "rate_review";
		if (label.indexOf("tender") >= 0) return "open_in_new";
		return "visibility";
	}

	function _renderDeadlines(section) {
		var el = document.getElementById("kt-ph-deadlines");
		if (!el) return;
		if (!section || section.error) {
			el.innerHTML =
				'<div class="kt-ph-unavailable" data-testid="kt-ph-deadlines-unavailable">This section is temporarily unavailable.</div>';
			return;
		}
		var items = section.items || [];
		var body;
		if (!items.length) {
			body =
				'<div class="kt-ph-empty" data-testid="kt-ph-deadlines-empty"><p class="kt-ph-empty__title">No upcoming procurement deadlines.</p></div>';
		} else {
			body = items
				.map(function (d) {
					var overdue = String(d.time_remaining || "").toLowerCase().indexOf("overdue") >= 0;
					var icon = _deadlineActionIcon(d);
					return (
						'<div class="kt-ph-deadline" data-testid="kt-ph-deadline-row" data-kt-ph-nav="' +
						_esc(d.target_url) +
						'"><div class="kt-ph-deadline__cal' +
						(overdue ? " kt-ph-deadline__cal--overdue" : "") +
						'"><span>' +
						_esc(d.display_date) +
						"</span><span>" +
						_esc(d.display_day) +
						'</span></div><div class="kt-ph-deadline__body"><p class="kt-ph-deadline__title">' +
						_esc(d.event) +
						": " +
						_esc(d.title) +
						'</p><p class="kt-ph-deadline__meta">' +
						_esc(d.time_remaining) +
						'</p><button type="button" class="kt-ph-deadline__action" data-kt-ph-nav="' +
						_esc(d.target_url) +
						'">' +
						_esc(d.action_label || "View") +
						'<span class="material-symbols-outlined" aria-hidden="true">' +
						_esc(icon) +
						"</span></button></div>" +
						'<span class="material-symbols-outlined kt-ph-deadline__chevron" aria-hidden="true">chevron_right</span></div>'
					);
				})
				.join("");
			body = '<div class="kt-ph-deadline-list">' + body + "</div>";
		}
		el.innerHTML =
			'<div class="kt-ph-card__head"><h3 class="kt-ph-card__title"><span class="material-symbols-outlined" style="color:var(--kt-ph-primary)">event_upcoming</span>Upcoming Deadlines</h3></div>' +
			body;
	}

	function _renderPortfolio(section, visibility) {
		var wrap = document.getElementById("kt-ph-portfolio-wrap");
		var el = document.getElementById("kt-ph-portfolio");
		var split = document.getElementById("kt-ph-split");
		if (!el || !wrap) return;
		var show = visibility && visibility.portfolio !== false && section && section.visible !== false;
		if (!show) {
			wrap.style.display = "none";
			if (split) split.classList.add("kt-ph-split--full");
			return;
		}
		wrap.style.display = "";
		if (split) split.classList.remove("kt-ph-split--full");
		if (section.error) {
			el.innerHTML =
				'<div class="kt-ph-unavailable" data-testid="kt-ph-portfolio-unavailable">This section is temporarily unavailable.</div>';
			return;
		}
		var figures = section.figures || [];
		var cards = figures
			.map(function (f) {
				var tone = f.tone && f.tone !== "default" ? " kt-ph-figure--" + f.tone : "";
				return (
					'<button type="button" class="kt-ph-figure' +
					tone +
					'" data-kt-ph-nav="' +
					_esc(f.url) +
					'"><p class="kt-ph-figure__label">' +
					_esc(f.label) +
					'</p><p class="kt-ph-figure__value">' +
					_esc(f.display) +
					"</p></button>"
				);
			})
			.join("");
		el.innerHTML =
			'<div class="kt-ph-card__head"><h3 class="kt-ph-card__title"><span class="material-symbols-outlined" style="color:var(--kt-ph-primary)">hub</span>Portfolio Snapshot</h3></div>' +
			'<div class="kt-ph-portfolio-grid">' +
			cards +
			"</div>";
	}

	function _applyPayload(payload) {
		_state.context = payload.context;
		_state.visibility = payload.visibility;
		_state.actions = payload.actions;
		_state.pipeline = payload.pipeline;
		_state.deadlines = payload.deadlines;
		_state.portfolio = payload.portfolio;
		_renderContext(payload.context);
		_renderActions(payload.actions);
		_renderPipeline(payload.pipeline);
		_renderDeadlines(payload.deadlines);
		_renderPortfolio(payload.portfolio, payload.visibility);
	}

	function _loadHome() {
		var rid = ++_state.requestId;
		_state.loading = true;
		frappe.call({
			method: "kentender_procurement.procurement_home.api.home.get_procurement_home",
			args: _selectedContextArgs(),
			callback: function (r) {
				if (rid !== _state.requestId) return;
				_state.loading = false;
				var msg = r && r.message;
				if (!msg || !msg.ok) {
					frappe.show_alert({ message: "Unable to load Procurement Home", indicator: "red" });
					return;
				}
				_applyPayload(msg);
			},
			error: function () {
				if (rid !== _state.requestId) return;
				_state.loading = false;
				frappe.show_alert({ message: "Unable to load Procurement Home", indicator: "red" });
			},
		});
	}

	function _setupSidebar(attempt) {
		attempt = attempt || 0;
		var sidebar = frappe.app && frappe.app.sidebar;
		if (sidebar && typeof sidebar.setup === "function") {
			sidebar.setup("Procurement");
			// Desk home hides the rail; setup alone does not restore display.
			var page = frappe.container && frappe.container.page && frappe.container.page.page;
			if ((!page || !page.hide_sidebar) && sidebar.wrapper && typeof sidebar.wrapper.show === "function") {
				sidebar.wrapper.show();
			}
			return;
		}
		if (attempt < 40) {
			setTimeout(function () {
				_setupSidebar(attempt + 1);
			}, 50);
		}
	}

	function _setBrowserTitle() {
		if (frappe.utils && typeof frappe.utils.set_title === "function") {
			frappe.utils.set_title("KenTender - Procurement Home");
		} else {
			document.title = "KenTender - Procurement Home";
		}
	}

	function _onShow(wrapper) {
		_ensureFonts();
		_setBrowserTitle();
		document.body.classList.add("kt-ph-page-shell");
		_setupSidebar();
		var host = _host(wrapper);
		_mountShell(host);
		_loadHome();
	}

	function _onHide() {
		document.body.classList.remove("kt-ph-page-shell");
	}

	frappe.pages["kt-procurement-home"].on_page_load = function (wrapper) {
		_ensureFonts();
		_mountShell(_host(wrapper));
	};

	frappe.pages["kt-procurement-home"].on_page_show = function (wrapper) {
		_onShow(wrapper);
	};

	frappe.pages["kt-procurement-home"].on_page_hide = function () {
		_onHide();
	};
})();
