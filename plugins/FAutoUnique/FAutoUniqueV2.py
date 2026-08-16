import phBot
from phBot import *
import QtBind
import time
import os
import json
import struct
import threading
import sys
import webbrowser

# ================= INFO =================
pName = 'FAutoUnique V2'
pVersion = '2.2.2'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

COLOR_PRIMARY = '#5b57e0'
COLOR_TEXT = '#2b3038'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#e74c3c'
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
    """مجلد الـ config الخاص بالبلجن داخل get_config_dir()"""
    return get_config_dir() + CONFIG_FOLDER + "\\"

def getConfig():
    """مسار ملف الـ JSON الخاص بكل character"""
    char = get_character_data()
    if char and char.get('name') and char.get('server'):
        return getPath() + char['server'] + "_" + char['name'] + ".json"
    return None

# ================= DATA & STATE =================
unique_script_map = {}
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
# grind slotunun training area bilgisi — av bitince buraya geri donmek icin
# (get_training_area()'dan yakalanir: region,x,y,z,radius,path)
saved_slot = None

# lock بيحمي unique_queue / alive_uniques / pending_uniques من race conditions
# لأنهم بيتعدّلوا من أكتر من thread (network event thread + threading.Timer callbacks)
_state_lock = threading.RLock()

# لو الـ unique المستهدف اختفى من get_monsters() بعد ما بدأنا نضربه فعلاً (engaged)
# لمدة أطول من دي، نعتبره مات ونرجع للتاون بدل ما ننتظر الـ timeout الكامل
LOST_TARGET_GRACE_SEC = 8.0

# State Machine: IDLE, HUNTING, RETURNING
bot_state = 'IDLE'
force_stopped = False
just_returned = False  # flag: وصلنا التاون للتو → تجاوز الـ town check مرة واحدة
unique_not_found_count = 0
script_finished = False
_in_town_state = True  # tracking يدوي للـ town state — True = في التاون

# Town region'lari — hem _is_in_town hem capture_slot kullaniyor
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
# لو unique ظهر ومفيش له script والبوت IDLE → يرجع للتاون
auto_return_enabled = False

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

# ================= CONFIG & FILE HELPERS =================
def add_manual_unique():
    try:
        name = QtBind.text(gui, txt_unique).strip()
        if not name:
            log("Please type a unique name")
            return
        if name not in discovered_uniques:
            discovered_uniques.add(name)
            refresh_unique_dropdown()
            save_config()
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
    # substring yerine _is_unique_match (exact / "name " / "name(" prefix) kullanıyoruz
    # ki 'Spider', 'Monkey', 'Goon' gibi genel isimler sıradan moblarla yanlışlıkla eşleşmesin
    return any(_is_unique_match(u, name) for u in COMMON_UNIQUES)

def is_unique(name):
    if not name: return False
    if name in discovered_uniques: return True
    if name in unique_script_map: return True
    return is_known_unique(name)

def get_scripts():
    try:
        if not os.path.exists(scripts_folder):
            os.makedirs(scripts_folder)
        return [f for f in os.listdir(scripts_folder) if f.endswith('.txt')]
    except Exception as e:
        log(f"get_scripts error: {e}")
        return []

def save_config():
    """يحفظ كل الـ settings في JSON خاص بالـ character الحالي"""
    try:
        cfg = getConfig()
        if not cfg: return
        path = getPath()
        if not os.path.exists(path):
            os.makedirs(path)
        data = {
            'mappings': unique_script_map,
            'discovered_uniques': sorted(list(discovered_uniques)),
            'plugin_active': plugin_active,
            'auto_return_enabled': auto_return_enabled,
            'saved_slot': saved_slot,
        }
        with open(cfg, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"save_config error: {e}")

def load_config():
    """يحمل الـ settings من JSON الخاص بالـ character الحالي"""
    global unique_script_map, discovered_uniques, plugin_active, auto_return_enabled, saved_slot
    try:
        cfg = getConfig()
        if cfg and os.path.exists(cfg):
            with open(cfg, 'r', encoding='utf-8') as f:
                data = json.load(f)
            unique_script_map = data.get('mappings', {})
            saved_uniques = data.get('discovered_uniques', [])
            discovered_uniques = set(saved_uniques)
            auto_return_enabled = data.get('auto_return_enabled', False)
            saved_slot = data.get('saved_slot', None)
            try:
                QtBind.setChecked(gui, chk_auto_return, auto_return_enabled)
            except: pass
            was_active = data.get('plugin_active', False)
            if was_active:
                log("Plugin was ENABLED → Auto-resuming...")
                plugin_active = True
                try:
                    QtBind.setChecked(gui, chk_auto_return, auto_return_enabled)
                except: pass
            else:
                plugin_active = False
        # دايماً نضيف الـ COMMON_UNIQUES
        discovered_uniques.update(COMMON_UNIQUES)
        refresh_mapping_list()
        refresh_unique_dropdown()
        update_plugin_status()
    except Exception as e:
        log(f"load_config error: {e}")

# ================= GUI HELPERS =================
def refresh_unique_dropdown():
    try:
        QtBind.clear(gui, dropdown_unique)
        all_uniques = sorted(list(discovered_uniques) + [u for u in COMMON_UNIQUES if u not in discovered_uniques])
        for unique in all_uniques:
            QtBind.append(gui, dropdown_unique, unique)
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
        for unique, script in unique_script_map.items():
            QtBind.append(gui, mappings_list, f"{unique} --> {script}")
    except Exception as e:
        log(f"refresh_mapping_list error: {e}")

def refresh_pending_list():
    try:
        QtBind.clear(gui, pending_list)
        for unique in pending_uniques:
            QtBind.append(gui, pending_list, f"{unique} --> [No Script]")
    except Exception as e:
        log(f"refresh_pending_list error: {e}")

def set_script():
    try:
        unique = QtBind.text(gui, dropdown_unique)
        script = QtBind.text(gui, dropdown_script)
        if not unique or not script: return
        unique_script_map[unique] = script
        save_config()
        refresh_mapping_list()
        log(f"Mapped: {unique} -> {script}")
    except Exception as e:
        log(f"set_script error: {e}")

def delete_selected_mapping():
    try:
        selected = QtBind.text(gui, mappings_list)
        if not selected: return
        unique = selected.split(' --> ')[0].strip()
        if unique in unique_script_map:
            del unique_script_map[unique]
            save_config()
            refresh_mapping_list()
    except Exception as e:
        log(f"delete_selected_mapping error: {e}")

def delete_pending():
    try:
        selected = QtBind.text(gui, pending_list)
        if not selected: return
        unique = selected.split(' --> ')[0].strip()
        with _state_lock:
            if unique in pending_uniques:
                pending_uniques.remove(unique)
        refresh_pending_list()
    except Exception as e:
        log(f"delete_pending error: {e}")

# ================= AUTO RETURN LOGIC =================
def do_auto_return(unique_name):
    """
    يُستدعى لما unique ظهر ومفيش له script.
    لو الشخصية بره التاون → يرجع للتاون.
    لو في التاون أصلاً → ما يعملش حاجة.
    """
    if not auto_return_enabled: return
    if _is_in_town() or just_returned:
        log(f"[AutoReturn] {unique_name} has no script → Already in town, no action needed.")
        return
    log(f"[AutoReturn] {unique_name} has no script → Outside town! Returning...")
    _trigger_return_to_town()

def _wait_for_town(on_arrived, label="Return", max_attempts=30):
    """
    Generic: بيستنى لحد ما الشخصية توصل التاون فعلاً (polling كل ثانية) — max 30 محاولة.
    بيستبدل الـ 3 نسخ المكررة اللي كانت موجودة قبل كده.
    """
    def _check(attempts=0):
        # disable edilirse bekleyen town-varis zincirini durdur
        if not plugin_active:
            if debug_enabled: log(f"[{label}] Plugin disabled → town-wait iptal.")
            return
        if _is_in_town():
            on_arrived()
            return
        if attempts >= max_attempts:
            log(f"[{label}] Town arrival timeout — stopping anyway.")
            on_arrived()
            return
        threading.Timer(1.0, _check, [attempts + 1]).start()
    _check()

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
        selected = QtBind.text(gui, mappings_list)
        if selected:
            unique = selected.split(' --> ')[0].strip()
            script_name = unique_script_map.get(unique)
            if script_name:
                script_path = os.path.join(scripts_folder, script_name)
                if os.path.exists(script_path):
                    with open(script_path, 'r', encoding='utf-8') as f:
                        script_content = f.read()
                    script_content = script_content.replace('{unique}', unique).replace('{event}', 'manual')
                    phBot.start_script(script_content)
                    with _state_lock:
                        if unique in unique_queue:
                            unique_queue.remove(unique)
                    update_queue_label()
                    log(f"Manual Start: {unique}")
                    return
        found_alive = [n for n, d in alive_uniques.items() if d.get('alive', False) and n in unique_script_map]
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
            status = "Script" if name in unique_script_map else "No Script"
            log(f"   * {name} ({status})")
    except Exception as e:
        log(f"check_alive_uniques error: {e}")

def stop_script_btn():
    global current_active_unique, unique_queue, bot_state
    try:
        stop_attack_loop()
        stop_loot_timer()
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
    unique öldükten sonra loot_wait_sec kadar KOŞULSUZ bekler.
    Eskiden get_drops() boş dönerse (pick filter'a uymayan bir item düştüyse,
    ya da server drop paketini henüz işlememişse) anında şehre dönüyordu —
    yani ayarlanan bekleme süresi hiç işlemiyordu. Artık get_drops() sadece
    bilgi amaçlı (yerde ne göründüğünü loglamak için) kullanılıyor, bekleme
    süresini KISALTMIYOR/KESMİYOR.
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
                log(f"[Loot] get_drops() bos (pick filter disinda olabilir) — yine de {total_sec}s bekleniyor...")
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
        stop_attack_loop()
        current_active_unique = None
        update_active_unique_label()
        bot_state = 'RETURNING'
        log("Returning to town...")
        threading.Timer(0.0, _do_return).start()
    except Exception as e:
        log(f"finish_hunt error: {e}")
        bot_state = 'IDLE'

def _trigger_return_to_town():
    """نقطة مركزية للرجوع للتاون من أي مكان"""
    global bot_state, just_returned
    just_returned = False
    bot_state = 'RETURNING'
    _set_in_town(False)  # لسه مش في التاون
    stop_attack_loop()
    stop_loot_timer()
    try: stop_script()
    except: pass
    try: stop_bot()
    except: pass
    log("[AutoReturn] Triggering return to town...")
    threading.Timer(0.5, _do_return).start()

def _do_return():
    try: use_return_scroll()
    except: pass
    # استنى وصول التاون الفعلي بدل timer ثابت
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
                if uname in unique_script_map and alive_uniques.get(uname, {}).get('alive', False):
                    log(f"[Town] Next unique: {uname} → Starting in 1s...")
                    threading.Timer(1.0, auto_start_next_unique).start()
                    return
                elif uname not in unique_script_map:
                    unique_queue.remove(uname)
                    log(f"[Town] {uname} has no script → removed from queue.")
        update_queue_label()

    # Islenecek alive+scriptli unique yok → TOWNDA BEKLEME, grind slotuna geri don
    if plugin_active:
        if restore_slot():
            pass  # restore_slot kendi logunu basiyor
        else:
            log("[Town] Kayitli slot yok → townda bekleniyor. (Slot icin plugini slotta enable et)")
    else:
        log("[Town] Plugin disabled → standing by in town.")

def get_loot_wait_seconds():
    try:
        if QtBind.isChecked(gui, cbx_loot_wait):
            return max(0, float(QtBind.text(gui, tbx_loot_wait) or "60"))
        return 0
    except: return 60

def _is_unique_match(unique_name: str, monster_name: str) -> bool:
    """
    تطابق دقيق — يمنع False Positives زي Tiger يتطابق مع Tiger Girl
    - exact match
    - أو monster_name يبدأ بـ unique_name متبوعاً بـ space أو قوس
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
    لو الـ spawn اسمه variant (Tiger Girl (INT)) وفي mapping لـ (Tiger Girl)
    → يرجع الاسم المحفوظ في الـ map عشان يستخدمه
    لو مفيش → يرجع spawn_name نفسه
    """
    if spawn_name in unique_script_map:
        return spawn_name
    for mapped in unique_script_map:
        if _is_unique_match(mapped, spawn_name):
            return mapped
    return spawn_name

# ================= CORE UNIQUE RUNNER =================
def _on_unique_spawn(unique_name):
    """
    يُستدعى لما unique يظهر والـ plugin active.
    - لو في unique شغال حالياً → حط الجديد في القائمة وكمل
    - لو مش في التاون → حط في القائمة وارجع للتاون أول
    - لو في التاون → ضرب فوراً
    """
    global bot_state, current_active_unique, force_stopped, just_returned

    # لو في unique شغال → متوقفوش، حط الجديد في القائمة بس (لو عنده script)
    if current_active_unique and current_active_unique.lower() != unique_name.lower():
        if unique_name in unique_script_map:
            with _state_lock:
                if unique_name not in unique_queue:
                    unique_queue.append(unique_name)
                    sort_queue_by_priority()
            update_queue_label()
            log(f"[Queue] {unique_name} queued (busy with {current_active_unique}).")
        return

    # ===== تحقق من التاون قبل أي حاجة =====
    # just_returned = True معناه وصلنا التاون للتو → تجاوز الـ check
    in_town = just_returned or _is_in_town()
    if not in_town:
        # --- Script'i OLMAYAN unique → grind'i BOLME ---
        # (eski surumde script olsun olmasin sehre donuyordu; rastgele bir unique
        #  yaninda spawn olunca bot slotu birakip sehre isinlaniyordu = bug)
        if unique_name not in unique_script_map:
            if auto_return_enabled and bot_state == 'IDLE':
                log(f"[Spawn] {unique_name} (script yok) → Auto Return acik, donuluyor...")
                do_auto_return(unique_name)
            else:
                log(f"[Spawn] {unique_name} (script yok) → yok sayiliyor, slotta kaliniyor.")
            return

        # --- Script'li unique → slotu kaydet, sehre don, sonra script calissin ---
        log(f"[Spawn] {unique_name} slotta spawn oldu → slot kaydedilip sehre donuluyor...")
        with _state_lock:
            if unique_name not in unique_queue:
                unique_queue.append(unique_name)
                sort_queue_by_priority()
        update_queue_label()
        if bot_state == 'IDLE':
            capture_slot()            # slotu birakmadan once kaydet (training area hala slot)
            _trigger_return_to_town()
        return

    # ===== INSTANT ATTACK: ضرب فوري لو الـ unique قريب =====
    try:
        monsters = phBot.get_monsters()
        if monsters:
            target_name = unique_name.lower()
            for m_id, m_data in monsters.items():
                m_name = m_data.get('name', '').lower()
                if _is_unique_match(target_name, m_name):
                    log(f"[INSTANT] Attacking {unique_name} immediately!")
                    phBot.set_target(m_id)
                    phBot.attack_monster(m_id)
                    break
    except Exception as e:
        if debug_enabled: log(f"[Spawn] instant attack error: {e}")

    # شغّل الـ script
    run_mapped_script(unique_name, 'spawn')

def run_mapped_script(unique_name, event_type):
    global current_active_unique, unique_queue, bot_state, force_stopped, just_returned
    try:
        # =================== DEATH EVENT ===================
        if event_type == 'death':
            if current_active_unique and current_active_unique.lower() == unique_name.lower():
                log(f"{unique_name} DIED. Stopping Bot immediately.")
                stop_attack_loop()
                stop_loot_timer()
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
                # لو الـ script الحالي بيمشي لنفس الـ unique المات → وقفه وارجع للتاون
                if current_active_unique and current_active_unique.lower() == unique_name.lower():
                    log(f"{unique_name} died while script was running → stopping script.")
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
                        log(f"{unique_name} died outside town → returning to town...")
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

        # ---- AUTO RETURN: unique ظهر ومفيش له script والبوت IDLE ----
        if unique_name not in unique_script_map:
            with _state_lock:
                if unique_name not in pending_uniques:
                    pending_uniques.append(unique_name)
                    refresh_pending_list()
                    log(f"[Pending] {unique_name} has no script → added to pending.")
            if bot_state == 'IDLE' and auto_return_enabled:
                do_auto_return(unique_name)
            alive_uniques[unique_name]['handled'] = True
            return

        # ---- لو الشخصية بره التاون → حط الـ unique في القائمة وكمل اللي إنت فيه ----
        if not just_returned and not _is_in_town():
            with _state_lock:
                if unique_name not in unique_queue:
                    unique_queue.append(unique_name)
                    sort_queue_by_priority()
                    update_queue_label()
                    log(f"[Queue] {unique_name} queued (outside town — will run after current).")
            alive_uniques[unique_name]['handled'] = True
            return

        if force_stopped:
            if bot_state == 'IDLE' and plugin_active:
                log(f"[Town] New spawn: {unique_name} → Releasing force stop...")
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
        script_path = os.path.join(scripts_folder, script_name)
        if not os.path.exists(script_path):
            log(f"Script not found: {script_path}")
            alive_uniques[unique_name]['handled'] = True
            return

        try:
            force_stopped = False
            just_returned = False
            _set_in_town(False)  # خرجنا من التاون
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

            # جيب coordinates الـ unique
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

            # ===== ENGAGE MODE =====
            # لو الـ unique موجود في الـ monsters list → ضبط training area عليه وشغّل البوت
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
                radius_set = set_training_radius(120.0)
                if position_set is False:
                    log("[Engage] Training position ayarlanamadi; aktif Training Area secili mi?")
                phBot.start_bot()
                start_attack_loop()
                log(f"Started: {unique_name} (Engage Mode — pos set to unique)")
            else:
                # الـ unique مش في الـ monsters list (بعيد) → شغّل الـ script للمشي إليه
                set_training_script(script_path)
                with open(script_path, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                script_content = script_content.replace('{unique}', unique_name).replace('{event}', 'auto')
                phBot.start_script(script_content)
                start_attack_loop()
                log(f"Started: {unique_name} (Script Mode — walking to unique)")

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
    يتحقق لو الشخصية في التاون عن طريق الـ region.
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
    """يحدث الـ town state اليدوي"""
    global _in_town_state
    _in_town_state = value

# ================= GRIND SLOT SAVE / RESTORE =================
def capture_slot():
    """
    Mevcut training area'yi (grind slotu) kaydeder ki av bitince geri donebilelim.
    - Sadece av DISINDA cagrilmali (current_active_unique None) — yoksa training area
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
        log(f"[Slot] Slota geri donuluyor ({s['x']:.0f},{s['y']:.0f}) region={s['region']} → grind devam.")
        return True
    except Exception as e:
        log(f"restore_slot error: {e}")
        return False

def _return_then_enable():
    """يعمل return scroll وبعدين ينتظر الوصول للتاون فعلياً (polling بدل timer ثابت)"""
    log("Plugin ENABLED - Not in town → Using return scroll first...")
    try: use_return_scroll()
    except: pass
    threading.Timer(1.0, lambda: _wait_for_town(_after_return_enable, label="Enable")).start()

def _after_return_enable():
    """بعد الـ return، يبدأ البلجن"""
    global bot_state, force_stopped, just_returned
    if not plugin_active: return
    bot_state = 'IDLE'
    force_stopped = False
    just_returned = False
    _set_in_town(True)
    log("Arrived in town → Plugin ready.")
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
    # تحقق من التاون فعلاً بعد ثانيتين
    threading.Timer(2.0, _check_town_on_enable).start()

def _check_town_on_enable():
    """يتحقق من التاون بعد delay من التفعيل"""
    global just_returned
    if not plugin_active: return
    # Enable aninda mevcut slotu yakala (training area kalici; town'da olsak bile gecerli slot'u verir)
    capture_slot()
    if _is_in_town():
        just_returned = True
        _set_in_town(True)
        log("Plugin ENABLED — In town, ready.")
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
        has_ready = any(u in unique_script_map and alive_uniques.get(u, {}).get('alive', False)
                        for u in list(unique_queue))
        if has_ready:
            log("Plugin ENABLED — Bekleyen scriptli unique var → sehre donup avlaniyor.")
            _trigger_return_to_town()
        else:
            log("Plugin ENABLED — Slotta grind. Scriptli unique spawn olunca avlanacak.")

def disable_plugin_monitoring():
    global plugin_active, current_active_unique, bot_state
    if not plugin_active: return
    stop_attack_loop()
    stop_loot_timer()
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
    plugin_active = False
    update_plugin_status()
    save_config()
    log("Plugin DISABLED")

def update_active_unique_label():
    try:
        if lbl_active_unique is None: return
        value = current_active_unique if current_active_unique else "None"
        color = COLOR_SUCCESS if current_active_unique else COLOR_MUTED
        QtBind.setText(
            gui, lbl_active_unique,
            fixed_width_text('<font color="%s"><b>%s</b></font>' % (color, value), 205)
        )
    except: pass

def update_plugin_status():
    """Keep the live status row synchronized with the plugin state."""
    try:
        if plugin_active:
            status = '<font color="%s"><b>ACTIVE - MONITORING UNIQUE SPAWNS</b></font>' % COLOR_SUCCESS
        else:
            status = '<font color="%s"><b>INACTIVE - AUTOMATION STOPPED</b></font>' % COLOR_MUTED
        QtBind.setText(gui, lbl_plugin_status, fixed_width_text(status, 300))
    except: pass

def update_queue_label():
    try:
        if lbl_queue is None: return
        queue_text = f"({len(unique_queue)}) {', '.join(unique_queue[:3])}" if unique_queue else "Empty"
        QtBind.setText(
            gui, lbl_queue,
            fixed_width_text('<font color="%s">%s</font>' % (COLOR_TEXT, queue_text), 300)
        )
        refresh_queue_list()
    except: pass

def refresh_queue_list():
    try:
        if queue_list is None: return
        QtBind.clear(gui, queue_list)
        if unique_queue:
            for i, unique in enumerate(unique_queue, 1):
                priority = get_unique_priority(unique)
                script = unique_script_map.get(unique, "[No Script]")
                QtBind.append(gui, queue_list, f"{i}. [{priority}] {unique} -> {script}")
        else:
            QtBind.append(gui, queue_list, "Empty")
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

        # لو مش في التاون (ومش رجعنا للتو) → ارجع الأول
        if not just_returned and not _is_in_town():
            log("[AutoReturn] auto_start_next_unique: Not in town → Returning first!")
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
        selected = QtBind.text(gui, dropdown_unique)
        if not selected or selected not in unique_script_map:
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
    engaged = [False]        # flag: اتعمل engage مرة واحدة بس
    lost_after_engage = [0]  # كام tick متتالي مالقيناهوش بعد ما كان engaged (احتمال مات)

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

                        # ===== ENGAGE: أول مرة نلاقيه → وقف الـ script وضبط الـ training area عليه =====
                        if not engaged[0]:
                            engaged[0] = True
                            script_finished = True
                            log(f"[Engage] Found {monster.get('name')} → stop script, set training pos, start bot")
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
                                    radius_set = set_training_radius(120.0)
                                    if position_set is False:
                                        log("[Engage] Training position ayarlanamadi; aktif Training Area secili mi?")
                                    phBot.start_bot()
                                    log(f"[Engage] Training area set to ({mx:.0f},{my:.0f}) region={region}")
                            except Exception as e:
                                if debug_enabled: log(f"[Engage] error: {e}")

                        # ضرب مستمر
                        phBot.set_target(monster_id)
                        phBot.attack_monster(monster_id)
                        if debug_enabled: log(f"Attacking {monster.get('name')}")
                        break

            if not unique_found:
                # ===== GENEL TIMEOUT: script_finished şartı olmadan hunt başından beri sayar =====
                # (Eskiden bu sayaç sadece unique bir kere bulunduktan sonra işliyordu; script
                #  hedefe hiç ulaşamazsa hiçbir zaman tetiklenmiyordu → bot HUNTING'de kilitli kalıyordu)
                unique_not_found_count += 1
                timeout_seconds = get_timeout_seconds()
                max_attempts = timeout_seconds / 0.1
                if unique_not_found_count >= max_attempts:
                    log(f"TIMEOUT: {current_active_unique} missing")
                    handle_unique_timeout()
                    return

                # ===== HIZLI FALLBACK: engage edildikten sonra unique aniden kayboldu =====
                # (muhtemelen öldü ama chat/packet death tespiti bunu yakalamadı) → tam
                # timeout süresini (dakikalarca) beklemeden kısa bir grace period sonunda
                # ölmüş gibi davranıp loot bekle + şehre dön akışını tetikle.
                if engaged[0]:
                    lost_after_engage[0] += 1
                    grace_attempts = LOST_TARGET_GRACE_SEC / 0.1
                    if lost_after_engage[0] >= grace_attempts:
                        log(f"[LostTarget] {current_active_unique} disappeared after engage → assuming dead, returning.")
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
    kısa grace period içinde geri gelmedi → muhtemelen öldü (chat/packet
    death event'i yakalayamamış olabilir). Normal ölüm akışıyla aynı şekilde
    loot bekle + şehre dön.
    """
    global current_active_unique, bot_state, unique_not_found_count
    try:
        name = current_active_unique
        if not name: return
        stop_attack_loop()
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
        log(f"Timeout: {timeout_unique}")
        stop_attack_loop()
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
        just_returned = False  # هنروح التاون دلوقتي
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
                '<font color="%s"><b>OPENING DISCORD INVITE...</b></font>' % COLOR_WARNING,
                300
            )
        )
    except Exception as error:
        log('[%s] Discord link error: %s' % (pName, error))
        QtBind.setText(
            gui, lbl_plugin_status,
            fixed_width_text(
                '<font color="%s"><b>COULD NOT OPEN DISCORD INVITE</b></font>' % COLOR_ERROR,
                300
            )
        )


OFFSCREEN_X = 3000
monitor_widgets = []
settings_widgets = []
screen_widgets = []


def _screen_widget(widget, monitor_position=None, settings_position=None):
    screen_widgets.append(widget)
    if monitor_position:
        monitor_widgets.append((widget, monitor_position[0], monitor_position[1]))
    if settings_position:
        settings_widgets.append((widget, settings_position[0], settings_position[1]))
    return widget


def _show_screen(visible_widgets):
    for widget in screen_widgets:
        QtBind.move(gui, widget, OFFSCREEN_X, 0)
    for widget, x, y in visible_widgets:
        QtBind.move(gui, widget, x, y)


def show_settings():
    _show_screen(settings_widgets)


def show_monitor():
    _show_screen(monitor_widgets)


gui = QtBind.init(__name__, pName)

QtBind.createLabel(
    gui, u'<font color="%s" size="4"><b>\u2728 FAUTO UNIQUE V2</b></font>' % COLOR_PRIMARY,
    12, 6)
QtBind.createLabel(gui, '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion), 210, 12)
btn_discord = QtBind.createButton(gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(
    gui, u'<font color="%s"><b>\u269c Made By FascinaTe</b></font>' % COLOR_PRIMARY,
    565, 11)
QtBind.createLineEdit(gui, '', 12, 30, 716, 1)

# Navigation
btn_show_settings = _screen_widget(
    QtBind.createButton(gui, 'show_settings', 'Settings', 638, 39),
    monitor_position=(638, 39))
btn_show_monitor = _screen_widget(
    QtBind.createButton(gui, 'show_monitor', 'Back to Monitor', OFFSCREEN_X, 39),
    settings_position=(610, 39))

# Monitor: live control
monitor_live_title = _screen_widget(QtBind.createLabel(
    gui, '<font color="%s"><b>\u25cf LIVE CONTROL</b></font>' % COLOR_PRIMARY, 12, 42),
    monitor_position=(12, 42))
monitor_status_title = _screen_widget(
    QtBind.createLabel(gui, '<font color="#6b7280"><b>Status</b></font>', 12, 69),
    monitor_position=(12, 69))
lbl_plugin_status = _screen_widget(QtBind.createLabel(
    gui,
    fixed_width_text('<font color="%s"><b>INACTIVE - AUTOMATION STOPPED</b></font>' % COLOR_MUTED, 300),
    100, 69), monitor_position=(100, 69))
monitor_active_title = _screen_widget(
    QtBind.createLabel(gui, '<font color="#6b7280"><b>Active hunt</b></font>', 12, 94),
    monitor_position=(12, 94))
lbl_active_unique = _screen_widget(QtBind.createLabel(
    gui, fixed_width_text('<font color="%s"><b>None</b></font>' % COLOR_MUTED, 205), 100, 94),
    monitor_position=(100, 94))
monitor_queue_summary_title = _screen_widget(
    QtBind.createLabel(gui, '<font color="#6b7280"><b>Queue</b></font>', 12, 119),
    monitor_position=(12, 119))
lbl_queue = _screen_widget(QtBind.createLabel(
    gui, fixed_width_text('<font color="%s">Empty</font>' % COLOR_TEXT, 300), 100, 119),
    monitor_position=(100, 119))
btn_plugin_enable = _screen_widget(
    QtBind.createButton(gui, 'enable_plugin_monitoring', 'Start Monitoring', 445, 67),
    monitor_position=(445, 67))
btn_plugin_disable = _screen_widget(
    QtBind.createButton(gui, 'disable_plugin_monitoring', 'Stop Monitoring', 565, 67),
    monitor_position=(565, 67))
monitor_top_line = _screen_widget(
    QtBind.createLineEdit(gui, '', 12, 132, 716, 1), monitor_position=(12, 132))

# Settings: behavior
settings_behavior_title = _screen_widget(QtBind.createLabel(
    gui, '<font color="%s"><b>BEHAVIOR SETTINGS</b></font>' % COLOR_PRIMARY,
    OFFSCREEN_X, 40), settings_position=(12, 40))
cbx_loot_wait = _screen_widget(QtBind.createCheckBox(
    gui, 'do_nothing', 'Wait for loot after death', OFFSCREEN_X, 62),
    settings_position=(12, 62))
QtBind.setChecked(gui, cbx_loot_wait, True)
tbx_loot_wait = _screen_widget(
    QtBind.createLineEdit(gui, '60', OFFSCREEN_X, 58, 48, 22), settings_position=(190, 58))
lbl_loot_unit = _screen_widget(QtBind.createLabel(
    gui, '<font color="%s">sec</font>' % COLOR_MUTED, OFFSCREEN_X, 63),
    settings_position=(244, 63))
cbx_unique_timeout = _screen_widget(QtBind.createCheckBox(
    gui, 'do_nothing', 'Hunt timeout', OFFSCREEN_X, 88), settings_position=(12, 88))
QtBind.setChecked(gui, cbx_unique_timeout, True)
tbx_unique_timeout = _screen_widget(
    QtBind.createCombobox(gui, OFFSCREEN_X, 84, 90, 22), settings_position=(190, 84))
QtBind.append(gui, tbx_unique_timeout, '10min')
QtBind.append(gui, tbx_unique_timeout, '20min')
QtBind.append(gui, tbx_unique_timeout, '30min')
chk_auto_return = _screen_widget(QtBind.createCheckBox(
    gui, 'toggle_auto_return', 'Return to town when an unmapped unique appears', OFFSCREEN_X, 114),
    settings_position=(12, 114))
QtBind.setChecked(gui, chk_auto_return, False)
settings_mapping_line = _screen_widget(
    QtBind.createLineEdit(gui, '', OFFSCREEN_X, 136, 716, 1), settings_position=(12, 136))
settings_mapping_title = _screen_widget(QtBind.createLabel(
    gui, '<font color="%s"><b>UNIQUE / SCRIPT MAPPING</b></font>' % COLOR_PRIMARY,
    OFFSCREEN_X, 146), settings_position=(12, 146))

# Shared selectors keep the same widget objects for mapping and manual queue actions.
lbl_unique = _screen_widget(QtBind.createLabel(gui, 'Unique', OFFSCREEN_X, 211),
                            monitor_position=(12, 267), settings_position=(12, 171))
dropdown_unique = _screen_widget(QtBind.createCombobox(gui, OFFSCREEN_X, 207, 190, 22),
                                 monitor_position=(65, 263), settings_position=(65, 167))
lbl_script = _screen_widget(QtBind.createLabel(gui, 'Script', OFFSCREEN_X, 211),
                            settings_position=(268, 171))
dropdown_script = _screen_widget(QtBind.createCombobox(gui, OFFSCREEN_X, 207, 210, 22),
                                 settings_position=(310, 167))
btn_set = _screen_widget(QtBind.createButton(gui, 'set_script', 'Assign Script', OFFSCREEN_X, 205),
                         settings_position=(530, 165))
btn_refresh = _screen_widget(QtBind.createButton(
    gui, 'refresh_scripts', 'Refresh Script List', OFFSCREEN_X, 205),
    settings_position=(580, 193))

lbl_custom_unique = _screen_widget(QtBind.createLabel(gui, 'Custom unique', OFFSCREEN_X, 273),
                                   settings_position=(12, 199))
txt_unique = _screen_widget(QtBind.createLineEdit(gui, '', OFFSCREEN_X, 269, 220, 22),
                            settings_position=(105, 195))
btn_add_unique = _screen_widget(QtBind.createButton(gui, 'add_manual_unique', 'Add Unique', OFFSCREEN_X, 267),
                                settings_position=(335, 193))
btn_scan = _screen_widget(QtBind.createButton(
    gui, 'scan_nearby_uniques', 'Discover Nearby Uniques', OFFSCREEN_X, 267),
    settings_position=(435, 193))

# The mappings list is shared: mapping management uses it on Settings and
# manual hunting keeps using the exact same selection on Monitor.
monitor_manual_line = _screen_widget(
    QtBind.createLineEdit(gui, '', OFFSCREEN_X, 240, 716, 1), monitor_position=(12, 240))
lbl_mappings = _screen_widget(QtBind.createLabel(
    gui, '<font color="%s"><b>MAPPED UNIQUES</b></font>' % COLOR_PRIMARY, OFFSCREEN_X, 307),
    monitor_position=(300, 246), settings_position=(12, 229))
mappings_list = _screen_widget(QtBind.createList(gui, OFFSCREEN_X, 246, 428, 25),
                               monitor_position=(300, 263), settings_position=(12, 246))
btn_delete = _screen_widget(QtBind.createButton(
    gui, 'delete_selected_mapping', 'Remove Mapping', OFFSCREEN_X, 276),
    settings_position=(12, 276))

# Monitor: queue and unmapped lists
monitor_queue_title = _screen_widget(QtBind.createLabel(
    gui, '<font color="%s"><b>HUNT QUEUE</b></font>' % COLOR_PRIMARY, OFFSCREEN_X, 142),
    monitor_position=(12, 142))
queue_list = _screen_widget(QtBind.createList(gui, OFFSCREEN_X, 159, 350, 55),
                            monitor_position=(12, 159))
btn_start_next = _screen_widget(QtBind.createButton(
    gui, 'auto_start_next_unique', 'Hunt Next in Queue', OFFSCREEN_X, 216),
    monitor_position=(12, 216))
btn_remove_from_queue = _screen_widget(QtBind.createButton(
    gui, 'remove_from_queue_btn', 'Remove from Queue', OFFSCREEN_X, 216),
    monitor_position=(145, 216))
btn_clear_queue = _screen_widget(QtBind.createButton(gui, 'clear_queue_btn', 'Clear Queue', OFFSCREEN_X, 216),
                                 monitor_position=(275, 216))

monitor_pending_title = _screen_widget(QtBind.createLabel(
    gui, '<font color="%s"><b>UNMAPPED UNIQUES</b></font>' % COLOR_PRIMARY, OFFSCREEN_X, 142),
    monitor_position=(378, 142))
pending_list = _screen_widget(QtBind.createList(gui, OFFSCREEN_X, 159, 350, 55),
                              monitor_position=(378, 159))
btn_pending_assign = _screen_widget(QtBind.createButton(gui, 'show_settings', 'Assign Script', OFFSCREEN_X, 216),
                                    monitor_position=(378, 216))
btn_delete_pending = _screen_widget(QtBind.createButton(
    gui, 'delete_pending', 'Remove Entry', OFFSCREEN_X, 216),
    monitor_position=(480, 216))

monitor_manual_title = _screen_widget(QtBind.createLabel(
    gui, '<font color="%s"><b>MANUAL HUNT</b></font>' % COLOR_PRIMARY, OFFSCREEN_X, 246),
    monitor_position=(12, 246))
btn_add_queue = _screen_widget(QtBind.createButton(
    gui, 'add_to_queue_btn', 'Queue Selected Unique', OFFSCREEN_X, 290),
    monitor_position=(65, 290))
btn_start = _screen_widget(QtBind.createButton(
    gui, 'start_script_btn', 'Hunt Selected Unique', OFFSCREEN_X, 290),
    monitor_position=(300, 290))
btn_stop = _screen_widget(QtBind.createButton(
    gui, 'stop_script_btn', 'Stop Current Hunt', OFFSCREEN_X, 290),
    monitor_position=(610, 290))

# Settings: secondary diagnostics
settings_diagnostics_line = _screen_widget(
    QtBind.createLineEdit(gui, '', OFFSCREEN_X, 219, 716, 1), settings_position=(12, 219))
settings_diagnostics_title = _screen_widget(QtBind.createLabel(
    gui, '<font color="%s"><b>DIAGNOSTICS</b></font>' % COLOR_MUTED, OFFSCREEN_X, 229),
    settings_position=(455, 229))
chk_debug = _screen_widget(QtBind.createCheckBox(gui, 'toggle_debug', 'Detailed log', OFFSCREEN_X, 280),
                           settings_position=(455, 250))
btn_force_scan = _screen_widget(QtBind.createButton(
    gui, 'force_scan_alive_uniques', 'Refresh Nearby Alive Status', OFFSCREEN_X, 276),
    settings_position=(455, 276))
btn_check_alive = _screen_widget(QtBind.createButton(
    gui, 'check_alive_uniques', 'Log Tracked Uniques', OFFSCREEN_X, 276),
    settings_position=(610, 276))

show_monitor()

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
    """يُستدعى تلقائياً لما الـ account يفتح ويدخل اللعبة"""
    try:
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
            log(f"[{pName}] Plugin was ENABLED → Checking location...")
            _check_location_on_join()
    except Exception as e:
        log(f"_load_config_after_join error: {e}")

def _check_location_on_join():
    """بعد الـ join، لو بره التاون → ارجع الأول"""
    if not plugin_active: return
    if not _is_in_town():
        _set_in_town(False)
        log(f"[{pName}] Not in town → Using return scroll...")
        try: use_return_scroll()
        except: pass
        threading.Timer(1.0, lambda: _wait_for_town(_after_return_enable, label="Join")).start()
    else:
        _set_in_town(True)
        log(f"[{pName}] In town → Ready and waiting for uniques...")

# ================= EVENTS =================
UNIQUE_OBJ_CACHE = {}

def bot_started():
    """
    يتنادى لما أي plugin يشغّل البوت.
    بنتجاهله خالص — البلجن بيتحكم في البوت بنفسه عن طريق run_mapped_script.
    """
    pass

def _kill_unwanted_bot():
    pass

def teleported():
    """
    phBot bu event'i 'teleport_accepted' değil 'teleported' adıyla tetikliyor
    (bkz. docs/phbot-api/events.md) — eski isim hiç çağrılmıyordu, bu yüzden
    teleport sonrası şehir state güncellemesi çalışmıyordu.
    """
    threading.Timer(1.5, _update_town_state_after_teleport).start()

def _update_town_state_after_teleport():
    """بعد الـ teleport بثانية ونص، نتحقق من الـ town state الحقيقي (region تحقق)"""
    _set_in_town(_is_in_town())

# phBot'un native unique-spawn event'i (bkz. docs/phbot-api/events.md → handle_event türleri).
# Chat metni parse etmekten ve ham paket (0x300C) sniff etmekten daha güvenilir — server'ın
# chat mesaj formatı/paket yapısı farklı olsa bile bu event doğrudan monster adını veriyor.
EVENT_UNIQUE_SPAWN = 0

def handle_event(t, data):
    """EVENT_UNIQUE_SPAWN geldiğinde data = unique canavarın adı (string)."""
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
            if unique_name not in unique_script_map:
                if unique_name not in pending_uniques:
                    pending_uniques.append(unique_name)
                    refresh_pending_list()
                    log(f"[Pending] {unique_name} has no script → added to pending (Event).")
            else:
                if unique_name not in unique_queue:
                    unique_queue.append(unique_name)
                    sort_queue_by_priority()
                    update_queue_label()
                    log(f"[Auto-Saved] {unique_name} added to queue (Event).")

        if plugin_active and is_new:
            log(f"Event Spawn: {unique_name} (Executing)")
            _on_unique_spawn(unique_name)
        elif not plugin_active and is_new:
            log(f"Event Spawn: {unique_name} (Plugin Disabled - Saved Only)")
    except Exception as e:
        if debug_enabled: log(f"handle_event error: {e}")

def _handle_unique_death_notification(unique_name, source_tag):
    """
    Chat metni ya da 0xAA6B paketinden gelen 'unique öldü' bilgisini tek yerden işler.
    Ham isim variant/farklı case olabilir (örn. 'Tiger girl' vs mapped 'Tiger Girl') —
    _find_mapped_name ile normalize edilip run_mapped_script'e mapped isim geçiliyor,
    yoksa current_active_unique ile eşleşmeyip ölüm sinyali sessizce kaybolabiliyordu.
    """
    if not unique_name or not is_unique(unique_name):
        return
    mapped_name = _find_mapped_name(unique_name)
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
    '[Killer] killed UniqueName from Region. (x/y)' formatını ayrıştırır — 0xAA6B
    paketinden gelen düz metin bildirimi için (bkz. docs/phbot-api/sro-opcodes.md,
    canlı capture'dan doğrulandı). Başarısız olursa (None, None) döner.
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
                    # لو الاسم variant (Tiger Girl (INT)) → استخدم الـ mapped name (Tiger Girl)
                    mapped_name = _find_mapped_name(name)
                    is_new = False
                    with _state_lock:
                        if mapped_name not in alive_uniques or not alive_uniques[mapped_name]['alive']:
                            alive_uniques[mapped_name] = {
                                'spawn_time': time.time(), 'alive': True,
                                'handled': False, 'last_seen': time.time(), 'obj_id': obj_id
                            }
                            is_new = True
                        if mapped_name not in unique_script_map:
                            if mapped_name not in pending_uniques:
                                pending_uniques.append(mapped_name)
                                refresh_pending_list()
                                log(f"[Pending] {name} has no script → added to pending.")
                            # ملوش script → متضيفوش للـ queue خالص
                        else:
                            if mapped_name not in unique_queue:
                                unique_queue.append(mapped_name)
                                sort_queue_by_priority()
                                update_queue_label()
                                log(f"[Auto-Saved] {name} → using mapping [{mapped_name}] added to queue.")
                    if is_new:
                        if plugin_active:
                            log(f"Packet Spawn: {name} → mapped as [{mapped_name}] (Executing)")
                            _on_unique_spawn(mapped_name)
                        else:
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
        # 'has spawned' bazı serverlarda hiç kullanılmıyor — bu server 'has appeared on <region>'
        # diyor (bkz. docs/phbot-api/sro-opcodes.md, canlı doğrulandı). İkisi de destekleniyor.
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
                    if unique_name not in unique_script_map:
                        if unique_name not in pending_uniques:
                            pending_uniques.append(unique_name)
                            refresh_pending_list()
                            log(f"[Pending] {unique_name} has no script → added to pending (Chat).")
                        # ملوش script → متضيفوش للـ queue
                    else:
                        if unique_name not in unique_queue:
                            unique_queue.append(unique_name)
                            sort_queue_by_priority()
                            update_queue_label()
                            log(f"[Auto-Saved] {unique_name} added to queue (Chat).")
                if plugin_active and is_new:
                    log(f"Chat Spawn: {unique_name} (Executing)")
                    _on_unique_spawn(unique_name)

        # --- DEATH ---
        elif 'has been killed' in msg_lower or 'has died' in msg_lower:
            unique_name = msg.split('has been killed')[0].split('has died')[0].strip()
            _handle_unique_death_notification(unique_name, "CHAT DEATH")

        # Bu server 'has been killed'/'has died' demiyor — '[Killer] killed Unique from
        # Region. (x/y)' formatını kullanıyor (bkz. sro-opcodes.md, canlı doğrulandı).
        elif ' killed ' in msg and ' from ' in msg and msg.strip().startswith('['):
            killer_name, unique_name = _parse_unique_kill_message(msg.strip())
            if unique_name:
                _handle_unique_death_notification(unique_name, f"CHAT DEATH (killer={killer_name})")
    except: pass


log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
