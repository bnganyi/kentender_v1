/**
 * Price Schedule bidder portal — overview / editor / review.
 */
(function () {
	function qs(sel, root) {
		return (root || document).querySelector(sel);
	}

	function qsa(sel, root) {
		return Array.prototype.slice.call((root || document).querySelectorAll(sel));
	}

	function toast(msg) {
		var el = qs("[data-testid='kt-ps-toast']");
		if (!el) {
			window.alert(msg);
			return;
		}
		el.hidden = false;
		el.textContent = msg;
		el.classList.add("is-visible");
		clearTimeout(toast._t);
		toast._t = setTimeout(function () {
			el.classList.remove("is-visible");
			el.hidden = true;
		}, 2800);
	}

	function call(method, args) {
		return new Promise(function (resolve, reject) {
			if (typeof frappe === "undefined" || !frappe.call) {
				reject(new Error("Session unavailable"));
				return;
			}
			frappe.call({
				method: method,
				args: args,
				error_handlers: {},
				callback: function (r) {
					if (r && r.exc) {
						var msg = "Request failed";
						try {
							var parsed =
								typeof r._server_messages === "string"
									? JSON.parse(r._server_messages)
									: null;
							if (parsed && parsed.length) {
								var first =
									typeof parsed[0] === "string" ? JSON.parse(parsed[0]) : parsed[0];
								msg = (first && (first.message || first.title)) || msg;
							}
						} catch (e) {
							/* keep */
						}
						reject(new Error(msg));
						return;
					}
					resolve((r && r.message) || r);
				},
				error: function (err) {
					var msg = "Request failed";
					try {
						if (err && err._server_messages) {
							var parsed = JSON.parse(err._server_messages);
							if (parsed && parsed[0]) {
								var first =
									typeof parsed[0] === "string" ? JSON.parse(parsed[0]) : parsed[0];
								msg = (first && first.message) || msg;
							}
						} else if (err && err.message) {
							msg = err.message;
						}
					} catch (e) {
						/* keep */
					}
					reject(new Error(msg));
				},
			});
		});
	}

	function overviewRoot() {
		return qs("[data-testid='kt-ps-root']");
	}

	function editorRoot() {
		return qs("[data-testid='kt-ps-editor-root']");
	}

	function reviewRoot() {
		return qs("[data-testid='kt-ps-review-root']");
	}

	function reloadWithParams(baseUrl, offerId, lotId) {
		var url = baseUrl.split("?")[0];
		var params = [];
		if (offerId) params.push("offer_id=" + encodeURIComponent(offerId));
		if (lotId) params.push("lot_id=" + encodeURIComponent(lotId));
		window.location.href = params.length ? url + "?" + params.join("&") : url;
	}

	function initOverview() {
		var root = overviewRoot();
		if (!root || editorRoot() || reviewRoot()) return;
		var sectionUrl = root.getAttribute("data-section-url") || window.location.pathname;

		qsa("[data-testid='kt-ps-offer-tab']", root).forEach(function (btn) {
			btn.addEventListener("click", function () {
				var offerId = btn.getAttribute("data-offer-id") || "main";
				var lotSel = qs("[data-testid='kt-ps-lot-select']", root);
				var lotId = lotSel ? lotSel.value : root.getAttribute("data-active-lot-id") || "";
				reloadWithParams(sectionUrl, offerId, lotId);
			});
		});

		var lotSelect = qs("[data-testid='kt-ps-lot-select']", root);
		if (lotSelect) {
			lotSelect.addEventListener("change", function () {
				reloadWithParams(
					sectionUrl,
					root.getAttribute("data-active-offer-id") || "main",
					lotSelect.value || ""
				);
			});
		}
	}

	function parseMoney(raw) {
		var text = String(raw == null ? "" : raw).trim().replace(/,/g, "");
		if (!text) return null;
		var n = Number(text);
		return isFinite(n) ? n : null;
	}

	function formatMoney(val, precision) {
		var p = precision == null ? 2 : precision;
		var n = typeof val === "number" ? val : parseMoney(val);
		if (n == null || !isFinite(n)) return "";
		return n.toLocaleString("en-US", {
			minimumFractionDigits: p,
			maximumFractionDigits: p,
		});
	}

	function collectEditorLines(root) {
		var lines = [];
		qsa("[data-testid='kt-ps-line-row']", root).forEach(function (tr) {
			var lineId = tr.getAttribute("data-line-id");
			if (!lineId) return;
			var item = { line_id: lineId };
			var currency = qs('[data-field="currency"]', tr);
			if (currency) item.currency = currency.value;
			var country = qs('[data-field="country_of_origin"]', tr);
			if (country) item.country_of_origin = country.value;
			var unitPrice = qs('[data-field="unit_price"]', tr);
			if (unitPrice) {
				var raw = (unitPrice.value || "").trim();
				if (raw !== "") item.unit_price = String(parseMoney(raw) != null ? parseMoney(raw) : raw.replace(/,/g, ""));
			}
			var periodPrices = {};
			qsa('[data-field="period_price"]', tr).forEach(function (inp) {
				var pk = inp.getAttribute("data-period");
				var val = (inp.value || "").trim();
				if (pk && val !== "") {
					var parsed = parseMoney(val);
					periodPrices[pk] = parsed != null ? String(parsed) : val.replace(/,/g, "");
				}
			});
			if (Object.keys(periodPrices).length) item.period_prices = periodPrices;
			lines.push(item);
		});
		return lines;
	}

	function rowIsPriced(tr, isRecurrent) {
		// Match server _line_has_input: any price entry counts toward "N of M items".
		if (isRecurrent) {
			var periods = qsa('[data-field="period_price"]', tr);
			return periods.some(function (inp) {
				return (inp.value || "").trim() !== "";
			});
		}
		var price = qs('[data-field="unit_price"]', tr);
		if (price && (price.value || "").trim()) return true;
		var country = qs('[data-field="country_of_origin"]', tr);
		return !!(country && (country.value || "").trim());
	}

	function applyEditorProgress(root, started, total) {
		var host = qs("[data-testid='kt-ps-editor-progress']", root);
		var label = qs("[data-testid='kt-ps-editor-progress-label']", root);
		var fill = qs("[data-testid='kt-ps-editor-progress-fill']", root);
		var t = Math.max(0, parseInt(total, 10) || 0);
		var s = Math.max(0, Math.min(t, parseInt(started, 10) || 0));
		var pct = t ? Math.round((100 * s) / t) : 0;
		if (host) {
			host.setAttribute("data-progress-started", String(s));
			host.setAttribute("data-progress-total", String(t));
		}
		if (label) {
			label.textContent = s + " of " + t + " items";
		}
		if (fill) {
			fill.style.width = pct + "%";
		}
	}

	function refreshEditorProgress(root) {
		var isRecurrent = root.getAttribute("data-is-recurrent") === "1";
		var total = 0;
		var started = 0;
		qsa("[data-testid='kt-ps-line-row']", root).forEach(function (tr) {
			if (tr.getAttribute("data-required") !== "1") return;
			total += 1;
			if (rowIsPriced(tr, isRecurrent)) started += 1;
		});
		applyEditorProgress(root, started, total);
	}

	function refreshClientTotals(root) {
		qsa("[data-testid='kt-ps-line-row']", root).forEach(function (tr) {
			var totalEl = qs("[data-testid='kt-ps-line-total']", tr);
			var priceEl = qs('[data-field="unit_price"]', tr);
			if (!totalEl || !priceEl) return;
			var qty = parseFloat(totalEl.getAttribute("data-qty") || "0");
			var price = parseMoney(priceEl.value);
			if (price == null || !isFinite(qty)) {
				totalEl.textContent = "—";
				return;
			}
			totalEl.textContent = formatMoney(qty * price, 2);
		});
	}

	function formatMoneyInputs(root) {
		qsa('[data-field="unit_price"], [data-field="period_price"]', root).forEach(function (inp) {
			var n = parseMoney(inp.value);
			if (n == null) return;
			inp.value = formatMoney(n, 2);
		});
	}

	function onEditorFieldChange(root) {
		refreshClientTotals(root);
		refreshEditorProgress(root);
	}

	function saveEditor(root, thenNavigate) {
		if (root.getAttribute("data-bid-sealed") === "1") return Promise.resolve();
		var pub = root.getAttribute("data-publication-ref");
		var payload = {
			schedule_key: root.getAttribute("data-schedule-key"),
			offer_id: root.getAttribute("data-active-offer-id") || "main",
			lot_id: root.getAttribute("data-active-lot-id") || "",
			lines: collectEditorLines(root),
		};
		return call("kentender_procurement.tender_configurations.save_price_schedule_lines", {
			published_tender_ref: pub,
			payload: payload,
		}).then(function (dto) {
			if (dto && dto.progress) {
				applyEditorProgress(
					root,
					dto.progress.started != null ? dto.progress.started : dto.progress.complete,
					dto.progress.total
				);
			} else {
				refreshEditorProgress(root);
			}
			toast("Draft saved");
			if (thenNavigate) {
				window.setTimeout(function () {
					window.location.href =
						thenNavigate ||
						root.getAttribute("data-continue-url") ||
						root.getAttribute("data-section-url") ||
						"/";
				}, 250);
			}
		});
	}

	function initEditor() {
		var root = editorRoot();
		if (!root) return;

		qsa(
			'[data-field="unit_price"], [data-field="period_price"], [data-field="country_of_origin"], [data-field="currency"]',
			root
		).forEach(function (inp) {
			inp.addEventListener("input", function () {
				onEditorFieldChange(root);
			});
			inp.addEventListener("change", function () {
				onEditorFieldChange(root);
			});
			if (inp.getAttribute("data-field") === "unit_price" || inp.getAttribute("data-field") === "period_price") {
				inp.addEventListener("blur", function () {
					var n = parseMoney(inp.value);
					if (n != null) inp.value = formatMoney(n, 2);
					onEditorFieldChange(root);
				});
				inp.addEventListener("focus", function () {
					var n = parseMoney(inp.value);
					if (n != null) inp.value = String(n);
				});
			}
		});

		// Initial sync — format restored values and refresh progress/totals.
		formatMoneyInputs(root);
		refreshClientTotals(root);
		refreshEditorProgress(root);

		var saveBtn = qs("[data-testid='kt-ps-save-draft']", root);
		if (saveBtn) {
			saveBtn.addEventListener("click", function () {
				saveBtn.disabled = true;
				saveEditor(root, null)
					.catch(function (err) {
						toast((err && err.message) || "Could not save draft");
					})
					.finally(function () {
						if (root.getAttribute("data-bid-sealed") !== "1") saveBtn.disabled = false;
					});
			});
		}

		var contBtn = qs("[data-testid='kt-ps-editor-continue']", root);
		if (contBtn) {
			contBtn.addEventListener("click", function () {
				contBtn.disabled = true;
				saveEditor(root, root.getAttribute("data-continue-url"))
					.catch(function (err) {
						toast((err && err.message) || "Could not save");
						if (root.getAttribute("data-bid-sealed") !== "1") contBtn.disabled = false;
					});
			});
		}
	}

	function initReview() {
		var root = reviewRoot();
		if (!root) return;
		var btn = qs("[data-testid='kt-ps-complete-btn']", root);
		if (!btn) return;
		btn.addEventListener("click", function () {
			if (root.getAttribute("data-bid-sealed") === "1") return;
			if (root.getAttribute("data-complete-enabled") !== "1") {
				toast("Resolve all pricing issues before completing Price Schedule.");
				return;
			}
			btn.disabled = true;
			call("kentender_procurement.tender_configurations.complete_price_schedule", {
				published_tender_ref: root.getAttribute("data-publication-ref"),
			})
				.then(function () {
					toast("Price Schedule complete — returning to checklist…");
					window.setTimeout(function () {
						window.location.href =
							root.getAttribute("data-workspace-url") ||
							root.getAttribute("data-section-url") ||
							"/";
					}, 350);
				})
				.catch(function (err) {
					toast((err && err.message) || "Could not complete Price Schedule");
					btn.disabled = false;
				});
		});
	}

	function boot() {
		initOverview();
		initEditor();
		initReview();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", boot);
	} else {
		boot();
	}
})();
