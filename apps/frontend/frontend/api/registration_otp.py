
import hashlib
import hmac
import secrets
import re

import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date, validate_email_address

from frappe.core.doctype.sms_settings.sms_settings import (
    _send_sms as frappe_send_sms,
)


OTP_DOCTYPE = "Registration OTP Challenge"
OTP_TTL_MINUTES = 5
MAX_ATTEMPTS = 5


def _email(value):
    return (value or "").strip().lower()


def _phone(value):
    value = (value or "").strip()

    # Preserve the international prefix and remove formatting characters.
    phone = ("+" if value.startswith("+") else "") + re.sub(r"\D", "", value)

    return phone


def _otp_hash(challenge_name, channel, code):
    secret = frappe.conf.get("tenant_registration_otp_secret")

    if not secret:
        raise RuntimeError(
            "Configure tenant_registration_otp_secret in site_config.json"
        )

    message = f"{challenge_name}:{channel}:{code}".encode()

    return hmac.new(
        secret.encode(),
        message,
        hashlib.sha256,
    ).hexdigest()


def _send_email(email, code):
    frappe.sendmail(
        recipients=[email],
        subject="Your Kentender verification code",
        message=(
            "<p>Your Kentender registration verification code is:</p>"
            f"<p style='font-size:24px;font-weight:bold;letter-spacing:4px'>"
            f"{frappe.utils.escape_html(code)}</p>"
            f"<p>This code expires in {OTP_TTL_MINUTES} minutes. "
            "If you did not request it, ignore this email.</p>"
        ),
        now=True,
    )



def _send_sms(phone, code):
    """
    Send registration OTP through the configured SMS gateway.
    Raise an exception if no SMS provider is configured.
    """

    message = (
        f"Your Kentender verification code is {code}. "
        f"It expires in {OTP_TTL_MINUTES} minutes."
    )

    # A custom send_sms hook takes precedence over the standard gateway.
    sms_hooks = frappe.get_hooks("send_sms")

    gateway_url = frappe.db.get_single_value(
        "SMS Settings",
        "sms_gateway_url"
    )

    if not sms_hooks and not gateway_url:
        raise RuntimeError(
            "SMS gateway is not configured in Frappe SMS Settings."
        )

    return frappe_send_sms(
        receiver_list=[phone],
        msg=message,
        sender_name="Kentender",
        success_msg=False,
    )


def _challenge_for(email, phone):
    challenge = frappe.get_doc({
        "doctype": OTP_DOCTYPE,
        "email": email,
        "phone": phone,
        "email_verified": 0,
        "sms_verified": 0,
        "email_attempts": 0,
        "sms_attempts": 0,
        "expires_at": add_to_date(
            now_datetime(),
            minutes=OTP_TTL_MINUTES,
        ),
        "verification_token": secrets.token_urlsafe(32),
    })

    challenge.insert(ignore_permissions=True)

    return challenge


@frappe.whitelist(allow_guest=True, methods=["POST"])
def send_registration_otps(email, phone):
    """
    Generate and send separate email and SMS verification codes.

    Both channels must be verified before tenant registration.
    """

    email = _email(email)
    phone = _phone(phone)

    # Validate email.
    if not email or not validate_email_address(email, throw=False):
        frappe.throw(_("Enter a valid email address."))

    # Validate international phone number.
    if (
        not phone.startswith("+")
        or not phone[1:].isdigit()
        or len(phone) < 9
        or len(phone) > 16
    ):
        frappe.throw(
            _(
                "Enter a valid phone number in international format, "
                "e.g. +254712345678."
            )
        )

    # Create challenge.
    challenge = _challenge_for(email, phone)

    # Generate independent six-digit OTPs.
    email_code = f"{secrets.randbelow(1_000_000):06d}"
    sms_code = f"{secrets.randbelow(1_000_000):06d}"

    # Store only HMAC hashes.
    challenge.email_otp_hash = _otp_hash(
        challenge.name,
        "email",
        email_code,
    )

    challenge.sms_otp_hash = _otp_hash(
        challenge.name,
        "sms",
        sms_code,
    )

    challenge.save(ignore_permissions=True)
    frappe.db.commit()

    # Send email independently.
    try:
        _send_email(email, email_code)

    except Exception:
        frappe.log_error(
            title="Registration Email OTP Failure",
            message=frappe.get_traceback(),
        )

        frappe.db.delete(OTP_DOCTYPE, challenge.name)
        frappe.db.commit()

        frappe.throw(
            _("We could not send the email verification code. Please try again later.")
        )

    # Send SMS independently.
    try:
        _send_sms(phone, sms_code)

    except Exception:
        frappe.log_error(
            title="Registration SMS OTP Failure",
            message=frappe.get_traceback(),
        )

        frappe.db.delete(OTP_DOCTYPE, challenge.name)
        frappe.db.commit()

        frappe.throw(
            _("We could not send the SMS verification code. Please try again later.")
        )

    return {
        "verification_token": challenge.verification_token,
        "message": _(
            "Verification codes sent. They expire in five minutes."
        ),
    }


def _verify(token, channel, code):
    """
    Verify either email or SMS OTP.
    """

    if (
        not token
        or not code
        or not str(code).isdigit()
        or len(str(code)) != 6
    ):
        frappe.throw(_("Enter the six-digit verification code."))

    # Find verification challenge.
    doc_name = frappe.db.get_value(
        OTP_DOCTYPE,
        {"verification_token": token},
        "name",
    )

    if not doc_name:
        frappe.throw(
            _("Verification session is invalid or expired.")
        )

    challenge = frappe.get_doc(
        OTP_DOCTYPE,
        doc_name,
    )

    # Check expiry.
    if challenge.expires_at < now_datetime():
        frappe.throw(
            _("The verification code has expired. Request a new code.")
        )

    verified_field = (
        "email_verified"
        if channel == "email"
        else "sms_verified"
    )

    hash_field = (
        "email_otp_hash"
        if channel == "email"
        else "sms_otp_hash"
    )

    attempts_field = (
        "email_attempts"
        if channel == "email"
        else "sms_attempts"
    )

    # Already verified.
    if challenge.get(verified_field):
        return {
            "verified": True,
            "message": _("This channel is already verified."),
        }

    # Check attempt limit.
    attempts = int(
        challenge.get(attempts_field) or 0
    )

    if attempts >= MAX_ATTEMPTS:
        frappe.throw(
            _("Too many incorrect attempts. Request new codes.")
        )

    # Calculate expected OTP hash.
    expected = _otp_hash(
        challenge.name,
        channel,
        str(code),
    )

    actual = challenge.get(hash_field) or ""

    # Compare hashes safely.
    if not hmac.compare_digest(expected, actual):

        challenge.db_set(
            attempts_field,
            attempts + 1,
            update_modified=False,
        )

        frappe.db.commit()

        frappe.throw(
            _("Incorrect verification code.")
        )

    # Mark channel as verified.
    challenge.db_set(
        verified_field,
        1,
        update_modified=False,
    )

    # Remove used OTP hash.
    challenge.db_set(
        hash_field,
        "",
        update_modified=False,
    )

    frappe.db.commit()

    return {
        "verified": True,
        "message": _("Verification successful."),
    }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def verify_registration_email(token, code):
    return _verify(
        token,
        "email",
        code,
    )


@frappe.whitelist(allow_guest=True, methods=["POST"])
def verify_registration_sms(token, code):
    return _verify(
        token,
        "sms",
        code,
    )

