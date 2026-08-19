frappe.pages['support-plan-view'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Support read-only Plan',
		single_column: true
	});
}