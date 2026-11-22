from kubedoctor.redact import redact

fake_groq = "gsk_" + "a1B2c3D4" * 4
fake_hook = "https://hooks." + "slack.com/services/" + "T000/B000/xxxx"

cases = [
    ("DB_PASSWORD=hunter2 starting up", "hunter2"),
    ("token: abc123xyz connecting", "abc123xyz"),
    ("connecting to postgres://admin:s3cret@db:5432/app", "s3cret"),
    ("Authorization: Bearer abcdefghijklmnop12345", "abcdefghijklmnop12345"),
    (f"key is {fake_groq}", fake_groq),
    (f"webhook {fake_hook}", "T000/B000"),
    ("contact alice@example.com for access", "alice@example.com"),
]

for text, secret in cases:
    out = redact(text)
    assert secret not in out, f"LEAKED: {text!r} -> {out!r}"
    print("ok:", out)

# things that must NOT be changed (these are real clues for the diagnosis)
keep = [
    "FATAL: DB_URL is not set",
    "could not connect to postgres at db:5432 (connection refused)",
    "Back-off pulling image nginx:does-not-exist",
    "Failed to pull image: not found",
]
for text in keep:
    assert redact(text) == text, f"OVER-REDACTED: {text!r} -> {redact(text)!r}"
    print("kept:", text)

print("\nall redaction tests passed")