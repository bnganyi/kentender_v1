/** P9-00 … P9-21a — workbench shell through Audit & Evidence + §13.3 export panel (doc 9 §14–17.12, §14.5). */
(function () {
	const LAYOUT_VERSION = 22;

	let tm2SearchTimer = null;

	const QUEUE_SLUGS = new Set([
		"draft",
		"std-incomplete",
		"ready-review",
		"returned",
		"approved",
		"published",
		"clarifications",
		"addenda",
		"closing-soon",
		"closed",
		"opening-ready",
		"evaluation-ready",
		"cancelled",
	]);

	const QUEUE_ROWS = [
		["tm2-queue-draft", __("Draft"), "draft"],
		["tm2-queue-std-incomplete", __("STD Incomplete"), "std-incomplete"],
		["tm2-queue-ready-review", __("Ready Review"), "ready-review"],
		["tm2-queue-returned", __("Returned"), "returned"],
		["tm2-queue-approved", __("Approved"), "approved"],
		["tm2-queue-published", __("Published"), "published"],
		["tm2-queue-clarifications", __("Clarifications"), "clarifications"],
		["tm2-queue-addenda", __("Addenda"), "addenda"],
		["tm2-queue-closing-soon", __("Closing Soon"), "closing-soon"],
		["tm2-queue-closed", __("Closed"), "closed"],
		["tm2-queue-opening-ready", __("Opening Ready"), "opening-ready"],
		["tm2-queue-evaluation-ready", __("Evaluation Ready"), "evaluation-ready"],
		["tm2-queue-cancelled", __("Cancelled"), "cancelled"],
	];

	function queueLabelForSlug(slug) {
		for (let i = 0; i < QUEUE_ROWS.length; i += 1) {
			if (QUEUE_ROWS[i][2] === slug) {
				return QUEUE_ROWS[i][1];
			}
		}
		return slug || "";
	}

	function setWorkbenchQueueUrl(slug) {
		if (slug && !QUEUE_SLUGS.has(slug)) {
			return;
		}
		const u = new URL(window.location.href);
		if (slug) {
			u.searchParams.set("queue", slug);
		} else {
			u.searchParams.delete("queue");
		}
		window.history.replaceState({}, "", u.pathname + u.search + u.hash);
	}

	function readQueueSlugFromUrl() {
		const raw = new URLSearchParams(window.location.search).get("queue");
		if (raw && QUEUE_SLUGS.has(raw)) {
			return raw;
		}
		return null;
	}

	function applyQueueSelection($w, slug) {
		const s = slug && QUEUE_SLUGS.has(slug) ? slug : null;
		$w.find(".tm2-kpi-chip, .tm2-queue-chip").removeClass("btn-primary");
		if (s) {
			$w.find('.tm2-kpi-chip[data-tm2-queue-slug="' + s + '"], .tm2-queue-chip[data-tm2-queue-slug="' + s + '"]').addClass(
				"btn-primary",
			);
		}
		const $f = $w.find('[data-testid="tm2-tender-list-filter"]');
		if (!$f.length) {
			return;
		}
		if (!s) {
			$f.text(__("All queues"));
			return;
		}
		$f.text(__("Queue") + ": " + queueLabelForSlug(s));
	}

	function refreshKpiCounts($w) {
		frappe.call({
			method: "kentender_procurement.tender_management.api.tm2_workbench.get_workbench_kpi_counts",
			callback(r) {
				const msg = r.message || {};
				if (!msg.ok) {
					return;
				}
				const counts = msg.counts || {};
				const queueCounts = msg.queue_counts || {};
				$w.find(".tm2-kpi-chip").each(function () {
					const $b = $(this);
					const tid = $b.attr("data-testid");
					const base = $b.data("tm2KpiBase") || "";
					const c = typeof counts[tid] === "number" ? counts[tid] : 0;
					$b.text(base + " (" + c + ")");
					const risk = c > 0 && (tid === "tm2-kpi-std-incomplete" || tid === "tm2-kpi-addenda");
					$b.toggleClass("border-left border-warning pl-2", risk);
				});
				$w.find(".tm2-queue-chip").each(function () {
					const $b = $(this);
					const slug = $b.attr("data-tm2-queue-slug");
					const base = $b.data("tm2QueueBase") || "";
					const c = slug && typeof queueCounts[slug] === "number" ? queueCounts[slug] : 0;
					$b.text(base + " (" + c + ")");
					const hot = slug === "std-incomplete" && c > 0;
					$b.toggleClass("border-bottom border-warning", hot);
				});
			},
		});
	}

	function initTm2WorkbenchQueueAndKpis($w) {
		$w.find(".tm2-kpi-chip").each(function () {
			const $b = $(this);
			if (!$b.data("tm2KpiBase")) {
				$b.data("tm2KpiBase", $.trim($b.text()));
			}
		});
		$w.find(".tm2-queue-chip").each(function () {
			const $b = $(this);
			if (!$b.data("tm2QueueBase")) {
				$b.data("tm2QueueBase", $.trim($b.text()));
			}
		});
		$w.off("click.tm2qs").on("click.tm2qs", ".tm2-kpi-chip, .tm2-queue-chip", function (e) {
			e.preventDefault();
			const slug = $(this).attr("data-tm2-queue-slug");
			if (!slug || !QUEUE_SLUGS.has(slug)) {
				return;
			}
			setWorkbenchQueueUrl(slug);
			applyQueueSelection($w, slug);
			refreshTenderList($w);
		});
		$w.off("input.tm2search").on("input.tm2search", '[data-testid="tm2-search-input"]', function () {
			scheduleTenderListSearch($w);
		});
		$w.off("click.tm2row").on("click.tm2row", '[data-testid="tm2-tender-list-rows"] [data-testid="tm2-tender-list-row"]', function (e) {
			e.preventDefault();
			const $row = $(this);
			const tc = ($row.attr("data-tm2-tender-code") || "").trim();
			$w.find('[data-testid="tm2-tender-list-rows"] [data-testid="tm2-tender-list-row"]').removeClass("border-primary");
			$row.addClass("border-primary");
			loadTenderDetail($w, tc);
		});
		initTm2DetailTabs($w);
		refreshKpiCounts($w);
		applyQueueSelection($w, readQueueSlugFromUrl());
		refreshTenderList($w);
		loadTenderDetail($w, "");
	}

	function is_tm2_route() {
		const r = frappe.get_route() || [];
		return r[0] === "tender-management-v2";
	}

	function esc(s) {
		return frappe.utils.escape_html(s);
	}

	function renderTenderListRows($w, items) {
		const $body = $w.find('[data-testid="tm2-tender-list-rows"]');
		if (!$body.length) {
			return;
		}
		$body.empty();
		if (!items || !items.length) {
			$body.append(
				`<div data-testid="tm2-tender-list-empty" class="text-muted small py-2">${esc(__("No tenders in this queue."))}</div>`,
			);
			return;
		}
		for (let i = 0; i < items.length; i += 1) {
			const it = items[i];
			const code = esc(String(it.tender_code || ""));
			const title = esc(String(it.tender_title || ""));
			const pkg = esc(String(it.package_code || ""));
			const method = esc(String(it.procurement_method || ""));
			const cat = esc(String(it.procurement_category || ""));
			const pe = esc(String(it.procuring_entity_code || ""));
			const st = esc(String(it.status || ""));
			const rs = esc(String(it.std_readiness_status || ""));
			const stdv = esc(String(it.std_template_version_code || __("—")));
			const deadline = esc(String(it.submission_deadline_label || __("No deadline set")));
			const blkRaw = it.blocker_summary ? String(it.blocker_summary) : "";
			const blockersHtml = blkRaw
				? `<div class="small mt-1 text-danger" data-testid="tm2-tender-list-row-blockers">${esc(blkRaw)}</div>`
				: `<div class="small mt-1 text-muted" data-testid="tm2-tender-list-row-blockers">${esc(__("No blockers"))}</div>`;
			const badges = Array.isArray(it.badges)
				? it.badges
						.map(function (b) {
							return `<span class="badge badge-light border mr-1 mb-1">${esc(String(b))}</span>`;
						})
						.join("")
				: "";
			const $row = $(
				`<div role="button" tabindex="0" class="tm2-tender-list-row border rounded px-2 py-2 mb-2 bg-white" data-testid="tm2-tender-list-row" data-tm2-tender-code="${code}">
					<div class="font-weight-bold small">${code} · ${title}</div>
					<div class="small text-muted">${esc(__("Package"))}: ${pkg} · ${method} · ${cat}</div>
					<div class="small text-muted">${esc(__("Entity"))}: ${pe}</div>
					<div class="small">${esc(__("Status"))}: ${st} · ${esc(__("STD"))}: ${stdv} · ${esc(__("Readiness"))}: ${rs}</div>
					<div class="small text-muted" data-testid="tm2-tender-list-row-deadline">${esc(__("Deadline"))}: ${deadline}</div>
					${blockersHtml}
					<div class="mt-1">${badges}</div>
				</div>`,
			);
			$body.append($row);
		}
	}

	function refreshTenderList($w) {
		const slug = readQueueSlugFromUrl();
		const q = ($w.find('[data-testid="tm2-search-input"]').val() || "").trim();
		const $body = $w.find('[data-testid="tm2-tender-list-rows"]');
		if ($body.length) {
			$body.html(`<div class="text-muted small py-2">${esc(__("Loading…"))}</div>`);
		}
		frappe.call({
			method: "kentender_procurement.tender_management.api.tm2_workbench.list_workbench_tenders",
			args: { queue: slug || "", search: q, limit: 50 },
			callback(r) {
				const msg = r.message || {};
				if (!msg.ok) {
					renderTenderListRows($w, []);
					if ($body.length) {
						$body.prepend(
							`<div class="small text-danger mb-2" data-testid="tm2-tender-list-error">${esc(
								msg.message || __("Could not load tenders."),
							)}</div>`,
						);
					}
					return;
				}
				renderTenderListRows($w, msg.items || []);
			},
			error() {
				renderTenderListRows($w, []);
			},
		});
	}

	function scheduleTenderListSearch($w) {
		if (tm2SearchTimer) {
			clearTimeout(tm2SearchTimer);
		}
		tm2SearchTimer = setTimeout(function () {
			refreshTenderList($w);
		}, 350);
	}

	function _hideAllTm2DetailPanels($w) {
		$w.find('[data-testid="tm2-tab-panel-overview"]').addClass("d-none");
		$w.find('[data-testid="tm2-tab-panel-std-readiness"]').addClass("d-none");
		$w.find('[data-testid="tm2-tab-panel-timeline"]').addClass("d-none");
		$w.find('[data-testid="tm2-tab-panel-supplier-access"]').addClass("d-none");
		$w.find('[data-testid="tm2-tab-panel-clarifications"]').addClass("d-none");
		$w.find('[data-testid="tm2-tab-panel-addenda"]').addClass("d-none");
		$w.find('[data-testid="tm2-tab-panel-submissions"]').addClass("d-none");
		$w.find('[data-testid="tm2-tab-panel-opening-readiness"]').addClass("d-none");
		$w.find('[data-testid="tm2-tab-panel-evaluation-handoff"]').addClass("d-none");
		$w.find('[data-testid="tm2-tab-panel-contract-handoff"]').addClass("d-none");
		$w.find('[data-testid="tm2-tab-panel-audit-evidence"]').addClass("d-none");
	}

	function switchDetailTab($w, tabTestId) {
		const $tabs = $w.find('[data-testid="tm2-detail-tabs"]');
		$tabs.find('[role="tab"]').removeClass("active").attr("aria-selected", "false");
		const $hit = $tabs.find(`[data-testid="${tabTestId}"]`);
		$hit.addClass("active").attr("aria-selected", "true");
		const $ov = $w.find('[data-testid="tm2-tab-panel-overview"]');
		const $sr = $w.find('[data-testid="tm2-tab-panel-std-readiness"]');
		const $tl = $w.find('[data-testid="tm2-tab-panel-timeline"]');
		const $sa = $w.find('[data-testid="tm2-tab-panel-supplier-access"]');
		const $cl = $w.find('[data-testid="tm2-tab-panel-clarifications"]');
		const $ad = $w.find('[data-testid="tm2-tab-panel-addenda"]');
		const $su = $w.find('[data-testid="tm2-tab-panel-submissions"]');
		const $or = $w.find('[data-testid="tm2-tab-panel-opening-readiness"]');
		const $eh = $w.find('[data-testid="tm2-tab-panel-evaluation-handoff"]');
		const $ch = $w.find('[data-testid="tm2-tab-panel-contract-handoff"]');
		const $ae = $w.find('[data-testid="tm2-tab-panel-audit-evidence"]');
		_hideAllTm2DetailPanels($w);
		if (tabTestId === "tm2-tab-overview") {
			$ov.removeClass("d-none");
			renderOverviewPanel($w);
			return;
		}
		if (tabTestId === "tm2-tab-std-readiness") {
			$sr.removeClass("d-none");
			renderStdReadinessPanel($w);
			return;
		}
		if (tabTestId === "tm2-tab-timeline") {
			$tl.removeClass("d-none");
			renderTimelinePanel($w);
			return;
		}
		if (tabTestId === "tm2-tab-supplier-access") {
			$sa.removeClass("d-none");
			renderSupplierAccessPanel($w);
			return;
		}
		if (tabTestId === "tm2-tab-clarifications") {
			$cl.removeClass("d-none");
			renderClarificationsPanel($w);
			return;
		}
		if (tabTestId === "tm2-tab-addenda") {
			$ad.removeClass("d-none");
			renderAddendaPanel($w);
			return;
		}
		if (tabTestId === "tm2-tab-submissions") {
			$su.removeClass("d-none");
			renderSubmissionsPanel($w);
			return;
		}
		if (tabTestId === "tm2-tab-opening-readiness") {
			$or.removeClass("d-none");
			renderOpeningReadinessPanel($w);
			return;
		}
		if (tabTestId === "tm2-tab-evaluation-handoff") {
			$eh.removeClass("d-none");
			renderEvaluationHandoffPanel($w);
			return;
		}
		if (tabTestId === "tm2-tab-contract-handoff") {
			$ch.removeClass("d-none");
			renderContractHandoffPanel($w);
			return;
		}
		if (tabTestId === "tm2-tab-audit-evidence") {
			$ae.removeClass("d-none");
			renderAuditEvidencePanel($w);
			return;
		}
	}

	function initTm2DetailTabs($w) {
		const $tabs = $w.find('[data-testid="tm2-detail-tabs"]');
		$tabs
			.off("click.tm2dt")
			.on(
				"click.tm2dt",
				'[data-testid="tm2-tab-overview"]:not([disabled]), [data-testid="tm2-tab-std-readiness"]:not([disabled]), [data-testid="tm2-tab-timeline"]:not([disabled]), [data-testid="tm2-tab-supplier-access"]:not([disabled]), [data-testid="tm2-tab-clarifications"]:not([disabled]), [data-testid="tm2-tab-addenda"]:not([disabled]), [data-testid="tm2-tab-submissions"]:not([disabled]), [data-testid="tm2-tab-opening-readiness"]:not([disabled]), [data-testid="tm2-tab-evaluation-handoff"]:not([disabled]), [data-testid="tm2-tab-contract-handoff"]:not([disabled]), [data-testid="tm2-tab-audit-evidence"]:not([disabled])',
				function (e) {
					e.preventDefault();
					const tid = $(this).attr("data-testid");
					if (!tid) {
						return;
					}
					switchDetailTab($w, tid);
				},
			);
		$w.off("click.tm2aexp").on("click.tm2aexp", '[data-testid="tm2-ae-action-export"]:not([disabled])', function (e) {
			e.preventDefault();
			openEvidenceExportDialog($w);
		});
		$w.off("click.tm2hexp").on("click.tm2hexp", '[data-testid="tm2-action-evidence-export"]:not([disabled])', function (e) {
			e.preventDefault();
			openEvidenceExportDialog($w);
		});
	}

	function _tm2ChecklistStatusLabel(st) {
		if (st === "pass") {
			return __("Pass");
		}
		if (st === "fail") {
			return __("Fail");
		}
		return __("Not assessed");
	}

	function renderStdReadinessPanel($w) {
		const $p = $w.find('[data-testid="tm2-tab-panel-std-readiness"]');
		const msg = $w.data("tm2DetailPayload");
		if (!msg || !msg.ok) {
			$p.html(`<div class="text-muted small">${esc(__("Select a tender to see STD & Readiness."))}</div>`);
			return;
		}
		const sr = msg.std_readiness || {};
		const bind = sr.binding || {};
		const meta = sr.readiness_meta || {};
		const rows = Array.isArray(sr.readiness_checklist) ? sr.readiness_checklist : [];
		const derived = Array.isArray(sr.derived_outputs) ? sr.derived_outputs : [];
		const demBlk = sr.dem_missing_block;

		let bindHtml = "";
		const pairs = [
			[__("Template (code)"), String(bind.std_template_code || "").trim() || __("—")],
			[__("Template title"), String(bind.std_template_title || "").trim() || __("—")],
			[__("Template lifecycle"), String(bind.std_template_lifecycle || "").trim() || __("—")],
			[__("Template version"), String(bind.std_template_version_code || "").trim() || __("—")],
			[__("Applicability profile"), String(bind.std_applicability_profile_code || "").trim() || __("—")],
			[__("Tender STD instance"), String(bind.tender_std_instance_code || "").trim() || __("—")],
			[__("Binding"), String(bind.binding_code || "").trim() || __("—")],
			[__("Binding status"), String(bind.binding_status || "").trim() || __("—")],
			[__("Bound by"), String(bind.bound_by || "").trim() || __("—")],
			[__("Bound at"), String(bind.bound_at_display || "").trim() || __("—")],
			[__("Publication snapshot"), String(bind.publication_snapshot_code || "").trim() || __("—")],
			[__("Published snapshot hash"), String(bind.published_snapshot_hash || "").trim() || __("—")],
		];
		for (let i = 0; i < pairs.length; i += 1) {
			const lab = esc(String(pairs[i][0]));
			const val = esc(String(pairs[i][1]));
			bindHtml += `<div class="d-flex justify-content-between border-bottom py-1 small"><span class="text-muted">${lab}</span><span class="text-right">${val}</span></div>`;
		}

		let metaHtml = "";
		if (String(meta.readiness_code || "").trim()) {
			metaHtml = `<div class="small text-muted mb-2" data-testid="tm2-std-readiness-meta">
				${esc(__("Latest readiness"))}: ${esc(String(meta.readiness_code || ""))} · ${esc(String(meta.readiness_status || ""))}
				· ${esc(String(meta.std_readiness_status || ""))}
				${meta.validated_at_display ? " · " + esc(String(meta.validated_at_display || "")) : ""}
			</div>`;
		}

		let chkHtml = "";
		for (let r = 0; r < rows.length; r += 1) {
			const row = rows[r] || {};
			const rawCheckId = String(row.id || `row-${r}`).replace(/[^a-z0-9_-]/gi, "-");
			const st = String(row.status || "unknown");
			const stLab = esc(_tm2ChecklistStatusLabel(st));
			const outc = String(row.output_code || "").trim();
			const outPart = outc ? ` <span class="text-monospace">${esc(outc)}</span>` : "";
			const own = esc(String(row.owner || ""));
			const srcm = esc(String(row.source_module || ""));
			chkHtml += `<div class="small border-bottom py-1 d-flex justify-content-between align-items-start" data-testid="tm2-std-check-${rawCheckId}">
				<div><span class="font-weight-bold">${stLab}</span> — ${esc(String(row.label || ""))}${outPart}</div>
				<div class="text-muted text-right" style="max-width:12rem">${own}<br/>${srcm}</div>
			</div>`;
		}
		if (!chkHtml) {
			chkHtml = `<div class="text-muted small">${esc(__("No checklist rows."))}</div>`;
		}

		let demHtml = "";
		if (demBlk && demBlk.blocker_code) {
			demHtml = `<div class="alert alert-danger small py-2 mb-3" data-testid="tm2-std-dem-blocker">
				<div class="font-weight-bold">${esc(String(demBlk.headline || ""))}</div>
				<div>${esc(__("Owner"))}: ${esc(String(demBlk.owner || ""))}</div>
				<div>${esc(__("Required action"))}: ${esc(String(demBlk.required_action || ""))}</div>
				<div>${esc(__("Blocker code"))}: <span data-testid="tm2-std-dem-blocker-code">${esc(String(demBlk.blocker_code || ""))}</span></div>
				<div>${esc(__("Severity"))}: ${esc(String(demBlk.severity || ""))}</div>
			</div>`;
		}

		const viewLabels = {
			dsm: __("View DSM summary"),
			dom: __("View DOM summary"),
			dem: __("View DEM summary"),
			dcm: __("View DCM summary"),
		};
		let derHtml = "";
		for (let d = 0; d < derived.length; d += 1) {
			const it = derived[d] || {};
			const did = String(it.id || "");
			const code = String(it.code || "").trim();
			const lab = esc(String(it.label || ""));
			const summaryKey = did === "dsm" || did === "dom" || did === "dem" || did === "dcm" ? did : "";
			const vlab = summaryKey ? String(viewLabels[summaryKey] || "") : "";
			const codeEsc = esc(code);
			const btnId =
				summaryKey && code
					? `<button type="button" class="btn btn-default btn-sm ml-2" data-testid="tm2-std-view-${summaryKey}">${esc(vlab)}</button>`
					: summaryKey
						? `<button type="button" class="btn btn-default btn-sm ml-2" disabled title="${esc(
								__("No output code yet — generate via STD Engine workflows."),
							)}">${esc(vlab)}</button>`
						: "";
			const derTid = (did || "x").replace(/[^a-z0-9_-]/gi, "-");
			derHtml += `<div class="small border-bottom py-1 d-flex justify-content-between align-items-center" data-testid="tm2-std-derived-${derTid}">
				<div><strong>${lab}:</strong> <span class="text-monospace">${codeEsc || esc(__("—"))}</span></div>
				<div>${btnId}</div>
			</div>`;
		}

		$p.html(
			`<div data-testid="tm2-std-binding-block" class="mb-3">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("STD binding"))}</div>
				${bindHtml}
			</div>
			${metaHtml}
			<div data-testid="tm2-std-readiness-checklist" class="mb-3">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Readiness checklist"))}</div>
				${chkHtml}
			</div>
			${demHtml}
			<div data-testid="tm2-std-derived-outputs">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Derived outputs (read-only)"))}</div>
				${derHtml || `<div class="text-muted small">${esc(__("No binding outputs yet."))}</div>`}
			</div>`,
		);

		$p.off("click.tm2vsum").on("click.tm2vsum", "[data-testid^='tm2-std-view-']", function (ev) {
			ev.preventDefault();
			const $b = $(this);
			if ($b.prop("disabled")) {
				return;
			}
			const tid = ($b.attr("data-testid") || "").replace("tm2-std-view-", "");
			const map = { dsm: __("DSM"), dom: __("DOM"), dem: __("DEM"), dcm: __("DCM") };
			let code = "";
			for (let x = 0; x < derived.length; x += 1) {
				const di = derived[x] || {};
				if (String(di.id || "") === tid) {
					code = String(di.code || "").trim();
					break;
				}
			}
			frappe.msgprint({
				title: __("Read-only summary"),
				message:
					`<p class="mb-0 small">${esc(
						__(
							"This workbench control does not regenerate or edit derived models. Use STD Engine desk flows when you are permitted to change artifacts.",
						),
					)}</p>` +
					`<p class="mb-0 small"><strong>${esc(String(map[tid] || tid))}:</strong> <span class="text-monospace">${esc(code)}</span></p>`,
				indicator: "blue",
			});
		});
	}

	function renderTimelinePanel($w) {
		const $p = $w.find('[data-testid="tm2-tab-panel-timeline"]');
		const msg = $w.data("tm2DetailPayload");
		if (!msg || !msg.ok) {
			$p.html(`<div class="text-muted small">${esc(__("Select a tender to see the Timeline tab."))}</div>`);
			return;
		}
		const tab = msg.timeline_tab || {};
		const kds = Array.isArray(tab.key_dates) ? tab.key_dates : [];
		let datesHtml = "";
		for (let i = 0; i < kds.length; i += 1) {
			const kd = kds[i] || {};
			const fid = String(kd.field || `idx-${i}`).replace(/[^a-z0-9_-]/gi, "-");
			datesHtml += `<div class="d-flex justify-content-between border-bottom py-1 small" data-testid="tm2-timeline-key-${fid}"><span class="text-muted">${esc(
				String(kd.label || ""),
			)}</span><span class="text-right">${esc(String(kd.value || ""))}</span></div>`;
		}
		if (!datesHtml) {
			datesHtml = `<div class="text-muted small" data-testid="tm2-timeline-key-empty">${esc(
				__("No TM2 Tender Timeline row yet."),
			)}</div>`;
		}

		let serverHtml = "";
		if (tab.show_official_server_time && tab.official_server_time_display) {
			serverHtml = `<div class="alert alert-light border py-2 mb-3 small" data-testid="tm2-timeline-server-time">${esc(
				String(tab.official_server_time_display),
			)}</div>`;
		} else {
			serverHtml = `<div class="text-muted small mb-2" data-testid="tm2-timeline-server-time-muted">${esc(
				__("Official server time is shown when the tender is in a published-active lifecycle state."),
			)}</div>`;
		}

		let noticeHtml = "";
		if (tab.post_publication_notice) {
			noticeHtml = `<div class="alert alert-info py-2 mb-3 small" data-testid="tm2-timeline-post-publish-notice">${esc(
				String(tab.post_publication_notice),
			)}</div>`;
		}

		const warns = Array.isArray(tab.warnings) ? tab.warnings : [];
		let warnHtml = "";
		for (let w = 0; w < warns.length; w += 1) {
			const ww = warns[w] || {};
			const wc = String(ww.warning_code || `w-${w}`).replace(/[^a-z0-9_-]/gi, "-");
			warnHtml += `<div class="small text-warning border-bottom py-1" data-testid="tm2-timeline-warn-${wc}">${esc(String(ww.message || ""))}</div>`;
		}
		if (!warnHtml) {
			warnHtml = `<div class="text-muted small">${esc(__("No timeline warnings detected for current dates."))}</div>`;
		}

		const ext = Array.isArray(tab.extension_history) ? tab.extension_history : [];
		let extHtml = "";
		for (let x = 0; x < ext.length; x += 1) {
			const row = ext[x] || {};
			const code = String(row.addendum_code || "").replace(/[^a-z0-9_-]/gi, "-") || `x-${x}`;
			extHtml += `<div class="small border-bottom py-1" data-testid="tm2-timeline-ext-${code}">${esc(String(row.display_line || ""))}</div>`;
		}
		if (!extHtml) {
			extHtml = `<div class="text-muted small">${esc(__("No addendum deadline revisions recorded in the audit trail yet."))}</div>`;
		}

		const tz = String(tab.timezone || "").trim();
		const tlc = String(tab.timeline_code || "").trim();
		const meta = `<div class="small text-muted mb-2" data-testid="tm2-timeline-meta">${esc(__("Timeline"))}: ${esc(
			tlc || __("—"),
		)} · ${esc(__("Timezone"))}: ${esc(tz || __("—"))}</div>`;

		$p.html(
			`${meta}
			${serverHtml}
			${noticeHtml}
			<div data-testid="tm2-timeline-key-dates" class="mb-3">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Deadlines (TM2 Tender Timeline)"))}</div>
				${datesHtml}
			</div>
			<div data-testid="tm2-timeline-warnings" class="mb-3">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Warnings"))}</div>
				${warnHtml}
			</div>
			<div data-testid="tm2-timeline-extension-history">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Extension history"))}</div>
				${extHtml}
			</div>`,
		);
	}

	function renderSupplierAccessPanel($w) {
		const $p = $w.find('[data-testid="tm2-tab-panel-supplier-access"]');
		const msg = $w.data("tm2DetailPayload");
		if (!msg || !msg.ok) {
			$p.html(`<div class="text-muted small">${esc(__("Select a tender to see the Supplier Access tab."))}</div>`);
			return;
		}
		const tab = msg.supplier_access_tab || {};
		const ar = tab.access_rule || {};
		const notice = esc(String(tab.read_only_notice || ""));

		let ruleHtml = "";
		if (!ar.has_rule) {
			ruleHtml = `<div class="text-muted small">${esc(__("No TM2 Tender Access Rule row yet."))}</div>`;
		} else {
			const lines = [
				[__("Access rule"), String(ar.access_rule_code || "")],
				[__("Visibility"), String(ar.visibility || "")],
				[__("Login required for documents"), ar.requires_supplier_login_for_documents ? __("Yes") : __("No")],
				[__("Invitation required"), ar.requires_invitation ? __("Yes") : __("No")],
				[__("Public notice allowed"), ar.allows_public_notice ? __("Yes") : __("No")],
				[__("Public document download allowed"), ar.allows_public_document_download ? __("Yes") : __("No")],
				[__("Eligibility service required"), ar.eligibility_service_required ? __("Yes") : __("No")],
				[__("Category restrictions"), String(ar.supplier_category_restriction_summary || __("—"))],
				[__("Policy snapshot on file"), ar.has_access_policy_snapshot ? __("Yes") : __("No")],
			];
			for (let i = 0; i < lines.length; i += 1) {
				ruleHtml += `<div class="d-flex justify-content-between border-bottom py-1 small"><span class="text-muted">${esc(
					String(lines[i][0]),
				)}</span><span class="text-right">${esc(String(lines[i][1]))}</span></div>`;
			}
		}

		const invs = Array.isArray(tab.invitations) ? tab.invitations : [];
		let invHtml = "";
		for (let j = 0; j < invs.length; j += 1) {
			const ir = invs[j] || {};
			const ic = String(ir.invitation_code || j).replace(/[^a-z0-9_-]/gi, "-");
			invHtml += `<tr data-testid="tm2-sa-inv-${ic}"><td class="small">${esc(String(ir.supplier_label || ""))}</td><td class="small">${esc(
				String(ir.invitation_code || ""),
			)}</td><td class="small">${esc(String(ir.status || ""))}</td><td class="small text-muted">${esc(
				String(ir.invited_at_display || ""),
			)}</td></tr>`;
		}
		if (!invHtml) {
			invHtml = `<tr><td colspan="4" class="text-muted small">${esc(__("No invitations yet."))}</td></tr>`;
		}

		const parts = Array.isArray(tab.participation_rows) ? tab.participation_rows : [];
		let prHtml = "";
		for (let k = 0; k < parts.length; k += 1) {
			const pr = parts[k] || {};
			const rk = String(pr.participation_code || k).replace(/[^a-z0-9_-]/gi, "-");
			const docs = pr.documents_downloaded ? __("Yes") : __("No");
			prHtml += `<tr data-testid="tm2-sa-part-${rk}">
				<td class="small">${esc(String(pr.supplier_label || ""))}</td>
				<td class="small">${esc(String(pr.eligibility_summary || ""))}</td>
				<td class="small">${esc(String(pr.invitation_status || ""))}</td>
				<td class="small">${esc(String(pr.participation_status || ""))}</td>
				<td class="small">${esc(String(docs))}</td>
				<td class="small">${esc(String(pr.clarification_count != null ? pr.clarification_count : ""))}</td>
				<td class="small">${esc(String(pr.addenda_ack_summary || ""))}</td>
				<td class="small">${esc(String(pr.bid_status || ""))}</td>
				<td class="small text-muted">${esc(String(pr.last_activity_display || ""))}</td>
			</tr>`;
		}
		if (!prHtml) {
			prHtml = `<tr><td colspan="9" class="text-muted small">${esc(__("No supplier participation rows yet."))}</td></tr>`;
		}

		$p.html(
			`<div class="alert alert-light border small py-2 mb-3" data-testid="tm2-sa-readonly-notice">${notice}</div>
			<div data-testid="tm2-sa-access-rule" class="mb-3">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Access rule"))}</div>
				${ruleHtml}
			</div>
			<div data-testid="tm2-sa-invitations" class="mb-3 table-responsive">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Invitations"))}</div>
				<table class="table table-bordered table-sm mb-0">
					<thead><tr>
						<th class="small">${esc(__("Supplier"))}</th>
						<th class="small">${esc(__("Invitation"))}</th>
						<th class="small">${esc(__("Status"))}</th>
						<th class="small">${esc(__("Invited at"))}</th>
					</tr></thead>
					<tbody>${invHtml}</tbody>
				</table>
			</div>
			<div data-testid="tm2-sa-participation" class="table-responsive">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Participation"))}</div>
				<table class="table table-bordered table-sm mb-0">
					<thead><tr>
						<th class="small">${esc(__("Supplier"))}</th>
						<th class="small">${esc(__("Eligibility"))}</th>
						<th class="small">${esc(__("Invitation"))}</th>
						<th class="small">${esc(__("Participation"))}</th>
						<th class="small">${esc(__("Docs downloaded"))}</th>
						<th class="small">${esc(__("Clarifications"))}</th>
						<th class="small">${esc(__("Addenda ack"))}</th>
						<th class="small">${esc(__("Bid status"))}</th>
						<th class="small">${esc(__("Last activity"))}</th>
					</tr></thead>
					<tbody>${prHtml}</tbody>
				</table>
			</div>`,
		);
	}

	function renderClarificationsPanel($w) {
		const $p = $w.find('[data-testid="tm2-tab-panel-clarifications"]');
		const msg = $w.data("tm2DetailPayload");
		if (!msg || !msg.ok) {
			$p.html(`<div class="text-muted small">${esc(__("Select a tender to see the Clarifications tab."))}</div>`);
			return;
		}
		const tab = msg.clarifications_tab || {};
		const notice = esc(String(tab.read_only_notice || ""));
		const order = Array.isArray(tab.status_filter_order) ? tab.status_filter_order : [];
		const sc = tab.status_counts && typeof tab.status_counts === "object" ? tab.status_counts : {};

		let chips = `<button type="button" class="btn btn-xs btn-default mb-1 mr-1 tm2-clar-filter-chip" data-testid="tm2-clar-filter-chip-all" data-tm2-clar-filter="">${esc(
			__("All"),
		)}</button>`;
		for (let i = 0; i < order.length; i += 1) {
			const st = String(order[i] || "").trim();
			if (!st) {
				continue;
			}
			const n = sc[st] != null ? Number(sc[st]) : 0;
			const slug = st.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "status";
			chips += `<button type="button" class="btn btn-xs btn-default mb-1 mr-1 tm2-clar-filter-chip" data-testid="tm2-clar-filter-chip-${esc(
				slug,
			)}" data-tm2-clar-filter="${esc(st)}">${esc(st)} (${n})</button>`;
		}

		const rows = Array.isArray(tab.rows) ? tab.rows : [];
		let body = "";
		for (let j = 0; j < rows.length; j += 1) {
			const row = rows[j] || {};
			const code = String(row.clarification_code || j).trim();
			const sfx = String(row.row_test_suffix || j).replace(/[^a-z0-9_-]/gi, "-");
			const st = String(row.status || "").trim();
			const warn = String(row.addendum_material_warning_text || "").trim();
			const flag = row.request_requires_addendum ? __("Request flagged for addendum") : "";
			let warnBlock = "";
			if (warn) {
				warnBlock = `<div class="alert alert-warning small py-1 mb-1" data-testid="tm2-clar-row-addendum-warning">${esc(
					warn,
				)}</div>`;
			} else if (flag) {
				warnBlock = `<div class="text-muted small mb-1" data-testid="tm2-clar-row-request-flag">${esc(flag)}</div>`;
			}
			const vis = String(row.response_visibility || "").trim();
			const visLine = vis
				? `<div class="text-muted small" data-testid="tm2-clar-row-visibility">${esc(
						__("Visibility") + ": " + vis,
					)}</div>`
				: "";
			body += `<tr data-testid="tm2-clar-row-${esc(sfx)}" data-tm2-clar-status="${esc(st)}">
				<td class="small align-top">
					<div class="font-weight-bold">${esc(code)}</div>
					<div class="text-muted">${esc(String(row.supplier_label || ""))}</div>
				</td>
				<td class="small align-top">${esc(String(row.section_refs_display || ""))}</td>
				<td class="small align-top">${esc(st)}</td>
				<td class="small align-top">
					${warnBlock}
					<div data-testid="tm2-clar-row-question">${esc(String(row.question_preview || ""))}</div>
					<div class="text-muted small mt-1">${esc(String(row.latest_response_code || ""))}${
						row.latest_response_code ? " · " : ""
					}${esc(String(row.latest_response_status || ""))}</div>
					${visLine}
					<div class="text-muted small">${esc(String(row.converted_addendum_code || ""))}</div>
				</td>
				<td class="small text-muted align-top">${esc(String(row.submitted_at_display || ""))}</td>
			</tr>`;
		}
		if (!body) {
			body = `<tr><td colspan="5" class="text-muted small">${esc(__("No clarification requests yet."))}</td></tr>`;
		}

		$p.html(
			`<div class="alert alert-light border small py-2 mb-3" data-testid="tm2-clar-readonly-notice">${notice}</div>
			<div class="mb-2" data-testid="tm2-clar-status-chips">${chips}</div>
			<div class="table-responsive" data-testid="tm2-clar-rows">
				<table class="table table-bordered table-sm mb-0">
					<thead><tr>
						<th class="small">${esc(__("Code · supplier"))}</th>
						<th class="small">${esc(__("Section / refs"))}</th>
						<th class="small">${esc(__("Status"))}</th>
						<th class="small">${esc(__("Question / response / addendum"))}</th>
						<th class="small">${esc(__("Submitted"))}</th>
					</tr></thead>
					<tbody>${body}</tbody>
				</table>
			</div>`,
		);

		$p.off("click.tm2clf").on("click.tm2clf", ".tm2-clar-filter-chip", function (ev) {
			ev.preventDefault();
			const f = ($(this).attr("data-tm2-clar-filter") || "").trim();
			const $rows = $p.find('[data-testid="tm2-clar-rows"] tr[data-tm2-clar-status]');
			if (!f) {
				$rows.removeClass("d-none");
				return;
			}
			$rows.each(function () {
				const st = ($(this).attr("data-tm2-clar-status") || "").trim();
				$(this).toggleClass("d-none", st !== f);
			});
		});
	}

	function renderAddendaPanel($w) {
		const $p = $w.find('[data-testid="tm2-tab-panel-addenda"]');
		const msg = $w.data("tm2DetailPayload");
		if (!msg || !msg.ok) {
			$p.html(`<div class="text-muted small">${esc(__("Select a tender to see the Addenda tab."))}</div>`);
			return;
		}
		const tab = msg.addenda_tab || {};
		const notice = esc(String(tab.read_only_notice || ""));
		const order = Array.isArray(tab.status_filter_order) ? tab.status_filter_order : [];
		const sc = tab.status_counts && typeof tab.status_counts === "object" ? tab.status_counts : {};

		let chips = `<button type="button" class="btn btn-xs btn-default mb-1 mr-1 tm2-ad-filter-chip" data-testid="tm2-ad-filter-chip-all" data-tm2-ad-filter="">${esc(
			__("All"),
		)}</button>`;
		for (let i = 0; i < order.length; i += 1) {
			const st = String(order[i] || "").trim();
			if (!st) {
				continue;
			}
			const n = sc[st] != null ? Number(sc[st]) : 0;
			const slug = st.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "status";
			chips += `<button type="button" class="btn btn-xs btn-default mb-1 mr-1 tm2-ad-filter-chip" data-testid="tm2-ad-filter-chip-${esc(
				slug,
			)}" data-tm2-ad-filter="${esc(st)}">${esc(st)} (${n})</button>`;
		}

		const rows = Array.isArray(tab.rows) ? tab.rows : [];
		let listBody = "";
		let cardsHtml = "";
		for (let j = 0; j < rows.length; j += 1) {
			const row = rows[j] || {};
			const ac = String(row.addendum_code || j).trim();
			const sfx = String(row.row_test_suffix || j).replace(/[^a-z0-9_-]/gi, "-");
			const st = String(row.status || "").trim();
			const ack = row.requires_supplier_acknowledgement ? __("Yes") : __("No");
			listBody += `<tr data-testid="tm2-ad-list-row-${esc(sfx)}" data-tm2-ad-status="${esc(st)}">
				<td class="small font-weight-bold">${esc(ac)}<span class="text-muted"> #${esc(String(row.addendum_number != null ? row.addendum_number : ""))}</span></td>
				<td class="small">${esc(String(row.title || ""))}</td>
				<td class="small">${esc(st)}</td>
				<td class="small">${esc(String(row.primary_impact_type || ""))}</td>
				<td class="small">${esc(String(row.deadline_impact_display || ""))}</td>
				<td class="small">${esc(String(ack))}</td>
				<td class="small">${esc(String(row.impact_analysis_status || ""))}</td>
				<td class="small">${esc(String(row.approval_status || ""))}</td>
				<td class="small text-muted">${esc(String(row.issued_at_display || ""))}</td>
			</tr>`;

			const trans = Array.isArray(row.output_transitions) ? row.output_transitions : [];
			let transHtml = "";
			for (let t = 0; t < trans.length; t += 1) {
				const tr = trans[t] || {};
				const k = String(tr.output_key || t).replace(/[^a-z0-9_-]/gi, "-");
				transHtml += `<tr data-testid="tm2-ad-out-row-${esc(k)}">
					<td class="small">${esc(String(tr.output_label || ""))}</td>
					<td class="small" data-testid="tm2-ad-transition-${esc(k)}">${esc(String(tr.arrow_display || ""))}</td>
				</tr>`;
			}
			if (!transHtml) {
				transHtml = `<tr><td colspan="2" class="text-muted small">${esc(__("No output transition rows on impact record yet."))}</td></tr>`;
			}

			const plines = Array.isArray(row.impact_parameter_lines) ? row.impact_parameter_lines : [];
			let pHtml = "";
			for (let p = 0; p < plines.length; p += 1) {
				pHtml += `<li class="small">${esc(String(plines[p] || ""))}</li>`;
			}
			const blines = Array.isArray(row.impact_boq_lines) ? row.impact_boq_lines : [];
			let bHtml = "";
			for (let b = 0; b < blines.length; b += 1) {
				bHtml += `<li class="small">${esc(String(blines[b] || ""))}</li>`;
			}

			const srcClr = String(row.source_clarification_code || "").trim();
			const srcLine = srcClr
				? `<div class="small text-muted mb-1">${esc(__("Source clarification"))}: ${esc(srcClr)}</div>`
				: "";

			cardsHtml += `<div class="border rounded p-2 mb-3" data-testid="tm2-ad-card-${esc(sfx)}">
				<div class="small font-weight-bold mb-1">${esc(ac)} · ${esc(st)}</div>
				<div class="small mb-1">${esc(String(row.title || ""))}</div>
				<div class="small text-muted mb-1">${esc(__("Affects"))}: ${esc(String(row.affects_display || ""))}</div>
				<div class="small text-muted mb-2">${esc(__("Acknowledgement required"))}: ${esc(String(ack))}${
					row.bid_resubmission_required
						? ` · ${esc(__("Bid resubmission flagged on impact record"))}`
						: ""
				}</div>
				${srcLine}
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Reason"))}</div>
				<div class="small mb-2" data-testid="tm2-ad-reason-${esc(sfx)}">${esc(String(row.reason_preview || ""))}</div>
				${
					pHtml || bHtml
						? `<div class="small font-weight-bold text-muted mb-1">${esc(__("Impact analysis (excerpt)"))}</div>
					${pHtml ? `<ul class="mb-2 pl-3">${pHtml}</ul>` : ""}
					${
						bHtml
							? `<div class="small font-weight-bold text-muted mb-1">${esc(__("BOQ refs (excerpt)"))}</div><ul class="mb-2 pl-3">${bHtml}</ul>`
							: ""
					}`
						: ""
				}
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Regenerated outputs (previous → revised)"))}</div>
				<div class="table-responsive">
					<table class="table table-bordered table-sm mb-0">
						<thead><tr><th class="small">${esc(__("Output"))}</th><th class="small">${esc(__("Transition"))}</th></tr></thead>
						<tbody>${transHtml}</tbody>
					</table>
				</div>
			</div>`;
		}
		if (!listBody) {
			listBody = `<tr><td colspan="9" class="text-muted small">${esc(__("No addenda yet."))}</td></tr>`;
		}

		$p.html(
			`<div class="alert alert-light border small py-2 mb-3" data-testid="tm2-ad-readonly-notice">${notice}</div>
			<div class="mb-2" data-testid="tm2-ad-status-chips">${chips}</div>
			<div class="table-responsive mb-3" data-testid="tm2-ad-list-wrap">
				<table class="table table-bordered table-sm mb-0">
					<thead><tr>
						<th class="small">${esc(__("Addendum"))}</th>
						<th class="small">${esc(__("Title"))}</th>
						<th class="small">${esc(__("Status"))}</th>
						<th class="small">${esc(__("Primary impact"))}</th>
						<th class="small">${esc(__("Deadline impact"))}</th>
						<th class="small">${esc(__("Ack req."))}</th>
						<th class="small">${esc(__("Impact analysis"))}</th>
						<th class="small">${esc(__("Approval"))}</th>
						<th class="small">${esc(__("Issued"))}</th>
					</tr></thead>
					<tbody>${listBody}</tbody>
				</table>
			</div>
			<div data-testid="tm2-ad-detail-cards">${cardsHtml}</div>`,
		);

		$p.off("click.tm2adf").on("click.tm2adf", ".tm2-ad-filter-chip", function (ev) {
			ev.preventDefault();
			const f = ($(this).attr("data-tm2-ad-filter") || "").trim();
			const $rows = $p.find('[data-testid="tm2-ad-list-wrap"] tr[data-tm2-ad-status]');
			const $cards = $p.find("[data-testid^='tm2-ad-card-']");
			if (!f) {
				$rows.removeClass("d-none");
				$cards.removeClass("d-none");
				return;
			}
			$rows.each(function () {
				const st = ($(this).attr("data-tm2-ad-status") || "").trim();
				$(this).toggleClass("d-none", st !== f);
			});
			$cards.each(function () {
				const $c = $(this);
				const id = $c.attr("data-testid") || "";
				const suf = id.replace(/^tm2-ad-card-/, "");
				const matchRow = $p.find(`[data-testid="tm2-ad-list-row-${suf}"]`);
				const st = (matchRow.attr("data-tm2-ad-status") || "").trim();
				$c.toggleClass("d-none", st !== f);
			});
		});
	}

	function renderSubmissionsPanel($w) {
		const $p = $w.find('[data-testid="tm2-tab-panel-submissions"]');
		const msg = $w.data("tm2DetailPayload");
		if (!msg || !msg.ok) {
			$p.html(`<div class="text-muted small">${esc(__("Select a tender to see the Submissions tab."))}</div>`);
			return;
		}
		const tab = msg.submissions_tab || {};
		const notice = esc(String(tab.read_only_notice || ""));
		const sealed = String(tab.sealed_notice || "").trim();
		const boqN = String(tab.boq_rates_suppressed_notice || "").trim();
		const sum = tab.summary || {};
		const validN = sum.valid_sealed_submissions != null ? Number(sum.valid_sealed_submissions) : 0;
		const lateN = sum.late_attempts != null ? Number(sum.late_attempts) : 0;
		const wN = sum.withdrawn_submissions != null ? Number(sum.withdrawn_submissions) : 0;
		const showPrice = !!tab.post_opening_financials_allowed;

		let sealBlock = "";
		if (sealed) {
			sealBlock = `<div class="alert alert-info small py-2 mb-2" data-testid="tm2-sub-sealed-notice">${esc(sealed)}</div>`;
		}
		let boqBlock = "";
		if (boqN) {
			boqBlock = `<div class="text-muted small mb-2" data-testid="tm2-sub-boq-notice">${esc(boqN)}</div>`;
		}

		const order = Array.isArray(tab.status_filter_order) ? tab.status_filter_order : [];
		const sc = tab.status_counts && typeof tab.status_counts === "object" ? tab.status_counts : {};
		let chips = `<button type="button" class="btn btn-xs btn-default mb-1 mr-1 tm2-sub-filter-chip" data-testid="tm2-sub-filter-chip-all" data-tm2-sub-filter="">${esc(
			__("All"),
		)}</button>`;
		for (let i = 0; i < order.length; i += 1) {
			const st = String(order[i] || "").trim();
			if (!st) {
				continue;
			}
			const n = sc[st] != null ? Number(sc[st]) : 0;
			const slug = st.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "status";
			chips += `<button type="button" class="btn btn-xs btn-default mb-1 mr-1 tm2-sub-filter-chip" data-testid="tm2-sub-filter-chip-${esc(
				slug,
			)}" data-tm2-sub-filter="${esc(st)}">${esc(st)} (${n})</button>`;
		}

		const rows = Array.isArray(tab.rows) ? tab.rows : [];
		let body = "";
		const priceHead = showPrice ? `<th class="small">${esc(__("Total (metadata)"))}</th>` : "";
		for (let j = 0; j < rows.length; j += 1) {
			const row = rows[j] || {};
			const sfx = String(row.row_test_suffix || j).replace(/[^a-z0-9_-]/gi, "-");
			const st = String(row.bid_status || "").trim();
			const priceCell = showPrice
				? `<td class="small">${esc(String(row.total_submitted_price_display || "").trim())}${
						row.currency ? " " + esc(String(row.currency)) : ""
					}</td>`
				: "";
			body += `<tr data-testid="tm2-sub-row-${esc(sfx)}" data-tm2-sub-status="${esc(st)}">
				<td class="small">${esc(String(row.supplier_label || ""))}</td>
				<td class="small">${esc(st)}</td>
				<td class="small text-muted">${esc(String(row.submitted_at_display || ""))}</td>
				<td class="small text-muted">${esc(String(row.sealed_at_display || ""))}</td>
				<td class="small">${esc(String(row.receipt_code || ""))}</td>
				${priceCell}
			</tr>`;
		}
		if (!body) {
			const colspan = showPrice ? 6 : 5;
			body = `<tr><td colspan="${colspan}" class="text-muted small">${esc(__("No bid submissions yet."))}</td></tr>`;
		}

		$p.html(
			`<div class="alert alert-light border small py-2 mb-3" data-testid="tm2-sub-readonly-notice">${notice}</div>
			${sealBlock}
			${boqBlock}
			<div class="border rounded px-2 py-2 mb-3 bg-light" data-testid="tm2-sub-summary">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Submission summary"))}</div>
				<div class="small" data-testid="tm2-sub-summary-valid">${esc(__("Valid sealed submissions"))}: ${esc(String(validN))}</div>
				<div class="small" data-testid="tm2-sub-summary-late">${esc(__("Late attempts"))}: ${esc(String(lateN))}</div>
				<div class="small" data-testid="tm2-sub-summary-withdrawn">${esc(__("Withdrawn"))}: ${esc(String(wN))}</div>
			</div>
			<div class="mb-2" data-testid="tm2-sub-status-chips">${chips}</div>
			<div class="table-responsive" data-testid="tm2-sub-table-wrap">
				<table class="table table-bordered table-sm mb-0">
					<thead><tr>
						<th class="small">${esc(__("Supplier"))}</th>
						<th class="small">${esc(__("Status"))}</th>
						<th class="small">${esc(__("Submitted at"))}</th>
						<th class="small">${esc(__("Sealed at"))}</th>
						<th class="small">${esc(__("Receipt"))}</th>
						${priceHead}
					</tr></thead>
					<tbody>${body}</tbody>
				</table>
			</div>`,
		);

		$p.off("click.tm2subf").on("click.tm2subf", ".tm2-sub-filter-chip", function (ev) {
			ev.preventDefault();
			const f = ($(this).attr("data-tm2-sub-filter") || "").trim();
			const $rows = $p.find('[data-testid="tm2-sub-table-wrap"] tr[data-tm2-sub-status]');
			if (!f) {
				$rows.removeClass("d-none");
				return;
			}
			$rows.each(function () {
				const st = ($(this).attr("data-tm2-sub-status") || "").trim();
				$(this).toggleClass("d-none", st !== f);
			});
		});
	}

	function renderOpeningReadinessPanel($w) {
		const $p = $w.find('[data-testid="tm2-tab-panel-opening-readiness"]');
		const msg = $w.data("tm2DetailPayload");
		if (!msg || !msg.ok) {
			$p.html(`<div class="text-muted small">${esc(__("Select a tender to see the Opening Readiness tab."))}</div>`);
			return;
		}
		const tab = msg.opening_readiness_tab || {};
		const notice = esc(String(tab.read_only_notice || ""));
		const st = esc(String(tab.readiness_status || "").trim() || "—");
		const orr = esc(String(tab.opening_readiness_code || "").trim() || "—");
		const cls = esc(String(tab.closing_record_code || "").trim() || "—");
		const clsStat = esc(String(tab.closing_record_status || "").trim());
		const dom = esc(String(tab.dom_output_code || "").trim() || "—");
		const snap = esc(String(tab.publication_snapshot_code || "").trim() || "—");
		const tsi = esc(String(tab.tender_std_instance_code || "").trim() || "—");
		const validN = tab.valid_sealed_submissions_count != null ? Number(tab.valid_sealed_submissions_count) : 0;
		const sealedN = tab.sealed_submission_ref_count != null ? Number(tab.sealed_submission_ref_count) : validN;
		const oprec = esc(String(tab.opening_record_code || "").trim() || "—");
		const prepAt = esc(String(tab.prepared_at_display || "").trim());
		const accAt = esc(String(tab.accepted_by_opening_module_at_display || "").trim());
		const arith = String(tab.works_arithmetic_notice || "").trim();

		let arithBlock = "";
		if (arith) {
			arithBlock = `<div class="alert alert-warning small py-2 mb-2" data-testid="tm2-or-arithmetic-warning">${esc(arith)}</div>`;
		}

		const blockers = Array.isArray(tab.readiness_blockers) ? tab.readiness_blockers : [];
		let blkHtml = "";
		if (blockers.length) {
			let rows = "";
			for (let b = 0; b < blockers.length; b += 1) {
				const row = blockers[b] || {};
				rows += `<tr><td class="small">${esc(String(row.code || ""))}</td><td class="small">${esc(
					String(row.message || ""),
				)}</td></tr>`;
			}
			blkHtml = `<div class="mb-2" data-testid="tm2-or-blockers-wrap"><div class="small font-weight-bold text-muted mb-1">${esc(
				__("Readiness blockers"),
			)}</div><table class="table table-bordered table-sm mb-0"><thead><tr><th class="small">${esc(
				__("Code"),
			)}</th><th class="small">${esc(__("Message"))}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
		}

		const rules = Array.isArray(tab.opening_rules) ? tab.opening_rules : [];
		let rulesLi = "";
		for (let r = 0; r < rules.length; r += 1) {
			const rule = rules[r] || {};
			const ok = String(rule.status || "").trim() === "pass";
			const mark = ok ? "✓" : "…";
			const clsMark = ok ? "text-success" : "text-muted";
			rulesLi += `<li class="small mb-1"><span class="${clsMark} mr-1">${mark}</span>${esc(String(rule.label || ""))}</li>`;
		}

		const tact = tab.tab_actions || {};
		const prep = tact.prepare_opening_readiness || {};
		const send = tact.send_to_opening || {};
		const prepHint = esc(String(prep.user_message || "").trim());
		const sendHint = esc(String(send.user_message || "").trim());
		const prepDis = prep.allowed && prep.ui_state === "enabled" ? "" : "disabled";
		const sendDis = send.allowed && send.ui_state === "enabled" ? "" : "disabled";

		$p.html(
			`<div class="alert alert-light border small py-2 mb-3" data-testid="tm2-or-readonly-notice">${notice}</div>
			${arithBlock}
			<div class="border rounded px-2 py-2 mb-3 bg-light" data-testid="tm2-or-summary">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Handoff status"))}</div>
				<div class="small" data-testid="tm2-or-readiness-status">${st}</div>
				<div class="small mt-2"><span class="text-muted">${esc(__("Opening readiness"))}:</span> <span data-testid="tm2-or-orr-code">${orr}</span></div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Closing record"))}:</span> ${cls}${
				clsStat ? " · " + clsStat : ""
			}</div>
				<div class="small mt-1"><span class="text-muted">${esc(__("DOM"))}:</span> <span data-testid="tm2-or-dom-ref">${dom}</span></div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Publication snapshot"))}:</span> ${snap}</div>
				<div class="small mt-1"><span class="text-muted">${esc(__("STD instance"))}:</span> ${tsi}</div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Valid sealed submissions"))}:</span> ${esc(String(validN))}</div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Sealed submission refs"))}:</span> ${esc(String(sealedN))}</div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Opening record"))}:</span> ${oprec}</div>
				<div class="small mt-1 text-muted">${esc(__("Prepared at"))}: ${prepAt || "—"} · ${esc(__("Accepted by opening module"))}: ${
				accAt || "—"
			}</div>
			</div>
			${blkHtml}
			<div class="mb-2" data-testid="tm2-or-opening-rules-wrap">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Opening rules"))}</div>
				<ul class="list-unstyled mb-0" data-testid="tm2-or-opening-rules">${rulesLi}</ul>
			</div>
			<div class="d-flex flex-wrap gap-2 mb-2" data-testid="tm2-or-tab-actions">
				<button type="button" class="btn btn-xs btn-default" data-testid="tm2-or-action-prepare" ${prepDis} title="${prepHint}">${esc(
				__("Prepare Opening Readiness"),
			)}</button>
				<button type="button" class="btn btn-xs btn-primary" data-testid="tm2-or-action-send" ${sendDis} title="${sendHint}">${esc(
				__("Send to Opening"),
			)}</button>
			</div>`,
		);
	}

	function renderEvaluationHandoffPanel($w) {
		const $p = $w.find('[data-testid="tm2-tab-panel-evaluation-handoff"]');
		const msg = $w.data("tm2DetailPayload");
		if (!msg || !msg.ok) {
			$p.html(`<div class="text-muted small">${esc(__("Select a tender to see the Evaluation Handoff tab."))}</div>`);
			return;
		}
		const tab = msg.evaluation_handoff_tab || {};
		const notice = esc(String(tab.read_only_notice || ""));
		const demRo = esc(String(tab.dem_readonly_notice || ""));
		const crit = esc(String(tab.criteria_derived_notice || ""));
		const st = esc(String(tab.handoff_status || "").trim() || "—");
		const ehr = esc(String(tab.evaluation_handoff_code || "").trim() || "—");
		const opn = esc(String(tab.opening_record_code || "").trim() || "—");
		const dem = esc(String(tab.dem_output_code || "").trim() || "—");
		const dsm = esc(String(tab.dsm_output_code || "").trim() || "—");
		const bundle = esc(String(tab.bundle_output_code || "").trim() || "—");
		const snap = esc(String(tab.publication_snapshot_code || "").trim() || "—");
		const tsi = esc(String(tab.tender_std_instance_code || "").trim() || "—");
		const openedLine = esc(String(tab.opened_submissions_display || "").trim() || "—");
		const addendaLine = esc(String(tab.addenda_display || "").trim() || "—");
		const sentAt = esc(String(tab.sent_at_display || "").trim());
		const accAt = esc(String(tab.accepted_by_evaluation_at_display || "").trim());

		const openedRows = Array.isArray(tab.opened_submissions) ? tab.opened_submissions : [];
		let oRows = "";
		for (let i = 0; i < openedRows.length; i += 1) {
			const row = openedRows[i] || {};
			const sfx = String(row.row_test_suffix || i).replace(/[^a-z0-9_-]/gi, "-");
			oRows += `<tr data-testid="tm2-eh-opened-row-${esc(sfx)}"><td class="small">${esc(String(row.supplier_label || ""))}</td><td class="small text-muted">${esc(
				String(row.bid_code || ""),
			)}</td></tr>`;
		}
		if (!oRows) {
			oRows = `<tr><td colspan="2" class="text-muted small">${esc(__("No opened submissions listed yet."))}</td></tr>`;
		}

		const blockers = Array.isArray(tab.handoff_blockers) ? tab.handoff_blockers : [];
		let blkHtml = "";
		if (blockers.length) {
			let rows = "";
			for (let b = 0; b < blockers.length; b += 1) {
				const row = blockers[b] || {};
				rows += `<tr><td class="small">${esc(String(row.code || ""))}</td><td class="small">${esc(String(row.message || ""))}</td></tr>`;
			}
			blkHtml = `<div class="mb-2" data-testid="tm2-eh-blockers-wrap"><div class="small font-weight-bold text-muted mb-1">${esc(
				__("Handoff blockers"),
			)}</div><table class="table table-bordered table-sm mb-0"><thead><tr><th class="small">${esc(__("Code"))}</th><th class="small">${esc(
				__("Message"),
			)}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
		}

		const tact = tab.tab_actions || {};
		const prep = tact.prepare_evaluation_handoff || {};
		const send = tact.send_to_evaluation || {};
		const prepHint = esc(String(prep.user_message || "").trim());
		const sendHint = esc(String(send.user_message || "").trim());
		const prepDis = prep.allowed && prep.ui_state === "enabled" ? "" : "disabled";
		const sendDis = send.allowed && send.ui_state === "enabled" ? "" : "disabled";

		$p.html(
			`<div class="alert alert-light border small py-2 mb-2" data-testid="tm2-eh-readonly-notice">${notice}</div>
			<div class="alert alert-info small py-2 mb-2" data-testid="tm2-eh-dem-readonly-notice">${demRo}</div>
			<div class="alert alert-warning small py-2 mb-3" data-testid="tm2-eh-criteria-notice">${crit}</div>
			<div class="border rounded px-2 py-2 mb-3 bg-light" data-testid="tm2-eh-summary">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Handoff status"))}</div>
				<div class="small" data-testid="tm2-eh-handoff-status">${st}</div>
				<div class="small mt-2"><span class="text-muted">${esc(__("Evaluation handoff"))}:</span> <span data-testid="tm2-eh-code">${ehr}</span></div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Opening record"))}:</span> ${opn}</div>
				<div class="small mt-1"><span class="text-muted">${esc(__("DEM"))}:</span> <span data-testid="tm2-eh-dem-ref">${dem}</span></div>
				<div class="small mt-1"><span class="text-muted">${esc(__("DSM"))}:</span> <span data-testid="tm2-eh-dsm-ref">${dsm}</span></div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Bundle"))}:</span> ${bundle}</div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Publication snapshot"))}:</span> ${snap}</div>
				<div class="small mt-1"><span class="text-muted">${esc(__("STD instance"))}:</span> ${tsi}</div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Opened submissions"))}:</span> ${openedLine}</div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Addenda"))}:</span> ${addendaLine}</div>
				<div class="small mt-1 text-muted">${esc(__("Sent at"))}: ${sentAt || "—"} · ${esc(__("Accepted by evaluation"))}: ${accAt || "—"}</div>
			</div>
			${blkHtml}
			<div class="mb-2" data-testid="tm2-eh-opened-table-wrap">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Opened submission rows"))}</div>
				<div class="table-responsive">
					<table class="table table-bordered table-sm mb-0">
						<thead><tr><th class="small">${esc(__("Supplier"))}</th><th class="small">${esc(__("Bid code"))}</th></tr></thead>
						<tbody>${oRows}</tbody>
					</table>
				</div>
			</div>
			<div class="d-flex flex-wrap gap-2 mb-2" data-testid="tm2-eh-tab-actions">
				<button type="button" class="btn btn-xs btn-default" data-testid="tm2-eh-action-prepare" ${prepDis} title="${prepHint}">${esc(
				__("Prepare Evaluation Handoff"),
			)}</button>
				<button type="button" class="btn btn-xs btn-primary" data-testid="tm2-eh-action-send" ${sendDis} title="${sendHint}">${esc(
				__("Send to Evaluation"),
			)}</button>
			</div>`,
		);
	}

	function renderContractHandoffPanel($w) {
		const $p = $w.find('[data-testid="tm2-tab-panel-contract-handoff"]');
		const msg = $w.data("tm2DetailPayload");
		if (!msg || !msg.ok) {
			$p.html(`<div class="text-muted small">${esc(__("Select a tender to see the Contract Handoff tab."))}</div>`);
			return;
		}
		const tab = msg.contract_handoff_tab || {};
		const notice = esc(String(tab.read_only_notice || ""));
		const dcmRo = esc(String(tab.dcm_readonly_notice || ""));
		const termsRo = esc(String(tab.contract_terms_notice || ""));
		const worksVs = esc(String(tab.works_contract_value_source_notice || "").trim());
		const uncEdu = esc(String(tab.uncorrected_price_education_notice || "").trim());
		const st = esc(String(tab.handoff_status || "").trim() || "—");
		const chr = esc(String(tab.contract_handoff_code || "").trim() || "—");
		const awd = esc(String(tab.award_decision_code || "").trim() || "—");
		const supLbl = esc(String(tab.awarded_supplier_label || "").trim() || "—");
		const supCode = esc(String(tab.awarded_supplier_code || "").trim());
		const supLine = supCode ? `${supLbl} (${supCode})` : supLbl;
		const dcm = esc(String(tab.dcm_output_code || "").trim() || "—");
		const snap = esc(String(tab.publication_snapshot_code || "").trim() || "—");
		const tsi = esc(String(tab.tender_std_instance_code || "").trim() || "—");
		const priceLine = esc(String(tab.final_evaluated_price_display || "").trim() || "—");
		const boq = esc(String(tab.final_boq_reference || "").trim() || "—");
		const addendaLine = esc(String(tab.addenda_display || "").trim() || "—");
		const createdAt = esc(String(tab.created_at_display || "").trim());
		const accAt = esc(String(tab.accepted_by_contract_module_at_display || "").trim());

		const blockers = Array.isArray(tab.handoff_blockers) ? tab.handoff_blockers : [];
		let blkHtml = "";
		if (blockers.length) {
			let rows = "";
			for (let b = 0; b < blockers.length; b += 1) {
				const row = blockers[b] || {};
				rows += `<tr><td class="small">${esc(String(row.code || ""))}</td><td class="small">${esc(String(row.message || ""))}</td></tr>`;
			}
			blkHtml = `<div class="mb-2" data-testid="tm2-ch-blockers-wrap"><div class="small font-weight-bold text-muted mb-1">${esc(
				__("Handoff blockers"),
			)}</div><table class="table table-bordered table-sm mb-0"><thead><tr><th class="small">${esc(__("Code"))}</th><th class="small">${esc(
				__("Message"),
			)}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
		}

		const tact = tab.tab_actions || {};
		const createAct = tact.create_contract_handoff || {};
		const createHint = esc(String(createAct.user_message || "").trim());
		const createDis = createAct.allowed && createAct.ui_state === "enabled" ? "" : "disabled";

		let worksHtml = "";
		if (worksVs) {
			worksHtml = `<div class="alert alert-secondary small py-2 mb-2" data-testid="tm2-ch-works-value-notice">${worksVs}</div>`;
		}
		let uncHtml = "";
		if (uncEdu) {
			uncHtml = `<div class="alert alert-light border small py-2 mb-2" data-testid="tm2-ch-uncorrected-education">${uncEdu}</div>`;
		}

		$p.html(
			`<div class="alert alert-light border small py-2 mb-2" data-testid="tm2-ch-readonly-notice">${notice}</div>
			<div class="alert alert-info small py-2 mb-2" data-testid="tm2-ch-dcm-readonly-notice">${dcmRo}</div>
			<div class="alert alert-warning small py-2 mb-2" data-testid="tm2-ch-contract-terms-notice">${termsRo}</div>
			${worksHtml}
			${uncHtml}
			<div class="border rounded px-2 py-2 mb-3 bg-light" data-testid="tm2-ch-summary">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Handoff status"))}</div>
				<div class="small" data-testid="tm2-ch-handoff-status">${st}</div>
				<div class="small mt-2"><span class="text-muted">${esc(__("Contract handoff"))}:</span> <span data-testid="tm2-ch-code">${chr}</span></div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Award decision"))}:</span> ${awd}</div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Awarded supplier"))}:</span> ${supLine}</div>
				<div class="small mt-1"><span class="text-muted">${esc(__("DCM"))}:</span> <span data-testid="tm2-ch-dcm-ref">${dcm}</span></div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Publication snapshot"))}:</span> ${snap}</div>
				<div class="small mt-1"><span class="text-muted">${esc(__("STD instance"))}:</span> ${tsi}</div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Final evaluated price (contract basis)"))}:</span> <span data-testid="tm2-ch-final-price">${priceLine}</span></div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Final BOQ reference"))}:</span> ${boq}</div>
				<div class="small mt-1"><span class="text-muted">${esc(__("Addenda"))}:</span> ${addendaLine}</div>
				<div class="small mt-1 text-muted">${esc(__("Created"))}: ${createdAt || "—"} · ${esc(__("Accepted by contract"))}: ${accAt || "—"}</div>
			</div>
			${blkHtml}
			<div class="d-flex flex-wrap gap-2 mb-2" data-testid="tm2-ch-tab-actions">
				<button type="button" class="btn btn-xs btn-primary" data-testid="tm2-ch-action-create" ${createDis} title="${createHint}">${esc(
				__("Create Contract Handoff"),
			)}</button>
			</div>`,
		);
	}

	function syncHeaderEvidenceExport($w, msg) {
		const $btn = $w.find('[data-testid="tm2-action-evidence-export"]');
		if (!$btn.length) {
			return;
		}
		if (!msg || !msg.ok) {
			$btn.prop("disabled", true);
			$btn.attr("title", __("Select a tender to export evidence."));
			return;
		}
		const tab = msg.audit_evidence_tab || {};
		const ex = (tab.tab_actions || {}).export_tender_evidence || {};
		const hint = String(ex.user_message || ex.message || "").trim();
		if (ex.allowed && ex.ui_state === "enabled") {
			$btn.prop("disabled", false);
			$btn.attr("title", hint || __("Export tender evidence package (§13.3)."));
		} else {
			$btn.prop("disabled", true);
			$btn.attr("title", hint || __("Evidence export is not available for this tender."));
		}
	}

	function openEvidenceExportDialog($w) {
		const msg = $w.data("tm2DetailPayload") || {};
		if (!msg.ok) {
			frappe.show_alert({ message: __("Select a tender first."), indicator: "orange" });
			return;
		}
		const tab = msg.audit_evidence_tab || {};
		const ex = (tab.tab_actions || {}).export_tender_evidence || {};
		if (!ex.allowed || ex.ui_state !== "enabled") {
			frappe.msgprint({
				title: __("Evidence export"),
				message: esc(String(ex.user_message || ex.message || __("Export is not allowed."))),
				indicator: "orange",
			});
			return;
		}
		const tc = String(msg.tender_code || "").trim();
		const st = String(msg.tender_status || "").trim();
		const inclAllowed = !!tab.include_confidential_toggle_allowed;
		let chkHtml = "";
		if (inclAllowed) {
			chkHtml = `<div class="form-check mb-0"><label class="small mb-0"><input type="checkbox" class="tm2-evidence-inc-conf" data-testid="tm2-evidence-export-include-confidential" /> ${esc(
				__("Include confidential sealed-bid material (post-opening corridor only)."),
			)}</label></div>`;
		}
		const panel = `<div data-testid="tm2-evidence-export-panel" class="small">
			<p class="mb-2"><strong>${esc(__("Tender"))}:</strong> ${esc(tc)} · <strong>${esc(__("Status"))}:</strong> <span data-testid="tm2-evidence-export-status">${esc(
			st,
		)}</span></p>
			<p class="text-muted mb-2">${esc(
				__("Builds the §13.3 read-only evidence package. Denied-action rows match the Audit tab and the export sensitive slice."),
			)}</p>
			${chkHtml}
		</div>`;
		const d = new frappe.ui.Dialog({
			title: __("Export tender evidence"),
			fields: [{ fieldtype: "HTML", fieldname: "tm2_evidence_export_intro", label: "", options: panel }],
			primary_action_label: __("Export"),
			primary_action() {
				let inc = 0;
				if (inclAllowed && d.$wrapper.find(".tm2-evidence-inc-conf").prop("checked")) {
					inc = 1;
				}
				d.hide();
				runAuditEvidenceExport($w, { include_confidential: inc });
			},
		});
		d.set_secondary_action_label(__("Cancel"));
		d.set_secondary_action(function () {
			d.hide();
		});
		d.show();
	}

	function runAuditEvidenceExport($w, opts) {
		const tc = ($w.data("tm2SelectedTenderCode") || "").trim();
		if (!tc) {
			frappe.show_alert({ message: __("Select a tender first."), indicator: "orange" });
			return;
		}
		const inc = opts && opts.include_confidential ? 1 : 0;
		frappe.call({
			method: "kentender_procurement.tender_management.api.tm2_workbench.export_workbench_tender_evidence",
			args: { tender_code: tc, include_confidential: inc },
			callback(r) {
				const msg = r.message || {};
				if (!msg.ok) {
					frappe.msgprint({
						title: __("Evidence export"),
						message: esc(String(msg.message || __("Export failed."))),
						indicator: "red",
					});
					return;
				}
				let raw = "";
				try {
					raw = JSON.stringify(msg, null, 2);
				} catch (e2) {
					raw = String(msg);
				}
				const max = 120000;
				const clipped = raw.length > max ? raw.slice(0, max) + "\n…" : raw;
				const d = new frappe.ui.Dialog({
					title: __("Tender evidence export"),
					fields: [
						{
							fieldtype: "HTML",
							fieldname: "tm2_ev_html",
							options: `<pre class="small" style="max-height:24rem;overflow:auto;white-space:pre-wrap">${esc(clipped)}</pre>`,
						},
					],
					primary_action_label: __("Close"),
					primary_action() {
						d.hide();
					},
				});
				d.show();
			},
			error() {
				frappe.msgprint({ title: __("Evidence export"), message: __("Request failed."), indicator: "red" });
			},
		});
	}

	function renderAuditEvidencePanel($w) {
		const $p = $w.find('[data-testid="tm2-tab-panel-audit-evidence"]');
		const msg = $w.data("tm2DetailPayload");
		if (!msg || !msg.ok) {
			$p.html(`<div class="text-muted small">${esc(__("Select a tender to see the Audit & Evidence tab."))}</div>`);
			return;
		}
		const tab = msg.audit_evidence_tab || {};
		const notice = esc(String(tab.read_only_notice || ""));
		const expNotice = esc(String(tab.evidence_export_notice || ""));
		const lifecycle = Array.isArray(tab.lifecycle_events) ? tab.lifecycle_events : [];
		const sens = Array.isArray(tab.sensitive_denials) ? tab.sensitive_denials : [];

		let lifeRows = "";
		for (let i = 0; i < lifecycle.length; i += 1) {
			const row = lifecycle[i] || {};
			const sfx = String(row.row_test_suffix != null ? row.row_test_suffix : i).replace(/[^a-z0-9_-]/gi, "-");
			lifeRows += `<div class="small border-bottom py-1" data-testid="tm2-ae-lifecycle-row-${esc(sfx)}">${esc(String(row.display_line || ""))}</div>`;
		}
		if (!lifeRows) {
			lifeRows = `<div class="text-muted small" data-testid="tm2-ae-lifecycle-empty">${esc(__("No lifecycle audit rows yet."))}</div>`;
		}

		let deniedTable = "";
		if (sens.length) {
			let drows = "";
			for (let s = 0; s < sens.length; s += 1) {
				const row = sens[s] || {};
				const sfx = String(row.row_test_suffix != null ? row.row_test_suffix : s).replace(/[^a-z0-9_-]/gi, "-");
				const when = esc(String(row.occurred_at_display || ""));
				const actor = esc(String(row.actor_display || ""));
				const act = esc(String(row.action_guess || ""));
				const dc = esc(String(row.denial_code || row.event_type || ""));
				drows += `<tr data-testid="tm2-ae-denied-row-${esc(sfx)}"><td class="small">${when}</td><td class="small">${actor}</td><td class="small">${act}</td><td class="small">${dc}</td></tr>`;
			}
			deniedTable = `<table class="table table-bordered table-sm mb-0" data-testid="tm2-ae-denied-table"><thead><tr><th class="small">${esc(
				__("When"),
			)}</th><th class="small">${esc(__("Actor"))}</th><th class="small">${esc(__("Action"))}</th><th class="small">${esc(
				__("Denial / type"),
			)}</th></tr></thead><tbody>${drows}</tbody></table>`;
		} else {
			deniedTable = `<div class="text-muted small" data-testid="tm2-ae-sensitive-empty">${esc(__("No denied or sensitive audit rows yet."))}</div>`;
		}

		const tact = tab.tab_actions || {};
		const ex = tact.export_tender_evidence || {};
		const exHint = esc(String(ex.user_message || "").trim());
		const exDis = ex.allowed && ex.ui_state === "enabled" ? "" : "disabled";

		$p.html(
			`<div class="alert alert-light border small py-2 mb-2" data-testid="tm2-ae-readonly-notice">${notice}</div>
			<div class="alert alert-info small py-2 mb-3" data-testid="tm2-ae-export-notice">${expNotice}</div>
			<div class="mb-3" data-testid="tm2-ae-export-wrap">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Evidence export"))}</div>
				<button type="button" class="btn btn-xs btn-primary" data-testid="tm2-ae-action-export" ${exDis} title="${exHint}">${esc(
				__("Export Tender Evidence"),
			)}</button>
			</div>
			<div class="mb-3" data-testid="tm2-ae-lifecycle-wrap">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Lifecycle timeline"))}</div>
				${lifeRows}
			</div>
			<div class="mb-2" data-testid="tm2-ae-sensitive-wrap">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Denied / sensitive actions"))}</div>
				${deniedTable}
			</div>`,
		);
	}

	function renderOverviewPanel($w) {
		const $p = $w.find('[data-testid="tm2-tab-panel-overview"]');
		const msg = $w.data("tm2DetailPayload");
		if (!msg || !msg.ok || !msg.overview) {
			$p.html(`<div class="text-muted small">${esc(__("Select a tender to see the Overview tab."))}</div>`);
			return;
		}
		const ov = msg.overview;
		const ts = ov.tender_summary || {};
		const next = ov.current_required_action || {};
		const pl = ov.package_lineage || {};
		const cs = ov.current_state || {};
		const tl = ov.timeline || {};
		const std = ov.std_binding || {};
		const out = ov.output_refs || {};
		const snap = String(ov.publication_snapshot_code || "").trim();
		const counts = ov.tab_counts || {};
		const events = Array.isArray(ov.recent_audit_events) ? ov.recent_audit_events : [];

		let keyDatesHtml = "";
		const kds = Array.isArray(tl.key_dates) ? tl.key_dates : [];
		for (let i = 0; i < kds.length; i += 1) {
			const kd = kds[i];
			keyDatesHtml += `<div class="d-flex justify-content-between border-bottom py-1 small"><span class="text-muted">${esc(
				String(kd.label || ""),
			)}</span><span class="text-right">${esc(String(kd.value || ""))}</span></div>`;
		}
		if (!keyDatesHtml) {
			keyDatesHtml = `<div class="text-muted small">${esc(__("No timeline row yet."))}</div>`;
		}

		let outHtml = "";
		const outKeys = ["bundle_output_code", "dsm_output_code", "dom_output_code", "dem_output_code", "dcm_output_code"];
		const outLabels = {
			bundle_output_code: __("Bundle"),
			dsm_output_code: __("DSM"),
			dom_output_code: __("DOM"),
			dem_output_code: __("DEM"),
			dcm_output_code: __("DCM"),
		};
		for (let j = 0; j < outKeys.length; j += 1) {
			const k = outKeys[j];
			const v = String(out[k] || "").trim();
			if (v) {
				outHtml += `<div class="small"><strong>${esc(String(outLabels[k] || k))}:</strong> ${esc(v)}</div>`;
			}
		}
		if (!outHtml) {
			outHtml = `<div class="text-muted small">${esc(__("Output codes appear after STD binding generates artifacts."))}</div>`;
		}

		let evHtml = "";
		for (let e = 0; e < events.length; e += 1) {
			const row = events[e];
			evHtml += `<div class="small border-bottom py-1" data-testid="tm2-overview-event-row">${esc(String(row.display_line || ""))}</div>`;
		}
		if (!evHtml) {
			evHtml = `<div class="text-muted small">${esc(__("No audit events yet."))}</div>`;
		}

		const stdLine = [
			std.std_template_code ? `${esc(__("Template"))}: ${esc(String(std.std_template_code))}` : "",
			std.std_template_version_code ? `${esc(__("Version"))}: ${esc(String(std.std_template_version_code))}` : "",
			std.binding_status ? `${esc(__("Binding"))}: ${esc(String(std.binding_status))}` : "",
		]
			.filter(Boolean)
			.join(" · ");

		$p.html(
			`<div data-testid="tm2-overview-next-step" class="alert alert-info border mb-4 py-3 px-3">
				<div class="small font-weight-bold text-uppercase">${esc(__("Current next step"))}</div>
				<div class="h6 font-weight-bold mt-2 mb-1">${esc(String(next.headline || ""))}</div>
				<div class="small text-muted">${esc(String(next.reason || ""))}</div>
			</div>
			<div data-testid="tm2-overview-tender-summary" class="mb-3">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Tender summary"))}</div>
				<div class="small"><strong>${esc(String(ts.tender_code || ""))}</strong> — ${esc(String(ts.tender_title || ""))}</div>
				<div class="small text-muted">${esc(String(ts.procuring_entity_code || ""))} · ${esc(String(ts.procurement_method || ""))} · ${esc(
				String(ts.procurement_category || ""),
			)}</div>
				<div class="small">${esc(__("Package"))}: ${esc(String(ts.procurement_package_code || ""))} · ${esc(__("Visibility"))}: ${esc(
				String(ts.tender_visibility || ""),
			)}</div>
				<div class="small">${esc(__("Status"))}: ${esc(String(cs.status || ""))} · ${esc(__("STD readiness"))}: ${esc(
				String(cs.std_readiness_status || ""),
			)}</div>
			</div>
			<div data-testid="tm2-overview-package-lineage" class="mb-3">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Package lineage"))}</div>
				<div class="small">${esc(String(pl.lineage_display || ""))}</div>
				<div class="small text-muted">${esc(__("Package status"))}: ${esc(String(pl.package_status || __("—")))}</div>
			</div>
			<div data-testid="tm2-overview-key-dates" class="mb-3">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Key dates"))}</div>
				${keyDatesHtml}
			</div>
			<div data-testid="tm2-overview-tab-counts" class="mb-3 small">
				<span class="font-weight-bold text-muted">${esc(__("Related counts"))}:</span>
				${esc(__("Clarifications"))}: ${esc(String(counts.clarifications_open != null ? counts.clarifications_open : 0))} ·
				${esc(__("Addenda (non-terminal)"))}: ${esc(String(counts.addenda_non_terminal != null ? counts.addenda_non_terminal : 0))} ·
				${esc(__("Bid submissions"))}: ${esc(String(counts.bid_submissions != null ? counts.bid_submissions : 0))}
			</div>
			<div data-testid="tm2-overview-recent-events" class="mb-3">
				<div class="small font-weight-bold text-muted mb-1">${esc(__("Recent events"))}</div>
				${evHtml}
			</div>
			<details class="mb-2 border rounded tm2-overview-technical-wrap" data-testid="tm2-overview-technical-collapsed">
				<summary class="px-3 py-2 small font-weight-bold text-muted tm2-overview-technical-summary" data-testid="tm2-overview-technical-summary">${esc(__("Technical references (advanced)"))}</summary>
				<div class="px-3 pb-3 tm2-overview-technical-body" data-testid="tm2-overview-technical-body">
					<div data-testid="tm2-overview-std-line" class="mb-2">
						<div class="small font-weight-bold text-muted mb-1">${esc(__("STD & snapshot"))}</div>
						<div class="small">${stdLine || esc(__("No active binding summary."))}</div>
						<div class="small">${esc(__("Publication snapshot"))}: ${esc(snap || __("—"))}</div>
					</div>
					<div data-testid="tm2-overview-output-refs">${outHtml}</div>
				</div>
			</details>`,
		);
	}

	function loadTenderDetail($w, tenderCode) {
		const tc = String(tenderCode || "").trim();
		$w.data("tm2SelectedTenderCode", tc);
		const $h = $w.find('[data-testid="tm2-tender-detail-header"]');
		const $cards = $w.find('[data-testid="tm2-state-summary-cards"]');
		const $bar = $w.find('[data-testid="tm2-action-bar"]');
		const $blk = $w.find('[data-testid="tm2-blockers-panel"]');
		if (!tc) {
			$h.html(`<span class="text-muted small">${esc(__("Select a tender from the list."))}</span>`);
			$cards
				.removeClass("d-flex flex-wrap")
				.html(`<div class="text-muted small">${esc(__("No tender selected."))}</div>`);
			$bar.empty();
			$blk.html(`<span class="text-muted small">${esc(__("No tender selected."))}</span>`);
			$w.find('[data-testid="tm2-tab-panel-overview"]').empty().removeClass("d-none");
			$w.find('[data-testid="tm2-tab-panel-std-readiness"]').empty().addClass("d-none");
			$w.find('[data-testid="tm2-tab-panel-timeline"]').empty().addClass("d-none");
			$w.find('[data-testid="tm2-tab-panel-supplier-access"]').empty().addClass("d-none");
			$w.find('[data-testid="tm2-tab-panel-clarifications"]').empty().addClass("d-none");
			$w.find('[data-testid="tm2-tab-panel-addenda"]').empty().addClass("d-none");
			$w.find('[data-testid="tm2-tab-panel-submissions"]').empty().addClass("d-none");
			$w.find('[data-testid="tm2-tab-panel-opening-readiness"]').empty().addClass("d-none");
			$w.find('[data-testid="tm2-tab-panel-evaluation-handoff"]').empty().addClass("d-none");
			$w.find('[data-testid="tm2-tab-panel-contract-handoff"]').empty().addClass("d-none");
			$w.find('[data-testid="tm2-tab-panel-audit-evidence"]').empty().addClass("d-none");
			const $dt = $w.find('[data-testid="tm2-detail-tabs"]');
			$dt.find('[role="tab"]').removeClass("active").attr("aria-selected", "false");
			$dt.find('[data-testid="tm2-tab-overview"]').addClass("active").attr("aria-selected", "true");
			$w.removeData("tm2DetailPayload");
			renderOverviewPanel($w);
			syncHeaderEvidenceExport($w, null);
			return;
		}
		$h.html(`<div class="text-muted small">${esc(__("Loading…"))}</div>`);
		$cards.removeClass("d-flex flex-wrap").html(`<div class="text-muted small">${esc(__("Loading…"))}</div>`);
		$bar.html(`<div class="text-muted small">${esc(__("Loading…"))}</div>`);
		$blk.html("");
		frappe.call({
			method: "kentender_procurement.tender_management.api.tm2_workbench.get_workbench_tender_detail",
			args: { tender_code: tc },
			callback(r) {
				const msg = r.message || {};
				if (!msg.ok) {
					$h.html(`<div class="small text-danger" data-testid="tm2-tender-detail-error">${esc(
						msg.message || __("Could not load detail."),
					)}</div>`);
					$cards.removeClass("d-flex flex-wrap").empty();
					$bar.empty();
					$w.find('[data-testid="tm2-tab-panel-overview"]').html(
						`<div class="text-muted small">${esc(__("Overview unavailable until a tender loads."))}</div>`,
					);
					$w.find('[data-testid="tm2-tab-panel-std-readiness"]').empty().addClass("d-none");
					$w.find('[data-testid="tm2-tab-panel-timeline"]').empty().addClass("d-none");
					$w.find('[data-testid="tm2-tab-panel-supplier-access"]').empty().addClass("d-none");
					$w.find('[data-testid="tm2-tab-panel-clarifications"]').empty().addClass("d-none");
					$w.find('[data-testid="tm2-tab-panel-addenda"]').empty().addClass("d-none");
					$w.find('[data-testid="tm2-tab-panel-submissions"]').empty().addClass("d-none");
					$w.find('[data-testid="tm2-tab-panel-opening-readiness"]').empty().addClass("d-none");
					$w.find('[data-testid="tm2-tab-panel-evaluation-handoff"]').empty().addClass("d-none");
					$w.find('[data-testid="tm2-tab-panel-contract-handoff"]').empty().addClass("d-none");
					$w.find('[data-testid="tm2-tab-panel-audit-evidence"]').empty().addClass("d-none");
					$w.find('[data-testid="tm2-tab-panel-overview"]').removeClass("d-none");
					const $dte = $w.find('[data-testid="tm2-detail-tabs"]');
					$dte.find('[role="tab"]').removeClass("active").attr("aria-selected", "false");
					$dte.find('[data-testid="tm2-tab-overview"]').addClass("active").attr("aria-selected", "true");
					syncHeaderEvidenceExport($w, null);
					return;
				}
				$w.data("tm2DetailPayload", msg);
				renderDetailHeader($h, msg);
				renderStateSummaryCards($cards, msg);
				renderActionBar($w, $bar, msg);
				renderBlockersPanel($blk, msg);
				const $dts = $w.find('[data-testid="tm2-detail-tabs"]');
				$dts.find('[role="tab"]').removeClass("active").attr("aria-selected", "false");
				$dts.find('[data-testid="tm2-tab-overview"]').addClass("active").attr("aria-selected", "true");
				$w.find('[data-testid="tm2-tab-panel-overview"]').removeClass("d-none");
				$w.find('[data-testid="tm2-tab-panel-std-readiness"]').empty().addClass("d-none");
				$w.find('[data-testid="tm2-tab-panel-timeline"]').empty().addClass("d-none");
				$w.find('[data-testid="tm2-tab-panel-supplier-access"]').empty().addClass("d-none");
				$w.find('[data-testid="tm2-tab-panel-clarifications"]').empty().addClass("d-none");
				$w.find('[data-testid="tm2-tab-panel-addenda"]').empty().addClass("d-none");
				$w.find('[data-testid="tm2-tab-panel-submissions"]').empty().addClass("d-none");
				$w.find('[data-testid="tm2-tab-panel-opening-readiness"]').empty().addClass("d-none");
				$w.find('[data-testid="tm2-tab-panel-evaluation-handoff"]').empty().addClass("d-none");
				$w.find('[data-testid="tm2-tab-panel-contract-handoff"]').empty().addClass("d-none");
				$w.find('[data-testid="tm2-tab-panel-audit-evidence"]').empty().addClass("d-none");
				renderOverviewPanel($w);
				syncHeaderEvidenceExport($w, msg);
			},
			error() {
				$h.html(`<div class="small text-danger">${esc(__("Request failed."))}</div>`);
			},
		});
	}

	function renderDetailHeader($h, msg) {
		const lines = Array.isArray(msg.header_lines) ? msg.header_lines : [];
		let html = "";
		for (let i = 0; i < lines.length; i += 1) {
			const c = i === 0 ? "font-weight-bold" : "small text-muted";
			html += `<div class="${c}">${esc(String(lines[i] || ""))}</div>`;
		}
		$h.html(html || `<span class="text-muted small">${esc(__("No detail."))}</span>`);
	}

	function renderStateSummaryCards($cards, msg) {
		$cards.removeClass("d-flex flex-wrap").empty();
		const cards = Array.isArray(msg.state_cards) ? msg.state_cards : [];
		if (!cards.length) {
			$cards.append(`<span class="text-muted small">${esc(__("No summary."))}</span>`);
			return;
		}
		$cards.addClass("d-flex flex-wrap");
		for (let i = 0; i < cards.length; i += 1) {
			const c = cards[i];
			const id = esc(String(c.id || "card"));
			const title = esc(String(c.title || ""));
			const lines = Array.isArray(c.lines) ? c.lines : [];
			let body = "";
			for (let j = 0; j < lines.length; j += 1) {
				body += `<div class="small">${esc(String(lines[j] || ""))}</div>`;
			}
			$cards.append(
				`<div data-testid="tm2-state-card-${id}" class="border rounded px-2 py-1 mb-2 mr-2 bg-light" style="min-width:9rem;max-width:16rem;flex:1 1 9rem"><div class="small font-weight-bold text-muted">${title}</div>${body}</div>`,
			);
		}
	}

	function renderBlockersPanel($blk, msg) {
		const summary = String(msg.blocker_summary || "").trim();
		if (summary) {
			$blk.html(
				`<div class="small text-danger" data-testid="tm2-blockers-summary">${esc(summary)}</div><div class="small text-muted">${esc(
					__("Resolve readiness and governance checks before publication executes."),
				)}</div>`,
			);
		} else {
			$blk.html(`<div class="small text-muted" data-testid="tm2-blockers-summary">${esc(__("No tender-level blockers."))}</div>`);
		}
	}

	function renderActionBar($w, $bar, msg) {
		$bar.empty();
		const actions = Array.isArray(msg.actions) ? msg.actions : [];
		const tc = String(msg.tender_code || "").trim();
		for (let i = 0; i < actions.length; i += 1) {
			const a = actions[i];
			const code = String(a.action_code || "");
			const ui = String(a.ui_state || "disabled");
			const lab = esc(String(a.label || code));
			const av = a.availability || {};
			const hint = esc(String(av.user_message || av.message || ""));
			const dis = ui !== "enabled";
			const slug = code.toLowerCase().replace(/_/g, "-");
			const $btn = $(
				`<button type="button" class="btn btn-default btn-sm mb-1 mr-1 tm2-action-btn" data-tm2-action-code="${esc(
					code,
				)}" data-testid="tm2-action-${slug}" ${dis ? "disabled" : ""} title="${hint}">${lab}</button>`,
			);
			$bar.append($btn);
		}
		$bar.off("click.tm2act").on("click.tm2act", ".tm2-action-btn", function (e) {
			e.preventDefault();
			const $b = $(this);
			if ($b.prop("disabled")) {
				return;
			}
			const ac = $b.attr("data-tm2-action-code") || "";
			if (ac === "TND2_PUBLISH") {
				openTm2PublishLegalModal($w, tc);
				return;
			}
			if (ac === "TND2_VIEW") {
				const payload = $w.data("tm2DetailPayload") || {};
				const name = String(payload.tm2_tender || "").trim();
				if (name) {
					frappe.set_route("Form", "TM2 Tender", name);
				}
				return;
			}
			frappe.show_alert({
				message: __("Action") + ": " + String(ac) + " — " + __("not wired in workbench yet."),
				indicator: "orange",
			});
		});
	}

	function openTm2PublishLegalModal($w, tenderCode) {
		const payload = $w.data("tm2DetailPayload") || {};
		const tc = String(tenderCode || payload.tender_code || "").trim();
		if (!tc) {
			return;
		}
		frappe.call({
			method: "kentender_procurement.tender_management.api.tm2_workbench.get_workbench_tender_action_availability",
			args: { tender_code: tc, action_code: "TND2_PUBLISH" },
			callback(r) {
				const wrap = r.message || {};
				if (!wrap.ok) {
					frappe.msgprint(wrap.message || __("Could not verify publish availability."));
					return;
				}
				const avail = wrap.availability || {};
				if (!avail.allowed) {
					frappe.msgprint({
						title: __("Publish not available"),
						message: String(avail.user_message || avail.message || __("Not allowed.")),
						indicator: "orange",
					});
					return;
				}
				showTm2PublishModalDom($w, payload, avail);
			},
			error() {
				frappe.msgprint(__("Request failed."));
			},
		});
	}

	function showTm2PublishModalDom($w, payload, avail) {
		if (!frappe.ui || !frappe.ui.Dialog) {
			return;
		}
		const tc = String(payload.tender_code || "").trim();
		const title = String(payload.tender_title || "");
		const st = String(payload.tender_status || "");
		const target = String(payload.publish_target_status || __("Published"));
		const refs = Array.isArray(payload.impacted_publication_refs) ? payload.impacted_publication_refs : [];
		let refsHtml = `<p class="small font-weight-bold mb-1">${esc(__("This will publish:"))}</p><ul class="small mb-2">`;
		if (refs.length) {
			for (let i = 0; i < refs.length; i += 1) {
				refsHtml += `<li>${esc(String(refs[i]))}</li>`;
			}
		} else {
			refsHtml += `<li class="text-muted">${esc(__("Output references will be locked at publish time."))}</li>`;
		}
		refsHtml += "</ul>";
		const warnings = Array.isArray(avail.blockers) ? avail.blockers : [];
		let warnHtml = "";
		if (warnings.length) {
			warnHtml = `<div class="alert alert-warning small py-2 mb-2" data-testid="tm2-publish-warnings"><strong>${esc(
				__("Warnings"),
			)}</strong><ul class="mb-0 pl-3">`;
			for (let wj = 0; wj < warnings.length; wj += 1) {
				const b = warnings[wj] || {};
				warnHtml += `<li>${esc(String(b.required_action || b.blocker_code || ""))}</li>`;
			}
			warnHtml += "</ul></div>";
		}
		const reasonReq = !!avail.reason_required;
		const needConfirm = !!avail.confirmation_required;
		const audit = esc(String((payload.legal && payload.legal.audit_notice) || ""));
		const dlg = new frappe.ui.Dialog({
			title: __("Publish tender"),
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "legal_intro",
					options: "<div data-testid=\"tm2-publish-modal-body\"></div>",
				},
			],
		});
		dlg.$wrapper.attr("data-testid", "tm2-modal-tnd2_publish");
		const $body = dlg.$wrapper.find('[data-testid="tm2-publish-modal-body"]');
		let confirmHtml = "";
		if (needConfirm) {
			confirmHtml = `<div class="form-group mb-2" data-testid="tm2-publish-confirm-wrap">
				<div class="checkbox">
					<label><input type="checkbox" data-testid="tm2-publish-confirm-cb" />
						<span class="small">${esc(
							__(
								"I understand this will publish a legally binding tender and lock the approved tender artifacts.",
							),
						)}</span>
					</label>
				</div></div>`;
		}
		let reasonHtml = "";
		if (reasonReq) {
			reasonHtml = `<div class="form-group mb-2"><label class="small">${esc(__("Reason"))}</label>
				<textarea class="form-control" rows="2" data-testid="tm2-publish-reason"></textarea></div>`;
		}
		$body.html(
			`<div class="small mb-2"><strong>${esc(__("Tender"))}:</strong> ${esc(tc)} — ${esc(title)}</div>
			<div class="small mb-2"><strong>${esc(__("Current state"))}:</strong> ${esc(st)}</div>
			<div class="small mb-2"><strong>${esc(__("Target state"))}:</strong> ${esc(target)}</div>
			${refsHtml}
			${warnHtml}
			${reasonHtml}
			${confirmHtml}
			<div class="small text-muted mb-2" data-testid="tm2-publish-audit">${audit}</div>`,
		);
		dlg.set_primary_action(__("Publish"), function () {
			if (needConfirm) {
				const ok = dlg.$wrapper.find('[data-testid="tm2-publish-confirm-cb"]').prop("checked");
				if (!ok) {
					frappe.show_alert({ message: __("Please confirm."), indicator: "orange" });
					return;
				}
			}
			let reason = "";
			if (reasonReq) {
				reason = String(dlg.$wrapper.find('[data-testid="tm2-publish-reason"]').val() || "").trim();
				if (!reason) {
					frappe.show_alert({ message: __("A reason is required."), indicator: "orange" });
					return;
				}
			}
			dlg.disable_primary_action();
			frappe.call({
				method: "kentender_procurement.tender_management.api.tm2_workbench.execute_workbench_tender_publish",
				args: { tender_code: tc, reason: reason || "" },
				callback(r2) {
					dlg.enable_primary_action();
					const out = r2.message || {};
					if (!out.ok) {
						frappe.msgprint({
							title: __("Publish failed"),
							message: String(out.message || __("Request failed.")),
							indicator: "red",
						});
						return;
					}
					dlg.hide();
					frappe.show_alert({ message: __("Tender published."), indicator: "green" });
					refreshTenderList($w);
					loadTenderDetail($w, tc);
				},
				error() {
					dlg.enable_primary_action();
					frappe.msgprint(__("Request failed."));
				},
			});
		});
		dlg.set_secondary_action_label(__("Cancel"));
		dlg.set_secondary_action(function () {
			dlg.hide();
		});
		dlg.show();
	}

	function openNewTenderPackagePicker() {
		if (!frappe.ui || !frappe.ui.Dialog) {
			frappe.msgprint(__("Desk UI is not ready."));
			return;
		}
		const state = {
			step: 1,
			pkg: null,
			stdOptions: [],
			selOpt: null,
			created: null,
			busy: false,
			lastPackageRows: [],
		};

		const dlg = new frappe.ui.Dialog({
			title: __("New Tender"),
			size: "large",
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "picker_html",
					label: "",
					options: "<div></div>",
				},
			],
		});
		dlg.show();
		dlg.$wrapper.find(".modal-dialog .modal-content").first().attr("data-testid", "tm2-new-tender-wizard");

		function stepTitle(n) {
			return __("Step {0} of 6", [String(n)]);
		}

		function syncFooter() {
			dlg.footer.removeClass("hide");
			dlg.get_secondary_btn().removeClass("hide");
			if (state.step <= 1) {
				dlg.set_secondary_action_label(__("Cancel"));
				dlg.set_secondary_action(function () {
					dlg.hide();
				});
			} else if (state.step < 6) {
				dlg.set_secondary_action_label(__("Back"));
				dlg.set_secondary_action(function () {
					if (state.busy) {
						return;
					}
					state.step = Math.max(1, state.step - 1);
					render();
				});
			} else {
				dlg.set_secondary_action_label(__("Close"));
				dlg.set_secondary_action(function () {
					dlg.hide();
				});
			}
			if (state.step === 5) {
				dlg.set_primary_action(__("Create draft & bind STD"), function () {
					submitWizard();
				});
			} else if (state.step === 6) {
				dlg.set_primary_action(__("Open tender"), function () {
					openCreatedTender();
				});
			} else {
				dlg.set_primary_action(__("Next"), function () {
					advance();
				});
			}
		}

		function openCreatedTender() {
			const name = state.created && state.created.tm2_tender ? String(state.created.tm2_tender) : "";
			if (!name) {
				dlg.hide();
				return;
			}
			dlg.hide();
			frappe.set_route("Form", "TM2 Tender", name);
		}

		function submitWizard() {
			if (state.busy || !state.pkg || !state.selOpt) {
				return;
			}
			state.busy = true;
			render();
			frappe.call({
				method: "kentender_procurement.tender_management.api.tm2_workbench.complete_new_tender_wizard",
				args: {
					package_code: state.pkg.package_code,
					preferred_std_template: state.selOpt.std_template,
					std_template_version_code: state.selOpt.template_version_code,
					applicability_profile_code: state.selOpt.applicability_profile_code,
				},
				callback(r) {
					state.busy = false;
					const msg = r.message || {};
					if (!msg.ok) {
						frappe.msgprint({
							title: __("Could not create tender"),
							message: msg.message || __("Request failed."),
							indicator: "red",
						});
						render();
						return;
					}
					state.created = msg;
					state.step = 6;
					render();
				},
				error() {
					state.busy = false;
					frappe.msgprint(__("Request failed."));
					render();
				},
			});
		}

		function advance() {
			if (state.busy) {
				return;
			}
			if (state.step === 1) {
				if (!state.pkg || !state.pkg.selectable) {
					frappe.show_alert({ message: __("Select an eligible package."), indicator: "orange" });
					return;
				}
				state.step = 2;
				render();
				return;
			}
			if (state.step === 2) {
				state.step = 3;
				loadStdOptions();
				return;
			}
			if (state.step === 3) {
				if (!state.selOpt) {
					frappe.show_alert({ message: __("Select an STD template version."), indicator: "orange" });
					return;
				}
				state.step = 4;
				render();
				return;
			}
			if (state.step === 4) {
				state.step = 5;
				render();
				return;
			}
		}

		function loadStdOptions() {
			if (!state.pkg) {
				return;
			}
			state.busy = true;
			state.stdOptions = [];
			state.selOpt = null;
			render();
			frappe.call({
				method: "kentender_procurement.tender_management.api.tm2_workbench.list_new_tender_wizard_std_options",
				args: { package_code: state.pkg.package_code },
				callback(r) {
					state.busy = false;
					const msg = r.message || {};
					if (!msg.ok) {
						frappe.msgprint(msg.message || __("Could not load STD options."));
						state.step = 2;
						render();
						return;
					}
					state.stdOptions = msg.options || [];
					if (state.stdOptions.length === 1) {
						state.selOpt = state.stdOptions[0];
					}
					render();
				},
				error() {
					state.busy = false;
					frappe.msgprint(__("Could not load STD options."));
					state.step = 2;
					render();
				},
			});
		}

		function reqList(pr) {
			if (!pr || typeof pr !== "object") {
				return "";
			}
			const labels = {
				boq: __("Bill of Quantities (BOQ)"),
				drawings: __("Drawings"),
				site_information: __("Site information"),
				key_personnel: __("Key personnel"),
				equipment: __("Equipment"),
				hse: __("HSE"),
				environmental_and_social: __("Environmental & Social (E&S)"),
			};
			let html = "<ul class=\"mb-0 small\">";
			for (const k in labels) {
				if (Object.prototype.hasOwnProperty.call(labels, k) && pr[k]) {
					html += `<li>${esc(labels[k])}</li>`;
				}
			}
			html += "</ul>";
			return html;
		}

		function render() {
			const $w2 = dlg.fields_dict.picker_html && dlg.fields_dict.picker_html.$wrapper;
			if (!$w2 || !$w2.length) {
				return;
			}
			let inner = "";
			if (state.step === 1) {
				inner = `
					<div data-testid="tm2-wizard-step-1">
						<p class="text-muted small mb-2" data-testid="tm2-wizard-step-label">${esc(stepTitle(1))}</p>
						<p class="small mb-2">${esc(__("Select a procurement package. Only eligible packages can proceed."))}</p>
						<div class="form-group mb-2">
							<label class="small text-muted">${esc(__("Search package code or title"))}</label>
							<input type="search" class="form-control form-control-sm" data-testid="tm2-package-picker-search" placeholder="${esc(
								__("Package code, title…"),
							)}" />
						</div>
						<div data-testid="tm2-package-picker-table" class="tm2-package-picker-table text-muted small">${esc(__("Loading…"))}</div>
					</div>`;
			} else if (state.step === 2) {
				const p = state.pkg || {};
				const wz = p.requires_std_wizard_choice
					? `<div class="alert alert-info small py-2 mb-2" data-testid="tm2-wizard-std-choice-hint">${esc(
							__(
								"This package requires you to choose an STD template version and applicability profile in the following steps.",
							),
						)}</div>`
					: "";
				inner = `
					<div data-testid="tm2-wizard-step-2">
						<p class="text-muted small mb-2" data-testid="tm2-wizard-step-label">${esc(stepTitle(2))}</p>
						${wz}
						<div class="border rounded p-2 mb-2 bg-light small">
							<div class="font-weight-bold">${esc(String(p.package_code || ""))}</div>
							<div class="text-muted">${esc(String(p.package_name || ""))}</div>
							<div>${esc(__("Status"))}: ${esc(String(p.status || ""))}</div>
						</div>
						<p class="small mb-0">${esc(
							__(
								"Confirm that planning data, budget, and procurement method are correct before creating a governed tender.",
							),
						)}</p>
					</div>`;
			} else if (state.step === 3) {
				if (state.busy && !state.stdOptions.length) {
					inner = `<div data-testid="tm2-wizard-step-3"><p class="text-muted small">${esc(__("Loading STD options…"))}</p></div>`;
				} else if (!state.stdOptions.length) {
					inner = `<div data-testid="tm2-wizard-step-3"><p class="text-danger small">${esc(
						__("No active compatible STD versions are available for this package."),
					)}</p></div>`;
				} else {
					let rows = "";
					for (let i = 0; i < state.stdOptions.length; i += 1) {
						const o = state.stdOptions[i];
						const sel =
							state.selOpt && state.selOpt.std_template === o.std_template ? " border-primary bg-light" : "";
						const tname = esc(String(o.template_name || o.template_code || ""));
						const ver = esc(String(o.template_version_code || ""));
						const tc = esc(String(o.template_code || ""));
						const st = esc(String(o.lifecycle_status || ""));
						const nm = esc(String(o.std_template || ""));
						rows += `<div class="tm2-wizard-std-option border rounded p-2 mb-2${sel}" data-testid="tm2-wizard-std-option" data-std-template="${nm}" style="cursor:pointer">
							<div class="font-weight-bold small">${tname}</div>
							<div class="small text-muted">${esc(__("Version"))}: ${ver}</div>
							<div class="small text-muted">${esc(__("Template code"))}: ${tc}</div>
							<div class="small">${esc(__("Lifecycle"))}: ${st}</div>
						</div>`;
					}
					inner = `
						<div data-testid="tm2-wizard-step-3">
							<p class="text-muted small mb-2" data-testid="tm2-wizard-step-label">${esc(stepTitle(3))}</p>
							<p class="small mb-2">${esc(__("Choose the STD template version to govern this tender (doc 9 §15.4)."))}</p>
							${rows}
						</div>`;
				}
			} else if (state.step === 4 && state.selOpt) {
				const o = state.selOpt;
				inner = `
					<div data-testid="tm2-wizard-step-4">
						<p class="text-muted small mb-2" data-testid="tm2-wizard-step-label">${esc(stepTitle(4))}</p>
						<p class="small mb-2">${esc(__("Applicability profile and activated requirements for this template (doc 9 §15.5)."))}</p>
						<div class="border rounded p-2 mb-2 bg-light small">
							<div><strong>${esc(__("Profile code"))}:</strong> ${esc(String(o.applicability_profile_code || ""))}</div>
							<div><strong>${esc(__("Version"))}:</strong> ${esc(String(o.template_version_code || ""))}</div>
						</div>
						<div class="small font-weight-bold mb-1">${esc(__("Activated requirements"))}</div>
						<div data-testid="tm2-wizard-profile-requirements">${reqList(o.profile_requirements)}</div>
					</div>`;
			} else if (state.step === 5 && state.selOpt && state.pkg) {
				const o = state.selOpt;
				const p = state.pkg;
				inner = `
					<div data-testid="tm2-wizard-step-5">
						<p class="text-muted small mb-2" data-testid="tm2-wizard-step-label">${esc(stepTitle(5))}</p>
						<p class="small mb-2">${esc(
							__(
								"Create a draft TM2 tender for this package and bind the selected STD instance. You can complete STD parameters after creation.",
							),
						)}</p>
						<ul class="small mb-0">
							<li>${esc(String(p.package_code || ""))} — ${esc(String(p.package_name || ""))}</li>
							<li>${esc(String(o.template_name || o.template_code || ""))} (${esc(String(o.template_version_code || ""))})</li>
							<li>${esc(__("Profile"))}: ${esc(String(o.applicability_profile_code || ""))}</li>
						</ul>
						${
							state.busy
								? `<p class="text-muted small mt-2 mb-0" data-testid="tm2-wizard-submit-busy">${esc(__("Creating…"))}</p>`
								: ""
						}
					</div>`;
			} else if (state.step === 6 && state.created) {
				const tc = esc(String(state.created.tender_code || ""));
				const si = esc(String(state.created.tender_std_instance || ""));
				inner = `
					<div data-testid="tm2-wizard-step-6">
						<p class="text-muted small mb-2" data-testid="tm2-wizard-step-label">${esc(stepTitle(6))}</p>
						<p class="small mb-2">${esc(
							__(
								"Tender draft created and STD instance bound. Open the tender form to complete STD readiness and publication steps.",
							),
						)}</p>
						<div class="border rounded p-2 bg-light small">
							<div data-testid="tm2-wizard-result-tender-code"><strong>${esc(__("Tender code"))}:</strong> ${tc}</div>
							<div data-testid="tm2-wizard-result-std-instance"><strong>${esc(__("STD instance"))}:</strong> ${si}</div>
						</div>
					</div>`;
			} else {
				inner = `<div class="text-muted small">${esc(__("Wizard state incomplete."))}</div>`;
			}
			$w2.html(`<div data-testid="tm2-package-picker" class="tm2-package-picker">${inner}</div>`);
			syncFooter();

			if (state.step === 1) {
				const $search = $w2.find('[data-testid="tm2-package-picker-search"]');
				const $tb = $w2.find('[data-testid="tm2-package-picker-table"]');
				let searchTimer = null;
				function loadRows() {
					const q = ($search.val() || "").trim();
					$tb.html(`<span class="text-muted">${esc(__("Loading…"))}</span>`);
					frappe.call({
						method: "kentender_procurement.tender_management.api.tm2_workbench.list_packages_for_new_tender",
						args: { search: q, limit: 50 },
						callback(r2) {
							const msg2 = r2.message || {};
							if (!msg2.ok) {
								$tb.html(`<span class="text-danger">${esc(msg2.message || __("Could not load packages."))}</span>`);
								state.lastPackageRows = [];
								return;
							}
							const rows = msg2.packages || [];
							state.lastPackageRows = rows;
							if (!rows.length) {
								$tb.html(`<span class="text-muted">${esc(__("No matching packages."))}</span>`);
								return;
							}
							$tb.empty();
							for (let j = 0; j < rows.length; j += 1) {
								const p2 = rows[j];
								const code = esc(String(p2.package_code || ""));
								const title = esc(String(p2.package_name || ""));
								const st2 = esc(String(p2.status || ""));
								const sel2 = !!p2.selectable;
								const wChoice = !!p2.requires_std_wizard_choice;
								const badge = sel2
									? wChoice
										? `<span class="badge badge-info">${esc(__("Eligible — choose STD"))}</span>`
										: `<span class="badge badge-success">${esc(__("Eligible"))}</span>`
									: `<span class="badge badge-secondary">${esc(__("Not eligible"))}</span>`;
								const hint = sel2
									? ""
									: `<div class="small text-muted mt-1">${esc(String(p2.user_message || p2.denial_code || ""))}</div>`;
								const selected =
									state.pkg && String(state.pkg.package_code) === String(p2.package_code) ? " border-primary bg-light" : "";
								const $row2 = $(
									`<div class="tm2-package-picker-row border-bottom py-2${selected}" data-testid="tm2-package-picker-row" data-package-code="${code}">
										<div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
											<div>
												<div class="font-weight-bold">${code}</div>
												<div class="small text-muted">${title}</div>
												<div class="small">${esc(__("Status"))}: ${st2}</div>
											</div>
											<div class="text-right">${badge}</div>
										</div>
										${hint}
									</div>`,
								);
								$tb.append($row2);
							}
						},
						error() {
							state.lastPackageRows = [];
							$tb.html(`<span class="text-danger">${esc(__("Request failed."))}</span>`);
						},
					});
				}
				loadRows();
				$search.off("input.kt2wiz").on("input.kt2wiz", function () {
					if (searchTimer) {
						clearTimeout(searchTimer);
					}
					searchTimer = setTimeout(loadRows, 350);
				});
				$tb.off("click.kt2pk").on("click.kt2pk", '[data-testid="tm2-package-picker-row"]', function (e) {
					e.preventDefault();
					const $row = $(this);
					const codeRaw = ($row.attr("data-package-code") || "").trim();
					let picked = null;
					for (let k = 0; k < state.lastPackageRows.length; k += 1) {
						if (String(state.lastPackageRows[k].package_code || "").trim() === codeRaw) {
							picked = state.lastPackageRows[k];
							break;
						}
					}
					if (!picked || !picked.selectable) {
						return;
					}
					state.pkg = picked;
					$tb.find(".tm2-package-picker-row").removeClass("border-primary bg-light");
					$row.addClass("border-primary bg-light");
				});
			}

			if (state.step === 3 && state.stdOptions.length && !state.busy) {
				$w2.off("click.kt2std").on("click.kt2std", '[data-testid="tm2-wizard-std-option"]', function (e) {
					e.preventDefault();
					const nm = $(this).attr("data-std-template") || "";
					let op = null;
					for (let i = 0; i < state.stdOptions.length; i += 1) {
						if (String(state.stdOptions[i].std_template) === nm) {
							op = state.stdOptions[i];
							break;
						}
					}
					if (!op) {
						return;
					}
					state.selOpt = op;
					$w2.find('[data-testid="tm2-wizard-std-option"]').removeClass("border-primary bg-light");
					$(this).addClass("border-primary bg-light");
				});
			}
		}

		dlg.$wrapper.one("shown.bs.modal.ktwiz", function () {
			render();
		});
		dlg.show();
		setTimeout(function () {
			render();
		}, 0);
	}

	function mountShell() {
		const el = frappe.pages["tender-management-v2"];
		if (!el) {
			return false;
		}
		const $w = $(el);
		if ($w.data("kt_tm2_layout_v") === LAYOUT_VERSION) {
			initTm2WorkbenchQueueAndKpis($w);
			return true;
		}
		$w.empty();

		const title = __("Tender Management");
		const blurb = __(
			"Create, publish, amend, close, and hand off STD-governed tenders.",
		);
		const layoutNote = __(
			"Workbench shell (P9-01–P9-02). New Tender wizard (P9-07). KPI + queue (P9-04–P9-05). Tender list (P9-06). Detail + action bar + publish modal (P9-08). Overview tab (P9-09). STD & Readiness tab (P9-10). Timeline tab (P9-11). Supplier Access tab (P9-12). Clarifications tab (P9-13). Addenda tab (P9-14). Submissions tab (P9-15). Opening Readiness tab (P9-16). Evaluation Handoff tab (P9-17). Contract Handoff tab (P9-18). Audit & Evidence tab (P9-19). Evidence export panel + denied-actions table (P9-21a).",
		);

		const kpi = [
			["tm2-kpi-draft", __("Draft"), "draft"],
			["tm2-kpi-std-incomplete", __("STD Incomplete"), "std-incomplete"],
			["tm2-kpi-publication-review", __("Publication Review"), "ready-review"],
			["tm2-kpi-published", __("Published"), "published"],
			["tm2-kpi-closing-soon", __("Closing Soon"), "closing-soon"],
			["tm2-kpi-clarifications", __("Clarifications Pending"), "clarifications"],
			["tm2-kpi-addenda", __("Addenda Pending"), "addenda"],
			["tm2-kpi-opening-ready", __("Opening Ready"), "opening-ready"],
		];

		const scopes = [
			["tm2-scope-my-work", __("My Work")],
			["tm2-scope-all", __("All")],
			["tm2-scope-drafts", __("Drafts")],
			["tm2-scope-published", __("Published")],
			["tm2-scope-closing-soon", __("Closing Soon")],
			["tm2-scope-opening-ready", __("Opening Ready")],
		];

		let kpiHtml = "";
		for (let i = 0; i < kpi.length; i += 1) {
			const tid = kpi[i][0];
			const lab = kpi[i][1];
			const kslug = kpi[i][2];
			kpiHtml += `<button type="button" class="btn btn-default btn-sm mb-1 mr-1 tm2-kpi-chip" data-testid="${tid}" data-tm2-queue-slug="${kslug}" title="${esc(
				lab,
			)}">${esc(lab)}</button>`;
		}

		let scopeHtml = "";
		for (let j = 0; j < scopes.length; j += 1) {
			const sid = scopes[j][0];
			const slab = scopes[j][1];
			scopeHtml += `<button type="button" class="btn btn-default btn-sm mb-1 mr-1" data-testid="${sid}" disabled title="${esc(
				slab,
			)}">${esc(slab)}</button>`;
		}

		const detailTabs = [
			["tm2-tab-overview", __("Overview")],
			["tm2-tab-std-readiness", __("STD & Readiness")],
			["tm2-tab-timeline", __("Timeline")],
			["tm2-tab-supplier-access", __("Supplier Access")],
			["tm2-tab-clarifications", __("Clarifications")],
			["tm2-tab-addenda", __("Addenda")],
			["tm2-tab-submissions", __("Submissions")],
			["tm2-tab-opening-readiness", __("Opening Readiness")],
			["tm2-tab-evaluation-handoff", __("Evaluation Handoff")],
			["tm2-tab-contract-handoff", __("Contract Handoff")],
			["tm2-tab-audit-evidence", __("Audit & Evidence")],
		];
		let detailTabsHtml = "";
		for (let t = 0; t < detailTabs.length; t += 1) {
			const tid = detailTabs[t][0];
			const tlab = detailTabs[t][1];
			const isOv = tid === "tm2-tab-overview";
			const enabledTab =
				tid === "tm2-tab-overview" ||
				tid === "tm2-tab-std-readiness" ||
				tid === "tm2-tab-timeline" ||
				tid === "tm2-tab-supplier-access" ||
				tid === "tm2-tab-clarifications" ||
				tid === "tm2-tab-addenda" ||
				tid === "tm2-tab-submissions" ||
				tid === "tm2-tab-opening-readiness" ||
				tid === "tm2-tab-evaluation-handoff" ||
				tid === "tm2-tab-contract-handoff" ||
				tid === "tm2-tab-audit-evidence";
			const disAttr = enabledTab ? "" : "disabled";
			const activeCls = isOv ? " active" : "";
			const ariaSel = isOv ? "true" : "false";
			detailTabsHtml += `<li class="nav-item" role="none">
				<button type="button" class="nav-link btn btn-link text-left px-2 py-1 small text-nowrap${activeCls}" role="tab" aria-selected="${ariaSel}" data-testid="${tid}" ${disAttr} title="${esc(
					tlab,
				)}">${esc(tlab)}</button>
			</li>`;
		}

		let queueHtml = "";
		for (let q = 0; q < QUEUE_ROWS.length; q += 1) {
			const qid = QUEUE_ROWS[q][0];
			const qlab = QUEUE_ROWS[q][1];
			const qslug = QUEUE_ROWS[q][2];
			queueHtml += `<button type="button" class="btn btn-link btn-sm p-1 mr-2 text-nowrap tm2-queue-chip" data-testid="${qid}" data-tm2-queue-slug="${qslug}">${esc(
				qlab,
			)}</button>`;
		}

		$w.append(
			`<div class="layout-main-section-wrapper">
				<div class="layout-main-section">
					<div data-testid="tm2-workbench-page" class="tm2-workbench-page">
						<div class="page-head pb-3 border-bottom mb-3">
							<div class="d-flex flex-wrap justify-content-between align-items-start gap-2">
								<div class="title-area flex-grow-1">
									<h1 class="page-title mb-1" data-testid="tm2-page-title">${esc(title)}</h1>
									<p class="text-muted small mb-0">${esc(blurb)}</p>
								</div>
								<div class="btn-group flex-shrink-0" role="group" aria-label="${esc(__("Workbench actions"))}">
									<button type="button" class="btn btn-default btn-sm" data-testid="tm2-action-my-actions" disabled title="${esc(
										__("Filters to your action items (P9-04+)."),
									)}">${esc(__("My Actions"))}</button>
									<button type="button" class="btn btn-default btn-sm" data-testid="tm2-action-evidence-export" disabled title="${esc(
										__("Select a tender to export evidence."),
									)}">${esc(__("Evidence Export"))}</button>
									<button type="button" class="btn btn-primary btn-sm" data-testid="tm2-action-new-tender" title="${esc(
										__("Choose a procurement package (not a free-form tender)."),
									)}">${esc(__("New Tender"))}</button>
								</div>
							</div>
						</div>

						<p class="text-muted small mb-3">${esc(layoutNote)}</p>

						<div data-testid="tm2-kpi-strip" class="tm2-kpi-strip border rounded px-2 py-2 mb-3 bg-light">
							<div class="small text-muted mb-1">${esc(__("KPI strip"))}</div>
							<div class="d-flex flex-wrap align-items-center">${kpiHtml}</div>
						</div>

						<div data-testid="tm2-scope-tabs" class="tm2-scope-tabs border-bottom pb-2 mb-3">
							<div class="small text-muted mb-1">${esc(__("Scope"))}</div>
							<div class="d-flex flex-wrap">${scopeHtml}</div>
						</div>

						<div data-testid="tm2-queue-bar" class="tm2-queue-bar border-bottom pb-2 mb-3">
							<div class="small text-muted mb-1">${esc(__("Queues"))}</div>
							<div class="d-flex flex-wrap align-items-center">${queueHtml}</div>
						</div>

						<div class="row g-2 mb-3">
							<div class="col-md-8">
								<label class="small text-muted mb-1 d-block">${esc(__("Search"))}</label>
								<input type="search" class="form-control form-control-sm" data-testid="tm2-search-input" placeholder="${esc(
									__("Tender code, title, package, supplier…"),
								)}" />
							</div>
							<div class="col-md-4">
								<label class="small text-muted mb-1 d-block">${esc(__("Filters"))}</label>
								<div data-testid="tm2-filter-panel" class="tm2-filter-panel border rounded px-2 py-2 bg-white text-muted small">${esc(
									__("Filter panel (P9-08+)."),
								)}</div>
							</div>
						</div>

						<div class="row">
							<div class="col-md-4 pr-md-2 mb-3 mb-md-0">
								<div data-testid="tm2-tender-list" class="tm2-tender-list border rounded p-3 bg-white" style="min-height: 10rem">
									<div class="small text-muted font-weight-bold mb-2">${esc(__("Tender list"))}</div>
									<div data-testid="tm2-tender-list-filter" class="tm2-tender-list-filter small text-muted mb-2"></div>
									<div data-testid="tm2-tender-list-rows" class="tm2-tender-list-rows"></div>
								</div>
							</div>
							<div class="col-md-8 pl-md-2">
								<div data-testid="tm2-tender-detail" class="tm2-tender-detail border rounded p-3 bg-white">
									<div class="small text-muted font-weight-bold mb-2">${esc(__("Tender detail"))}</div>
									<div data-testid="tm2-tender-detail-header" class="tm2-tender-detail-header border-bottom pb-2 mb-2">
										<span class="text-muted small">${esc(__("Select a tender from the list."))}</span>
									</div>
									<div data-testid="tm2-state-summary-cards" class="tm2-state-summary-cards mb-3">
										<span class="text-muted small">${esc(__("No tender selected."))}</span>
									</div>
									<div data-testid="tm2-action-bar" class="tm2-action-bar border-bottom pb-2 mb-2"></div>
									<div data-testid="tm2-blockers-panel" class="tm2-blockers-panel mb-2">
										<span class="text-muted small">${esc(__("No tender selected."))}</span>
									</div>
									<div class="tm2-detail-tabs-wrap">
										<div class="small text-muted mb-1">${esc(__("Detail tabs"))}</div>
										<ul class="nav nav-tabs flex-nowrap flex-md-wrap border-bottom-0" role="tablist" data-testid="tm2-detail-tabs" style="overflow-x:auto">
											${detailTabsHtml}
										</ul>
										<div data-testid="tm2-tab-panels" class="tm2-tab-panels mt-2 pt-2 border-top">
											<div data-testid="tm2-tab-panel-overview" class="tm2-tab-panel-overview"></div>
											<div data-testid="tm2-tab-panel-std-readiness" class="tm2-tab-panel-std-readiness d-none"></div>
											<div data-testid="tm2-tab-panel-timeline" class="tm2-tab-panel-timeline d-none"></div>
											<div data-testid="tm2-tab-panel-supplier-access" class="tm2-tab-panel-supplier-access d-none"></div>
											<div data-testid="tm2-tab-panel-clarifications" class="tm2-tab-panel-clarifications d-none"></div>
											<div data-testid="tm2-tab-panel-addenda" class="tm2-tab-panel-addenda d-none"></div>
											<div data-testid="tm2-tab-panel-submissions" class="tm2-tab-panel-submissions d-none"></div>
											<div data-testid="tm2-tab-panel-opening-readiness" class="tm2-tab-panel-opening-readiness d-none"></div>
											<div data-testid="tm2-tab-panel-evaluation-handoff" class="tm2-tab-panel-evaluation-handoff d-none"></div>
											<div data-testid="tm2-tab-panel-contract-handoff" class="tm2-tab-panel-contract-handoff d-none"></div>
											<div data-testid="tm2-tab-panel-audit-evidence" class="tm2-tab-panel-audit-evidence d-none"></div>
										</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>`,
		);

		$w.off("click.kt2nt").on("click.kt2nt", '[data-testid="tm2-action-new-tender"]', function (e) {
			e.preventDefault();
			openNewTenderPackagePicker();
		});

		initTm2WorkbenchQueueAndKpis($w);

		$w.data("kt_tm2_layout_v", LAYOUT_VERSION);
		return true;
	}

	function scheduleBoot() {
		if (!is_tm2_route()) {
			return;
		}
		if (mountShell()) {
			return;
		}
		let n = 0;
		const max = 60;
		const t = setInterval(function () {
			n += 1;
			const r2 = frappe.get_route() || [];
			if (r2[0] !== "tender-management-v2") {
				clearInterval(t);
				return;
			}
			if (mountShell()) {
				clearInterval(t);
			} else if (n >= max) {
				clearInterval(t);
			}
		}, 50);
	}

	$(document).on("page-change", scheduleBoot);
	if (frappe.router && frappe.router.on) {
		frappe.router.on("change", scheduleBoot);
	}
	scheduleBoot();
})();
