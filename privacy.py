"""Privacy layer: mask personal data BEFORE any text is sent to an AI model.

Why this exists: the PwC role involves "handling confidential information".
Showing a working redaction step is the clearest proof you take that seriously.
"""
import re

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d{1,3}[\s-]?)?(?:\d[\s-]?){9,11}\d(?!\w)")


def build_name_map(names):
    """Map real names -> neutral placeholders (Person A, Person B ...)."""
    mapping = {}
    for i, name in enumerate(sorted({n for n in names if isinstance(n, str) and n.strip()})):
        mapping[name] = f"Person {chr(65 + i % 26)}{'' if i < 26 else i // 26}"
    return mapping


def mask_text(text, name_map):
    """Replace emails, phone numbers and known names with placeholders."""
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    # Longest names first so "Anita Rao" is replaced before "Anita"
    for real in sorted(name_map, key=len, reverse=True):
        text = re.sub(re.escape(real), name_map[real], text, flags=re.IGNORECASE)
        first = real.split()[0]
        if len(first) > 2:
            text = re.sub(rf"\b{re.escape(first)}\b", name_map[real], text, flags=re.IGNORECASE)
    return text


def unmask_text(text, name_map):
    """Put real names back into the AI output (done locally, never sent out)."""
    for real, placeholder in name_map.items():
        text = text.replace(placeholder, real)
    return text
