// Civic Ledger component gallery — renders every component variant from the
// kentender_core.cl_components library in isolation. This is the proof of POC
// goal 2 (reuse): new pages compose from the library instead of rebuilding.
(function () {
	"use strict";

	function esc(v) {
		return frappe.utils.escape_html(String(v == null ? "" : v));
	}

	function section(id, title, html) {
		return (
			'<section class="mb-6" data-testid="kt-cl-gallery-section" data-section="' +
			esc(id) +
			'">' +
			'<h2 class="font-headline-md text-headline-md font-semibold text-on-surface mb-2">' +
			esc(title) +
			"</h2>" +
			'<div class="p-4 bg-surface-container-lowest rounded-lg border border-outline-variant">' +
			html +
			"</div></section>"
		);
	}

	function galleryHtml() {
		var comp = kentender_core.cl_components;
		var out = [];

		out.push(
			section(
				"buttons",
				__("Buttons"),
				'<div class="flex gap-2">' +
					comp.button({ label: __("Export APP"), icon: "download", variant: "outline" }) +
					comp.button({ label: __("Submit Draft"), icon: "upload_file", variant: "primary" }) +
					"</div>",
			),
		);

		out.push(
			section(
				"breadcrumbs",
				__("Breadcrumbs"),
				comp.breadcrumbs({ items: [{ label: __("Dashboard") }], current: __("Procurement Home") }),
			),
		);

		out.push(
			section(
				"status-chips",
				__("Status chips"),
				'<div class="flex gap-2 flex-wrap">' +
					comp.statusChip({ tone: "approved" }) +
					comp.statusChip({ tone: "review" }) +
					comp.statusChip({ tone: "draft" }) +
					comp.statusChip({ tone: "rejected" }) +
					"</div>",
			),
		);

		out.push(
			section(
				"kpi-cards",
				__("KPI cards"),
				'<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">' +
					comp.kpiCard({
						variant: "metric",
						tone: "emerald",
						label: __("Approved Items"),
						value: "1,245",
						icon: "verified",
						delta: __("+12% from last quarter"),
					}) +
					comp.kpiCard({
						variant: "metric",
						tone: "amber",
						label: __("Pending Review"),
						value: "84",
						icon: "pending_actions",
						delta: __("Requires HOD Action"),
					}) +
					comp.kpiCard({
						variant: "progress",
						tone: "blue",
						label: __("Estimated Budget"),
						value: "KES 4.2B",
						icon: "payments",
						progress: 65,
						progressLabel: __("65% Alloc"),
					}) +
					"</div>",
			),
		);

		out.push(
			section(
				"calendar",
				__("Calendar widget"),
				'<div class="grid grid-cols-1 md:grid-cols-12 gap-4">' +
					comp.calendarWidget({
						title: __("Upcoming Tenders"),
						items: [
							{ day: "15", month: "OCT", title: __("ICT Equipment Supply"), subtitle: __("Dept of Technology"), tone: "primary" },
							{ day: "22", month: "OCT", title: __("Road Maintenance"), subtitle: __("Ministry of Transport"), tone: "secondary" },
							{ day: "05", month: "NOV", title: __("Medical Framework"), subtitle: __("Ministry of Health"), tone: "neutral" },
						],
					}) +
					"</div>",
			),
		);

		out.push(
			section(
				"data-table",
				__("Data table"),
				comp.dataTable({
					title: __("Departmental Procurement Plans"),
					filter: {
						label: __("Filter by department"),
						options: [
							{ value: "", label: __("All Departments") },
							{ value: "health", label: __("Ministry of Health") },
							{ value: "education", label: __("Ministry of Education") },
						],
					},
					columns: [
						{ label: __("Department"), th: "pl-4" },
						{ label: __("Item Category") },
						{ label: __("Estimated Cost (KES)"), th: "text-right" },
						{ label: __("Approval Status"), th: "text-center" },
						{ label: __("Actions"), th: "pr-4 text-right" },
					],
					rows: [
						{ department: __("Ministry of Health"), category: __("Pharmaceuticals"), cost: "450,000,000", status: { tone: "approved" }, action: { icon: "visibility" } },
						{ department: __("Ministry of Education"), category: __("Textbooks & Stationery"), cost: "210,500,000", status: { tone: "review" }, action: { icon: "visibility" } },
						{ department: __("Dept of ICT"), category: __("Hardware & Licenses"), cost: "85,000,000", status: { tone: "draft" }, action: { icon: "edit" } },
					],
					footerText: __("Showing 1-3 of 42 entries"),
				}),
			),
		);

		out.push(
			section(
				"top-bar",
				__("Top bar"),
				comp.topBar({
					breadcrumbs: [
						{ label: __("Dashboard") },
						{ label: __("Tender Management") },
					],
					showSearch: false,
					showUserMeta: true,
				})
			)
		);

		return (
			'<div class="kt-cl-shell kt-cl-gallery" data-testid="kt-cl-gallery">' +
			'<div class="max-w-[1280px] mx-auto p-4 space-y-4">' +
			out.join("") +
			"</div></div>"
		);
	}

	frappe.pages["kt-cl-components"].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Civic Ledger Components"),
			single_column: true,
		});

		$(page.main).html(galleryHtml());
		if (kentender_core.cl_components.bindBreadcrumbRoutes) {
			kentender_core.cl_components.bindBreadcrumbRoutes(page.main);
		}
	};
})();
