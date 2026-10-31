
"""Background tenant provisioning for Frappe/ERPNext v16.

Run this only as the OS account that owns the Bench. Never expose it directly
as a guest-whitelisted method.
"""

import json
import os
import re
import secrets
import hashlib
import shutil
import subprocess
import tempfile
import urllib.request
import urllib.error

from pathlib import Path

import frappe
from frappe import _
from frappe.utils import now_datetime

from frontend.services.tenant_notification import (
    send_tenant_welcome_email,
)


REGISTRATION_DOCTYPE = "Tenant Registration"

DEFAULT_APPS = [
    "erpnext",
    "kentender_core",
    "kentender_strategy",
    "kentender_budget",
    "kentender_procurement",
    "kentender_suppliers",
    "kentender_governance",
    "kentender_compliance",
    "kentender_stores",
    "kentender_assets",
    "kentender_integrations",
    "kentender_transparency",
]


# ---------------------------------------------------------------------------
# PROVISIONING LOGGING
# ---------------------------------------------------------------------------

def _log(registration_name, step, status, message=None):
    try:
        frappe.get_doc({
            "doctype": "Tenant Provisioning Log",
            "registration": registration_name,
            "step": str(step)[:140],
            "status": status,
            "message": (message or "")[:2000],
        }).insert(ignore_permissions=True)

        frappe.db.commit()

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Tenant Provisioning Log failure"
        )


def _set_status(doc, status, error=None):
    doc.status = status
    doc.provisioning_error = (error or "")[:4000] or None
    doc.save(ignore_permissions=True)
    frappe.db.commit()


# ---------------------------------------------------------------------------
# BENCH CONFIGURATION
# ---------------------------------------------------------------------------

def _bench_path():
    configured = frappe.conf.get("tenant_registration_bench_path")

    if not configured:
        raise RuntimeError(
            "Set tenant_registration_bench_path in the central site's site_config.json"
        )

    bench = Path(configured).expanduser().resolve()

    if not (bench / "apps" / "frappe").is_dir():
        raise RuntimeError("Configured Bench path is invalid")

    if not (bench / "sites").is_dir():
        raise RuntimeError("Configured Bench sites directory was not found")

    if not (bench / "env" / "bin" / "python").exists():
        raise RuntimeError("Configured Bench virtual environment was not found")

    return bench


def _bench_executable(bench):
    configured = frappe.conf.get("tenant_registration_bench_executable")

    candidates = [configured] if configured else []

    candidates += [
        str(bench / "env" / "bin" / "bench"),
        shutil.which("bench"),
        str(Path.home() / ".local/bin/bench"),
    ]

    for candidate in candidates:
        if candidate:
            path = Path(candidate).expanduser()

            if path.is_file():
                return str(path.resolve())

    raise RuntimeError(
        "Bench executable not found; set tenant_registration_bench_executable"
    )


def _run(bench, args, timeout=1800, extra_env=None, input_text=None):
    env = {
        **os.environ,
        "PYTHONUNBUFFERED": "1",
    }

    if extra_env:
        env.update(extra_env)

    result = subprocess.run(
        [
            _bench_executable(bench),
            *[str(x) for x in args],
        ],
        cwd=str(bench),
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
        env=env,
    )

    if result.returncode:
        raise RuntimeError(
            f"Bench command failed (exit {result.returncode}). "
            f"Output tail:\n{result.stdout[-8000:]}"
        )

    return result.stdout


# ---------------------------------------------------------------------------
# TENANT VALIDATION
# ---------------------------------------------------------------------------

def _safe_site(site):
    if not isinstance(site, str) or not re.fullmatch(
        r"[a-z0-9](?:[a-z0-9.-]{0,178}[a-z0-9])?",
        site
    ):
        raise ValueError("Invalid generated site hostname")

    if ".." in site or "/" in site or "\\" in site:
        raise ValueError("Invalid generated site hostname")

    return site


def _allowed_apps():
    raw = frappe.conf.get("tenant_registration_allowed_apps")

    apps = (
        json.loads(raw)
        if isinstance(raw, str)
        else (raw or DEFAULT_APPS)
    )

    if not isinstance(apps, list) or not apps:
        raise RuntimeError(
            "tenant_registration_allowed_apps must be a non-empty JSON list"
        )

    for app in apps:
        if not isinstance(app, str) or not re.fullmatch(
            r"[a-z][a-z0-9_]{1,63}",
            app
        ):
            raise RuntimeError(
                "Invalid app identifier in tenant_registration_allowed_apps"
            )

    if "erpnext" not in apps or "kentender_core" not in apps:
        raise RuntimeError(
            "The allowed apps list must include erpnext and kentender_core"
        )

    return apps


def _site_is_initialized(bench, site):
    return (
        bench / "sites" / site / "site_config.json"
    ).is_file()


# ---------------------------------------------------------------------------
# SITE CREATION
# ---------------------------------------------------------------------------

def _create_site(bench, site):
    # Use a random temporary password for the built-in Administrator account.
    args = [
        "new-site",
        site,
        "--admin-password",
        secrets.token_urlsafe(36),
    ]

    db_root_user = frappe.conf.get("tenant_db_root_user", "root")
    db_root_password = frappe.conf.get("tenant_db_root_password")

    if not db_root_password:
        raise RuntimeError(
            "Missing tenant_db_root_password in the central site configuration"
        )

    if db_root_user:
        args += [
            "--db-root-username",
            db_root_user,
        ]

    args += [
        "--db-root-password",
        db_root_password,
    ]

    _run(bench, args, timeout=1200)


# ---------------------------------------------------------------------------
# TENANT ONBOARDING
# ---------------------------------------------------------------------------

def _run_onboarding(bench, site, payload):
    """
    Write a temporary owner-only payload and invoke the onboarding method.

    IMPORTANT:
    The current method is still in the central frontend app.
    It must be moved to an app installed on the tenant before this command
    can work against a tenant that does not have frontend installed.
    """

    sites_dir = bench / "sites"

    fd, file_name = tempfile.mkstemp(
        prefix=".tenant-onboarding-",
        suffix=".json",
        dir=str(sites_dir)
    )

    try:
        os.fchmod(fd, 0o600)

        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
            handle.flush()
            os.fsync(handle.fileno())

        _run(
            bench,
            [
                "--site",
                site,
                "execute",
                "frontend.services.tenant_onboarding.initialize_tenant_from_file",
            ],
            timeout=900,
            extra_env={
                "KENTENDER_TENANT_PAYLOAD_FILE": file_name,
            },
        )

    finally:
        try:
            os.unlink(file_name)
        except FileNotFoundError:
            pass


# ---------------------------------------------------------------------------
# HOSTAFRICA DNS INTEGRATION
# ---------------------------------------------------------------------------

def _create_hostafrica_dns_record(site):
    """
    Create an A record for a tenant using the HostAfrica DNS API.

    Configuration is read from the central site's site_config.json.
    """

    token = frappe.conf.get("hostafrica_api_token")

    domain_name = frappe.conf.get(
        "hostafrica_domain_name",
        "midas.co.ke"
    )

    zone_id = frappe.conf.get("hostafrica_zone_id")
    domain_id = frappe.conf.get("hostafrica_domain_id")

    service_id = frappe.conf.get(
        "hostafrica_service_id",
        1
    )

    backend = frappe.conf.get(
        "hostafrica_backend",
        "dns_manager"
    )

    ip_address = frappe.conf.get("hostafrica_ip")

    if not all([
        token,
        domain_name,
        zone_id,
        domain_id,
        ip_address,
    ]):
        raise RuntimeError(
            "HostAfrica DNS configuration is incomplete."
        )

    site = _safe_site(site)
    domain_name = domain_name.strip(".").lower()

    if not site.endswith("." + domain_name):
        raise ValueError(
            "Tenant hostname does not belong to the configured DNS domain."
        )

    record_name = site[:-(len(domain_name) + 1)]

    # This implementation supports direct subdomains only.
    if not record_name or "." in record_name:
        raise ValueError(
            "Only direct tenant subdomains are supported."
        )

    payload = {
        "domain_name": domain_name,
        "zone_id": str(zone_id),
        "domain_id": str(domain_id),
        "service_id": int(service_id),
        "backend": backend,
        "record": {
            "id": "",
            "name": record_name,
            "type": "A",
            "content": ip_address,
            "ttl": 1,
            "priority": 1,
            "weight": 1,
            "port": 1,
        },
    }

    request = urllib.request.Request(
        "https://api.hostafrica.com/dns/add-record",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": (
                token if token.lower().startswith("bearer ")
                else f"Bearer {token}"
            ),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:

            response_body = response.read().decode("utf-8")
            result = json.loads(response_body)

    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode(
            "utf-8",
            errors="replace"
        )

        raise RuntimeError(
            f"HostAfrica DNS API returned HTTP {exc.code}: "
            f"{error_body[:1500]}"
        ) from exc

    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Could not connect to HostAfrica DNS API: {exc.reason}"
        ) from exc

    if not isinstance(result, dict) or result.get("status") != "success":
        raise RuntimeError(
            "HostAfrica DNS creation failed: "
            f"{json.dumps(result)[:1500]}"
        )

    return {
        "hostname": site,
        "record_name": record_name,
        "ip_address": ip_address,
        "message": result.get("data", {}).get(
            "message",
            "DNS record created"
        ),
    }


# ---------------------------------------------------------------------------
# SSL CONFIGURATION
# ---------------------------------------------------------------------------

def _configure_tls(site):
    wrapper = "/usr/local/sbin/kentender-configure-tls"

    result = subprocess.run(
        [
            "sudo",
            "-n",
            wrapper,
            site,
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=1200,
        check=False,
    )

    if result.returncode:
        raise RuntimeError(
            f"TLS setup failed (exit {result.returncode}). "
            f"Output tail:\n{result.stdout[-5000:]}"
        )


# ---------------------------------------------------------------------------
# PROVISIONING ENTRY POINT
# ---------------------------------------------------------------------------

def provision_registration(registration_name):
    """Serialize retries with a MariaDB advisory lock."""

    lock_name = (
        "tenant-prov:"
        + hashlib.sha256(
            str(registration_name).encode()
        ).hexdigest()[:48]
    )

    acquired = frappe.db.sql(
        "select get_lock(%s, 0)",
        (lock_name,)
    )

    if not acquired or acquired[0][0] != 1:
        return

    try:
        return _provision_registration_locked(registration_name)

    finally:
        frappe.db.sql(
            "select release_lock(%s)",
            (lock_name,)
        )


def _provision_registration_locked(registration_name):
    """Provision one registration while holding its advisory lock."""

    doc = frappe.get_doc(
        REGISTRATION_DOCTYPE,
        registration_name
    )

    if doc.status == "Active":
        # Provisioning has already completed. Retry only the welcome email
        # if it has not been submitted; do not recreate the tenant.
        try:
            email_result = send_tenant_welcome_email(doc.name)

            if email_result.get("success"):
                _log(
                    doc.name,
                    "Welcome email",
                    "Success",
                    email_result.get("message")
                )
            else:
                _log(
                    doc.name,
                    "Welcome email",
                    "Skipped",
                    email_result.get("message")
                )

        except Exception:
            _log(
                doc.name,
                "Welcome email",
                "Failed",
                frappe.get_traceback()[-1800:]
            )

            frappe.log_error(
                frappe.get_traceback(),
                f"Tenant welcome email retry failed: {doc.name}"
            )

        return

    bench = _bench_path()
    site = _safe_site(doc.tenant_site)
    apps = _allowed_apps()

    base_domain = (
        frappe.conf.get("tenant_registration_base_domain")
        or "midas.co.ke"
    ).strip(".").lower()

    if (
        site == base_domain
        or not site.endswith("." + base_domain)
        or site == frappe.local.site
    ):
        raise ValueError(
            "Generated tenant hostname is outside the configured tenant domain"
        )

    password = doc.get_password("admin_password")

    if not password:
        raise RuntimeError(
            "The registration password is unavailable. "
            "Ask the user to register again."
        )

    _set_status(doc, "Provisioning")

    _log(
        doc.name,
        "Start",
        "Running",
        f"Provisioning {site}"
    )

    payload = {
        "company_name": doc.company_name,
        "country": doc.country,
        "phone": doc.phone,
        "administrator_name": doc.administrator_name,
        "email": doc.email,
        "password": password,
        "currency": doc.currency,
        "financial_year_start": (
            doc.financial_year_start or "07-01"
        ),
        "abbr": (
            frappe.conf.get("tenant_registration_company_abbr")
            or "KT"
        )[:5],
    }

    try:
        # Enable Frappe DNS multitenancy.
        _run(
            bench,
            ["config", "dns_multitenant", "on"],
            timeout=120
        )

        # Create site if it does not exist.
        site_dir = bench / "sites" / site

        if not site_dir.exists():
            _log(
                doc.name,
                "Create site",
                "Running"
            )

            _create_site(bench, site)

        elif not _site_is_initialized(bench, site):
            raise RuntimeError(
                f"An incomplete site directory already exists for {site}; "
                "an administrator must inspect and clean it before retrying."
            )

        # Install required applications.
        for app in apps:
            installed = _run(
                bench,
                [
                    "--site",
                    site,
                    "list-apps",
                ],
                timeout=180
            )

            if re.search(
                rf"(?m)^\s*{re.escape(app)}\s*$",
                installed
            ):
                continue

            _log(
                doc.name,
                f"Install {app}",
                "Running"
            )

            _run(
                bench,
                [
                    "--site",
                    site,
                    "install-app",
                    app,
                ],
                timeout=3600
            )

        # Configure tenant hostname.
        _run(
            bench,
            [
                "--site",
                site,
                "set-config",
                "host_name",
                f"https://{site}",
            ],
            timeout=120
        )

        # Run migrations.
        _run(
            bench,
            [
                "--site",
                site,
                "migrate",
            ],
            timeout=2400
        )

        # Initialize company and administrator.
        _log(
            doc.name,
            "Initialize company and administrator",
            "Running"
        )

        _run_onboarding(
            bench,
            site,
            payload
        )

        # Create DNS record through HostAfrica.
        _log(
            doc.name,
            "Create DNS record",
            "Running"
        )

        dns_result = _create_hostafrica_dns_record(site)

        _log(
            doc.name,
            "Create DNS record",
            "Success",
            json.dumps(dns_result)
        )

        # Configure HTTPS.
        _log(
            doc.name,
            "Configure HTTPS",
            "Running"
        )

        _configure_tls(site)

        # Enable scheduler.
        _run(
            bench,
            [
                "--site",
                site,
                "enable-scheduler",
            ],
            timeout=180
        )

        # Disable maintenance mode.
        _run(
            bench,
            [
                "--site",
                site,
                "set-maintenance-mode",
                "off",
            ],
            timeout=180
        )

        # Clear submitted password only after all steps succeed.
        doc.admin_password = ""
        doc.provisioned_at = now_datetime()
        doc.status = "Active"
        doc.provisioning_error = None

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        _log(
            doc.name,
            "Provisioning complete",
            "Success",
            f"Tenant ready: https://{site}"
        )

        try:
            _send_success_email(doc)

        except Exception:
            _log(
                doc.name,
                "Welcome email",
                "Failed",
                "Tenant is active, but the welcome email could not be sent. "
                "Check Email Queue and error logs."
            )

            frappe.log_error(
                frappe.get_traceback(),
                f"Tenant welcome email failed: {registration_name}"
            )

    except Exception:
        error = frappe.get_traceback()

        _set_status(
            doc,
            "Failed",
            error
        )

        _log(
            doc.name,
            "Provisioning failed",
            "Failed",
            error[-1800:]
        )

        frappe.log_error(
            error,
            f"Tenant provisioning failed: {registration_name}"
        )

        raise


# ---------------------------------------------------------------------------
# SUCCESS EMAIL
# ---------------------------------------------------------------------------

def _send_success_email(doc):
    """Send the welcome email through the dedicated notification service.

    Retained for compatibility with the existing provisioning workflow.
    """

    result = send_tenant_welcome_email(doc.name)

    if not result.get("success"):
        if result.get("already_processing"):
            return

        raise RuntimeError(
            result.get("message", "Welcome email submission failed.")
        )

    return result

