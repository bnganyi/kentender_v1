/* ── Demand Intake and Approval — Hub Page ──────────────────────────────────── */
/* Sidebar pattern: frappe-custom-page-sidebar-pattern.mdc                      */
/* Route pattern:   frappe-workspace-route-pattern.mdc                           */

(function () {
	"use strict";

	// ── Font loader (same guard as Budget Hub) ────────────────────────────────
	function _ensureFonts() {
		if (document.getElementById("kt-dia-fonts")) return;
		var link = document.createElement("link");
		link.id = "kt-dia-fonts";
		link.rel = "stylesheet";
		link.href =
			"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&" +
			"family=Manrope:wght@600;700&" +
			"family=JetBrains+Mono:wght@400;500&" +
			"family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap";
		document.head.appendChild(link);
	}

	// ── H1: Page state ────────────────────────────────────────────────────────
	var _state = {
		portfolio:        {},
		roleKey:          "requisitioner",
		currency:         "KES",
		alignmentPct:     0,
		categoryBreakdown: { Goods: 0, Works: 0, Services: 0 },
		demands:          [],
		total:            0,
		hasMore:          false,
		page:             0,
		limit:            10,
		lifecycleFilter:  "all",
		search:           "",
		filters:          {},
		loading:          false,
		canCreate:        true,
	};

	var _STATUS_MAP = {
		draft:     { cls: "kt-dia-chip--draft",     lbl: "Draft" },
		submitted: { cls: "kt-dia-chip--submitted",  lbl: "Submitted" },
		dept:      { cls: "kt-dia-chip--dept",       lbl: "Dept. Review" },
		funding:   { cls: "kt-dia-chip--funding",    lbl: "Funding Review" },
		final:     { cls: "kt-dia-chip--final",      lbl: "Final Approval" },
		approved:  { cls: "kt-dia-chip--approved",   lbl: "Approved" },
		planning:  { cls: "kt-dia-chip--planning",   lbl: "Planning Ready" },
		rejected:  { cls: "kt-dia-chip--rejected",   lbl: "Rejected" },
		cancelled: { cls: "kt-dia-chip--cancelled",  lbl: "Cancelled" },
	};

	// Maps Demand.status (API) → _STATUS_MAP key
	var _API_STATUS_TO_KEY = {
		"Draft":                   "draft",
		"Pending HoD Approval":    "dept",
		"Pending Finance Approval":"funding",
		"Approved":                "approved",
		"Planning Ready":          "planning",
		"Rejected":                "rejected",
		"Cancelled":               "cancelled",
	};

	// Status chips with dot indicator — pulse for in-flight statuses
	var _CHIP_PULSE = { funding: true, dept: true };
	function _chip(statusKey) {
		var s = _STATUS_MAP[statusKey] || _STATUS_MAP.draft;
		var dotCls = "kt-dia-dot" + (_CHIP_PULSE[statusKey] ? " kt-dia-dot--pulse" : "");
		return (
			'<span class="kt-dia-chip ' + s.cls + '">' +
				'<span class="' + dotCls + '"></span>' +
				s.lbl +
			"</span>"
		);
	}

	// ── H3: Amount formatter ──────────────────────────────────────────────────
	function _fmt(amount, currency) {
		var num = parseFloat(amount);
		if (isNaN(num)) return "";
		var formatted = num.toLocaleString("en-KE", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		return (currency || "KES") + "\u00a0" + formatted;
	}

	// ── H3: Row builder from live API row ─────────────────────────────────────
	// d = row from get_dia_queue_list (fields: name, demand_id, title,
	//     requesting_department_label, requisition_type, total_amount, status)
	function _buildRow(d) {
		var statusKey = _API_STATUS_TO_KEY[d.status] || "draft";
		var dept = d.requesting_department_label || d.requesting_department || "";
		var amount = _fmt(d.total_amount, _state.currency);
		var demandName = d.name || "";
		var demandId   = d.demand_id || demandName;
		return (
			'<tr data-testid="kt-dia-row" data-demand-id="' + demandId + '" data-demand-name="' + demandName + '">' +
			"<td>" +
				'<div class="kt-dia-table__title" data-testid="kt-dia-row-title">' + (d.title || "") + "</div>" +
				'<div class="kt-dia-table__ref">REF: ' + demandId + "</div>" +
			"</td>" +
			'<td><span class="kt-dia-dept-chip">' + dept + "</span></td>" +
			"<td>" + (d.requisition_type || "") + "</td>" +
			'<td class="kt-dia-table__amount kt-dia-table__amount--right">' + amount + "</td>" +
			"<td>" + _chip(statusKey) + "</td>" +
			'<td class="kt-dia-table__actions-cell"><span class="kt-dia-table__action" data-action="open">Open</span></td>' +
			"</tr>"
		);
	}

	// ── HTML shell (skeleton table on first paint; API fills it via H3) ─────────
	function _html() {
		var rows = _skeletonRows();
		return (
'<div class="kt-dia-hub" data-testid="kt-dia-hub">' +

  // ── Top bar ──────────────────────────────────────────────────────────
  '<div class="kt-dia-topbar">' +
    '<div class="kt-dia-topbar__left">' +
      '<span class="kt-dia-topbar__title" data-testid="kt-dia-topbar-title">Demand Management</span>' +
      '<div class="kt-dia-topbar__sep"></div>' +
      '<span class="kt-dia-topbar__sub">KenTender DIA</span>' +
    '</div>' +
    '<div class="kt-dia-topbar__right">' +
      '<div class="kt-dia-topbar__search">' +
        '<span class="material-symbols-outlined">search</span>' +
        '<input type="text" placeholder="Search demands..." data-testid="kt-dia-search">' +
      '</div>' +
      '<button class="kt-dia-topbar__icon-btn" aria-label="Notifications">' +
        '<span class="material-symbols-outlined">notifications</span>' +
        '<span class="kt-dia-topbar__notif-dot"></span>' +
      '</button>' +
      '<button class="kt-dia-topbar__icon-btn" aria-label="Help">' +
        '<span class="material-symbols-outlined">help_outline</span>' +
      '</button>' +
      '<button class="kt-dia-topbar__icon-btn" aria-label="Account">' +
        '<span class="material-symbols-outlined">account_circle</span>' +
      '</button>' +
    '</div>' +
  '</div>' +

  // ── Main content ─────────────────────────────────────────────────────
  '<div class="kt-dia-main">' +

    // KPI strip
    '<div class="kt-dia-kpi-strip" data-testid="kt-dia-kpi-strip">' +

      // My Drafts
      '<div class="kt-dia-kpi-card kt-dia-kpi-card--active" data-testid="kt-dia-kpi-drafts">' +
        '<span class="kt-dia-kpi-card__icon"><span class="material-symbols-outlined">edit_note</span></span>' +
        '<div class="kt-dia-kpi-card__label">My Drafts</div>' +
        '<div class="kt-dia-kpi-card__count" data-testid="kt-dia-kpi-drafts-count">12 <em>Active</em></div>' +
        '<div class="kt-dia-kpi-bar"><div class="kt-dia-kpi-bar__fill" style="width:100%"></div></div>' +
        '<div class="kt-dia-kpi-card__meta">Last entry 2h ago</div>' +
      '</div>' +

      // Pending Dept Review
      '<div class="kt-dia-kpi-card" data-testid="kt-dia-kpi-dept">' +
        '<span class="kt-dia-kpi-card__icon"><span class="material-symbols-outlined">groups</span></span>' +
        '<div class="kt-dia-kpi-card__label">Pending Dept. Review</div>' +
        '<div class="kt-dia-kpi-card__count" data-testid="kt-dia-kpi-dept-count">8 <em>Units</em></div>' +
        '<div class="kt-dia-kpi-bar"><div class="kt-dia-kpi-bar__fill" style="width:50%"></div></div>' +
        '<div class="kt-dia-kpi-card__meta">Avg 1.2d wait</div>' +
      '</div>' +

      // Funding Review
      '<div class="kt-dia-kpi-card kt-dia-kpi-card--funding" data-testid="kt-dia-kpi-funding">' +
        '<span class="kt-dia-kpi-card__icon kt-dia-kpi-card__icon--funding"><span class="material-symbols-outlined">account_balance_wallet</span></span>' +
        '<div class="kt-dia-kpi-card__label">Funding Review</div>' +
        '<div class="kt-dia-kpi-card__count" data-testid="kt-dia-kpi-funding-count">5 <em>In Pipeline</em></div>' +
        '<div class="kt-dia-kpi-bar kt-dia-kpi-bar--funding"><div class="kt-dia-kpi-bar__fill" style="width:42%"></div></div>' +
        '<div class="kt-dia-kpi-card__badge kt-dia-kpi-card__badge--warn">High Priority</div>' +
      '</div>' +

      // Final Approval
      '<div class="kt-dia-kpi-card kt-dia-kpi-card--final" data-testid="kt-dia-kpi-final">' +
        '<span class="kt-dia-kpi-card__icon kt-dia-kpi-card__icon--final"><span class="material-symbols-outlined">verified</span></span>' +
        '<div class="kt-dia-kpi-card__label">Final Approval</div>' +
        '<div class="kt-dia-kpi-card__count" data-testid="kt-dia-kpi-final-count">3 <em>Ready</em></div>' +
        '<div class="kt-dia-kpi-bar kt-dia-kpi-bar--final"><div class="kt-dia-kpi-bar__fill" style="width:25%"></div></div>' +
        '<div class="kt-dia-kpi-card__badge kt-dia-kpi-card__badge--ok">Funding Validated</div>' +
      '</div>' +

    '</div>' + // end kpi-strip

    // Demand table section — header INSIDE the card (design pattern)
    '<div class="kt-dia-table-card">' +
      '<div class="kt-dia-section-hdr">' +
        '<div>' +
          '<div class="kt-dia-section-title">Active Departmental Demands</div>' +
          '<div class="kt-dia-section-sub">Real-time status of all procurement needs currently in the intake funnel.</div>' +
        '</div>' +
        '<div class="kt-dia-section-actions">' +
          '<button class="kt-dia-btn-new" data-testid="kt-dia-btn-new" data-dia="new-demand">' +
            '<span class="material-symbols-outlined">add</span>New Demand' +
          '</button>' +
          '<button class="kt-dia-btn-ghost" data-testid="kt-dia-btn-filter">' +
            '<span class="material-symbols-outlined">filter_list</span>' +
            'Filter<span class="kt-dia-filter-badge" data-testid="kt-dia-filter-badge" style="display:none"></span>' +
          '</button>' +
          '<button class="kt-dia-btn-ghost" data-testid="kt-dia-btn-export">' +
            '<span class="material-symbols-outlined">download</span>Export' +
          '</button>' +
        '</div>' +
      '</div>' +

      // H4: Lifecycle status chips
      '<div class="kt-dia-lifecycle-chips" data-testid="kt-dia-lifecycle-chips">' +
        '<button class="kt-dia-lc-chip kt-dia-lc-chip--active" data-lc="all" data-testid="kt-dia-chip-all">All</button>' +
        '<button class="kt-dia-lc-chip" data-lc="draft" data-testid="kt-dia-chip-draft">Draft</button>' +
        '<button class="kt-dia-lc-chip" data-lc="submitted" data-testid="kt-dia-chip-submitted">HoD Review</button>' +
        '<button class="kt-dia-lc-chip" data-lc="under_review" data-testid="kt-dia-chip-under-review">Finance Review</button>' +
        '<button class="kt-dia-lc-chip" data-lc="approved" data-testid="kt-dia-chip-approved">Approved</button>' +
        '<button class="kt-dia-lc-chip" data-lc="planning_ready" data-testid="kt-dia-chip-planning">Planning Ready</button>' +
        '<button class="kt-dia-lc-chip" data-lc="rejected" data-testid="kt-dia-chip-rejected">Rejected</button>' +
      '</div>' +

      // H7: Filter panel (collapsed by default)
      '<div class="kt-dia-filter-panel" data-testid="kt-dia-filter-panel" style="display:none">' +
        '<div class="kt-dia-filter-panel__fields">' +
          '<select class="kt-dia-filter-select" data-filter="demand_type" data-testid="kt-dia-filter-type">' +
            '<option value="">All Types</option>' +
          '</select>' +
          '<select class="kt-dia-filter-select" data-filter="requisition_type" data-testid="kt-dia-filter-category">' +
            '<option value="">All Categories</option>' +
          '</select>' +
          '<select class="kt-dia-filter-select" data-filter="requesting_department" data-testid="kt-dia-filter-dept">' +
            '<option value="">All Departments</option>' +
          '</select>' +
        '</div>' +
        '<div class="kt-dia-filter-panel__actions">' +
          '<button class="kt-dia-btn-ghost" data-action="apply-filters" data-testid="kt-dia-filter-apply">Apply</button>' +
          '<button class="kt-dia-btn-ghost kt-dia-btn-ghost--muted" data-action="clear-filters" data-testid="kt-dia-filter-clear">Clear</button>' +
        '</div>' +
      '</div>' +

      '<div class="kt-dia-table-scroll">' +
        '<table class="kt-dia-table" data-testid="kt-dia-table">' +
          '<thead>' +
            '<tr>' +
              '<th>Demand Title</th>' +
              '<th>Dept.</th>' +
              '<th>Category</th>' +
              '<th class="kt-dia-th--right">Est. Value</th>' +
              '<th>Status</th>' +
              '<th class="kt-dia-th--center">Actions</th>' +
            '</tr>' +
          '</thead>' +
          '<tbody data-testid="kt-dia-table-body">' + rows + '</tbody>' +
        '</table>' +
      '</div>' +

      '<div class="kt-dia-table-footer">' +
        '<div class="kt-dia-footer-left">' +
          '<label class="kt-dia-rpp-label">Rows per page:' +
            '<select class="kt-dia-rpp-select" data-testid="kt-dia-rows-per-page">' +
              '<option value="10" selected>10</option>' +
              '<option value="20">20</option>' +
              '<option value="50">50</option>' +
            '</select>' +
          '</label>' +
          '<span class="kt-dia-count-label" data-testid="kt-dia-table-count">Loading\u2026</span>' +
        '</div>' +
        '<div class="kt-dia-pagination" data-testid="kt-dia-pagination">' +
          '<button class="kt-dia-page-btn" data-page="prev" disabled>' +
            '<span class="material-symbols-outlined">chevron_left</span>' +
          '</button>' +
          '<div class="kt-dia-page-nums" data-testid="kt-dia-page-nums"></div>' +
          '<button class="kt-dia-page-btn" data-page="next" disabled>' +
            '<span class="material-symbols-outlined">chevron_right</span>' +
          '</button>' +
        '</div>' +
      '</div>' +
    '</div>' +

    // Analytics grid
    '<div class="kt-dia-analytics-grid">' +

      // Budget Consumption bar chart — shell; JS populates via _loadConsumptionChart()
      '<div class="kt-dia-analytics-card" data-testid="kt-dia-chart-card">' +
        '<div class="kt-dia-chart-header">' +
          '<div class="kt-dia-analytics-card__title" data-testid="kt-dia-chart-title">Budget Consumption</div>' +
        '</div>' +
        '<div class="kt-dia-bar-chart kt-dia-bar-chart--loading" data-testid="kt-dia-bar-chart">' +
          // skeleton bars shown until API resolves
          '<div class="kt-dia-chart-skeleton">' +
            '<div class="kt-dia-chart-skel-bar" style="height:72px"></div>' +
            '<div class="kt-dia-chart-skel-bar" style="height:52px"></div>' +
            '<div class="kt-dia-chart-skel-bar" style="height:88px"></div>' +
            '<div class="kt-dia-chart-skel-bar" style="height:40px"></div>' +
            '<div class="kt-dia-chart-skel-bar" style="height:64px"></div>' +
          '</div>' +
        '</div>' +
        '<div class="kt-dia-chart-legend" data-testid="kt-dia-chart-legend"></div>' +
      '</div>' +

      // Strategic Goal Match — light gradient card (design: primary/10 opacity)
      '<div class="kt-dia-goal-card" data-testid="kt-dia-goal-card">' +
        '<div class="kt-dia-goal-card__bg"></div>' +
        '<div class="kt-dia-goal-card__content">' +
          '<div class="kt-dia-goal-card__icon"><span class="material-symbols-outlined">auto_awesome</span></div>' +
          '<div class="kt-dia-goal-card__title">Strategic Goal Match</div>' +
          '<div class="kt-dia-goal-card__pct" data-testid="kt-dia-goal-pct">—</div>' +
          '<div class="kt-dia-goal-card__desc">of current demands align with the <strong>Vision 2030 Healthcare Modernisation</strong> pillar.</div>' +
          '<button class="kt-dia-goal-card__btn">Review Strategy Linkages</button>' +
        '</div>' +
      '</div>' +

    '</div>' + // end analytics-grid

  '</div>' + // end main

  // FAB
  '<button class="kt-dia-fab" data-testid="kt-dia-fab" data-dia="new-demand" aria-label="New Procurement Demand">' +
    '<span class="material-symbols-outlined">add</span>' +
    '<span class="kt-dia-fab__tooltip">New Procurement Demand</span>' +
  '</button>' +

'</div>'   // end kt-dia-hub
		);
	}

	// ── Mount ────────────────────────────────────────────────────────────────
	function _mount(wrapper) {
		_ensureFonts();
		if (!wrapper) return;
		if (wrapper.querySelector(".kt-dia-hub")) return; // already mounted
		wrapper.innerHTML = _html();
		_bindEvents(wrapper);
	}

	// ── H8: Skeleton rows ─────────────────────────────────────────────────────
	function _skeletonRows() {
		var row = "";
		for (var i = 0; i < 5; i++) {
			row += '<tr class="kt-dia-skeleton-row">';
			for (var j = 0; j < 6; j++) {
				row += '<td><div class="kt-dia-skeleton"></div></td>';
			}
			row += "</tr>";
		}
		return row;
	}

	// ── H2: KPI strip update ──────────────────────────────────────────────────
	var _KPI_CONFIG = [
		{ testid: "kt-dia-kpi-drafts",  countTestid: "kt-dia-kpi-drafts-count",  field: "draft_count",         label: "Active" },
		{ testid: "kt-dia-kpi-dept",    countTestid: "kt-dia-kpi-dept-count",    field: "submitted_count",      label: "Units" },
		{ testid: "kt-dia-kpi-funding", countTestid: "kt-dia-kpi-funding-count", field: "under_review_count",   label: "In Pipeline" },
		{ testid: "kt-dia-kpi-final",   countTestid: "kt-dia-kpi-final-count",   field: "approved_count",       label: "Ready" },
	];

	function _renderKpis() {
		var p = _state.portfolio || {};
		var total = Math.max(p.total || 0, 1);
		_KPI_CONFIG.forEach(function (cfg) {
			var count = p[cfg.field] || 0;
			var countEl = document.querySelector('[data-testid="' + cfg.countTestid + '"]');
			if (countEl) {
				countEl.innerHTML = count + " <em>" + cfg.label + "</em>";
			}
			var card = document.querySelector('[data-testid="' + cfg.testid + '"]');
			if (card) {
				var fill = card.querySelector(".kt-dia-kpi-bar__fill");
				if (fill) {
					fill.style.width = Math.min(100, Math.round(count / total * 100)) + "%";
				}
			}
		});
	}

	// ── H11: Strategic Goal Match ─────────────────────────────────────────────
	function _renderGoalMatch() {
		var el = document.querySelector('[data-testid="kt-dia-goal-pct"]');
		if (el) el.textContent = _state.alignmentPct + "%";
	}

	// ── H8: Table loading skeleton ────────────────────────────────────────────
	function _showTableSkeleton() {
		var tbody = document.querySelector('[data-testid="kt-dia-table-body"]');
		if (tbody) tbody.innerHTML = _skeletonRows();
		var countEl = document.querySelector('[data-testid="kt-dia-table-count"]');
		if (countEl) countEl.textContent = "Loading\u2026";
	}

	// ── H3: Render demand rows ────────────────────────────────────────────────
	function _renderTable(emptyCaption) {
		var tbody = document.querySelector('[data-testid="kt-dia-table-body"]');
		if (!tbody) return;
		tbody.classList.remove('kt-dia-table-body--loading');
		if (!_state.demands.length) {
			tbody.innerHTML =
				'<tr><td colspan="6" class="kt-dia-table__empty">' +
				(emptyCaption || "No demands found.") +
				"</td></tr>";
		} else {
			tbody.innerHTML = _state.demands.map(_buildRow).join("");
		}
		// Update count label
		var countEl = document.querySelector('[data-testid="kt-dia-table-count"]');
		if (countEl) {
			if (_state.demands.length) {
				var start = _state.page * _state.limit + 1;
				var end   = _state.page * _state.limit + _state.demands.length;
				var total = _state.total;
				countEl.textContent =
					total > 0
						? "Showing " + start + " to " + end + " of " + total + " demands"
						: "Showing " + start + " to " + end + " demands";
			} else {
				countEl.textContent = "No demands match this view.";
			}
		}
		// Prev / next
		var prevBtn = document.querySelector('[data-page="prev"]');
		var nextBtn = document.querySelector('[data-page="next"]');
		if (prevBtn) prevBtn.disabled = _state.page === 0;
		if (nextBtn) nextBtn.disabled = !_state.hasMore;
		// Numbered page buttons
		_renderPageButtons();
	}

	// ── Numbered page buttons ─────────────────────────────────────────────────
	function _renderPageButtons() {
		var container = document.querySelector('[data-testid="kt-dia-page-nums"]');
		if (!container) return;
		var totalPages = _state.total > 0
			? Math.ceil(_state.total / _state.limit)
			: (_state.hasMore ? _state.page + 2 : _state.page + 1);
		if (totalPages <= 1) {
			container.innerHTML = '';
			return;
		}
		var current = _state.page; // 0-indexed
		// Build page window: always show first, last, and up to 3 around current
		var pages = [];
		var WINDOW = 2;
		for (var p = 0; p < totalPages; p++) {
			if (
				p === 0 ||
				p === totalPages - 1 ||
				(p >= current - WINDOW && p <= current + WINDOW)
			) {
				pages.push(p);
			}
		}
		// Insert ellipsis markers
		var html = '';
		var prev = -1;
		for (var i = 0; i < pages.length; i++) {
			if (prev !== -1 && pages[i] > prev + 1) {
				html += '<span class="kt-dia-page-ellipsis">\u2026</span>';
			}
			var active = pages[i] === current ? ' kt-dia-page-num--active' : '';
			html +=
				'<button class="kt-dia-page-num' + active + '" data-page-num="' + pages[i] + '">' +
				(pages[i] + 1) +
				'</button>';
			prev = pages[i];
		}
		container.innerHTML = html;
	}

	// ── H3: Load demand list from API ─────────────────────────────────────────
	function _loadDemands(resetPage) {
		if (resetPage) _state.page = 0;

		var tbody = document.querySelector('[data-testid="kt-dia-table-body"]');
		var hasCurrentRows = tbody && tbody.querySelector('tr[data-demand-name]');
		if (hasCurrentRows) {
			// Rows already visible — dim in place instead of wiping to skeleton
			tbody.classList.add('kt-dia-table-body--loading');
		} else {
			_showTableSkeleton();
		}

		var args = {
			work_tab: "all",
			limit: _state.limit,
			start: _state.page * _state.limit,
		};
		if (_state.lifecycleFilter && _state.lifecycleFilter !== "all") {
			args.lifecycle_filter = _state.lifecycleFilter;
		}
		if (_state.search) args.search = _state.search;
		if (Object.keys(_state.filters).length) {
			args.filters = JSON.stringify(_state.filters);
		}
		frappe.call({
			method: "kentender_procurement.demand_intake.api.queue_list.get_dia_queue_list",
			args: args,
			callback: function (r) {
				var data = (r && r.message) || {};
				_state.demands = data.demands || [];
				_state.hasMore = !!data.has_more;
				_state.total   = (typeof data.total_count === "number") ? data.total_count : 0;
				_renderTable(data.empty_caption);
			},
			error: function () {
				var tbody = document.querySelector('[data-testid="kt-dia-table-body"]');
				if (tbody) {
					tbody.classList.remove('kt-dia-table-body--loading');
					tbody.innerHTML =
						'<tr><td colspan="6" class="kt-dia-table__empty">Failed to load demands. Please refresh.</td></tr>';
				}
			},
		});
	}

	// ── H4: Lifecycle chip active state ──────────────────────────────────────
	function _renderLifecycleChips() {
		var chips = document.querySelectorAll("[data-lc]");
		chips.forEach(function (chip) {
			var active = chip.getAttribute("data-lc") === _state.lifecycleFilter;
			chip.classList.toggle("kt-dia-lc-chip--active", active);
		});
	}

	// ── H7: Filter meta (loaded once, cached) ────────────────────────────────
	var _filterMeta = null;

	function _loadFilterMeta(cb) {
		if (_filterMeta) { cb(_filterMeta); return; }
		frappe.call({
			method: "kentender_procurement.demand_intake.api.queue_list.get_dia_queue_filter_meta",
			callback: function (r) {
				var data = (r && r.message) || {};
				if (data.ok) {
					_filterMeta = data;
					cb(_filterMeta);
				}
			},
		});
	}

	function _populateFilterPanel(meta) {
		var typeEl  = document.querySelector('[data-filter="demand_type"]');
		var catEl   = document.querySelector('[data-filter="requisition_type"]');
		var deptEl  = document.querySelector('[data-filter="requesting_department"]');
		if (!typeEl || !catEl || !deptEl) return;

		function _opts(items, labelKey) {
			return (items || []).map(function (v) {
				var val   = typeof v === "string" ? v : v.value;
				var label = typeof v === "string" ? v : (v.label || v.value);
				return '<option value="' + val + '">' + label + "</option>";
			}).join("");
		}
		typeEl.innerHTML = '<option value="">All Types</option>' + _opts(meta.demand_types || []);
		catEl.innerHTML  = '<option value="">All Categories</option>' + _opts(meta.requisition_types || []);
		deptEl.innerHTML = '<option value="">All Departments</option>' + _opts(meta.departments || []);

		// Restore current filter selections
		typeEl.value = _state.filters.demand_type || "";
		catEl.value  = _state.filters.requisition_type || "";
		deptEl.value = _state.filters.requesting_department || "";
	}

	function _toggleFilterPanel() {
		var panel = document.querySelector('[data-testid="kt-dia-filter-panel"]');
		if (!panel) return;
		var open = panel.style.display !== "none";
		if (open) {
			panel.style.display = "none";
		} else {
			panel.style.display = "";
			_loadFilterMeta(_populateFilterPanel);
		}
	}

	function _applyFilters() {
		var typeEl  = document.querySelector('[data-filter="demand_type"]');
		var catEl   = document.querySelector('[data-filter="requisition_type"]');
		var deptEl  = document.querySelector('[data-filter="requesting_department"]');
		var filters = {};
		if (typeEl  && typeEl.value)  filters.demand_type            = typeEl.value;
		if (catEl   && catEl.value)   filters.requisition_type       = catEl.value;
		if (deptEl  && deptEl.value)  filters.requesting_department  = deptEl.value;
		_state.filters = filters;
		_updateFilterBadge();
		_toggleFilterPanel();
		_loadDemands(true);
	}

	function _clearFilters() {
		_state.filters = {};
		_updateFilterBadge();
		// Reset selects
		var panel = document.querySelector('[data-testid="kt-dia-filter-panel"]');
		if (panel) {
			panel.querySelectorAll("select").forEach(function (s) { s.value = ""; });
		}
		_toggleFilterPanel();
		_loadDemands(true);
	}

	function _updateFilterBadge() {
		var count = Object.keys(_state.filters).length;
		var badge = document.querySelector('[data-testid="kt-dia-filter-badge"]');
		if (!badge) return;
		if (count > 0) {
			badge.textContent = String(count);
			badge.style.display = "inline-flex";
		} else {
			badge.style.display = "none";
		}
	}

	// ── H12: Consumption chart ───────────────────────────────────────────────
	var _CHART_BAR_MAX_H = 96; // px — tallest bar height
	var _CHART_SERIES = [
		{ key: "total_value",    cls: "kt-dia-bar--total",    label: "Total Planned" },
		{ key: "approved_value", cls: "kt-dia-bar--approved", label: "Approved & Ready" },
	];

	function _renderConsumptionChart(data) {
		var chartEl  = document.querySelector('[data-testid="kt-dia-bar-chart"]');
		var titleEl  = document.querySelector('[data-testid="kt-dia-chart-title"]');
		var legendEl = document.querySelector('[data-testid="kt-dia-chart-legend"]');
		if (!chartEl) return;

		if (titleEl && data.period_label) {
			titleEl.textContent = "Budget Consumption — " + data.period_label;
		}

		var bars = data.bars || [];
		if (!bars.length) {
			chartEl.classList.remove("kt-dia-bar-chart--loading");
			chartEl.innerHTML =
				'<div class="kt-dia-chart-empty">No active demand data for this period.</div>';
			return;
		}

		// Compute scale: tallest total_value → _CHART_BAR_MAX_H px
		var maxVal = Math.max.apply(null, bars.map(function (b) { return b.total_value || 0; }));
		if (maxVal <= 0) maxVal = 1;

		function _scalePx(val) {
			return Math.max(4, Math.round((val / maxVal) * _CHART_BAR_MAX_H));
		}

		var groupsHtml = bars.map(function (b) {
			var barsHtml = _CHART_SERIES.map(function (s) {
				var h = _scalePx(b[s.key] || 0);
				var title = s.label + ": " + _fmt(b[s.key] || 0, _state.currency);
				return '<div class="kt-dia-bar ' + s.cls + '" style="height:' + h + 'px" title="' + title + '"></div>';
			}).join('');
			// Truncate long labels to keep layout clean
			var lbl = (b.label || '').length > 12 ? b.label.slice(0, 11) + '…' : (b.label || '');
			return (
				'<div class="kt-dia-bar-group">' +
					'<div class="kt-dia-bar-group__bars">' + barsHtml + '</div>' +
					'<div class="kt-dia-bar-group__label" title="' + (b.label || '') + '">' + lbl + '</div>' +
				'</div>'
			);
		}).join('');

		chartEl.classList.remove("kt-dia-bar-chart--loading");
		chartEl.innerHTML = groupsHtml;

		if (legendEl) {
			legendEl.innerHTML = _CHART_SERIES.map(function (s) {
				return '<div class="kt-dia-legend-item">' +
					'<div class="kt-dia-legend-dot kt-dia-legend-dot--' + s.cls.replace('kt-dia-bar--', '') + '"></div>' +
					s.label +
				'</div>';
			}).join('');
		}
	}

	function _loadConsumptionChart() {
		frappe.call({
			method: "kentender_procurement.demand_intake.api.chart.get_dia_consumption_chart_data",
			callback: function (r) {
				var data = (r && r.message) || {};
				if (data.ok) {
					_renderConsumptionChart(data);
				} else {
					var chartEl = document.querySelector('[data-testid="kt-dia-bar-chart"]');
					if (chartEl) {
						chartEl.classList.remove("kt-dia-bar-chart--loading");
						chartEl.innerHTML = '<div class="kt-dia-chart-empty">Chart data unavailable.</div>';
					}
				}
			},
			error: function () {
				var chartEl = document.querySelector('[data-testid="kt-dia-bar-chart"]');
				if (chartEl) {
					chartEl.classList.remove("kt-dia-bar-chart--loading");
					chartEl.innerHTML = '<div class="kt-dia-chart-empty">Could not load chart.</div>';
				}
			},
		});
	}

	// ── H1: Load landing data (KPIs + alignment + trigger table) ─────────────
	function _loadLandingData() {
		frappe.call({
			method: "kentender_procurement.demand_intake.api.landing.get_dia_landing_shell_data",
			callback: function (r) {
				var data = (r && r.message) || {};
				if (!data.ok) {
					_renderInlineError(data.message || "Unable to load Demand Hub. Check your permissions.");
					return;
				}
				_state.portfolio        = data.portfolio || {};
				_state.roleKey          = data.role_key || "requisitioner";
				_state.currency         = data.currency || "KES";
				_state.alignmentPct     = typeof data.alignment_pct === "number" ? data.alignment_pct : 0;
				_state.categoryBreakdown= data.category_breakdown || {};
				_state.canCreate        = data.can_create !== false;
				_renderKpis();
				_renderGoalMatch();
				_loadDemands(true);
				_loadConsumptionChart();
			},
			error: function () {
				_renderInlineError("Could not connect to the server. Please refresh the page.");
			},
		});
	}

	// ── H1: Inline error banner (replaces hub content) ────────────────────────
	function _renderInlineError(msg) {
		var hub = document.querySelector('[data-testid="kt-dia-hub"]');
		if (!hub) return;
		hub.innerHTML =
			'<div class="kt-dia-error-banner" role="alert">' +
				'<span class="material-symbols-outlined">error_outline</span>' +
				"<span>" + (msg || "An error occurred.") + "</span>" +
			"</div>";
	}

	// ── H5: Search debounce timer ─────────────────────────────────────────────
	var _searchTimer = null;

	// ── H4, H5, H6, H7, H9, H10: Event bindings ──────────────────────────────
	function _bindEvents(wrapper) {
		wrapper.addEventListener("click", function (e) {
			// H9: Open demand row
			var openAction = e.target.closest("[data-action='open']");
			if (openAction) {
				var row = openAction.closest("tr[data-demand-name]");
				if (row) {
					var name = row.getAttribute("data-demand-name");
					if (name) frappe.set_route("demand-workbench", name);
				}
				return;
			}

			// H10: New Demand (section button or FAB) → route to Create Demand wizard
			if (e.target.closest("[data-dia='new-demand']")) {
				frappe.set_route("create-demand");
				return;
			}

			// H4: Lifecycle chip
			var chip = e.target.closest("[data-lc]");
			if (chip) {
				_state.lifecycleFilter = chip.getAttribute("data-lc") || "all";
				_renderLifecycleChips();
				_loadDemands(true);
				return;
			}

			// H7: Toggle filter panel
			if (e.target.closest('[data-testid="kt-dia-btn-filter"]')) {
				_toggleFilterPanel();
				return;
			}

			// H7: Apply / clear filters
			if (e.target.closest('[data-action="apply-filters"]')) {
				_applyFilters();
				return;
			}
			if (e.target.closest('[data-action="clear-filters"]')) {
				_clearFilters();
				return;
			}

			// H6: Pagination prev / next
			var pageBtn = e.target.closest("[data-page]");
			if (pageBtn) {
				var dir = pageBtn.getAttribute("data-page");
				if (dir === "prev" && _state.page > 0) {
					_state.page--;
					_loadDemands(false);
				} else if (dir === "next" && _state.hasMore) {
					_state.page++;
					_loadDemands(false);
				}
				return;
			}
		});

		// H5: Debounced search
		var searchInput = wrapper.querySelector('[data-testid="kt-dia-search"]');
		if (searchInput) {
			searchInput.addEventListener("input", function () {
				clearTimeout(_searchTimer);
				var val = searchInput.value.trim();
				_searchTimer = setTimeout(function () {
					_state.search = val;
					_loadDemands(true);
				}, 300);
			});
		}

		// Rows-per-page selector
		var rppSelect = wrapper.querySelector('[data-testid="kt-dia-rows-per-page"]');
		if (rppSelect) {
			rppSelect.addEventListener("change", function () {
				_state.limit = parseInt(rppSelect.value, 10) || 10;
				_loadDemands(true);
			});
		}

		// Numbered page buttons (delegated — container is rebuilt on each render)
		var pagination = wrapper.querySelector('[data-testid="kt-dia-pagination"]');
		if (pagination) {
			pagination.addEventListener("click", function (e) {
				var numBtn = e.target.closest('[data-page-num]');
				if (numBtn) {
					var pg = parseInt(numBtn.getAttribute('data-page-num'), 10);
					if (!isNaN(pg) && pg !== _state.page) {
						_state.page = pg;
						_loadDemands(false);
					}
				}
			});
		}
	}

	// ── Frappe page registration ──────────────────────────────────────────────
	frappe.pages["demand-hub"].on_page_load = function (wrapper) {
		_mount(wrapper);
	};

	frappe.pages["demand-hub"].on_page_show = function (wrapper) {
		document.body.classList.add("kt-dia-shell");

		// REQUIRED: defer so Frappe's sidebar reset fires first, then we restore.
		// See: .cursor/rules/frappe-custom-page-sidebar-pattern.mdc
		setTimeout(function () {
			if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
				frappe.app.sidebar.setup("Demand Intake and Approval");
			}
		}, 0);

		_mount(wrapper);
		_loadLandingData();
	};

	frappe.pages["demand-hub"].on_page_hide = function () {
		document.body.classList.remove("kt-dia-shell");
	};
})();
