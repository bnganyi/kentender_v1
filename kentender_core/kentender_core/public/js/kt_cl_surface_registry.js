// Civic Ledger surface registry — maps Desk route slugs to chrome metadata.
// Seeded from A2_IT_Tender_Wizard_Complete_Screen_Registry_v3.md.
// Only UI-00 has a live page script in Step 2; remaining entries are chrome stubs.
frappe.provide("kentender_core.cl_surface_registry");

(function () {
	"use strict";

	var SIDEBAR_KEY = "procurement";

	function crumb(label, route) {
		var item = { label: label };
		if (route) item.route = route;
		return item;
	}

	/** Shared crumb targets for Tender Management Civic Ledger surfaces. */
	function crumbDashboard() {
		/* Planned Home → capability overview (feature via route_options / query). */
		return crumb(__("Home"), ["coming-soon"]);
	}
	function crumbTenderManagement() {
		return crumb(__("Tender Management"), ["tender-management-v2"]);
	}
	function crumbTenderConfigurations() {
		return crumb(__("Tender Configurations"), ["it-tender-configuration-dashboard"]);
	}
	function crumbConfigurationHome() {
		return crumb(__("Tender Configuration Home"), ["it-tender-configuration-overview"]);
	}
	/** UI-01 itself: leaf is current (bold, not a link). */
	function trailUi01Home() {
		return [
			crumbDashboard(),
			crumbTenderConfigurations(),
			crumb(__("Tender Configuration Home")),
		];
	}

	/**
	 * Standard chrome for a registered surface (C1-M1).
	 * Toolbar: context trail (ancestors; last crumb bold). No search.
	 * Page header: leaf H1 + subtitle + actions only (no duplicate crumbs).
	 */
	function chrome(pageTitle, subtitle, toolbarTrail, actions) {
		return {
			toolbar: {
				breadcrumbs: toolbarTrail || [],
				showSearch: false,
				showUserMeta: true,
			},
			pageHeader: {
				title: pageTitle,
				subtitle: subtitle || "",
				hideBreadcrumbs: true,
				actions: actions || [],
			},
		};
	}

	var createAction = {
		label: __("Create Tender Configuration"),
		icon: "add_circle",
		variant: "primary",
		key: "create",
		testid: "kt-cl-action-create-tender-config",
	};

	var trailTm = [crumbDashboard(), crumbTenderManagement()];
	var trailConfigs = [crumbDashboard(), crumbTenderConfigurations()];
	var trailConfigHome = [
		crumbDashboard(),
		crumbTenderConfigurations(),
		crumbConfigurationHome(),
	];
	/** CFG-01 leaf: Home is a link; Tender Profile is current. */
	function trailCfg01Profile() {
		return [
			crumbDashboard(),
			crumbTenderConfigurations(),
			crumbConfigurationHome(),
			crumb(__("Tender Profile")),
		];
	}
	/** CFG-02 leaf: Home is a link; Tender Data Sheet is current. */
	function trailCfg02Tds() {
		return [
			crumbDashboard(),
			crumbTenderConfigurations(),
			crumbConfigurationHome(),
			crumb(__("Tender Data Sheet")),
		];
	}
	/** CFG-03 leaf: Home is a link; IT Requirements is current. */
	function trailCfg03Requirements() {
		return [
			crumbDashboard(),
			crumbTenderConfigurations(),
			crumbConfigurationHome(),
			crumb(__("IT Requirements")),
		];
	}
	/** CFG-04 leaf: Home is a link; Implementation Schedule is current. */
	function trailCfg04ImplementationSchedule() {
		return [
			crumbDashboard(),
			crumbTenderConfigurations(),
			crumbConfigurationHome(),
			crumb(__("Implementation Schedule")),
		];
	}
	/** CFG-05 leaf: Home is a link; System Inventory is current. */
	function trailCfg05SystemInventory() {
		return [
			crumbDashboard(),
			crumbTenderConfigurations(),
			crumbConfigurationHome(),
			crumb(__("System Inventory & Bidder Background")),
		];
	}
	/** CFG-06 leaf: Home is a link; Price Schedule is current. */
	function trailCfg06PriceSchedule() {
		return [
			crumbDashboard(),
			crumbTenderConfigurations(),
			crumbConfigurationHome(),
			crumb(__("Price Schedule")),
		];
	}
	/** CFG-07 leaf: Home is a link; Evaluation Setup is current. */
	function trailCfg07EvaluationSetup() {
		return [
			crumbDashboard(),
			crumbTenderConfigurations(),
			crumbConfigurationHome(),
			crumb(__("Evaluation Setup")),
		];
	}
	/** CFG-08 leaf: Home is a link; Forms & Evidence is current. */
	function trailCfg08FormsEvidence() {
		return [
			crumbDashboard(),
			crumbTenderConfigurations(),
			crumbConfigurationHome(),
			crumb(__("Forms & Evidence")),
		];
	}
	/** CFG-09 leaf: Home is a link; Contract Values is current. */
	function trailCfg09ContractValues() {
		return [
			crumbDashboard(),
			crumbTenderConfigurations(),
			crumbConfigurationHome(),
			crumb(__("Contract Values")),
		];
	}
	/** WF-01 leaf: Readiness Check & Report. */
	function trailWf01Readiness() {
		return [
			crumbDashboard(),
			crumbTenderConfigurations(),
			crumbConfigurationHome(),
			crumb(__("Readiness Check & Report")),
		];
	}
	/** WF-02 leaf: Review & Approval. */
	function trailWf02Review() {
		return [
			crumbDashboard(),
			crumbTenderConfigurations(),
			crumbConfigurationHome(),
			crumb(__("Review & Approval")),
		];
	}
	/** WF-03 leaf: Tender Document Preview (includes publication handoff). */
	function trailWf03Preview() {
		return [
			crumbDashboard(),
			crumbTenderConfigurations(),
			crumbConfigurationHome(),
			crumb(__("Tender Document Preview")),
		];
	}
	/** PUB-A1 leaf: Electronic Tender Package Review. */
	function trailPubA1PackageReview() {
		return [
			crumbDashboard(),
			crumbTenderConfigurations(),
			crumbConfigurationHome(),
			crumb(__("Electronic Tender Package Review")),
		];
	}
	/** PUB-A2 leaf: Tenders (publications) queue. */
	function trailPubA2Publications() {
		return [crumbDashboard(), crumbTenderManagement(), crumb(__("Tenders"))];
	}
	/** PUB-A3 leaf: Publication Setup. */
	function trailPubA3Setup() {
		return [
			crumbDashboard(),
			crumbTenderManagement(),
			crumb(__("Tenders"), ["publications"]),
			crumb(__("Publication Setup")),
		];
	}
	/** BW-A1 leaf: Published Tender Overview (bidder) — entered from public /tenders. */
	function trailBwA1Overview() {
		return [
			crumbDashboard(),
			crumb(__("Available Tenders")),
			crumb(__("Published Tender Overview")),
		];
	}

	function crumbStrategyAlignment() {
		return crumb(__("Strategy Alignment"), ["strategy-alignment"]);
	}
	function trailStrategy() {
		return [crumbDashboard(), crumbStrategyAlignment()];
	}
	function trailStrategyPlan(leafLabel) {
		return [crumbDashboard(), crumbStrategyAlignment(), crumb(leafLabel)];
	}

	/**
	 * A2 screen IDs → routePrefixes use existing Desk page names where present.
	 * UI-M01 is a modal (no Desk route); kept for registry completeness with empty prefixes.
	 */
	var surfaces = {
		"STR-UI-01": {
			id: "STR-UI-01",
			label: "Strategy Portfolio",
			routePrefixes: ["strategy-alignment"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Strategy Alignment"),
				__(
					"Govern strategic outcomes, public-value commitments and performance targets used across procurement."
				),
				trailStrategy(),
				[]
			),
		},
		"STR-UI-02": {
			id: "STR-UI-02",
			label: "Plan Overview",
			routePrefixes: ["strategy-plan-overview"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(__("Plan Overview"), "", trailStrategyPlan(__("Plan Overview")), []),
		},
		"STR-UI-03": {
			id: "STR-UI-03",
			label: "Plan Structure",
			routePrefixes: ["strategy-plan-structure"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(__("Plan Structure"), "", trailStrategyPlan(__("Plan Structure")), []),
		},
		"STR-UI-05": {
			id: "STR-UI-05",
			label: "Public Value Objective Catalogue",
			routePrefixes: ["strategy-pvo-catalogue"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Public Value Objective Catalogue"),
				"",
				trailStrategyPlan(__("Public Value Objectives")),
				[]
			),
		},
		"STR-UI-06": {
			id: "STR-UI-06",
			label: "Public Value Objective Editor",
			routePrefixes: ["strategy-pvo-editor"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Public Value Objective"),
				"",
				trailStrategyPlan(__("Public Value Objective")),
				[]
			),
		},
		"STR-UI-07": {
			id: "STR-UI-07",
			label: "Plan Value Commitments",
			routePrefixes: ["strategy-plan-value-commitments"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Value Commitments"),
				"",
				trailStrategyPlan(__("Value Commitments")),
				[]
			),
		},
		"STR-UI-08": {
			id: "STR-UI-08",
			label: "Measurement Register",
			routePrefixes: ["strategy-plan-measurements"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(__("Measurements"), "", trailStrategyPlan(__("Measurements")), []),
		},
		"STR-UI-09": {
			id: "STR-UI-09",
			label: "Submit Measurement",
			routePrefixes: ["strategy-measurement-submit"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Submit Measurement"),
				"",
				trailStrategyPlan(__("Submit Measurement")),
				[]
			),
		},
		"STR-UI-10": {
			id: "STR-UI-10",
			label: "Verify Measurement",
			routePrefixes: ["strategy-measurement-verify"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Verify Measurement"),
				"",
				trailStrategyPlan(__("Verify Measurement")),
				[]
			),
		},
		"STR-UI-11": {
			id: "STR-UI-11",
			label: "Corrective Actions",
			routePrefixes: ["strategy-corrective-actions"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Corrective Actions"),
				"",
				trailStrategyPlan(__("Corrective Actions")),
				[]
			),
		},
		"STR-UI-12": {
			id: "STR-UI-12",
			label: "Downstream Usage",
			routePrefixes: ["strategy-plan-downstream-usage"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Downstream Usage"),
				"",
				trailStrategyPlan(__("Downstream Usage")),
				[]
			),
		},
		"STR-UI-13": {
			id: "STR-UI-13",
			label: "Readiness and Review",
			routePrefixes: ["strategy-plan-review"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(__("Review"), "", trailStrategyPlan(__("Review")), []),
		},
		"STR-UI-14": {
			id: "STR-UI-14",
			label: "Audit History",
			routePrefixes: ["strategy-plan-audit"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(__("Audit"), "", trailStrategyPlan(__("Audit")), []),
		},
		"UI-00": {
			id: "UI-00",
			label: "Tender Configurations Dashboard",
			routePrefixes: ["it-tender-configuration-dashboard"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Tender Configurations"),
				__(
					"Create configurations from approved procurement packages and manage configurations already in progress."
				),
				trailTm,
				[createAction]
			),
		},
		"UI-M01": {
			id: "UI-M01",
			label: "Create IT Tender Configuration",
			routePrefixes: [],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Create Tender Configuration"),
				__("Select an approved procurement package to start configuration."),
				trailConfigs,
				[]
			),
		},
		"UI-01": {
			id: "UI-01",
			label: "Tender Configuration Home",
			routePrefixes: ["it-tender-configuration-overview"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Tender Configuration Home"),
				__(
					"Complete the required configuration steps before review, preview, and publication handoff."
				),
				trailUi01Home(),
				[]
			),
		},
		"CFG-01": {
			id: "CFG-01",
			label: "Tender Profile",
			routePrefixes: ["it-tender-configuration-tender-profile"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Tender Profile"),
				__(
					"Confirm the tender identity, procurement context, lot structure, and applicable standard tender document."
				),
				trailCfg01Profile(),
				[]
			),
		},
		"CFG-02": {
			id: "CFG-02",
			label: "Tender Data Sheet",
			routePrefixes: ["it-tender-configuration-tds"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Tender Data Sheet"),
				__(
					"Set the tender-specific instructions, dates, submission rules, and allowed options for this IT tender."
				),
				trailCfg02Tds(),
				[]
			),
		},
		"CFG-03": {
			id: "CFG-03",
			label: "IT Requirements",
			routePrefixes: ["it-tender-configuration-it-requirements"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("IT Requirements"),
				__("Define what bidders must supply, deliver, integrate, support, or prove."),
				trailCfg03Requirements(),
				[]
			),
		},
		"CFG-04": {
			id: "CFG-04",
			label: "Implementation Schedule",
			routePrefixes: ["it-tender-configuration-implementation-schedule"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Implementation Schedule"),
				__(
					"Define the delivery approach, milestones, deliverables, timing, and acceptance checkpoints for this IT tender."
				),
				trailCfg04ImplementationSchedule(),
				[]
			),
		},
		"CFG-05": {
			id: "CFG-05",
			label: "System Inventory & Bidder Background",
			routePrefixes: ["it-tender-configuration-system-inventory"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("System Inventory & Bidder Background"),
				__("Disclose bidder-relevant inventory, site, system, and background context."),
				trailCfg05SystemInventory(),
				[]
			),
		},
		"CFG-06": {
			id: "CFG-06",
			label: "Price Schedule",
			routePrefixes: ["it-tender-configuration-price-schedule"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Price Schedule"),
				__("Define how bidders should price the tender."),
				trailCfg06PriceSchedule(),
				[]
			),
		},
		"CFG-07": {
			id: "CFG-07",
			label: "Evaluation Setup",
			routePrefixes: ["it-tender-configuration-evaluation-setup"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Evaluation Setup"),
				__("Configure criteria and scoring for bid evaluation."),
				trailCfg07EvaluationSetup(),
				[]
			),
		},
		"CFG-08": {
			id: "CFG-08",
			label: "Forms & Evidence",
			routePrefixes: ["it-tender-configuration-forms-and-evidence"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Forms & Evidence"),
				__("Select non-price forms, declarations, and evidence requirements."),
				trailCfg08FormsEvidence(),
				[]
			),
		},
		"CFG-09": {
			id: "CFG-09",
			label: "Contract Values",
			routePrefixes: ["it-tender-configuration-scc"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Contract Values"),
				__("Set tender-specific contract values and obligations (SCC)."),
				trailCfg09ContractValues(),
				[]
			),
		},
		"WF-01": {
			id: "WF-01",
			label: "Readiness Check & Report",
			routePrefixes: ["it-tender-configuration-validation-report"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Readiness Check & Report"),
				__("Check whether this tender configuration is complete enough for review."),
				trailWf01Readiness(),
				[]
			),
		},
		"WF-02": {
			id: "WF-02",
			label: "Review & Approval",
			routePrefixes: ["it-tender-configuration-review-and-approval"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Review & Approval"),
				__(
					"Review the completed tender configuration and decide whether it can proceed to document preview."
				),
				trailWf02Review(),
				[]
			),
		},
		"WF-03": {
			id: "WF-03",
			label: "Tender Document Preview",
			routePrefixes: [
				"it-tender-configuration-render-preview",
				"it-tender-configuration-publication-readiness",
			],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Tender Document Preview"),
				__(
					"Review the generated tender document artifact, then confirm the package and continue to Publication Setup."
				),
				trailWf03Preview(),
				[]
			),
		},
		"WF-04": {
			id: "WF-04",
			label: "Publication Handoff (retired)",
			routePrefixes: [],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Tender Document Preview"),
				__(
					"Publication Handoff is merged into Tender Document Preview / Package Review. Confirm the package, then continue to Publication Setup."
				),
				trailWf03Preview(),
				[]
			),
		},
		"PUB-A1": {
			id: "PUB-A1",
			label: "Electronic Tender Package Review",
			routePrefixes: ["it-tender-package-review"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Electronic Tender Package Review"),
				__(
					"Confirm that the approved configuration has been converted into a complete electronic tender package."
				),
				trailPubA1PackageReview(),
				[]
			),
		},
		"PUB-A2": {
			id: "PUB-A2",
			label: "Tenders",
			routePrefixes: ["publications"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Tenders"),
				__(
					"Set publication details, publish confirmed electronic tender packages, and monitor published tenders."
				),
				trailPubA2Publications(),
				[]
			),
		},
		"PUB-A3": {
			id: "PUB-A3",
			label: "Publication Setup",
			routePrefixes: ["publication-setup"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Publication Setup"),
				__(
					"Set publication details and publish the confirmed electronic tender package."
				),
				trailPubA3Setup(),
				[]
			),
		},
		"BW-A1": {
			id: "BW-A1",
			label: "Published Tender Overview",
			routePrefixes: ["published-tender-overview"],
			sidebarWorkspaceKey: SIDEBAR_KEY,
			chrome: chrome(
				__("Published Tender Overview"),
				__(
					"Review the published tender, documents, and deadlines before starting or continuing a bid."
				),
				trailBwA1Overview(),
				[]
			),
		},
	};

	function routeKey(route) {
		var r = route || (typeof frappe !== "undefined" && frappe.get_route ? frappe.get_route() : []) || [];
		if (!r.length) return "";
		if (r[0] === "Form" && r.length >= 2) {
			return ("Form/" + r[1]).toLowerCase();
		}
		return String(r[0] || "").toLowerCase();
	}

	kentender_core.cl_surface_registry = {
		surfaces: surfaces,

		/** Ordered A2 screen IDs for contract tests. */
		allIds: function () {
			return [
				"UI-00",
				"UI-M01",
				"UI-01",
				"CFG-01",
				"CFG-02",
				"CFG-03",
				"CFG-04",
				"CFG-05",
				"CFG-06",
				"CFG-07",
				"CFG-08",
				"CFG-09",
				"WF-01",
				"WF-02",
				"WF-03",
				"WF-04",
				"PUB-A1",
				"PUB-A2",
				"PUB-A3",
				"BW-A1",
			];
		},

		get: function (id) {
			return surfaces[id] || null;
		},

		resolveFromRoute: function (route) {
			var key = routeKey(route);
			if (!key) return null;
			var ids = Object.keys(surfaces);
			for (var i = 0; i < ids.length; i++) {
				var surface = surfaces[ids[i]];
				var prefixes = (surface.routePrefixes || []).map(function (p) {
					return String(p).toLowerCase();
				});
				if (prefixes.indexOf(key) >= 0) {
					return surface;
				}
				/* Also match path prefixes like procurement-planning/plans */
				for (var j = 0; j < prefixes.length; j++) {
					if (key === prefixes[j] || key.indexOf(prefixes[j] + "/") === 0) {
						return surface;
					}
				}
			}
			return null;
		},
	};

	frappe.provide("kentender_core.cl");
	kentender_core.cl.surface_registry = kentender_core.cl_surface_registry;
})();
