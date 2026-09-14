#!/usr/bin/env python3
"""Write assets/contributions.json from the GitHub search API.

Run by .github/workflows/contributions.yml. The page reads the committed JSON
rather than calling GitHub from the browser, so it renders instantly, needs no
token, and cannot be broken by the API's per-IP search rate limit.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER = os.environ.get("OSS_STATS_USER", "basil-k-aji-dev")
OUT = Path(__file__).resolve().parent.parent / "assets" / "contributions.json"

# Contributions to other people's repositories. Set to "0" to include own repos.
EXCLUDE_OWN = os.environ.get("OSS_STATS_EXCLUDE_OWN", "1") != "0"


def search(query: str) -> dict:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-site",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    total, items = 0, []
    for page in range(1, 11):
        url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(
            {"q": query, "per_page": 100, "page": page}
        )
        request = urllib.request.Request(url, headers=headers)
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                if exc.code in (403, 429) and attempt < 3:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise
        total = payload.get("total_count", 0)
        batch = payload.get("items", [])
        items.extend(batch)
        if len(items) >= total or not batch:
            break
    return {"total": total, "items": items}


def repo_of(item: dict) -> str:
    return item.get("repository_url", "").replace("https://api.github.com/repos/", "")


def main() -> int:
    merged = search(f"is:pr author:{USER} is:merged")
    open_prs = search(f"is:pr author:{USER} is:open")
    everything = search(f"is:pr author:{USER}")

    repos: dict[str, dict] = {}
    shown = {"merged": 0, "open": 0}
    for bucket, payload in (("merged", merged), ("open", open_prs)):
        for item in payload["items"]:
            name = repo_of(item)
            if not name:
                continue
            if EXCLUDE_OWN and name.lower().startswith(f"{USER.lower()}/"):
                continue
            entry = repos.setdefault(name, {"repo": name, "merged": 0, "open": 0, "prs": []})
            entry[bucket] += 1
            shown[bucket] += 1
            entry["prs"].append(
                {
                    "number": item.get("number"),
                    "title": item.get("title", ""),
                    "url": item.get("html_url", ""),
                    "state": bucket,
                    "updated": (item.get("updated_at") or "")[:10],
                }
            )

    ranked = sorted(
        repos.values(),
        key=lambda r: (-(r["merged"] + r["open"]), -r["merged"], r["repo"].lower()),
    )
    for entry in ranked:
        entry["total"] = entry["merged"] + entry["open"]
        entry["prs"].sort(key=lambda p: p["updated"], reverse=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "user": USER,
                "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "excludes_own_repos": EXCLUDE_OWN,
                "merged": shown["merged"],
                "in_review": shown["open"],
                "repo_count": len(repos),
                "all_prs_including_own": everything["total"],
                "repos": ranked,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT} — {shown['merged']} merged, {shown['open']} in review, {len(repos)} repos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
