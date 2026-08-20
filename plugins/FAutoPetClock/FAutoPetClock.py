from phBot import *
import QtBind

import json
import os
import re
import struct
import time
import webbrowser


pName = 'FAutoPetClock'
pVersion = '1.4.1'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

COLOR_PRIMARY = '#5b57e0'
# Balanced blue-violet chosen instead of near-black so text remains visible on
# both phBot's Light and Dark themes.
COLOR_TEXT = '#6976c9'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#d93a4d'

DEFAULT_SETTINGS = {
    'automatic_monitoring': False,
    'revive_expired_pets': True,
    'prioritize_expired_pets': True,
    'extend_near_expiry': False,
    'detect_expired_by_summon': True,
    'enable_custom_pets': False,
    'custom_pet_patterns': [],
    'near_expiry_hours': 6,
    'scan_interval_seconds': 10,
    'clock_priority': 'Shortest duration first'
}

RESPONSE_TIMEOUT_SECONDS = 10.0
VERIFY_TIMEOUT_SECONDS = 12.0
FAILED_TARGET_COOLDOWN_SECONDS = 60.0
MIN_SCAN_INTERVAL_SECONDS = 2
MAX_SCAN_INTERVAL_SECONDS = 300
MIN_THRESHOLD_HOURS = 1
MAX_THRESHOLD_HOURS = 23
MAX_ACTIVITY_LINES = 60
OFFSCREEN_X = 3000
SUMMON_TEST_TIMEOUT_SECONDS = 9.0
UNSUMMON_TIMEOUT_SECONDS = 9.0
MAX_SUMMON_TEST_ATTEMPTS = 2
# Pick Pet summon item-use TID observed on locale 22:
# client 0x704C = [inventory slot] CD 10.
DEFAULT_PICK_PET_SUMMON_TAIL = b'\xCD\x10'
# Manually verified locale 22 Clock item-use TID: ED 66 on the wire.
LOCALE22_CLOCK_USE_TID = 0x66ED

settings = dict(DEFAULT_SETTINGS)
settings_loading = False
settings_loaded_for = None
paused = False
last_scan_time = 0.0
pending_operation = None
failed_targets = {}
last_snapshot = {'pets': [], 'clocks': []}
activity_lines = []
custom_pet_patterns = []
summon_test = None
summon_test_states = {}
clock_verification_targets = set()


def fixed_width_text(content, width):
    return (
        '<table width="{0}" cellspacing="0" cellpadding="0">'
        '<tr><td>{1}</td></tr></table>'
    ).format(width, content)


def html_escape(value):
    return (str(value).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def packet_hex(data):
    return ' '.join('%02X' % value for value in bytes(data or b''))


gui = QtBind.init(__name__, pName)

QtBind.createLabel(
    gui, u'<font color="%s" size="4"><b>⏱ %s</b></font>' %
    (COLOR_PRIMARY, pName), 12, 6)
QtBind.createLabel(
    gui, '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion), 205, 12)
btn_discord = QtBind.createButton(
    gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(
    gui, u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' %
    COLOR_PRIMARY, 565, 11)
QtBind.createLineEdit(gui, '', 12, 30, 716, 1)

QtBind.createLabel(
    gui, '<font color="%s"><b>AUTOMATION SETTINGS</b></font>' % COLOR_PRIMARY,
    12, 42)
chk_monitor = QtBind.createCheckBox(
    gui, 'monitor_changed', 'Enable automatic monitoring', 12, 65)
chk_revive = QtBind.createCheckBox(
    gui, 'setting_changed', 'Revive expired Pick Pets', 12, 88)
chk_expired_first = QtBind.createCheckBox(
    gui, 'setting_changed', 'Prioritize expired Pets first', 175, 88)
chk_extend = QtBind.createCheckBox(
    gui, 'setting_changed', 'Extend pets near expiration', 12, 111)
chk_summon_test = QtBind.createCheckBox(
    gui, 'setting_changed', 'Verify dead Pets by summon test', 190, 111)

QtBind.createLabel(gui, '<font color="%s">Near-expiry threshold</font>' %
                   COLOR_TEXT, 12, 142)
txt_threshold = QtBind.createLineEdit(gui, '6', 150, 137, 55, 22)
QtBind.createLabel(gui, '<font color="%s">hours</font>' % COLOR_MUTED, 210, 142)

QtBind.createLabel(gui, '<font color="%s">Inventory scan every</font>' %
                   COLOR_TEXT, 12, 171)
txt_scan_interval = QtBind.createLineEdit(gui, '10', 150, 166, 55, 22)
QtBind.createLabel(gui, '<font color="%s">sec</font>' % COLOR_MUTED, 210, 171)

QtBind.createLabel(gui, '<font color="%s">Clock priority</font>' % COLOR_TEXT,
                   12, 200)
cmb_priority = QtBind.createCombobox(gui, 110, 195, 220, 22)
QtBind.append(gui, cmb_priority, 'Shortest duration first')
QtBind.append(gui, cmb_priority, 'Longest duration first')
QtBind.append(gui, cmb_priority, 'Inventory slot order')

btn_save = QtBind.createButton(gui, 'save_clicked', 'Save Settings', 12, 229)
btn_scan = QtBind.createButton(
    gui, 'test_pets_clicked', 'Test Pets Now', 112, 229)
btn_pause = QtBind.createButton(gui, 'pause_clicked', 'Pause', 218, 229)
btn_custom_pets = QtBind.createButton(
    gui, 'show_custom_pets_clicked', 'Custom Pets', 278, 229)

QtBind.createLineEdit(gui, '', 370, 42, 1, 208)
QtBind.createLabel(
    gui, '<font color="%s"><b>LIVE STATUS</b></font>' % COLOR_PRIMARY,
    390, 42)

QtBind.createLabel(gui, '<font color="%s"><b>Status</b></font>' % COLOR_MUTED,
                   390, 68)
lbl_status = QtBind.createLabel(
    gui,
    fixed_width_text('<font color="%s"><b>WAITING FOR CHARACTER</b></font>' %
                     COLOR_WARNING, 235),
    480, 68)
QtBind.createLabel(gui, '<font color="%s"><b>Pick Pets</b></font>' % COLOR_MUTED,
                   390, 96)
lbl_pet_count = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s">0 detected</font>' % COLOR_TEXT, 235),
    480, 96)
QtBind.createLabel(gui, '<font color="%s"><b>Expired</b></font>' % COLOR_MUTED,
                   390, 124)
lbl_expired_count = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s">0 waiting</font>' % COLOR_TEXT, 235),
    480, 124)
QtBind.createLabel(gui, '<font color="%s"><b>Clocks</b></font>' % COLOR_MUTED,
                   390, 152)
lbl_clock_count = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s">0 available</font>' % COLOR_TEXT, 235),
    480, 152)
QtBind.createLabel(gui, '<font color="%s"><b>Current</b></font>' % COLOR_MUTED,
                   390, 180)
lbl_current = QtBind.createLabel(
    gui,
    fixed_width_text('<font color="%s">No active operation</font>' %
                     COLOR_TEXT, 235),
    480, 180)
QtBind.createLabel(gui, '<font color="%s"><b>Last scan</b></font>' % COLOR_MUTED,
                   390, 208)
lbl_last_scan = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s">Not scanned yet</font>' % COLOR_TEXT,
                          235),
    480, 208)

QtBind.createLineEdit(gui, '', 12, 258, 716, 1)
QtBind.createLabel(
    gui, '<font color="%s"><b>PICK PET INVENTORY</b></font>' % COLOR_PRIMARY,
    12, 268)
QtBind.createLabel(
    gui, '<font color="%s"><b>RECENT ACTIVITY</b></font>' % COLOR_PRIMARY,
    382, 268)
lst_pets = QtBind.createList(gui, 12, 290, 350, 135)
lst_activity = QtBind.createList(gui, 382, 290, 346, 135)

# Custom-pet configuration is a separate overlay page so the primary monitoring
# screen stays readable in phBot's fixed-width plugin area.
custom_background = QtBind.createList(gui, OFFSCREEN_X, 38, 716, 387)
custom_title = QtBind.createLabel(
    gui, '<font color="%s"><b>CUSTOM PICK PETS</b></font>' % COLOR_PRIMARY,
    OFFSCREEN_X, 50)
custom_back = QtBind.createButton(
    gui, 'hide_custom_pets_clicked', 'Back', OFFSCREEN_X, 46)
chk_custom_pets = QtBind.createCheckBox(
    gui, 'setting_changed', 'Enable custom Pick Pets', OFFSCREEN_X, 80)
custom_help = QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s">Use an exact servername (safest), or * for a verified family.</font>' %
        COLOR_TEXT, 680),
    OFFSCREEN_X, 108)
custom_example = QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s">Example: ITEM_HELL_GRAB_BATMAN_SCROLL or ITEM_HELL_GRAB_*_SCROLL</font>' %
        COLOR_MUTED, 680),
    OFFSCREEN_X, 132)
txt_custom_pattern = QtBind.createLineEdit(gui, '', OFFSCREEN_X, 158, 430, 22)
btn_add_custom = QtBind.createButton(
    gui, 'add_custom_pattern_clicked', 'Add Pattern', OFFSCREEN_X, 157)
btn_remove_custom = QtBind.createButton(
    gui, 'remove_custom_pattern_clicked', 'Remove Selected', OFFSCREEN_X, 157)
lst_custom_patterns = QtBind.createList(gui, OFFSCREEN_X, 194, 680, 150)
custom_status = QtBind.createLabel(
    gui,
    fixed_width_text('<font color="%s">Custom pet support is disabled.</font>' %
                     COLOR_MUTED, 680),
    OFFSCREEN_X, 360)
custom_save = QtBind.createButton(
    gui, 'save_clicked', 'Save Settings', OFFSCREEN_X, 390)

CUSTOM_PANEL_LAYOUT = (
    (custom_background, 12, 38),
    (custom_title, 24, 50),
    (custom_back, 665, 46),
    (chk_custom_pets, 24, 80),
    (custom_help, 24, 108),
    (custom_example, 24, 132),
    (txt_custom_pattern, 24, 158),
    (btn_add_custom, 470, 157),
    (btn_remove_custom, 565, 157),
    (lst_custom_patterns, 24, 194),
    (custom_status, 24, 360),
    (custom_save, 24, 390)
)


def plugin_log(message):
    log('[%s] %s' % (pName, message))


def set_status(message, color=COLOR_MUTED):
    QtBind.setText(
        gui, lbl_status,
        fixed_width_text(
            '<font color="%s"><b>%s</b></font>' %
            (color, html_escape(message)), 235))


def set_current(message, color=COLOR_TEXT):
    QtBind.setText(
        gui, lbl_current,
        fixed_width_text('<font color="%s">%s</font>' %
                         (color, html_escape(message)), 235))


def set_custom_status(message, color=COLOR_MUTED):
    QtBind.setText(
        gui, custom_status,
        fixed_width_text('<font color="%s">%s</font>' %
                         (color, html_escape(message)), 680))


def refresh_custom_pattern_list():
    QtBind.clear(gui, lst_custom_patterns)
    if not custom_pet_patterns:
        QtBind.append(gui, lst_custom_patterns, 'No custom patterns configured.')
    else:
        for pattern in custom_pet_patterns:
            QtBind.append(gui, lst_custom_patterns, pattern)
    if settings.get('enable_custom_pets', False):
        set_custom_status('%d custom pattern(s) enabled.' %
                          len(custom_pet_patterns), COLOR_SUCCESS)
    else:
        set_custom_status('Custom pet support is disabled.', COLOR_MUTED)


def add_activity(message):
    timestamp = time.strftime('%H:%M:%S')
    line = '[%s] %s' % (timestamp, message)
    activity_lines.append(line)
    if len(activity_lines) > MAX_ACTIVITY_LINES:
        del activity_lines[:-MAX_ACTIVITY_LINES]
    QtBind.clear(gui, lst_activity)
    for entry in activity_lines:
        QtBind.append(gui, lst_activity, entry)
    plugin_log(message)


def clamp_int(value, default, minimum, maximum):
    try:
        value = int(str(value).strip())
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def get_character_key():
    try:
        character = get_character_data() or {}
    except Exception:
        return None
    server = str(character.get('server') or '').strip()
    name = str(character.get('name') or '').strip()
    if not server or not name:
        return None
    return server, name


def safe_filename(value):
    return re.sub(r'[<>:"/\\|?*]', '_', str(value))


def get_settings_path(character_key=None):
    if character_key is None:
        character_key = get_character_key()
    if not character_key:
        return None
    folder = os.path.join(get_config_dir(), pName)
    filename = safe_filename('%s_%s.json' % character_key)
    return os.path.join(folder, filename)


def read_gui_settings():
    selected_priority = str(QtBind.text(gui, cmb_priority) or '').strip()
    priorities = (
        'Shortest duration first',
        'Longest duration first',
        'Inventory slot order'
    )
    if selected_priority not in priorities:
        selected_priority = DEFAULT_SETTINGS['clock_priority']
    return {
        'automatic_monitoring': bool(QtBind.isChecked(gui, chk_monitor)),
        'revive_expired_pets': bool(QtBind.isChecked(gui, chk_revive)),
        'prioritize_expired_pets': bool(
            QtBind.isChecked(gui, chk_expired_first)),
        'extend_near_expiry': bool(QtBind.isChecked(gui, chk_extend)),
        'detect_expired_by_summon': bool(
            QtBind.isChecked(gui, chk_summon_test)),
        'enable_custom_pets': bool(QtBind.isChecked(gui, chk_custom_pets)),
        'custom_pet_patterns': list(custom_pet_patterns),
        'near_expiry_hours': clamp_int(
            QtBind.text(gui, txt_threshold),
            DEFAULT_SETTINGS['near_expiry_hours'],
            MIN_THRESHOLD_HOURS, MAX_THRESHOLD_HOURS),
        'scan_interval_seconds': clamp_int(
            QtBind.text(gui, txt_scan_interval),
            DEFAULT_SETTINGS['scan_interval_seconds'],
            MIN_SCAN_INTERVAL_SECONDS, MAX_SCAN_INTERVAL_SECONDS),
        'clock_priority': selected_priority
    }


def apply_settings_to_gui():
    global settings_loading
    settings_loading = True
    try:
        QtBind.setChecked(gui, chk_monitor, settings['automatic_monitoring'])
        QtBind.setChecked(gui, chk_revive, settings['revive_expired_pets'])
        QtBind.setChecked(
            gui, chk_expired_first, settings['prioritize_expired_pets'])
        QtBind.setChecked(gui, chk_extend, settings['extend_near_expiry'])
        QtBind.setChecked(
            gui, chk_summon_test, settings['detect_expired_by_summon'])
        QtBind.setChecked(gui, chk_custom_pets, settings['enable_custom_pets'])
        QtBind.setText(gui, txt_threshold, str(settings['near_expiry_hours']))
        QtBind.setText(gui, txt_scan_interval,
                       str(settings['scan_interval_seconds']))
        QtBind.setText(gui, cmb_priority, settings['clock_priority'])
    finally:
        settings_loading = False


def load_settings(character_key):
    global settings, settings_loaded_for, paused, custom_pet_patterns
    global summon_test
    failed_targets.clear()
    clock_verification_targets.clear()
    settings = dict(DEFAULT_SETTINGS)
    path = get_settings_path(character_key)
    try:
        if path and os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as settings_file:
                loaded = json.load(settings_file)
            if not isinstance(loaded, dict):
                raise ValueError('settings root must be an object')
            for key in DEFAULT_SETTINGS:
                if key in loaded:
                    settings[key] = loaded[key]
        settings['automatic_monitoring'] = bool(settings['automatic_monitoring'])
        settings['revive_expired_pets'] = bool(settings['revive_expired_pets'])
        settings['prioritize_expired_pets'] = bool(
            settings['prioritize_expired_pets'])
        settings['extend_near_expiry'] = bool(settings['extend_near_expiry'])
        settings['detect_expired_by_summon'] = bool(
            settings['detect_expired_by_summon'])
        settings['enable_custom_pets'] = bool(settings['enable_custom_pets'])
        loaded_patterns = settings.get('custom_pet_patterns') or []
        if not isinstance(loaded_patterns, list):
            loaded_patterns = []
        custom_pet_patterns = []
        for value in loaded_patterns:
            pattern = normalize_custom_pattern(value)
            if pattern and pattern not in custom_pet_patterns:
                custom_pet_patterns.append(pattern)
        settings['custom_pet_patterns'] = list(custom_pet_patterns)
        settings['near_expiry_hours'] = clamp_int(
            settings['near_expiry_hours'], DEFAULT_SETTINGS['near_expiry_hours'],
            MIN_THRESHOLD_HOURS, MAX_THRESHOLD_HOURS)
        settings['scan_interval_seconds'] = clamp_int(
            settings['scan_interval_seconds'],
            DEFAULT_SETTINGS['scan_interval_seconds'],
            MIN_SCAN_INTERVAL_SECONDS, MAX_SCAN_INTERVAL_SECONDS)
        if settings['clock_priority'] not in (
                'Shortest duration first', 'Longest duration first',
                'Inventory slot order'):
            settings['clock_priority'] = DEFAULT_SETTINGS['clock_priority']
        settings_loaded_for = character_key
        summon_test = None
        summon_test_states.clear()
        paused = False
        QtBind.setText(gui, btn_pause, 'Pause')
        apply_settings_to_gui()
        refresh_custom_pattern_list()
        add_activity('Character settings loaded.')
    except (OSError, IOError, ValueError, TypeError) as error:
        settings = dict(DEFAULT_SETTINGS)
        custom_pet_patterns = []
        summon_test = None
        summon_test_states.clear()
        settings_loaded_for = character_key
        apply_settings_to_gui()
        refresh_custom_pattern_list()
        add_activity('Settings could not be loaded; defaults restored: %s' % error)


def save_settings_file():
    global settings
    character_key = get_character_key()
    path = get_settings_path(character_key)
    if not path:
        set_status('JOIN THE GAME BEFORE SAVING', COLOR_WARNING)
        return False
    settings = read_gui_settings()
    folder = os.path.dirname(path)
    temp_path = path + '.tmp'
    try:
        if not os.path.isdir(folder):
            os.makedirs(folder)
        with open(temp_path, 'w', encoding='utf-8') as settings_file:
            json.dump(settings, settings_file, ensure_ascii=False, indent=2,
                      sort_keys=True)
            settings_file.write('\n')
        os.replace(temp_path, path)
        add_activity('Settings saved for %s.' % character_key[1])
        return True
    except (OSError, IOError, ValueError, TypeError) as error:
        set_status('SETTINGS COULD NOT BE SAVED', COLOR_ERROR)
        plugin_log('Settings save error: %s' % error)
        return False


def normalize_custom_pattern(value):
    pattern = str(value or '').strip().upper()
    if not pattern or len(pattern) > 160:
        return ''
    if not pattern.startswith('ITEM_') or 'SCROLL' not in pattern:
        return ''
    if not re.match(r'^[A-Z0-9_*]+$', pattern):
        return ''
    return pattern


def custom_pattern_matches(servername, pattern):
    expression = '^%s$' % re.escape(pattern).replace(r'\*', '.*')
    return re.match(expression, servername, re.IGNORECASE) is not None


def is_configured_custom_pet_servername(servername):
    if not settings.get('enable_custom_pets', False):
        return False
    candidates = [str(servername or '').upper()]
    if candidates[0] and not candidates[0].endswith('_SCROLL'):
        candidates.append(candidates[0] + '_SCROLL')
    return any(custom_pattern_matches(candidate, pattern)
               for candidate in candidates
               for pattern in custom_pet_patterns)


def is_pick_pet_scroll(item):
    servername = str(item.get('servername') or '').upper()
    standard_pet = ('COS_P_' in servername and 'SCROLL' in servername
                    and 'COS_P_EXTENSION' not in servername)
    if standard_pet:
        return True
    if not settings.get('enable_custom_pets', False):
        return False
    return is_configured_custom_pet_servername(servername)


def is_reincarnation_clock(item):
    servername = str(item.get('servername') or '').upper()
    return servername.startswith('ITEM_COS_P_EXTENSION')


def pick_pet_server_key(servername):
    """Normalize active-pet and summon-scroll server names for comparison."""
    servername = str(servername or '').upper()
    if not servername or 'COS_P_EXTENSION' in servername:
        return ''
    marker = 'COS_P_'
    marker_index = servername.find(marker)
    if marker_index >= 0:
        key = servername[marker_index + len(marker):]
    else:
        key = servername
        if key.startswith('ITEM_'):
            key = key[5:]
    scroll_index = key.find('_SCROLL')
    if scroll_index >= 0:
        key = key[:scroll_index]
    return key.strip('_')


def pet_keys_match(left, right):
    if not left or not right:
        return False
    return (left == right or left.startswith(right + '_')
            or right.startswith(left + '_')
            or left.endswith('_' + right)
            or right.endswith('_' + left))


def expiration_value(item):
    try:
        return int(item.get('expiration'))
    except (TypeError, ValueError, AttributeError):
        return None


def clock_duration_days(item):
    servername = str(item.get('servername') or '').upper()
    match = re.search(r'_(\d+)D(?:$|_)', servername)
    if match:
        try:
            return int(match.group(1))
        except (TypeError, ValueError):
            pass
    return 9999


def target_key(item):
    return '%s|%s|%s' % (
        item.get('slot'), item.get('model'), item.get('servername'))


def summon_tail_for(item):
    if not item or not is_pick_pet_scroll(item):
        return None
    return DEFAULT_PICK_PET_SUMMON_TAIL


def active_pick_pets():
    result = []
    try:
        for pet_id, pet in (get_pets() or {}).items():
            if not pet:
                continue
            servername = str(pet.get('servername') or '').upper()
            if (pet.get('type') == 'pick' or 'COS_P_' in servername
                    or is_configured_custom_pet_servername(servername)):
                entry = dict(pet)
                entry['id'] = int(pet_id)
                result.append(entry)
    except Exception as error:
        plugin_log('Active Pick Pet inspection error: %s' % error)
    return result


def active_pet_matches_item(pet, item):
    return pet_keys_match(
        pick_pet_server_key(pet.get('servername')),
        pick_pet_server_key(item.get('servername')))


def inject_pet_summon(item):
    slot = int(item['slot'])
    tail = summon_tail_for(item)
    if slot < 0 or slot > 255 or not tail:
        return False
    inject_joymax(0x704C, struct.pack('<B', slot) + tail, True)
    return True


def inject_pet_unsummon(pet):
    inject_joymax(0x7116, struct.pack('<I', int(pet['id'])), False)


def find_matching_inventory_pet(reference, pets=None):
    if pets is None:
        pets, unused_clocks = scan_inventory()
    exact = [item for item in pets
             if item.get('model') == reference.get('model')
             and item.get('servername') == reference.get('servername')]
    for item in exact:
        if item.get('slot') == reference.get('slot'):
            return item
    return exact[0] if exact else None


def finish_summon_test(message, failed=False):
    global summon_test, last_scan_time, paused
    manual_only = bool(summon_test and summon_test.get('manual_only'))
    add_activity(message)
    summon_test = None
    last_scan_time = 0.0
    set_current('No active operation')
    if failed:
        paused = True
        QtBind.setText(gui, btn_pause, 'Resume')
        set_status('PAUSED AFTER TEST FAILURE', COLOR_ERROR)
        add_activity('Automatic processing paused for safety.')
    elif manual_only:
        paused = True
        QtBind.setText(gui, btn_pause, 'Resume')
        pets, clocks = scan_inventory()
        refresh_snapshot_gui(pets, clocks)
        alive = sum(1 for item in pets
                    if summon_test_states.get(target_key(item)) == 'alive')
        dead = sum(1 for item in pets
                   if summon_test_states.get(target_key(item)) == 'dead')
        set_status('PET TEST COMPLETE', COLOR_SUCCESS)
        set_current('Alive %d | Expired %d' % (alive, dead), COLOR_SUCCESS)
        add_activity(
            'Pet test result: %d alive, %d expired. No Clock was used.' %
            (alive, dead))
    else:
        set_status('MONITORING', COLOR_SUCCESS)


def restore_original_pet_or_finish():
    global summon_test
    original = summon_test.get('original') if summon_test else None
    if not original:
        finish_summon_test(
            'Summon verification cycle completed.',
            bool(summon_test and summon_test.get('failure_after_restore')))
        return
    pets, unused_clocks = scan_inventory()
    item = find_matching_inventory_pet(original, pets)
    if not item or not inject_pet_summon(item):
        finish_summon_test(
            'Could not restore the Pick Pet that was active before testing.',
            True)
        return
    summon_test['phase'] = 'waiting-restore'
    summon_test['current'] = dict(item)
    summon_test['deadline'] = time.time() + SUMMON_TEST_TIMEOUT_SECONDS
    set_status('RESTORING ORIGINAL PET', COLOR_WARNING)
    set_current(item.get('name') or item.get('servername'), COLOR_WARNING)
    add_activity('Restoring the previously active Pick Pet from slot %d.' %
                 item['slot'])


def start_next_summon_test():
    global summon_test
    while summon_test and summon_test['queue']:
        item = summon_test['queue'].pop(0)
        if target_key(item) in summon_test_states:
            continue
        if not inject_pet_summon(item):
            add_activity('Skipped %s: summon request could not be built.' %
                         (item.get('name') or item.get('servername')))
            continue
        summon_test['current'] = dict(item)
        summon_test['attempt'] = 1
        summon_test['phase'] = 'waiting-summon'
        summon_test['deadline'] = time.time() + SUMMON_TEST_TIMEOUT_SECONDS
        set_status('TESTING PET', COLOR_WARNING)
        set_current('%s (attempt 1/%d)' %
                    (item.get('name') or item.get('servername'),
                     MAX_SUMMON_TEST_ATTEMPTS), COLOR_WARNING)
        add_activity('Summon-testing %s from slot %d (attempt 1/%d).' %
                     (item.get('name') or item.get('servername'), item['slot'],
                      MAX_SUMMON_TEST_ATTEMPTS))
        return
    restore_original_pet_or_finish()


def begin_summon_test_cycle(pets, manual_only=False):
    global summon_test
    candidates = [dict(item) for item in pets
                  if target_key(item) not in summon_test_states
                  and summon_tail_for(item)]
    if not candidates:
        return False

    active = active_pick_pets()
    if len(active) > 1:
        add_activity('Summon test stopped: multiple active Pick Pets detected.')
        return False

    original = None
    if active:
        matches = [item for item in pets
                   if summon_tail_for(item)
                   if active_pet_matches_item(active[0], item)]
        if not matches:
            add_activity(
                'Summon test stopped: active Pick Pet cannot be restored safely.')
            return False
        original = dict(matches[0])
        summon_test_states[target_key(original)] = 'alive'
        candidates = [item for item in candidates
                      if target_key(item) != target_key(original)]

    summon_test = {
        'phase': 'starting',
        'queue': candidates,
        'current': None,
        'attempt': 0,
        'original': original,
        'failure_after_restore': False,
        'manual_only': bool(manual_only),
        'deadline': 0.0
    }
    if active:
        inject_pet_unsummon(active[0])
        summon_test['phase'] = 'waiting-initial-close'
        summon_test['deadline'] = time.time() + UNSUMMON_TIMEOUT_SECONDS
        set_status('CLOSING ACTIVE PET', COLOR_WARNING)
        set_current(active[0].get('name') or 'Active Pick Pet', COLOR_WARNING)
        add_activity('Closing the active Pick Pet before summon verification.')
    else:
        start_next_summon_test()
    return True


def process_summon_test():
    global summon_test
    if not summon_test:
        return
    now = time.time()
    phase = summon_test['phase']
    active = active_pick_pets()

    if phase == 'waiting-initial-close':
        if not active:
            start_next_summon_test()
        elif now > summon_test['deadline']:
            finish_summon_test('Active Pick Pet could not be closed.', True)
        return

    current = summon_test.get('current')
    matching = [pet for pet in active
                if current and active_pet_matches_item(pet, current)]
    if phase == 'waiting-summon':
        if matching:
            summon_test_states[target_key(current)] = 'alive'
            clock_verification_targets.discard(target_key(current))
            add_activity('%s is alive; summon test succeeded.' %
                         (current.get('name') or current.get('servername')))
            inject_pet_unsummon(matching[0])
            summon_test['phase'] = 'waiting-test-close'
            summon_test['deadline'] = now + UNSUMMON_TIMEOUT_SECONDS
            return
        if now <= summon_test['deadline']:
            return
        if summon_test['attempt'] < MAX_SUMMON_TEST_ATTEMPTS:
            summon_test['attempt'] += 1
            if not inject_pet_summon(current):
                finish_summon_test('Pet summon retry could not be sent.', True)
                return
            summon_test['deadline'] = now + SUMMON_TEST_TIMEOUT_SECONDS
            set_current('%s (attempt %d/%d)' %
                        (current.get('name') or current.get('servername'),
                         summon_test['attempt'], MAX_SUMMON_TEST_ATTEMPTS),
                        COLOR_WARNING)
            add_activity('Retrying summon test for %s (attempt %d/%d).' %
                         (current.get('name') or current.get('servername'),
                          summon_test['attempt'], MAX_SUMMON_TEST_ATTEMPTS))
            return
        summon_test_states[target_key(current)] = 'dead'
        add_activity('%s marked expired after %d failed summon attempts.' %
                     (current.get('name') or current.get('servername'),
                      MAX_SUMMON_TEST_ATTEMPTS))
        if target_key(current) in clock_verification_targets:
            clock_verification_targets.discard(target_key(current))
            summon_test['failure_after_restore'] = True
            summon_test['queue'] = []
            add_activity(
                'Clock verification failed; no additional Clock will be used.')
        start_next_summon_test()
        return

    if phase == 'waiting-test-close':
        if not matching:
            start_next_summon_test()
        elif now > summon_test['deadline']:
            finish_summon_test('Tested Pick Pet could not be closed.', True)
        return

    if phase == 'waiting-restore':
        if matching:
            finish_summon_test(
                'Original Pick Pet restored successfully.',
                bool(summon_test.get('failure_after_restore')))
        elif now > summon_test['deadline']:
            finish_summon_test('Original Pick Pet could not be restored.', True)


def scan_inventory():
    inventory = get_inventory() or {}
    items = inventory.get('items') or []
    try:
        first_slot = int(inventory.get('first', 13))
    except (TypeError, ValueError):
        first_slot = 13
    pets = []
    clocks = []
    for slot, item in enumerate(items):
        if slot < first_slot or not isinstance(item, dict) or not item:
            continue
        entry = dict(item)
        entry['slot'] = slot
        if is_reincarnation_clock(item):
            clocks.append(entry)
        elif is_pick_pet_scroll(item):
            pets.append(entry)

    active_pet_keys = []
    try:
        for pet in (get_pets() or {}).values():
            if not pet:
                continue
            servername = str(pet.get('servername') or '').upper()
            pet_key = pick_pet_server_key(servername)
            # Some custom servers expose collection pets as type "none" even
            # though their stable server name still belongs to COS_P_.
            if pet_key and (pet.get('type') == 'pick' or 'COS_P_' in servername
                            or is_configured_custom_pet_servername(servername)):
                active_pet_keys.append(pet_key)
    except Exception as error:
        plugin_log('Active Pick Pet inspection error: %s' % error)

    for item in pets:
        scroll_key = pick_pet_server_key(item.get('servername'))
        item['summoned'] = any(
            pet_keys_match(scroll_key, active_key)
            for active_key in active_pet_keys)
    return pets, clocks


def format_remaining(seconds):
    if seconds is None:
        return 'UNKNOWN'
    if seconds <= 0:
        return 'EXPIRED'
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    if days:
        return '%dd %02dh %02dm' % (days, hours, minutes)
    return '%02dh %02dm' % (hours, minutes)


def refresh_snapshot_gui(pets, clocks):
    if settings.get('detect_expired_by_summon', False):
        expired_count = sum(
            1 for item in pets
            if summon_test_states.get(target_key(item)) == 'dead')
    else:
        expired_count = sum(1 for item in pets
                            if not item.get('summoned')
                            if expiration_value(item) is not None
                            and expiration_value(item) <= 0)
    clock_count = 0
    for item in clocks:
        clock_count += max(1, clamp_int(item.get('quantity'), 1, 1, 999999))
    QtBind.setText(
        gui, lbl_pet_count,
        fixed_width_text('<font color="%s">%d detected</font>' %
                         (COLOR_TEXT, len(pets)), 235))
    QtBind.setText(
        gui, lbl_expired_count,
        fixed_width_text('<font color="%s">%d waiting</font>' %
                         (COLOR_ERROR if expired_count else COLOR_TEXT,
                          expired_count), 235))
    QtBind.setText(
        gui, lbl_clock_count,
        fixed_width_text('<font color="%s">%d available</font>' %
                         (COLOR_SUCCESS if clocks else COLOR_WARNING,
                          clock_count), 235))
    QtBind.setText(
        gui, lbl_last_scan,
        fixed_width_text('<font color="%s">%s</font>' %
                         (COLOR_TEXT, time.strftime('%H:%M:%S')), 235))

    QtBind.clear(gui, lst_pets)
    if not pets:
        QtBind.append(gui, lst_pets, 'No Pick Pet scrolls detected.')
    for item in pets:
        remaining = expiration_value(item)
        tested_state = summon_test_states.get(target_key(item))
        if settings.get('detect_expired_by_summon', False) and tested_state:
            state = 'EXPIRED' if tested_state == 'dead' else 'ALIVE'
        elif settings.get('detect_expired_by_summon', False):
            state = 'UNTESTED'
        elif item.get('summoned'):
            state = 'SUMMONED'
        elif remaining is None:
            state = 'UNKNOWN'
        elif remaining <= 0:
            state = 'EXPIRED'
        else:
            state = 'ACTIVE'
        QtBind.append(
            gui, lst_pets,
            'Slot %d | %s | %s | %s' %
            (item['slot'], item.get('name') or item.get('servername'), state,
             format_remaining(remaining)))


def eligible_targets(pets, now):
    threshold_seconds = int(settings['near_expiry_hours']) * 3600
    expired_targets = []
    near_expiry_targets = []
    for item in pets:
        remaining = expiration_value(item)
        if item.get('summoned'):
            continue
        key = target_key(item)
        retry_at = failed_targets.get(key, 0.0)
        if retry_at > now:
            continue
        verified_dead = (
            settings.get('detect_expired_by_summon', False)
            and summon_test_states.get(key) == 'dead')
        if verified_dead and settings['revive_expired_pets']:
            entry = dict(item)
            entry['reason'] = 'summon-verified-expired'
            expired_targets.append(entry)
        elif settings.get('detect_expired_by_summon', False):
            # In summon-test mode, an unreliable inventory expiration must
            # never override the observed result of an actual summon attempt.
            continue
        elif remaining is None:
            continue
        elif remaining <= 0 and settings['revive_expired_pets']:
            entry = dict(item)
            entry['reason'] = 'expired'
            expired_targets.append(entry)
        elif (remaining > 0 and remaining <= threshold_seconds
              and settings['extend_near_expiry']):
            entry = dict(item)
            entry['reason'] = 'near-expiry'
            near_expiry_targets.append(entry)
    expired_targets.sort(
        key=lambda item: (expiration_value(item), item['slot']))
    near_expiry_targets.sort(
        key=lambda item: (expiration_value(item), item['slot']))
    if settings.get('prioritize_expired_pets', True):
        # Keep the queues physically separate so an active/near-expiry pet can
        # never interleave with the expired-pet revival queue.
        return expired_targets + near_expiry_targets
    return sorted(
        expired_targets + near_expiry_targets,
        key=lambda item: item['slot'])


def select_clock(clocks):
    priority = settings.get('clock_priority')
    if priority == 'Inventory slot order':
        return sorted(clocks, key=lambda item: item['slot'])[0]
    if priority == 'Longest duration first':
        return sorted(
            clocks,
            key=lambda item: (-clock_duration_days(item), item['slot']))[0]
    return sorted(
        clocks,
        key=lambda item: (clock_duration_days(item), item['slot']))[0]


def get_item_use_tid(item):
    item_data = get_item(int(item.get('model', 0) or 0))
    if not item_data:
        return None, None
    tid = (int(bool(item_data.get('cash_item'))) + (3 * 4)
           + (int(item_data.get('tid1', 0)) * 32)
           + (int(item_data.get('tid2', 0)) * 128)
           + (int(item_data.get('tid3', 0)) * 2048))
    return tid, item_data


def build_clock_packet(clock, pet_slot):
    clock_slot = int(clock['slot'])
    locale = int(get_locale())
    if locale == 22:
        # Verified manual vSRO capture:
        # [Clock slot][two-byte item-use TID][Pick Pet scroll slot].
        return (struct.pack(
            '<BHB', clock_slot, LOCALE22_CLOCK_USE_TID, pet_slot),
                LOCALE22_CLOCK_USE_TID)
    if locale == 18:
        tid, item_data = get_item_use_tid(clock)
        if tid is None:
            raise ValueError('static Clock item data is unavailable')
        packet = struct.pack(
            '<BBBBB',
            clock_slot,
            (3 << 4) + int(bool(item_data.get('cash_item'))),
            int(item_data.get('tid1', 0)) * 4,
            int(item_data.get('tid2', 0)),
            int(item_data.get('tid3', 0)))
        return packet + struct.pack('<B', pet_slot), tid
    raise ValueError('unsupported locale for targeted Clock use: %s' % locale)


def start_clock_operation(target, clock):
    global pending_operation
    clock_slot = int(clock['slot'])
    pet_slot = int(target['slot'])
    if clock_slot < 0 or clock_slot > 255 or pet_slot < 0 or pet_slot > 255:
        add_activity('Item slot is outside the one-byte packet range.')
        failed_targets[target_key(target)] = time.time() + FAILED_TARGET_COOLDOWN_SECONDS
        return False

    try:
        packet, use_tid = build_clock_packet(clock, pet_slot)
    except Exception as error:
        add_activity('Clock packet could not be built: %s' % error)
        failed_targets[target_key(target)] = (
            time.time() + FAILED_TARGET_COOLDOWN_SECONDS)
        return False
    pending_operation = {
        'phase': 'waiting-response',
        'clock_slot': clock_slot,
        'clock_name': clock.get('name') or clock.get('servername'),
        'pet_slot': pet_slot,
        'pet_model': target.get('model'),
        'pet_servername': target.get('servername'),
        'pet_name': target.get('name') or target.get('servername'),
        'previous_expiration': expiration_value(target),
        'reason': target.get('reason'),
        'use_tid': use_tid,
        'deadline': time.time() + RESPONSE_TIMEOUT_SECONDS,
        'target_key': target_key(target)
    }
    inject_joymax(0x704C, packet, True)
    set_status('WAITING FOR SERVER', COLOR_WARNING)
    set_current('%s (slot %d)' %
                (pending_operation['pet_name'], pet_slot), COLOR_WARNING)
    add_activity('Requested %s for %s (slots %d -> %d, packet %s).' %
                 (pending_operation['clock_name'], pending_operation['pet_name'],
                  clock_slot, pet_slot,
                  ' '.join('%02X' % value for value in packet)))
    return True


def find_pending_pet(pets):
    if not pending_operation:
        return None
    for item in pets:
        if item['slot'] == pending_operation['pet_slot']:
            if (item.get('model') == pending_operation['pet_model']
                    and item.get('servername') ==
                    pending_operation['pet_servername']):
                return item
    matches = [item for item in pets
               if item.get('model') == pending_operation['pet_model']
               and item.get('servername') == pending_operation['pet_servername']]
    if len(matches) == 1:
        return matches[0]
    return None


def finish_operation(success, message, pause_on_failure=False):
    global pending_operation, last_scan_time, paused
    if pending_operation and not success:
        failed_targets[pending_operation['target_key']] = (
            time.time() + FAILED_TARGET_COOLDOWN_SECONDS)
    add_activity(message)
    pending_operation = None
    set_current('No active operation')
    last_scan_time = 0.0
    if success:
        set_status('MONITORING', COLOR_SUCCESS)
    else:
        if pause_on_failure:
            paused = True
            QtBind.setText(gui, btn_pause, 'Resume')
            set_status('PAUSED AFTER FAILURE', COLOR_ERROR)
            add_activity('Automatic processing paused for safety.')
        else:
            set_status('RETRY DELAY', COLOR_ERROR)


def verify_pending_operation():
    if not pending_operation or pending_operation['phase'] != 'verifying':
        return
    pets, clocks = scan_inventory()
    last_snapshot['pets'] = pets
    last_snapshot['clocks'] = clocks
    refresh_snapshot_gui(pets, clocks)
    item = find_pending_pet(pets)
    if item:
        current_expiration = expiration_value(item)
        previous = pending_operation['previous_expiration']
        if current_expiration is not None:
            if previous is None:
                verified = current_expiration > 0
            elif previous <= 0:
                verified = current_expiration > 0
            else:
                verified = current_expiration > previous + 60
            if verified:
                finish_operation(
                    True,
                    'Duration confirmed for %s: %s.' %
                    (pending_operation['pet_name'],
                     format_remaining(current_expiration)))
                return
    if time.time() > pending_operation['deadline']:
        finish_operation(
            False, 'Server accepted the Clock, but duration update was not confirmed.',
            True)


def perform_scan(allow_action):
    global last_snapshot
    pets, clocks = scan_inventory()
    last_snapshot = {'pets': pets, 'clocks': clocks}
    refresh_snapshot_gui(pets, clocks)
    if not allow_action:
        set_status('SCAN COMPLETE', COLOR_SUCCESS)
        return

    if settings.get('detect_expired_by_summon', False):
        untested = [item for item in pets
                    if target_key(item) not in summon_test_states]
        if untested and begin_summon_test_cycle(pets):
            return

    now = time.time()
    targets = eligible_targets(pets, now)
    if not targets:
        set_status('MONITORING', COLOR_SUCCESS)
        set_current('No active operation')
        return
    if not clocks:
        set_status('NO CLOCKS AVAILABLE', COLOR_WARNING)
        set_current('%d pet(s) waiting' % len(targets), COLOR_WARNING)
        return
    start_clock_operation(targets[0], select_clock(clocks))


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        set_status('OPENING DISCORD INVITE', COLOR_SUCCESS)
    except Exception as error:
        plugin_log('Discord link error: %s' % error)
        set_status('COULD NOT OPEN DISCORD', COLOR_ERROR)


def show_custom_pets_clicked():
    refresh_custom_pattern_list()
    for widget, x, y in CUSTOM_PANEL_LAYOUT:
        QtBind.move(gui, widget, x, y)


def hide_custom_pets_clicked():
    for widget, unused_x, y in CUSTOM_PANEL_LAYOUT:
        QtBind.move(gui, widget, OFFSCREEN_X, y)


def add_custom_pattern_clicked():
    pattern = normalize_custom_pattern(QtBind.text(gui, txt_custom_pattern))
    if not pattern:
        set_custom_status(
            'Use ITEM_...SCROLL with optional * wildcard; no spaces or ?.',
            COLOR_ERROR)
        return
    if pattern in custom_pet_patterns:
        set_custom_status('This pattern is already configured.', COLOR_WARNING)
        return
    custom_pet_patterns.append(pattern)
    settings['custom_pet_patterns'] = list(custom_pet_patterns)
    QtBind.clear(gui, txt_custom_pattern)
    refresh_custom_pattern_list()
    set_custom_status('Pattern added. Save Settings to keep it.', COLOR_SUCCESS)


def remove_custom_pattern_clicked():
    index = QtBind.currentIndex(gui, lst_custom_patterns)
    if index < 0 or index >= len(custom_pet_patterns):
        set_custom_status('Select a configured pattern to remove.', COLOR_WARNING)
        return
    removed = custom_pet_patterns.pop(index)
    settings['custom_pet_patterns'] = list(custom_pet_patterns)
    refresh_custom_pattern_list()
    set_custom_status('Removed %s. Save Settings to keep the change.' % removed,
                      COLOR_SUCCESS)


def monitor_changed(checked):
    if settings_loading:
        return
    settings['automatic_monitoring'] = bool(checked)
    if checked:
        set_status('MONITORING ENABLED', COLOR_SUCCESS)
    else:
        set_status('MONITORING DISABLED', COLOR_MUTED)


def setting_changed(checked):
    if settings_loading:
        return
    settings.update(read_gui_settings())
    if not settings.get('detect_expired_by_summon', False):
        summon_test_states.clear()
    refresh_custom_pattern_list()


def save_clicked():
    if save_settings_file():
        set_status('SETTINGS SAVED', COLOR_SUCCESS)


def scan_clicked():
    try:
        perform_scan(False)
        add_activity('Manual inventory scan completed.')
    except Exception as error:
        set_status('SCAN FAILED', COLOR_ERROR)
        plugin_log('Manual scan error: %s' % error)


def test_pets_clicked():
    global paused
    try:
        if pending_operation or summon_test:
            set_status('AN OPERATION IS ALREADY ACTIVE', COLOR_WARNING)
            return
        if not get_character_key():
            set_status('JOIN THE GAME BEFORE TESTING', COLOR_WARNING)
            return
        settings['detect_expired_by_summon'] = True
        QtBind.setChecked(gui, chk_summon_test, True)
        pets, clocks = scan_inventory()
        last_snapshot['pets'] = pets
        last_snapshot['clocks'] = clocks
        refresh_snapshot_gui(pets, clocks)
        if not pets:
            set_status('NO PICK PETS FOUND', COLOR_WARNING)
            return
        summon_test_states.clear()
        if not begin_summon_test_cycle(pets, True):
            set_status('PET TEST COULD NOT START', COLOR_WARNING)
            set_current('Check active Pick Pet detection', COLOR_WARNING)
            add_activity(
                'Manual pet test could not start because the active Pick Pet cannot be restored safely.')
            return
        paused = True
        QtBind.setText(gui, btn_pause, 'Resume')
        add_activity('Manual pet test started. Clock use is disabled for this test.')
    except Exception as error:
        set_status('PET TEST FAILED', COLOR_ERROR)
        plugin_log('Manual pet test error: %s' % error)


def pause_clicked():
    global paused
    paused = not paused
    if paused:
        QtBind.setText(gui, btn_pause, 'Resume')
        set_status('PAUSED', COLOR_WARNING)
        add_activity('Automatic processing paused for this session.')
    else:
        QtBind.setText(gui, btn_pause, 'Pause')
        set_status('MONITORING', COLOR_SUCCESS)
        add_activity('Automatic processing resumed.')


def joined_game():
    global settings_loaded_for, last_scan_time, pending_operation, summon_test
    settings_loaded_for = None
    last_scan_time = 0.0
    pending_operation = None
    summon_test = None
    summon_test_states.clear()
    clock_verification_targets.clear()
    set_status('WAITING FOR CHARACTER', COLOR_WARNING)


def disconnected():
    global settings_loaded_for, pending_operation, last_scan_time, summon_test
    settings_loaded_for = None
    pending_operation = None
    summon_test = None
    summon_test_states.clear()
    clock_verification_targets.clear()
    last_scan_time = 0.0
    failed_targets.clear()
    set_status('WAITING FOR CONNECTION', COLOR_MUTED)
    set_current('No active operation')


def handle_silkroad(opcode, data):
    if opcode == 0x704C and data:
        raw = bytes(data)
        pets, clocks = scan_inventory()
        clock_slots = set(int(item['slot']) for item in clocks
                          if 0 <= int(item['slot']) <= 255)
        if raw[0] in clock_slots:
            add_activity('MANUAL CLOCK CAPTURE 0x704C: %s' % packet_hex(raw))
    return True


def handle_joymax(opcode, data):
    if opcode == 0xB04C and data:
        raw = bytes(data)
        add_activity('SERVER 0xB04C: %s' % packet_hex(raw))
        if not pending_operation:
            return True
        response_tid = None
        if len(raw) >= 6:
            response_tid = struct.unpack_from('<H', raw, 4)[0]
        response_matches = (
            (len(raw) >= 2
             and raw[1] == pending_operation['clock_slot'])
            or response_tid == pending_operation.get('use_tid'))
        if (pending_operation['phase'] == 'waiting-response'
                and response_matches):
            if raw[0] == 1:
                if settings.get('detect_expired_by_summon', False):
                    clock_verification_targets.add(
                        pending_operation['target_key'])
                    summon_test_states.pop(
                        pending_operation['target_key'], None)
                    finish_operation(
                        True,
                        'Server accepted the Clock for %s; summon verification queued.' %
                        pending_operation['pet_name'])
                    return True
                pending_operation['phase'] = 'verifying'
                pending_operation['deadline'] = time.time() + VERIFY_TIMEOUT_SECONDS
                set_status('VERIFYING PET DURATION', COLOR_WARNING)
                add_activity('Server accepted the Clock; verifying duration update.')
            else:
                status = raw[0]
                finish_operation(
                    False, 'Server rejected the Clock (status %d).' % status, True)
        elif pending_operation['phase'] == 'waiting-response':
            add_activity('The item-use response did not match the pending Clock.')
    return True


def event_loop():
    global settings_loaded_for, last_scan_time
    try:
        character_key = get_character_key()
        if not character_key:
            return
        if settings_loaded_for != character_key:
            load_settings(character_key)
            last_scan_time = 0.0

        if summon_test:
            process_summon_test()
            return

        if pending_operation:
            if pending_operation['phase'] == 'waiting-response':
                if time.time() > pending_operation['deadline']:
                    finish_operation(
                        False, 'Timed out waiting for the server response.', True)
            elif pending_operation['phase'] == 'verifying':
                verify_pending_operation()
            return

        if paused or not settings.get('automatic_monitoring', False):
            if paused:
                set_status('PAUSED', COLOR_WARNING)
            else:
                set_status('MONITORING DISABLED', COLOR_MUTED)
            return

        now = time.time()
        if now - last_scan_time < settings['scan_interval_seconds']:
            return
        last_scan_time = now
        perform_scan(True)
    except Exception as error:
        set_status('MONITORING ERROR', COLOR_ERROR)
        plugin_log('Event loop error: %s' % error)


apply_settings_to_gui()
refresh_custom_pattern_list()
QtBind.append(gui, lst_pets, 'Join the game to inspect Pick Pets.')
QtBind.append(gui, lst_activity, 'Automatic monitoring is disabled by default.')
log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
