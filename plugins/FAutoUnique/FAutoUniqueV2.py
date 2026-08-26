import phBot
from phBot import *
import QtBind
import time
import os
import json
import math
import struct
import threading
import sys
import webbrowser

# ================= INFO =================
pName = 'FAutoUnique V2'
pVersion = '2.7.0'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

COLOR_PRIMARY = '#5b57e0'
COLOR_TEXT = '#2b3038'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#e74c3c'

UI_LANGUAGE = 'en'
UI_TEXT = {
    'en': {
        'dashboard': 'Dashboard', 'unique_manager': 'Unique Manager',
        'hunt_settings': 'Hunt Settings', 'logs': 'Logs', 'apply_language': 'Apply',
        'live_hunt_status': 'LIVE HUNT STATUS', 'plugin': 'Plugin', 'bot_state': 'Bot state',
        'current_target': 'Current target', 'route': 'Route', 'action': 'Action', 'queue': 'Queue',
        'start_monitoring': 'Start Monitoring', 'stop_monitoring': 'Stop Monitoring',
        'stop_current_hunt': 'Stop Current Hunt', 'hunt_queue': 'HUNT QUEUE',
        'hunt_next': 'Hunt Next', 'remove_selected': 'Remove Selected', 'clear_queue': 'Clear Queue',
        'needs_setup_heading': 'NEEDS SETUP', 'configure_uniques': 'Configure Uniques',
        'remove_entry': 'Remove Entry', 'apply': 'Apply', 'load_selected': 'Load Selected',
        'scan_nearby': 'Scan Nearby', 'custom': 'Custom', 'add_unique': 'Add Unique',
        'queue_selected': 'Queue Selected', 'hunt_selected': 'Hunt Selected', 'status': 'Status',
        'priority': 'Priority', 'script_route_heading': 'SCRIPT ROUTE', 'refresh': 'Refresh',
        'assign_script': 'Assign Script', 'use_script_route': 'Use Script Route',
        'remove_script': 'Remove Script', 'coordinate_route_heading': 'COORDINATE ROUTE',
        'edit_coordinates': 'Edit Coordinates', 'use_coord': 'Use Coord',
        'first_reverse': 'First use Reverse', 'save_reverse': 'Save Reverse',
        'coordinate_editor': 'COORDINATE EDITOR', 'back': '\u2190 Back',
        'saved_coordinate_route': 'SAVED COORDINATE ROUTE', 'capture_current': 'Capture Current',
        'capture_nearby': 'Capture Nearby', 'manual_coordinate': 'MANUAL COORDINATE', 'add': 'Add',
        'loot_behavior': 'LOOT BEHAVIOR', 'wait_after_death': 'Wait after unique death',
        'seconds': 'seconds', 'hunt_timeout': 'HUNT TIMEOUT', 'enable_hunt_timeout': 'Enable hunt timeout',
        'automation': 'AUTOMATION', 'auto_return': 'Return to town for an unconfigured unique',
        'auto_learn': 'Automatically learn unique coordinates',
        'duplicate_help': 'Points within 30m of a saved point are ignored.',
        'diagnostics': 'DIAGNOSTICS', 'debug_logging': 'Detailed debug logging',
        'refresh_alive': 'Refresh Nearby Alive Status', 'log_tracked': 'Log Tracked Uniques',
        'recent_activity': 'RECENT PLUGIN ACTIVITY',
        'activity_help': 'Shows the latest 100 important GUI-visible state changes.',
        'clear_activity': 'Clear Activity', 'language': 'Language:',
        'active': 'ACTIVE', 'disabled': 'DISABLED', 'idle': 'IDLE', 'none': 'None',
        'hunting': 'HUNTING', 'returning': 'RETURNING', 'coordinates': 'Coordinates',
        'ready': 'Ready', 'no_route': 'Needs Setup', 'script_route': 'Script Route',
        'coordinate_route': 'Coordinate Route', 'no_script': 'No script assigned.',
        'monitoring_disabled': 'Monitoring is disabled', 'waiting_unique': 'Waiting for a unique',
        'running_route': 'Running hunt route', 'searching_points': 'Searching saved spawn points',
        'waiting_reverse': 'Waiting for Reverse teleport', 'returning_town': 'Returning to town',
        'queue_empty': 'Queue is empty.', 'no_setup': 'No uniques need setup.',
        'no_matches': 'No uniques match this search.', 'no_saved_points': 'No saved points',
        'saved_point': '{count} saved point', 'saved_points': '{count} saved points',
        'select_unique_configure': 'Select a unique to configure.', 'editor_ready': 'Ready.',
        'no_unique_selected': 'No unique selected', 'reverse_placeholder': 'Select Reverse location',
        'opening_discord': 'OPENING DISCORD INVITE...', 'discord_error': 'COULD NOT OPEN DISCORD INVITE',
        'reverse_enabled_status': 'First Reverse enabled to {location} for {unique}.',
        'reverse_disabled_status': 'First Reverse disabled for {unique}.',
    },
    'tr': {
        'dashboard': 'Kontrol Paneli', 'unique_manager': 'Unique Yönetimi',
        'hunt_settings': 'Av Ayarları', 'logs': 'Kayıtlar', 'apply_language': 'Uygula',
        'live_hunt_status': 'CANLI AV DURUMU', 'plugin': 'Plugin', 'bot_state': 'Bot durumu',
        'current_target': 'Mevcut hedef', 'route': 'Rota', 'action': 'İşlem', 'queue': 'Kuyruk',
        'start_monitoring': 'İzlemeyi Başlat', 'stop_monitoring': 'İzlemeyi Durdur',
        'stop_current_hunt': 'Mevcut Avı Durdur', 'hunt_queue': 'AV KUYRUĞU',
        'hunt_next': 'Sıradaki', 'remove_selected': 'Seçileni Sil', 'clear_queue': 'Kuyruğu Temizle',
        'needs_setup_heading': 'AYAR GEREKENLER', 'configure_uniques': 'Uniqueleri Ayarla',
        'remove_entry': 'Kaydı Sil', 'apply': 'Uygula', 'load_selected': 'Seçileni Yükle',
        'scan_nearby': 'Yakını Tara', 'custom': 'Özel', 'add_unique': 'Unique Ekle',
        'queue_selected': 'Kuyruğa Al', 'hunt_selected': 'Seçileni Avla', 'status': 'Durum',
        'priority': 'Öncelik', 'script_route_heading': 'SCRIPT ROTASI', 'refresh': 'Yenile',
        'assign_script': 'Script Ata', 'use_script_route': 'Script Rotası',
        'remove_script': 'Scripti Sil', 'coordinate_route_heading': 'KOORDINAT ROTASI',
        'edit_coordinates': 'Koordinatları Aç', 'use_coord': 'Rota Seç',
        'first_reverse': 'Önce Reverse kullan', 'save_reverse': 'Rev Kaydet',
        'coordinate_editor': 'KOORDİNAT EDİTÖRÜ', 'back': '\u2190 Geri',
        'saved_coordinate_route': 'KAYITLI KOORDINAT ROTASI', 'capture_current': 'Mevcut Konum',
        'capture_nearby': 'Yakındaki Unique', 'manual_coordinate': 'MANUEL KOORDİNAT', 'add': 'Ekle',
        'loot_behavior': 'LOOT DAVRANIŞI', 'wait_after_death': 'Unique ölümünden sonra bekle',
        'seconds': 'saniye', 'hunt_timeout': 'AV ZAMAN AŞIMI', 'enable_hunt_timeout': 'Av zaman aşımını etkinleştir',
        'automation': 'OTOMASYON', 'auto_return': 'Ayarsız unique için şehre dön',
        'auto_learn': 'Unique koordinatlarını otomatik öğren',
        'duplicate_help': 'Kayıtlı noktaya 30m içindeki noktalar yok sayılır.',
        'diagnostics': 'TANILAMA', 'debug_logging': 'Ayrıntılı teknik kayıt',
        'refresh_alive': 'Yakındaki Durumu Yenile', 'log_tracked': 'İzlenenleri Logla',
        'recent_activity': 'SON PLUGIN HAREKETLERİ',
        'activity_help': 'Kullanıcıya gösterilen son 100 önemli durum değişikliğini gösterir.',
        'clear_activity': 'Hareketleri Temizle', 'language': 'Dil:',
        'active': 'AKTİF', 'disabled': 'DEVRE DIŞI', 'idle': 'BEKLİYOR', 'none': 'Yok',
        'hunting': 'AVLANIYOR', 'returning': 'DÖNÜYOR', 'coordinates': 'Koordinatlar',
        'ready': 'Hazır', 'no_route': 'Ayar Gerekli', 'script_route': 'Script Rotası',
        'coordinate_route': 'Koordinat Rotası', 'no_script': 'Script atanmamış.',
        'monitoring_disabled': 'İzleme devre dışı', 'waiting_unique': 'Unique bekleniyor',
        'running_route': 'Av rotası çalışıyor', 'searching_points': 'Kayıtlı noktalar aranıyor',
        'waiting_reverse': 'Reverse ışınlanması bekleniyor', 'returning_town': 'Şehre dönülüyor',
        'queue_empty': 'Kuyruk boş.', 'no_setup': 'Ayar bekleyen unique yok.',
        'no_matches': 'Aramayla eşleşen unique yok.', 'no_saved_points': 'Kayıtlı nokta yok',
        'saved_point': '{count} kayıtlı nokta', 'saved_points': '{count} kayıtlı nokta',
        'select_unique_configure': 'Ayarlamak için bir unique seçin.', 'editor_ready': 'Hazır.',
        'no_unique_selected': 'Unique seçilmedi', 'reverse_placeholder': 'Reverse konumu seçin',
        'opening_discord': 'DISCORD DAVETİ AÇILIYOR...', 'discord_error': 'DISCORD DAVETİ AÇILAMADI',
        'reverse_enabled_status': '{unique} için First Reverse konumu {location} olarak etkin.',
        'reverse_disabled_status': '{unique} için First Reverse devre dışı.',
    },
}


def tr(key, **values):
    table = UI_TEXT.get(UI_LANGUAGE, UI_TEXT['en'])
    text = table.get(key, UI_TEXT['en'].get(key, key))
    try:
        return text.format(**values)
    except Exception:
        return text


UI_MESSAGE_TR = {
    'Select a unique from the list first.': 'Önce listeden bir unique seçin.',
    'Could not select the unique.': 'Unique seçilemedi.',
    'Select a unique before editing coordinates.': 'Koordinatları düzenlemek için bir unique seçin.',
    'Select a unique before saving Reverse settings.': 'Reverse ayarını kaydetmek için bir unique seçin.',
    'Choose a Reverse location, then save again.': 'Bir Reverse konumu seçip tekrar kaydedin.',
    'Select a unique before enabling First Reverse.': 'First Reverse için önce bir unique seçin.',
    'Script route assigned.': 'Script rotası atandı.',
    'Coordinate route selected.': 'Koordinat rotası seçildi.',
    'Script route selected.': 'Script rotası seçildi.',
    'No script mapping to remove.': 'Silinecek script eşleştirmesi yok.',
    'Script mapping removed.': 'Script eşleştirmesi silindi.',
    'Select a unique first.': 'Önce bir unique seçin.',
    'Selected unique is not nearby.': 'Seçili unique yakında değil.',
    'Selected coordinate removed.': 'Seçili koordinat silindi.',
    'Coordinate saved': 'Koordinat kaydedildi',
    'Select a unique first': 'Once bir unique secin',
    'Invalid coordinate values': 'Koordinat değerleri geçersiz',
    'Region and coordinates are required': 'Region ve koordinatlar gerekli',
    'A saved point is already within 30m': '30m içinde kayıtlı bir nokta zaten var',
}


def translate_ui_message(message):
    if UI_LANGUAGE != 'tr':
        return message
    if message in UI_MESSAGE_TR:
        return UI_MESSAGE_TR[message]
    if message.startswith('Bot state: '):
        state = message[len('Bot state: '):]
        return 'Bot durumu: %s' % {
            'IDLE': tr('idle'), 'HUNTING': tr('hunting'),
            'RETURNING': tr('returning')}.get(state, state)
    if message == 'Current target: None':
        return 'Mevcut hedef: %s' % tr('none')
    replacements = (
        ('Selected ', 'Seçildi: '), ('Editing saved points for ', 'Kayıtlı noktalar düzenleniyor: '),
        ('Current target: ', 'Mevcut hedef: '), ('Bot state: ', 'Bot durumu: '),
        ('Queued: ', 'Kuyruğa eklendi: '), ('Detected: ', 'Tespit edildi: '),
        ('Killed: ', 'Öldürüldü: '), ('Hunt timeout: ', 'Av zaman aşımı: '),
        ('Coordinate search started: ', 'Koordinat araması başladı: '),
        ('Hunt route started: ', 'Av rotası başladı: '),
        ('Using Reverse for ', 'Reverse kullanılıyor: '),
        ('Reverse complete: ', 'Reverse tamamlandı: '),
        ('Language changed to ', 'Dil değiştirildi: '),
        ('Reverse error for ', 'Reverse hatası: '),
        ('Reverse could not be used; ', 'Reverse kullanılamadı; '),
        ('Reverse timed out; ', 'Reverse zaman aşımına uğradı; '),
    )
    for source, target in replacements:
        if message.startswith(source):
            translated = target + message[len(source):]
            return translated.replace(' remains queued.', ' kuyrukta tutuluyor.')
    exact = {
        'Hunt completed': 'Av tamamlandı', 'Returning to town': 'Şehre dönülüyor',
        'Queue is empty': 'Kuyruk boş', 'Monitoring enabled': 'İzleme etkin',
        'Monitoring disabled': 'İzleme devre dışı',
    }
    return exact.get(message, message)
# Eski pluginin mapping ve slot ayarlari kaybolmasin diye mevcut config
# klasorunu kullanmaya devam et. UI/plugin adi bundan bagimsizdir.
CONFIG_FOLDER = 'AutoUniuqe'
                    # scriptli unique spawn olunca slotu kaydedip (get_training_area) sehre doner,
                    # script'i calistirir, is bitince townda BEKLEMEDEN slota geri doner
                    # (restore_slot). Script'siz unique artik grind'i bolmuyor. Disable'da bekleyen
                    # return/wait timer zincirleri plugin_active guard'lariyla durduruluyor.
                    # v5.6: timeout never firing, presumed-death fallback, teleported() hook,
                    # native EVENT_UNIQUE_SPAWN, stricter name matching, loot-wait kosulsuz

# ================= PATHS =================
plugin_path = os.path.dirname(os.path.realpath(__file__))
scripts_folder = os.path.join(plugin_path, 'scripts')

def getPath():
    """Return the plugin config folder inside get_config_dir()."""
    return get_config_dir() + CONFIG_FOLDER + "\\"

def getConfig():
    """Return the per-character JSON config path."""
    char = get_character_data()
    if char and char.get('name') and char.get('server'):
        return getPath() + char['server'] + "_" + char['name'] + ".json"
    return None

# ================= DATA & STATE =================
unique_script_map = {}
unique_coordinate_map = {}
unique_route_modes = {}
unique_reverse_settings = {}
pending_uniques = []
alive_uniques = {}
last_check_time = 0
check_interval = 1.0
debug_enabled = False
attack_timer = None
loot_timer = None
current_active_unique = None
unique_queue = []
plugin_active = False
# grind slotunun training area bilgisi â€” av bitince buraya geri donmek icin
# (get_training_area()'dan yakalanir: region,x,y,z,radius,path)
saved_slot = None
auto_learn_coordinates = False
learned_unique_ids = set()

# Coordinate hunt settings. generate_script() itself is limited by phBot to one
# pathfinding request every five seconds.
COORDINATE_SEARCH_SEC = 2.0
COORDINATE_SCAN_INTERVAL_SEC = 0.25
COORDINATE_ARRIVAL_DISTANCE = 10.0
COORDINATE_DUPLICATE_DISTANCE = 30.0
UNIQUE_TRAINING_RADIUS = 50.0
PATHFINDING_COOLDOWN_SEC = 5.2
coordinate_hunt = None
coordinate_timer = None
last_pathfinding_time = 0.0
coordinate_run_token = 0

REVERSE_LOCATIONS = [
    'Constantinople', 'Forest of Sorrow', 'Garden of Gods', 'Roc Mountain',
    'Heart Peak', 'Lost Town', 'Shepherd Town', 'Wind Town', 'Niya Remains',
    'Mysterious Death Desert', 'Fertility Temple', 'Hotan', 'Grassland Road',
    'Karakoram Cross Road', 'Ancient Remains', 'Spider Forest',
    'Black Robber Den', 'Tarim Basin', 'Donwhang', 'Hyungno Homeland',
    'Jangan', 'Grassland', "Bandit's Mountain Stronghold",
    'Donwhang Stone Cave', 'Baghdad', 'Kirk', 'Phantom Desert', 'Arabia Coast',
]
REVERSE_LOCATION_PLACEHOLDER = 'Select Reverse location'
REVERSE_TIMEOUT_SEC = 30.0
reverse_hunt_pending = None
reverse_timeout_timer = None
reverse_run_token = 0

# Protect unique_queue / alive_uniques / pending_uniques from race conditions
# between the network event thread and threading.Timer callbacks.
_state_lock = threading.RLock()

# If an engaged target disappears from get_monsters() longer than this grace
# period, treat it as dead and return instead of waiting for the full timeout.
LOST_TARGET_GRACE_SEC = 8.0

# State Machine: IDLE, HUNTING, RETURNING
bot_state = 'IDLE'
force_stopped = False
just_returned = False  # Skip the town check once immediately after returning.
unique_not_found_count = 0
script_finished = False
_in_town_state = True  # Manually tracked town state.

# Town region'lari â€” hem _is_in_town hem capture_slot kullaniyor
# (slot'u yanlislikla town sanmamak icin)
TOWN_REGIONS = {
    25000, 25001, 25002, 25003,  # Jangan
    24064, 24065, 24066, 24067,  # Donwhang
    23687,                        # Hotan (confirmed)
    23040, 23041, 23042, 23043,  # Hotan area
    22016, 22017, 22018, 22019,  # Constantinople
    21504, 21505, 21506, 21507,  # Samarkand
    20480, 20481, 20482, 20483,  # Roc
    19456, 19457, 19458, 19459,  # Alexandria
    18432, 18433, 18434, 18435,  # Bagdad
}
# ================= AUTO RETURN STATE =================
# Return to town when an unmapped unique appears while the bot is idle.
auto_return_enabled = False
town_return_pending = False

unique_priorities = {
    'Demon Shaitan': 10, 'DemonShiten': 10,
    'Isyutaru': 9, 'Cerberus': 9,
    'Lord Yarkan': 8, 'Captain Ivy': 8,
    'Tiger Girl': 7, 'Uruchi': 7,
}

def get_unique_priority(unique_name):
    if unique_name in unique_priorities:
        return unique_priorities[unique_name]
    return 5

def sort_queue_by_priority():
    global unique_queue
    try:
        unique_queue.sort(key=lambda x: get_unique_priority(x), reverse=True)
    except Exception as e:
        if debug_enabled: log(f"sort_queue_by_priority error: {e}")

COMMON_UNIQUES = [
    'Tiger Girl', 'Sphinx', 'Captain Ivy', 'Uruchi', 'Merikh', 'Dark Soul',
    'Shabahoon of Lamp', 'Osiris', 'Lord Yarkan', 'Manho', 'Demon Shaitan',
    'Isyutaru', 'Nephthys', 'Tai-Sui', 'Cerberus', 'Hang-A', 'Undine',
    'Ganiazo Dow', 'Gnome', 'Salamander', 'Sylph', 'Seth', 'Haroeris',
    'Anubis', 'Isis', 'Neith', 'Selket', 'Goon', 'Battle Golem',
    'Supreme Medusa', 'Queen Medusa (Rapid)', 'Queen Medusa (STR)', 'Queen Medusa (INT)',
    'Death Bone (INT)', 'Hextech Death Bone (STR)', 'Isyutaru (INT)',
    'Mirage Shadow (STR)', 'Mirage Shadow (INT)', 'Holy Treasure Box',
    'Styria Storage Box', 'The King (Roc)', 'RoC', 'White Knight',
    'Madness Taishan (STR)', 'Madness Taishan (INT)', 'Royale Soldier (STR)',
    'Royale Soldier (INT)', 'Arabia Spirit (INT)', 'Arabia Penon (INT)',
    'Arabia Knight (INT)', 'Arabia Berserk (INT)', 'Arabia (Ong)',
    'Overlord (STR)', 'Baal', 'Eris', 'Devil Benepika (INT)', 'Launatun',
    'Dark Soul (INT)', 'Madness Cloud (INT)', 'Phase I of Cataclysm Tower',
    'Phase II of Red Obstacle', 'Phase III of Red Obstacle',
    'Phase III of Red Goalkeeper', 'Thief Boss Kalia', 'Homocidal Santa (INT)',
    'Ghost Beast', 'Flame Cow King', 'Horus', 'General Paimon',
    'Karak', 'Ogy', 'BeakYung', 'Tiger Woman', 'Mujigigi',
    'Venom', 'Spider', 'Dark Spider', 'Elder Spider', 'Monkey'
]

discovered_uniques = set()

# GUI-only selection and activity state. Backend collections remain authoritative.
selected_unique_name = ''
unique_browser_items = []
activity_entries = []
ACTIVITY_LIMIT = 100
_last_activity_state = {
    'plugin': None, 'target': None, 'queue': None, 'bot': None, 'action': None
}
_recent_activity_events = {}
_last_dashboard_snapshot = None

# ================= CONFIG & FILE HELPERS =================
def add_manual_unique():
    global selected_unique_name
    try:
        name = QtBind.text(gui, txt_unique).strip()
        if not name:
            log("Please type a unique name")
            return
        if name not in discovered_uniques:
            discovered_uniques.add(name)
            refresh_unique_dropdown()
            save_config()
        selected_unique_name = name
        refresh_selected_unique_details()
        QtBind.setText(gui, txt_unique, "")
        log(f"Added manual unique: {name}")
    except Exception as e:
        log(f"add_manual_unique error: {e}")

def scan_nearby_uniques():
    try:
        monsters = phBot.get_monsters()
        if not monsters: return
        found = []
        for monster_id, monster in monsters.items():
            name = monster.get('name', '')
            mtype = monster.get('type', 0)
            if mtype >= 2 or is_known_unique(name):
                if name and name not in discovered_uniques:
                    discovered_uniques.add(name)
                    found.append(name)
        if found:
            log(f"Scanned: {', '.join(found)}")
            refresh_unique_dropdown()
            save_config()
    except Exception as e:
        log(f"scan_nearby_uniques error: {e}")

def is_known_unique(name):
    if not name: return False
    # substring yerine _is_unique_match (exact / "name " / "name(" prefix) kullanÄ±yoruz
    # ki 'Spider', 'Monkey', 'Goon' gibi genel isimler sÄ±radan moblarla yanlÄ±ÅŸlÄ±kla eÅŸleÅŸmesin
    return any(_is_unique_match(u, name) for u in COMMON_UNIQUES)

def is_unique(name):
    if not name: return False
    if name in discovered_uniques: return True
    if name in unique_script_map: return True
    if name in unique_coordinate_map: return True
    return is_known_unique(name)

def has_hunt_route(unique_name):
    """Return True when a unique has either coordinates or a walk script."""
    mode = get_route_mode(unique_name)
    if mode == 'coordinates':
        return bool(unique_coordinate_map.get(unique_name))
    return unique_name in unique_script_map

def get_route_mode(unique_name):
    mode = unique_route_modes.get(unique_name)
    if mode == 'script':
        if unique_name in unique_script_map:
            return 'script'
        if unique_coordinate_map.get(unique_name):
            return 'coordinates'
        return None
    if mode == 'coordinates':
        if unique_coordinate_map.get(unique_name):
            return 'coordinates'
        if unique_name in unique_script_map:
            return 'script'
        return None
    if unique_name in unique_script_map:
        return 'script'
    if unique_coordinate_map.get(unique_name):
        return 'coordinates'
    return None

def _distance_2d(x1, y1, x2, y2):
    return math.sqrt((float(x1) - float(x2)) ** 2 + (float(y1) - float(y2)) ** 2)

def _normalise_point(point, source='Manual'):
    return {
        'region': int(point.get('region', 0) or 0),
        'x': float(point.get('x', 0) or 0),
        'y': float(point.get('y', 0) or 0),
        'z': float(point.get('z', 0) or 0),
        'source': point.get('source', source) or source,
    }

def _add_coordinate(unique_name, point, source='Manual'):
    """Add a spawn point unless the same-region list already has one within 30m."""
    if not unique_name:
        return False, 'Select a unique first'
    try:
        point = _normalise_point(point, source)
    except (TypeError, ValueError):
        return False, 'Invalid coordinate values'
    if point['region'] == 0 or (point['x'] == 0 and point['y'] == 0):
        return False, 'Region and coordinates are required'
    points = unique_coordinate_map.setdefault(unique_name, [])
    for saved in points:
        if int(saved.get('region', 0) or 0) != point['region']:
            continue
        if _distance_2d(saved.get('x', 0), saved.get('y', 0), point['x'], point['y']) <= COORDINATE_DUPLICATE_DISTANCE:
            return False, 'A saved point is already within 30m'
    points.append(point)
    # Explicit manual capture selects coordinate mode. Automatic learning only
    # selects it when the unique did not already have a script route.
    if source != 'Learned' or unique_name not in unique_script_map:
        unique_route_modes[unique_name] = 'coordinates'
    discovered_uniques.add(unique_name)
    with _state_lock:
        if unique_name in pending_uniques:
            pending_uniques.remove(unique_name)
    save_config()
    refresh_mapping_list()
    refresh_coordinate_list()
    refresh_pending_list()
    return True, 'Coordinate saved'

def get_scripts():
    try:
        if not os.path.exists(scripts_folder):
            os.makedirs(scripts_folder)
        return [f for f in os.listdir(scripts_folder) if f.endswith('.txt')]
    except Exception as e:
        log(f"get_scripts error: {e}")
        return []

def save_config():
    """Save settings to the current character's JSON file."""
    try:
        cfg = getConfig()
        if not cfg: return
        path = getPath()
        if not os.path.exists(path):
            os.makedirs(path)
        data = {
            'mappings': unique_script_map,
            'coordinate_mappings': unique_coordinate_map,
            'route_modes': unique_route_modes,
            'reverse_settings': unique_reverse_settings,
            'language': UI_LANGUAGE,
            'discovered_uniques': sorted(list(discovered_uniques)),
            'plugin_active': plugin_active,
            'auto_return_enabled': auto_return_enabled,
            'auto_learn_coordinates': auto_learn_coordinates,
            'saved_slot': saved_slot,
        }
        with open(cfg, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"save_config error: {e}")

def load_config():
    """Load settings from the current character's JSON file."""
    global unique_script_map, unique_coordinate_map, unique_route_modes, unique_reverse_settings, discovered_uniques
    global plugin_active, auto_return_enabled, auto_learn_coordinates, saved_slot, UI_LANGUAGE
    try:
        cfg = getConfig()
        UI_LANGUAGE = 'en'
        unique_reverse_settings = {}
        if cfg and os.path.exists(cfg):
            with open(cfg, 'r', encoding='utf-8') as f:
                data = json.load(f)
            unique_script_map = data.get('mappings', {})
            unique_route_modes = data.get('route_modes', {})
            raw_reverse_settings = data.get('reverse_settings', {})
            if isinstance(raw_reverse_settings, dict):
                for unique_name, setting in raw_reverse_settings.items():
                    if not isinstance(setting, dict):
                        continue
                    location = str(setting.get('location', '') or '').strip()
                    unique_reverse_settings[unique_name] = {
                        'enabled': bool(setting.get('enabled', False)),
                        'location': location if location in REVERSE_LOCATIONS else '',
                    }
            raw_coordinate_map = data.get('coordinate_mappings', {})
            unique_coordinate_map = {}
            for unique_name, points in raw_coordinate_map.items():
                valid_points = []
                for point in points if isinstance(points, list) else []:
                    try:
                        valid_points.append(_normalise_point(point))
                    except (TypeError, ValueError, AttributeError):
                        pass
                if valid_points:
                    unique_coordinate_map[unique_name] = valid_points
            saved_uniques = data.get('discovered_uniques', [])
            discovered_uniques = set(saved_uniques)
            auto_return_enabled = data.get('auto_return_enabled', False)
            auto_learn_coordinates = data.get('auto_learn_coordinates', False)
            saved_slot = data.get('saved_slot', None)
            UI_LANGUAGE = data.get('language', 'en')
            if UI_LANGUAGE not in ('en', 'tr'):
                UI_LANGUAGE = 'en'
            try:
                QtBind.setChecked(gui, chk_auto_return, auto_return_enabled)
                QtBind.setChecked(gui, chk_auto_learn, auto_learn_coordinates)
            except: pass
            was_active = data.get('plugin_active', False)
            if was_active:
                log("Plugin was ENABLED -> Auto-resuming...")
                plugin_active = True
                try:
                    QtBind.setChecked(gui, chk_auto_return, auto_return_enabled)
                except: pass
            else:
                plugin_active = False
        # Always include the built-in unique names.
        discovered_uniques.update(COMMON_UNIQUES)
        refresh_mapping_list()
        refresh_unique_dropdown()
        refresh_coordinate_list()
        update_plugin_status()
        apply_language()
    except Exception as e:
        log(f"load_config error: {e}")

# ================= GUI HELPERS =================
def refresh_unique_dropdown():
    try:
        QtBind.clear(gui, dropdown_unique)
        all_uniques = sorted(list(discovered_uniques) + [u for u in COMMON_UNIQUES if u not in discovered_uniques])
        for unique in all_uniques:
            QtBind.append(gui, dropdown_unique, unique)
        refresh_unique_browser()
    except Exception as e:
        log(f"refresh_unique_dropdown error: {e}")

def refresh_scripts():
    try:
        QtBind.clear(gui, dropdown_script)
        for script in get_scripts():
            QtBind.append(gui, dropdown_script, script)
    except Exception as e:
        log(f"refresh_scripts error: {e}")

def refresh_mapping_list():
    try:
        QtBind.clear(gui, mappings_list)
        all_mapped = sorted(set(unique_script_map) | set(unique_coordinate_map))
        for unique in all_mapped:
            points = unique_coordinate_map.get(unique, [])
            mode = get_route_mode(unique)
            if mode == 'coordinates' and points:
                route = 'Coordinates (%d)' % len(points)
            else:
                route = unique_script_map.get(unique, '')
            QtBind.append(gui, mappings_list, f"{unique} --> {route}")
        refresh_unique_browser()
        refresh_selected_unique_details()
        refresh_configuration_health()
    except Exception as e:
        log(f"refresh_mapping_list error: {e}")

def refresh_pending_list():
    try:
        QtBind.clear(gui, pending_list)
        if pending_uniques:
            for unique in pending_uniques:
                marker = '[AYAR YOK]' if UI_LANGUAGE == 'tr' else '[NO ROUTE]'
                QtBind.append(gui, pending_list, f"{unique}    {marker}")
        else:
            QtBind.append(gui, pending_list, tr('no_setup'))
        refresh_unique_browser()
        refresh_configuration_health()
    except Exception as e:
        log(f"refresh_pending_list error: {e}")

def set_script():
    try:
        unique = _selected_unique()
        script = QtBind.text(gui, dropdown_script)
        if not unique or not script: return
        unique_script_map[unique] = script
        unique_route_modes[unique] = 'script'
        with _state_lock:
            if unique in pending_uniques:
                pending_uniques.remove(unique)
        save_config()
        refresh_mapping_list()
        refresh_pending_list()
        set_manager_status('Script route assigned.', COLOR_SUCCESS)
        log(f"Mapped: {unique} -> {script}")
    except Exception as e:
        log(f"set_script error: {e}")

def delete_selected_mapping():
    try:
        unique = _selected_unique()
        if not unique: return
        changed = False
        if get_route_mode(unique) == 'coordinates' and unique_coordinate_map.get(unique):
            del unique_coordinate_map[unique]
            unique_route_modes.pop(unique, None)
            changed = True
        elif unique in unique_script_map:
            del unique_script_map[unique]
            unique_route_modes.pop(unique, None)
            changed = True
        if changed:
            save_config()
            refresh_mapping_list()
            refresh_coordinate_list()
    except Exception as e:
        log(f"delete_selected_mapping error: {e}")

def delete_pending():
    try:
        selected = QtBind.text(gui, pending_list)
        if not selected: return
        if selected in (UI_TEXT['en']['no_setup'], UI_TEXT['tr']['no_setup']): return
        unique = selected.rsplit('    [NO ROUTE]', 1)[0].rsplit('    [AYAR YOK]', 1)[0].strip()
        with _state_lock:
            if unique in pending_uniques:
                pending_uniques.remove(unique)
        refresh_pending_list()
    except Exception as e:
        log(f"delete_pending error: {e}")

def _selected_unique():
    return selected_unique_name.strip()

def refresh_coordinate_list():
    try:
        QtBind.clear(gui, coordinate_list)
        unique_name = _selected_unique()
        points = unique_coordinate_map.get(unique_name, [])
        for index, point in enumerate(points, 1):
            QtBind.append(
                gui, coordinate_list,
                '%d. R%d | %.0f, %.0f, %.0f | %s' % (
                    index, point['region'], point['x'], point['y'], point.get('z', 0),
                    point.get('source', 'Manual')
                )
            )
        count_text = tr('saved_point' if len(points) == 1 else 'saved_points', count=len(points))
        if not points:
            count_text = tr('no_saved_points')
        QtBind.setText(gui, lbl_coordinate_count, fixed_width_text(
            '<font color="%s">%s</font>' % (COLOR_TEXT, count_text), 180))
    except Exception as error:
        if debug_enabled: log('refresh_coordinate_list error: %s' % error)

def coordinate_unique_changed(*args):
    refresh_coordinate_list()

def add_coordinate_fields():
    unique_name = _selected_unique()
    try:
        point = {
            'region': QtBind.text(gui, txt_coord_region).strip(),
            'x': QtBind.text(gui, txt_coord_x).strip(),
            'y': QtBind.text(gui, txt_coord_y).strip(),
            'z': QtBind.text(gui, txt_coord_z).strip() or '0',
        }
        added, message = _add_coordinate(unique_name, point, 'Manual')
        log('[Coordinates] %s: %s' % (unique_name or 'No unique', message))
        set_coordinate_editor_status(message, COLOR_SUCCESS if added else COLOR_WARNING)
        if added:
            QtBind.setText(gui, txt_coord_x, '')
            QtBind.setText(gui, txt_coord_y, '')
    except Exception as error:
        log('[Coordinates] Could not add point: %s' % error)

def add_my_current_position():
    unique_name = _selected_unique()
    try:
        position = phBot.get_position()
        if not position:
            log('[Coordinates] Character position is unavailable')
            return
        added, message = _add_coordinate(unique_name, position, 'Manual')
        log('[Coordinates] %s: %s' % (unique_name or 'No unique', message))
        set_coordinate_editor_status(message, COLOR_SUCCESS if added else COLOR_WARNING)
    except Exception as error:
        log('[Coordinates] Could not save current position: %s' % error)

def _find_visible_unique(unique_name):
    best = None
    character_position = phBot.get_position() or {}
    px = float(character_position.get('x', 0) or 0)
    py = float(character_position.get('y', 0) or 0)
    for monster_id, monster in (phBot.get_monsters() or {}).items():
        if not _is_unique_match(unique_name, monster.get('name', '')):
            continue
        distance = _distance_2d(px, py, monster.get('x', 0), monster.get('y', 0))
        if best is None or distance < best[0]:
            best = (distance, monster_id, monster)
    return best

def add_nearby_unique_position():
    unique_name = _selected_unique()
    if not unique_name:
        log('[Coordinates] Select a unique first')
        set_coordinate_editor_status('Select a unique first.', COLOR_WARNING)
        return
    try:
        found = _find_visible_unique(unique_name)
        if not found:
            log('[Coordinates] Selected unique is not nearby')
            set_coordinate_editor_status('Selected unique is not nearby.', COLOR_WARNING)
            return
        monster = found[2]
        point = {
            'region': monster.get('region', 0), 'x': monster.get('x', 0),
            'y': monster.get('y', 0), 'z': monster.get('z', 0),
        }
        added, message = _add_coordinate(unique_name, point, 'Manual')
        log('[Coordinates] %s: %s' % (unique_name, message))
        set_coordinate_editor_status(message, COLOR_SUCCESS if added else COLOR_WARNING)
    except Exception as error:
        log('[Coordinates] Could not save nearby unique: %s' % error)

def remove_coordinate():
    unique_name = _selected_unique()
    try:
        index = QtBind.currentIndex(gui, coordinate_list)
        points = unique_coordinate_map.get(unique_name, [])
        if index < 0 or index >= len(points):
            log('[Coordinates] Select a saved point first')
            return
        points.pop(index)
        if not points:
            unique_coordinate_map.pop(unique_name, None)
            if unique_name in unique_script_map:
                unique_route_modes[unique_name] = 'script'
            else:
                unique_route_modes.pop(unique_name, None)
        save_config()
        refresh_mapping_list()
        refresh_coordinate_list()
        refresh_pending_list()
        log('[Coordinates] Removed selected point for %s' % unique_name)
        set_coordinate_editor_status('Selected coordinate removed.', COLOR_SUCCESS)
    except Exception as error:
        log('[Coordinates] Could not remove point: %s' % error)

def toggle_auto_learn(checked=None):
    global auto_learn_coordinates
    auto_learn_coordinates = bool(checked)
    save_config()
    log('[Coordinates] Automatic learning is %s' % ('ON' if auto_learn_coordinates else 'OFF'))

def use_coordinate_route():
    unique_name = _selected_unique()
    if not unique_name or not unique_coordinate_map.get(unique_name):
        log('[Coordinates] Add at least one point for the selected unique first')
        return
    unique_route_modes[unique_name] = 'coordinates'
    save_config()
    refresh_mapping_list()
    set_manager_status('Coordinate route selected.', COLOR_SUCCESS)
    log('[Coordinates] %s will use its coordinate list' % unique_name)

def use_script_route():
    unique_name = _selected_unique()
    if not unique_name or unique_name not in unique_script_map:
        log('[Coordinates] Assign a script to the selected unique first')
        return
    unique_route_modes[unique_name] = 'script'
    save_config()
    refresh_mapping_list()
    set_manager_status('Script route selected.', COLOR_SUCCESS)
    log('[Coordinates] %s will use its assigned script' % unique_name)


def save_unique_reverse_setting():
    """Save Reverse-before-coordinates preferences for the selected unique."""
    unique_name = _selected_unique()
    if not unique_name:
        set_manager_status('Select a unique before saving Reverse settings.', COLOR_WARNING)
        return
    enabled = QtBind.isChecked(gui, chk_first_reverse)
    location = QtBind.text(gui, cmb_reverse_location).strip()
    if location not in REVERSE_LOCATIONS:
        location = ''
    unique_reverse_settings[unique_name] = {
        'enabled': enabled,
        'location': location,
    }
    save_config()
    if enabled and not location:
        set_manager_status('Choose a Reverse location, then save again.', COLOR_WARNING)
        log('[Reverse] %s is enabled but has no location.' % unique_name)
        return
    state = 'enabled to %s' % location if enabled else 'disabled'
    set_manager_status(tr('reverse_enabled_status', location=location, unique=unique_name)
                       if enabled else tr('reverse_disabled_status', unique=unique_name), COLOR_SUCCESS)
    log('[Reverse] %s: %s' % (unique_name, state))


def toggle_unique_reverse(checked=None):
    """Persist the checkbox immediately; the Save button commits dropdown changes."""
    unique_name = _selected_unique()
    if not unique_name:
        try: QtBind.setChecked(gui, chk_first_reverse, False)
        except: pass
        set_manager_status('Select a unique before enabling First Reverse.', COLOR_WARNING)
        return
    setting = unique_reverse_settings.setdefault(unique_name, {'enabled': False, 'location': ''})
    setting['enabled'] = bool(checked)
    selected_location = QtBind.text(gui, cmb_reverse_location).strip()
    if selected_location in REVERSE_LOCATIONS:
        setting['location'] = selected_location
    save_config()

# ================= AUTO RETURN LOGIC =================
def do_auto_return(unique_name):
    """
    Handle an unmapped unique spawn.
    Return when outside town; do nothing when already in town.
    """
    if not auto_return_enabled: return
    if _is_in_town() or just_returned:
        log(f"[AutoReturn] {unique_name} has no script -> Already in town, no action needed.")
        return
    log(f"[AutoReturn] {unique_name} has no script -> Outside town! Returning...")
    _trigger_return_to_town()

def _wait_for_town(on_arrived, label="Return", max_attempts=30):
    """
    Poll once per second until the character reaches town or the attempt limit.
    """
    global town_return_pending
    town_return_pending = True

    def _check(attempts=0):
        global town_return_pending
        # disable edilirse bekleyen town-varis zincirini durdur
        if not plugin_active:
            town_return_pending = False
            if debug_enabled: log(f"[{label}] Plugin disabled -> town wait cancelled.")
            return
        if _is_in_town():
            town_return_pending = False
            on_arrived()
            return
        if attempts >= max_attempts:
            _town_wait_failed(label)
            return
        threading.Timer(1.0, _check, [attempts + 1]).start()
    _check()


def _town_wait_failed(label):
    """Keep the queue pending when a return scroll is cancelled or fails."""
    global bot_state
    bot_state = 'RETURNING'
    _set_in_town(False)
    append_activity_once('return-failed:%s' % label,
                         'Return failed; waiting for town')
    refresh_runtime_dashboard()
    log('[%s] Town arrival timeout - return failed; queue preserved and waiting for town.' % label)

def toggle_auto_return(checked=None):
    global auto_return_enabled
    auto_return_enabled = bool(checked)
    state = "ON" if auto_return_enabled else "OFF"
    save_config()
    log(f"[AutoReturn] Auto Return is {state}")

# ================= QUEUE & SCRIPT LOGIC =================
def force_scan_alive_uniques():
    try:
        monsters = phBot.get_monsters()
        if monsters:
            with _state_lock:
                for monster_id, monster in monsters.items():
                    name = monster.get('name', '')
                    mtype = monster.get('type', 0)
                    if (mtype >= 2 or is_unique(name)) and name:
                        if name not in alive_uniques or not alive_uniques[name].get('alive', False):
                            alive_uniques[name] = {
                                'spawn_time': time.time(), 'alive': True,
                                'handled': False, 'last_seen': time.time()
                            }
        check_alive_uniques()
    except Exception as e:
        log(f"force_scan_alive_uniques error: {e}")

def start_script_btn():
    global force_stopped
    try:
        force_stopped = False
        unique = _selected_unique()
        if unique:
            if get_route_mode(unique) == 'coordinates' and unique_coordinate_map.get(unique):
                if not plugin_active:
                    log('[Coordinates] Start Monitoring before starting a manual coordinate hunt')
                    return
                alive_uniques[unique] = {
                    'spawn_time': time.time(), 'alive': True,
                    'handled': False, 'last_seen': time.time()
                }
                run_mapped_script(unique, 'spawn')
                if current_active_unique == unique:
                    log(f"Manual Coordinate Hunt: {unique}")
                return
            script_name = unique_script_map.get(unique)
            if script_name:
                script_path = os.path.join(scripts_folder, script_name)
                if os.path.exists(script_path):
                    with open(script_path, 'r', encoding='utf-8') as f:
                        script_content = f.read()
                    script_content = script_content.replace('{unique}', unique).replace('{event}', 'manual')
                    phBot.start_script(script_content)
                    append_activity_once('manual-route:%s' % unique,
                                         'Manual route started: %s' % unique)
                    with _state_lock:
                        if unique in unique_queue:
                            unique_queue.remove(unique)
                    update_queue_label()
                    log(f"Manual Start: {unique}")
                    return
        found_alive = [n for n, d in alive_uniques.items() if d.get('alive', False) and has_hunt_route(n)]
        if found_alive:
            with _state_lock:
                for uname in found_alive:
                    if uname not in unique_queue:
                        unique_queue.append(uname)
                sort_queue_by_priority()
            update_queue_label()
            auto_start_next_unique()
        else:
            log("No alive mapped uniques found. Select one manually.")
    except Exception as e:
        log(f"start_script_btn error: {e}")

def check_alive_uniques():
    try:
        tracked_alive = [n for n, d in alive_uniques.items() if d.get('alive', False)]
        if not tracked_alive:
            log("No tracked alive uniques")
            return
        for name in tracked_alive:
            status = "Coordinates" if get_route_mode(name) == 'coordinates' else ("Script" if name in unique_script_map else "No Route")
            log(f"   * {name} ({status})")
    except Exception as e:
        log(f"check_alive_uniques error: {e}")

def stop_script_btn():
    global current_active_unique, unique_queue, bot_state
    try:
        stop_attack_loop()
        stop_loot_timer()
        stop_coordinate_hunt()
        try: stop_script()
        except: pass
        try: stop_bot()
        except: pass
        current_active_unique = None
        update_active_unique_label()
        bot_state = 'IDLE'
        log("Script stopped manually. Bot is IDLE.")
    except Exception as e:
        log(f"stop_script_btn error: {e}")

# ================= LOOT SYSTEM =================
def wait_for_loot_async(remaining_sec, total_sec=None):
    """
    unique Ã¶ldÃ¼kten sonra loot_wait_sec kadar KOÅULSUZ bekler.
    Eskiden get_drops() boÅŸ dÃ¶nerse (pick filter'a uymayan bir item dÃ¼ÅŸtÃ¼yse,
    ya da server drop paketini henÃ¼z iÅŸlememiÅŸse) anÄ±nda ÅŸehre dÃ¶nÃ¼yordu â€”
    yani ayarlanan bekleme sÃ¼resi hiÃ§ iÅŸlemiyordu. ArtÄ±k get_drops() sadece
    bilgi amaÃ§lÄ± (yerde ne gÃ¶rÃ¼ndÃ¼ÄŸÃ¼nÃ¼ loglamak iÃ§in) kullanÄ±lÄ±yor, bekleme
    sÃ¼resini KISALTMIYOR/KESMÄ°YOR.
    """
    global loot_timer
    if not plugin_active: return
    if total_sec is None:
        total_sec = remaining_sec
        try:
            drops = phBot.get_drops()
            if drops:
                names = ', '.join(d.get('name', '?') for d in drops.values())
                log(f"[Loot] Dusen itemler: {names}")
            else:
                log(f"[Loot] get_drops() bos (pick filter disinda olabilir) - yine de {total_sec}s bekleniyor...")
        except Exception as e:
            log(f"[Loot] get_drops() error: {e}")

    if remaining_sec <= 0:
        finish_hunt_and_return()
        return
    loot_timer = threading.Timer(1.0, wait_for_loot_async, [remaining_sec - 1, total_sec])
    loot_timer.start()

def stop_loot_timer():
    global loot_timer
    if loot_timer:
        loot_timer.cancel()
        loot_timer = None

def finish_hunt_and_return():
    global current_active_unique, bot_state
    if not plugin_active: return
    try:
        append_activity_once('hunt-complete', 'Hunt completed')
        stop_attack_loop()
        stop_coordinate_hunt()
        try: stop_script()
        except: pass
        try: stop_bot()
        except: pass
        current_active_unique = None
        update_active_unique_label()
        bot_state = 'RETURNING'
        log("Returning to town...")
        threading.Timer(0.0, _do_return).start()
    except Exception as e:
        log(f"finish_hunt error: {e}")
        bot_state = 'IDLE'

def _trigger_return_to_town():
    """Central entry point for returning to town."""
    global bot_state, just_returned
    just_returned = False
    append_activity_once('return-town', 'Returning to town')
    bot_state = 'RETURNING'
    _set_in_town(False)  # The character has not reached town yet.
    stop_attack_loop()
    stop_loot_timer()
    stop_coordinate_hunt()
    try: stop_script()
    except: pass
    try: stop_bot()
    except: pass
    log("[AutoReturn] Triggering return to town...")
    threading.Timer(0.5, _do_return).start()

def _do_return():
    try: use_return_scroll()
    except: pass
    # Wait for actual town arrival instead of using a fixed delay.
    threading.Timer(1.0, lambda: _wait_for_town(_stop_after_return, label="Return")).start()

def _stop_after_return():
    global force_stopped, just_returned, bot_state
    force_stopped = False
    just_returned = True
    bot_state = 'IDLE'
    _set_in_town(True)
    # Training area'yi koru; bos script vermek area'yi tamamen resetler ve
    # sonrasinda grind slotunun geri yuklenmesini engeller.
    try: stop_script()
    except: pass
    try: stop_bot()
    except: pass
    log("Bot HARD STOPPED in town.")
    check_next_unique_after_return()
    threading.Timer(15.0, _clear_just_returned).start()

def _clear_just_returned():
    global just_returned
    just_returned = False

_keep_bot_stopped_counter = [0]

def check_next_unique_after_return():
    global bot_state
    bot_state = 'IDLE'
    update_queue_label()
    if plugin_active and unique_queue:
        with _state_lock:
            for uname in list(unique_queue):
                if has_hunt_route(uname) and alive_uniques.get(uname, {}).get('alive', False):
                    log(f"[Town] Next unique: {uname} -> Starting in 1s...")
                    threading.Timer(1.0, auto_start_next_unique).start()
                    return
                elif not has_hunt_route(uname):
                    unique_queue.remove(uname)
                    log(f"[Town] {uname} has no script -> removed from queue.")
        update_queue_label()

    # No queued hunt remains. Monitoring stays active, but the bot must remain
    # stopped in town instead of restoring the previous grind slot.
    if plugin_active:
        try: stop_script()
        except: pass
        try: stop_bot()
        except: pass
        log("[Town] Hunt queue empty; monitoring active and bot stopped in town.")
    else:
        log("[Town] Plugin disabled -> standing by in town.")

def get_loot_wait_seconds():
    try:
        if QtBind.isChecked(gui, cbx_loot_wait):
            return max(0, float(QtBind.text(gui, tbx_loot_wait) or "60"))
        return 0
    except: return 60

def _is_unique_match(unique_name: str, monster_name: str) -> bool:
    """
    Strict matching prevents false positives such as Tiger matching Tiger Girl.
    - exact match
    - or monster_name starts with unique_name followed by a space or parenthesis
    """
    u = unique_name.strip().lower()
    m = monster_name.strip().lower()
    if u == m:
        return True
    if m.startswith(u + " ") or m.startswith(u + "("):
        return True
    return False

def _find_mapped_name(spawn_name: str) -> str:
    """
    Resolve a spawn variant such as Tiger Girl (INT) to its mapped base name.
    Return the original spawn name when no mapping matches.
    """
    if has_hunt_route(spawn_name):
        return spawn_name
    for mapped in set(unique_script_map) | set(unique_coordinate_map):
        if _is_unique_match(mapped, spawn_name):
            return mapped
    return spawn_name


def _reverse_setting_for(unique_name):
    setting = unique_reverse_settings.get(unique_name, {})
    location = str(setting.get('location', '') or '').strip()
    return bool(setting.get('enabled', False)), location


def _cancel_pending_reverse(reason=None):
    """Invalidate a pending Reverse continuation and cancel its timeout."""
    global reverse_hunt_pending, reverse_timeout_timer, reverse_run_token
    had_pending = reverse_hunt_pending is not None
    reverse_run_token += 1
    reverse_hunt_pending = None
    if reverse_timeout_timer:
        reverse_timeout_timer.cancel()
        reverse_timeout_timer = None
    if reason and had_pending and debug_enabled:
        log('[Reverse] Pending coordinate hunt cancelled: %s' % reason)


def _fail_pending_reverse(token, message):
    """Abort this attempt without losing an alive unique from the queue."""
    global current_active_unique, bot_state
    if token != reverse_run_token or not reverse_hunt_pending:
        return
    unique_name = reverse_hunt_pending['unique']
    _cancel_pending_reverse()
    with _state_lock:
        if alive_uniques.get(unique_name, {}).get('alive', False):
            if unique_name not in unique_queue:
                unique_queue.append(unique_name)
                sort_queue_by_priority()
            alive_uniques[unique_name]['handled'] = True
    current_active_unique = None
    bot_state = 'IDLE'
    update_active_unique_label()
    update_queue_label()
    append_activity_once('reverse-failed:%s' % unique_name, message)
    set_manager_status(message, COLOR_ERROR)
    log('[Reverse] %s' % message)


def _reverse_timed_out(token):
    unique_name = reverse_hunt_pending['unique'] if reverse_hunt_pending else 'Unique'
    _fail_pending_reverse(token, 'Reverse timed out; %s remains queued.' % unique_name)


def _resume_coordinate_hunt_after_reverse(token):
    """Continue after teleport data settles, if the hunt is still valid."""
    global reverse_hunt_pending, reverse_timeout_timer, current_active_unique, bot_state
    if token != reverse_run_token or not reverse_hunt_pending:
        return
    unique_name = reverse_hunt_pending['unique']
    location = reverse_hunt_pending['location']
    reverse_hunt_pending = None
    if reverse_timeout_timer:
        reverse_timeout_timer.cancel()
        reverse_timeout_timer = None
    if not plugin_active or current_active_unique != unique_name:
        return
    if not alive_uniques.get(unique_name, {}).get('alive', False):
        log('[Reverse] %s is no longer alive; coordinate hunt cancelled.' % unique_name)
        current_active_unique = None
        bot_state = 'IDLE'
        update_active_unique_label()
        return
    if get_route_mode(unique_name) != 'coordinates' or not unique_coordinate_map.get(unique_name):
        log('[Reverse] %s no longer has an active coordinate route.' % unique_name)
        current_active_unique = None
        bot_state = 'IDLE'
        update_active_unique_label()
        return
    _set_in_town(False)
    append_activity_once('reverse-complete:%s' % unique_name,
                         'Reverse complete: %s -> %s' % (unique_name, location))
    log('[Reverse] Arrived at %s; starting %s coordinate route.' % (location, unique_name))
    start_coordinate_hunt(unique_name)
    refresh_runtime_dashboard(force=True)


def _start_reverse_before_coordinates(unique_name, location):
    """Use Reverse and defer coordinate pathfinding until teleported()."""
    global reverse_hunt_pending, reverse_timeout_timer, reverse_run_token
    _cancel_pending_reverse()
    reverse_run_token += 1
    token = reverse_run_token
    reverse_hunt_pending = {
        'token': token, 'unique': unique_name, 'location': location,
        'started': time.time(), 'phase': 'waiting',
    }
    try:
        used = reverse_return(3, location)
    except Exception as error:
        _fail_pending_reverse(token, 'Reverse error for %s: %s' % (unique_name, error))
        return False
    if not used:
        _fail_pending_reverse(token,
                              'Reverse could not be used; %s remains queued.' % unique_name)
        return False
    reverse_timeout_timer = threading.Timer(REVERSE_TIMEOUT_SEC, _reverse_timed_out, [token])
    reverse_timeout_timer.start()
    append_activity_once('reverse-start:%s' % unique_name,
                         'Using Reverse for %s: %s' % (unique_name, location))
    log('[Reverse] Using %s before %s coordinate route.' % (location, unique_name))
    refresh_runtime_dashboard(force=True)
    return True


def start_coordinate_route(unique_name):
    """Apply this unique's optional Reverse, then begin its coordinate hunt."""
    enabled, location = _reverse_setting_for(unique_name)
    if enabled:
        if location not in REVERSE_LOCATIONS:
            log('[Reverse] %s has no valid Reverse location; hunt remains queued.' % unique_name)
            with _state_lock:
                if unique_name not in unique_queue:
                    unique_queue.append(unique_name)
                    sort_queue_by_priority()
            update_queue_label()
            return False
        try:
            visible = _find_visible_unique(unique_name)
        except Exception:
            visible = None
        if visible:
            log('[Reverse] %s is already visible; engaging without Reverse.' % unique_name)
            _engage_coordinate_target(unique_name, visible[1], visible[2])
            return True
        return _start_reverse_before_coordinates(unique_name, location)
    start_coordinate_hunt(unique_name)
    return True


def stop_coordinate_hunt():
    """Cancel coordinate navigation and invalidate every pending callback."""
    global coordinate_hunt, coordinate_timer, coordinate_run_token
    _cancel_pending_reverse('coordinate hunt stopped')
    coordinate_run_token += 1
    coordinate_hunt = None
    if coordinate_timer:
        coordinate_timer.cancel()
        coordinate_timer = None

def _schedule_coordinate_tick(token, delay=COORDINATE_SCAN_INTERVAL_SEC):
    global coordinate_timer
    if token != coordinate_run_token:
        return
    coordinate_timer = threading.Timer(delay, _coordinate_tick_guarded, [token])
    coordinate_timer.start()

def _coordinate_tick_guarded(token):
    """Keep the coordinate monitor alive after transient phBot API errors."""
    try:
        _coordinate_tick(token)
    except Exception as error:
        if token != coordinate_run_token or not coordinate_hunt or not plugin_active:
            return
        log('[Coordinates] Search monitor error: %s; retrying' % error)
        _schedule_coordinate_tick(token, 0.5)

def _engage_coordinate_target(unique_name, monster_id, monster):
    """Stop navigation and immediately start botting at the visible unique."""
    global coordinate_hunt, bot_state
    try: stop_script()
    except: pass
    try: stop_bot()
    except: pass
    region = int(monster.get('region', 0) or 0)
    if region == 0:
        position = phBot.get_position() or {}
        region = int(position.get('region', 0) or 0)
    x = float(monster.get('x', 0) or 0)
    y = float(monster.get('y', 0) or 0)
    if region == 0 or (x == 0 and y == 0):
        log('[Coordinates] Visible unique position is invalid')
        handle_unique_timeout()
        return
    position_set = set_training_position(region, x, y, 0.0)
    set_training_radius(UNIQUE_TRAINING_RADIUS)
    if position_set is False:
        log('[Coordinates] Training position could not be set; select an active Training Area')
    phBot.start_bot()
    stop_coordinate_hunt()
    start_attack_loop()
    bot_state = 'HUNTING'
    log('[Coordinates] Found %s at (%.0f, %.0f); training area set and bot started' % (unique_name, x, y))

def _coordinate_hunt_exhausted(unique_name):
    global current_active_unique, bot_state, unique_not_found_count
    stop_coordinate_hunt()
    try: stop_script()
    except: pass
    with _state_lock:
        if unique_name in alive_uniques:
            alive_uniques[unique_name]['alive'] = False
            alive_uniques[unique_name]['handled'] = False
    current_active_unique = None
    unique_not_found_count = 0
    update_active_unique_label()
    bot_state = 'RETURNING'
    log('[Coordinates] %s was not found at any saved point' % unique_name)
    _trigger_return_to_town()

def _start_coordinate_point(token):
    global coordinate_hunt, last_pathfinding_time
    if token != coordinate_run_token or not coordinate_hunt or not plugin_active:
        return
    unique_name = coordinate_hunt['unique']
    points = coordinate_hunt['points']
    index = coordinate_hunt['index']
    if index >= len(points):
        _coordinate_hunt_exhausted(unique_name)
        return
    visible = _find_visible_unique(unique_name)
    if visible:
        _engage_coordinate_target(unique_name, visible[1], visible[2])
        return
    elapsed = time.time() - last_pathfinding_time
    if elapsed < PATHFINDING_COOLDOWN_SEC:
        wait_seconds = PATHFINDING_COOLDOWN_SEC - elapsed
        log('[Coordinates] Pathfinding cooldown; next point starts in %.1fs' % wait_seconds)
        _schedule_coordinate_tick(token, wait_seconds)
        coordinate_hunt['phase'] = 'pathfinding_wait'
        return
    point = points[index]
    last_pathfinding_time = time.time()
    try:
        commands = generate_script(point['region'], point['x'], point['y'], point.get('z', 0.0))
    except Exception as error:
        log('[Coordinates] Route generation failed for point %d: %s' % (index + 1, error))
        coordinate_hunt['index'] += 1
        _schedule_coordinate_tick(token)
        return
    if not isinstance(commands, list) or not commands:
        if commands is False:
            coordinate_hunt['phase'] = 'pathfinding_wait'
            _schedule_coordinate_tick(token, PATHFINDING_COOLDOWN_SEC)
            return
        log('[Coordinates] No route for point %d; trying the next point' % (index + 1))
        coordinate_hunt['index'] += 1
        _schedule_coordinate_tick(token)
        return
    try:
        start_script('\n'.join(commands))
        coordinate_hunt['phase'] = 'walking'
        coordinate_hunt['route_started'] = time.time()
        log('[Coordinates] Walking to point %d/%d: R%d (%.0f, %.0f)' % (
            index + 1, len(points), point['region'], point['x'], point['y']))
        _schedule_coordinate_tick(token)
    except Exception as error:
        log('[Coordinates] Could not start route for point %d: %s' % (index + 1, error))
        coordinate_hunt['index'] += 1
        _schedule_coordinate_tick(token)

def _coordinate_tick(token):
    if token != coordinate_run_token or not coordinate_hunt or not plugin_active:
        return
    unique_name = coordinate_hunt['unique']
    visible = _find_visible_unique(unique_name)
    if visible:
        _engage_coordinate_target(unique_name, visible[1], visible[2])
        return
    if time.time() - coordinate_hunt['started'] >= get_timeout_seconds():
        log('[Coordinates] Hunt timeout while searching for %s' % unique_name)
        handle_unique_timeout()
        return
    phase = coordinate_hunt.get('phase')
    if phase == 'pathfinding_wait':
        _start_coordinate_point(token)
        return
    point = coordinate_hunt['points'][coordinate_hunt['index']]
    if phase == 'walking':
        position = phBot.get_position() or {}
        same_region = int(position.get('region', 0) or 0) == int(point['region'])
        arrived = same_region and _distance_2d(position.get('x', 0), position.get('y', 0), point['x'], point['y']) <= COORDINATE_ARRIVAL_DISTANCE
        if arrived:
            try: stop_script()
            except: pass
            coordinate_hunt['phase'] = 'scanning'
            coordinate_hunt['scan_deadline'] = time.time() + COORDINATE_SEARCH_SEC
            log('[Coordinates] Point %d reached; scanning for 2 seconds' % (coordinate_hunt['index'] + 1))
    elif phase == 'scanning' and time.time() >= coordinate_hunt.get('scan_deadline', 0):
        coordinate_hunt['index'] += 1
        coordinate_hunt['phase'] = 'pathfinding_wait'
        _start_coordinate_point(token)
        return
    _schedule_coordinate_tick(token)

def start_coordinate_hunt(unique_name):
    global coordinate_hunt, coordinate_run_token
    stop_coordinate_hunt()
    coordinate_run_token += 1
    token = coordinate_run_token
    coordinate_hunt = {
        'unique': unique_name,
        'points': [dict(point) for point in unique_coordinate_map.get(unique_name, [])],
        'index': 0, 'phase': 'pathfinding_wait', 'started': time.time()
    }
    _start_coordinate_point(token)

# ================= CORE UNIQUE RUNNER =================
def _on_unique_spawn(unique_name):
    """
    Handle a unique spawn while the plugin is active.
    - Queue it when another unique is active.
    - Queue it and return first when outside town.
    - Start immediately when already in town.
    """
    global bot_state, current_active_unique, force_stopped, just_returned
    append_activity_once('detected:%s' % unique_name, 'Detected: %s' % unique_name)

    # Keep the current hunt running and queue the new mapped unique.
    if current_active_unique and current_active_unique.lower() != unique_name.lower():
        if has_hunt_route(unique_name):
            with _state_lock:
                if unique_name not in unique_queue:
                    unique_queue.append(unique_name)
                    sort_queue_by_priority()
            update_queue_label()
            log(f"[Queue] {unique_name} queued (busy with {current_active_unique}).")
        return

    # A spawn event for the coordinate hunt already in progress must not enter
    # the generic "outside town" return/queue branch. Check the visible list
    # immediately and wake the route monitor so engagement cannot be delayed by
    # a stale or failed timer.
    if (current_active_unique and coordinate_hunt and
            current_active_unique.lower() == unique_name.lower()):
        try:
            visible = _find_visible_unique(current_active_unique)
            if visible:
                _engage_coordinate_target(current_active_unique, visible[1], visible[2])
                return
        except Exception as error:
            log('[Coordinates] Immediate spawn check error: %s' % error)
        if coordinate_timer:
            coordinate_timer.cancel()
        _schedule_coordinate_tick(coordinate_run_token, 0.0)
        return

    # Check the town state before starting any new action.
    # just_returned skips this check once immediately after arrival.
    in_town = just_returned or _is_in_town()
    if not in_town:
        # A visible coordinate-route target can be engaged from the grind slot
        # without an unnecessary town round trip. Preserve the grind slot first.
        if get_route_mode(unique_name) == 'coordinates' and bot_state == 'IDLE':
            try:
                visible = _find_visible_unique(unique_name)
            except Exception as error:
                visible = None
                if debug_enabled:
                    log('[Coordinates] Visible target check error: %s' % error)
            if visible:
                log('[Coordinates] %s is already visible -> engaging directly.' % unique_name)
                capture_slot()
                run_mapped_script(unique_name, 'spawn', allow_outside_coordinate=True)
                return

        # --- Script'i OLMAYAN unique â†’ grind'i BOLME ---
        # (eski surumde script olsun olmasin sehre donuyordu; rastgele bir unique
        #  yaninda spawn olunca bot slotu birakip sehre isinlaniyordu = bug)
        if not has_hunt_route(unique_name):
            if auto_return_enabled and bot_state == 'IDLE':
                log(f"[Spawn] {unique_name} (script yok) -> Auto Return acik, donuluyor...")
                do_auto_return(unique_name)
            else:
                log(f"[Spawn] {unique_name} (script yok) -> yok sayiliyor, slotta kaliniyor.")
            return

        # --- Script'li unique â†’ slotu kaydet, sehre don, sonra script calissin ---
        log(f"[Spawn] {unique_name} slotta spawn oldu -> slot kaydedilip sehre donuluyor...")
        with _state_lock:
            if unique_name not in unique_queue:
                unique_queue.append(unique_name)
                sort_queue_by_priority()
        update_queue_label()
        if bot_state == 'IDLE':
            capture_slot()            # slotu birakmadan once kaydet (training area hala slot)
            _trigger_return_to_town()
        return

    # Attack immediately when the unique is already nearby.
    try:
        monsters = phBot.get_monsters()
        if monsters:
            target_name = unique_name.lower()
            for m_id, m_data in monsters.items():
                m_name = m_data.get('name', '').lower()
                if _is_unique_match(target_name, m_name):
                    log(f"[INSTANT] Attacking {unique_name} immediately!")
                    break
    except Exception as e:
        if debug_enabled: log(f"[Spawn] instant attack error: {e}")

    # Start the mapped script flow.
    run_mapped_script(unique_name, 'spawn')

def run_mapped_script(unique_name, event_type, allow_outside_coordinate=False):
    global current_active_unique, unique_queue, bot_state, force_stopped, just_returned
    try:
        # =================== DEATH EVENT ===================
        if event_type == 'death':
            if current_active_unique and current_active_unique.lower() == unique_name.lower():
                log(f"{unique_name} DIED. Stopping Bot immediately.")
                stop_attack_loop()
                stop_loot_timer()
                stop_coordinate_hunt()
                try: stop_script()
                except: pass
                try: stop_bot()
                except: pass
                with _state_lock:
                    if unique_name in unique_queue:
                        unique_queue.remove(unique_name)
                update_queue_label()
                current_active_unique = None
                update_active_unique_label()
                bot_state = 'RETURNING'
                loot_wait_sec = get_loot_wait_seconds()
                if loot_wait_sec > 0:
                    log(f"Waiting loot {loot_wait_sec}s...")
                    wait_for_loot_async(loot_wait_sec)
                else:
                    finish_hunt_and_return()
            else:
                with _state_lock:
                    removed = unique_name in unique_queue
                    if removed:
                        unique_queue.remove(unique_name)
                if removed:
                    update_queue_label()
                    log(f"{unique_name} removed from queue (Died while waiting).")
                # Stop the active route and return if its target died.
                if current_active_unique and current_active_unique.lower() == unique_name.lower():
                    log(f"{unique_name} died while script was running -> stopping script.")
                    stop_attack_loop()
                    stop_loot_timer()
                    try: stop_script()
                    except: pass
                    try: stop_bot()
                    except: pass
                    current_active_unique = None
                    update_active_unique_label()
                    bot_state = 'IDLE'
                    if not _is_in_town():
                        log(f"{unique_name} died outside town -> returning to town...")
                        _trigger_return_to_town()
                    elif unique_queue and plugin_active:
                        threading.Timer(1.0, auto_start_next_unique).start()
            if unique_name in alive_uniques:
                alive_uniques[unique_name]['alive'] = False
                alive_uniques[unique_name]['handled'] = False
            return

        # =================== SPAWN EVENT ===================
        if not is_unique(unique_name): return
        if unique_name not in alive_uniques: return
        if not alive_uniques[unique_name].get('alive', False): return
        if alive_uniques[unique_name].get('handled', False): return

        # Auto-return for an unmapped unique while the bot is idle.
        if not has_hunt_route(unique_name):
            with _state_lock:
                if unique_name not in pending_uniques:
                    pending_uniques.append(unique_name)
                    refresh_pending_list()
                    log(f"[Pending] {unique_name} has no script -> added to pending.")
            if bot_state == 'IDLE' and auto_return_enabled:
                do_auto_return(unique_name)
            alive_uniques[unique_name]['handled'] = True
            return

        # Queue the unique when the character is outside town.
        if (not allow_outside_coordinate and not just_returned and
                not _is_in_town()):
            with _state_lock:
                if unique_name not in unique_queue:
                    unique_queue.append(unique_name)
                    sort_queue_by_priority()
                    update_queue_label()
                    log(f"[Queue] {unique_name} queued (outside town - will run after current).")
            alive_uniques[unique_name]['handled'] = True
            return

        if force_stopped:
            if bot_state == 'IDLE' and plugin_active:
                log(f"[Town] New spawn: {unique_name} -> Releasing force stop...")
                force_stopped = False
            else:
                log(f"Blocked: Bot is force stopped.")
                return

        if bot_state != 'IDLE':
            if current_active_unique and current_active_unique.lower() != unique_name.lower():
                with _state_lock:
                    if unique_name not in unique_queue:
                        unique_queue.append(unique_name)
                        sort_queue_by_priority()
                update_queue_label()
                log(f"{unique_name} added to queue (Bot is {bot_state}).")
            else:
                log(f"Already targeting {unique_name}")
            return

        script_name = unique_script_map.get(unique_name)
        script_path = os.path.join(scripts_folder, script_name) if script_name else None
        coordinate_mode = get_route_mode(unique_name) == 'coordinates'
        if not coordinate_mode and (not script_path or not os.path.exists(script_path)):
            log(f"Script not found: {script_path}")
            alive_uniques[unique_name]['handled'] = True
            return

        try:
            force_stopped = False
            just_returned = False
            _set_in_town(False)  # The character is leaving town.
            try: stop_bot()
            except: pass

            with _state_lock:
                if unique_name in unique_queue:
                    unique_queue.remove(unique_name)
            update_queue_label()

            current_active_unique = unique_name
            update_active_unique_label()

            if not plugin_active:
                log("Plugin disabled! Aborting.")
                current_active_unique = None
                bot_state = 'IDLE'
                return

            # Look up the unique coordinates.
            monsters = phBot.get_monsters()
            target_x, target_y, target_region = 0, 0, 0
            found_coords = False
            if monsters:
                for m_id, m_data in monsters.items():
                    if _is_unique_match(unique_name.lower(), m_data.get('name', '').lower()):
                        target_x      = m_data.get('x', 0)
                        target_y      = m_data.get('y', 0)
                        target_region = m_data.get('region', 0)
                        found_coords  = True
                        log(f"Found {unique_name} at: ({target_x}, {target_y}) region={target_region}")
                        break

            bot_state = 'HUNTING'

            # Coordinate routes take priority when at least one point is saved.
            if coordinate_mode and unique_coordinate_map.get(unique_name):
                started = start_coordinate_route(unique_name)
                alive_uniques[unique_name]['handled'] = True
                if started:
                    log(f"ACTIVE: {current_active_unique}")
                else:
                    current_active_unique = None
                    bot_state = 'IDLE'
                    update_active_unique_label()
                return

            # ===== ENGAGE MODE =====
            # If the unique is nearby, move the training area to it and start the bot.
            if found_coords and target_x != 0:
                if target_region == 0:
                    try:
                        pos = phBot.get_position()
                        if pos: target_region = pos.get('region', 0)
                    except: pass
                # set_training_script('') aktif training area'yi sifirlar; bu durumda
                # set_training_position hicbir sey yapmaz. Mevcut area'yi koruyup
                # koordinat ve radius'u ayri ayri guncelle.
                position_set = set_training_position(target_region, target_x, target_y, 0.0)
                radius_set = set_training_radius(UNIQUE_TRAINING_RADIUS)
                if position_set is False:
                    log("[Engage] Training position ayarlanamadi; aktif Training Area secili mi?")
                phBot.start_bot()
                start_attack_loop()
                log(f"Started: {unique_name} (Engage Mode - pos set to unique)")
            else:
                # If the unique is distant, run the walk script to reach it.
                set_training_script(script_path)
                with open(script_path, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                script_content = script_content.replace('{unique}', unique_name).replace('{event}', 'auto')
                phBot.start_script(script_content)
                start_attack_loop()
                log(f"Started: {unique_name} (Script Mode - walking to unique)")

            alive_uniques[unique_name]['handled'] = True
            log(f"ACTIVE: {current_active_unique}")

        except Exception as e:
            log(f"run_mapped_script error: {e}")
            current_active_unique = None
            update_active_unique_label()
            alive_uniques[unique_name]['handled'] = False
            bot_state = 'IDLE'

    except Exception as e:
        log(f"run_mapped_script critical error: {e}")

# ================= PLUGIN CONTROLS =================
def do_nothing(checked=None): pass

def toggle_debug(checked=None):
    global debug_enabled
    debug_enabled = bool(checked)
    log(f"Debug mode {'ON' if debug_enabled else 'OFF'}")

def _is_in_town():
    """
    Determine whether the character is in town from the current region.
    """
    global _in_town_state
    try:
        pos = phBot.get_position()
        if pos:
            region = pos.get('region', 0)
            if region in TOWN_REGIONS:
                _in_town_state = True
                return True
            else:
                _in_town_state = False
                return False
    except: pass
    return _in_town_state

def _set_in_town(value: bool):
    """Update the manually tracked town state."""
    global _in_town_state
    _in_town_state = value

# ================= GRIND SLOT SAVE / RESTORE =================
def capture_slot():
    """
    Mevcut training area'yi (grind slotu) kaydeder ki av bitince geri donebilelim.
    - Sadece av DISINDA cagrilmali (current_active_unique None) â€” yoksa training area
      unique'in koordinatina bakiyor olur, onu slot sanmayalim.
    - Town'u slot sanmamak icin region town ise kaydetmez.
    get_training_area() kalici bir ayar dondurur (karakter fiziksel olarak town'da olsa
    bile configli slot'u verir), o yuzden enable aninda town'da da olsa slot yakalanabilir.
    """
    global saved_slot
    if current_active_unique:
        return
    try:
        area = get_training_area()
        if not area:
            return
        region = int(area.get('region', 0) or 0)
        x = float(area.get('x', 0) or 0)
        y = float(area.get('y', 0) or 0)
        if x == 0 and y == 0:
            return  # ayarlanmamis / gecersiz slot
        if region in TOWN_REGIONS:
            return  # town'u slot olarak kaydetme
        saved_slot = {
            'region': region, 'x': x, 'y': y,
            'z': float(area.get('z', 0) or 0),
            'radius': float(area.get('radius', 50.0) or 50.0),
            'path': area.get('path', '') or '',
        }
        save_config()
        log(f"[Slot] Grind slotu kaydedildi ({x:.0f},{y:.0f}) region={region}")
    except Exception as e:
        log(f"capture_slot error: {e}")

def restore_slot():
    """
    Kaydedilen grind slotuna geri doner ve botu baslatir (townda beklemez).
    Slot yoksa False doner ki cagiran 'townda bekle' desin.
    """
    try:
        if not saved_slot:
            return False
        s = saved_slot
        saved_path = s.get('path', '') or ''
        if saved_path:
            try: set_training_script(saved_path)
            except: pass
        position_set = set_training_position(s['region'], s['x'], s['y'], s.get('z', 0.0))
        radius_set = set_training_radius(s.get('radius', 50.0))
        if position_set is False:
            log("[Slot] Training position geri yuklenemedi; aktif Training Area secili mi?")
            return False
        phBot.start_bot()
        log(f"[Slot] Slota geri donuluyor ({s['x']:.0f},{s['y']:.0f}) region={s['region']} -> grind devam.")
        return True
    except Exception as e:
        log(f"restore_slot error: {e}")
        return False

def _return_then_enable():
    """Use a return scroll and poll until the character reaches town."""
    log("Plugin ENABLED - Not in town -> Using return scroll first...")
    try: use_return_scroll()
    except: pass
    threading.Timer(1.0, lambda: _wait_for_town(_after_return_enable, label="Enable")).start()

def _after_return_enable():
    """Finish enabling the plugin after returning to town."""
    global bot_state, force_stopped, just_returned
    if not plugin_active: return
    bot_state = 'IDLE'
    force_stopped = False
    just_returned = False
    _set_in_town(True)
    log("Arrived in town -> Plugin ready.")
    if not current_active_unique and unique_queue:
        log("Auto-starting first unique from saved queue...")
        auto_start_next_unique()
    else:
        log("Plugin is active and waiting for uniques...")

def enable_plugin_monitoring():
    global plugin_active, force_stopped, just_returned
    if plugin_active: return
    force_stopped = False
    plugin_active = True
    update_plugin_status()
    save_config()
    log("Plugin ENABLED")
    # Check the actual town state after a short delay.
    threading.Timer(2.0, _check_town_on_enable).start()

def _check_town_on_enable():
    """Check the town state shortly after monitoring is enabled."""
    global just_returned
    if not plugin_active: return
    # Enable aninda mevcut slotu yakala (training area kalici; town'da olsak bile gecerli slot'u verir)
    capture_slot()
    if _is_in_town():
        just_returned = True
        _set_in_town(True)
        log("Plugin ENABLED - In town, ready.")
        if not current_active_unique and unique_queue:
            log("Auto-starting first unique from saved queue...")
            threading.Timer(1.0, auto_start_next_unique).start()
        else:
            log("Plugin is active and waiting for uniques...")
        threading.Timer(10.0, _clear_just_returned).start()
    else:
        _set_in_town(False)
        # Slotta grind ediyoruz. Kuyrukta islenmeyi bekleyen alive+scriptli unique varsa
        # once sehre donup onu avla; yoksa grind'i BOLME, slotta beklemeye devam et.
        has_ready = any(has_hunt_route(u) and alive_uniques.get(u, {}).get('alive', False)
                        for u in list(unique_queue))
        if has_ready:
            log("Plugin ENABLED - Bekleyen scriptli unique var -> sehre donup avlaniyor.")
            _trigger_return_to_town()
        else:
            log("Plugin ENABLED - Slotta grind. Scriptli unique spawn olunca avlanacak.")

def disable_plugin_monitoring():
    global plugin_active, current_active_unique, bot_state, town_return_pending
    if not plugin_active: return
    stop_attack_loop()
    stop_loot_timer()
    stop_coordinate_hunt()
    if current_active_unique:
        try: stop_bot()
        except: pass
    try: stop_script()
    except: pass
    try: stop_bot()
    except: pass
    current_active_unique = None
    update_active_unique_label()
    bot_state = 'IDLE'
    town_return_pending = False
    plugin_active = False
    update_plugin_status()
    save_config()
    log("Plugin DISABLED")

def update_active_unique_label():
    try:
        if lbl_active_unique is None: return
        value = current_active_unique if current_active_unique else tr('none')
        color = COLOR_SUCCESS if current_active_unique else COLOR_MUTED
        QtBind.setText(
            gui, lbl_active_unique,
            fixed_width_text('<font color="%s"><b>%s</b></font>' % (color, value), 250)
        )
        if _last_activity_state['target'] != value:
            _last_activity_state['target'] = value
            append_activity('Current target: %s' % value)
        refresh_runtime_dashboard()
    except: pass

def update_plugin_status():
    """Keep the live status row synchronized with the plugin state."""
    try:
        if plugin_active:
            status = '<font color="%s"><b>%s</b></font>' % (COLOR_SUCCESS, tr('active'))
        else:
            status = '<font color="%s"><b>%s</b></font>' % (COLOR_MUTED, tr('disabled'))
        QtBind.setText(gui, lbl_plugin_status, fixed_width_text(status, 250))
        if _last_activity_state['plugin'] != plugin_active:
            _last_activity_state['plugin'] = plugin_active
            append_activity('Monitoring %s' % ('enabled' if plugin_active else 'disabled'))
        refresh_runtime_dashboard()
    except: pass

def update_queue_label():
    try:
        if lbl_queue is None: return
        queue_text = f"({len(unique_queue)}) {', '.join(unique_queue[:3])}" if unique_queue else tr('queue_empty')
        QtBind.setText(
            gui, lbl_queue,
            fixed_width_text('<font color="%s">%s</font>' % (COLOR_TEXT, queue_text), 300)
        )
        refresh_queue_list()
        queue_state = tuple(unique_queue)
        previous_queue = _last_activity_state['queue']
        if previous_queue != queue_state:
            _last_activity_state['queue'] = queue_state
            previous_names = set(previous_queue or ())
            for unique_name in queue_state:
                if unique_name not in previous_names:
                    append_activity_once('queued:%s' % unique_name,
                                         'Queued: %s' % unique_name)
            if previous_queue is not None and not queue_state and previous_queue:
                append_activity('Queue is empty')
        refresh_configuration_health()
    except: pass

def refresh_queue_list():
    try:
        if queue_list is None: return
        QtBind.clear(gui, queue_list)
        if unique_queue:
            for i, unique in enumerate(unique_queue, 1):
                priority = get_unique_priority(unique)
                route = ('%s (%d)' % (tr('coordinates'), len(unique_coordinate_map[unique]))) if get_route_mode(unique) == 'coordinates' else unique_script_map.get(unique, "[%s]" % tr('no_route'))
                QtBind.append(gui, queue_list, f"{i}. [{priority}] {unique} -> {route}")
        else:
            QtBind.append(gui, queue_list, tr('queue_empty'))
    except: pass

def clear_queue_btn():
    with _state_lock:
        unique_queue.clear()
    update_queue_label()
    log("Queue cleared")

def remove_from_queue_btn():
    try:
        selected = QtBind.text(gui, queue_list)
        if not selected or "Empty" in selected: return
        if "->" in selected:
            unique_name = selected.split("->")[0].strip()
            if ". " in unique_name: unique_name = unique_name.split(". ", 1)[1].strip()
            with _state_lock:
                removed = unique_name in unique_queue
                if removed:
                    unique_queue.remove(unique_name)
            if removed:
                update_queue_label()
    except: pass

def auto_start_next_unique():
    global current_active_unique
    try:
        if not plugin_active: return
        if not unique_queue: return

        # Return first when outside town and not immediately after arrival.
        if not just_returned and not _is_in_town():
            log("[AutoReturn] auto_start_next_unique: Not in town -> Returning first!")
            if bot_state == 'IDLE':
                _trigger_return_to_town()
            return

        with _state_lock:
            if not unique_queue: return
            sort_queue_by_priority()
            next_unique = unique_queue.pop(0)
        update_queue_label()
        log(f"Auto-starting: {next_unique}")
        if next_unique in alive_uniques:
            alive_uniques[next_unique]['handled'] = False
        run_mapped_script(next_unique, 'spawn')
    except Exception as e:
        log(f"auto_start_next_unique error: {e}")

def add_to_queue_btn():
    try:
        selected = _selected_unique()
        if not selected or not has_hunt_route(selected):
            log("Select a mapped unique first")
            return
        with _state_lock:
            if selected not in unique_queue:
                unique_queue.append(selected)
                sort_queue_by_priority()
        update_queue_label()
    except: pass

# ================= ATTACK SYSTEM =================
def get_timeout_seconds():
    try:
        if not QtBind.isChecked(gui, cbx_unique_timeout): return 99999
        txt = QtBind.text(gui, tbx_unique_timeout)
        if not txt: return 1200
        if "min" in txt.lower():
            val = int(''.join(filter(str.isdigit, txt)))
            return val * 60
        return 1200
    except: return 1200

def start_attack_loop():
    global attack_timer, unique_not_found_count, script_finished
    if attack_timer: attack_timer.cancel()
    unique_not_found_count = 0
    script_finished = False
    engaged = [False]        # Ensure the engage setup runs only once.
    lost_after_engage = [0]  # Consecutive missing ticks after engagement.

    def attack_tick():
        global attack_timer, unique_not_found_count, script_finished, current_active_unique
        if not current_active_unique or not plugin_active: return
        try:
            monsters = phBot.get_monsters()
            unique_found = False
            target_name = current_active_unique.lower()
            if monsters:
                for monster_id, monster in monsters.items():
                    monster_name = monster.get('name', '').lower()
                    if _is_unique_match(target_name, monster_name):
                        unique_found = True
                        unique_not_found_count = 0
                        lost_after_engage[0] = 0

                        # On first contact, stop the route and center the training area on the target.
                        if not engaged[0]:
                            engaged[0] = True
                            script_finished = True
                            log(f"[Engage] Found {monster.get('name')} -> stop script, set training pos, start bot")
                            try: phBot.stop_script()
                            except: pass
                            try: phBot.stop_bot()
                            except: pass
                            try:
                                mx = float(monster.get('x', 0))
                                my = float(monster.get('y', 0))
                                region = int(monster.get('region', 0) or 0)
                                if region == 0:
                                    pos = phBot.get_position()
                                    if pos: region = int(pos.get('region', 0) or 0)
                                if region != 0:
                                    # Bos training script vermek area'yi resetledigi icin
                                    # burada yalnizca koordinat ve radius degistirilir.
                                    position_set = set_training_position(region, mx, my, 0.0)
                                    radius_set = set_training_radius(UNIQUE_TRAINING_RADIUS)
                                    if position_set is False:
                                        log("[Engage] Training position ayarlanamadi; aktif Training Area secili mi?")
                                    phBot.start_bot()
                                    log(f"[Engage] Training area set to ({mx:.0f},{my:.0f}) region={region}")
                            except Exception as e:
                                if debug_enabled: log(f"[Engage] error: {e}")

                        # phBot selects the unique through its own target settings.
                        # There is no public set_target/attack_monster plugin API.
                        if debug_enabled: log(f"Tracking {monster.get('name')}")
                        break

            if not unique_found:
                # ===== GENEL TIMEOUT: script_finished ÅŸartÄ± olmadan hunt baÅŸÄ±ndan beri sayar =====
                # (Eskiden bu sayaÃ§ sadece unique bir kere bulunduktan sonra iÅŸliyordu; script
                #  hedefe hiÃ§ ulaÅŸamazsa hiÃ§bir zaman tetiklenmiyordu â†’ bot HUNTING'de kilitli kalÄ±yordu)
                unique_not_found_count += 1
                timeout_seconds = get_timeout_seconds()
                max_attempts = timeout_seconds / 0.1
                if unique_not_found_count >= max_attempts:
                    log(f"TIMEOUT: {current_active_unique} missing")
                    handle_unique_timeout()
                    return

                # ===== HIZLI FALLBACK: engage edildikten sonra unique aniden kayboldu =====
                # (muhtemelen Ã¶ldÃ¼ ama chat/packet death tespiti bunu yakalamadÄ±) â†’ tam
                # timeout sÃ¼resini (dakikalarca) beklemeden kÄ±sa bir grace period sonunda
                # Ã¶lmÃ¼ÅŸ gibi davranÄ±p loot bekle + ÅŸehre dÃ¶n akÄ±ÅŸÄ±nÄ± tetikle.
                if engaged[0]:
                    lost_after_engage[0] += 1
                    grace_attempts = LOST_TARGET_GRACE_SEC / 0.1
                    if lost_after_engage[0] >= grace_attempts:
                        log(f"[LostTarget] {current_active_unique} disappeared after engage -> assuming dead, returning.")
                        handle_presumed_death()
                        return
        except: pass

        if current_active_unique and plugin_active:
            attack_timer = threading.Timer(0.1, attack_tick)
            attack_timer.start()

    attack_timer = threading.Timer(0.0, attack_tick)
    attack_timer.start()

def handle_presumed_death():
    """
    unique engage edildikten sonra get_monsters() listesinden kayboldu ve
    kÄ±sa grace period iÃ§inde geri gelmedi â†’ muhtemelen Ã¶ldÃ¼ (chat/packet
    death event'i yakalayamamÄ±ÅŸ olabilir). Normal Ã¶lÃ¼m akÄ±ÅŸÄ±yla aynÄ± ÅŸekilde
    loot bekle + ÅŸehre dÃ¶n.
    """
    global current_active_unique, bot_state, unique_not_found_count
    try:
        name = current_active_unique
        if not name: return
        stop_attack_loop()
        stop_coordinate_hunt()
        with _state_lock:
            if name in unique_queue:
                unique_queue.remove(name)
            if name in alive_uniques:
                alive_uniques[name]['alive'] = False
                alive_uniques[name]['handled'] = False
        update_queue_label()
        current_active_unique = None
        unique_not_found_count = 0
        update_active_unique_label()
        bot_state = 'RETURNING'
        loot_wait_sec = get_loot_wait_seconds()
        if loot_wait_sec > 0:
            log(f"Waiting loot {loot_wait_sec}s...")
            wait_for_loot_async(loot_wait_sec)
        else:
            finish_hunt_and_return()
    except Exception as e:
        log(f"handle_presumed_death error: {e}")
        bot_state = 'IDLE'

def stop_attack_loop():
    global attack_timer
    if attack_timer:
        attack_timer.cancel()
        attack_timer = None

def handle_unique_timeout():
    global current_active_unique, unique_not_found_count, bot_state, just_returned
    try:
        timeout_unique = current_active_unique
        append_activity_once('timeout:%s' % timeout_unique,
                             'Hunt timeout: %s' % (timeout_unique or 'Unknown'))
        log(f"Timeout: {timeout_unique}")
        stop_attack_loop()
        stop_coordinate_hunt()
        try: stop_script()
        except: pass
        try: stop_bot()
        except: pass
        with _state_lock:
            if timeout_unique in alive_uniques:
                alive_uniques[timeout_unique]['alive'] = False
                alive_uniques[timeout_unique]['handled'] = False
            if timeout_unique in unique_queue:
                unique_queue.remove(timeout_unique)
                update_queue_label()
        current_active_unique = None
        unique_not_found_count = 0
        update_active_unique_label()
        bot_state = 'RETURNING'
        just_returned = False  # A new return-to-town flow is starting.
        phBot.use_return_scroll()
        log("Returning to town (Timeout)...")
        threading.Timer(1.0, lambda: _wait_for_town(_stop_after_return, label="Timeout")).start()
    except Exception as e:
        log(f"handle_unique_timeout error: {e}")

# ================= GUI =================
def fixed_width_text(content, width):
    return (
        '<table width="{0}" cellspacing="0" cellpadding="0">'
        '<tr><td>{1}</td></tr></table>'
    ).format(width, content)


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        QtBind.setText(
            gui, lbl_plugin_status,
            fixed_width_text(
                '<font color="%s"><b>%s</b></font>' % (COLOR_WARNING, tr('opening_discord')),
                300
            )
        )
    except Exception as error:
        log('[%s] Discord link error: %s' % (pName, error))
        QtBind.setText(
            gui, lbl_plugin_status,
            fixed_width_text(
                '<font color="%s"><b>%s</b></font>' % (COLOR_ERROR, tr('discord_error')),
                300
            )
        )


OFFSCREEN_X = 3000
dashboard_widgets = []
manager_widgets = []
coordinate_editor_widgets = []
hunt_settings_widgets = []
logs_widgets = []
screen_widgets = []
localized_widgets = []


def _localized(widget, key, style='plain'):
    localized_widgets.append((widget, key, style))
    return widget


def _localized_text(key, style):
    text = tr(key)
    if style == 'heading':
        return '<font color="%s"><b>%s</b></font>' % (COLOR_PRIMARY, text)
    if style == 'bold':
        return '<b>%s</b>' % text
    if style == 'muted':
        return '<font color="%s">%s</font>' % (COLOR_MUTED, text)
    return text


FILTER_KEYS = ('all', 'ready_filter', 'needs_setup_filter', 'script_filter', 'coordinate_filter')
FILTER_TEXT = {
    'en': {'all': 'All', 'ready_filter': 'Ready', 'needs_setup_filter': 'Needs Setup',
           'script_filter': 'Script Route', 'coordinate_filter': 'Coordinate Route'},
    'tr': {'all': 'Tümü', 'ready_filter': 'Hazır', 'needs_setup_filter': 'Ayar Gerekli',
           'script_filter': 'Script Rotası', 'coordinate_filter': 'Koordinat Rotası'},
}


def _selected_filter_key():
    selected = QtBind.text(gui, cmb_unique_filter).strip()
    for language_table in FILTER_TEXT.values():
        for key, value in language_table.items():
            if value == selected:
                return key
    return 'all'


def refresh_unique_filter_options(selected_key=None):
    if selected_key is None:
        selected_key = _selected_filter_key()
    QtBind.clear(gui, cmb_unique_filter)
    for key in FILTER_KEYS:
        QtBind.append(gui, cmb_unique_filter, FILTER_TEXT[UI_LANGUAGE][key])
    QtBind.setText(gui, cmb_unique_filter, FILTER_TEXT[UI_LANGUAGE].get(selected_key, FILTER_TEXT[UI_LANGUAGE]['all']))


def refresh_reverse_location_options():
    selected = QtBind.text(gui, cmb_reverse_location).strip()
    if selected not in REVERSE_LOCATIONS:
        selected = ''
    QtBind.clear(gui, cmb_reverse_location)
    QtBind.append(gui, cmb_reverse_location, tr('reverse_placeholder'))
    for location in REVERSE_LOCATIONS:
        QtBind.append(gui, cmb_reverse_location, location)
    QtBind.setText(gui, cmb_reverse_location, selected or tr('reverse_placeholder'))


def apply_language():
    try:
        selected_filter = _selected_filter_key()
        for widget, key, style in localized_widgets:
            QtBind.setText(gui, widget, _localized_text(key, style))
        QtBind.setText(gui, cmb_language, u'T\u00fcrk\u00e7e' if UI_LANGUAGE == 'tr' else 'English')
        refresh_unique_filter_options(selected_filter)
        refresh_reverse_location_options()
        refresh_unique_browser()
        refresh_selected_unique_details()
        refresh_coordinate_list()
        unique_name = _selected_unique()
        set_manager_status(('Selected %s.' % unique_name) if unique_name
                           else tr('select_unique_configure'), COLOR_MUTED)
        if unique_name:
            set_coordinate_editor_status('Editing saved points for %s.' % unique_name, COLOR_MUTED)
        else:
            set_coordinate_editor_status(tr('editor_ready'), COLOR_MUTED)
        update_plugin_status()
        update_queue_label()
        refresh_runtime_dashboard(True)
        refresh_configuration_health()
        append_activity('Language changed to %s' % (u'T\u00fcrk\u00e7e' if UI_LANGUAGE == 'tr' else 'English'))
    except Exception as error:
        log('[Language] Could not apply GUI language: %s' % error)


def apply_language_clicked():
    global UI_LANGUAGE
    UI_LANGUAGE = 'tr' if QtBind.text(gui, cmb_language).strip() == u'T\u00fcrk\u00e7e' else 'en'
    save_config()
    apply_language()


def _screen_widget(widget, dashboard_position=None, manager_position=None,
                   editor_position=None, settings_position=None, logs_position=None):
    screen_widgets.append(widget)
    if dashboard_position:
        dashboard_widgets.append((widget, dashboard_position[0], dashboard_position[1]))
    if manager_position:
        manager_widgets.append((widget, manager_position[0], manager_position[1]))
    if editor_position:
        coordinate_editor_widgets.append((widget, editor_position[0], editor_position[1]))
    if settings_position:
        hunt_settings_widgets.append((widget, settings_position[0], settings_position[1]))
    if logs_position:
        logs_widgets.append((widget, logs_position[0], logs_position[1]))
    return widget


def _show_screen(visible_widgets):
    for widget in screen_widgets:
        QtBind.move(gui, widget, OFFSCREEN_X, 0)
    for widget, x, y in visible_widgets:
        QtBind.move(gui, widget, x, y)


def _all_unique_names():
    return sorted(set(COMMON_UNIQUES) | set(discovered_uniques) |
                  set(unique_script_map) | set(unique_coordinate_map) |
                  set(unique_reverse_settings))


def _unique_status(unique_name):
    if not has_hunt_route(unique_name):
        return 'NO ROUTE'
    mode = get_route_mode(unique_name)
    if mode == 'coordinates':
        return 'COORD'
    if mode == 'script':
        return 'SCRIPT'
    return 'NO ROUTE'


def refresh_unique_browser():
    global unique_browser_items
    try:
        if unique_browser_list is None: return
        query = QtBind.text(gui, txt_unique_search).strip().lower()
        selected_filter = _selected_filter_key()
        unique_browser_items = []
        QtBind.clear(gui, unique_browser_list)
        for unique_name in _all_unique_names():
            status = _unique_status(unique_name)
            if query and query not in unique_name.lower():
                continue
            if selected_filter == 'ready_filter' and status == 'NO ROUTE':
                continue
            if selected_filter == 'needs_setup_filter' and status != 'NO ROUTE':
                continue
            if selected_filter == 'script_filter' and status != 'SCRIPT':
                continue
            if selected_filter == 'coordinate_filter' and status != 'COORD':
                continue
            unique_browser_items.append(unique_name)
            status_text = {'NO ROUTE': tr('no_route'), 'SCRIPT': tr('script_route'),
                           'COORD': tr('coordinate_route')}.get(status, status)
            QtBind.append(gui, unique_browser_list, '%s    [%s]' % (unique_name, status_text))
        if not unique_browser_items:
            QtBind.append(gui, unique_browser_list, tr('no_matches'))
    except Exception as error:
        if debug_enabled: log('refresh_unique_browser error: %s' % error)


def apply_unique_filter():
    refresh_unique_browser()


def select_unique_from_browser():
    global selected_unique_name
    try:
        index = QtBind.currentIndex(gui, unique_browser_list)
        if index < 0 or index >= len(unique_browser_items):
            set_manager_status('Select a unique from the list first.', COLOR_WARNING)
            return
        selected_unique_name = unique_browser_items[index]
        refresh_selected_unique_details()
        refresh_coordinate_list()
        set_manager_status('Selected %s' % selected_unique_name, COLOR_SUCCESS)
    except Exception as error:
        set_manager_status('Could not select the unique.', COLOR_ERROR)
        if debug_enabled: log('select_unique_from_browser error: %s' % error)


def set_manager_status(message, color=COLOR_MUTED):
    try:
        message = translate_ui_message(message)
        QtBind.setText(gui, lbl_manager_status, fixed_width_text(
            '<font color="%s">%s</font>' % (color, message), 360))
    except: pass


def set_coordinate_editor_status(message, color=COLOR_MUTED):
    try:
        message = translate_ui_message(message)
        QtBind.setText(gui, lbl_coordinate_editor_status, fixed_width_text(
            '<font color="%s">%s</font>' % (color, message), 696))
    except: pass


def refresh_selected_unique_details():
    try:
        unique_name = _selected_unique()
        if not unique_name:
            name, status, route, priority, script = tr('no_unique_selected'), tr('no_route'), tr('none'), '-', tr('no_script')
        else:
            marker = _unique_status(unique_name)
            status = tr('no_route') if marker == 'NO ROUTE' else tr('ready')
            route = {'SCRIPT': tr('script_route'), 'COORD': tr('coordinate_route')}.get(marker, tr('none'))
            name = unique_name
            priority = str(get_unique_priority(unique_name))
            script = unique_script_map.get(unique_name, tr('no_script'))
        QtBind.setText(gui, lbl_selected_unique, fixed_width_text(
            '<font color="%s"><b>%s</b></font>' % (COLOR_TEXT, name), 360))
        QtBind.setText(gui, lbl_detail_status, fixed_width_text(status, 100))
        QtBind.setText(gui, lbl_detail_route, fixed_width_text(route, 100))
        QtBind.setText(gui, lbl_detail_priority, fixed_width_text(priority, 15))
        QtBind.setText(gui, lbl_assigned_script, fixed_width_text(
            '<font color="%s">%s</font>' % (COLOR_TEXT, script), 260))
        reverse_setting = unique_reverse_settings.get(unique_name, {}) if unique_name else {}
        QtBind.setChecked(gui, chk_first_reverse,
                          bool(reverse_setting.get('enabled', False)))
        reverse_location = reverse_setting.get('location', '')
        QtBind.setText(gui, cmb_reverse_location,
                       reverse_location if reverse_location in REVERSE_LOCATIONS
                       else tr('reverse_placeholder'))
        refresh_coordinate_list()
    except Exception as error:
        if debug_enabled: log('refresh_selected_unique_details error: %s' % error)


def remove_script_mapping():
    unique_name = _selected_unique()
    if not unique_name or unique_name not in unique_script_map:
        set_manager_status('No script mapping to remove.', COLOR_WARNING)
        return
    del unique_script_map[unique_name]
    if unique_coordinate_map.get(unique_name):
        unique_route_modes[unique_name] = 'coordinates'
    else:
        unique_route_modes.pop(unique_name, None)
    save_config()
    refresh_mapping_list()
    refresh_pending_list()
    set_manager_status('Script mapping removed.', COLOR_SUCCESS)


def refresh_configuration_health():
    try:
        names = _all_unique_names()
        script_count = sum(1 for name in names if _unique_status(name) == 'SCRIPT')
        coord_count = sum(1 for name in names if _unique_status(name) == 'COORD')
        ready_count = sum(1 for name in names if _unique_status(name) != 'NO ROUTE')
        needs_count = len(names) - ready_count
        labels = ('Toplam', 'Hazir', 'Script', 'Koord', 'Ayar Gerekli') if UI_LANGUAGE == 'tr' else (
            'Total', 'Ready', 'Script', 'Coord', 'Needs Setup')
        summary = ('<b>%s:</b> %d  |  <b>%s:</b> %d  |  '
                   '<b>%s:</b> %d  |  <b>%s:</b> %d  |  '
                   '<b>%s:</b> %d') % (
                       labels[0], len(names), labels[1], ready_count,
                       labels[2], script_count, labels[3], coord_count, labels[4], needs_count)
        QtBind.setText(gui, lbl_config_summary, fixed_width_text(summary, 696))
    except: pass


def _current_action_text():
    if bot_state == 'RETURNING': return tr('returning_town')
    if bot_state == 'HUNTING':
        if reverse_hunt_pending: return tr('waiting_reverse')
        if coordinate_hunt: return tr('searching_points')
        return tr('running_route')
    return tr('waiting_unique') if plugin_active else tr('monitoring_disabled')


def refresh_runtime_dashboard(force=False):
    global _last_dashboard_snapshot
    try:
        route = 'None'
        if current_active_unique:
            route = tr('coordinates') if get_route_mode(current_active_unique) == 'coordinates' else 'Script'
        else:
            route = tr('none')
        action = _current_action_text()
        snapshot = (bot_state, current_active_unique, route, action)
        if not force and snapshot == _last_dashboard_snapshot:
            return
        _last_dashboard_snapshot = snapshot
        state_color = COLOR_SUCCESS if bot_state == 'HUNTING' else (
            COLOR_WARNING if bot_state == 'RETURNING' else COLOR_MUTED)
        state_text = {'IDLE': tr('idle'), 'HUNTING': tr('hunting'),
                      'RETURNING': tr('returning')}.get(bot_state, bot_state)
        QtBind.setText(gui, lbl_bot_state, fixed_width_text(
            '<font color="%s"><b>%s</b></font>' % (state_color, state_text), 180))
        QtBind.setText(gui, lbl_active_route, fixed_width_text(route, 180))
        QtBind.setText(gui, lbl_current_action, fixed_width_text(action, 250))
        if _last_activity_state['bot'] != bot_state:
            _last_activity_state['bot'] = bot_state
            append_activity('Bot state: %s' % bot_state)
        if _last_activity_state['action'] != action:
            _last_activity_state['action'] = action
            if bot_state == 'HUNTING' and current_active_unique:
                if coordinate_hunt:
                    append_activity_once('coordinate-start:%s' % current_active_unique,
                                         'Coordinate search started: %s' % current_active_unique)
                else:
                    append_activity_once('route-start:%s' % current_active_unique,
                                         'Hunt route started: %s' % current_active_unique)
    except: pass


def append_activity(message):
    try:
        entry = '%s  %s' % (time.strftime('%H:%M:%S'), message)
        activity_entries.append(entry)
        if len(activity_entries) > ACTIVITY_LIMIT:
            del activity_entries[0]
        if activity_list is not None:
            QtBind.clear(gui, activity_list)
            for item in activity_entries:
                timestamp, separator, raw_message = item.partition('  ')
                translated = translate_ui_message(raw_message) if separator else translate_ui_message(item)
                QtBind.append(gui, activity_list,
                              '%s  %s' % (timestamp, translated) if separator else translated)
    except: pass


def append_activity_once(key, message, cooldown=2.0):
    now = time.time()
    if now - _recent_activity_events.get(key, 0.0) < cooldown:
        return
    _recent_activity_events[key] = now
    append_activity(message)


def clear_activity_log():
    del activity_entries[:]
    try: QtBind.clear(gui, activity_list)
    except: pass


def show_dashboard():
    _show_screen(dashboard_widgets)
    update_plugin_status()
    update_active_unique_label()
    update_queue_label()
    refresh_runtime_dashboard(True)
    refresh_pending_list()
    refresh_configuration_health()


def show_unique_manager():
    _show_screen(manager_widgets)
    refresh_scripts()
    refresh_unique_browser()
    refresh_selected_unique_details()


def show_coordinate_editor():
    unique_name = _selected_unique()
    if not unique_name:
        set_manager_status('Select a unique before editing coordinates.', COLOR_WARNING)
        return
    _show_screen(coordinate_editor_widgets)
    QtBind.setText(gui, lbl_coordinate_editor_unique, fixed_width_text(
        '<font color="%s"><b>%s</b></font>' % (COLOR_TEXT, unique_name), 500))
    QtBind.setText(gui, txt_coord_region, '')
    QtBind.setText(gui, txt_coord_x, '')
    QtBind.setText(gui, txt_coord_y, '')
    QtBind.setText(gui, txt_coord_z, '0')
    refresh_coordinate_list()
    set_coordinate_editor_status('Editing saved points for %s.' % unique_name, COLOR_MUTED)


def back_to_unique_manager():
    show_unique_manager()
    unique_name = _selected_unique()
    if unique_name:
        set_manager_status('Selected %s.' % unique_name, COLOR_MUTED)


def show_hunt_settings():
    _show_screen(hunt_settings_widgets)


def show_logs():
    _show_screen(logs_widgets)


def show_settings():
    show_hunt_settings()


def show_monitor():
    show_dashboard()

def show_coordinates():
    show_unique_manager()


gui = QtBind.init(__name__, pName)

QtBind.createLabel(
    gui, u'<font color="%s" size="4"><b>\u2728 FAUTO UNIQUE V2</b></font>' % COLOR_PRIMARY,
    12, 6)
QtBind.createLabel(gui, '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion), 210, 12)
btn_discord = QtBind.createButton(gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(
    gui, u'<font color="%s"><b>\u269c Made By FascinaTe</b></font>' % COLOR_PRIMARY,
    565, 11)
QtBind.createLineEdit(gui, '', 12, 30, 696, 1)

# Four primary pages and the Coordinate Editor use QtBind.move/OFFSCREEN_X.
btn_nav_dashboard = _localized(QtBind.createButton(gui, 'show_dashboard', 'Dashboard', 12, 38), 'dashboard')
btn_nav_manager = _localized(QtBind.createButton(gui, 'show_unique_manager', 'Unique Manager', 110, 38), 'unique_manager')
btn_nav_settings = _localized(QtBind.createButton(gui, 'show_hunt_settings', 'Hunt Settings', 230, 38), 'hunt_settings')
btn_nav_logs = _localized(QtBind.createButton(gui, 'show_logs', 'Logs', 340, 38), 'logs')
lbl_language = _localized(QtBind.createLabel(gui, 'Language:', 430, 43), 'language')
cmb_language = QtBind.createCombobox(gui, 500, 38, 100, 22)
QtBind.append(gui, cmb_language, 'English')
QtBind.append(gui, cmb_language, u'T\u00fcrk\u00e7e')
btn_language = _localized(QtBind.createButton(gui, 'apply_language_clicked', 'Apply', 605, 38), 'apply_language')

# Legacy controls remain off-screen so old refresh helpers retain valid widget objects.
dropdown_unique = QtBind.createCombobox(gui, OFFSCREEN_X, 0, 1, 1)
mappings_list = QtBind.createList(gui, OFFSCREEN_X, 0, 1, 1)

# Dashboard
_screen_widget(_localized(QtBind.createLabel(gui, '<font color="%s"><b>LIVE HUNT STATUS</b></font>' % COLOR_PRIMARY,
                                  OFFSCREEN_X, 65), 'live_hunt_status', 'heading'), dashboard_position=(12, 65))
lbl_plugin_status = _screen_widget(QtBind.createLabel(gui, fixed_width_text(
    '<font color="%s"><b>DISABLED</b></font>' % COLOR_MUTED, 250), OFFSCREEN_X, 86),
    dashboard_position=(100, 86))
_screen_widget(_localized(QtBind.createLabel(gui, '<b>Plugin</b>', OFFSCREEN_X, 86), 'plugin', 'bold'), dashboard_position=(12, 86))
lbl_bot_state = _screen_widget(QtBind.createLabel(gui, fixed_width_text('IDLE', 180), OFFSCREEN_X, 107),
                               dashboard_position=(100, 107))
_screen_widget(_localized(QtBind.createLabel(gui, '<b>Bot state</b>', OFFSCREEN_X, 107), 'bot_state', 'bold'), dashboard_position=(12, 107))
lbl_active_unique = _screen_widget(QtBind.createLabel(gui, fixed_width_text('None', 250), OFFSCREEN_X, 128),
                                   dashboard_position=(100, 128))
_screen_widget(_localized(QtBind.createLabel(gui, '<b>Current target</b>', OFFSCREEN_X, 128), 'current_target', 'bold'), dashboard_position=(12, 128))
lbl_active_route = _screen_widget(QtBind.createLabel(gui, fixed_width_text('None', 180), OFFSCREEN_X, 149),
                                  dashboard_position=(100, 149))
_screen_widget(_localized(QtBind.createLabel(gui, '<b>Route</b>', OFFSCREEN_X, 149), 'route', 'bold'), dashboard_position=(12, 149))
lbl_current_action = _screen_widget(QtBind.createLabel(gui, fixed_width_text('Monitoring is disabled', 250),
                                                       OFFSCREEN_X, 170), dashboard_position=(100, 170))
_screen_widget(_localized(QtBind.createLabel(gui, '<b>Action</b>', OFFSCREEN_X, 170), 'action', 'bold'), dashboard_position=(12, 170))
lbl_queue = _screen_widget(QtBind.createLabel(gui, fixed_width_text('Queue is empty.', 300), OFFSCREEN_X, 191),
                           dashboard_position=(100, 191))
_screen_widget(_localized(QtBind.createLabel(gui, '<b>Queue</b>', OFFSCREEN_X, 191), 'queue', 'bold'), dashboard_position=(12, 191))
btn_plugin_enable = _screen_widget(_localized(QtBind.createButton(gui, 'enable_plugin_monitoring', 'Start Monitoring',
                                                       OFFSCREEN_X, 84), 'start_monitoring'), dashboard_position=(445, 84))
btn_plugin_disable = _screen_widget(_localized(QtBind.createButton(gui, 'disable_plugin_monitoring', 'Stop Monitoring',
                                                        OFFSCREEN_X, 84), 'stop_monitoring'), dashboard_position=(565, 84))
btn_stop = _screen_widget(_localized(QtBind.createButton(gui, 'stop_script_btn', 'Stop Current Hunt', OFFSCREEN_X, 112),
                          'stop_current_hunt'), dashboard_position=(565, 112))
_screen_widget(QtBind.createLineEdit(gui, '', OFFSCREEN_X, 210, 696, 1), dashboard_position=(12, 210))
_screen_widget(_localized(QtBind.createLabel(gui, '<font color="%s"><b>HUNT QUEUE</b></font>' % COLOR_PRIMARY,
                                  OFFSCREEN_X, 216), 'hunt_queue', 'heading'), dashboard_position=(12, 216))
queue_list = _screen_widget(QtBind.createList(gui, OFFSCREEN_X, 233, 350, 42), dashboard_position=(12, 233))
btn_start_next = _screen_widget(_localized(QtBind.createButton(gui, 'auto_start_next_unique', 'Hunt Next', OFFSCREEN_X, 277),
                                'hunt_next'), dashboard_position=(12, 277))
btn_remove_from_queue = _screen_widget(_localized(QtBind.createButton(gui, 'remove_from_queue_btn', 'Remove Selected',
                                                           OFFSCREEN_X, 277), 'remove_selected'), dashboard_position=(105, 277))
btn_clear_queue = _screen_widget(_localized(QtBind.createButton(gui, 'clear_queue_btn', 'Clear Queue', OFFSCREEN_X, 277),
                                 'clear_queue'), dashboard_position=(225, 277))
_screen_widget(_localized(QtBind.createLabel(gui, '<font color="%s"><b>NEEDS SETUP</b></font>' % COLOR_PRIMARY,
                                  OFFSCREEN_X, 216), 'needs_setup_heading', 'heading'), dashboard_position=(378, 216))
pending_list = _screen_widget(QtBind.createList(gui, OFFSCREEN_X, 233, 330, 42), dashboard_position=(378, 233))
btn_pending_assign = _screen_widget(_localized(QtBind.createButton(gui, 'show_unique_manager', 'Configure Uniques',
                                                        OFFSCREEN_X, 277), 'configure_uniques'), dashboard_position=(378, 277))
btn_delete_pending = _screen_widget(_localized(QtBind.createButton(gui, 'delete_pending', 'Remove Entry', OFFSCREEN_X, 277),
                                    'remove_entry'), dashboard_position=(500, 277))
lbl_config_summary = _screen_widget(QtBind.createLabel(gui, fixed_width_text(
    '<b>Total:</b> 0  |  <b>Ready:</b> 0  |  <b>Script:</b> 0  |  '
    '<b>Coord:</b> 0  |  <b>Needs Setup:</b> 0', 696), OFFSCREEN_X, 299),
    dashboard_position=(12, 299))

# Unique Manager: browser owns selection; detail controls own mapping and coordinate actions.
txt_unique_search = _screen_widget(QtBind.createLineEdit(gui, '', OFFSCREEN_X, 65, 145, 22),
                                   manager_position=(12, 65))
cmb_unique_filter = _screen_widget(QtBind.createCombobox(gui, OFFSCREEN_X, 65, 100, 22),
                                   manager_position=(162, 65))
refresh_unique_filter_options('all')
_screen_widget(_localized(QtBind.createButton(gui, 'apply_unique_filter', 'Apply', OFFSCREEN_X, 64), 'apply'),
               manager_position=(267, 64))
unique_browser_list = _screen_widget(QtBind.createList(gui, OFFSCREEN_X, 92, 300, 128),
                                     manager_position=(12, 92))
_screen_widget(_localized(QtBind.createButton(gui, 'select_unique_from_browser', 'Load Selected', OFFSCREEN_X, 223), 'load_selected'),
               manager_position=(12, 223))
btn_scan = _screen_widget(_localized(QtBind.createButton(gui, 'scan_nearby_uniques', 'Scan Nearby', OFFSCREEN_X, 223),
                          'scan_nearby'), manager_position=(112, 223))
_screen_widget(_localized(QtBind.createLabel(gui, 'Custom', OFFSCREEN_X, 257), 'custom'), manager_position=(12, 257))
txt_unique = _screen_widget(QtBind.createLineEdit(gui, '', OFFSCREEN_X, 252, 145, 22), manager_position=(62, 252))
btn_add_unique = _screen_widget(_localized(QtBind.createButton(gui, 'add_manual_unique', 'Add Unique', OFFSCREEN_X, 251),
                                'add_unique'), manager_position=(212, 251))
btn_add_queue = _screen_widget(_localized(QtBind.createButton(gui, 'add_to_queue_btn', 'Queue Selected', OFFSCREEN_X, 280),
                               'queue_selected'), manager_position=(12, 280))
btn_start = _screen_widget(_localized(QtBind.createButton(gui, 'start_script_btn', 'Hunt Selected', OFFSCREEN_X, 280),
                           'hunt_selected'), manager_position=(120, 280))
_screen_widget(QtBind.createLineEdit(gui, '', OFFSCREEN_X, 65, 1, 245), manager_position=(325, 65))
lbl_selected_unique = _screen_widget(QtBind.createLabel(gui, fixed_width_text('<b>None selected</b>', 360),
                                                        OFFSCREEN_X, 65), manager_position=(345, 65))
_screen_widget(_localized(QtBind.createLabel(gui, '<b>Status</b>', OFFSCREEN_X, 88), 'status', 'bold'), manager_position=(345, 88))
lbl_detail_status = _screen_widget(QtBind.createLabel(gui, fixed_width_text('Needs Setup', 100), OFFSCREEN_X, 88),
                                   manager_position=(395, 88))
_screen_widget(_localized(QtBind.createLabel(gui, '<b>Route</b>', OFFSCREEN_X, 88), 'route', 'bold'), manager_position=(500, 88))
lbl_detail_route = _screen_widget(QtBind.createLabel(gui, fixed_width_text('None', 100), OFFSCREEN_X, 88),
                                  manager_position=(540, 88))
_screen_widget(_localized(QtBind.createLabel(gui, '<b>Priority</b>', OFFSCREEN_X, 88), 'priority', 'bold'), manager_position=(640, 88))
lbl_detail_priority = _screen_widget(QtBind.createLabel(gui, fixed_width_text('-', 15), OFFSCREEN_X, 88),
                                     manager_position=(690, 88))
_screen_widget(_localized(QtBind.createLabel(gui, '<font color="%s"><b>SCRIPT ROUTE</b></font>' % COLOR_PRIMARY,
                                  OFFSCREEN_X, 110), 'script_route_heading', 'heading'), manager_position=(345, 110))
lbl_assigned_script = _screen_widget(QtBind.createLabel(gui, fixed_width_text('No script assigned.', 260),
                                                        OFFSCREEN_X, 110), manager_position=(445, 110))
dropdown_script = _screen_widget(QtBind.createCombobox(gui, OFFSCREEN_X, 128, 220, 22), manager_position=(345, 128))
btn_refresh = _screen_widget(_localized(QtBind.createButton(gui, 'refresh_scripts', 'Refresh', OFFSCREEN_X, 127),
                             'refresh'), manager_position=(570, 127))
btn_set = _screen_widget(_localized(QtBind.createButton(gui, 'set_script', 'Assign Script', OFFSCREEN_X, 153),
                         'assign_script'), manager_position=(345, 153))
btn_use_script = _screen_widget(_localized(QtBind.createButton(gui, 'use_script_route', 'Use Script Route', OFFSCREEN_X, 153),
                                'use_script_route'), manager_position=(445, 153))
btn_remove_script = _screen_widget(_localized(QtBind.createButton(gui, 'remove_script_mapping', 'Remove Script', OFFSCREEN_X, 153),
                                   'remove_script'), manager_position=(565, 153))
_screen_widget(_localized(QtBind.createLabel(gui, '<font color="%s"><b>COORDINATE ROUTE</b></font>' % COLOR_PRIMARY,
                                  OFFSCREEN_X, 180), 'coordinate_route_heading', 'heading'), manager_position=(345, 180))
lbl_coordinate_count = _screen_widget(QtBind.createLabel(gui, fixed_width_text(
    '<font color="%s">No saved points</font>' % COLOR_TEXT, 180), OFFSCREEN_X, 200),
    manager_position=(345, 200))
btn_edit_coordinates = _screen_widget(_localized(QtBind.createButton(gui, 'show_coordinate_editor', 'Edit Coordinates',
                                                           OFFSCREEN_X, 195), 'edit_coordinates'), manager_position=(530, 195))
btn_use_coordinates = _screen_widget(_localized(QtBind.createButton(gui, 'use_coordinate_route', 'Use Coord',
                                                         OFFSCREEN_X, 195), 'use_coord'), manager_position=(640, 195))
chk_first_reverse = _screen_widget(_localized(QtBind.createCheckBox(gui, 'toggle_unique_reverse', 'First use Reverse',
                                                         OFFSCREEN_X, 226), 'first_reverse'), manager_position=(345, 226))
QtBind.setChecked(gui, chk_first_reverse, False)
cmb_reverse_location = _screen_widget(QtBind.createCombobox(gui, OFFSCREEN_X, 247, 260, 22),
                                      manager_position=(345, 247))
refresh_reverse_location_options()
btn_save_reverse = _screen_widget(_localized(QtBind.createButton(gui, 'save_unique_reverse_setting', 'Save Reverse',
                                                       OFFSCREEN_X, 246), 'save_reverse'), manager_position=(610, 246))
lbl_manager_status = _screen_widget(QtBind.createLabel(gui, fixed_width_text(
    '<font color="%s">Select a unique to configure.</font>' % COLOR_MUTED, 360), OFFSCREEN_X, 278),
    manager_position=(345, 278))

# Coordinate Editor: dedicated point-list and capture/manual-editing page.
_screen_widget(_localized(QtBind.createLabel(gui, '<font color="%s"><b>COORDINATE EDITOR</b></font>' % COLOR_PRIMARY,
                                  OFFSCREEN_X, 65), 'coordinate_editor', 'heading'), editor_position=(12, 65))
_screen_widget(_localized(QtBind.createButton(gui, 'back_to_unique_manager', u'\u2190 Back', OFFSCREEN_X, 64),
               'back'), editor_position=(650, 64))
lbl_coordinate_editor_unique = _screen_widget(QtBind.createLabel(gui, fixed_width_text(
    '<font color="%s"><b>No unique selected</b></font>' % COLOR_TEXT, 500), OFFSCREEN_X, 87),
    editor_position=(12, 87))
_screen_widget(_localized(QtBind.createLabel(gui, '<font color="%s"><b>SAVED COORDINATE ROUTE</b></font>' % COLOR_PRIMARY,
                                  OFFSCREEN_X, 108), 'saved_coordinate_route', 'heading'), editor_position=(12, 108))
coordinate_list = _screen_widget(QtBind.createList(gui, OFFSCREEN_X, 124, 696, 82),
                                 editor_position=(12, 124))
btn_remove_coordinate = _screen_widget(_localized(QtBind.createButton(gui, 'remove_coordinate', 'Remove Selected',
                                                            OFFSCREEN_X, 211), 'remove_selected'), editor_position=(12, 211))
btn_add_current = _screen_widget(_localized(QtBind.createButton(gui, 'add_my_current_position', 'Capture Current',
                                                      OFFSCREEN_X, 211), 'capture_current'), editor_position=(150, 211))
btn_add_nearby = _screen_widget(_localized(QtBind.createButton(gui, 'add_nearby_unique_position', 'Capture Nearby',
                                                     OFFSCREEN_X, 211), 'capture_nearby'), editor_position=(270, 211))
_screen_widget(_localized(QtBind.createLabel(gui, '<font color="%s"><b>MANUAL COORDINATE</b></font>' % COLOR_PRIMARY,
                                  OFFSCREEN_X, 236), 'manual_coordinate', 'heading'), editor_position=(12, 236))
for text_value, x in (('R', 12), ('X', 120), ('Y', 285), ('Z', 450)):
    _screen_widget(QtBind.createLabel(gui, text_value, OFFSCREEN_X, 258), editor_position=(x, 258))
txt_coord_region = _screen_widget(QtBind.createLineEdit(gui, '', OFFSCREEN_X, 254, 75, 22),
                                  editor_position=(30, 254))
txt_coord_x = _screen_widget(QtBind.createLineEdit(gui, '', OFFSCREEN_X, 254, 130, 22),
                             editor_position=(138, 254))
txt_coord_y = _screen_widget(QtBind.createLineEdit(gui, '', OFFSCREEN_X, 254, 130, 22),
                             editor_position=(303, 254))
txt_coord_z = _screen_widget(QtBind.createLineEdit(gui, '0', OFFSCREEN_X, 254, 100, 22),
                             editor_position=(468, 254))
btn_add_coordinate = _screen_widget(_localized(QtBind.createButton(gui, 'add_coordinate_fields', 'Add', OFFSCREEN_X, 253),
                                    'add'), editor_position=(580, 253))
lbl_coordinate_editor_status = _screen_widget(QtBind.createLabel(gui, fixed_width_text(
    '<font color="%s">Ready.</font>' % COLOR_MUTED, 696), OFFSCREEN_X, 283),
    editor_position=(12, 283))

# Hunt Settings
_screen_widget(_localized(QtBind.createLabel(gui, '<font color="%s"><b>LOOT BEHAVIOR</b></font>' % COLOR_PRIMARY,
                                  OFFSCREEN_X, 65), 'loot_behavior', 'heading'), settings_position=(12, 65))
cbx_loot_wait = _screen_widget(_localized(QtBind.createCheckBox(gui, 'do_nothing', 'Wait after unique death', OFFSCREEN_X, 86),
                               'wait_after_death'), settings_position=(12, 86))
QtBind.setChecked(gui, cbx_loot_wait, True)
tbx_loot_wait = _screen_widget(QtBind.createLineEdit(gui, '60', OFFSCREEN_X, 82, 55, 22), settings_position=(190, 82))
_screen_widget(_localized(QtBind.createLabel(gui, 'seconds', OFFSCREEN_X, 87), 'seconds'), settings_position=(250, 87))
_screen_widget(QtBind.createLineEdit(gui, '', OFFSCREEN_X, 110, 696, 1), settings_position=(12, 110))
_screen_widget(_localized(QtBind.createLabel(gui, '<font color="%s"><b>HUNT TIMEOUT</b></font>' % COLOR_PRIMARY,
                                  OFFSCREEN_X, 119), 'hunt_timeout', 'heading'), settings_position=(12, 119))
cbx_unique_timeout = _screen_widget(_localized(QtBind.createCheckBox(gui, 'do_nothing', 'Enable hunt timeout', OFFSCREEN_X, 140),
                                    'enable_hunt_timeout'), settings_position=(12, 140))
QtBind.setChecked(gui, cbx_unique_timeout, True)
tbx_unique_timeout = _screen_widget(QtBind.createCombobox(gui, OFFSCREEN_X, 136, 90, 22), settings_position=(190, 136))
for timeout_value in ('10min', '20min', '30min'): QtBind.append(gui, tbx_unique_timeout, timeout_value)
_screen_widget(QtBind.createLineEdit(gui, '', OFFSCREEN_X, 164, 696, 1), settings_position=(12, 164))
_screen_widget(_localized(QtBind.createLabel(gui, '<font color="%s"><b>AUTOMATION</b></font>' % COLOR_PRIMARY,
                                  OFFSCREEN_X, 173), 'automation', 'heading'), settings_position=(12, 173))
chk_auto_return = _screen_widget(_localized(QtBind.createCheckBox(gui, 'toggle_auto_return',
    'Return to town for an unconfigured unique', OFFSCREEN_X, 194), 'auto_return'), settings_position=(12, 194))
QtBind.setChecked(gui, chk_auto_return, False)
chk_auto_learn = _screen_widget(_localized(QtBind.createCheckBox(gui, 'toggle_auto_learn',
    'Automatically learn unique coordinates', OFFSCREEN_X, 218), 'auto_learn'), settings_position=(12, 218))
QtBind.setChecked(gui, chk_auto_learn, False)
_screen_widget(_localized(QtBind.createLabel(gui, '<font color="%s">Points within 30m of a saved point are ignored.</font>' % COLOR_MUTED,
                                  OFFSCREEN_X, 240), 'duplicate_help', 'muted'), settings_position=(32, 240))
_screen_widget(QtBind.createLineEdit(gui, '', OFFSCREEN_X, 258, 696, 1), settings_position=(12, 258))
_screen_widget(_localized(QtBind.createLabel(gui, '<font color="%s"><b>DIAGNOSTICS</b></font>' % COLOR_PRIMARY,
                                  OFFSCREEN_X, 267), 'diagnostics', 'heading'), settings_position=(12, 267))
chk_debug = _screen_widget(_localized(QtBind.createCheckBox(gui, 'toggle_debug', 'Detailed debug logging', OFFSCREEN_X, 290),
                           'debug_logging'), settings_position=(12, 290))
btn_force_scan = _screen_widget(_localized(QtBind.createButton(gui, 'force_scan_alive_uniques', 'Refresh Nearby Alive Status',
                                                    OFFSCREEN_X, 286), 'refresh_alive'), settings_position=(210, 286))
btn_check_alive = _screen_widget(_localized(QtBind.createButton(gui, 'check_alive_uniques', 'Log Tracked Uniques', OFFSCREEN_X, 286),
                                 'log_tracked'), settings_position=(375, 286))

# Logs
_screen_widget(_localized(QtBind.createLabel(gui, '<font color="%s"><b>RECENT PLUGIN ACTIVITY</b></font>' % COLOR_PRIMARY,
                                  OFFSCREEN_X, 65), 'recent_activity', 'heading'), logs_position=(12, 65))
_screen_widget(_localized(QtBind.createLabel(gui, '<font color="%s">Shows the latest 100 important GUI-visible state changes.</font>' % COLOR_MUTED,
                                  OFFSCREEN_X, 84), 'activity_help', 'muted'), logs_position=(12, 84))
activity_list = _screen_widget(QtBind.createList(gui, OFFSCREEN_X, 102, 696, 176), logs_position=(12, 102))
_screen_widget(_localized(QtBind.createButton(gui, 'clear_activity_log', 'Clear Activity', OFFSCREEN_X, 282),
               'clear_activity'), logs_position=(12, 282))

show_dashboard()

# ================= INITIALIZATION =================
try:
    if not os.path.exists(scripts_folder): os.makedirs(scripts_folder)
    path = getPath()
    if not os.path.exists(path): os.makedirs(path)
    discovered_uniques.update(COMMON_UNIQUES)
    refresh_unique_dropdown()
    refresh_scripts()
    _char = get_character_data()
    if _char and _char.get('name') and _char.get('server'):
        load_config()
        log(f"{pName} v{pVersion} loaded (config loaded for {_char['name']}).")
    else:
        log(f"{pName} v{pVersion} loaded.")
except Exception as e:
    log(f"Init error: {e}")

def joined_game():
    """Called automatically after the character enters the game."""
    try:
        learned_unique_ids.clear()
        # joined_game aninda character data henuz hazir olmayabilir. Config dosya
        # adi server+character'a bagli oldugu icin yuklemeyi kisa sure ertele.
        log(f"[{pName}] Character joined - config load scheduled...")
        threading.Timer(2.0, _load_config_after_join).start()
    except Exception as e:
        log(f"joined_game error: {e}")

def _load_config_after_join(attempt=0):
    """Character data hazir oldugunda config'i yukler; en fazla 10 saniye dener."""
    try:
        char = get_character_data()
        if not char or not char.get('name') or not char.get('server'):
            if attempt < 8:
                threading.Timer(1.0, _load_config_after_join, [attempt + 1]).start()
            else:
                log(f"[{pName}] Config yuklenemedi: character data hazir degil.")
            return
        load_config()
        refresh_scripts()
        if plugin_active:
            log(f"[{pName}] Plugin was ENABLED -> Checking location...")
            _check_location_on_join()
    except Exception as e:
        log(f"_load_config_after_join error: {e}")

def _check_location_on_join():
    """Return first when the character joins outside town."""
    if not plugin_active: return
    if not _is_in_town():
        _set_in_town(False)
        log(f"[{pName}] Not in town -> Using return scroll...")
        try: use_return_scroll()
        except: pass
        threading.Timer(1.0, lambda: _wait_for_town(_after_return_enable, label="Join")).start()
    else:
        _set_in_town(True)
        log(f"[{pName}] In town -> Ready and waiting for uniques...")

# ================= EVENTS =================
UNIQUE_OBJ_CACHE = {}

def bot_started():
    """
    Ignore bot-start notifications because run_mapped_script controls the bot.
    """
    pass

def _kill_unwanted_bot():
    pass

def teleported():
    """
    phBot bu event'i 'teleport_accepted' deÄŸil 'teleported' adÄ±yla tetikliyor
    (bkz. docs/phbot-api/events.md) â€” eski isim hiÃ§ Ã§aÄŸrÄ±lmÄ±yordu, bu yÃ¼zden
    teleport sonrasÄ± ÅŸehir state gÃ¼ncellemesi Ã§alÄ±ÅŸmÄ±yordu.
    """
    if reverse_hunt_pending and reverse_hunt_pending.get('phase') == 'waiting':
        reverse_hunt_pending['phase'] = 'settling'
        token = reverse_hunt_pending['token']
        if reverse_timeout_timer:
            reverse_timeout_timer.cancel()
        threading.Timer(1.5, _resume_coordinate_hunt_after_reverse, [token]).start()
    threading.Timer(1.5, _update_town_state_after_teleport).start()

def _update_town_state_after_teleport():
    """Refresh the region-based town state shortly after teleporting."""
    global town_return_pending
    arrived_in_town = _is_in_town()
    _set_in_town(arrived_in_town)
    if town_return_pending and arrived_in_town and plugin_active:
        town_return_pending = False
        log('[Return] Town reached after the earlier return timeout; resuming queue.')
        _stop_after_return()

def event_loop():
    """Learn one spawn point per visible unique instance when enabled."""
    # Keep GUI-only runtime labels synchronized without changing hunt state.
    refresh_runtime_dashboard()
    if not auto_learn_coordinates:
        return
    try:
        monsters = phBot.get_monsters() or {}
        for monster_id, monster in monsters.items():
            if monster_id in learned_unique_ids:
                continue
            name = (monster.get('name') or '').strip()
            if not name or not is_unique(name):
                continue
            mapped_name = _find_mapped_name(name)
            learned_unique_ids.add(monster_id)
            point = {
                'region': monster.get('region', 0), 'x': monster.get('x', 0),
                'y': monster.get('y', 0), 'z': monster.get('z', 0),
            }
            added, message = _add_coordinate(mapped_name, point, 'Learned')
            if added:
                log('[Coordinates] Automatically learned %s at R%d (%.0f, %.0f)' % (
                    mapped_name, int(point['region']), float(point['x']), float(point['y'])))
            elif debug_enabled:
                log('[Coordinates] %s learning skipped: %s' % (mapped_name, message))
    except Exception as error:
        if debug_enabled: log('[Coordinates] Auto-learning error: %s' % error)

def disconnected():
    global town_return_pending
    town_return_pending = False
    stop_attack_loop()
    stop_loot_timer()
    stop_coordinate_hunt()

# phBot'un native unique-spawn event'i (bkz. docs/phbot-api/events.md â†’ handle_event tÃ¼rleri).
# Chat metni parse etmekten ve ham paket (0x300C) sniff etmekten daha gÃ¼venilir â€” server'Ä±n
# chat mesaj formatÄ±/paket yapÄ±sÄ± farklÄ± olsa bile bu event doÄŸrudan monster adÄ±nÄ± veriyor.
EVENT_UNIQUE_SPAWN = 0

def handle_event(t, data):
    """EVENT_UNIQUE_SPAWN geldiÄŸinde data = unique canavarÄ±n adÄ± (string)."""
    try:
        if t != EVENT_UNIQUE_SPAWN or not data:
            return
        unique_name = str(data).strip()
        if not unique_name or not is_unique(unique_name):
            return

        is_new = False
        with _state_lock:
            if unique_name not in alive_uniques or not alive_uniques[unique_name]['alive']:
                alive_uniques[unique_name] = {
                    'spawn_time': time.time(), 'alive': True,
                    'handled': False, 'last_seen': time.time()
                }
                is_new = True
            if not has_hunt_route(unique_name):
                if unique_name not in pending_uniques:
                    pending_uniques.append(unique_name)
                    refresh_pending_list()
                    log(f"[Pending] {unique_name} has no script -> added to pending (Event).")
            else:
                is_active_target = bool(current_active_unique and current_active_unique.lower() == unique_name.lower())
                if not is_active_target and unique_name not in unique_queue:
                    unique_queue.append(unique_name)
                    sort_queue_by_priority()
                    update_queue_label()
                    log(f"[Auto-Saved] {unique_name} added to queue (Event).")

        if (plugin_active and current_active_unique and coordinate_hunt and
                current_active_unique.lower() == unique_name.lower()):
            _on_unique_spawn(unique_name)
            return
        if plugin_active and is_new:
            if debug_enabled:
                log(f"Event Spawn: {unique_name} (Executing)")
            _on_unique_spawn(unique_name)
        elif not plugin_active and is_new:
            if debug_enabled:
                log(f"Event Spawn: {unique_name} (Plugin Disabled - Saved Only)")
    except Exception as e:
        if debug_enabled: log(f"handle_event error: {e}")

def _handle_unique_death_notification(unique_name, source_tag):
    """
    Chat metni ya da 0xAA6B paketinden gelen 'unique Ã¶ldÃ¼' bilgisini tek yerden iÅŸler.
    Ham isim variant/farklÄ± case olabilir (Ã¶rn. 'Tiger girl' vs mapped 'Tiger Girl') â€”
    _find_mapped_name ile normalize edilip run_mapped_script'e mapped isim geÃ§iliyor,
    yoksa current_active_unique ile eÅŸleÅŸmeyip Ã¶lÃ¼m sinyali sessizce kaybolabiliyordu.
    """
    if not unique_name or not is_unique(unique_name):
        return
    mapped_name = _find_mapped_name(unique_name)
    append_activity_once('killed:%s' % mapped_name, 'Killed: %s' % mapped_name)
    if debug_enabled:
        log(f"{source_tag}: {unique_name} -> {mapped_name}")
    with _state_lock:
        if mapped_name in alive_uniques:
            alive_uniques[mapped_name]['alive'] = False
            alive_uniques[mapped_name]['handled'] = False
        if not plugin_active and mapped_name in unique_queue:
            unique_queue.remove(mapped_name)
    if plugin_active:
        run_mapped_script(mapped_name, 'death')
    else:
        update_queue_label()

def _parse_unique_kill_message(msg):
    """
    '[Killer] killed UniqueName from Region. (x/y)' formatÄ±nÄ± ayrÄ±ÅŸtÄ±rÄ±r â€” 0xAA6B
    paketinden gelen dÃ¼z metin bildirimi iÃ§in (bkz. docs/phbot-api/sro-opcodes.md,
    canlÄ± capture'dan doÄŸrulandÄ±). BaÅŸarÄ±sÄ±z olursa (None, None) dÃ¶ner.
    """
    try:
        if not msg.startswith('[') or ' killed ' not in msg or ' from ' not in msg:
            return None, None
        close = msg.index(']')
        killer = msg[1:close].strip()
        rest = msg[close + 1:].strip()
        if rest.startswith('killed '):
            rest = rest[len('killed '):]
        unique_part, _, _region_part = rest.partition(' from ')
        return killer.strip(), unique_part.strip()
    except Exception:
        return None, None

def handle_joymax(opcode, data):
    try:
        if opcode == 0xAA6B and data and len(data) >= 3:
            try:
                msg_len = struct.unpack_from("<H", data, 0)[0]
                raw = data[2:2 + msg_len]
            except Exception:
                raw = data[2:].split(b'\x03')[0]
            msg = raw.decode('ascii', errors='ignore')
            killer_name, unique_name = _parse_unique_kill_message(msg)
            if unique_name:
                _handle_unique_death_notification(unique_name, f"PACKET DEATH (0xAA6B, killer={killer_name})")

        elif opcode == 0x300C and data and len(data) >= 6:
            event_type = data[0]
            obj_id = struct.unpack_from("<I", data, 2)[0]

            name = None
            if obj_id in UNIQUE_OBJ_CACHE:
                name = UNIQUE_OBJ_CACHE[obj_id]
            else:
                mob = phBot.get_monster(obj_id)
                if mob: name = (mob.get("name") or "").strip()

            # --- SPAWN ---
            if event_type == 5 and name:
                UNIQUE_OBJ_CACHE[obj_id] = name
                if is_unique(name):
                    # Resolve variants such as Tiger Girl (INT) to the mapped base name.
                    mapped_name = _find_mapped_name(name)
                    is_new = False
                    with _state_lock:
                        if mapped_name not in alive_uniques or not alive_uniques[mapped_name]['alive']:
                            alive_uniques[mapped_name] = {
                                'spawn_time': time.time(), 'alive': True,
                                'handled': False, 'last_seen': time.time(), 'obj_id': obj_id
                            }
                            is_new = True
                        if not has_hunt_route(mapped_name):
                            if mapped_name not in pending_uniques:
                                pending_uniques.append(mapped_name)
                                refresh_pending_list()
                                log(f"[Pending] {name} has no script -> added to pending.")
                            # Unmapped uniques do not enter the hunt queue.
                        else:
                            if mapped_name not in unique_queue:
                                unique_queue.append(mapped_name)
                                sort_queue_by_priority()
                                update_queue_label()
                                log(f"[Auto-Saved] {name} -> using mapping [{mapped_name}] added to queue.")
                    if is_new:
                        if plugin_active:
                            if debug_enabled:
                                log(f"Packet Spawn: {name} -> mapped as [{mapped_name}] (Executing)")
                            _on_unique_spawn(mapped_name)
                        else:
                            if debug_enabled:
                                log(f"Packet Spawn: {name} (Plugin Disabled - Saved Only)")

            # --- DEATH ---
            elif event_type == 6 and name:
                _handle_unique_death_notification(name, "PACKET DEATH (0x300C)")
                UNIQUE_OBJ_CACHE.pop(obj_id, None)

        return True
    except: return True


def handle_chat(t, player, msg):
    if not msg: return
    try:
        msg_lower = msg.lower()

        # --- SPAWN ---
        # 'has spawned' bazÄ± serverlarda hiÃ§ kullanÄ±lmÄ±yor â€” bu server 'has appeared on <region>'
        # diyor (bkz. docs/phbot-api/sro-opcodes.md, canlÄ± doÄŸrulandÄ±). Ä°kisi de destekleniyor.
        if 'has spawned' in msg_lower or 'has appeared' in msg_lower:
            split_word = 'has spawned' if 'has spawned' in msg_lower else 'has appeared'
            unique_name = msg.split(split_word)[0].strip()
            if unique_name and is_unique(unique_name):
                is_new = False
                with _state_lock:
                    if unique_name not in alive_uniques or not alive_uniques[unique_name]['alive']:
                        alive_uniques[unique_name] = {
                            'spawn_time': time.time(), 'alive': True,
                            'handled': False, 'last_seen': time.time()
                        }
                        is_new = True
                    if not has_hunt_route(unique_name):
                        if unique_name not in pending_uniques:
                            pending_uniques.append(unique_name)
                            refresh_pending_list()
                            log(f"[Pending] {unique_name} has no script -> added to pending (Chat).")
                        # Unmapped uniques do not enter the hunt queue.
                    else:
                        if unique_name not in unique_queue:
                            unique_queue.append(unique_name)
                            sort_queue_by_priority()
                            update_queue_label()
                            log(f"[Auto-Saved] {unique_name} added to queue (Chat).")
                if plugin_active and is_new:
                    if debug_enabled:
                        log(f"Chat Spawn: {unique_name} (Executing)")
                    _on_unique_spawn(unique_name)

        # --- DEATH ---
        elif 'has been killed' in msg_lower or 'has died' in msg_lower:
            unique_name = msg.split('has been killed')[0].split('has died')[0].strip()
            _handle_unique_death_notification(unique_name, "CHAT DEATH")

        # Bu server 'has been killed'/'has died' demiyor â€” '[Killer] killed Unique from
        # Region. (x/y)' formatÄ±nÄ± kullanÄ±yor (bkz. sro-opcodes.md, canlÄ± doÄŸrulandÄ±).
        elif ' killed ' in msg and ' from ' in msg and msg.strip().startswith('['):
            killer_name, unique_name = _parse_unique_kill_message(msg.strip())
            if unique_name:
                _handle_unique_death_notification(unique_name, f"CHAT DEATH (killer={killer_name})")
    except: pass


log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)

