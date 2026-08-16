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

WEBHOOK_URL = os.environ.get("DISCORD_PLUGIN_WEBHOOK", "").strip()

# Optional:
# Eğer bu secret/variable tanımlıysa yeni mesaj göndermek yerine
# mevcut Discord mesajı güncellenir.
MESSAGE_ID = os.environ.get("DISCORD_PLUGIN_MESSAGE_ID", "").strip()

REPOSITORY_URL = "https://github.com/fascinate78/phbot-plugins"

WEBHOOK_USERNAME = "FascinaTe Plugins"

EMBED_TITLE = "🧩 FascinaTe phBot Plugins"

USER_AGENT = "FascinaTe-phBot-Plugins-GitHub-Action/1.0"


# Discord embed description maksimum 4096 karakter.
# Bir miktar güvenli alan bırakıyoruz.
MAX_EMBED_DESCRIPTION = 3900

# Tek plugin açıklamasının çok uzun olması durumunda.
MAX_PLUGIN_DESCRIPTION = 220


# ============================================================
# HELPERS
# ============================================================

def fail(message: str, exit_code: int = 1):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(exit_code)


def truncate(text: str, max_length: int) -> str:
    """
    Metni Discord limitlerine uygun şekilde kısaltır.
    """
    if not text:
        return ""

    text = str(text).strip()

    if len(text) <= max_length:
        return text

    return text[: max_length - 3].rstrip() + "..."


def load_manifest():
    """
    manifest.json dosyasını yükler.
    """
    if not MANIFEST_PATH.exists():
        fail(f"{MANIFEST_PATH} bulunamadı.")

    try:
        with MANIFEST_PATH.open("r", encoding="utf-8") as file:
            manifest = json.load(file)
    except json.JSONDecodeError as exc:
        fail(f"manifest.json geçerli JSON değil: {exc}")
    except Exception as exc:
        fail(f"manifest.json okunamadı: {exc}")

    return manifest


def get_plugins(manifest):
    """
    Manifest içindeki plugin listesini bulur.

    Desteklenen yapılar:

    {
        "plugins": [...]
    }

    veya doğrudan:

    [...]
    """
    if isinstance(manifest, dict):
        plugins = manifest.get("plugins", [])
    elif isinstance(manifest, list):
        plugins = manifest
    else:
        fail("manifest.json beklenmeyen bir yapıya sahip.")

    if not isinstance(plugins, list):
        fail("manifest.json içindeki 'plugins' alanı liste değil.")

    if not plugins:
        fail("manifest.json içinde plugin bulunamadı.")

    return plugins


def plugin_sort_key(plugin):
    return str(
        plugin.get("name")
        or plugin.get("id")
        or ""
    ).lower()


def build_plugin_entry(plugin):
    """
    Bir plugin için Discord Markdown metni oluşturur.
    """
    name = (
        plugin.get("name")
        or plugin.get("id")
        or "Unknown Plugin"
    )

    version = str(plugin.get("version") or "?")

    description = truncate(
        plugin.get("description") or "",
        MAX_PLUGIN_DESCRIPTION
    )

    download_url = plugin.get("download_url") or ""
    changelog_url = plugin.get("changelog_url") or ""

    core = bool(plugin.get("core", False))

    icon = "⭐" if core else "📦"

    lines = [
        f"**{icon} {name}** `v{version}`"
    ]

    if description:
        lines.append(description)

    links = []

    if download_url:
        links.append(f"[⬇️ Download]({download_url})")

    if changelog_url:
        links.append(f"[📝 Changelog]({changelog_url})")

    if links:
        lines.append(" • ".join(links))

    return "\n".join(lines)


def build_embed_description(plugins):
    """
    Pluginleri tek embed description'a dönüştürür.

    Discord 4096 karakter limitini aşarsa kalan pluginleri
    özet şekilde gösterir.
    """
    entries = []
    current_length = 0
    hidden_count = 0

    for plugin in plugins:
        entry = build_plugin_entry(plugin)

        separator_length = 2 if entries else 0
        new_length = current_length + separator_length + len(entry)

        # Sonuna uyarı yazabilmek için biraz alan bırakıyoruz.
        if new_length > MAX_EMBED_DESCRIPTION - 120:
            hidden_count += 1
            continue

        entries.append(entry)
        current_length = new_length

    description = "\n\n".join(entries)

    if hidden_count:
        description += (
            f"\n\n"
            f"**+ {hidden_count} plugin daha mevcut.**\n"
            f"[Tüm pluginleri GitHub'da görüntüle]({REPOSITORY_URL})"
        )

    return description


def build_payload(plugins):
    """
    Discord webhook payload oluşturur.
    """
    description = build_embed_description(plugins)

    core_count = sum(
        1 for plugin in plugins
        if plugin.get("core", False)
    )

    normal_count = len(plugins) - core_count

    footer_parts = [
        f"{len(plugins)} plugins"
    ]

    if core_count:
        footer_parts.append(f"{core_count} core")

    if normal_count:
        footer_parts.append(f"{normal_count} standard")

    footer_parts.append("Automatically synced from GitHub")

    payload = {
        "username": WEBHOOK_USERNAME,
        "allowed_mentions": {
            "parse": []
        },
        "embeds": [
            {
                "title": EMBED_TITLE,
                "description": description,
                "url": REPOSITORY_URL,
                "footer": {
                    "text": " • ".join(footer_parts)
                }
            }
        ]
    }

    return payload


# ============================================================
# DISCORD
# ============================================================

def webhook_base_url():
    """
    Webhook URL içindeki query parametrelerini kaldırır.
    """
    parsed = urllib.parse.urlsplit(WEBHOOK_URL)

    return urllib.parse.urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip("/"),
            "",
            ""
        )
    )


def send_request(url, payload, method):
    """
    Discord'a HTTP isteği gönderir.
    """
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

            response_body = response.read().decode(
                "utf-8",
                errors="replace"
            )

            print(
                f"Discord request successful: "
                f"HTTP {response.status}"
            )

            if response_body:
                try:
                    return json.loads(response_body)
                except json.JSONDecodeError:
                    return response_body

            return None

    except urllib.error.HTTPError as exc:
        body = exc.read().decode(
            "utf-8",
            errors="replace"
        )

        print("", file=sys.stderr)
        print(
            f"Discord HTTP error: {exc.code} {exc.reason}",
            file=sys.stderr
        )

        print(
            f"Discord response: {body or '(empty response)'}",
            file=sys.stderr
        )

        if exc.code == 401:
            print(
                "Webhook authentication başarısız. "
                "Webhook URL/token kontrol et.",
                file=sys.stderr
            )

        elif exc.code == 403:
            print(
                "Discord isteği Forbidden (403) olarak reddetti. "
                "Webhook'un aktif olduğunu, doğru kanala ait olduğunu "
                "ve GitHub Secret içindeki URL'nin güncel olduğunu kontrol et.",
                file=sys.stderr
            )

        elif exc.code == 404:
            print(
                "Webhook veya mesaj bulunamadı. "
                "Webhook URL veya DISCORD_PLUGIN_MESSAGE_ID yanlış olabilir.",
                file=sys.stderr
            )

        elif exc.code == 429:
            print(
                "Discord rate limit uyguladı.",
                file=sys.stderr
            )

        raise

    except urllib.error.URLError as exc:
        print(
            f"Discord bağlantı hatası: {exc}",
            file=sys.stderr
        )
        raise


def create_message(payload):
    """
    İlk Discord mesajını oluşturur.

    wait=true sayesinde Discord oluşturulan mesajın JSON'unu
    geri döndürür ve message ID'yi alabiliriz.
    """
    base_url = webhook_base_url()

    url = f"{base_url}?wait=true"

    print("Yeni Discord plugin listesi mesajı oluşturuluyor...")

    response = send_request(
        url=url,
        payload=payload,
        method="POST"
    )

    if isinstance(response, dict):
        message_id = response.get("id")

        if message_id:
            print("")
            print("========================================")
            print("Discord mesajı oluşturuldu.")
            print(f"MESSAGE ID: {message_id}")
            print("========================================")
            print("")
            print(
                "Bu ID'yi GitHub Actions secret/variable olarak "
                "'DISCORD_PLUGIN_MESSAGE_ID' adıyla kaydedersen "
                "sonraki çalıştırmalarda aynı mesaj güncellenir."
            )

    return response


def update_message(payload, message_id):
    """
    Mevcut Discord webhook mesajını düzenler.
    """
    base_url = webhook_base_url()

    encoded_message_id = urllib.parse.quote(
        message_id,
        safe=""
    )

    url = (
        f"{base_url}/messages/"
        f"{encoded_message_id}"
    )

    print(
        f"Mevcut Discord mesajı güncelleniyor: "
        f"{message_id}"
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
    print("========================================")
    print("FascinaTe Discord Plugin List Sync")
    print("========================================")

    if not WEBHOOK_URL:
        fail(
            "DISCORD_PLUGIN_WEBHOOK environment variable "
            "tanımlı değil."
        )

    if not WEBHOOK_URL.startswith(
        (
            "https://discord.com/api/webhooks/",
            "https://discordapp.com/api/webhooks/"
        )
    ):
        fail(
            "DISCORD_PLUGIN_WEBHOOK geçerli bir Discord "
            "webhook URL'sine benzemiyor."
        )

    manifest = load_manifest()

    plugins = get_plugins(manifest)

    plugins = sorted(
        plugins,
        key=plugin_sort_key
    )

    print(f"Manifest yüklendi.")
    print(f"Bulunan plugin sayısı: {len(plugins)}")

    for plugin in plugins:
        name = (
            plugin.get("name")
            or plugin.get("id")
            or "Unknown"
        )

        version = plugin.get("version") or "?"

        print(f" - {name} v{version}")

    payload = build_payload(plugins)

    if MESSAGE_ID:
        update_message(
            payload,
            MESSAGE_ID
        )

        print("")
        print("Discord plugin listesi güncellendi.")

    else:
        create_message(payload)

        print("")
        print("Discord plugin listesi gönderildi.")


if __name__ == "__main__":
    main()
