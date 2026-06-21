// PP2 canonical workspace renderer (hard-cut).
(function () {
	const ROOT_PATH = "/desk/procurement-planning";
	const API = {
		landing:
			"kentender_procurement.procurement_planning.api.landing.get_pp_landing_shell_data",
		list: "kentender_procurement.procurement_planning.api.package_list.get_pp_package_list",
		detail:
			"kentender_procurement.procurement_planning.api.package_detail.get_pp_package_detail",
	};

	const state = {
		routeToken: 0,
		landing: null,
		queueId: "all_packages",
		search: "",
		rows: [],
		selectedPackageName: "",
		detail: null,
	};

	function esc(v) {
		return frappe.utils.escape_html(String(v == null ? "" : v));
	}

	function isPlanningRoute() {
		const p = String(window.location.pathname || "").toLowerCase();
		return p.startsWith(ROOT_PATH);
	}

	function readSlug() {
		const p = String(window.location.pathname || "").toLowerCase();
		if (p.endsWith("/approved-demands")) return "approved-demands";
		if (p.endsWith("/packages")) return "packages";
		if (p.endsWith("/releases")) return "releases";
		if (p.endsWith("/evidence")) return "evidence";
		return "";
	}

	function resolveRoot() {
		return (
			document.getElementById("kt-pp-root") ||
			document.querySelector(".kt-pp-injected-shell")
		);
	}

	function ensureRootHost() {
		let root = resolveRoot();
		if (root) return root;
		const mountPoint =
			document.querySelector(".layout-main-section .editor-js-container") ||
			document.querySelector(".layout-main-section") ||
			document.querySelector(".page-content");
		if (!mountPoint) return null;
		root = document.createElement("div");
		root.id = "kt-pp-root";
		root.className = "kt-pp-injected-shell";
		// Hard-cut: replace workspace editor blocks with canonical PP2 app host.
		mountPoint.innerHTML = "";
		mountPoint.appendChild(root);
		return root;
	}

	function callApi(method, args) {
		return new Promise(function (resolve, reject) {
			frappe.call({
				method: method,
				args: args || {},
				callback: function (r) {
					resolve((r && r.message) || {});
				},
				error: function (e) {
					reject(e);
				},
			});
		});
	}

	function planningStatusBadgeHtml(status, opts) {
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningStatusBadge &&
			typeof kentender_procurement.PlanningStatusBadge.html === "function"
				? kentender_procurement.PlanningStatusBadge
				: null;
		return api
			? api.html(status, opts || {})
			: '<span class="pp2-planning-status-badge is-unknown" data-testid="pp2-planning-status-badge">' +
					esc(status || "—") +
					"</span>";
	}

	function planningHandoffCardHtml(card, opts) {
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningHandoffCard &&
			typeof kentender_procurement.PlanningHandoffCard.render === "function"
				? kentender_procurement.PlanningHandoffCard
				: null;
		if (api) return api.render(card || {}, opts || {});
		return (
			'<article class="pp2-planning-handoff-card is-neutral" data-testid="pp2-planning-handoff-card" data-handoff-kind="' +
			esc(card && card.kind) +
			'"><div data-testid="pp2-handoff-card-title">' +
			esc(card && card.title) +
			"</div></article>"
		);
	}

	function stripTechnicalCodes(value) {
		const raw = String(value == null ? "" : value).trim();
		if (!raw) return "";
		return raw
			.replace(/\s*\(([A-Z]{2,}(?:-[A-Z0-9]+){1,})\)\s*/g, " ")
			.replace(/\b(?:PLANINCL|PKGREL|PKGCONSUME|JRN|TND|DEM|PKG)-[A-Z0-9-]+\b/g, "")
			.replace(/\s{2,}/g, " ")
			.trim();
	}

	function cleanBusinessLabel(value, fallback) {
		const cleaned = stripTechnicalCodes(value);
		if (cleaned) return cleaned;
		return String(fallback || "—");
	}

	function slugForTestid(code) {
		const s = String(code || "")
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-+|-+$/g, "");
		return s || "pkg";
	}

	function pickQueues(landing) {
		const q = (landing && landing.queue_tabs) || {};
		const merged = []
			.concat(q.all || [])
			.concat(q.mywork || [])
			.concat(q.approved || [])
			.concat(q.ready || []);
		const out = [];
		const seen = new Set();
		let hasAllPackages = false;
		for (let i = 0; i < merged.length; i += 1) {
			const item = merged[i] || {};
			const id = String(item.id || "").trim();
			if (!id || seen.has(id)) continue;
			seen.add(id);
			if (id === "all_packages") hasAllPackages = true;
			out.push(item);
		}
		if (!hasAllPackages) {
			out.unshift({
				id: "all_packages",
				label: __("All packages"),
				testid: "pp-queue-all-packages",
			});
		}
		const byId = {};
		for (let x = 0; x < out.length; x += 1) {
			byId[String(out[x].id || "")] = out[x];
		}
		function firstExisting(candidates) {
			for (let i = 0; i < candidates.length; i += 1) {
				const id = candidates[i];
				if (byId[id]) return byId[id];
			}
			return null;
		}
		const mywork = firstExisting(
			((q.mywork || []).map(function (item) {
				return String(item.id || "");
			}) || []).concat(["draft_packages"]),
		);
		const primaryDefs = [
			{ key: "all", label: __("All"), candidates: ["all_packages"] },
			{ key: "my_work", label: __("My Work"), fixed: mywork },
			{
				key: "needs_review",
				label: __("Needs Review"),
				candidates: ["pending_approval", "submitted_packages", "structured_packages"],
			},
			{ key: "ready_for_release", label: __("Ready for Release"), candidates: ["ready_for_tender"] },
			{
				key: "released_consumed",
				label: __("Released / Consumed"),
				candidates: ["released_consumed", "released_to_tender", "approved_not_handed_off", "all_packages"],
			},
			{
				key: "blocked",
				label: __("Blocked"),
				candidates: ["high_risk_escalation", "method_override", "high_risk_packages"],
			},
		];
		const primary = [];
		const used = new Set();
		for (let p = 0; p < primaryDefs.length; p += 1) {
			const def = primaryDefs[p];
			const match = def.fixed || firstExisting(def.candidates || []);
			const id = String((match && match.id) || "all_packages");
			if (match) used.add(id);
			primary.push({
				id: id,
				label: def.label,
				testid: String((match && match.testid) || "pp-queue-" + def.key),
				available: Boolean(match),
			});
		}
		const advanced = out.filter(function (item) {
			return !used.has(String(item.id || ""));
		});
		return { primary: primary, advanced: advanced, all: out };
	}

	function renderNonPackageSurface(root, slug) {
		const labels = {
			"": __("Planning Home"),
			"approved-demands": __("Approved Demands"),
			releases: __("Released to Tender"),
			evidence: __("Planning Evidence"),
		};
		const emptyMessages = {
			"": __("No items need your attention right now."),
			"approved-demands": __("No approved demands match this queue."),
			releases: __("No released packages match this queue."),
			evidence: __("No packages match this queue."),
		};
		root.innerHTML =
			'<section class="pp2-surface-empty-state" data-testid="pp2-surface-empty-state">' +
			'<h3 class="h6 mb-1">' +
			esc(labels[slug || ""] || __("Procurement Planning")) +
			"</h3>" +
			'<p class="text-muted small mb-0">' +
			esc(emptyMessages[slug || ""] || __("No items need your attention right now.")) +
			"</p>" +
			"</section>";
	}

	function renderPackageShell(root) {
		const queueModel = pickQueues(state.landing);
		const queues = queueModel.primary || [];
		let queueHtml = "";
		for (let i = 0; i < queues.length; i += 1) {
			const item = queues[i] || {};
			const id = String(item.id || "");
			const active = id === state.queueId ? " is-active" : "";
			const disabled = item.available === false ? " is-disabled" : "";
			queueHtml +=
				'<button type="button" class="btn btn-xs btn-default pp2-canonical-queue' +
				active +
				disabled +
				'" data-testid="' +
				esc(item.testid || "pp-queue-" + id) +
				'" data-pp-queue="' +
				esc(id) +
				'" data-pp-queue-available="' +
				(item.available === false ? "0" : "1") +
				'">' +
				esc(item.label || id) +
				"</button>";
		}
		let advancedHtml = "";
		const advanced = queueModel.advanced || [];
		for (let j = 0; j < advanced.length; j += 1) {
			const item = advanced[j] || {};
			const id = String(item.id || "");
			advancedHtml +=
				'<button type="button" class="btn btn-xs btn-default mt-1 me-1" data-testid="' +
				esc(item.testid || "pp-queue-" + id) +
				'" data-pp-queue="' +
				esc(id) +
				'">' +
				esc(item.label || id) +
				"</button>";
		}
		root.innerHTML =
			'<section class="pp2-canonical-packages" data-testid="pp-landing-page">' +
			'<div class="pp2-canonical-packages__toolbar" data-testid="pp-control-bar">' +
			'<div class="pp2-canonical-packages__queues" id="kt-pp-queue-row">' +
			queueHtml +
			"</div>" +
			'<input type="search" class="form-control input-xs pp2-canonical-packages__search" data-testid="pp-package-search" placeholder="' +
			esc(__("Search packages...")) +
			'" value="' +
			esc(state.search) +
			'" />' +
			"</div>" +
			(advancedHtml
				? '<details class="pp2-canonical-packages__advanced mt-1" data-testid="pp2-advanced-queue-filters"><summary>' +
					esc(__("Advanced filters")) +
					"</summary>" +
					advancedHtml +
					"</details>"
				: "") +
			'<div class="pp2-canonical-packages__layout">' +
			'<section class="pp2-canonical-packages__list" data-testid="pp-package-list"></section>' +
			'<section class="pp2-canonical-packages__detail" data-testid="pp-detail-panel"></section>' +
			"</div>" +
			"</section>";
	}

	function renderRows(root) {
		const list = root.querySelector('[data-testid="pp-package-list"]');
		if (!list) return;
		if (!state.rows.length) {
			list.innerHTML =
				'<div class="text-muted small p-3" data-testid="pp-empty-list">' +
				esc(__("No packages available.")) +
				"</div>";
			return;
		}
		let html = "";
		for (let i = 0; i < state.rows.length; i += 1) {
			const row = state.rows[i] || {};
			const code = String(row.package_code || row.name || "");
			const slug = slugForTestid(code);
			const active = String(row.name || "") === state.selectedPackageName ? " is-active" : "";
			html +=
				'<button type="button" class="pp2-canonical-row' +
				active +
				'" data-testid="pp-row-' +
				esc(slug) +
				'" data-pp-package="' +
				esc(row.name || "") +
				'">' +
				'<div class="pp2-canonical-row__title">' +
				esc(row.package_name || code) +
				"</div>" +
				'<div class="pp2-canonical-row__meta"><span class="font-monospace">' +
				esc(code) +
				"</span> · " +
				esc(row.procurement_method || "—") +
				"</div>" +
				'<div class="pp2-canonical-row__status">' +
				planningStatusBadgeHtml(row.status || "", { context: "package", scope: "list" }) +
				"</div>" +
				"</button>";
		}
		list.innerHTML = html;
	}

	function renderDetail(root) {
		const detailHost = root.querySelector('[data-testid="pp-detail-panel"]');
		if (!detailHost) return;
		const d = state.detail;
		if (!d) {
			detailHost.innerHTML =
				'<div class="text-muted small p-3">' +
				esc(__("Select a package to view details.")) +
				"</div>";
			return;
		}
		const wfStatus = (d.workflow && d.workflow.planning_status) || d.planning_status || "";
		const currentState = cleanBusinessLabel(d.status, __("In progress"));
		const whatHappened = d.planning_consumption_handoff
			? __("Package released from Planning and consumed by Tender Management.")
			: d.planning_release_handoff
				? __("Package released to Tender Management.")
				: d.planning_inclusion_handoff
					? __("Approved demand included in procurement plan and packaged.")
					: __("Package prepared in Procurement Planning.");
		const whatNext = d.planning_consumption_handoff
			? __("Continue in Tender Management.")
			: d.planning_release_handoff
				? __("Continue in Tender Management to progress the tender.")
				: d.release_blocked_by_plan
					? __("Approve the procurement plan before release.")
					: __("Review blockers, then release the package to Tender Management.");
		const blockerItems = [];
		if (d.release_blocked_by_plan) {
			blockerItems.push(__("Procurement plan must be approved before release."));
		}
		const checks = (d.business_readiness && d.business_readiness.checks) || [];
		for (let b = 0; b < checks.length; b += 1) {
			if (checks[b] && checks[b].ok === false) {
				blockerItems.push(cleanBusinessLabel(checks[b].label, __("Readiness check failed")));
			}
		}
		const blockers = blockerItems.length
			? blockerItems
			: [__("No blockers currently. You may continue to the next action.")];
		const primaryHref =
			String(
				(d.planning_release_handoff && d.planning_release_handoff.tender_open_route) ||
					(d.procurement_journey && d.procurement_journey.open_route) ||
					"",
			).trim();
		const primaryText =
			d.planning_consumption_handoff || d.planning_release_handoff
				? __("Continue in Tender Management")
				: __("Open Procurement Journey");
		const evidenceHref =
			ROOT_PATH +
			"/evidence" +
			(d.package_code ? "?package_code=" + encodeURIComponent(d.package_code) : "");
		const stack = [];
		if (d.planning_inclusion_handoff && d.planning_inclusion_handoff.handoff_code) {
			stack.push(
				planningHandoffCardHtml({
					kind: "inclusion",
					title:
						d.planning_inclusion_handoff.title ||
						__("Approved demand included in procurement plan"),
					status: d.planning_inclusion_handoff.status,
					source_object_type: d.planning_inclusion_handoff.source_object_type,
					source_object_code: d.planning_inclusion_handoff.source_object_code,
					target_object_type: d.planning_inclusion_handoff.target_object_type,
					target_object_code: d.planning_inclusion_handoff.target_object_code,
					source_label: d.planning_inclusion_handoff.source_label,
					target_label: d.planning_inclusion_handoff.target_label,
				}),
			);
		}
		if (d.planning_release_handoff && d.planning_release_handoff.handoff_code) {
			stack.push(
				planningHandoffCardHtml(
					{
						kind: "release",
						title:
							d.planning_release_handoff.title ||
							__("Package released to Tender Management"),
						status: d.planning_release_handoff.status,
						source_object_type: d.planning_release_handoff.source_object_type,
						source_object_code: d.planning_release_handoff.source_object_code,
						target_object_type: d.planning_release_handoff.target_object_type,
						target_object_code:
							d.planning_release_handoff.target_object_code ||
							d.planning_release_handoff.tender_code,
						source_label: d.planning_release_handoff.source_label,
						target_label:
							d.planning_release_handoff.target_label ||
							d.planning_release_handoff.tender_title ||
							d.planning_release_handoff.tender_code,
						locked_summary: d.planning_release_handoff.locked_summary,
						passed_forward_summary: d.planning_release_handoff.passed_forward_summary,
						open_route: d.planning_release_handoff.tender_open_route,
					},
					{ action_text: __("Open target") },
				),
			);
		}
		if (
			d.planning_consumption_handoff &&
			(d.planning_consumption_handoff.consumption_code || d.planning_consumption_handoff.status)
		) {
			stack.push(
				planningHandoffCardHtml({
					kind: "consumption",
					title:
						d.planning_consumption_handoff.title ||
						__("Tender Management consumed the package"),
					status: d.planning_consumption_handoff.status,
					source_object_type: d.planning_consumption_handoff.source_object_type,
					source_object_code: d.planning_consumption_handoff.source_object_code,
					target_object_type: d.planning_consumption_handoff.target_object_type,
					target_object_code: d.planning_consumption_handoff.target_object_code,
					source_label: d.planning_consumption_handoff.source_label,
					target_label: d.planning_consumption_handoff.target_label,
				}),
			);
		}
		detailHost.innerHTML =
			'<article class="pp2-canonical-detail" data-testid="pp2-package-detail-canonical">' +
			'<header class="pp2-canonical-detail__head">' +
			'<h3 class="h6 mb-1" data-testid="pp-detail-title">' +
			esc(d.package_name || "") +
			"</h3>" +
			'<div class="small text-muted" data-testid="pp-detail-template">' +
			esc(d.template_name || "—") +
			"</div>" +
			'<div class="small text-muted" data-testid="pp-detail-method">' +
			esc(d.procurement_method || "—") +
			"</div>" +
			'<div class="pp2-canonical-detail__status">' +
			planningStatusBadgeHtml(d.status || "", { context: "package", scope: "header" }) +
			"</div>" +
			"</header>" +
			'<section class="pp2-canonical-detail__workflow" data-testid="pp2-business-summary">' +
			'<div data-testid="pp2-business-what-panel">' +
			'<h4 class="small text-muted mb-1">' +
			esc(__("What happened")) +
			"</h4>" +
			'<div data-testid="pp2-what-happened-panel">' +
			'<p class="small mb-2" data-testid="pp2-business-what-happened">' +
			esc(whatHappened) +
			"</p>" +
			"</div>" +
			'<h4 class="small text-muted mb-1">' +
			esc(__("Current state")) +
			"</h4>" +
			'<p class="small mb-2" data-testid="pp2-business-current-state">' +
			esc(currentState) +
			"</p>" +
			'<h4 class="small text-muted mb-1">' +
			esc(__("What next")) +
			"</h4>" +
			'<div data-testid="pp2-what-next-panel">' +
			'<p class="small mb-2" data-testid="pp2-business-what-next">' +
			esc(whatNext) +
			"</p>" +
			"</div>" +
			'<h4 class="small text-muted mb-1">' +
			esc(__("Blockers")) +
			"</h4>" +
			'<ul class="small mb-2" data-testid="pp2-business-blockers">' +
			blockers
				.map(function (item) {
					return "<li>" + esc(item) + "</li>";
				})
				.join("") +
			"</ul>" +
			planningStatusBadgeHtml(wfStatus, { context: "demand", scope: "workflow" }) +
			(primaryHref
				? '<p class="mb-2"><a class="btn btn-sm btn-primary" data-testid="pp2-business-primary-action" href="' +
					esc(primaryHref) +
					'">' +
					esc(primaryText) +
					"</a></p>"
				: "") +
			'<p class="mb-0" data-testid="pp2-view-evidence-action"><a data-testid="pp2-business-evidence-link" href="' +
			esc(evidenceHref) +
			'">' +
			esc(__("Open evidence")) +
			"</a></p>" +
			"</div>" +
			"</section>" +
			'<section class="pp2-planning-handoff-stack" data-testid="pp2-package-handoff-stack">' +
			stack.join("") +
			"</section>" +
			'<details class="small text-muted mt-2" data-testid="pp2-package-technical-details"><summary data-testid="pp2-technical-details-toggle">' +
			esc(__("Technical details")) +
			"</summary>" +
			"<div>" +
			esc(
				__("Package code") +
					": " +
					String(d.package_code || "—") +
					" | " +
					__("Journey code") +
					": " +
					String((d.procurement_journey && d.procurement_journey.journey_code) || "—"),
			) +
			"</div></details>" +
			"</article>";
	}

	async function loadPackageList(token) {
		const msg = await callApi(API.list, {
			queue_id: state.queueId || "all_packages",
			query: state.search || "",
		});
		if (token !== state.routeToken) return;
		state.rows = (msg && msg.rows) || [];
		if (!state.selectedPackageName && state.rows.length) {
			state.selectedPackageName = String(state.rows[0].name || "");
		}
	}

	async function loadPackageDetail(token) {
		if (!state.selectedPackageName) {
			state.detail = null;
			return;
		}
		const msg = await callApi(API.detail, { package: state.selectedPackageName });
		if (token !== state.routeToken) return;
		state.detail = msg || null;
	}

	function bindEvents(root, token) {
		root.addEventListener("click", function (ev) {
			const target = ev && ev.target && ev.target.closest ? ev.target : null;
			if (!target) return;
			const queueBtn = target.closest("[data-pp-queue]");
			if (queueBtn) {
				if (String(queueBtn.getAttribute("data-pp-queue-available") || "1") === "0") return;
				state.queueId = String(queueBtn.getAttribute("data-pp-queue") || "all_packages");
				state.selectedPackageName = "";
				run(token + 1);
				return;
			}
			const row = target.closest("[data-pp-package]");
			if (row) {
				state.selectedPackageName = String(row.getAttribute("data-pp-package") || "");
				run(token + 1);
			}
		});
		const search = root.querySelector('[data-testid="pp-package-search"]');
		if (search) {
			search.addEventListener("input", function (ev) {
				state.search = String(ev.target.value || "");
				window.clearTimeout(search.__pp2Debounce);
				search.__pp2Debounce = window.setTimeout(function () {
					state.selectedPackageName = "";
					run(token + 1);
				}, 250);
			});
		}
	}

	async function run(nextToken) {
		const root = ensureRootHost();
		if (!root || !isPlanningRoute()) return;
		state.routeToken = nextToken || state.routeToken + 1;
		const token = state.routeToken;
		const slug = readSlug();
		if (slug !== "packages") {
			renderNonPackageSurface(root, slug);
			return;
		}
		try {
			if (!state.landing) {
				state.landing = await callApi(API.landing, {});
				if (token !== state.routeToken) return;
				const queueModel = pickQueues(state.landing);
				const queues = queueModel.primary || queueModel.all || [];
				const hasCurrent = queues.some((q) => String(q.id || "") === state.queueId);
				if (!hasCurrent && queues.length) {
					const allPackages = queues.find((q) => String(q.id || "") === "all_packages");
					state.queueId = String((allPackages && allPackages.id) || queues[0].id || "all_packages");
				}
			}
			renderPackageShell(root);
			bindEvents(root, token);
			await loadPackageList(token);
			if (token !== state.routeToken) return;
			await loadPackageDetail(token);
			if (token !== state.routeToken) return;
			renderRows(root);
			renderDetail(root);
		} catch (e) {
			root.innerHTML =
				'<div class="alert alert-danger" data-testid="pp2-canonical-error">' +
				esc(__("Unable to render Procurement Planning packages.")) +
				"</div>";
		}
	}

	function scheduleRun() {
		window.setTimeout(function () {
			run();
		}, 0);
	}

	$(document).on("page-change", scheduleRun);
	$(document).on("app_ready", scheduleRun);
	if (frappe.router && frappe.router.on) {
		frappe.router.on("change", scheduleRun);
	}
	scheduleRun();
})();
