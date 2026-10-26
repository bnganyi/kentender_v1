import hashlib
import hmac
import secrets
import re
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date, validate_email_address

OTP_DOCTYPE = "Registration OTP Challenge"
OTP_TTL_MINUTES = 5
MAX_ATTEMPTS = 5


def _email(value):
    return (value or "").strip().lower()


def _phone(value):
    value = (value or "").strip()
    return ("+" if value.startswith("+") else "") + re.sub(r"\D", "", value)


def _otp_hash(challenge_name, channel, code):
    secret = frappe.conf.get("tenant_registration_otp_secret")
    if not secret:
        raise RuntimeError("Configure tenant_registration_otp_secret in site_config.json")
    message = f"{challenge_name}:{channel}:{code}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def _send_email(email, code):
    frappe.sendmail(
        recipients=[email],
        subject="Your Kentender verification code",
        message=(
            "<p>Your Kentender registration verification code is:</p>"
            f"<p style='font-size:24px;font-weight:bold;letter-spacing:4px'>{frappe.utils.escape_html(code)}</p>"
            f"<p>This code expires in {OTP_TTL_MINUTES} minutes. If you did not request it, ignore this email.</p>"
        ),
        now=True,
    )


def _send_sms(phone, code):
    # Use Frappe's configured SMS Settings/gateway. No provider credentials are embedded here.
    from frappe.core.doctype.sms_settings.sms_settings import send_sms
    send_sms([phone], f"Your Kentender verification code is {code}. It expires in {OTP_TTL_MINUTES} minutes.")


def _challenge_for(email, phone):
    challenge = frappe.get_doc({
        "doctype": OTP_DOCTYPE,
        "email": email,
        "phone": phone,
        "email_verified": 0,
        "sms_verified": 0,
        "email_attempts": 0,
        "sms_attempts": 0,
        "expires_at": add_to_date(now_datetime(), minutes=OTP_TTL_MINUTES),
        "verification_token": secrets.token_urlsafe(32),
    })
    challenge.insert(ignore_permissions=True)
    return challenge


@frappe.whitelist(allow_guest=True, methods=["POST"])
def send_registration_otps(email, phone):
    """Send separate email and SMS OTPs using the central site's configured channels."""
    email, phone = _email(email), _phone(phone)
    if not validate_email_address(email, throw=False):
        frappe.throw(_("Enter a valid email address."))
    if len(phone) < 8 or len(phone) > 16:
        frappe.throw(_("Enter a valid phone number in international format, e.g. +254712345678."))

    # Don't expose whether an identity is already registered.
    challenge = _challenge_for(email, phone)
    email_code, sms_code = f"{secrets.randbelow(1_000_000):06d}", f"{secrets.randbelow(1_000_000):06d}"
    challenge.email_otp_hash = _otp_hash(challenge.name, "email", email_code)
    challenge.sms_otp_hash = _otp_hash(challenge.name, "sms", sms_code)
    challenge.save(ignore_permissions=True)
    frappe.db.commit()

    try:
        _send_email(email, email_code)
        _send_sms(phone, sms_code)
    except Exception:
        frappe.log_error(title="Registration OTP delivery failed", message=f"OTP delivery failed for challenge {challenge.name}; recipient details omitted.")
        frappe.db.delete(OTP_DOCTYPE, challenge.name)
        frappe.db.commit()
        frappe.throw(_("We could not send a verification code. Please try again later."))

    return {"verification_token": challenge.verification_token, "message": _("Verification codes sent. They expire in five minutes.")}


def _verify(token, channel, code):
    if not token or not code or not str(code).isdigit() or len(str(code)) != 6:
        frappe.throw(_("Enter the six-digit verification code."))
    doc = frappe.db.get_value(OTP_DOCTYPE, {"verification_token": token}, "name")
    if not doc:
        frappe.throw(_("Verification session is invalid or expired."))
    challenge = frappe.get_doc(OTP_DOCTYPE, doc)
    if challenge.expires_at < now_datetime():
        frappe.throw(_("The verification code has expired. Request a new code."))
    verified_field = "email_verified" if channel == "email" else "sms_verified"
    hash_field = "email_otp_hash" if channel == "email" else "sms_otp_hash"
    attempts_field = "email_attempts" if channel == "email" else "sms_attempts"
    if challenge.get(verified_field):
        return {"verified": True, "message": _("This channel is already verified.")}
    attempts = int(challenge.get(attempts_field) or 0)
    if attempts >= MAX_ATTEMPTS:
        frappe.throw(_("Too many incorrect attempts. Request new codes."))
    expected = _otp_hash(challenge.name, channel, str(code))
    actual = challenge.get(hash_field) or ""
    if not hmac.compare_digest(expected, actual):
        challenge.db_set(attempts_field, attempts + 1, update_modified=False)
        frappe.db.commit()
        frappe.throw(_("Incorrect verification code."))
    challenge.db_set(verified_field, 1, update_modified=False)
    challenge.db_set(hash_field, "", update_modified=False)
    frappe.db.commit()
    return {"verified": True, "message": _("Verification successful.")}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def verify_registration_email(token, code):
    return _verify(token, "email", code)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def verify_registration_sms(token, code):
    return _verify(token, "sms", code)
