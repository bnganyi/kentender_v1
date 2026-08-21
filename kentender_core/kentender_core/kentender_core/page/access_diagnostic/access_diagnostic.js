frappe.pages['access-diagnostic'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Access diagnostic',
		single_column: true
	});
}