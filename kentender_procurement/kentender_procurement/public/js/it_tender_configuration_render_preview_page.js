// WF-03 — Tender Document Preview + Publication Handoff (WG-03; WG-04 merged).
// Route contract: /desk/it-tender-configuration-render-preview/<configuration_id>
// Retired WG-04 route publication-readiness rewrites to render-preview.
(function () {
	"use strict";

	var SURFACE_ID = "WF-03";
	var PAGE_SLUG = "it-tender-configuration-render-preview";
	var RETIRED_SLUG = "it-tender-configuration-publication-readiness";
	var GET_API = "kentender_procurement.tender_configurations.get_tender_configuration_document_preview";
	var GENERATE_API = "kentender_procurement.tender_configurations.generate_tender_configuration_document_preview";
	var CONFIRM_API = "kentender_procurement.tender_configurations.confirm_tender_configuration_document_preview";
	var RETURN_API = "kentender_procurement.tender_configurations.return_tender_configuration_preview_for_correction";
	var SEND_API = "kentender_procurement.tender_configurations.send_tender_configuration_to_publication_workflow";
	var PDF_API = "kentender_procurement.tender_configurations.download_tender_configuration_document_preview_pdf";
	var STORAGE_KEY = "kt_cl_wf03_configuration_id";
	var BACK_ROUTE = "it-tender-configuration-overview";
	var READINESS_ROUTE = "it-tender-configuration-validation-report";
	var MODAL_HOST_ID = "kt-cl-wf03-modal-host";
	var CFG_STEPS = [
		{ value: "", label: "—" },
		{ value: "CFG-01", label: "CFG-01 Profile" },
		{ value: "CFG-02", label: "CFG-02 TDS" },
		{ value: "CFG-03", label: "CFG-03 Requirements" },
		{ value: "CFG-04", label: "CFG-04 Schedule" },
		{ value: "CFG-05", label: "CFG-05 Inventory" },
		{ value: "CFG-06", label: "CFG-06 Price Schedule" },
		{ value: "CFG-07", label: "CFG-07 Evaluation" },
		{ value: "CFG-08", label: "CFG-08 Forms & Evidence" },
		{ value: "CFG-09", label: "CFG-09 Contract Values" },
	];

	var state = {
		payload: null,
		configurationId: null,
		page: null,
		mounting: false,
		busy: false,
		confirmChecked: false,
		searchQuery: "",
		searchIndex: -1,
		searchMatches: [],
		activeOutlineKey: "",
		fitWidth: true,
		outlineObserver: null,
	};

	function surface() {
		var reg = kentender_core.cl_surface_registry;
		return reg && typeof reg.get === "function" ? reg.get(SURFACE_ID) : null;
	}

	function c() {
		return kentender_core.cl_components || kentender_core.cl.components;
	}

	function esc(v) {
		return frappe.utils.escape_html(v == null ? "" : String(v));
	}

	function configurationId() {
		var route = frappe.get_route() || [];
		if (route.length > 1 && route[1]) {
			return String(route[1]).trim();
		}
		if (frappe.route_options && frappe.route_options.configuration_id) {
			return String(frappe.route_options.configuration_id).trim();
		}
		try {
			var params = new URLSearchParams(window.location.search || "");
			if (params.get("configuration_id")) {
				return String(params.get("configuration_id")).trim();
			}
		} catch (e) {
			/* ignore */
		}
		try {
			var stored = window.sessionStorage.getItem(STORAGE_KEY);
			if (stored) {
				return stored;
			}
		} catch (e2) {
			/* ignore */
		}
		return null;
	}

	function emptyHtml() {
		return (
			'<div class="rounded border border-outline-variant bg-surface-container-lowest p-6" data-testid="kt-cl-wf03-empty">' +
			'<p class="text-body-md text-on-surface-variant">' +
			__("Select a tender configuration from Configuration Home.") +
			"</p>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary mt-4" data-action="back-home" data-testid="kt-cl-wf03-back">' +
			__("Back to Configuration Home") +
			"</button></div>"
		);
	}

	function outlineHtml(data) {
		var active = state.activeOutlineKey || "";
		var items = (data.outline || [])
			.map(function (item, idx) {
				var key = item.key || item.label || String(idx);
				var isActive = active && active === key;
				return (
					'<li class="kt-cl-wf03-outline-item' +
					(isActive ? " is-active" : "") +
					'" data-action="outline-jump" data-section-key="' +
					esc(key) +
					'" data-testid="kt-cl-wf03-outline-' +
					esc(key) +
					'" role="button" tabindex="0" aria-current="' +
					(isActive ? "true" : "false") +
					'">' +
					esc(item.label || key) +
					"</li>"
				);
			})
			.join("");
		return (
			'<nav class="kt-cl-wf03-outline" data-testid="kt-cl-wf03-outline" aria-label="' +
			esc(__("Document outline")) +
			'">' +
			"<h3>" +
			__("Document outline") +
			"</h3><ul>" +
			items +
			"</ul></nav>"
		);
	}

	function exceptionBannerHtml(data) {
		if ((data.preview_status || "") !== "Exception found" && !data.render_exception && !data.generation_block) {
			return "";
		}
		var block = data.generation_block || {};
		var area = block.blocking_area || "";
		var message = block.message || "";
		// Prefer structured fields — never dump the joined render_exception into the banner.
		if (!message && data.render_exception && !block.blocking_area) {
			message = data.render_exception;
		}
		var action =
			block.action ||
			__("Fix the affected configuration step, then regenerate the preview.");
		if (!message) {
			message = __(
				"Preview generation was blocked. Complete the owning configuration step, then regenerate."
			);
		}
		var ownerRoute = block.owner_route || "";
		var ownerStep = block.owner_step || "";
		var primaryLabel =
			block.cta_label ||
			(ownerRoute && ownerStep ? __("Open {0}", [ownerStep]) : __("Open Readiness Check"));
		var primaryAction = ownerRoute ? "open-owner-step" : "open-readiness";
		var secondary = ownerRoute
			? '<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--outline" data-action="open-readiness" data-testid="kt-cl-wf03-exception-readiness">' +
				__("Open Readiness Check") +
				"</button>"
			: "";
		return (
			'<div class="kt-cl-wf03-exception" data-testid="kt-cl-wf03-exception" role="alert">' +
			(area
				? '<p class="kt-cl-wf03-exception-area" data-testid="kt-cl-wf03-exception-area"><strong>' +
					esc(area) +
					"</strong></p>"
				: "") +
			'<p data-testid="kt-cl-wf03-exception-message">' +
			esc(message) +
			"</p>" +
			'<p class="kt-cl-wf03-exception-action" data-testid="kt-cl-wf03-exception-action">' +
			esc(action) +
			"</p>" +
			'<div class="kt-cl-wf03-exception-actions">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="' +
			esc(primaryAction) +
			'" data-owner-route="' +
			esc(ownerRoute) +
			'" data-testid="kt-cl-wf03-exception-cta">' +
			esc(primaryLabel) +
			"</button>" +
			secondary +
			"</div></div>"
		);
	}

	function previewHtml(data) {
		var blocked =
			(data.preview_status || "") === "Exception found" || !!data.generation_block;
		var html = blocked ? "" : data.preview_html || "";
		var hasPreview = !!html;
		var watermark = data.watermark_label || __("PREVIEW — NOT FOR PUBLICATION");
		var status = data.preview_status_label || data.preview_status || __("Not generated");
		var fitActive = !!state.fitWidth;
		var toolsBar = hasPreview
			? '<div class="kt-cl-wf03-preview-tools" data-testid="kt-cl-wf03-preview-tools">' +
				'<div class="kt-cl-wf03-preview-tools-row kt-cl-wf03-search" data-testid="kt-cl-wf03-search">' +
				'<input type="search" class="kt-cl-wf03-search-input" data-action="search-input" data-testid="kt-cl-wf03-search-input" placeholder="' +
				esc(__("Search in preview")) +
				'" value="' +
				esc(state.searchQuery || "") +
				'" />' +
				'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--outline" data-action="search-next" data-testid="kt-cl-wf03-search-next">' +
				__("Next") +
				"</button></div>" +
				'<div class="kt-cl-wf03-preview-tools-row kt-cl-wf03-view-toolbar" data-testid="kt-cl-wf03-view-toolbar">' +
				'<div class="kt-cl-wf03-view-group" role="group" aria-label="' +
				esc(__("Zoom")) +
				'">' +
				'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--outline' +
				(fitActive ? " is-active" : "") +
				'" data-action="fit-width" data-testid="kt-cl-wf03-fit-width" aria-pressed="' +
				(fitActive ? "true" : "false") +
				'">' +
				__("Fit to width") +
				"</button>" +
				'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--outline' +
				(fitActive ? "" : " is-active") +
				'" data-action="actual-size" data-testid="kt-cl-wf03-actual-size" aria-pressed="' +
				(fitActive ? "false" : "true") +
				'">' +
				__("Actual size") +
				"</button></div>" +
				'<label class="kt-cl-wf03-page-select-wrap">' +
				'<span class="sr-only">' +
				__("Section") +
				"</span>" +
				'<select class="kt-cl-wf03-page-select" data-action="page-select" data-testid="kt-cl-wf03-page-select"></select>' +
				"</label></div>" +
				'<div class="kt-cl-wf03-preview-tools-row kt-cl-wf03-preview-tools-row--full">' +
				'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--outline kt-cl-wf03-open-full-btn" data-action="open-full-preview" data-testid="kt-cl-wf03-open-full">' +
				__("Open full-page preview") +
				"</button></div></div>"
			: "";
		var emptyMsg = blocked
			? __(
					"Document preview was not generated. Resolve the readiness issue above, then regenerate."
				)
			: __("Generate a preview to review the tender document.");
		var inner = hasPreview
			? '<div class="kt-cl-wf03-preview-viewport' +
				(state.fitWidth ? " is-fit-width" : "") +
				'" data-testid="kt-cl-wf03-preview-viewport">' +
				'<iframe class="kt-cl-wf03-preview-frame" data-testid="kt-cl-wf03-preview-frame" title="' +
				esc(__("Tender document preview")) +
				'" sandbox="allow-same-origin"></iframe></div>' +
				'<textarea class="kt-cl-wf03-preview-src hidden" data-testid="kt-cl-wf03-preview-src">' +
				esc(html) +
				"</textarea>"
			: '<div class="kt-cl-wf03-preview-empty" data-testid="kt-cl-wf03-preview-empty">' +
				esc(emptyMsg) +
				"</div>";
		return (
			'<section class="kt-cl-wf03-preview" data-testid="kt-cl-wf03-preview">' +
			'<div class="kt-cl-wf03-preview-head">' +
			"<h3>" +
			__("Document preview") +
			"</h3>" +
			'<span class="kt-cl-wf03-preview-status" data-testid="kt-cl-wf03-preview-status">' +
			esc(status) +
			"</span></div>" +
			toolsBar +
			(hasPreview
				? '<p class="kt-cl-wf03-watermark" data-testid="kt-cl-wf03-watermark">' +
					esc(watermark) +
					"</p>"
				: "") +
			inner +
			"</section>"
		);
	}

	function confirmationHtml(data) {
		var checks = data.confirmation_checks || [];
		var canConfirm = !!(data.can_confirm_preview);
		var checked = state.confirmChecked || data.user_confirmed === 1;
		var list = checks
			.map(function (item, idx) {
				var id = item.id || String(idx);
				return (
					'<li data-testid="kt-cl-wf03-confirm-check-' +
					esc(id) +
					'">' +
					esc(item.label || "") +
					"</li>"
				);
			})
			.join("");
		return (
			'<aside class="kt-cl-wf03-confirmation" data-testid="kt-cl-wf03-confirmation">' +
			"<h3>" +
			__("Preview confirmation") +
			"</h3>" +
			'<ul class="kt-cl-wf03-confirm-list">' +
			list +
			"</ul>" +
			'<label class="kt-cl-wf02-check-item" data-testid="kt-cl-wf03-confirm-wrap">' +
			'<input type="checkbox" data-action="toggle-confirm" data-testid="kt-cl-wf03-confirm-checkbox"' +
			(checked ? " checked" : "") +
			(checked && data.user_confirmed ? " disabled" : "") +
			" />" +
			"<span>" +
			__("I have reviewed the generated tender document.") +
			"</span></label>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary kt-cl-wf03-confirm-btn" data-action="confirm-preview" data-testid="kt-cl-wf03-confirm-btn"' +
			(canConfirm && checked && !state.busy && !data.user_confirmed ? "" : " disabled") +
			">" +
			__("Confirm Preview") +
			"</button></aside>"
		);
	}

	function publicationPackageHtml(data) {
		if (!data.show_publication_package) {
			return "";
		}
		var pkg = data.publication_package || {};
		var items = (pkg.items || [])
			.map(function (label, idx) {
				return (
					'<li data-testid="kt-cl-wf03-pkg-item-' +
					esc(String(idx)) +
					'">' +
					esc(label) +
					"</li>"
				);
			})
			.join("");
		var sent = !!pkg.sent;
		return (
			'<section class="kt-cl-wf03-publication" data-testid="kt-cl-wf03-publication">' +
			"<h3>" +
			__("Publication Package") +
			"</h3>" +
			'<ul class="kt-cl-wf03-pkg-list">' +
			items +
			"</ul>" +
			'<p class="kt-cl-wf03-pkg-note" data-testid="kt-cl-wf03-pkg-note">' +
			esc(pkg.note || "") +
			"</p>" +
			(sent
				? '<p class="kt-cl-wf03-pkg-sent" data-testid="kt-cl-wf03-pkg-sent">' +
					__("Sent to publication workflow on {0}", [pkg.sent_at || "—"]) +
					"</p>"
				: '<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="send-publication" data-testid="kt-cl-wf03-send"' +
					(pkg.can_send && !state.busy ? "" : " disabled") +
					">" +
					__("Send to Publication Workflow") +
					"</button>") +
			"</section>"
		);
	}

	function footerHtml(data) {
		var canRegen = !!(data && data.can_regenerate_preview);
		var canReturn = !!(data && data.can_return_for_correction);
		var canDownload = !!(data && data.can_download_preview_pdf);
		return (
			'<div class="kt-cl-wizard-footer" data-testid="kt-cl-wf03-footer">' +
			'<div class="kt-cl-wizard-footer-start">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="back-home" data-testid="kt-cl-wf03-back">' +
			__("Back to Configuration Home") +
			"</button></div>" +
			'<div class="kt-cl-wizard-footer-end">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="regenerate" data-testid="kt-cl-wf03-regenerate"' +
			(canRegen && !state.busy ? "" : " disabled") +
			">" +
			__("Regenerate Preview") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--outline" data-action="download" data-testid="kt-cl-wf03-download"' +
			(canDownload && !state.busy ? "" : " disabled") +
			">" +
			__("Download Preview PDF") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="return-correction" data-testid="kt-cl-wf03-return"' +
			(canReturn && !state.busy ? "" : " disabled") +
			">" +
			__("Return for Correction") +
			"</button></div></div>"
		);
	}

	function pageHtml(data) {
		var comp = c();
		var ctx = data.context || data;
		state.confirmChecked = state.confirmChecked || data.user_confirmed === 1;
		return (
			'<div data-testid="kt-cl-wf03-root" data-configuration-id="' +
			esc(data.configuration_id || "") +
			'">' +
			comp.configurationContextStrip(ctx) +
			exceptionBannerHtml(data) +
			'<div class="kt-cl-wf03-layout" data-testid="kt-cl-wf03-layout">' +
			outlineHtml(data) +
			previewHtml(data) +
			confirmationHtml(data) +
			"</div>" +
			publicationPackageHtml(data) +
			footerHtml(data) +
			"</div>"
		);
	}

	function setActiveOutlineKey($root, key) {
		if (!key || state.activeOutlineKey === key) {
			return;
		}
		state.activeOutlineKey = key;
		$root.find(".kt-cl-wf03-outline-item").each(function () {
			var $item = $(this);
			var active = $item.attr("data-section-key") === key;
			$item.toggleClass("is-active", active);
			$item.attr("aria-current", active ? "true" : "false");
		});
		var $select = $root.find('[data-testid="kt-cl-wf03-page-select"]');
		if ($select.length && $select.val() !== key) {
			$select.val(key);
		}
	}

	function populatePageSelect($root) {
		var $select = $root.find('[data-testid="kt-cl-wf03-page-select"]');
		if (!$select.length) {
			return;
		}
		var outline = (state.payload && state.payload.outline) || [];
		var opts = outline
			.map(function (item) {
				var key = item.key || "";
				return (
					'<option value="' +
					esc(key) +
					'">' +
					esc(item.label || key) +
					"</option>"
				);
			})
			.join("");
		$select.html(opts);
		if (state.activeOutlineKey) {
			$select.val(state.activeOutlineKey);
		} else if (outline.length) {
			$select.val(outline[0].key || "");
		}
	}

	function bindOutlineScrollSync($root, frame) {
		var doc = null;
		try {
			doc = frame.contentDocument || (frame.contentWindow && frame.contentWindow.document);
		} catch (e) {
			return;
		}
		if (!doc || !doc.body) {
			return;
		}
		var sections = Array.prototype.slice.call(doc.querySelectorAll(".kt-preview-section[id^='sec-']"));
		if (!sections.length) {
			return;
		}
		if (state.outlineObserver && typeof state.outlineObserver.disconnect === "function") {
			state.outlineObserver.disconnect();
		}
		var win = frame.contentWindow;
		function pickActive() {
			var bestKey = "";
			var bestTop = -Infinity;
			sections.forEach(function (el) {
				var top = el.getBoundingClientRect().top;
				if (top <= 96 && top > bestTop) {
					bestTop = top;
					bestKey = (el.id || "").replace(/^sec-/, "");
				}
			});
			if (!bestKey && sections[0]) {
				bestKey = (sections[0].id || "").replace(/^sec-/, "");
			}
			if (bestKey) {
				setActiveOutlineKey($root, bestKey);
			}
		}
		if (win) {
			win.addEventListener("scroll", pickActive, { passive: true });
		}
		pickActive();
		state.outlineObserver = {
			disconnect: function () {
				if (win) {
					win.removeEventListener("scroll", pickActive);
				}
			},
		};
	}

	function hydratePreviewFrame($root) {
		var $src = $root.find('[data-testid="kt-cl-wf03-preview-src"]');
		var $frame = $root.find('[data-testid="kt-cl-wf03-preview-frame"]');
		if (!$src.length || !$frame.length) {
			return;
		}
		var html = $src.val() || $src.text() || "";
		if (!html) {
			return;
		}
		populatePageSelect($root);
		try {
			var frame = $frame[0];
			frame.onload = function () {
				bindOutlineScrollSync($root, frame);
				applyViewportMode($root);
			};
			frame.srcdoc = html;
		} catch (e) {
			/* ignore */
		}
	}

	function applyViewportMode($root) {
		var $viewport = $root.find('[data-testid="kt-cl-wf03-preview-viewport"]');
		if (!$viewport.length) {
			return;
		}
		var fit = !!state.fitWidth;
		$viewport.toggleClass("is-fit-width", fit);
		$viewport.toggleClass("is-actual-size", !fit);
		var $fit = $root.find('[data-testid="kt-cl-wf03-fit-width"]');
		var $actual = $root.find('[data-testid="kt-cl-wf03-actual-size"]');
		$fit.toggleClass("is-active", fit).attr("aria-pressed", fit ? "true" : "false");
		$actual.toggleClass("is-active", !fit).attr("aria-pressed", fit ? "false" : "true");
		var frame = $root.find('[data-testid="kt-cl-wf03-preview-frame"]')[0];
		if (frame) {
			// Force layout so Actual size (A4 width) is visible vs Fit to width.
			frame.style.width = fit ? "100%" : "794px";
			frame.style.maxWidth = fit ? "100%" : "794px";
			frame.style.marginLeft = fit ? "0" : "auto";
			frame.style.marginRight = fit ? "0" : "auto";
			frame.style.display = "block";
		}
	}

	function remountWithPayload(page, data) {
		var sh = kentender_core.cl_shell;
		var surf = surface();
		var pageHeader = {
			title: __("Tender Document Preview"),
			subtitle: __(
				"Review the generated tender document before sending it to the publication workflow."
			),
			hideBreadcrumbs: true,
		};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}
		state.payload = data;
		sh.mountContent(page.main, {
			pageHeader: pageHeader,
			mainHtml: data ? pageHtml(data) : emptyHtml(),
		});
		var $root = $(page.main);
		bind($root, page);
		hydratePreviewFrame($root);
	}

	function generatePreview(page) {
		if (state.busy || !state.configurationId) {
			return;
		}
		state.busy = true;
		remountWithPayload(page, state.payload || {});
		frappe.call({
			method: GENERATE_API,
			args: { configuration_id: state.configurationId },
			callback: function (r) {
				state.busy = false;
				remountWithPayload(page, r.message || state.payload);
				frappe.show_alert({ message: __("Preview generated"), indicator: "green" }, 4);
			},
			error: function () {
				state.busy = false;
				remountWithPayload(page, state.payload || {});
			},
		});
	}

	function confirmPreview(page) {
		if (state.busy || !state.configurationId || !state.confirmChecked) {
			return;
		}
		state.busy = true;
		frappe.call({
			method: CONFIRM_API,
			args: {
				configuration_id: state.configurationId,
				payload: { confirm_ready_for_handoff: 1 },
			},
			callback: function (r) {
				state.busy = false;
				state.confirmChecked = true;
				remountWithPayload(page, r.message || state.payload);
				frappe.show_alert({ message: __("Preview confirmed"), indicator: "green" }, 5);
			},
			error: function () {
				state.busy = false;
				remountWithPayload(page, state.payload || {});
			},
		});
	}

	function sendToPublication(page) {
		if (state.busy || !state.configurationId) {
			return;
		}
		kentender_core.cl.confirm({
			title: __("Send to Publication Workflow?"),
			message: __(
				"This sends the approved package to the publication workflow. It does not publish the tender."
			),
			confirmLabel: __("Send to Publication Workflow"),
			cancelLabel: __("Cancel"),
			onConfirm: function () {
				state.busy = true;
				remountWithPayload(page, state.payload || {});
				frappe.call({
					method: SEND_API,
					args: { configuration_id: state.configurationId },
					callback: function (r) {
						state.busy = false;
						remountWithPayload(page, r.message || state.payload);
						frappe.show_alert(
							{ message: __("Sent to publication workflow"), indicator: "green" },
							5
						);
					},
					error: function () {
						state.busy = false;
						remountWithPayload(page, state.payload || {});
					},
				});
			},
		});
	}

	function previewFrameDoc($root) {
		var frame = $root.find('[data-testid="kt-cl-wf03-preview-frame"]')[0];
		if (!frame) {
			return null;
		}
		try {
			return frame.contentDocument || (frame.contentWindow && frame.contentWindow.document);
		} catch (e) {
			return null;
		}
	}

	function jumpToOutlineSection($root, sectionKey) {
		if (!sectionKey) {
			return;
		}
		setActiveOutlineKey($root, sectionKey);
		var doc = previewFrameDoc($root);
		if (!doc) {
			return;
		}
		var el = doc.getElementById("sec-" + sectionKey);
		if (el && typeof el.scrollIntoView === "function") {
			el.scrollIntoView({ behavior: "smooth", block: "start" });
		}
	}

	function clearSearchHighlights(doc) {
		if (!doc) {
			return;
		}
		var marks = doc.querySelectorAll("mark.kt-cl-wf03-hit");
		for (var i = 0; i < marks.length; i++) {
			var mark = marks[i];
			var parent = mark.parentNode;
			if (!parent) {
				continue;
			}
			parent.replaceChild(doc.createTextNode(mark.textContent || ""), mark);
			parent.normalize();
		}
	}

	function runPreviewSearch($root, query) {
		var doc = previewFrameDoc($root);
		state.searchQuery = query || "";
		state.searchMatches = [];
		state.searchIndex = -1;
		if (!doc || !state.searchQuery) {
			clearSearchHighlights(doc);
			return;
		}
		clearSearchHighlights(doc);
		var walker = doc.createTreeWalker(doc.body || doc, NodeFilter.SHOW_TEXT, null);
		var needle = state.searchQuery.toLowerCase();
		var nodes = [];
		while (walker.nextNode()) {
			nodes.push(walker.currentNode);
		}
		nodes.forEach(function (textNode) {
			var text = textNode.nodeValue || "";
			var lower = text.toLowerCase();
			var idx = lower.indexOf(needle);
			if (idx < 0 || !textNode.parentNode) {
				return;
			}
			var before = text.slice(0, idx);
			var match = text.slice(idx, idx + needle.length);
			var after = text.slice(idx + needle.length);
			var mark = doc.createElement("mark");
			mark.className = "kt-cl-wf03-hit";
			mark.textContent = match;
			var frag = doc.createDocumentFragment();
			if (before) {
				frag.appendChild(doc.createTextNode(before));
			}
			frag.appendChild(mark);
			if (after) {
				frag.appendChild(doc.createTextNode(after));
			}
			textNode.parentNode.replaceChild(frag, textNode);
			state.searchMatches.push(mark);
		});
		if (state.searchMatches.length) {
			state.searchIndex = 0;
			focusSearchMatch();
		}
	}

	function focusSearchMatch() {
		if (!state.searchMatches.length) {
			return;
		}
		if (state.searchIndex < 0 || state.searchIndex >= state.searchMatches.length) {
			state.searchIndex = 0;
		}
		var el = state.searchMatches[state.searchIndex];
		if (el && typeof el.scrollIntoView === "function") {
			el.scrollIntoView({ behavior: "smooth", block: "center" });
		}
	}

	function nextSearchMatch($root) {
		if (!state.searchQuery) {
			return;
		}
		if (!state.searchMatches.length) {
			runPreviewSearch($root, state.searchQuery);
			return;
		}
		state.searchIndex = (state.searchIndex + 1) % state.searchMatches.length;
		focusSearchMatch();
	}

	function downloadPreviewPdf() {
		if (!state.configurationId || state.busy) {
			return;
		}
		if (!(state.payload && state.payload.can_download_preview_pdf)) {
			frappe.show_alert(
				{
					message: __("Preview PDF is unavailable until a clean preview is generated."),
					indicator: "orange",
				},
				5
			);
			return;
		}
		var url =
			"/api/method/" +
			PDF_API +
			"?configuration_id=" +
			encodeURIComponent(state.configurationId);
		var filename =
			((state.payload && (state.payload.configuration_ref || state.payload.configuration_id)) ||
				"tender-preview") + "-preview.pdf";
		state.busy = true;
		fetch(url, { credentials: "same-origin" })
			.then(function (resp) {
				if (!resp.ok) {
					throw new Error("PDF download failed");
				}
				return resp.blob();
			})
			.then(function (blob) {
				var objectUrl = URL.createObjectURL(blob);
				var a = document.createElement("a");
				a.href = objectUrl;
				a.download = filename;
				a.setAttribute("data-testid", "kt-cl-wf03-download-link");
				document.body.appendChild(a);
				a.click();
				document.body.removeChild(a);
				URL.revokeObjectURL(objectUrl);
				frappe.show_alert({ message: __("Preview PDF downloaded"), indicator: "green" }, 3);
			})
			.catch(function () {
				frappe.show_alert({ message: __("Could not download preview PDF"), indicator: "red" }, 5);
			})
			.finally(function () {
				state.busy = false;
			});
	}

	function ensureModalHost() {
		var host = document.getElementById(MODAL_HOST_ID);
		if (!host) {
			host = document.createElement("div");
			host.id = MODAL_HOST_ID;
			document.body.appendChild(host);
		}
		return $(host);
	}

	function closeReturnModal() {
		var $host = ensureModalHost();
		$host.empty().off(".wf03modal");
	}

	function openReturnModal(page) {
		var outline = (state.payload && state.payload.outline) || [];
		var sectionOpts = outline
			.map(function (item) {
				var key = item.key || item.label || "";
				var label = item.label || key;
				return (
					'<option value="' +
					esc(label) +
					'" data-key="' +
					esc(key) +
					'">' +
					esc(label) +
					"</option>"
				);
			})
			.join("");
		var cfgOpts = CFG_STEPS.map(function (step) {
			return '<option value="' + esc(step.value) + '">' + esc(step.label) + "</option>";
		}).join("");
		var $host = ensureModalHost();
		$host.html(
			'<div class="kt-cl-wf03-drawer-overlay" data-testid="kt-cl-wf03-return-modal">' +
				'<button type="button" class="kt-cl-wf03-drawer-backdrop" data-action="close-return" aria-label="' +
				esc(__("Close")) +
				'"></button>' +
				'<aside class="kt-cl-wf03-drawer" role="dialog" aria-modal="true">' +
				'<header class="kt-cl-wf03-drawer-header"><h2>' +
				__("Return for Correction") +
				'</h2><button type="button" class="kt-cl-wf03-drawer-close" data-action="close-return" data-testid="kt-cl-wf03-return-close">&times;</button></header>' +
				'<div class="kt-cl-wf03-drawer-body">' +
				"<p>" +
				__(
					"Returning this configuration will stop the publication handoff until the issue is corrected, readiness is rechecked where required, and review approval is refreshed if the correction affects approved content."
				) +
				"</p>" +
				'<label class="kt-cl-wf03-field"><span class="kt-cl-wf03-field-label">' +
				__("Affected document section") +
				' <span class="kt-cl-wf03-req">*</span></span>' +
				'<select class="kt-cl-wf03-control" data-testid="kt-cl-wf03-return-section">' +
				'<option value="">' +
				__("Select section") +
				"</option>" +
				sectionOpts +
				"</select></label>" +
				'<label class="kt-cl-wf03-field"><span class="kt-cl-wf03-field-label">' +
				__("Correction reason") +
				' <span class="kt-cl-wf03-req">*</span></span>' +
				'<textarea class="kt-cl-wf03-control kt-cl-wf03-control--area" data-testid="kt-cl-wf03-return-reason"></textarea></label>' +
				'<div class="kt-cl-wf03-field"><span class="kt-cl-wf03-field-label">' +
				__("Severity") +
				' <span class="kt-cl-wf03-req">*</span></span>' +
				'<div class="kt-cl-wf03-sev-picker" data-testid="kt-cl-wf03-return-severity">' +
				'<button type="button" class="kt-cl-wf03-sev-opt" data-severity="Low">' +
				__("Low") +
				"</button>" +
				'<button type="button" class="kt-cl-wf03-sev-opt is-active" data-severity="Medium">' +
				__("Medium") +
				"</button>" +
				'<button type="button" class="kt-cl-wf03-sev-opt" data-severity="High">' +
				__("High") +
				"</button></div></div>" +
				'<label class="kt-cl-wf03-field"><span class="kt-cl-wf03-field-label">' +
				__("Suggested owning configuration step") +
				" (" +
				__("optional") +
				")</span>" +
				'<select class="kt-cl-wf03-control" data-testid="kt-cl-wf03-return-cfg-step">' +
				cfgOpts +
				"</select></label>" +
				'<p class="kt-cl-wf03-inline-error" data-testid="kt-cl-wf03-return-error" hidden></p>' +
				"</div>" +
				'<footer class="kt-cl-wf03-drawer-footer">' +
				'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="close-return" data-testid="kt-cl-wf03-return-cancel">' +
				__("Cancel") +
				"</button>" +
				'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="submit-return" data-testid="kt-cl-wf03-return-submit">' +
				__("Return for Correction") +
				"</button></footer></aside></div>"
		);
		$host.off(".wf03modal");
		$host.on("click.wf03modal", "[data-action='close-return']", function (e) {
			e.preventDefault();
			closeReturnModal();
		});
		$host.on("click.wf03modal", "[data-severity]", function (e) {
			e.preventDefault();
			$host.find("[data-severity]").removeClass("is-active");
			$(this).addClass("is-active");
			$host.find('[data-testid="kt-cl-wf03-return-error"]').attr("hidden", true).text("");
		});
		$host.on("click.wf03modal", "[data-action='submit-return']", function (e) {
			e.preventDefault();
			var section = String($host.find('[data-testid="kt-cl-wf03-return-section"]').val() || "").trim();
			var reason = String($host.find('[data-testid="kt-cl-wf03-return-reason"]').val() || "").trim();
			var severity = String($host.find("[data-severity].is-active").attr("data-severity") || "").trim();
			var cfgStep = String($host.find('[data-testid="kt-cl-wf03-return-cfg-step"]').val() || "").trim();
			var $err = $host.find('[data-testid="kt-cl-wf03-return-error"]');
			if (!section || !reason || !severity) {
				$err
					.text(__("Affected section, correction reason, and severity are required."))
					.removeAttr("hidden");
				return;
			}
			$err.attr("hidden", true).text("");
			state.busy = true;
			frappe.call({
				method: RETURN_API,
				args: {
					configuration_id: state.configurationId,
					payload: {
						affected_section: section,
						reason: reason,
						severity: severity,
						owning_cfg_step: cfgStep,
					},
				},
				callback: function (r) {
					state.busy = false;
					closeReturnModal();
					remountWithPayload(page, r.message || state.payload);
					frappe.show_alert({ message: __("Returned for correction"), indicator: "orange" }, 5);
				},
				error: function (err) {
					state.busy = false;
					var msg =
						(err && err.message) ||
						(err && err._server_messages) ||
						__("Could not return for correction.");
					$err.text(typeof msg === "string" ? msg : __("Could not return for correction.")).removeAttr("hidden");
				},
			});
		});
	}

	function injectWf03Styles() {
		["kt-cl-wf03-inline-style", "kt-cl-wf03-inline-style-v2"].forEach(function (id) {
			var stale = document.getElementById(id);
			if (stale && stale.parentNode) {
				stale.parentNode.removeChild(stale);
			}
		});
		if (document.getElementById("kt-cl-wf03-inline-style-v3")) {
			return;
		}
		var style = document.createElement("style");
		style.id = "kt-cl-wf03-inline-style-v3";
		style.textContent =
			".kt-cl-wf03-outline-item{cursor:pointer;padding:.35rem .5rem;border-radius:.25rem}" +
			".kt-cl-wf03-outline-item:hover{background:rgba(0,34,68,.06)}" +
			".kt-cl-wf03-outline-item.is-active{background:rgba(0,34,68,.12);font-weight:700;color:#002244}" +
			".kt-cl-wf03-preview-tools{display:flex;flex-direction:column;gap:.5rem;margin:0 0 .75rem;padding:.65rem .75rem;background:#f0f4f8;border:1px solid #c4c6cf;border-radius:.25rem;overflow:hidden;max-width:100%;box-sizing:border-box}" +
			".kt-cl-wf03-preview-tools-row{display:flex;align-items:center;gap:.5rem;min-width:0;max-width:100%}" +
			".kt-cl-wf03-preview-tools-row--full{display:flex}" +
			".kt-cl-wf03-search{margin:0}" +
			".kt-cl-wf03-search-input{flex:1 1 auto;min-width:0;height:2.25rem;border:1px solid #c4c6cf;border-radius:.25rem;padding:0 .65rem;background:#fff;box-sizing:border-box}" +
			".kt-cl-wf03-view-toolbar{margin:0;flex-wrap:nowrap}" +
			".kt-cl-wf03-view-group{display:inline-flex;align-items:center;gap:.35rem;flex:0 0 auto}" +
			".kt-cl-wf03-page-select-wrap{flex:1 1 auto;min-width:0;margin:0}" +
			".kt-cl-wf03-page-select{display:block;width:100%;max-width:100%;height:2.25rem;border:1px solid #c4c6cf;border-radius:.25rem;padding:0 .55rem;background:#fff;box-sizing:border-box}" +
			".kt-cl-wf03-preview-tools .kt-cl-wizard-btn{height:2.25rem;margin:0;flex:0 0 auto;white-space:nowrap}" +
			".kt-cl-wf03-preview-tools .kt-cl-wizard-btn.is-active{background:#002244;border-color:#002244;color:#fff}" +
			".kt-cl-wf03-open-full-btn{width:100%;justify-content:center;max-width:100%;box-sizing:border-box}" +
			".kt-cl-wf03-preview-viewport{min-height:28rem;border:1px solid #c4c6cf;border-radius:.25rem;background:#eef1f5;overflow:auto}" +
			".kt-cl-wf03-preview-viewport.is-fit-width .kt-cl-wf03-preview-frame{width:100%!important;max-width:100%!important;min-height:28rem;border:0;margin:0;display:block}" +
			".kt-cl-wf03-preview-viewport.is-actual-size .kt-cl-wf03-preview-frame{width:794px!important;max-width:794px!important;min-height:28rem;border:0;margin:0 auto;display:block;box-shadow:0 0 0 1px #c4c6cf,0 8px 24px rgba(16,24,40,.12);background:#fff}" +
			".sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0}" +
			".kt-cl-wf03-exception{margin:0 0 1rem;padding:.75rem 1rem;border:1px solid #f2b8b5;border-radius:.25rem;background:#f9dedc;color:#410e0b}" +
			".kt-cl-wf03-exception p{margin:0 0 .75rem}" +
			".kt-cl-wf03-exception-actions{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin-top:.25rem}" +
			".kt-cl-wf03-exception-actions .kt-cl-wizard-btn{margin:0}" +
			".kt-cl-wf03-exception-area{margin-bottom:.35rem!important}" +
			".kt-cl-wf03-exception-action{font-weight:600}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-drawer-overlay{position:fixed;inset:0;z-index:1300}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-drawer-backdrop{position:absolute;inset:0;border:0;background:rgba(0,34,68,.2);cursor:pointer}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-drawer{position:fixed;top:0;right:0;bottom:0;width:min(420px,100vw);display:flex;flex-direction:column;background:#fff;border-left:1px solid #c4c6cf;z-index:1301}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-drawer-header{display:flex;justify-content:space-between;align-items:center;padding:1rem 1.25rem;background:#f0f4f8;border-bottom:1px solid #c4c6cf}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-drawer-header h2{margin:0;font-size:1.15rem;color:#002244}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-drawer-close{border:0;background:transparent;font-size:1.5rem;cursor:pointer}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-drawer-body{flex:1;overflow:auto;padding:1.25rem;display:flex;flex-direction:column;gap:1rem}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-field{display:flex;flex-direction:column;gap:.4rem}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-field-label{font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:#5f6368}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-req{color:#ba1a1a}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-control{width:100%;border:1px solid #c4c6cf;border-radius:.25rem;padding:.65rem .75rem;background:#f0f4f8}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-control--area{min-height:5.5rem;resize:vertical}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-sev-picker{display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-sev-opt{border:1px solid #c4c6cf;background:#fff;border-radius:.25rem;padding:.55rem;font-size:10px;font-weight:700;text-transform:uppercase;cursor:pointer}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-sev-opt.is-active{border-color:#002244;background:rgba(0,34,68,.08);color:#002244}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-drawer-footer{display:flex;gap:.75rem;padding:1rem 1.25rem;border-top:1px solid #c4c6cf;background:#f0f4f8}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-drawer-footer .kt-cl-wizard-btn{flex:1}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-inline-error{margin:0;padding:.55rem .75rem;border:1px solid #f2b8b5;border-radius:.25rem;background:#f9dedc;color:#410e0b;font-size:13px}" +
			"#" +
			MODAL_HOST_ID +
			" .kt-cl-wf03-inline-error[hidden]{display:none!important}";
		document.head.appendChild(style);
	}

	function bind($root, page) {
		injectWf03Styles();
		$root.off(".wf03");
		$root.on("click.wf03", "[data-action='back-home']", function (e) {
			e.preventDefault();
			if (!state.configurationId) {
				frappe.set_route("it-tender-configuration-dashboard");
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route(BACK_ROUTE, state.configurationId);
		});
		$root.on("click.wf03", "[data-action='open-readiness']", function (e) {
			e.preventDefault();
			if (!state.configurationId) {
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route(READINESS_ROUTE, state.configurationId);
		});
		$root.on("click.wf03", "[data-action='open-owner-step']", function (e) {
			e.preventDefault();
			if (!state.configurationId) {
				return;
			}
			var route = String($(this).attr("data-owner-route") || "").trim();
			if (!route) {
				var block = (state.payload && state.payload.generation_block) || {};
				route = String(block.owner_route || "").trim();
			}
			if (!route) {
				frappe.route_options = { configuration_id: state.configurationId };
				frappe.set_route(READINESS_ROUTE, state.configurationId);
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route(route, state.configurationId);
		});
		$root.on("click.wf03", "[data-action='regenerate']", function (e) {
			e.preventDefault();
			generatePreview(page);
		});
		$root.on("click.wf03", "[data-action='download']", function (e) {
			e.preventDefault();
			downloadPreviewPdf();
		});
		$root.on("click.wf03", "[data-action='outline-jump']", function (e) {
			e.preventDefault();
			jumpToOutlineSection($root, $(this).attr("data-section-key"));
		});
		$root.on("keydown.wf03", "[data-action='outline-jump']", function (e) {
			if (e.key === "Enter" || e.key === " ") {
				e.preventDefault();
				jumpToOutlineSection($root, $(this).attr("data-section-key"));
			}
		});
		$root.on("change.wf03", "[data-action='page-select']", function () {
			jumpToOutlineSection($root, String($(this).val() || ""));
		});
		$root.on("click.wf03", "[data-action='fit-width']", function (e) {
			e.preventDefault();
			state.fitWidth = true;
			applyViewportMode($root);
		});
		$root.on("click.wf03", "[data-action='actual-size']", function (e) {
			e.preventDefault();
			state.fitWidth = false;
			applyViewportMode($root);
		});
		$root.on("click.wf03", "[data-action='open-full-preview']", function (e) {
			e.preventDefault();
			var html = (state.payload && state.payload.preview_html) || "";
			if (!html) {
				return;
			}
			var w = window.open("", "_blank");
			if (w) {
				w.document.open();
				w.document.write(html);
				w.document.close();
			}
		});
		$root.on("input.wf03", "[data-action='search-input']", function () {
			runPreviewSearch($root, String($(this).val() || ""));
		});
		$root.on("click.wf03", "[data-action='search-next']", function (e) {
			e.preventDefault();
			nextSearchMatch($root);
		});
		$root.on("change.wf03", "[data-action='toggle-confirm']", function () {
			state.confirmChecked = $(this).prop("checked");
			remountWithPayload(page, state.payload || {});
		});
		$root.on("click.wf03", "[data-action='confirm-preview']", function (e) {
			e.preventDefault();
			confirmPreview(page);
		});
		$root.on("click.wf03", "[data-action='send-publication']", function (e) {
			e.preventDefault();
			sendToPublication(page);
		});
		$root.on("click.wf03", "[data-action='return-correction']", function (e) {
			e.preventDefault();
			openReturnModal(page);
		});
	}

	function mount(page) {
		if (state.mounting) {
			return;
		}
		state.page = page;
		var sh = kentender_core.cl_shell;
		var surf = surface();
		if (!sh || typeof sh.mountContent !== "function") {
			page.main.html(
				'<div class="p-4 text-danger">' + __("Civic Ledger shell is not loaded.") + "</div>"
			);
			return;
		}
		var pageHeader = {
			title: __("Tender Document Preview"),
			subtitle: __(
				"Review the generated tender document before sending it to the publication workflow."
			),
			hideBreadcrumbs: true,
		};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}

		var id = configurationId();
		state.configurationId = id;
		if (!id) {
			sh.mountContent(page.main, { pageHeader: pageHeader, mainHtml: emptyHtml() });
			bind($(page.main), page);
			return;
		}

		var route = frappe.get_route() || [];
		if (route[0] === RETIRED_SLUG) {
			state.mounting = true;
			frappe.set_route(PAGE_SLUG, id);
			setTimeout(function () {
				state.mounting = false;
			}, 0);
			return;
		}
		if (!(route[0] === PAGE_SLUG && route[1] === id)) {
			state.mounting = true;
			frappe.set_route(PAGE_SLUG, id);
			setTimeout(function () {
				state.mounting = false;
			}, 0);
			return;
		}

		try {
			window.sessionStorage.setItem(STORAGE_KEY, id);
		} catch (e) {
			/* ignore */
		}

		frappe.call({
			method: GET_API,
			args: { configuration_id: id },
			callback: function (r) {
				var data = r.message || null;
				if (data && data.user_confirmed) {
					state.confirmChecked = true;
				}
				remountWithPayload(page, data);
				if (
					data &&
					!data.preview_html &&
					data.can_regenerate_preview &&
					(data.preview_status || "") === "Not generated" &&
					!data.generation_block
				) {
					generatePreview(page);
				}
			},
			error: function () {
				sh.mountContent(page.main, { pageHeader: pageHeader, mainHtml: emptyHtml() });
				bind($(page.main), page);
			},
		});
	}

	function registerPage(slug) {
		if (!frappe.pages[slug]) {
			return;
		}
		frappe.pages[slug].on_page_load = function (wrapper) {
			var page = frappe.ui.make_app_page({
				parent: wrapper,
				title: __("Tender Document Preview"),
				single_column: true,
			});
			wrapper.page = page;
			frappe.pages[slug].page = page;
			mount(page);
		};
		frappe.pages[slug].on_page_show = function (wrapper) {
			if (wrapper && wrapper.page) {
				frappe.pages[slug].page = wrapper.page;
				mount(wrapper.page);
			}
		};
	}

	registerPage(PAGE_SLUG);
	registerPage(RETIRED_SLUG);
})();
