import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

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

try:
    response = client.models.generate_content(
        model=MODEL,
        contents="Explain in one line what a support ticket is.",
        config=types.GenerateContentConfig(max_output_tokens=1024),
    )
except errors.APIError as e:
    sys.exit(f"Gemini API error ({e.code}): {e.message}")

if not response.text:
    sys.exit("No text returned by the model.")

print(response.text.strip())
