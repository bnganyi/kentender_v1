// Copyright (c) 2026, KenTender and contributors
// Doc 9 §22.2 — primary Tender Management UX is the workbench, not raw DocType forms.

frappe.ui.form.on("TM2 Tender", {
	refresh(frm) {
		frm.clear_custom_buttons();
		frm.add_custom_button(
			__("Open Tender Management"),
			() => {
				frappe.set_route("tender-management-v2");
			},
			__("Workbench"),
		);
	},
});
