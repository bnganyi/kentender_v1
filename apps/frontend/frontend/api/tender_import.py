
from pathlib import Path
from urllib.parse import urljoin

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
    """Aggregate public tenders and tenant branding from all configured sites."""

    bench_path = Path(frappe.utils.get_bench_path())
    sites_path = bench_path / "sites"

    default_site = str(
        frappe.conf.get("default_site") or ""
    ).strip().lower()

    current_site = str(
        frappe.local.site or ""
    ).strip().lower()

    # Exclude the central portal and non-tenant directories.
    excluded_sites = {
        "kentender",
        "localhost",
        "127.0.0.1",
        default_site,
        current_site,
    }

    sites = sorted(
        path.name
        for path in sites_path.iterdir()
        if path.is_dir()
        and (path / "site_config.json").exists()
        and path.name.lower() not in excluded_sites
    )

    all_rows = []
    all_tenants = []

    methods = set()
    reservations = set()
    errors = []

    # Preserve all existing tender filters.
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
        tenant_url = f"https://{site}"

        try:
            # Request the tenant's published tenders.
            url = urljoin(
                tenant_url + "/",
                "api/method/"
                "kentender_procurement.bid_submission.api."
                "get_available_tenders",
            )

            response = requests.get(
                url,
                params=params,
                timeout=8,
                verify=False,
            )

            response.raise_for_status()

            payload = response.json()

            if payload.get("exc") or payload.get("exception"):
                raise RuntimeError(
                    payload.get("exception")
                    or payload.get("exc")
                    or "Tenant tender request failed"
                )

            message = payload.get("message") or {}

            # -------------------------------------------------
            # TENANT BRANDING
            # -------------------------------------------------

            tenant_image = str(
                message.get("tenant_image") or ""
            ).strip()

            tenant_image_url = (
                urljoin(tenant_url + "/", tenant_image)
                if tenant_image
                else ""
            )

            tenant_rows = message.get("rows") or []

            # Register the tenant independently of its tender count.
            all_tenants.append({
                "tenant_site": site,
                "tenant_url": tenant_url,
                "tenant_image": tenant_image,
                "tenant_image_url": tenant_image_url,
                "has_logo": bool(tenant_image),
                "tender_count": len(tenant_rows),
                "status": "success",
            })

            # -------------------------------------------------
            # TENDER ROWS
            # -------------------------------------------------

            for row in tenant_rows:
                href = row.get("href") or ""

                redirect_url = (
                    urljoin(tenant_url + "/", href)
                    if href
                    else tenant_url
                )

                all_rows.append({
                    **row,
                    "tenant_site": site,
                    "tenant_url": tenant_url,
                    "tenant_image": tenant_image,
                    "tenant_image_url": tenant_image_url,
                    "redirect_url": redirect_url,
                })

            # -------------------------------------------------
            # AGGREGATE FILTER OPTIONS
            # -------------------------------------------------

            options = message.get("options") or {}

            for option in options.get("method") or []:
                value = str(
                    option.get("value") or ""
                ).strip()

                if value:
                    methods.add(value)

            for option in options.get("reservation") or []:
                value = str(
                    option.get("value") or ""
                ).strip()

                if value:
                    reservations.add(value)

        except Exception as exc:
            error_message = str(exc)

            errors.append({
                "tenant": site,
                "error": error_message,
            })

            # Keep failed tenants visible for diagnostics.
            all_tenants.append({
                "tenant_site": site,
                "tenant_url": tenant_url,
                "tenant_image": "",
                "tenant_image_url": "",
                "has_logo": False,
                "tender_count": 0,
                "status": "error",
                "error": error_message,
            })

    # ---------------------------------------------------------
    # RESPONSE
    # ---------------------------------------------------------

    count = len(all_rows)

    return {
        # All published tender rows from reachable tenants.
        "rows": all_rows,

        # All discovered tenants, including those with zero tenders.
        "tenants": all_tenants,

        # Tenant summary.
        "tenant_count": len(all_tenants),

        # Tender summary.
        "count_text": (
            f"{count} Tender{'s' if count != 1 else ''}"
            if count
            else ""
        ),

        "empty_text": (
            "No tenders match these filters."
            if not count
            else ""
        ),

        # Aggregated filter options.
        "options": {
            "method": [
                {"value": "", "label": "All methods"}
            ] + [
                {"value": value, "label": value}
                for value in sorted(methods)
            ],

            "reservation": [
                {"value": "", "label": "All categories"}
            ] + [
                {
                    "value": value,
                    "label": (
                        "No reservation"
                        if value.lower() == "none"
                        else value
                    ),
                }
                for value in sorted(reservations)
            ],
        },

        # Failed tenant requests.
        "tenant_errors": errors,
    }

