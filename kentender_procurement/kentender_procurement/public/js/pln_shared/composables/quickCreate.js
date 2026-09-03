// Wraps Frappe's native "+ Create a new X" quick-entry dialog — the same
// affordance frappe.ui.form.ControlLink offers on a standard Link field —
// so a plain <select> lookup can create a missing option without abandoning
// the form underneath it. Only fits simple, directly-creatable catalogues
// (a few required fields, no governed multi-step lifecycle).
//
// Resolves with the created doc on save. A cancelled dialog never resolves —
// nothing here needs to react to "the user changed their mind".
export function quickCreate(doctype) {
	return new Promise((resolve) => {
		frappe.ui.form.make_quick_entry(doctype, (doc) => resolve(doc));
	});
}
