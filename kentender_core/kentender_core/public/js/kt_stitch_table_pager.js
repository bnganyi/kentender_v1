// Shared Stitch Desk client-side table pager (pairs with kt_stitch_table_footer.js).
frappe.provide("kentender_core.table");

(function () {
	"use strict";

	/**
	 * Bind pagination chrome on $root.
	 * Looks for [data-kt-table-footer] (canonical) or opts.footerSelector.
	 * opts.renderPage(pageRows, state) paints the current page.
	 */
	kentender_core.table.attachPagination = function ($root, opts) {
		opts = opts || {};
		var existing = $root.data("ktTablePagerApi");
		if (existing && existing._bound) {
			if (typeof opts.renderPage === "function") {
				existing._renderPage = opts.renderPage;
			}
			return existing;
		}

		var footerSel = opts.footerSelector || "[data-kt-table-footer]";
		var $footer = $root.find(footerSel).first();
		if (!$footer.length) {
			$footer = $root.find("[data-kt-str-table-footer]").first();
		}
		var state = {
			page: 1,
			pageSize: 20,
			rows: [],
		};
		$root.data("ktTablePager", state);

		function totalPages() {
			var n = state.rows.length;
			if (!n) {
				return 1;
			}
			return Math.max(1, Math.ceil(n / state.pageSize));
		}

		function pageItems(current, pages) {
			if (pages <= 1) {
				return [1];
			}
			if (pages <= 7) {
				var all = [];
				for (var i = 1; i <= pages; i++) {
					all.push(i);
				}
				return all;
			}
			var show = {};
			function mark(p) {
				if (p >= 1 && p <= pages) {
					show[p] = 1;
				}
			}
			mark(1);
			mark(2);
			mark(3);
			mark(pages - 2);
			mark(pages - 1);
			mark(pages);
			mark(current - 1);
			mark(current);
			mark(current + 1);
			var sorted = Object.keys(show)
				.map(function (k) {
					return parseInt(k, 10);
				})
				.sort(function (a, b) {
					return a - b;
				});
			var out = [];
			for (var j = 0; j < sorted.length; j++) {
				if (j > 0 && sorted[j] - sorted[j - 1] > 1) {
					out.push("ellipsis");
				}
				out.push(sorted[j]);
			}
			return out;
		}

		function paintChrome() {
			if (!$footer.length) {
				return;
			}
			var total = state.rows.length;
			var pages = totalPages();
			if (state.page > pages) {
				state.page = pages;
			}
			if (state.page < 1) {
				state.page = 1;
			}
			var start = total ? (state.page - 1) * state.pageSize + 1 : 0;
			var end = Math.min(state.page * state.pageSize, total);
			var rangeText;
			if (!total) {
				rangeText = __("Showing 0 of 0");
			} else if (start === 1 && end === total) {
				rangeText = __("Showing {0} of {1}", [String(total), String(total)]);
			} else {
				rangeText = __("Showing {0}-{1} of {2}", [String(start), String(end), String(total)]);
			}
			$footer.find("[data-kt-footer-range], [data-kt-str-footer-range]").text(rangeText);
			$footer.find("[data-kt-footer-page-size], [data-kt-str-footer-page-size]").val(String(state.pageSize));
			$footer.find("[data-kt-footer-prev], [data-kt-str-footer-prev]").prop("disabled", state.page <= 1);
			$footer
				.find("[data-kt-footer-next], [data-kt-str-footer-next]")
				.prop("disabled", !total || state.page >= pages);

			var $pages = $footer.find("[data-kt-footer-pages], [data-kt-str-footer-pages]");
			if ($pages.length) {
				var btnClass = $footer.hasClass("kt-str-table-footer")
					? "kt-str-footer-page-btn"
					: "kt-stitch-footer-page-btn";
				var ellClass = $footer.hasClass("kt-str-table-footer")
					? "kt-str-footer-ellipsis"
					: "kt-stitch-footer-ellipsis";
				var html = "";
				pageItems(state.page, pages).forEach(function (tok) {
					if (tok === "ellipsis") {
						html +=
							'<span class="' +
							ellClass +
							'" data-kt-footer-ellipsis aria-hidden="true">…</span>';
						return;
					}
					var active = tok === state.page;
					html +=
						'<button type="button" class="' +
						btnClass +
						(active ? " is-active" : "") +
						'" data-kt-footer-page-num="' +
						tok +
						'" data-kt-str-footer-page-num="' +
						tok +
						'" aria-label="' +
						__("Page {0}", [String(tok)]) +
						'"' +
						(active ? ' aria-current="page"' : "") +
						">" +
						tok +
						"</button>";
				});
				$pages.html(html);
			}
		}

		function render() {
			paintChrome();
			var startIdx = (state.page - 1) * state.pageSize;
			var pageRows = state.rows.slice(startIdx, startIdx + state.pageSize);
			if (typeof api._renderPage === "function") {
				api._renderPage(pageRows, state);
			}
		}

		function setRows(rows, resetPage) {
			state.rows = rows || [];
			if (resetPage) {
				state.page = 1;
			}
			render();
		}

		var api = {
			_bound: true,
			_renderPage: opts.renderPage,
			setRows: setRows,
			render: render,
			state: state,
		};
		$root.data("ktTablePagerApi", api);

		if ($footer.length && !$footer.data("ktTablePagerBound")) {
			$footer.data("ktTablePagerBound", 1);
			$footer.on(
				"change.ktTablePager",
				"[data-kt-footer-page-size], [data-kt-str-footer-page-size]",
				function () {
					state.pageSize = parseInt($(this).val(), 10) || 20;
					state.page = 1;
					render();
				}
			);
			$footer.on("click.ktTablePager", "[data-kt-footer-prev], [data-kt-str-footer-prev]", function (e) {
				e.preventDefault();
				if (state.page > 1) {
					state.page -= 1;
					render();
				}
			});
			$footer.on("click.ktTablePager", "[data-kt-footer-next], [data-kt-str-footer-next]", function (e) {
				e.preventDefault();
				if (state.page < totalPages()) {
					state.page += 1;
					render();
				}
			});
			$footer.on(
				"click.ktTablePager",
				"[data-kt-footer-page-num], [data-kt-str-footer-page-num]",
				function (e) {
					e.preventDefault();
					var p = parseInt(
						$(this).attr("data-kt-footer-page-num") ||
							$(this).attr("data-kt-str-footer-page-num"),
						10
					);
					if (!p || p === state.page || p < 1 || p > totalPages()) {
						return;
					}
					state.page = p;
					render();
				}
			);
		}
		return api;
	};
})();
