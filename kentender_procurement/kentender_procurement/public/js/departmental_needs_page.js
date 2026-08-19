(function () {
	"use strict";

	const PAGE = "departmental-needs";

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function statusClass(value) {
		if (value === "Accepted for planning") return "is-accepted";
		if (value === "Submitted") return "is-submitted";
		if (value === "Returned" || value === "Not taken forward") return "is-returned";
		return "is-neutral";
	}

	function usageClass(value) {
		return value === "Fully included" ? "is-included" : "is-neutral";
	}

	function summaryCard(label, value, tone) {
		return `<section class="kt-nds-card ${tone}" data-testid="nds-summary-${tone}"><span>${esc(label)}</span><strong>${esc(value || 0)}</strong></section>`;
	}

	function actionLink(row) {
		const action = (row.actions || [])[0];
		if (!action) return "";
		return `<button class="kt-nds-link" type="button" data-nds-action="${esc(action.code)}" data-need="${esc(row.name)}">${esc(action.label)} <span aria-hidden="true">→</span></button>`;
	}

	function emptyState(copy) {
		return `<div class="kt-nds-empty">${esc(copy)}</div>`;
	}

	function tableRows(rows, work) {
		if (!rows.length) return `<tr><td colspan="${work ? 6 : 6}">${emptyState(work ? "No work is awaiting departmental review." : "No Departmental Needs match this context.")}</td></tr>`;
		return rows.map((row) => work ? `
			<tr>
				<td class="kt-nds-ref">${esc(row.reference)}</td><td class="kt-nds-title">${esc(row.title)}</td>
				<td>${esc(row.submitted_by)}</td><td>${esc(row.required_by_label)}</td>
				<td><span class="kt-nds-pill ${statusClass(row.status)}">${esc(row.status)}</span></td><td class="kt-nds-action">${actionLink(row)}</td>
			</tr>` : `
			<tr>
				<td><div class="kt-nds-title">${esc(row.title)}</div><div class="kt-nds-ref">${esc(row.reference)}</div></td>
				<td>${esc(row.indicative_requirement)}</td><td>${esc(row.required_by_label)}</td>
				<td><span class="kt-nds-pill ${statusClass(row.status)}">${esc(row.status)}</span></td>
				<td><span class="kt-nds-pill ${usageClass(row.planning_usage)}">${esc(row.planning_usage)}</span></td><td class="kt-nds-action">${actionLink(row)}</td>
			</tr>`).join("");
	}

	function readyMarkup(data) {
		const c = data.context || {}, s = data.summary || {};
		const canCreate = (data.actions || []).some((row) => row.code === "create");
		return `<div class="kt-nds" data-testid="departmental-needs-workspace">
			<header class="kt-nds-header">
				<div><nav aria-label="Breadcrumb"><span>Home</span><b aria-hidden="true">›</b><span>Departmental Needs</span></nav>
				<h1>Departmental Needs</h1><p>Capture and review departmental requirements for procurement planning.</p>
				<div class="kt-nds-context"><b>Procuring Entity:</b> ${esc(c.procuring_entity_label)} <i>|</i> <b>Department:</b> ${esc(c.organisation_unit_label)} <i>|</i> <b>Planning year:</b> ${esc(c.financial_year || "Select year")} <button type="button" data-nds-change-context>Change</button></div></div>
				${canCreate ? '<button class="btn btn-primary kt-nds-create" type="button" data-nds-action="create">＋ Create need</button>' : ""}
			</header>
			<div class="kt-nds-summary">${summaryCard("Total needs", s.total_needs, "total")}${summaryCard("Awaiting departmental review", s.awaiting_departmental_review, "waiting")}${summaryCard("Accepted for planning", s.accepted_for_planning, "accepted")}${summaryCard("Included in approved plan", s.included_in_approved_plan, "included")}</div>
			<section class="kt-nds-section"><h2>⚠ <span>Work requiring action</span></h2><div class="kt-nds-table-wrap"><table><thead><tr><th>Reference</th><th>Need</th><th>Submitted by</th><th>Required by</th><th>Status</th><th>Action</th></tr></thead><tbody>${tableRows(data.work_requiring_action || [], true)}</tbody></table></div></section>
			<section class="kt-nds-section"><h2>▤ <span>Departmental needs</span></h2><div class="kt-nds-table-wrap"><table><thead><tr><th>Need &amp; Reference</th><th>Indicative requirement</th><th>Required by</th><th>Status</th><th>Planning usage</th><th>Action</th></tr></thead><tbody>${tableRows(data.needs || [], false)}</tbody></table><footer>Showing ${esc((data.needs || []).length ? `1-${(data.needs || []).length}` : "0")} of ${esc((data.needs || []).length)} needs</footer></div></section>
		</div>`;
	}

	function blockedMarkup(data) {
		const selecting = data.outcome === "CONTEXT_SELECTION_REQUIRED";
		return `<div class="kt-nds kt-nds-blocked" data-testid="departmental-needs-context-state"><h1>Departmental Needs</h1><p>${selecting ? "Select the Procuring Entity and department context you want to work in." : "An active organisational assignment is required to access Departmental Needs."}</p>${selecting ? '<button class="btn btn-primary" type="button" data-nds-change-context>Select context</button>' : ""}</div>`;
	}

	function query() {
		const params = new URLSearchParams(window.location.search);
		return { procuring_entity: params.get("procuring_entity") || "", organisation_unit: params.get("organisation_unit") || "", financial_year: params.get("financial_year") || "" };
	}

	async function load(state) {
		state.body.innerHTML = '<div class="kt-nds-loading">Loading Departmental Needs…</div>';
		try {
			const response = await frappe.call({ method: "kentender_procurement.departmental_needs.api.get_workspace", args: query() });
			state.data = response.message || {};
			state.body.innerHTML = state.data.ok ? readyMarkup(state.data) : blockedMarkup(state.data);
			bind(state);
		} catch (error) {
			state.body.innerHTML = emptyState("Departmental Needs could not be loaded.");
			throw error;
		}
	}

	function chooseContext(state) {
		const contexts = state.data.contexts || [];
		if (!contexts.length) return;
		const dialog = new frappe.ui.Dialog({ title: __("Change Departmental Needs context"), fields: [
			{ fieldtype: "Select", fieldname: "context", label: __("Procuring Entity and department"), options: contexts.map((row, i) => ({ label: `${row.procuring_entity_label} — ${row.organisation_unit_label}`, value: String(i) })), reqd: 1 },
			{ fieldtype: "Data", fieldname: "financial_year", label: __("Planning year"), default: (state.data.context || {}).financial_year || "" }
		], primary_action_label: __("Apply"), primary_action(values) {
			const row = contexts[Number(values.context)]; if (!row) return;
			const params = new URLSearchParams({ procuring_entity: row.procuring_entity, organisation_unit: row.organisation_unit });
			if (values.financial_year) params.set("financial_year", values.financial_year);
			window.location.assign(`/desk/departmental-needs?${params.toString()}`);
		} });
		dialog.show();
	}

	function bind(state) {
		state.body.querySelectorAll("[data-nds-change-context]").forEach((el) => el.addEventListener("click", () => chooseContext(state)));
		state.body.querySelectorAll("[data-nds-action]").forEach((el) => el.addEventListener("click", () => {
			frappe.show_alert({ message: __("This Departmental Needs interaction is awaiting its approved detailed screen contract."), indicator: "orange" }, 7);
		}));
	}

	frappe.pages[PAGE] = frappe.pages[PAGE] || {};
	frappe.pages[PAGE].on_page_load = function (wrapper) {
		const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Departmental Needs"), single_column: true });
		wrapper.ktDepartmentalNeeds = { page, body: page.main.get(0), data: {} };
	};
	frappe.pages[PAGE].on_page_show = function (wrapper) { return load(wrapper.ktDepartmentalNeeds); };
})();
