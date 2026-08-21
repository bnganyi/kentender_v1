frappe.pages['user-operational-acc'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'User operational access',
		single_column: true
	});
}