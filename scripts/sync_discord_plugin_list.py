import json
import os
import urllib.request


WEBHOOK_URL = os.environ.get("DISCORD_PLUGIN_WEBHOOK")

if not WEBHOOK_URL:
    raise RuntimeError("DISCORD_PLUGIN_WEBHOOK is not configured.")


with open("manifest.json", "r", encoding="utf-8") as file:
    manifest = json.load(file)


plugins = manifest.get("plugins", [])

if not plugins:
    raise RuntimeError("No plugins found in manifest.json")


plugins = sorted(
    plugins,
    key=lambda plugin: plugin.get("name", "").lower()
)


lines = []

for plugin in plugins:
    name = plugin.get("name", "Unknown Plugin")
    version = plugin.get("version", "?")
    description = plugin.get("description", "")
    download_url = plugin.get("download_url", "")
    changelog_url = plugin.get("changelog_url", "")
    core = plugin.get("core", False)

    if core:
        name_display = f"⭐ {name}"
    else:
        name_display = f"📦 {name}"

    links = []

    if download_url:
        links.append(f"[Download]({download_url})")

    if changelog_url:
        links.append(f"[Changelog]({changelog_url})")

    links_text = " • ".join(links)

    entry = (
        f"**{name_display}** `v{version}`\n"
        f"{description}\n"
        f"{links_text}"
    )

    lines.append(entry)


description = "\n\n".join(lines)


payload = {
    "username": "FascinaTe Plugins",
    "embeds": [
        {
            "title": "🧩 FascinaTe phBot Plugins",
            "description": description,
            "url": "https://github.com/fascinate78/phbot-plugins",
            "footer": {
                "text": f"{len(plugins)} plugins • Automatically synced from GitHub"
            }
        }
    ]
}


data = json.dumps(payload).encode("utf-8")

request = urllib.request.Request(
    WEBHOOK_URL,
    data=data,
    headers={
        "Content-Type": "application/json"
    },
    method="POST"
)


with urllib.request.urlopen(request) as response:
    print(
        f"Discord plugin list sent successfully. "
        f"HTTP {response.status}"
    )
