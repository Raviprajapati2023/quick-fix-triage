import csv
from triage import triage
from rules import apply_rules

FIELDS = ["id", "channel", "category", "urgency", "summary",
          "customer_name", "address", "assigned_to", "alert_sent", "status"]

tickets = []

with open("messages.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        try:
            result = triage(row["text"]).model_dump(mode="json")
            result = apply_rules(result)
            result["status"] = "ok"
        except Exception as e:
            print(f"Message {row['id']} failed: {e}")
            result = {"status": "needs_review"}

        result["id"] = row["id"]
        result["channel"] = row["channel"]
        tickets.append(result)
        print(row["id"], result.get("category"), result.get("urgency"))

with open("tickets.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(tickets)

print(f"Saved {len(tickets)} tickets to tickets.csv")