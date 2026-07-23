/**
 * Officer Bid Submissions stub (internal Procurement rail).
 * Bidder discovery lives on public Website /tenders (A0).
 */
frappe.pages["bid-submissions"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Bid Submissions"),
		single_column: true,
	});
	wrapper.page = page;
	page.main.html(
		'<div class="padding" data-testid="kt-officer-bid-submissions-stub">' +
			"<h3>" +
			__("Officer bid intake") +
			"</h3>" +
			"<p class='text-muted'>" +
			__(
				"This is the internal Bid Submissions queue for officers. Bidder discovery and electronic submission start from the public Available Tenders page."
			) +
			"</p>" +
			'<p><a class="btn btn-primary btn-sm" href="/tenders" data-testid="kt-officer-bid-submissions-open-tenders">' +
			__("Open Available Tenders") +
			"</a></p>" +
			"</div>"
	);
};
