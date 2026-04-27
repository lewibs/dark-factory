---
name: generate-mermaid-ink-url
description: "How to turn a Mermaid diagram string into a tappable mermaid.ink render URL using Python's standard library base64 module."
user-invocable: false
---
## When to use

When you need to share or display a Mermaid diagram as an image URL — for example, to push a tappable link to a developer's phone, embed it in a notification, or add it to a doc — without making any HTTP requests locally.

## Steps

1. **Extract the diagram text** — obtain the raw Mermaid diagram content (without fences) as a plain string.

2. **Validate input** — if the string is empty or whitespace-only, raise (or return) an error rather than generating a broken URL.

3. **Base64-encode with URL-safe alphabet** — use `base64.urlsafe_b64encode`, not the standard `base64.b64encode`, because `mermaid.ink` expects URL-safe encoding:

   ```python
   import base64
   encoded = base64.urlsafe_b64encode(mermaid_string.encode("utf-8")).decode("utf-8")
   url = f"https://mermaid.ink/img/{encoded}"
   ```

4. **Return or print the URL** — no HTTP request is made locally; the browser renders the diagram when the user taps the link.

## Notes

- Use `urlsafe_b64encode` (replaces `+` → `-` and `/` → `_`). Standard `b64encode` will produce a broken URL because `+` and `/` are not URL-safe without percent-encoding.
- The script at `scripts/mermaid_to_image.py` implements this pattern; import or call it rather than re-implementing inline.
- `mermaid.ink` is treated as an external black box — do not depend on its availability for correctness tests; unit tests should only assert the URL structure (`startswith("https://mermaid.ink/img/")`).
- Padding characters (`=`) from base64 output are harmless in the URL for `mermaid.ink`, but if a future service requires padding-free encoding, strip them with `.rstrip("=")`.
