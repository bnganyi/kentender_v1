import json
import os
import re
import subprocess
import shutil
from pathlib import Path

import frappe
from frappe import _
from frappe.utils import now_datetime

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

def _log(registration_name, step, status, message=None):
    try:
        frappe.get_doc({
            "doctype": "Tenant Provisioning Log",
            "registration": registration_name,
            "step": step[:140],
            "status": status,
            "message": (message or "")[:2000],
        }).insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Tenant Provisioning Log failure")

def _set_status(doc, status, error=None):
    doc.status = status
    if error:
        doc.provisioning_error = error[:4000]
    else:
        doc.provisioning_error = None
    doc.save(ignore_permissions=True)
    frappe.db.commit()

def _bench_path():
    path = frappe.conf.get("tenant_registration_bench_path")
    if not path:
        frappe.throw(_("Set tenant_registration_bench_path in site_config.json."))
    resolved = Path(path).resolve()
    if not (resolved / "apps" / "frappe").is_dir() or not (resolved / "env" / "bin" / "python").exists():
        frappe.throw(_("Configured bench path is invalid."))
    # The worker must run on the same host and OS user as this bench.
    return resolved

def _allowed_apps():
    raw = frappe.conf.get("tenant_registration_allowed_apps")
    if not raw:
        return DEFAULT_APPS
    apps = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(apps, list) or not apps:
        frappe.throw(_("tenant_registration_allowed_apps must be a non-empty JSON list."))
    # Only allow simple app identifiers; never accept an app list from a public request.
    for app in apps:
        if not re.fullmatch(r"[a-z][a-z0-9_]{1,63}", str(app)):
            frappe.throw(_("Invalid app name in tenant_registration_allowed_apps."))
    if "erpnext" not in apps:
        frappe.throw(_("The allowed apps list must include erpnext."))
    return apps

def _bench_executable(bench):
    configured = frappe.conf.get("tenant_registration_bench_executable")
    if configured:
        candidate = Path(configured).expanduser().resolve()
        if candidate.is_file():
            return str(candidate)
        raise RuntimeError("Configured tenant_registration_bench_executable does not exist")
    found = shutil.which("bench")
    if found:
        return found
    fallback = Path.home() / ".local" / "bin" / "bench"
    if fallback.is_file():
        return str(fallback)
    raise RuntimeError("Could not find the Bench executable in PATH or ~/.local/bin/bench")

def _run(bench, args, timeout=1800, input_text=None, extra_env=None):
    command = [_bench_executable(bench), *args]
    child_env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    if extra_env:
        child_env.update(extra_env)
    result = subprocess.run(
        command,
        cwd=str(bench),
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
        env=child_env,
    )
    # Do not log command arguments containing secrets. This command list never includes passwords.
    if result.returncode:
        raise RuntimeError(
            f"Bench command failed (exit {result.returncode}): {' '.join(args)}\n"
            f"{result.stdout[-12000:]}"
        )
    return result.stdout

def _safe_site(site):
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{2,180}", site):
        raise ValueError("Invalid generated site name")
    if ".." in site or site.startswith(".") or site.endswith("."):
        raise ValueError("Invalid generated site name")
    return site

def provision_registration(registration_name):
    """Long-running background job. Never expose this method as a public endpoint."""
    doc = frappe.get_doc(REGISTRATION_DOCTYPE, registration_name)
    if doc.status == "Active":
        return
    if doc.status == "Provisioning":
        # Avoid duplicate concurrent workers. A production deployment should also
        # use a distributed lock for this registration.
        return

    bench = _bench_path()
    site = _safe_site(doc.tenant_site)
    apps = _allowed_apps()
    base_domain = frappe.conf.get("tenant_registration_base_domain", "midas.co.ke").strip(".")
    if not site.endswith("." + base_domain) or site == frappe.local.site:
        raise ValueError("Generated tenant hostname is outside the configured tenant domain")

    _set_status(doc, "Provisioning")
    _log(doc.name, "Start", "Running", f"Creating site {site}")

    try:
        # Ensure DNS multitenancy is enabled at bench level.
        _run(bench, ["config", "dns_multitenant", "on"], timeout=120)

        sites_dir = bench / "sites" / site
        if sites_dir.exists():
            raise RuntimeError(f"Site directory already exists: {site}")

        # Bench may prompt for MariaDB root password; production setup should use
        # configured non-interactive DB credentials or a controlled provisioning account.
        _run(bench, ["new-site", site], timeout=900)

        for app in apps:
            _log(doc.name, f"Install {app}", "Running")
            _run(bench, ["--site", site, "install-app", app], timeout=2400)

        _run(bench, ["--site", site, "set-config", "host_name",
                     f"https://{site}"], timeout=120)
        _run(bench, ["--site", site, "migrate"], timeout=1800)
        _run(bench, ["--site", site, "enable-scheduler"], timeout=120)
        _run(bench, ["--site", site, "set-maintenance-mode", "off"], timeout=120)

        # Initialize company and admin. The encrypted Password field is fetched
        # only inside this worker and passed through stdin to bench execute, not argv.
        admin_password = doc.get_password("admin_password")
        if not admin_password:
            raise RuntimeError("Registration password is unavailable; request a new registration.")
        payload = {
            "company_name": doc.company_name,
            "country": doc.country,
            "administrator_name": doc.administrator_name,
            "email": doc.email,
            "password": admin_password,
            "abbr": (frappe.conf.get("tenant_registration_company_abbr", "KT") or "KT")[:5],
        }
        # Pass the one-time payload via the child process environment rather than
        # command-line arguments. Restrict OS access to the bench worker account.
        _run(
            bench,
            ["--site", site, "execute",
             "kentender_core.services.tenant_onboarding.initialize_tenant_from_env"],
            timeout=600,
            extra_env={"KENTENDER_TENANT_PAYLOAD": json.dumps(payload)},
        )

        # Clear the password from the central registration after provisioning.
        doc.admin_password = ""
        doc.provisioned_at = now_datetime()
        doc.status = "Active"
        doc.provisioning_error = None
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        _log(doc.name, "Provisioning complete", "Success", f"Tenant created: https://{site}")
        _send_success_email(doc)
    except Exception:
        error = frappe.get_traceback()
        _set_status(doc, "Failed", error)
        # Clear stored password on failure too; retries should use a fresh secure
        # password-reset/activation flow rather than retaining credentials.
        try:
            doc.admin_password = ""
            doc.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            pass
        _log(doc.name, "Provisioning failed", "Failed", error[-1800:])
        frappe.log_error(error, f"Tenant provisioning failed: {registration_name}")
        raise

def _send_success_email(doc):
    scheme = frappe.conf.get("tenant_registration_scheme", "https")
    url = f"{scheme}://{doc.tenant_site}"
    subject = _("Your Kentender workspace is ready")
    message = f"""
        <p>Hello {frappe.utils.escape_html(doc.administrator_name)},</p>
        <p>Your workspace for <b>{frappe.utils.escape_html(doc.company_name)}</b> is ready.</p>
        <p><a href="{url}">Open your Kentender workspace</a></p>
        <p>Administrator email: {frappe.utils.escape_html(doc.email)}</p>
        <p>Use the password you supplied during registration. If you cannot sign in, use the password reset option on the tenant login page.</p>
        <p>Regards,<br>Kentender Team</p>
    """
    frappe.sendmail(recipients=[doc.email], subject=subject, message=message, delayed=False)
    doc.email_sent_at = now_datetime()
    doc.save(ignore_permissions=True)
    frappe.db.commit()
