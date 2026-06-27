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

	// ── Health chip (W1-03 client-side derivation) ───────────────────────────
	// Approved/Active: available/total ratio.  Other statuses use doc status.

	function _deriveChip(bud) {
		const status = bud.status || "Draft";
		if (status === "Draft")     return { cls: "kt-bgt-chip--draft",     lbl: "Draft" };
		if (status === "Submitted") return { cls: "kt-bgt-chip--reviewing", lbl: "Reviewing" };
		if (status === "Rejected")  return { cls: "kt-bgt-chip--rejected",  lbl: "Rejected" };
		// Approved / Active
		const total = bud.total_budget_amount || 0;
		const avail = bud.available_amount;
		if (avail === null || avail === undefined || total <= 0) {
			return { cls: "kt-bgt-chip--healthy", lbl: "Healthy" };
		}
		const ratio = avail / total;
		if (ratio <= 0)   return { cls: "kt-bgt-chip--critical",  lbl: "Exhausted" };
		if (ratio < 0.10) return { cls: "kt-bgt-chip--reviewing", lbl: "Reviewing" };
		return { cls: "kt-bgt-chip--healthy", lbl: "Healthy" };
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
      <section>
        <div class="kt-bgt-guardrails__heading">
          <span class="material-symbols-outlined">warning</span>
          <h2>Critical Guardrails</h2>
        </div>
        <div class="kt-bgt-guardrails-grid">
          <div class="kt-bgt-guardrail kt-bgt-guardrail--error">
            <div class="kt-bgt-guardrail__icon-wrap" style="background:rgba(255,218,214,1)">
              <span class="material-symbols-outlined" style="color:#93000a">priority_high</span>
            </div>
            <div>
              <h4 class="kt-bgt-guardrail__title" style="color:#93000a">Low Balance: Infrastructure Expansion</h4>
              <p class="kt-bgt-guardrail__desc">Available funds below 15% threshold for Category A works. Planned tender release blocked.</p>
            </div>
            <button class="kt-bgt-guardrail__action" style="color:#93000a">Review</button>
          </div>
          <div class="kt-bgt-guardrail kt-bgt-guardrail--warning">
            <div class="kt-bgt-guardrail__icon-wrap" style="background:rgba(245,158,11,0.2)">
              <span class="material-symbols-outlined" style="color:#F59E0B">link_off</span>
            </div>
            <div>
              <h4 class="kt-bgt-guardrail__title" style="color:#191c1e">Funding Exception: Unlinked Strategy</h4>
              <p class="kt-bgt-guardrail__desc">4 Budget lines lack mapping to Strategic Pillar 3. Audit compliance risk detected.</p>
            </div>
            <button class="kt-bgt-guardrail__action" style="color:#00346f">Fix Link</button>
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
              <thead>
                <tr>
                  <th>Budget Name</th>
                  <th>Allocation</th>
                  <th>Available (KES)</th>
                  <th>Status</th>
                  <th>Actions</th>
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
            <div class="kt-bgt-timeline">

              <div class="kt-bgt-tl-item">
                <span class="kt-bgt-tl-dot" style="background:rgba(16,185,129,0.2)">
                  <span class="material-symbols-outlined" style="color:#10B981">add</span>
                </span>
                <div>
                  <p class="kt-bgt-tl-title">Budget Allocation</p>
                  <p class="kt-bgt-tl-desc">KES 50,000,000 allocated to MoH Lab Equipping Programme.</p>
                  <div class="kt-bgt-tl-meta">
                    <span class="material-symbols-outlined">schedule</span>
                    2 hours ago &bull; REF: BK-9021
                  </div>
                </div>
              </div>

              <div class="kt-bgt-tl-item">
                <span class="kt-bgt-tl-dot" style="background:rgba(245,158,11,0.2)">
                  <span class="material-symbols-outlined" style="color:#F59E0B">lock</span>
                </span>
                <div>
                  <p class="kt-bgt-tl-title">Funds Reserved</p>
                  <p class="kt-bgt-tl-desc">KES 12,400,000 held for Tender #2026/045 (School Books).</p>
                  <div class="kt-bgt-tl-meta">
                    <span class="material-symbols-outlined">schedule</span>
                    5 hours ago &bull; REF: RS-4410
                  </div>
                </div>
              </div>

              <div class="kt-bgt-tl-item">
                <span class="kt-bgt-tl-dot" style="background:rgba(0,52,111,0.2)">
                  <span class="material-symbols-outlined" style="color:#00346f">task_alt</span>
                </span>
                <div>
                  <p class="kt-bgt-tl-title">Revision Approved</p>
                  <p class="kt-bgt-tl-desc">Transport Dept. budget version 2.4 activated by PS Finance.</p>
                  <div class="kt-bgt-tl-meta">
                    <span class="material-symbols-outlined">schedule</span>
                    Yesterday &bull; REF: RV-0112
                  </div>
                </div>
              </div>

              <div class="kt-bgt-tl-item kt-bgt-tl-item--faded">
                <span class="kt-bgt-tl-dot" style="background:rgba(194,198,211,0.2)">
                  <span class="material-symbols-outlined" style="color:#737783">undo</span>
                </span>
                <div>
                  <p class="kt-bgt-tl-title">Reservation Released</p>
                  <p class="kt-bgt-tl-desc">KES 2,000,000 surplus returned from cancelled demand DM-44.</p>
                  <div class="kt-bgt-tl-meta">
                    <span class="material-symbols-outlined">schedule</span>
                    2 days ago &bull; REF: RL-8821
                  </div>
                </div>
              </div>

            </div>
          </div>

          <!-- Strategic Alignment Score -->
          <div class="kt-bgt-alignment-card">
            <div class="kt-bgt-alignment-card__content">
              <h4 class="kt-bgt-alignment-card__label">Strategic Alignment Score</h4>
              <div class="kt-bgt-alignment-card__score-row">
                <span class="kt-bgt-alignment-card__score">94%</span>
                <span class="kt-bgt-alignment-card__badge">Optimal</span>
              </div>
              <p class="kt-bgt-alignment-card__sub">All active spending correlates with Vision 2030 objectives.</p>
            </div>
          </div>
        </div>

      </div>

      <!-- ── ANALYTICS ──────────────────────────────────────────────────────── -->
      <div class="kt-bgt-analytics-grid">

        <!-- Funding Source Distribution -->
        <div class="kt-bgt-analytics-card">
          <div class="kt-bgt-analytics-card__hdr">
            <h3 class="kt-bgt-analytics-card__title">Funding Source Distribution</h3>
            <button class="kt-bgt-analytics-card__more" type="button">
              <span class="material-symbols-outlined">more_horiz</span>
            </button>
          </div>
          <div class="kt-bgt-donut-wrap">
            <div class="kt-bgt-donut">
              <svg viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#e0e3e5" stroke-width="3"/>
                <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#00346f" stroke-width="3" stroke-dasharray="70 30" stroke-dashoffset="0"/>
                <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#00629d" stroke-width="3" stroke-dasharray="20 80" stroke-dashoffset="-70"/>
                <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#F59E0B" stroke-width="3" stroke-dasharray="10 90" stroke-dashoffset="-90"/>
              </svg>
              <div class="kt-bgt-donut__center">
                <span class="kt-bgt-donut__total-label">Total</span>
                <span class="kt-bgt-donut__total-sub">FY 26/27</span>
              </div>
            </div>
            <div class="kt-bgt-donut-legend">
              <div class="kt-bgt-legend-row">
                <div class="kt-bgt-legend-row__left">
                  <span class="kt-bgt-dot" style="background:#00346f"></span>Exchequer
                </div>
                <span class="kt-bgt-legend-row__val">70%</span>
              </div>
              <div class="kt-bgt-legend-row">
                <div class="kt-bgt-legend-row__left">
                  <span class="kt-bgt-dot" style="background:#00629d"></span>External Grants
                </div>
                <span class="kt-bgt-legend-row__val">20%</span>
              </div>
              <div class="kt-bgt-legend-row">
                <div class="kt-bgt-legend-row__left">
                  <span class="kt-bgt-dot" style="background:#F59E0B"></span>Internal Revenue
                </div>
                <span class="kt-bgt-legend-row__val">10%</span>
              </div>
            </div>
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
	}

	function _buildBudgetRow(bud) {
		const chip    = _deriveChip(bud);
		// W1-03: allocation_pct = allocated ÷ total, label "Allocated"
		const allocPct = Math.min(100, Math.round(bud.allocation_pct || 0));
		// Primary line: budget_name; secondary: fiscal_year + strategic plan
		const primaryLbl = bud.budget_name || bud.name || "—";
		const subParts = [];
		if (bud.fiscal_year)          subParts.push(bud.fiscal_year);
		if (bud.strategic_plan_title) subParts.push(bud.strategic_plan_title);
		const subLbl = subParts.join(" \u00b7 ");

		return `<tr data-budget-name="${bud.name}">
  <td>
    <div class="kt-bgt-budget-name">${primaryLbl}</div>
    ${subLbl ? `<div class="kt-bgt-budget-sub">${subLbl}</div>` : ""}
  </td>
  <td style="width:192px">
    <div class="kt-bgt-bar-row">
      <span class="kt-bgt-bar-pct">${allocPct}%</span>
      <div class="kt-bgt-bar-track">
        <div class="kt-bgt-bar-allocated" style="width:${allocPct}%"></div>
      </div>
    </div>
    <div class="kt-bgt-bar-legend">
      <span><span class="kt-bgt-dot" style="background:#00346f"></span>Allocated</span>
    </div>
  </td>
  <td><span class="kt-bgt-avail-value">${_fmtKES(bud.available_amount)}</span></td>
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
				opt.value = b.procuring_entity;
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
				tr.style.display = (match && match.procuring_entity === val) ? "" : "none";
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

	// ── Data loader ───────────────────────────────────────────────────────────

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
	};

	frappe.pages["budget-hub"].on_page_hide = function () {
		document.body.classList.remove("kt-bgt-shell");
	};
})();
