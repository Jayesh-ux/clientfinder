"""CLIENTFINDER - HTML email rendering engine.

Port of the career-ops HTML-injection core (build-cv-html.mjs /
generate-cover-letter.mjs) into Python, for rich-text client-outreach emails.

Porting rules that carry over verbatim:
  1. Single-pass {{TOKEN}} substitution via re.sub + lambda (NOT iterative
     replace) - a substituted value that itself contains {{TOKEN}} text is
     left literal instead of being re-interpreted.
  2. Escaping applied once, at the leaf. Scalar tokens get escape_html();
     block tokens are built by builder functions that escape their own leaves.
  3. Empty-string means the block disappears (no orphan markup).
  4. URL scheme allowlist (mailto: tel: http: https:) - bare emails get
     mailto:, bare domains get https:// ; a disallowed explicit scheme -> "".
  5. render_strict() raises if any {{TOKEN}} survives substitution.

Nothing here sends anything - it only renders copy. Drafts stay drafts.
"""
import html as _html
import re

TOKEN_RE = re.compile(r"\{\{[A-Z_]+\}\}")
URL_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")
ALLOWED_SCHEMES = ("mailto:", "tel:", "http:", "https:")


def escape_html(text):
    """Escape text for safe interpolation into an HTML email body."""
    if text is None:
        return ""
    return _html.escape(str(text), quote=True)


def sanitize_url(value):
    """Allowlist URL schemes; prepend mailto:/https: for bare inputs.

    Mirrors career-ops build-cv-html.mjs sanitizeUrl. Returns "" for an
    explicit but disallowed scheme so scraped/LLM-derived URLs can never
    inject untrusted schemes into an email a client will click.
    """
    if not value:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    if "@" in s and "://" not in s and s.lower().startswith(("mailto:", " ", "")):
        bare = s.split("mailto:", 1)[-1]
        if re.match(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$", bare):
            return "mailto:" + bare
    m = URL_SCHEME_RE.match(s)
    if m:
        return s if s[: m.end()].lower() in ALLOWED_SCHEMES else ""
    if "@" in s and re.match(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$", s):
        return "mailto:" + s
    return "https://" + s


def as_url(value):
    u = sanitize_url(value)
    return u if u.startswith("http") else sanitize_url("https://" + (value or ""))


def render(html, replacements):
    """Single-pass {{TOKEN}} substitution. Unknown tokens are left literal.

    replacements: dict of the exact string "{{TOKEN}}" -> replacement, or
    token name "TOKEN" -> replacement (normalized to {{TOKEN}} internally).
    """
    if not html:
        return ""
    norm = {}
    for k, v in (replacements or {}).items():
        key = k if k.startswith("{{") else "{{" + k + "}}"
        norm[key] = str(v)
    return TOKEN_RE.sub(lambda m: norm.get(m.group(0), m.group(0)), html)


def render_strict(html, replacements):
    """Single-pass substitution that raises on any surviving {{TOKEN}}.

    Fail loudly instead of leaking a placeholder like {{BUSINESS_NAME}} into a
    client's inbox.
    """
    out = render(html, replacements)
    unresolved = sorted({t for t in TOKEN_RE.findall(out)})
    if unresolved:
        raise ValueError("Unresolved placeholders: " + ", ".join(unresolved))
    return out


# ----------------------------------------------------------------- build blocks

def build_contact_line(items):
    """Join present contact items with a render-safe separator.

    items: iterable of (kind, value) where kind in {phone, email, url, text}.
    Missing entries drop BOTH their element and the separator (for building
    the block, we only add a separator between present items).
    """
    parts = []
    for kind, value in items:
        if not value:
            continue
        v = escape_html(value)
        if kind == "email":
            href = sanitize_url(value)
            parts.append(f'<a href="{escape_html(href)}" style="color:#2563eb;text-decoration:none;">{v}</a>' if href else v)
        elif kind == "phone":
            tel = sanitize_url("tel:" + re.sub(r"\s+", "", str(value)))
            parts.append(f'<a href="{escape_html(tel)}" style="color:#2563eb;text-decoration:none;">{v}</a>' if tel else v)
        elif kind == "url":
            href = as_url(value)
            parts.append(f'<a href="{escape_html(href)}" style="color:#2563eb;text-decoration:none;">{v}</a>' if href else v)
        else:
            parts.append(v)
    return '<span style="color:#9ca3af;">&nbsp;|&nbsp;</span>'.join(parts)