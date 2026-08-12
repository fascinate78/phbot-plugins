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

EMBED_COLOR = 0x5865F2  # Discord blurple
DISCORD_EMBED_LIMIT = 10
DESCRIPTION_MAX = 4000


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
    body = re.sub(r"^###\s+(.+)$", r"**\1**", body, flags=re.MULTILINE)
    if len(body) > DESCRIPTION_MAX:
        body = body[: DESCRIPTION_MAX - 20] + "\n... (kirpildi)"
    return plugin_name, version, body


def build_embeds(changed_files, repo, sha):
    embeds = []
    for path in changed_files:
        path = path.strip()
        if not path or not path.endswith("changelog.md") or not os.path.exists(path):
            continue
        parsed = parse_changelog(path)
        if not parsed:
            continue
        plugin_name, version, body = parsed
        embeds.append(
            {
                "title": f"{plugin_name} - {version}",
                "url": f"https://github.com/{repo}/blob/{sha}/{path}",
                "description": body,
                "color": EMBED_COLOR,
                "footer": {"text": "phBot Plugins Changelog"},
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
