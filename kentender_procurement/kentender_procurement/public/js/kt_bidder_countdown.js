/**
 * Bidder portal live countdown — ticks every second (text-only DOM update; no network).
 * Elements: [data-kt-countdown][data-deadline="ISO/datetime"]
 * Format matches available_tenders.format_time_remaining: "XXd XXh XXm XXs"
 */
(function () {
	"use strict";

	var SELECTOR = "[data-kt-countdown][data-deadline]";
	var timerId = null;

	function pad2(n) {
		return n < 10 ? "0" + n : String(n);
	}

	function parseDeadline(raw) {
		if (!raw) return null;
		var text = String(raw).trim();
		if (!text) return null;
		// Prefer ISO / "YYYY-MM-DD HH:MM:SS" → Date
		var normalized = text.indexOf("T") >= 0 ? text : text.replace(" ", "T");
		var ms = Date.parse(normalized);
		if (!isNaN(ms)) return ms;
		ms = Date.parse(text);
		return isNaN(ms) ? null : ms;
	}

	function formatRemaining(deadlineMs, nowMs) {
		var secs = Math.floor((deadlineMs - nowMs) / 1000);
		if (secs <= 0) return "0d 00h 00m 00s";
		var days = Math.floor(secs / 86400);
		var rem = secs % 86400;
		var hours = Math.floor(rem / 3600);
		rem = rem % 3600;
		var mins = Math.floor(rem / 60);
		var s = rem % 60;
		return pad2(days) + "d " + pad2(hours) + "h " + pad2(mins) + "m " + pad2(s) + "s";
	}

	function tick() {
		var nodes = document.querySelectorAll(SELECTOR);
		if (!nodes.length) return;
		var now = Date.now();
		for (var i = 0; i < nodes.length; i++) {
			var el = nodes[i];
			var deadlineMs = parseDeadline(el.getAttribute("data-deadline"));
			if (deadlineMs == null) continue;
			var next = formatRemaining(deadlineMs, now);
			if (el.textContent !== next) {
				el.textContent = next;
			}
		}
	}

	function start() {
		tick();
		if (timerId != null) return;
		timerId = window.setInterval(tick, 1000);
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", start);
	} else {
		start();
	}

	// Expose for focused tests / debugging
	window.KTBidderCountdown = {
		formatRemaining: formatRemaining,
		parseDeadline: parseDeadline,
		tick: tick,
	};
})();
