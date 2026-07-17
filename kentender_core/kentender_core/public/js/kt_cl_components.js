// Civic Ledger components — HTML copied from B-Components/code.html (lines 311-356)
frappe.provide("kentender_core.cl_components");

(function () {
	"use strict";

	function spec() {
		return kentender_core.cl_code_spec || {};
	}

	function escapeHtml(value) {
		return String(value == null ? "" : value)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function msIcon(name, sizePx, extraClass) {
		return (
			'<span class="material-symbols-outlined' +
			(extraClass ? " " + extraClass : "") +
			'" style="font-size: ' +
			(sizePx || 20) +
			'px;" aria-hidden="true">' +
			escapeHtml(name) +
			"</span>"
		);
	}

	function initials(name) {
		var parts = String(name || "")
			.trim()
			.split(/\s+/)
			.filter(Boolean);
		if (!parts.length) return "U";
		if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
		return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
	}

	function sessionUserLabel() {
		try {
			return (frappe.session && frappe.session.user_fullname) || frappe.session.user || "User";
		} catch (e) {
			return "User";
		}
	}

	kentender_core.cl_components = {
		escapeHtml: escapeHtml,
		icon: msIcon,

		renderTopToolbar: function (opts) {
			opts = opts || {};
			var title = opts.title || "";
			var showSearch = opts.showSearch !== false;
			var searchPlaceholder =
				opts.searchPlaceholder || "Search APP, tenders, or departments...";
			var avatarUrl = opts.avatarUrl || "";

			// code.html lines 311-331
			var searchHtml = showSearch
				? '<div class="hidden md:flex relative mr-4">' +
					'<span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-on-surface-variant" style="font-size: 18px;" aria-hidden="true">search</span>' +
					'<input class="pl-8 pr-3 py-1 border border-outline-variant rounded-full bg-surface-container-lowest focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-body-md transition-colors w-64 h-7" placeholder="' +
					escapeHtml(searchPlaceholder) +
					'" type="text" data-testid="kt-cl-toolbar-search" aria-label="' +
					escapeHtml(__("Search")) +
					'" />' +
					"</div>"
				: "";

			var avatarHtml = avatarUrl
				? '<img alt="User profile avatar" class="w-full h-full object-cover" src="' +
					escapeHtml(avatarUrl) +
					'" />'
				: '<span class="font-body-md text-body-md font-bold">' +
					escapeHtml(initials(sessionUserLabel())) +
					"</span>";

			return (
				'<header class="' +
				spec().TOOLBAR_ROOT +
				'" data-testid="kt-cl-toolbar">' +
				'<div class="flex items-center gap-2 ml-2">' +
				'<h1 class="font-headline-md text-headline-md font-bold text-on-surface truncate max-w-[300px]" data-testid="kt-cl-toolbar-title">' +
				escapeHtml(title) +
				"</h1></div>" +
				'<div class="flex items-center gap-4"></div>' +
				'<div class="flex items-center gap-2">' +
				searchHtml +
				'<button type="button" class="p-1.5 rounded-full hover:bg-surface-container-low transition-colors cursor-pointer active:opacity-80 text-primary" data-testid="kt-cl-toolbar-notifications" aria-label="' +
				escapeHtml(__("Notifications")) +
				'">' +
				msIcon("notifications", 20) +
				"</button>" +
				'<button type="button" class="p-1.5 rounded-full hover:bg-surface-container-low transition-colors cursor-pointer active:opacity-80 text-on-surface-variant" data-testid="kt-cl-toolbar-help" aria-label="' +
				escapeHtml(__("Help")) +
				'">' +
				msIcon("help_outline", 20) +
				"</button>" +
				'<div class="ml-2 w-7 h-7 rounded-full overflow-hidden border border-outline-variant cursor-pointer flex items-center justify-center" data-testid="kt-cl-toolbar-avatar" title="' +
				escapeHtml(sessionUserLabel()) +
				'">' +
				avatarHtml +
				"</div></div></header>"
			);
		},

		renderBreadcrumbs: function (opts) {
			opts = opts || {};
			var items = opts.items || [];
			var current = opts.current || "";
			var parts = [];

			items.forEach(function (item) {
				parts.push(
					'<span class="font-label-sm text-label-sm text-on-surface-variant">' +
						(item.route && item.route.length
							? '<a href="#" class="text-on-surface-variant" data-kt-cl-route="' +
								escapeHtml(JSON.stringify(item.route)) +
								'">' +
								escapeHtml(item.label || "") +
								"</a>"
							: escapeHtml(item.label || "")) +
						"</span>",
				);
				parts.push(msIcon("chevron_right", 12, "text-outline"));
			});

			if (current) {
				parts.push(
					'<span class="font-label-sm text-label-sm text-primary font-medium" data-testid="kt-cl-breadcrumb-current">' +
						escapeHtml(current) +
						"</span>",
				);
			}

			// code.html lines 337-341
			return (
				'<nav class="' +
				spec().BREADCRUMB_ROOT +
				'" data-testid="kt-cl-breadcrumbs" aria-label="' +
				escapeHtml(__("Breadcrumb")) +
				'">' +
				parts.join("") +
				"</nav>"
			);
		},

		renderPageSubtitle: function (opts) {
			opts = opts || {};
			var text = opts.text || "";
			if (!text) return "";
			// code.html line 344
			return (
				'<p class="font-body-md text-body-md text-on-surface-variant" data-testid="kt-cl-page-subtitle">' +
				escapeHtml(text) +
				"</p>"
			);
		},

		renderActionButton: function (opts) {
			opts = opts || {};
			var label = opts.label || "";
			var variant = opts.variant === "primary" ? "primary" : "outline";
			var cls = variant === "primary" ? spec().BTN_PRIMARY : spec().BTN_OUTLINE;
			var testid = opts.testid ? ' data-testid="' + escapeHtml(opts.testid) + '"' : "";
			var key = opts.key ? ' data-kt-cl-action="' + escapeHtml(opts.key) + '"' : "";
			return (
				'<button type="button" class="' +
				cls +
				'"' +
				testid +
				key +
				">" +
				(opts.icon ? msIcon(opts.icon, 16) : "") +
				escapeHtml(label) +
				"</button>"
			);
		},

		renderPageHeaderActions: function (actions) {
			return (actions || [])
				.map(
					function (action) {
						return this.renderActionButton(action);
					}.bind(this),
				)
				.join("");
		},

		renderPageHeader: function (opts) {
			opts = opts || {};
			var breadcrumbsHtml = this.renderBreadcrumbs({
				items: opts.breadcrumbs || opts.items || [],
				current: opts.current,
			});
			var subtitleHtml = this.renderPageSubtitle({ text: opts.subtitle });
			var actionsHtml =
				opts.actionsHtml ||
				(opts.actions ? this.renderPageHeaderActions(opts.actions) : "");

			// code.html lines 337-356
			return (
				'<div data-testid="kt-cl-page-header">' +
				breadcrumbsHtml +
				'<div class="flex flex-col md:flex-row justify-between items-start md:items-end gap-3">' +
				"<div>" +
				subtitleHtml +
				"</div>" +
				(actionsHtml
					? '<div class="flex gap-2" data-testid="kt-cl-page-header-actions">' +
						actionsHtml +
						"</div>"
					: "") +
				"</div></div>"
			);
		},

		// ---- Bento grid (code.html 358-360) -------------------------------
		metricsGrid: function (cardsHtml) {
			return (
				'<div class="' +
				spec().METRICS_WRAP +
				'" data-testid="kt-cl-metrics-grid">' +
				(cardsHtml || "") +
				"</div>"
			);
		},

		bentoGrid: function (opts) {
			opts = opts || {};
			return (
				'<div class="' +
				spec().BENTO_GRID +
				'" data-testid="kt-cl-bento">' +
				(opts.metricsHtml || "") +
				(opts.asideHtml || "") +
				"</div>"
			);
		},

		// ---- KPI card (code.html 362-405) ---------------------------------
		kpiCard: function (opts) {
			opts = opts || {};
			var s = spec();
			var variant = opts.variant === "progress" ? "progress" : "metric";
			var tone = opts.tone || (variant === "progress" ? "blue" : "emerald");
			var label = opts.label || "";
			var value = opts.value || "";
			var icon = opts.icon || "insights";

			if (variant === "progress") {
				var tp = (s.KPI.progress && s.KPI.progress[tone]) || s.KPI.progress.blue;
				var pct = opts.progress == null ? 0 : Math.max(0, Math.min(100, Number(opts.progress)));
				var pctLabel = opts.progressLabel != null ? opts.progressLabel : pct + "% Alloc";
				return (
					'<div class="' +
					tp.card +
					'" data-testid="kt-cl-kpi-card" data-variant="progress" data-tone="' +
					escapeHtml(tone) +
					'">' +
					'<div class="flex justify-between items-start">' +
					'<h3 class="' +
					tp.label +
					'">' +
					escapeHtml(label) +
					"</h3>" +
					'<span class="' +
					tp.badge +
					'">' +
					msIcon(icon, 20) +
					"</span></div>" +
					'<div class="mt-2">' +
					'<div class="' +
					s.KPI_VALUE +
					'">' +
					escapeHtml(value) +
					"</div>" +
					'<div class="flex items-center gap-2 mt-2">' +
					'<div class="' +
					tp.track +
					'">' +
					'<div class="' +
					tp.fill +
					'" style="width: ' +
					pct +
					'%;"></div>' +
					"</div>" +
					'<p class="' +
					tp.pct +
					'">' +
					escapeHtml(pctLabel) +
					"</p>" +
					"</div></div></div>"
				);
			}

			var tm = (s.KPI.metric && s.KPI.metric[tone]) || s.KPI.metric.emerald;
			var delta = opts.delta || "";
			return (
				'<div class="' +
				tm.card +
				'" data-testid="kt-cl-kpi-card" data-variant="metric" data-tone="' +
				escapeHtml(tone) +
				'">' +
				"<div>" +
				'<h3 class="' +
				tm.label +
				'">' +
				escapeHtml(label) +
				"</h3>" +
				'<div class="' +
				s.KPI_VALUE_ROW +
				'">' +
				'<div class="' +
				s.KPI_VALUE +
				'">' +
				escapeHtml(value) +
				"</div>" +
				'<span class="' +
				tm.badgeInline +
				'">' +
				msIcon(icon, 20) +
				"</span></div>" +
				'<p class="' +
				tm.delta +
				'">' +
				escapeHtml(delta) +
				"</p></div>" +
				'<span class="' +
				tm.badgeMobile +
				'">' +
				msIcon(icon, 24) +
				"</span></div>"
			);
		},

		// ---- Calendar widget (code.html 407-447) --------------------------
		calendarWidget: function (opts) {
			opts = opts || {};
			var c = spec().CALENDAR;
			var title = opts.title || __("Upcoming Tenders");
			var viewAll = opts.viewAllLabel || __("View All");
			var items = opts.items || [];

			var itemsHtml = items
				.map(function (it) {
					var tone = it.tone || "neutral";
					var boxCls = c.dateBox[tone] || c.dateBox.neutral;
					return (
						'<div class="' +
						c.item +
						'" data-testid="kt-cl-calendar-item">' +
						'<div class="' +
						boxCls +
						'">' +
						'<span class="' +
						c.day +
						'">' +
						escapeHtml(it.day || "") +
						"</span>" +
						'<span class="' +
						c.month +
						'">' +
						escapeHtml(it.month || "") +
						"</span></div>" +
						'<div class="' +
						c.body +
						'">' +
						'<h4 class="' +
						c.itemTitle +
						'">' +
						escapeHtml(it.title || "") +
						"</h4>" +
						'<p class="' +
						c.itemSubtitle +
						'">' +
						escapeHtml(it.subtitle || "") +
						"</p></div></div>"
					);
				})
				.join("");

			return (
				'<div class="' +
				c.widget +
				'" data-testid="kt-cl-calendar">' +
				'<div class="' +
				c.header +
				'">' +
				'<h3 class="' +
				c.title +
				'">' +
				escapeHtml(title) +
				"</h3>" +
				'<button type="button" class="' +
				c.viewAll +
				'" data-testid="kt-cl-calendar-viewall">' +
				escapeHtml(viewAll) +
				"</button></div>" +
				'<div class="' +
				c.list +
				'" data-testid="kt-cl-calendar-list">' +
				itemsHtml +
				"</div></div>"
			);
		},

		// ---- Status chip (code.html 482-549) ------------------------------
		statusChip: function (opts) {
			opts = opts || {};
			var s = spec();
			var tone = (s.CHIP && s.CHIP[opts.tone]) || (s.CHIP && s.CHIP.draft) || {};
			var chipCls =
				s.CHIP_BASE +
				" " +
				(tone.chip || "") +
				" " +
				s.CHIP_TYPO +
				(tone.dotChip ? " " + tone.dotChip : "");
			var dotCls = s.CHIP_DOT + " " + (tone.dot || "") + " mr-1";
			var label = opts.label != null ? opts.label : tone.label || "";
			return (
				'<span class="' +
				chipCls +
				'" data-testid="kt-cl-status-chip" data-tone="' +
				escapeHtml(opts.tone || "") +
				'">' +
				'<span class="' +
				dotCls +
				'"></span>' +
				escapeHtml(label) +
				"</span>"
			);
		},

		// ---- Data table (code.html 449-563) -------------------------------
		dataTable: function (opts) {
			opts = opts || {};
			var self = this;
			var t = spec().TABLE;
			var title = opts.title || "";
			var columns = opts.columns || [];
			var rows = opts.rows || [];
			var footerText = opts.footerText || "";

			var filterHtml = "";
			if (opts.filter) {
				var options = (opts.filter.options || [])
					.map(function (o) {
						return (
							'<option value="' +
							escapeHtml(o.value || "") +
							'">' +
							escapeHtml(o.label || "") +
							"</option>"
						);
					})
					.join("");
				filterHtml =
					'<div class="flex gap-2 w-full sm:w-auto">' +
					'<div class="' +
					t.filterWrap +
					'">' +
					'<span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-on-surface-variant" style="font-size: 16px;" aria-hidden="true">filter_list</span>' +
					'<select class="' +
					t.select +
					'" data-testid="kt-cl-table-filter" aria-label="' +
					escapeHtml(opts.filter.label || __("Filter")) +
					'">' +
					options +
					"</select></div></div>";
			}

			var thead = columns
				.map(function (col) {
					return (
						'<th class="' +
						t.th +
						(col.th ? " " + col.th : "") +
						'">' +
						escapeHtml(col.label || "") +
						"</th>"
					);
				})
				.join("");

			var tbody = rows
				.map(function (row, idx) {
					var trCls = idx % 2 === 1 ? t.trAlt : t.tr;
					var cells;
					if (row.cells) {
						cells = row.cells
							.map(function (cell) {
								return '<td class="' + (cell.cls || t.tdText) + '">' + (cell.html || "") + "</td>";
							})
							.join("");
					} else {
						var actionIcon = (row.action && row.action.icon) || "visibility";
						cells =
							'<td class="' +
							t.tdStrong +
							'">' +
							escapeHtml(row.department || "") +
							"</td>" +
							'<td class="' +
							t.tdText +
							'">' +
							escapeHtml(row.category || "") +
							"</td>" +
							'<td class="' +
							t.tdNumber +
							'">' +
							escapeHtml(row.cost || "") +
							"</td>" +
							'<td class="' +
							t.tdStatus +
							'">' +
							self.statusChip(row.status || {}) +
							"</td>" +
							'<td class="' +
							t.tdAction +
							'">' +
							'<button type="button" class="' +
							t.rowAction +
							'" data-testid="kt-cl-row-action">' +
							msIcon(actionIcon, 18) +
							"</button></td>";
					}
					return '<tr class="' + trCls + '" data-testid="kt-cl-table-row">' + cells + "</tr>";
				})
				.join("");

			return (
				'<div class="' +
				t.root +
				'" data-testid="kt-cl-data-table">' +
				'<div class="' +
				t.head +
				'">' +
				'<h2 class="' +
				t.title +
				'">' +
				escapeHtml(title) +
				"</h2>" +
				filterHtml +
				"</div>" +
				'<div class="' +
				t.scroll +
				'">' +
				'<table class="' +
				t.table +
				'">' +
				"<thead><tr class=\"" +
				t.theadTr +
				'">' +
				thead +
				"</tr></thead>" +
				'<tbody class="' +
				t.tbody +
				'">' +
				tbody +
				"</tbody></table></div>" +
				'<div class="' +
				t.footer +
				'">' +
				'<span class="' +
				t.footerText +
				'" data-testid="kt-cl-table-footer">' +
				escapeHtml(footerText) +
				"</span>" +
				'<div class="' +
				t.footerPager +
				'"></div></div></div>'
			);
		},

		bindBreadcrumbRoutes: function (root) {
			var $root = root && root.jquery ? root : $(root);
			$root.find("[data-kt-cl-route]").off("click.ktClCrumb").on("click.ktClCrumb", function (e) {
				e.preventDefault();
				try {
					var route = JSON.parse($(this).attr("data-kt-cl-route") || "[]");
					if (route && route.length) {
						frappe.set_route.apply(frappe, route);
					}
				} catch (err) {
					/* ignore */
				}
			});
		},
	};

	// Library-friendly aliases so new pages compose via kentender_core.cl.components.*
	var C = kentender_core.cl_components;
	C.topBar = C.renderTopToolbar;
	C.breadcrumbs = C.renderBreadcrumbs;
	C.pageHeader = C.renderPageHeader;
	C.button = C.renderActionButton;

	frappe.provide("kentender_core.cl");
	kentender_core.cl.components = C;
})();
