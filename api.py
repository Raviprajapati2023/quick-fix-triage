from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import db
from rules import TEAM_FOR_CATEGORY, apply_rules
from triage import Category, Urgency, triage

app = FastAPI(title="QuickFix Triage API")
db.init_db()


class IncomingMessage(BaseModel):
    text: str
    channel: str = "email"


class Review(BaseModel):
    reviewed_by: str
    # Leave a field out to keep the AI's value.
    category: Optional[Category] = None
    urgency: Optional[Urgency] = None
    assigned_to: Optional[str] = None
    summary: Optional[str] = None
    customer_name: Optional[str] = None
    address: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/triage")
def triage_message(msg: IncomingMessage):
    try:
        ticket = triage(msg.text).model_dump(mode="json")
        ticket = apply_rules(ticket)
        ticket["status"] = "ok"
    except Exception:
        ticket = {"status": "needs_review", "assigned_to": "Front desk"}
    ticket["channel"] = msg.channel
    return db.save_ticket(ticket, msg.text)


@app.get("/tickets")
def list_tickets(
    status: Optional[str] = None,
    urgency: Optional[Urgency] = None,
    reviewed: Optional[bool] = None,
):
    """Examples: ?status=needs_review   ?urgency=high&reviewed=false"""
    return db.list_tickets(
        status=status,
        urgency=urgency.value if urgency else None,
        reviewed=reviewed,
    )


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int):
    ticket = db.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.patch("/tickets/{ticket_id}")
def review_ticket(ticket_id: int, review: Review):
    if db.get_ticket(ticket_id) is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    changes = review.model_dump(mode="json", exclude_none=True, exclude={"reviewed_by"})
    # A new category means a new team, unless the reviewer picked one.
    if "category" in changes and "assigned_to" not in changes:
        changes["assigned_to"] = TEAM_FOR_CATEGORY[changes["category"]]

    return db.review_ticket(ticket_id, review.reviewed_by, changes)
