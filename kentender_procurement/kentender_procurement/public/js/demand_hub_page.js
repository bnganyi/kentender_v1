/* ── Demand Intake and Approval — Hub Page (static shell, no backend) ─────── */
/* Sidebar pattern: frappe-custom-page-sidebar-pattern.mdc                     */
/* Route pattern:   frappe-workspace-route-pattern.mdc                          */

(function () {
	"use strict";

	// ── Font loader (same guard as Budget Hub) ───────────────────────────────
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

	// ── Static demand rows (placeholder until API wiring) ───────────────────
	var _DEMO_ROWS = [
		{
			id: "DM-2024-001", ref: "REF: DM-2024-001",
			title: "District Hospital Renovation Works",
			dept: "Health Services", category: "Works",
			amount: "KES 98,000,000", status: "funding",
		},
		{
			id: "DM-2024-002", ref: "REF: DM-2024-002",
			title: "Security Systems Upgrade — HQ",
			dept: "Admin & ICT", category: "Goods",
			amount: "KES 14,200,000", status: "dept",
		},
		{
			id: "DM-2024-003", ref: "REF: DM-2024-003",
			title: "Legal Advisory Framework 2024",
			dept: "Legal Affairs", category: "Consultancy",
			amount: "KES 5,500,000", status: "final",
		},
		{
			id: "DM-2024-004", ref: "REF: DM-2024-004",
			title: "Emergency Medical Supplies",
			dept: "Health Services", category: "Goods",
			amount: "KES 22,150,000", status: "draft",
		},
	];

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

	function _chip(status) {
		var s = _STATUS_MAP[status] || _STATUS_MAP.draft;
		return '<span class="kt-dia-chip ' + s.cls + '">' + s.lbl + "</span>";
	}

	function _buildRow(d) {
		return (
			'<tr data-testid="kt-dia-row" data-demand-id="' + d.id + '">' +
			"<td>" +
				'<div class="kt-dia-table__title" data-testid="kt-dia-row-title">' + d.title + "</div>" +
				'<div class="kt-dia-table__ref">' + d.ref + "</div>" +
			"</td>" +
			'<td class="kt-dia-table__dept">' + d.dept + "</td>" +
			"<td>" + d.category + "</td>" +
			'<td class="kt-dia-table__amount">' + d.amount + "</td>" +
			"<td>" + _chip(d.status) + "</td>" +
			'<td><span class="kt-dia-table__action">OPEN</span></td>' +
			"</tr>"
		);
	}

	// ── Static HTML shell ────────────────────────────────────────────────────
	function _html() {
		var rows = _DEMO_ROWS.map(_buildRow).join("");
		return (
'<div class="kt-dia-hub" data-testid="kt-dia-hub">' +

  // ── Top bar ──────────────────────────────────────────────────────────
  '<div class="kt-dia-topbar">' +
    '<span class="kt-dia-topbar__title" data-testid="kt-dia-topbar-title">Demand Management</span>' +
    '<div class="kt-dia-topbar__search">' +
      '<span class="material-symbols-outlined">search</span>' +
      '<input type="text" placeholder="Search demands..." data-testid="kt-dia-search">' +
    '</div>' +
    '<div class="kt-dia-topbar__actions">' +
      '<button class="kt-dia-btn-new" data-testid="kt-dia-btn-new" data-dia="new-demand">' +
        '<span class="material-symbols-outlined">add</span>New Demand' +
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
        '<span class="kt-dia-kpi-card__icon"><span class="material-symbols-outlined">group</span></span>' +
        '<div class="kt-dia-kpi-card__label">Pending Dept. Review</div>' +
        '<div class="kt-dia-kpi-card__count" data-testid="kt-dia-kpi-dept-count">8 <em>Units</em></div>' +
        '<div class="kt-dia-kpi-bar"><div class="kt-dia-kpi-bar__fill" style="width:67%"></div></div>' +
        '<div class="kt-dia-kpi-card__meta">Avg 1.2d wait</div>' +
      '</div>' +

      // Funding Review
      '<div class="kt-dia-kpi-card" data-testid="kt-dia-kpi-funding">' +
        '<span class="kt-dia-kpi-card__icon"><span class="material-symbols-outlined">account_balance_wallet</span></span>' +
        '<div class="kt-dia-kpi-card__label">Funding Review</div>' +
        '<div class="kt-dia-kpi-card__count" data-testid="kt-dia-kpi-funding-count">5 <em>In Pipeline</em></div>' +
        '<div class="kt-dia-kpi-bar"><div class="kt-dia-kpi-bar__fill" style="width:42%"></div></div>' +
        '<div class="kt-dia-kpi-card__badge kt-dia-kpi-card__badge--warn">High Priority</div>' +
      '</div>' +

      // Final Approval
      '<div class="kt-dia-kpi-card" data-testid="kt-dia-kpi-final">' +
        '<span class="kt-dia-kpi-card__icon"><span class="material-symbols-outlined">verified</span></span>' +
        '<div class="kt-dia-kpi-card__label">Final Approval</div>' +
        '<div class="kt-dia-kpi-card__count" data-testid="kt-dia-kpi-final-count">3 <em>Ready</em></div>' +
        '<div class="kt-dia-kpi-bar"><div class="kt-dia-kpi-bar__fill" style="width:25%"></div></div>' +
        '<div class="kt-dia-kpi-card__badge kt-dia-kpi-card__badge--ok">Funding Validated</div>' +
      '</div>' +

    '</div>' + // end kpi-strip

    // Demand table section
    '<div>' +
      '<div class="kt-dia-section-hdr">' +
        '<div>' +
          '<span class="kt-dia-section-title">Active Departmental Demands</span>' +
          '<span class="kt-dia-section-sub">Real-time status of all procurement needs currently in the intake funnel.</span>' +
        '</div>' +
        '<div class="kt-dia-section-actions">' +
          '<button class="kt-dia-btn-ghost" data-testid="kt-dia-btn-filter">' +
            '<span class="material-symbols-outlined">filter_list</span>Filter' +
          '</button>' +
          '<button class="kt-dia-btn-ghost" data-testid="kt-dia-btn-export">' +
            '<span class="material-symbols-outlined">download</span>Export' +
          '</button>' +
        '</div>' +
      '</div>' +

      '<div class="kt-dia-table-card">' +
        '<table class="kt-dia-table" data-testid="kt-dia-table">' +
          '<thead>' +
            '<tr>' +
              '<th>Demand Title</th>' +
              '<th>Dept.</th>' +
              '<th>Category</th>' +
              '<th>Est. Value</th>' +
              '<th>Status</th>' +
              '<th>Actions</th>' +
            '</tr>' +
          '</thead>' +
          '<tbody data-testid="kt-dia-table-body">' + rows + '</tbody>' +
        '</table>' +
        '<div class="kt-dia-table-footer">' +
          '<span data-testid="kt-dia-table-count">Showing 1 to 4 of 28 demands</span>' +
          '<div class="kt-dia-pagination">' +
            '<button class="kt-dia-page-btn"><span class="material-symbols-outlined">chevron_left</span></button>' +
            '<button class="kt-dia-page-btn kt-dia-page-btn--active">1</button>' +
            '<button class="kt-dia-page-btn">2</button>' +
            '<button class="kt-dia-page-btn">3</button>' +
            '<button class="kt-dia-page-btn"><span class="material-symbols-outlined">chevron_right</span></button>' +
          '</div>' +
        '</div>' +
      '</div>' +
    '</div>' +

    // Analytics grid
    '<div class="kt-dia-analytics-grid">' +

      // Budget Consumption bar chart
      '<div class="kt-dia-analytics-card" data-testid="kt-dia-chart-card">' +
        '<div class="kt-dia-analytics-card__title">Budget Consumption (Q1 – 2026)</div>' +
        '<div class="kt-dia-bar-chart">' +
          '<div class="kt-dia-bar-group">' +
            '<div class="kt-dia-bar-group__bars">' +
              '<div class="kt-dia-bar kt-dia-bar--health" style="height:85px"></div>' +
              '<div class="kt-dia-bar kt-dia-bar--infra"  style="height:60px"></div>' +
            '</div>' +
            '<div class="kt-dia-bar-group__label">Health</div>' +
          '</div>' +
          '<div class="kt-dia-bar-group">' +
            '<div class="kt-dia-bar-group__bars">' +
              '<div class="kt-dia-bar kt-dia-bar--ict"   style="height:45px"></div>' +
              '<div class="kt-dia-bar kt-dia-bar--admin" style="height:30px"></div>' +
            '</div>' +
            '<div class="kt-dia-bar-group__label">ICT</div>' +
          '</div>' +
          '<div class="kt-dia-bar-group">' +
            '<div class="kt-dia-bar-group__bars">' +
              '<div class="kt-dia-bar kt-dia-bar--health" style="height:95px"></div>' +
              '<div class="kt-dia-bar kt-dia-bar--infra"  style="height:70px"></div>' +
            '</div>' +
            '<div class="kt-dia-bar-group__label">Infrastructure</div>' +
          '</div>' +
          '<div class="kt-dia-bar-group">' +
            '<div class="kt-dia-bar-group__bars">' +
              '<div class="kt-dia-bar kt-dia-bar--admin" style="height:40px"></div>' +
              '<div class="kt-dia-bar kt-dia-bar--ict"   style="height:20px"></div>' +
            '</div>' +
            '<div class="kt-dia-bar-group__label">Admin</div>' +
          '</div>' +
        '</div>' +
        '<div class="kt-dia-chart-legend">' +
          '<div class="kt-dia-legend-item"><div class="kt-dia-legend-dot" style="background:#00346f"></div>Health</div>' +
          '<div class="kt-dia-legend-item"><div class="kt-dia-legend-dot" style="background:#7c9bc7"></div>Infrastructure</div>' +
        '</div>' +
      '</div>' +

      // Strategic Goal Match
      '<div class="kt-dia-goal-card" data-testid="kt-dia-goal-card">' +
        '<div class="kt-dia-goal-card__icon"><span class="material-symbols-outlined">auto_awesome</span></div>' +
        '<div class="kt-dia-goal-card__title">Strategic Goal Match</div>' +
        '<div class="kt-dia-goal-card__pct" data-testid="kt-dia-goal-pct">84%</div>' +
        '<div class="kt-dia-goal-card__desc">of current demands align with the <strong>Vision 2030 Healthcare Modernisation</strong> pillar.</div>' +
        '<button class="kt-dia-goal-card__btn">Review Strategy Linkages</button>' +
      '</div>' +

    '</div>' + // end analytics-grid

  '</div>' + // end main
'</div>'   // end kt-dia-hub
		);
	}

	// ── Mount ────────────────────────────────────────────────────────────────
	function _mount(wrapper) {
		_ensureFonts();
		if (!wrapper) return;
		if (wrapper.querySelector(".kt-dia-hub")) return; // already mounted
		wrapper.innerHTML = _html();
	}

	// ── Frappe page registration ─────────────────────────────────────────────
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
	};

	frappe.pages["demand-hub"].on_page_hide = function () {
		document.body.classList.remove("kt-dia-shell");
	};
})();
