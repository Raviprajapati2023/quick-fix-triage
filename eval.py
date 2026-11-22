import csv
from triage import triage

total = 0
category_correct = 0
urgency_correct = 0
missed_urgent = []
failed = []

with open("messages.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        total += 1
        try:
            result = triage(row["text"]).model_dump(mode="json")
        except Exception as e:
            # Count a failed call as wrong on both fields, but keep going.
            print(f"#{row['id']} failed: {e}")
            failed.append(row["id"])
            result = {"category": None, "urgency": None}

        if result["category"] == row["expected_category"]:
            category_correct += 1
        else:
            print(f"#{row['id']} category: expected {row['expected_category']}, got {result['category']}")

        if result["urgency"] == row["expected_urgency"]:
            urgency_correct += 1
        else:
            print(f"#{row['id']} urgency: expected {row['expected_urgency']}, got {result['urgency']}")

        if row["expected_urgency"] == "high" and result["urgency"] != "high":
            missed_urgent.append(row["id"])

print()
print(f"Category correct: {category_correct}/{total}")
print(f"Urgency correct:  {urgency_correct}/{total}")
print(f"Missed urgent messages: {missed_urgent if missed_urgent else 'none'}")
print(f"Failed calls: {failed if failed else 'none'}")
