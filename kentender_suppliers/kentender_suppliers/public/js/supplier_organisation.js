// BDS-CHG-001 v0.8 plan OD-D — the Supplier Account support officer's two
// access actions on the standard form. The server decides who may act and
// checks the reason and record version; the form only collects the reason.
frappe.ui.form.on("Supplier Organisation", {
	refresh(frm) {
		if (frm.is_new()) return;
		const suspended = frm.doc.account_status === "Suspended";
		const label = suspended ? __("Restore access") : __("Suspend access");
		const method = suspended ? "restore_supplier_account" : "suspend_supplier_account";
		frm.add_custom_button(label, () => {
			frappe.prompt(
				[{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason"), reqd: 1, description: __("10 to 500 characters.") }],
				(values) => {
					frappe.call({
						method: `kentender_suppliers.supplier_accounts.api.${method}`,
						args: { organisation: frm.doc.name, reason: values.reason, expected_version: frm.doc.record_version, idempotency_key: frappe.utils.get_random(24) },
						freeze: true,
					}).then((r) => {
						const result = r.message || {};
						if (result.ok === false) {
							frappe.msgprint(Object.values(result.errors || {}).join(" ") || result.message);
							return;
						}
						frappe.show_alert({ message: suspended ? __("Access restored") : __("Access suspended"), indicator: "green" });
						frm.reload_doc();
					});
				},
				label,
				label
			);
		});
	},
});
