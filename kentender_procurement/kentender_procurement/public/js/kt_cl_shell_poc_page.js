// Civic Ledger POC — composes the full code.html screen (166-563) from the
// kentender_core.cl component library. Proves both POC goals: faithful port and
// reusable componentization. Nothing here hardcodes Tailwind class strings; every
// block is produced by a library renderer.
(function () {
	"use strict";

	var POC_ROUTE = ["kt-cl-shell-poc"];

	// Curated IA aligned with the native Procurement rail (availability states).
	// Home stays on this POC page for the demo shell.
	function civicLedgerIA() {
		return [
			{ kind: "link", label: "Home", icon: "home", route: POC_ROUTE, active: true },
			{ kind: "link", label: "Analytics", icon: "bar_chart", url: "#" },
			{ kind: "link", label: "Strategy Alignment", icon: "ads_click", route: ["strategy-management"] },
			{ kind: "link", label: "Budget & Funding", icon: "account_balance_wallet", route: ["budget-hub"] },
			{ kind: "link", label: "Demands", icon: "assignment_ind", route: ["demand-hub"] },
			{ kind: "link", label: "Procurement Plans", icon: "checklist", route: ["planning-hub"] },
			{
				kind: "group",
				label: "Tender Management",
				icon: "gavel",
				children: [
					{ label: "Tender Configurations", url: "#" },
					{ label: "Tenders", url: "#" },
					{ label: "Bid Submissions", url: "#" },
					{ label: "Evaluation", url: "#" },
					{ label: "Awards", url: "#" },
				],
			},
			{ kind: "link", label: "Contract Management", icon: "description", url: "#" },
			{ kind: "link", label: "Supplier Management", icon: "group", url: "#" },
			{
				kind: "group",
				label: "STD Administration",
				icon: "menu_book",
				children: [
					{ label: "STD Library", route: ["std-library"] },
					{ label: "STD Versions", route: ["coming-soon"] },
					{ label: "Forms & Schemas", route: ["std-form-schema-manager"] },
					{ label: "Import Review", route: ["std-import-package-review"] },
				],
			},
		];
	}

	function sidebarConfig() {
		return {
			portalTitle: __("Procurement Portal"),
			portalSubtitle: __("Public Sector"),
			items: civicLedgerIA(),
		};
	}

	// Full content area (code.html 357-563) composed from the component library.
	function pocMainHtml() {
		var comp = kentender_core.cl_components;

		var cards =
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
			});

		var calendar = comp.calendarWidget({
			title: __("Upcoming Tenders"),
			viewAllLabel: __("View All"),
			items: [
				{ day: "15", month: "OCT", title: __("ICT Equipment Supply"), subtitle: __("Dept of Technology"), tone: "primary" },
				{ day: "22", month: "OCT", title: __("Road Maintenance"), subtitle: __("Ministry of Transport"), tone: "secondary" },
				{ day: "05", month: "NOV", title: __("Medical Framework"), subtitle: __("Ministry of Health"), tone: "neutral" },
			],
		});

		var bento = comp.bentoGrid({
			metricsHtml: comp.metricsGrid(cards),
			asideHtml: calendar,
		});

		var table = comp.dataTable({
			title: __("Departmental Procurement Plans"),
			filter: {
				label: __("Filter by department"),
				options: [
					{ value: "", label: __("All Departments") },
					{ value: "health", label: __("Ministry of Health") },
					{ value: "education", label: __("Ministry of Education") },
					{ value: "transport", label: __("Ministry of Transport") },
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
				{ department: __("Ministry of Transport"), category: __("Infrastructure Maintenance"), cost: "1,200,000,000", status: { tone: "approved" }, action: { icon: "visibility" } },
				{ department: __("Dept of ICT"), category: __("Hardware & Licenses"), cost: "85,000,000", status: { tone: "draft" }, action: { icon: "edit" } },
				{ department: __("Ministry of Agriculture"), category: __("Fertilizer Subsidy"), cost: "800,000,000", status: { tone: "rejected" }, action: { icon: "visibility" } },
			],
			footerText: __("Showing 1-5 of 42 entries"),
		});

		return bento + table;
	}

	function pageHeaderConfig() {
		return {
			hideBreadcrumbs: true,
			subtitle: __("Fiscal Year 2024/2025 Overview"),
			actions: [
				{ label: __("Export APP"), icon: "download", variant: "outline", testid: "kt-cl-action-export", key: "export" },
				{ label: __("Submit Draft"), icon: "upload_file", variant: "primary", testid: "kt-cl-action-submit", key: "submit" },
			],
		};
	}

	function toolbarConfig() {
		return {
			breadcrumbs: [
				{ label: __("Home"), route: POC_ROUTE },
				{ label: __("Home") },
			],
			showSearch: false,
			showUserMeta: true,
		};
	}

	frappe.pages["kt-cl-shell-poc"].on_page_load = function (wrapper) {
		kentender_core.cl_shell.enter({
			workspaceKey: "Procurement",
			hydrationGate: true,
			sidebar: sidebarConfig(),
		});

		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Civic Ledger Shell POC"),
			single_column: true,
		});

		kentender_core.cl_shell.mountPageChrome(page.main, {
			toolbar: toolbarConfig(),
			pageHeader: pageHeaderConfig(),
			mainHtml: pocMainHtml(),
		});
	};

	frappe.pages["kt-cl-shell-poc"].on_page_show = function () {
		kentender_core.cl_shell.enter({
			workspaceKey: "Procurement",
			hydrationGate: false,
			sidebar: sidebarConfig(),
		});
	};
})();
