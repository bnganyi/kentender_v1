// Copyright (c) 2026, KenTender and contributors
// STD Administration Console POC — Admin Steps 3–4 (viewer + validation + rule trace)
// STD-GOV-011 — governance Desk actions (doc 7 §20) under "STD Governance"

const KENTENDER_STD_TEMPLATE =
	'kentender_procurement.kentender_procurement.doctype.std_template.std_template';

const STD_GOV_LIFECYCLE = {
	IMPORTED: 'Imported',
	VALIDATION_FAILED: 'Validation Failed',
	VALIDATED: 'Validated',
	SUBMITTED: 'Submitted for Approval',
	RETURNED: 'Returned for Correction',
	REJECTED: 'Rejected',
	APPROVED: 'Approved',
	ACTIVE: 'Active',
	SUSPENDED: 'Suspended',
	SUPERSEDED: 'Superseded',
	RETIRED: 'Retired',
	ARCHIVED: 'Archived',
};

const STD_GOV_CONTROLLED_REPLACEMENT = [
	STD_GOV_LIFECYCLE.IMPORTED,
	STD_GOV_LIFECYCLE.VALIDATION_FAILED,
	STD_GOV_LIFECYCLE.VALIDATED,
	STD_GOV_LIFECYCLE.RETURNED,
];

function std_gov_roles() {
	return frappe.boot?.user?.roles || frappe.user_roles || [];
}

function std_gov_is_site_administrator() {
	return frappe.session.user === 'Administrator';
}

function std_gov_has_role(role) {
	return std_gov_is_site_administrator() || std_gov_roles().includes(role);
}

function std_gov_can_run_validation() {
	return (
		std_gov_is_site_administrator() ||
		std_gov_has_role('System Manager') ||
		std_gov_has_role('STD Template Administrator')
	);
}

function std_gov_can_replace_package(frm) {
	if (!STD_GOV_CONTROLLED_REPLACEMENT.includes(frm.doc.lifecycle_status)) {
		return false;
	}
	if (std_gov_is_site_administrator() || std_gov_has_role('System Manager')) {
		return true;
	}
	if (std_gov_has_role('STD Template Administrator')) {
		return true;
	}
	if (std_gov_has_role('STD Template Importer') && frm.doc.imported_by === frappe.session.user) {
		return true;
	}
	return false;
}

function std_gov_can_submit(frm) {
	if (frm.doc.lifecycle_status !== STD_GOV_LIFECYCLE.VALIDATED) {
		return false;
	}
	if (!(std_gov_is_site_administrator() || std_gov_has_role('System Manager') || std_gov_has_role('STD Template Administrator'))) {
		return false;
	}
	if (!frm.doc.validation_is_current) {
		return false;
	}
	const st = frm.doc.latest_validation_status || '';
	return ['Pass', 'Pass with Warnings'].includes(st);
}

function std_gov_can_return(frm) {
	if (frm.doc.lifecycle_status !== STD_GOV_LIFECYCLE.SUBMITTED) {
		return false;
	}
	return (
		std_gov_is_site_administrator() ||
		std_gov_has_role('System Manager') ||
		std_gov_has_role('STD Template Reviewer') ||
		std_gov_has_role('STD Template Approver')
	);
}

function std_gov_can_reject(frm) {
	if (frm.doc.lifecycle_status !== STD_GOV_LIFECYCLE.SUBMITTED) {
		return false;
	}
	return std_gov_is_site_administrator() || std_gov_has_role('System Manager') || std_gov_has_role('STD Template Approver');
}

function std_gov_can_approve(frm) {
	return std_gov_can_reject(frm);
}

function std_gov_can_activate_ops() {
	return (
		std_gov_is_site_administrator() ||
		std_gov_has_role('System Manager') ||
		std_gov_has_role('STD Template Activator')
	);
}

function std_gov_can_archive() {
	return (
		std_gov_is_site_administrator() ||
		std_gov_has_role('System Manager') ||
		std_gov_has_role('STD Template Administrator')
	);
}

function std_gov_can_snapshot() {
	return (
		std_gov_is_site_administrator() ||
		std_gov_has_role('System Manager') ||
		std_gov_has_role('STD Template Administrator') ||
		std_gov_has_role('STD Template Auditor')
	);
}

function std_gov_json_dialog(title, obj) {
	const body = `<pre style="max-height:70vh;overflow:auto;">${frappe.utils.escape_html(
		JSON.stringify(obj, null, 2),
	)}</pre>`;
	std_admin_html_dialog(title, body);
}

function std_gov_call(method, args, opts) {
	frappe.call({
		method: `${KENTENDER_STD_TEMPLATE}.${method}`,
		args,
		freeze: true,
		freeze_message: opts?.freeze_message || __('Working…'),
		callback(r) {
			if (r.exc) {
				frappe.msgprint({ title: __('Error'), message: __('Request failed.'), indicator: 'red' });
				return;
			}
			const msg = r.message || {};
			if (opts?.on_message) {
				opts.on_message(msg);
			}
		},
	});
}

function std_governance_add_buttons(frm) {
	const g = __('STD Governance');

	const add = (label, fn, show) => {
		if (!show) {
			return;
		}
		frm.add_custom_button(__(label), fn, g);
	};

	add(
		'Replace Package',
		() => {
			const d = new frappe.ui.Dialog({
				title: __('Replace STD package'),
				fields: [
					{
						fieldname: 'reason',
						label: __('Reason'),
						fieldtype: 'Small Text',
						reqd: 1,
					},
					{
						fieldname: 'package_json',
						label: __('package_json (JSON object)'),
						fieldtype: 'Code',
						options: 'JSON',
						reqd: 1,
					},
					{
						fieldname: 'manifest_json',
						label: __('manifest_json (optional JSON object)'),
						fieldtype: 'Code',
						options: 'JSON',
						reqd: 0,
					},
				],
				primary_action_label: __('Replace'),
				primary_action() {
					const reason = (d.get_value('reason') || '').trim();
					const package_json = (d.get_value('package_json') || '').trim();
					const manifest_json = (d.get_value('manifest_json') || '').trim();
					if (!reason || !package_json) {
						frappe.msgprint({ message: __('Reason and package_json are required.'), indicator: 'orange' });
						return;
					}
					d.hide();
					std_gov_call(
						'replace_std_template_package',
						{
							std_template: frm.doc.name,
							package_json,
							manifest_json: manifest_json || null,
							reason,
						},
						{
							freeze_message: __('Replacing package…'),
							on_message(msg) {
								if (msg && msg.ok) {
									frappe.show_alert({ message: __('Package replaced.'), indicator: 'green' });
									frm.reload_doc();
								} else {
									frappe.msgprint({ message: __('Unexpected response'), indicator: 'orange' });
									frm.reload_doc();
								}
							},
						},
					);
				},
			});
			d.show();
		},
		std_gov_can_replace_package(frm) && (frm.perm?.[0]?.write || frappe.model.can_write('STD Template')),
	);

	add(
		'Run Governance Validation',
		() => {
			std_gov_call(
				'run_std_template_validation',
				{ std_template: frm.doc.name },
				{
					freeze_message: __('Running governance validation…'),
					on_message(msg) {
						frappe.show_alert({
							message: (msg && msg.status) || __('Validation finished'),
							indicator: msg && msg.ok ? 'green' : 'orange',
						});
						frm.reload_doc();
					},
				},
			);
		},
		std_gov_can_run_validation(),
	);

	add(
		'Submit for Approval',
		() => {
			frappe.prompt(
				[
					{
						fieldname: 'comment',
						label: __('Comment (optional)'),
						fieldtype: 'Small Text',
						reqd: 0,
					},
				],
				(values) => {
					std_gov_call(
						'submit_std_template_for_approval',
						{ std_template: frm.doc.name, comment: values.comment || '' },
						{
							freeze_message: __('Submitting…'),
							on_message(msg) {
								if (msg && msg.ok) {
									frappe.show_alert({ message: __('Submitted.'), indicator: 'green' });
								}
								frm.reload_doc();
							},
						},
					);
				},
				__('Submit for approval'),
				__('Submit'),
			);
		},
		std_gov_can_submit(frm),
	);

	add(
		'Return for Correction',
		() => {
			frappe.prompt(
				[
					{
						fieldname: 'reason',
						label: __('Return reason'),
						fieldtype: 'Small Text',
						reqd: 1,
					},
				],
				(values) => {
					const reason = (values.reason || '').trim();
					if (!reason) {
						return;
					}
					std_gov_call(
						'return_std_template_for_correction',
						{ std_template: frm.doc.name, reason },
						{
							freeze_message: __('Returning…'),
							on_message(msg) {
								if (msg && msg.ok) {
									frappe.show_alert({ message: __('Returned.'), indicator: 'green' });
								}
								frm.reload_doc();
							},
						},
					);
				},
				__('Return for correction'),
				__('Return'),
			);
		},
		std_gov_can_return(frm),
	);

	add(
		'Reject',
		() => {
			frappe.prompt(
				[
					{
						fieldname: 'reason',
						label: __('Rejection reason'),
						fieldtype: 'Small Text',
						reqd: 1,
					},
				],
				(values) => {
					const reason = (values.reason || '').trim();
					if (!reason) {
						return;
					}
					std_gov_call(
						'reject_std_template',
						{ std_template: frm.doc.name, reason },
						{
							freeze_message: __('Rejecting…'),
							on_message(msg) {
								if (msg && msg.ok) {
									frappe.show_alert({ message: __('Rejected.'), indicator: 'green' });
								}
								frm.reload_doc();
							},
						},
					);
				},
				__('Reject STD template'),
				__('Reject'),
			);
		},
		std_gov_can_reject(frm),
	);

	add(
		'Approve',
		() => {
			const fields = [
				{
					fieldname: 'comments',
					label: __('Approval comments'),
					fieldtype: 'Small Text',
					reqd: 1,
				},
			];
			if (std_gov_has_role('System Manager')) {
				fields.push({
					fieldname: 'override_reason',
					label: __('Override reason (SoD / System Manager only)'),
					fieldtype: 'Small Text',
					reqd: 0,
				});
			}
			frappe.prompt(
				fields,
				(values) => {
					const comments = (values.comments || '').trim();
					if (!comments) {
						return;
					}
					const override_reason = (values.override_reason || '').trim() || null;
					std_gov_call(
						'approve_std_template',
						{ std_template: frm.doc.name, comments, override_reason },
						{
							freeze_message: __('Approving…'),
							on_message(msg) {
								if (msg && msg.ok) {
									frappe.show_alert({ message: __('Approved.'), indicator: 'green' });
								}
								frm.reload_doc();
							},
						},
					);
				},
				__('Approve STD template'),
				__('Approve'),
			);
		},
		std_gov_can_approve(frm),
	);

	add(
		'Activate',
		() => {
			const d = new frappe.ui.Dialog({
				title: __('Activate STD template'),
				fields: [
					{ fieldname: 'reason', label: __('Activation reason'), fieldtype: 'Small Text', reqd: 1 },
					{ fieldname: 'active_from', label: __('Active from'), fieldtype: 'Date', reqd: 0 },
					{ fieldname: 'active_until', label: __('Active until'), fieldtype: 'Date', reqd: 0 },
					{
						fieldname: 'is_default_active_version',
						label: __('Default active version for profile'),
						fieldtype: 'Check',
						default: 1,
					},
				],
				primary_action_label: __('Activate'),
				primary_action() {
					const reason = (d.get_value('reason') || '').trim();
					if (!reason) {
						return;
					}
					d.hide();
					std_gov_call(
						'activate_std_template',
						{
							std_template: frm.doc.name,
							reason,
							active_from: d.get_value('active_from') || null,
							active_until: d.get_value('active_until') || null,
							is_default_active_version: d.get_value('is_default_active_version') ? 1 : 0,
						},
						{
							freeze_message: __('Activating…'),
							on_message(msg) {
								if (msg && msg.ok) {
									frappe.show_alert({ message: __('Activated.'), indicator: 'green' });
								}
								frm.reload_doc();
							},
						},
					);
				},
			});
			d.show();
		},
		frm.doc.lifecycle_status === STD_GOV_LIFECYCLE.APPROVED && std_gov_can_activate_ops(),
	);

	add(
		'Suspend',
		() => {
			frappe.prompt(
				[{ fieldname: 'reason', label: __('Suspension reason'), fieldtype: 'Small Text', reqd: 1 }],
				(values) => {
					const reason = (values.reason || '').trim();
					if (!reason) {
						return;
					}
					std_gov_call(
						'suspend_std_template',
						{ std_template: frm.doc.name, reason },
						{
							freeze_message: __('Suspending…'),
							on_message(msg) {
								if (msg && msg.ok) {
									frappe.show_alert({ message: __('Suspended.'), indicator: 'green' });
								}
								frm.reload_doc();
							},
						},
					);
				},
				__('Suspend'),
				__('Confirm'),
			);
		},
		frm.doc.lifecycle_status === STD_GOV_LIFECYCLE.ACTIVE && std_gov_can_activate_ops(),
	);

	add(
		'Reinstate',
		() => {
			frappe.prompt(
				[{ fieldname: 'reason', label: __('Reinstatement reason'), fieldtype: 'Small Text', reqd: 1 }],
				(values) => {
					const reason = (values.reason || '').trim();
					if (!reason) {
						return;
					}
					std_gov_call(
						'reinstate_std_template',
						{ std_template: frm.doc.name, reason },
						{
							freeze_message: __('Reinstating…'),
							on_message(msg) {
								if (msg && msg.ok) {
									frappe.show_alert({ message: __('Reinstated.'), indicator: 'green' });
								}
								frm.reload_doc();
							},
						},
					);
				},
				__('Reinstate'),
				__('Confirm'),
			);
		},
		frm.doc.lifecycle_status === STD_GOV_LIFECYCLE.SUSPENDED && std_gov_can_activate_ops(),
	);

	add(
		'Supersede',
		() => {
			frappe.prompt(
				[
					{
						fieldname: 'replacement_template',
						label: __('Replacement STD Template (name)'),
						fieldtype: 'Data',
						reqd: 1,
					},
					{ fieldname: 'reason', label: __('Supersession reason'), fieldtype: 'Small Text', reqd: 1 },
					{ fieldname: 'effective_date', label: __('Effective date'), fieldtype: 'Date', reqd: 0 },
				],
				(values) => {
					const replacement_template = (values.replacement_template || '').trim();
					const reason = (values.reason || '').trim();
					if (!replacement_template || !reason) {
						return;
					}
					std_gov_call(
						'supersede_std_template',
						{
							std_template: frm.doc.name,
							replacement_template,
							reason,
							effective_date: values.effective_date || null,
						},
						{
							freeze_message: __('Superseding…'),
							on_message(msg) {
								if (msg && msg.ok) {
									frappe.show_alert({ message: __('Superseded.'), indicator: 'green' });
								}
								frm.reload_doc();
							},
						},
					);
				},
				__('Supersede'),
				__('Confirm'),
			);
		},
		[STD_GOV_LIFECYCLE.ACTIVE, STD_GOV_LIFECYCLE.SUSPENDED].includes(frm.doc.lifecycle_status) &&
			std_gov_can_activate_ops(),
	);

	add(
		'Retire',
		() => {
			frappe.prompt(
				[{ fieldname: 'reason', label: __('Retirement reason'), fieldtype: 'Small Text', reqd: 1 }],
				(values) => {
					const reason = (values.reason || '').trim();
					if (!reason) {
						return;
					}
					std_gov_call(
						'retire_std_template',
						{ std_template: frm.doc.name, reason },
						{
							freeze_message: __('Retiring…'),
							on_message(msg) {
								if (msg && msg.ok) {
									frappe.show_alert({ message: __('Retired.'), indicator: 'green' });
								}
								frm.reload_doc();
							},
						},
					);
				},
				__('Retire'),
				__('Confirm'),
			);
		},
		[STD_GOV_LIFECYCLE.ACTIVE, STD_GOV_LIFECYCLE.SUSPENDED, STD_GOV_LIFECYCLE.APPROVED].includes(
			frm.doc.lifecycle_status,
		) && std_gov_can_activate_ops(),
	);

	add(
		'Archive',
		() => {
			frappe.prompt(
				[{ fieldname: 'reason', label: __('Archive reason'), fieldtype: 'Small Text', reqd: 1 }],
				(values) => {
					const reason = (values.reason || '').trim();
					if (!reason) {
						return;
					}
					std_gov_call(
						'archive_std_template',
						{ std_template: frm.doc.name, reason },
						{
							freeze_message: __('Archiving…'),
							on_message(msg) {
								if (msg && msg.ok) {
									frappe.show_alert({ message: __('Archived.'), indicator: 'green' });
								}
								frm.reload_doc();
							},
						},
					);
				},
				__('Archive'),
				__('Confirm'),
			);
		},
		[STD_GOV_LIFECYCLE.REJECTED, STD_GOV_LIFECYCLE.RETIRED, STD_GOV_LIFECYCLE.SUPERSEDED].includes(
			frm.doc.lifecycle_status,
		) && std_gov_can_archive(),
	);

	add(
		'Generate Governance Snapshot',
		() => {
			std_gov_call(
				'generate_std_template_governance_snapshot',
				{ std_template: frm.doc.name },
				{
					freeze_message: __('Generating snapshot…'),
					on_message(msg) {
						if (msg && msg.ok) {
							frappe.show_alert({ message: __('Snapshot generated.'), indicator: 'green' });
						}
						frm.reload_doc();
					},
				},
			);
		},
		std_gov_can_snapshot(),
	);

	add(
		'View Governance Summary',
		() => {
			std_gov_call(
				'get_std_template_governance_summary',
				{ std_template: frm.doc.name },
				{
					freeze_message: __('Loading…'),
					on_message(msg) {
						std_gov_json_dialog(__('Governance summary'), msg);
					},
				},
			);
		},
		true,
	);

	add(
		'View Usage Impact',
		() => {
			std_gov_call(
				'get_std_template_usage_impact',
				{ std_template: frm.doc.name },
				{
					freeze_message: __('Loading…'),
					on_message(msg) {
						std_gov_json_dialog(__('Usage impact'), msg);
					},
				},
			);
		},
		true,
	);

	add(
		'View Audit Timeline',
		() => {
			std_gov_call(
				'get_std_template_audit_timeline',
				{ std_template: frm.doc.name },
				{
					freeze_message: __('Loading…'),
					on_message(msg) {
						std_gov_json_dialog(__('Audit timeline'), msg);
					},
				},
			);
		},
		true,
	);
}

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

		frm.clear_custom_buttons();
		std_governance_add_buttons(frm);

		const method = `${KENTENDER_STD_TEMPLATE}.get_template_package_summary`;

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
						const reimport = `${KENTENDER_STD_TEMPLATE}.reimport_std_template_package`;
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
					method: `${KENTENDER_STD_TEMPLATE}.create_or_open_std_demo_tender`,
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
							method: `${KENTENDER_STD_TEMPLATE}.create_or_open_std_demo_tender`,
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
					method: `${KENTENDER_STD_TEMPLATE}.validate_std_package`,
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
					method: `${KENTENDER_STD_TEMPLATE}.trace_std_rules_for_sample`,
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
							method: `${KENTENDER_STD_TEMPLATE}.trace_std_rules_for_sample`,
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
							method: `${KENTENDER_STD_TEMPLATE}.trace_std_rules_for_tender`,
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
