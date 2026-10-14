"""Phase 2 spike S9 (tracker CM8-210): on a site without the tendering apps, which seams are absent, and does absence fail closed?"""

from __future__ import annotations

import frappe

from kentender_contracts.spike import native, signing

HOOKS = ("kt_trust_signing_services", "kt_award_contracting_receivers", "kt_supplier_account_provider", "kt_my_work_providers", "kt_portal_surfaces")


def s9_independence() -> list[dict]:
	apps = frappe.get_installed_apps()
	native.record("S9.installed_apps", apps=apps, tendering_apps_present=[a for a in apps if a in ("kentender_procurement", "kentender_strategy", "kentender_budget")])
	native.record("S9.seams_present_on_this_site", hooks={h: [str(p) for p in (frappe.get_hooks(h) or [])] for h in HOOKS})
	native.record("S9.signing_provider_absent_fails_closed", provider=(type(signing.provider()).__name__ if signing.provider() else None),
		outcome=signing.sign("someone@example.test", "agreement-1", "0" * 64, "S9-CORR")["outcome"])
	doctypes = ("Tender", "Bid", "Award Case", "Evaluation Case", "Procurement Commitment", "Funding Reservation")
	native.record("S9.tendering_doctypes_absent_without_error", absent=[d for d in doctypes if not frappe.db.exists("DocType", d)], present=[d for d in doctypes if frappe.db.exists("DocType", d)])
	native.record("S9.contract_records_work_here", case_doctype=bool(frappe.db.exists("DocType", "Contract Case")), supplier_provider_hook_present=bool(frappe.get_hooks("kt_supplier_account_provider")))
	return native.save("s9_independence")
