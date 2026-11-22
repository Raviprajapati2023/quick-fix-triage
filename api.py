from fastapi import FastAPI
from pydantic import BaseModel
from triage import triage
from rules import apply_rules

app = FastAPI(title="QuickFix Triage API")


class IncomingMessage(BaseModel):
    text: str
    channel: str = "email"


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
    return ticket