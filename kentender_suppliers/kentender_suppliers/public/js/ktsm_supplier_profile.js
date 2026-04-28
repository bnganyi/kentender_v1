frappe.ui.form.on("KTSM Supplier Profile", {
	refresh(frm) {
		if (!frm.page) return;
		frm.page.clear_inner_toolbar();
		frm.page.set_indicator(
			`${frm.doc.approval_status || "Draft"} / ${frm.doc.compliance_status || "Unknown"}`,
			(frm.doc.approval_status || "").toLowerCase() === "approved" ? "green" : "orange"
		);

		frm.page.add_inner_button("Back to Supplier Workbench", () => {
			frappe.set_route("Workspaces", "KTSM Supplier Registry");
		});

		frm.page.add_inner_button("Open Documents Register", () => {
			routeToList("KTSM Supplier Document", { supplier_profile: frm.doc.name });
		});

		frm.page.add_inner_button("Edit Identity", () => {
			frappe.prompt(
				[
					{
						fieldname: "supplier_name",
						fieldtype: "Data",
						label: "Supplier Name",
						reqd: 1,
						default: frm.doc.identity_display || "",
					},
					{
						fieldname: "supplier_type",
						fieldtype: "Select",
						label: "Supplier Type",
						options: "Company\nIndividual",
						default: "Company",
					},
				],
				(values) => {
					frappe.call({
						method: "kentender_suppliers.api.ktsm_landing.update_builder_identity",
						args: {
							profile_name: frm.doc.name,
							supplier_name: values.supplier_name,
							supplier_type: values.supplier_type,
						},
						callback: () => frm.reload_doc(),
					});
				},
				"Edit Supplier Identity",
				"Save"
			);
		});

		frm.page.add_inner_button("Open Category Assignments", () => {
			routeToList("KTSM Category Assignment", { supplier_profile: frm.doc.name });
		});

		frm.page.add_inner_button("Submit for Review", () => {
			frappe.call({
				method: "kentender_suppliers.api.smw_workflow.ktsm_submit_for_review",
				args: { supplier_profile: frm.doc.name },
				callback: () => frm.reload_doc(),
			});
		});

		ensureBuilderSummary(frm);
	}
});

function ensureBuilderSummary(frm) {
	const wrapper = frm.fields_dict.section_identity?.wrapper;
	if (!wrapper) return;
	ensureBuilderStyles();
	const hostId = "ktsm-builder-summary";
	let host = wrapper.querySelector(`#${hostId}`);
	if (!host) {
		host = document.createElement("div");
		host.id = hostId;
		host.style.marginBottom = "12px";
		host.setAttribute("data-testid", "ktsm-builder-summary");
		wrapper.prepend(host);
	}
	frappe.call({
		method: "kentender_suppliers.api.ktsm_landing.get_builder_payload",
		args: { profile_name: frm.doc.name },
		callback(r) {
			const msg = r.message || {};
			if (!msg.ok) {
				host.innerHTML = "";
				return;
			}
			const missing = (msg.readiness?.missing_required_documents || []).map((x) =>
				frappe.utils.escape_html(String(x))
			);
			const readiness = msg.readiness || {};
			const steps = [
				{
					label: "Identity",
					done: !!readiness.has_identity,
					hint: "ERP Supplier anchor, code, type",
				},
				{
					label: "Metadata",
					done: !!((msg.profile || {}).risk_level || (msg.profile || {}).external_user),
					hint: "Risk and external linkage",
				},
				{
					label: "Categories",
					done: !!readiness.has_categories,
					hint: "Requested and qualification rows",
				},
				{
					label: "Documents",
					done: !!readiness.has_documents,
					hint: "KTSM document register entries",
				},
				{
					label: "Submit",
					done: !missing.length && frm.doc.approval_status !== "Draft",
					hint: "Workflow handoff for review",
				},
			];
			const completed = steps.filter((s) => s.done).length;
			host.innerHTML = `
				<div class="ktsm-builder-shell" data-testid="ktsm-builder-shell">
					<div class="ktsm-builder-head">
						<div>
							<div class="ktsm-builder-title">Supplier Builder</div>
							<div class="ktsm-builder-sub">Use this guided form to complete supplier metadata inside KenTender before governance transitions.</div>
						</div>
						<div class="ktsm-builder-progress">${completed}/${steps.length} steps</div>
					</div>
					<div class="ktsm-builder-steps" data-testid="ktsm-builder-steps">
						${steps
							.map(
								(step) => `
							<div class="ktsm-step ${step.done ? "is-done" : "is-pending"}">
								<div class="ktsm-step-name">${frappe.utils.escape_html(step.label)}</div>
								<div class="ktsm-step-hint">${frappe.utils.escape_html(step.hint)}</div>
							</div>
						`
							)
							.join("")}
					</div>
					<div class="ktsm-builder-actions">
						<button type="button" class="btn btn-xs btn-default" data-ktsm-builder-open-docs>Open Documents Register</button>
						<button type="button" class="btn btn-xs btn-default" data-ktsm-builder-open-cats>Open Category Assignments</button>
					</div>
					<div class="ktsm-builder-blockers ${missing.length ? "has-blockers" : "is-clear"}" data-testid="ktsm-builder-missing-docs">
						${missing.length
							? `Blockers before submit: ${missing.join(", ")}`
							: "No required-document blockers detected."}
					</div>
				</div>
			`;
			wireBuilderQuickActions(host, frm);
		}
	});
}

function wireBuilderQuickActions(host, frm) {
	const openDocs = host.querySelector("[data-ktsm-builder-open-docs]");
	const openCats = host.querySelector("[data-ktsm-builder-open-cats]");
	if (openDocs) {
		openDocs.addEventListener("click", () => {
			routeToList("KTSM Supplier Document", { supplier_profile: frm.doc.name });
		});
	}
	if (openCats) {
		openCats.addEventListener("click", () => {
			routeToList("KTSM Category Assignment", { supplier_profile: frm.doc.name });
		});
	}
}

function doctypeSlug(doctype) {
	return String(doctype || "")
		.toLowerCase()
		.replace(/\s+/g, "-");
}

function routeToList(doctype, routeOptions) {
	if (!doctype) return;
	let query = "";
	if (routeOptions && typeof URLSearchParams !== "undefined") {
		query = "?" + new URLSearchParams(routeOptions).toString();
	}
	if (window.location.pathname.indexOf("/desk") === 0) {
		window.location.href = "/desk/List/" + encodeURIComponent(doctype) + "/List" + query;
		return;
	}
	window.location.href = "/app/" + doctypeSlug(doctype) + "/view/list" + query;
}

function ensureBuilderStyles() {
	if (document.getElementById("ktsm-builder-style")) return;
	const style = document.createElement("style");
	style.id = "ktsm-builder-style";
	style.textContent = `
		.ktsm-builder-shell { border: 1px solid var(--border-color); border-radius: 8px; background: var(--fg-color); padding: 10px; margin-bottom: 12px; }
		.ktsm-builder-head { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 8px; align-items: flex-start; }
		.ktsm-builder-title { font-weight: 600; font-size: 13px; }
		.ktsm-builder-sub { font-size: 12px; color: var(--text-muted); max-width: 720px; }
		.ktsm-builder-progress { font-size: 11px; border: 1px solid var(--border-color); border-radius: 999px; padding: 2px 8px; background: var(--control-bg); white-space: nowrap; }
		.ktsm-builder-steps { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 6px; margin-bottom: 8px; }
		.ktsm-step { border: 1px solid var(--border-color); border-radius: 6px; padding: 6px; background: var(--control-bg); }
		.ktsm-step.is-done { border-color: #2e8b57; }
		.ktsm-step.is-pending { border-color: #d5a100; }
		.ktsm-step-name { font-size: 12px; font-weight: 600; }
		.ktsm-step-hint { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
		.ktsm-builder-actions { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
		.ktsm-builder-blockers { font-size: 12px; padding: 6px 8px; border-radius: 6px; }
		.ktsm-builder-blockers.has-blockers { background: #fff7e6; border: 1px solid #f1c26a; color: #8a5a00; }
		.ktsm-builder-blockers.is-clear { background: #eefaf2; border: 1px solid #85c69a; color: #1d6b3a; }
	`;
	document.head.appendChild(style);
}

