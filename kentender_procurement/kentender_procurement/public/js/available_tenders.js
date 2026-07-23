/**
 * A0 Available Tenders — progressive enhancement only.
 * Filters work via GET without this script.
 */
(function () {
	"use strict";
	var root = document.querySelector("[data-testid='kt-a0-tenders-root']");
	if (!root) return;
	root.setAttribute("data-kt-a0-enhanced", "1");
})();
