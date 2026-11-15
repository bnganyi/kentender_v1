
import frappe

from frappe.core.doctype.user.user import (
    test_password_strength as frappe_test_password_strength,
)


def _get_password_feedback(password, administrator_name, email):
    """
    Run Frappe's native password-strength test.

    Construct user_data as a Python tuple to satisfy Frappe's
    method type validation.
    """

    user_data = (
        administrator_name or "",
        None,
        None,
        email or "",
        None,
    )

    return frappe_test_password_strength(
        new_password=password,
        user_data=user_data,
    )


def validate_admin_password(password, administrator_name, email):
    """
    Validate a tenant administrator password using Frappe's
    configured password policy.
    """

    if not password:
        frappe.throw("Administrator password is required.")

    if len(password) < 12 or len(password) > 256:
        frappe.throw(
            "Password must contain between 12 and 256 characters."
        )

    if not frappe.get_system_settings("enable_password_policy"):
        frappe.throw(
            "Password policy is disabled. Enable it before accepting "
            "tenant registrations."
        )

    result = _get_password_feedback(
        password=password,
        administrator_name=administrator_name,
        email=email,
    )

    feedback = result.get("feedback") or {}

    if not feedback.get("password_policy_validation_passed", False):
        warning = feedback.get("warning") or (
            "Password does not meet the configured security policy."
        )

        suggestions = feedback.get("suggestions") or []

        message = str(warning)

        if suggestions:
            message += "\n" + "\n".join(
                str(item) for item in suggestions
            )

        frappe.throw(
            message,
            title="Password requirements not met",
        )

    return True


@frappe.whitelist(allow_guest=True, methods=["POST"])
def check_registration_password_strength(
    new_password=None,
    administrator_name=None,
    email=None,
):
    """
    Public endpoint for checking password strength during
    tenant registration.

    Only individual string arguments are accepted from the browser.
    The user_data tuple is constructed internally.
    """

    if not new_password:
        return {
            "feedback": {
                "warning": "Password is required.",
                "suggestions": [],
                "password_policy_validation_passed": False,
            }
        }

    if len(new_password) < 12 or len(new_password) > 256:
        return {
            "feedback": {
                "warning": (
                    "Password must contain between 12 and 256 characters."
                ),
                "suggestions": [],
                "password_policy_validation_passed": False,
            }
        }

    if not frappe.get_system_settings("enable_password_policy"):
        return {
            "feedback": {
                "warning": "Password policy is not enabled.",
                "suggestions": [],
                "password_policy_validation_passed": False,
            }
        }

    result = _get_password_feedback(
        password=new_password,
        administrator_name=administrator_name,
        email=email,
    )

    return result

