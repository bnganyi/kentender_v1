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

	function sessionAvatarUrl(explicit) {
		if (explicit) return explicit;
		try {
			var user = (frappe.session && frappe.session.user) || "";
			if (frappe.user_info && user) {
				var info = frappe.user_info(user);
				if (info && info.image) return info.image;
			}
			if (frappe.boot && frappe.boot.user && frappe.boot.user.image) {
				return frappe.boot.user.image;
			}
		} catch (e) {
			/* ignore */
		}
		return "";
	}

	function sessionUserRole(explicit) {
		if (explicit) return explicit;
		try {
			var roles = (frappe.boot && frappe.boot.user && frappe.boot.user.roles) || [];
			var skip = {
				Administrator: 1,
				Guest: 1,
				All: 1,
				"System Manager": 1,
				"Desk User": 1,
			};
			for (var i = 0; i < roles.length; i++) {
				if (!skip[roles[i]]) return roles[i];
			}
			return roles[0] || "";
		} catch (e) {
			return "";
		}
	}

	kentender_core.cl_components = {
		escapeHtml: escapeHtml,
		icon: msIcon,

		/**
		 * Civic Ledger top toolbar (C1-M1 standard):
		 *   left:  context trail (ancestors; last crumb bold) — or legacy `title`
		 *   right: notifications · help · name/role · avatar  (no search by default)
		 */
		renderTopToolbar: function (opts) {
			opts = opts || {};
			var title = opts.title || "";
			var trail = opts.breadcrumbs || opts.trail || [];
			var showSearch = opts.showSearch === true;
			var showUserMeta = opts.showUserMeta !== false;
			var searchPlaceholder =
				opts.searchPlaceholder || "Search APP, tenders, or departments...";
			var userName = opts.userName || sessionUserLabel();
			var userRole = sessionUserRole(opts.userRole || "");
			var avatarUrl = sessionAvatarUrl(opts.avatarUrl || "");

			var searchHtml = showSearch
				? '<div class="hidden md:flex relative">' +
					'<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline" style="font-size: 18px;" aria-hidden="true">search</span>' +
					'<input class="h-9 w-64 pl-9 pr-4 bg-surface-container-low border-none rounded-full text-body-sm focus:ring-1 focus:ring-primary" placeholder="' +
					escapeHtml(searchPlaceholder) +
					'" type="text" data-testid="kt-cl-toolbar-search" aria-label="' +
					escapeHtml(__("Search")) +
					'" />' +
					"</div>"
				: "";

			var leftHtml = "";
			if (trail.length) {
				var ancestors = trail.slice(0, -1);
				var leaf = trail[trail.length - 1] || {};
				/* Last crumb is context only (bold, not a link) — C1-M1 TopAppBar. */
				leftHtml = this.renderBreadcrumbs({
					items: ancestors,
					current: leaf.label || "",
					currentRoute: null,
					variant: "toolbar",
				});
			} else if (title) {
				leftHtml =
					'<h1 class="font-headline-md text-headline-md font-bold text-on-surface truncate max-w-[300px]" data-testid="kt-cl-toolbar-title">' +
					escapeHtml(title) +
					"</h1>";
			}

			var avatarHtml = avatarUrl
				? '<img alt="User profile avatar" class="w-full h-full object-cover" src="' +
					escapeHtml(avatarUrl) +
					'" />'
				: '<span class="font-body-md text-body-md font-bold">' +
					escapeHtml(initials(userName)) +
					"</span>";

			/* C1-M1: sep + name/role (right-aligned, tight stack) + 32px circular avatar. */
			var userMetaHtml = showUserMeta
				? '<div class="kt-cl-toolbar-user-sep" data-testid="kt-cl-toolbar-user-sep" aria-hidden="true"></div>' +
					'<div class="kt-cl-toolbar-user" data-testid="kt-cl-toolbar-user">' +
					'<div class="kt-cl-toolbar-user-meta">' +
					'<p data-testid="kt-cl-toolbar-user-name">' +
					escapeHtml(userName) +
					"</p>" +
					'<p data-testid="kt-cl-toolbar-user-role">' +
					escapeHtml(userRole || __("User")) +
					"</p></div>" +
					'<div class="kt-cl-toolbar-avatar" data-testid="kt-cl-toolbar-avatar" title="' +
					escapeHtml(userName) +
					'">' +
					avatarHtml +
					"</div></div>"
				: '<div class="kt-cl-toolbar-avatar" data-testid="kt-cl-toolbar-avatar" title="' +
					escapeHtml(userName) +
					'">' +
					avatarHtml +
					"</div>";

			return (
				'<header class="' +
				spec().TOOLBAR_ROOT +
				'" data-testid="kt-cl-toolbar">' +
				'<div class="flex items-center gap-4 min-w-0">' +
				leftHtml +
				"</div>" +
				'<div class="flex items-center gap-3">' +
				searchHtml +
				'<button type="button" class="kt-cl-toolbar-icon-btn text-on-surface-variant" data-testid="kt-cl-toolbar-notifications" aria-label="' +
				escapeHtml(__("Notifications")) +
				'">' +
				msIcon("notifications", 22) +
				"</button>" +
				'<button type="button" class="kt-cl-toolbar-icon-btn text-on-surface-variant" data-testid="kt-cl-toolbar-help" aria-label="' +
				escapeHtml(__("Help")) +
				'">' +
				msIcon("help_outline", 22) +
				"</button>" +
				userMetaHtml +
				"</div></header>"
			);
		},

		renderBreadcrumbs: function (opts) {
			opts = opts || {};
			var items = opts.items || [];
			var current = opts.current || "";
			var currentRoute = opts.currentRoute || null;
			var variant = opts.variant === "toolbar" ? "toolbar" : "page";
			var parts = [];
			var mutedCls =
				variant === "toolbar"
					? ""
					: "font-label-sm text-label-sm text-on-surface-variant";
			var currentCls =
				variant === "toolbar"
					? "text-primary font-bold"
					: "font-label-sm text-label-sm text-primary font-medium";

			items.forEach(function (item) {
				parts.push(
					'<span class="' +
						mutedCls +
						'">' +
						(item.route && item.route.length
							? '<a href="#" class="text-on-surface-variant" data-kt-cl-route="' +
								escapeHtml(JSON.stringify(item.route)) +
								'">' +
								escapeHtml(item.label || "") +
								"</a>"
							: escapeHtml(item.label || "")) +
						"</span>",
				);
				parts.push(msIcon("chevron_right", variant === "toolbar" ? 14 : 12, "text-outline"));
			});

			if (current) {
				if (currentRoute && currentRoute.length) {
					parts.push(
						'<a href="#" class="' +
							currentCls +
							'" data-testid="kt-cl-breadcrumb-current" data-kt-cl-route="' +
							escapeHtml(JSON.stringify(currentRoute)) +
							'">' +
							escapeHtml(current) +
							"</a>",
					);
				} else {
					parts.push(
						'<span class="' +
							currentCls +
							'" data-testid="kt-cl-breadcrumb-current">' +
							escapeHtml(current) +
							"</span>",
					);
				}
			}

			var rootCls =
				variant === "toolbar"
					? spec().BREADCRUMB_TOOLBAR || spec().BREADCRUMB_ROOT
					: spec().BREADCRUMB_ROOT;

			return (
				'<nav class="' +
				rootCls +
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

		renderPageTitle: function (opts) {
			opts = opts || {};
			var title = opts.title || "";
			if (!title) return "";
			return (
				'<h2 class="' +
				spec().PAGE_TITLE +
				'" data-testid="kt-cl-page-title">' +
				escapeHtml(title) +
				"</h2>"
			);
		},

		renderPageHeader: function (opts) {
			opts = opts || {};
			/* C1-M1 standard: trail lives in the toolbar. Default hide page-level crumbs.
			 * Pass hideBreadcrumbs: false only for demos that still show a page trail. */
			var hideBreadcrumbs = opts.hideBreadcrumbs !== false;
			var breadcrumbsHtml = hideBreadcrumbs
				? ""
				: this.renderBreadcrumbs({
						items: opts.breadcrumbs || opts.items || [],
						current: opts.current,
					});
			var titleHtml = this.renderPageTitle({ title: opts.title });
			var subtitleHtml = this.renderPageSubtitle({ text: opts.subtitle });
			var actionsHtml =
				opts.actionsHtml ||
				(opts.actions ? this.renderPageHeaderActions(opts.actions) : "");

			return (
				'<div data-testid="kt-cl-page-header">' +
				breadcrumbsHtml +
				'<div class="flex flex-col md:flex-row justify-between items-start md:items-end gap-3">' +
				"<div>" +
				titleHtml +
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

		// ---- UI-00 queue summary (C1-M1 accent cards) --------------------
		queueSummaryCard: function (opts) {
			opts = opts || {};
			var q = spec().QUEUE || {};
			var accent = opts.accentClass || "bg-primary";
			var iconWrap = opts.iconWrapClass || q.summaryIconWrap || "";
			return (
				'<div class="' +
				(q.summaryCard || "") +
				'" data-testid="kt-cl-queue-summary-card" data-key="' +
				escapeHtml(opts.key || "") +
				'">' +
				'<div class="' +
				(q.summaryAccent || "") +
				" " +
				accent +
				'"></div>' +
				'<div class="' +
				iconWrap +
				'">' +
				msIcon(opts.icon || "pending_actions", 22, opts.iconClass || "text-primary") +
				"</div>" +
				"<div>" +
				'<p class="' +
				(q.summaryLabel || "") +
				'">' +
				escapeHtml(opts.label || "") +
				"</p>" +
				'<p class="' +
				(q.summaryValue || "") +
				'" data-testid="kt-cl-queue-summary-value">' +
				escapeHtml(opts.value != null ? String(opts.value) : "0") +
				"</p></div></div>"
			);
		},

		queueSummaryGrid: function (cardsHtml) {
			var q = spec().QUEUE || {};
			return (
				'<div class="' +
				(q.summaryGrid || "") +
				'" data-testid="kt-cl-queue-summary-grid">' +
				(cardsHtml || "") +
				"</div>"
			);
		},

		tabBar: function (opts) {
			opts = opts || {};
			var q = spec().QUEUE || {};
			var tabs = opts.tabs || [];
			var active = opts.active || (tabs[0] && tabs[0].key) || "";
			var html = tabs
				.map(function (tab) {
					var isActive = tab.key === active;
					return (
						'<button type="button" class="' +
						(isActive ? q.tabActive : q.tabIdle) +
						'" data-testid="kt-cl-ui00-tab-' +
						escapeHtml(tab.key || "") +
						'" data-tab="' +
						escapeHtml(tab.key || "") +
						'" aria-selected="' +
						(isActive ? "true" : "false") +
						'">' +
						escapeHtml(tab.label || "") +
						"</button>"
					);
				})
				.join("");
			return (
				'<div class="' +
				(q.tabBar || "") +
				'" data-testid="kt-cl-tab-bar" role="tablist">' +
				html +
				"</div>"
			);
		},

		filterBar: function (opts) {
			opts = opts || {};
			var q = spec().QUEUE || {};
			var filters = opts.filters || [];
			var searchHtml = "";
			var fieldHtml = [];

			filters.forEach(function (f) {
				var id = f.key || "";
				var label =
					'<label class="' +
					(q.filterLabel || "") +
					'" for="kt-cl-filter-' +
					escapeHtml(id) +
					'">' +
					escapeHtml(f.label || "") +
					"</label>";
				if (f.type === "search") {
					searchHtml =
						'<div class="kt-cl-filter-search" data-testid="kt-cl-ui00-filter-' +
						escapeHtml(id) +
						'">' +
						label +
						'<input id="kt-cl-filter-' +
						escapeHtml(id) +
						'" type="search" class="' +
						(q.filterInput || "") +
						'" placeholder="' +
						escapeHtml(f.placeholder || "") +
						'" value="' +
						escapeHtml(f.value || "") +
						'" data-filter="' +
						escapeHtml(id) +
						'" data-filter-type="search" autocomplete="off"/></div>';
					return;
				}
				var options = (f.options || [])
					.map(function (o) {
						var selected = (f.value || "") === (o.value || "") ? " selected" : "";
						return (
							'<option value="' +
							escapeHtml(o.value || "") +
							'"' +
							selected +
							">" +
							escapeHtml(o.label || "") +
							"</option>"
						);
					})
					.join("");
				var hidden = f.hidden ? ' style="display:none"' : "";
				fieldHtml.push(
					'<div class="kt-cl-filter-field" data-testid="kt-cl-ui00-filter-' +
						escapeHtml(id) +
						'"' +
						hidden +
						">" +
						label +
						'<select id="kt-cl-filter-' +
						escapeHtml(id) +
						'" class="' +
						(q.filterSelect || "") +
						'" data-filter="' +
						escapeHtml(id) +
						'">' +
						options +
						"</select></div>"
				);
			});

			var sepHtml = searchHtml
				? '<div class="kt-cl-filter-sep" data-testid="kt-cl-filter-sep" aria-hidden="true">|</div>'
				: "";
			var fieldsWrap = fieldHtml.length
				? '<div class="kt-cl-filter-fields">' + fieldHtml.join("") + "</div>"
				: "";

			return (
				'<div class="' +
				(q.filterBar || "") +
				'" data-testid="kt-cl-filter-bar">' +
				searchHtml +
				sepHtml +
				fieldsWrap +
				"</div>"
			);
		},

		/**
		 * Standard filter-bar wiring for queue/data tables.
		 * onChange(key, value, event) — page updates state and reloads.
		 */
		bindFilterBar: function (root, opts) {
			opts = opts || {};
			var $root = root && root.jquery ? root : $(root);
			if (!$root || !$root.length) return;
			var ns = opts.namespace || ".ktClFilter";
			var onChange = typeof opts.onChange === "function" ? opts.onChange : function () {};
			var debounceMs = opts.debounceMs == null ? 300 : opts.debounceMs;

			$root.off(ns);
			$root.on(
				"input" + ns,
				'input[data-filter-type="search"], input[data-filter="search"]',
				frappe.utils.debounce(function (e) {
					var $el = $(e.currentTarget);
					onChange($el.attr("data-filter") || "search", $el.val() || "", e);
				}, debounceMs)
			);
			$root.on("change" + ns, "select[data-filter]", function (e) {
				var $el = $(e.currentTarget);
				onChange($el.attr("data-filter"), $el.val() || "", e);
			});
		},

		queueTable: function (opts) {
			opts = opts || {};
			var q = spec().QUEUE || {};
			var columns = opts.columns || [];
			var rows = opts.rows || [];
			var thead = columns
				.map(function (col) {
					return '<th class="' + (q.th || "") + '">' + escapeHtml(col.label || "") + "</th>";
				})
				.join("");
			var tbody = rows
				.map(function (row, idx) {
					var cells = (row.cells || [])
						.map(function (cell) {
							return (
								'<td class="' +
								(cell.cls || q.tdText || "") +
								'">' +
								(cell.html != null ? cell.html : escapeHtml(cell.text || "")) +
								"</td>"
							);
						})
						.join("");
					return (
						'<tr class="' +
						(q.tr || "") +
						'" data-testid="kt-cl-ui00-row-' +
						escapeHtml(row.id || String(idx)) +
						'" data-row-id="' +
						escapeHtml(row.id || "") +
						'">' +
						cells +
						"</tr>"
					);
				})
				.join("");

			var pagerHtml = "";
			var pageSizeHtml = "";
			var pageSizeOptions = opts.pageSizeOptions || [10, 20, 50, 100];
			var currentPageSize =
				opts.pageSize ||
				(opts.pagination && opts.pagination.page_size) ||
				pageSizeOptions[1] ||
				20;

			if (opts.showPageSize !== false) {
				var sizeOpts = pageSizeOptions
					.map(function (n) {
						var v = String(n);
						var selected = String(currentPageSize) === v ? " selected" : "";
						return '<option value="' + escapeHtml(v) + '"' + selected + ">" + escapeHtml(v) + "</option>";
					})
					.join("");
				pageSizeHtml =
					'<div class="' +
					(q.pageSizeWrap || "") +
					'" data-testid="kt-cl-ui00-page-size-wrap">' +
					'<label class="' +
					(q.pageSizeLabel || "") +
					'" for="kt-cl-page-size">' +
					escapeHtml(__("Rows per page")) +
					"</label>" +
					'<select id="kt-cl-page-size" class="' +
					(q.pageSizeSelect || "") +
					'" data-page-size data-testid="kt-cl-ui00-page-size" aria-label="' +
					escapeHtml(__("Rows per page")) +
					'">' +
					sizeOpts +
					"</select></div>";
			}

			if (opts.pagination) {
				var p = opts.pagination;
				var buttons = "";
				var totalPages = p.total_pages || 1;
				var page = p.page || 1;
				buttons +=
					'<button type="button" class="' +
					(q.pagerBtn || "") +
					'" data-page="prev" data-testid="kt-cl-ui00-page-prev">' +
					msIcon("chevron_left", 16) +
					"</button>";
				for (var i = 1; i <= Math.min(totalPages, 5); i++) {
					buttons +=
						'<button type="button" class="' +
						(i === page ? q.pagerBtnActive : q.pagerBtn) +
						'" data-page="' +
						i +
						'" data-testid="kt-cl-ui00-page-' +
						i +
						'">' +
						i +
						"</button>";
				}
				buttons +=
					'<button type="button" class="' +
					(q.pagerBtn || "") +
					'" data-page="next" data-testid="kt-cl-ui00-page-next">' +
					msIcon("chevron_right", 16) +
					"</button>";
				pagerHtml =
					'<div class="' +
					(q.pager || "") +
					'" data-testid="kt-cl-ui00-pager">' +
					buttons +
					"</div>";
			}

			var footerRight =
				pageSizeHtml || pagerHtml
					? '<div class="' +
						(q.footerRight || "") +
						'" data-testid="kt-cl-ui00-footer-right">' +
						pageSizeHtml +
						pagerHtml +
						"</div>"
					: "";

			return (
				'<div data-testid="kt-cl-ui00-table">' +
				'<div class="' +
				(q.tableScroll || "") +
				'">' +
				'<table class="' +
				(q.table || "") +
				'"><thead><tr class="' +
				(q.theadTr || "") +
				'">' +
				thead +
				'</tr></thead><tbody class="' +
				(q.tbody || "") +
				'">' +
				tbody +
				"</tbody></table></div>" +
				'<div class="' +
				(q.footer || "") +
				'">' +
				'<p class="' +
				(q.footerText || "") +
				'" data-testid="kt-cl-ui00-table-footer">' +
				escapeHtml(opts.footerText || "") +
				"</p>" +
				footerRight +
				"</div></div>"
			);
		},

		configurationContextStrip: function (ctx) {
			ctx = ctx || {};
			var h = spec().CONFIG_HOME || {};
			var blockers = parseInt(ctx.blocker_count, 10) || 0;
			var warnings = parseInt(ctx.warning_count, 10) || 0;
			var issuesLabel =
				ctx.issues_label ||
				(blockers || warnings
					? blockers + " Blockers / " + warnings + " Warnings"
					: __("None"));
			var issuesCls =
				blockers || warnings ? h.contextValueError || "" : h.contextValue || "";
			/* C1-M3 §4 — exactly eight fields (pack labels). */
			var cells = [
				{
					key: "package_ref",
					label: __("Procurement Package Ref"),
					value: ctx.procurement_package_ref || "",
				},
				{
					key: "title",
					label: __("Procurement Title"),
					value: ctx.procurement_title || "",
					wide: true,
				},
				{
					key: "entity",
					label: __("Procuring Entity"),
					value: ctx.procuring_entity_name || "",
				},
				{
					key: "method",
					label: __("Procurement Method"),
					value: ctx.procurement_method_label || "",
				},
				{
					key: "family",
					label: __("STD Family"),
					value: ctx.std_family_label || "",
				},
				{
					key: "std_document",
					label: __("Standard Tender Document"),
					value: ctx.standard_tender_document_label || "",
				},
			];
			var html = cells
				.map(function (cell) {
					return (
						'<div class="' +
						(h.contextCell || "") +
						(cell.wide ? " kt-cl-config-context-cell--wide" : "") +
						'" data-testid="kt-cl-config-context-' +
						cell.key +
						'">' +
						'<p class="' +
						(h.contextLabel || "") +
						'">' +
						escapeHtml(cell.label) +
						"</p>" +
						'<p class="' +
						(h.contextValue || "") +
						'">' +
						escapeHtml(cell.value) +
						"</p></div>"
					);
				})
				.join("");
			html +=
				'<div class="' +
				(h.contextCell || "") +
				'" data-testid="kt-cl-config-context-status">' +
				'<p class="' +
				(h.contextLabel || "") +
				'">' +
				__("Configuration Status") +
				"</p>" +
				'<div class="' +
				(h.contextStatusRow || "") +
				'">' +
				'<span class="' +
				(h.contextStatusDot || "") +
				'" data-tone="' +
				escapeHtml(ctx.status_tone || "in_progress") +
				'" aria-hidden="true"></span>' +
				'<span class="' +
				(h.contextValue || "") +
				'">' +
				escapeHtml(ctx.configuration_status_label || "") +
				"</span></div></div>";
			html +=
				'<div class="' +
				(h.contextCell || "") +
				'" data-testid="kt-cl-config-context-issues">' +
				'<p class="' +
				(h.contextLabel || "") +
				'">' +
				__("Issues") +
				"</p>" +
				'<p class="' +
				issuesCls +
				" kt-cl-config-issues-value" +
				(blockers || warnings ? " is-alert" : "") +
				'">' +
				escapeHtml(issuesLabel) +
				"</p></div>";
			return (
				'<div class="' +
				(h.contextStrip || "") +
				'" data-testid="kt-cl-config-context-strip">' +
				html +
				"</div>"
			);
		},

		nextBestActionPanel: function (opts) {
			opts = opts || {};
			var h = spec().CONFIG_HOME || {};
			var tone = opts.tone || "default";
			var iconName = tone === "attention" || tone === "error" ? "warning" : "arrow_forward";
			var iconWrap =
				tone === "attention" || tone === "error"
					? "w-12 h-12 rounded-full bg-error flex items-center justify-center flex-shrink-0"
					: "w-12 h-12 rounded-full bg-white/15 flex items-center justify-center flex-shrink-0";
			/* Layout: single row — copy left, CTA right (C1-M3). Copy prefixes per REVISED_v6. */
			return (
				'<div class="kt-cl-ui01-next-action ' +
				(h.nextAction || "") +
				'" data-testid="kt-cl-ui01-next-action">' +
				'<div class="kt-cl-ui01-next-body relative z-10">' +
				'<div class="kt-cl-ui01-next-icon ' +
				iconWrap +
				'">' +
				msIcon(iconName, 28) +
				"</div>" +
				'<div class="kt-cl-ui01-next-copy">' +
				'<p class="kt-cl-ui01-next-eyebrow">' +
				__("Next Best Action") +
				"</p>" +
				'<h3 class="kt-cl-ui01-next-title" data-testid="kt-cl-ui01-next-label">' +
				escapeHtml(__("Next step: {0}", [opts.label || ""])) +
				"</h3>" +
				'<p class="kt-cl-ui01-next-reason" data-testid="kt-cl-ui01-next-reason">' +
				escapeHtml(__("Reason: {0}", [opts.reason || ""])) +
				"</p></div></div>" +
				'<button type="button" class="kt-cl-ui01-next-btn ' +
				(h.nextActionBtn || "") +
				'" data-action="next-action" data-route="' +
				escapeHtml(opts.route || "") +
				'" data-testid="kt-cl-ui01-next-btn">' +
				escapeHtml(opts.buttonLabel || __("Continue")) +
				"</button>" +
				'<div class="kt-cl-ui01-next-glow" aria-hidden="true"></div>' +
				"</div>"
			);
		},

		configurationStepsGrid: function (opts) {
			opts = opts || {};
			var h = spec().CONFIG_HOME || {};
			var steps = opts.steps || [];
			var cards = steps
				.map(function (step) {
					var status = step.status_label || "";
					var cardCls = h.stepCard || "";
					if (status === "Needs attention") {
						cardCls = h.stepCardAttention || cardCls;
					} else if (status === "Not available yet") {
						cardCls = h.stepCardUnavailable || cardCls;
					}
					var issues = "";
					var b = parseInt(step.blocker_count, 10) || 0;
					var w = parseInt(step.warning_count, 10) || 0;
					if (b || w) {
						issues =
							'<p class="kt-cl-ui01-step-issues">' +
							escapeHtml(b + " Blockers / " + w + " Warnings") +
							"</p>";
					}
					var footerLeft = "";
					if (
						step.show_progress_bar &&
						(status === "In progress" || status === "Needs attention")
					) {
						var pct = parseInt(step.progress_pct, 10);
						if (isNaN(pct)) pct = 0;
						pct = Math.max(0, Math.min(100, pct));
						var met = parseInt(step.progress_met_count, 10);
						var req = parseInt(step.progress_required_count, 10);
						var aria =
							!isNaN(met) && !isNaN(req) && req > 0
								? __("{0} of {1} required items", [String(met), String(req)])
								: __("Step progress");
						footerLeft =
							'<div class="kt-cl-ui01-step-progress" data-testid="kt-cl-ui01-step-progress-' +
							escapeHtml(step.id || "") +
							'" aria-label="' +
							escapeHtml(aria) +
							'" data-progress-pct="' +
							pct +
							'">' +
							'<div class="kt-cl-ui01-step-progress-fill" style="width:' +
							pct +
							'%"></div></div>';
					} else if (step.last_updated_label) {
						footerLeft =
							'<span class="kt-cl-ui01-step-meta">' +
							escapeHtml(__("Last update: {0}", [step.last_updated_label])) +
							"</span>";
					} else {
						footerLeft = '<span class="kt-cl-ui01-step-meta"></span>';
					}
					var btnPrimary = status === "Needs attention";
					var btnCls = btnPrimary
						? "kt-cl-ui01-step-btn kt-cl-ui01-step-btn--primary"
						: "kt-cl-ui01-step-btn kt-cl-ui01-step-btn--link";
					var badgeTone =
						status === "Complete"
							? "complete"
							: status === "Needs attention"
								? "attention"
								: status === "In progress"
									? "progress"
									: status === "Not available yet"
										? "unavailable"
										: "default";
					return (
						'<div class="' +
						cardCls +
						'" data-testid="kt-cl-ui01-step-' +
						escapeHtml(step.id || "") +
						'" data-step-id="' +
						escapeHtml(step.id || "") +
						'" data-step-status="' +
						escapeHtml(status) +
						'" data-action="open-step" data-route="' +
						escapeHtml(step.route || "") +
						'">' +
						'<div class="kt-cl-ui01-step-card-top">' +
						'<span class="kt-cl-ui01-step-id">' +
						escapeHtml(step.id || "") +
						"</span>" +
						'<div class="kt-cl-ui01-step-card-top-end">' +
						'<div class="kt-cl-ui01-step-badge kt-cl-ui01-step-badge--' +
						badgeTone +
						'" data-testid="kt-cl-ui01-step-badge-' +
						escapeHtml(step.id || "") +
						'">' +
						'<span class="kt-cl-ui01-step-badge-dot" aria-hidden="true"></span>' +
						'<span class="kt-cl-ui01-step-badge-label">' +
						escapeHtml(status) +
						"</span></div>" +
						'<button type="button" class="kt-cl-ui01-step-details" data-action="open-drawer" data-step-id="' +
						escapeHtml(step.id || "") +
						'" data-testid="kt-cl-ui01-step-details-' +
						escapeHtml(step.id || "") +
						'" aria-label="' +
						escapeHtml(__("Step details")) +
						'" title="' +
						escapeHtml(__("Step details")) +
						'">' +
						msIcon("info", 18) +
						"</button></div></div>" +
						'<h4 class="kt-cl-ui01-step-title">' +
						escapeHtml(step.title || "") +
						"</h4>" +
						'<p class="kt-cl-ui01-step-desc">' +
						escapeHtml(step.description || "") +
						"</p>" +
						issues +
						'<div class="kt-cl-ui01-step-footer">' +
						footerLeft +
						'<button type="button" class="' +
						btnCls +
						'" data-action="open-step" data-route="' +
						escapeHtml(step.route || "") +
						'" data-step-id="' +
						escapeHtml(step.id || "") +
						'" data-testid="kt-cl-ui01-step-action-' +
						escapeHtml(step.id || "") +
						'">' +
						escapeHtml(step.action_label || __("Start")) +
						"</button></div></div>"
					);
				})
				.join("");
			return (
				'<section data-testid="kt-cl-ui01-steps">' +
				'<h3 class="' +
				(h.stepsSectionTitle || "") +
				'">' +
				__("Configuration Steps") +
				"</h3>" +
				'<div class="' +
				(h.stepsGrid || "") +
				'">' +
				cards +
				"</div></section>"
			);
		},

		handoffPanel: function (opts) {
			opts = opts || {};
			var h = spec().CONFIG_HOME || {};
			var handoff = opts.handoff || {};
			var order = [
				"readiness_check",
				"review_status",
				"tender_document_preview",
				"publication_handoff",
			];
			var icons = {
				readiness_check: "assignment_turned_in",
				review_status: "rate_review",
				tender_document_preview: "picture_as_pdf",
				publication_handoff: "send",
			};
			var items = order
				.map(function (key) {
					var item = handoff[key] || {};
					var disabled = !item.route && !item.action_label;
					var status = String(item.status_label || "");
					var isAlert =
						/blocker/i.test(status) ||
						/returned/i.test(status) ||
						key === "readiness_check" && /found/i.test(status);
					var actionHtml = "";
					if (item.action_label) {
						actionHtml =
							'<button type="button" class="kt-cl-ui01-handoff-action" data-action="handoff" data-route="' +
							escapeHtml(item.route || "") +
							'" data-testid="kt-cl-ui01-handoff-action-' +
							key +
							'">' +
							escapeHtml(item.action_label) +
							"</button>";
					}
					return (
						'<div class="kt-cl-ui01-handoff-item ' +
						(h.handoffItem || "") +
						(disabled ? " is-disabled" : "") +
						(isAlert ? " is-alert" : "") +
						'" data-testid="kt-cl-ui01-handoff-' +
						key +
						'">' +
						'<div class="kt-cl-ui01-handoff-item-row">' +
						'<div class="kt-cl-ui01-handoff-item-icon' +
						(isAlert ? " is-alert" : "") +
						'">' +
						msIcon(icons[key] || "info", 20) +
						"</div>" +
						'<div class="kt-cl-ui01-handoff-item-copy">' +
						'<h4 class="kt-cl-ui01-handoff-item-title">' +
						escapeHtml(item.label || "") +
						"</h4>" +
						'<p class="kt-cl-ui01-handoff-item-status' +
						(isAlert ? " is-alert" : "") +
						'">' +
						escapeHtml(status) +
						"</p>" +
						actionHtml +
						"</div></div></div>"
					);
				})
				.join("");
			return (
				'<div class="kt-cl-ui01-handoff ' +
				(h.handoffRoot || "") +
				'" data-testid="kt-cl-ui01-handoff">' +
				'<div class="kt-cl-ui01-handoff-header ' +
				(h.handoffHeader || "") +
				'" data-testid="kt-cl-ui01-handoff-header">' +
				'<h3 class="kt-cl-ui01-handoff-title">' +
				__("Completion & Handoff") +
				"</h3>" +
				'<span class="kt-cl-ui01-handoff-header-icon" aria-hidden="true">' +
				msIcon("verified", 18) +
				"</span></div>" +
				'<div class="kt-cl-ui01-handoff-body">' +
				items +
				"</div></div>"
			);
		},

		overallProgressPanel: function (opts) {
			opts = opts || {};
			var complete = parseInt(opts.complete, 10) || 0;
			var total = parseInt(opts.total, 10) || 9;
			if (total < 1) total = 9;
			/* Prefer average of per-step exit-condition %; fall back to complete/total. */
			var pct =
				opts.progressPct != null && opts.progressPct !== ""
					? parseInt(opts.progressPct, 10)
					: Math.round((complete / total) * 100);
			if (isNaN(pct)) pct = 0;
			pct = Math.max(0, Math.min(100, pct));
			return (
				'<div class="kt-cl-ui01-progress" data-testid="kt-cl-ui01-progress">' +
				'<p class="kt-cl-ui01-progress-label">' +
				__("Overall Progress") +
				"</p>" +
				'<div class="kt-cl-ui01-progress-row">' +
				'<p class="kt-cl-ui01-progress-pct" data-testid="kt-cl-ui01-progress-pct">' +
				pct +
				"%</p>" +
				'<p class="kt-cl-ui01-progress-meta" data-testid="kt-cl-ui01-progress-meta">' +
				escapeHtml(__("{0} of {1} steps complete", [String(complete), String(total)])) +
				"</p></div>" +
				'<div class="kt-cl-ui01-progress-track" aria-hidden="true">' +
				'<div class="kt-cl-ui01-progress-fill" style="width:' +
				pct +
				'%"></div></div></div>'
			);
		},

		resourcesPanel: function (opts) {
			opts = opts || {};
			var items = opts.items || [];
			var list = items
				.map(function (item, idx) {
					var icon = item.icon || "description";
					return (
						'<li class="kt-cl-ui01-resources-item">' +
						'<span class="kt-cl-ui01-resources-link" data-testid="kt-cl-ui01-resource-' +
						idx +
						'">' +
						"<span>" +
						escapeHtml(item.label || "") +
						"</span>" +
						msIcon(icon, 16) +
						"</span></li>"
					);
				})
				.join("");
			return (
				'<div class="kt-cl-ui01-resources" data-testid="kt-cl-ui01-resources">' +
				'<h5 class="kt-cl-ui01-resources-title">' +
				__("Resources") +
				"</h5>" +
				"<ul class=\"kt-cl-ui01-resources-list\">" +
				list +
				"</ul></div>"
			);
		},

		stepDetailsDrawer: function (opts) {
			opts = opts || {};
			var h = spec().CONFIG_HOME || {};
			var step = opts.step || {};
			var db = parseInt(step.blocker_count, 10) || 0;
			var dw = parseInt(step.warning_count, 10) || 0;
			var issuesText =
				db || dw ? db + " Blockers / " + dw + " Warnings" : __("None");
			var issuesCls = db || dw ? " text-error font-bold" : "";
			return (
				'<div class="kt-cl-ui01-drawer-overlay ' +
				(h.drawerOverlay || "") +
				'" data-testid="kt-cl-ui01-drawer-overlay" role="dialog" aria-modal="true">' +
				'<aside class="kt-cl-ui01-drawer ' +
				(h.drawerPanel || "") +
				'" data-testid="kt-cl-ui01-drawer">' +
				'<header class="kt-cl-ui01-drawer-header">' +
				"<div>" +
				'<p class="text-label-sm text-on-surface-variant">' +
				escapeHtml(step.id || "") +
				"</p>" +
				'<h2 class="text-headline-md font-bold text-primary" data-testid="kt-cl-ui01-drawer-title">' +
				escapeHtml(step.title || "") +
				"</h2></div>" +
				'<button type="button" class="kt-cl-ui01-drawer-close" data-action="close-drawer" data-testid="kt-cl-ui01-drawer-close" aria-label="' +
				__("Close") +
				'">' +
				msIcon("close", 22) +
				"</button></header>" +
				'<div class="kt-cl-ui01-drawer-body">' +
				"<div><p class=\"text-label-sm text-on-surface-variant uppercase\">" +
				__("Purpose") +
				'</p><p class="text-body-md text-on-surface" data-testid="kt-cl-ui01-drawer-purpose">' +
				escapeHtml(step.description || "") +
				"</p></div>" +
				"<div><p class=\"text-label-sm text-on-surface-variant uppercase\">" +
				__("Status") +
				'</p><p class="text-body-md font-bold" data-testid="kt-cl-ui01-drawer-status">' +
				escapeHtml(step.status_label || "") +
				"</p></div>" +
				'<div data-testid="kt-cl-ui01-drawer-issues"><p class="text-label-sm text-on-surface-variant uppercase">' +
				__("Issues") +
				'</p><p class="text-body-md' +
				issuesCls +
				'">' +
				escapeHtml(issuesText) +
				"</p></div>" +
				"<div><p class=\"text-label-sm text-on-surface-variant uppercase\">" +
				__("What you will configure") +
				'</p><p class="text-body-sm" data-testid="kt-cl-ui01-drawer-will">' +
				escapeHtml(step.will_configure || "") +
				"</p></div>" +
				"<div><p class=\"text-label-sm text-on-surface-variant uppercase\">" +
				__("What this step does not configure") +
				'</p><p class="text-body-sm" data-testid="kt-cl-ui01-drawer-wont">' +
				escapeHtml(step.will_not_configure || "") +
				"</p></div></div>" +
				'<footer class="kt-cl-ui01-drawer-footer">' +
				'<button type="button" class="kt-cl-ui01-drawer-action" data-action="drawer-primary" data-route="' +
				escapeHtml(step.route || "") +
				'" data-testid="kt-cl-ui01-drawer-action">' +
				escapeHtml(step.action_label || __("Continue")) +
				"</button></footer></aside></div>"
			);
		},

		createTenderConfigurationModal: function (opts) {
			opts = opts || {};
			var q = spec().QUEUE || {};
			var selectedLabel = opts.selectedLabel || "";
			var hasSelection = !!opts.hasSelection;
			var preview = opts.preview || {};
			var placeholder = __("Select a package first");
			function field(label, value) {
				return (
					"<div>" +
					'<span class="text-label-sm font-label-sm text-secondary uppercase block mb-1">' +
					escapeHtml(label) +
					"</span>" +
					'<span class="text-body-md font-medium text-primary">' +
					escapeHtml(value || placeholder) +
					"</span></div>"
				);
			}
			var previewBlock = hasSelection
				? '<div class="bg-surface-container-low rounded p-6 border border-outline-variant" data-testid="kt-cl-uim01-preview">' +
					'<div class="flex items-center gap-2 mb-4">' +
					msIcon("info", 20, "text-on-secondary-container") +
					'<h3 class="text-label-md font-label-md text-on-secondary-container uppercase tracking-wider">' +
					__("Package Details Preview") +
					"</h3></div>" +
					'<div class="grid grid-cols-1 sm:grid-cols-2 gap-y-6 gap-x-12">' +
					field(__("Planning Package Ref"), preview.planning_package_ref) +
					field(__("Procurement Title"), preview.procurement_title) +
					field(__("Procuring Entity"), preview.procuring_entity_name) +
					field(__("Procurement Method"), preview.procurement_method_label) +
					field(__("STD Family"), preview.std_family_label) +
					field(__("Standard Tender Document"), preview.applicable_std_document_label) +
					"</div></div>"
				: '<div class="bg-surface-container-lowest rounded p-6 border border-outline-variant border-dashed" data-testid="kt-cl-uim01-empty">' +
					'<div class="flex flex-col items-center justify-center py-4 text-center">' +
					msIcon("find_in_page", 36, "text-outline") +
					'<p class="text-body-md text-on-surface-variant italic mt-2">' +
					__("Select a package to view configuration details") +
					"</p></div></div>";

			var createDisabled = hasSelection && opts.canCreate ? "" : " disabled";
			var createCls =
				"px-8 py-3 bg-primary text-on-primary font-bold text-body-md rounded shadow-sm hover:opacity-90 transition-all flex items-center gap-2" +
				(createDisabled ? " opacity-50 cursor-not-allowed" : "");

			return (
				'<div class="' +
				(q.modalOverlay || "") +
				'" data-testid="kt-cl-uim01-overlay" role="dialog" aria-modal="true">' +
				'<section class="' +
				(q.modalRoot || "") +
				'" data-testid="kt-cl-uim01-modal">' +
				'<header class="' +
				(q.modalHeader || "") +
				'">' +
				'<div class="flex justify-between items-start mb-2">' +
				'<h2 class="text-headline-lg font-headline-lg text-primary">' +
				__("Create Tender Configuration") +
				"</h2>" +
				'<button type="button" class="text-on-surface-variant hover:text-primary transition-colors" data-action="close" data-testid="kt-cl-uim01-close" aria-label="' +
				__("Close") +
				'">' +
				msIcon("close", 22) +
				"</button></div>" +
				'<p class="text-body-md text-on-surface-variant leading-relaxed">' +
				__(
					"Select an approved procurement package. KenTender will create a tender configuration using the applicable Standard Tender Document."
				) +
				"</p></header>" +
				'<div class="' +
				(q.modalBody || "") +
				'">' +
				'<div class="space-y-2">' +
				'<label class="block text-body-md font-bold text-primary">' +
				__("Approved Procurement Package") +
				"</label>" +
				'<div class="relative">' +
				'<button type="button" class="flex items-center w-full px-3 py-3 bg-surface-container-lowest border border-outline-variant rounded focus:ring-1 focus:ring-on-secondary-container text-left" data-action="toggle-package" data-testid="kt-cl-uim01-package-trigger">' +
				msIcon("search", 20, "text-on-surface-variant mr-3") +
				'<span class="text-body-md text-primary font-medium flex-1" data-testid="kt-cl-uim01-package-label">' +
				escapeHtml(selectedLabel || __("Choose an approved procurement package…")) +
				"</span>" +
				msIcon("arrow_drop_down", 22, "text-on-surface-variant") +
				"</button>" +
				'<div class="hidden absolute z-10 mt-1 w-full max-h-56 overflow-y-auto bg-surface-container-lowest border border-outline-variant rounded shadow-lg" data-testid="kt-cl-uim01-package-list"></div>' +
				"</div>" +
				'<p class="text-label-md font-label-md text-on-surface-variant">' +
				__("Choose the approved package that needs a tender configuration.") +
				"</p></div>" +
				previewBlock +
				"</div>" +
				'<footer class="' +
				(q.modalFooter || "") +
				'">' +
				'<button type="button" class="px-6 py-2 text-body-md font-medium text-secondary hover:bg-surface-container-highest transition-colors rounded" data-action="cancel" data-testid="kt-cl-uim01-cancel">' +
				__("Cancel") +
				"</button>" +
				'<button type="button" class="' +
				createCls +
				'" data-action="create" data-testid="kt-cl-uim01-create"' +
				createDisabled +
				">" +
				__("Create Configuration") +
				" " +
				msIcon("arrow_forward", 16) +
				"</button></footer></section></div>"
			);
		},

		/**
		 * Shared CFG/WF bottom bar: Back on the left; Save + primary Continue on the right.
		 * Primary CTA uses high-contrast on-primary (white) on navy — not muted on-primary-container.
		 */
		wizardStepFooter: function (opts) {
			opts = opts || {};
			var footerTestid = opts.testid || "kt-cl-wizard-footer";
			var backTestid = opts.backTestid || "kt-cl-wizard-back";
			var saveTestid = opts.saveTestid || "kt-cl-wizard-save";
			var continueTestid = opts.continueTestid || "kt-cl-wizard-continue";
			var saveDisabled = opts.saveDisabled ? " disabled" : "";
			var continueDisabled = opts.continueDisabled ? " disabled" : "";
			var continueIcon = opts.continueIcon === false ? "" : msIcon("arrow_forward", 16);
			return (
				'<div class="kt-cl-wizard-footer" data-testid="' +
				escapeHtml(footerTestid) +
				'">' +
				'<div class="kt-cl-wizard-footer-start">' +
				'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="' +
				escapeHtml(opts.backAction || "back-home") +
				'" data-testid="' +
				escapeHtml(backTestid) +
				'">' +
				escapeHtml(opts.backLabel || __("Back to Configuration Home")) +
				"</button></div>" +
				'<div class="kt-cl-wizard-footer-end">' +
				'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--outline" data-action="' +
				escapeHtml(opts.saveAction || "save") +
				'" data-testid="' +
				escapeHtml(saveTestid) +
				'"' +
				saveDisabled +
				">" +
				escapeHtml(opts.saveLabel || __("Save")) +
				"</button>" +
				'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="' +
				escapeHtml(opts.continueAction || "continue") +
				'" data-testid="' +
				escapeHtml(continueTestid) +
				'"' +
				continueDisabled +
				">" +
				escapeHtml(opts.continueLabel || __("Continue")) +
				continueIcon +
				"</button></div></div>"
			);
		},
	};

	// Library-friendly aliases so new pages compose via kentender_core.cl.components.*
	var C = kentender_core.cl_components;
	C.topBar = C.renderTopToolbar;
	C.breadcrumbs = C.renderBreadcrumbs;
	C.pageHeader = C.renderPageHeader;
	C.pageTitle = C.renderPageTitle;
	C.button = C.renderActionButton;
	C.filterBar = C.filterBar;
	C.bindFilterBar = C.bindFilterBar;

	frappe.provide("kentender_core.cl");
	kentender_core.cl.components = C;
})();
