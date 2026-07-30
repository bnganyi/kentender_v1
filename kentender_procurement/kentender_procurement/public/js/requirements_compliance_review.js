/**
 * Requirements Compliance — review Complete Section (returns to checklist).
 */
(function () {
	function root() {
		return document.querySelector("[data-testid='kt-rc-review-root']");
	}

	function toast(msg) {
		var el = document.querySelector("[data-testid='kt-rc-review-toast']");
		if (!el) {
			window.alert(msg);
			return;
		}
		el.textContent = msg;
		el.hidden = false;
		el.classList.add("is-visible");
		clearTimeout(toast._t);
		toast._t = setTimeout(function () {
			el.classList.remove("is-visible");
		}, 3200);
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
				// Keep KT_RC_* errors in the page toast — avoid the Desk exception modal.
				error_handlers: {},
				callback: function (r) {
					if (r && r.exc) {
						var msg =
							(r._server_messages && r._server_messages) ||
							(r.message && r.message._error_message) ||
							"";
						try {
							var parsed = typeof r._server_messages === "string" ? JSON.parse(r._server_messages) : null;
							if (parsed && parsed.length) {
								var first = typeof parsed[0] === "string" ? JSON.parse(parsed[0]) : parsed[0];
								msg = (first && (first.message || first.title)) || msg;
							}
						} catch (e) {
							/* keep msg */
						}
						reject(new Error(msg || "Request failed"));
						return;
					}
					resolve((r && r.message) || r);
				},
				error: function (err) {
					var msg = "Request failed";
					try {
						if (err && err.message) msg = err.message;
						if (err && err._server_messages) {
							var parsed = JSON.parse(err._server_messages);
							if (parsed && parsed[0]) {
								var first = typeof parsed[0] === "string" ? JSON.parse(parsed[0]) : parsed[0];
								msg = (first && first.message) || msg;
							}
						}
					} catch (e) {
						/* keep msg */
					}
					reject(new Error(msg));
				},
			});
		});
	}

	function completeSection() {
		var r = root();
		if (!r || r.getAttribute("data-bid-sealed") === "1") return;
		if (r.getAttribute("data-complete-enabled") !== "1") {
			toast("Complete all applicable required responses before completing this section.");
			return;
		}
		var btn = r.querySelector("[data-testid='kt-rc-complete-btn']");
		if (btn) btn.disabled = true;
		var pub = r.getAttribute("data-publication-ref");
		call("kentender_procurement.tender_configurations.complete_requirements_compliance_section", {
			published_tender_ref: pub,
		})
			.then(function () {
				toast("Section complete — returning to checklist…");
				window.setTimeout(function () {
					// Checklist is the section orchestrator; do not loop back into the RC matrix.
					window.location.href =
						r.getAttribute("data-workspace-url") || r.getAttribute("data-section-url") || "/";
				}, 350);
			})
			.catch(function (err) {
				var msg = (err && err.message) || "Could not complete section";
				// Strip internal error titles from toast copy.
				if (msg.indexOf("KT_RC_") === 0) {
					msg = "Complete all applicable required responses before completing this section.";
				}
				toast(msg);
				if (btn) btn.disabled = r.getAttribute("data-complete-enabled") !== "1";
			});
	}

	document.addEventListener("click", function (ev) {
		var t = ev.target;
		if (!t) return;
		if (t.closest("[data-testid='kt-rc-complete-btn']")) {
			ev.preventDefault();
			completeSection();
		}
	});
})();
