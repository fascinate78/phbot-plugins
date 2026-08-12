#!/usr/bin/env python3
"""Post Discord embeds for plugin changelog.md files changed in a push.

Reads changed file paths from stdin (one per line), parses the newest
`## vX.Y.Z` section of each plugins/<Plugin>/changelog.md, and posts one
Discord embed per plugin to the webhook in DISCORD_WEBHOOK_URL.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

DISCORD_EMBED_LIMIT = 10
DESCRIPTION_MAX = 4000

CATEGORY_EMOJI = {
    "Added": "\N{SPARKLES}",
    "Improved": "\N{WRENCH}",
    "Fixed": "\N{LADY BEETLE}",
    "Removed": "\N{WASTEBASKET}\N{VARIATION SELECTOR-16}",
}
CATEGORY_COLOR = {
    "Fixed": 0xED4245,  # red
    "Added": 0x57F287,  # green
    "Improved": 0x5865F2,  # blurple
    "Removed": 0x99AAB5,  # gray
}
DEFAULT_COLOR = 0x5865F2


def parse_changelog(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()

    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    plugin_name = os.path.basename(os.path.dirname(path))
    if title_match:
        plugin_name = re.sub(r"\s*changelog\s*$", "", title_match.group(1), flags=re.IGNORECASE).strip()

    sections = re.split(r"^##\s+", text, flags=re.MULTILINE)[1:]
    if not sections:
        return None

    lines = sections[0].strip().splitlines()
    if not lines:
        return None
    version = lines[0].strip()
    body = "\n".join(lines[1:]).strip() or "_(bos changelog girisi)_"

    categories_found = re.findall(r"^###\s+(\w+)\s*$", body, flags=re.MULTILINE)

    def format_heading(match):
        name = match.group(1).strip()
        emoji = CATEGORY_EMOJI.get(name)
        return f"{emoji} **{name}**" if emoji else f"**{name}**"

    body = re.sub(r"^###\s+(.+)$", format_heading, body, flags=re.MULTILINE)
    if len(body) > DESCRIPTION_MAX:
        body = body[: DESCRIPTION_MAX - 20] + "\n... (kirpildi)"

    color = DEFAULT_COLOR
    for category in ("Fixed", "Added", "Improved", "Removed"):
        if category in categories_found:
            color = CATEGORY_COLOR[category]
            break

    return plugin_name, version, body, color


def build_embeds(changed_files, repo, sha):
    embeds = []
    for path in changed_files:
        path = path.strip()
        if not path or not path.endswith("changelog.md") or not os.path.exists(path):
            continue
        parsed = parse_changelog(path)
        if not parsed:
            continue
        plugin_name, version, body, color = parsed
        embeds.append(
            {
                "title": f"\N{PACKAGE} {plugin_name} \N{EM DASH} {version}",
                "url": f"https://github.com/{repo}/blob/{sha}/{path}",
                "description": body,
                "color": color,
                "footer": {"text": "phBot Plugins Changelog"},
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
    return embeds


def send_webhook(webhook_url, embeds):
    for i in range(0, len(embeds), DISCORD_EMBED_LIMIT):
        chunk = embeds[i : i + DISCORD_EMBED_LIMIT]
        payload = json.dumps({"username": "Plugin Changelog", "embeds": chunk}).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (compatible; phbot-plugins-changelog-bot/1.0)",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                print(f"Discord webhook status: {resp.status}")
        except urllib.error.HTTPError as exc:
            print(f"Discord webhook failed: {exc.code} {exc.read().decode('utf-8', 'ignore')}", file=sys.stderr)
            raise


def main():
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("DISCORD_WEBHOOK_URL secret is not set.", file=sys.stderr)
        sys.exit(1)

    repo = os.environ.get("GITHUB_REPOSITORY", "fascinate78/phbot-plugins")
    sha = os.environ.get("GITHUB_SHA", "main")

    changed_files = sys.stdin.read().splitlines()
    embeds = build_embeds(changed_files, repo, sha)

    if not embeds:
        print("Bildirilecek changelog degisikligi yok.")
        return

    send_webhook(webhook_url, embeds)


if __name__ == "__main__":
    main()
