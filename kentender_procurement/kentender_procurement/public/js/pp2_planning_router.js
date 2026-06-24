/** PP2 P5-001 — Procurement Planning nested surfaces inside main Procurement shell. */
(function () {
	const WORKSPACE_NAME = "Procurement Planning";
	const ROOT_PATH = "/desk/procurement-planning";
	const RIGHT_PANEL_STATE_KEY = "kt-pp2-right-panel-collapsed";
	let sidebarObserver = null;
	let sidebarRefreshQueued = false;
	let bootRetryTimer = null;
	let bootRunToken = 0;
	let sidebarFastpathPatched = false;
	let sidebarLookupPatched = false;
	let sidebarSetupListenerBound = false;

	const SURFACE_LABELS = {
		"": __("Workbench"),
		plans: __("Procurement Plans"),
		releases: __("Released to Tender"),
	};

	const SURFACES = {
		"": {
			testId: "pp3-planning-workbench",
			title: __("Procurement Planning"),
			subtitle: __("Workbench"),
		},
		plans: {
			testId: "pp3-procurement-plans-page",
			title: __("Procurement Planning"),
			subtitle: __("Procurement Plans"),
		},
		releases: {
			testId: "pp2-released-to-tender-page",
			title: __("Procurement Planning"),
			subtitle: __("Released to Tender"),
		},
		"package-detail": {
			testId: "pp3-package-detail-surface",
			title: __("Procurement Planning"),
			subtitle: __("Package Detail"),
		},
	};
	const APPROVED_DEMANDS_QUEUE_API =
		"kentender_procurement.procurement_planning.api.approved_demands.get_pp_approved_demands_awaiting_planning";
	const APPROVED_DEMANDS_DRAWER_API =
		"kentender_procurement.procurement_planning.api.approved_demands.get_pp_approved_demand_planning_drawer";
	const ACTIVE_PLAN_API =
		"kentender_procurement.procurement_planning.api.active_plan.get_pp_active_plan_view_model";
	const CREATE_PACKAGE_DRAWER_API =
		"kentender_procurement.procurement_planning.api.planning_inclusion.get_pp_create_package_modal_drawer";
	const WORKBENCH_QUEUE_BY_UI_QUEUE = {
		needs_planning: true,
		draft_packages: true,
		needs_review: true,
		ready_to_release: true,
		blocked: true,
		recently_released: true,
	};
	const approvedDemandFetchTokens = new WeakMap();
	const approvedDemandSummaryTokens = new WeakMap();

	function esc(s) {
		return frappe.utils.escape_html(String(s == null ? "" : s));
	}

	function workspaceNameMatches(name) {
		if (!name) return false;
		if (name === WORKSPACE_NAME) return true;
		try {
			if (frappe.router && typeof frappe.router.slug === "function") {
				return frappe.router.slug(String(name)) === frappe.router.slug(WORKSPACE_NAME);
			}
		} catch (e) {
			/* ignore */
		}
		return String(name).toLowerCase().replace(/\s+/g, "-") === "procurement-planning";
	}

	function isPlanningWorkspaceRoute() {
		try {
			const route = frappe.get_route() || [];
			if (route[0] === "Workspaces" && route.length >= 2) {
				const workspaceName = route[1] === "private" && route.length >= 3 ? route[2] : route[1];
				if (workspaceName) {
					return workspaceNameMatches(workspaceName);
				}
			}
		} catch (e) {
			/* ignore */
		}
		const path = String(window.location.pathname || "").toLowerCase();
		return path.includes("/procurement-planning");
	}

	function readSurfaceSlug() {
		const path = String(window.location.pathname || "").toLowerCase();
		if (path.endsWith("/plans")) return "plans";
		if (path.endsWith("/releases")) return "releases";
		return "";
	}

	const CANONICAL_PLANNING_SLUGS = {
		plans: true,
		releases: true,
	};

	const INTERNAL_PLANNING_LEGACY_SLUGS = {
		"approved-demands": true,
		packages: true,
		home: true,
		evidence: true,
		inclusions: true,
		readiness: true,
		review: true,
		lines: true,
		technical: true,
		"release-package": true,
		"technical-details": true,
		audit: true,
	};

	const INTERNAL_PLANNING_ACCESS_ROLES = [
		"Procurement Planner",
		"Planning Reviewer",
		"Planning Authority",
		"Auditor",
		"Administrator",
		"System Manager",
		"Procurement Officer",
		"Tender Manager",
		"Budget Officer",
	];

	const INTERNAL_PLANNING_DENIED_ROLES = ["Supplier"];

	function readUserRoles() {
		try {
			const testRoles = window.__kt_pp2_test_roles;
			if (Array.isArray(testRoles)) {
				return testRoles.slice();
			}
		} catch (e) {
			/* ignore */
		}
		try {
			if (frappe.boot && frappe.boot.user && frappe.boot.user.roles) {
				return frappe.boot.user.roles.slice();
			}
			if (frappe.user_roles) {
				return frappe.user_roles.slice();
			}
		} catch (e) {
			/* ignore */
		}
		return [];
	}

	function mayAccessInternalPlanningLegacyRoute() {
		const roles = readUserRoles();
		for (let i = 0; i < INTERNAL_PLANNING_DENIED_ROLES.length; i += 1) {
			if (roles.indexOf(INTERNAL_PLANNING_DENIED_ROLES[i]) === -1) continue;
			for (let j = 0; j < INTERNAL_PLANNING_ACCESS_ROLES.length; j += 1) {
				if (roles.indexOf(INTERNAL_PLANNING_ACCESS_ROLES[j]) !== -1) {
					return true;
				}
			}
			return false;
		}
		return true;
	}

	function parsePlanningPathname(pathname) {
		const path = String(pathname || "").toLowerCase();
		const prefix = ROOT_PATH.toLowerCase();
		if (!path.startsWith(prefix)) return [];
		const rest = path.slice(prefix.length).replace(/^\/+/, "");
		if (!rest) return [];
		return rest.split("/").filter(Boolean);
	}

	function readPlanningRawSegments(pathname) {
		const path = String(pathname || "");
		const prefix = ROOT_PATH.toLowerCase();
		if (!path.toLowerCase().startsWith(prefix)) return [];
		const rest = path.slice(ROOT_PATH.length).replace(/^\/+/, "");
		if (!rest) return [];
		return rest.split("/").filter(Boolean);
	}

	function buildWorkbenchRedirectUrl(query) {
		const url = new URL(window.location.origin + ROOT_PATH);
		const q = query || {};
		Object.keys(q).forEach(function (key) {
			const value = String(q[key] || "").trim();
			if (!value) return;
			url.searchParams.set(key, value);
		});
		return url.pathname + url.search;
	}

	function buildWorkbenchPackageRedirectUrl(packageCode) {
		const code = String(packageCode || "").trim();
		const queue = String(new URLSearchParams(window.location.search || "").get("queue") || "").trim();
		const item = String(new URLSearchParams(window.location.search || "").get("item") || "").trim();
		const params = {};
		if (code) {
			params.package_code = decodeURIComponent(code);
		}
		if (queue) {
			params.queue = queue;
		}
		if (item) {
			params.item = item;
		}
		return buildWorkbenchRedirectUrl(params);
	}

	function buildWorkbenchApprovedDemandsRedirectUrl() {
		const search = new URLSearchParams(window.location.search || "");
		const params = {};
		const queue = String(search.get("queue") || "").trim();
		const item = String(search.get("item") || "").trim();
		if (queue) {
			params.queue = queue;
		}
		if (item) {
			params.item = item;
		}
		return buildWorkbenchRedirectUrl(params);
	}

	function buildPackageDetailUrl(packageCode) {
		const code = String(packageCode || "").trim();
		if (!code) return ROOT_PATH;
		return `${ROOT_PATH}/packages/${encodeURIComponent(code)}`;
	}

	function buildPackagesRedirectUrl(packageCode) {
		return buildPackageDetailUrl(packageCode);
	}

	function resolvePlanningRoute(pathname) {
		const segments = parsePlanningPathname(pathname);
		const rawSegments = readPlanningRawSegments(pathname);
		if (!segments.length) {
			return { action: "canonical", slug: "" };
		}

		const head = segments[0];
		if (CANONICAL_PLANNING_SLUGS[head] && segments.length === 1) {
			return { action: "canonical", slug: head };
		}

		const requiresInternalAccess =
			INTERNAL_PLANNING_LEGACY_SLUGS[head] ||
			(head === "packages" && segments.length > 1) ||
			(head === "plans" && segments.length > 1) ||
			(head === "releases" && segments.length > 1);
		if (requiresInternalAccess && !mayAccessInternalPlanningLegacyRoute()) {
			return { action: "not_found", reason: "denied" };
		}

		if (head === "home" && segments.length === 1) {
			return {
				action: "redirect",
				slug: "",
				redirectUrl: buildWorkbenchRedirectUrl(),
			};
		}
		if (head === "approved-demands" && segments.length === 1) {
			return {
				action: "redirect",
				slug: "",
				redirectUrl: buildWorkbenchApprovedDemandsRedirectUrl(),
			};
		}
		if (head === "packages" && segments.length === 1) {
			return {
				action: "redirect",
				slug: "",
				redirectUrl: buildWorkbenchPackageRedirectUrl(),
			};
		}

		if (head === "evidence") {
			return {
				action: "redirect",
				slug: "",
				redirectUrl: buildPackagesRedirectUrl(rawSegments[1] || ""),
			};
		}
		if (head === "inclusions") {
			return {
				action: "redirect",
				slug: "",
				redirectUrl: buildWorkbenchApprovedDemandsRedirectUrl(),
			};
		}
		if (
			head === "readiness" ||
			head === "review" ||
			head === "lines" ||
			head === "technical" ||
			head === "technical-details" ||
			head === "audit" ||
			head === "release-package"
		) {
			return {
				action: "redirect",
				slug: "",
				redirectUrl: buildWorkbenchRedirectUrl(),
			};
		}
		if (head === "releases" && segments.length > 1) {
			return {
				action: "redirect",
				slug: "releases",
				redirectUrl: `${ROOT_PATH}/releases`,
			};
		}
		if (head === "plans" && segments.length > 1) {
			return {
				action: "redirect",
				slug: "plans",
				redirectUrl: `${ROOT_PATH}/plans`,
			};
		}
		if (head === "packages" && segments.length > 1) {
			return {
				action: "package_detail",
				packageCode: decodeURIComponent(rawSegments[1] || ""),
			};
		}

		if (!CANONICAL_PLANNING_SLUGS[head]) {
			return { action: "not_found", reason: "unknown" };
		}

		return { action: "canonical", slug: head };
	}

	function applyPlanningRouteRedirect(redirectUrl) {
		const target = String(redirectUrl || "").trim();
		if (!target) return false;
		const url = new URL(target, window.location.origin);
		const next = url.pathname + url.search + url.hash;
		const curr = window.location.pathname + window.location.search + window.location.hash;
		if (next === curr) return false;
		window.history.replaceState({}, "", next);
		return true;
	}

	function renderRouteNotFound(root) {
		if (!root) return;
		root.innerHTML =
			'<section class="pp2-route-not-found" data-testid="pp2-route-not-found">' +
			'<h3 class="h6 mb-1">' +
			esc(__("Planning page unavailable")) +
			"</h3>" +
			'<p class="text-muted small mb-0">' +
			esc(__("You do not have access to this planning information.")) +
			"</p>" +
			"</section>";
	}

	function surfaceForSlug(slug) {
		return SURFACES[slug] || SURFACES[""];
	}

	function isPlanningHomeSlug(slug) {
		return String(slug == null ? "" : slug) === "";
	}

	function isProcurementPlansSlug(slug) {
		return String(slug || "").trim() === "plans";
	}

	function isPackageDetailSlug(slug) {
		return String(slug || "").trim() === "package-detail";
	}

	function clearWorkbenchHosts(mainHost) {
		if (!mainHost) return;
		const testIds = [
			"pp2-primary-queue-host",
			"pp2-primary-filters-host",
			"pp2-primary-work-list-host",
		];
		for (let i = 0; i < testIds.length; i += 1) {
			const el = mainHost.querySelector('[data-testid="' + testIds[i] + '"]');
			if (el && el.parentNode) {
				el.parentNode.removeChild(el);
			}
		}
	}

	function formatMoneyValue(value, currency) {
		const amount = Number(value || 0);
		const curr = String(currency || "KES").trim() || "KES";
		const safeAmount = Number.isFinite(amount) ? amount : 0;
		return safeAmount.toLocaleString() + " " + curr;
	}

	function approvedDemandEmptyMessage(queueId) {
		const key = String(queueId || "").trim();
		if (key === "blocked") {
			return __("No blocked approved demands match this queue.");
		}
		if (key === "already-planned") {
			return __("No fully planned approved demands match this queue.");
		}
		return __("No approved demands match this queue.");
	}

	function mapApprovedDemandQueueRow(row, queueId) {
		const data = row || {};
		const demand = data.demand || {};
		const demandId = String(demand.id || "").trim();
		const title = String(demand.name || demand.code || demandId).trim();
		const category = String(data.category || "").trim();
		const valueLabel = formatMoneyValue(data.estimated_value, data.currency);
		const blockerLabel = String((data.blocker_summary && data.blocker_summary.label) || "").trim();
		const budgetLine = data.budget_line || {};
		const budgetLinked = String(budgetLine.id || budgetLine.code || "").trim().length > 0;
		const planningStatus = String(data.planning_status || "").trim() || (String(queueId || "").trim() === "already-planned" ? __("Fully Planned") : __("Ready for Planning"));
		return {
			id: demandId,
			title: title,
			subtitle: [category, valueLabel].filter(Boolean).join(" · "),
			category_value: [category, valueLabel].filter(Boolean).join(" · "),
			funding_status: budgetLinked ? __("Budget linked") : __("Budget not linked"),
			planning_status: planningStatus,
			status_label: planningStatus,
			blocker_label: blockerLabel,
			blocker_count: Number((data.blocker_summary && data.blocker_summary.count) || 0),
			raw: data,
		};
	}

	function approvedDemandSummaryFacts(item, drawerMessage) {
		const raw = (item && item.raw) || {};
		const drawer = drawerMessage || {};
		const demand = drawer.demand || {};
		const category = String(demand.category || raw.category || "").trim();
		const value = formatMoneyValue(
			demand.estimated_value != null ? demand.estimated_value : raw.estimated_value,
			demand.currency || raw.currency
		);
		return [category, value].filter(Boolean).join(" · ");
	}

	function approvedDemandSummaryFromDrawer(item, queueId, drawerMessage) {
		const raw = (item && item.raw) || {};
		const drawer = drawerMessage || {};
		const demand = drawer.demand || {};
		const demandTitle = String(demand.name || (item && item.title) || "").trim();
		const categoryLabel = String(demand.category || raw.category || "").trim();
		const valueLabel = formatMoneyValue(
			demand.estimated_value != null ? demand.estimated_value : raw.estimated_value,
			demand.currency || raw.currency
		);
		const budgetLine = (drawer.budget_context && drawer.budget_context.budget_line) || {};
		const budgetLinked = String(budgetLine.id || budgetLine.code || "").trim().length > 0;
		const eligibility = drawer.eligibility || {};
		const includeAllowed = eligibility.allowed !== false;
		const blockers = Array.isArray(eligibility.blockers)
			? eligibility.blockers
					.map(function (row) {
						return String((row && row.message) || "").trim();
					})
					.filter(Boolean)
			: [];
		const demandStatus = String(demand.planning_status || (item && item.planning_status) || "").trim();
		const fallbackNextAction = String(queueId || "").trim() === "blocked"
			? __("Resolve blockers before including in plan")
			: __("Include in plan");
		const evidenceRoute = String(
			(drawer.actions && drawer.actions.approval_certificate_route) ||
				(drawer.evidence && drawer.evidence.view_route) ||
				""
		).trim();
		const demandItems = Array.isArray(drawer.demand_items) ? drawer.demand_items : [];
		const demandItemCodes = demandItems
			.map(function (row) {
				if (!row || typeof row !== "object") return "";
				return String(row.code || row.demand_item_code || row.item_code || "").trim();
			})
			.filter(Boolean);
		const targetPlan = drawer.target_plan || {};
		return {
			context_slug: "approved-demands",
			demand_code: String(demand.code || (raw.demand && raw.demand.code) || "").trim(),
			title: demandTitle,
			status_label: demandStatus,
			key_facts: [categoryLabel, valueLabel].filter(Boolean).join(" · "),
			value_label: valueLabel,
			funding_label: budgetLinked ? __("Budget linked") : __("Budget not linked"),
			blockers: blockers,
			blocker_count: blockers.length,
			include_allowed: includeAllowed,
			include_blocker_message: blockers[0] || "",
			demand_item_codes: demandItemCodes,
			target_plan_code: String(targetPlan.code || targetPlan.id || targetPlan.name || "").trim(),
			target_plan_name: String(targetPlan.name || "").trim(),
			next_action_label: blockers.length ? __("Resolve blockers before including in plan") : fallbackNextAction,
			primary_action: {
				label: __("Include in Plan"),
				action: "include_in_plan",
				testid: "pp2-include-in-plan-button",
			},
			secondary_actions: [
				{
					label: __("View Demand"),
					action: "view_demand",
					route: evidenceRoute,
					testid: "pp2-view-demand-button",
				},
			],
			show_evidence_action: true,
			evidence_testid: "pp2-view-demand-evidence",
		};
	}

	function buildWorkbenchOpenPackageUrl(packageCode) {
		const code = String(packageCode || "").trim();
		const params = { queue: "draft-packages" };
		if (code) {
			params.package_code = decodeURIComponent(code);
		}
		return buildWorkbenchRedirectUrl(params);
	}

	function refreshWorkbenchWorkList(shell, slug, queueKey) {
		if (!shell || !isPlanningHomeSlug(slug)) return;
		const mainHost = shell.querySelector('[data-testid="pp2-primary-main-host"]');
		if (!mainHost) return;
		const normalizedQueue = String(queueKey || "").trim();
		if (normalizedQueue) {
			const queueTabsApi =
				kentender_procurement &&
				kentender_procurement.PlanningWorkbenchQueueTabs &&
				typeof kentender_procurement.PlanningWorkbenchQueueTabs.setQueueUrl === "function"
					? kentender_procurement.PlanningWorkbenchQueueTabs
					: null;
			if (queueTabsApi) {
				queueTabsApi.setQueueUrl(normalizedQueue);
				const queueHost = mainHost.querySelector('[data-testid="pp2-primary-queue-host"]');
				if (queueHost && typeof queueTabsApi.render === "function") {
					queueTabsApi.render(queueHost, { activeQueue: normalizedQueue });
				}
			}
		}
		mountPlanningWorkList(mainHost, slug, shell);
	}

	function createPackageSuccessSummary(payloadSummary, createResult, contextOpts) {
		const summaryData = payloadSummary || {};
		const result = createResult || {};
		const ctx = contextOpts || {};
		const workbench = ctx.workbench === true;
		const pkgRow = result.package && typeof result.package === "object" ? result.package : {};
		const packageCode = String(result.package_code || pkgRow.package_code || "").trim();
		const packageName = String(pkgRow.package_name || summaryData.title || "").trim();
		const message = __("Package created.");
		return {
			context_slug: workbench ? "workbench" : "approved-demands",
			create_package_success: true,
			title: message,
			create_package_success_message: message,
			next_action_label: __("Complete readiness and submit for review."),
			package_code: packageCode,
			package_name: packageName,
			primary_action: {
				label: __("Open Package"),
				action: "open_package_next",
				testid: "pp2-open-package-next-action",
			},
			secondary_actions: workbench
				? [
						{
							label: __("Back to Workbench"),
							action: "back_to_workbench",
							testid: "pp3-back-to-workbench",
						},
					]
				: [
						{
							label: __("Back to Approved Demands"),
							action: "back_to_approved_demands",
							testid: "pp2-back-to-approved-demands",
						},
					],
			show_evidence_action: false,
			demand_code: String(result.demand_code || summaryData.demand_code || "").trim(),
			target_plan_code: String(
				result.procurement_plan_code || summaryData.target_plan_code || "",
			).trim(),
			inclusion_code: String(result.inclusion_code || summaryData.inclusion_code || "").trim(),
		};
	}

	function mountCreatePackageSuccessSummary(shell, payloadSummary, createResult, opts) {
		const o = opts || {};
		const slug = String(o.slug || readSurfaceSlug() || "").trim();
		const workbench = isPlanningHomeSlug(slug);
		const successSummary = createPackageSuccessSummary(payloadSummary, createResult, {
			workbench: workbench,
		});
		mountPlanningSelectedSummary(shell, {
			summary: successSummary,
			slug: slug,
			onPrimaryAction: function (action) {
				const actionKey = String((action && action.action) || "").trim();
				if (actionKey !== "open_package_next") return;
				const packageCode = String(successSummary.package_code || "").trim();
				if (!packageCode) {
					frappe.show_alert({
						indicator: "orange",
						message: __("Package reference is missing."),
					});
					return;
				}
				window.location.href = buildWorkbenchOpenPackageUrl(packageCode);
			},
			onSecondaryAction: function (action) {
				const actionKey = String((action && action.action) || "").trim();
				if (actionKey === "back_to_workbench") {
					const packageCode = String(successSummary.package_code || "").trim();
					if (packageCode) {
						window.location.href = buildWorkbenchOpenPackageUrl(packageCode);
						return;
					}
					refreshWorkbenchWorkList(shell, slug, "draft_packages");
					return;
				}
				if (actionKey === "back_to_approved_demands") {
					window.location.href = ROOT_PATH + "?queue=needs-planning";
				}
			},
		});
	}

	function includePlanSuccessSummary(payloadSummary, includeResult, contextOpts) {
		const summaryData = payloadSummary || {};
		const result = includeResult || {};
		const ctx = contextOpts || {};
		const workbench = ctx.workbench === true;
		const successMessage = __("Demand added to the active procurement plan.");
		const legacyMessage = __("Demand added to the procurement plan.");
		const message = workbench ? successMessage : legacyMessage;
		return {
			context_slug: workbench ? "workbench" : "approved-demands",
			include_success: true,
			title: message,
			include_success_message: message,
			next_action_label: __("Create package."),
			primary_action: {
				label: __("Create Package"),
				action: "create_package_next",
				testid: "pp2-create-package-next-action",
			},
			secondary_actions: workbench
				? [
						{
							label: __("Back to Workbench"),
							action: "back_to_workbench",
							testid: "pp3-back-to-workbench",
						},
					]
				: [
						{
							label: __("Back to Approved Demands"),
							action: "back_to_approved_demands",
							testid: "pp2-back-to-approved-demands",
						},
					],
			show_evidence_action: false,
			demand_code: String(result.demand_code || summaryData.demand_code || "").trim(),
			target_plan_code: String(
				result.procurement_plan_code || summaryData.target_plan_code || "",
			).trim(),
			inclusion_code: String(result.inclusion_code || "").trim(),
		};
	}

	function openCreatePackageModalForShell(shell, summaryData, opts) {
		const o = opts || {};
		const createApi =
			kentender_procurement &&
			kentender_procurement.PlanningCreatePackageModal &&
			typeof kentender_procurement.PlanningCreatePackageModal.open === "function"
				? kentender_procurement.PlanningCreatePackageModal
				: null;
		const payload = summaryData || {};
		if (!createApi) {
			frappe.show_alert({
				indicator: "orange",
				message: __("Create Package modal is unavailable."),
			});
			return;
		}
		const launch = function (drawerMessage) {
			const drawer = drawerMessage || {};
			if (!drawer.ok) {
				frappe.show_alert({
					indicator: "orange",
					message:
						String(drawer.message || "").trim() ||
						__("Create Package context is unavailable."),
				});
				return;
			}
			createApi.open({
				demand_name: String(drawer.demand_name || payload.title || "").trim(),
				active_plan_name: String(drawer.active_plan_name || payload.target_plan_name || "").trim(),
				category_label: String(drawer.category_label || "").trim(),
				method_label: String(drawer.method_label || "").trim(),
				value_label: String(drawer.value_label || payload.value_label || "").trim(),
				funding_label: String(drawer.funding_label || payload.funding_label || "").trim(),
				package_title_default: String(drawer.package_title_default || drawer.demand_name || "").trim(),
				inclusion_code: String(drawer.inclusion_code || payload.inclusion_code || "").trim(),
				create_allowed: drawer.create_allowed !== false,
				blocker_code: String(drawer.blocker_code || "").trim(),
				blocker_message: String(drawer.blocker_message || "").trim(),
				duplicate_package: drawer.duplicate_package === true,
				existing_package_name: String(drawer.existing_package_name || "").trim(),
				existing_package_code: String(drawer.existing_package_code || "").trim(),
				onSuccess: function (createResult) {
					if (typeof o.onCreateSuccess === "function") {
						o.onCreateSuccess(createResult || {});
						return;
					}
					mountCreatePackageSuccessSummary(shell, payload, createResult || {}, {
						slug: o.slug,
					});
				},
				onOpenExistingPackage: function () {
					window.location.href = buildWorkbenchOpenPackageUrl(
						String(drawer.existing_package_code || "").trim(),
					);
				},
			});
		};
		frappe.call({
			method: CREATE_PACKAGE_DRAWER_API,
			args: {
				demand_code: String(payload.demand_code || "").trim(),
				plan_code: String(payload.target_plan_code || "").trim(),
				inclusion_code: String(payload.inclusion_code || "").trim(),
			},
			callback: function (response) {
				launch((response && response.message) || {});
			},
			error: function () {
				frappe.show_alert({
					indicator: "orange",
					message: __("Create Package context could not be loaded."),
				});
			},
		});
	}

	function mountIncludePlanSuccessSummary(shell, payloadSummary, includeResult, opts) {
		const o = opts || {};
		const slug = String(o.slug || readSurfaceSlug() || "").trim();
		const workbench = isPlanningHomeSlug(slug);
		const successSummary = includePlanSuccessSummary(payloadSummary, includeResult, {
			workbench: workbench,
		});
		mountPlanningSelectedSummary(shell, {
			summary: successSummary,
			slug: slug,
			onPrimaryAction: function (action) {
				const actionKey = String((action && action.action) || "").trim();
				if (actionKey !== "create_package_next") return;
				if (workbench) {
					openCreatePackageModalForShell(shell, successSummary, { slug: slug });
					return;
				}
				window.location.href = ROOT_PATH + "/packages";
			},
			onSecondaryAction: function (action) {
				const actionKey = String((action && action.action) || "").trim();
				if (actionKey === "back_to_workbench") {
					mountPlanningSelectedSummary(shell, { slug: slug });
					const mainHost = shell && shell.querySelector
						? shell.querySelector('[data-testid="pp2-primary-main-host"]')
						: null;
					if (mainHost) {
						mountPlanningWorkList(mainHost, slug, shell);
					}
					return;
				}
				if (actionKey === "back_to_approved_demands") {
					window.location.href = ROOT_PATH + "?queue=needs-planning";
				}
			},
		});
	}

	function openIncludePlanModalForShell(shell, summaryPayload, opts) {
		const o = opts || {};
		const includeApi =
			kentender_procurement &&
			kentender_procurement.PlanningIncludePlanModal &&
			typeof kentender_procurement.PlanningIncludePlanModal.open === "function"
				? kentender_procurement.PlanningIncludePlanModal
				: null;
		const summaryData = summaryPayload || {};
		if (!includeApi) {
			frappe.show_alert({
				indicator: "orange",
				message: __("Include in Plan modal is unavailable."),
			});
			return;
		}
		includeApi.open({
			demand_code: String(summaryData.demand_code || "").trim(),
			demand_name: String(summaryData.title || "").trim(),
			value_label: String(summaryData.value_label || "").trim(),
			funding_label: String(summaryData.funding_label || "").trim(),
			target_plan_code: String(summaryData.target_plan_code || "").trim(),
			target_plan_name: String(summaryData.target_plan_name || "").trim(),
			target_plan_locked: o.target_plan_locked === true,
			demand_item_codes: Array.isArray(summaryData.demand_item_codes) ? summaryData.demand_item_codes : [],
			include_allowed: summaryData.include_allowed !== false,
			blocker_message: String(summaryData.include_blocker_message || "").trim(),
			onBlocked: function (message) {
				const withAlert = Object.assign({}, summaryData, {
					include_alert_message: String(message || "").trim(),
				});
				mountPlanningSelectedSummary(shell, {
					summary: withAlert,
					slug: o.slug,
					onPrimaryAction: function () {
						openIncludePlanModalForShell(shell, withAlert, o);
					},
					onSecondaryAction: o.onSecondaryAction,
					onEvidenceAction: o.onEvidenceAction,
				});
			},
			onSuccess: function (includeResult) {
				if (typeof o.onIncludeSuccess === "function") {
					o.onIncludeSuccess(includeResult || {}, summaryData);
					return;
				}
				mountIncludePlanSuccessSummary(shell, summaryData, includeResult || {}, o);
			},
		});
	}

	function requestIncludePlanModalForShell(shell, summaryPayload, opts) {
		const summaryData = summaryPayload || {};
		const demandCode = String(summaryData.demand_code || "").trim();
		const launch = function (payload) {
			openIncludePlanModalForShell(shell, payload, opts);
		};
		const fetchDrawer = function (planCode) {
			if (!demandCode) {
				launch(summaryData);
				return;
			}
			const args = { demand_code: demandCode };
			if (planCode) args.plan_code = planCode;
			frappe.call({
				method: APPROVED_DEMANDS_DRAWER_API,
				args: args,
				callback: function (response) {
					const message = response && response.message ? response.message : {};
					if (message && message.ok && typeof opts.refreshSummaryFromDrawer === "function") {
						launch(opts.refreshSummaryFromDrawer(message) || summaryData);
						return;
					}
					launch(summaryData);
				},
				error: function () {
					launch(summaryData);
				},
			});
		};
		if (opts.useActivePlanContext) {
			frappe.call({
				method: ACTIVE_PLAN_API,
				args: {},
				callback: function (response) {
					const message = response && response.message ? response.message : {};
					const planCode = message && message.has_active_plan ? String(message.plan_code || "").trim() : "";
					fetchDrawer(planCode);
				},
				error: function () {
					fetchDrawer("");
				},
			});
			return;
		}
		fetchDrawer("");
	}

	function workbenchPseudoItemFromWorkItem(workItem) {
		const it = workItem || {};
		const subtitle = String(it.subtitle || "").trim();
		const parts = subtitle
			.split(" · ")
			.map(function (part) {
				return String(part || "").trim();
			})
			.filter(Boolean);
		const budgetLinked = /budget linked/i.test(subtitle);
		let valuePart = "";
		if (parts.length >= 3) {
			valuePart = parts[1];
		} else if (parts.length === 2 && !budgetLinked) {
			valuePart = parts[1];
		}
		return {
			title: String(it.title || "").trim(),
			raw: {
				demand: { code: String(it.underlying_object_code || "").trim() },
				category: parts[0] || "",
				estimated_value: valuePart,
				currency: "KES",
			},
		};
	}

	function openWorkbenchIncludePlanModal(shell, workItem, slug) {
		const pseudoItem = workbenchPseudoItemFromWorkItem(workItem);
		const baseSummary = approvedDemandSummaryFromDrawer(pseudoItem, "needs_planning", {});
		requestIncludePlanModalForShell(shell, baseSummary, {
			slug: slug,
			useActivePlanContext: true,
			target_plan_locked: true,
			refreshSummaryFromDrawer: function (drawerMessage) {
				return approvedDemandSummaryFromDrawer(pseudoItem, "needs_planning", drawerMessage || {});
			},
		});
	}

	function renderApprovedDemandSummary(shell, item, queueId) {
		if (!shell || !item) return;
		const summaryHost = ensureSummaryHost(shell);
		if (!summaryHost) return;
		const demandCode = String((((item || {}).raw || {}).demand || {}).code || "").trim();
		const token = (approvedDemandSummaryTokens.get(summaryHost) || 0) + 1;
		approvedDemandSummaryTokens.set(summaryHost, token);
		const baseSummary = approvedDemandSummaryFromDrawer(item, queueId, {});
		const includeModalOpts = {
			slug: "approved-demands",
			refreshSummaryFromDrawer: function (drawerMessage) {
				return approvedDemandSummaryFromDrawer(item, queueId, drawerMessage || {});
			},
			onSecondaryAction: function (action) {
				const route = String((action && action.route) || "").trim();
				if (!route) return;
				window.location.href = route;
			},
		};
		mountPlanningSelectedSummary(shell, {
			summary: baseSummary,
			slug: "approved-demands",
			onPrimaryAction: function () {
				requestIncludePlanModalForShell(shell, baseSummary, includeModalOpts);
			},
			onSecondaryAction: includeModalOpts.onSecondaryAction,
		});
		if (!demandCode) return;
		frappe.call({
			method: APPROVED_DEMANDS_DRAWER_API,
			args: { demand_code: demandCode },
			callback: function (response) {
				if (approvedDemandSummaryTokens.get(summaryHost) !== token) return;
				const message = response && response.message ? response.message : {};
				if (!message || !message.ok) return;
				const refreshedSummary = approvedDemandSummaryFromDrawer(item, queueId, message);
				mountPlanningSelectedSummary(shell, {
					summary: refreshedSummary,
					slug: "approved-demands",
					onPrimaryAction: function () {
						requestIncludePlanModalForShell(shell, refreshedSummary, includeModalOpts);
					},
					onSecondaryAction: includeModalOpts.onSecondaryAction,
				});
			},
		});
	}

	function renderApprovedDemandsQueue(mainHost, shell) {
		if (!mainHost || !shell) return;
		const workListHost = mainHost.querySelector('[data-testid="pp2-primary-work-list-host"]');
		if (!workListHost) return;
		const queueApi =
			kentender_procurement &&
			kentender_procurement.PlanningQueueTabs &&
			typeof kentender_procurement.PlanningQueueTabs.readActiveFromUrl === "function"
				? kentender_procurement.PlanningQueueTabs
				: null;
		const workListApi =
			kentender_procurement &&
			kentender_procurement.PlanningWorkList &&
			typeof kentender_procurement.PlanningWorkList.renderForSlug === "function"
				? kentender_procurement.PlanningWorkList
				: null;
		if (!queueApi || !workListApi) return;
		const queueId = queueApi.readActiveFromUrl("approved-demands");
		const token = (approvedDemandFetchTokens.get(workListHost) || 0) + 1;
		approvedDemandFetchTokens.set(workListHost, token);
		workListApi.renderForSlug(workListHost, "approved-demands", {
			items: [],
			emptyMessage: __("Loading approved demands..."),
		});

		frappe.call({
			method: APPROVED_DEMANDS_QUEUE_API,
			args: { queue: queueId, start: 0, limit: 50 },
			callback: function (response) {
				if (approvedDemandFetchTokens.get(workListHost) !== token) return;
				const message = response && response.message ? response.message : {};
				if (!message || !message.ok) {
					workListApi.renderForSlug(workListHost, "approved-demands", {
						items: [],
						emptyMessage: approvedDemandEmptyMessage(queueId),
					});
					mountPlanningSelectedSummary(shell, { slug: "approved-demands" });
					return;
				}
				const rows = Array.isArray(message.rows) ? message.rows : [];
				const items = rows.map(function (row) {
					return mapApprovedDemandQueueRow(row, queueId);
				});
				let selectedId = "";
				if (typeof workListApi.readSelectedFromUrl === "function") {
					selectedId = workListApi.readSelectedFromUrl(items);
					try {
						const rawItem = new URLSearchParams(window.location.search).get("item");
						if (rawItem && !selectedId && typeof workListApi.setSelectedUrl === "function") {
							workListApi.setSelectedUrl("");
						}
					} catch (e) {
						/* ignore */
					}
				}

				workListApi.renderForSlug(workListHost, "approved-demands", {
					items: items,
					selectedId: selectedId,
					emptyMessage: approvedDemandEmptyMessage(queueId),
					onSelect: function (_itemId, item) {
						if (!item) {
							mountPlanningSelectedSummary(shell, { slug: "approved-demands" });
							return;
						}
						renderApprovedDemandSummary(shell, item, queueId);
					},
				});

				if (!selectedId) {
					mountPlanningSelectedSummary(shell, { slug: "approved-demands" });
					return;
				}
				let selectedItem = null;
				for (let i = 0; i < items.length; i += 1) {
					if (String(items[i].id || "") === String(selectedId || "")) {
						selectedItem = items[i];
						break;
					}
				}
				if (!selectedItem) {
					mountPlanningSelectedSummary(shell, { slug: "approved-demands" });
					return;
				}
				renderApprovedDemandSummary(shell, selectedItem, queueId);
			},
			error: function () {
				if (approvedDemandFetchTokens.get(workListHost) !== token) return;
				workListApi.renderForSlug(workListHost, "approved-demands", {
					items: [],
					emptyMessage: approvedDemandEmptyMessage(queueId),
				});
				mountPlanningSelectedSummary(shell, { slug: "approved-demands" });
			},
		});
	}

	function bindApprovedDemandsQueueRefresh(mainHost, shell) {
		if (!mainHost || !shell) return;
		const queueHost = mainHost.querySelector('[data-testid="pp2-primary-queue-host"]');
		if (!queueHost || queueHost.getAttribute("data-pp2-approved-bound") === "1") return;
		queueHost.setAttribute("data-pp2-approved-bound", "1");
		queueHost.addEventListener("click", function (event) {
			const target = event.target && event.target.closest ? event.target.closest("[data-pp2-queue-id]") : null;
			if (!target) return;
			window.setTimeout(function () {
				renderApprovedDemandsQueue(mainHost, shell);
			}, 0);
		});
	}

	function mountPlanningHome(root) {
		if (!root) return;
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningHome &&
			typeof kentender_procurement.PlanningHome.render === "function"
				? kentender_procurement.PlanningHome
				: null;
		if (api) {
			api.render(root);
			return;
		}
		root.innerHTML =
			'<article class="pp2-planning-home" data-testid="pp2-planning-home-surface">' +
			'<div class="pp2-planning-home__body" data-testid="pp2-planning-home-body">' +
			'<div class="pp2-planning-home__summary-host"></div>' +
			'<div class="pp2-planning-home__queues" data-testid="pp2-planning-home-queues"></div>' +
			"</div></article>";
	}

	function readRightPanelCollapsed() {
		try {
			const raw = window.localStorage.getItem(RIGHT_PANEL_STATE_KEY);
			if (raw === null) return true;
			return raw === "1";
		} catch (e) {
			return true;
		}
	}

	function writeRightPanelCollapsed(collapsed) {
		try {
			window.localStorage.setItem(RIGHT_PANEL_STATE_KEY, collapsed ? "1" : "0");
		} catch (e) {
			/* ignore */
		}
	}

	function syncSurfaceUrl(slug, options) {
		const opts = options || {};
		const url = new URL(window.location.href);
		const preserveSearch = opts.preserveSearch !== false;
		url.pathname = slug ? `${ROOT_PATH}/${slug}` : ROOT_PATH;
		if (!preserveSearch) {
			url.search = "";
		}
		const next = url.pathname + url.search + url.hash;
		const curr = window.location.pathname + window.location.search + window.location.hash;
		if (next !== curr) {
			window.history.replaceState({}, "", next);
		}
	}

	function resolveWorkspaceRoot() {
		return (
			document.getElementById("kt-pp-root") ||
			document.querySelector(".kt-pp-injected-shell")
		);
	}

	function ensureWorkspaceRoot() {
		let root = resolveWorkspaceRoot();
		if (root) return root;
		const mountPoint =
			document.querySelector(".layout-main-section .editor-js-container") ||
			document.querySelector(".layout-main-section") ||
			document.querySelector(".page-content");
		if (!mountPoint) return null;
		root = document.createElement("div");
		root.id = "kt-pp-root";
		root.className = "kt-pp-injected-shell";
		mountPoint.innerHTML = "";
		mountPoint.appendChild(root);
		return root;
	}

	const SURFACE_PURPOSE = {
		"": __("Convert approved demand into tender-ready procurement packages."),
		"approved-demands": __("Which approved demands can be planned now?"),
		plans: __("Create, activate, and review procurement plans."),
		packages: __("Which packages need work, review, release, or follow-up?"),
		releases: __("Which packages have left Planning, and where did they go?"),
	};

	function surfacePurposeForSlug(slug) {
		const emptyApi =
			kentender_procurement &&
			kentender_procurement.PlanningEmptyState &&
			typeof kentender_procurement.PlanningEmptyState.purposeForSlug === "function"
				? kentender_procurement.PlanningEmptyState
				: null;
		if (emptyApi) return emptyApi.purposeForSlug(slug);
		const key = slug == null ? "" : String(slug);
		return SURFACE_PURPOSE[key] || SURFACE_PURPOSE[""];
	}

	function renderSurfaceEmptyState(root, slug) {
		if (!root) return;
		const emptyApi =
			kentender_procurement &&
			kentender_procurement.PlanningEmptyState &&
			typeof kentender_procurement.PlanningEmptyState.renderForSlug === "function"
				? kentender_procurement.PlanningEmptyState
				: null;
		root.innerHTML =
			'<section class="pp2-surface-empty-state" data-testid="pp2-surface-empty-state"></section>';
		const wrapper = root.querySelector('[data-testid="pp2-surface-empty-state"]');
		if (!wrapper) return;
		if (emptyApi) {
			emptyApi.renderForSlug(wrapper, slug);
			return;
		}
		wrapper.innerHTML =
			'<div class="pp2-empty-state" data-testid="pp2-empty-state">' +
			'<p class="text-muted small mb-0" data-testid="pp2-empty-state-message">' +
			esc(__("No items need your attention right now.")) +
			"</p></div>";
	}

	function mountPlanningPageHeader(contextHost, slug) {
		if (!contextHost) return;
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningPageHeader &&
			typeof kentender_procurement.PlanningPageHeader.renderForSlug === "function"
				? kentender_procurement.PlanningPageHeader
				: null;
		if (api) {
			api.renderForSlug(contextHost, slug);
			return;
		}
		const copy = surfacePurposeForSlug(slug);
		const surface = surfaceForSlug(slug);
		contextHost.innerHTML =
			'<header class="pp2-page-header" data-testid="pp2-page-header">' +
			'<h2 class="h5 mb-1" data-testid="pp2-page-title">' +
			esc(surface.subtitle || __("Procurement Planning")) +
			"</h2>" +
			'<p class="text-muted small mb-0" data-testid="pp2-page-purpose">' +
			esc(copy) +
			"</p></header>";
	}

	function clearPlanningWorkUnavailable(mainHost) {
		if (!mainHost) return;
		const panel = mainHost.querySelector('[data-testid="pp3-planning-work-unavailable"]');
		if (panel && panel.parentNode) {
			panel.parentNode.removeChild(panel);
		}
	}

	function mountPlanningWorkUnavailable(mainHost) {
		if (!mainHost) return;
		clearWorkbenchHosts(mainHost);
		clearPlanningWorkUnavailable(mainHost);
		let panel = mainHost.querySelector('[data-testid="pp3-planning-work-unavailable"]');
		if (!panel) {
			panel = document.createElement("section");
			panel.className = "pp3-planning-work-unavailable";
			panel.setAttribute("data-testid", "pp3-planning-work-unavailable");
			mainHost.appendChild(panel);
		}
		panel.innerHTML =
			'<p class="pp3-planning-work-unavailable__message text-muted mb-0">' +
			esc(__("Planning work is unavailable until an active procurement plan is selected.")) +
			"</p>";
	}

	function fetchActivePlanPayload() {
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningActivePlanBanner &&
			typeof kentender_procurement.PlanningActivePlanBanner.fetchPayload === "function"
				? kentender_procurement.PlanningActivePlanBanner
				: null;
		if (!api) {
			return Promise.resolve({ has_active_plan: true });
		}
		return api.fetchPayload({});
	}

	function mountPlanningContextWithPayload(contextHost, slug, payload) {
		if (!contextHost) return;
		contextHost.innerHTML =
			'<div class="pp2-primary-context-active-plan" data-testid="pp3-active-plan-host"></div>' +
			'<div class="pp2-primary-context-page-header" data-testid="pp2-page-header-host"></div>';
		const activePlanHost = contextHost.querySelector('[data-testid="pp3-active-plan-host"]');
		const pageHeaderHost = contextHost.querySelector('[data-testid="pp2-page-header-host"]');
		const bannerApi =
			kentender_procurement &&
			kentender_procurement.PlanningActivePlanBanner &&
			typeof kentender_procurement.PlanningActivePlanBanner.render === "function"
				? kentender_procurement.PlanningActivePlanBanner
				: null;
		if (bannerApi && activePlanHost) {
			bannerApi.render(activePlanHost, payload || {});
		} else if (activePlanHost) {
			activePlanHost.innerHTML = "";
		}
		mountPlanningPageHeader(pageHeaderHost, slug);
	}

	function mountWorkbenchRootWork(mainHost, shell, slug, activePlanPayload) {
		if (!mainHost || !shell) return;
		const payload = activePlanPayload || {};
		const contextHost = shell.querySelector('[data-testid="pp2-primary-context-host"]');
		if (contextHost) {
			mountPlanningContextWithPayload(contextHost, slug, payload);
		}
		clearWorkbenchHosts(mainHost);
		clearPlanningWorkUnavailable(mainHost);
		if (!payload.has_active_plan) {
			shell.setAttribute("data-pp3-planning-blocked", "1");
			mountPlanningWorkUnavailable(mainHost);
			mountPlanningSelectedSummary(shell, { slug: slug });
			return;
		}
		shell.removeAttribute("data-pp3-planning-blocked");
		mountPlanningQueueTabs(mainHost, slug);
		mountPlanningWorkList(mainHost, slug, shell);
		bindWorkbenchQueueRefresh(mainHost, slug, shell);
	}

	function mountActivePlanBanner(host) {
		if (!host) return;
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningActivePlanBanner &&
			typeof kentender_procurement.PlanningActivePlanBanner.fetchAndRender === "function"
				? kentender_procurement.PlanningActivePlanBanner
				: null;
		if (!api) {
			host.innerHTML = "";
			return;
		}
		api.fetchAndRender(host, {});
	}

	function mountPlanningContext(contextHost, slug) {
		if (!contextHost) return;
		contextHost.innerHTML =
			'<div class="pp2-primary-context-active-plan" data-testid="pp3-active-plan-host"></div>' +
			'<div class="pp2-primary-context-page-header" data-testid="pp2-page-header-host"></div>';
		const activePlanHost = contextHost.querySelector('[data-testid="pp3-active-plan-host"]');
		const pageHeaderHost = contextHost.querySelector('[data-testid="pp2-page-header-host"]');
		if (isProcurementPlansSlug(slug)) {
			if (activePlanHost) activePlanHost.innerHTML = "";
		} else if (isPackageDetailSlug(slug)) {
			if (activePlanHost) activePlanHost.innerHTML = "";
		} else {
			mountActivePlanBanner(activePlanHost);
		}
		mountPlanningPageHeader(pageHeaderHost, slug);
	}

	function mountProcurementPlansSurface(mainHost, slug, root) {
		if (!mainHost) return;
		clearWorkbenchHosts(mainHost);
		clearPlanningWorkUnavailable(mainHost);
		const children = Array.from(mainHost.children);
		for (let i = 0; i < children.length; i += 1) {
			if (children[i] !== root) {
				mainHost.removeChild(children[i]);
			}
		}
		const markerId = surfaceForSlug(slug).testId;
		if (root) {
			root.innerHTML =
				'<article class="pp3-procurement-plans-surface" data-testid="' +
				esc(markerId) +
				'"><div class="pp3-procurement-plans-surface__body" data-testid="pp3-procurement-plans-body"></div></article>';
			const bodyHost = root.querySelector('[data-testid="pp3-procurement-plans-body"]');
			if (bodyHost) {
				bodyHost.innerHTML =
					'<div class="pp3-procurement-plans-layout"><div class="pp3-procurement-plans-layout__list" data-testid="pp3-procurement-plans-list-host"></div><div class="pp3-procurement-plans-layout__summary" data-testid="pp3-procurement-plans-summary-host"></div></div>';
				const listHost = bodyHost.querySelector('[data-testid="pp3-procurement-plans-list-host"]');
				const planListApi =
					kentender_procurement &&
					kentender_procurement.PlanningPlanList &&
					typeof kentender_procurement.PlanningPlanList.render === "function"
						? kentender_procurement.PlanningPlanList
						: null;
				if (planListApi && listHost) {
					const summaryHost = bodyHost.querySelector(
						'[data-testid="pp3-procurement-plans-summary-host"]',
					);
					const summaryApi =
						kentender_procurement &&
						kentender_procurement.PlanningPlanSummary &&
						typeof kentender_procurement.PlanningPlanSummary.render === "function"
							? kentender_procurement.PlanningPlanSummary
							: null;
					function renderSummary(plan) {
						if (!summaryApi || !summaryHost || !plan) return;
						summaryApi.render(summaryHost, {
							plan: plan,
							onRefresh: function () {
								if (typeof window.__kt_pp_refresh_procurement_plans === "function") {
									window.__kt_pp_refresh_procurement_plans();
								}
							},
						});
					}
					function selectPlan(plan) {
						const planId = String((plan && plan.plan_id) || "").trim();
						if (!planId) return;
						try {
							const url = new URL(window.location.href);
							url.searchParams.set("plan", planId);
							window.history.replaceState({}, "", url.pathname + url.search);
						} catch (e) {
							/* ignore */
						}
						renderSummary(plan);
						const rows = listHost.querySelectorAll('[data-testid="pp3-plan-row"]');
						for (let i = 0; i < rows.length; i += 1) {
							const row = rows[i];
							const active = String(row.getAttribute("data-pp3-plan-id") || "").trim() === planId;
							row.classList.toggle("is-active", active);
							row.setAttribute("aria-selected", active ? "true" : "false");
						}
					}
					planListApi.render(listHost, {
						onSelect: selectPlan,
						onLoaded: function (_payload, plans) {
							if (!Array.isArray(plans) || !plans.length) return;
							let selectedId = "";
							try {
								selectedId = String(
									new URLSearchParams(window.location.search).get("plan") || "",
								).trim();
							} catch (e) {
								selectedId = "";
							}
							const match =
								plans.find(function (row) {
									return String(row.plan_id || row.plan_code || "").trim() === selectedId;
								}) || plans[0];
							if (match) selectPlan(match);
						},
						selectedPlanId: (function () {
							try {
								return new URLSearchParams(window.location.search).get("plan") || "";
							} catch (e) {
								return "";
							}
						})(),
					});
					window.__kt_pp_refresh_procurement_plans = function () {
						planListApi.render(listHost, {
							onSelect: selectPlan,
							selectedPlanId: (function () {
								try {
									return new URLSearchParams(window.location.search).get("plan") || "";
								} catch (e) {
									return "";
								}
							})(),
						});
					};
				}
			}
		}
	}

	function mountPackageDetailSurface(mainHost, packageCode, root) {
		if (!mainHost) return;
		clearWorkbenchHosts(mainHost);
		clearPlanningWorkUnavailable(mainHost);
		const children = Array.from(mainHost.children);
		for (let i = 0; i < children.length; i += 1) {
			if (children[i] !== root) {
				mainHost.removeChild(children[i]);
			}
		}
		const markerId = surfaceForSlug("package-detail").testId;
		if (root) {
			root.innerHTML =
				'<article class="pp3-package-detail-surface" data-testid="' +
				esc(markerId) +
				'"><div class="pp3-package-detail-surface__body" data-testid="pp3-package-detail-host"></div></article>';
			const bodyHost = root.querySelector('[data-testid="pp3-package-detail-host"]');
			const detailApi =
				kentender_procurement &&
				kentender_procurement.PlanningPackageDetail &&
				typeof kentender_procurement.PlanningPackageDetail.render === "function"
					? kentender_procurement.PlanningPackageDetail
					: null;
			if (detailApi && bodyHost) {
				detailApi.render(bodyHost, { packageCode: packageCode });
			}
		}
	}

	function mountPlanningQueueTabs(mainHost, slug) {
		if (!mainHost) return;
		let queueHost = mainHost.querySelector('[data-testid="pp2-primary-queue-host"]');
		if (!queueHost) {
			queueHost = document.createElement("div");
			queueHost.className = "pp2-primary-queue-host";
			queueHost.setAttribute("data-testid", "pp2-primary-queue-host");
			mainHost.insertBefore(queueHost, mainHost.firstChild);
		} else if (mainHost.firstChild !== queueHost) {
			mainHost.insertBefore(queueHost, mainHost.firstChild);
		}
		const isWorkbenchRoot = isPlanningHomeSlug(slug);
		const pp3Api =
			kentender_procurement &&
			kentender_procurement.PlanningWorkbenchQueueTabs &&
			typeof kentender_procurement.PlanningWorkbenchQueueTabs.renderForSlug === "function"
				? kentender_procurement.PlanningWorkbenchQueueTabs
				: null;
		const pp2Api =
			kentender_procurement &&
			kentender_procurement.PlanningQueueTabs &&
			typeof kentender_procurement.PlanningQueueTabs.renderForSlug === "function"
				? kentender_procurement.PlanningQueueTabs
				: null;
		const api = isWorkbenchRoot ? pp3Api : pp2Api;
		if (api) {
			api.renderForSlug(queueHost, slug);
			return;
		}
		if (isWorkbenchRoot) {
			const fallbackQueueKeys = {
				needs_planning: true,
				draft_packages: true,
				needs_review: true,
				ready_to_release: true,
				blocked: true,
				recently_released: true,
			};
			let activeQueue = "needs_planning";
			try {
				const rawQueue = new URLSearchParams(window.location.search).get("queue");
				if (rawQueue && fallbackQueueKeys[rawQueue]) {
					activeQueue = rawQueue;
				}
			} catch (e) {
				/* ignore */
			}
			const queueChipHtml = function (queueKey, label, testId) {
				const active = queueKey === activeQueue;
				return (
					'<button type="button" class="btn btn-default btn-sm pp3-workbench-queue-tabs__chip' +
					(active ? " is-active" : "") +
					'" data-testid="' +
					testId +
					'" data-pp3-queue-key="' +
					queueKey +
					'" role="tab" aria-selected="' +
					(active ? "true" : "false") +
					'">' +
					esc(label) +
					"</button>"
				);
			};
			queueHost.innerHTML =
				'<nav class="pp3-workbench-queue-tabs" data-testid="pp3-workbench-queue-tabs" role="tablist">' +
				queueChipHtml("needs_planning", __("Needs Planning"), "pp3-queue-needs-planning") +
				queueChipHtml("draft_packages", __("Draft Packages"), "pp3-queue-draft-packages") +
				queueChipHtml("needs_review", __("Needs Review"), "pp3-queue-needs-review") +
				queueChipHtml("ready_to_release", __("Ready to Release"), "pp3-queue-ready-release") +
				queueChipHtml("blocked", __("Blocked"), "pp3-queue-blocked") +
				queueChipHtml("recently_released", __("Recently Released"), "pp3-queue-recently-released") +
				"</nav>";
			const fallbackButtons = queueHost.querySelectorAll("[data-pp3-queue-key]");
			for (let i = 0; i < fallbackButtons.length; i += 1) {
				const button = fallbackButtons[i];
				if (button.getAttribute("data-bound") === "1") continue;
				button.setAttribute("data-bound", "1");
				button.addEventListener("click", function () {
					const queueKey = String(button.getAttribute("data-pp3-queue-key") || "").trim();
					if (!fallbackQueueKeys[queueKey]) return;
					try {
						const url = new URL(window.location.href);
						url.searchParams.set("queue", queueKey);
						window.history.replaceState({}, "", url.pathname + url.search + url.hash);
					} catch (e) {
						/* ignore */
					}
					mountPlanningQueueTabs(mainHost, slug);
				});
			}
			return;
		}
		queueHost.innerHTML = "";
	}

	function mountPlanningAdvancedFilters(mainHost, slug) {
		if (!mainHost) return;
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningAdvancedFilters &&
			typeof kentender_procurement.PlanningAdvancedFilters.renderForSlug === "function"
				? kentender_procurement.PlanningAdvancedFilters
				: null;
		let filtersHost = mainHost.querySelector('[data-testid="pp2-primary-filters-host"]');
		if (!api || !api.isAvailableForSlug(slug)) {
			if (filtersHost) filtersHost.remove();
			return;
		}
		const queueHost = mainHost.querySelector('[data-testid="pp2-primary-queue-host"]');
		const workListHost = mainHost.querySelector('[data-testid="pp2-primary-work-list-host"]');
		if (!filtersHost) {
			filtersHost = document.createElement("div");
			filtersHost.className = "pp2-primary-filters-host";
			filtersHost.setAttribute("data-testid", "pp2-primary-filters-host");
		}
		if (workListHost) {
			mainHost.insertBefore(filtersHost, workListHost);
		} else if (queueHost && queueHost.nextSibling) {
			mainHost.insertBefore(filtersHost, queueHost.nextSibling);
		} else if (queueHost) {
			if (queueHost.nextSibling) {
				mainHost.insertBefore(filtersHost, queueHost.nextSibling);
			} else {
				mainHost.appendChild(filtersHost);
			}
		} else {
			mainHost.insertBefore(filtersHost, mainHost.firstChild);
		}
		api.renderForSlug(filtersHost, slug);
	}

	function ensureSummaryHost(shell) {
		if (!shell) return null;
		const rightPanel = shell.querySelector('[data-testid="pp2-primary-right-panel"]');
		if (!rightPanel) return null;
		let summaryHost = rightPanel.querySelector('[data-testid="pp2-primary-summary-host"]');
		if (!summaryHost) {
			summaryHost = document.createElement("div");
			summaryHost.className = "pp2-primary-summary-host";
			summaryHost.setAttribute("data-testid", "pp2-primary-summary-host");
			const nextAction = rightPanel.querySelector('[data-testid="pp2-primary-next-action-panel"]');
			if (nextAction) {
				rightPanel.insertBefore(summaryHost, nextAction);
			} else {
				rightPanel.appendChild(summaryHost);
			}
		}
		return summaryHost;
	}

	function mountPlanningSelectedSummary(shell, opts) {
		if (!shell) return;
		const summaryHost = ensureSummaryHost(shell);
		if (!summaryHost) return;
		const o = opts || {};
		const summarySlug = String((o.summary && o.summary.context_slug) || "").trim();
		const resolvedSlug = String(
			o.slug != null ? o.slug : summarySlug || readSurfaceSlug(),
		).trim();
		const isWorkbenchRoot = isPlanningHomeSlug(resolvedSlug);
		const pp3Api =
			kentender_procurement &&
			kentender_procurement.PlanningWorkbenchSelectedSummary &&
			typeof kentender_procurement.PlanningWorkbenchSelectedSummary.renderIdle === "function"
				? kentender_procurement.PlanningWorkbenchSelectedSummary
				: null;
		const api =
			isWorkbenchRoot && pp3Api
				? pp3Api
				: kentender_procurement &&
					kentender_procurement.PlanningSelectedSummaryPanel &&
					typeof kentender_procurement.PlanningSelectedSummaryPanel.renderIdle === "function"
					? kentender_procurement.PlanningSelectedSummaryPanel
				: null;
		if (!api) {
			summaryHost.innerHTML = "";
			return;
		}
		if (o.summary && String(o.summary.title || "").trim()) {
			api.render(summaryHost, o);
			return;
		}
		api.renderIdle(summaryHost, o);
	}

	function mountPlanningWorkList(mainHost, slug, shell) {
		if (!mainHost) return;
		const queueHost = mainHost.querySelector('[data-testid="pp2-primary-queue-host"]');
		const filtersHost = mainHost.querySelector('[data-testid="pp2-primary-filters-host"]');
		const insertAfter = filtersHost || queueHost;
		let workListHost = mainHost.querySelector('[data-testid="pp2-primary-work-list-host"]');
		if (!workListHost) {
			workListHost = document.createElement("div");
			workListHost.className = "pp2-primary-work-list-host";
			workListHost.setAttribute("data-testid", "pp2-primary-work-list-host");
			if (insertAfter && insertAfter.nextSibling) {
				mainHost.insertBefore(workListHost, insertAfter.nextSibling);
			} else if (insertAfter) {
				mainHost.appendChild(workListHost);
			} else {
				mainHost.insertBefore(workListHost, mainHost.firstChild);
			}
		} else {
			const desiredNext = insertAfter ? insertAfter.nextSibling : mainHost.firstChild;
			if (insertAfter && workListHost.previousSibling !== insertAfter) {
				mainHost.insertBefore(workListHost, desiredNext);
			} else if (!insertAfter && mainHost.firstChild !== workListHost) {
				mainHost.insertBefore(workListHost, mainHost.firstChild);
			}
		}
		const isWorkbenchRoot = isPlanningHomeSlug(slug);
		const pp3Api =
			kentender_procurement &&
			kentender_procurement.PlanningWorkbenchWorkList &&
			typeof kentender_procurement.PlanningWorkbenchWorkList.renderForSlug === "function"
				? kentender_procurement.PlanningWorkbenchWorkList
				: null;
		const pp2Api =
			kentender_procurement &&
			kentender_procurement.PlanningWorkList &&
			typeof kentender_procurement.PlanningWorkList.renderForSlug === "function"
				? kentender_procurement.PlanningWorkList
				: null;
		const api = isWorkbenchRoot ? pp3Api : pp2Api;
		const onSelect = function (_itemId, item) {
			if (!shell) return;
			const summaryApi =
				isWorkbenchRoot
					? kentender_procurement &&
						kentender_procurement.PlanningWorkbenchSelectedSummary &&
						typeof kentender_procurement.PlanningWorkbenchSelectedSummary.summaryFromWorkItem === "function"
						? kentender_procurement.PlanningWorkbenchSelectedSummary
						: null
					: kentender_procurement &&
						kentender_procurement.PlanningSelectedSummaryPanel &&
						typeof kentender_procurement.PlanningSelectedSummaryPanel.summaryFromWorkItem === "function"
						? kentender_procurement.PlanningSelectedSummaryPanel
					: null;
			if (summaryApi && item) {
				const summary = summaryApi.summaryFromWorkItem(item);
				mountPlanningSelectedSummary(shell, {
					slug: slug,
					summary: summary,
					onPrimaryAction: function (action) {
						if (String((action && action.action) || "").trim() === "include_in_plan") {
							openWorkbenchIncludePlanModal(shell, item, slug);
						}
					},
					onEvidenceAction: isWorkbenchRoot
						? function (selectedSummary) {
							openWorkbenchEvidenceDrawer(selectedSummary || summary);
						}
						: null,
				});
			}
		};
		if (api) {
			let queueKey = "needs_planning";
			if (isWorkbenchRoot) {
				const queueTabsApi =
					kentender_procurement &&
					kentender_procurement.PlanningWorkbenchQueueTabs &&
					typeof kentender_procurement.PlanningWorkbenchQueueTabs.readActiveFromUrl === "function"
						? kentender_procurement.PlanningWorkbenchQueueTabs
						: null;
				if (queueTabsApi) {
					queueKey = String(queueTabsApi.readActiveFromUrl() || "").trim() || "needs_planning";
				}
				if (!WORKBENCH_QUEUE_BY_UI_QUEUE[queueKey]) {
					queueKey = "needs_planning";
				}
				api.renderForSlug(workListHost, slug, { queue: queueKey, onSelect: onSelect });
				return;
			}
			api.renderForSlug(workListHost, slug, { items: [], onSelect: onSelect });
			return;
		}
		workListHost.innerHTML = "";
	}

	function bindWorkbenchQueueRefresh(mainHost, slug, shell) {
		if (!mainHost || !isPlanningHomeSlug(slug)) return;
		const queueHost = mainHost.querySelector('[data-testid="pp2-primary-queue-host"]');
		if (!queueHost || queueHost.getAttribute("data-pp3-work-list-bound") === "1") return;
		queueHost.setAttribute("data-pp3-work-list-bound", "1");
		queueHost.addEventListener("click", function () {
			window.requestAnimationFrame(function () {
				mountPlanningWorkList(mainHost, slug, shell);
			});
		});
	}

	function slugifySidebarKey(value) {
		const raw = String(value || "").trim();
		if (!raw) return "";
		try {
			if (frappe.router && typeof frappe.router.slug === "function") {
				return frappe.router.slug(raw);
			}
		} catch (e) {
			/* ignore */
		}
		return raw.toLowerCase().replace(/\s+/g, "-");
	}

	function resolveRouteSidebarPayload() {
		try {
			const route = (frappe.get_route && frappe.get_route()) || [];
			if (!route.length) return null;
			let entity = "";
			if (route[0] === "Workspaces") {
				entity = route[1] === "private" ? route[2] : route[1];
			} else if (route.length === 1) {
				entity = route[0];
			} else {
				entity = route[1];
			}
			const keyRaw = String(entity || "").trim();
			if (!keyRaw) return null;
			const bag = (frappe.boot && frappe.boot.workspace_sidebar_item) || {};
			return bag[keyRaw.toLowerCase()] || bag[slugifySidebarKey(keyRaw)] || null;
		} catch (e) {
			return null;
		}
	}

	function patchSidebarSingleSegmentFastpath() {
		if (sidebarFastpathPatched) return;
		try {
			if (!frappe.ui || !frappe.ui.Sidebar || !frappe.ui.Sidebar.prototype) {
				return;
			}
			const proto = frappe.ui.Sidebar.prototype;
			const original = proto.set_workspace_sidebar;
			if (typeof original !== "function" || original.__ktSingleSegmentFastpathPatched) {
				sidebarFastpathPatched = true;
				return;
			}
			const patched = function (router) {
				try {
					const mapped = resolveRouteSidebarPayload();
					if (mapped && mapped.label) {
						this.setup(mapped.label);
						return;
					}
				} catch (e) {
					/* ignore */
				}
				return original.call(this, router);
			};
			patched.__ktSingleSegmentFastpathPatched = true;
			proto.set_workspace_sidebar = patched;
			sidebarFastpathPatched = true;
		} catch (e2) {
			/* ignore */
		}
	}

	function patchSidebarLookupBySlug() {
		if (sidebarLookupPatched) return;
		try {
			if (!frappe.ui || !frappe.ui.Sidebar || !frappe.ui.Sidebar.prototype) {
				return;
			}
			const proto = frappe.ui.Sidebar.prototype;
			const original = proto.get_workspace_sidebars;
			if (typeof original !== "function" || original.__ktSlugLookupPatched) {
				sidebarLookupPatched = true;
				return;
			}
			const patched = function (link_to) {
				const requested = slugifySidebarKey(link_to);
				let sidebars = [];
				try {
					Object.entries(this.all_sidebar_items || {}).forEach(function (pair) {
						const sidebar = pair[1] || {};
						const items = sidebar.items || [];
						const label = sidebar.label || pair[0];
						for (let i = 0; i < items.length; i += 1) {
							const itemLink = items[i] && items[i].link_to;
							if (!itemLink) continue;
							if (String(itemLink) === String(link_to) || slugifySidebarKey(itemLink) === requested) {
								sidebars.push(label);
								break;
							}
						}
					});
				} catch (e) {
					/* ignore */
				}
				return sidebars;
			};
			patched.__ktSlugLookupPatched = true;
			proto.get_workspace_sidebars = patched;
			sidebarLookupPatched = true;
		} catch (e2) {
			/* ignore */
		}
	}

	function pruneDuplicatePrimaryShells(activeShell) {
		if (!activeShell || !activeShell.parentNode) return;
		const shells = document.querySelectorAll('[data-testid="pp2-primary-workspace-shell"]');
		for (let i = 0; i < shells.length; i += 1) {
			const shell = shells[i];
			if (shell === activeShell) continue;
			if (shell.parentNode) {
				shell.parentNode.removeChild(shell);
			}
		}
	}

	function ensurePrimaryWorkspaceShell(root, slug) {
		if (!root) return null;
		const surface = surfaceForSlug(slug);
		let shell =
			root.closest('[data-testid="pp2-primary-workspace-shell"]') ||
			document.querySelector('[data-testid="pp2-primary-workspace-shell"]');
		if (shell && !shell.isConnected) {
			shell = null;
		}
		if (!shell) {
			shell = document.createElement("section");
			shell.className = "pp2-primary-workspace-shell";
			shell.setAttribute("data-testid", "pp2-primary-workspace-shell");
			const collapsed = readRightPanelCollapsed();
			shell.setAttribute("data-right-panel-collapsed", collapsed ? "1" : "0");
			shell.innerHTML =
				'<div class="pp2-primary-workspace-shell__marker" data-testid="pp3-procurement-planning-shell" aria-hidden="true"></div>' +
				'<div class="pp2-primary-workspace-shell__header">' +
				'<div class="pp2-primary-workspace-shell__breadcrumb text-muted small" data-testid="pp2-primary-breadcrumb"></div>' +
				'<div class="pp2-primary-workspace-shell__context" data-testid="pp2-primary-context-host"></div>' +
				"</div>" +
				'<div class="pp2-primary-workspace-shell__layout">' +
				'<div class="pp2-primary-workspace-shell__main" data-testid="pp2-primary-main-host"></div>' +
				'<aside class="pp2-primary-workspace-shell__right" data-testid="pp2-primary-right-panel">' +
				'<button type="button" class="btn btn-xs btn-default pp2-primary-workspace-shell__toggle" data-testid="pp2-primary-right-panel-toggle"></button>' +
				'<div class="pp2-primary-summary-host" data-testid="pp2-primary-summary-host"></div>' +
				'<div class="pp2-primary-workspace-shell__next-action text-muted small" data-testid="pp2-primary-next-action-panel"></div>' +
				"</aside>" +
				"</div>";
			root.parentNode.insertBefore(shell, root);
		}

		let mainHost = shell.querySelector('[data-testid="pp2-primary-main-host"]');
		if (!mainHost) {
			if (shell.parentNode) {
				shell.parentNode.removeChild(shell);
			}
			return ensurePrimaryWorkspaceShell(root, slug);
		}

		if (mainHost && root.parentNode !== mainHost) {
			mainHost.appendChild(root);
		}
		pruneDuplicatePrimaryShells(shell);

		const breadcrumb = shell.querySelector('[data-testid="pp2-primary-breadcrumb"]');
		if (breadcrumb) {
			breadcrumb.textContent = __("Procurement Planning") + " / " + surface.subtitle;
		}
		const contextHost = shell.querySelector('[data-testid="pp2-primary-context-host"]');
		if (contextHost && !isPlanningHomeSlug(slug)) {
			mountPlanningContext(contextHost, slug);
		}
		const nextActionPanel = shell.querySelector('[data-testid="pp2-primary-next-action-panel"]');
		if (nextActionPanel) {
			nextActionPanel.innerHTML = "";
		}

		const toggle = shell.querySelector('[data-testid="pp2-primary-right-panel-toggle"]');
		if (toggle && toggle.getAttribute("data-bound") !== "1") {
			toggle.setAttribute("data-bound", "1");
			toggle.addEventListener("click", function () {
				const collapsed = shell.getAttribute("data-right-panel-collapsed") === "1";
				shell.setAttribute("data-right-panel-collapsed", collapsed ? "0" : "1");
				writeRightPanelCollapsed(!collapsed);
				toggle.textContent = collapsed ? __("Collapse panel") : __("Expand panel");
			});
		}
		if (toggle) {
			const collapsed = shell.getAttribute("data-right-panel-collapsed") === "1";
			toggle.textContent = collapsed ? __("Expand panel") : __("Collapse panel");
		}
		if (isPlanningHomeSlug(slug)) {
			shell.removeAttribute("data-pp2-home-layout");
			ensureSummaryHost(shell);
			mountPlanningSelectedSummary(shell, { slug: slug });
		} else {
			shell.removeAttribute("data-pp2-home-layout");
			ensureSummaryHost(shell);
			mountPlanningSelectedSummary(shell, { slug: slug });
		}

		return shell;
	}

	function syncSidebarActive(slug) {
		try {
			const target = String(SURFACE_LABELS[slug || ""] || SURFACE_LABELS[""]).trim().toLowerCase();
			const items = document.querySelectorAll(".standard-sidebar-item");
			for (let i = 0; i < items.length; i += 1) {
				const label = String(items[i].textContent || "")
					.trim()
					.toLowerCase();
				items[i].classList.toggle("active-sidebar", label === target);
			}
		} catch (e) {
			/* ignore */
		}
	}

	function collapsePlanningSidebarParent(parent, attempt) {
		if (!parent || isPlanningWorkspaceRoute()) return;
		const nested = parent.querySelector(".nested-container");
		const dropIcon = parent.querySelector(".drop-icon");
		if (!nested || !dropIcon || typeof dropIcon.click !== "function") return;
		if (window.getComputedStyle(nested).display === "none") return;
		dropIcon.click();
		if ((attempt || 0) < 3) {
			window.setTimeout(function () {
				collapsePlanningSidebarParent(parent, (attempt || 0) + 1);
			}, 60);
		}
	}

	function enhanceSidebarVisualHierarchy(slug, parentActive) {
		const parent = document.querySelector('.section-item[title="Procurement Planning"]');
		if (!parent) return false;
		parent.classList.add("kt-pp2-sidebar-parent");
		parent.classList.toggle("kt-pp2-sidebar-parent-active", !!parentActive);
		if (!parentActive) {
			collapsePlanningSidebarParent(parent, 0);
		}
		const sectionBreak = parent.querySelector(".section-break");
		if (sectionBreak && !sectionBreak.querySelector(".kt-pp2-parent-icon")) {
			const icon = document.createElement("span");
			icon.className = "kt-pp2-parent-icon sidebar-item-icon text-ink-gray-7";
			let iconHtml = "";
			try {
				if (frappe.utils && typeof frappe.utils.icon === "function") {
					iconHtml = frappe.utils.icon("kanban", "sm");
				}
			} catch (e) {
				/* ignore */
			}
			icon.innerHTML = iconHtml || '<span aria-hidden="true">▦</span>';
			sectionBreak.insertBefore(icon, sectionBreak.firstChild);
		}
		const anchors = parent.querySelectorAll(".nested-container .item-anchor");
		for (let i = 0; i < anchors.length; i += 1) {
			anchors[i].classList.add("kt-pp2-sidebar-child");
			const labelEl = anchors[i].querySelector(".sidebar-item-label");
			const label = String(labelEl ? labelEl.textContent || "" : "")
				.trim()
				.toLowerCase();
			const targetLabel = parentActive ? String(SURFACE_LABELS[slug || ""] || "").trim().toLowerCase() : "";
			const isActive = !!targetLabel && label === targetLabel;
			anchors[i].classList.toggle("kt-pp2-sidebar-child-active", isActive);
			const standardItem = anchors[i].querySelector(".standard-sidebar-item");
			if (standardItem) {
				standardItem.classList.toggle("active-sidebar", isActive);
			}
		}
		return true;
	}

	const FORBIDDEN_PLANNING_NAV_LABELS = {
		"approved demands": true,
		packages: true,
		"planning evidence": true,
		"planning inclusion detail": true,
		"release package detail": true,
		"readiness review": true,
		"review & approval": true,
		"package lines": true,
		"technical details": true,
		"audit trail": true,
		"planning release package": true,
		"planning release package view": true,
		"release to tender review": true,
		"advanced / technical details": true,
	};

	const FORBIDDEN_PLANNING_HREF_SUBSTRINGS = [
		"/procurement-planning/approved-demands",
		"/procurement-planning/packages",
		"/procurement-planning/evidence",
		"/procurement-planning/inclusions",
		"/procurement-planning/readiness",
		"/procurement-planning/review",
		"/procurement-planning/lines",
		"/procurement-planning/technical",
		"/procurement-planning/audit",
		"/procurement-planning/releases/",
	];

	function planningNestedNavAnchors() {
		const section = document.querySelector('.section-item[title="Procurement Planning"]');
		if (!section) return [];
		const nested = section.querySelector(".nested-container");
		const scope = nested || section;
		return Array.from(scope.querySelectorAll(".item-anchor"));
	}

	function isForbiddenPlanningNavLink(label, href) {
		const normalizedLabel = String(label || "")
			.trim()
			.toLowerCase();
		const normalizedHref = String(href || "").toLowerCase();
		if (FORBIDDEN_PLANNING_NAV_LABELS[normalizedLabel]) return true;
		for (let i = 0; i < FORBIDDEN_PLANNING_HREF_SUBSTRINGS.length; i += 1) {
			if (normalizedHref.indexOf(FORBIDDEN_PLANNING_HREF_SUBSTRINGS[i]) !== -1) return true;
		}
		return false;
	}

	function pruneForbiddenPlanningNavLinks() {
		const anchors = planningNestedNavAnchors();
		for (let i = 0; i < anchors.length; i += 1) {
			const anchor = anchors[i];
			const labelEl = anchor.querySelector(".sidebar-item-label");
			const label = String(labelEl ? labelEl.textContent || "" : "");
			const href = String(anchor.getAttribute("href") || "");
			if (!isForbiddenPlanningNavLink(label, href)) continue;
			const item = anchor.closest(".sidebar-item-container");
			if (item) {
				item.remove();
			} else {
				anchor.remove();
			}
		}
	}

	function normalizeChildLinkRoutes() {
		pruneForbiddenPlanningNavLinks();
		const visibleLabelByOriginal = {
			"planning home": __("Workbench"),
			plans: __("Procurement Plans"),
		};
		const removableLegacyLabels = {
			"approved demands": true,
			packages: true,
			"planning evidence": true,
		};
		const routeByLabel = {
			workbench: ROOT_PATH,
			"planning home": ROOT_PATH,
			"procurement plans": `${ROOT_PATH}/plans`,
			plans: `${ROOT_PATH}/plans`,
			"released to tender": `${ROOT_PATH}/releases`,
		};
		const testIdByLabel = {
			workbench: "pp3-nav-workbench",
			"planning home": "pp3-nav-workbench",
			"procurement plans": "pp3-nav-procurement-plans",
			plans: "pp3-nav-procurement-plans",
			"released to tender": "pp3-nav-released-to-tender",
		};
		const anchors = planningNestedNavAnchors();
		for (let i = 0; i < anchors.length; i += 1) {
			const anchor = anchors[i];
			const labelEl = anchor.querySelector(".sidebar-item-label");
			const rawLabel = String(labelEl ? labelEl.textContent || "" : "");
			const label = rawLabel.trim().toLowerCase();
			if (removableLegacyLabels[label]) {
				const item = anchor.closest(".sidebar-item-container");
				if (item) {
					item.remove();
				} else {
					anchor.remove();
				}
				continue;
			}
			const relabel = visibleLabelByOriginal[label];
			if (relabel && labelEl) {
				labelEl.textContent = relabel;
			}
			const targetPath = routeByLabel[label];
			if (!targetPath) continue;
			anchor.setAttribute("href", targetPath);
			const testId = testIdByLabel[label];
			if (testId) {
				anchor.setAttribute("data-testid", testId);
			}
		}
	}

	function queueSidebarRefresh() {
		if (sidebarRefreshQueued) return;
		sidebarRefreshQueued = true;
		window.requestAnimationFrame(function () {
			sidebarRefreshQueued = false;
			scheduleBoot();
		});
	}

	function elementTouchesSidebar(el) {
		if (!el || !el.matches) return false;
		if (el.matches(".layout-side-section, .layout-side-section *")) return true;
		return !!(el.querySelector && el.querySelector(".layout-side-section"));
	}

	function ensureSidebarObserver() {
		if (sidebarObserver || typeof MutationObserver === "undefined") return;
		const target = document.body || document.documentElement;
		if (!target) return;
		sidebarObserver = new MutationObserver(function (mutations) {
			for (let i = 0; i < mutations.length; i += 1) {
				const m = mutations[i];
				if (elementTouchesSidebar(m.target)) {
					queueSidebarRefresh();
					return;
				}
				if (m.addedNodes && m.addedNodes.length) {
					for (let j = 0; j < m.addedNodes.length; j += 1) {
						if (elementTouchesSidebar(m.addedNodes[j])) {
							queueSidebarRefresh();
							return;
						}
					}
				}
				if (m.removedNodes && m.removedNodes.length) {
					for (let k = 0; k < m.removedNodes.length; k += 1) {
						if (elementTouchesSidebar(m.removedNodes[k])) {
							queueSidebarRefresh();
							return;
						}
					}
				}
			}
		});
		sidebarObserver.observe(target, { childList: true, subtree: true });
	}

	function ensureSidebarSetupListener() {
		if (sidebarSetupListenerBound) return;
		sidebarSetupListenerBound = true;
		$(document).on("sidebar_setup.kt_pp2_hierarchy", function () {
			// Frappe emits sidebar_setup before the new sidebar DOM is fully painted.
			// Defer one frame so the enhancer can find and decorate the parent node.
			window.requestAnimationFrame(function () {
				scheduleBoot();
			});
		});
	}

	function closePlanningEvidenceDrawer() {
		const pp2DrawerApi =
			kentender_procurement &&
			kentender_procurement.PlanningEvidenceDrawer &&
			typeof kentender_procurement.PlanningEvidenceDrawer.close === "function"
				? kentender_procurement.PlanningEvidenceDrawer
				: null;
		if (pp2DrawerApi) {
			pp2DrawerApi.close();
		}
		const pp3DrawerApi =
			kentender_procurement &&
			kentender_procurement.PlanningWorkbenchEvidenceDrawer &&
			typeof kentender_procurement.PlanningWorkbenchEvidenceDrawer.close === "function"
				? kentender_procurement.PlanningWorkbenchEvidenceDrawer
				: null;
		if (pp3DrawerApi) {
			pp3DrawerApi.close();
		}
	}

	function openWorkbenchEvidenceDrawer(summary) {
		const drawerApi =
			kentender_procurement &&
			kentender_procurement.PlanningWorkbenchEvidenceDrawer &&
			typeof kentender_procurement.PlanningWorkbenchEvidenceDrawer.open === "function"
				? kentender_procurement.PlanningWorkbenchEvidenceDrawer
				: null;
		if (!drawerApi) return;
		const s = summary || {};
		const title = String(s.title || "").trim();
		const packageCode = String(s.packageCode || s.package_code || "").trim();
		const underlyingObjectType = String(s.underlyingObjectType || s.underlying_object_type || "").trim();
		const underlyingObjectCode = String(s.underlyingObjectCode || s.underlying_object_code || "").trim();
		drawerApi.open({
			title: title,
			package_code: packageCode,
			underlying_object_type: underlyingObjectType,
			underlying_object_code: underlyingObjectCode,
		});
	}

	function removePp2PlanningShellIfWrongRoute() {
		closePlanningEvidenceDrawer();
		document.querySelectorAll('[data-testid="pp2-primary-workspace-shell"]').forEach(function (el) {
			el.remove();
		});
		document.querySelectorAll("#kt-pp-root, .kt-pp-injected-shell").forEach(function (el) {
			el.remove();
		});
		document.body.classList.remove("kt-pp2-shell");
	}

	function mount() {
		closePlanningEvidenceDrawer();
		const planningRoute = isPlanningWorkspaceRoute();
		normalizeChildLinkRoutes();
		if (!planningRoute) {
			removePp2PlanningShellIfWrongRoute();
			return enhanceSidebarVisualHierarchy("", false);
		}

		const resolution = resolvePlanningRoute(window.location.pathname);
		if (resolution.action === "redirect" && applyPlanningRouteRedirect(resolution.redirectUrl)) {
			window.requestAnimationFrame(function () {
				scheduleBoot();
			});
			return true;
		}

		const slug =
			resolution.action === "canonical"
				? resolution.slug != null
					? resolution.slug
					: readSurfaceSlug()
				: readSurfaceSlug();
		const hierarchyReady = enhanceSidebarVisualHierarchy(slug, planningRoute);
		const root = ensureWorkspaceRoot();
		if (!root) return false;

		if (resolution.action === "not_found") {
			const shell = ensurePrimaryWorkspaceShell(root, "");
			if (!shell) return false;
			root.setAttribute("data-testid", surfaceForSlug("").testId);
			renderRouteNotFound(root);
			document.body.classList.add("kt-pp2-shell");
			syncSidebarActive("");
			return hierarchyReady;
		}

		if (resolution.action === "package_detail") {
			const packageCode = String(resolution.packageCode || "").trim();
			const detailSlug = "package-detail";
			const shell = ensurePrimaryWorkspaceShell(root, detailSlug);
			if (!shell) return false;
			const mainHost = shell.querySelector('[data-testid="pp2-primary-main-host"]');
			root.removeAttribute("data-testid");
			const summaryHost = shell.querySelector('[data-testid="pp2-primary-summary-host"]');
			if (summaryHost) {
				summaryHost.innerHTML = "";
			}
			if (mainHost) {
				mountPackageDetailSurface(mainHost, packageCode, root);
			}
			document.body.classList.add("kt-pp2-shell");
			syncSidebarActive("");
			return hierarchyReady;
		}

		const searchParams = new URLSearchParams(window.location.search || "");
		const hasPackageCode = searchParams.has("package_code");
		const hasApprovedDemandQuery = searchParams.has("queue") || searchParams.has("item");
		syncSurfaceUrl(slug, {
			preserveSearch: slug === "" && (hasPackageCode || hasApprovedDemandQuery),
		});
		const shell = ensurePrimaryWorkspaceShell(root, slug);
		if (!shell) return false;
		const mainHost = shell.querySelector('[data-testid="pp2-primary-main-host"]');
		const markerId = surfaceForSlug(slug).testId;
		if (isPlanningHomeSlug(slug) || isProcurementPlansSlug(slug)) {
			root.removeAttribute("data-testid");
		} else {
			root.setAttribute("data-testid", markerId);
		}
		if (isPlanningHomeSlug(slug)) {
			if (mainHost) {
				clearWorkbenchHosts(mainHost);
				const children = Array.from(mainHost.children);
				for (let i = 0; i < children.length; i += 1) {
					if (children[i] !== root) {
						mainHost.removeChild(children[i]);
					}
				}
				root.innerHTML =
					'<article class="pp3-planning-workbench-surface" data-testid="' +
					esc(markerId) +
					'"></article>';
				mountPlanningWorkUnavailable(mainHost);
				shell.setAttribute("data-pp3-planning-blocked", "1");
				fetchActivePlanPayload().then(function (activePlanPayload) {
					if (!shell.isConnected || !mainHost.isConnected) return;
					mountWorkbenchRootWork(mainHost, shell, slug, activePlanPayload || {});
				});
			}
		} else if (isProcurementPlansSlug(slug)) {
			if (mainHost) {
				const children = Array.from(mainHost.children);
				for (let i = 0; i < children.length; i += 1) {
					if (children[i] !== root) {
						mainHost.removeChild(children[i]);
					}
				}
				mountProcurementPlansSurface(mainHost, slug, root);
			}
		} else if (mainHost) {
			const queueHost = mainHost.querySelector('[data-testid="pp2-primary-queue-host"]');
			const filtersHost = mainHost.querySelector('[data-testid="pp2-primary-filters-host"]');
			const workListHost = mainHost.querySelector('[data-testid="pp2-primary-work-list-host"]');
			const children = Array.from(mainHost.children);
			for (let i = 0; i < children.length; i += 1) {
				if (
					children[i] !== root &&
					children[i] !== queueHost &&
					children[i] !== filtersHost &&
					children[i] !== workListHost
				) {
					mainHost.removeChild(children[i]);
				}
			}
			mountPlanningQueueTabs(mainHost, slug);
			const queueApi = isPlanningHomeSlug(slug)
				? kentender_procurement &&
					kentender_procurement.PlanningWorkbenchQueueTabs &&
					typeof kentender_procurement.PlanningWorkbenchQueueTabs.readActiveFromUrl === "function"
					? kentender_procurement.PlanningWorkbenchQueueTabs
					: null
				: kentender_procurement &&
					kentender_procurement.PlanningQueueTabs &&
					typeof kentender_procurement.PlanningQueueTabs.readActiveFromUrl === "function"
					? kentender_procurement.PlanningQueueTabs
					: null;
			if (queueApi) {
				try {
					const raw = new URLSearchParams(window.location.search).get("queue");
					if (raw) {
						const activeQueue = queueApi.readActiveFromUrl(slug);
						if (raw !== activeQueue) {
							queueApi.setQueueUrl(activeQueue);
						}
					}
				} catch (e) {
					/* ignore */
				}
			}
			mountPlanningAdvancedFilters(mainHost, slug);
			mountPlanningWorkList(mainHost, slug, shell);
			if (slug === "approved-demands") {
				bindApprovedDemandsQueueRefresh(mainHost, shell);
				renderApprovedDemandsQueue(mainHost, shell);
			}
			const workListApi =
				kentender_procurement &&
				kentender_procurement.PlanningWorkList &&
				typeof kentender_procurement.PlanningWorkList.readSelectedFromUrl === "function"
					? kentender_procurement.PlanningWorkList
					: null;
			if (workListApi) {
				try {
					const rawItem = new URLSearchParams(window.location.search).get("item");
					if (rawItem && !workListApi.readSelectedFromUrl([])) {
						workListApi.setSelectedUrl("");
					}
				} catch (e) {
					/* ignore */
				}
			}
			renderSurfaceEmptyState(root, slug);
		}
		document.body.classList.add("kt-pp2-shell");
		syncSidebarActive(slug);
		return hierarchyReady;
	}

	function scheduleBoot() {
		patchSidebarSingleSegmentFastpath();
		patchSidebarLookupBySlug();
		ensureSidebarObserver();
		ensureSidebarSetupListener();
		bootRunToken += 1;
		const token = bootRunToken;
		if (bootRetryTimer) {
			clearTimeout(bootRetryTimer);
			bootRetryTimer = null;
		}
		if (mount()) return;
		let retries = 0;
		const retry = function () {
			if (token !== bootRunToken) return;
			retries += 1;
			if (mount() || retries >= 10) {
				bootRetryTimer = null;
				return;
			}
			bootRetryTimer = window.setTimeout(retry, 70);
		};
		bootRetryTimer = window.setTimeout(retry, 70);
	}

	$(document).on("page-change", scheduleBoot);
	$(document).on("app_ready", scheduleBoot);
	if (frappe.router && frappe.router.on) {
		frappe.router.on("change", scheduleBoot);
	}
	patchSidebarSingleSegmentFastpath();
	patchSidebarLookupBySlug();
	scheduleBoot();
})();
