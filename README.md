# QuickFix Triage

An AI support-ticket triage assistant for **QuickFix Home Services**, a home repair company in India.

## What it does

Reads customer messages (**English or Hinglish**), sorts them by type and urgency, assigns a team, and alerts the on-call channel for urgent ones.

Under the hood it uses the **Google Gemini API** to turn each message into a structured ticket: what kind of problem it is, how urgent it is, a one-line summary, and the customer's name and address if they gave them.

## Example

Input (Hinglish):

```
light ka switch dabane pe chingari aati hai, bachche ghar pe hain
```

Output:

```json
{
  "category": "electrical",
  "urgency": "high",
  "summary": "Sparks coming from light switch",
  "customer_name": null,
  "address": null,
  "assigned_to": "Electrician team",
  "alert_sent": true,
  "status": "ok"
}
```

## How to run

First complete the [Setup](#setup) below. Then:

**Batch mode** (CSV in, CSV out):

1. Put messages in `messages.csv`
2. Run:

   ```bash
   python run_batch.py      # results in tickets.csv
   ```

**API mode:**

```bash
uvicorn api:app --reload
```

Open <http://127.0.0.1:8000/docs> in your browser. Click **POST /triage**, then **Try it out**, paste a message, and press **Execute**.

**Measure accuracy** against the expected answers in `messages.csv`:

```bash
python eval.py
```

**Quick checks:**

```bash
python hello.py      # check that your Gemini API key works
python triage.py     # run two sample messages
```

## Results (test set of 12 messages)

- Category correct: __/12
- Urgency correct: __/12
- Missed urgent messages: __

_Run `python eval.py` to get these numbers._

## What a human still checks

- Every ticket with status `"needs_review"`
- Every high-urgency ticket (the AI flags, a person confirms)

## Known limits

- Not tested on pure Hindi or voice notes yet
- Does not reply to customers (by design, version 1)

## Ideas for version 2

- Read WhatsApp and email directly instead of a CSV
- Store tickets in a database

## How it works

- **Structured output:** the code sets Gemini's `response_schema` to the `Ticket` model, so the reply is always valid JSON with exactly these fields:

  | Field | Allowed values |
  |---|---|
  | `category` | `electrical`, `plumbing`, `appliance`, `billing`, `other` |
  | `urgency` | `high`, `medium`, `low` |
  | `summary` | One short line in English |
  | `customer_name` | Name if mentioned, otherwise `null` |
  | `address` | Address if mentioned, otherwise `null` |

- **Urgency rules:**
  - **high:** danger to people or property (sparks, burning smell, gas, flooding, or a broken appliance that affects medicine or health)
  - **medium:** something is broken but not dangerous
  - **low:** questions, billing, bookings, feedback

- **Team assignment:** each category maps to a team (electrical → Electrician team, plumbing → Plumber team, appliance → Appliance team, billing → Accounts desk, other → Front desk).
- **Alerts:** high-urgency tickets are posted to `ALERT_WEBHOOK_URL`. If it isn't set, the alert is printed instead.
- **Failures:** if the AI call fails, the ticket gets status `needs_review` instead of being dropped.
- **Consistent answers:** `temperature=0`, so the same message gets the same classification.
- **Automatic retries:** if Gemini is busy (429/503 errors), the request is retried with backoff.

## Project structure

```
quick-fix-triage/
├── triage.py          # AI triage: triage(message) -> Ticket
├── rules.py           # Team assignment and urgent alerts
├── run_batch.py       # Triage messages.csv -> tickets.csv
├── api.py             # FastAPI app: POST /triage
├── eval.py            # Accuracy check against expected answers
├── messages.csv       # Test messages with expected category/urgency
├── hello.py           # Small script to check your Gemini API key works
├── requirements.txt   # Python dependencies
├── .env.example       # Template for your .env file
└── .gitignore         # Keeps .env and venv/ out of Git
```

## Setup

You need **Python 3.10+** and a **Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey).

```bash
# 1. Clone the repo
git clone https://github.com/Raviprajapati2023/quick-fix-triage.git
cd quick-fix-triage

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API key
copy .env.example .env         # Windows
# cp .env.example .env         # macOS / Linux
```

Then open `.env` and set your key:

```
GEMINI_API_KEY=your-real-key-here
```

> **Never commit `.env`.** It is already listed in `.gitignore`.

## Use it from your own code

```python
from triage import triage

ticket = triage("Kitchen sink is leaking since morning, Ramesh, Andheri West")
print(ticket.category, ticket.urgency)   # Category.plumbing Urgency.medium
print(ticket.model_dump(mode="json"))    # as a plain dict
```

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | none | Your Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-3.1-flash-lite` | The Gemini model to use |
| `ALERT_WEBHOOK_URL` | No | none | Webhook that receives urgent-ticket alerts |
