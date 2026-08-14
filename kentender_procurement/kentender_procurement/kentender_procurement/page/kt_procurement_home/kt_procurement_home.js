// The page_js controller owns layout and lifecycle. Keep generated Page
// scaffolding inert so it cannot race the controller during SPA navigation.
frappe.pages["kt-procurement-home"].on_page_load = function () {};
