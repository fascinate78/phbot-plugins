from phBot import *
import QtBind
import json
import os
import struct
import time
import webbrowser


pName = 'FDevilAwakener'
pVersion = '1.0.2'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

SUPPORTED_LOCALE = 65
SCROLL_SERVERNAME = 'ITEM_ETC_NASRUN_UPGRADE_SCROLL'
USE_ITEM_OPCODE = 0x704C
USE_ITEM_RESPONSE_OPCODE = 0xB04C
AWAKENING_RESULT_OPCODE = 0x3545
AWAKENING_PAYLOAD_MIDDLE = b'\x30\x0C\x03\x11'
DEVIL_INACTIVE_ERROR = 0x18F8
AWAKENING_NO_RESULT_ERROR = 0x18DD
ACTION_DELAY_SECONDS = 1.5
RESULT_TIMEOUT_SECONDS = 8.0
INVENTORY_REFRESH_SECONDS = 1.0

COLOR_PRIMARY = '#5b57e0'
COLOR_TEXT = '#2b3038'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#d93a4d'

running = False
waiting_result = False
pending_devil_slot = -1
pending_scroll_slot = -1
pending_since = 0.0
next_action_time = 0.0
last_inventory_refresh = 0.0
attempts_sent = 0
results_received = 0
last_plus = 0
last_duration = 0
target_plus = 8
maximum_scrolls = 10
use_all_scrolls = True
active_mode = 'automatic'
selected_devil_key = None
devil_candidates = []


def fixed_width_text(content, width):
    return (
        '<table width="{0}" cellspacing="0" cellpadding="0">'
        '<tr><td>{1}</td></tr></table>'
    ).format(width, content)


def plugin_log(message):
    log('[%s] %s' % (pName, message))


def config_path():
    try:
        base_directory = get_config_dir()
    except Exception:
        base_directory = None
    if not base_directory:
        base_directory = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_directory, pName, 'settings.json')


def is_devil(item):
    if not item:
        return False
    servername = str(item.get('servername') or '').upper()
    name = str(item.get('name') or '').upper()
    if servername == SCROLL_SERVERNAME:
        return False
    return ('NASRUN' in servername and 'AVATAR' in servername) or name.startswith("DEVIL'S SPIRIT")


def inventory_items():
    inventory = get_inventory()
    if not inventory:
        return []
    return inventory.get('items') or []


def scan_devils(items=None):
    if items is None:
        items = inventory_items()
    found = []
    for slot, item in enumerate(items):
        # Awakening targets must be in normal inventory, not an equipment slot.
        if slot < 13:
            continue
        if is_devil(item):
            found.append({
                'slot': slot,
                'model': int(item.get('model') or 0),
                'servername': str(item.get('servername') or ''),
                'name': str(item.get('name') or item.get('servername') or 'Devil'),
                'plus': int(item.get('plus') or 0)
            })
    return found


def scan_scrolls(items=None):
    if items is None:
        items = inventory_items()
    found = []
    for slot, item in enumerate(items):
        if not item:
            continue
        if str(item.get('servername') or '').upper() == SCROLL_SERVERNAME:
            quantity = int(item.get('quantity') or 0)
            if quantity > 0:
                found.append({'slot': slot, 'quantity': quantity})
    return found


def total_scroll_count(items=None):
    return sum(entry['quantity'] for entry in scan_scrolls(items))


def devil_key(devil):
    return (devil['model'], devil['servername'], devil['slot'])


def format_devil(devil):
    return 'Slot %d | %s | +%d' % (devil['slot'], devil['name'], devil['plus'])


gui = QtBind.init(__name__, pName)

QtBind.createLabel(
    gui, '<font color="%s" size="4"><b>\u2728 FDEVIL AWAKENER</b></font>' % COLOR_PRIMARY,
    12, 6)
QtBind.createLabel(gui, '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion), 226, 12)
btn_discord = QtBind.createButton(gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(
    gui, u'<font color="%s"><b>\u269c Made By FascinaTe</b></font>' % COLOR_PRIMARY,
    565, 11)
QtBind.createLineEdit(gui, '', 12, 30, 696, 1)

QtBind.createLabel(gui, '<font color="%s"><b>AWAKENING CONTROL</b></font>' % COLOR_PRIMARY, 12, 42)
QtBind.createLabel(gui, '<font color="%s">Mode</font>' % COLOR_TEXT, 12, 68)
cmb_mode = QtBind.createCombobox(gui, 115, 63, 230, 22)
QtBind.append(gui, cmb_mode, 'Automatic inventory Devil')
QtBind.append(gui, cmb_mode, 'Selected Devil')

QtBind.createLabel(gui, '<font color="%s">Target enhancement</font>' % COLOR_TEXT, 12, 98)
txt_target = QtBind.createLineEdit(gui, '8', 145, 93, 45, 22)
QtBind.createLabel(gui, '<font color="%s">(+1 to +10)</font>' % COLOR_MUTED, 198, 98)

QtBind.createLabel(gui, '<font color="%s">Maximum scrolls</font>' % COLOR_TEXT, 12, 128)
txt_maximum = QtBind.createLineEdit(gui, '10', 145, 123, 45, 22)
chk_use_all = QtBind.createCheckBox(
    gui, 'use_all_changed', 'Use all available scrolls', 198, 126)

btn_start = QtBind.createButton(gui, 'start_clicked', 'Start Awakening', 12, 160)
btn_stop = QtBind.createButton(gui, 'stop_clicked', 'Stop', 137, 160)
btn_save = QtBind.createButton(gui, 'save_clicked', 'Save Settings', 202, 160)

QtBind.createLabel(gui, '<font color="%s"><b>SELECTED DEVIL</b></font>' % COLOR_PRIMARY, 12, 198)
lst_devils = QtBind.createList(gui, 12, 220, 333, 55)
btn_refresh = QtBind.createButton(gui, 'refresh_clicked', 'Refresh Devils', 12, 280)
QtBind.createLabel(
    gui, '<font color="%s">Automatic mode uses the first available Devil.</font>' % COLOR_MUTED,
    125, 284)

QtBind.createLineEdit(gui, '', 365, 43, 1, 250)
QtBind.createLabel(gui, '<font color="%s"><b>LIVE STATUS</b></font>' % COLOR_PRIMARY, 386, 42)

QtBind.createLabel(gui, '<font color="%s"><b>State</b></font>' % COLOR_TEXT, 386, 70)
lbl_state = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s"><b>READY</b></font>' % COLOR_MUTED, 210), 480, 70)
QtBind.createLabel(gui, '<font color="%s"><b>Devil</b></font>' % COLOR_TEXT, 386, 100)
lbl_devil = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s">None selected</font>' % COLOR_MUTED, 215), 480, 100)
QtBind.createLabel(gui, '<font color="%s"><b>Current result</b></font>' % COLOR_TEXT, 386, 130)
lbl_plus = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s"><b>+0</b></font>' % COLOR_MUTED, 100), 500, 130)
QtBind.createLabel(gui, '<font color="%s"><b>Duration</b></font>' % COLOR_TEXT, 386, 160)
lbl_duration = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s">00:00:00</font>' % COLOR_MUTED, 120), 480, 160)
QtBind.createLabel(gui, '<font color="%s"><b>Attempts</b></font>' % COLOR_TEXT, 386, 190)
lbl_attempts = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s">0 sent / 0 results</font>' % COLOR_MUTED, 170), 480, 190)
QtBind.createLabel(gui, '<font color="%s"><b>Scrolls</b></font>' % COLOR_TEXT, 386, 220)
lbl_scrolls = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s">0 available</font>' % COLOR_MUTED, 170), 480, 220)
lbl_message = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s">Ready to scan inventory.</font>' % COLOR_MUTED, 310),
    386, 255)


def set_state(state, color=COLOR_MUTED):
    QtBind.setText(
        gui, lbl_state,
        fixed_width_text('<font color="%s"><b>%s</b></font>' % (color, state), 210))


def set_message(message, color=COLOR_MUTED):
    QtBind.setText(
        gui, lbl_message,
        fixed_width_text('<font color="%s">%s</font>' % (color, message), 310))


def update_devil_label(text, color=COLOR_TEXT):
    QtBind.setText(
        gui, lbl_devil,
        fixed_width_text('<font color="%s">%s</font>' % (color, text), 215))


def format_duration(seconds):
    seconds = max(0, int(seconds))
    return '%02d:%02d:%02d' % (seconds // 3600, (seconds % 3600) // 60, seconds % 60)


def update_live_values(items=None):
    scrolls = total_scroll_count(items)
    QtBind.setText(
        gui, lbl_scrolls,
        fixed_width_text('<font color="%s">%d available</font>' % (COLOR_TEXT, scrolls), 170))
    QtBind.setText(
        gui, lbl_plus,
        fixed_width_text('<font color="%s"><b>+%d</b></font>' % (COLOR_PRIMARY, last_plus), 100))
    QtBind.setText(
        gui, lbl_duration,
        fixed_width_text('<font color="%s">%s</font>' %
                         (COLOR_TEXT, format_duration(last_duration)), 120))
    QtBind.setText(
        gui, lbl_attempts,
        fixed_width_text('<font color="%s">%d sent / %d results</font>' %
                         (COLOR_TEXT, attempts_sent, results_received), 170))


def stop_process(message, color=COLOR_WARNING, state='STOPPED'):
    global running, waiting_result, pending_devil_slot, pending_scroll_slot
    running = False
    waiting_result = False
    pending_devil_slot = -1
    pending_scroll_slot = -1
    set_state(state, color)
    set_message(message, color)
    plugin_log(message)


def refresh_devils(select_key=None):
    global devil_candidates
    devil_candidates = scan_devils()
    QtBind.clear(gui, lst_devils)
    for devil in devil_candidates:
        QtBind.append(gui, lst_devils, format_devil(devil))
    if not devil_candidates:
        update_devil_label('No Devil found', COLOR_WARNING)
        set_message('No Devil found in inventory.', COLOR_WARNING)
    elif select_key:
        for devil in devil_candidates:
            if devil_key(devil) == select_key:
                update_devil_label(devil['name'])
                break
    update_live_values()
    return devil_candidates


def selected_candidate():
    index = QtBind.currentIndex(gui, lst_devils)
    if index < 0 or index >= len(devil_candidates):
        return None
    return devil_candidates[index]


def resolve_devil(items):
    current = scan_devils(items)
    if active_mode == 'automatic':
        return current[0] if current else None
    if not selected_devil_key:
        return None
    model, servername, original_slot = selected_devil_key
    for devil in current:
        if devil['slot'] == original_slot and devil['model'] == model and devil['servername'] == servername:
            return devil
    matching = [d for d in current if d['model'] == model and d['servername'] == servername]
    return matching[0] if len(matching) == 1 else None


def read_positive_integer(widget, label, minimum, maximum):
    raw = str(QtBind.text(gui, widget) or '').strip()
    try:
        value = int(raw)
    except Exception:
        raise ValueError('%s must be a number.' % label)
    if value < minimum or value > maximum:
        raise ValueError('%s must be between %d and %d.' % (label, minimum, maximum))
    return value


def save_settings(show_status=True):
    settings = {
        'target_plus': int(target_plus),
        'maximum_scrolls': int(maximum_scrolls),
        'use_all_scrolls': bool(use_all_scrolls),
        'mode': active_mode
    }
    path = config_path()
    try:
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        with open(path, 'w', encoding='utf-8') as handle:
            json.dump(settings, handle, indent=2, sort_keys=True)
        if show_status:
            set_message('Settings saved.', COLOR_SUCCESS)
        return True
    except Exception as error:
        plugin_log('Could not save settings: %s' % error)
        if show_status:
            set_message('Could not save settings.', COLOR_ERROR)
        return False


def load_settings():
    global target_plus, maximum_scrolls, use_all_scrolls, active_mode
    try:
        with open(config_path(), 'r', encoding='utf-8') as handle:
            settings = json.load(handle)
        target_plus = max(1, min(10, int(settings.get('target_plus', 8))))
        maximum_scrolls = max(1, min(9999, int(settings.get('maximum_scrolls', 10))))
        use_all_scrolls = bool(settings.get('use_all_scrolls', True))
        active_mode = settings.get('mode', 'automatic')
        if active_mode not in ('automatic', 'selected'):
            active_mode = 'automatic'
    except Exception:
        pass
    QtBind.setText(gui, txt_target, str(target_plus))
    QtBind.setText(gui, txt_maximum, str(maximum_scrolls))
    QtBind.setChecked(gui, chk_use_all, use_all_scrolls)
    QtBind.setText(
        gui, cmb_mode,
        'Selected Devil' if active_mode == 'selected' else 'Automatic inventory Devil')


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        set_message('Opening Discord invite...', COLOR_SUCCESS)
    except Exception as error:
        plugin_log('Discord link error: %s' % error)
        set_message('Could not open Discord invite.', COLOR_ERROR)


def use_all_changed(checked):
    global use_all_scrolls
    use_all_scrolls = bool(checked)
    QtBind.setEnabled(gui, txt_maximum, not use_all_scrolls)


def refresh_clicked():
    if running:
        set_message('Stop awakening before refreshing the list.', COLOR_WARNING)
        return
    refresh_devils()
    if devil_candidates:
        set_message('Found %d Devil item(s).' % len(devil_candidates), COLOR_SUCCESS)


def save_clicked():
    global target_plus, maximum_scrolls, use_all_scrolls, active_mode
    if running:
        set_message('Stop awakening before changing settings.', COLOR_WARNING)
        return
    try:
        target_plus = read_positive_integer(txt_target, 'Target enhancement', 1, 10)
        maximum_scrolls = read_positive_integer(txt_maximum, 'Maximum scrolls', 1, 9999)
        use_all_scrolls = QtBind.isChecked(gui, chk_use_all)
        mode_text = str(QtBind.text(gui, cmb_mode) or '')
        active_mode = 'selected' if mode_text == 'Selected Devil' else 'automatic'
        save_settings()
    except ValueError as error:
        set_message(str(error), COLOR_ERROR)


def start_clicked():
    global running, waiting_result, attempts_sent, results_received
    global last_plus, last_duration, target_plus, maximum_scrolls
    global use_all_scrolls, active_mode, selected_devil_key, next_action_time

    if running:
        set_message('Awakening is already running.', COLOR_WARNING)
        return
    try:
        if get_locale() != SUPPORTED_LOCALE:
            set_state('UNSUPPORTED LOCALE', COLOR_ERROR)
            set_message('This plugin requires Silkroad-R locale 65.', COLOR_ERROR)
            return
        target_plus = read_positive_integer(txt_target, 'Target enhancement', 1, 10)
        maximum_scrolls = read_positive_integer(txt_maximum, 'Maximum scrolls', 1, 9999)
        use_all_scrolls = QtBind.isChecked(gui, chk_use_all)
        mode_text = str(QtBind.text(gui, cmb_mode) or '')
        active_mode = 'selected' if mode_text == 'Selected Devil' else 'automatic'
        if active_mode == 'selected':
            chosen = selected_candidate()
            if not chosen:
                set_state('SELECTION REQUIRED', COLOR_WARNING)
                set_message('Select a Devil from the list first.', COLOR_WARNING)
                return
            selected_devil_key = devil_key(chosen)
        else:
            selected_devil_key = None

        items = inventory_items()
        devil = resolve_devil(items)
        if not devil:
            set_state('DEVIL NOT FOUND', COLOR_ERROR)
            set_message('The requested Devil is not in inventory.', COLOR_ERROR)
            return
        if total_scroll_count(items) <= 0:
            set_state('NO SCROLLS', COLOR_ERROR)
            set_message('No Awakening Enhancement Scroll found.', COLOR_ERROR)
            return

        attempts_sent = 0
        results_received = 0
        last_plus = devil['plus']
        last_duration = 0
        waiting_result = False
        running = True
        next_action_time = time.time()
        update_devil_label('%s (slot %d)' % (devil['name'], devil['slot']))
        update_live_values(items)
        if last_plus >= target_plus:
            stop_process('Target already reached at +%d.' % last_plus, COLOR_SUCCESS, 'TARGET REACHED')
            return
        set_state('RUNNING', COLOR_SUCCESS)
        set_message('Searching for the next safe attempt...', COLOR_MUTED)
        save_settings(False)
    except ValueError as error:
        set_state('INVALID SETTINGS', COLOR_ERROR)
        set_message(str(error), COLOR_ERROR)
    except Exception as error:
        plugin_log('Start error: %s' % error)
        stop_process('Could not start awakening.', COLOR_ERROR, 'ERROR')


def stop_clicked():
    if running:
        stop_process('Stopped by user.', COLOR_WARNING)
    else:
        set_message('Awakening is not running.', COLOR_MUTED)


def send_awaken_request(devil, scroll):
    global waiting_result, pending_devil_slot, pending_scroll_slot
    global pending_since, attempts_sent
    payload = struct.pack('<B', scroll['slot']) + AWAKENING_PAYLOAD_MIDDLE + struct.pack('<B', devil['slot'])
    inject_joymax(USE_ITEM_OPCODE, payload, False)
    attempts_sent += 1
    waiting_result = True
    pending_devil_slot = devil['slot']
    pending_scroll_slot = scroll['slot']
    pending_since = time.time()
    set_state('WAITING FOR RESULT', COLOR_WARNING)
    set_message('Attempt %d sent to Devil slot %d.' % (attempts_sent, devil['slot']), COLOR_WARNING)
    update_live_values()


def event_loop():
    global last_inventory_refresh, next_action_time
    now = time.time()
    if not running:
        if now - last_inventory_refresh >= INVENTORY_REFRESH_SECONDS:
            last_inventory_refresh = now
            update_live_values()
        return
    if waiting_result:
        if now - pending_since > RESULT_TIMEOUT_SECONDS:
            stop_process('Server result timed out; no retry was sent.', COLOR_ERROR, 'TIMEOUT')
        return
    if now < next_action_time:
        return
    try:
        items = inventory_items()
        devil = resolve_devil(items)
        if not devil:
            stop_process('Selected Devil could not be resolved safely.', COLOR_ERROR, 'DEVIL LOST')
            return
        if devil['plus'] >= target_plus:
            stop_process('Target reached at +%d.' % devil['plus'], COLOR_SUCCESS, 'TARGET REACHED')
            return
        scrolls = scan_scrolls(items)
        if not scrolls:
            stop_process('Scrolls exhausted before reaching +%d.' % target_plus,
                         COLOR_WARNING, 'SCROLLS EXHAUSTED')
            return
        if not use_all_scrolls and attempts_sent >= maximum_scrolls:
            stop_process('Maximum scroll limit reached at +%d.' % last_plus,
                         COLOR_WARNING, 'LIMIT REACHED')
            return
        update_devil_label('%s (slot %d)' % (devil['name'], devil['slot']))
        send_awaken_request(devil, scrolls[0])
    except Exception as error:
        plugin_log('Event loop error: %s' % error)
        stop_process('Unexpected inventory or packet error.', COLOR_ERROR, 'ERROR')


def handle_joymax(opcode, data):
    global waiting_result, results_received, last_plus, last_duration, next_action_time
    if not running or not waiting_result:
        return True
    try:
        if opcode == USE_ITEM_RESPONSE_OPCODE and len(data) >= 3 and data[0] == 2:
            error_code = struct.unpack_from('<H', data, 1)[0]
            if error_code == DEVIL_INACTIVE_ERROR:
                stop_process('Devil is inactive. Activate it before awakening.',
                             COLOR_ERROR, 'DEVIL INACTIVE')
            elif error_code == AWAKENING_NO_RESULT_ERROR:
                # Locale 65 sends 0x18DD immediately before a successful B04C
                # quantity update when a scroll is consumed without a 0x3545
                # enhancement result. This is a completed failed roll, not a
                # fatal item-use rejection.
                waiting_result = False
                results_received += 1
                set_state('RUNNING', COLOR_SUCCESS)
                set_message('No enhancement result; continuing to target +%d...' %
                            target_plus, COLOR_WARNING)
                next_action_time = time.time() + ACTION_DELAY_SECONDS
                update_live_values()
            else:
                stop_process('Server rejected item use (0x%04X).' % error_code,
                             COLOR_ERROR, 'SERVER REJECTED')
        elif opcode == AWAKENING_RESULT_OPCODE and len(data) >= 19:
            devil_slot = data[1]
            if devil_slot != pending_devil_slot:
                return True
            result_plus = struct.unpack_from('<H', data, 13)[0]
            duration = struct.unpack_from('<I', data, 15)[0]
            if result_plus < 1 or result_plus > 10 or duration <= 0:
                packet_hex = ' '.join('{:02X}'.format(value) for value in data)
                plugin_log('Ignored malformed 0x3545 result: %s' % packet_hex)
                return True
            waiting_result = False
            results_received += 1
            last_plus = result_plus
            last_duration = duration
            update_live_values()
            if result_plus >= target_plus:
                stop_process('Target reached: +%d with %s remaining.' %
                             (result_plus, format_duration(duration)),
                             COLOR_SUCCESS, 'TARGET REACHED')
            else:
                set_state('RUNNING', COLOR_SUCCESS)
                set_message('Result +%d; target is +%d. Continuing...' %
                            (result_plus, target_plus), COLOR_WARNING)
                next_action_time = time.time() + ACTION_DELAY_SECONDS
    except Exception as error:
        plugin_log('Packet parse error for 0x%04X: %s' % (opcode, error))
        stop_process('Could not parse the server result safely.', COLOR_ERROR, 'PARSE ERROR')
    return True


def disconnected():
    if running:
        stop_process('Disconnected; awakening stopped.', COLOR_ERROR, 'DISCONNECTED')


load_settings()
QtBind.setEnabled(gui, txt_maximum, not use_all_scrolls)
refresh_devils()

log('[%s] Loaded - \u269c Made By FascinaTe' % pName)
