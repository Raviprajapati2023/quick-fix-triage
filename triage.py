import os
import sys
from enum import Enum
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

load_dotenv()  # reads .env into environment

if not os.getenv("GEMINI_API_KEY"):
    sys.exit("GEMINI_API_KEY is not set. Add it to your .env file.")

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

# Picks up GEMINI_API_KEY automatically; retries temporary 429/5xx errors with backoff.
client = genai.Client(
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=5, initial_delay=2.0, max_delay=30.0)
    )
)


class Category(str, Enum):
    electrical = "electrical"
    plumbing = "plumbing"
    appliance = "appliance"
    billing = "billing"
    other = "other"


class Urgency(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Ticket(BaseModel):
    category: Category
    urgency: Urgency
    summary: str  # one short line in English
    customer_name: Optional[str]
    address: Optional[str]


# The JSON shape is enforced by response_schema below, so the prompt only
# needs to explain *how* to fill the fields.
SYSTEM_PROMPT = """You are a support triage assistant for QuickFix Home Services,
a home repair company in India. Messages may be in English or Hinglish.

Read ONE customer message and classify it.
- summary: one short line in English.
- customer_name / address: fill in only if the customer mentions them, otherwise null.

Urgency rules:
- high: danger to people or property. Sparks, burning smell, gas, water flooding,
  or a broken appliance that affects medicine or health.
- medium: something is broken but not dangerous.
- low: questions, billing, bookings, feedback.
"""


def triage(message: str) -> Ticket:
    """Classify one customer message into a Ticket."""
    response = client.models.generate_content(
        model=MODEL,
        contents=message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",  # forces pure JSON, no ``` fences
            response_schema=Ticket,                 # forces exactly these fields/values
            temperature=0,                          # same message -> same answer
            max_output_tokens=1024,
        ),
    )
    if response.parsed is None:
        raise ValueError(f"Model did not return a valid ticket: {response.text!r}")
    return response.parsed


if __name__ == "__main__":
    samples = [
        "light ka switch dabane pe chingari aati hai, bachche ghar pe hain",
        "I was charged twice for my AC service, invoice QF-2231",
    ]
    for msg in samples:
        try:
            ticket = triage(msg)
            print(ticket.model_dump_json(indent=2))
        except errors.APIError as e:
            print(f"Gemini API error ({e.code}): {e.message}")
        except ValueError as e:
            print(e)
