// Copyright (c) 2026, KenTender and contributors
// For license information, please see license.txt
//
// STD-WORKS-POC Steps 12 + 13 — Procurement Tender Desk buttons.
// Admin Console Step 5 — STD Demo workspace HTML + actions (Trace rules, Open package viewer).
//
// Sidecar client script that adds custom buttons under "STD POC" and, for demo
// tenders, "STD Demo". Each button is a thin wrapper around whitelisted server
// methods on `procurement_tender.py` / `std_template.py`.

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
		if (frm.is_new()) {
			return;
		}

		const STD_POC_GROUP = __("STD POC");
		const STD_DEMO_GROUP = __("STD Demo");

		const VARIANT_OPTIONS = [
			"VARIANT-INTERNATIONAL",
			"VARIANT-TENDER-SECURING-DECLARATION",
			"VARIANT-RESERVED-TENDER",
			"VARIANT-MISSING-SITE-VISIT-DATE",
			"VARIANT-MISSING-ALTERNATIVE-SCOPE",
			"VARIANT-SINGLE-LOT",
			"VARIANT-RETENTION-MONEY-SECURITY",
		].join("\n");

		if (isStdDemoWorkspace(frm)) {
			const loading = frm.get_field("html_std_demo_workspace");
			if (loading && loading.$wrapper) {
				loading.$wrapper.html(
					`<div class="text-muted" style="padding:8px;">${__(
						"Loading demo workspace summary…",
					)}</div>`,
				);
			}
			const demoHtmlMethod =
				"kentender_procurement.kentender_procurement.doctype.procurement_tender.procurement_tender.get_std_demo_workspace_html";
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

			const ptInspect =
				"kentender_procurement.kentender_procurement.doctype.procurement_tender.procurement_tender";

			frm.add_custom_button(
				__("Required forms inspector"),
				() => {
					frappe.call({
						method: `${ptInspect}.get_required_forms_inspection`,
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
						method: `${ptInspect}.get_boq_inspection`,
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
						method: `${ptInspect}.get_preview_audit_summary`,
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
					message: __("Save the tender before running STD POC actions."),
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

		const call_std_poc = (method, args = {}, label = method) => {
			if (!ensure_saved_and_template()) return;
			const method_path =
				"kentender_procurement.kentender_procurement.doctype.procurement_tender.procurement_tender." +
				method;
			frappe.call({
				method: method_path,
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
					frm.reload_doc();
				},
			});
		};

		frm.add_custom_button(
			__("Load Template Defaults"),
			() => call_std_poc("load_template_defaults", {}, "Load Template Defaults"),
			STD_POC_GROUP,
		);

		frm.add_custom_button(
			__("Load Sample Tender"),
			() => call_std_poc("load_sample_tender", {}, "Load Sample Tender"),
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
						call_std_poc(
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
			() => call_std_poc("validate_tender_configuration", {}, "Validate Configuration"),
			STD_POC_GROUP,
		);

		frm.add_custom_button(
			__("Generate Required Forms"),
			() => call_std_poc("generate_required_forms", {}, "Generate Required Forms"),
			STD_POC_GROUP,
		);

		frm.add_custom_button(
			__("Generate Sample BoQ"),
			() => call_std_poc("generate_sample_boq", {}, "Generate Sample BoQ"),
			STD_POC_GROUP,
		);

		frm.add_custom_button(
			__("Prepare Render Context"),
			() => call_std_poc("prepare_render_context", {}, "Prepare Render Context"),
			STD_POC_GROUP,
		);

		frm.add_custom_button(
			__("Generate Tender Pack Preview"),
			() =>
				call_std_poc(
					"generate_tender_pack_preview",
					{},
					"Generate Tender Pack Preview",
				),
			STD_POC_GROUP,
		);
	},
});
