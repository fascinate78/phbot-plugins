from phBot import *
import QtBind
import phBotChat
import json
import os
import struct
import time
import webbrowser


pName = 'FSroRAutoTrade'
pVersion = '3.1.0'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'
CHAT_PARTY = 4
SYNC_PROTOCOL = '#FRT'

EVENT_TRANSPORT_DIED = 3
EVENT_DIED = 7

STATE_IDLE = 'IDLE'
STATE_RETURNING = 'RETURNING'
STATE_LEAVING_PARTY = 'LEAVING_PARTY'
STATE_EQUIPPING = 'EQUIPPING'
STATE_RUNNING_TRADE = 'RUNNING_TRADE'
STATE_UNEQUIPPING = 'UNEQUIPPING'
STATE_WAITING_ACTION = 'WAITING_ACTION'
STATE_SETTLING_POUCH = 'SETTLING_POUCH'
STATE_DEATH_RECOVERY = 'DEATH_RECOVERY'
STATE_ERROR = 'ERROR'

POLL_SECONDS = 1.0
RETURN_TIMEOUT = 90.0
PARTY_TIMEOUT = 20.0
EQUIP_TIMEOUT = 20.0
TRADE_TIMEOUT = 1800.0
CITY_CONFIRM_TIMEOUT = 90.0
DEATH_RECOVERY_TIMEOUT = 60.0
RESPAWN_RETRY_SECONDS = 5.0
RESPAWN_MAX_ATTEMPTS = 3
RESPAWN_FINAL_WAIT_SECONDS = 10.0
POUCH_SETTLE_TIMEOUT = 30.0
POUCH_SETTLE_INTERVAL = 2.0
POUCH_STABLE_READS = 3
ACTION_RETRY_SECONDS = 3.0
TRANSPORT_DEATH_CONFIRM_SECONDS = 5.0
TRANSPORT_TELEPORT_GRACE_SECONDS = 5.0
TRANSPORT_SNAPSHOT_MAX_AGE = 10.0
SYNC_CHECK_INTERVAL = 10.0
SYNC_RESPONSE_TIMEOUT = 30.0
SYNC_PREPARE_TIMEOUT = 30.0

state = STATE_IDLE
state_since = time.time()
last_poll = 0.0
last_action = 0.0
cycle_active = False
cycle_armed = True
trade_command_received = False
trade_settled_received = False
trade_complete_time = 0.0
profile_name = 'default'
settings_loading = False
job_candidates = []
script_candidates = []
training_inside_streak = 0
pending_action = None
pouch_settle_started = 0.0
pouch_last_poll = 0.0
pouch_last_count = None
pouch_stable_reads = 0
death_teleport_received = False
respawn_attempts = 0
last_respawn_request = 0.0
last_box_count = None
status_panel_open = False
STATUS_OFFSCREEN_X = 3000
pending_transport_death_time = 0.0
pending_transport_death_region = 0
last_teleport_time = 0.0
tracked_transport_id = 0
transport_load_seen = False
transport_unloaded_after_load = False
last_transport_box_count = None
last_transport_snapshot_time = 0.0
profile_candidates = []
trade_profile_active = False
sync_run_id = ''
sync_phase = 'IDLE'
sync_expected_members = set()
sync_ready_members = {}
sync_ack_members = set()
sync_last_check = 0.0
sync_phase_since = 0.0
sync_wait_details = {}
current_language = 'en'


def _config_directory():
    try:
        root = get_config_dir()
    except Exception:
        root = None
    if not root:
        root = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root, pName)


def _scripts_directory():
    return os.path.join(_config_directory(), 'scripts')


def _settings_path():
    return os.path.join(_config_directory(), 'settings.json')


def _ensure_directories():
    try:
        if not os.path.isdir(_scripts_directory()):
            os.makedirs(_scripts_directory())
        return True
    except Exception as ex:
        log('[%s] Config klasoru olusturulamadi: %s' % (pName, ex))
        return False


def _fixed_width_text(content, width):
    return ('<table width="%d" cellspacing="0" cellpadding="0">'
            '<tr><td>%s</td></tr></table>') % (width, content)


gui = QtBind.init(__name__, pName)

QtBind.createLabel(
    gui, '<font color="#FF0000" size="4"><b>🐫 FSRO-R AUTO TRADE</b></font>', 12, 6
)
QtBind.createLabel(gui, '<font color="#9aa0ac">v%s</font>' % pVersion, 280, 12)
btn_language = QtBind.createButton(gui, 'btn_language_clicked', 'EN / TR', 325, 3)
btn_status_tab = QtBind.createButton(gui, 'btn_status_tab_clicked', '📊  Sync Status', 385, 3)
btn_discord = QtBind.createButton(gui, 'discord_clicked', u'💬 Discord', 510, 3)
QtBind.createLabel(
    gui, u'<font color="#FF0000"><b>⚜ Made By FascinaTe</b></font>', 610, 11
)
QtBind.createLineEdit(gui, '', 12, 30, 716, 1)

lbl_box_section = QtBind.createLabel(gui, '<font color="#FF0000"><b>📦 BOX CONTROL</b></font>', 10, 38)
chk_enabled = QtBind.createCheckBox(gui, 'chk_enabled_changed', 'Plugin aktif', 10, 58)

lbl_box_total_title = QtBind.createLabel(gui, '<font color="#6b7280"><b>Total boxes:</b></font>', 10, 83)
# QtBind label genisligini ilk metne gore sabitler. Genis bir ilk degerle
# olusturup tekrar 0'a cekmek, 3+ haneli kutu sayilarinin kirpilmasini onler.
lbl_box_count = QtBind.createLabel(
    gui, _fixed_width_text('<font color="#FF0000"><b>0</b></font>', 80), 125, 83)
lbl_target_title = QtBind.createLabel(gui, '<font color="#6b7280"><b>Trade target:</b></font>', 10, 111)
txt_target = QtBind.createLineEdit(gui, '80', 125, 107, 70, 22)
lbl_safety_title = QtBind.createLabel(gui, '<font color="#6b7280"><b>Safety limit (&lt;):</b></font>', 10, 139)
txt_safety = QtBind.createLineEdit(gui, '5', 125, 135, 70, 22)
lbl_delay_title = QtBind.createLabel(gui, '<font color="#6b7280"><b>Action delay:</b></font>', 10, 167)
txt_action_delay = QtBind.createLineEdit(gui, '2000', 125, 163, 70, 22)
lbl_delay_unit = QtBind.createLabel(gui, '<font color="#9aa0ac">ms</font>', 198, 167)
btn_check = QtBind.createButton(gui, 'btn_check_clicked', '↻  Kutuyu Kontrol Et', 10, 192)

lbl_job_section = QtBind.createLabel(gui, '<font color="#FF0000"><b>🥷 JOB ITEM</b></font>', 240, 38)
cmb_job_item = QtBind.createCombobox(gui, 240, 63, 330, 22)
btn_refresh_jobs = QtBind.createButton(gui, 'btn_refresh_jobs_clicked', '↻  Job Itemlerini Yenile', 240, 95)
chk_grind_with_job = QtBind.createCheckBox(
    gui, 'chk_grind_with_job_changed', 'Kasarken job itemi giyili kalsin', 240, 130
)
lbl_required_commands = QtBind.createLabel(
    gui, '<font color="#FF0000"><b>⚠ Scriptte ZORUNLU komutlar:</b></font>', 240, 155
)
lbl_settled_command = QtBind.createLabel(
    gui, '<font color="#FF0000"><b>Trade sonrasi: FSroRAutoTrade_settled</b></font>', 240, 175
)
lbl_complete_command = QtBind.createLabel(
    gui, '<font color="#FF0000"><b>Script sonunda: FSroRAutoTrade_complete</b></font>', 240, 195
)

lbl_script_section = QtBind.createLabel(
    gui, '<font color="#FF0000"><b>📜 KERVAN SCRIPTİ</b></font>'
         ' <font color="#9aa0ac">Config/FSroRAutoTrade/scripts</font>', 10, 220
)
cmb_script = QtBind.createCombobox(gui, 10, 237, 400, 22)
btn_refresh_scripts = QtBind.createButton(gui, 'btn_refresh_scripts_clicked', '↻  Scriptleri Yenile', 425, 236)

btn_save = QtBind.createButton(gui, 'btn_save_clicked', '💾  Ayarlari Kaydet', 10, 280)
btn_manual = QtBind.createButton(gui, 'btn_manual_clicked', '▶  Kervani Manuel Baslat', 145, 280)
btn_abort = QtBind.createButton(gui, 'btn_abort_clicked', '■  Islemi Iptal Et', 330, 280)

lbl_live_section = QtBind.createLabel(gui, '<font color="#FF0000"><b>● LIVE STATUS</b></font>', 10, 320)
lbl_state_title = QtBind.createLabel(gui, '<font color="#6b7280"><b>State:</b></font>', 10, 345)
lbl_state = QtBind.createLabel(
    gui, _fixed_width_text('<font color="#c98a1a"><b>Hazir</b></font>', 480), 70, 345)
lbl_message = QtBind.createLabel(
    gui, _fixed_width_text('<font color="#9aa0ac">Config klasoru hazirlaniyor...</font>', 700), 10, 372)
lbl_training_title = QtBind.createLabel(gui, '<font color="#6b7280"><b>Training Area:</b></font>', 10, 400)
lbl_training = QtBind.createLabel(
    gui, _fixed_width_text('<font color="#9aa0ac">Kontrol bekleniyor.</font>', 600), 105, 400)

# Sync ekranindaki buyuk arka plan ana ekran widget'larini orter. Header ve geri
# donus butonu her iki ekranda da gorunur kalir.
lst_sync_background = QtBind.createList(gui, STATUS_OFFSCREEN_X, 38, 716, 390)
chk_sync_enabled = QtBind.createCheckBox(
    gui, 'chk_sync_enabled_changed', 'Party synchronized trade', STATUS_OFFSCREEN_X, 45)
chk_sync_coordinator = QtBind.createCheckBox(
    gui, 'chk_sync_coordinator_changed', 'This character is coordinator', STATUS_OFFSCREEN_X, 45)
lbl_sync_coordinator = QtBind.createLabel(gui, '<b>Coordinator:</b>', STATUS_OFFSCREEN_X, 77)
txt_sync_coordinator = QtBind.createLineEdit(gui, '', STATUS_OFFSCREEN_X, 72, 180, 22)
lbl_sync_members = QtBind.createLabel(gui, '<b>Required members:</b>', STATUS_OFFSCREEN_X, 77)
txt_sync_members = QtBind.createLineEdit(gui, '', STATUS_OFFSCREEN_X, 72, 265, 22)
lbl_farm_profile = QtBind.createLabel(gui, '<b>Farm Profile:</b>', STATUS_OFFSCREEN_X, 112)
cmb_farm_profile = QtBind.createCombobox(gui, STATUS_OFFSCREEN_X, 107, 180, 22)
lbl_trade_profile = QtBind.createLabel(gui, '<b>Trade Profile:</b>', STATUS_OFFSCREEN_X, 112)
cmb_trade_profile = QtBind.createCombobox(gui, STATUS_OFFSCREEN_X, 107, 180, 22)
btn_refresh_profiles = QtBind.createButton(
    gui, 'btn_refresh_profiles_clicked', '↻ Profiles', STATUS_OFFSCREEN_X, 106)
lbl_sync_state = QtBind.createLabel(
    gui, _fixed_width_text('<font color="#9aa0ac">Sync idle.</font>', 700),
    STATUS_OFFSCREEN_X, 145)
lst_status_panel = QtBind.createList(gui, STATUS_OFFSCREEN_X, 175, 716, 235)

sync_panel_positions = (
    (lst_sync_background, 12, 38),
    (chk_sync_enabled, 20, 45),
    (chk_sync_coordinator, 245, 45),
    (lbl_sync_coordinator, 20, 77),
    (txt_sync_coordinator, 125, 72),
    (lbl_sync_members, 325, 77),
    (txt_sync_members, 450, 72),
    (lbl_farm_profile, 20, 112),
    (cmb_farm_profile, 125, 107),
    (lbl_trade_profile, 325, 112),
    (cmb_trade_profile, 430, 107),
    (btn_refresh_profiles, 625, 106),
    (lbl_sync_state, 20, 145),
    (lst_status_panel, 12, 175)
)

main_panel_positions = (
    (lbl_box_section, 10, 38), (chk_enabled, 10, 58),
    (lbl_box_total_title, 10, 83), (lbl_box_count, 125, 83),
    (lbl_target_title, 10, 111), (txt_target, 125, 107),
    (lbl_safety_title, 10, 139), (txt_safety, 125, 135),
    (lbl_delay_title, 10, 167), (txt_action_delay, 125, 163),
    (lbl_delay_unit, 198, 167), (btn_check, 10, 192),
    (lbl_job_section, 240, 38), (cmb_job_item, 240, 63),
    (btn_refresh_jobs, 240, 95), (chk_grind_with_job, 240, 130),
    (lbl_required_commands, 240, 155), (lbl_settled_command, 240, 175),
    (lbl_complete_command, 240, 195), (lbl_script_section, 10, 220),
    (cmb_script, 10, 237), (btn_refresh_scripts, 425, 236),
    (btn_save, 10, 280), (btn_manual, 145, 280), (btn_abort, 330, 280),
    (lbl_live_section, 10, 320), (lbl_state_title, 10, 345),
    (lbl_state, 70, 345), (lbl_message, 10, 372),
    (lbl_training_title, 10, 400), (lbl_training, 105, 400)
)

TRANSLATIONS = {
    'en': {
        'status': '📊  Sync Status', 'back': '←  Main Screen',
        'box_section': '<font color="#FF0000"><b>📦 BOX CONTROL</b></font>',
        'enabled': 'Plugin enabled', 'total': '<font color="#6b7280"><b>Total boxes:</b></font>',
        'target': '<font color="#6b7280"><b>Trade target:</b></font>',
        'safety': '<font color="#6b7280"><b>Safety limit (&lt;):</b></font>',
        'delay': '<font color="#6b7280"><b>Action delay:</b></font>',
        'check': '↻  Check Boxes', 'job_section': '<font color="#FF0000"><b>🥷 JOB ITEM</b></font>',
        'refresh_jobs': '↻  Refresh Job Items', 'grind_job': 'Keep job item equipped while grinding',
        'required': '<font color="#FF0000"><b>⚠ Required script commands:</b></font>',
        'settled': '<font color="#FF0000"><b>After trade: FSroRAutoTrade_settled</b></font>',
        'complete': '<font color="#FF0000"><b>Script end: FSroRAutoTrade_complete</b></font>',
        'script': '<font color="#FF0000"><b>📜 TRADE SCRIPT</b></font> <font color="#9aa0ac">Config/FSroRAutoTrade/scripts</font>',
        'refresh_scripts': '↻  Refresh Scripts', 'save': '💾  Save Settings',
        'manual': '▶  Start Trade Manually', 'abort': '■  Abort Operation',
        'live': '<font color="#FF0000"><b>● LIVE STATUS</b></font>',
        'state': '<font color="#6b7280"><b>State:</b></font>',
        'training': '<font color="#6b7280"><b>Training Area:</b></font>',
        'sync_enabled': 'Party synchronized trade', 'is_coordinator': 'This character is coordinator',
        'coordinator': '<b>Coordinator:</b>', 'members': '<b>Required members:</b>',
        'farm': '<b>Farm Profile:</b>', 'trade': '<b>Trade Profile:</b>', 'profiles': '↻ Profiles'
    },
    'tr': {
        'status': '📊  Senkron Durum', 'back': '←  Ana Ekran',
        'box_section': '<font color="#FF0000"><b>📦 KUTU KONTROLÜ</b></font>',
        'enabled': 'Plugin aktif', 'total': '<font color="#6b7280"><b>Toplam kutu:</b></font>',
        'target': '<font color="#6b7280"><b>Kervan hedefi:</b></font>',
        'safety': '<font color="#6b7280"><b>Güvenlik sınırı (&lt;):</b></font>',
        'delay': '<font color="#6b7280"><b>Komut gecikmesi:</b></font>',
        'check': '↻  Kutuyu Kontrol Et', 'job_section': '<font color="#FF0000"><b>🥷 JOB ITEMİ</b></font>',
        'refresh_jobs': '↻  Job Itemlerini Yenile', 'grind_job': 'Kasarken job itemi giyili kalsın',
        'required': '<font color="#FF0000"><b>⚠ Scriptte zorunlu komutlar:</b></font>',
        'settled': '<font color="#FF0000"><b>Trade sonrası: FSroRAutoTrade_settled</b></font>',
        'complete': '<font color="#FF0000"><b>Script sonunda: FSroRAutoTrade_complete</b></font>',
        'script': '<font color="#FF0000"><b>📜 KERVAN SCRIPTİ</b></font> <font color="#9aa0ac">Config/FSroRAutoTrade/scripts</font>',
        'refresh_scripts': '↻  Scriptleri Yenile', 'save': '💾  Ayarları Kaydet',
        'manual': '▶  Kervanı Manuel Başlat', 'abort': '■  İşlemi İptal Et',
        'live': '<font color="#FF0000"><b>● CANLI DURUM</b></font>',
        'state': '<font color="#6b7280"><b>Durum:</b></font>',
        'training': '<font color="#6b7280"><b>Training Area:</b></font>',
        'sync_enabled': 'Parti senkronlu kervan', 'is_coordinator': 'Bu karakter koordinatör',
        'coordinator': '<b>Koordinatör:</b>', 'members': '<b>Zorunlu üyeler:</b>',
        'farm': '<b>Farm Profili:</b>', 'trade': '<b>Trade Profili:</b>', 'profiles': '↻ Profiller'
    }
}


def _ui(key):
    return TRANSLATIONS.get(current_language, TRANSLATIONS['en']).get(key, key)


def _apply_language():
    pairs = (
        (lbl_box_section, 'box_section'), (chk_enabled, 'enabled'),
        (lbl_box_total_title, 'total'), (lbl_target_title, 'target'),
        (lbl_safety_title, 'safety'), (lbl_delay_title, 'delay'),
        (btn_check, 'check'), (lbl_job_section, 'job_section'),
        (btn_refresh_jobs, 'refresh_jobs'), (chk_grind_with_job, 'grind_job'),
        (lbl_required_commands, 'required'), (lbl_settled_command, 'settled'),
        (lbl_complete_command, 'complete'), (lbl_script_section, 'script'),
        (btn_refresh_scripts, 'refresh_scripts'), (btn_save, 'save'),
        (btn_manual, 'manual'), (btn_abort, 'abort'), (lbl_live_section, 'live'),
        (lbl_state_title, 'state'), (lbl_training_title, 'training'),
        (chk_sync_enabled, 'sync_enabled'), (chk_sync_coordinator, 'is_coordinator'),
        (lbl_sync_coordinator, 'coordinator'), (lbl_sync_members, 'members'),
        (lbl_farm_profile, 'farm'), (lbl_trade_profile, 'trade'),
        (btn_refresh_profiles, 'profiles')
    )
    for widget, key in pairs:
        QtBind.setText(gui, widget, _ui(key))
    QtBind.setText(gui, btn_status_tab, _ui('back') if status_panel_open else _ui('status'))
    QtBind.setText(gui, btn_language, 'TR' if current_language == 'en' else 'EN')


def _html_escape(value):
    return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _set_message(message, write_log=False):
    QtBind.setText(gui, lbl_message,
                   _fixed_width_text(
                       '<font color="#9aa0ac">%s</font>' % _html_escape(message), 700))
    if write_log:
        log('[%s] %s' % (pName, message))


def _set_state(new_state, message):
    global state, state_since, last_action
    state = new_state
    state_since = time.time()
    last_action = 0.0
    color = '#CC0000' if new_state == STATE_ERROR else '#c98a1a'
    if new_state == STATE_IDLE:
        color = '#1f9d63'
    QtBind.setText(gui, lbl_state,
                   _fixed_width_text(
                       '<font color="%s"><b>● %s</b></font>' % (color, new_state), 480))
    _set_message(message, True)


def _set_training_text(message):
    QtBind.setText(gui, lbl_training, _fixed_width_text(
        '<font color="#9aa0ac">%s</font>' % _html_escape(message), 600))


def _set_sync_text(message, color='#9aa0ac'):
    QtBind.setText(gui, lbl_sync_state, _fixed_width_text(
        '<font color="%s">%s</font>' % (color, _html_escape(message)), 700))


def _action_delay_seconds():
    value = _number(txt_action_delay, 0, 'Komut gecikmesi')
    if value is None:
        return 2.0
    return min(value, 60000) / 1000.0


def _schedule_action(action, message):
    global pending_action
    pending_action = action
    _set_state(STATE_WAITING_ACTION, '%s (%d ms bekleniyor)' % (
        message, int(_action_delay_seconds() * 1000)))


def _fail(message):
    global cycle_active, pending_action, pending_transport_death_time
    cycle_active = False
    pending_action = None
    pending_transport_death_time = 0.0
    try:
        stop_script()
    except Exception:
        pass
    try:
        stop_bot()
    except Exception:
        pass
    _set_state(STATE_ERROR, message)


def _recover_error_at_training():
    """Kullanici botu manuel baslatip slota donunce gecici hatayi temizler."""
    global cycle_active, cycle_armed, pending_action
    global trade_command_received, trade_settled_received, trade_complete_time
    global pending_transport_death_time, pending_transport_death_region
    global pouch_settle_started, pouch_last_poll
    global pouch_last_count, pouch_stable_reads, death_teleport_received
    global respawn_attempts, last_respawn_request

    cycle_active = False
    cycle_armed = True
    pending_action = None
    trade_command_received = False
    trade_settled_received = False
    trade_complete_time = 0.0
    pending_transport_death_time = 0.0
    _reset_transport_tracking()
    pending_transport_death_region = 0
    pouch_settle_started = 0.0
    pouch_last_poll = 0.0
    pouch_last_count = None
    pouch_stable_reads = 0
    death_teleport_received = False
    respawn_attempts = 0
    last_respawn_request = 0.0
    _set_state(STATE_IDLE,
               'Training area 3/3 dogrulandi; hata sifirlandi ve kontrol yeniden basladi.')


def _iter_items(value):
    if value is None:
        return
    if isinstance(value, (list, tuple)):
        for entry in value:
            for item in _iter_items(entry):
                yield item
        return
    if not isinstance(value, dict):
        return
    if ('name' in value or 'servername' in value or 'model' in value):
        yield value
        return
    if 'items' in value:
        for item in _iter_items(value.get('items')):
            yield item
        return
    for entry in value.values():
        for item in _iter_items(entry):
            yield item


def _quantity(item):
    try:
        value = int(item.get('quantity', 1) or 1)
        return value if value > 0 else 0
    except (TypeError, ValueError):
        return 1


def _is_specialty_box(item):
    name = str(item.get('name') or '').strip().lower()
    servername = str(item.get('servername') or '').strip().lower()
    if 'specialty goods box' in name:
        return True
    return ('specialty' in servername and
            ('goods' in servername or 'box' in servername))


def _read_box_count(show_error=False):
    global last_box_count
    try:
        pouch = get_job_pouch()
    except Exception as ex:
        if show_error:
            _set_message('Job pouch okunamadi: %s' % ex, True)
        return None
    if pouch is None:
        if show_error:
            _set_message('Job pouch verisi henuz hazir degil.', True)
        return None
    total = sum(_quantity(item) for item in _iter_items(pouch)
                if _is_specialty_box(item))
    last_box_count = total
    QtBind.setText(gui, lbl_box_count,
                   _fixed_width_text(
                       '<font color="#FF0000"><b>%d</b></font>' % total, 80))
    return total


def _training_debug_snapshot():
    result = {
        'status': 'Bilinmiyor', 'position_region': '-', 'training_region': '-',
        'distance': '-', 'radius': '-', 'inside': False
    }
    try:
        area = get_training_area()
        position = get_position()
    except Exception as ex:
        result['status'] = 'API hatasi: %s' % ex
        return result
    if not area:
        result['status'] = 'Aktif training area yok'
        return result
    if not position:
        result['status'] = 'Karakter konumu hazir degil'
        return result
    try:
        area_region = int(area.get('region', 0) or 0)
        position_region = int(position.get('region', 0) or 0)
        radius = float(area.get('radius', 50.0) or 50.0)
        dx = float(position.get('x', 0.0)) - float(area.get('x', 0.0))
        dy = float(position.get('y', 0.0)) - float(area.get('y', 0.0))
        distance = (dx * dx + dy * dy) ** 0.5
        same_region = not (area_region and position_region and
                           area_region != position_region)
        inside = same_region and distance <= radius
        result.update({
            'status': 'Iceride' if inside else
                      ('Farkli region' if not same_region else 'Disarida'),
            'position_region': position_region,
            'training_region': area_region,
            'distance': '%.1f' % distance,
            'radius': '%.1f' % radius,
            'inside': inside
        })
    except (TypeError, ValueError, KeyError) as ex:
        result['status'] = 'Gecersiz veri: %s' % ex
    return result


def _refresh_status_panel():
    if not status_panel_open:
        return
    training = _training_debug_snapshot()
    target_text = QtBind.text(gui, txt_target) or '-'
    safety_text = QtBind.text(gui, txt_safety) or '-'
    delay_text = QtBind.text(gui, txt_action_delay) or '-'
    job = _selected_job() or {}
    script_name = _selected_script_name() or '-'
    action_name = '-'
    if pending_action:
        action_name = getattr(pending_action, '__name__', str(pending_action))

    tr = current_language == 'tr'
    blockers = []
    if not QtBind.isChecked(gui, chk_enabled):
        blockers.append('Plugin pasif' if tr else 'Plugin disabled')
    if state == STATE_ERROR:
        blockers.append('ERROR durumu' if tr else 'ERROR state')
    if cycle_active:
        blockers.append('Aktif döngü var' if tr else 'Cycle already active')
    if training_inside_streak < 3:
        blockers.append('Training 3/3 değil' if tr else 'Training is not 3/3')
    if not cycle_armed:
        blockers.append('Cycle armed kapalı' if tr else 'Cycle is not armed')
    try:
        if last_box_count is None or int(last_box_count) < int(target_text):
            blockers.append('Kutu hedefin altında' if tr else 'Boxes below target')
    except Exception:
        blockers.append('Kutu/hedef geçersiz' if tr else 'Invalid box/target value')

    labels = ({
        'title': '=== FSroRAutoTrade CANLI DURUM ===', 'action': 'Bekleyen aksiyon',
        'boxes': 'Kutu / hedef', 'safety': 'Güvenlik sınırı', 'delay': 'Komut gecikmesi',
        'distance': 'Mesafe / radius', 'job': 'Seçili job itemi', 'script': 'Seçili script',
        'settled': 'Trade settled alındı', 'complete': 'Trade complete alındı',
        'transport_event': 'Transport event bekliyor', 'transport_load': 'Transport son yükü',
        'load_seen': 'Transport yük görüldü', 'delivered': 'Transport teslim edildi',
        'blockers': 'Otomatik tetik engeli', 'updated': 'Son güncelleme',
        'none': 'YOK - tetiklemeye hazır'
    } if tr else {
        'title': '=== FSroRAutoTrade LIVE STATUS ===', 'action': 'Pending action',
        'boxes': 'Boxes / target', 'safety': 'Safety limit', 'delay': 'Action delay',
        'distance': 'Distance / radius', 'job': 'Selected job item', 'script': 'Selected script',
        'settled': 'Trade settled received', 'complete': 'Trade complete received',
        'transport_event': 'Transport event pending', 'transport_load': 'Last transport load',
        'load_seen': 'Transport load seen', 'delivered': 'Transport delivered',
        'blockers': 'Automatic trigger blockers', 'updated': 'Last update',
        'none': 'NONE - ready to trigger'
    })
    rows = [
        labels['title'],
        'Plugin enabled       : %s' % QtBind.isChecked(gui, chk_enabled),
        'State                : %s' % state,
        'Cycle active         : %s' % cycle_active,
        'Cycle armed          : %s' % cycle_armed,
        '%-21s: %s' % (labels['action'], action_name),
        '%-21s: %s / %s' % (labels['boxes'],
            '-' if last_box_count is None else last_box_count, target_text),
        '%-21s: <%s' % (labels['safety'], safety_text),
        '%-21s: %s ms' % (labels['delay'], delay_text),
        'Training status      : %s' % training['status'],
        'Training streak      : %d/3' % training_inside_streak,
        'Position region      : %s' % training['position_region'],
        'Training region      : %s' % training['training_region'],
        '%-21s: %s / %s' % (labels['distance'], training['distance'], training['radius']),
        '%-21s: %s' % (labels['job'],
            job.get('name') or job.get('servername') or '-'),
        '%-21s: %s' % (labels['script'], script_name),
        'Sync enabled         : %s' % QtBind.isChecked(gui, chk_sync_enabled),
        'Sync coordinator     : %s' % _coordinator_name(),
        'Sync phase / run     : %s / %s' % (sync_phase, sync_run_id or '-'),
        'READY / expected     : %d / %d' % (
            len(sync_ready_members), len(sync_expected_members)),
        'ACK / expected       : %d / %d' % (
            len(sync_ack_members), len(sync_expected_members)),
        'Farm / trade profile : %s / %s' % (
            _selected_phbot_profile(cmb_farm_profile),
            _selected_phbot_profile(cmb_trade_profile)),
        '%-21s: %s' % (labels['settled'], trade_settled_received),
        '%-21s: %s' % (labels['complete'], trade_command_received),
        '%-21s: %s' % (labels['transport_event'], pending_transport_death_time > 0),
        '%-21s: %s' % (labels['transport_load'],
            '-' if last_transport_box_count is None else last_transport_box_count),
        '%-21s: %s' % (labels['load_seen'], transport_load_seen),
        '%-21s: %s' % (labels['delivered'], transport_unloaded_after_load),
        '%-21s: %s' % (labels['blockers'], ', '.join(blockers) if blockers else labels['none']),
        '%-21s: %s' % (labels['updated'], time.strftime('%H:%M:%S'))
    ]
    QtBind.clear(gui, lst_status_panel)
    for row in rows:
        QtBind.append(gui, lst_status_panel, row)


def _update_training_status():
    """Karakterin aktif training radius'u icinde oldugunu dogrular."""
    global training_inside_streak
    try:
        area = get_training_area()
        position = get_position()
    except Exception as ex:
        training_inside_streak = 0
        _set_training_text('Konum okunamadi: %s' % ex)
        return False

    if not area:
        training_inside_streak = 0
        _set_training_text('Aktif training area yok.')
        return False
    if not position:
        training_inside_streak = 0
        _set_training_text('Karakter konumu hazir degil.')
        return False

    try:
        area_region = int(area.get('region', 0) or 0)
        position_region = int(position.get('region', 0) or 0)
        if area_region and position_region and area_region != position_region:
            training_inside_streak = 0
            _set_training_text('Disarida (farkli region).')
            return False

        radius = float(area.get('radius', 50.0) or 50.0)
        dx = float(position.get('x', 0.0)) - float(area.get('x', 0.0))
        dy = float(position.get('y', 0.0)) - float(area.get('y', 0.0))
        distance_squared = dx * dx + dy * dy
        inside = distance_squared <= radius * radius
        distance = distance_squared ** 0.5
    except (TypeError, ValueError, KeyError) as ex:
        training_inside_streak = 0
        _set_training_text('Training verisi gecersiz: %s' % ex)
        return False

    if inside:
        training_inside_streak = min(3, training_inside_streak + 1)
        _set_training_text('Iceride %.1fm/%.1fm (%d/3)' % (
            distance, radius, training_inside_streak))
        return training_inside_streak >= 3

    training_inside_streak = 0
    _set_training_text('Disarida %.1fm/%.1fm' % (distance, radius))
    return False


def _is_in_town():
    """Resmi city API'si olmadigi icin yakin sehir NPC'leriyle dogrular."""
    try:
        position = get_position()
        npcs = get_npcs()
    except Exception:
        return False
    if not position or not npcs:
        return False

    keywords = (
        'STORE', 'WAREHOUSE', 'BLACKSMITH', 'POTION', 'GROCERY',
        'STABLE', 'SMITH', 'ARMOR', 'WEAPON', 'ACCESSORY'
    )
    nearby_count = 0
    for npc in npcs.values():
        try:
            npc_region = int(npc.get('region', 0) or 0)
            position_region = int(position.get('region', 0) or 0)
            if npc_region and position_region and npc_region != position_region:
                continue
            dx = float(position.get('x', 0.0)) - float(npc.get('x', 0.0))
            dy = float(position.get('y', 0.0)) - float(npc.get('y', 0.0))
            if dx * dx + dy * dy > 120.0 * 120.0:
                continue
            nearby_count += 1
            text = ('%s %s' % (
                npc.get('name', ''), npc.get('servername', ''))).upper()
            if any(keyword in text for keyword in keywords):
                return True
        except (TypeError, ValueError):
            continue
    # Return noktalarinda genellikle birden fazla sabit NPC gorunur.
    return nearby_count >= 2


def _transport_is_alive():
    try:
        pets = get_pets()
        if not isinstance(pets, dict):
            return False
        for pet in pets.values():
            if not isinstance(pet, dict):
                continue
            if pet.get('type') not in ('transport', 'horse'):
                continue
            try:
                if float(pet.get('hp', 1) or 0) > 0:
                    return True
            except (TypeError, ValueError):
                return True
    except Exception as ex:
        log('[%s] Transport kontrol edilemedi: %s' % (pName, ex))
    return False


def _reset_transport_tracking():
    global tracked_transport_id, transport_load_seen
    global transport_unloaded_after_load, last_transport_box_count
    global last_transport_snapshot_time
    tracked_transport_id = 0
    transport_load_seen = False
    transport_unloaded_after_load = False
    last_transport_box_count = None
    last_transport_snapshot_time = 0.0


def _poll_transport_load(now):
    """Ayni transport petindeki yuklu kutularin teslimatta bosaldigini izler."""
    global tracked_transport_id, transport_load_seen
    global transport_unloaded_after_load, last_transport_box_count
    global last_transport_snapshot_time
    try:
        pets = get_pets()
    except Exception:
        return
    if not isinstance(pets, dict):
        return

    selected_id = 0
    selected_pet = None
    for pet_id, pet in pets.items():
        if not isinstance(pet, dict):
            continue
        if pet.get('type') == 'transport':
            selected_id, selected_pet = pet_id, pet
            break
        if selected_pet is None and pet.get('type') == 'horse':
            selected_id, selected_pet = pet_id, pet
    if selected_pet is None:
        return

    count = sum(_quantity(item) for item in _iter_items(selected_pet.get('items'))
                if _is_specialty_box(item))
    try:
        selected_id = int(selected_id)
    except (TypeError, ValueError):
        selected_id = str(selected_id)

    # Teleport sonrasi yeni entity ID gelirse onceki petin sifirlanmasi teslimat
    # sayilmaz; yeni pet icin temiz bir snapshot serisi baslatilir.
    if selected_id != tracked_transport_id:
        tracked_transport_id = selected_id
        last_transport_box_count = count
        last_transport_snapshot_time = now
        if count > 0:
            transport_load_seen = True
            transport_unloaded_after_load = False
        return

    previous = last_transport_box_count
    if count > 0:
        transport_load_seen = True
        transport_unloaded_after_load = False
    elif transport_load_seen and previous is not None and previous > 0:
        transport_unloaded_after_load = True
        log('[%s] Transport yuku teslimat sonrasi bosaldi (%d -> 0).' %
            (pName, previous))
    last_transport_box_count = count
    last_transport_snapshot_time = now


def _confirm_pending_transport_death(now):
    global pending_transport_death_time, pending_transport_death_region
    if pending_transport_death_time <= 0:
        return
    if now - pending_transport_death_time < TRANSPORT_DEATH_CONFIRM_SECONDS:
        return

    event_time = pending_transport_death_time
    event_region = pending_transport_death_region
    pending_transport_death_time = 0.0
    pending_transport_death_region = 0
    if not cycle_active:
        return

    if (last_teleport_time and
            abs(last_teleport_time - event_time) <= TRANSPORT_TELEPORT_GRACE_SECONDS):
        _set_message('Transport event teleport kaynakli; yok sayildi.', True)
        return

    try:
        position = get_position()
        current_region = int(position.get('region', 0) or 0) if position else 0
    except Exception:
        current_region = 0
    if event_region and current_region and event_region != current_region:
        _set_message('Transport event region gecisi kaynakli; yok sayildi.', True)
        return

    if _transport_is_alive():
        _set_message('Transport halen canli; olum eventi yok sayildi.', True)
        return

    if trade_settled_received:
        _set_message('Trade teslimati isaretlendi; pet termination eventi yok sayildi.', True)
        return

    snapshot_fresh = (last_transport_snapshot_time > 0 and
                      now - last_transport_snapshot_time <= TRANSPORT_SNAPSHOT_MAX_AGE)
    if (snapshot_fresh and transport_load_seen and
            transport_unloaded_after_load and last_transport_box_count == 0):
        _set_message('Yuk teslim edilip transport kapatildi; event yok sayildi.', True)
        return

    if snapshot_fresh and last_transport_box_count is not None and last_transport_box_count > 0:
        _fail('Transport olumu dogrulandi; son gorulen yuk %d kutu.' %
              last_transport_box_count)
        return

    # Pet yuk snapshot'i yoksa despawn ile gercek olumu guvenilir bicimde
    # ayiramayiz. Yanlis pozitif ile tamamlanan kervani kesmek yerine script
    # watchdog'una birak.
    _set_message('Transport eventi yuk snapshoti olmadigi icin yok sayildi.', True)


def _number(widget, minimum, label):
    try:
        value = int(QtBind.text(gui, widget).strip())
    except Exception:
        _set_message('%s tam sayi olmali.' % label, True)
        return None
    if value < minimum:
        _set_message('%s en az %d olmali.' % (label, minimum), True)
        return None
    return value


def _character_name():
    try:
        data = get_character_data()
        if data and data.get('name'):
            return str(data.get('name'))
    except Exception:
        pass
    return 'default'


def _read_settings_file():
    try:
        with open(_settings_path(), 'r') as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _selected_job():
    try:
        selected_label = QtBind.text(gui, cmb_job_item)
        for item in job_candidates:
            if item.get('label') == selected_label:
                return item
    except Exception:
        pass
    return None


def _selected_script_name():
    try:
        selected = QtBind.text(gui, cmb_script)
        if selected in script_candidates:
            return selected
    except Exception:
        pass
    return ''


def _read_script_text(path):
    """Walk scriptini Windows varsayilan codec'inden bagimsiz olarak okur."""
    with open(path, 'rb') as handle:
        raw = handle.read()

    if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        return raw.decode('utf-16')

    encodings = ('utf-8-sig', 'cp1254', 'cp1256', 'cp1251', 'latin-1')

    last_error = None
    for encoding in encodings:
        try:
            return raw.decode(encoding)
        except (LookupError, UnicodeDecodeError) as ex:
            last_error = ex
    raise UnicodeDecodeError(
        'unknown', raw, 0, len(raw),
        'Desteklenen script kodlamalariyla okunamadi: %s' % last_error)


def _selected_phbot_profile(widget):
    selected = str(QtBind.text(gui, widget) or '').strip()
    for candidate in profile_candidates:
        if candidate['label'] == selected:
            return candidate['name']
    return None


def _fill_profile_combobox(widget, wanted):
    values = list(profile_candidates)
    values.sort(key=lambda item: (
        0 if item['name'] == wanted else 1,
        item['label'].lower()))
    _fill_combobox(widget, values)


def _refresh_profiles(wanted_farm=None, wanted_trade=None):
    global profile_candidates
    try:
        character = get_character_data() or {}
        server = str(character.get('server') or '').strip()
        name = str(character.get('name') or '').strip()
        root = get_config_dir()
    except Exception:
        server, name, root = '', '', None
    if not server or not name or not root:
        profile_candidates = []
        _fill_combobox(cmb_farm_profile, [])
        _fill_combobox(cmb_trade_profile, [])
        return False

    prefix = '%s_%s' % (server, name)
    found = {'': 'Default'}
    try:
        for file_name in os.listdir(root):
            if file_name == prefix + '.json':
                found[''] = 'Default'
                continue
            marker = prefix + '.'
            if not file_name.startswith(marker) or not file_name.endswith('.json'):
                continue
            profile = file_name[len(marker):-5]
            if profile:
                found[profile] = profile
    except Exception as ex:
        _set_message('phBot profilleri okunamadi: %s' % ex, True)
        return False

    profile_candidates = [
        {'name': profile, 'label': label}
        for profile, label in found.items()
    ]
    if wanted_farm is None:
        wanted_farm = get_profile()
    if wanted_trade is None:
        wanted_trade = ''
    _fill_profile_combobox(cmb_farm_profile, wanted_farm)
    _fill_profile_combobox(cmb_trade_profile, wanted_trade)
    return True


def _required_member_names():
    raw = str(QtBind.text(gui, txt_sync_members) or '')
    return set(value.strip().lower() for value in raw.replace(';', ',').split(',')
               if value.strip())


def _profile_values():
    job = _selected_job() or {}
    return {
        'enabled': bool(QtBind.isChecked(gui, chk_enabled)),
        'target': _number(txt_target, 1, 'Kervan hedefi'),
        'safety': _number(txt_safety, 1, 'Guvenlik siniri'),
        'action_delay_ms': _number(txt_action_delay, 0, 'Komut gecikmesi'),
        'grind_with_job': bool(QtBind.isChecked(gui, chk_grind_with_job)),
        'job_model': int(job.get('model', 0) or 0),
        'job_servername': str(job.get('servername') or ''),
        'script': _selected_script_name(),
        'sync_enabled': bool(QtBind.isChecked(gui, chk_sync_enabled)),
        'sync_coordinator': bool(QtBind.isChecked(gui, chk_sync_coordinator)),
        'coordinator_name': str(QtBind.text(gui, txt_sync_coordinator) or '').strip(),
        'required_members': str(QtBind.text(gui, txt_sync_members) or '').strip(),
        'farm_profile': _selected_phbot_profile(cmb_farm_profile),
        'trade_profile': _selected_phbot_profile(cmb_trade_profile),
        'language': current_language
    }


def _save_settings(silent=False, validate_sync=True):
    values = _profile_values()
    if (values['target'] is None or values['safety'] is None or
            values['action_delay_ms'] is None):
        return False
    if validate_sync and values['sync_enabled']:
        valid, reason = _validate_sync_setup()
        if not valid:
            _set_sync_text(reason, '#e74c3c')
            if not silent:
                _set_message('Sync ayari gecersiz: %s' % reason, True)
            return False
    data = _read_settings_file()
    profiles = data.get('profiles')
    if not isinstance(profiles, dict):
        profiles = {}
    profiles[profile_name] = values
    data['profiles'] = profiles
    try:
        _ensure_directories()
        with open(_settings_path(), 'w') as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
        if not silent:
            _set_message('Ayarlar kaydedildi: %s' % profile_name, True)
        return True
    except Exception as ex:
        _set_message('Ayarlar kaydedilemedi: %s' % ex, True)
        return False


def _fill_combobox(widget, values):
    QtBind.clear(gui, widget)
    for value in values:
        QtBind.append(gui, widget, value.get('label', '') if isinstance(value, dict) else value)


def _inventory_items():
    try:
        inventory = get_inventory()
    except Exception:
        return []
    if not inventory:
        return []
    result = []
    for slot, item in enumerate(inventory.get('items') or []):
        if item:
            copy = dict(item)
            copy['slot'] = slot
            result.append(copy)
    return result


def _is_job_item(item):
    text = ('%s %s' % (item.get('name', ''), item.get('servername', ''))).upper()
    if 'OUTFIT' in text:
        return True
    try:
        data = get_item(int(item.get('model', 0)))
        return bool(data and int(data.get('tid2', -1)) == 7)
    except Exception:
        return False


def _refresh_jobs(wanted_servername='', wanted_model=0):
    global job_candidates
    candidates = []
    seen = set()
    for item in _inventory_items():
        if not _is_job_item(item):
            continue
        identity = (int(item.get('model', 0) or 0), str(item.get('servername') or ''))
        if identity in seen:
            continue
        seen.add(identity)
        entry = dict(item)
        entry['label'] = '%s [%s]' % (
            item.get('name') or item.get('servername') or 'Job item', item.get('model', '?'))
        candidates.append(entry)
    wanted = wanted_servername
    if not wanted and wanted_model:
        for item in candidates:
            if int(item.get('model', 0) or 0) == int(wanted_model):
                wanted = item.get('servername', '')
                break
    # QtBind combobox icin secim ayarlama API'si yoktur. Kayitli secimi
    # listenin basina tasimak reload sonrasi ayni itemi secili tutar.
    if wanted:
        candidates.sort(key=lambda item: 0 if str(item.get('servername') or '') == str(wanted) else 1)
    job_candidates = candidates
    _fill_combobox(cmb_job_item, job_candidates)
    return bool(job_candidates)


def _refresh_scripts(wanted=''):
    global script_candidates
    _ensure_directories()
    try:
        names = [name for name in os.listdir(_scripts_directory())
                 if os.path.isfile(os.path.join(_scripts_directory(), name)) and
                 not name.startswith('.')]
        names.sort(key=lambda value: value.lower())
    except Exception:
        names = []
    if wanted in names:
        names.remove(wanted)
        names.insert(0, wanted)
    script_candidates = names
    _fill_combobox(cmb_script, script_candidates)
    return bool(script_candidates)


def _load_profile():
    global profile_name, settings_loading, current_language
    settings_loading = True
    profile_name = _character_name()
    data = _read_settings_file().get('profiles', {}).get(profile_name, {})
    current_language = str(data.get('language', 'en')).lower()
    if current_language not in TRANSLATIONS:
        current_language = 'en'
    QtBind.setText(gui, txt_target, str(data.get('target', 80)))
    QtBind.setText(gui, txt_safety, str(data.get('safety', 5)))
    QtBind.setText(gui, txt_action_delay, str(data.get('action_delay_ms', 2000)))
    QtBind.setChecked(gui, chk_grind_with_job, bool(data.get('grind_with_job', False)))
    _refresh_jobs(data.get('job_servername', ''), data.get('job_model', 0))
    _refresh_scripts(data.get('script', ''))
    _refresh_profiles(data.get('farm_profile', ''), data.get('trade_profile', ''))
    QtBind.setChecked(gui, chk_sync_enabled, bool(data.get('sync_enabled', False)))
    QtBind.setChecked(gui, chk_sync_coordinator,
                      bool(data.get('sync_coordinator', False)))
    QtBind.setText(gui, txt_sync_coordinator,
                   str(data.get('coordinator_name', '')))
    QtBind.setText(gui, txt_sync_members,
                   str(data.get('required_members', '')))
    QtBind.setChecked(gui, chk_enabled, bool(data.get('enabled', False)))
    _apply_language()
    settings_loading = False
    _set_message('Profil yuklendi: %s' % profile_name, True)


def _job_identity():
    selected = _selected_job()
    if not selected:
        return None
    return (int(selected.get('model', 0) or 0), str(selected.get('servername') or ''))


def _same_job(item, identity):
    if not item or not identity:
        return False
    model, servername = identity
    if model and int(item.get('model', 0) or 0) == model:
        return True
    return bool(servername and str(item.get('servername') or '') == servername)


def _find_job(identity):
    for item in _inventory_items():
        if _same_job(item, identity):
            return item
    return None


def _empty_inventory_slot():
    try:
        inventory = get_inventory()
        items = inventory.get('items') or []
        size = int(inventory.get('size', len(items)))
        for slot in range(13, min(size, len(items))):
            if items[slot] is None:
                return slot
    except Exception:
        pass
    return -1


def _move_item(source, destination):
    packet = struct.pack('<BBBH', 0, int(source), int(destination), 0)
    inject_joymax(0x7034, packet, False)


def _own_name():
    return _character_name()


def _coordinator_name():
    if QtBind.isChecked(gui, chk_sync_coordinator):
        return _own_name()
    return str(QtBind.text(gui, txt_sync_coordinator) or '').strip()


def _party_names():
    names = set()
    try:
        for member in (get_party() or {}).values():
            name = str(member.get('name') or '').strip().lower()
            if name:
                names.add(name)
    except Exception:
        pass
    return names


def _send_sync(command, argument=''):
    if not sync_run_id:
        return False
    message = '%s|%s|%s' % (SYNC_PROTOCOL, sync_run_id, command)
    if argument:
        message += '|' + str(argument)
    try:
        result = phBotChat.Party(message)
    except Exception as ex:
        log('[%s] Party sync mesaji hatasi: %s' % (pName, ex))
        return False
    if not result:
        log('[%s] Party sync mesaji gonderilemedi: %s' % (pName, message))
    return bool(result)


def _apply_phbot_profile(profile, label):
    if profile is None:
        _set_message('%s profili secilmedi.' % label, True)
        return False
    try:
        set_profile(profile)
        active = get_profile()
    except Exception as ex:
        _set_message('%s profili yuklenemedi: %s' % (label, ex), True)
        return False
    if active == profile:
        return True
    _set_message('%s profili dogrulanamadi: %s' % (
        label, 'Default' if profile == '' else profile), True)
    return False


def _validate_sync_setup():
    coordinator = _coordinator_name()
    farm = _selected_phbot_profile(cmb_farm_profile)
    trade = _selected_phbot_profile(cmb_trade_profile)
    if not coordinator:
        return False, 'Coordinator name is empty'
    if farm is None or trade is None:
        return False, 'Farm or trade profile is not selected'
    if farm == trade:
        return False, 'Farm and trade profiles must be different'
    members = _required_member_names()
    if not members:
        return False, 'Required members list is empty'
    if coordinator.lower() not in members:
        return False, 'Required members must include coordinator'
    return True, ''


def _local_sync_readiness(target):
    if not QtBind.isChecked(gui, chk_enabled):
        return False, 'PLUGIN_DISABLED', 0
    if cycle_active or state != STATE_IDLE:
        return False, 'BUSY_%s' % state, 0
    if not cycle_armed:
        return False, 'CYCLE_NOT_ARMED', 0
    if training_inside_streak < 3:
        return False, 'TRAINING_%d_3' % training_inside_streak, 0
    local_target = _number(txt_target, 1, 'Kervan hedefi')
    if local_target is None or local_target != target:
        return False, 'TARGET_MISMATCH_%s' % local_target, 0
    count = _read_box_count(False)
    if count is None:
        return False, 'POUCH_UNAVAILABLE', 0
    if count < target:
        return False, 'BOX_%d_%d' % (count, target), count
    if not _selected_job() or not _find_job(_job_identity()):
        return False, 'JOB_ITEM_MISSING', count
    script_name = _selected_script_name()
    script_path = os.path.join(_scripts_directory(), script_name)
    if not script_name or not os.path.isfile(script_path):
        return False, 'SCRIPT_MISSING', count
    try:
        script_text = _read_script_text(script_path)
    except Exception:
        return False, 'SCRIPT_UNREADABLE', count
    if ('FSroRAutoTrade_settled' not in script_text or
            'FSroRAutoTrade_complete' not in script_text):
        return False, 'SCRIPT_COMMANDS_MISSING', count
    valid, reason = _validate_sync_setup()
    if not valid:
        return False, 'SETUP_%s' % reason.replace(' ', '_').upper(), count
    return True, 'READY', count


def _sync_all_recent(now):
    for member in sync_expected_members:
        if now - sync_ready_members.get(member, 0.0) > SYNC_RESPONSE_TIMEOUT:
            return False
    return True


def _sync_reset(message='Sync idle.'):
    global sync_run_id, sync_phase, sync_expected_members
    global sync_last_check, sync_phase_since
    sync_run_id = ''
    sync_phase = 'IDLE'
    sync_expected_members = set()
    sync_ready_members.clear()
    sync_ack_members.clear()
    sync_wait_details.clear()
    sync_last_check = 0.0
    sync_phase_since = 0.0
    _set_sync_text(message)


def _sync_begin_coordinator(now, target):
    global sync_run_id, sync_phase, sync_expected_members
    global sync_last_check, sync_phase_since
    valid, reason = _validate_sync_setup()
    if not valid:
        _set_sync_text(reason, '#e74c3c')
        return
    required = _required_member_names()
    own = _own_name().lower()
    party = _party_names()
    missing = required.difference(party | set([own]))
    if missing:
        _set_sync_text('Missing party members: %s' % ', '.join(sorted(missing)), '#c98a1a')
        return
    sync_run_id = '%s-%d' % (own, int(now * 1000))
    sync_expected_members = required.difference(set([own]))
    sync_ready_members.clear()
    sync_ack_members.clear()
    sync_wait_details.clear()
    sync_phase = 'WAIT_READY'
    sync_phase_since = now
    sync_last_check = now
    _send_sync('CHECK', str(target))
    _set_sync_text('Waiting READY: 0/%d' % len(sync_expected_members), '#c98a1a')


def _sync_start_local():
    global sync_phase, trade_profile_active
    if cycle_active or sync_phase == 'STARTED':
        return
    target = _number(txt_target, 1, 'Kervan hedefi')
    ready, reason, count = _local_sync_readiness(target or 0)
    if not ready:
        _set_sync_text('START rejected locally: %s' % reason, '#e74c3c')
        _send_sync('FAILED', '%s:%s' % (_own_name(), reason))
        return
    trade_profile = _selected_phbot_profile(cmb_trade_profile)
    if not _apply_phbot_profile(trade_profile, 'Trade'):
        _send_sync('FAILED', '%s:TRADE_PROFILE' % _own_name())
        _set_sync_text('Trade profile could not be activated', '#e74c3c')
        return
    trade_profile_active = True
    sync_phase = 'STARTED'
    _set_sync_text('START received; trade profile active (%d boxes)' % count, '#1f9d63')
    if not _begin_cycle(False):
        trade_profile_active = False
        _apply_phbot_profile(_selected_phbot_profile(cmb_farm_profile), 'Farm')
        _send_sync('FAILED', '%s:BEGIN_CYCLE' % _own_name())


def _poll_sync(now, target, training_ready):
    global sync_phase, sync_last_check, sync_phase_since
    if not QtBind.isChecked(gui, chk_sync_enabled) or cycle_active:
        return
    if not QtBind.isChecked(gui, chk_sync_coordinator):
        if sync_phase == 'WAIT_START' and now - sync_phase_since > SYNC_RESPONSE_TIMEOUT * 2:
            _sync_reset('Coordinator timeout; waiting for a new CHECK.')
        return
    if sync_phase == 'IDLE':
        if training_ready and cycle_armed and last_box_count is not None and last_box_count >= target:
            _sync_begin_coordinator(now, target)
        return
    if sync_phase == 'WAIT_READY':
        if now - sync_last_check >= SYNC_CHECK_INTERVAL:
            sync_last_check = now
            _send_sync('CHECK', str(target))
        if _sync_all_recent(now):
            own_ready, own_reason, own_count = _local_sync_readiness(target)
            if not own_ready:
                _set_sync_text('Coordinator no longer ready: %s' % own_reason, '#c98a1a')
                return
            sync_phase = 'WAIT_ACK'
            sync_phase_since = now
            sync_ack_members.clear()
            _send_sync('PREPARE', str(target))
            _set_sync_text('All READY; waiting final ACK', '#c98a1a')
    elif sync_phase == 'WAIT_ACK':
        if sync_expected_members.issubset(sync_ack_members):
            own_ready, own_reason, own_count = _local_sync_readiness(target)
            party_missing = sync_expected_members.difference(_party_names())
            if not own_ready or party_missing:
                reason = own_reason if not own_ready else (
                    'PARTY_MISSING_%s' % ','.join(sorted(party_missing)))
                _send_sync('ABORT', reason)
                _sync_reset('Sync aborted before START: %s' % reason)
                return
            _send_sync('START', str(target))
            _sync_start_local()
        elif now - sync_phase_since > SYNC_PREPARE_TIMEOUT:
            _send_sync('ABORT', 'ACK_TIMEOUT')
            _sync_reset('Sync aborted: ACK timeout')


def _begin_cycle(manual=False):
    global cycle_active, cycle_armed
    global trade_command_received, trade_settled_received
    global trade_complete_time, pending_transport_death_time
    if cycle_active:
        _set_message('Zaten aktif bir kervan islemi var.', True)
        return False
    if not QtBind.isChecked(gui, chk_enabled):
        _set_message('Kervan baslatmak icin once Plugin aktif secenegini acin.', True)
        return False
    if not manual and training_inside_streak < 3:
        _set_message('Otomatik kervan icin karakter training area icinde olmali.', True)
        return False
    target = _number(txt_target, 1, 'Kervan hedefi')
    safety = _number(txt_safety, 1, 'Guvenlik siniri')
    if target is None or safety is None:
        return False
    if not _selected_job():
        _set_message('Once kullanilacak job itemini secin.', True)
        return False
    script_name = _selected_script_name()
    if not script_name:
        _set_message('Once kervan scriptini secin.', True)
        return False
    script_path = os.path.join(_scripts_directory(), script_name)
    if not os.path.isfile(script_path):
        _set_message('Secilen kervan scripti bulunamadi.', True)
        return False
    count = _read_box_count(True)
    if count is None:
        return False
    if not manual and count < target:
        return False
    _save_settings(True)
    cycle_active = True
    cycle_armed = False
    trade_command_received = False
    trade_settled_received = False
    trade_complete_time = 0.0
    pending_transport_death_time = 0.0
    try:
        stop_script()
    except Exception:
        pass
    try:
        stop_bot()
    except Exception:
        pass
    _schedule_action(_use_initial_return_scroll,
                     'Bot ve walking durduruldu; return scroll hazirlaniyor.')
    return True


def _use_initial_return_scroll():
    _set_state(STATE_RETURNING, 'Return scroll kullaniliyor.')
    try:
        if not use_return_scroll():
            _fail('Return scroll kullanilamadi veya bulunamadi.')
            return False
    except Exception as ex:
        _fail('Return scroll hatasi: %s' % ex)
        return False
    return True


def _begin_party_leave_or_equip():
    try:
        party = get_party()
    except Exception as ex:
        _fail('Party bilgisi okunamadi: %s' % ex)
        return
    if party:
        inject_joymax(0x7061, b'', False)
        _set_state(STATE_LEAVING_PARTY, 'Sehre varildi; partyden cikiliyor.')
    else:
        _begin_equip()


def _begin_equip():
    identity = _job_identity()
    item = _find_job(identity)
    if not item:
        _fail('Secilen job itemi envanterde bulunamadi.')
        return
    if int(item.get('slot', -1)) == 8:
        _schedule_action(_start_trade_script,
                         'Job itemi zaten giyili; kervan scripti hazirlaniyor.')
        return
    _move_item(item.get('slot'), 8)
    _set_state(STATE_EQUIPPING, 'Job itemi giyiliyor: %s' % item.get('name', '?'))


def _start_trade_script():
    global trade_command_received, trade_settled_received, trade_complete_time
    name = _selected_script_name()
    path = os.path.join(_scripts_directory(), name)
    try:
        script_text = _read_script_text(path)
    except Exception as ex:
        _fail('Kervan scripti okunamadi: %s' % ex)
        return
    if not script_text.strip():
        _fail('Kervan scripti bos.')
        return
    if 'FSroRAutoTrade_complete' not in script_text:
        _fail('Script sonunda FSroRAutoTrade_complete komutu bulunmuyor.')
        return
    if 'FSroRAutoTrade_settled' not in script_text:
        _fail('Trade komutundan sonra FSroRAutoTrade_settled komutu bulunmuyor.')
        return
    trade_command_received = False
    trade_settled_received = False
    trade_complete_time = 0.0
    try:
        result = start_script(script_text)
    except Exception as ex:
        _fail('Kervan scripti baslatilamadi: %s' % ex)
        return
    if result is False:
        _fail('phBot kervan scriptini baslatmayi reddetti.')
        return
    _set_state(STATE_RUNNING_TRADE, 'Kervan scripti calisiyor: %s' % name)


def _try_finish_trade():
    if state != STATE_RUNNING_TRADE:
        return
    if not trade_command_received:
        return
    if not _is_in_town():
        _set_message('Tamamlama komutu alindi; karakterin sehirde oldugu dogrulaniyor.')
        if trade_complete_time and time.time() - trade_complete_time > CITY_CONFIRM_TIMEOUT:
            _fail('Karakterin sehirde oldugu %d saniyede dogrulanamadi.' % CITY_CONFIRM_TIMEOUT)
        return
    _begin_pouch_settle()


def _begin_pouch_settle():
    global pouch_settle_started, pouch_last_poll
    global pouch_last_count, pouch_stable_reads
    pouch_settle_started = time.time()
    pouch_last_poll = 0.0
    pouch_last_count = None
    pouch_stable_reads = 0
    _set_state(STATE_SETTLING_POUCH,
               'Sehir dogrulandi; teslim sonrasi job pouch guncellenmesi bekleniyor.')


def _poll_pouch_settle(now):
    global pouch_last_poll, pouch_last_count, pouch_stable_reads
    if now - pouch_last_poll < POUCH_SETTLE_INTERVAL:
        return
    pouch_last_poll = now

    count = _read_box_count(False)
    safety = _number(txt_safety, 1, 'Guvenlik siniri')
    if safety is None:
        _fail('Kutu guvenlik siniri gecersiz.')
        return

    if count is not None:
        if count == pouch_last_count:
            pouch_stable_reads += 1
        else:
            pouch_last_count = count
            pouch_stable_reads = 1
        _set_message('Pouch sabitleniyor: %d kutu (%d/%d), gerekli: <%d' % (
            count, pouch_stable_reads, POUCH_STABLE_READS, safety))

        # Yalnizca guvenli dusuk deger kararlı hale gelirse devam et. Yuksek
        # deger stale olabilir; timeout dolana kadar guncellenmesini bekle.
        if count < safety and pouch_stable_reads >= POUCH_STABLE_READS:
            _set_message('Pouch dogrulandi: %d kutu kaldi.' % count, True)
            if QtBind.isChecked(gui, chk_grind_with_job):
                _schedule_action(_start_grinding, 'Botun baslatilmasi hazirlaniyor.')
            else:
                _schedule_action(_begin_unequip,
                                 'Job iteminin cikarilmasi hazirlaniyor.')
            return

    if now - pouch_settle_started >= POUCH_SETTLE_TIMEOUT:
        if pouch_last_count is None:
            _fail('Teslim sonrasi job pouch %d saniyede okunamadi.' % POUCH_SETTLE_TIMEOUT)
        else:
            _fail('Teslim sonrasi %d kutu kaldi; guvenli kosul <%d saglanmadi.' % (
                pouch_last_count, safety))


def _begin_unequip():
    identity = _job_identity()
    item = _find_job(identity)
    if not item or int(item.get('slot', -1)) != 8:
        _start_grinding()
        return
    destination = _empty_inventory_slot()
    if destination < 0:
        _fail('Job itemi cikarilamadi: envanterde bos slot yok.')
        return
    _move_item(8, destination)
    _set_state(STATE_UNEQUIPPING, 'Job itemi cikariliyor.')


def _start_grinding():
    global cycle_active, trade_profile_active
    if trade_profile_active:
        farm_profile = _selected_phbot_profile(cmb_farm_profile)
        if not _apply_phbot_profile(farm_profile, 'Farm'):
            _fail('Farm profiline donulemedi; bot guvenlik icin baslatilmadi.')
            return
        trade_profile_active = False
    try:
        result = start_bot()
    except Exception as ex:
        _fail('Bot baslatilamadi: %s' % ex)
        return
    if result is False:
        _fail('phBot botu baslatmayi reddetti.')
        return
    cycle_active = False
    _set_state(STATE_IDLE, 'Kervan tamamlandi; bot bir kez baslatildi.')
    _sync_reset('Trade completed; farm profile active.')


def _send_respawn_request(now=None):
    """Olum ekranindaki sehirde yeniden dogma secenegini sunucuya gonderir."""
    global respawn_attempts, last_respawn_request
    if now is None:
        now = time.time()
    if respawn_attempts >= RESPAWN_MAX_ATTEMPTS:
        return False
    try:
        inject_joymax(0x3053, b'\x01', False)
    except Exception as ex:
        _fail('Sehirde yeniden dogma istegi gonderilemedi: %s' % ex)
        return False
    respawn_attempts += 1
    last_respawn_request = now
    _set_message('Sehirde yeniden dogma istegi gonderildi (%d/%d).' % (
        respawn_attempts, RESPAWN_MAX_ATTEMPTS), True)
    return True


def FSroRAutoTrade_settled(arguments):
    global trade_settled_received, pending_transport_death_time
    if not cycle_active or state != STATE_RUNNING_TRADE:
        log('[%s] Teslimat komutu aktif kervan disinda yok sayildi.' % pName)
        return 0
    trade_settled_received = True
    if pending_transport_death_time > 0:
        pending_transport_death_time = 0.0
        _set_message('Trade teslim edildi; bekleyen pet termination eventi yok sayildi.', True)
    else:
        _set_message('Trade teslimat komutu alindi.', True)
    return 0


def FSroRAutoTrade_complete(arguments):
    global trade_command_received, trade_complete_time
    if not cycle_active or state != STATE_RUNNING_TRADE:
        log('[%s] Tamamlama komutu aktif kervan disinda yok sayildi.' % pName)
        return 0
    trade_command_received = True
    trade_complete_time = time.time()
    _set_message('Kervan tamamlama komutu alindi; sehir kontrol ediliyor.', True)
    _try_finish_trade()
    return 0


def teleported():
    global death_teleport_received, last_teleport_time
    last_teleport_time = time.time()
    if not cycle_active:
        return
    if state == STATE_RETURNING:
        _schedule_action(_begin_party_leave_or_equip,
                         'Sehre varildi; sonraki islem hazirlaniyor.')
    elif state == STATE_DEATH_RECOVERY:
        death_teleport_received = True
        _set_message('Olum sonrasi teleport algilandi; sehir dogrulaniyor.', True)


def joined_game():
    global profile_name
    profile_name = 'default'


def handle_chat(t, player, msg):
    global sync_run_id, sync_phase, sync_phase_since
    if (t != CHAT_PARTY or not player or not msg or
            not msg.startswith(SYNC_PROTOCOL + '|')):
        return False
    parts = msg.split('|', 3)
    if len(parts) < 3:
        return True
    run_id = parts[1]
    command = parts[2].upper()
    argument = parts[3] if len(parts) > 3 else ''
    sender = str(player).lower()
    coordinator = _coordinator_name().lower()
    own = _own_name().lower()

    if not QtBind.isChecked(gui, chk_sync_enabled):
        return True

    if command == 'CHECK':
        if sender != coordinator or cycle_active:
            return True
        try:
            target = int(argument)
        except Exception:
            return True
        if run_id != sync_run_id:
            sync_run_id = run_id
            sync_phase = 'WAIT_START'
        sync_phase_since = time.time()
        ready, reason, count = _local_sync_readiness(target)
        if ready:
            _send_sync('READY', str(count))
            _set_sync_text('READY %d; coordinator command pending' % count, '#1f9d63')
        else:
            _send_sync('WAIT', '%s:%d' % (reason, count))
            _set_sync_text('WAIT: %s' % reason, '#c98a1a')
        return True

    if not sync_run_id or run_id != sync_run_id:
        return True

    if QtBind.isChecked(gui, chk_sync_coordinator):
        if sender not in sync_expected_members:
            return True
        if command == 'READY' and sync_phase == 'WAIT_READY':
            sync_ready_members[sender] = time.time()
            sync_wait_details.pop(sender, None)
            _set_sync_text('Waiting READY: %d/%d' % (
                len(sync_ready_members), len(sync_expected_members)), '#c98a1a')
        elif command == 'WAIT' and sync_phase == 'WAIT_READY':
            sync_ready_members.pop(sender, None)
            sync_wait_details[sender] = argument
            _set_sync_text('%s waiting: %s' % (player, argument), '#c98a1a')
        elif command == 'ACK' and sync_phase == 'WAIT_ACK':
            sync_ack_members.add(sender)
            _set_sync_text('Waiting ACK: %d/%d' % (
                len(sync_ack_members), len(sync_expected_members)), '#c98a1a')
        elif command == 'FAILED':
            _send_sync('ABORT', argument or player)
            _sync_reset('Sync failed: %s' % (argument or player))
        return True

    if sender != coordinator:
        return True
    if command == 'PREPARE' and sync_phase == 'WAIT_START':
        try:
            target = int(argument)
        except Exception:
            return True
        ready, reason, count = _local_sync_readiness(target)
        if ready:
            _send_sync('ACK', str(count))
            _set_sync_text('Final ACK sent; START pending', '#c98a1a')
        else:
            _send_sync('FAILED', '%s:%s' % (_own_name(), reason))
            _set_sync_text('PREPARE rejected: %s' % reason, '#e74c3c')
    elif command == 'START' and sync_phase == 'WAIT_START':
        _sync_start_local()
    elif command == 'ABORT':
        _sync_reset('Sync aborted by coordinator: %s' % argument)
    return True


def handle_event(event_type, data):
    global pending_action, cycle_armed, death_teleport_received
    global pending_transport_death_time, pending_transport_death_region
    global respawn_attempts, last_respawn_request
    if not cycle_active:
        return
    if event_type == EVENT_DIED:
        pending_action = None
        cycle_armed = True
        death_teleport_received = False
        respawn_attempts = 0
        last_respawn_request = 0.0
        pending_transport_death_time = 0.0
        pending_transport_death_region = 0
        _reset_transport_tracking()
        try:
            stop_script()
        except Exception:
            pass
        try:
            stop_bot()
        except Exception:
            pass
        _set_state(STATE_DEATH_RECOVERY,
                   'Karakter oldu; sehirde yeniden dogma hazirlaniyor.')
        try:
            character = get_character_data()
        except Exception:
            character = None
        if character and character.get('dead'):
            _send_respawn_request()
    elif event_type == EVENT_TRANSPORT_DIED:
        pending_transport_death_time = time.time()
        try:
            position = get_position()
            pending_transport_death_region = int(
                position.get('region', 0) or 0) if position else 0
        except Exception:
            pending_transport_death_region = 0
        _set_message('Transport eventi alindi (ID: %s); dogrulama bekleniyor.' % data,
                     True)


def disconnected():
    global trade_profile_active
    if cycle_active:
        _fail('Kervan dongusu sirasinda baglanti kesildi; otomatik devam iptal edildi.')
    trade_profile_active = False
    _sync_reset('Disconnected; sync reset.')


def finished():
    """Plugin reload/kapanisinda yarim kalan otomasyonu guvenli durdurur."""
    if not cycle_active:
        return
    try:
        stop_script()
    except Exception:
        pass
    try:
        stop_bot()
    except Exception:
        pass
    log('[%s] Plugin kapatildi/reload edildi; aktif kervan islemi durduruldu.' % pName)


def btn_check_clicked():
    count = _read_box_count(True)
    if count is not None:
        _set_message('Specialty Goods Box toplam: %d' % count, True)


def btn_status_tab_clicked():
    global status_panel_open
    status_panel_open = not status_panel_open
    if status_panel_open:
        _read_box_count(False)
        for widget, x, y in main_panel_positions:
            QtBind.move(gui, widget, STATUS_OFFSCREEN_X, y)
        for widget, x, y in sync_panel_positions:
            QtBind.move(gui, widget, x, y)
        QtBind.setText(gui, btn_status_tab, _ui('back'))
        _refresh_status_panel()
    else:
        for widget, x, y in sync_panel_positions:
            QtBind.move(gui, widget, STATUS_OFFSCREEN_X, y)
        for widget, x, y in main_panel_positions:
            QtBind.move(gui, widget, x, y)
        QtBind.setText(gui, btn_status_tab, _ui('status'))


def btn_language_clicked():
    global current_language
    current_language = 'tr' if current_language == 'en' else 'en'
    _apply_language()
    if not settings_loading:
        _save_settings(True, False)


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        _set_message('Opening Discord invite...', True)
    except Exception as error:
        log('[%s] Discord link error: %s' % (pName, error))
        _set_message('Could not open Discord invite', False)


def btn_refresh_profiles_clicked():
    farm = _selected_phbot_profile(cmb_farm_profile)
    trade = _selected_phbot_profile(cmb_trade_profile)
    if _refresh_profiles(farm, trade):
        _set_sync_text('%d phBot profiles found.' % len(profile_candidates), '#1f9d63')
    else:
        _set_sync_text('No phBot profiles found for this character.', '#e74c3c')


def btn_refresh_jobs_clicked():
    current = _selected_job() or {}
    if _refresh_jobs(current.get('servername', ''), current.get('model', 0)):
        _set_message('%d job itemi bulundu.' % len(job_candidates), True)
    else:
        _set_message('OUTFIT/job itemi bulunamadi.', True)


def btn_refresh_scripts_clicked():
    current = _selected_script_name()
    if _refresh_scripts(current):
        _set_message('%d script bulundu.' % len(script_candidates), True)
    else:
        _set_message('Script bulunamadi: %s' % _scripts_directory(), True)


def btn_save_clicked():
    _save_settings(False)


def btn_manual_clicked():
    _begin_cycle(True)


def btn_abort_clicked():
    global cycle_active, cycle_armed, pending_action, pending_transport_death_time
    global trade_profile_active
    if sync_run_id and QtBind.isChecked(gui, chk_sync_coordinator):
        _send_sync('ABORT', 'USER_ABORT')
    cycle_active = False
    cycle_armed = False
    pending_action = None
    pending_transport_death_time = 0.0
    try:
        stop_script()
    except Exception:
        pass
    if trade_profile_active:
        if _apply_phbot_profile(_selected_phbot_profile(cmb_farm_profile), 'Farm'):
            trade_profile_active = False
    _sync_reset('Sync aborted by user.')
    _set_state(STATE_IDLE, 'Aktif islem kullanici tarafindan iptal edildi; bot baslatilmadi.')


def chk_enabled_changed(checked):
    if settings_loading:
        return
    if not checked and cycle_active:
        btn_abort_clicked()
    _save_settings(True)
    _set_message('Plugin %s.' % ('aktif' if checked else 'pasif'), True)


def chk_grind_with_job_changed(checked):
    if not settings_loading:
        _save_settings(True)


def chk_sync_enabled_changed(checked):
    if settings_loading:
        return
    if not checked:
        if sync_run_id and QtBind.isChecked(gui, chk_sync_coordinator):
            _send_sync('ABORT', 'SYNC_DISABLED')
        _sync_reset('Party synchronization disabled.')
    _save_settings(True)


def chk_sync_coordinator_changed(checked):
    if settings_loading:
        return
    if checked:
        QtBind.setText(gui, txt_sync_coordinator, _own_name())
    _sync_reset('Coordinator setting changed.')
    _save_settings(True)


def _poll_state(now):
    global last_action, pending_action
    global respawn_attempts, last_respawn_request
    elapsed = now - state_since
    identity = _job_identity()

    if state == STATE_WAITING_ACTION:
        if elapsed >= _action_delay_seconds():
            action = pending_action
            pending_action = None
            if action:
                action()
            else:
                _fail('Bekleyen komut bulunamadi.')
    elif state == STATE_RETURNING:
        if elapsed > RETURN_TIMEOUT:
            _fail('Sehre donus zaman asimina ugradi.')
    elif state == STATE_LEAVING_PARTY:
        try:
            party = get_party()
        except Exception:
            party = None
        if not party:
            _schedule_action(_begin_equip, 'Partyden cikildi; job itemi hazirlaniyor.')
        elif elapsed > PARTY_TIMEOUT:
            _fail('Partyden cikis zaman asimina ugradi.')
        elif now - last_action >= max(ACTION_RETRY_SECONDS, _action_delay_seconds()):
            last_action = now
            inject_joymax(0x7061, b'', False)
    elif state == STATE_EQUIPPING:
        item = _find_job(identity)
        if item and int(item.get('slot', -1)) == 8:
            _schedule_action(_start_trade_script,
                             'Job itemi giyildi; kervan scripti hazirlaniyor.')
        elif elapsed > EQUIP_TIMEOUT:
            _fail('Job itemi giyme zaman asimina ugradi.')
    elif state == STATE_RUNNING_TRADE:
        if trade_command_received:
            _try_finish_trade()
        elif elapsed > TRADE_TIMEOUT:
            _fail('Kervan scripti zaman asimina ugradi.')
    elif state == STATE_SETTLING_POUCH:
        _poll_pouch_settle(now)
    elif state == STATE_DEATH_RECOVERY:
        if elapsed > DEATH_RECOVERY_TIMEOUT:
            _fail('Olum sonrasi sehre donus %d saniyede tamamlanmadi.' %
                  DEATH_RECOVERY_TIMEOUT)
            return
        try:
            character = get_character_data()
        except Exception:
            character = None
        if not character:
            return
        if character.get('dead'):
            if (respawn_attempts < RESPAWN_MAX_ATTEMPTS and
                    now - last_respawn_request >= RESPAWN_RETRY_SECONDS):
                _send_respawn_request(now)
                return
            if (respawn_attempts >= RESPAWN_MAX_ATTEMPTS and
                    now - last_respawn_request >= RESPAWN_FINAL_WAIT_SECONDS):
                _fail('Sehirde yeniden dogma basarisiz: %d deneme cevapsiz kaldi.' %
                      RESPAWN_MAX_ATTEMPTS)
            return
        if not death_teleport_received or not _is_in_town():
            return
        _set_message('Karakter sehirde ve canli; kasilma duzeni hazirlaniyor.', True)
        if QtBind.isChecked(gui, chk_grind_with_job):
            _schedule_action(_start_grinding,
                             'Olum sonrasi sehir dogrulandi; bot hazirlaniyor.')
        else:
            _schedule_action(_begin_unequip,
                             'Olum sonrasi sehir dogrulandi; job itemi kontrol ediliyor.')
    elif state == STATE_UNEQUIPPING:
        item = _find_job(identity)
        if not item or int(item.get('slot', -1)) != 8:
            _schedule_action(_start_grinding,
                             'Job itemi cikarildi; bot hazirlaniyor.')
        elif elapsed > EQUIP_TIMEOUT:
            _fail('Job itemi cikarma zaman asimina ugradi.')


def event_loop():
    global last_poll, cycle_armed, profile_name, training_inside_streak
    now = time.time()
    if now - last_poll < POLL_SECONDS:
        return
    last_poll = now

    current_profile = _character_name()
    if current_profile != profile_name:
        _load_profile()

    _refresh_status_panel()
    if cycle_active and state == STATE_RUNNING_TRADE:
        _poll_transport_load(now)
    _confirm_pending_transport_death(now)

    if cycle_active:
        _poll_state(now)
        return

    if not QtBind.isChecked(gui, chk_enabled):
        training_inside_streak = 0
        _set_training_text('Plugin pasif.')
        return

    training_ready = _update_training_status()

    if state == STATE_ERROR:
        if not training_ready:
            return
        _recover_error_at_training()

    count = _read_box_count(False)
    if count is None:
        return
    target = _number(txt_target, 1, 'Kervan hedefi')
    if target is None:
        return
    if count < target:
        cycle_armed = True
    if QtBind.isChecked(gui, chk_sync_enabled):
        _poll_sync(now, target, training_ready)
        return
    if training_ready and cycle_armed and count >= target:
        _begin_cycle(False)


_ensure_directories()
_refresh_jobs()
_refresh_scripts()
_load_profile()
log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
