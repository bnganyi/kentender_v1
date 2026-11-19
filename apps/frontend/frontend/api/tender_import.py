from pathlib import Path

import frappe
import requests


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_available_tenders(
	search="",
	method="",
	reservation="",
	closing="all",
	exact="",
	created_from="",
	created_to="",
	expiry_from="",
	expiry_to="",
	reference="",
):
	"""Aggregate public tender lists from all configured tenant sites."""
	bench_path = Path(frappe.utils.get_bench_path())
	sites_path = bench_path / "sites"
	default_site = str(frappe.conf.get("default_site") or "").strip().lower()
	sites = sorted(
		path.name
		for path in sites_path.iterdir()
		if path.is_dir()
		and (path / "site_config.json").exists()
		and path.name.lower() not in {"kentender", "localhost", "127.0.0.1", default_site}
	)

	all_rows = []
	methods = set()
	reservations = set()
	errors = []
	params = {
		"search": search,
		"method": method,
		"reservation": reservation,
		"closing": closing,
		"exact": exact,
		"created_from": created_from,
		"created_to": created_to,
		"expiry_from": expiry_from,
		"expiry_to": expiry_to,
		"reference": reference,
	}

	for site in sites:
		try:
			url = f"https://{site}/api/method/kentender_procurement.bid_submission.api.get_available_tenders"
			response = requests.get(url, params=params, timeout=8, verify=False)
			response.raise_for_status()
			payload = response.json()
			if payload.get("exc") or payload.get("exception"):
				raise RuntimeError(payload.get("exception") or payload.get("exc") or "Tenant tender request failed")

			message = payload.get("message") or {}
			for row in message.get("rows") or []:
				tenant_url = f"https://{site}"
				href = row.get("href") or ""
				redirect_url = f"{tenant_url}{href}" if href else tenant_url
				all_rows.append({
					**row,
					"tenant_site": site,
					"tenant_url": tenant_url,
					"redirect_url": redirect_url,
				})

			for option in (message.get("options") or {}).get("method") or []:
				value = str(option.get("value") or "").strip()
				if value:
					methods.add(value)
			for option in (message.get("options") or {}).get("reservation") or []:
				value = str(option.get("value") or "").strip()
				if value:
					reservations.add(value)
		except Exception as exc:
			errors.append({"tenant": site, "error": str(exc)})

	count = len(all_rows)
	return {
		"rows": all_rows,
		"count_text": f"{count} Tender{'s' if count != 1 else ''}" if count else "",
		"empty_text": "No tenders match these filters." if not count else "",
		"options": {
			"method": [{"value": "", "label": "All methods"}] + [
				{"value": value, "label": value} for value in sorted(methods)
			],
			"reservation": [{"value": "", "label": "All categories"}] + [
				{"value": value, "label": "No reservation" if value.lower() == "none" else value}
				for value in sorted(reservations)
			],
		},
		"tenant_errors": errors,
	}
