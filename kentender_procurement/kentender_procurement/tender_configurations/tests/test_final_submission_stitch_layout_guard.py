# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Static layout guard — Final Submission Stitch 01–05 fidelity."""

from __future__ import annotations

import unittest
from pathlib import Path

_APP = Path(__file__).resolve().parents[2]
_WWW = _APP / "www" / "tenders"
_JS = _APP / "public" / "js"
_CSS = _APP / "public" / "css"
_HOOKS = _APP / "hooks.py"


def _read(path: Path) -> str:
	return path.read_text(encoding="utf-8")


class TestFinalSubmissionStitchLayoutGuard(unittest.TestCase):
	def test_review_and_validate_markers(self) -> None:
		html = _read(_WWW / "review_and_validate.html")
		self.assertIn('data-testid="kt-fs-rav-root"', html)
		self.assertIn('data-testid="kt-fs-rav-title"', html)
		self.assertIn("Review & Validate", html)
		self.assertIn("Blocking Issues", html)
		self.assertIn("Section Summary", html)
		self.assertIn("Section", html)
		self.assertIn("Status", html)
		self.assertIn("Issues", html)
		self.assertIn("Last updated", html)
		self.assertIn("Action", html)
		self.assertIn("Back to Checklist", html)
		self.assertIn("Validate again", html)
		self.assertIn("Review Final Bid", html)
		self.assertIn('data-testid="kt-fs-rav-footer"', html)
		self.assertNotIn("cdn.tailwindcss.com", html)

	def test_final_bid_review_markers(self) -> None:
		html = _read(_WWW / "final_bid_review.html")
		self.assertIn('data-testid="kt-fs-fbr-root"', html)
		self.assertIn("Final Bid Review", html)
		self.assertIn('data-testid="kt-fs-fbr-status"', html)
		self.assertIn("Continue to Submit Bid", html)
		self.assertIn("Bid Section Summaries", html)
		self.assertIn("kt-fs-context-grid", html)
		self.assertIn("Offer Type", html)
		self.assertIn('data-testid="kt-fs-fbr-sections"', html)
		self.assertIn("kt-fs-section-card--price", html)
		self.assertNotIn("Form of Tender uses these Price Schedule totals", html)
		self.assertNotIn("Bid totals by currency", html)
		self.assertNotIn("cdn.tailwindcss.com", html)

	def test_submit_bid_markers(self) -> None:
		html = _read(_WWW / "submit_bid.html")
		self.assertIn('data-testid="kt-fs-submit-root"', html)
		self.assertIn("Submit Bid", html)
		self.assertIn("Submission Summary", html)
		self.assertIn("kt-fs-submit-grid", html)
		self.assertIn("Final Declaration", html)
		self.assertIn("I confirm and submit this bid on behalf of the bidder.", html)
		self.assertIn("Submit this bid?", html)
		self.assertIn('data-testid="kt-fs-confirm-dialog"', html)
		self.assertIn("kt-fs-confirm-overlay", html)
		self.assertIn("kt-fs-confirm-card", html)
		self.assertIn('data-testid="kt-fs-confirm-summary"', html)
		self.assertIn('data-testid="kt-fs-confirm-meta-grid"', html)
		self.assertIn('data-testid="kt-fs-confirm-cancel"', html)
		self.assertIn("Authenticated Submitter", html)
		self.assertIn("kt-fs-submitter-card", html)
		self.assertIn("Awaiting Confirmation", html)
		self.assertNotIn("cdn.tailwindcss.com", html)
		self.assertNotIn("kt-fs-dialog-meta", html)
		self.assertNotIn('class="kt-fs-dialog"', html)

	def test_receipt_markers(self) -> None:
		html = _read(_WWW / "submission_receipt.html")
		self.assertIn('data-testid="kt-fs-receipt-root"', html)
		self.assertIn("Receipt Summary", html)
		self.assertIn("Receipt Reference", html)
		self.assertIn("kt-fs-receipt-hero", html)
		self.assertIn("kt-fs-receipt-grid", html)
		self.assertIn("kt-fs-receipt-totals-card", html)
		self.assertIn('data-testid="kt-fs-receipt-legal"', html)
		self.assertIn('data-testid="kt-fs-receipt-info"', html)
		self.assertIn("Print Receipt", html)
		self.assertIn("Download Receipt", html)
		self.assertIn("Return to My Bids", html)
		self.assertIn('data-testid="kt-fs-receipt-code"', html)
		self.assertNotIn("cdn.tailwindcss.com", html)
		self.assertNotIn("seal_hash", html)

	def test_css_footer_contract(self) -> None:
		css = _read(_CSS / "final_submission_web.css")
		self.assertIn("position: fixed", css)
		self.assertIn("left: var(--kt-a2-sidebar", css)
		# Primary CTA text must stay white inside footer (not inherit #515f74)
		self.assertIn(".kt-fs-footer .kt-fs-btn--primary", css)
		self.assertIn("color: #fff !important", css)
		self.assertNotIn(".kt-fs-footer > a {", css)
		self.assertIn("kt-fs-context-grid", css)
		self.assertIn("kt-fs-section-card--price", css)
		self.assertIn("kt-fs-submit-grid", css)
		self.assertIn("kt-fs-submitter-card", css)

	def test_tp_approach_hides_evidence_type_slugs(self) -> None:
		html = _read(
			_APP / "templates" / "includes" / "technical_proposal" / "kt_tp_approach.html"
		)
		self.assertIn("kt-tp-evidence-title", html)
		self.assertNotIn("item.evidence_type", html)

	def test_js_submit_and_validate(self) -> None:
		js = _read(_JS / "final_submission_web.js")
		self.assertIn("submit_electronic_bid", js)
		self.assertIn("get_bid_submission_readiness", js)
		self.assertIn("declaration_confirmed", js)
		self.assertIn("print", js)

	def test_hooks_routes_before_section_catchall(self) -> None:
		hooks = _read(_HOOKS)
		rav = hooks.index("review-and-validate")
		submit = hooks.index("submit-bid")
		receipt = hooks.index("submission-receipt")
		catchall = hooks.index('"/tenders/<publication_ref>/sections/<section_key>"')
		self.assertLess(rav, catchall)
		self.assertLess(submit, catchall)
		self.assertLess(receipt, catchall)
