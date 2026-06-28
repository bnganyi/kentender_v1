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

	// Budget header payload from the last successful _loadBuilderData call.
	// Used by the modal to filter Programme options by strategic_plan.
	let _budgetData = null;


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
		return "kt-wbench-status-pill--draft";
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

		// KPI summary cards
		const approved  = budget.total_budget_amount || 0;
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

		if (!_lines.length) {
			list.innerHTML = '<p class="kt-wbench-lines-empty">No active budget lines.</p>';
			return;
		}

	list.innerHTML = _lines.map(function (line, i) {
		return _buildLineCard(line, i === 0, i);
	}).join("");

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

	// Single API call that populates both Zone 1 and Zone 2.
	function _loadBuilderData(wrapper, budgetName) {
		if (!budgetName) return;
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
		if (s.includes("active"))    return "kt-wbench-line-status--active";
		if (s.includes("commit"))    return "kt-wbench-line-status--committed";
		if (s.includes("reserved"))  return "kt-wbench-line-status--reserved";
		if (s.includes("exhaust"))   return "kt-wbench-line-status--exhausted";
		return "kt-wbench-line-status--active";
	}

	function _buildLineCard(line, isActive, idx) {
		const activeCls = isActive ? "kt-wbench-line-card--active" : "";
		const activeBtn = isActive
			? `<button class="kt-wbench-line-btn" data-line-act="open-line" data-line-idx="${idx}">Open Line</button>
			   <button class="kt-wbench-line-btn">Reserve Funds</button>
			   <button class="kt-wbench-line-btn kt-wbench-line-btn--highlight">View Linked Artefacts</button>`
			: `<button class="kt-wbench-line-btn" data-line-act="open-line" data-line-idx="${idx}">Open Line</button>
			   <button class="kt-wbench-line-btn">View Linked Artefacts</button>`;

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
		const status      = line.line_status             || (line.is_active ? "Active" : "Inactive");

		return `<div class="kt-wbench-line-card ${activeCls}" data-line-idx="${line.idx}" data-line-name="${line.name}" data-testid="kt-wbench-line-card">
			<div class="kt-wbench-line-card-head">
				<div>
					<h4 class="kt-wbench-line-name">${title}</h4>
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
				${activeBtn}
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
				<button class="kt-wbench-btn kt-wbench-btn-ghost">
					<span class="material-symbols-outlined">edit_square</span>
					Revise Budget
				</button>
				<button class="kt-wbench-btn kt-wbench-btn-ghost">
					<span class="material-symbols-outlined">cancel</span>
					Close Budget
				</button>
				<button class="kt-wbench-btn kt-wbench-btn-primary">
					<span class="material-symbols-outlined">visibility</span>
					View Evidence
				</button>
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
					<button class="kt-wbench-btn-filter">
						<span class="material-symbols-outlined">filter_list</span>
						All Lines
					</button>
					<button class="kt-wbench-btn-add">
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

	// ── Interactions ──────────────────────────────────────────────────────────

	function _bindInteractions(wrapper) {
		// Back to Budget Hub
		wrapper.addEventListener("click", function (e) {
			const backBtn = e.target.closest("[data-wbench='back-link']");
			if (!backBtn) return;
			e.preventDefault();
			frappe.set_route("budget-hub");
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

	// "Add Budget Line" button → open create modal (static shell; W6-05 wires save)
	wrapper.addEventListener("click", function (e) {
		if (!e.target.closest(".kt-wbench-btn-add")) return;

		// Resolve the budget name from the rendered header for the context chip
		const titleEl  = wrapper.querySelector("[data-testid='kt-wbench-budget-name']");
		const ctxLabel = (titleEl && titleEl.textContent.trim()) || null;

		_showBudgetLineModal({
			title:        "Add Budget Line",
			contextLabel: ctxLabel,
			primaryLabel: "Add Line",
			onSubmit: function (vals, close /*, setError */) {
				// W6-05: call upsert_budget_line here; for now stub with alert
				frappe.show_alert({ message: "Save wired in W6-05", indicator: "blue" });
				close();
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
				notes:                  line.notes                || "",
			},
			primaryLabel: "Save Changes",
			onSubmit: function (vals, close /*, setError */) {
				// W6-05: call upsert_budget_line with budget_line_id = line.name
				frappe.show_alert({ message: "Save wired in W6-05", indicator: "blue" });
				close();
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
			<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
				<div class="kt-wbench-modal-field" style="${FIELD_WRAP}" data-field="funding_source">
					<label class="kt-wbench-modal-lbl" style="${LBL_STYLE}" for="ktwm_funding_source">Funding Source</label>
					<select id="ktwm_funding_source" name="funding_source"
						class="kt-wbench-modal-select" style="${INPUT_STYLE}">
						${LINK_LOADING_OPT}
					</select>
				</div>
				<div class="kt-wbench-modal-field" style="${FIELD_WRAP}" data-field="program">
					<label class="kt-wbench-modal-lbl" style="${LBL_STYLE}" for="ktwm_program">Programme</label>
					<select id="ktwm_program" name="program"
						class="kt-wbench-modal-select" style="${INPUT_STYLE}">
						${LINK_LOADING_OPT}
					</select>
				</div>
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

		// ── Async: populate Funding Source and Programme selects ─────────────
		// Both selects start with a "Loading…" placeholder; we fire two parallel
		// frappe.db.get_list calls and replace the options once they arrive.
		// After both settle, pre-populate defaults if we are in edit mode.

		const fsSelect  = overlay.querySelector("[name='funding_source']");
		const prgSelect = overlay.querySelector("[name='program']");
		const strategicPlan = (_budgetData && _budgetData.strategic_plan) || null;

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

		// Programme — filtered by budget's strategic_plan when available
		var prgFilters = strategicPlan
			? [["strategic_plan", "=", strategicPlan]]
			: [];

		frappe.db.get_list("Strategy Program", {
			filters: prgFilters,
			fields:  ["name", "program_title", "program_code", "strategic_plan"],
			limit:   500,
		}).then(function (rows) {
			_fillSelect(
				prgSelect,
				rows,
				function (r) { return r.name; },
				function (r) {
					return r.program_title + (r.program_code ? " (" + r.program_code + ")" : "");
				},
				defaults.program || ""
			);
		}).catch(function () {
			if (prgSelect) {
				prgSelect.innerHTML = "<option value=''>— Could not load —</option>";
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
			const vals = getValues();

			// Inline required-field validation (W6-05 will extend for API errors)
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

			// W6-05: onSubmit will call upsert_budget_line and close on success
			if (typeof onSubmit === "function") onSubmit(vals, close, setError);
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

		return { overlay, close, getValues, setError, clearErrors };
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
				frappe.app.sidebar.setup("Budget Management");
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
