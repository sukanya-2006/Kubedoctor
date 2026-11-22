import re

# Values stop at whitespace, quotes, commas and semicolons so we don't swallow
# the end of a JSON string or a sentence.
_VALUE = r"[^\s\"',;]+"

PATTERNS = [
    # private key blocks
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
     "[REDACTED PRIVATE KEY]"),
    # connection strings with credentials: scheme://user:pass@host
    (re.compile(r"([a-zA-Z][a-zA-Z0-9+.-]*://)[^\s/:@]+:[^\s/@]+@"), r"\1[REDACTED]@"),
    # key=value or key: value for sensitive-looking names
    (re.compile(
        r"(?i)\b([\w.-]*(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|auth)[\w.-]*)"
        r"(\s*[=:]\s*)" + _VALUE),
     r"\1\2[REDACTED]"),
    # authorization headers
    (re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"), r"\1 [REDACTED]"),
    # well-known token shapes
    (re.compile(r"\bgsk_[A-Za-z0-9]{20,}"), "[REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"), "[REDACTED]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), "[REDACTED]"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), "[REDACTED]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"), "[REDACTED JWT]"),
    (re.compile(r"https://hooks\.slack\.com/services/\S+"), "[REDACTED WEBHOOK]"),
    # email addresses
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
]


def redact(text):
    text = str(text or "")
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text