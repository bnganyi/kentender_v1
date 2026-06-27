/* global frappe */
// ── Budget Hub page — static, pixel-faithful to code.html ──────────────────
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

	// ── Static HTML — exact faithful translation of code.html ────────────────
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
          <p class="kt-bgt-topbar__user-name">James Mwangi</p>
          <p class="kt-bgt-topbar__user-role">Procurement Lead</p>
        </div>
        <div class="kt-bgt-topbar__avatar">JM</div>
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
      <div class="kt-bgt-kpis">

        <div class="kt-bgt-kpi-card" style="border-color:#E2E8F0" onmouseenter="this.style.borderColor='#00629d'" onmouseleave="this.style.borderColor='#E2E8F0'">
          <div class="kt-bgt-kpi-card__top">
            <span class="kt-bgt-kpi-icon" style="background:rgba(16,185,129,0.1)">
              <span class="material-symbols-outlined" style="color:#10B981">account_balance_wallet</span>
            </span>
            <span class="kt-bgt-kpi-badge" style="background:rgba(16,185,129,0.1);color:#10B981">+12.5%</span>
          </div>
          <div>
            <p class="kt-bgt-kpi-label">Available Balance (KES)</p>
            <h3 class="kt-bgt-kpi-value">4,120,450,000</h3>
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
            <h3 class="kt-bgt-kpi-value">842,100,500</h3>
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
            <h3 class="kt-bgt-kpi-value">2,250,900,000</h3>
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
            <h3 class="kt-bgt-kpi-value">14</h3>
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
            <div class="kt-bgt-filter-wrap">
              <span class="kt-bgt-filter-label">Filter by:</span>
              <select class="kt-bgt-filter-select">
                <option>All Entities</option>
                <option>Health</option>
                <option>Education</option>
              </select>
            </div>
          </div>
          <div class="kt-bgt-table-wrap">
            <table class="kt-bgt-table">
              <thead>
                <tr>
                  <th>Entity / Budget Name</th>
                  <th>Consumption</th>
                  <th>Available (KES)</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <div class="kt-bgt-budget-name">Ministry of Health FY 2026/27</div>
                    <div class="kt-bgt-budget-sub">Primary: Health Infrastructure Renovation</div>
                  </td>
                  <td style="width:192px">
                    <div class="kt-bgt-bar-row">
                      <span class="kt-bgt-bar-pct">68%</span>
                      <div class="kt-bgt-bar-track">
                        <div class="kt-bgt-bar-committed" style="width:45%"></div>
                        <div class="kt-bgt-bar-reserved"  style="width:23%"></div>
                      </div>
                    </div>
                    <div class="kt-bgt-bar-legend">
                      <span><span class="kt-bgt-dot" style="background:#6366F1"></span>Commit</span>
                      <span><span class="kt-bgt-dot" style="background:#F59E0B"></span>Reserve</span>
                    </div>
                  </td>
                  <td><span class="kt-bgt-avail-value">1,240.5M</span></td>
                  <td><span class="kt-bgt-chip kt-bgt-chip--healthy">Healthy</span></td>
                  <td>
                    <button class="kt-bgt-table-action" type="button">
                      <span class="material-symbols-outlined">edit_square</span>
                    </button>
                  </td>
                </tr>
                <tr>
                  <td>
                    <div class="kt-bgt-budget-name">Dept. of Education (Capitation)</div>
                    <div class="kt-bgt-budget-sub">Strategy: Digital Learning Initiative</div>
                  </td>
                  <td>
                    <div class="kt-bgt-bar-row">
                      <span class="kt-bgt-bar-pct">92%</span>
                      <div class="kt-bgt-bar-track">
                        <div class="kt-bgt-bar-committed" style="width:80%"></div>
                        <div class="kt-bgt-bar-reserved"  style="width:12%"></div>
                      </div>
                    </div>
                    <div class="kt-bgt-bar-legend">
                      <span><span class="kt-bgt-dot" style="background:#6366F1"></span>Commit</span>
                      <span><span class="kt-bgt-dot" style="background:#F59E0B"></span>Reserve</span>
                    </div>
                  </td>
                  <td><span class="kt-bgt-avail-value">45.2M</span></td>
                  <td><span class="kt-bgt-chip kt-bgt-chip--reviewing">Reviewing</span></td>
                  <td>
                    <button class="kt-bgt-table-action" type="button">
                      <span class="material-symbols-outlined">edit_square</span>
                    </button>
                  </td>
                </tr>
                <tr>
                  <td>
                    <div class="kt-bgt-budget-name">State Dept for Transport</div>
                    <div class="kt-bgt-budget-sub">Strategy: Rural Access Roads</div>
                  </td>
                  <td>
                    <div class="kt-bgt-bar-row">
                      <span class="kt-bgt-bar-pct">15%</span>
                      <div class="kt-bgt-bar-track">
                        <div class="kt-bgt-bar-committed" style="width:10%"></div>
                        <div class="kt-bgt-bar-reserved"  style="width:5%"></div>
                      </div>
                    </div>
                  </td>
                  <td><span class="kt-bgt-avail-value">2,850.0M</span></td>
                  <td><span class="kt-bgt-chip kt-bgt-chip--healthy">Healthy</span></td>
                  <td>
                    <button class="kt-bgt-table-action" type="button">
                      <span class="material-symbols-outlined">edit_square</span>
                    </button>
                  </td>
                </tr>
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

	// ── Mount the page ────────────────────────────────────────────────────────
	// wrapper is the raw #page-budget-hub div (page_js page — no layout-main-section)
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
		// Apply shell class so CSS hides Frappe's page-head
		document.body.classList.add("kt-bgt-shell");

		// Re-establish the Budget Management sidebar on every show
		if (frappe.app && frappe.app.sidebar) {
			frappe.app.sidebar.setup("Budget Management");
		}

		// Ensure content is mounted (in case on_page_load missed the DOM)
		_mount(wrapper);
	};

	frappe.pages["budget-hub"].on_page_hide = function () {
		document.body.classList.remove("kt-bgt-shell");
	};
})();
