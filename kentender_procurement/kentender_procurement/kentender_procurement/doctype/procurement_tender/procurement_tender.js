// Copyright (c) 2026, KenTender and contributors
// For license information, please see license.txt
//
// STD-WORKS-POC Steps 12 + 13 — Procurement Tender Desk buttons (admin STD POC group).
// Doc 5 §24 — Works Hardening button group (WH-012).
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

function officerApplyGuidedConditionalVisibility(frm, msg) {
	if (!msg || !Array.isArray(msg.guided_fieldnames)) {
		return;
	}
	const hidden = new Set(msg.hidden_fieldnames || []);
	for (const fn of msg.guided_fieldnames) {
		if (!frm.fields_dict[fn]) {
			continue;
		}
		frm.set_df_property(fn, "hidden", hidden.has(fn) ? 1 : 0);
	}
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

		if (hasOfficerDeskRole() && !frm.is_new()) {
			frappe.call({
				method: `${PT_MODULE}.get_officer_conditional_state_for_tender`,
				args: { tender_name: frm.doc.name },
				callback(r) {
					const msg = r.message || {};
					officerApplyGuidedConditionalVisibility(frm, msg);
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

			// Doc 5 §24 — Works Hardening (WH-012)
			const WORKS_HARDENING_GROUP = __("Works Hardening");
			const wh012_esc = (v) =>
				frappe.utils.escape_html(v === null || v === undefined ? "" : String(v));
			const wh012_top_findings_rows = (findings, limit) => {
				const rows = (findings || []).slice(0, limit || 60);
				return rows
					.map(
						(f) =>
							`<tr><td>${wh012_esc(f.severity)}</td><td>${wh012_esc(
								f.finding_code,
							)}</td><td>${wh012_esc(f.message)}</td></tr>`,
					)
					.join("");
			};

			frm.add_custom_button(
				__("Run Works Hardening"),
				() => {
					if (!ensure_saved_and_template()) return;
					frappe.call({
						method: `${PT_MODULE}.run_works_tender_stage_hardening`,
						args: { tender_name: frm.doc.name },
						freeze: true,
						freeze_message: __("Running Works Hardening…"),
						callback(r) {
							if (r && r.exc) {
								frm.reload_doc();
								return;
							}
							const msg = r.message || {};
							if (msg.ok === false) {
								frappe.msgprint({
									title: __("Works Hardening"),
									message:
										msg.message || __("Validation blocked or failed."),
									indicator: "orange",
								});
							} else {
								frappe.show_alert({
									message: __("Works Hardening completed."),
									indicator: "green",
								});
							}
							frm.reload_doc();
						},
					});
				},
				WORKS_HARDENING_GROUP,
			);

			frm.add_custom_button(
				__("Check Works Hardening"),
				() => {
					if (!ensure_saved_and_template()) return;
					frappe.call({
						method: `${PT_MODULE}.validate_works_tender_stage`,
						args: { tender_name: frm.doc.name },
						freeze: true,
						freeze_message: __("Validating…"),
						callback(r) {
							const env = r.message || {};
							const sum = env.summary || {};
							const parts = [
								`<h4>${__("Overall")}</h4>`,
								`<p><strong>${__("Status")}:</strong> ${wh012_esc(env.status)}</p>`,
								`<p><strong>${__("Boundary")}:</strong> ${wh012_esc(
									env.boundary_code,
								)}</p>`,
								`<p>${__("Severity counts")}: ${__("Critical")} ${wh012_esc(
									env.critical_count,
								)}, ${__("High")} ${wh012_esc(env.high_count)}, ${__(
									"Medium",
								)} ${wh012_esc(env.medium_count)}, ${__("Low")} ${wh012_esc(
									env.low_count,
								)}, ${__("Info")} ${wh012_esc(env.info_count)}</p>`,
								`<h4>${__("Area status")}</h4>`,
								"<ul>",
								`<li>${__("Works requirements")}: ${wh012_esc(
									sum.works_requirements_status,
								)}</li>`,
								`<li>${__("Section attachments")}: ${wh012_esc(
									sum.attachments_status,
								)}</li>`,
								`<li>${__("BoQ hardening")}: ${wh012_esc(
									sum.boq_hardening_status,
								)}</li>`,
								`<li>${__("Required forms")}: ${wh012_esc(sum.forms_status)}</li>`,
								`<li>${__("Lot / BoQ linkage")}: ${wh012_esc(
									sum.lot_linkage_status,
								)}</li>`,
								`<li>${__("Derived models")}: ${wh012_esc(
									sum.derived_models_status,
								)}</li>`,
								`<li>${__("Audit")}: ${wh012_esc(sum.audit_status)}</li>`,
								"</ul>",
								`<h4>${__("Findings")} (${(env.findings || []).length})</h4>`,
								'<div style="max-height:320px;overflow:auto;">',
								`<table class="table table-bordered"><thead><tr><th>${__(
									"Severity",
								)}</th><th>${__("Code")}</th><th>${__(
									"Message",
								)}</th></tr></thead><tbody>`,
								wh012_top_findings_rows(env.findings, 60),
								"</tbody></table></div>",
							];
							std_poc_demo_html_dialog(
								__("Works Hardening — Check"),
								parts.join(""),
							);
							frm.reload_doc();
						},
					});
				},
				WORKS_HARDENING_GROUP,
			);

			frm.add_custom_button(
				__("View Works Hardening Summary"),
				() => {
					if (frm.is_dirty()) {
						frappe.msgprint({
							title: __("Save the tender first"),
							message: __(
								"Save the tender before running this action.",
							),
							indicator: "orange",
						});
						return;
					}
					frappe.call({
						method: `${PT_MODULE}.get_works_hardening_summary`,
						args: { tender_name: frm.doc.name },
						freeze: true,
						freeze_message: __("Loading summary…"),
						callback(r1) {
							frappe.call({
								method: `${PT_MODULE}.get_works_hardening_findings`,
								args: { tender_name: frm.doc.name },
								freeze: true,
								freeze_message: __("Loading findings…"),
								callback(r2) {
									const m1 = r1.message || {};
									const m2 = r2.message || {};
									const s = m1.summary || {};
									const counts = s.counts || {};
									const findings = m2.findings || [];
									const body = [
										`<h4>${__("Overall hardening")}</h4>`,
										`<p><strong>${__("Status")}:</strong> ${wh012_esc(
											s.works_hardening_status,
										)}</p>`,
										`<p><strong>${__("Checked at")}:</strong> ${wh012_esc(
											s.works_hardening_checked_at,
										)}</p>`,
										`<h4>${__("1. Works requirements status")}</h4>`,
										`<p>${wh012_esc(s.works_requirements_status)} — ${__(
											"Rows",
										)}: ${wh012_esc(counts.works_requirements)}</p>`,
										`<h4>${__("2. Section attachments status")}</h4>`,
										`<p>${wh012_esc(s.attachments_status)} — ${__(
											"Rows",
										)}: ${wh012_esc(counts.section_attachments)}</p>`,
										`<h4>${__("3. BoQ hardening status")}</h4>`,
										`<p>${wh012_esc(s.boq_hardening_status)} — ${__(
											"BoQ items",
										)}: ${wh012_esc(counts.boq_items)}</p>`,
										`<h4>${__("4. Derived models status")}</h4>`,
										`<p>${wh012_esc(s.derived_models_status)} — ${__(
											"Rows",
										)}: ${wh012_esc(counts.derived_model_readiness)}</p>`,
										`<h4>${__("5. Hardening findings")}</h4>`,
										`<p>${__("Count")}: ${wh012_esc(findings.length)}</p>`,
										'<div style="max-height:240px;overflow:auto;">',
										`<table class="table table-sm table-bordered"><thead><tr><th>${__(
											"Severity",
										)}</th><th>${__("Code")}</th><th>${__(
											"Message",
										)}</th></tr></thead><tbody>`,
										wh012_top_findings_rows(findings, 80),
										"</tbody></table></div>",
										`<h4>${__("6. Snapshot hash")}</h4>`,
										`<p><code>${wh012_esc(
											s.works_hardening_snapshot_hash,
										)}</code></p>`,
									];
									std_poc_demo_html_dialog(
										__("Works Hardening — Summary"),
										body.join(""),
									);
								},
							});
						},
					});
				},
				WORKS_HARDENING_GROUP,
			);

			frm.add_custom_button(
				__("View Works Snapshot"),
				() => {
					if (frm.is_dirty()) {
						frappe.msgprint({
							title: __("Save the tender first"),
							message: __(
								"Save the tender before running this action.",
							),
							indicator: "orange",
						});
						return;
					}
					frappe.call({
						method: `${PT_MODULE}.get_works_tender_stage_snapshot`,
						args: { tender_name: frm.doc.name },
						freeze: true,
						freeze_message: __("Loading snapshot…"),
						callback(r) {
							const msg = r.message || {};
							const hash = msg.hash || "";
							const snap = msg.snapshot;
							let html = "";
							if (officerOnlyHideRawJson()) {
								const pv = snap && snap.preview ? snap.preview : {};
								const val = snap && snap.validation ? snap.validation : {};
								html = [
									`<h4>${__("Snapshot hash")}</h4>`,
									`<p><code>${wh012_esc(hash)}</code></p>`,
									`<h4>${__("Snapshot identity")}</h4>`,
									`<p>${__("Type")}: ${wh012_esc(
										snap && snap.snapshot_type,
									)} — ${__("Version")}: ${wh012_esc(
										snap && snap.snapshot_version,
									)}</p>`,
									`<h4>${__("Preview (summary)")}</h4>`,
									`<pre style="white-space:pre-wrap;max-height:200px;overflow:auto;">${wh012_esc(
										JSON.stringify(pv, null, 2),
									)}</pre>`,
									`<h4>${__("Validation (summary)")}</h4>`,
									`<pre style="white-space:pre-wrap;max-height:200px;overflow:auto;">${wh012_esc(
										JSON.stringify(val, null, 2),
									)}</pre>`,
									`<p class="text-muted">${__(
										"Full snapshot JSON is available to system administrators.",
									)}</p>`,
								].join("");
							} else {
								const json =
									snap === null || snap === undefined
										? __("No snapshot stored yet. Run Works Hardening first.")
										: JSON.stringify(snap, null, 2);
								html = [
									`<h4>${__("Snapshot hash")}</h4>`,
									`<p><code>${wh012_esc(hash)}</code></p>`,
									`<h4>${__("Snapshot JSON")}</h4>`,
									`<pre style="white-space:pre-wrap;max-height:70vh;overflow:auto;">${wh012_esc(
										json,
									)}</pre>`,
								].join("");
							}
							std_poc_demo_html_dialog(
								__("Works Hardening — Snapshot"),
								html,
							);
						},
					});
				},
				WORKS_HARDENING_GROUP,
			);
		}
	},
});
