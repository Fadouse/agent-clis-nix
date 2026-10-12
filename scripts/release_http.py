"""Read official release metadata without sending GitHub tokens to other hosts."""

import json
import os
import urllib.parse
import urllib.request


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Fadouse-agent-clis-updater"})
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme == "https" and parsed.netloc == "api.github.com":
        if token := os.environ.get("GH_TOKEN"):
            # Authenticate this request only; do not forward secrets on redirects.
            request.add_unredirected_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def fetch_json(url: str):
    return json.loads(fetch(url))
