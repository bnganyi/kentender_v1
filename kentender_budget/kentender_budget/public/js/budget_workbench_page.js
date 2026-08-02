/* global frappe */
// ── Budget Workbench page — W5-06: Zone 1 + Zone 2 live API wiring ──────────
// Zone 1 (header + KPI cards) and Zone 2 (budget lines) are both populated from
// get_budget_builder_data in a single API call.
// Route: /app/budget-workbench/{budget_name}
(function () {
	"use strict";

	// ── Ensure Google Fonts + Material Symbols (same guard as hub page) ──────
	function _ensureFonts() {
		if (!document.getElementById("kt-bgt-fonts")) {
			const l = document.createElement("link");
			l.id    = "kt-bgt-fonts";
			l.rel   = "stylesheet";
			l.href  =
				"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700" +
				"&family=Manrope:wght@600;700;800" +
				"&family=JetBrains+Mono:wght@500&display=swap";
			document.head.appendChild(l);
		}
		if (!document.getElementById("kt-bgt-icons")) {
			const l = document.createElement("link");
			l.id    = "kt-bgt-icons";
			l.rel   = "stylesheet";
			l.href  =
				"https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap";
			document.head.appendChild(l);
		}
	}

	// ── Lines store (populated by _loadBuilderData on each API response) ────────
	// Simple module-level array — only one workbench is ever mounted at a time.
	let _lines = [];

	// Currently active status filter for Zone 2. "all" = no filter.
	let _lineFilter = "all";

	// Budget header payload from the last successful _loadBuilderData call.
	// Used by the modal to filter Programme options by strategic_plan.
	let _budgetData = null;

	// Page wrapper element — stored on first load so modals can trigger reloads.
	let _wrapper = null;


	function _fmtKES(n, currency) {
		if (n === null || n === undefined || isNaN(n)) return "\u2014";
		const sym = currency || "KES";
		return sym + "\u00a0" + Math.round(n).toLocaleString("en-KE");
	}
	function _fmtNum(n) {
		if (n === null || n === undefined || isNaN(n)) return "\u2014";
		return Math.round(n).toLocaleString("en-KE");
	}

	// ── Zone 1 helpers ────────────────────────────────────────────────────────

	function _setText(root, selector, text) {
		const el = root.querySelector(selector);
		if (el) el.textContent = text;
	}

	function _statusPillClass(status) {
		const s = (status || "").toLowerCase();
		if (s === "active")    return "kt-wbench-status-pill--active";
		if (s === "approved")  return "kt-wbench-status-pill--approved";
		if (s === "draft")     return "kt-wbench-status-pill--draft";
		if (s === "submitted") return "kt-wbench-status-pill--submitted";
		if (s === "closed")    return "kt-wbench-status-pill--closed";
		if (s === "cancelled") return "kt-wbench-status-pill--cancelled";
		if (s === "revised")   return "kt-wbench-status-pill--closed";
		if (s === "rejected")  return "kt-wbench-status-pill--closed";
		return "kt-wbench-status-pill--draft";
	}

	// Returns the HTML for the status-conditional action button bar.
	// | Budget status                               | Buttons shown
	// | Draft revision (supersedes_budget set)      | Submit Revision · Cancel Revision
	// | Draft original (no predecessor)             | Submit for Approval · Delete
	// | Submitted revision                          | Approve Revision · Return · Reject
	// | Submitted original                          | Approve · Reject
	// | Active                                      | Revise Budget · View Evidence
	// | Revised / Rejected / Cancelled / Closed     | View Evidence only
	function _renderActionBar(wrapper, budget) {
		const actionsEl = wrapper.querySelector(".kt-wbench-actions");
		if (!actionsEl) return;
		const status     = (budget.status || "Draft");
		const isRevision = !!budget.supersedes_budget;
		const isDraft    = status === "Draft";
		const isEditable = status === "Draft" || status === "Rejected";

		let html = "";

		if (isDraft && isRevision) {
			html = `
				<button class="kt-wbench-btn kt-wbench-btn-primary" data-wbench="submit-revision-btn" data-testid="kt-wbench-btn-submit-revision">
					<span class="material-symbols-outlined">send</span>Submit Revision
				</button>
				<button class="kt-wbench-btn kt-wbench-btn-ghost" data-wbench="cancel-revision-btn" data-testid="kt-wbench-btn-cancel-revision">
					<span class="material-symbols-outlined">cancel</span>Cancel Revision
				</button>`;
		} else if (isDraft && !isRevision) {
			html = `
				<button class="kt-wbench-btn kt-wbench-btn-ghost" data-wbench="edit-budget-btn" data-testid="kt-wbench-btn-edit-budget">
					<span class="material-symbols-outlined">edit</span>Edit Budget
				</button>
				<button class="kt-wbench-btn kt-wbench-btn-primary" data-wbench="submit-btn" data-testid="kt-wbench-btn-submit">
					<span class="material-symbols-outlined">send</span>Submit for Approval
				</button>`;
		} else if (status === "Submitted" && isRevision) {
			html = `
				<button class="kt-wbench-btn kt-wbench-btn-primary" data-wbench="approve-revision-btn" data-testid="kt-wbench-btn-approve-revision">
					<span class="material-symbols-outlined">check_circle</span>Approve Revision
				</button>
				<button class="kt-wbench-btn kt-wbench-btn-ghost" data-wbench="return-revision-btn" data-testid="kt-wbench-btn-return-revision">
					<span class="material-symbols-outlined">undo</span>Return
				</button>`;
		} else if (status === "Submitted" && !isRevision) {
			html = `
				<button class="kt-wbench-btn kt-wbench-btn-primary" data-wbench="approve-btn" data-testid="kt-wbench-btn-approve">
					<span class="material-symbols-outlined">check_circle</span>Approve
				</button>
				<button class="kt-wbench-btn kt-wbench-btn-ghost" data-wbench="reject-btn" data-testid="kt-wbench-btn-reject">
					<span class="material-symbols-outlined">cancel</span>Reject
				</button>`;
		} else if (status === "Active") {
			html = `
				<button class="kt-wbench-btn kt-wbench-btn-ghost" data-wbench="revise-btn" data-testid="kt-wbench-btn-revise">
					<span class="material-symbols-outlined">edit_square</span>Revise Budget
				</button>
				<button class="kt-wbench-btn kt-wbench-btn-primary">
					<span class="material-symbols-outlined">visibility</span>View Evidence
				</button>`;
		} else if (status === "Approved") {
			html = `
				<button class="kt-wbench-btn kt-wbench-btn-primary" data-wbench="activate-btn" data-testid="kt-wbench-btn-activate">
					<span class="material-symbols-outlined">rocket_launch</span>Activate Budget
				</button>`;
		} else if (status === "Rejected") {
			html = `
				<button class="kt-wbench-btn kt-wbench-btn-ghost" data-wbench="edit-budget-btn" data-testid="kt-wbench-btn-edit-budget">
					<span class="material-symbols-outlined">edit</span>Edit Budget
				</button>
				<button class="kt-wbench-btn kt-wbench-btn-primary" data-wbench="resubmit-btn" data-testid="kt-wbench-btn-resubmit">
					<span class="material-symbols-outlined">send</span>Resubmit for Approval
				</button>`;
		} else {
			html = `
				<button class="kt-wbench-btn kt-wbench-btn-primary">
					<span class="material-symbols-outlined">visibility</span>View Evidence
				</button>`;
		}

		actionsEl.innerHTML = html;

		// Show/hide "Add Budget Line" — only visible when Draft or Rejected
		const addBtn = wrapper.querySelector("[data-testid='kt-wbench-btn-add']");
		if (addBtn) {
			addBtn.style.display = isEditable ? "" : "none";
		}
	}

	// Renders (or removes) the revision context banner above Zone 1.
	function _renderRevisionBanner(wrapper, budget) {
		const existingBanner = wrapper.querySelector("[data-wbench='revision-banner']");
		if (existingBanner) existingBanner.remove();

		if (!budget.supersedes_budget) return;

		const banner = document.createElement("div");
		banner.setAttribute("data-wbench", "revision-banner");
		banner.className = "kt-wbench-revision-banner";
		banner.innerHTML = `
			<span class="material-symbols-outlined kt-wbench-revision-banner-icon">history</span>
			<span>Revision of <strong>${budget.supersedes_budget}</strong> &mdash; Version ${budget.version_no || ""}</span>
			<button class="kt-wbench-revision-banner-btn" data-wbench="view-changes-btn">
				<span class="material-symbols-outlined" style="font-size:14px;vertical-align:-2px;">compare_arrows</span>
				View Changes
			</button>`;

		const zone1 = wrapper.querySelector("[data-testid='kt-wbench-zone1']");
		if (zone1) zone1.parentNode.insertBefore(banner, zone1);
	}

	// Opens a modal dialog showing the before/after allocation diff for a revision budget.
	function _openRevisionDiffModal(budget) {
		if (!budget || !budget.supersedes_budget) return;

		frappe.call({
			method: "kentender_budget.api.revision.get_revision_diff",
			args:   { budget_name: budget.name },
			callback: function (r) {
				const diff = r && r.message;
				if (!diff || !diff.is_revision) {
					frappe.msgprint({ message: "No changes found for this revision.", title: "Changes", indicator: "blue" });
					return;
				}

				const predTotals = diff.predecessor || {};
				const revTotals  = diff.revision    || {};
				const fmt = function (n) { return (n || 0).toLocaleString("en-KE", { minimumFractionDigits: 2 }); };
				const delta = (revTotals.allocated || 0) - (predTotals.allocated || 0);
				const deltaSign = delta >= 0 ? "+" : "";
				const deltaCls  = delta >= 0 ? "color:#1a7f37" : "color:#cf222e";

				const lineDiffRows = (diff.line_diffs || []).map(function (ld) {
					const chg     = ld.change || 0;
					const chgSign = chg >= 0 ? "+" : "";
					const chgCls  = chg > 0 ? "color:#1a7f37" : (chg < 0 ? "color:#cf222e" : "");
					const badge   = ld.is_new
						? "<span style='display:inline-block;margin-left:6px;padding:1px 5px;border-radius:3px;font-size:9px;font-weight:700;background:#dafbe1;color:#116329;vertical-align:middle;'>NEW</span>"
						: ld.is_removed
						? "<span style='display:inline-block;margin-left:6px;padding:1px 5px;border-radius:3px;font-size:9px;font-weight:700;background:#ffd8d8;color:#a40000;vertical-align:middle;'>REMOVED</span>"
						: "";
					return `<tr>
						<td style="padding:6px 12px;border-bottom:1px solid #e8eaed;">${ld.budget_line_name || ld.budget_line_code}${badge}</td>
						<td style="padding:6px 12px;border-bottom:1px solid #e8eaed;text-align:right;font-variant-numeric:tabular-nums;">${fmt(ld.before_allocated)}</td>
						<td style="padding:6px 12px;border-bottom:1px solid #e8eaed;text-align:right;font-variant-numeric:tabular-nums;">${fmt(ld.after_allocated)}</td>
						<td style="padding:6px 12px;border-bottom:1px solid #e8eaed;text-align:right;font-variant-numeric:tabular-nums;${chgCls}">${chgSign}${fmt(chg)}</td>
					</tr>`;
				}).join("");

				const html = `
					<div style="margin-bottom:12px;display:flex;align-items:center;gap:8px;font-size:13px;color:#45464d;">
						<span>Predecessor: <strong>${diff.predecessor_name || budget.supersedes_budget}</strong></span>
						<span style="margin-left:auto;font-weight:700;font-size:13px;${deltaCls}">${deltaSign}${fmt(delta)} KES total</span>
					</div>
					<table style="width:100%;border-collapse:collapse;font-size:12px;">
						<thead>
							<tr style="background:#f6f8fa;">
								<th style="padding:6px 12px;text-align:left;font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:#656d76;border-bottom:2px solid #d0d7de;">Line</th>
								<th style="padding:6px 12px;text-align:right;font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:#656d76;border-bottom:2px solid #d0d7de;">Before</th>
								<th style="padding:6px 12px;text-align:right;font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:#656d76;border-bottom:2px solid #d0d7de;">After</th>
								<th style="padding:6px 12px;text-align:right;font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:#656d76;border-bottom:2px solid #d0d7de;">Change</th>
							</tr>
						</thead>
						<tbody>${lineDiffRows || "<tr><td colspan='4' style='padding:16px 12px;text-align:center;color:#656d76;'>No line changes found.</td></tr>"}</tbody>
					</table>`;

				frappe.msgprint({
					title: "Before / After — Allocation Changes",
					message: html,
					wide: true,
				});
			},
			error: function () {
				frappe.msgprint({ message: "Could not load revision diff.", title: "Error", indicator: "red" });
			},
		});
	}

	// Fills Zone 1 DOM nodes in-place from API response; removes skeleton state.
	function _populateZone1(wrapper, budget, totals) {
		const z1 = wrapper.querySelector("[data-testid='kt-wbench-zone1']");
		if (!z1) return;

		const currency = budget.currency || "KES";

		// Breadcrumb name
		const crumbEl = wrapper.querySelector("[data-testid='kt-wbench-budget-name']");
		if (crumbEl) crumbEl.textContent = budget.budget_name || budget.name;

		// Title
		const titleEl = z1.querySelector("[data-testid='kt-wbench-title']");
		if (titleEl) {
			titleEl.textContent = budget.budget_name || budget.name;
			titleEl.classList.remove("kt-wbench-skel");
		}

		// Status pill
		const statusEl     = z1.querySelector("[data-testid='kt-wbench-status']");
		const statusTextEl = z1.querySelector("[data-wbench='status-text']");
		if (statusEl && statusTextEl) {
			statusEl.className = "kt-wbench-status-pill " + _statusPillClass(budget.status);
			statusTextEl.textContent = budget.status || "\u2014";
		}

		// Subtitle metadata
		_setText(z1, "[data-wbench='entity']",      budget.procuring_entity || "\u2014");
		_setText(z1, "[data-wbench='fiscal-year']", budget.fiscal_year      ? String(budget.fiscal_year) : "\u2014");
		_setText(z1, "[data-wbench='currency']",    currency);

		// KPI summary cards — "Approved Budget" is the sum of active line allocations,
		// not the static total_budget_amount ceiling (per Budget totals design doc §1).
		const approved  = (totals && totals.allocated_sum)  || 0;
		const available = (totals && totals.available_sum)  || 0;
		const reserved  = (totals && totals.reserved_sum)   || 0;
		const committed = (totals && totals.committed_sum)  || 0;

		const approvedEl = z1.querySelector("[data-testid='kt-wbench-approved']");
		if (approvedEl) {
			approvedEl.textContent = _fmtKES(approved, currency);
			approvedEl.classList.remove("kt-wbench-skel");
		}
		const availableEl = z1.querySelector("[data-testid='kt-wbench-available']");
		if (availableEl) {
			availableEl.textContent = _fmtKES(available, currency);
			availableEl.classList.remove("kt-wbench-skel");
		}
		const reservedEl = z1.querySelector("[data-testid='kt-wbench-reserved']");
		if (reservedEl) {
			reservedEl.textContent = _fmtKES(reserved, currency);
			reservedEl.classList.remove("kt-wbench-skel");
		}
		const committedEl = z1.querySelector("[data-testid='kt-wbench-committed']");
		if (committedEl) {
			committedEl.textContent = _fmtKES(committed, currency);
			committedEl.classList.remove("kt-wbench-skel");
		}

		// Clear loading flag
		z1.removeAttribute("data-loading");

		// Status-conditional action buttons + "Add Budget Line" visibility
		_renderActionBar(wrapper, budget);
		// Revision context banner (above Zone 1, removed if not a revision)
		_renderRevisionBanner(wrapper, budget);
	}

	function _showZone1Error(wrapper) {
		const z1 = wrapper.querySelector("[data-testid='kt-wbench-zone1']");
		if (!z1) return;
		const titleEl = z1.querySelector("[data-testid='kt-wbench-title']");
		if (titleEl) {
			titleEl.textContent = "Could not load budget data";
			titleEl.classList.remove("kt-wbench-skel");
			titleEl.style.color = "var(--ktw-error)";
		}
		z1.removeAttribute("data-loading");
	}

	// Renders the live lines list into Zone 2; updates module-level _lines store.
	function _populateZone2(wrapper, apiLines) {
		_lines = (apiLines || []).map(function (l, i) {
			return Object.assign({}, l, { idx: i });
		});

		const list = wrapper.querySelector("[data-testid='kt-wbench-lines-list']");
		if (!list) return;

		// Reset filter to "all" on fresh data load so pills stay coherent.
		_lineFilter = "all";
		_refreshFilterPills(wrapper);
		_applyLineFilter(wrapper);

		// Auto-select first line: clear artefacts panel ready for W5-07 click handler
		const artBody = wrapper.querySelector("[data-testid='kt-wbench-artefacts-body']");
		if (artBody) {
			artBody.innerHTML =
				'<p class="kt-wbench-art-empty" style="padding:20px 16px">Select a budget line to view linked artefacts.</p>';
		}
	}

	function _showZone2Error(wrapper) {
		const list = wrapper.querySelector("[data-testid='kt-wbench-lines-list']");
		if (list) {
			list.innerHTML = '<p class="kt-wbench-lines-empty" style="color:var(--ktw-error)">Could not load budget lines.</p>';
		}
	}

	// ── Zone 2 filter pills ───────────────────────────────────────────────────

	// Re-render visible cards from the in-memory _lines store.
	function _applyLineFilter(wrapper) {
		const filter = _lineFilter;
		const visible = filter === "all"
			? _lines
			: _lines.filter(function (l) {
				return (l.line_status || "Draft").toLowerCase() === filter.toLowerCase();
			  });

		const list = wrapper.querySelector("[data-testid='kt-wbench-lines-list']");
		if (!list) return;

		if (!visible.length) {
			const label = filter === "all" ? "No budget lines." : `No lines with status "${filter}".`;
			list.innerHTML = `<p class="kt-wbench-lines-empty">${label}</p>`;
			return;
		}
		list.innerHTML = visible.map(function (line, i) {
			return _buildLineCard(line, i === 0, line.idx);
		}).join("");
	}

	// Rebuild the pill bar to show one pill per distinct status present in _lines,
	// plus the "All Lines" pill. Updates active highlight from _lineFilter.
	function _refreshFilterPills(wrapper) {
		const container = wrapper.querySelector("[data-testid='kt-wbench-filter-pills']");
		if (!container) return;

		const statuses = [];
		_lines.forEach(function (l) {
			const s = l.line_status || "Draft";
			if (!statuses.includes(s)) statuses.push(s);
		});

		// "All" pill always first; only show status pills if >1 status exists
		const pills = [{ value: "all", label: "All Lines", icon: "filter_list" }];
		if (statuses.length > 1) {
			statuses.forEach(function (s) {
				pills.push({ value: s, label: s, icon: null });
			});
		}

		container.innerHTML = pills.map(function (p) {
			const isActive = _lineFilter === p.value;
			const activeCls = isActive ? " kt-wbench-filter-pill--active" : "";
			const icon = p.icon
				? `<span class="material-symbols-outlined">${p.icon}</span>`
				: "";
			return `<button class="kt-wbench-filter-pill${activeCls}"
				data-filter="${p.value}" data-testid="kt-wbench-filter-${p.value.toLowerCase()}">${icon}${p.label}</button>`;
		}).join("");
	}

	// Single API call that populates both Zone 1 and Zone 2.
	function _loadBuilderData(wrapper, budgetName) {
		if (!budgetName) return;
		_wrapper = wrapper;
		frappe.call({
			method: "kentender_budget.api.builder.get_budget_builder_data",
			args:   { budget_name: budgetName, lines_filter: "active" },
			callback: function (r) {
				if (!r || !r.message) {
					_showZone1Error(wrapper);
					_showZone2Error(wrapper);
					return;
				}
				const data = r.message;
				_budgetData = data.budget || {};
				_populateZone1(wrapper, _budgetData, data.totals || {});
				_populateZone2(wrapper, data.budget_lines || []);
			},
			error: function () {
				_showZone1Error(wrapper);
				_showZone2Error(wrapper);
			},
		});
	}

	// ── HTML builders ─────────────────────────────────────────────────────────

	function _lineStatusClass(status) {
		const s = (status || "").toLowerCase().replace(/\s+/g, "-");
		if (s === "active")              return "kt-wbench-line-status--active";
		if (s === "draft")               return "kt-wbench-line-status--draft";
		if (s === "approved")            return "kt-wbench-line-status--approved";
		if (s === "exhausted")           return "kt-wbench-line-status--exhausted";
		if (s === "revised")             return "kt-wbench-line-status--revised";
		if (s === "cancelled")           return "kt-wbench-line-status--cancelled";
		if (s === "removed")             return "kt-wbench-line-status--removed";
		if (s.includes("commit"))        return "kt-wbench-line-status--committed";
		if (s.includes("reserved"))      return "kt-wbench-line-status--reserved";
		return "kt-wbench-line-status--draft";
	}

	function _buildLineCard(line, isActive, idx) {
		const activeCls = isActive ? "kt-wbench-line-card--active" : "";
		const lineStatus = (line.line_status || "Draft").toLowerCase();
		const canReserve = lineStatus === "active";

		const btns = `<button class="kt-wbench-line-btn" data-line-act="open-line" data-line-idx="${idx}" data-testid="kt-wbench-btn-open-line">Open Line</button>
		   ${canReserve ? `<button class="kt-wbench-line-btn">Reserve Funds</button>` : ""}
		   <button class="kt-wbench-line-btn${isActive ? " kt-wbench-line-btn--highlight" : ""}">View Linked Artefacts</button>`;

		const reserved  = line.amount_reserved  || 0;
		const committed = line.amount_committed  || 0;
		const available = line.amount_available  || 0;

		const reservedValueCls  = reserved  > 0 ? "kt-wbench-line-fin-value--reserved"  : "";
		const committedValueCls = committed > 0 ? "kt-wbench-line-fin-value--committed" : "";
		const availableValueCls = available > 0 ? "kt-wbench-line-fin-value--available" : "";

		const title       = line.budget_line_name  || line.name;
		const dept        = line.department        || "\u2014";
		const econ        = line.economic_classification || "\u2014";
		const fundSrc     = line.funding_source_label    || line.funding_source || "\u2014";
		const strategyObj = line.program_label           || "\u2014";
		const status      = line.line_status || "Draft";

		return `<div class="kt-wbench-line-card ${activeCls}" data-line-idx="${line.idx}" data-line-name="${line.name}" data-testid="kt-wbench-line-card">
			<div class="kt-wbench-line-card-head">
				<div>
					<h4 class="kt-wbench-line-name" data-testid="kt-wbench-line-name">${title}</h4>
					<div class="kt-wbench-line-meta">
						<span class="kt-wbench-line-meta-item"><strong>Dept:</strong> ${dept}</span>
						<span class="kt-wbench-line-meta-item"><strong>Type:</strong> ${econ} &bull; ${fundSrc}</span>
					</div>
					<p class="kt-wbench-line-strategy-link">Programme: <span>${strategyObj}</span></p>
				</div>
				<span class="kt-wbench-line-status ${_lineStatusClass(status)}">${status}</span>
			</div>
			<div class="kt-wbench-line-financials">
				<div class="kt-wbench-line-fin-col">
					<span class="kt-wbench-line-fin-label">Approved</span>
					<span class="kt-wbench-line-fin-value">${_fmtNum(line.amount_allocated)}</span>
				</div>
				<div class="kt-wbench-line-fin-col">
					<span class="kt-wbench-line-fin-label">Reserved</span>
					<span class="kt-wbench-line-fin-value ${reservedValueCls}">${_fmtNum(reserved)}</span>
				</div>
				<div class="kt-wbench-line-fin-col">
					<span class="kt-wbench-line-fin-label">Committed</span>
					<span class="kt-wbench-line-fin-value ${committedValueCls}">${_fmtNum(committed)}</span>
				</div>
				<div class="kt-wbench-line-fin-col">
					<span class="kt-wbench-line-fin-label">Actual</span>
					<span class="kt-wbench-line-fin-value">${_fmtNum(line.amount_consumed)}</span>
				</div>
				<div class="kt-wbench-line-fin-col">
					<span class="kt-wbench-line-fin-label">Available</span>
					<span class="kt-wbench-line-fin-value ${availableValueCls}">${_fmtNum(available)}</span>
				</div>
			</div>
			<div class="kt-wbench-line-actions">
				${btns}
			</div>
		</div>`;
	}

	// ── Zone 3: Artefacts panel renderers ─────────────────────────────────────

	function _artefactChipClass(status) {
		const s = (status || "").toLowerCase();
		if (s === "active" || s === "reserved" || s === "budget reserved") return "kt-wbench-art-chip--reserved";
		if (s === "committed" || s === "converted")                        return "kt-wbench-art-chip--committed";
		if (s === "released" || s === "available"
			|| s.includes("ready") || s === "approved")                    return "kt-wbench-art-chip--available";
		return "kt-wbench-art-chip--reserved";
	}

	function _movDotClass(eventType) {
		if (eventType === "reservation")  return "kt-wbench-mov-dot--reserved";
		if (eventType === "release")      return "kt-wbench-mov-dot--primary";
		if (eventType === "commitment")   return "kt-wbench-mov-dot--committed";
		return "kt-wbench-mov-dot--primary";
	}

	function _buildArtefactsPanel(lineName, lineTitle, art) {
		const strategy = art.strategy || {};
		const demands   = art.demands   || [];
		const packages  = art.packages  || [];
		const tenders   = art.tenders   || [];
		const contracts = art.contracts || [];
		const movements = art.movements || [];

		// ── Strategy — single card with title + description (original design) ──
		const strategyTitle = strategy.program_label || null;
		const strategyDesc  = strategy.program_description || strategy.sub_program_label || null;
		const strategyHtml  = strategyTitle
			? `<div class="kt-wbench-art-card">
				<p class="kt-wbench-art-card-title">${strategyTitle}</p>
				${strategyDesc ? `<p class="kt-wbench-art-card-desc">Objective: ${strategyDesc}</p>` : ""}
			</div>`
			: `<p class="kt-wbench-art-empty">None yet</p>`;

		// ── Demands ───────────────────────────────────────────────────────────
		const demandsHtml = demands.length
			? demands.map(function (d, i) {
				return `<div class="kt-wbench-art-card">
					<p class="kt-wbench-art-card-title">${i + 1}. ${d.ref || d.source_docname || "\u2014"}</p>
					<div class="kt-wbench-art-card-row">
						<span class="kt-wbench-art-chip ${_artefactChipClass(d.status)}">${d.status || "\u2014"}</span>
						<span class="kt-wbench-art-card-amount">${_fmtNum(d.amount)}</span>
					</div>
					<button class="kt-wbench-art-open-btn">Open Demand</button>
				</div>`;
			}).join("")
			: `<p class="kt-wbench-art-empty">None yet</p>`;

		// ── Packages ──────────────────────────────────────────────────────────
		const packagesHtml = packages.length
			? packages.map(function (p, i) {
				return `<div class="kt-wbench-art-card">
					<p class="kt-wbench-art-card-title">${i + 1}. ${p.title || p.ref || p.name}</p>
					<div class="kt-wbench-art-card-row">
						<span class="kt-wbench-art-chip ${_artefactChipClass(p.status)}">${p.status || "\u2014"}</span>
						<span class="kt-wbench-art-card-amount">${_fmtNum(p.amount)}</span>
					</div>
					<button class="kt-wbench-art-open-btn">Open Package</button>
				</div>`;
			}).join("")
			: `<p class="kt-wbench-art-empty">None yet</p>`;

		// ── Tenders ───────────────────────────────────────────────────────────
		const tendersHtml = tenders.length
			? tenders.map(function (t) {
				return `<div class="kt-wbench-art-card">
					<p class="kt-wbench-art-card-title">${t.title || t.ref || t.name}</p>
				</div>`;
			}).join("")
			: `<p class="kt-wbench-art-empty">None yet</p>`;

		// ── Contracts ─────────────────────────────────────────────────────────
		const contractsHtml = contracts.length
			? contracts.map(function (c) {
				return `<div class="kt-wbench-art-card">
					<p class="kt-wbench-art-card-title">${c.title || c.ref || c.name}</p>
				</div>`;
			}).join("")
			: `<p class="kt-wbench-art-empty">None yet</p>`;

		// ── Movements timeline ────────────────────────────────────────────────
		const movementsHtml = movements.length
			? movements.map(function (m) {
				const ts = m.ts ? new Date(m.ts).toLocaleDateString("en-KE", { day: "2-digit", month: "short", year: "numeric" }) : "";
				return `<div class="kt-wbench-mov-item">
					<div class="kt-wbench-mov-dot ${_movDotClass(m.event_type)}">
						<div class="kt-wbench-mov-dot-inner"></div>
					</div>
					<p class="kt-wbench-mov-title">${m.title || m.event_type}</p>
					<p class="kt-wbench-mov-sub">${m.desc || ""}${ts ? " \u2022 " + ts : ""}</p>
				</div>`;
			}).join("")
			: `<p class="kt-wbench-art-empty">No movements recorded.</p>`;

		return `
			<div class="kt-wbench-art-section">
				<p class="kt-wbench-line-context-label">Budget Line</p>
				<p class="kt-wbench-line-context-name" data-testid="kt-wbench-artefacts-line-name">${lineTitle || lineName}</p>
			</div>

			<div class="kt-wbench-art-section">
				<div class="kt-wbench-art-section-header">
					<p class="kt-wbench-art-label">Strategy</p>
					<button class="kt-wbench-art-link-btn">
						Open Strategy
						<span class="material-symbols-outlined">open_in_new</span>
					</button>
				</div>
				${strategyHtml}
			</div>

			<div class="kt-wbench-art-section">
				<div class="kt-wbench-art-section-header">
					<p class="kt-wbench-art-label">Linked Demands (${demands.length})</p>
					${demands.length > 1 ? `<button class="kt-wbench-art-link-btn">View all</button>` : ""}
				</div>
				${demandsHtml}
			</div>

			<div class="kt-wbench-art-section">
				<div class="kt-wbench-art-section-header">
					<p class="kt-wbench-art-label">Linked Packages (${packages.length})</p>
					${packages.length > 1 ? `<button class="kt-wbench-art-link-btn">View packages</button>` : ""}
				</div>
				${packagesHtml}
			</div>

			<div class="kt-wbench-art-section">
				<div class="kt-wbench-art-grid2">
					<div>
						<p class="kt-wbench-art-label" style="margin-bottom:8px">Tenders</p>
						${tendersHtml}
					</div>
					<div>
						<p class="kt-wbench-art-label" style="margin-bottom:8px">Contracts</p>
						${contractsHtml}
					</div>
				</div>
			</div>

			<div class="kt-wbench-art-section">
				<p class="kt-wbench-art-label" style="margin-bottom:12px">Budget Movements</p>
				<div class="kt-wbench-movements">
					${movementsHtml}
				</div>
			</div>`;
	}

	// Fetches artefacts from the API and paints Zone 3 in-place.
	// A stale-response guard token prevents a slow previous call from
	// overwriting a newer selection.
	let _artefactsToken = 0;

	function _loadArtefacts(wrapper, line) {
		const artBody = wrapper.querySelector("[data-testid='kt-wbench-artefacts-body']");
		if (!artBody) return;

		const token = ++_artefactsToken;

		artBody.innerHTML = `
			<div class="kt-wbench-art-section">
				<p class="kt-wbench-line-context-label">Budget Line</p>
				<p class="kt-wbench-line-context-name">${line.budget_line_name || line.name}</p>
			</div>
			<div class="kt-wbench-art-section kt-wbench-art-loading">
				<span class="material-symbols-outlined kt-wbench-art-spinner">autorenew</span>
				<p class="kt-wbench-art-empty">Loading artefacts&hellip;</p>
			</div>`;

		frappe.call({
			method: "kentender_budget.api.artefacts.get_budget_line_artefacts",
			args:   { budget_line_name: line.name },
			callback: function (r) {
				if (token !== _artefactsToken) return; // stale response
				if (!r || !r.message) {
					artBody.innerHTML =
						'<p class="kt-wbench-art-empty" style="padding:20px 16px;color:var(--ktw-error)">Could not load artefacts.</p>';
					return;
				}
				artBody.innerHTML = _buildArtefactsPanel(
					line.name,
					line.budget_line_name || line.name,
					r.message
				);
			},
			error: function () {
				if (token !== _artefactsToken) return;
				artBody.innerHTML =
					'<p class="kt-wbench-art-empty" style="padding:20px 16px;color:var(--ktw-error)">Could not load artefacts.</p>';
			},
		});
	}

	function _html(budgetName) {
		// Zone 1 renders skeleton; _loadBuilderData fills real values after API call.
		// Zone 2 lines list renders a loading placeholder; replaced by _populateZone2.
		// Zone 3 artefacts panel is empty until the user selects a line (W5-07).
		const displayName = budgetName || "\u2014";

		return `
<div class="kt-wbench" data-testid="kt-wbench-root">

	<!-- Breadcrumb -->
	<nav class="kt-wbench-breadcrumb" aria-label="breadcrumb">
		<a href="#" data-wbench="back-link" class="kt-wbench-back-link">
			<span class="material-symbols-outlined">arrow_back</span>
			<span>Back to Budget Hub</span>
		</a>
		<span class="kt-wbench-breadcrumb-sep">|</span>
		<span data-testid="kt-wbench-budget-name">${displayName}</span>
	</nav>

	<!-- Zone 1: Budget Identity + Financial Summary -->
	<section class="kt-wbench-zone1" data-testid="kt-wbench-zone1" data-loading="true">

		<div class="kt-wbench-title-row">
			<div>
				<div class="kt-wbench-title-group">
					<h2 class="kt-wbench-title kt-wbench-skel" data-testid="kt-wbench-title">${displayName}</h2>
					<span class="kt-wbench-status-pill kt-wbench-status-pill--loading" data-testid="kt-wbench-status">
						<span class="kt-wbench-status-dot"></span>
						<span data-wbench="status-text">Loading&hellip;</span>
					</span>
				</div>
				<p class="kt-wbench-subtitle">
					Procuring Entity: <strong data-wbench="entity">&mdash;</strong>
					&nbsp;&bull;&nbsp;
					Fiscal Year: <strong data-wbench="fiscal-year">&mdash;</strong>
					&nbsp;&bull;&nbsp;
					Currency: <strong data-wbench="currency">&mdash;</strong>
				</p>
			</div>
			<div class="kt-wbench-actions">
				<!-- Populated dynamically by _renderActionBar() after data loads -->
			</div>
		</div>

		<!-- 4-up financial summary cards -->
		<div class="kt-wbench-summary-cards" data-testid="kt-wbench-summary-cards">
			<div class="kt-wbench-summary-card">
				<p class="kt-wbench-summary-card-label">Approved Budget</p>
				<p class="kt-wbench-summary-card-value kt-wbench-skel" data-testid="kt-wbench-approved">&mdash;</p>
			</div>
			<div class="kt-wbench-summary-card">
				<p class="kt-wbench-summary-card-label">Available Balance</p>
				<p class="kt-wbench-summary-card-value kt-wbench-summary-card-value--available kt-wbench-skel" data-testid="kt-wbench-available">&mdash;</p>
			</div>
			<div class="kt-wbench-summary-card">
				<p class="kt-wbench-summary-card-label">Reserved Amount</p>
				<p class="kt-wbench-summary-card-value kt-wbench-summary-card-value--reserved kt-wbench-skel" data-testid="kt-wbench-reserved">&mdash;</p>
			</div>
			<div class="kt-wbench-summary-card">
				<p class="kt-wbench-summary-card-label">Committed Amount</p>
				<p class="kt-wbench-summary-card-value kt-wbench-summary-card-value--committed kt-wbench-skel" data-testid="kt-wbench-committed">&mdash;</p>
			</div>
		</div>
	</section>

	<!-- Zones 2 + 3 -->
	<div class="kt-wbench-body">

		<!-- Zone 2: Budget Lines -->
		<section class="kt-wbench-lines-panel" data-testid="kt-wbench-lines-panel">
			<div class="kt-wbench-lines-toolbar">
				<h3 class="kt-wbench-lines-title">Budget Lines</h3>
				<div class="kt-wbench-toolbar-actions">
					<div class="kt-wbench-filter-pills" data-testid="kt-wbench-filter-pills">
						<button class="kt-wbench-filter-pill kt-wbench-filter-pill--active"
							data-filter="all" data-testid="kt-wbench-filter-all">
							<span class="material-symbols-outlined">filter_list</span>All Lines
						</button>
					</div>
					<button class="kt-wbench-btn-add" data-testid="kt-wbench-btn-add">
						<span class="material-symbols-outlined">add</span>
						Add Budget Line
					</button>
				</div>
			</div>
			<div class="kt-wbench-lines-list" data-testid="kt-wbench-lines-list">
				<p class="kt-wbench-lines-loading">Loading budget lines&hellip;</p>
			</div>
		</section>

		<!-- Zone 3: Associated Artefacts -->
		<section class="kt-wbench-artefacts" data-testid="kt-wbench-artefacts">
			<div class="kt-wbench-artefacts-header">
				<h3 class="kt-wbench-artefacts-title">Associated Artefacts</h3>
				<button class="kt-wbench-artefacts-close" aria-label="Close artefacts panel">
					<span class="material-symbols-outlined">close</span>
				</button>
			</div>
			<div class="kt-wbench-artefacts-body" data-testid="kt-wbench-artefacts-body">
				<p class="kt-wbench-art-empty" style="padding:20px 16px">Select a budget line to view linked artefacts.</p>
			</div>
		</section>

	</div><!-- /.kt-wbench-body -->
</div><!-- /.kt-wbench -->`;
	}

	// ── Edit Budget header modal ──────────────────────────────────────────────

	function _showEditBudgetModal(budget) {
		function esc(s) {
			var div = document.createElement("div");
			div.textContent = s == null ? "" : String(s);
			return div.innerHTML;
		}
		var FIELD_WRAP  = "display:flex;flex-direction:column;";
		var LBL_STYLE   = "display:block;font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#45464d;margin-bottom:6px;font-family:'Inter',sans-serif;";
		var INPUT_STYLE = "width:100%;background:#f1f5f9;border:1px solid transparent;border-radius:4px;padding:8px 12px;font-size:13px;font-family:'Inter',sans-serif;color:#191c1e;outline:none;box-sizing:border-box;";
		var ERR_STYLE   = "font-size:11px;color:#ba1a1a;margin-top:4px;display:none;";

		var bodyHtml = `
			<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
				<div style="${FIELD_WRAP}" data-field="budget_display_name">
					<label style="${LBL_STYLE}" for="kteb_name">Budget Name <span style="color:#ba1a1a">*</span></label>
					<input id="kteb_name" name="budget_display_name" type="text"
						style="${INPUT_STYLE}" value="${esc(budget.budget_name || "")}">
					<span style="${ERR_STYLE}" data-err="budget_display_name"></span>
				</div>
				<div style="${FIELD_WRAP}" data-field="fiscal_year">
					<label style="${LBL_STYLE}" for="kteb_fy">Fiscal Year <span style="color:#ba1a1a">*</span></label>
					<input id="kteb_fy" name="fiscal_year" type="number" min="2000" max="2099" step="1"
						style="${INPUT_STYLE}" value="${esc(budget.fiscal_year || "")}">
					<span style="${ERR_STYLE}" data-err="fiscal_year"></span>
				</div>
			</div>
			<div style="${FIELD_WRAP}" data-field="currency">
				<label style="${LBL_STYLE}" for="kteb_cur">Currency</label>
				<select id="kteb_cur" name="currency" style="${INPUT_STYLE}">
					${["KES","USD","EUR","GBP"].map(function (c) {
						return `<option value="${c}"${c === (budget.currency || "KES") ? " selected" : ""}>${c}</option>`;
					}).join("")}
				</select>
			</div>
			<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
				<div style="${FIELD_WRAP}">
					<label style="${LBL_STYLE}" for="kteb_eff">Effective Date</label>
					<input id="kteb_eff" name="effective_date" type="date"
						style="${INPUT_STYLE}" value="${esc(budget.effective_date || "")}">
				</div>
				<div style="${FIELD_WRAP}">
					<label style="${LBL_STYLE}" for="kteb_close">Closing Date</label>
					<input id="kteb_close" name="closing_date" type="date"
						style="${INPUT_STYLE}" value="${esc(budget.closing_date || "")}">
				</div>
			</div>
		`;

		var OVERLAY_STYLE =
			"position:fixed;top:0;right:0;bottom:0;left:0;z-index:9999;" +
			"display:flex;align-items:center;justify-content:center;padding:16px;";
		var BACKDROP_STYLE =
			"position:absolute;top:0;right:0;bottom:0;left:0;" +
			"background:rgba(15,23,42,0.4);backdrop-filter:blur(4px);";
		var BOX_STYLE =
			"position:relative;background:#fff;width:100%;max-width:540px;" +
			"border-radius:4px;box-shadow:0 25px 50px rgba(0,0,0,.25);overflow:hidden;";

		var html = `
		<div class="kt-wbench-modal-overlay" style="${OVERLAY_STYLE}" data-testid="kt-wbench-edit-budget-overlay">
			<div class="kt-wbench-modal-backdrop" style="${BACKDROP_STYLE}" data-testid="kt-wbench-edit-budget-backdrop"></div>
			<div class="kt-wbench-modal-box" style="${BOX_STYLE}" role="dialog" aria-modal="true">
				<div class="kt-wbench-modal-hdr" style="padding:16px 24px;border-bottom:1px solid #c6c6cd;background:#f2f4f6;display:flex;justify-content:space-between;align-items:center;">
					<span style="font-size:18px;line-height:26px;font-weight:600;color:#000;font-family:'Manrope',sans-serif;">Edit Budget</span>
					<button class="kt-eb-close" aria-label="Close"
						style="padding:4px;background:transparent;border:none;border-radius:4px;cursor:pointer;color:#45464d;display:flex;align-items:center;">
						<span class="material-symbols-outlined" style="font-size:20px">close</span>
					</button>
				</div>
				<div class="kt-wbench-modal-body"
					style="padding:24px;display:flex;flex-direction:column;gap:16px;max-height:calc(80vh - 130px);overflow-y:auto;">
					<div data-role="kt-eb-api-error"
						style="display:none;align-items:flex-start;gap:10px;padding:10px 14px;
						       background:#fff8f7;border:1px solid #f5c2bb;border-radius:4px;
						       font-size:13px;color:#ba1a1a;line-height:1.45;">
						<span class="material-symbols-outlined" style="font-size:16px;flex-shrink:0;margin-top:1px">error</span>
						<span data-role="kt-eb-api-error-msg"></span>
					</div>
					${bodyHtml}
				</div>
				<div class="kt-wbench-modal-ftr"
					style="padding:16px 24px;border-top:1px solid #c6c6cd;background:#fff;display:flex;justify-content:flex-end;align-items:center;gap:16px;">
					<button class="kt-eb-cancel"
						style="padding:8px 20px;background:transparent;border:none;cursor:pointer;font-size:12px;font-weight:700;letter-spacing:.05em;color:#45464d;font-family:'Inter',sans-serif;">Cancel</button>
					<button class="kt-eb-submit" data-testid="kt-wbench-edit-budget-submit"
						style="padding:8px 24px;background:#0f172a;color:#fff;border:none;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.05em;cursor:pointer;font-family:'Inter',sans-serif;">
						Save Changes
					</button>
				</div>
			</div>
		</div>`;

		var el = document.createElement("div");
		el.innerHTML = html;
		var overlay = el.firstElementChild;
		document.body.appendChild(overlay);

		var submitBtn = overlay.querySelector(".kt-eb-submit");

		function _close() {
			if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
		}

		function _showErr(field, msg) {
			var span = overlay.querySelector("[data-err='" + field + "']");
			if (span) { span.textContent = msg; span.style.display = msg ? "block" : "none"; }
		}

		function _showInlineError(msg) {
			var banner = overlay.querySelector("[data-role='kt-eb-api-error']");
			var msgEl  = overlay.querySelector("[data-role='kt-eb-api-error-msg']");
			if (!banner || !msgEl) return;
			msgEl.textContent = msg;
			banner.style.display = "flex";
		}

		function _setSubmitting(busy) {
			submitBtn.disabled = busy;
			submitBtn.textContent = busy ? "Saving…" : "Save Changes";
		}

		overlay.querySelector(".kt-eb-close").addEventListener("click", _close);
		overlay.querySelector(".kt-eb-cancel").addEventListener("click", _close);
		overlay.querySelector("[data-testid='kt-wbench-edit-budget-backdrop']").addEventListener("click", _close);

		submitBtn.addEventListener("click", function () {
			var name  = (overlay.querySelector("[name='budget_display_name']").value || "").trim();
			var fy    = overlay.querySelector("[name='fiscal_year']").value;
			var cur   = overlay.querySelector("[name='currency']").value;
			var effD  = overlay.querySelector("[name='effective_date']").value || null;
			var clsD  = overlay.querySelector("[name='closing_date']").value || null;

			var valid = true;
			if (!name)  { _showErr("budget_display_name", "Budget Name is required."); valid = false; }
			if (!fy)    { _showErr("fiscal_year", "Fiscal Year is required."); valid = false; }
			if (!valid) return;

			_setSubmitting(true);
			frappe.call({
				method: "kentender_budget.api.approval.update_budget",
				args: {
					budget_name:          budget.name,
					budget_display_name:  name,
					fiscal_year:          parseInt(fy, 10),
					currency:             cur,
					effective_date:       effD,
					closing_date:         clsD,
				},
				always_callback: true,
				callback: function (r) {
					if (r && r.message) {
						_close();
						_loadBuilderData(_wrapper, budget.name);
					}
				},
				error: function (r) {
					_setSubmitting(false);
					var raw = (r && r.responseJSON && r.responseJSON.exception)
					          || (r && r.message) || "Could not save.";
					var lines = String(raw).split("\n").map(function (l) { return l.trim(); }).filter(Boolean);
					_showInlineError(lines[lines.length - 1] || raw);
				},
			});
		});
	}

	// ── Interactions ──────────────────────────────────────────────────────────

	function _bindInteractions(wrapper) {
		// Back to Budget Hub
		wrapper.addEventListener("click", function (e) {
			const backBtn = e.target.closest("[data-wbench='back-link']");
			if (!backBtn) return;
			e.preventDefault();
			frappe.set_route("budget-hub");
		});

		// "Edit Budget" — opens header edit modal (Draft / Rejected only)
		wrapper.addEventListener("click", function (e) {
			if (!e.target.closest("[data-wbench='edit-budget-btn']")) return;
			if (_budgetData) _showEditBudgetModal(_budgetData);
		});

		// Filter pills — client-side filter on already-loaded _lines
		wrapper.addEventListener("click", function (e) {
			const pill = e.target.closest("[data-filter]");
			if (!pill) return;
			_lineFilter = pill.dataset.filter || "all";
			_refreshFilterPills(wrapper);
			_applyLineFilter(wrapper);
		});

		// ── Revision workflow action buttons ─────────────────────────────────

		// "View Changes" banner button — opens the diff modal
		wrapper.addEventListener("click", function (e) {
			if (!e.target.closest("[data-wbench='view-changes-btn']")) return;
			_openRevisionDiffModal(_budgetData);
		});

		// "Revise Budget" — creates a Draft revision and navigates to it
		wrapper.addEventListener("click", function (e) {
			if (!e.target.closest("[data-wbench='revise-btn']")) return;
			const btn = e.target.closest("[data-wbench='revise-btn']");
			btn.disabled = true;
			btn.textContent = "Creating revision…";
			frappe.call({
				method: "kentender_budget.api.revision.request_revision",
				args:   { budget_name: _budgetData && _budgetData.name },
				callback: function (r) {
					btn.disabled = false;
					if (r && r.message && r.message.name) {
						frappe.show_alert({ message: "Revision created.", indicator: "green" });
						frappe.set_route("budget-workbench", r.message.name);
					}
				},
				error: function (r) {
					btn.disabled = false;
					btn.innerHTML = '<span class="material-symbols-outlined">edit_square</span>Revise Budget';
					var msg = (r && r.message) ? r.message : "Could not create revision.";
					frappe.msgprint({ message: msg, title: "Error", indicator: "red" });
				},
			});
		});

		// "Submit Revision"
		wrapper.addEventListener("click", function (e) {
			if (!e.target.closest("[data-wbench='submit-revision-btn']")) return;
			frappe.call({
				method: "kentender_budget.api.revision.submit_revision",
				args:   { budget_name: _budgetData && _budgetData.name },
				callback: function () {
					frappe.show_alert({ message: "Revision submitted for approval.", indicator: "green" });
					_loadBuilderData(wrapper, _budgetData && _budgetData.name);
				},
				error: function (r) {
					frappe.msgprint({ message: (r && r.message) || "Could not submit revision.", title: "Error", indicator: "red" });
				},
			});
		});

		// "Approve Revision"
		wrapper.addEventListener("click", function (e) {
			if (!e.target.closest("[data-wbench='approve-revision-btn']")) return;
			frappe.confirm(
				"Approve this revision? It will become the new Active budget and the predecessor will be locked as Revised.",
				function () {
					frappe.call({
						method: "kentender_budget.api.revision.approve_revision",
						args:   { budget_name: _budgetData && _budgetData.name },
						callback: function () {
							frappe.show_alert({ message: "Revision approved and activated.", indicator: "green" });
							_loadBuilderData(wrapper, _budgetData && _budgetData.name);
						},
						error: function (r) {
							frappe.msgprint({ message: (r && r.message) || "Could not approve revision.", title: "Error", indicator: "red" });
						},
					});
				}
			);
		});

		// "Return" revision
		wrapper.addEventListener("click", function (e) {
			if (!e.target.closest("[data-wbench='return-revision-btn']")) return;
			frappe.prompt(
				[{ fieldname: "reason", label: "Return Reason", fieldtype: "Small Text", reqd: 1 }],
				function (vals) {
					frappe.call({
						method: "kentender_budget.api.revision.return_revision",
						args:   { budget_name: _budgetData && _budgetData.name, reason: vals.reason },
						callback: function () {
							frappe.show_alert({ message: "Revision returned for correction.", indicator: "orange" });
							_loadBuilderData(wrapper, _budgetData && _budgetData.name);
						},
						error: function (r) {
							frappe.msgprint({ message: (r && r.message) || "Could not return revision.", title: "Error", indicator: "red" });
						},
					});
				},
				"Return Revision",
				"Return"
			);
		});

		// "Cancel Revision"
		wrapper.addEventListener("click", function (e) {
			if (!e.target.closest("[data-wbench='cancel-revision-btn']")) return;
			frappe.confirm(
				"Cancel this revision? It cannot be undone.",
				function () {
					frappe.call({
						method: "kentender_budget.api.revision.cancel_revision",
						args:   { budget_name: _budgetData && _budgetData.name },
						callback: function () {
							frappe.show_alert({ message: "Revision cancelled.", indicator: "orange" });
							_loadBuilderData(wrapper, _budgetData && _budgetData.name);
						},
						error: function (r) {
							frappe.msgprint({ message: (r && r.message) || "Could not cancel revision.", title: "Error", indicator: "red" });
						},
					});
				}
			);
		});

		// ── Original budget (non-revision) workflow buttons ──────────────────

		// "Submit for Approval" — Draft → Submitted
		wrapper.addEventListener("click", function (e) {
			if (!e.target.closest("[data-wbench='submit-btn']")) return;
			const btn = e.target.closest("[data-wbench='submit-btn']");
			btn.disabled = true;
			btn.textContent = "Submitting…";
			frappe.call({
				method: "kentender_budget.api.approval.submit_budget",
				args:   { budget_name: _budgetData && _budgetData.name },
				callback: function () {
					frappe.show_alert({ message: "Budget submitted for approval.", indicator: "green" });
					_loadBuilderData(wrapper, _budgetData && _budgetData.name);
				},
				error: function () {
					btn.disabled = false;
					btn.innerHTML = '<span class="material-symbols-outlined">send</span>Submit for Approval';
				},
			});
		});

		// "Approve" — Submitted → Approved
		wrapper.addEventListener("click", function (e) {
			if (!e.target.closest("[data-wbench='approve-btn']")) return;
			frappe.confirm(
				"Approve this budget? It will move to Approved status and can then be activated.",
				function () {
					frappe.call({
						method: "kentender_budget.api.approval.approve_budget",
						args:   { budget_name: _budgetData && _budgetData.name },
						callback: function () {
							frappe.show_alert({ message: "Budget approved.", indicator: "green" });
							_loadBuilderData(wrapper, _budgetData && _budgetData.name);
						},
						error: function (r) {
							frappe.msgprint({ message: (r && r.message) || "Could not approve budget.", title: "Error", indicator: "red" });
						},
					});
				}
			);
		});

		// "Reject" — Submitted → Rejected (reason required)
		wrapper.addEventListener("click", function (e) {
			if (!e.target.closest("[data-wbench='reject-btn']")) return;
			frappe.prompt(
				[{ fieldname: "reason", label: "Rejection Reason", fieldtype: "Small Text", reqd: 1 }],
				function (vals) {
					frappe.call({
						method: "kentender_budget.api.approval.reject_budget",
						args:   { budget_name: _budgetData && _budgetData.name, rejection_reason: vals.reason },
						callback: function () {
							frappe.show_alert({ message: "Budget rejected and returned to officer.", indicator: "orange" });
							_loadBuilderData(wrapper, _budgetData && _budgetData.name);
						},
						error: function (r) {
							frappe.msgprint({ message: (r && r.message) || "Could not reject budget.", title: "Error", indicator: "red" });
						},
					});
				},
				"Reject Budget",
				"Reject"
			);
		});

		// "Activate Budget" — Approved → Active
		wrapper.addEventListener("click", function (e) {
			if (!e.target.closest("[data-wbench='activate-btn']")) return;
			frappe.confirm(
				"Activate this budget? It will become live and available for reservations.",
				function () {
					frappe.call({
						method: "kentender_budget.api.approval.activate_budget",
						args:   { budget_name: _budgetData && _budgetData.name },
						callback: function () {
							frappe.show_alert({ message: "Budget activated.", indicator: "green" });
							_loadBuilderData(wrapper, _budgetData && _budgetData.name);
						},
						error: function (r) {
							frappe.msgprint({ message: (r && r.message) || "Could not activate budget.", title: "Error", indicator: "red" });
						},
					});
				}
			);
		});

		// "Resubmit for Approval" — Rejected → Submitted
		wrapper.addEventListener("click", function (e) {
			if (!e.target.closest("[data-wbench='resubmit-btn']")) return;
			const btn = e.target.closest("[data-wbench='resubmit-btn']");
			btn.disabled = true;
			btn.textContent = "Resubmitting…";
			frappe.call({
				method: "kentender_budget.api.approval.submit_budget",
				args:   { budget_name: _budgetData && _budgetData.name },
				callback: function () {
					frappe.show_alert({ message: "Budget resubmitted for approval.", indicator: "green" });
					_loadBuilderData(wrapper, _budgetData && _budgetData.name);
				},
				error: function () {
					btn.disabled = false;
					btn.innerHTML = '<span class="material-symbols-outlined">send</span>Resubmit for Approval';
				},
			});
		});

		// Line card click → activate + load artefacts on-demand
		wrapper.addEventListener("click", function (e) {
			const card = e.target.closest("[data-line-idx]");
			if (!card) return;

			const idx  = parseInt(card.dataset.lineIdx, 10);
			const line = _lines[idx];
			if (!line) return;

			// Rebuild all cards with new active state
			const list = wrapper.querySelector("[data-testid='kt-wbench-lines-list']");
			if (list) {
				list.innerHTML = _lines
					.map(function (l, i) { return _buildLineCard(l, i === idx, i); })
					.join("");
			}

		// Fetch and render Zone 3 for the selected line
		_loadArtefacts(wrapper, line);
	});

	// "Add Budget Line" button → open create modal
	wrapper.addEventListener("click", function (e) {
		if (!e.target.closest(".kt-wbench-btn-add")) return;

		// Resolve the budget name from the rendered header for the context chip
		const titleEl  = wrapper.querySelector("[data-testid='kt-wbench-budget-name']");
		const ctxLabel = (titleEl && titleEl.textContent.trim()) || null;

		_showBudgetLineModal({
			title:        "Add Budget Line",
			contextLabel: ctxLabel,
			primaryLabel: "Add Line",
			onSubmit: function (vals, close, setError, setApiError, setSubmitting) {
				setSubmitting(true);
				frappe.call({
					method: "kentender_budget.api.builder.upsert_budget_line",
					args: {
						budget_name:             _budgetData && _budgetData.name,
						budget_line_name:        vals.budget_line_name,
						amount_allocated:        parseFloat(vals.amount_allocated) || 0,
						economic_classification: vals.economic_classification || null,
						department:              vals.department              || null,
						funding_source:          vals.funding_source          || null,
						program:                 vals.program                 || null,
						sub_program:             vals.sub_program             || null,
						output_indicator:        vals.output_indicator        || null,
						performance_target:      vals.performance_target      || null,
						notes:                   vals.notes                   || null,
					},
			callback: function () {
					setSubmitting(false);
					close();
					frappe.show_alert({ message: "Budget line added.", indicator: "green" });
					_loadBuilderData(wrapper, _budgetData && _budgetData.name);
				},
					error: function (r) {
						setSubmitting(false);
						var msg = (r && r.exc_type) ? r.exc_type + ": " : "";
						msg += (r && r.message) ? r.message
							: (r && r.exception ? r.exception : "Could not save budget line.");
						setApiError(msg);
					},
				});
			},
		});
	});

	// "Open Line" button → open edit modal pre-populated with the line's values
	wrapper.addEventListener("click", function (e) {
		const btn = e.target.closest("[data-line-act='open-line']");
		if (!btn) return;
		e.stopPropagation(); // don't also trigger the line-card selection handler

		const idx  = parseInt(btn.dataset.lineIdx, 10);
		const line = _lines[idx];
		if (!line) return;

		const titleEl  = wrapper.querySelector("[data-testid='kt-wbench-budget-name']");
		const ctxLabel = (titleEl && titleEl.textContent.trim()) || null;

		_showBudgetLineModal({
			title:        "Edit Budget Line",
			contextLabel: ctxLabel,
			defaults: {
				budget_line_name:       line.budget_line_name    || "",
				amount_allocated:       line.amount_allocated    || 0,
				economic_classification: line.economic_classification || "",
				department:             line.department           || "",
				funding_source:         line.funding_source       || "",
				program:                line.program              || "",
				sub_program:            line.sub_program          || "",
				output_indicator:       line.output_indicator     || "",
				performance_target:     line.performance_target   || "",
				notes:                  line.notes                || "",
			},
		primaryLabel: "Save Changes",
		onSubmit: function (vals, close, setError, setApiError, setSubmitting) {
			setSubmitting(true);
			frappe.call({
				method: "kentender_budget.api.builder.upsert_budget_line",
				args: {
					budget_name:             _budgetData && _budgetData.name,
					budget_line_id:          line.name,
					budget_line_name:        vals.budget_line_name,
					amount_allocated:        parseFloat(vals.amount_allocated) || 0,
					economic_classification: vals.economic_classification || null,
					department:              vals.department              || null,
					funding_source:          vals.funding_source          || null,
					program:                 vals.program                 || null,
					sub_program:             vals.sub_program             || null,
					output_indicator:        vals.output_indicator        || null,
					performance_target:      vals.performance_target      || null,
					notes:                   vals.notes                   || null,
				},
				callback: function () {
					setSubmitting(false);
					close();
					frappe.show_alert({ message: "Budget line updated.", indicator: "green" });
					_loadBuilderData(wrapper, _budgetData && _budgetData.name);
				},
				error: function () {
					setSubmitting(false);
					// Frappe already shows the server error message automatically;
					// just reset the button state — no duplicate inline banner needed.
				},
			});
		},
		});
	});
}

	// ── Budget Line Modal ─────────────────────────────────────────────────────
	// Matches the Strategy Builder indicator/target modal pattern exactly:
	// overlay → backdrop + box → hdr / body (scrollable) / ftr.
	//
	// opts = {
	//   title       : string            — modal heading
	//   contextLabel: string|null       — grey context chip below header (e.g. budget name)
	//   defaults    : object            — pre-filled field values (edit mode)
	//   primaryLabel: string            — submit button text ("Add Line" / "Save Changes")
	//   onSubmit    : (values) => void  — called with collected form values on success
	// }
	//
	// Returns { overlay, close } for callers that need to close programmatically.

	function _showBudgetLineModal({ title, contextLabel, defaults = {}, primaryLabel, onSubmit }) {
		function esc(s) {
			const d = document.createElement("div");
			d.textContent = s == null ? "" : String(s);
			return d.innerHTML;
		}

		const ctxRow = contextLabel
			? `<div class="kt-wbench-modal-ctx"
				style="display:flex;align-items:center;gap:8px;padding:8px 16px;background:#f2f4f6;border:1px solid #c6c6cd;border-radius:4px;color:#45464d;font-size:13px;">
				<span class="material-symbols-outlined" style="font-size:16px">receipt_long</span>
				<span>${esc(contextLabel)}</span>
			</div>` : "";

		// ── Field HTML builders ──────────────────────────────────────────────
		const FIELD_WRAP  = "display:flex;flex-direction:column;";
		const LBL_STYLE   = "display:block;font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#45464d;margin-bottom:6px;font-family:'Inter',sans-serif;";
		const INPUT_STYLE = "width:100%;background:#f1f5f9;border:1px solid transparent;border-radius:4px;padding:8px 12px;font-size:13px;font-family:'Inter',sans-serif;color:#191c1e;outline:none;box-sizing:border-box;";
		const ERR_STYLE   = "font-size:11px;color:#ba1a1a;margin-top:4px;display:none;";

		function textField(name, label, opts) {
			const id  = "ktwm_" + name;
			const req = opts.required ? `<span style="color:#ba1a1a"> *</span>` : "";
			const val = defaults[name] != null ? esc(defaults[name]) : "";
			return `<div class="kt-wbench-modal-field" style="${FIELD_WRAP}" data-field="${name}">
				<label class="kt-wbench-modal-lbl" style="${LBL_STYLE}" for="${id}">${esc(label)}${req}</label>
				<input id="${id}" name="${name}" type="text"
					class="kt-wbench-modal-input" style="${INPUT_STYLE}"
					value="${val}"
					placeholder="${esc(opts.placeholder || "")}">
				<span class="kt-wbench-modal-error" style="${ERR_STYLE}" data-err="${name}"></span>
			</div>`;
		}

		function numberField(name, label, opts) {
			const id  = "ktwm_" + name;
			const req = opts.required ? `<span style="color:#ba1a1a"> *</span>` : "";
			const val = defaults[name] != null ? esc(String(defaults[name])) : "0";
			return `<div class="kt-wbench-modal-field" style="${FIELD_WRAP}" data-field="${name}">
				<label class="kt-wbench-modal-lbl" style="${LBL_STYLE}" for="${id}">${esc(label)}${req}</label>
				<input id="${id}" name="${name}" type="number" min="0" step="any"
					class="kt-wbench-modal-input" style="${INPUT_STYLE}"
					value="${val}"
					placeholder="0">
				<span class="kt-wbench-modal-error" style="${ERR_STYLE}" data-err="${name}"></span>
			</div>`;
		}

		function selectField(name, label, options, opts) {
			const id   = "ktwm_" + name;
			const req  = opts && opts.required ? `<span style="color:#ba1a1a"> *</span>` : "";
			const cur  = defaults[name] || "";
			const optsHtml = [{ value: "", label: "— Select —" }]
				.concat(options.map((o) => typeof o === "string" ? { value: o, label: o } : o))
				.map((o) => `<option value="${esc(o.value)}"${o.value === cur ? " selected" : ""}>${esc(o.label)}</option>`)
				.join("");
			return `<div class="kt-wbench-modal-field" style="${FIELD_WRAP}" data-field="${name}">
				<label class="kt-wbench-modal-lbl" style="${LBL_STYLE}" for="${id}">${esc(label)}${req}</label>
				<select id="${id}" name="${name}" class="kt-wbench-modal-select" style="${INPUT_STYLE}">${optsHtml}</select>
			</div>`;
		}

		function textareaField(name, label) {
			const id  = "ktwm_" + name;
			const val = defaults[name] != null ? esc(defaults[name]) : "";
			return `<div class="kt-wbench-modal-field" style="${FIELD_WRAP}" data-field="${name}">
				<label class="kt-wbench-modal-lbl" style="${LBL_STYLE}" for="${id}">${esc(label)}</label>
				<textarea id="${id}" name="${name}"
					class="kt-wbench-modal-textarea" style="${INPUT_STYLE}resize:vertical;min-height:72px;"
					placeholder="Optional notes">${val}</textarea>
			</div>`;
		}

		// ── Field definitions ─────────────────────────────────────────────────
		const econOptions = [
			"Works", "Goods", "Services", "Consultancy",
			"Non-Consultancy Services", "Other",
		];

		// Link fields start with a loading placeholder; populated after modal mounts
		// via frappe.db.get_list (see async loader below).
		const LINK_LOADING_OPT = `<option value="" disabled selected>Loading…</option>`;

		const bodyHtml = `
			${ctxRow}
			${textField("budget_line_name", "Budget Line Name",
				{ required: true, placeholder: "e.g. Health Infrastructure Works" })}
			<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
				${numberField("amount_allocated", "Amount Allocated (KES)", { required: true })}
				${selectField("economic_classification", "Economic Classification", econOptions, {})}
			</div>
			${textField("department", "Department / Cost Centre",
				{ placeholder: "e.g. Cost centre or department name" })}
			<div class="kt-wbench-modal-field" style="${FIELD_WRAP}" data-field="funding_source">
				<label class="kt-wbench-modal-lbl" style="${LBL_STYLE}" for="ktwm_funding_source">Funding Source</label>
				<select id="ktwm_funding_source" name="funding_source"
					class="kt-wbench-modal-select" style="${INPUT_STYLE}">
					${LINK_LOADING_OPT}
				</select>
			</div>
			${textareaField("notes", "Notes")}
		`;

		// Inline the critical layout styles on overlay + backdrop so the modal
		// renders correctly even when the CSS file is served from browser cache
		// (same technique Frappe uses for its own New Dialog).
		const OVERLAY_STYLE =
			"position:fixed;top:0;right:0;bottom:0;left:0;z-index:9999;" +
			"display:flex;align-items:center;justify-content:center;padding:16px;";
		const BACKDROP_STYLE =
			"position:absolute;top:0;right:0;bottom:0;left:0;" +
			"background:rgba(15,23,42,0.4);backdrop-filter:blur(4px);";
		const BOX_STYLE =
			"position:relative;background:#fff;width:100%;max-width:540px;" +
			"border-radius:4px;box-shadow:0 25px 50px rgba(0,0,0,.25);overflow:hidden;";

		const html = `
		<div class="kt-wbench-modal-overlay" style="${OVERLAY_STYLE}" data-testid="kt-wbench-modal-overlay">
			<div class="kt-wbench-modal-backdrop" style="${BACKDROP_STYLE}" data-testid="kt-wbench-modal-backdrop"></div>
			<div class="kt-wbench-modal-box" style="${BOX_STYLE}" data-testid="kt-wbench-modal-box" role="dialog" aria-modal="true" aria-labelledby="ktwm-title">
				<div class="kt-wbench-modal-hdr" style="padding:16px 24px;border-bottom:1px solid #c6c6cd;background:#f2f4f6;display:flex;justify-content:space-between;align-items:center;">
					<span class="kt-wbench-modal-title" id="ktwm-title" data-testid="kt-wbench-modal-title"
						style="font-size:18px;line-height:26px;font-weight:600;color:#000;font-family:'Manrope',sans-serif;">${esc(title)}</span>
					<button class="kt-wbench-modal-close" data-testid="kt-wbench-modal-close" aria-label="Close"
						style="padding:4px;background:transparent;border:none;border-radius:4px;cursor:pointer;color:#45464d;display:flex;align-items:center;">
						<span class="material-symbols-outlined" style="font-size:20px">close</span>
					</button>
				</div>
				<div class="kt-wbench-modal-body"
					style="padding:24px;display:flex;flex-direction:column;gap:16px;max-height:calc(80vh - 130px);overflow-y:auto;">
					<!-- API error banner — hidden until an API call fails -->
					<div data-role="kt-wbench-api-error"
						style="display:none;align-items:flex-start;gap:10px;padding:10px 14px;
						       background:#fff8f7;border:1px solid #f5c2bb;border-radius:4px;
						       font-size:13px;color:#ba1a1a;line-height:1.45;">
						<span class="material-symbols-outlined" style="font-size:16px;flex-shrink:0;margin-top:1px">error</span>
						<span data-role="kt-wbench-api-error-msg"></span>
					</div>
					${bodyHtml}
				</div>
				<div class="kt-wbench-modal-ftr"
					style="padding:16px 24px;border-top:1px solid #c6c6cd;background:#fff;display:flex;justify-content:flex-end;align-items:center;gap:16px;">
					<button class="kt-wbench-modal-cancel" data-testid="kt-wbench-modal-cancel"
						style="padding:8px 20px;background:transparent;border:none;cursor:pointer;font-size:12px;font-weight:700;letter-spacing:.05em;color:#45464d;font-family:'Inter',sans-serif;">Cancel</button>
					<button class="kt-wbench-modal-submit" data-testid="kt-wbench-modal-submit"
						style="padding:8px 24px;background:#0f172a;color:#fff;border:none;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.05em;cursor:pointer;font-family:'Inter',sans-serif;">
						${esc(primaryLabel || "Save")}
					</button>
				</div>
			</div>
		</div>`;

		// ── Mount ───────────────────────────────────────────────────────────

		const el = document.createElement("div");
		el.innerHTML = html;
		const overlay = el.firstElementChild;
		document.body.appendChild(overlay);

		// ── Async: populate Funding Source select ─────────────────────────────

		const fsSelect = overlay.querySelector("[name='funding_source']");

		function _fillSelect(selectEl, rows, valueFn, labelFn, currentVal) {
			if (!selectEl) return;
			const opts = [{ value: "", label: "— None —" }].concat(
				rows.map(function (r) { return { value: valueFn(r), label: labelFn(r) }; })
			);
			selectEl.innerHTML = opts
				.map(function (o) {
					const sel = (o.value === (currentVal || "")) ? " selected" : "";
					const d   = document.createElement("div");
					d.textContent = o.label;
					return `<option value="${o.value}"${sel}>${d.innerHTML}</option>`;
				})
				.join("");
		}

		// Funding Source — all active sources
		frappe.db.get_list("Funding Source", {
			filters: { is_active: 1 },
			fields:  ["name", "title", "source_code"],
			limit:   500,
		}).then(function (rows) {
			_fillSelect(
				fsSelect,
				rows,
				function (r) { return r.name; },
				function (r) { return r.title + (r.source_code ? " (" + r.source_code + ")" : ""); },
				defaults.funding_source || ""
			);
		}).catch(function () {
			if (fsSelect) {
				fsSelect.innerHTML = "<option value=''>— Could not load —</option>";
			}
		});

		// Auto-focus first input
		setTimeout(function () {
			const first = overlay.querySelector(".kt-wbench-modal-input");
			if (first) first.focus();
		}, 80);

		// Active label on focus
		overlay.querySelectorAll(".kt-wbench-modal-input, .kt-wbench-modal-select, .kt-wbench-modal-textarea")
			.forEach(function (inp) {
				inp.addEventListener("focus", function () {
					const lbl = overlay.querySelector("label[for='" + inp.id + "']");
					if (lbl) lbl.classList.add("active");
				});
				inp.addEventListener("blur", function () {
					const lbl = overlay.querySelector("label[for='" + inp.id + "']");
					if (lbl) lbl.classList.remove("active");
				});
			});

		// ── Helpers ─────────────────────────────────────────────────────────

		function getValues() {
			const vals = {};
			overlay.querySelectorAll("[name]").forEach(function (el) {
				vals[el.name] = el.tagName === "SELECT" ? el.value : (el.value || "").trim();
			});
			return vals;
		}

		function setError(fieldName, message) {
			const inp = overlay.querySelector("[name='" + fieldName + "']");
			const err = overlay.querySelector("[data-err='" + fieldName + "']");
			if (inp) { inp.style.borderColor = "#ba1a1a"; inp.style.boxShadow = "0 0 0 1px #ba1a1a"; }
			if (err) { err.textContent = message; err.style.display = "block"; }
		}

		function clearErrors() {
			overlay.querySelectorAll(".kt-wbench-modal-input, .kt-wbench-modal-select").forEach(function (el) {
				el.style.borderColor = "transparent";
				el.style.boxShadow   = "none";
			});
			overlay.querySelectorAll("[data-err]").forEach(function (el) {
				el.style.display = "none";
				el.textContent = "";
			});
		}

		// ── API error banner ─────────────────────────────────────────────────
		// Shown inside the modal body when the API call fails; modal stays open.

		var _apiBanner = overlay.querySelector("[data-role='kt-wbench-api-error']");
		var _apiBannerMsg = overlay.querySelector("[data-role='kt-wbench-api-error-msg']");

		function setApiError(msg) {
			if (!_apiBanner || !_apiBannerMsg) return;
			_apiBannerMsg.textContent = msg || "An unexpected error occurred. Please try again.";
			_apiBanner.style.display = "flex";
			// Scroll banner into view
			_apiBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
		}

		function clearApiError() {
			if (!_apiBanner) return;
			_apiBanner.style.display = "none";
			if (_apiBannerMsg) _apiBannerMsg.textContent = "";
		}

		// ── Submit button state ──────────────────────────────────────────────
		// setSubmitting(true)  — disables button, swaps label to spinner
		// setSubmitting(false) — restores original label text

		var _submitBtn = overlay.querySelector("[data-testid='kt-wbench-modal-submit']");
		var _submitBtnOriginalHtml = _submitBtn ? _submitBtn.innerHTML : "";

		function setSubmitting(submitting) {
			if (!_submitBtn) return;
			if (submitting) {
				_submitBtn.disabled = true;
				_submitBtn.style.opacity = "0.75";
				_submitBtn.innerHTML =
					"<span class='material-symbols-outlined' " +
					"style='font-size:15px;animation:kt-wbench-spin 1s linear infinite;'>progress_activity</span>" +
					"&nbsp;Saving…";
			} else {
				_submitBtn.disabled = false;
				_submitBtn.style.opacity = "";
				_submitBtn.innerHTML = _submitBtnOriginalHtml;
			}
		}

		// ── Close ────────────────────────────────────────────────────────────

		function close() {
			if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
			document.removeEventListener("keydown", onKey);
		}

		function onKey(e) { if (e.key === "Escape") close(); }
		document.addEventListener("keydown", onKey);

		overlay.querySelector("[data-testid='kt-wbench-modal-backdrop']").addEventListener("click", close);
		overlay.querySelector("[data-testid='kt-wbench-modal-close']").addEventListener("click", close);
		overlay.querySelector("[data-testid='kt-wbench-modal-cancel']").addEventListener("click", close);

		// ── Submit ───────────────────────────────────────────────────────────

		overlay.querySelector("[data-testid='kt-wbench-modal-submit']").addEventListener("click", function () {
			clearErrors();
			clearApiError();
			const vals = getValues();

			// Inline required-field validation
			let hasError = false;
			if (!vals.budget_line_name) {
				setError("budget_line_name", "Budget Line Name is required.");
				hasError = true;
			}
			if (vals.amount_allocated === "" || isNaN(Number(vals.amount_allocated)) || Number(vals.amount_allocated) < 0) {
				setError("amount_allocated", "Enter a valid amount (0 or greater).");
				hasError = true;
			}
			if (hasError) return;

			if (typeof onSubmit === "function") onSubmit(vals, close, setError, setApiError, setSubmitting);
		});

		// Enter submits (except textarea)
		overlay.addEventListener("keydown", function (e) {
			if (e.key === "Enter" && e.target.tagName !== "TEXTAREA") {
				overlay.querySelector("[data-testid='kt-wbench-modal-submit']").click();
			}
		});

		// Reset error highlight on any input change
		overlay.querySelectorAll(".kt-wbench-modal-input, .kt-wbench-modal-select").forEach(function (el) {
			el.addEventListener("input", function () {
				el.style.borderColor = "transparent";
				el.style.boxShadow   = "none";
				const err = overlay.querySelector("[data-err='" + el.name + "']");
				if (err) { err.style.display = "none"; err.textContent = ""; }
			});
		});

		return { overlay, close, getValues, setError, clearErrors, setApiError, clearApiError, setSubmitting };
	}

	// ── Mount ─────────────────────────────────────────────────────────────────


	function _mount(wrapper) {
		_ensureFonts();
		if (!wrapper) return;
		if (wrapper.querySelector(".kt-wbench")) return; // already mounted

		const route      = frappe.get_route ? frappe.get_route() : [];
		const budgetName = route[1] || null;

		wrapper.innerHTML = _html(budgetName);
		_bindInteractions(wrapper);

		// Kick off Zone 1 + Zone 2 live data — runs async, fills skeleton in-place
		_loadBuilderData(wrapper, budgetName);
	}

	// ── Frappe page registration ──────────────────────────────────────────────
	frappe.pages["budget-workbench"].on_page_load = function (wrapper) {
		_mount(wrapper);
	};

	frappe.pages["budget-workbench"].on_page_show = function (wrapper) {
		document.body.classList.add("kt-wbench-shell");

		// Defer sidebar setup to next tick so Frappe's own reset completes first.
		setTimeout(function () {
			if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
				frappe.app.sidebar.setup("Procurement");
			}
		}, 0);

		const route      = frappe.get_route ? frappe.get_route() : [];
		const budgetName = route[1] || null;

		const existing = wrapper.querySelector(".kt-wbench");
		if (existing) {
			// Budget name may have changed (user opened a different budget).
			// Reload Zone 1 from the API with the new name.
			const crumbEl = wrapper.querySelector("[data-testid='kt-wbench-budget-name']");
			if (crumbEl && budgetName) crumbEl.textContent = budgetName;

			// Re-apply skeleton so user sees the load state while new data arrives
			const z1 = wrapper.querySelector("[data-testid='kt-wbench-zone1']");
			if (z1 && budgetName) {
				wrapper.querySelectorAll(
					"[data-testid='kt-wbench-title']," +
					"[data-testid='kt-wbench-approved']," +
					"[data-testid='kt-wbench-available']," +
					"[data-testid='kt-wbench-reserved']," +
					"[data-testid='kt-wbench-committed']"
				).forEach(function (el) { el.classList.add("kt-wbench-skel"); });
				z1.setAttribute("data-loading", "true");
				_loadBuilderData(wrapper, budgetName);
			}
		} else {
			_mount(wrapper);
		}
	};

	frappe.pages["budget-workbench"].on_page_hide = function () {
		document.body.classList.remove("kt-wbench-shell");
	};

})();
