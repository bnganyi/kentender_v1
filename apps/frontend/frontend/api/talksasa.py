
import json
import re

import frappe
import requests


TALKSASA_URL = "https://bulksms.talksasa.com/api/v3/sms/send"


def send_sms(receiver_list, msg, sender_name="", success_msg=True):
    """
    Frappe SMS hook for Talksasa.

    Sends each recipient using the Talksasa JSON REST API.
    """

    token = frappe.conf.get("talksasa_api_token")
    sender_id = frappe.conf.get("talksasa_sender_id") or "TALK-SASA"

    if not token:
        raise RuntimeError("Talksasa API token is not configured.")

    if isinstance(receiver_list, str):
        try:
            receiver_list = json.loads(receiver_list)
        except (ValueError, TypeError):
            receiver_list = [receiver_list]

    if not isinstance(receiver_list, list):
        receiver_list = [receiver_list]

    if not receiver_list:
        raise ValueError("No SMS recipients supplied.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    results = []

    for recipient in receiver_list:
        phone = re.sub(r"\D", "", str(recipient))

        if not phone:
            raise ValueError("Invalid SMS recipient.")

        # Talksasa expects the Kenyan international number without '+'.
        if phone.startswith("0"):
            phone = "254" + phone[1:]

        if not phone.startswith("254") and len(phone) == 9:
            phone = "254" + phone

        payload = {
            "recipient": phone,
            "sender_id": sender_id,
            "type": "plain",
            "message": msg,
        }

        try:
            response = requests.post(
                TALKSASA_URL,
                headers=headers,
                json=payload,
                timeout=20,
            )

            response.raise_for_status()

            try:
                result = response.json()
            except ValueError:
                raise RuntimeError(
                    "Talksasa returned an invalid JSON response."
                )

            # Reject explicit provider-side failures.
            if (
                result.get("status") is False
                or result.get("success") is False
            ):
                raise RuntimeError(
                    "Talksasa rejected the SMS request: "
                    + str(result.get("message", "Unknown provider error"))
                )

            results.append(result)

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Talksasa HTTP request failed: {exc}"
            ) from exc

    return results

