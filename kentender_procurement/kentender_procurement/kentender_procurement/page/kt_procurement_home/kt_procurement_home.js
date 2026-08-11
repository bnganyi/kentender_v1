frappe.pages['kt-procurement-home'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Procurement Home',
		single_column: true
	});
}