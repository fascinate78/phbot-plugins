from phBot import *
import QtBind

import json
import os
import re
import struct
import time
import webbrowser


pName = 'FAutoPetClock'
pVersion = '1.0.4'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

COLOR_PRIMARY = '#5b57e0'
COLOR_TEXT = '#2b3038'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#d93a4d'

DEFAULT_SETTINGS = {
    'automatic_monitoring': False,
    'revive_expired_pets': True,
    'extend_near_expiry': False,
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

settings = dict(DEFAULT_SETTINGS)
settings_loading = False
settings_loaded_for = None
paused = False
last_scan_time = 0.0
pending_operation = None
failed_targets = {}
last_snapshot = {'pets': [], 'clocks': []}
activity_lines = []


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
chk_extend = QtBind.createCheckBox(
    gui, 'setting_changed', 'Extend pets near expiration', 12, 111)

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
btn_scan = QtBind.createButton(gui, 'scan_clicked', 'Scan Now', 122, 229)
btn_pause = QtBind.createButton(gui, 'pause_clicked', 'Pause', 210, 229)

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
        'extend_near_expiry': bool(QtBind.isChecked(gui, chk_extend)),
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
        QtBind.setChecked(gui, chk_extend, settings['extend_near_expiry'])
        QtBind.setText(gui, txt_threshold, str(settings['near_expiry_hours']))
        QtBind.setText(gui, txt_scan_interval,
                       str(settings['scan_interval_seconds']))
        QtBind.setText(gui, cmb_priority, settings['clock_priority'])
    finally:
        settings_loading = False


def load_settings(character_key):
    global settings, settings_loaded_for, paused
    failed_targets.clear()
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
        settings['extend_near_expiry'] = bool(settings['extend_near_expiry'])
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
        paused = False
        QtBind.setText(gui, btn_pause, 'Pause')
        apply_settings_to_gui()
        add_activity('Character settings loaded.')
    except (OSError, IOError, ValueError, TypeError) as error:
        settings = dict(DEFAULT_SETTINGS)
        settings_loaded_for = character_key
        apply_settings_to_gui()
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


def is_pick_pet_scroll(item):
    servername = str(item.get('servername') or '').upper()
    return ('COS_P_' in servername and 'SCROLL' in servername
            and 'COS_P_EXTENSION' not in servername)


def is_reincarnation_clock(item):
    servername = str(item.get('servername') or '').upper()
    return servername.startswith('ITEM_COS_P_EXTENSION')


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

    active_servernames = []
    try:
        for pet in (get_pets() or {}).values():
            if pet and pet.get('type') == 'pick':
                servername = str(pet.get('servername') or '').upper()
                if servername:
                    active_servernames.append(servername)
    except Exception as error:
        plugin_log('Active Pick Pet inspection error: %s' % error)

    for item in pets:
        scroll_servername = str(item.get('servername') or '').upper()
        item['summoned'] = any(
            servername in scroll_servername for servername in active_servernames)
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
        if item.get('summoned'):
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
    targets = []
    for item in pets:
        remaining = expiration_value(item)
        if remaining is None or item.get('summoned'):
            continue
        key = target_key(item)
        retry_at = failed_targets.get(key, 0.0)
        if retry_at > now:
            continue
        if remaining <= 0 and settings['revive_expired_pets']:
            entry = dict(item)
            entry['reason'] = 'expired'
            targets.append(entry)
        elif (remaining > 0 and remaining <= threshold_seconds
              and settings['extend_near_expiry']):
            entry = dict(item)
            entry['reason'] = 'near-expiry'
            targets.append(entry)
    return sorted(targets, key=lambda item: (expiration_value(item), item['slot']))


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
    tid, item_data = get_item_use_tid(clock)
    if tid is None:
        raise ValueError('static Clock item data is unavailable')
    locale = int(get_locale())
    if locale == 22:
        # Verified manual vSRO capture:
        # [Clock slot][two-byte item-use TID][Pick Pet scroll slot].
        return struct.pack('<BHB', clock_slot, tid, pet_slot), tid
    if locale == 18:
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
    global settings_loaded_for, last_scan_time, pending_operation
    settings_loaded_for = None
    last_scan_time = 0.0
    pending_operation = None
    set_status('WAITING FOR CHARACTER', COLOR_WARNING)


def disconnected():
    global settings_loaded_for, pending_operation, last_scan_time
    settings_loaded_for = None
    pending_operation = None
    last_scan_time = 0.0
    failed_targets.clear()
    set_status('WAITING FOR CONNECTION', COLOR_MUTED)
    set_current('No active operation')


def handle_silkroad(opcode, data):
    if opcode == 0x704C and data:
        raw = bytes(data)
        clock_slots = set(
            int(item['slot']) for item in scan_inventory()[1]
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
QtBind.append(gui, lst_pets, 'Join the game to inspect Pick Pets.')
QtBind.append(gui, lst_activity, 'Automatic monitoring is disabled by default.')
log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
