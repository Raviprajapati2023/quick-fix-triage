# QuickFix Triage

An AI support-ticket triage assistant for **QuickFix Home Services**, a home repair company in India.

It reads a customer message (in **English or Hinglish**) and uses the **Google Gemini API** to turn it into a structured ticket: what kind of problem it is, how urgent it is, a one-line summary, and the customer's name and address if they gave them.

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
  "address": null
}
```

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

- **Consistent answers:** `temperature=0`, so the same message gets the same classification.
- **Automatic retries:** if Gemini is busy (429/503 errors), the request is retried with backoff.

## Project structure

```
quick-fix-triage/
├── triage.py          # Main triage logic: triage(message) -> Ticket
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

## Usage

Check that your key works:

```bash
python hello.py
```

Run the triage examples:

```bash
python triage.py
```

Use it from your own code:

```python
from triage import triage

ticket = triage("Kitchen sink is leaking since morning, Ramesh, Andheri West")
print(ticket.category, ticket.urgency)   # Category.plumbing Urgency.medium
print(ticket.model_dump())               # as a plain dict
```

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | none | Your Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-3.1-flash-lite` | The Gemini model to use |
