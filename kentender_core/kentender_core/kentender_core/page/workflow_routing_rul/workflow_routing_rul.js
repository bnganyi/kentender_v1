frappe.pages['workflow-routing-rul'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Workflow routing rule',
		single_column: true
	});
}