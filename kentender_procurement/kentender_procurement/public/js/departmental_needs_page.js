// NDS-UI-01 — high-fidelity hand-port of docs/mvp-1-r1/01_departmental_needs/NDS-UI-01.html.
// The existing KenTender shell owns navigation; this fixture owns the live main canvas.
(function () {
	"use strict";

	const PAGE = "departmental-needs";
	const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function dateLabel(iso) {
		if (!iso) return "—";
		const d = new Date(`${iso}T00:00:00`);
		if (Number.isNaN(d.getTime())) return esc(iso);
		return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
	}

	function statusTone(value) {
		if (value === "Accepted for planning") return "accepted";
		if (value === "Submitted") return "reserved";
		if (value === "Returned" || value === "Not taken forward") return "error";
		return "neutral";
	}

	function statusLabel(value) {
		return value === "Accepted for planning" ? "Accepted" : value;
	}

	function usageTone(value) {
		if (value === "Fully included") return "committed";
		if (value === "Partially included") return "reserved";
		return "neutral";
	}

	function pill(label, tone) {
		return `<span class="kt-nds-pill kt-nds-pill--${tone}">${esc(label)}</span>`;
	}

	function usagePill(value) {
		const tone = usageTone(value);
		return `<span class="kt-nds-pill kt-nds-pill--pill kt-nds-pill--${tone}"><span class="kt-nds-pill-dot" aria-hidden="true"></span>${esc(value)}</span>`;
	}

	function summaryCard(testid, tone, label, value) {
		return `<div class="kt-nds-card" data-testid="${esc(testid)}">
			<span class="kt-nds-card-bar kt-nds-card-bar--${tone}" aria-hidden="true"></span>
			<span class="kt-nds-card-label">${esc(label)}</span>
			<strong class="kt-nds-card-value">${esc(value || 0)}</strong>
		</div>`;
	}

	function rowAction(row) {
		const action = (row.actions || [])[0];
		if (!action) return "";
		return `<button type="button" class="text-primary kt-nds-row-action" data-nds-action="${esc(action.code)}" data-need="${esc(row.name)}">
			${esc(action.label)}<span class="material-symbols-outlined" aria-hidden="true">arrow_forward</span>
		</button>`;
	}

	function emptyRow(colspan, copy) {
		return `<tr class="kt-nds-empty-row"><td colspan="${colspan}"><div class="kt-nds-empty">${esc(copy)}</div></td></tr>`;
	}

	function workRows(rows) {
		if (!rows.length) return emptyRow(6, "No work is awaiting departmental review.");
		return rows.map((row) => `
			<tr>
				<td class="kt-nds-td-ref">${esc(row.reference)}</td>
				<td class="kt-nds-td-primary">${esc(row.title)}</td>
				<td class="kt-nds-td-muted">${esc(row.submitted_by)}</td>
				<td class="kt-nds-td-muted">${dateLabel(row.required_by)}</td>
				<td>${pill(statusLabel(row.status), statusTone(row.status))}</td>
				<td class="kt-nds-td-action">${rowAction(row)}</td>
			</tr>`).join("");
	}

	function needRows(rows) {
		if (!rows.length) return emptyRow(6, "No Departmental Needs match this context.");
		return rows.map((row) => `
			<tr class="${row.status === "Submitted" ? "kt-nds-tr--flag" : ""}">
				<td>
					<div class="kt-nds-need-title">${esc(row.title)}</div>
					<div class="kt-nds-need-ref">${esc(row.reference)}</div>
				</td>
				<td class="kt-nds-td-muted">${esc(row.indicative_requirement)}</td>
				<td class="kt-nds-td-muted">${dateLabel(row.required_by)}</td>
				<td>${pill(statusLabel(row.status), statusTone(row.status))}</td>
				<td>${usagePill(row.planning_usage)}</td>
				<td class="kt-nds-td-action">${rowAction(row)}</td>
			</tr>`).join("");
	}

	function contextOptions(contexts, selected) {
		return contexts.map((row) => {
			const isSelected = row.procuring_entity === selected.procuring_entity && row.organisation_unit === selected.organisation_unit;
			return `<option value="${esc(row.procuring_entity)}::${esc(row.organisation_unit)}"${isSelected ? " selected" : ""}>${esc(row.procuring_entity_label)} — ${esc(row.organisation_unit_label)}</option>`;
		}).join("");
	}

	function fyOptions(years, selected) {
		// The currently-viewed year may be a future year admitted only via the exact
		// seed fixture (outside the normal intake-window admission rule) — still show
		// it as the selected option so the control never silently disagrees with the
		// summary line above it.
		const rows = selected && !years.some((row) => row.id === selected) ? [{ id: selected, label: selected }, ...years] : years;
		return rows.map((row) => `<option value="${esc(row.id)}"${row.id === selected ? " selected" : ""}>${esc(row.label)}</option>`).join("");
	}

	// Custom Stitch-styled dialog — literal hand-port of NDS-UI-01-1.html's
	// modal (lines 503-546), appended inside the Stitch-scoped canvas rather
	// than via frappe.ui.Dialog (see planning_ui_fixtures/remove_plan_item_dialog.js
	// for the established convention this follows).
	function contextDialogHtml(data) {
		const c = data.context || {};
		return `<div class="kt-nds-context-dialog" data-kt-nds-context-dialog role="dialog" aria-modal="true" aria-labelledby="kt-nds-context-dialog-title">
			<div class="kt-nds-context-dialog-backdrop" data-kt-nds-context-dialog-backdrop></div>
			<div class="kt-nds-context-dialog-card">
				<div class="kt-nds-context-dialog-header">
					<h3 id="kt-nds-context-dialog-title" class="kt-nds-context-dialog-title">${esc(__("Change Departmental Needs context"))}</h3>
					<button type="button" class="kt-nds-context-dialog-close" aria-label="${esc(__("Close"))}" data-kt-nds-context-dialog-cancel>
						<span class="material-symbols-outlined" aria-hidden="true">close</span>
					</button>
				</div>
				<div class="kt-nds-context-dialog-body">
					<div class="kt-nds-context-field">
						<label class="kt-nds-field-label" for="kt-nds-context-pe-ou">${esc(__("Procuring Entity and department"))}</label>
						<select id="kt-nds-context-pe-ou" class="kt-nds-context-select-field" data-kt-nds-context-select>${contextOptions(data.contexts || [], c)}</select>
					</div>
					<div class="kt-nds-context-field">
						<label class="kt-nds-field-label" for="kt-nds-context-fy">${esc(__("Planning year"))}</label>
						<select id="kt-nds-context-fy" class="kt-nds-context-select-field" data-kt-nds-fy-select>${fyOptions(data.financial_years || [], c.financial_year)}</select>
					</div>
				</div>
				<div class="kt-nds-context-dialog-footer">
					<button type="button" class="kt-nds-context-dialog-cancel-btn" data-kt-nds-context-dialog-cancel>${esc(__("Cancel"))}</button>
					<button type="button" class="bg-primary" data-kt-nds-context-dialog-apply>${esc(__("Apply"))}</button>
				</div>
			</div>
		</div>`;
	}

	function openContextDialog(state) {
		const $body = window.jQuery && jQuery(state.body);
		if (!$body || !$body.length) return;
		// Append inside .kt-nds-root (not state.body directly) — the shared Stitch
		// button/select chrome and this file's --kt-nds-* variables are only in
		// scope for descendants of .kt-stitch-canvas.
		const $mount = $body.find(".kt-nds-root").first();
		if (!$mount.length) return;
		$mount.find("[data-kt-nds-context-dialog]").remove();
		const opener = document.activeElement;
		const $dialog = jQuery(contextDialogHtml(state.data)).appendTo($mount);

		function close() {
			$dialog.off(".ktNdsCtxDialog").remove();
			if (opener && document.contains(opener)) opener.focus();
		}
		$dialog.on("click.ktNdsCtxDialog", "[data-kt-nds-context-dialog-cancel], [data-kt-nds-context-dialog-backdrop]", close);
		$dialog.on("keydown.ktNdsCtxDialog", (event) => {
			if (event.key === "Escape") { event.preventDefault(); close(); return; }
			if (event.key !== "Tab") return;
			const nodes = $dialog.find("select:not(:disabled), button:not(:disabled)").filter(":visible").toArray();
			if (!nodes.length) return;
			const first = nodes[0], last = nodes[nodes.length - 1];
			if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
			else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
		});
		$dialog.on("click.ktNdsCtxDialog", "[data-kt-nds-context-dialog-apply]", () => {
			const [procuring_entity, organisation_unit] = String($dialog.find("[data-kt-nds-context-select]").val() || "").split("::");
			const financial_year = $dialog.find("[data-kt-nds-fy-select]").val() || "";
			if (!procuring_entity || !organisation_unit) return;
			close();
			applyContext(state, { procuring_entity, organisation_unit, financial_year });
		});
		$dialog.find("[data-kt-nds-context-select]").trigger("focus");
	}

	function tableFooterHtml() {
		return window.kentender_core &&
			kentender_core.ui_fixtures &&
			typeof kentender_core.ui_fixtures.tablePaginationFooterHtml === "function"
			? kentender_core.ui_fixtures.tablePaginationFooterHtml({ ns: "kt", testid: "kt-nds-table-footer" })
			: "";
	}

	function readyMarkup(data) {
		const c = data.context || {}, s = data.summary || {};
		const canCreate = (data.actions || []).some((row) => row.code === "create");
		const needs = data.needs || [];
		return `<div class="kt-nds-root kt-stitch-canvas" data-testid="departmental-needs-workspace">
			<div class="kt-nds-top">
				<div>
					<h1 class="kt-nds-title">Departmental Needs</h1>
					<p class="kt-nds-subtitle">Capture and review departmental requirements for procurement planning.</p>
					<div class="kt-nds-context">
						<span><span class="kt-nds-context-label">Procuring Entity:</span> ${esc(c.procuring_entity_label)}</span>
						<span class="kt-nds-context-sep" aria-hidden="true">|</span>
						<span><span class="kt-nds-context-label">Department:</span> ${esc(c.organisation_unit_label)}</span>
						<span class="kt-nds-context-sep" aria-hidden="true">|</span>
						<span><span class="kt-nds-context-label">Planning year:</span> ${esc(c.financial_year || "Select year")}</span>
						<button type="button" class="text-primary kt-nds-context-change" data-nds-change-context>
							<span class="material-symbols-outlined" aria-hidden="true">edit</span>Change
						</button>
					</div>
				</div>
				${canCreate ? `<button type="button" class="bg-primary kt-nds-create" data-nds-action="create">
					<span class="material-symbols-outlined" aria-hidden="true">add_circle</span>Create need
				</button>` : ""}
			</div>

			<div class="kt-nds-summary">
				${summaryCard("nds-summary-total", "total", "Total needs", s.total_needs)}
				${summaryCard("nds-summary-waiting", "waiting", "Awaiting departmental review", s.awaiting_departmental_review)}
				${summaryCard("nds-summary-accepted", "accepted", "Accepted for planning", s.accepted_for_planning)}
				${summaryCard("nds-summary-included", "included", "Included in approved plan", s.included_in_approved_plan)}
			</div>

			<section class="kt-nds-section">
				<h2 class="kt-nds-section-title">
					<span class="material-symbols-outlined kt-nds-icon kt-nds-icon--reserved" aria-hidden="true">assignment_late</span>Work requiring action
				</h2>
				<div class="kt-nds-table-wrap">
					<div class="kt-nds-table-scroll">
						<table class="kt-nds-table kt-nds-table--work">
							<thead><tr class="bg-surface-container-low">
								<th class="kt-nds-th-ref">Reference</th><th>Need</th><th class="kt-nds-th-narrow">Submitted by</th>
								<th class="kt-nds-th-narrow">Required by</th><th class="kt-nds-th-status">Status</th><th class="kt-nds-th-right">Action</th>
							</tr></thead>
							<tbody>${workRows(data.work_requiring_action || [])}</tbody>
						</table>
					</div>
				</div>
			</section>

			<section class="kt-nds-section">
				<div class="kt-nds-section-head">
					<h2 class="kt-nds-section-title">
						<span class="material-symbols-outlined kt-nds-icon kt-nds-icon--primary" aria-hidden="true">list_alt</span>Departmental needs
					</h2>
					<div class="kt-nds-toolbar">
						<button type="button" class="border rounded-lg kt-nds-toolbar-btn" data-nds-action="filter" title="Filter">
							<span class="material-symbols-outlined" aria-hidden="true">filter_list</span>
						</button>
						<button type="button" class="border rounded-lg kt-nds-toolbar-btn" data-nds-action="download" title="Download">
							<span class="material-symbols-outlined" aria-hidden="true">download</span>
						</button>
					</div>
				</div>
				<div class="kt-nds-table-wrap" data-kt-nds-needs-panel>
					<div class="kt-nds-table-scroll">
						<table class="kt-nds-table kt-nds-table--needs">
							<thead><tr class="bg-surface-container-low">
								<th class="kt-nds-th-need">Need &amp; Reference</th><th>Indicative requirement</th><th>Required by</th>
								<th>Status</th><th>Planning usage</th><th class="kt-nds-th-right">Action</th>
							</tr></thead>
							<tbody data-kt-nds-needs-tbody>${needRows(needs)}</tbody>
						</table>
					</div>
					${tableFooterHtml()}
				</div>
			</section>
		</div>`;
	}

	function blockedMarkup(data) {
		const selecting = data.outcome === "CONTEXT_SELECTION_REQUIRED";
		return `<div class="kt-nds-root kt-stitch-canvas kt-nds-blocked" data-testid="departmental-needs-context-state">
			<h1 class="kt-nds-title">Departmental Needs</h1>
			<p class="kt-nds-subtitle">${selecting ? "Select the Procuring Entity and department context you want to work in." : "An active organisational assignment is required to access Departmental Needs."}</p>
			${selecting ? `<button type="button" class="bg-primary kt-nds-create" data-nds-change-context>${esc(__("Select context"))}</button>` : ""}
		</div>`;
	}

	function emptyState(copy) {
		return `<div class="kt-nds-root kt-stitch-canvas"><div class="kt-nds-empty">${esc(copy)}</div></div>`;
	}

	function query() {
		const params = new URLSearchParams(window.location.search);
		return { procuring_entity: params.get("procuring_entity") || "", organisation_unit: params.get("organisation_unit") || "", financial_year: params.get("financial_year") || "" };
	}

	function activateSurface() {
		document.body.classList.add("kt-nds-surface");
	}

	function deactivateSurface() {
		document.body.classList.remove("kt-nds-surface");
	}

	function enterShell() {
		activateSurface();
		const sh = kentender_core.cl_shell;
		if (!sh || typeof sh.enterNative !== "function") return;
		sh.enterNative({
			sidebarWorkspaceKey: "procurement",
			toolbar: {
				breadcrumbs: [
					{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
					{ label: __("Departmental Needs") },
				],
				showSearch: false,
				showUserMeta: true,
			},
		});
	}

	function render(state, html) {
		const sh = kentender_core.cl_shell;
		if (sh && typeof sh.mountContent === "function") {
			sh.mountContent(state.page.main, { mainHtml: html, pageHeader: { title: "", hidden: true } });
			state.body = state.page.main.find('[data-testid="kt-cl-page-body"]').get(0) || state.page.main.get(0);
		} else {
			state.page.main.html(html);
			state.body = state.page.main.get(0);
		}
	}

	async function load(state) {
		enterShell();
		render(state, '<div class="kt-nds-root kt-stitch-canvas"><div class="kt-nds-loading">Loading Departmental Needs…</div></div>');
		try {
			const response = await frappe.call({ method: "kentender_procurement.departmental_needs.api.get_workspace", args: query() });
			state.data = response.message || {};
			render(state, state.data.ok ? readyMarkup(state.data) : blockedMarkup(state.data));
			bind(state);
		} catch (error) {
			render(state, emptyState("Departmental Needs could not be loaded."));
			throw error;
		}
	}

	function applyContext(state, overrides) {
		const current = query();
		const next = { ...current, ...overrides };
		const params = new URLSearchParams();
		if (next.procuring_entity) params.set("procuring_entity", next.procuring_entity);
		if (next.organisation_unit) params.set("organisation_unit", next.organisation_unit);
		if (next.financial_year) params.set("financial_year", next.financial_year);
		// Canonical route only — see NDS-CHG-001 §9.2 ("/departmental-needs is the only route").
		const url = `/desk/departmental-needs${params.toString() ? `?${params.toString()}` : ""}`;
		window.history.pushState(null, "", url);
		return load(state);
	}

	function bindPagination(state) {
		const $root = window.jQuery && jQuery(state.body).find("[data-kt-nds-needs-panel]");
		if (!$root || !$root.length || !kentender_core.table || typeof kentender_core.table.attachPagination !== "function") return;
		const $tbody = $root.find("[data-kt-nds-needs-tbody]");
		kentender_core.table
			.attachPagination($root, { renderPage: (pageRows) => $tbody.html(needRows(pageRows)) })
			.setRows(state.data.needs || [], true);
	}

	// NDS-CHG-002 §8.1 route table, mapped onto this app's own /desk/<page-name>
	// Desk-routing convention (the spec's `/departmental-needs/...` paths are
	// logical routes, not literal URLs — every other module in this app maps
	// its own logical routes the same way, e.g. Budget's /desk/budget-register).
	function navigateForAction(code, needName) {
		if (code === "create") { frappe.set_route("departmental-needs-new"); return; }
		if (code === "edit") { frappe.set_route("departmental-needs-edit", { need: needName }); return; }
		if (code === "review") { frappe.set_route("departmental-needs-review", { need: needName }); return; }
		frappe.set_route("departmental-needs-detail", { need: needName });
	}

	function bind(state) {
		// Delegated: row actions and context controls repaint inside state.body on every reload.
		const $body = window.jQuery && jQuery(state.body);
		if ($body && $body.length) {
			$body.off(".ktNdsActions");
			$body.on("click.ktNdsActions", "[data-nds-change-context]", () => openContextDialog(state));
			$body.on("click.ktNdsActions", "[data-nds-action]", function () {
				navigateForAction(this.getAttribute("data-nds-action"), this.getAttribute("data-need"));
			});
		} else {
			state.body.querySelectorAll("[data-nds-action]").forEach((el) => el.addEventListener("click", () => {
				navigateForAction(el.getAttribute("data-nds-action"), el.getAttribute("data-need"));
			}));
		}
		bindPagination(state);
	}

	frappe.pages[PAGE] = frappe.pages[PAGE] || {};
	frappe.pages[PAGE].on_page_load = function (wrapper) {
		const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Departmental Needs"), single_column: true });
		wrapper.ktDepartmentalNeeds = { page, body: page.main.get(0), data: {} };
	};
	frappe.pages[PAGE].on_page_show = function (wrapper) { return load(wrapper.ktDepartmentalNeeds); };
	frappe.pages[PAGE].on_page_hide = function () {
		deactivateSurface();
		const sh = kentender_core.cl_shell;
		if (sh && typeof sh.leaveNative === "function") sh.leaveNative();
	};
})();
