/* global frappe, $ */
/**
 * Unread count on the Desk sidebar's "Notification" item.
 *
 * Frappe's sidebar renders the bell with no unread marker: its notification code toggles
 * `.notifications-unseen` inside `.notifications-icon`, and neither element exists in the
 * sidebar markup, so a new Notification Log never changes the bell. This adds the marker
 * from the real unread count (read = 0 for the signed-in user) and keeps it current from
 * the realtime "notification" event, route changes, the bell's own mark-as-read actions
 * and a slow poll (realtime is not reachable on every deployment, e.g. the dev server).
 */
(function () {
	"use strict";

	var BADGE_CLASS = "kt-notification-badge";
	var POLL_MS = 60 * 1000;
	var inflight = false;

	function _item() {
		return $(".standard-items-sections .sidebar-notification");
	}

	function _render(count) {
		var $item = _item();
		if (!$item.length) return;
		var $badge = $item.find("." + BADGE_CLASS);
		if (!count) {
			$badge.remove();
			$item.removeAttr("data-kt-unread");
			return;
		}
		var text = count > 99 ? "99+" : String(count);
		if (!$badge.length) {
			var $row = $item.find(".item-anchor").first();
			$badge = $('<span class="' + BADGE_CLASS + '" role="status"></span>').appendTo($row.length ? $row : $item);
		}
		$badge.text(text).attr("aria-label", count + (count === 1 ? " unread notification" : " unread notifications"));
		$item.attr("data-kt-unread", String(count));
	}

	function refresh() {
		if (inflight || !frappe.session || frappe.session.user === "Guest") return;
		if (!_item().length) return;
		inflight = true;
		frappe
			.call({
				method: "frappe.client.get_count",
				type: "GET",
				args: { doctype: "Notification Log", filters: { for_user: frappe.session.user, read: 0 } },
				freeze: false,
				no_spinner: true,
			})
			.then(function (r) {
				_render(Number(r && r.message) || 0);
			})
			.catch(function () {})
			.always(function () {
				inflight = false;
			});
	}

	function install() {
		if (!window.frappe || !frappe.session || !frappe.router) return false;
		if (frappe.session.user === "Guest") return true;

		if (frappe.realtime && frappe.realtime.on) {
			frappe.realtime.on("notification", refresh);
			frappe.realtime.on("indicator_hide", refresh);
		}
		// Reading one notice or all of them is the bell's own request (its click handlers stop propagation, so
		// listen for the request, not the click); recount when it lands.
		$(document).ajaxComplete(function (_event, _xhr, settings) {
			if (/notification_log\.(mark_as_read|mark_all_as_read)/.test((settings && settings.url) || "")) refresh();
		});
		frappe.router.on("change", refresh);
		setInterval(refresh, POLL_MS);
		// The sidebar item is built after the app is ready; try until it exists.
		var tries = 0;
		var timer = setInterval(function () {
			tries += 1;
			if (_item().length) {
				clearInterval(timer);
				refresh();
			} else if (tries > 40) {
				clearInterval(timer);
			}
		}, 500);
		return true;
	}

	$(function () {
		if (!install()) {
			$(document).one("startup", install);
		}
	});
})();
