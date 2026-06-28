/* global frappe */
// ── Budget Hub page — live data wired to get_budget_landing_data ────────────
(function () {
	"use strict";

	// ── Inject Google Fonts + Material Symbols if not already present ─────────
	function _ensureFonts() {
		if (!document.getElementById("kt-bgt-fonts")) {
			const l = document.createElement("link");
			l.id = "kt-bgt-fonts";
			l.rel = "stylesheet";
			l.href =
				"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700" +
				"&family=Manrope:wght@600;700;800" +
				"&family=JetBrains+Mono:wght@500&display=swap";
			document.head.appendChild(l);
		}
		if (!document.getElementById("kt-bgt-icons")) {
			const l = document.createElement("link");
			l.id = "kt-bgt-icons";
			l.rel = "stylesheet";
			l.href =
				"https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap";
			document.head.appendChild(l);
		}
	}

	// ── Number formatting ─────────────────────────────────────────────────────

	/** Full KES with commas — for KPI cards */
	function _fmtFull(n) {
		if (n === null || n === undefined || isNaN(n)) return "—";
		return Math.round(n).toLocaleString("en-KE");
	}

	/** Compact million/billion — kept for internal use */
	function _fmtCompact(n) {
		if (n === null || n === undefined || isNaN(n)) return "—";
		if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(2) + "B";
		if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1) + "M";
		if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1) + "K";
		return Math.round(n).toLocaleString("en-KE");
	}

	/** KES + full toLocaleString — for table available cells (W1-03) */
	function _fmtKES(n) {
		if (n === null || n === undefined || isNaN(n)) return "—";
		return "KES\u00a0" + Math.round(n).toLocaleString("en-KE");
	}

	/** Percentage rounded to 1 dp */
	function _fmtPct(n) {
		if (n === null || n === undefined || isNaN(n)) return "0%";
		return Math.round(n) + "%";
	}

	/** Build initials from a display name (or user email) */
	function _initials(name) {
		if (!name) return "?";
		const parts = name.trim().split(/\s+/);
		if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
		return name.substring(0, 2).toUpperCase();
	}

	// ── Relative timestamp ────────────────────────────────────────────────────
	/** Convert a Frappe UTC datetime string to a human-readable "N ago" label. */
	function _timeAgo(tsStr) {
		if (!tsStr) return "";
		// Frappe stores datetimes as UTC "YYYY-MM-DD HH:MM:SS"; parse as UTC.
		const ts = new Date(String(tsStr).replace(" ", "T") + "Z");
		if (isNaN(ts.getTime())) return tsStr;
		const diffMs  = Date.now() - ts.getTime();
		const diffMin = Math.floor(diffMs / 60000);
		const diffHr  = Math.floor(diffMs / 3600000);
		const diffDay = Math.floor(diffMs / 86400000);
		if (diffMin <  1)  return "just now";
		if (diffMin < 60)  return diffMin + "m ago";
		if (diffHr  < 24)  return diffHr  + "h ago";
		if (diffDay === 1) return "Yesterday";
		return diffDay + " days ago";
	}

	// ── Movement timeline — icon / colour per event_type (W3-01) ─────────────
	const _MOV_STYLE = {
		allocation:  { bg: "rgba(16,185,129,0.2)",  color: "#10B981" },
		reservation: { bg: "rgba(245,158,11,0.2)",  color: "#F59E0B" },
		release:     { bg: "rgba(194,198,211,0.2)", color: "#737783" },
		revision:    { bg: "rgba(0,52,111,0.2)",    color: "#00346f" },
	};

	function _buildMovRow(ev) {
		const style   = _MOV_STYLE[ev.event_type] || _MOV_STYLE.revision;
		const fadedCls = ev.event_type === "release" ? " kt-bgt-tl-item--faded" : "";
		const metaRef  = ev.ref ? ` &bull; REF: ${ev.ref}` : "";
		return `<div class="kt-bgt-tl-item${fadedCls}">
  <span class="kt-bgt-tl-dot" style="background:${style.bg}">
    <span class="material-symbols-outlined" style="color:${style.color}">${ev.icon || "schedule"}</span>
  </span>
  <div>
    <p class="kt-bgt-tl-title">${ev.title}</p>
    <p class="kt-bgt-tl-desc">${ev.desc}</p>
    <div class="kt-bgt-tl-meta">
      <span class="material-symbols-outlined">schedule</span>
      ${_timeAgo(ev.ts)}${metaRef}
    </div>
  </div>
</div>`;
	}

	function _populateTimeline(wrapper, movements) {
		const tl = wrapper.querySelector("[data-testid='kt-bgt-timeline']");
		if (!tl) return;
		if (!movements || !movements.length) {
			tl.innerHTML = `<div class="kt-bgt-tl-empty">No recent movements.</div>`;
			return;
		}
		tl.innerHTML = movements.map(_buildMovRow).join("");
	}

	// ── Health chip — maps canonical server-side health_status (W2-03) ─────────
	// Server computes: exhausted / reviewing / healthy (Approved/Active),
	//                  submitted / draft / rejected (workflow states).

	const _CHIP = {
		healthy:   { cls: "kt-bgt-chip--healthy",   lbl: "Healthy" },
		reviewing: { cls: "kt-bgt-chip--reviewing", lbl: "Reviewing" },
		exhausted: { cls: "kt-bgt-chip--critical",  lbl: "Exhausted" },
		submitted: { cls: "kt-bgt-chip--reviewing", lbl: "Reviewing" },
		draft:     { cls: "kt-bgt-chip--draft",     lbl: "Draft" },
		rejected:  { cls: "kt-bgt-chip--rejected",  lbl: "Rejected" },
	};

	function _deriveChip(bud) {
		return _CHIP[bud.health_status] || _CHIP.draft;
	}

	// ── Static shell HTML ─────────────────────────────────────────────────────
	function _html() {
		return `
<div class="kt-bgt-workbench" data-testid="kt-bgt-workbench">

  <!-- ── TOPBAR ──────────────────────────────────────────────────────────── -->
  <header class="kt-bgt-topbar" data-testid="kt-bgt-topbar">
    <div class="kt-bgt-topbar__left">
      <h1 class="kt-bgt-topbar__title">Budget Management</h1>
      <label class="kt-bgt-topbar__search">
        <span class="kt-bgt-topbar__search-icon material-symbols-outlined">search</span>
        <input type="text" placeholder="Search budgets, demands..." />
      </label>
    </div>
    <div class="kt-bgt-topbar__right">
      <button class="kt-bgt-topbar__icon-btn" type="button" aria-label="Notifications">
        <span class="material-symbols-outlined">notifications</span>
        <span class="kt-bgt-topbar__notif-dot"></span>
      </button>
      <button class="kt-bgt-topbar__icon-btn" type="button" aria-label="History">
        <span class="material-symbols-outlined">history</span>
      </button>
      <button class="kt-bgt-topbar__icon-btn" type="button" aria-label="Help">
        <span class="material-symbols-outlined">help</span>
      </button>
      <div class="kt-bgt-topbar__user">
        <div class="kt-bgt-topbar__user-text">
          <p class="kt-bgt-topbar__user-name" data-testid="kt-bgt-user-name">—</p>
          <p class="kt-bgt-topbar__user-role" data-testid="kt-bgt-user-role">—</p>
        </div>
        <div class="kt-bgt-topbar__avatar" data-testid="kt-bgt-user-avatar">—</div>
      </div>
    </div>
  </header>

  <!-- ── SCROLLABLE BODY ──────────────────────────────────────────────────── -->
  <div class="kt-bgt-body">
    <div class="kt-bgt-sections">

      <!-- ── PAGE HEADER / BREADCRUMB ──────────────────────────────────────── -->
      <div class="kt-bgt-page-hdr">
        <div>
          <nav class="kt-bgt-crumb">
            <span>Portfolio</span>
            <span class="kt-bgt-crumb-sep material-symbols-outlined">chevron_right</span>
            <span class="kt-bgt-crumb-active">Active Budgets</span>
          </nav>
          <h1 class="kt-bgt-page-title">Budget Hub</h1>
          <p class="kt-bgt-page-desc">Financial control layer for FY 2026/27. Manage envelopes, track reservations, and ensure strategic alignment across all procuring entities.</p>
        </div>
        <div class="kt-bgt-hdr-actions">
          <button class="kt-bgt-btn-ghost" type="button">
            <span class="material-symbols-outlined">download</span>
            Export Report
          </button>
          <button class="kt-bgt-btn-primary" type="button">
            <span class="material-symbols-outlined">add_box</span>
            Create Budget
          </button>
        </div>
      </div>

      <!-- ── KPI CARDS ─────────────────────────────────────────────────────── -->
      <div class="kt-bgt-kpis" data-testid="kt-bgt-kpis">

        <div class="kt-bgt-kpi-card" style="border-color:#E2E8F0" onmouseenter="this.style.borderColor='#00629d'" onmouseleave="this.style.borderColor='#E2E8F0'">
          <div class="kt-bgt-kpi-card__top">
            <span class="kt-bgt-kpi-icon" style="background:rgba(16,185,129,0.1)">
              <span class="material-symbols-outlined" style="color:#10B981">account_balance_wallet</span>
            </span>
          </div>
          <div>
            <p class="kt-bgt-kpi-label">Available Balance (KES)</p>
            <h3 class="kt-bgt-kpi-value kt-bgt-kpi--loading" data-testid="kt-bgt-kpi-available">—</h3>
          </div>
          <p class="kt-bgt-kpi-footer">Unallocated funding envelope</p>
        </div>

        <div class="kt-bgt-kpi-card" onmouseenter="this.style.borderColor='#F59E0B'" onmouseleave="this.style.borderColor='#E2E8F0'">
          <div class="kt-bgt-kpi-card__top">
            <span class="kt-bgt-kpi-icon" style="background:rgba(245,158,11,0.1)">
              <span class="material-symbols-outlined" style="color:#F59E0B">lock_clock</span>
            </span>
          </div>
          <div>
            <p class="kt-bgt-kpi-label">Total Reserved</p>
            <h3 class="kt-bgt-kpi-value kt-bgt-kpi--loading" data-testid="kt-bgt-kpi-reserved">—</h3>
          </div>
          <p class="kt-bgt-kpi-footer">Held for approved demands</p>
        </div>

        <div class="kt-bgt-kpi-card" onmouseenter="this.style.borderColor='#6366F1'" onmouseleave="this.style.borderColor='#E2E8F0'">
          <div class="kt-bgt-kpi-card__top">
            <span class="kt-bgt-kpi-icon" style="background:rgba(99,102,241,0.1)">
              <span class="material-symbols-outlined" style="color:#6366F1">verified</span>
            </span>
          </div>
          <div>
            <p class="kt-bgt-kpi-label">Total Committed</p>
            <h3 class="kt-bgt-kpi-value kt-bgt-kpi--loading" data-testid="kt-bgt-kpi-committed">—</h3>
          </div>
          <p class="kt-bgt-kpi-footer">Locked in active contracts</p>
        </div>

        <div class="kt-bgt-kpi-card" onmouseenter="this.style.borderColor='#00346f'" onmouseleave="this.style.borderColor='#E2E8F0'">
          <div class="kt-bgt-kpi-card__top">
            <span class="kt-bgt-kpi-icon" style="background:rgba(0,52,111,0.1)">
              <span class="material-symbols-outlined" style="color:#00346f">rate_review</span>
            </span>
            <span class="kt-bgt-kpi-pulse"></span>
          </div>
          <div>
            <p class="kt-bgt-kpi-label">Pending Approvals</p>
            <h3 class="kt-bgt-kpi-value kt-bgt-kpi--loading" data-testid="kt-bgt-kpi-pending">—</h3>
          </div>
          <p class="kt-bgt-kpi-footer">Requires executive signature</p>
        </div>

      </div>

      <!-- ── CRITICAL GUARDRAILS ────────────────────────────────────────────── -->
      <section data-testid="kt-bgt-guardrails-section">
        <div class="kt-bgt-guardrails__heading">
          <span class="material-symbols-outlined">warning</span>
          <h2>Critical Guardrails</h2>
        </div>
        <div class="kt-bgt-guardrails-grid" data-testid="kt-bgt-guardrails-grid">
          <div class="kt-bgt-guardrails-loading">
            <span class="material-symbols-outlined">pending</span> Checking guardrails…
          </div>
        </div>
      </section>

      <!-- ── ACTIVE BUDGETS + RECENT MOVEMENTS ─────────────────────────────── -->
      <div class="kt-bgt-main-grid">

        <!-- Active Budget Envelopes table -->
        <div>
          <div class="kt-bgt-section-hdr">
            <h2 class="kt-bgt-section-title">Active Budget Envelopes</h2>
            <div class="kt-bgt-filter-wrap" data-testid="kt-bgt-entity-filter-wrap" style="display:none">
              <span class="kt-bgt-filter-label">Filter by:</span>
              <select class="kt-bgt-filter-select" data-testid="kt-bgt-entity-filter">
                <option value="">All Entities</option>
              </select>
            </div>
          </div>
          <div class="kt-bgt-table-wrap">
            <table class="kt-bgt-table">
              <colgroup>
                <col style="width:25%"><!-- Budget Name -->
                <col style="width:27%"><!-- Allocation bar -->
                <col style="width:22%"><!-- Available (KES) -->
                <col style="width:16%"><!-- Status -->
                <col style="width:10%"><!-- Actions -->
              </colgroup>
              <thead>
                <tr>
                  <th>Budget Name</th>
                  <th>Obligation</th>
                  <th>Available (KES)</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody data-testid="kt-bgt-budget-tbody">
                <tr><td colspan="5" class="kt-bgt-table-loading">Loading budgets…</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Recent Movements -->
        <div class="kt-bgt-movements-panel">
          <div class="kt-bgt-section-hdr">
            <h2 class="kt-bgt-section-title">Recent Movements</h2>
            <button class="kt-bgt-view-all" type="button">View All</button>
          </div>
          <div class="kt-bgt-movements-card">
            <div class="kt-bgt-timeline" data-testid="kt-bgt-timeline">
              <div class="kt-bgt-tl-loading">
                <span class="material-symbols-outlined">pending</span> Loading movements…
              </div>
            </div>
          </div>

          <!-- Strategic Alignment Score -->
          <div class="kt-bgt-alignment-card">
            <div class="kt-bgt-alignment-card__content">
              <h4 class="kt-bgt-alignment-card__label">Strategic Alignment Score</h4>
              <div class="kt-bgt-alignment-card__score-row">
                <span class="kt-bgt-alignment-card__score kt-bgt-kpi--loading"
                      data-testid="kt-bgt-alignment-score">—</span>
                <span class="kt-bgt-alignment-card__badge"
                      data-testid="kt-bgt-alignment-badge"></span>
              </div>
              <p class="kt-bgt-alignment-card__sub"
                 data-testid="kt-bgt-alignment-sub">Checking alignment…</p>
            </div>
          </div>
        </div>

      </div>

      <!-- ── ANALYTICS ──────────────────────────────────────────────────────── -->
      <div class="kt-bgt-analytics-grid">

        <!-- Funding Source Distribution -->
        <div class="kt-bgt-analytics-card" data-testid="kt-bgt-funding-card">
          <div class="kt-bgt-analytics-card__hdr">
            <h3 class="kt-bgt-analytics-card__title">Funding Source Distribution</h3>
          </div>
          <div class="kt-bgt-donut-wrap" data-testid="kt-bgt-funding-donut-wrap">
            <div class="kt-bgt-donut-loading">Loading…</div>
          </div>
        </div>

        <!-- Consumption Velocity -->
        <div class="kt-bgt-analytics-card">
          <div class="kt-bgt-analytics-card__hdr">
            <h3 class="kt-bgt-analytics-card__title">Consumption Velocity</h3>
            <button class="kt-bgt-analytics-card__more" type="button">
              <span class="material-symbols-outlined">more_horiz</span>
            </button>
          </div>
          <div class="kt-bgt-bar-chart">
            <div class="kt-bgt-bar-chart__bars">
              <div class="kt-bgt-bar-chart__bar" style="height:40%;background:rgba(0,52,111,0.2)"></div>
              <div class="kt-bgt-bar-chart__bar" style="height:55%;background:rgba(0,52,111,0.3)"></div>
              <div class="kt-bgt-bar-chart__bar" style="height:45%;background:rgba(0,52,111,0.4)"></div>
              <div class="kt-bgt-bar-chart__bar" style="height:70%;background:rgba(0,52,111,0.5)"></div>
              <div class="kt-bgt-bar-chart__bar" style="height:65%;background:rgba(0,52,111,0.6)"></div>
              <div class="kt-bgt-bar-chart__bar" style="height:85%;background:rgba(0,52,111,0.8)"></div>
              <div class="kt-bgt-bar-chart__bar" style="height:95%;background:#00346f"></div>
            </div>
            <div class="kt-bgt-bar-chart__labels">
              <span>Jul</span><span>Aug</span><span>Sep</span>
              <span>Oct</span><span>Nov</span><span>Dec</span>
              <span>Jan</span>
            </div>
            <p class="kt-bgt-bar-chart__note">Spending velocity increased by 18% in Q3 due to infrastructure awards.</p>
          </div>
        </div>

      </div>

    </div>
  </div>
</div>`;
	}

	// ── DOM population ────────────────────────────────────────────────────────

	function _populateUser(wrapper) {
		const info = frappe.boot && frappe.boot.user_info &&
		             frappe.boot.user_info[frappe.session.user];
		const fullName = (info && info.fullname) || frappe.session.user || "User";
		const roleEl   = wrapper.querySelector("[data-testid='kt-bgt-user-role']");
		const nameEl   = wrapper.querySelector("[data-testid='kt-bgt-user-name']");
		const avatarEl = wrapper.querySelector("[data-testid='kt-bgt-user-avatar']");
		if (nameEl)   nameEl.textContent  = fullName;
		if (avatarEl) avatarEl.textContent = _initials(fullName);
		if (roleEl)   roleEl.textContent  = "Budget Officer";
	}

	function _populateKPIs(wrapper, portfolio) {
		const set = (testid, val) => {
			const el = wrapper.querySelector(`[data-testid='${testid}']`);
			if (el) {
				el.textContent = val;
				el.classList.remove("kt-bgt-kpi--loading");
			}
		};
		set("kt-bgt-kpi-available", _fmtFull(portfolio.available_sum));
		set("kt-bgt-kpi-reserved",  _fmtFull(portfolio.reserved_sum));
		// W1-02: committed is a Phase 2 field (contract commitments not yet wired);
		// show a neutral dash until convert_to_commitment flows are active in UI.
		set("kt-bgt-kpi-committed", "\u2013");
		set("kt-bgt-kpi-pending",   String(portfolio.pending_approval_count || 0));

		// W3-04: Strategic Alignment Score
		const pct = portfolio.alignment_score_pct;
		if (pct !== undefined && pct !== null) {
			const badge = pct >= 90 ? "Optimal"
			            : pct >= 70 ? "Good"
			            : pct >= 50 ? "Fair"
			            :             "Poor";
			const sub   = pct >= 90
			            ? "All active spending correlates with strategic objectives."
			            : pct >= 70
			            ? "Most active lines are linked to a strategic objective."
			            : pct >= 50
			            ? "Over half of active lines are strategically linked."
			            : "Many active lines are missing a sub-programme link.";
			set("kt-bgt-alignment-score", pct.toFixed(1) + "%");
			set("kt-bgt-alignment-badge", badge);
			set("kt-bgt-alignment-sub",   sub);

			const badgeEl = wrapper.querySelector("[data-testid='kt-bgt-alignment-badge']");
			if (badgeEl) {
				badgeEl.className = "kt-bgt-alignment-card__badge kt-bgt-alignment-badge--"
				                  + badge.toLowerCase();
			}
		}
	}

	function _buildBudgetRow(bud) {
		const chip = _deriveChip(bud);
		// W2-05: real obligation bar — committed_pct + reserved_pct dual segments
		const consPct = Math.min(100, Math.round(bud.consumption_pct || 0));
		const comPct  = Math.min(100, Math.round(bud.committed_pct   || 0));
		const resPct  = Math.min(100, Math.round(bud.reserved_pct    || 0));
		const hasOblig = comPct > 0 || resPct > 0;

		const primaryLbl = bud.budget_name || bud.name || "—";
		const subParts = [];
		if (bud.fiscal_year)          subParts.push(bud.fiscal_year);
		if (bud.strategic_plan_title) subParts.push(bud.strategic_plan_title);
		const subLbl = subParts.join(" \u00b7 ");

		const barLegend = hasOblig
			? `<div class="kt-bgt-bar-legend">
				<span><span class="kt-bgt-dot" style="background:#6366F1"></span>Committed</span>
				<span><span class="kt-bgt-dot" style="background:#F59E0B"></span>Reserved</span>
			   </div>`
			: `<div class="kt-bgt-bar-legend kt-bgt-bar-legend--empty">No obligations</div>`;

		return `<tr data-budget-name="${bud.name}">
  <td>
    <div class="kt-bgt-budget-name">${primaryLbl}</div>
    ${subLbl ? `<div class="kt-bgt-budget-sub">${subLbl}</div>` : ""}
  </td>
  <td>
    <div class="kt-bgt-bar-row">
      <span class="kt-bgt-bar-pct">${consPct}%</span>
      <div class="kt-bgt-bar-track">
        <div class="kt-bgt-bar-committed" style="width:${comPct}%"></div>
        <div class="kt-bgt-bar-reserved"  style="width:${resPct}%"></div>
      </div>
    </div>
    ${barLegend}
  </td>
  <td><span class="kt-bgt-avail-value">${_fmtFull(bud.available_amount)}</span></td>
  <td><span class="kt-bgt-chip ${chip.cls}">${chip.lbl}</span></td>
  <td>
    <button class="kt-bgt-table-action" type="button" title="Open ${bud.budget_name || ""}">
      <span class="material-symbols-outlined">edit_square</span>
    </button>
  </td>
</tr>`;
	}

	function _populateTable(wrapper, budgets) {
		const tbody = wrapper.querySelector("[data-testid='kt-bgt-budget-tbody']");
		if (!tbody) return;
		if (!budgets || !budgets.length) {
			tbody.innerHTML = `<tr><td colspan="5" class="kt-bgt-table-empty">No budgets found.</td></tr>`;
			return;
		}
		tbody.innerHTML = budgets.map(_buildBudgetRow).join("");

		// Entity filter dropdown — show only if procuring_entity data exists
		const filterWrap = wrapper.querySelector("[data-testid='kt-bgt-entity-filter-wrap']");
		const select     = wrapper.querySelector("[data-testid='kt-bgt-entity-filter']");
		if (!filterWrap || !select) return;

		const seen = new Set();
		budgets.forEach(b => {
			if (b.procuring_entity && !seen.has(b.procuring_entity)) {
				seen.add(b.procuring_entity);
				const opt = document.createElement("option");
				// W2-05: use entity_code as value for a stable business key
				opt.value = b.procuring_entity_code || b.procuring_entity;
				opt.textContent = b.procuring_entity_name || b.procuring_entity;
				select.appendChild(opt);
			}
		});

		if (!seen.size) {
			filterWrap.style.display = "none";
			return;
		}

		filterWrap.style.display = "";
		select.addEventListener("change", () => {
			const val = select.value;
			tbody.querySelectorAll("tr[data-budget-name]").forEach(tr => {
				if (!val) { tr.style.display = ""; return; }
				const match = budgets.find(b => b.name === tr.dataset.budgetName);
				// Match on entity_code (W2-05); fall back to internal name for
				// budgets where entity_code was not populated
				tr.style.display = (match && (
					(match.procuring_entity_code && match.procuring_entity_code === val) ||
					match.procuring_entity === val
				)) ? "" : "none";
			});
		});
	}

	function _populateError(wrapper, msg) {
		const tbody = wrapper.querySelector("[data-testid='kt-bgt-budget-tbody']");
		if (tbody) {
			tbody.innerHTML = `<tr><td colspan="5" class="kt-bgt-table-error">
				<span class="material-symbols-outlined">error</span> Failed to load budget data: ${msg}
			</td></tr>`;
		}
		["kt-bgt-kpi-available","kt-bgt-kpi-reserved","kt-bgt-kpi-committed","kt-bgt-kpi-pending"]
			.forEach(id => {
				const el = wrapper.querySelector(`[data-testid='${id}']`);
				if (el) { el.textContent = "—"; el.classList.remove("kt-bgt-kpi--loading"); }
			});
	}

	// ── Critical Guardrails (W3-02) ──────────────────────────────────────────

	const _GUARDRAIL_STYLE = {
		error:   { bg: "rgba(255,218,214,1)",  color: "#93000a", actColor: "#93000a" },
		warning: { bg: "rgba(245,158,11,0.2)", color: "#F59E0B", actColor: "#00346f" },
	};

	const _GUARDRAIL_ICON = {
		low_balance:       "priority_high",
		unlinked_strategy: "link_off",
		expiry:            "event_busy",
	};

	function _buildGuardrailCard(g) {
		const style    = _GUARDRAIL_STYLE[g.severity] || _GUARDRAIL_STYLE.warning;
		const icon     = _GUARDRAIL_ICON[g.check_type] || "warning";
		const modCls   = `kt-bgt-guardrail--${g.severity}`;
		const titleClr = g.severity === "error" ? style.color : "#191c1e";
		return `<div class="kt-bgt-guardrail ${modCls}">
  <div class="kt-bgt-guardrail__icon-wrap" style="background:${style.bg}">
    <span class="material-symbols-outlined" style="color:${style.color}">${icon}</span>
  </div>
  <div>
    <h4 class="kt-bgt-guardrail__title" style="color:${titleClr}">${g.title}</h4>
    <p class="kt-bgt-guardrail__desc">${g.description}</p>
  </div>
  <button class="kt-bgt-guardrail__action" style="color:${style.actColor}"
          type="button">${g.action_label}</button>
</div>`;
	}

	function _populateGuardrails(wrapper, guardrails) {
		const section = wrapper.querySelector("[data-testid='kt-bgt-guardrails-section']");
		const grid    = wrapper.querySelector("[data-testid='kt-bgt-guardrails-grid']");
		if (!section || !grid) return;

		if (!guardrails || !guardrails.length) {
			// Hide entire panel when no active guardrails
			section.style.display = "none";
			return;
		}

		section.style.display = "";
		grid.innerHTML = guardrails.map(_buildGuardrailCard).join("");
	}

	// ── Funding Source Distribution (W3-03) ──────────────────────────────────

	/** Source-type → colour palette. */
	const _FUND_COLORS = {
		"Exchequer":    "#00346f",
		"Donor":        "#00629d",
		"Grant":        "#26364b",
		"Loan":         "#6366F1",
		"Own Revenue":  "#F59E0B",
		"Other":        "#737783",
		"Unclassified": "#c2c6d3",
	};

	/** Return a colour for a source type, cycling through a fallback palette. */
	function _fundColor(sourceType, idx) {
		if (_FUND_COLORS[sourceType]) return _FUND_COLORS[sourceType];
		const fallback = ["#00629d","#26364b","#6366F1","#F59E0B","#737783","#c2c6d3"];
		return fallback[idx % fallback.length];
	}

	/** Compact number formatter: 1 500 000 → "1.5M", 500 000 → "500K". */
	function _compactKES(n) {
		if (n >= 1_000_000_000) return (n / 1_000_000_000).toFixed(1).replace(/\.0$/, "") + "B";
		if (n >= 1_000_000)     return (n / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M";
		if (n >= 1_000)         return (n / 1_000).toFixed(0) + "K";
		return n.toLocaleString();
	}

	/**
	 * Build SVG donut from an array of segments.
	 * r = 15.915 → circumference ≈ 100 so pct values map directly to dash lengths.
	 * The SVG element has CSS `transform: rotate(-90deg)` which positions the start
	 * at 12 o'clock, so dashOffset accumulates negatively from 0.
	 */
	function _buildDonutSVG(segments) {
		const R = 15.915;
		let offset = 0;
		const circles = segments.map((s, i) => {
			const color = _fundColor(s.source_type, i);
			const pct   = s.pct;
			const el = `<circle cx="18" cy="18" r="${R}" fill="transparent"
  stroke="${color}" stroke-width="3"
  stroke-dasharray="${pct} ${100 - pct}"
  stroke-dashoffset="${-offset}"/>`;
			offset += pct;
			return el;
		});
		return `<svg viewBox="0 0 36 36" aria-hidden="true">
  <circle cx="18" cy="18" r="${R}" fill="transparent" stroke="#e0e3e5" stroke-width="3"/>
  ${circles.join("\n  ")}
</svg>`;
	}

	/** Build legend rows from segments. */
	function _buildDonutLegend(segments) {
		return segments.map((s, i) => {
			const color = _fundColor(s.source_type, i);
			return `<div class="kt-bgt-legend-row">
  <div class="kt-bgt-legend-row__left">
    <span class="kt-bgt-dot" style="background:${color}"></span>${s.source_type}
  </div>
  <span class="kt-bgt-legend-row__val">${s.pct}%</span>
</div>`;
		}).join("");
	}

	/** Replace the donut-wrap loading state with live SVG + legend. */
	function _populateFundingDonut(wrapper, data) {
		const wrap = wrapper.querySelector("[data-testid='kt-bgt-funding-donut-wrap']");
		if (!wrap) return;

		const { segments = [], total = 0 } = data;

		if (!segments.length) {
			wrap.innerHTML = `<p class="kt-bgt-donut-empty">No active budget lines.</p>`;
			return;
		}

		wrap.innerHTML = `
<div class="kt-bgt-donut" data-testid="kt-bgt-funding-donut">
  ${_buildDonutSVG(segments)}
  <div class="kt-bgt-donut__center">
    <span class="kt-bgt-donut__total-label">${_compactKES(total)}</span>
    <span class="kt-bgt-donut__total-sub">KES total</span>
  </div>
</div>
<div class="kt-bgt-donut-legend" data-testid="kt-bgt-funding-legend">
  ${_buildDonutLegend(segments)}
</div>`;
	}

	// ── Data loaders ──────────────────────────────────────────────────────────

	function _loadData(wrapper) {
		frappe.call({
			method: "kentender_budget.api.landing.get_budget_landing_data",
			freeze: false,
			callback: function (r) {
				if (r && r.message) {
					const data = r.message;
					_populateKPIs(wrapper, data.portfolio || {});
					_populateTable(wrapper, data.budgets || []);
				} else {
					_populateError(wrapper, "Empty response from server.");
				}
			},
			error: function (err) {
				const msg = (err && err.message) ? err.message : "Server error.";
				_populateError(wrapper, msg);
			},
		});
	}

	/** W3-01: Load recent budget movements for the timeline panel. */
	function _loadMovements(wrapper) {
		frappe.call({
			method: "kentender_budget.api.movements.get_budget_movements",
			args: { limit: 10 },
			freeze: false,
			callback: function (r) {
				if (r && r.message) {
					_populateTimeline(wrapper, r.message.movements || []);
				}
			},
		});
	}

	/** W3-02: Load critical guardrail checks; hides panel when none active. */
	function _loadGuardrails(wrapper) {
		frappe.call({
			method: "kentender_budget.api.guardrails.compute_budget_guardrails",
			freeze: false,
			callback: function (r) {
				if (r && r.message) {
					_populateGuardrails(wrapper, r.message.guardrails || []);
				}
			},
		});
	}

	/** W3-03: Load funding source distribution; renders live SVG donut. */
	function _loadFundingSources(wrapper) {
		frappe.call({
			method: "kentender_budget.api.funding_sources.get_funding_source_distribution",
			freeze: false,
			callback: function (r) {
				if (r && r.message) {
					_populateFundingDonut(wrapper, r.message);
				}
			},
		});
	}

	// ── Mount ─────────────────────────────────────────────────────────────────
	// wrapper is the raw #page-budget-hub div (page_js page)
	function _mount(wrapper) {
		_ensureFonts();
		if (!wrapper) return;
		if (wrapper.querySelector(".kt-bgt-workbench")) return; // already mounted
		wrapper.innerHTML = _html();
	}

	// ── Frappe page registration ──────────────────────────────────────────────
	frappe.pages["budget-hub"].on_page_load = function (wrapper) {
		_mount(wrapper);
	};

	frappe.pages["budget-hub"].on_page_show = function (wrapper) {
		document.body.classList.add("kt-bgt-shell");
		if (frappe.app && frappe.app.sidebar) {
			frappe.app.sidebar.setup("Budget Management");
		}
		_mount(wrapper);
		_populateUser(wrapper);
		_loadData(wrapper);
		_loadMovements(wrapper);
		_loadGuardrails(wrapper);
		_loadFundingSources(wrapper);
	};

	frappe.pages["budget-hub"].on_page_hide = function () {
		document.body.classList.remove("kt-bgt-shell");
	};
})();
