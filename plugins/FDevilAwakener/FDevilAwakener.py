from phBot import *
import QtBind
import json
import os
import struct
import time
import webbrowser


pName = 'FDevilAwakener'
pVersion = '1.1.2'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

SUPPORTED_LOCALES = (18, 65)
ISRO_LOCALE = 18
SCROLL_SERVERNAME = 'ITEM_ETC_NASRUN_UPGRADE_SCROLL'
USE_ITEM_OPCODE = 0x704C
USE_ITEM_RESPONSE_OPCODE = 0xB04C
AWAKENING_RESULT_OPCODE = 0x3545
AWAKENING_PAYLOAD_MIDDLE = b'\x30\x0C\x03\x11'
DEVIL_INACTIVE_ERROR = 0x18F8
AWAKENING_NO_RESULT_ERROR = 0x18DD
MOVE_ITEM_OPCODE = 0x7034
MOVE_ITEM_RESPONSE_OPCODE = 0xB034
DEVIL_EQUIPMENT_SLOT = 4
ISRO_UNEQUIP_OPERATION = 0x23
ISRO_EQUIP_OPERATION = 0x24
ISRO_POST_MOVE_DELAY_SECONDS = 1.5
ISRO_INVENTORY_SETTLE_SECONDS = 1.5
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
only_equipped_devil = False
equipped_only_run = False
restore_required = False
original_devil_identity = None
workflow_phase = 'idle'
completion_message = ''
completion_color = COLOR_MUTED
completion_state = 'STOPPED'


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
    first_slot = 17 if get_locale() == ISRO_LOCALE else 13
    for slot, item in enumerate(items):
        # Awakening targets must be in normal inventory, not an equipment slot.
        if slot < first_slot:
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


def item_identity(slot, item):
    return {
        'slot': int(slot),
        'model': int(item.get('model') or 0),
        'servername': str(item.get('servername') or ''),
        'name': str(item.get('name') or item.get('servername') or 'Devil')
    }


def identity_matches(item, identity):
    if not item or not identity:
        return False
    return (int(item.get('model') or 0) == identity['model'] and
            str(item.get('servername') or '') == identity['servername'])


def find_identity_in_inventory(items, identity):
    first_slot = 17 if get_locale() == ISRO_LOCALE else 13
    matches = []
    for slot in range(first_slot, len(items)):
        if identity_matches(items[slot], identity):
            matches.append(slot)
    return matches[0] if len(matches) == 1 else -1


def first_normal_inventory_slot():
    return 17 if get_locale() == ISRO_LOCALE else 13


def empty_normal_inventory_slots(items):
    first_slot = first_normal_inventory_slot()
    return sum(1 for slot in range(first_slot, len(items)) if not items[slot])


def resolve_restore_slot(items):
    # B034 supplies the exact slot used by the Devil that this run unequipped.
    # Prefer it over a model search, which is ambiguous with duplicate Devils.
    if (pending_devil_slot >= first_normal_inventory_slot() and
            pending_devil_slot < len(items) and
            identity_matches(items[pending_devil_slot], original_devil_identity)):
        return pending_devil_slot
    return find_identity_in_inventory(items, original_devil_identity)


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

chk_only_equipped = QtBind.createCheckBox(
    gui, 'only_equipped_changed', 'Only use equipped Devil', 115, 90)

QtBind.createLabel(gui, '<font color="%s">Target enhancement</font>' % COLOR_TEXT, 12, 120)
txt_target = QtBind.createLineEdit(gui, '8', 145, 115, 45, 22)
QtBind.createLabel(gui, '<font color="%s">(+1 to +10)</font>' % COLOR_MUTED, 198, 120)

QtBind.createLabel(gui, '<font color="%s">Maximum scrolls</font>' % COLOR_TEXT, 12, 150)
txt_maximum = QtBind.createLineEdit(gui, '10', 145, 145, 45, 22)
chk_use_all = QtBind.createCheckBox(
    gui, 'use_all_changed', 'Use all available scrolls', 198, 148)

btn_start = QtBind.createButton(gui, 'start_clicked', 'Start Awakening', 12, 180)
btn_stop = QtBind.createButton(gui, 'stop_clicked', 'Stop', 137, 180)
btn_save = QtBind.createButton(gui, 'save_clicked', 'Save Settings', 202, 180)

QtBind.createLabel(gui, '<font color="%s"><b>SELECTED DEVIL</b></font>' % COLOR_PRIMARY, 12, 210)
lst_devils = QtBind.createList(gui, 12, 230, 333, 45)
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
    global workflow_phase, completion_message, completion_color, completion_state
    if equipped_only_run and restore_required and workflow_phase == 'unequipping':
        waiting_result = False
        completion_message = message
        completion_color = color
        completion_state = state
        workflow_phase = 'cancel_after_unequip'
        set_state('STOP REQUESTED', COLOR_WARNING)
        set_message('Waiting for unequip before restoring the Devil...', COLOR_WARNING)
        return
    if equipped_only_run and restore_required and workflow_phase not in (
            'restoring', 'restore_pending', 'cancel_after_unequip'):
        waiting_result = False
        completion_message = message
        completion_color = color
        completion_state = state
        workflow_phase = 'restore_pending'
        set_state('RESTORING DEVIL', COLOR_WARNING)
        set_message('Awakening ended; restoring the equipped Devil...', COLOR_WARNING)
        return
    running = False
    waiting_result = False
    pending_devil_slot = -1
    pending_scroll_slot = -1
    workflow_phase = 'idle'
    set_state(state, color)
    set_message(message, color)
    plugin_log(message)


def finish_after_restore(restored):
    global running, waiting_result, restore_required, equipped_only_run
    global workflow_phase, pending_devil_slot, pending_scroll_slot
    running = False
    waiting_result = False
    restore_required = False
    equipped_only_run = False
    workflow_phase = 'idle'
    pending_devil_slot = -1
    pending_scroll_slot = -1
    if restored:
        set_state(completion_state, completion_color)
        set_message(completion_message + ' Devil restored.', completion_color)
        plugin_log(completion_message + ' Devil restored to slot 4.')
    else:
        set_state('RESTORE FAILED', COLOR_ERROR)
        set_message('Devil remains in inventory; equip it manually.', COLOR_ERROR)
        plugin_log('Automatic Devil restore failed; equip it manually.')


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
    if equipped_only_run:
        slot = find_identity_in_inventory(items, original_devil_identity)
        for devil in current:
            if devil['slot'] == slot:
                return devil
        return None
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
        'mode': active_mode,
        'only_equipped_devil': bool(only_equipped_devil)
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
    global only_equipped_devil
    try:
        with open(config_path(), 'r', encoding='utf-8') as handle:
            settings = json.load(handle)
        target_plus = max(1, min(10, int(settings.get('target_plus', 8))))
        maximum_scrolls = max(1, min(9999, int(settings.get('maximum_scrolls', 10))))
        use_all_scrolls = bool(settings.get('use_all_scrolls', True))
        only_equipped_devil = bool(settings.get('only_equipped_devil', False))
        active_mode = settings.get('mode', 'automatic')
        if active_mode not in ('automatic', 'selected'):
            active_mode = 'automatic'
    except Exception:
        pass
    QtBind.setText(gui, txt_target, str(target_plus))
    QtBind.setText(gui, txt_maximum, str(maximum_scrolls))
    QtBind.setChecked(gui, chk_use_all, use_all_scrolls)
    QtBind.setChecked(gui, chk_only_equipped, only_equipped_devil)
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


def only_equipped_changed(checked):
    global only_equipped_devil
    only_equipped_devil = bool(checked)
    QtBind.setEnabled(gui, cmb_mode, not only_equipped_devil)
    QtBind.setEnabled(gui, lst_devils, not only_equipped_devil)
    QtBind.setEnabled(gui, btn_refresh, not only_equipped_devil)
    if only_equipped_devil:
        set_message('Equipped-only mode will use Devil slot 4.', COLOR_MUTED)


def refresh_clicked():
    if running:
        set_message('Stop awakening before refreshing the list.', COLOR_WARNING)
        return
    refresh_devils()
    if devil_candidates:
        set_message('Found %d Devil item(s).' % len(devil_candidates), COLOR_SUCCESS)


def save_clicked():
    global target_plus, maximum_scrolls, use_all_scrolls, active_mode
    global only_equipped_devil
    if running:
        set_message('Stop awakening before changing settings.', COLOR_WARNING)
        return
    try:
        target_plus = read_positive_integer(txt_target, 'Target enhancement', 1, 10)
        maximum_scrolls = read_positive_integer(txt_maximum, 'Maximum scrolls', 1, 9999)
        use_all_scrolls = QtBind.isChecked(gui, chk_use_all)
        only_equipped_devil = QtBind.isChecked(gui, chk_only_equipped)
        mode_text = str(QtBind.text(gui, cmb_mode) or '')
        active_mode = 'selected' if mode_text == 'Selected Devil' else 'automatic'
        save_settings()
    except ValueError as error:
        set_message(str(error), COLOR_ERROR)


def start_clicked():
    global running, waiting_result, attempts_sent, results_received
    global last_plus, last_duration, target_plus, maximum_scrolls
    global use_all_scrolls, active_mode, selected_devil_key, next_action_time
    global only_equipped_devil, equipped_only_run, restore_required
    global original_devil_identity, workflow_phase, pending_since

    if running:
        set_message('Awakening is already running.', COLOR_WARNING)
        return
    try:
        locale = get_locale()
        if locale not in SUPPORTED_LOCALES:
            set_state('UNSUPPORTED LOCALE', COLOR_ERROR)
            set_message('Supported locales are iSRO 18 and Silkroad-R 65.', COLOR_ERROR)
            return
        target_plus = read_positive_integer(txt_target, 'Target enhancement', 1, 10)
        maximum_scrolls = read_positive_integer(txt_maximum, 'Maximum scrolls', 1, 9999)
        use_all_scrolls = QtBind.isChecked(gui, chk_use_all)
        only_equipped_devil = QtBind.isChecked(gui, chk_only_equipped)
        if only_equipped_devil and locale != ISRO_LOCALE:
            set_state('ISRO REQUIRED', COLOR_ERROR)
            set_message('Equipped-only mode requires iSRO locale 18.', COLOR_ERROR)
            return
        mode_text = str(QtBind.text(gui, cmb_mode) or '')
        active_mode = 'selected' if mode_text == 'Selected Devil' else 'automatic'
        if only_equipped_devil:
            selected_devil_key = None
        elif active_mode == 'selected':
            chosen = selected_candidate()
            if not chosen:
                set_state('SELECTION REQUIRED', COLOR_WARNING)
                set_message('Select a Devil from the list first.', COLOR_WARNING)
                return
            selected_devil_key = devil_key(chosen)
        else:
            selected_devil_key = None

        items = inventory_items()
        if total_scroll_count(items) <= 0:
            set_state('NO SCROLLS', COLOR_ERROR)
            set_message('No Awakening Enhancement Scroll found.', COLOR_ERROR)
            return

        attempts_sent = 0
        results_received = 0
        equipped_only_run = only_equipped_devil
        restore_required = False
        original_devil_identity = None
        if equipped_only_run:
            if len(items) <= DEVIL_EQUIPMENT_SLOT or not is_devil(items[DEVIL_EQUIPMENT_SLOT]):
                set_state('EQUIPPED DEVIL NOT FOUND', COLOR_ERROR)
                set_message('No Devil is equipped in slot 4.', COLOR_ERROR)
                equipped_only_run = False
                return
            free_slots = empty_normal_inventory_slots(items)
            if free_slots <= 0:
                set_state('INVENTORY FULL', COLOR_ERROR)
                set_message('A free inventory slot is required to unequip the Devil.', COLOR_ERROR)
                equipped_only_run = False
                return
            equipped_item = items[DEVIL_EQUIPMENT_SLOT]
            original_devil_identity = item_identity(DEVIL_EQUIPMENT_SLOT, equipped_item)
            last_plus = int(equipped_item.get('plus') or 0)
            devil = None
        else:
            devil = resolve_devil(items)
            if not devil:
                set_state('DEVIL NOT FOUND', COLOR_ERROR)
                set_message('The requested Devil is not in inventory.', COLOR_ERROR)
                return
            last_plus = devil['plus']
        last_duration = 0
        waiting_result = False
        running = True
        next_action_time = time.time()
        if equipped_only_run:
            update_devil_label('%s (equipped)' % original_devil_identity['name'])
        else:
            update_devil_label('%s (slot %d)' % (devil['name'], devil['slot']))
        update_live_values(items)
        if last_plus >= target_plus:
            restore_required = False
            equipped_only_run = False
            stop_process('Target already reached at +%d.' % last_plus, COLOR_SUCCESS, 'TARGET REACHED')
            return
        if only_equipped_devil:
            restore_required = True
            workflow_phase = 'unequipping'
            pending_since = time.time()
            inject_joymax(
                MOVE_ITEM_OPCODE,
                bytes([ISRO_UNEQUIP_OPERATION, DEVIL_EQUIPMENT_SLOT,
                       min(255, free_slots)]),
                False)
            set_state('UNEQUIPPING DEVIL', COLOR_WARNING)
            set_message('Removing Devil with %d free inventory slot(s)...' % free_slots,
                        COLOR_WARNING)
        else:
            workflow_phase = 'awakening'
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
    # Captured iSRO item-use requests use the encrypted Joymax path, while the
    # established Silkroad-R locale 65 profile uses the unencrypted path.
    inject_joymax(USE_ITEM_OPCODE, payload, get_locale() == ISRO_LOCALE)
    attempts_sent += 1
    waiting_result = True
    pending_devil_slot = devil['slot']
    pending_scroll_slot = scroll['slot']
    pending_since = time.time()
    set_state('WAITING FOR RESULT', COLOR_WARNING)
    set_message('Attempt %d sent to Devil slot %d.' % (attempts_sent, devil['slot']), COLOR_WARNING)
    update_live_values()


def event_loop():
    global last_inventory_refresh, next_action_time, workflow_phase
    global pending_devil_slot, pending_since, restore_required
    global completion_message, completion_color, completion_state
    global last_plus, last_duration
    now = time.time()
    if not running:
        if now - last_inventory_refresh >= INVENTORY_REFRESH_SECONDS:
            last_inventory_refresh = now
            update_live_values()
        return
    if workflow_phase in ('unequipping', 'cancel_after_unequip'):
        items = inventory_items()
        moved_slot = find_identity_in_inventory(items, original_devil_identity)
        if moved_slot >= 0:
            pending_devil_slot = moved_slot
            update_devil_label('%s (slot %d)' %
                               (original_devil_identity['name'], moved_slot))
            if workflow_phase == 'cancel_after_unequip':
                workflow_phase = 'restore_pending'
                set_state('RESTORING DEVIL', COLOR_WARNING)
                set_message('Stop confirmed; restoring the Devil...', COLOR_WARNING)
            else:
                workflow_phase = 'awakening'
                next_action_time = now + ISRO_POST_MOVE_DELAY_SECONDS
                set_state('RUNNING', COLOR_SUCCESS)
                set_message('Equipped Devil removed; awakening will begin.', COLOR_SUCCESS)
            return
        if now - pending_since > RESULT_TIMEOUT_SECONDS:
            restore_required_now = (len(items) > DEVIL_EQUIPMENT_SLOT and
                                    identity_matches(items[DEVIL_EQUIPMENT_SLOT],
                                                     original_devil_identity))
            if restore_required_now:
                restore_required = False
                completion_message = 'Unequip did not complete.'
                completion_color = COLOR_ERROR
                completion_state = 'TIMEOUT'
                finish_after_restore(True)
            else:
                stop_process('Timed out while removing the equipped Devil.', COLOR_ERROR, 'TIMEOUT')
        return
    if workflow_phase == 'restore_pending':
        items = inventory_items()
        if (len(items) > DEVIL_EQUIPMENT_SLOT and
                identity_matches(items[DEVIL_EQUIPMENT_SLOT], original_devil_identity)):
            restore_required = False
            finish_after_restore(True)
            return
        restore_slot = resolve_restore_slot(items)
        if restore_slot < 0:
            restore_required = False
            finish_after_restore(False)
            return
        pending_devil_slot = restore_slot
        workflow_phase = 'restoring'
        pending_since = now
        inject_joymax(
            MOVE_ITEM_OPCODE,
            bytes([ISRO_EQUIP_OPERATION, restore_slot, DEVIL_EQUIPMENT_SLOT]),
            False)
        set_state('RESTORING DEVIL', COLOR_WARNING)
        set_message('Equipping the original Devil in slot 4...', COLOR_WARNING)
        return
    if workflow_phase == 'restoring':
        items = inventory_items()
        if (len(items) > DEVIL_EQUIPMENT_SLOT and
                identity_matches(items[DEVIL_EQUIPMENT_SLOT], original_devil_identity)):
            finish_after_restore(True)
        elif now - pending_since > RESULT_TIMEOUT_SECONDS:
            restore_required = False
            finish_after_restore(False)
        return
    if workflow_phase == 'inventory_result':
        if now < next_action_time:
            return
        items = inventory_items()
        devil = resolve_devil(items)
        if not devil:
            stop_process('Devil inventory result could not be read safely.',
                         COLOR_ERROR, 'DEVIL LOST')
            return
        observed_plus = int(devil.get('plus') or 0)
        # A random roll can legitimately return the previous value. Wait for
        # phBot's inventory cache to settle, then accept the observed value.
        if observed_plus == last_plus and now - pending_since < ISRO_INVENTORY_SETTLE_SECONDS:
            next_action_time = now + 0.25
            return
        last_plus = observed_plus
        last_duration = 10800
        update_live_values(items)
        if last_plus >= target_plus:
            stop_process('Target reached: +%d from inventory data.' % last_plus,
                         COLOR_SUCCESS, 'TARGET REACHED')
        else:
            workflow_phase = 'awakening'
            next_action_time = now + ACTION_DELAY_SECONDS
            set_state('RUNNING', COLOR_SUCCESS)
            set_message('Inventory result +%d; target is +%d. Continuing...' %
                        (last_plus, target_plus), COLOR_WARNING)
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
    global workflow_phase, pending_devil_slot, pending_since, restore_required
    if not running:
        return True
    try:
        if opcode == MOVE_ITEM_RESPONSE_OPCODE and len(data) >= 2:
            if (workflow_phase in ('unequipping', 'cancel_after_unequip') and
                    data[1] == ISRO_UNEQUIP_OPERATION):
                if data[0] == 1 and len(data) >= 4:
                    pending_devil_slot = data[3]
                    update_devil_label('%s (slot %d)' %
                                       (original_devil_identity['name'], pending_devil_slot))
                    if workflow_phase == 'cancel_after_unequip':
                        workflow_phase = 'restore_pending'
                        set_state('RESTORING DEVIL', COLOR_WARNING)
                        set_message('Stop confirmed; restoring the Devil...', COLOR_WARNING)
                    else:
                        workflow_phase = 'awakening'
                        next_action_time = time.time() + ISRO_POST_MOVE_DELAY_SECONDS
                        set_state('RUNNING', COLOR_SUCCESS)
                        set_message('Equipped Devil removed; awakening will begin.', COLOR_SUCCESS)
                else:
                    restore_required = False
                    stop_process('Server rejected the Devil unequip request.',
                                 COLOR_ERROR, 'UNEQUIP REJECTED')
                return True
            if (len(data) >= 3 and workflow_phase == 'restoring' and
                    data[1] == ISRO_EQUIP_OPERATION and
                    data[2] == pending_devil_slot):
                if data[0] == 1:
                    finish_after_restore(True)
                else:
                    restore_required = False
                    finish_after_restore(False)
                return True
        if not waiting_result:
            return True
        if (opcode == USE_ITEM_RESPONSE_OPCODE and get_locale() == ISRO_LOCALE and
                len(data) >= 8 and data[0] == 1 and
                data[1] == pending_scroll_slot and
                bytes(data[4:8]) == AWAKENING_PAYLOAD_MIDDLE):
            waiting_result = False
            results_received += 1
            workflow_phase = 'inventory_result'
            pending_since = time.time()
            next_action_time = pending_since + 0.25
            remaining_scrolls = struct.unpack_from('<H', data, 2)[0]
            set_state('READING RESULT', COLOR_WARNING)
            set_message('Scroll accepted; reading Devil + from inventory (%d left)...' %
                        remaining_scrolls, COLOR_WARNING)
            update_live_values()
        elif (opcode == USE_ITEM_RESPONSE_OPCODE and get_locale() == ISRO_LOCALE and
              len(data) >= 3 and data[0] == 2):
            # iSRO emits unrelated, slotless B04C errors such as 0x183E and
            # 0x185B alongside accepted Awakening requests. They cannot be
            # correlated to our scroll slot, so keep waiting for a matching
            # success; the normal timeout remains the failure guard.
            error_code = struct.unpack_from('<H', data, 1)[0]
            plugin_log('Ignored uncorrelated iSRO B04C error 0x%04X while waiting.' %
                       error_code)
        elif opcode == USE_ITEM_RESPONSE_OPCODE and len(data) >= 3 and data[0] == 2:
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
    global restore_required, equipped_only_run
    if running:
        restore_required = False
        equipped_only_run = False
        stop_process('Disconnected; check the Devil equipment manually.',
                     COLOR_ERROR, 'DISCONNECTED')


load_settings()
QtBind.setEnabled(gui, txt_maximum, not use_all_scrolls)
QtBind.setEnabled(gui, cmb_mode, not only_equipped_devil)
QtBind.setEnabled(gui, lst_devils, not only_equipped_devil)
QtBind.setEnabled(gui, btn_refresh, not only_equipped_devil)
refresh_devils()

log('[%s] Loaded - \u269c Made By FascinaTe' % pName)
