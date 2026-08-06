/** PP2 P5-001 — Procurement Planning nested surfaces inside main Procurement shell. */
(function () {
	const WORKSPACE_NAME = "Procurement Planning";
	const ROOT_PATH = "/desk/procurement-planning";
	const RIGHT_PANEL_STATE_KEY = "kt-pp2-right-panel-collapsed";
	// Single-use route handoff read by `create_package_wizard_page.js` on
	// `on_page_show` — must match its HANDOFF_KEY constant verbatim.
	const PP_WIZARD_HANDOFF_KEY = "kt_pw_wizard_handoff_v1";
	let sidebarObserver = null;
	let sidebarRefreshQueued = false;
	let bootRetryTimer = null;
	let bootRunToken = 0;
	let sidebarFastpathPatched = false;
	let sidebarLookupPatched = false;
	let sidebarSetupListenerBound = false;

	const SURFACE_LABELS = {
		"": __("Planning Workbench"),
		plans: __("Planning Workbench"),
		releases: __("Planning Workbench"),
	};

	const SURFACES = {
		"": {
			testId: "pp4-workbench",
			title: __("Planning Workbench"),
			subtitle: __("Planning Workbench"),
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
	const PP_LANDING_SHELL_API =
		"kentender_procurement.procurement_planning.api.landing.get_pp_landing_shell_data";
	const WORKBENCH_QUEUE_COUNTS_API =
		"kentender_procurement.procurement_planning.api.workbench_queue_counts.get_pp_workbench_queue_counts";
	const WORKBENCH_ITEM_VIEW_MODEL_API =
		"kentender_procurement.procurement_planning.api.workbench_item.get_pp_workbench_item_view_model";
	const INCLUDE_DEMAND_IN_PLAN_API =
		"kentender_procurement.procurement_planning.api.approved_demands.include_pp_demand_in_procurement_plan";
	const CREATE_PACKAGE_FROM_INCLUSION_API =
		"kentender_procurement.procurement_planning.api.planning_inclusion.create_pp_package_from_planning_inclusion";
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
	const pp4MountSignatureByRoot = new WeakMap();
	const WORKBENCH_STATE_QUERY_KEYS = [
		"queue",
		"item",
		"plan",
		"search",
		"department",
		"category",
		"value_range",
		"created_from",
		"created_to",
		"sort",
		"page",
		"page_size",
	];
	const WORKBENCH_PAGE_SIZE_OPTIONS = [10, 25, 50];
	const WORKBENCH_DEFAULT_PAGE_SIZE = 10;
	const WORKBENCH_ALLOWED_QUEUES = {
		needs_planning: true,
		draft_packages: true,
		needs_review: true,
		ready_to_release: true,
		blocked: true,
		recently_released: true,
		"all-packages": true,
	};
	const WORKBENCH_QUEUE_ALIASES = {
		"needs-planning": "needs_planning",
		"draft-packages": "draft_packages",
		"needs-review": "needs_review",
		"ready-to-release": "ready_to_release",
		"released-recently": "recently_released",
	};
	const WORKBENCH_SORT_OPTIONS = {
		newest: true,
		oldest: true,
		value_high_low: true,
		value_low_high: true,
		title_asc: true,
		title_desc: true,
	};

	function esc(s) {
		return frappe.utils.escape_html(String(s == null ? "" : s));
	}

	function normalizeWorkbenchQueueValue(rawValue) {
		const raw = String(rawValue || "").trim();
		if (!raw) return "needs_planning";
		const mapped = WORKBENCH_QUEUE_ALIASES[raw] || raw;
		return WORKBENCH_ALLOWED_QUEUES[mapped] ? mapped : "needs_planning";
	}

	function normalizePositiveIntValue(rawValue, fallback) {
		const n = Number(rawValue);
		if (!Number.isFinite(n) || n < 1) return String(fallback || 1);
		return String(Math.floor(n));
	}

	function normalizeWorkbenchPageSizeValue(rawValue) {
		const n = Number(rawValue);
		return WORKBENCH_PAGE_SIZE_OPTIONS.indexOf(n) !== -1 ? n : WORKBENCH_DEFAULT_PAGE_SIZE;
	}

	function readWorkbenchStateFromUrl(urlLike) {
		const url = urlLike ? new URL(urlLike, window.location.origin) : new URL(window.location.href);
		const search = url.searchParams;
		const state = {
			queue: normalizeWorkbenchQueueValue(search.get("queue")),
			item: String(search.get("item") || "").trim(),
			plan: String(search.get("plan") || "").trim(),
			search: String(search.get("search") || "").trim(),
			department: String(search.get("department") || "").trim(),
			category: String(search.get("category") || "").trim(),
			value_range: String(search.get("value_range") || "").trim(),
			created_from: String(search.get("created_from") || "").trim(),
			created_to: String(search.get("created_to") || "").trim(),
			sort: String(search.get("sort") || "").trim(),
			page: normalizePositiveIntValue(search.get("page"), 1),
			page_size: normalizeWorkbenchPageSizeValue(search.get("page_size")),
		};
		if (!WORKBENCH_SORT_OPTIONS[state.sort]) {
			state.sort = "newest";
		}
		return state;
	}

	function hasWorkbenchStateQuery(searchParams) {
		const params = searchParams || new URLSearchParams(window.location.search || "");
		for (let i = 0; i < WORKBENCH_STATE_QUERY_KEYS.length; i += 1) {
			if (params.has(WORKBENCH_STATE_QUERY_KEYS[i])) return true;
		}
		return false;
	}

	function writeWorkbenchStateToUrl(partialState, options) {
		const opts = options || {};
		const url = new URL(window.location.href);
		const current = readWorkbenchStateFromUrl(url.toString());
		const next = Object.assign({}, current, partialState || {});
		next.queue = normalizeWorkbenchQueueValue(next.queue);
		next.page = normalizePositiveIntValue(next.page, 1);
		next.page_size = normalizeWorkbenchPageSizeValue(next.page_size);
		next.sort = WORKBENCH_SORT_OPTIONS[String(next.sort || "").trim()] ? String(next.sort || "").trim() : "newest";
		WORKBENCH_STATE_QUERY_KEYS.forEach(function (key) {
			const value = String(next[key] || "").trim();
			if (!value) {
				url.searchParams.delete(key);
				return;
			}
			url.searchParams.set(key, value);
		});
		const target = url.pathname + url.search + url.hash;
		if (opts.replace !== false) {
			window.history.replaceState({}, "", target);
		} else {
			window.history.pushState({}, "", target);
		}
		return next;
	}

	function canonicalizeWorkbenchStateQuery() {
		if (!isPlanningWorkspaceRoute()) return;
		if (readSurfaceSlug() !== "") return;
		const params = new URLSearchParams(window.location.search || "");
		if (!hasWorkbenchStateQuery(params)) return;
		const currentUrl = window.location.pathname + window.location.search + window.location.hash;
		writeWorkbenchStateToUrl({}, { replace: true });
		const nextUrl = window.location.pathname + window.location.search + window.location.hash;
		return nextUrl !== currentUrl;
	}

	function renderPlanningWorkbenchV4(root) {
		if (!root) return;
		root.setAttribute("data-testid", "pp4-workbench-root");
		root.className = "kt-pp-injected-shell pp4-workbench-root";
		root.innerHTML =
			'<section class="pp4-workbench" data-testid="pp4-workbench">' +
			'<iframe class="pp4-workbench-design-iframe" data-testid="pp4-workbench-design-iframe" src="/assets/kentender_procurement/workbench_design/needs_planning_default.html?v=wb-typo-v1" title="Planning Workbench Needs Planning Default"></iframe>' +
			"</section>";
	}

	function withWorkbenchIframeDocument(root, callback) {
		if (!root || typeof callback !== "function") return;
		const iframe = root.querySelector('[data-testid="pp4-workbench-design-iframe"]');
		if (!iframe) return;
		let invoked = false;
		const tryInvoke = function () {
			if (invoked) return true;
			let doc = null;
			try {
				doc = iframe.contentDocument || (iframe.contentWindow && iframe.contentWindow.document);
			} catch (e) {
				doc = null;
			}
			// A freshly-created iframe's transient about:blank document also reports
			// readyState "complete" with an empty <body>, which races the real
			// navigation when this is invoked synchronously (before the browser has
			// started loading `src`). Require an actual rendered child to avoid
			// mistaking that placeholder for the loaded design document.
			if (!doc || doc.readyState !== "complete" || !doc.body || !doc.body.firstElementChild) return false;
			invoked = true;
			callback(doc);
			return true;
		};
		if (tryInvoke()) return;
		iframe.addEventListener("load", tryInvoke, { once: true });
	}

	function applyWorkbenchActivePlanCard(doc, payload) {
		if (!doc) return;
		const data = payload || {};
		const card = doc.querySelector(".bg-primary-container.border-primary-container");
		if (!card) return;
		const nonIconSpans = Array.prototype.filter.call(card.querySelectorAll("span"), function (el) {
			return !el.classList.contains("material-symbols-outlined");
		});
		if (nonIconSpans[0]) {
			nonIconSpans[0].textContent = data.status_label || "Active";
		}
		const titleEl = card.querySelector(".font-headline-lg");
		if (titleEl) {
			titleEl.textContent = data.plan_title || "";
		}
		const metaEl = card.querySelector(".mt-4.text-white.font-body-sm");
		if (metaEl) {
			const iconEl = metaEl.querySelector(".material-symbols-outlined");
			const fy = String(data.fiscal_year || "").trim();
			metaEl.textContent = "";
			if (iconEl) metaEl.appendChild(iconEl);
			metaEl.appendChild(doc.createTextNode(fy ? __("FY {0}", [fy]) : ""));
		}
	}

	function redirectWorkbenchToPlanningHubForNoActivePlan(payload) {
		const data = payload || {};
		frappe.show_alert({
			indicator: "orange",
			message:
				String(data.message || "").trim() ||
				__("No active procurement plan exists. Create or activate a plan to continue."),
		});
		window.location.href = "/desk/planning-hub";
	}

	// "Back to Hub" ships in the design as a plain `<div>` (no href/route) —
	// wire it to the same destination the no-active-plan gate already
	// redirects to, matching the existing `window.location.href` pattern
	// used by `redirectWorkbenchToPlanningHubForNoActivePlan`.
	function initializeWorkbenchBackToHubLink(root) {
		if (!root) return;
		withWorkbenchIframeDocument(root, function (doc) {
			const link = doc.querySelector(".text-secondary.cursor-pointer");
			if (!link || link.getAttribute("data-pp4-back-to-hub-bound") === "1") return;
			link.setAttribute("data-pp4-back-to-hub-bound", "1");
			link.addEventListener("click", function (event) {
				event.preventDefault();
				window.location.href = "/desk/planning-hub";
			});
		});
	}

	// Post-launch fix — the header's own "+ Create New Package" toolbar
	// button ships in the design with no id/data-testid/route (it was
	// missed by the PW11 entry-point-replacement sweep, which only
	// covered the selection-toolbar action and the "In Creation"
	// placeholder-row action). It must open the same canonical Package
	// Creation Wizard as every other Create Package entry point, just
	// with no demands pre-selected (Step 1 shows the full eligible list
	// for manual selection). Matches the "Back to Hub" pattern above:
	// find by content, bind once via a runtime-only guard attribute.
	function initializeWorkbenchCreateNewPackageButton(root) {
		if (!root) return;
		withWorkbenchIframeDocument(root, function (doc) {
			const btn = Array.prototype.filter
				.call(doc.querySelectorAll("button"), function (el) {
					return el.textContent.indexOf("Create New Package") !== -1;
				})[0];
			if (!btn || btn.getAttribute("data-pp4-create-package-bound") === "1") return;
			btn.setAttribute("data-pp4-create-package-bound", "1");
			btn.addEventListener("click", function (event) {
				event.preventDefault();
				const planCode = workbenchActivePlanCodeByRoot.get(root);
				if (!planCode) {
					frappe.show_alert({ indicator: "red", message: __("No active procurement plan found.") });
					return;
				}
				openPlanningPackageWizard(root, doc, { plan_code: planCode });
			});
		});
	}

	// W10 — Filter drawer + Sort menu, ported in spirit from
	// `demand_hub_page.js`'s DIA filter drawer (draft/applied two-layer
	// state, `Apply`/`Clear All`, badge count on the Filter button) but
	// wired through this router's own URL-state model instead of an
	// internal `_state` object, since every other workbench control
	// (page/page_size/queue) already round-trips through the URL.
	const WORKBENCH_FILTER_META_API =
		"kentender_procurement.procurement_planning.api.workbench_item.get_pp_workbench_filter_meta";
	const WORKBENCH_SORT_LABELS = {
		newest: __("Newest first"),
		oldest: __("Oldest first"),
		value_high_low: __("Value: High to Low"),
		value_low_high: __("Value: Low to High"),
		title_asc: __("Title: A to Z"),
		title_desc: __("Title: Z to A"),
	};
	// The meta API's `sort_options` use `value_desc`/`value_asc`; the
	// router's own URL-state vocabulary (and backend `_apply_sort`/
	// `_apply_demand_sort`) accept both spellings, but state normalization
	// only recognizes the `value_high_low`/`value_low_high` forms — map
	// the meta response onto those so the Sort menu and URL state agree.
	const WORKBENCH_SORT_VALUE_ALIASES = {
		value_desc: "value_high_low",
		value_asc: "value_low_high",
	};
	let workbenchFilterMetaCache = null;

	function fetchWorkbenchFilterMeta(callback) {
		if (workbenchFilterMetaCache) {
			callback(workbenchFilterMetaCache);
			return;
		}
		frappe.call({
			method: WORKBENCH_FILTER_META_API,
			freeze: false,
			callback: function (response) {
				const payload = (response && response.message) || {};
				if (payload.ok) workbenchFilterMetaCache = payload;
				callback(payload.ok ? payload : { departments: [], categories: [], value_ranges: [], sort_options: [] });
			},
		});
	}

	function workbenchFilterDrawerEls(doc) {
		return {
			backdrop: doc.querySelector('[data-testid="pp4-workbench-filter-backdrop"]'),
			drawer: doc.querySelector('[data-testid="pp4-workbench-filter-drawer"]'),
			closeBtn: doc.querySelector('[data-testid="pp4-workbench-filter-close"]'),
			filterBtn: doc.querySelector('[data-testid="pp4-workbench-filter-btn"]'),
			filterBadge: doc.querySelector('[data-testid="pp4-workbench-filter-badge"]'),
			searchEl: doc.querySelector('[data-testid="pp4-workbench-filter-search"]'),
			departmentEl: doc.querySelector('[data-testid="pp4-workbench-filter-department"]'),
			categoryEl: doc.querySelector('[data-testid="pp4-workbench-filter-category"]'),
			valueRangeEl: doc.querySelector('[data-testid="pp4-workbench-filter-value-range"]'),
			createdFromEl: doc.querySelector('[data-testid="pp4-workbench-filter-created-from"]'),
			createdToEl: doc.querySelector('[data-testid="pp4-workbench-filter-created-to"]'),
			clearBtn: doc.querySelector('[data-testid="pp4-workbench-filter-clear"]'),
			applyBtn: doc.querySelector('[data-testid="pp4-workbench-filter-apply"]'),
			sortBtn: doc.querySelector('[data-testid="pp4-workbench-sort-btn"]'),
			sortMenu: doc.querySelector('[data-testid="pp4-workbench-sort-menu"]'),
		};
	}

	function refetchActiveWorkbenchQueueList(root, doc) {
		const uiQueue = readWorkbenchStateFromUrl().queue;
		if (uiQueue === "needs_planning") {
			fetchAndRenderWorkbenchNeedsPlanningList(root, doc);
			return;
		}
		fetchAndRenderWorkbenchPackageQueueList(root, doc, uiQueue);
	}

	function workbenchActiveFilterCount(state) {
		return [state.search, state.department, state.category, state.value_range, state.created_from, state.created_to]
			.filter(function (v) {
				return String(v || "").trim();
			}).length;
	}

	function syncWorkbenchFilterBadge(doc) {
		const els = workbenchFilterDrawerEls(doc);
		if (!els.filterBadge || !els.filterBtn) return;
		const count = workbenchActiveFilterCount(readWorkbenchStateFromUrl());
		if (count > 0) {
			els.filterBadge.textContent = String(count);
			els.filterBadge.classList.remove("hidden");
			els.filterBadge.classList.add("flex");
			els.filterBtn.classList.add("border-primary", "text-primary");
		} else {
			els.filterBadge.classList.add("hidden");
			els.filterBadge.classList.remove("flex");
			els.filterBtn.classList.remove("border-primary", "text-primary");
		}
	}

	function syncWorkbenchFilterDrawerInputsFromState(doc) {
		const els = workbenchFilterDrawerEls(doc);
		const state = readWorkbenchStateFromUrl();
		if (els.searchEl && els.searchEl !== doc.activeElement) els.searchEl.value = state.search || "";
		if (els.departmentEl) els.departmentEl.value = state.department || "";
		if (els.categoryEl) els.categoryEl.value = state.category || "";
		if (els.valueRangeEl) els.valueRangeEl.value = state.value_range || "";
		if (els.createdFromEl) els.createdFromEl.value = state.created_from || "";
		if (els.createdToEl) els.createdToEl.value = state.created_to || "";
	}

	function populateWorkbenchFilterDrawerOptions(doc, meta) {
		const els = workbenchFilterDrawerEls(doc);
		function opts(items, allLabel) {
			return (
				'<option value="">' + esc(allLabel) + "</option>" +
				(items || [])
					.map(function (item) {
						return '<option value="' + esc(item.value) + '">' + esc(item.label || item.value) + "</option>";
					})
					.join("")
			);
		}
		if (els.departmentEl) els.departmentEl.innerHTML = opts(meta.departments, __("All Departments"));
		if (els.categoryEl) els.categoryEl.innerHTML = opts(meta.categories, __("All Categories"));
		if (els.valueRangeEl) els.valueRangeEl.innerHTML = opts(meta.value_ranges, __("All Values"));
		syncWorkbenchFilterDrawerInputsFromState(doc);
	}

	// Same Tailwind-vs-`[hidden]` specificity pitfall as the pagination page
	// slots (`flex`/`fixed` utilities on the drawer/backdrop themselves have
	// equal specificity to `[hidden]`, so the attribute alone is silently
	// overridden) — always pair the attribute with an inline `display`
	// override, which wins regardless of stylesheet ordering.
	function setWorkbenchHiddenState(el, isHidden) {
		if (!el) return;
		if (isHidden) {
			el.setAttribute("hidden", "");
			el.style.display = "none";
		} else {
			el.removeAttribute("hidden");
			el.style.display = "";
		}
	}

	function openWorkbenchFilterDrawer(doc) {
		const els = workbenchFilterDrawerEls(doc);
		if (!els.backdrop || !els.drawer) return;
		syncWorkbenchFilterDrawerInputsFromState(doc);
		setWorkbenchHiddenState(els.backdrop, false);
		setWorkbenchHiddenState(els.drawer, false);
		fetchWorkbenchFilterMeta(function (meta) {
			populateWorkbenchFilterDrawerOptions(doc, meta);
		});
	}

	function closeWorkbenchFilterDrawer(doc) {
		const els = workbenchFilterDrawerEls(doc);
		if (!els.backdrop || !els.drawer) return;
		setWorkbenchHiddenState(els.backdrop, true);
		setWorkbenchHiddenState(els.drawer, true);
	}

	function initializeWorkbenchFilterDrawer(root) {
		if (!root) return;
		withWorkbenchIframeDocument(root, function (doc) {
			const els = workbenchFilterDrawerEls(doc);
			if (!els.filterBtn || els.filterBtn.getAttribute("data-pp4-filter-bound") === "1") {
				syncWorkbenchFilterBadge(doc);
				return;
			}
			els.filterBtn.setAttribute("data-pp4-filter-bound", "1");
			els.filterBtn.addEventListener("click", function () {
				openWorkbenchFilterDrawer(doc);
			});
			if (els.closeBtn) els.closeBtn.addEventListener("click", function () { closeWorkbenchFilterDrawer(doc); });
			if (els.backdrop) els.backdrop.addEventListener("click", function () { closeWorkbenchFilterDrawer(doc); });
			if (els.applyBtn) {
				els.applyBtn.addEventListener("click", function () {
					writeWorkbenchStateToUrl({
						search: els.searchEl ? els.searchEl.value : "",
						department: els.departmentEl ? els.departmentEl.value : "",
						category: els.categoryEl ? els.categoryEl.value : "",
						value_range: els.valueRangeEl ? els.valueRangeEl.value : "",
						created_from: els.createdFromEl ? els.createdFromEl.value : "",
						created_to: els.createdToEl ? els.createdToEl.value : "",
						page: 1,
					});
					closeWorkbenchFilterDrawer(doc);
					syncWorkbenchFilterBadge(doc);
					refetchActiveWorkbenchQueueList(root, doc);
				});
			}
			if (els.clearBtn) {
				els.clearBtn.addEventListener("click", function () {
					writeWorkbenchStateToUrl({
						search: "",
						department: "",
						category: "",
						value_range: "",
						created_from: "",
						created_to: "",
						page: 1,
					});
					syncWorkbenchFilterDrawerInputsFromState(doc);
					closeWorkbenchFilterDrawer(doc);
					syncWorkbenchFilterBadge(doc);
					refetchActiveWorkbenchQueueList(root, doc);
				});
			}
			syncWorkbenchFilterBadge(doc);

			// Sort — a small popover menu (design ships "Sort" as an inert
			// button with no open-menu mockup, so this popover is fabricated
			// the same way the rows-per-page menu is), sourced from the same
			// meta endpoint's `sort_options`.
			if (els.sortBtn && els.sortMenu) {
				els.sortBtn.addEventListener("click", function (event) {
					event.stopPropagation();
					const isHidden = els.sortMenu.hasAttribute("hidden");
					setWorkbenchHiddenState(els.sortMenu, true);
					if (!isHidden) return;
					fetchWorkbenchFilterMeta(function (meta) {
						const state = readWorkbenchStateFromUrl();
						const options = (meta.sort_options && meta.sort_options.length)
							? meta.sort_options
							: Object.keys(WORKBENCH_SORT_LABELS).map(function (value) {
								return { value: value, label: WORKBENCH_SORT_LABELS[value] };
							});
						els.sortMenu.innerHTML = options
							.map(function (opt) {
								const normalized = WORKBENCH_SORT_VALUE_ALIASES[opt.value] || opt.value;
								const active = normalized === state.sort;
								return (
									'<button type="button" data-pp4-sort-value="' + esc(normalized) + '" class="w-full text-left px-4 py-2 font-body-sm ' +
									(active ? "text-primary font-bold bg-surface-container-low" : "text-on-surface-variant hover:bg-surface-container-low") +
									' transition-colors">' + esc(opt.label || normalized) + "</button>"
								);
							})
							.join("");
						setWorkbenchHiddenState(els.sortMenu, false);
					});
				});
				els.sortMenu.addEventListener("click", function (event) {
					const btn = event.target.closest("[data-pp4-sort-value]");
					if (!btn) return;
					setWorkbenchHiddenState(els.sortMenu, true);
					writeWorkbenchStateToUrl({ sort: btn.getAttribute("data-pp4-sort-value"), page: 1 });
					refetchActiveWorkbenchQueueList(root, doc);
				});
				if (!doc.__pp4SortMenuOutsideClickBound) {
					doc.__pp4SortMenuOutsideClickBound = true;
					doc.addEventListener("click", function () {
						setWorkbenchHiddenState(els.sortMenu, true);
					});
				}
			}
		});
	}

	function fetchAndApplyWorkbenchActivePlanContext(root) {
		if (!root) return;
		frappe.call({
			method: ACTIVE_PLAN_API,
			freeze: false,
			args: {},
			callback: function (response) {
				const payload = (response && response.message) || {};
				if (!payload.has_active_plan) {
					redirectWorkbenchToPlanningHubForNoActivePlan(payload);
					return;
				}
				workbenchActivePlanCodeByRoot.set(root, String(payload.plan_code || "").trim());
				withWorkbenchIframeDocument(root, function (doc) {
					applyWorkbenchActivePlanCard(doc, payload);
				});
			},
		});
	}

	// W3 — Queue Tabs + Counts. Order matches the design's tab bar left-to-right.
	// The "6. Blocked" design shows a count badge ("Blocked (12)") on its own
	// tab, so that one is real per-pixel-fidelity (backed by the existing
	// `get_pp_workbench_queue_counts` data); Released stays plain-text (bare
	// "Released" across every screen, including its own).
	const WORKBENCH_QUEUE_TAB_ORDER = [
		{ uiQueue: "needs_planning", label: "Needs Planning", showCount: true },
		{ uiQueue: "draft_packages", label: "In Creation", showCount: true },
		{ uiQueue: "needs_review", label: "Awaiting Review", showCount: true },
		{ uiQueue: "ready_to_release", label: "Ready for Release", showCount: true },
		{ uiQueue: "blocked", label: "Blocked", showCount: true },
		{ uiQueue: "recently_released", label: "Released", showCount: false },
	];
	const WORKBENCH_QUEUE_TAB_ACTIVE_CLASSES = [
		"text-primary",
		"font-bold",
		"border-b-2",
		"border-primary",
		"bg-surface-container-lowest",
	];
	const WORKBENCH_QUEUE_TAB_INACTIVE_CLASSES = ["text-on-surface-variant", "hover:bg-surface-container-high", "transition-colors"];

	function workbenchQueueTabButtons(doc) {
		if (!doc) return [];
		const bar = doc.querySelector(".scrollbar-hide");
		if (!bar) return [];
		return Array.prototype.slice.call(bar.querySelectorAll(":scope > button"));
	}

	function setWorkbenchQueueTabActiveState(btn, isActive) {
		if (!btn) return;
		const toRemove = isActive ? WORKBENCH_QUEUE_TAB_INACTIVE_CLASSES : WORKBENCH_QUEUE_TAB_ACTIVE_CLASSES;
		const toAdd = isActive ? WORKBENCH_QUEUE_TAB_ACTIVE_CLASSES : WORKBENCH_QUEUE_TAB_INACTIVE_CLASSES;
		toRemove.forEach(function (cls) {
			btn.classList.remove(cls);
		});
		toAdd.forEach(function (cls) {
			btn.classList.add(cls);
		});
	}

	function applyWorkbenchQueueActiveTab(doc, activeUiQueue) {
		const buttons = workbenchQueueTabButtons(doc);
		if (!buttons.length) return;
		WORKBENCH_QUEUE_TAB_ORDER.forEach(function (tab, index) {
			setWorkbenchQueueTabActiveState(buttons[index], tab.uiQueue === activeUiQueue);
		});
	}

	function applyWorkbenchQueueTabCounts(doc, counts) {
		const buttons = workbenchQueueTabButtons(doc);
		if (!buttons.length) return;
		const data = counts || {};
		WORKBENCH_QUEUE_TAB_ORDER.forEach(function (tab, index) {
			if (!tab.showCount) return;
			const btn = buttons[index];
			if (!btn) return;
			const raw = Number(data[tab.uiQueue] || 0);
			const safeCount = Number.isFinite(raw) && raw > 0 ? raw : 0;
			btn.textContent = tab.label + " (" + String(safeCount).padStart(2, "0") + ")";
		});
	}

	function bindWorkbenchQueueTabs(root, doc) {
		const buttons = workbenchQueueTabButtons(doc);
		if (!buttons.length) return;
		buttons.forEach(function (btn, index) {
			const tab = WORKBENCH_QUEUE_TAB_ORDER[index];
			if (!tab || !btn || btn.getAttribute("data-pp4-wq-bound") === "1") return;
			btn.setAttribute("data-pp4-wq-bound", "1");
			btn.addEventListener("click", function () {
				const current = readWorkbenchStateFromUrl();
				if (current.queue === tab.uiQueue) return;
			writeWorkbenchStateToUrl({ queue: tab.uiQueue, page: 1 });
			applyWorkbenchQueueActiveTab(doc, tab.uiQueue);
			applyWorkbenchQueueTableVisibility(doc, tab.uiQueue);
			applyWorkbenchInsightsVariant(doc, tab.uiQueue);
			if (Object.prototype.hasOwnProperty.call(WORKBENCH_PACKAGE_UI_QUEUE_TO_API_QUEUE, tab.uiQueue)) {
				fetchAndRenderWorkbenchPackageQueueList(root, doc, tab.uiQueue);
			}
		});
	});
}

	function fetchAndApplyWorkbenchQueueCounts(root) {
		if (!root) return;
		frappe.call({
			method: WORKBENCH_QUEUE_COUNTS_API,
			freeze: false,
			args: {},
			callback: function (response) {
				const payload = (response && response.message) || {};
				if (!payload || payload.ok === false) return;
				withWorkbenchIframeDocument(root, function (doc) {
					applyWorkbenchQueueTabCounts(doc, payload.counts || {});
				});
			},
		});
	}

	function initializeWorkbenchQueueTabs(root) {
		if (!root) return;
		withWorkbenchIframeDocument(root, function (doc) {
			const activeUiQueue = readWorkbenchStateFromUrl().queue;
			applyWorkbenchQueueActiveTab(doc, activeUiQueue);
			applyWorkbenchQueueTableVisibility(doc, activeUiQueue);
			applyWorkbenchInsightsVariant(doc, activeUiQueue);
			bindWorkbenchQueueTabs(root, doc);
		});
		fetchAndApplyWorkbenchQueueCounts(root);
	}

	// W4 — Needs Planning List (Primary Screen). Binds the design's own static
	// table rows/footer to live `get_pp_approved_demands_awaiting_planning`
	// data. Only the "Needs Planning" (default) queue has a pixel design today,
	// so this always renders that dataset regardless of the active tab — the
	// same accepted limitation already documented for W3 (per-queue list
	// rendering lands with W6/W7/W8, once those queue screens are designed).
	const WORKBENCH_NEEDS_PLANNING_PAGE_SIZE = 10;
	const WORKBENCH_NEEDS_PLANNING_TABLE_SECTION_TESTID = "pp4-workbench-needs-planning-table-section";
	const WORKBENCH_PACKAGE_TABLE_SECTION_TESTID = "pp4-workbench-package-table-section";
	const WORKBENCH_CATEGORY_TONE_BY_VALUE = {
		goods: "cat-goods",
		works: "cat-works",
		services: "cat-services",
		consultancy: "cat-consultancy",
	};

	// Shared across every row builder (Needs Planning + all 5 package-queue
	// tables) so the dot+pill category chip stays visually identical
	// everywhere, rather than each builder reimplementing its own class
	// string. `badgeEl` is expected to already contain the dot `<span>`
	// (ported verbatim from Needs Planning's own markup into every table).
	function applyWorkbenchCategoryChip(doc, badgeEl, categoryValue) {
		if (!badgeEl) return;
		const value = String(categoryValue || "").trim();
		const tone = WORKBENCH_CATEGORY_TONE_BY_VALUE[value.toLowerCase()] || "cat-goods";
		badgeEl.className =
			"px-2.5 py-1 rounded-full bg-" + tone + "/10 text-" + tone + " font-label-sm font-semibold flex items-center gap-1 w-fit";
		const dot = badgeEl.querySelector("span");
		if (dot) dot.className = "w-1.5 h-1.5 rounded-full bg-" + tone;
		while (badgeEl.lastChild && badgeEl.lastChild !== dot) {
			badgeEl.removeChild(badgeEl.lastChild);
		}
		badgeEl.appendChild(doc.createTextNode(" " + (value || "\u2014")));
	}

	// No design mockup shows an empty state for any table, so this row is
	// fabricated (not ported) from tokens already used elsewhere in this
	// file. `colspan` is read from the table's own `<thead>` rather than
	// hardcoded, since every table has a different column count.
	function appendWorkbenchEmptyStateRow(doc, tbody, message) {
		if (!doc || !tbody) return;
		const table = tbody.closest("table");
		const headerRow = table ? table.querySelector("thead tr") : null;
		const colspan = headerRow ? headerRow.children.length : 1;
		const td = doc.createElement("td");
		td.setAttribute("colspan", String(colspan));
		td.className = "py-16 text-center";
		const wrap = doc.createElement("div");
		wrap.className = "flex flex-col items-center gap-2 text-on-surface-variant";
		const icon = doc.createElement("span");
		icon.className = "material-symbols-outlined text-[32px]";
		icon.textContent = "inbox";
		const label = doc.createElement("span");
		label.className = "font-body-sm";
		label.textContent = message;
		wrap.appendChild(icon);
		wrap.appendChild(label);
		td.appendChild(wrap);
		const tr = doc.createElement("tr");
		tr.setAttribute("data-testid", "pp4-workbench-empty-row");
		tr.appendChild(td);
		tbody.appendChild(tr);
	}

	// "Rows per page" is `footer.children[0]` (the summary/pagination group
	// used above is `footer.children[1]`) — its own `<div class="relative ...">`
	// trigger + the `<span class="font-label-md ...">` that shows the current
	// page size, ported verbatim from Needs Planning into every table's
	// footer during the earlier UI-consistency pass.
	function workbenchRowsPerPageEls(footer) {
		const group = footer ? footer.children[0] : null;
		const trigger = group ? group.querySelector(".relative") : null;
		const valueEl = trigger ? trigger.querySelector("span.font-label-md") : null;
		if (!trigger || !valueEl) return null;
		return { trigger: trigger, valueEl: valueEl };
	}

	// The design ships the "Rows per page" control as inert decoration (a
	// `<div>`, not a `<select>`) — no mockup shows its open-menu state, so
	// this small options popover is fabricated (not ported) the same way the
	// empty-state row is, reusing the trigger's own already-`relative`
	// positioning so it needs no extra wrapper markup.
	function ensureWorkbenchPageSizeMenu(trigger) {
		let menu = trigger.querySelector('[data-pp4-page-size-menu="1"]');
		if (menu) return menu;
		const doc = trigger.ownerDocument;
		menu = doc.createElement("div");
		menu.setAttribute("data-pp4-page-size-menu", "1");
		menu.setAttribute("hidden", "");
		menu.className =
			"absolute bottom-full left-0 mb-1 bg-surface-container-lowest border border-outline-variant rounded shadow-md py-1 z-10 min-w-[64px]";
		WORKBENCH_PAGE_SIZE_OPTIONS.forEach(function (size) {
			const option = doc.createElement("button");
			option.type = "button";
			option.setAttribute("data-pp4-page-size-option", String(size));
			option.className = "block w-full text-left px-3 py-1.5 font-label-md text-on-surface hover:bg-surface-container-high transition-colors";
			option.textContent = String(size);
			menu.appendChild(option);
		});
		trigger.appendChild(menu);
		return menu;
	}

	function closeAllWorkbenchPageSizeMenus(doc) {
		if (!doc) return;
		doc.querySelectorAll('[data-pp4-page-size-menu="1"]').forEach(function (menu) {
			menu.setAttribute("hidden", "");
		});
	}

	// Binds the trigger (idempotent) and keeps the displayed value in sync
	// with the real page-size state on every render.
	function applyWorkbenchRowsPerPageControl(footerEls, pageSize, onPageSizeChange) {
		if (!footerEls || !footerEls.pageSizeTrigger || !footerEls.pageSizeValueEl) return;
		const trigger = footerEls.pageSizeTrigger;
		const doc = trigger.ownerDocument;
		footerEls.pageSizeValueEl.textContent = String(pageSize);
		const menu = ensureWorkbenchPageSizeMenu(trigger);
		if (trigger.getAttribute("data-pp4-page-size-bound") === "1") return;
		trigger.setAttribute("data-pp4-page-size-bound", "1");
		trigger.addEventListener("click", function (event) {
			event.stopPropagation();
			const isHidden = menu.hasAttribute("hidden");
			closeAllWorkbenchPageSizeMenus(doc);
			if (isHidden) menu.removeAttribute("hidden");
		});
		menu.addEventListener("click", function (event) {
			const optionBtn = event.target.closest("[data-pp4-page-size-option]");
			if (!optionBtn) return;
			event.stopPropagation();
			menu.setAttribute("hidden", "");
			const size = Number(optionBtn.getAttribute("data-pp4-page-size-option"));
			if (Number.isFinite(size) && typeof onPageSizeChange === "function") onPageSizeChange(size);
		});
		if (!doc.__pp4PageSizeOutsideClickBound) {
			doc.__pp4PageSizeOutsideClickBound = true;
			doc.addEventListener("click", function () {
				closeAllWorkbenchPageSizeMenus(doc);
			});
		}
	}

	const WORKBENCH_PAGE_BTN_ACTIVE_CLASS = "w-8 h-8 flex items-center justify-center bg-primary text-white rounded-lg font-label-md";
	const WORKBENCH_PAGE_BTN_INACTIVE_CLASS =
		"w-8 h-8 flex items-center justify-center hover:bg-surface-container-high rounded-lg font-label-md text-on-surface-variant transition-colors";

	// Shared by both footer flavors (Needs Planning + the 5 package-queue
	// tables) so the "1 to N of M" summary, prev/next disabled state, and the
	// design's 3 numbered page-slot buttons all stay driven by the same real
	// pagination math everywhere. The 3 numbered buttons are the design's own
	// static markup (never fabricated) — this only ever mutates their
	// textContent/class/hidden attribute and (de)activates a click binding,
	// sliding a window of real page numbers through the fixed slot count so
	// the total-pages count is never just decorative "1 2 3" regardless of
	// how many rows actually exist.
	function applyWorkbenchPaginationFooter(footerEls, opts) {
		if (!footerEls) return;
		const options = opts || {};
		const pageSize = Math.max(1, Number(options.pageSize) || 1);
		const total = Math.max(0, Number(options.total) || 0);
		const totalPages = Math.max(1, Math.ceil(total / pageSize));
		const page = Math.min(Math.max(1, Number(options.page) || 1), totalPages);
		const start = (page - 1) * pageSize;
		const from = total === 0 ? 0 : start + 1;
		const to = Math.min(start + Number(options.rowsRendered || 0), total);
		footerEls.summaryEl.textContent = __("{0} to {1} of {2}", [from, to, total]);
		footerEls.prevBtn.disabled = page <= 1;
		footerEls.nextBtn.disabled = page >= totalPages;
		applyWorkbenchRowsPerPageControl(footerEls, pageSize, options.onPageSizeChange);

		const slots = footerEls.pageBtns || [];
		const slotCount = slots.length;
		if (!slotCount) return;
		let windowStart = 1;
		if (totalPages > slotCount) {
			windowStart = Math.min(Math.max(1, page - Math.floor(slotCount / 2)), totalPages - slotCount + 1);
		}
		slots.forEach(function (btn, idx) {
			const pageNumber = windowStart + idx;
			if (pageNumber > totalPages) {
				// `hidden` alone loses to the button's own Tailwind `flex`
				// utility class (same specificity, utility declared later in
				// the generated stylesheet), so force it with an inline
				// style too — inline styles always win regardless of
				// stylesheet ordering.
				btn.setAttribute("hidden", "");
				btn.style.display = "none";
				return;
			}
			btn.removeAttribute("hidden");
			btn.style.display = "";
			btn.textContent = String(pageNumber);
			btn.className = pageNumber === page ? WORKBENCH_PAGE_BTN_ACTIVE_CLASS : WORKBENCH_PAGE_BTN_INACTIVE_CLASS;
			btn.setAttribute("data-pp4-page-number", String(pageNumber));
			if (btn.getAttribute("data-pp4-page-btn-bound") === "1") return;
			btn.setAttribute("data-pp4-page-btn-bound", "1");
			btn.addEventListener("click", function () {
				const target = Number(btn.getAttribute("data-pp4-page-number"));
				if (Number.isFinite(target) && typeof options.onPageChange === "function") {
					options.onPageChange(target);
				}
			});
		});
	}

	const workbenchNeedsPlanningRowTemplateByRoot = new WeakMap();
	const workbenchActivePlanCodeByRoot = new WeakMap();
	const workbenchNeedsPlanningRowDataByRoot = new WeakMap();
	const workbenchNeedsPlanningSelectionByRoot = new WeakMap();

	// W6 added a second table+footer pair (package queues) to the same
	// document, so table/footer lookups must be scoped to their own
	// toggleable section rather than relying on document-order "first match".
	function workbenchNeedsPlanningTableBody(doc) {
		const section = doc ? doc.querySelector('[data-testid="' + WORKBENCH_NEEDS_PLANNING_TABLE_SECTION_TESTID + '"]') : null;
		return section ? section.querySelector("table tbody") : null;
	}

	function workbenchNeedsPlanningFooterEls(doc) {
		const section = doc ? doc.querySelector('[data-testid="' + WORKBENCH_NEEDS_PLANNING_TABLE_SECTION_TESTID + '"]') : null;
		const footer = section ? section.querySelector("footer") : null;
		if (!footer) return null;
		// `footer.children[1]` (not `querySelector("div:nth-child(2)")`, which
		// would also match the nested "rows per page" dropdown div — its own
		// 2nd child — since :nth-child is scoped to each element's own parent).
		const summaryGroup = footer.children[1];
		if (!summaryGroup) return null;
		const summaryEl = summaryGroup.querySelector("span");
		const buttons = Array.prototype.slice.call(summaryGroup.querySelectorAll("button"));
		if (!summaryEl || buttons.length < 2) return null;
		const pageSizeEls = workbenchRowsPerPageEls(footer);
		return {
			summaryEl: summaryEl,
			prevBtn: buttons[0],
			nextBtn: buttons[buttons.length - 1],
			pageBtns: buttons.slice(1, buttons.length - 1),
			pageSizeTrigger: pageSizeEls ? pageSizeEls.trigger : null,
			pageSizeValueEl: pageSizeEls ? pageSizeEls.valueEl : null,
		};
	}

	function workbenchDemandFormRoute(demandId) {
		return String(demandId || "").trim();
	}

	function buildWorkbenchNeedsPlanningRow(template, doc, row) {
		const tr = template.cloneNode(true);
		const data = row || {};
		const demand = data.demand || {};
		const demandId = workbenchDemandFormRoute(demand.id);
		tr.setAttribute("data-demand-id", demandId);

		const cells = tr.querySelectorAll("td");
		const checkbox = cells[0] ? cells[0].querySelector('input[type="checkbox"]') : null;
		if (checkbox) checkbox.checked = false;

		const links = cells[1] ? cells[1].querySelectorAll("a") : [];
		const titleLink = links[0];
		const refLink = links[1];
		const href = demandId ? "/app/demand/" + encodeURIComponent(demandId) : "#";
		if (titleLink) {
			const icon = titleLink.querySelector(".material-symbols-outlined");
			titleLink.textContent = "";
			titleLink.appendChild(doc.createTextNode(String(demand.name || demand.code || "").trim() + " "));
			if (icon) titleLink.appendChild(icon);
			titleLink.setAttribute("href", href);
		}
		if (refLink) {
			refLink.textContent = String(demand.code || "").trim();
			refLink.setAttribute("href", href);
		}

		const deptEl = cells[2] ? cells[2].querySelector("span") : null;
		if (deptEl) deptEl.textContent = String(data.department || "").trim() || "\u2014";

		const categoryBadge = cells[3] ? cells[3].querySelector("span") : null;
		applyWorkbenchCategoryChip(doc, categoryBadge, data.category);

		const valueSpans = cells[4] ? cells[4].querySelectorAll("span") : [];
		if (valueSpans[0]) valueSpans[0].textContent = String(data.currency || "KES").trim();
		if (valueSpans[1]) {
			const amount = Number(data.estimated_value || 0);
			valueSpans[1].textContent = (Number.isFinite(amount) ? Math.round(amount) : 0).toLocaleString("en-US");
		}

		const budgetLine = data.budget_line || {};
		const budgetLinked = String(budgetLine.id || budgetLine.code || "").trim().length > 0;
		const budgetWrap = cells[5] ? cells[5].querySelector("div") : null;
		if (budgetWrap) {
			const budgetIcon = budgetWrap.querySelector(".material-symbols-outlined");
			const budgetLabel = budgetWrap.querySelector("span:last-child");
			budgetWrap.className = "flex items-center gap-2 font-label-md " + (budgetLinked ? "text-status-success" : "text-status-warning");
			if (budgetIcon) budgetIcon.textContent = budgetLinked ? "verified" : "lock_clock";
			if (budgetLabel) budgetLabel.textContent = budgetLinked ? __("LINKED") : __("UNLINKED");
		}

		tr.addEventListener("click", function (event) {
			if (event.target && event.target.closest('input[type="checkbox"]')) return;
			if (!demandId) return;
			event.preventDefault();
			frappe.set_route("demand-workbench", demandId);
		});

		return tr;
	}

	function renderWorkbenchNeedsPlanningRows(root, doc, payload) {
		const tbody = workbenchNeedsPlanningTableBody(doc);
		if (!tbody) return;
		const template = workbenchNeedsPlanningRowTemplateByRoot.get(root);
		if (!template) return;
		while (tbody.firstChild) {
			tbody.removeChild(tbody.firstChild);
		}
		const rows = payload && payload.ok !== false && Array.isArray(payload.rows) ? payload.rows : [];
		const rowDataByDemandId = {};
		rows.forEach(function (row) {
			tbody.appendChild(buildWorkbenchNeedsPlanningRow(template, doc, row));
			const demand = (row && row.demand) || {};
			const demandId = workbenchDemandFormRoute(demand.id);
			if (demandId) {
				rowDataByDemandId[demandId] = {
					// `demand.id` is the internal Frappe name (used only as the DOM/selection
					// key above); the planning-inclusion APIs expect the business `demand.code`.
					code: demand.code || demand.id,
					estimated_value: Number(row.estimated_value || 0),
					currency: String(row.currency || "KES").trim() || "KES",
				};
			}
		});
		if (!rows.length) {
			appendWorkbenchEmptyStateRow(doc, tbody, __("No demands need planning right now."));
		}
		workbenchNeedsPlanningRowDataByRoot.set(root, rowDataByDemandId);
		// Selection is page/list-scoped: a fresh render (page change or a
		// completed action) always starts from no selection, since the newly
		// cloned checkboxes are unchecked anyway.
		workbenchNeedsPlanningSelectionByRoot.set(root, new Map());
		workbenchUpdateSelectionToolbar(root, doc);

		const footerEls = workbenchNeedsPlanningFooterEls(doc);
		if (!footerEls) return;
		const total = Number((payload && payload.total) || 0);
		const state = readWorkbenchStateFromUrl();
		applyWorkbenchPaginationFooter(footerEls, {
			page: state.page,
			pageSize: state.page_size,
			total: total,
			rowsRendered: rows.length,
			onPageChange: function (targetPage) {
				writeWorkbenchStateToUrl({ page: targetPage });
				fetchAndRenderWorkbenchNeedsPlanningList(root, doc);
			},
			onPageSizeChange: function (size) {
				writeWorkbenchStateToUrl({ page_size: size, page: 1 });
				fetchAndRenderWorkbenchNeedsPlanningList(root, doc);
			},
		});
	}

	// W5 — Needs Planning Actions. Drives the floating selection toolbar
	// (ported verbatim from the "2. Needs planning - selection" design) with
	// real selected-row state, and wires its two bulk actions against the
	// live planning-inclusion APIs. "View Demand" is already covered by the
	// W4 row click (-> demand-workbench), so there is no separate action here.
	function workbenchSelectionToolbarEls(doc) {
		if (!doc) return null;
		const toolbar = doc.getElementById("selection-toolbar");
		if (!toolbar) return null;
		const countEl = toolbar.querySelector(".w-10.h-10.rounded-full.bg-primary");
		const totalEl = toolbar.querySelector(".font-body-sm.text-on-surface-variant");
		const buttons = Array.prototype.slice.call(toolbar.querySelectorAll("button"));
		if (!countEl || !totalEl || buttons.length < 3) return null;
		return {
			toolbar: toolbar,
			countEl: countEl,
			totalEl: totalEl,
			addToPlanBtn: buttons[0],
			createPackageBtn: buttons[1],
			closeBtn: buttons[2],
		};
	}

	function workbenchUpdateSelectionToolbar(root, doc) {
		const els = workbenchSelectionToolbarEls(doc);
		if (!els) return;
		const selection = workbenchNeedsPlanningSelectionByRoot.get(root);
		const items = selection ? Array.from(selection.values()) : [];
		if (!items.length) {
			els.toolbar.style.opacity = "0";
			els.toolbar.style.transform = "translate(-50%, 40px)";
			els.toolbar.style.pointerEvents = "none";
			return;
		}
		const total = items.reduce(function (sum, item) {
			return sum + (Number(item.estimated_value) || 0);
		}, 0);
		const currency = (items[0] && items[0].currency) || "KES";
		els.countEl.textContent = String(items.length);
		els.totalEl.textContent = __("Est. Total: {0} {1}", [currency, Math.round(total).toLocaleString("en-US")]);
		els.toolbar.style.opacity = "1";
		els.toolbar.style.transform = "translate(-50%, 0)";
		els.toolbar.style.pointerEvents = "auto";
	}

	function workbenchClearNeedsPlanningSelection(root, doc) {
		workbenchNeedsPlanningSelectionByRoot.set(root, new Map());
		const tbody = workbenchNeedsPlanningTableBody(doc);
		if (tbody) {
			Array.prototype.forEach.call(tbody.querySelectorAll('input[type="checkbox"]'), function (cb) {
				cb.checked = false;
			});
		}
		workbenchUpdateSelectionToolbar(root, doc);
	}

	function bindWorkbenchNeedsPlanningRowSelection(root, doc) {
		const tbody = workbenchNeedsPlanningTableBody(doc);
		if (!tbody || tbody.getAttribute("data-pp4-np-selection-bound") === "1") return;
		tbody.setAttribute("data-pp4-np-selection-bound", "1");
		tbody.addEventListener("change", function (event) {
			const checkbox = event.target && event.target.closest ? event.target.closest('input[type="checkbox"]') : null;
			if (!checkbox) return;
			const tr = checkbox.closest("tr");
			const demandId = tr ? tr.getAttribute("data-demand-id") : "";
			if (!demandId) return;
			const selection = workbenchNeedsPlanningSelectionByRoot.get(root) || new Map();
			workbenchNeedsPlanningSelectionByRoot.set(root, selection);
			if (checkbox.checked) {
				const rowData = (workbenchNeedsPlanningRowDataByRoot.get(root) || {})[demandId];
				selection.set(demandId, rowData || { code: demandId, estimated_value: 0, currency: "KES" });
			} else {
				selection.delete(demandId);
			}
			workbenchUpdateSelectionToolbar(root, doc);
		});
	}

	function workbenchCallSequential(items, callFn, onDone) {
		const results = [];
		let i = 0;
		function next() {
			if (i >= items.length) {
				onDone(results);
				return;
			}
			const item = items[i];
			i += 1;
			callFn(item, function (result) {
				results.push(result);
				next();
			});
		}
		next();
	}

	function workbenchReportSelectionActionOutcome(results, successMessage, failureMessage) {
		const okResults = results.filter(function (r) {
			return r && r.ok;
		});
		const failResults = results.filter(function (r) {
			return !(r && r.ok);
		});
		if (okResults.length) {
			frappe.show_alert({ indicator: "green", message: successMessage(okResults.length) });
		}
		if (failResults.length) {
			const firstMessage = String((failResults[0] && failResults[0].message) || "").trim();
			frappe.show_alert({
				indicator: "red",
				message: firstMessage || failureMessage(failResults.length),
			});
		}
	}

	function workbenchAddSelectedDemandsToActivePlan(root, doc) {
		const selection = workbenchNeedsPlanningSelectionByRoot.get(root);
		const items = selection ? Array.from(selection.values()) : [];
		if (!items.length) return;
		const planCode = workbenchActivePlanCodeByRoot.get(root);
		if (!planCode) {
			frappe.show_alert({ indicator: "red", message: __("No active procurement plan found.") });
			return;
		}
		workbenchCallSequential(
			items,
			function (item, done) {
				frappe.call({
					method: INCLUDE_DEMAND_IN_PLAN_API,
					args: { demand_code: item.code, procurement_plan_code: planCode, demand_item_codes: "[]" },
					callback: function (response) {
						done((response && response.message) || { ok: false });
					},
				});
			},
			function (results) {
				workbenchReportSelectionActionOutcome(
					results,
					function (n) {
						return __("{0} demand(s) added to the active plan.", [n]);
					},
					function (n) {
						return __("{0} demand(s) could not be added to the active plan.", [n]);
					}
				);
				fetchAndRenderWorkbenchNeedsPlanningList(root, doc);
				fetchAndApplyWorkbenchQueueCounts(root);
			}
		);
	}

	// PW11 — the bulk "Create Package" toolbar action first adds every
	// selected demand to the active plan (same call as "Add to Plan"), then
	// opens the Package Creation Wizard pre-selected with the resulting
	// inclusions instead of silently auto-creating one package per demand —
	// the wizard is the single canonical create-package path (see the
	// Package Wizard tracker's entry-point-replacement scope decision).
	function workbenchCreatePackagesFromSelectedDemands(root, doc) {
		const selection = workbenchNeedsPlanningSelectionByRoot.get(root);
		const items = selection ? Array.from(selection.values()) : [];
		if (!items.length) return;
		const planCode = workbenchActivePlanCodeByRoot.get(root);
		if (!planCode) {
			frappe.show_alert({ indicator: "red", message: __("No active procurement plan found.") });
			return;
		}
		workbenchCallSequential(
			items,
			function (item, done) {
				frappe.call({
					method: INCLUDE_DEMAND_IN_PLAN_API,
					args: { demand_code: item.code, procurement_plan_code: planCode, demand_item_codes: "[]" },
					callback: function (includeResponse) {
						done((includeResponse && includeResponse.message) || { ok: false });
					},
				});
			},
			function (results) {
				const inclusionCodes = results
					.filter(function (r) {
						return r && r.ok && r.inclusion_code;
					})
					.map(function (r) {
						return r.inclusion_code;
					});
				workbenchReportSelectionActionOutcome(
					results,
					function (n) {
						return __("{0} demand(s) added to the active plan.", [n]);
					},
					function (n) {
						return __("{0} demand(s) could not be added to the active plan.", [n]);
					}
				);
				workbenchClearNeedsPlanningSelection(root, doc);
				fetchAndRenderWorkbenchNeedsPlanningList(root, doc);
				fetchAndApplyWorkbenchQueueCounts(root);
				if (!inclusionCodes.length) return;
				openPlanningPackageWizard(root, doc, {
					plan_code: planCode,
					initial_demand_rows: inclusionCodes.map(function (code) {
						return { inclusion_code: code };
					}),
				});
			}
		);
	}

	// Shared launcher for the Package Creation Wizard — every "Create
	// Package" trigger on the Workbench routes through this (PW11).
	//
	// The wizard is a dedicated Desk Page (`create-package-wizard`), not a
	// Dialog, so there is no in-place open()/onSuccess()/onCancel() call —
	// control simply navigates away. Pre-selection is handed off via a
	// single-use sessionStorage entry the wizard page consumes on
	// `on_page_show` (see `create_package_wizard_page.js`). Since the
	// wizard is a full navigation, "success" naturally lands back on this
	// Workbench route through the wizard's own "Back to Workbench"/"Open
	// Package" actions rather than a callback here.
	function openPlanningPackageWizard(root, doc, opts) {
		const o = opts || {};
		const inclusionCodes = (o.initial_demand_rows || [])
			.map(function (row) {
				return row && row.inclusion_code;
			})
			.filter(Boolean);
		try {
			window.sessionStorage.setItem(
				PP_WIZARD_HANDOFF_KEY,
				JSON.stringify({
					plan_code: o.plan_code || "",
					plan_name: o.plan_name || "",
					initial_inclusion_codes: inclusionCodes,
				})
			);
		} catch (e) {
			/* sessionStorage unavailable — wizard falls back to manual Step 1 selection */
		}
		frappe.set_route("create-package-wizard");
	}

	function bindWorkbenchSelectionToolbarActions(root, doc) {
		const els = workbenchSelectionToolbarEls(doc);
		if (!els || els.toolbar.getAttribute("data-pp4-np-toolbar-bound") === "1") return;
		els.toolbar.setAttribute("data-pp4-np-toolbar-bound", "1");
		els.closeBtn.addEventListener("click", function () {
			workbenchClearNeedsPlanningSelection(root, doc);
		});
		els.addToPlanBtn.addEventListener("click", function () {
			workbenchAddSelectedDemandsToActivePlan(root, doc);
		});
		els.createPackageBtn.addEventListener("click", function () {
			workbenchCreatePackagesFromSelectedDemands(root, doc);
		});
	}

	// W10 — every filter-drawer/sort field maps 1:1 onto a named kwarg the
	// backend already accepts (`get_pp_approved_demands_awaiting_planning`
	// and `get_pp_workbench_item_view_model` both gained parity support),
	// so both fetch functions below simply forward whatever's already
	// parsed into URL state — no per-field translation needed.
	function workbenchQueryFilterArgs(state) {
		const args = {};
		if (state.search) args.search_text = state.search;
		if (state.department) args.department = state.department;
		if (state.category) args.category = state.category;
		if (state.value_range) args.value_range = state.value_range;
		if (state.created_from) args.created_from = state.created_from;
		if (state.created_to) args.created_to = state.created_to;
		if (state.sort) args.sort = state.sort;
		return args;
	}

	function fetchAndRenderWorkbenchNeedsPlanningList(root, doc) {
		if (!root || !doc) return;
		const state = readWorkbenchStateFromUrl();
		const page = Math.max(1, Number(state.page) || 1);
		const pageSize = Number(state.page_size) || WORKBENCH_NEEDS_PLANNING_PAGE_SIZE;
		const filterArgs = workbenchQueryFilterArgs(state);
		// `get_pp_approved_demands_awaiting_planning` takes `search`
		// (top-level named kwarg on the *view-model* API) as `search_text`,
		// but its own drawer-refinement fields (department/value_range/
		// created range/sort) use the exact same names as the unified API.
		frappe.call({
			method: APPROVED_DEMANDS_QUEUE_API,
			freeze: false,
			args: Object.assign(
				{
					start: (page - 1) * pageSize,
					limit: pageSize,
				},
				filterArgs
			),
			callback: function (response) {
				const payload = (response && response.message) || {};
				renderWorkbenchNeedsPlanningRows(root, doc, payload);
			},
		});
	}

	function bindWorkbenchNeedsPlanningPagination(root, doc) {
		const footerEls = workbenchNeedsPlanningFooterEls(doc);
		if (!footerEls || footerEls.prevBtn.getAttribute("data-pp4-np-page-bound") === "1") return;
		footerEls.prevBtn.setAttribute("data-pp4-np-page-bound", "1");
		footerEls.nextBtn.setAttribute("data-pp4-np-page-bound", "1");
		// The design's own "next" button never had a `disabled:opacity-30`
		// variant (the mock kept it permanently enabled-looking); add the same
		// utility its "prev" sibling already uses so real disabled state reads
		// consistently once both buttons are data-driven.
		if (String(footerEls.nextBtn.className || "").indexOf("disabled:opacity-30") === -1) {
			footerEls.nextBtn.className = footerEls.nextBtn.className + " disabled:opacity-30";
		}
		footerEls.prevBtn.addEventListener("click", function () {
			if (footerEls.prevBtn.disabled) return;
			const state = readWorkbenchStateFromUrl();
			writeWorkbenchStateToUrl({ page: Math.max(1, Number(state.page) - 1) });
			fetchAndRenderWorkbenchNeedsPlanningList(root, doc);
		});
		footerEls.nextBtn.addEventListener("click", function () {
			if (footerEls.nextBtn.disabled) return;
			const state = readWorkbenchStateFromUrl();
			writeWorkbenchStateToUrl({ page: Number(state.page) + 1 });
			fetchAndRenderWorkbenchNeedsPlanningList(root, doc);
		});
	}

	function initializeWorkbenchNeedsPlanningList(root) {
		if (!root) return;
		withWorkbenchIframeDocument(root, function (doc) {
			if (!workbenchNeedsPlanningRowTemplateByRoot.has(root)) {
				const tbody = workbenchNeedsPlanningTableBody(doc);
				const firstRow = tbody ? tbody.querySelector("tr") : null;
				if (firstRow) workbenchNeedsPlanningRowTemplateByRoot.set(root, firstRow.cloneNode(true));
			}
			bindWorkbenchNeedsPlanningPagination(root, doc);
			bindWorkbenchNeedsPlanningRowSelection(root, doc);
			bindWorkbenchSelectionToolbarActions(root, doc);
			fetchAndRenderWorkbenchNeedsPlanningList(root, doc);
		});
	}

	// W6 — In Creation / Awaiting Review / Ready for Release Lists.
	// (Remaining-queues pass, W7/W8): every non-Needs-Planning queue now has
	// its own real pixel design and its own table shape. In Creation keeps
	// its original table; Awaiting Review + Ready for Release share one
	// table (confirmed byte-identical in the source designs); Blocked and
	// Released each have their own. `WORKBENCH_QUEUE_GROUPS` is the single
	// source of truth mapping each uiQueue to the DOM section it renders
	// into and the row-builder function that clones that section's own
	// pristine `<tr>` — never freehand-built markup, mirroring the W4
	// discipline for Needs Planning.
	const WORKBENCH_PACKAGE_QUEUE_PAGE_SIZE = 10;
	const WORKBENCH_PACKAGE_UI_QUEUE_TO_API_QUEUE = {
		draft_packages: "draft_packages",
		needs_review: "needs_review",
		ready_to_release: "ready_release",
		blocked: "blocked",
		recently_released: "recently_released",
	};
	const WORKBENCH_REVIEW_RELEASE_TABLE_SECTION_TESTID = "pp4-workbench-review-release-table-section";
	const WORKBENCH_BLOCKED_TABLE_SECTION_TESTID = "pp4-workbench-blocked-table-section";
	const WORKBENCH_RELEASED_TABLE_SECTION_TESTID = "pp4-workbench-released-table-section";
	// Every distinct table section across the 5 non-Needs-Planning queues
	// (Awaiting Review + Ready for Release share one, so this is 4 entries
	// for 5 queues) — used to lazily capture one row template per section
	// and to bind/toggle each section's own footer independently.
	const WORKBENCH_QUEUE_GROUP_SECTION_TESTIDS = [
		WORKBENCH_PACKAGE_TABLE_SECTION_TESTID,
		WORKBENCH_REVIEW_RELEASE_TABLE_SECTION_TESTID,
		WORKBENCH_BLOCKED_TABLE_SECTION_TESTID,
		WORKBENCH_RELEASED_TABLE_SECTION_TESTID,
	];
	// Maps the package's own real `readiness_status` (also reused as-is for
	// Blocked's fixed "error" tone) to a small, fixed icon vocabulary —
	// replaces the fake per-uiQueue sample values the first pass of the
	// In Creation table used.
	const WORKBENCH_READINESS_ICON_BY_TONE = {
		success: "check_circle",
		error: "error",
		warning: "warning",
		neutral: "pending",
	};
	const workbenchPackageQueueRowTemplateByRoot = new WeakMap();

	function workbenchPackageQueueTableBody(doc, sectionTestId) {
		const section = doc ? doc.querySelector('[data-testid="' + (sectionTestId || WORKBENCH_PACKAGE_TABLE_SECTION_TESTID) + '"]') : null;
		return section ? section.querySelector("table tbody") : null;
	}

	function workbenchPackageQueueFooterEls(doc, sectionTestId) {
		const section = doc ? doc.querySelector('[data-testid="' + (sectionTestId || WORKBENCH_PACKAGE_TABLE_SECTION_TESTID) + '"]') : null;
		const footer = section ? section.querySelector("footer") : null;
		if (!footer) return null;
		const summaryGroup = footer.children[1];
		if (!summaryGroup) return null;
		const summaryEl = summaryGroup.querySelector("span");
		const buttons = Array.prototype.slice.call(summaryGroup.querySelectorAll("button"));
		if (!summaryEl || buttons.length < 2) return null;
		const pageSizeEls = workbenchRowsPerPageEls(footer);
		return {
			summaryEl: summaryEl,
			prevBtn: buttons[0],
			nextBtn: buttons[buttons.length - 1],
			pageBtns: buttons.slice(1, buttons.length - 1),
			pageSizeTrigger: pageSizeEls ? pageSizeEls.trigger : null,
			pageSizeValueEl: pageSizeEls ? pageSizeEls.valueEl : null,
		};
	}

	const WORKBENCH_QUEUE_GROUP_SECTION_TESTID_BY_UI_QUEUE = {
		draft_packages: WORKBENCH_PACKAGE_TABLE_SECTION_TESTID,
		needs_review: WORKBENCH_REVIEW_RELEASE_TABLE_SECTION_TESTID,
		ready_to_release: WORKBENCH_REVIEW_RELEASE_TABLE_SECTION_TESTID,
		blocked: WORKBENCH_BLOCKED_TABLE_SECTION_TESTID,
		recently_released: WORKBENCH_RELEASED_TABLE_SECTION_TESTID,
	};

	function applyWorkbenchQueueTableVisibility(doc, activeUiQueue) {
		if (!doc) return;
		const needsSection = doc.querySelector('[data-testid="' + WORKBENCH_NEEDS_PLANNING_TABLE_SECTION_TESTID + '"]');
		const packageSection = doc.querySelector('[data-testid="' + WORKBENCH_PACKAGE_TABLE_SECTION_TESTID + '"]');
		const activeSectionTestId = WORKBENCH_QUEUE_GROUP_SECTION_TESTID_BY_UI_QUEUE[activeUiQueue] || "";
		if (needsSection) needsSection.hidden = activeUiQueue !== "needs_planning";
		if (packageSection) packageSection.hidden = activeSectionTestId !== WORKBENCH_PACKAGE_TABLE_SECTION_TESTID;
		WORKBENCH_QUEUE_GROUP_SECTION_TESTIDS.forEach(function (sectionTestId) {
			if (sectionTestId === WORKBENCH_PACKAGE_TABLE_SECTION_TESTID) return;
			const section = doc.querySelector('[data-testid="' + sectionTestId + '"]');
			if (section) section.hidden = sectionTestId !== activeSectionTestId;
		});
	}

	// W7/W8: the "Workbench Insights" heading stays static text for every
	// queue (per direction); only these two insight-items blocks toggle.
	const WORKBENCH_INSIGHTS_DEFAULT_TESTID = "pp4-workbench-insights-default";
	const WORKBENCH_INSIGHTS_RELEASED_TESTID = "pp4-workbench-insights-released";

	function applyWorkbenchInsightsVariant(doc, activeUiQueue) {
		if (!doc) return;
		const defaultEl = doc.querySelector('[data-testid="' + WORKBENCH_INSIGHTS_DEFAULT_TESTID + '"]');
		const releasedEl = doc.querySelector('[data-testid="' + WORKBENCH_INSIGHTS_RELEASED_TESTID + '"]');
		const isReleased = activeUiQueue === "recently_released";
		if (defaultEl) defaultEl.hidden = isReleased;
		if (releasedEl) releasedEl.hidden = !isReleased;
	}

	// Abbreviates a KES amount to the design's "1.4B"/"450M"/"12.5M" style
	// (Needs Planning's full "850,000,000" notation is a different column
	// on a different table, left untouched by this helper).
	function workbenchAbbreviateMoney(value) {
		const amount = Number(value) || 0;
		const sign = amount < 0 ? "-" : "";
		const abs = Math.abs(amount);
		function trimmed(divided) {
			const fixed = divided.toFixed(1);
			return fixed.endsWith(".0") ? fixed.slice(0, -2) : fixed;
		}
		if (abs >= 1e9) return sign + trimmed(abs / 1e9) + "B";
		if (abs >= 1e6) return sign + trimmed(abs / 1e6) + "M";
		if (abs >= 1e3) return sign + trimmed(abs / 1e3) + "K";
		return sign + String(Math.round(abs));
	}

	// Demands "Added to Active Plan" but not yet packaged have no
	// `Procurement Package` doc, so they carry `is_placeholder`/
	// `inclusion_code` instead of a real `underlying_object_id` — same
	// column shape as a real draft package row, but clicking one opens the
	// Package Creation Wizard pre-selected with the existing inclusion
	// (PW11) instead of routing to a package form that doesn't exist yet.
	function workbenchCreatePackageFromInclusionRow(root, doc, inclusionCode) {
		if (!inclusionCode) return;
		const planCode = workbenchActivePlanCodeByRoot.get(root);
		openPlanningPackageWizard(root, doc, {
			plan_code: planCode,
			initial_demand_rows: [{ inclusion_code: inclusionCode }],
		});
	}

	function buildWorkbenchPackageQueueRow(template, doc, item, uiQueue, root) {
		const tr = template.cloneNode(true);
		const data = item || {};
		const isPlaceholder = Boolean(data.is_placeholder);
		const packageCode = workbenchPackageRouteCode(data);
		const inclusionCode = String(data.inclusion_code || "").trim();
		tr.setAttribute("data-package-id", packageCode);
		if (isPlaceholder) tr.setAttribute("data-inclusion-code", inclusionCode);

		const cells = tr.querySelectorAll("td");
		const titleLinks = cells[0] ? cells[0].querySelectorAll("a") : [];
		const titleLink = titleLinks[0];
		const refLink = titleLinks[1];
		const href = packageCode ? buildPackageDetailUrl(packageCode) : "#";
		if (titleLink) {
			const icon = titleLink.querySelector(".material-symbols-outlined");
			titleLink.textContent = "";
			titleLink.appendChild(doc.createTextNode(String(data.title || "").trim() + " "));
			if (icon) titleLink.appendChild(icon);
			titleLink.setAttribute("href", href);
		}
		if (refLink) {
			refLink.textContent = String(data.underlying_object_code || "").trim();
			refLink.setAttribute("href", href);
		}

		const linkedDemandsEl = cells[1] ? cells[1].querySelector("span") : null;
		if (linkedDemandsEl) {
			const demandCount = Number(data.consolidated_demand_count);
			linkedDemandsEl.textContent = String(Number.isFinite(demandCount) ? Math.round(demandCount) : 0);
		}

		const categoryBadge = cells[2] ? cells[2].querySelector("span") : null;
		applyWorkbenchCategoryChip(doc, categoryBadge, data.category_label);

		const valueSpans = cells[3] ? cells[3].querySelectorAll("span") : [];
		if (valueSpans[0]) valueSpans[0].textContent = String(data.currency || "KES").trim();
		if (valueSpans[1]) valueSpans[1].textContent = workbenchAbbreviateMoney(data.estimated_value_number);

		const readinessWrap = cells[4] ? cells[4].querySelector("div") : null;
		applyWorkbenchPackagePillReadiness(readinessWrap, data.readiness_tone, String(data.readiness_status || "").trim());

		tr.addEventListener("click", function (event) {
			event.preventDefault();
			if (isPlaceholder) {
				workbenchCreatePackageFromInclusionRow(root, doc, inclusionCode);
				return;
			}
			if (!packageCode) return;
			navigateToPackageDetailPage(packageCode);
		});

		return tr;
	}

	// Fills the same "rounded-full w-fit" pill style used by the In
	// Creation table's own Readiness column (icon + label share one
	// tinted background), with the package's real readiness fields.
	function applyWorkbenchPackagePillReadiness(wrapEl, tone, label) {
		if (!wrapEl) return;
		const safeTone = WORKBENCH_READINESS_ICON_BY_TONE[tone] ? tone : "neutral";
		const icon = wrapEl.querySelector(".material-symbols-outlined");
		const labelEl = wrapEl.querySelector("span:last-child");
		wrapEl.className = "flex items-center gap-2 px-3 py-1 bg-status-" + safeTone + "/10 text-status-" + safeTone + " rounded-full w-fit";
		if (icon) icon.textContent = WORKBENCH_READINESS_ICON_BY_TONE[safeTone];
		if (labelEl) labelEl.textContent = label;
	}

	// Fills the stacked icon-over-pill style used by Awaiting Review /
	// Ready for Release's Readiness column and Blocked's Blocker Reason
	// column (same DOM shape in both designs: icon has no background,
	// only the label span is tinted).
	function applyWorkbenchStackedStatusPill(wrapEl, tone, label) {
		if (!wrapEl) return;
		const safeTone = WORKBENCH_READINESS_ICON_BY_TONE[tone] ? tone : "neutral";
		const icon = wrapEl.querySelector(".material-symbols-outlined");
		const labelEl = wrapEl.querySelector("span:last-child");
		if (icon) {
			icon.className = "material-symbols-outlined text-status-" + safeTone + " text-[20px]";
			icon.textContent = WORKBENCH_READINESS_ICON_BY_TONE[safeTone];
		}
		if (labelEl) {
			labelEl.className = "bg-status-" + safeTone + "/10 text-status-" + safeTone + " font-label-md text-label-md px-2 py-0.5 rounded";
			labelEl.textContent = label;
		}
	}

	// Awaiting Review + Ready for Release table (6 columns: Title & Ref,
	// Linked, Category, Est. Value, Review Status, Readiness). The title is
	// a real `<a>` (Needs-Planning-style, no separate "Actions" column) but
	// navigation is still bound to the whole row, same as the other new
	// row builders.
	function buildWorkbenchReviewReleaseRow(template, doc, item) {
		const tr = template.cloneNode(true);
		const data = item || {};
		const packageCode = workbenchPackageRouteCode(data);
		tr.setAttribute("data-package-id", packageCode);

		const cells = tr.querySelectorAll("td");
		const titleLinks = cells[0] ? cells[0].querySelectorAll("a") : [];
		const titleLink = titleLinks[0];
		const refLink = titleLinks[1];
		const href = packageCode ? buildPackageDetailUrl(packageCode) : "#";
		if (titleLink) {
			const icon = titleLink.querySelector(".material-symbols-outlined");
			titleLink.textContent = "";
			titleLink.appendChild(doc.createTextNode(String(data.title || "").trim() + " "));
			if (icon) titleLink.appendChild(icon);
			titleLink.setAttribute("href", href);
		}
		if (refLink) {
			refLink.textContent = String(data.underlying_object_code || "").trim();
			refLink.setAttribute("href", href);
		}

		const linkedSpans = cells[1] ? cells[1].querySelectorAll("span") : [];
		const linkedCountEl = linkedSpans[linkedSpans.length - 1];
		if (linkedCountEl) {
			const demandCount = Number(data.consolidated_demand_count);
			linkedCountEl.textContent = String(Number.isFinite(demandCount) ? Math.round(demandCount) : 0);
		}

		const categoryBadge = cells[2] ? cells[2].querySelector("span") : null;
		applyWorkbenchCategoryChip(doc, categoryBadge, data.category_label);

		const valueEl = cells[3] ? cells[3].querySelector("span") : null;
		if (valueEl) valueEl.textContent = String(data.currency || "KES").trim() + " " + workbenchAbbreviateMoney(data.estimated_value_number);

		// Granular sub-stage review labels shown in the design (e.g.
		// "Technical Review"/"Budget Clearance") have no backing concept
		// yet — bound to the coarse package status instead (flagged gap,
		// see WORKBENCH_WIRING_TRACKER.md).
		const reviewStatusEl = cells[4] ? cells[4].querySelector("span") : null;
		if (reviewStatusEl) reviewStatusEl.textContent = String(data.status_pill_label || "").trim() || "\u2014";

		const readinessWrap = cells[5] ? cells[5].querySelector("div") : null;
		applyWorkbenchStackedStatusPill(readinessWrap, data.readiness_tone, String(data.readiness_status || "").trim());

		tr.addEventListener("click", function (event) {
			if (!packageCode) return;
			event.preventDefault();
			navigateToPackageDetailPage(packageCode);
		});

		return tr;
	}

	// Blocked table (6 columns: Title & Ref, Linked, Category, Est. Value,
	// Review Status, Blocker Reason). The title is a real `<a>`
	// (Needs-Planning-style, no separate "Actions" column). Rows can be a
	// blocked demand or a blocked package (`underlying_object_type`), so
	// both the row click and the title `href` branch to the matching Desk
	// surface for each.
	function buildWorkbenchBlockedRow(template, doc, item) {
		const tr = template.cloneNode(true);
		const data = item || {};
		const targetId = String(data.underlying_object_id || "").trim();
		const targetCode = workbenchPackageRouteCode(data);
		const isBlockedDemand = data.underlying_object_type === "approved_demand";
		tr.setAttribute("data-package-id", targetId);

		const cells = tr.querySelectorAll("td");
		const titleLinks = cells[0] ? cells[0].querySelectorAll("a") : [];
		const titleLink = titleLinks[0];
		const refLink = titleLinks[1];
		const href = targetId
			? isBlockedDemand
				? "/app/demand/" + encodeURIComponent(targetId)
				: buildPackageDetailUrl(targetCode || targetId)
			: "#";
		if (titleLink) {
			const icon = titleLink.querySelector(".material-symbols-outlined");
			titleLink.textContent = "";
			titleLink.appendChild(doc.createTextNode(String(data.title || "").trim() + " "));
			if (icon) titleLink.appendChild(icon);
			titleLink.setAttribute("href", href);
		}
		if (refLink) {
			refLink.textContent = String(data.underlying_object_code || "").trim();
			refLink.setAttribute("href", href);
		}

		const linkedSpans = cells[1] ? cells[1].querySelectorAll("span") : [];
		const linkedCountEl = linkedSpans[linkedSpans.length - 1];
		if (linkedCountEl) {
			const demandCount = Number(data.consolidated_demand_count);
			linkedCountEl.textContent = String(Number.isFinite(demandCount) ? Math.round(demandCount) : 0);
		}

		const categoryBadge = cells[2] ? cells[2].querySelector("span") : null;
		applyWorkbenchCategoryChip(doc, categoryBadge, data.category_label);

		const valueEl = cells[3] ? cells[3].querySelector("span") : null;
		if (valueEl) valueEl.textContent = String(data.currency || "KES").trim() + " " + workbenchAbbreviateMoney(data.estimated_value_number);

		const reviewStatusEl = cells[4] ? cells[4].querySelector("span") : null;
		if (reviewStatusEl) reviewStatusEl.textContent = String(data.review_status_label || "").trim() || "\u2014";

		// No real per-blocker severity classification exists yet (flagged
		// gap) — every row uses one fixed "error" tone, matching the
		// design's own first sample row.
		const blockerWrap = cells[5] ? cells[5].querySelector("div") : null;
		applyWorkbenchStackedStatusPill(blockerWrap, "error", String(data.status_detail || "").trim() || "\u2014");

		tr.addEventListener("click", function (event) {
			if (!targetId) return;
			event.preventDefault();
			if (isBlockedDemand) {
				frappe.set_route("demand-workbench", targetId);
			} else {
				navigateToPackageDetailPage(targetCode || targetId);
			}
		});

		return tr;
	}

	// Released table (5 columns: Title & Ref, Linked, Category, Est. Value,
	// Tender Status). Title is a real `<a>` link, same pattern as In
	// Creation.
	function buildWorkbenchReleasedRow(template, doc, item) {
		const tr = template.cloneNode(true);
		const data = item || {};
		const packageCode = workbenchPackageRouteCode(data);
		tr.setAttribute("data-package-id", packageCode);

		const cells = tr.querySelectorAll("td");
		const titleLinks = cells[0] ? cells[0].querySelectorAll("a") : [];
		const titleLink = titleLinks[0];
		const refLink = titleLinks[1];
		const href = packageCode ? buildPackageDetailUrl(packageCode) : "#";
		if (titleLink) {
			const icon = titleLink.querySelector(".material-symbols-outlined");
			titleLink.textContent = "";
			titleLink.appendChild(doc.createTextNode(String(data.title || "").trim() + " "));
			if (icon) titleLink.appendChild(icon);
			titleLink.setAttribute("href", href);
		}
		if (refLink) {
			refLink.textContent = String(data.underlying_object_code || "").trim();
			refLink.setAttribute("href", href);
		}

		const linkedSpans = cells[1] ? cells[1].querySelectorAll("span") : [];
		const linkedCountEl = linkedSpans[linkedSpans.length - 1];
		if (linkedCountEl) {
			const demandCount = Number(data.consolidated_demand_count);
			linkedCountEl.textContent = String(Number.isFinite(demandCount) ? Math.round(demandCount) : 0);
		}

		const categoryBadge = cells[2] ? cells[2].querySelector("span") : null;
		applyWorkbenchCategoryChip(doc, categoryBadge, data.category_label);

		const valueEl = cells[3] ? cells[3].querySelector("span") : null;
		if (valueEl) valueEl.textContent = String(data.currency || "KES").trim() + " " + workbenchAbbreviateMoney(data.estimated_value_number);

		// No granular tender-status concept exists yet (flagged gap) —
		// "Tender Created" (real: tender_code present) gets the design's
		// success tone; any other coarse fallback text reuses the design's
		// own secondary/neutral tone (its "Published" sample row).
		const tenderStatusEl = cells[4] ? cells[4].querySelector("span") : null;
		if (tenderStatusEl) {
			const label = String(data.tender_status_label || "").trim() || "\u2014";
			const isCreated = label === "Tender Created";
			tenderStatusEl.className = isCreated
				? "bg-status-success/10 text-status-success font-label-md text-label-md px-3 py-1 rounded uppercase tracking-tighter"
				: "bg-secondary-container/10 text-secondary font-label-md text-label-md px-3 py-1 rounded uppercase tracking-tighter";
			tenderStatusEl.textContent = label;
		}

		tr.addEventListener("click", function (event) {
			if (!packageCode) return;
			event.preventDefault();
			navigateToPackageDetailPage(packageCode);
		});

		return tr;
	}

	// Single source of truth: which DOM section + row-builder function each
	// non-Needs-Planning uiQueue renders through (its API queue value comes
	// from `WORKBENCH_PACKAGE_UI_QUEUE_TO_API_QUEUE` above).
	const WORKBENCH_QUEUE_GROUPS = {
		draft_packages: { sectionTestId: WORKBENCH_PACKAGE_TABLE_SECTION_TESTID, rowBuilder: buildWorkbenchPackageQueueRow },
		needs_review: { sectionTestId: WORKBENCH_REVIEW_RELEASE_TABLE_SECTION_TESTID, rowBuilder: buildWorkbenchReviewReleaseRow },
		ready_to_release: { sectionTestId: WORKBENCH_REVIEW_RELEASE_TABLE_SECTION_TESTID, rowBuilder: buildWorkbenchReviewReleaseRow },
		blocked: { sectionTestId: WORKBENCH_BLOCKED_TABLE_SECTION_TESTID, rowBuilder: buildWorkbenchBlockedRow },
		recently_released: { sectionTestId: WORKBENCH_RELEASED_TABLE_SECTION_TESTID, rowBuilder: buildWorkbenchReleasedRow },
	};

	function renderWorkbenchPackageQueueRows(root, doc, uiQueue, payload) {
		const group = WORKBENCH_QUEUE_GROUPS[uiQueue];
		if (!group) return;
		const tbody = workbenchPackageQueueTableBody(doc, group.sectionTestId);
		if (!tbody) return;
		const templates = workbenchPackageQueueRowTemplateByRoot.get(root) || {};
		const template = templates[group.sectionTestId];
		if (!template) return;
		while (tbody.firstChild) {
			tbody.removeChild(tbody.firstChild);
		}
		const items = payload && payload.ok !== false && Array.isArray(payload.items) ? payload.items : [];
		items.forEach(function (item) {
			tbody.appendChild(group.rowBuilder(template, doc, item, uiQueue, root));
		});
		if (!items.length) {
			appendWorkbenchEmptyStateRow(doc, tbody, __("No packages in this queue right now."));
		}

		const footerEls = workbenchPackageQueueFooterEls(doc, group.sectionTestId);
		if (!footerEls) return;
		const total = Number((payload && payload.total) || 0);
		const state = readWorkbenchStateFromUrl();
		applyWorkbenchPaginationFooter(footerEls, {
			page: state.page,
			pageSize: state.page_size,
			total: total,
			rowsRendered: items.length,
			onPageChange: function (targetPage) {
				writeWorkbenchStateToUrl({ page: targetPage });
				fetchAndRenderWorkbenchPackageQueueList(root, doc, readWorkbenchStateFromUrl().queue);
			},
			onPageSizeChange: function (size) {
				writeWorkbenchStateToUrl({ page_size: size, page: 1 });
				fetchAndRenderWorkbenchPackageQueueList(root, doc, readWorkbenchStateFromUrl().queue);
			},
		});
	}

	function fetchAndRenderWorkbenchPackageQueueList(root, doc, uiQueue) {
		if (!root || !doc) return;
		const apiQueue = WORKBENCH_PACKAGE_UI_QUEUE_TO_API_QUEUE[uiQueue];
		if (!apiQueue) return;
		const state = readWorkbenchStateFromUrl();
		const page = Math.max(1, Number(state.page) || 1);
		const pageSize = Number(state.page_size) || WORKBENCH_PACKAGE_QUEUE_PAGE_SIZE;
		const filterArgs = {};
		if (state.search) filterArgs.search = state.search;
		if (state.department) filterArgs.department = state.department;
		if (state.category) filterArgs.category = state.category;
		if (state.value_range) filterArgs.value_range = state.value_range;
		if (state.created_from) filterArgs.created_from = state.created_from;
		if (state.created_to) filterArgs.created_to = state.created_to;
		if (state.sort) filterArgs.sort = state.sort;
		frappe.call({
			method: WORKBENCH_ITEM_VIEW_MODEL_API,
			freeze: false,
			args: Object.assign(
				{
					queue: apiQueue,
					start: (page - 1) * pageSize,
					limit: pageSize,
				},
				filterArgs
			),
			callback: function (response) {
				const payload = (response && response.message) || {};
				renderWorkbenchPackageQueueRows(root, doc, uiQueue, payload);
			},
		});
	}

	function bindWorkbenchPackageQueuePagination(root, doc) {
		WORKBENCH_QUEUE_GROUP_SECTION_TESTIDS.forEach(function (sectionTestId) {
			const footerEls = workbenchPackageQueueFooterEls(doc, sectionTestId);
			if (!footerEls || footerEls.prevBtn.getAttribute("data-pp4-pkg-page-bound") === "1") return;
			footerEls.prevBtn.setAttribute("data-pp4-pkg-page-bound", "1");
			footerEls.nextBtn.setAttribute("data-pp4-pkg-page-bound", "1");
			footerEls.prevBtn.addEventListener("click", function () {
				if (footerEls.prevBtn.disabled) return;
				const state = readWorkbenchStateFromUrl();
				writeWorkbenchStateToUrl({ page: Math.max(1, Number(state.page) - 1) });
				fetchAndRenderWorkbenchPackageQueueList(root, doc, readWorkbenchStateFromUrl().queue);
			});
			footerEls.nextBtn.addEventListener("click", function () {
				if (footerEls.nextBtn.disabled) return;
				const state = readWorkbenchStateFromUrl();
				writeWorkbenchStateToUrl({ page: Number(state.page) + 1 });
				fetchAndRenderWorkbenchPackageQueueList(root, doc, readWorkbenchStateFromUrl().queue);
			});
		});
	}

	function initializeWorkbenchPackageQueueList(root) {
		if (!root) return;
		withWorkbenchIframeDocument(root, function (doc) {
			if (!workbenchPackageQueueRowTemplateByRoot.has(root)) {
				workbenchPackageQueueRowTemplateByRoot.set(root, {});
			}
			const templates = workbenchPackageQueueRowTemplateByRoot.get(root);
			WORKBENCH_QUEUE_GROUP_SECTION_TESTIDS.forEach(function (sectionTestId) {
				if (templates[sectionTestId]) return;
				const tbody = workbenchPackageQueueTableBody(doc, sectionTestId);
				const firstRow = tbody ? tbody.querySelector("tr") : null;
				if (firstRow) templates[sectionTestId] = firstRow.cloneNode(true);
			});
			bindWorkbenchPackageQueuePagination(root, doc);
			const activeUiQueue = readWorkbenchStateFromUrl().queue;
			if (Object.prototype.hasOwnProperty.call(WORKBENCH_PACKAGE_UI_QUEUE_TO_API_QUEUE, activeUiQueue)) {
				fetchAndRenderWorkbenchPackageQueueList(root, doc, activeUiQueue);
			}
		});
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
			let value = String(q[key] || "").trim();
			if (!value) return;
			if (key === "queue") value = normalizeWorkbenchQueueValue(value);
			if (key === "page") value = normalizePositiveIntValue(value, 1);
			if (key === "sort") {
				value = WORKBENCH_SORT_OPTIONS[value] ? value : "newest";
			}
			url.searchParams.set(key, value);
		});
		return url.pathname + url.search;
	}

	function buildWorkbenchPackageRedirectUrl(packageCode) {
		const code = String(packageCode || "").trim();
		if (code) {
			return buildPackageDetailUrl(code);
		}
		const state = readWorkbenchStateFromUrl();
		const queue = String(state.queue || "").trim();
		const item = String(state.item || "").trim();
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
		const state = readWorkbenchStateFromUrl();
		const params = {};
		const queue = String(state.queue || "").trim();
		const item = String(state.item || "").trim();
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
		return `/app/package-detail/${encodeURIComponent(code)}`;
	}

	function workbenchPackageRouteCode(data) {
		const row = data || {};
		return String(row.underlying_object_code || row.underlying_object_id || "").trim();
	}

	function navigateToPackageDetailPage(packageCode) {
		const code = String(packageCode || "").trim();
		if (!code) return;
		if (
			kentender_procurement &&
			typeof kentender_procurement.openPackageDetailPage === "function"
		) {
			kentender_procurement.openPackageDetailPage(code);
			return;
		}
		frappe.route_options = { package: code };
		frappe.set_route("package-detail", code);
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
			return {
				action: "redirect",
				slug: "",
				redirectUrl: buildWorkbenchRedirectUrl(),
			};
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
				action: "redirect",
				slug: "",
				redirectUrl: buildPackageDetailUrl(rawSegments[1] || ""),
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

	function isReleasedToTenderSlug(slug) {
		return String(slug || "").trim() === "releases";
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
		const strategyObjective =
			(drawer.budget_context && drawer.budget_context.strategy_objective) || {};
		const strategyName = String(strategyObjective.name || "").trim();
		const strategyCode = String(strategyObjective.code || "").trim();
		let strategyLabel = "";
		if (strategyName && strategyCode) {
			strategyLabel = strategyName + " (" + strategyCode + ")";
		} else if (strategyName) {
			strategyLabel = strategyName;
		} else if (strategyCode) {
			strategyLabel = strategyCode;
		}
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
			strategy_label: strategyLabel,
			blockers: blockers,
			blocker_count: blockers.length,
			include_allowed: includeAllowed,
			include_blocker_message: blockers[0] || "",
			demand_item_codes: demandItemCodes,
			target_plan_code: String(targetPlan.code || targetPlan.id || targetPlan.name || "").trim(),
			target_plan_name: String(targetPlan.name || "").trim(),
			next_action_label: blockers.length ? __("Resolve blockers before including in plan") : fallbackNextAction,
			primary_action: {
				label: __("Add to Active Plan"),
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

	function refreshWorkbenchWorkList(shell, slug, queueKey, refreshOpts) {
		if (!shell || !isPlanningHomeSlug(slug)) return;
		const mainHost = shell.querySelector('[data-testid="pp2-primary-main-host"]');
		if (!mainHost) return;
		const normalizedQueue = String(queueKey || "").trim();
		const ro = refreshOpts || {};
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
				if (queueHost && typeof queueTabsApi.fetchAndRender === "function") {
					queueTabsApi.fetchAndRender(queueHost, { activeQueue: normalizedQueue });
				} else if (queueHost && typeof queueTabsApi.render === "function") {
					queueTabsApi.render(queueHost, { activeQueue: normalizedQueue });
				}
			}
		}
		const workListHost = mainHost.querySelector('[data-testid="pp2-primary-work-list-host"]');
		const workListApi =
			kentender_procurement &&
			kentender_procurement.PlanningWorkbenchWorkList &&
			typeof kentender_procurement.PlanningWorkbenchWorkList.fetchAndRender === "function"
				? kentender_procurement.PlanningWorkbenchWorkList
				: null;
		if (workListHost && workListApi && ro.suppressAutoSelect === true) {
			workListApi.fetchAndRender(workListHost, {
				queue: normalizedQueue || "needs_planning",
				suppressAutoSelect: true,
			});
			return;
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
		const planName = String(summaryData.target_plan_name || summaryData.active_plan_name || "").trim();
		const demandCode = String(result.demand_code || summaryData.demand_code || "").trim();
		const legacyMessage = __("Demand added to the procurement plan.");
		const message = workbench
			? planName
				? __("This demand has been added to:") + " " + planName
				: __("Demand added to the active procurement plan.")
			: legacyMessage;
		return {
			context_slug: workbench ? "workbench" : "approved-demands",
			include_success: true,
			title: String(summaryData.title || "").trim(),
			include_success_message: message,
			status_headline: workbench ? __("Added to active plan") : "",
			target_plan_name: planName,
			next_step_detail: workbench
				? __("Create a procurement package for this demand.")
				: "",
			next_action_label: __("Create Package"),
			primary_action: {
				label: __("Create Package"),
				action: "create_package_next",
				testid: "pp2-create-package-next-action",
			},
			secondary_actions: workbench
				? [
						{
							label: __("View Demand"),
							action: "view_demand",
							testid: "pp3-view-demand-button",
						},
					]
				: [
						{
							label: __("Back to Approved Demands"),
							action: "back_to_approved_demands",
							testid: "pp2-back-to-approved-demands",
						},
					],
			show_evidence_action: workbench,
			underlying_object_type: "approved_demand",
			underlying_object_code: demandCode,
			demand_code: demandCode,
			target_plan_code: String(
				result.procurement_plan_code || summaryData.target_plan_code || "",
			).trim(),
			inclusion_code: String(result.inclusion_code || "").trim(),
		};
	}

	// PW11 — routes into the Package Creation Wizard instead of the retired
	// single-field modal. The drawer pre-flight call is kept: it still
	// surfaces the "duplicate package already exists" / "not ready" blocker
	// dialogs before the wizard ever opens (the wizard's own Step 1
	// eligibility list simply omits already-packaged inclusions, which
	// would otherwise silently drop this business-readable detail).
	function openCreatePackageModalForShell(shell, summaryData) {
		const payload = summaryData || {};
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
			if (drawer.create_allowed === false) {
				if (drawer.duplicate_package) {
					const existingCode = String(drawer.existing_package_code || "").trim();
					frappe.msgprint({
						title: __("Package already exists"),
						indicator: "orange",
						message:
							'<div data-testid="pp2-create-package-duplicate-dialog">' +
							'<p data-testid="pp2-create-package-blocker-message">' +
							frappe.utils.escape_html(
								String(drawer.blocker_message || "").trim() ||
									__(
										"A procurement package already exists for this included demand. Open the existing package to continue."
									)
							) +
							"</p></div>",
						primary_action: existingCode
							? {
									label: __("Open Package"),
									action: function () {
										window.location.href = buildWorkbenchOpenPackageUrl(existingCode);
									},
								}
							: undefined,
					});
					return;
				}
				frappe.msgprint({
					title: __("Unable to create package"),
					indicator: "orange",
					message:
						'<div data-testid="pp2-create-package-blocker-message">' +
						frappe.utils.escape_html(
							String(drawer.blocker_message || "").trim() ||
								__("This demand is not ready for package creation.")
						) +
						"</div>",
				});
				return;
			}
			// Wizard is now a full-page navigation (see `openPlanningPackageWizard`
			// above) — there is no in-place onSuccess/onCancel callback anymore;
			// the wizard's own Step 4 ("Open Package"/"Back to Workbench")
			// handles the post-create journey once control leaves this shell.
			openPlanningPackageWizard(null, null, {
				plan_code: String(payload.target_plan_code || "").trim(),
				plan_name: String(drawer.active_plan_name || payload.target_plan_name || "").trim(),
				initial_demand_rows: [
					{ inclusion_code: String(drawer.inclusion_code || payload.inclusion_code || "").trim() },
				],
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
				if (actionKey === "view_demand") {
					const demandCode = String(successSummary.demand_code || "").trim();
					if (!demandCode) return;
					frappe.call({
						method: APPROVED_DEMANDS_DRAWER_API,
						args: { demand_code: demandCode },
						callback: function (response) {
							const message = (response && response.message) || {};
							const route = String(
								(message.actions && message.actions.approval_certificate_route) ||
									(message.evidence && message.evidence.view_route) ||
									"",
							).trim();
							if (route) {
								window.location.href = route;
							}
						},
					});
					return;
				}
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
			onEvidenceAction: function () {
				openWorkbenchEvidenceDrawer({
					title: String(successSummary.title || payloadSummary.title || "").trim(),
					underlying_object_type: "approved_demand",
					underlying_object_code: String(successSummary.demand_code || "").trim(),
				});
			},
		});
		if (workbench) {
			const queueKey =
				kentender_procurement &&
				kentender_procurement.PlanningWorkbenchWorkList &&
				typeof kentender_procurement.PlanningWorkbenchWorkList.queueFromUrl === "function"
					? kentender_procurement.PlanningWorkbenchWorkList.queueFromUrl()
					: "needs_planning";
			refreshWorkbenchWorkList(shell, slug, queueKey, { suppressAutoSelect: true });
		}
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
				message: __("Add to Active Plan modal is unavailable."),
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
			'<div class="pp2-primary-context-page-header" data-testid="pp2-page-header-host"></div>' +
			'<div class="pp2-primary-context-active-plan" data-testid="pp3-active-plan-host"></div>';
		const pageHeaderHost = contextHost.querySelector('[data-testid="pp2-page-header-host"]');
		const activePlanHost = contextHost.querySelector('[data-testid="pp3-active-plan-host"]');
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
			'<div class="pp2-primary-context-page-header" data-testid="pp2-page-header-host"></div>' +
			'<div class="pp2-primary-context-active-plan" data-testid="pp3-active-plan-host"></div>';
		const pageHeaderHost = contextHost.querySelector('[data-testid="pp2-page-header-host"]');
		const activePlanHost = contextHost.querySelector('[data-testid="pp3-active-plan-host"]');
		if (isProcurementPlansSlug(slug)) {
			if (activePlanHost) activePlanHost.innerHTML = "";
		} else if (isReleasedToTenderSlug(slug) || isPackageDetailSlug(slug)) {
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

	function mountReleasedToTenderSurface(mainHost, slug, root) {
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
				'<article class="pp3-released-to-tender-surface" data-testid="' +
				esc(markerId) +
				'"><div class="pp3-released-to-tender-surface__body" data-testid="pp3-released-to-tender-body"></div></article>';
			const bodyHost = root.querySelector('[data-testid="pp3-released-to-tender-body"]');
			const listApi =
				kentender_procurement &&
				kentender_procurement.PlanningReleasedList &&
				typeof kentender_procurement.PlanningReleasedList.render === "function"
					? kentender_procurement.PlanningReleasedList
					: null;
			if (listApi && bodyHost) {
				let selectedCode = "";
				try {
					selectedCode = String(
						new URLSearchParams(window.location.search).get("package") || "",
					).trim();
				} catch (e) {
					selectedCode = "";
				}
				function selectRow(row) {
					const code = String(((row && row.package) || {}).code || "").trim();
					if (!code) return;
					try {
						const url = new URL(window.location.href);
						url.searchParams.set("package", code);
						window.history.replaceState({}, "", url.pathname + url.search);
					} catch (err) {
						/* ignore */
					}
					const rows = bodyHost.querySelectorAll('[data-testid="pp3-released-row"]');
					for (let i = 0; i < rows.length; i += 1) {
						const rowEl = rows[i];
						const active =
							String(rowEl.getAttribute("data-pp3-package-code") || "").trim() === code;
						rowEl.classList.toggle("is-active", active);
						rowEl.setAttribute("aria-selected", active ? "true" : "false");
					}
					const summaryHost = bodyHost.querySelector(
						'[data-testid="pp3-released-summary-host"]',
					);
					const summaryApi =
						kentender_procurement &&
						kentender_procurement.PlanningReleasedSummary &&
						typeof kentender_procurement.PlanningReleasedSummary.render === "function"
							? kentender_procurement.PlanningReleasedSummary
							: null;
					if (summaryApi && summaryHost) {
						summaryApi.render(summaryHost, {
							packageCode: code,
							onViewEvidence: function (ctx) {
								openWorkbenchEvidenceDrawer({
									title: (ctx && ctx.title) || "",
									package_code: (ctx && ctx.package_code) || code,
								});
							},
						});
					}
				}
				listApi.render(bodyHost, {
					selectedPackageCode: selectedCode,
					onSelect: selectRow,
					onViewEvidence: function (ctx) {
						openWorkbenchEvidenceDrawer({
							title: (ctx && ctx.title) || "",
							package_code: (ctx && ctx.package_code) || "",
						});
					},
				});
			}
		}
	}

	function mountPackageDetailSurface(mainHost, packageCode, root) {
		navigateToPackageDetailPage(packageCode);
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
			if (
				isWorkbenchRoot &&
				typeof kentender_procurement.PlanningWorkbenchQueueTabs.fetchAndRender === "function"
			) {
				kentender_procurement.PlanningWorkbenchQueueTabs.fetchAndRender(queueHost, { slug: slug });
				return;
			}
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
				'<div class="pp2-primary-workspace-shell__right-body" data-testid="pp2-primary-right-panel-body">' +
				'<div class="pp2-primary-summary-host" data-testid="pp2-primary-summary-host"></div>' +
				'<div class="pp2-primary-workspace-shell__next-action text-muted small" data-testid="pp2-primary-next-action-panel"></div>' +
				"</div>" +
				'<div class="pp2-primary-workspace-shell__right-footer" data-testid="pp2-primary-right-panel-footer">' +
				'<button type="button" class="btn btn-xs btn-link pp2-primary-workspace-shell__toggle text-muted" data-testid="pp2-primary-right-panel-toggle" aria-label="' +
				esc(__("Collapse panel")) +
				'"></button>' +
				"</div>" +
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
		shell.setAttribute("data-surface", String(slug || "workbench").trim() || "workbench");
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
				toggle.setAttribute(
					"aria-label",
					collapsed ? __("Collapse panel") : __("Expand panel"),
				);
			});
		}
		if (toggle) {
			const collapsed = shell.getAttribute("data-right-panel-collapsed") === "1";
			toggle.textContent = collapsed ? __("Expand panel") : __("Collapse panel");
			toggle.setAttribute(
				"aria-label",
				collapsed ? __("Expand panel") : __("Collapse panel"),
			);
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
		return false;
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
		return Array.from(document.querySelectorAll(".item-anchor"));
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
		const anchors = planningNestedNavAnchors();
		for (let i = 0; i < anchors.length; i += 1) {
			const anchor = anchors[i];
			if (!(anchor instanceof HTMLAnchorElement)) continue;
			const labelEl = anchor.querySelector(".sidebar-item-label");
			const rawLabel = String(labelEl ? labelEl.textContent || "" : "").trim().toLowerCase();
			if (rawLabel !== "planning workbench" && rawLabel !== "procurement planning" && rawLabel !== "workbench") {
				continue;
			}
			if (labelEl) {
				labelEl.textContent = __("Planning Workbench");
			}
			anchor.setAttribute("href", ROOT_PATH);
			anchor.setAttribute("data-testid", "pp4-nav-planning-workbench");
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
		document.body.classList.remove("kt-pp4-shell");
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
			renderRouteNotFound(root);
			document.body.classList.remove("kt-pp2-shell");
			document.body.classList.add("kt-pp4-shell");
			syncSidebarActive("");
			return hierarchyReady;
		}

		const searchParams = new URLSearchParams(window.location.search || "");
		const hasPackageCode = searchParams.has("package_code");
		const hasWorkbenchState = hasWorkbenchStateQuery(searchParams);
		const hasApprovedDemandQuery = searchParams.has("queue") || searchParams.has("item");
		const hasPlanCode = searchParams.has("plan");
		syncSurfaceUrl(slug, {
			preserveSearch: slug === "" && (hasPackageCode || hasWorkbenchState || hasApprovedDemandQuery || hasPlanCode),
		});
		canonicalizeWorkbenchStateQuery();
		const routeSignature = String(window.location.pathname || "") + "|" + String(window.location.search || "");
		document.querySelectorAll('[data-testid="pp2-primary-workspace-shell"]').forEach(function (el) {
			el.remove();
		});
		const alreadyMounted = root.getAttribute("data-pp4-mounted") === "1";
		const lastSignature = pp4MountSignatureByRoot.get(root) || "";
		if (alreadyMounted && lastSignature === routeSignature) {
			document.body.classList.remove("kt-pp2-shell");
			document.body.classList.add("kt-pp4-shell");
			syncSidebarActive("");
			return hierarchyReady;
		}
		renderPlanningWorkbenchV4(root);
		root.setAttribute("data-pp4-mounted", "1");
		pp4MountSignatureByRoot.set(root, routeSignature);
		// W2: active-plan context + gate. W3: queue tab counts + active-tab affordance.
		// W4/W5: Needs Planning list + selection binding. W6: package queue
		// lists (In Creation / Awaiting Review / Ready for Release). Blocked
		// and Released queues (W7/W8) still await a pixel design.
		fetchAndApplyWorkbenchActivePlanContext(root);
		initializeWorkbenchBackToHubLink(root);
		initializeWorkbenchCreateNewPackageButton(root);
		initializeWorkbenchFilterDrawer(root);
		initializeWorkbenchQueueTabs(root);
		initializeWorkbenchNeedsPlanningList(root);
		initializeWorkbenchPackageQueueList(root);
		document.body.classList.remove("kt-pp2-shell");
		document.body.classList.add("kt-pp4-shell");
		syncSidebarActive("");
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
