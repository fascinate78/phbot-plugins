import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


# ============================================================
# CONFIG
# ============================================================

MANIFEST_PATH = Path("manifest.json")

WEBHOOK_URL = os.environ.get(
    "DISCORD_PLUGIN_WEBHOOK",
    ""
).strip()

MESSAGE_ID = os.environ.get(
    "DISCORD_PLUGIN_MESSAGE_ID",
    ""
).strip()

REPOSITORY_URL = (
    "https://github.com/fascinate78/phbot-plugins"
)

WEBHOOK_USERNAME = "FascinaTe Plugins"

EMBED_TITLE = "\U0001f9e9 FascinaTe phBot Plugins"

USER_AGENT = (
    "FascinaTe-phBot-Plugins-GitHub-Action/1.0"
)

# Her embed'de ka癟 plugin g繹sterilecek.
PLUGINS_PER_EMBED = 6

# Discord bir mesajda en fazla 10 embed kabul eder.
MAX_EMBEDS = 10

# Plugin a癟覺klamas覺 癟ok uzunsa k覺salt覺l覺r.
MAX_PLUGIN_DESCRIPTION = 220

# Discord limits the combined text of all embeds in one message to 6000
# characters. Keep a small margin so future metadata changes do not put the
# payload exactly on the API boundary.
MAX_TOTAL_EMBED_CHARACTERS = 5900


# ============================================================
# HELPERS
# ============================================================

def fail(message: str, exit_code: int = 1):
    print(
        f"ERROR: {message}",
        file=sys.stderr
    )
    sys.exit(exit_code)


def truncate(text: str, max_length: int) -> str:
    if not text or max_length <= 0:
        return ""

    text = str(text).strip()

    if len(text) <= max_length:
        return text

    return (
        text[: max_length - 3].rstrip()
        + "..."
    )


# ============================================================
# MANIFEST
# ============================================================

def load_manifest():
    if not MANIFEST_PATH.exists():
        fail(
            f"{MANIFEST_PATH} bulunamad覺."
        )

    try:
        with MANIFEST_PATH.open(
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except json.JSONDecodeError as exc:
        fail(
            f"manifest.json ge癟erli JSON de?il: {exc}"
        )

    except Exception as exc:
        fail(
            f"manifest.json okunamad覺: {exc}"
        )


def get_plugins(manifest):
    if isinstance(manifest, dict):
        plugins = manifest.get(
            "plugins",
            []
        )

    elif isinstance(manifest, list):
        plugins = manifest

    else:
        fail(
            "manifest.json beklenmeyen "
            "bir yap覺ya sahip."
        )

    if not isinstance(plugins, list):
        fail(
            "manifest.json i癟indeki "
            "'plugins' alan覺 liste de?il."
        )

    if not plugins:
        fail(
            "manifest.json i癟inde plugin bulunamad覺."
        )

    return plugins


def plugin_sort_key(plugin):
    return str(
        plugin.get("name")
        or plugin.get("id")
        or ""
    ).lower()


# ============================================================
# PLUGIN FORMAT
# ============================================================

def build_plugin_entry(
    plugin,
    max_description=MAX_PLUGIN_DESCRIPTION
):
    name = (
        plugin.get("name")
        or plugin.get("id")
        or "Unknown Plugin"
    )

    version = str(
        plugin.get("version")
        or "?"
    )

    description = truncate(
        plugin.get("description") or "",
        max_description
    )

    download_url = (
        plugin.get("download_url")
        or ""
    )

    changelog_url = (
        plugin.get("changelog_url")
        or ""
    )

    core = bool(
        plugin.get("core", False)
    )

    icon = "\u2b50" if core else "\U0001f4e6"

    lines = [
        f"**{icon} {name}** `v{version}`"
    ]

    if description:
        lines.append(
            description
        )

    links = []

    if download_url:
        links.append(
            f"[\u2b07\ufe0f Download]({download_url})"
        )

    if changelog_url:
        links.append(
            f"[\U0001f4dd Changelog]({changelog_url})"
        )

    if links:
        lines.append(
            " \u2022 ".join(links)
        )

    return "\n".join(lines)


# ============================================================
# EMBED GROUPS
# ============================================================

def split_plugins_into_groups(plugins):
    groups = []

    for index in range(
        0,
        len(plugins),
        PLUGINS_PER_EMBED
    ):
        group = plugins[
            index:index + PLUGINS_PER_EMBED
        ]

        groups.append(group)

    return groups


def count_embed_characters(embeds):
    total = 0

    for embed in embeds:
        total += len(embed.get("title", ""))
        total += len(embed.get("description", ""))
        total += len(embed.get("author", {}).get("name", ""))
        total += len(embed.get("footer", {}).get("text", ""))

        for field in embed.get("fields", []):
            total += len(field.get("name", ""))
            total += len(field.get("value", ""))

    return total


def build_embeds_with_description_limit(
    plugins,
    max_description
):
    groups = split_plugins_into_groups(
        plugins
    )

    if len(groups) > MAX_EMBEDS:
        fail(
            f"{len(plugins)} plugin i癟in "
            f"{len(groups)} embed gerekiyor. "
            f"Discord tek mesajda en fazla "
            f"{MAX_EMBEDS} embed kabul ediyor."
        )

    core_count = sum(
        1
        for plugin in plugins
        if plugin.get("core", False)
    )

    normal_count = (
        len(plugins) - core_count
    )

    total_pages = len(groups)

    embeds = []

    for page_index, group in enumerate(
        groups,
        start=1
    ):
        entries = [
            build_plugin_entry(
                plugin,
                max_description
            )
            for plugin in group
        ]

        description = "\n\n".join(
            entries
        )

        embed = {
            "description": description
        }

        # 襤lk embed
        if page_index == 1:
            embed["title"] = EMBED_TITLE
            embed["url"] = REPOSITORY_URL

            embed["author"] = {
                "name": (
                    f"Plugin Listesi \u2022 "
                    f"{page_index}/{total_pages}"
                )
            }

        else:
            embed["author"] = {
                "name": (
                    f"Plugin Listesi \u2022 "
                    f"{page_index}/{total_pages}"
                )
            }

        # Son embed footer
        if page_index == total_pages:
            embed["footer"] = {
                "text": (
                    f"{len(plugins)} plugins \u2022 "
                    f"{core_count} core \u2022 "
                    f"{normal_count} standard \u2022 "
                    f"Automatically synced from GitHub"
                )
            }

        embeds.append(
            embed
        )

    return embeds


def build_embeds(plugins):
    # Find the longest description limit that keeps the combined embed text
    # below Discord's per-message limit. A binary search avoids relying on a
    # fixed plugin count or today's manifest contents.
    minimum_embeds = build_embeds_with_description_limit(
        plugins,
        0
    )

    if (
        count_embed_characters(minimum_embeds)
        > MAX_TOTAL_EMBED_CHARACTERS
    ):
        fail(
            "Plugin adlari ve baglantilari, aciklamalar olmadan bile "
            "Discord embed karakter sinirini asiyor."
        )

    low = 0
    high = MAX_PLUGIN_DESCRIPTION
    best_embeds = minimum_embeds

    while low <= high:
        candidate_limit = (low + high) // 2
        candidate_embeds = build_embeds_with_description_limit(
            plugins,
            candidate_limit
        )

        if (
            count_embed_characters(candidate_embeds)
            <= MAX_TOTAL_EMBED_CHARACTERS
        ):
            best_embeds = candidate_embeds
            low = candidate_limit + 1
        else:
            high = candidate_limit - 1

    return best_embeds


# ============================================================
# PAYLOAD
# ============================================================

def build_payload(plugins):
    return {
        "username": WEBHOOK_USERNAME,

        "allowed_mentions": {
            "parse": []
        },

        "embeds": build_embeds(
            plugins
        )
    }


# ============================================================
# DISCORD HTTP
# ============================================================

def webhook_base_url():
    parsed = urllib.parse.urlsplit(
        WEBHOOK_URL
    )

    return urllib.parse.urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip("/"),
            "",
            ""
        )
    )


def send_request(
    url,
    payload,
    method
):
    data = json.dumps(
        payload,
        ensure_ascii=False
    ).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT
        }
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:

            body = response.read().decode(
                "utf-8",
                errors="replace"
            )

            print(
                "Discord request successful: "
                f"HTTP {response.status}"
            )

            if body:
                try:
                    return json.loads(
                        body
                    )

                except json.JSONDecodeError:
                    return body

            return None

    except urllib.error.HTTPError as exc:
        body = exc.read().decode(
            "utf-8",
            errors="replace"
        )

        print(
            "",
            file=sys.stderr
        )

        print(
            f"Discord HTTP error: "
            f"{exc.code} {exc.reason}",
            file=sys.stderr
        )

        print(
            f"Discord response: "
            f"{body or '(empty response)'}",
            file=sys.stderr
        )

        if exc.code == 401:
            print(
                "Webhook authentication ba?ar覺s覺z. "
                "Webhook URL/token kontrol et.",
                file=sys.stderr
            )

        elif exc.code == 403:
            print(
                "Discord iste?i Forbidden (403) "
                "olarak reddetti.",
                file=sys.stderr
            )

        elif exc.code == 404:
            print(
                "Webhook veya Discord mesaj覺 "
                "bulunamad覺. "
                "DISCORD_PLUGIN_MESSAGE_ID "
                "yanl覺? olabilir.",
                file=sys.stderr
            )

        elif exc.code == 429:
            print(
                "Discord rate limit uygulad覺.",
                file=sys.stderr
            )

        raise

    except urllib.error.URLError as exc:
        print(
            f"Discord ba?lant覺 hatas覺: {exc}",
            file=sys.stderr
        )

        raise


# ============================================================
# CREATE MESSAGE
# ============================================================

def create_message(payload):
    base_url = webhook_base_url()

    url = (
        f"{base_url}?wait=true"
    )

    print(
        "Yeni Discord plugin listesi "
        "mesaj覺 olu?turuluyor..."
    )

    response = send_request(
        url=url,
        payload=payload,
        method="POST"
    )

    if isinstance(response, dict):
        message_id = response.get(
            "id"
        )

        if message_id:
            print("")
            print(
                "========================================"
            )
            print(
                "Discord mesaj覺 olu?turuldu."
            )
            print(
                f"MESSAGE ID: {message_id}"
            )
            print(
                "========================================"
            )

    return response


# ============================================================
# UPDATE MESSAGE
# ============================================================

def update_message(
    payload,
    message_id
):
    base_url = webhook_base_url()

    encoded_message_id = (
        urllib.parse.quote(
            message_id,
            safe=""
        )
    )

    url = (
        f"{base_url}/messages/"
        f"{encoded_message_id}"
    )

    print(
        "Mevcut Discord mesaj覺 "
        f"g羹ncelleniyor: {message_id}"
    )

    return send_request(
        url=url,
        payload=payload,
        method="PATCH"
    )


# ============================================================
# MAIN
# ============================================================

def main():
    print(
        "========================================"
    )
    print(
        "FascinaTe Discord Plugin List Sync"
    )
    print(
        "========================================"
    )

    if not WEBHOOK_URL:
        fail(
            "DISCORD_PLUGIN_WEBHOOK "
            "environment variable tan覺ml覺 de?il."
        )

    if not WEBHOOK_URL.startswith(
        (
            "https://discord.com/api/webhooks/",
            "https://discordapp.com/api/webhooks/"
        )
    ):
        fail(
            "DISCORD_PLUGIN_WEBHOOK "
            "ge癟erli bir Discord webhook URL'sine "
            "benzemiyor."
        )

    manifest = load_manifest()

    plugins = get_plugins(
        manifest
    )

    plugins = sorted(
        plugins,
        key=plugin_sort_key
    )

    print(
        f"Bulunan plugin say覺s覺: "
        f"{len(plugins)}"
    )

    for plugin in plugins:
        name = (
            plugin.get("name")
            or plugin.get("id")
            or "Unknown"
        )

        version = (
            plugin.get("version")
            or "?"
        )

        core = bool(
            plugin.get(
                "core",
                False
            )
        )

        icon = (
            "CORE"
            if core
            else "PLUGIN"
        )

        print(
            f" - [{icon}] "
            f"{name} v{version}"
        )

    groups = split_plugins_into_groups(
        plugins
    )

    print("")
    print(
        f"Olu?turulacak embed say覺s覺: "
        f"{len(groups)}"
    )

    for index, group in enumerate(
        groups,
        start=1
    ):
        print(
            f" - Embed {index}: "
            f"{len(group)} plugin"
        )

    payload = build_payload(
        plugins
    )

    if MESSAGE_ID:
        update_message(
            payload,
            MESSAGE_ID
        )

        print("")
        print(
            "Discord plugin listesi "
            "ba?ar覺yla g羹ncellendi."
        )

    else:
        create_message(
            payload
        )

        print("")
        print(
            "Discord plugin listesi "
            "ba?ar覺yla olu?turuldu."
        )


if __name__ == "__main__":
    main()
