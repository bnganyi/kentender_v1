// Copyright (c) 2026, KenTender and contributors
// For license information, please see license.txt
//
// STD-WORKS-POC Steps 12 + 13 — Procurement Tender Desk buttons (admin STD POC group).
// Admin Console Step 5 — STD Demo workspace (admin-only demo group).
// Procurement Officer Tender Configuration POC — Officer Tender Configuration group.

function std_poc_demo_html_dialog(title, html) {
	const d = new frappe.ui.Dialog({
		title: title || __("Result"),
		size: "extra-large",
		fields: [{ fieldtype: "HTML", options: html || "<div></div>" }],
		primary_action_label: __("Close"),
		primary_action() {
			d.hide();
		},
	});
	d.show();
}

const STD_POC_TEMPLATE_DEMO = "KE-PPRA-WORKS-BLDG-2022-04-POC";
const DEMO_WORKSPACE_MARKER = "STD DEMO WORKSPACE";

const PT_MODULE =
	"kentender_procurement.kentender_procurement.doctype.procurement_tender.procurement_tender";

function hasAdminStdPocRole() {
	return (
		frappe.user.has_role("System Manager") || frappe.user.has_role("Administrator")
	);
}

function hasOfficerDeskRole() {
	return frappe.user.has_role("Procurement Officer") || hasAdminStdPocRole();
}

function officerOnlyHideRawJson() {
	return frappe.user.has_role("Procurement Officer") && !hasAdminStdPocRole();
}

function isStdDemoWorkspace(frm) {
	if (!frm || !frm.doc) {
		return false;
	}
	const poc = String(frm.doc.poc_notes || "");
	if (poc.includes(DEMO_WORKSPACE_MARKER)) {
		return true;
	}
	return (frm.doc.std_template || "") === STD_POC_TEMPLATE_DEMO;
}

frappe.ui.form.on("Procurement Tender", {
	refresh(frm) {
		if (officerOnlyHideRawJson()) {
			frm.set_df_property("configuration_json", "hidden", 1);
		} else {
			frm.set_df_property("configuration_json", "hidden", 0);
		}

		const STD_POC_GROUP = __("STD POC");
		const STD_DEMO_GROUP = __("STD Demo");
		const OFFICER_GROUP = __("Officer Tender Configuration");

		if (frm.is_new()) {
			if (hasOfficerDeskRole()) {
				frm.add_custom_button(
					__("Start new tender from POC STD"),
					() => {
						frappe.call({
							method: `${PT_MODULE}.get_available_std_templates_for_officer`,
							freeze: true,
							freeze_message: __("Loading templates…"),
							callback(r) {
								const rows = r.message || [];
								if (!rows.length) {
									frappe.msgprint(
										__(
											"No POC STD template found. Import STD-WORKS-POC package first.",
										),
									);
									return;
								}
								frappe.call({
									method: `${PT_MODULE}.initialize_officer_tender_from_template`,
									args: { std_template: rows[0].name },
									freeze: true,
									freeze_message: __("Creating tender…"),
									callback(r2) {
										const msg = r2.message || {};
										if (msg.tender) {
											frappe.set_route("Form", "Procurement Tender", msg.tender);
										}
									},
								});
							},
						});
					},
					OFFICER_GROUP,
				);
			}
			return;
		}

		if (hasOfficerDeskRole() && frm.doc.configuration_json) {
			frappe.call({
				method: `${PT_MODULE}.get_officer_conditional_state_for_tender`,
				args: { tender_name: frm.doc.name },
				callback(r) {
					const msg = r.message || {};
					const notices = msg.notices || [];
					const field = frm.get_field("html_officer_guided_notices");
					if (!field || !field.$wrapper) {
						return;
					}
					if (!notices.length) {
						field.$wrapper.html(
							`<div class="text-muted">${__(
								"No conditional branch notices for the current configuration.",
							)}</div>`,
						);
						return;
					}
					const html = notices
						.map(
							(n) =>
								`<div class="alert alert-${
									n.level === "info" ? "info" : "default"
								}">${frappe.utils.escape_html(n.message || "")}</div>`,
						)
						.join("");
					field.$wrapper.html(html);
				},
			});
		}

		const VARIANT_OPTIONS = [
			"VARIANT-INTERNATIONAL",
			"VARIANT-TENDER-SECURING-DECLARATION",
			"VARIANT-RESERVED-TENDER",
			"VARIANT-MISSING-SITE-VISIT-DATE",
			"VARIANT-MISSING-ALTERNATIVE-SCOPE",
			"VARIANT-SINGLE-LOT",
			"VARIANT-RETENTION-MONEY-SECURITY",
		].join("\n");

		if (hasAdminStdPocRole() && isStdDemoWorkspace(frm)) {
			const loading = frm.get_field("html_std_demo_workspace");
			if (loading && loading.$wrapper) {
				loading.$wrapper.html(
					`<div class="text-muted" style="padding:8px;">${__(
						"Loading demo workspace summary…",
					)}</div>`,
				);
			}
			const demoHtmlMethod = `${PT_MODULE}.get_std_demo_workspace_html`;
			frappe.call({
				method: demoHtmlMethod,
				args: { tender_name: frm.doc.name },
				callback(r) {
					const msg = r.message || {};
					const field = frm.get_field("html_std_demo_workspace");
					if (!field || !field.$wrapper) {
						return;
					}
					if (!msg.ok) {
						field.$wrapper.html(
							`<div class="alert alert-warning">${frappe.utils.escape_html(
								msg.error || __("Could not load demo workspace HTML."),
							)}</div>`,
						);
						return;
					}
					field.$wrapper.html(msg.html || "");
				},
			});

			const stdTpl =
				"kentender_procurement.kentender_procurement.doctype.std_template.std_template";

			frm.add_custom_button(
				__("Trace Current Rules"),
				() => {
					frappe.call({
						method: `${stdTpl}.trace_std_rules_for_tender`,
						args: { tender_name: frm.doc.name },
						freeze: true,
						freeze_message: __("Tracing rules…"),
						callback(r) {
							const msg = r.message || {};
							if (msg.html) {
								std_poc_demo_html_dialog(__("Rule trace — current tender"), msg.html);
								return;
							}
							if (msg.error) {
								frappe.msgprint({
									title: __("Rule trace"),
									message: frappe.utils.escape_html(msg.error),
									indicator: "orange",
								});
							}
						},
					});
				},
				STD_DEMO_GROUP,
			);

			frm.add_custom_button(
				__("Open Package Viewer"),
				() => {
					if (!frm.doc.std_template) {
						frappe.msgprint({
							message: __("Missing STD Template link."),
							indicator: "orange",
						});
						return;
					}
					frappe.set_route("Form", "STD Template", frm.doc.std_template);
				},
				STD_DEMO_GROUP,
			);

			frm.add_custom_button(
				__("Required forms inspector"),
				() => {
					frappe.call({
						method: `${PT_MODULE}.get_required_forms_inspection`,
						args: { tender_name: frm.doc.name },
						freeze: true,
						freeze_message: __("Loading inspector…"),
						callback(r) {
							const msg = r.message || {};
							if (msg.html) {
								std_poc_demo_html_dialog(__("Required forms inspector"), msg.html);
							}
						},
					});
				},
				STD_DEMO_GROUP,
			);

			frm.add_custom_button(
				__("BoQ inspector"),
				() => {
					frappe.call({
						method: `${PT_MODULE}.get_boq_inspection`,
						args: { tender_name: frm.doc.name },
						freeze: true,
						freeze_message: __("Loading inspector…"),
						callback(r) {
							const msg = r.message || {};
							if (msg.html) {
								std_poc_demo_html_dialog(__("BoQ inspector"), msg.html);
							}
						},
					});
				},
				STD_DEMO_GROUP,
			);

			frm.add_custom_button(
				__("Preview and audit viewer"),
				() => {
					frappe.call({
						method: `${PT_MODULE}.get_preview_audit_summary`,
						args: { tender_name: frm.doc.name },
						freeze: true,
						freeze_message: __("Loading preview and audit…"),
						callback(r) {
							const msg = r.message || {};
							if (msg.html) {
								std_poc_demo_html_dialog(__("Preview and audit viewer"), msg.html);
							}
						},
					});
				},
				STD_DEMO_GROUP,
			);
		}

		const ensure_saved_and_template = () => {
			if (frm.is_new() || frm.is_dirty()) {
				frappe.msgprint({
					title: __("Save the tender first"),
					message: __("Save the tender before running this action."),
					indicator: "orange",
				});
				return false;
			}
			if (!frm.doc.std_template) {
				frappe.msgprint({
					title: __("Missing STD Template"),
					message: __("Select an STD Template before running this action."),
					indicator: "red",
				});
				return false;
			}
			return true;
		};

		const call_pt_method = (method, args = {}, label = method, reload = true) => {
			if (!ensure_saved_and_template()) return;
			frappe.call({
				method: `${PT_MODULE}.${method}`,
				args: { tender_name: frm.doc.name, ...args },
				freeze: true,
				freeze_message: __("Running {0}...", [label]),
				callback: (r) => {
					if (!r || !r.message) return;
					if (r.message.ok === false) {
						frappe.msgprint({
							title: __("Action could not complete"),
							message: r.message.message || __("See messages above."),
							indicator: "orange",
						});
					} else {
						frappe.show_alert({
							message: r.message.message || __("Action complete."),
							indicator: "green",
						});
					}
					if (reload) {
						frm.reload_doc();
					}
				},
			});
		};

		if (hasAdminStdPocRole()) {
			frm.add_custom_button(
				__("Load Template Defaults"),
				() => call_pt_method("load_template_defaults", {}, "Load Template Defaults"),
				STD_POC_GROUP,
			);

			frm.add_custom_button(
				__("Load Sample Tender"),
				() => call_pt_method("load_sample_tender", {}, "Load Sample Tender"),
				STD_POC_GROUP,
			);

			frm.add_custom_button(
				__("Load Sample Variant"),
				() => {
					if (!ensure_saved_and_template()) return;
					frappe.prompt(
						[
							{
								label: __("Variant code"),
								fieldname: "variant_code",
								fieldtype: "Select",
								options: VARIANT_OPTIONS,
								reqd: 1,
							},
						],
						(values) =>
							call_pt_method(
								"load_sample_variant",
								{ variant_code: values.variant_code },
								"Load Sample Variant",
							),
						__("Choose a sample variant"),
						__("Apply"),
					);
				},
				STD_POC_GROUP,
			);

			frm.add_custom_button(
				__("Validate Configuration"),
				() =>
					call_pt_method("validate_tender_configuration", {}, "Validate Configuration"),
				STD_POC_GROUP,
			);

			frm.add_custom_button(
				__("Generate Required Forms"),
				() =>
					call_pt_method("generate_required_forms", {}, "Generate Required Forms"),
				STD_POC_GROUP,
			);

			frm.add_custom_button(
				__("Generate Sample BoQ"),
				() => call_pt_method("generate_sample_boq", {}, "Generate Sample BoQ"),
				STD_POC_GROUP,
			);

			frm.add_custom_button(
				__("Prepare Render Context"),
				() => call_pt_method("prepare_render_context", {}, "Prepare Render Context"),
				STD_POC_GROUP,
			);

			frm.add_custom_button(
				__("Generate Tender Pack Preview"),
				() =>
					call_pt_method(
						"generate_tender_pack_preview",
						{},
						"Generate Tender Pack Preview",
					),
				STD_POC_GROUP,
			);
		}

		if (hasOfficerDeskRole()) {
			frm.add_custom_button(
				__("Load Sample Tender (POC)"),
				() =>
					call_pt_method("load_sample_tender", {}, __("Load Sample Tender (POC)")),
				OFFICER_GROUP,
			);

			frm.add_custom_button(
				__("Sync Configuration"),
				() => call_pt_method("sync_officer_configuration", {}, __("Sync Configuration")),
				OFFICER_GROUP,
			);

			frm.add_custom_button(
				__("Validate (officer)"),
				() =>
					call_pt_method(
						"validate_officer_configuration",
						{},
						__("Validate (officer)"),
					),
				OFFICER_GROUP,
			);

			frm.add_custom_button(
				__("Validation feedback"),
				() => {
					if (!ensure_saved_and_template()) return;
					frappe.call({
						method: `${PT_MODULE}.get_officer_validation_feedback`,
						args: { tender_name: frm.doc.name },
						freeze: true,
						callback(r) {
							const msg = r.message || {};
							const lines = [
								`<p><strong>${__("Validation status")}:</strong> ${frappe.utils.escape_html(
									msg.validation_status || "",
								)}</p>`,
								`<p><strong>${__("Tender status (officer)")}:</strong> ${frappe.utils.escape_html(
									msg.tender_status_ux || "",
								)}</p>`,
								`<p><strong>${__("Messages")}:</strong> ${msg.message_count ?? 0}</p>`,
							];
							std_poc_demo_html_dialog(__("Validation feedback"), lines.join(""));
						},
					});
				},
				OFFICER_GROUP,
			);

			frm.add_custom_button(
				__("Generate required forms (officer)"),
				() =>
					call_pt_method(
						"generate_officer_required_forms",
						{},
						__("Generate required forms (officer)"),
					),
				OFFICER_GROUP,
			);

			frm.add_custom_button(
				__("View required forms checklist"),
				() => {
					if (!ensure_saved_and_template()) return;
					frappe.call({
						method: `${PT_MODULE}.get_officer_required_forms_checklist`,
						args: { tender_name: frm.doc.name },
						freeze: true,
						callback(r) {
							const msg = r.message || {};
							const rows = msg.rows || [];
							const body = rows
								.map(
									(row) =>
										`<tr><td>${frappe.utils.escape_html(
											row.form_code || "",
										)}</td><td>${frappe.utils.escape_html(
											row.form_title || "",
										)}</td><td>${frappe.utils.escape_html(
											row.required_because || "",
										)}</td></tr>`,
								)
								.join("");
							const html = `<table class="table table-bordered"><thead><tr><th>${__(
								"Code",
							)}</th><th>${__("Form")}</th><th>${__(
								"Required because",
							)}</th></tr></thead><tbody>${body}</tbody></table>`;
							std_poc_demo_html_dialog(__("Required forms checklist"), html);
						},
					});
				},
				OFFICER_GROUP,
			);

			frm.add_custom_button(
				__("Generate representative BoQ"),
				() =>
					call_pt_method(
						"generate_officer_representative_boq",
						{},
						__("Generate representative BoQ"),
					),
				OFFICER_GROUP,
			);

			frm.add_custom_button(
				__("BoQ status"),
				() => {
					if (!ensure_saved_and_template()) return;
					frappe.call({
						method: `${PT_MODULE}.get_officer_boq_status`,
						args: { tender_name: frm.doc.name },
						freeze: true,
						callback(r) {
							const msg = r.message || {};
							const html = `<pre style="white-space:pre-wrap;">${frappe.utils.escape_html(
								JSON.stringify(msg, null, 2),
							)}</pre>`;
							std_poc_demo_html_dialog(__("BoQ status"), html);
						},
					});
				},
				OFFICER_GROUP,
			);

			frm.add_custom_button(
				__("Generate preview (officer)"),
				() =>
					call_pt_method(
						"generate_officer_preview",
						{},
						__("Generate preview (officer)"),
					),
				OFFICER_GROUP,
			);

			frm.add_custom_button(
				__("Preview and audit summary (officer)"),
				() => {
					if (!ensure_saved_and_template()) return;
					frappe.call({
						method: `${PT_MODULE}.get_officer_preview_audit_summary`,
						args: { tender_name: frm.doc.name },
						freeze: true,
						callback(r) {
							const msg = r.message || {};
							if (msg.html) {
								std_poc_demo_html_dialog(
									__("Preview and audit summary (officer)"),
									msg.html,
								);
							}
						},
					});
				},
				OFFICER_GROUP,
			);

			frm.add_custom_button(
				__("Mark ready for review"),
				() =>
					call_pt_method(
						"mark_officer_tender_ready_for_review",
						{},
						__("Mark ready for review"),
					),
				OFFICER_GROUP,
			);

			frm.add_custom_button(
				__("Reset to configuring"),
				() =>
					call_pt_method(
						"reset_officer_tender_to_configuring",
						{},
						__("Reset to configuring"),
					),
				OFFICER_GROUP,
			);
		}
	},
});
