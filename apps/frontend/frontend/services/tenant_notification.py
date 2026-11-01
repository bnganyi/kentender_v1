"""Tenant lifecycle email notifications for the central Kentender site.

This module must run on the central site where Tenant Registration is stored.
It does not need to be installed on tenant sites.
"""

import hashlib

import frappe
from frappe import _
from frappe.utils import escape_html, now_datetime


REGISTRATION_DOCTYPE = "Tenant Registration"


def send_tenant_welcome_email(registration_name):
    """Send the welcome email once, after a registration becomes Active.

    Idempotency:
      * Requires the registration to be Active.
      * Uses the existing email_sent_at field as the sent marker.
      * Uses a MariaDB advisory lock to prevent concurrent duplicate sends.
      * If provisioning completed but email sending failed, calling this
        function again retries the notification.
    """

    lock_name = (
        "tenant-email:"
        + hashlib.sha256(
            str(registration_name).encode()
        ).hexdigest()[:48]
    )

    acquired = frappe.db.sql(
        "select get_lock(%s, 0)",
        (lock_name,)
    )

    if not acquired or acquired[0][0] != 1:
        frappe.logger("tenant_notification").info(
            f"Welcome email already being processed for {registration_name}"
        )
        return {
            "success": False,
            "already_processing": True,
            "message": "Welcome email is already being processed.",
        }

    try:
        doc = frappe.get_doc(
            REGISTRATION_DOCTYPE,
            registration_name
        )

        if doc.status != "Active":
            frappe.logger("tenant_notification").warning(
                f"Welcome email skipped for {registration_name}: "
                f"registration status is {doc.status}"
            )
            return {
                "success": False,
                "message": "Registration is not Active; email was not sent.",
            }

        # Idempotency check.
        if doc.get("email_sent_at"):
            return {
                "success": True,
                "already_sent": True,
                "message": "Welcome email was already sent.",
            }

        recipient = (doc.email or "").strip().lower()
        company_name = (doc.company_name or "").strip()
        site = (doc.tenant_site or "").strip().lower()

        administrator_name = (
            (doc.administrator_name or "").strip()
            or "Administrator"
        )

        if not recipient or not company_name or not site:
            raise RuntimeError(
                "Cannot send welcome email: recipient, company name, "
                "or tenant hostname is missing."
            )

        tenant_url = f"https://{site}"

        safe_name = escape_html(administrator_name)
        safe_company = escape_html(company_name)
        safe_email = escape_html(recipient)
        safe_url = escape_html(tenant_url)

        subject = _("Your Kentender workspace is ready")

        message = f"""
        <div style="font-family: Arial, sans-serif;
                    max-width: 650px;
                    margin: 0 auto;
                    color: #333;
                    line-height: 1.6;">

            <h2 style="color: #2457A7;">
                Welcome to Kentender!
            </h2>

            <p>Hello {safe_name},</p>

            <p>
                Your workspace for
                <strong>{safe_company}</strong>
                has been successfully created and is ready to use.
            </p>

            <p>
                You can access your workspace using the link below:
            </p>

            <p style="margin: 24px 0;">
                <a href="{safe_url}"
                   style="background: #2457A7;
                          color: #fff;
                          padding: 12px 22px;
                          text-decoration: none;
                          border-radius: 5px;
                          display: inline-block;">
                    Access Your Workspace
                </a>
            </p>

            <p>
                <strong>Administrator email:</strong>
                {safe_email}
            </p>

            <p>
                Sign in using the password you chose during registration.
                If you cannot sign in, use the password-reset option
                on the login page.
            </p>

            <p>
                For security reasons, Kentender will never ask you to send
                your password by email. Please do not share it.
            </p>

            <p>
                If you need assistance, please contact our support team.
            </p>

            <p>
                Kind regards,<br>
                <strong>Kentender Support Team</strong>
            </p>
        </div>
        """

        # Submit using the outgoing email account configured in Frappe.
        frappe.sendmail(
            recipients=[recipient],
            subject=subject,
            message=message,
            delayed=False,
        )

        # Record successful submission so a retry does not send it again.
        doc.email_sent_at = now_datetime()
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        frappe.logger("tenant_notification").info(
            f"Welcome email submitted for {registration_name} "
            f"to {recipient}"
        )

        return {
            "success": True,
            "already_sent": False,
            "recipient": recipient,
            "message": "Welcome email submitted successfully.",
        }

    finally:
        frappe.db.sql(
            "select release_lock(%s)",
            (lock_name,)
        )
