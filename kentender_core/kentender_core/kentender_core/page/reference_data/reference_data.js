frappe.pages['reference-data'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Reference Data',
		single_column: true
	});
}