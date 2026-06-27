/* global frappe */
// ── Budget Hub page — loaded via page_js on budget-builder route ──────────
(function () {
	"use strict";

	// ── Font injection (Manrope + JetBrains Mono) ────────────────────────────
	if (!document.getElementById("kt-bgt-fonts")) {
		const link = document.createElement("link");
		link.id = "kt-bgt-fonts";
		link.rel = "stylesheet";
		link.href =
			"https://fonts.googleapis.com/css2?family=Manrope:wght@600;700;800&family=JetBrains+Mono:wght@500&display=swap";
		document.head.appendChild(link);
	}

	// ────────────────────────────────────────────────────────────────────────
	//  BudgetHub class
	// ────────────────────────────────────────────────────────────────────────
	class BudgetHub {
		constructor(wrapper) {
			this.wrapper = wrapper;
			this.page    = wrapper.page;
			this.$body   = $(wrapper).find(".layout-main-section");
			this._data   = null;
		}

		// ── Public ────────────────────────────────────────────────────────
		init() {
			this._setup_page_actions();
			this._render_shell();
			this._load_data();
		}

		// ── Page header actions ───────────────────────────────────────────
		_setup_page_actions() {
			if (!this.page) return;
			this.page.set_title("Budget Hub");
		}

		// ── Static shell ──────────────────────────────────────────────────
		_render_shell() {
			this.$body.html(`
<div class="kt-bgt" id="kt-bgt-root">

  <!-- ── Page header ──────────────────────────────────────────────────── -->
  <div class="kt-bgt-page-hdr">
    <div>
      <div class="kt-bgt-crumb">
        <span>Portfolio</span>
        <span class="material-symbols-outlined kt-bgt-crumb-sep" style="font-size:13px">chevron_right</span>
        <span class="kt-bgt-crumb-cur">Active Budgets</span>
      </div>
      <h1 class="kt-bgt-title kt-bgt-headline">Budget Hub</h1>
      <p class="kt-bgt-subtitle">Financial control layer for FY 2026/27. Manage envelopes, track reservations, and ensure strategic alignment across all procuring entities.</p>
    </div>
    <div class="kt-bgt-hdr-actions">
      <button class="kt-bgt-btn-outline" id="kt-bgt-export">
        <span class="material-symbols-outlined">download</span> Export Report
      </button>
      <button class="kt-bgt-btn-primary" id="kt-bgt-create">
        <span class="material-symbols-outlined">add_box</span> Create Budget
      </button>
    </div>
  </div>

  <!-- ── KPI bento ─────────────────────────────────────────────────────── -->
  <div class="kt-bgt-kpis">
    <div class="kt-bgt-kpi kt-bgt-kpi--available">
      <div class="kt-bgt-kpi-head">
        <span class="kt-bgt-kpi-icon kt-bgt-kpi-icon--available">
          <span class="material-symbols-outlined">account_balance_wallet</span>
        </span>
        <span class="kt-bgt-kpi-badge" id="kt-bgt-kpi-avail-badge" style="display:none">+0%</span>
      </div>
      <div class="kt-bgt-kpi-body">
        <p class="kt-bgt-kpi-label-text">Available Balance (KES)</p>
        <p class="kt-bgt-kpi-val kt-bgt-mono" id="kt-bgt-kpi-available">—</p>
      </div>
      <p class="kt-bgt-kpi-foot">Unallocated funding envelope</p>
    </div>

    <div class="kt-bgt-kpi kt-bgt-kpi--reserved">
      <div class="kt-bgt-kpi-head">
        <span class="kt-bgt-kpi-icon kt-bgt-kpi-icon--reserved">
          <span class="material-symbols-outlined">lock_clock</span>
        </span>
      </div>
      <div class="kt-bgt-kpi-body">
        <p class="kt-bgt-kpi-label-text">Total Reserved</p>
        <p class="kt-bgt-kpi-val kt-bgt-mono" id="kt-bgt-kpi-reserved">—</p>
      </div>
      <p class="kt-bgt-kpi-foot">Held for approved demands</p>
    </div>

    <div class="kt-bgt-kpi kt-bgt-kpi--committed">
      <div class="kt-bgt-kpi-head">
        <span class="kt-bgt-kpi-icon kt-bgt-kpi-icon--committed">
          <span class="material-symbols-outlined">verified</span>
        </span>
      </div>
      <div class="kt-bgt-kpi-body">
        <p class="kt-bgt-kpi-label-text">Total Committed</p>
        <p class="kt-bgt-kpi-val kt-bgt-mono" id="kt-bgt-kpi-committed">—</p>
      </div>
      <p class="kt-bgt-kpi-foot">Locked in active contracts</p>
    </div>

    <div class="kt-bgt-kpi kt-bgt-kpi--pending">
      <div class="kt-bgt-kpi-head">
        <span class="kt-bgt-kpi-icon kt-bgt-kpi-icon--pending">
          <span class="material-symbols-outlined">rate_review</span>
        </span>
        <span class="kt-bgt-kpi-pulse" id="kt-bgt-pulse" style="display:none"></span>
      </div>
      <div class="kt-bgt-kpi-body">
        <p class="kt-bgt-kpi-label-text">Pending Approvals</p>
        <p class="kt-bgt-kpi-val kt-bgt-mono" id="kt-bgt-kpi-pending">—</p>
      </div>
      <p class="kt-bgt-kpi-foot">Requires executive signature</p>
    </div>
  </div>

  <!-- ── Critical Guardrails ───────────────────────────────────────────── -->
  <section class="kt-bgt-guardrails">
    <div class="kt-bgt-guardrails-hdr">
      <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">warning</span>
      <h2>Critical Guardrails</h2>
    </div>
    <div class="kt-bgt-guardrails-grid">
      <div class="kt-bgt-guard-card">
        <div class="kt-bgt-guard-icon kt-bgt-guard-icon--err">
          <span class="material-symbols-outlined">priority_high</span>
        </div>
        <div class="kt-bgt-guard-content">
          <p class="kt-bgt-guard-title">Low Balance: Infrastructure Expansion</p>
          <p class="kt-bgt-guard-desc">Available funds below 15% threshold for Category A works. Planned tender release blocked.</p>
        </div>
        <button class="kt-bgt-guard-action">Review</button>
      </div>
      <div class="kt-bgt-guard-card kt-bgt-guard-card--warn">
        <div class="kt-bgt-guard-icon kt-bgt-guard-icon--warn">
          <span class="material-symbols-outlined">link_off</span>
        </div>
        <div class="kt-bgt-guard-content">
          <p class="kt-bgt-guard-title">Funding Exception: Unlinked Strategy</p>
          <p class="kt-bgt-guard-desc">4 Budget lines lack mapping to Strategic Pillar 3. Audit compliance risk detected.</p>
        </div>
        <button class="kt-bgt-guard-action">Fix Link</button>
      </div>
    </div>
  </section>

  <!-- ── Main 2-col grid ───────────────────────────────────────────────── -->
  <div class="kt-bgt-main-grid">

    <!-- Left: Budget Envelopes -->
    <div>
      <div class="kt-bgt-envelopes-hdr">
        <h2>Active Budget Envelopes</h2>
        <div class="kt-bgt-filter">
          <span>Filter by:</span>
          <select id="kt-bgt-filter-entity">
            <option value="">All Entities</option>
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
          <tbody id="kt-bgt-table-body">
            ${_skeletonRows(4)}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Right: Movements + Alignment -->
    <div>
      <div class="kt-bgt-movements-hdr">
        <h2>Recent Movements</h2>
        <button id="kt-bgt-view-all">View All</button>
      </div>
      <div class="kt-bgt-timeline-card">
        <div class="kt-bgt-timeline" id="kt-bgt-timeline">
          <div class="kt-bgt-loading"><span class="material-symbols-outlined" style="font-size:16px">hourglass_top</span> Loading…</div>
        </div>
      </div>
      <div class="kt-bgt-alignment">
        <p class="kt-bgt-alignment-title">Strategic Alignment Score</p>
        <div class="kt-bgt-alignment-score">
          <span class="kt-bgt-alignment-pct" id="kt-bgt-align-score">—</span>
          <span class="kt-bgt-alignment-badge">Optimal</span>
        </div>
        <p class="kt-bgt-alignment-sub">All active spending correlates with Vision 2030 objectives.</p>
      </div>
    </div>

  </div>

  <!-- ── Analytics row ─────────────────────────────────────────────────── -->
  <div class="kt-bgt-analytics">

    <!-- Funding Source Distribution -->
    <div class="kt-bgt-analytics-card">
      <div class="kt-bgt-analytics-hdr">
        <h3>Funding Source Distribution</h3>
        <span class="material-symbols-outlined">more_horiz</span>
      </div>
      <div class="kt-bgt-donut-body">
        <div class="kt-bgt-donut-container" id="kt-bgt-donut-wrap">
          <svg class="kt-bgt-donut-svg" viewBox="0 0 36 36" id="kt-bgt-donut-svg">
            <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#e0e3e5" stroke-width="3"/>
            <circle cx="18" cy="18" r="15.915" fill="transparent"
                    stroke="#00346f" stroke-dasharray="70 30" stroke-dashoffset="0" stroke-width="3"/>
            <circle cx="18" cy="18" r="15.915" fill="transparent"
                    stroke="#00629d" stroke-dasharray="20 80" stroke-dashoffset="-70" stroke-width="3"/>
            <circle cx="18" cy="18" r="15.915" fill="transparent"
                    stroke="#F59E0B" stroke-dasharray="10 90" stroke-dashoffset="-90" stroke-width="3"/>
          </svg>
          <div class="kt-bgt-donut-label">
            <span style="font-size:9px;font-weight:700">Total</span><br>
            <span style="font-size:9px;color:#424751">FY 26/27</span>
          </div>
        </div>
        <div class="kt-bgt-donut-legend">
          <div class="kt-bgt-donut-row">
            <span class="kt-bgt-donut-row-lbl">
              <span class="kt-bgt-donut-dot" style="background:#00346f"></span> Exchequer
            </span>
            <span class="kt-bgt-donut-val">70%</span>
          </div>
          <div class="kt-bgt-donut-row">
            <span class="kt-bgt-donut-row-lbl">
              <span class="kt-bgt-donut-dot" style="background:#00629d"></span> External Grants
            </span>
            <span class="kt-bgt-donut-val">20%</span>
          </div>
          <div class="kt-bgt-donut-row">
            <span class="kt-bgt-donut-row-lbl">
              <span class="kt-bgt-donut-dot" style="background:#F59E0B"></span> Internal Revenue
            </span>
            <span class="kt-bgt-donut-val">10%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Consumption Velocity -->
    <div class="kt-bgt-analytics-card">
      <div class="kt-bgt-analytics-hdr">
        <h3>Consumption Velocity</h3>
        <span class="material-symbols-outlined">more_horiz</span>
      </div>
      <div class="kt-bgt-bars" id="kt-bgt-velocity-bars">
        ${_velocityBars()}
      </div>
      <div class="kt-bgt-bars-labels">
        <span>Jul</span><span>Aug</span><span>Sep</span>
        <span>Oct</span><span>Nov</span><span>Dec</span>
        <span class="kt-bgt-bar-cur">Jan</span>
      </div>
      <p class="kt-bgt-velocity-foot">Spending velocity increased by 18% in Q3 due to infrastructure awards.</p>
    </div>

  </div>

</div>
`);
			this._bind_actions();
		}

		// ── Load data ─────────────────────────────────────────────────────
		_load_data() {
			frappe.call({
				method: "kentender_budget.api.landing.get_budget_landing_data",
				freeze: false,
				callback: (r) => {
					if (r.message) {
						this._data = r.message;
						this._populate_kpis(r.message);
						this._populate_table(r.message.budgets || []);
					}
				},
			});
			this._load_movements();
			this._populate_alignment();
		}

		_load_movements() {
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Budget Reservation",
					fields: [
						"name", "reservation_id", "amount", "currency",
						"status", "source_doctype", "source_business_id",
						"budget_line", "creation",
					],
					limit: 4,
					order_by: "creation desc",
				},
				callback: (r) => {
					this._populate_movements(r.message || []);
				},
			});
		}

		// ── Populate KPIs ─────────────────────────────────────────────────
		_populate_kpis(data) {
			const p = data.portfolio || {};
			const budgets = data.budgets || [];

			const totalAvail     = budgets.reduce((s, b) => s + (b.available_amount || 0), 0);
			const totalReserved  = budgets.reduce((s, b) => s + (b.reserved_amount  || 0), 0);
			const totalCommitted = budgets.reduce((s, b) => s + (b.committed_amount || 0), 0);
			const pending        = p.pending_approval_count || 0;

			$("#kt-bgt-kpi-available").text(_fmt(totalAvail));
			$("#kt-bgt-kpi-reserved").text(_fmt(totalReserved));
			$("#kt-bgt-kpi-committed").text(totalCommitted > 0 ? _fmt(totalCommitted) : "0");
			$("#kt-bgt-kpi-pending").text(pending);

			if (pending > 0) {
				$("#kt-bgt-pulse").show();
			}
		}

		// ── Populate table ────────────────────────────────────────────────
		_populate_table(budgets) {
			const $tbody = $("#kt-bgt-table-body");
			const $filter = $("#kt-bgt-filter-entity");

			// Populate entity filter
			const entities = [...new Set(budgets.map((b) => b.budget_name))];
			entities.forEach((e) => {
				$filter.append(`<option value="${frappe.utils.escape_html(e)}">${frappe.utils.escape_html(e)}</option>`);
			});

			const render = (list) => {
				if (!list.length) {
					$tbody.html(
						`<tr><td colspan="5" class="kt-bgt-empty">No budgets found</td></tr>`
					);
					return;
				}
				$tbody.html(list.map((b) => this._budget_row(b)).join(""));
				this._bind_table_actions($tbody, list);
			};

			render(budgets);

			$filter.on("change", function () {
				const val = $(this).val();
				render(val ? budgets.filter((b) => b.budget_name === val) : budgets);
			});
		}

		_budget_row(b) {
			const total     = b.total_budget_amount || 0;
			const reserved  = b.reserved_amount || 0;
			const committed = b.committed_amount || 0;
			const avail     = b.available_amount || 0;

			const resW = total > 0 ? Math.min(100, (reserved  / total) * 100) : 0;
			const comW = total > 0 ? Math.min(100, (committed / total) * 100) : 0;
			const totalUsed = Math.min(100, resW + comW);

			const chip  = _statusChip(b.status);
			const plan  = b.strategic_plan_title
				? frappe.utils.escape_html(b.strategic_plan_title)
				: (b.strategic_plan ? frappe.utils.escape_html(b.strategic_plan) : "—");

			return `
<tr data-budget="${frappe.utils.escape_html(b.name)}">
  <td class="kt-bgt-td-name">
    <strong>${frappe.utils.escape_html(b.budget_name)}</strong>
    <small>${frappe.utils.escape_html(String(b.fiscal_year || ""))}&nbsp;·&nbsp;${plan}</small>
  </td>
  <td style="min-width:140px">
    <div class="kt-bgt-bar-wrap">
      <span class="kt-bgt-bar-pct">${Math.round(totalUsed)}%</span>
      <div class="kt-bgt-bar-track">
        <div class="kt-bgt-bar-committed" style="width:${comW.toFixed(1)}%"></div>
        <div class="kt-bgt-bar-reserved"  style="width:${resW.toFixed(1)}%"></div>
      </div>
    </div>
    <div class="kt-bgt-bar-legend">
      <span class="kt-l-committed">Commit</span>
      <span class="kt-l-reserved">Reserve</span>
    </div>
  </td>
  <td><span class="kt-bgt-avail kt-bgt-mono">${_fmtShort(avail)}</span></td>
  <td>${chip}</td>
  <td class="kt-bgt-td-action">
    <button data-budget="${frappe.utils.escape_html(b.name)}" title="Open budget">
      <span class="material-symbols-outlined">edit_square</span>
    </button>
  </td>
</tr>`;
		}

		_bind_table_actions($tbody, budgets) {
			$tbody.find("button[data-budget]").on("click", function () {
				const name = $(this).data("budget");
				frappe.set_route("budget-builder", name);
			});
		}

		// ── Populate movements ────────────────────────────────────────────
		_populate_movements(rows) {
			const $tl = $("#kt-bgt-timeline");
			if (!rows.length) {
				$tl.html(`<p style="font-size:13px;color:#737783;text-align:center;padding:16px 0">No recent reservations</p>`);
				return;
			}
			$tl.html(rows.map((r, i) => _moveItem(r, i)).join(""));
		}

		_populate_alignment() {
			// Derived placeholder — will be wired to a real score API later
			$("#kt-bgt-align-score").text("94%");
		}

		// ── Button bindings ───────────────────────────────────────────────
		_bind_actions() {
			$("#kt-bgt-create").on("click", () => {
				const d = new frappe.ui.Dialog({
					title: "Create New Budget",
					fields: [
						{
							label: "Budget Name",
							fieldname: "budget_name",
							fieldtype: "Data",
							reqd: 1,
						},
						{
							label: "Procuring Entity",
							fieldname: "procuring_entity",
							fieldtype: "Link",
							options: "Procuring Entity",
							reqd: 1,
						},
						{
							label: "Fiscal Year",
							fieldname: "fiscal_year",
							fieldtype: "Int",
							default: new Date().getFullYear(),
							reqd: 1,
						},
						{
							label: "Strategic Plan",
							fieldname: "strategic_plan",
							fieldtype: "Link",
							options: "Strategic Plan",
							reqd: 1,
						},
						{
							label: "Currency",
							fieldname: "currency",
							fieldtype: "Link",
							options: "Currency",
							default: "KES",
							reqd: 1,
						},
						{
							label: "Total Budget Amount",
							fieldname: "total_budget_amount",
							fieldtype: "Currency",
							reqd: 1,
						},
					],
					primary_action_label: "Create",
					primary_action: (values) => {
						frappe.call({
							method: "frappe.client.insert",
							args: {
								doc: {
									doctype: "Budget",
									budget_name: values.budget_name,
									procuring_entity: values.procuring_entity,
									fiscal_year: values.fiscal_year,
									strategic_plan: values.strategic_plan,
									currency: values.currency,
									total_budget_amount: values.total_budget_amount,
									status: "Draft",
								},
							},
							callback: (r) => {
								if (r.message) {
									d.hide();
									frappe.show_alert({ message: __("Budget created"), indicator: "green" });
									frappe.set_route("budget-builder", r.message.name);
								}
							},
						});
					},
				});
				d.show();
			});

			$("#kt-bgt-export").on("click", () => {
				frappe.show_alert({ message: __("Export coming soon"), indicator: "blue" });
			});

			$("#kt-bgt-view-all").on("click", () => {
				frappe.set_route("List", "Budget Reservation");
			});
		}
	}

	// ── Helpers ───────────────────────────────────────────────────────────────

	function _fmt(val) {
		if (val === null || val === undefined) return "—";
		return frappe.utils.fmt_money(val, false, "KES");
	}

	function _fmtShort(val) {
		if (!val && val !== 0) return "—";
		if (val >= 1e9) return (val / 1e9).toFixed(1) + "B";
		if (val >= 1e6) return (val / 1e6).toFixed(1) + "M";
		if (val >= 1e3) return (val / 1e3).toFixed(1) + "K";
		return String(Math.round(val));
	}

	function _statusChip(status) {
		const map = {
			Draft:     { cls: "kt-bgt-chip--draft",     lbl: "Draft" },
			Submitted: { cls: "kt-bgt-chip--reviewing",  lbl: "Reviewing" },
			Approved:  { cls: "kt-bgt-chip--healthy",    lbl: "Healthy" },
			Active:    { cls: "kt-bgt-chip--active",     lbl: "Active" },
			Closed:    { cls: "kt-bgt-chip--closed",     lbl: "Closed" },
			Revised:   { cls: "kt-bgt-chip--revised",    lbl: "Revised" },
			Rejected:  { cls: "kt-bgt-chip--rejected",   lbl: "Rejected" },
		};
		const s = map[status] || { cls: "kt-bgt-chip--draft", lbl: status || "—" };
		return `<span class="kt-bgt-chip ${s.cls}">${s.lbl}</span>`;
	}

	function _moveIcon(status) {
		if (!status) return { cls: "kt-bgt-move-dot--neutral", icon: "circle" };
		const s = status.toLowerCase();
		if (s === "active")    return { cls: "kt-bgt-move-dot--reserve", icon: "lock" };
		if (s === "released")  return { cls: "kt-bgt-move-dot--release", icon: "undo" };
		if (s === "converted") return { cls: "kt-bgt-move-dot--commit",  icon: "task_alt" };
		if (s === "cancelled") return { cls: "kt-bgt-move-dot--release", icon: "cancel" };
		return { cls: "kt-bgt-move-dot--neutral", icon: "radio_button_unchecked" };
	}

	function _moveTitle(r) {
		const s = (r.status || "").toLowerCase();
		if (s === "active")    return "Funds Reserved";
		if (s === "released")  return "Reservation Released";
		if (s === "converted") return "Converted to Commitment";
		if (s === "cancelled") return "Reservation Cancelled";
		return "Budget Reservation";
	}

	function _moveItem(r, idx) {
		const ic    = _moveIcon(r.status);
		const title = _moveTitle(r);
		const dimCls = idx >= 3 ? " kt-bgt-move--dim" : "";
		const ref   = r.reservation_id || r.name || "";
		const desc  = r.source_business_id
			? `KES ${_fmtShort(r.amount || 0)} — ${frappe.utils.escape_html(r.source_business_id)}`
			: `KES ${_fmtShort(r.amount || 0)} reservation`;
		const when  = r.creation ? frappe.datetime.prettyDate(r.creation) : "";

		return `
<div class="kt-bgt-move${dimCls}">
  <span class="kt-bgt-move-dot ${ic.cls}" style="font-variation-settings:'FILL' 1">
    <span class="material-symbols-outlined">${ic.icon}</span>
  </span>
  <p class="kt-bgt-move-title">${title}</p>
  <p class="kt-bgt-move-desc">${desc}</p>
  <div class="kt-bgt-move-meta">
    <span class="material-symbols-outlined">schedule</span>
    ${frappe.utils.escape_html(when)}${ref ? " · REF: " + frappe.utils.escape_html(ref) : ""}
  </div>
</div>`;
	}

	function _skeletonRows(n) {
		return Array.from({ length: n })
			.map(
				() => `
<tr class="kt-bgt-skel-row kt-bgt-skel">
  <td><div class="kt-bgt-skel-bar" style="width:60%;height:14px"></div><div class="kt-bgt-skel-bar" style="width:40%;height:10px;margin-top:6px"></div></td>
  <td><div class="kt-bgt-skel-bar" style="width:100%;height:10px"></div></td>
  <td><div class="kt-bgt-skel-bar" style="width:70%;height:14px"></div></td>
  <td><div class="kt-bgt-skel-bar" style="width:50%;height:14px"></div></td>
  <td><div class="kt-bgt-skel-bar" style="width:24px;height:24px;border-radius:4px"></div></td>
</tr>`
			)
			.join("");
	}

	function _velocityBars() {
		// Monthly consumption percentage — static display data matching design
		const data = [
			{ lbl: "Jul", pct: 40,  cur: false },
			{ lbl: "Aug", pct: 55,  cur: false },
			{ lbl: "Sep", pct: 45,  cur: false },
			{ lbl: "Oct", pct: 70,  cur: false },
			{ lbl: "Nov", pct: 65,  cur: false },
			{ lbl: "Dec", pct: 85,  cur: false },
			{ lbl: "Jan", pct: 95,  cur: true  },
		];
		return data
			.map((d) => {
				const opacity = d.cur ? "1" : (0.2 + (d.pct / 100) * 0.6).toFixed(2);
				return `<div class="kt-bgt-bar-col"
                      style="height:${d.pct}%;background:rgba(0,52,111,${opacity});border-radius:4px 4px 0 0"
                      title="${d.lbl}: ${d.pct}%"></div>`;
			})
			.join("");
	}

	// ── Page registration ─────────────────────────────────────────────────────
	frappe.pages["budget-builder"].on_page_load = function (wrapper) {
		frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Budget Hub"),
			single_column: true,
		});
		const hub = new BudgetHub(wrapper);
		hub.init();
	};

	frappe.pages["budget-builder"].on_page_show = function (wrapper) {
		// Re-render if route has no budget_name (i.e. hub view)
		const route = frappe.get_route();
		if (!route[1]) {
			const hub = new BudgetHub(wrapper);
			hub.init();
		}
	};
})();
