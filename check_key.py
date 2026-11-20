import os
from dotenv import load_dotenv

load_dotenv(override=True)
key = os.getenv("GROQ_API_KEY")

print("key found:", bool(key))
print("starts with gsk_:", key.startswith("gsk_") if key else None)
print("length:", len(key) if key else 0)
print("has spaces or quotes:", any(c in key for c in " \"'") if key else None)