// Canonical markup/class strings from IT-STD-Wizard-v3/B-Components/code.html.
// This file is the single source of truth for every Civic Ledger class string;
// kt_cl_components.js / kt_cl_sidebar.js consume it, and the Python parity guard
// asserts these markers exist in both code.html and the rendered output.
frappe.provide("kentender_core.cl_code_spec");

(function () {
	"use strict";

	// ---- Sidebar (code.html 166-307) ------------------------------------
	var SIDENAV_ROOT =
		"fixed left-0 top-0 h-screen z-50 hidden md:flex flex-col w-64 bg-surface-container-low border-r border-outline-variant";

	var NAV_LINK_ACTIVE =
		"flex items-center gap-3 px-4 py-2 text-primary bg-primary-fixed-dim/20 font-bold border-r-4 border-primary cursor-pointer transition-all duration-200";

	var NAV_LINK =
		"flex items-center gap-3 px-4 py-2 text-on-surface-variant hover:bg-surface-container-high transition-colors cursor-pointer transition-all duration-200";

	var NAV_PARENT =
		"flex items-center justify-between px-4 py-2 text-on-surface-variant font-bold mt-2 mb-1 cursor-pointer";

	// Two-level sub-navigation (children of a collapsible group).
	// Refined beyond the code.html mock (see kt_cl_code_layout.css): the raw
	// mock utilities ("flex items-center px-4 py-1.5 text-on-surface-variant
	// hover:text-primary ...") are replaced by semantic classes so the children
	// get cleaner indentation, one tree connector line aligned to the parent
	// icon centre, tight consistent spacing, and clear hover/active states.
	var NAV_CHILDREN_LIST = "kt-cl-nav-children";
	var NAV_CHILD = "kt-cl-nav-child";
	var NAV_CHILD_ACTIVE = "kt-cl-nav-child is-active";

	var NAV_FOOTER_LINK =
		"flex items-center gap-3 px-3 py-1.5 rounded text-on-surface-variant hover:bg-surface-container-high transition-colors cursor-pointer transition-all duration-200";

	// ---- Top bar (C1-M1 code-in-progress.html TopAppBar) --------------
	var TOOLBAR_ROOT =
		"sticky top-0 z-40 flex justify-between items-center px-6 w-full bg-surface-container-lowest border-b border-outline-variant h-16 shrink-0";
	/* Toolbar context trail (ancestors; last crumb bold). */
	var BREADCRUMB_TOOLBAR =
		"text-sm font-label-md text-on-surface-variant flex items-center gap-2";

	// ---- Page header (code.html 337-356 + DESIGN.md display title) ------
	var BREADCRUMB_ROOT = "flex items-center gap-1 mb-1";
	/* Semantic class + token utilities; layout CSS asserts DESIGN.md display size
	 * until civic_ledger.css is regenerated with text-display/font-display. */
	var PAGE_TITLE = "kt-cl-page-title text-display font-display font-bold text-primary";

	var BTN_OUTLINE =
		"px-3 py-1.5 rounded border border-primary text-primary hover:bg-primary-fixed/10 transition-colors font-label-md text-label-md flex items-center gap-1.5";
	var BTN_PRIMARY =
		"px-3 py-1.5 rounded bg-primary text-on-primary hover:bg-primary-fixed-variant transition-colors font-label-md text-label-md flex items-center gap-1.5";

	// ---- Bento grid (code.html 358-360) ---------------------------------
	var BENTO_GRID = "grid grid-cols-1 md:grid-cols-12 gap-4";
	var METRICS_WRAP = "md:col-span-8 grid grid-cols-1 sm:grid-cols-3 gap-4";

	// ---- KPI cards (code.html 362-405) ----------------------------------
	var KPI_VALUE = "text-3xl font-bold text-on-surface";
	var KPI_VALUE_ROW = "flex items-center gap-3 mt-2";
	var KPI = {
		metric: {
			emerald: {
				card: "bg-gradient-to-br from-emerald-50 to-white dark:from-emerald-900/20 dark:to-surface border border-emerald-200 dark:border-emerald-800/50 rounded-lg p-4 flex flex-row items-center justify-between sm:flex-col sm:items-start sm:justify-between shadow-sm hover:shadow-md transition-shadow",
				label: "font-label-md text-label-md text-emerald-800 dark:text-emerald-300 uppercase tracking-wider font-semibold",
				badgeInline:
					"p-2 bg-emerald-100 text-emerald-600 dark:bg-emerald-800 dark:text-emerald-300 rounded-full hidden sm:inline-flex shadow-sm",
				badgeMobile:
					"p-2 bg-emerald-100 text-emerald-600 dark:bg-emerald-800 dark:text-emerald-300 rounded sm:hidden shadow-sm",
				delta: "font-body-sm text-body-sm text-emerald-700 dark:text-emerald-400 mt-1 font-medium",
			},
			amber: {
				card: "bg-gradient-to-br from-amber-50 to-white dark:from-amber-900/20 dark:to-surface border border-amber-200 dark:border-amber-800/50 rounded-lg p-4 flex flex-row items-center justify-between sm:flex-col sm:items-start sm:justify-between shadow-sm hover:shadow-md transition-shadow",
				label: "font-label-md text-label-md text-amber-800 dark:text-amber-300 uppercase tracking-wider font-semibold",
				badgeInline:
					"p-2 bg-amber-100 text-amber-600 dark:bg-amber-800 dark:text-amber-300 rounded-full hidden sm:inline-flex shadow-sm",
				badgeMobile:
					"p-2 bg-amber-100 text-amber-600 dark:bg-amber-800 dark:text-amber-300 rounded sm:hidden shadow-sm",
				delta: "font-body-sm text-body-sm text-amber-700 dark:text-amber-400 mt-1 font-medium",
			},
		},
		progress: {
			blue: {
				card: "bg-gradient-to-br from-blue-50 to-white dark:from-blue-900/20 dark:to-surface border border-blue-200 dark:border-blue-800/50 rounded-lg p-4 flex flex-col justify-between shadow-sm hover:shadow-md transition-shadow",
				label: "font-label-md text-label-md text-blue-800 dark:text-blue-300 uppercase tracking-wider font-semibold",
				badge: "p-2 bg-blue-100 text-blue-600 dark:bg-blue-800 dark:text-blue-300 rounded-full shadow-sm",
				track: "w-full bg-blue-100 dark:bg-blue-900 h-1.5 rounded-full overflow-hidden",
				fill: "bg-blue-600 h-full rounded-full shadow-sm",
				pct: "font-body-sm text-body-sm text-blue-700 dark:text-blue-400 whitespace-nowrap text-right font-medium",
			},
		},
	};

	// ---- Calendar widget (code.html 407-447) ----------------------------
	var CALENDAR = {
		widget:
			"md:col-span-4 bg-surface-container-lowest border border-outline-variant rounded-lg p-3 flex flex-col hover:shadow-[0px_2px_8px_rgba(0,0,0,0.05)] transition-shadow",
		header: "flex justify-between items-center mb-2 border-b border-outline-variant pb-2",
		title: "font-headline-md text-headline-md font-semibold text-on-surface",
		viewAll: "text-secondary hover:text-on-secondary-container font-label-sm text-label-sm",
		list: "flex-1 overflow-y-auto space-y-1 pr-1 max-h-[140px]",
		item: "flex items-center gap-3 p-1.5 rounded bg-surface-container-low border border-transparent hover:border-outline-variant transition-colors",
		dateBox: {
			primary:
				"flex flex-col items-center justify-center bg-primary-container/10 text-primary-container rounded p-1 min-w-[36px]",
			secondary:
				"flex flex-col items-center justify-center bg-secondary/10 text-secondary rounded p-1 min-w-[36px]",
			neutral:
				"flex flex-col items-center justify-center bg-surface-container-high text-on-surface-variant rounded p-1 min-w-[36px]",
		},
		day: "font-label-md text-label-md font-bold",
		month: "font-label-sm text-[9px]",
		body: "min-w-0 flex-1",
		itemTitle: "font-body-md text-body-md font-medium text-on-surface truncate",
		itemSubtitle: "font-body-sm text-body-sm text-on-surface-variant truncate",
	};

	// ---- Data table (code.html 449-563) ---------------------------------
	var TABLE = {
		root: "bg-surface-container-lowest border border-outline-variant rounded-lg flex flex-col hover:shadow-[0px_2px_8px_rgba(0,0,0,0.05)] transition-shadow",
		head: "p-3 border-b border-outline-variant flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3",
		title: "font-headline-md text-headline-md font-semibold text-on-surface",
		filterWrap: "relative w-full sm:w-56",
		select:
			"kt-cl-filter-control kt-cl-filter-select w-full pl-8 pr-3 py-1 text-body-md appearance-none cursor-pointer h-7",
		scroll: "table-container overflow-x-auto w-full",
		table: "w-full min-w-[800px] text-left border-collapse",
		theadTr: "bg-surface-bright border-b border-outline-variant",
		th: "px-3 py-1.5 font-label-md text-label-md text-on-surface-variant",
		tbody: "divide-y divide-outline-variant/50",
		tr: "hover:bg-surface-container-lowest transition-colors group",
		trAlt: "bg-surface-bright/50 hover:bg-surface-container-lowest transition-colors group",
		tdText: "px-3 py-1.5 font-body-md text-body-md text-on-surface-variant",
		tdStrong: "px-3 py-1.5 pl-4 font-body-md text-body-md text-on-surface font-medium",
		tdNumber: "px-3 py-1.5 font-label-md text-body-md text-on-surface text-right font-medium",
		tdStatus: "px-3 py-1.5 text-center",
		tdAction: "px-3 py-1.5 pr-4 text-right",
		rowAction:
			"text-secondary hover:text-on-secondary-container p-0.5 rounded hover:bg-surface-container-low transition-colors",
		footer: "p-2 border-t border-outline-variant flex justify-between items-center bg-surface-bright/50 rounded-b-lg",
		footerText: "font-body-sm text-body-sm text-on-surface-variant ml-2",
		footerPager: "flex gap-1 mr-2",
	};

	// ---- Status chips (code.html 482-549) -------------------------------
	var CHIP_BASE = "inline-flex items-center px-1.5 py-0.5 rounded-sm";
	var CHIP_TYPO = "font-label-sm text-label-sm";
	var CHIP_DOT = "w-1.5 h-1.5 rounded-full";
	var CHIP = {
		approved: { chip: "bg-primary-fixed/20 text-on-primary-fixed-variant", dot: "bg-primary", label: "Approved" },
		review: {
			chip: "bg-secondary-fixed/30 text-on-secondary-fixed-variant",
			dot: "bg-secondary",
			label: "Under Review",
		},
		draft: {
			chip: "bg-surface-container-high text-on-surface-variant",
			dotChip: "border border-outline-variant",
			dot: "bg-outline",
			label: "Draft",
		},
		rejected: { chip: "bg-error-container/30 text-on-error-container", dot: "bg-error", label: "Rejected" },
	};

	// ---- UI-00 queue chrome (C1-M1 code-ready-to-configure.html) ---------
	var QUEUE = {
		/* C1-M1 mock: fixed 4-column KPI row (responsive handled in layout CSS). */
		summaryGrid: "grid grid-cols-4 gap-4 mb-8",
		summaryCard:
			"bg-surface-container-lowest border border-outline-variant p-4 flex items-center gap-4 relative overflow-hidden",
		summaryAccent: "absolute left-0 top-0 bottom-0 w-1",
		summaryIconWrap: "w-10 h-10 rounded bg-surface-container-high flex items-center justify-center shrink-0",
		summaryLabel: "text-label-md text-on-surface-variant uppercase tracking-tighter",
		summaryValue: "text-headline-lg font-bold text-primary",
		/* A2 Publications bento: label top, large value + watermark icon */
		summaryCardBento:
			"kt-cl-queue-summary-card--bento bg-surface-container-lowest border border-outline-variant border-l-8 p-6 flex flex-col justify-between",
		summaryLabelBento:
			"text-xs font-bold text-on-surface-variant uppercase tracking-wider",
		summaryBentoRow: "flex items-end justify-between mt-4 gap-2",
		summaryValueBento: "text-4xl font-bold text-primary-container leading-none",
		summaryWatermarkIcon: "kt-cl-queue-summary-watermark text-4xl",
		canvas:
			"bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm overflow-hidden flex flex-col",
		tabBar:
			"flex items-center px-6 border-b border-outline-variant bg-surface-container-low/30 overflow-x-auto no-scrollbar",
		tabActive:
			"px-4 py-4 text-label-md font-bold text-primary border-b-2 border-primary whitespace-nowrap",
		tabIdle:
			"px-4 py-4 text-label-md font-medium text-on-surface-variant hover:text-primary transition-colors whitespace-nowrap",
		/* C1-M1 filter strip: search flex-grows into leftover space + | + compact filters. */
		filterBar:
			"kt-cl-filter-bar p-4 border-b border-outline-variant bg-surface-container-low/10",
		filterLabel: "block text-[10px] font-label-md text-on-surface-variant mb-1 uppercase",
		filterInput: "kt-cl-filter-control kt-cl-filter-input",
		filterSelect: "kt-cl-filter-control kt-cl-filter-select",
		tableScroll: "overflow-x-auto overflow-y-auto max-h-[500px]",
		table: "w-full text-left border-collapse min-w-[1000px]",
		theadTr: "bg-surface-container-low border-b border-outline-variant sticky top-0 z-10",
		th: "px-4 py-3 text-label-md text-on-surface-variant uppercase font-bold tracking-wider",
		tbody: "divide-y divide-outline-variant/30",
		tr: "hover:bg-surface-bright transition-colors group",
		tdRef: "px-4 py-2 font-label-md text-primary font-bold",
		tdTitle: "px-4 py-2 text-body-md font-medium text-on-surface",
		tdText: "px-4 py-2 text-body-sm",
		tdMuted: "px-4 py-2 text-label-sm text-on-surface-variant",
		tdAction: "px-4 py-2",
		rowBtn: "h-7 px-3 bg-primary text-on-primary rounded text-label-sm hover:opacity-90 whitespace-nowrap",
		footer:
			"p-4 bg-surface-bright border-t border-outline-variant flex justify-between items-center gap-3",
		footerText: "text-label-sm text-on-surface-variant font-medium",
		footerRight: "kt-cl-table-footer-right flex items-center gap-3",
		pageSizeWrap: "kt-cl-page-size flex items-center gap-2",
		pageSizeLabel: "text-label-sm text-on-surface-variant font-medium whitespace-nowrap",
		pageSizeSelect: "kt-cl-filter-control kt-cl-filter-select kt-cl-page-size-select",
		pager: "flex gap-2",
		pagerBtn:
			"w-8 h-8 flex items-center justify-center rounded border border-outline-variant bg-surface-container-lowest text-on-surface-variant hover:bg-surface-container-high transition-colors text-label-sm",
		pagerBtnActive: "w-8 h-8 flex items-center justify-center rounded bg-primary text-on-primary text-label-sm font-bold",
		modalOverlay:
			"fixed inset-0 z-[100] flex items-center justify-center p-4 kt-cl-modal-overlay",
		modalRoot:
			"bg-surface-container-lowest w-full max-w-2xl rounded shadow-xl border border-outline-variant flex flex-col max-h-[90vh]",
		modalHeader: "p-6 border-b border-outline-variant bg-surface-container-low",
		modalBody: "p-6 overflow-y-auto space-y-8",
		modalFooter:
			"p-6 border-t border-outline-variant flex justify-between items-center bg-surface-container-low",
	};

	/* UI-01 / wizard chrome — C1-M3 code.html (context strip shared across CFG pages). */
	var CONFIG_HOME = {
		contextStrip:
			"kt-cl-config-context-strip bg-surface-container-lowest rounded-lg border border-outline-variant p-4 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 mb-8 gap-0",
		contextCell: "kt-cl-config-context-cell border-r border-outline-variant/30 px-4 last:border-0",
		contextLabel:
			"text-label-sm text-on-surface-variant mb-1 uppercase tracking-wider",
		contextValue: "text-body-sm font-bold text-primary",
		contextValueError: "text-body-sm font-bold text-error",
		contextStatusRow: "flex items-center gap-1.5",
		contextStatusDot: "kt-cl-config-status-dot w-2 h-2 rounded-full bg-amber-500 shrink-0",
		layoutGrid: "grid grid-cols-12 gap-6",
		mainCol: "col-span-12 lg:col-span-9 space-y-6",
		sideCol: "col-span-12 lg:col-span-3 space-y-6",
		nextAction:
			"kt-cl-ui01-next-action bg-primary-container text-white rounded-xl p-6 shadow-md relative overflow-hidden flex flex-row flex-nowrap items-center justify-between gap-6",
		nextActionBtn:
			"kt-cl-ui01-next-btn relative z-10 px-8 py-3 bg-white text-primary-container font-bold rounded-lg hover:bg-primary-fixed transition-colors flex-shrink-0 whitespace-nowrap",
		stepsSectionTitle: "text-headline-md font-bold text-primary mb-4",
		stepsGrid: "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4",
		stepCard:
			"kt-cl-ui01-step-card bento-card bg-surface-container-lowest border border-outline-variant p-5 rounded-xl flex flex-col h-full",
		stepCardAttention:
			"kt-cl-ui01-step-card bento-card bg-surface-container-lowest border-2 border-error p-5 rounded-xl flex flex-col h-full shadow-sm",
		stepCardUnavailable:
			"kt-cl-ui01-step-card bento-card bg-surface-container-low border border-outline-variant border-dashed p-5 rounded-xl flex flex-col h-full opacity-70",
		handoffRoot:
			"kt-cl-ui01-handoff bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden shadow-sm",
		handoffHeader:
			"bg-surface-container-low px-5 py-3 border-b border-outline-variant flex items-center justify-between",
		handoffItem:
			"p-3 hover:bg-surface-bright rounded-lg transition-colors border-b border-outline-variant/30 last:border-0",
		drawerOverlay:
			"fixed inset-0 z-[100] flex justify-end kt-cl-modal-overlay",
		drawerPanel:
			"kt-cl-ui01-drawer bg-surface-container-lowest w-full max-w-md h-full shadow-xl border-l border-outline-variant flex flex-col",
	};

	kentender_core.cl_code_spec = {
		SIDENAV_ROOT: SIDENAV_ROOT,
		NAV_LINK_ACTIVE: NAV_LINK_ACTIVE,
		NAV_LINK: NAV_LINK,
		NAV_PARENT: NAV_PARENT,
		NAV_CHILDREN_LIST: NAV_CHILDREN_LIST,
		NAV_CHILD: NAV_CHILD,
		NAV_CHILD_ACTIVE: NAV_CHILD_ACTIVE,
		NAV_FOOTER_LINK: NAV_FOOTER_LINK,
		TOOLBAR_ROOT: TOOLBAR_ROOT,
		BREADCRUMB_TOOLBAR: BREADCRUMB_TOOLBAR,
		BREADCRUMB_ROOT: BREADCRUMB_ROOT,
		PAGE_TITLE: PAGE_TITLE,
		BTN_OUTLINE: BTN_OUTLINE,
		BTN_PRIMARY: BTN_PRIMARY,
		BENTO_GRID: BENTO_GRID,
		METRICS_WRAP: METRICS_WRAP,
		KPI_VALUE: KPI_VALUE,
		KPI_VALUE_ROW: KPI_VALUE_ROW,
		KPI: KPI,
		CALENDAR: CALENDAR,
		TABLE: TABLE,
		CHIP_BASE: CHIP_BASE,
		CHIP_TYPO: CHIP_TYPO,
		CHIP_DOT: CHIP_DOT,
		CHIP: CHIP,
		QUEUE: QUEUE,
		CONFIG_HOME: CONFIG_HOME,
		CODE_HTML_PATH: "docs/std-prod-impl/IT-STD-Wizard-v3/B-Components/code.html",
	};
})();
