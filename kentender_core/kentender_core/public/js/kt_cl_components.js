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
