from phBot import *
import QtBind
import time
import webbrowser
from threading import Timer


pName = 'FFateManager'
pVersion = '1.0.1'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

OPCODE_FATE_REQUEST = 0x7151
OPCODE_FATE_RESPONSE = 0xB151

COLOR_PRIMARY = '#5b57e0'
COLOR_TEXT = '#2b3038'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#d93a4d'

FATE_REQUEST_DELAY = 0.55
NEXT_ITEM_DELAY = 0.85
MAX_BLUE_LINES = 32

selected_inventory = []
queued_items = []
is_running = False
current_item_index = 0
awaiting_response = False
single_roll_item = None
pending_timer = None
timer_token = 0


def plugin_log(message):
    log('[%s] %s' % (pName, str(message)))


def fixed_width_text(content, width):
    return (
        '<table width="{0}" cellspacing="0" cellpadding="0">'
        '<tr><td>{1}</td></tr></table>'
    ).format(width, content)


def html_safe(value):
    return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def set_status(message, color=COLOR_MUTED):
    QtBind.setText(
        gui, lbl_status,
        fixed_width_text(
            '<font color="%s"><b>%s</b></font>' % (color, html_safe(message)), 700)
    )


def set_result(message, color=COLOR_MUTED):
    QtBind.setText(
        gui, lbl_result,
        fixed_width_text(
            '<font color="%s">%s</font>' % (color, html_safe(message)), 310)
    )


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        set_status('Opening Discord invite...', COLOR_SUCCESS)
    except Exception as error:
        plugin_log('Discord link error: %s' % error)
        set_status('Could not open Discord invite', COLOR_ERROR)


def item_is_eligible(item):
    try:
        data = get_item(int(item.get('model', 0)))
        return bool(data and int(data.get('tid1', 0)) == 1)
    except Exception:
        return False


def inventory_snapshot():
    inventory = get_inventory()
    if not inventory or 'items' not in inventory:
        return []
    result = []
    for slot, item in enumerate(inventory['items']):
        if slot < 13 or not item or not item_is_eligible(item):
            continue
        copied = dict(item)
        copied['slot'] = slot
        result.append(copied)
    return result


def find_inventory_item(slot):
    inventory = get_inventory()
    if not inventory or 'items' not in inventory:
        return None
    items = inventory['items']
    if slot < 0 or slot >= len(items):
        return None
    return items[slot]


def get_fate_slot():
    inventory = get_inventory()
    if not inventory or 'items' not in inventory:
        return None
    for slot, item in enumerate(inventory['items']):
        if item and 'Wheel of Fate' in str(item.get('name', '')):
            return slot
    return None


def selected_inventory_item():
    index = QtBind.currentIndex(gui, lst_inventory)
    if index < 0 or index >= len(selected_inventory):
        return None
    return selected_inventory[index]


def format_item(item):
    return 'Slot %d | +%s | %s' % (
        item['slot'], item.get('plus', 0), item.get('name', 'Unknown'))


def refresh_inventory():
    global selected_inventory
    selected_inventory = inventory_snapshot()
    QtBind.clear(gui, lst_inventory)
    for item in selected_inventory:
        QtBind.append(gui, lst_inventory, format_item(item))
    if selected_inventory:
        set_status('%d eligible inventory item(s) found' % len(selected_inventory), COLOR_SUCCESS)
    else:
        set_status('No eligible unequipped item was found', COLOR_WARNING)


def show_selected_item():
    item = selected_inventory_item()
    if not item:
        set_status('Select an inventory item first', COLOR_WARNING)
        return
    QtBind.setText(
        gui, lbl_selected,
        fixed_width_text(
            '<font color="%s"><b>%s</b></font>' % (
                COLOR_TEXT, html_safe(format_item(item))), 310)
    )
    set_status('Item selected; choose the target blue-line count', COLOR_MUTED)


def read_target_count():
    try:
        value = int(QtBind.text(gui, txt_target_count).strip())
    except Exception:
        return None
    if value < 1 or value > MAX_BLUE_LINES:
        return None
    return value


def add_to_queue():
    item = selected_inventory_item()
    if not item:
        set_status('Select an inventory item first', COLOR_WARNING)
        return
    target = read_target_count()
    if target is None:
        set_status('Target blue lines must be between 1 and %d' % MAX_BLUE_LINES, COLOR_ERROR)
        return
    queued = {
        'slot': item['slot'], 'model': item['model'],
        'name': item.get('name', 'Unknown'), 'plus': item.get('plus', 0),
        'target': target, 'last_count': None
    }
    for index, existing in enumerate(queued_items):
        if existing['slot'] == queued['slot']:
            queued_items[index] = queued
            refresh_queue()
            set_status('Queue target updated for slot %d' % queued['slot'], COLOR_SUCCESS)
            return
    queued_items.append(queued)
    refresh_queue()
    set_status('Item added to the Fate queue', COLOR_SUCCESS)


def refresh_queue():
    QtBind.clear(gui, lst_queue)
    for index, item in enumerate(queued_items):
        marker = '>' if is_running and index == current_item_index else ' '
        current = '?' if item['last_count'] is None else str(item['last_count'])
        QtBind.append(gui, lst_queue, '%s Slot %d | blue %s/%d | %s' % (
            marker, item['slot'], current, item['target'], item['name']))


def remove_queued_item():
    if is_running:
        set_status('Stop automation before editing the queue', COLOR_WARNING)
        return
    index = QtBind.currentIndex(gui, lst_queue)
    if index < 0 or index >= len(queued_items):
        set_status('Select a queued item first', COLOR_WARNING)
        return
    del queued_items[index]
    refresh_queue()
    set_status('Queued item removed', COLOR_MUTED)


def clear_queue():
    if is_running:
        set_status('Stop automation before clearing the queue', COLOR_WARNING)
        return
    queued_items[:] = []
    refresh_queue()
    set_status('Queue cleared', COLOR_MUTED)


def invalidate_timer():
    global pending_timer, timer_token, awaiting_response
    timer_token += 1
    awaiting_response = False
    if pending_timer:
        try:
            pending_timer.cancel()
        except Exception:
            pass
    pending_timer = None


def schedule_request(delay):
    global pending_timer, timer_token
    token = timer_token

    def callback():
        if is_running and token == timer_token:
            send_fate_request()

    pending_timer = Timer(delay, callback)
    pending_timer.daemon = True
    pending_timer.start()


def active_item():
    if current_item_index < 0 or current_item_index >= len(queued_items):
        return None
    return queued_items[current_item_index]


def build_request(item_slot, fate_slot):
    return b'\x02\x19\x02' + bytes([item_slot, fate_slot])


def send_fate_request():
    global awaiting_response
    if not is_running or awaiting_response:
        return
    item = active_item()
    if not item:
        stop_automation('All queued items completed', COLOR_SUCCESS)
        return
    live_item = find_inventory_item(item['slot'])
    if not live_item or live_item.get('model') != item['model']:
        stop_automation('Item moved or changed at slot %d' % item['slot'], COLOR_ERROR)
        return
    fate_slot = get_fate_slot()
    if fate_slot is None:
        stop_automation('Wheel of Fate not found', COLOR_ERROR)
        return
    if item['slot'] > 255 or fate_slot > 255:
        stop_automation('Inventory slot is outside packet range', COLOR_ERROR)
        return
    awaiting_response = True
    inject_joymax(OPCODE_FATE_REQUEST, build_request(item['slot'], fate_slot), False)
    set_status('Rolling %s for at least %d blue line(s)...' % (
        item['name'], item['target']), COLOR_WARNING)


def test_one_roll():
    global single_roll_item, awaiting_response
    if is_running:
        set_status('Stop automation before running a one-roll test', COLOR_WARNING)
        return
    if single_roll_item is not None or awaiting_response:
        set_status('A one-roll test is already waiting for a response', COLOR_WARNING)
        return
    item = selected_inventory_item()
    if not item:
        set_status('Select an inventory item first', COLOR_WARNING)
        return
    live_item = find_inventory_item(item['slot'])
    if not live_item or live_item.get('model') != item['model']:
        set_status('Selected item moved or changed', COLOR_ERROR)
        return
    fate_slot = get_fate_slot()
    if fate_slot is None:
        set_status('Wheel of Fate not found', COLOR_ERROR)
        return
    if item['slot'] > 255 or fate_slot > 255:
        set_status('Inventory slot is outside packet range', COLOR_ERROR)
        return
    single_roll_item = {
        'slot': item['slot'], 'model': item['model'],
        'name': item.get('name', 'Unknown')
    }
    awaiting_response = True
    inject_joymax(OPCODE_FATE_REQUEST, build_request(item['slot'], fate_slot), False)
    set_status('One-roll Fate test sent; waiting for 0xB151...', COLOR_WARNING)


def start_automation():
    global is_running, current_item_index
    if is_running:
        set_status('Automation is already running', COLOR_WARNING)
        return
    if single_roll_item is not None or awaiting_response:
        set_status('Wait for the one-roll test response', COLOR_WARNING)
        return
    if not queued_items:
        set_status('Add at least one item to the queue', COLOR_WARNING)
        return
    for item in queued_items:
        live_item = find_inventory_item(item['slot'])
        if not live_item or live_item.get('model') != item['model']:
            set_status('Queued item is no longer at slot %d' % item['slot'], COLOR_ERROR)
            return
    if get_fate_slot() is None:
        set_status('Wheel of Fate not found', COLOR_ERROR)
        return
    current_item_index = 0
    is_running = True
    invalidate_timer()
    refresh_queue()
    set_status('Fate automation started', COLOR_SUCCESS)
    send_fate_request()


def stop_automation(message='Automation stopped', color=COLOR_WARNING):
    global is_running
    is_running = False
    invalidate_timer()
    refresh_queue()
    set_status(message, color)


def parse_blue_line_count(data):
    # All supplied live Fate responses use the standard equipment layout:
    # slot at byte 4 and total magic-option record count at byte 26. That count
    # includes one internal 0x40 record which is not a visible blue line.
    # Stat IDs and values are irrelevant to Fate targets and are intentionally
    # not decoded here.
    packet_length = len(data)
    if packet_length < 35:
        return None
    record_count = data[26]
    if record_count < 1 or record_count > MAX_BLUE_LINES + 1:
        return None
    # The verified layout has a 35-byte item header, bounded option data, and
    # an 8-byte response suffix. Reject truncated packets before trusting the
    # header count. The internal option is represented by the leading marker;
    # each visible blue line contributes an 8-byte record.
    blue_count = record_count - 1
    minimum_length = 43 + (blue_count * 8)
    if packet_length < minimum_length:
        return None
    return blue_count


def response_slot(data):
    if len(data) < 5 or data[0] != 1 or data[2] != 1:
        return None
    return data[4]


def log_response_raw(label, data):
    plugin_log('%s 0xB151 raw (%d bytes): %s%s' % (
        label, len(data), ' '.join('%02X' % value for value in data[:512]),
        ' ...' if len(data) > 512 else ''))


def process_one_roll_response(data):
    global single_roll_item, awaiting_response
    item = single_roll_item
    single_roll_item = None
    awaiting_response = False
    if not item:
        return
    slot = response_slot(data)
    count = parse_blue_line_count(data)
    log_response_raw('One-roll', data)
    if slot != item['slot']:
        set_result('Rejected response: unexpected item slot', COLOR_ERROR)
        set_status('One-roll response did not match the selected item', COLOR_ERROR)
        return
    if count is None:
        set_result('0xB151 received; blue-line layout was not verified', COLOR_ERROR)
        set_status('One-roll response could not be decoded; raw packet logged', COLOR_ERROR)
        return
    set_result('Last one-roll result: %d blue line(s)' % count, COLOR_SUCCESS)
    set_status('One-roll test completed; no repeat was scheduled', COLOR_SUCCESS)
    plugin_log('One-roll slot %d result: %d blue line(s)' % (item['slot'], count))


def process_fate_response(data):
    global current_item_index, awaiting_response
    item = active_item()
    awaiting_response = False
    if not item:
        return
    slot = response_slot(data)
    count = parse_blue_line_count(data)
    if slot != item['slot']:
        log_response_raw('Unexpected-slot automation response', data)
        stop_automation('Response item slot did not match; automation stopped', COLOR_ERROR)
        return
    if count is None:
        log_response_raw('Automation decode failure', data)
        stop_automation('Blue-line count could not be verified; automation stopped', COLOR_ERROR)
        return
    item['last_count'] = count
    set_result('Slot %d result: %d blue line(s)' % (item['slot'], count), COLOR_SUCCESS)
    plugin_log('Slot %d result: %d/%d blue line(s)' % (
        item['slot'], count, item['target']))
    if count >= item['target']:
        current_item_index += 1
        refresh_queue()
        if current_item_index >= len(queued_items):
            stop_automation('All Fate targets reached', COLOR_SUCCESS)
        else:
            set_status('Target reached; moving to the next item', COLOR_SUCCESS)
            schedule_request(NEXT_ITEM_DELAY)
    else:
        refresh_queue()
        schedule_request(FATE_REQUEST_DELAY)


def disconnected():
    global single_roll_item
    single_roll_item = None
    if is_running or awaiting_response:
        stop_automation('Disconnected; automation stopped', COLOR_ERROR)
    else:
        invalidate_timer()
        set_status('Disconnected', COLOR_MUTED)


def handle_joymax(opcode, data):
    try:
        if opcode == OPCODE_FATE_RESPONSE:
            if single_roll_item is not None:
                process_one_roll_response(data)
            elif is_running and awaiting_response:
                process_fate_response(data)
    except Exception as error:
        plugin_log('Packet processing error for 0x%04X: %s' % (opcode, error))
        if opcode == OPCODE_FATE_RESPONSE and (is_running or awaiting_response):
            stop_automation('Packet processing failed; automation stopped', COLOR_ERROR)
    return True


# GUI
gui = QtBind.init(__name__, pName)

QtBind.createLabel(gui, '<font color="%s" size="4"><b>✦ %s</b></font>' % (
    COLOR_PRIMARY, pName), 12, 6)
QtBind.createLabel(gui, '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion), 190, 12)
QtBind.createButton(gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(
    gui, u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' % COLOR_PRIMARY,
    565, 11)
QtBind.createLineEdit(gui, '', 12, 30, 716, 1)

QtBind.createLabel(gui, '<font color="%s"><b>1. ELIGIBLE INVENTORY</b></font>' % COLOR_PRIMARY, 12, 44)
QtBind.createLabel(gui, fixed_width_text(
    '<font color="%s">Select an unequipped item, then test or queue it.</font>' % COLOR_MUTED,
    350), 12, 64)
btn_refresh = QtBind.createButton(gui, 'refresh_inventory', '↻ Refresh', 12, 88)
btn_inspect = QtBind.createButton(gui, 'show_selected_item', 'Select Item', 105, 88)
btn_test = QtBind.createButton(gui, 'test_one_roll', 'Test One Roll', 205, 88)
lst_inventory = QtBind.createList(gui, 12, 116, 350, 130)

QtBind.createLineEdit(gui, '', 378, 44, 1, 205)
QtBind.createLabel(gui, '<font color="%s"><b>2. TARGET & QUEUE</b></font>' % COLOR_PRIMARY, 394, 44)
lbl_selected = QtBind.createLabel(gui, fixed_width_text(
    '<font color="%s"><b>No item selected</b></font>' % COLOR_MUTED, 310), 394, 65)
QtBind.createLabel(gui, 'Target blue lines', 394, 92)
txt_target_count = QtBind.createLineEdit(gui, '6', 494, 88, 42, 20)
QtBind.createButton(gui, 'add_to_queue', 'Add / Update Queue', 548, 85)
lst_queue = QtBind.createList(gui, 394, 116, 322, 100)
QtBind.createButton(gui, 'remove_queued_item', 'Remove', 394, 222)
QtBind.createButton(gui, 'clear_queue', 'Clear', 478, 222)
QtBind.createButton(gui, 'start_automation', '▶ START', 558, 222)
QtBind.createButton(gui, 'stop_automation', '■ STOP', 647, 222)

lbl_result = QtBind.createLabel(gui, fixed_width_text(
    '<font color="%s">No verified Fate result yet</font>' % COLOR_MUTED, 310), 12, 257)
lbl_status = QtBind.createLabel(gui, fixed_width_text(
    '<font color="%s"><b>Ready</b></font>' % COLOR_MUTED, 700), 12, 282)

refresh_inventory()
set_result('Use Test One Roll to verify the first result', COLOR_WARNING)

log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
