/**
 * P2-008 — Shared PP3 planning evidence drawer.
 */
(function () {
	frappe.provide("kentender_procurement");

	const EVIDENCE_API =
		"kentender_procurement.procurement_planning.api.evidence_view_model.get_pp_evidence_view_model";
	const REQUIRED_TESTID_LITERALS = [
		'data-testid="pp3-evidence-drawer"',
		'data-testid="pp3-evidence-title"',
		'data-testid="pp3-evidence-timeline"',
		'data-testid="pp3-evidence-record-list"',
		'data-testid="pp3-technical-details-toggle"',
		'data-testid="pp3-technical-details-panel"',
		'data-testid="pp3-technical-details-code"',
	];
	if (!REQUIRED_TESTID_LITERALS.length) {
		/* static literals preserved for G2 selector guard */
	}

	let rootEl = null;
	let escapeHandler = null;
	let loadToken = 0;

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function toTimelineLabels(timeline) {
		const rows = Array.isArray(timeline) ? timeline : [];
		const out = [];
		for (let i = 0; i < rows.length; i += 1) {
			const row = rows[i] || {};
			const label = String(row.label || row || "").trim();
			if (label) out.push(label);
		}
		return out;
	}

	function toRecordLabels(records) {
		const rows = Array.isArray(records) ? records : [];
		const out = [];
		for (let i = 0; i < rows.length; i += 1) {
			const row = rows[i] || {};
			const label = String(row.label || row || "").trim();
			if (label) out.push(label);
		}
		return out;
	}

	function timelineHtml(labels) {
		const list = Array.isArray(labels) ? labels : [];
		if (!list.length) {
			return '<p class="text-muted small mb-0">' + esc(__("No timeline events available.")) + "</p>";
		}
		let rows = "";
		for (let i = 0; i < list.length; i += 1) {
			rows +=
				'<li class="pp2-evidence-drawer__timeline-item">' +
				'<span class="pp2-evidence-drawer__timeline-mark" aria-hidden="true">✓</span> ' +
				esc(list[i]) +
				"</li>";
		}
		return '<ul class="pp2-evidence-drawer__timeline-list mb-0 ps-0">' + rows + "</ul>";
	}

	function recordsHtml(labels) {
		const list = Array.isArray(labels) ? labels : [];
		if (!list.length) {
			return '<p class="text-muted small mb-0">' + esc(__("No evidence records are available for this item.")) + "</p>";
		}
		let rows = "";
		for (let i = 0; i < list.length; i += 1) {
			rows += '<li class="pp2-evidence-drawer__record-item">' + esc(list[i]) + "</li>";
		}
		return rows;
	}

	function technicalHtml(technical) {
		const details = technical || {};
		const mayView = !!details.may_view_technical;
		if (!mayView) return "";
		const codes = Array.isArray(details.codes) ? details.codes : [];
		const fields = Array.isArray(details.fields) ? details.fields : [];
		let codeRows = "";
		for (let i = 0; i < codes.length; i += 1) {
			const code = String(codes[i] || "").trim();
			if (!code) continue;
			codeRows +=
				'<div class="pp2-evidence-drawer__technical-row" data-testid="pp3-technical-details-code">' +
				esc(code) +
				"</div>";
		}
		let fieldRows = "";
		for (let j = 0; j < fields.length; j += 1) {
			const field = fields[j] || {};
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
		const body =
			codeRows || fieldRows
				? codeRows + fieldRows
				: '<p class="text-muted small mb-0">' +
					esc(__("No technical details are available for this item.")) +
					"</p>";
		return (
			'<section class="pp2-evidence-drawer__section pp2-evidence-drawer__section--technical">' +
			'<details class="pp2-evidence-drawer__technical">' +
			'<summary class="pp2-evidence-drawer__technical-toggle" data-testid="pp3-technical-details-toggle">' +
			esc(__("Technical Details")) +
			"</summary>" +
			'<div class="pp2-evidence-drawer__technical-panel" data-testid="pp3-technical-details-panel">' +
			body +
			"</div>" +
			"</details>" +
			"</section>"
		);
	}

	function html(opts) {
		const o = opts || {};
		const title = String(o.title || __("Evidence")).trim() || __("Evidence");
		const timeline = toTimelineLabels(o.timeline);
		const records = toRecordLabels(o.records);
		return (
			'<div class="pp2-evidence-drawer pp3-evidence-drawer" data-testid="pp3-evidence-drawer" data-open="1">' +
			'<div class="pp2-evidence-drawer__backdrop" data-testid="pp3-evidence-drawer-backdrop"></div>' +
			'<aside class="pp2-evidence-drawer__panel" role="dialog" aria-modal="true" aria-label="' +
			esc(__("Evidence")) +
			'">' +
			'<header class="pp2-evidence-drawer__header">' +
			'<h2 class="h6 pp2-evidence-drawer__title mb-0" data-testid="pp3-evidence-title">' +
			esc(title) +
			"</h2>" +
			'<button type="button" class="btn btn-default btn-sm pp2-evidence-drawer__close" data-testid="pp3-evidence-drawer-close" aria-label="' +
			esc(__("Close")) +
			'">' +
			esc(__("Close")) +
			"</button>" +
			"</header>" +
			'<section class="pp2-evidence-drawer__section">' +
			'<h3 class="pp2-evidence-drawer__section-title small text-muted mb-2">' +
			esc(__("Timeline")) +
			"</h3>" +
			'<div data-testid="pp3-evidence-timeline">' +
			timelineHtml(timeline) +
			"</div>" +
			"</section>" +
			'<section class="pp2-evidence-drawer__section">' +
			'<h3 class="pp2-evidence-drawer__section-title small text-muted mb-2">' +
			esc(__("Records")) +
			"</h3>" +
			'<ul class="pp2-evidence-drawer__record-list mb-0 ps-3" data-testid="pp3-evidence-record-list">' +
			recordsHtml(records) +
			"</ul>" +
			"</section>" +
			technicalHtml(o.technical_details || {}) +
			"</aside>" +
			"</div>"
		);
	}

	function render(host, opts) {
		if (!host || host.nodeType !== 1) return;
		host.innerHTML = html(opts || {});
	}

	function ensureRoot() {
		return rootEl && rootEl.isConnected ? rootEl : null;
	}

	function isOpen() {
		return !!ensureRoot();
	}

	function unbindEscape() {
		if (escapeHandler) {
			document.removeEventListener("keydown", escapeHandler, true);
			escapeHandler = null;
		}
	}

	function close() {
		unbindEscape();
		if (rootEl && rootEl.parentNode) {
			rootEl.parentNode.removeChild(rootEl);
		}
		rootEl = null;
		document.body.classList.remove("pp2-evidence-drawer-open");
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
		const closeBtn = host.querySelector('[data-testid="pp3-evidence-drawer-close"]');
		const backdrop = host.querySelector('[data-testid="pp3-evidence-drawer-backdrop"]');
		if (closeBtn && closeBtn.getAttribute("data-bound") !== "1") {
			closeBtn.setAttribute("data-bound", "1");
			closeBtn.addEventListener("click", function (event) {
				if (event && typeof event.preventDefault === "function") event.preventDefault();
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

	function update(opts) {
		const root = ensureRoot();
		if (!root) return;
		const parent = root.parentNode;
		if (!parent) return;
		const wrapper = document.createElement("div");
		wrapper.innerHTML = html(opts || {});
		const nextRoot = wrapper.firstElementChild;
		if (!nextRoot) return;
		parent.replaceChild(nextRoot, root);
		rootEl = nextRoot;
		bindActions(rootEl);
	}

	function fetchEvidence(packageCode, token) {
		return new Promise(function (resolve) {
			frappe.call({
				method: EVIDENCE_API,
				args: { package_code: String(packageCode || "").trim() },
				callback: function (response) {
					if (token !== loadToken) return;
					resolve((response && response.message) || {});
				},
				error: function () {
					if (token !== loadToken) return;
					resolve({ ok: false });
				},
			});
		});
	}

	function inferPackageCode(opts) {
		const o = opts || {};
		const explicit = String(o.package_code || o.packageCode || "").trim();
		if (explicit) return explicit;
		const type = String(o.underlying_object_type || o.underlyingObjectType || "").trim().toLowerCase();
		const code = String(o.underlying_object_code || o.underlyingObjectCode || "").trim();
		if (!code) return "";
		if (type === "procurement_package") return code;
		if (/^PKG[-:]/i.test(code)) return code;
		return "";
	}

	function open(opts) {
		close();
		const o = opts || {};
		loadToken += 1;
		const token = loadToken;
		const wrapper = document.createElement("div");
		wrapper.innerHTML = html({
			title: String(o.title || __("Evidence")).trim(),
			timeline: [__("Loading evidence...")],
			records: [],
			technical_details: { may_view_technical: false },
		});
		rootEl = wrapper.firstElementChild;
		if (!rootEl) return;
		document.body.appendChild(rootEl);
		document.body.classList.add("pp2-evidence-drawer-open");
		bindActions(rootEl);
		bindEscape();
		const closeBtn = rootEl.querySelector('[data-testid="pp3-evidence-drawer-close"]');
		if (closeBtn && typeof closeBtn.focus === "function") closeBtn.focus();

		const packageCode = inferPackageCode(o);
		if (!packageCode) {
			update({
				title: String(o.title || __("Evidence")).trim(),
				timeline: [],
				records: [],
				technical_details: { may_view_technical: false },
			});
			return;
		}
		fetchEvidence(packageCode, token).then(function (payload) {
			if (token !== loadToken || !isOpen()) return;
			if (!payload || !payload.ok) {
				update({
					title: String(o.title || __("Evidence")).trim(),
					timeline: [],
					records: [],
					technical_details: { may_view_technical: false },
				});
				return;
			}
			update({
				title: String(payload.title || o.title || __("Evidence")).trim(),
				timeline: payload.timeline,
				records: payload.records,
				technical_details: payload.technical_details || {},
			});
		});
	}

	kentender_procurement.PlanningWorkbenchEvidenceDrawer = {
		html: html,
		render: render,
		open: open,
		close: close,
		isOpen: isOpen,
		ensureRoot: ensureRoot,
	};
})();
