// Copyright (c) 2026, KenTender and contributors
// STD Administration Console POC — Admin Steps 3–4 (viewer + validation + rule trace)

function std_admin_html_dialog(title, html) {
	const d = new frappe.ui.Dialog({
		title: title || __('Result'),
		size: 'extra-large',
		fields: [{ fieldtype: 'HTML', options: html || '<div></div>' }],
		primary_action_label: __('Close'),
		primary_action() {
			d.hide();
		},
	});
	d.show();
}

function std_admin_prompt_string(title, label, on_submit) {
	const d = new frappe.ui.Dialog({
		title,
		fields: [{ fieldname: 'value', label, fieldtype: 'Data', reqd: 1 }],
		primary_action_label: __('Run'),
		primary_action() {
			const v = (d.get_value('value') || '').trim();
			if (!v) {
				frappe.msgprint({ message: __('Value is required.'), indicator: 'orange' });
				return;
			}
			d.hide();
			on_submit(v);
		},
	});
	d.show();
}

frappe.ui.form.on('STD Template', {
	refresh(frm) {
		if (frm.is_new() || !frm.doc.name) {
			return;
		}

		const method =
			'kentender_procurement.kentender_procurement.doctype.std_template.std_template.get_template_package_summary';

		frappe
			.call({
				method,
				args: { template_name: frm.doc.name },
				freeze: true,
				freeze_message: __('Loading package viewer…'),
			})
			.then((r) => {
				const msg = r.message || {};
				const field = frm.get_field('html_std_package_viewer');
				if (!field || !field.$wrapper) {
					return;
				}
				if (!msg.ok) {
					field.$wrapper.html(
						`<div class="alert alert-danger">${frappe.utils.escape_html(
							msg.error || __('Failed to build package viewer'),
						)}</div>`,
					);
					return;
				}
				field.$wrapper.html(msg.html || '');
			})
			.catch(() => {
				const field = frm.get_field('html_std_package_viewer');
				if (field && field.$wrapper) {
					field.$wrapper.html(
						`<div class="alert alert-danger">${__('Could not load package viewer.')}</div>`,
					);
				}
			});

		frm.add_custom_button(
			__('Re-import POC Package'),
			() => {
				frappe.confirm(
					__(
						'Re-run the controlled STD-WORKS-POC seed import? This updates the STD Template from the repository package.',
					),
					() => {
						const reimport =
							'kentender_procurement.kentender_procurement.doctype.std_template.std_template.reimport_std_template_package';
						frappe.call({
							method: reimport,
							args: { template_name: frm.doc.name },
							freeze: true,
							freeze_message: __('Re-importing…'),
							callback(r) {
								if (r.message && r.message.ok) {
									frappe.show_alert({ message: __('Package re-imported.'), indicator: 'green' });
									frm.reload_doc();
								} else {
									frappe.msgprint({
										title: __('Re-import'),
										message: frappe.utils.escape_html(
											(r.message && r.message.message) || __('Re-import finished; check response.'),
										),
										indicator: 'orange',
									});
									frm.reload_doc();
								}
							},
						});
					},
				);
			},
			__('STD Admin'),
		);

		const std = 'kentender_procurement.kentender_procurement.doctype.std_template.std_template';

		const demo_variant_options = [
			'VARIANT-INTERNATIONAL',
			'VARIANT-TENDER-SECURING-DECLARATION',
			'VARIANT-RESERVED-TENDER',
			'VARIANT-MISSING-SITE-VISIT-DATE',
			'VARIANT-MISSING-ALTERNATIVE-SCOPE',
			'VARIANT-SINGLE-LOT',
			'VARIANT-RETENTION-MONEY-SECURITY',
		].join('\n');

		frm.add_custom_button(
			__('Create/Open Demo Tender'),
			() => {
				frappe.call({
					method: `${std}.create_or_open_std_demo_tender`,
					args: { template_name: frm.doc.name, variant_code: null },
					freeze: true,
					freeze_message: __('Creating demo tender…'),
					callback(r) {
						const msg = r.message || {};
						if (!msg.ok) {
							frappe.msgprint({
								title: __('Demo tender'),
								message: frappe.utils.escape_html(
									msg.message || msg.error || __('Could not create demo tender.'),
								),
								indicator: 'orange',
							});
							return;
						}
						frappe.show_alert({
							message: msg.message || __('Demo tender ready.'),
							indicator: 'green',
						});
						frappe.set_route('Form', 'Procurement Tender', msg.tender);
					},
				});
			},
			__('STD Admin'),
		);

		frm.add_custom_button(
			__('Create Demo Tender (variant)'),
			() => {
				frappe.prompt(
					[
						{
							label: __('Variant code'),
							fieldname: 'variant_code',
							fieldtype: 'Select',
							options: demo_variant_options,
							reqd: 1,
						},
					],
					(values) => {
						frappe.call({
							method: `${std}.create_or_open_std_demo_tender`,
							args: {
								template_name: frm.doc.name,
								variant_code: values.variant_code,
							},
							freeze: true,
							freeze_message: __('Creating demo tender…'),
							callback(r) {
								const msg = r.message || {};
								if (!msg.ok) {
									frappe.msgprint({
										title: __('Demo tender'),
										message: frappe.utils.escape_html(
											msg.message || msg.error || __('Could not create demo tender.'),
										),
										indicator: 'orange',
									});
									return;
								}
								frappe.show_alert({
									message: msg.message || __('Demo tender ready.'),
									indicator: 'green',
								});
								frappe.set_route('Form', 'Procurement Tender', msg.tender);
							},
						});
					},
					__('Choose sample variant'),
					__('Create'),
				);
			},
			__('STD Admin'),
		);

		frm.add_custom_button(
			__('Validate Package'),
			() => {
				frappe.call({
					method: `${std}.validate_std_package`,
					args: { template_name: frm.doc.name },
					freeze: true,
					freeze_message: __('Validating package…'),
					callback(r) {
						const msg = r.message || {};
						if (!msg.html) {
							frappe.msgprint({
								title: __('Package validation'),
								message: frappe.utils.escape_html(msg.error || __('No result')),
								indicator: 'orange',
							});
							return;
						}
						std_admin_html_dialog(__('Package validation'), msg.html);
					},
				});
			},
			__('STD Admin'),
		);

		frm.add_custom_button(
			__('Trace Primary Sample Rules'),
			() => {
				frappe.call({
					method: `${std}.trace_std_rules_for_sample`,
					args: { template_name: frm.doc.name, variant_code: null },
					freeze: true,
					freeze_message: __('Tracing rules…'),
					callback(r) {
						const msg = r.message || {};
						if (msg.html) {
							std_admin_html_dialog(__('Rule trace — primary sample'), msg.html);
							return;
						}
						if (msg.error) {
							frappe.msgprint({
								title: __('Rule trace'),
								message: frappe.utils.escape_html(msg.error),
								indicator: 'orange',
							});
						}
					},
				});
			},
			__('STD Admin'),
		);

		frm.add_custom_button(
			__('Trace Variant Rules'),
			() => {
				std_admin_prompt_string(
					__('Trace variant rules'),
					__('Variant code'),
					(variant_code) => {
						frappe.call({
							method: `${std}.trace_std_rules_for_sample`,
							args: { template_name: frm.doc.name, variant_code },
							freeze: true,
							freeze_message: __('Tracing rules…'),
							callback(r) {
								const msg = r.message || {};
								if (msg.html) {
									std_admin_html_dialog(
										`${__('Rule trace — variant')} (${variant_code})`,
										msg.html,
									);
									return;
								}
								if (msg.error) {
									frappe.msgprint({
										title: __('Rule trace'),
										message: frappe.utils.escape_html(msg.error),
										indicator: 'orange',
									});
								}
							},
						});
					},
				);
			},
			__('STD Admin'),
		);

		frm.add_custom_button(
			__('Trace Tender Rules'),
			() => {
				std_admin_prompt_string(
					__('Trace tender rules'),
					__('Procurement Tender name'),
					(tender_name) => {
						frappe.call({
							method: `${std}.trace_std_rules_for_tender`,
							args: { tender_name },
							freeze: true,
							freeze_message: __('Tracing rules…'),
							callback(r) {
								const msg = r.message || {};
								if (msg.html) {
									std_admin_html_dialog(
										`${__('Rule trace — tender')} (${tender_name})`,
										msg.html,
									);
									return;
								}
								if (msg.error) {
									frappe.msgprint({
										title: __('Rule trace'),
										message: frappe.utils.escape_html(msg.error),
										indicator: 'orange',
									});
								}
							},
						});
					},
				);
			},
			__('STD Admin'),
		);
	},
});
