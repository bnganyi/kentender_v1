/**
 * P5B-008 / P5B-009 — Shared Planning evidence drawer (on-demand shell + technical details).
 */
(function () {
	frappe.provide("kentender_procurement");

	const TECHNICAL_ROLES = {
		Auditor: true,
		"Planning Authority": true,
		Administrator: true,
		"System Manager": true,
	};

	const DEFAULT_TIMELINE = [
		__("Demand approved"),
		__("Demand included in procurement plan"),
		__("Package prepared"),
		__("Readiness passed"),
		__("Package released to Tender Management"),
		__("Tender Management consumed package"),
	];

	const DEFAULT_RECORDS = [
		__("Demand Approval Certificate"),
		__("Planning Inclusion Record"),
		__("Planning Release Package"),
		__("Tender Consumption Record"),
		__("Readiness Result"),
		__("Review Decision"),
	];

	const DEFAULT_TECHNICAL = {
		codes: [
			"PLANINCL-MOH-2026-001",
			"PKGREL-MOH-2026-001",
			"PKGCONSUME-MOH-2026-001",
			"PKG-MOH-2026-001",
			"TND-MOH-2026-001",
		],
		fields: [
			{ key: "source_object_code", value: "DEM-MOH-2026-001" },
			{ key: "target_object_code", value: "PKG-MOH-2026-001" },
			{ key: "locked_summary_json", value: '{"package_code":"PKG-MOH-2026-001"}' },
			{ key: "passed_forward_summary_json", value: '{"release_code":"PKGREL-MOH-2026-001"}' },
			{ key: "technical_refs_json", value: '{"inclusion":"PLANINCL-MOH-2026-001"}' },
			{ key: "audit_event_ref", value: "AUD-PP2-MOH-2026-001" },
		],
	};

	let rootEl = null;
	let escapeHandler = null;

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function resolveMayViewTechnical(opts) {
		if (opts && typeof opts.may_view_technical === "boolean") {
			return opts.may_view_technical;
		}
		try {
			const roles = (frappe.boot && frappe.boot.user && frappe.boot.user.roles) || [];
			for (let i = 0; i < roles.length; i += 1) {
				if (TECHNICAL_ROLES[roles[i]]) return true;
			}
		} catch (e) {
			/* ignore */
		}
		return false;
	}

	function normalizeTechnical(technical) {
		if (!technical || typeof technical !== "object") {
			return {
				codes: DEFAULT_TECHNICAL.codes.slice(),
				fields: DEFAULT_TECHNICAL.fields.map(function (row) {
					return { key: row.key, value: row.value };
				}),
			};
		}
		const codes =
			Array.isArray(technical.codes) && technical.codes.length
				? technical.codes.slice()
				: DEFAULT_TECHNICAL.codes.slice();
		const fields =
			Array.isArray(technical.fields) && technical.fields.length
				? technical.fields.map(function (row) {
						return {
							key: String((row && row.key) || "").trim(),
							value: String((row && row.value) || "").trim(),
						};
					})
				: DEFAULT_TECHNICAL.fields.map(function (row) {
						return { key: row.key, value: row.value };
					});
		return { codes: codes, fields: fields };
	}

	function defaultFixture(opts) {
		const o = opts || {};
		return {
			title: String(o.title || __("Evidence")).trim() || __("Evidence"),
			timeline: Array.isArray(o.timeline) && o.timeline.length ? o.timeline.slice() : DEFAULT_TIMELINE.slice(),
			records: Array.isArray(o.records) && o.records.length ? o.records.slice() : DEFAULT_RECORDS.slice(),
			technical: normalizeTechnical(o.technical),
			may_view_technical: resolveMayViewTechnical(o),
		};
	}

	function timelineHtml(steps) {
		const list = Array.isArray(steps) ? steps : [];
		if (!list.length) {
			return (
				'<p class="text-muted small mb-0">' + esc(__("No timeline events available.")) + "</p>"
			);
		}
		let items = "";
		for (let i = 0; i < list.length; i += 1) {
			const label = String(list[i] || "").trim();
			if (!label) continue;
			items +=
				'<li class="pp2-evidence-drawer__timeline-item">' +
				'<span class="pp2-evidence-drawer__timeline-mark" aria-hidden="true">✓</span> ' +
				esc(label) +
				"</li>";
		}
		return '<ul class="pp2-evidence-drawer__timeline-list mb-0 ps-0">' + items + "</ul>";
	}

	function recordsHtml(records) {
		const list = Array.isArray(records) ? records : [];
		if (!list.length) {
			return (
				'<p class="text-muted small mb-0">' + esc(__("No evidence records available.")) + "</p>"
			);
		}
		let items = "";
		for (let i = 0; i < list.length; i += 1) {
			const label = String(list[i] || "").trim();
			if (!label) continue;
			items +=
				'<li class="pp2-evidence-drawer__record-item">' + esc(label) + "</li>";
		}
		return items;
	}

	function technicalDetailsHtml(technical, mayViewTechnical) {
		if (!mayViewTechnical) return "";
		const data = normalizeTechnical(technical);
		let codeRows = "";
		for (let i = 0; i < data.codes.length; i += 1) {
			const code = String(data.codes[i] || "").trim();
			if (!code) continue;
			codeRows +=
				'<div class="pp2-evidence-drawer__technical-row" data-testid="pp2-technical-details-code">' +
				esc(code) +
				"</div>";
		}
		let fieldRows = "";
		for (let j = 0; j < data.fields.length; j += 1) {
			const field = data.fields[j] || {};
			const key = String(field.key || "").trim();
			if (!key) continue;
			const value = String(field.value || "").trim();
			fieldRows +=
				'<div class="pp2-evidence-drawer__technical-row">' +
				'<span class="pp2-evidence-drawer__technical-key">' +
				esc(key) +
				"</span>" +
				(value
					? '<span class="pp2-evidence-drawer__technical-value">' + esc(value) + "</span>"
					: "") +
				"</div>";
		}
		return (
			'<section class="pp2-evidence-drawer__section pp2-evidence-drawer__section--technical">' +
			'<details class="pp2-evidence-drawer__technical">' +
			'<summary class="pp2-evidence-drawer__technical-toggle" data-testid="pp2-technical-details-toggle">' +
			esc(__("Technical Details")) +
			"</summary>" +
			'<div class="pp2-evidence-drawer__technical-panel" data-testid="pp2-technical-details-panel">' +
			codeRows +
			fieldRows +
			"</div>" +
			"</details>" +
			"</section>"
		);
	}

	function html(opts) {
		const fixture = defaultFixture(opts);
		return (
			'<div class="pp2-evidence-drawer" data-testid="pp2-evidence-drawer" data-open="1">' +
			'<div class="pp2-evidence-drawer__backdrop" data-testid="pp2-evidence-drawer-backdrop"></div>' +
			'<aside class="pp2-evidence-drawer__panel" role="dialog" aria-modal="true" aria-label="' +
			esc(__("Evidence")) +
			'">' +
			'<header class="pp2-evidence-drawer__header">' +
			'<h2 class="h6 pp2-evidence-drawer__title mb-0" data-testid="pp2-evidence-title">' +
			esc(fixture.title) +
			"</h2>" +
			'<button type="button" class="btn btn-default btn-sm pp2-evidence-drawer__close"' +
			' data-testid="pp2-evidence-drawer-close" aria-label="' +
			esc(__("Close")) +
			'">' +
			esc(__("Close")) +
			"</button>" +
			"</header>" +
			'<section class="pp2-evidence-drawer__section">' +
			'<h3 class="pp2-evidence-drawer__section-title small text-muted mb-2">' +
			esc(__("Timeline")) +
			"</h3>" +
			'<div data-testid="pp2-evidence-timeline">' +
			timelineHtml(fixture.timeline) +
			"</div>" +
			"</section>" +
			'<section class="pp2-evidence-drawer__section">' +
			'<h3 class="pp2-evidence-drawer__section-title small text-muted mb-2">' +
			esc(__("Records")) +
			"</h3>" +
			'<ul class="pp2-evidence-drawer__record-list mb-0 ps-3" data-testid="pp2-evidence-record-list">' +
			recordsHtml(fixture.records) +
			"</ul>" +
			"</section>" +
			technicalDetailsHtml(fixture.technical, fixture.may_view_technical) +
			"</aside>" +
			"</div>"
		);
	}

	function unbindEscape() {
		if (escapeHandler) {
			document.removeEventListener("keydown", escapeHandler, true);
			escapeHandler = null;
		}
	}

	function bindEscape() {
		unbindEscape();
		escapeHandler = function (event) {
			if (!event || event.key !== "Escape") return;
			close();
		};
		document.addEventListener("keydown", escapeHandler, true);
	}

	function bindActions(host) {
		if (!host) return;
		const closeBtn = host.querySelector('[data-testid="pp2-evidence-drawer-close"]');
		const backdrop = host.querySelector('[data-testid="pp2-evidence-drawer-backdrop"]');
		if (closeBtn && closeBtn.getAttribute("data-bound") !== "1") {
			closeBtn.setAttribute("data-bound", "1");
			closeBtn.addEventListener("click", function (event) {
				if (event && typeof event.preventDefault === "function") {
					event.preventDefault();
				}
				close();
			});
		}
		if (backdrop && backdrop.getAttribute("data-bound") !== "1") {
			backdrop.setAttribute("data-bound", "1");
			backdrop.addEventListener("click", function () {
				close();
			});
		}
	}

	function ensureRoot() {
		return rootEl && rootEl.isConnected ? rootEl : null;
	}

	function isOpen() {
		return !!ensureRoot();
	}

	function close() {
		unbindEscape();
		if (rootEl && rootEl.parentNode) {
			rootEl.parentNode.removeChild(rootEl);
		}
		rootEl = null;
		document.body.classList.remove("pp2-evidence-drawer-open");
	}

	function open(opts) {
		close();
		const markup = html(opts || {});
		const wrapper = document.createElement("div");
		wrapper.innerHTML = markup;
		rootEl = wrapper.firstElementChild;
		if (!rootEl) return;
		document.body.appendChild(rootEl);
		document.body.classList.add("pp2-evidence-drawer-open");
		bindActions(rootEl);
		bindEscape();
		const closeBtn = rootEl.querySelector('[data-testid="pp2-evidence-drawer-close"]');
		if (closeBtn && typeof closeBtn.focus === "function") {
			closeBtn.focus();
		}
	}

	kentender_procurement.PlanningEvidenceDrawer = {
		TECHNICAL_ROLES: TECHNICAL_ROLES,
		DEFAULT_TIMELINE: DEFAULT_TIMELINE,
		DEFAULT_RECORDS: DEFAULT_RECORDS,
		DEFAULT_TECHNICAL: DEFAULT_TECHNICAL,
		resolveMayViewTechnical: resolveMayViewTechnical,
		defaultFixture: defaultFixture,
		html: html,
		open: open,
		close: close,
		isOpen: isOpen,
		ensureRoot: ensureRoot,
	};
})();
