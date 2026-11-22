import os
import requests

TEAM_FOR_CATEGORY = {
    "electrical": "Electrician team",
    "plumbing": "Plumber team",
    "appliance": "Appliance team",
    "billing": "Accounts desk",
    "other": "Front desk",
}


def send_alert(ticket):
    url = os.getenv("ALERT_WEBHOOK_URL")
    if not url:
        print("No ALERT_WEBHOOK_URL set, would have alerted:", ticket.get("summary"))
        return False
    message = f"URGENT {ticket['category']}: {ticket['summary']} | Address: {ticket.get('address')}"
    requests.post(url, json={"text": message}, timeout=10)
    return True


def apply_rules(ticket):
    ticket["assigned_to"] = TEAM_FOR_CATEGORY.get(ticket.get("category"), "Front desk")
    ticket["alert_sent"] = False
    if ticket.get("urgency") == "high":
        ticket["alert_sent"] = send_alert(ticket)
    return ticket