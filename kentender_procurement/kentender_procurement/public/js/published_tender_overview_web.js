/**
 * A1 Website Published Tender Overview — Start/Continue Bid CTA.
 * Guest Start/Continue uses login link in the template; this script handles authenticated CTA.
 */
(function () {
	"use strict";

	var root = document.querySelector("[data-testid='kt-a1w-overview-root']");
	if (!root) return;

	var START_API = "kentender_procurement.tender_configurations.start_or_get_bid_workspace";
	var publicationRef = root.getAttribute("data-publication-ref") || "";
	var loginUrl = root.getAttribute("data-login-url") || "/login";
	var workspaceUrl = root.getAttribute("data-workspace-url") || "";
	var busy = false;

	function goWorkspace(route) {
		var path = route || workspaceUrl || "";
		if (!path) {
			window.location.href = "/tenders";
			return;
		}
		// Portal A2 checklist (absolute website path)
		if (path.indexOf("/tenders/") === 0) {
			window.location.href = path;
			return;
		}
		if (path.indexOf("http") === 0) {
			window.location.href = path;
			return;
		}
		if (path.indexOf("/app/") === 0) {
			window.location.href = path;
			return;
		}
		window.location.href = "/app/" + path.replace(/^\/+/, "");
	}

	function onPrimaryClick(ev) {
		var btn = ev.target.closest("[data-action='start-bid']");
		if (!btn || !root.contains(btn)) return;
		ev.preventDefault();
		if (busy) return;

		var isGuest = root.getAttribute("data-is-guest") === "1";
		if (isGuest) {
			window.location.href = loginUrl;
			return;
		}
		if (!publicationRef || typeof frappe === "undefined" || !frappe.call) {
			if (workspaceUrl) {
				window.location.href = workspaceUrl;
			}
			return;
		}

		busy = true;
		btn.setAttribute("disabled", "disabled");
		frappe.call({
			method: START_API,
			args: { published_tender_ref: publicationRef },
			callback: function (r) {
				busy = false;
				btn.removeAttribute("disabled");
				var msg = (r && r.message) || {};
				var route = msg.bidder_workspace_route || "";
				if (route) {
					goWorkspace(route);
					return;
				}
				if (workspaceUrl) {
					window.location.href = workspaceUrl;
				}
			},
			error: function () {
				busy = false;
				btn.removeAttribute("disabled");
				if (typeof frappe !== "undefined" && frappe.msgprint) {
					frappe.msgprint(__("Could not open bid workspace. Please try again."));
				}
			},
		});
	}

	root.addEventListener("click", onPrimaryClick);
	root.setAttribute("data-kt-a1w-enhanced", "1");
})();
