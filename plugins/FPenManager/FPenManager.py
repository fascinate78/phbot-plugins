from phBot import *
import QtBind
import struct
import webbrowser
from threading import Timer


pName = 'FPenManager'
pVersion = '1.0.0'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

OPCODE_PEN_REQUEST = 0x7151
OPCODE_PEN_RESPONSE = 0xB151
PEN_ITEM_NAME = 'Feather Pen of Fortune'

COLOR_PRIMARY = '#5b57e0'
COLOR_TEXT = '#2b3038'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#d93a4d'
OFFSCREEN_X = 3000
ROLL_DELAY = 1.55
NEXT_ITEM_DELAY = 0.80
MAX_TARGET_VALUE = 2147483647

# Verified classic response codes used by the server. Repeated records with the
# same name are intentionally summed before targets are evaluated.
STAT_CODES = {
    0x39: 'STR', 0x53: 'STR', 0x54: 'STR', 0x55: 'STR',
    0x3A: 'INT', 0x56: 'INT', 0x57: 'INT', 0x58: 'INT',
    0x3B: 'Durability', 0x59: 'Durability', 0x5A: 'Durability',
    0x3C: 'Attack Rate', 0x5C: 'Attack Rate',
    0x3D: 'Evade Block', 0x5F: 'Evade Block',
    0x3E: 'Evade Critical', 0x3F: 'Parry Ratio', 0x65: 'Parry Ratio',
    0x40: 'HP', 0x68: 'HP', 0x41: 'MP', 0x6B: 'MP',
    0x42: 'Frostbite Resist', 0x43: 'Lightning Resist',
    0x44: 'Fire Resist', 0x45: 'Poison Resist', 0x46: 'Zombie Resist',
    0x47: 'Critical', 0x7D: 'Critical', 0x7E: 'Critical',
    0x48: 'Block', 0x49: 'Stun Resist',
    0x4A: 'HP/MP Recovery', 0x4B: 'Combustion Resist',
    0x4C: 'Disease Resist', 0x4D: 'Sleep Resist', 0x4E: 'Fear Resist'
}
STAT_NAMES = []
for _stat_name in STAT_CODES.values():
    if _stat_name not in STAT_NAMES:
        STAT_NAMES.append(_stat_name)

selected_inventory = []
current_targets = []
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
    return ('<table width="{0}" cellspacing="0" cellpadding="0">'
            '<tr><td>{1}</td></tr></table>').format(width, content)


def html_safe(value):
    return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def set_status(message, color=COLOR_MUTED):
    QtBind.setText(gui, lbl_status, fixed_width_text(
        '<font color="%s"><b>%s</b></font>' % (color, html_safe(message)), 680))


def set_result(message, color=COLOR_MUTED):
    QtBind.setText(gui, lbl_result, fixed_width_text(
        '<font color="%s">%s</font>' % (color, html_safe(message)), 470))


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
    return items[slot] if 0 <= slot < len(items) else None


def get_pen_slot():
    inventory = get_inventory()
    if not inventory or 'items' not in inventory:
        return None
    for slot, item in enumerate(inventory['items']):
        if item and PEN_ITEM_NAME in str(item.get('name', '')):
            return slot
    return None


def selected_inventory_item():
    index = QtBind.currentIndex(gui, lst_inventory)
    return selected_inventory[index] if 0 <= index < len(selected_inventory) else None


def format_item(item):
    return 'Slot %d | +%s | %s' % (
        item['slot'], item.get('plus', 0), item.get('name', 'Unknown'))


def refresh_inventory():
    global selected_inventory
    selected_inventory = inventory_snapshot()
    QtBind.clear(gui, lst_inventory)
    for item in selected_inventory:
        QtBind.append(gui, lst_inventory, format_item(item))
    set_status('%d eligible inventory item(s) found' % len(selected_inventory),
               COLOR_SUCCESS if selected_inventory else COLOR_WARNING)


def show_selected_item():
    item = selected_inventory_item()
    if not item:
        set_status('Select an inventory item first', COLOR_WARNING)
        return
    QtBind.setText(gui, lbl_selected, fixed_width_text(
        '<font color="%s"><b>%s</b></font>' % (COLOR_TEXT, html_safe(format_item(item))), 350))
    set_status('Item selected; add minimum total stat targets', COLOR_MUTED)


def read_target_value():
    try:
        value = int(QtBind.text(gui, txt_target_value).strip())
    except Exception:
        return None
    return value if 1 <= value <= MAX_TARGET_VALUE else None


def refresh_targets():
    QtBind.clear(gui, lst_targets)
    for target in current_targets:
        QtBind.append(gui, lst_targets, '%s >= %d total' % (target['name'], target['value']))


def add_target():
    name = QtBind.text(gui, lst_stats)
    value = read_target_value()
    if not name:
        set_status('Select a stat first', COLOR_WARNING)
        return
    if value is None:
        set_status('Target value must be a positive integer', COLOR_ERROR)
        return
    for target in current_targets:
        if target['name'] == name:
            target['value'] = value
            refresh_targets()
            set_status('Updated %s target to %d total' % (name, value), COLOR_SUCCESS)
            return
    current_targets.append({'name': name, 'value': value})
    refresh_targets()
    set_status('Added %s target: %d total' % (name, value), COLOR_SUCCESS)


def remove_target():
    index = QtBind.currentIndex(gui, lst_targets)
    if index < 0 or index >= len(current_targets):
        set_status('Select a target to remove', COLOR_WARNING)
        return
    removed = current_targets.pop(index)
    refresh_targets()
    set_status('Removed %s target' % removed['name'], COLOR_MUTED)


def add_to_queue():
    item = selected_inventory_item()
    if not item:
        set_status('Select an inventory item first', COLOR_WARNING)
        return
    if not current_targets:
        set_status('Add at least one stat target', COLOR_WARNING)
        return
    queued = {'slot': item['slot'], 'model': item['model'],
              'name': item.get('name', 'Unknown'),
              'targets': [dict(value) for value in current_targets], 'totals': {}}
    for index, existing in enumerate(queued_items):
        if existing['slot'] == queued['slot']:
            queued_items[index] = queued
            refresh_queue()
            set_status('Queue targets updated for slot %d' % queued['slot'], COLOR_SUCCESS)
            return
    queued_items.append(queued)
    refresh_queue()
    set_status('Item added to the Pen queue', COLOR_SUCCESS)


def target_summary(item):
    parts = []
    for target in item['targets']:
        current = item['totals'].get(target['name'])
        parts.append('%s %s/%d' % (
            target['name'], '?' if current is None else current, target['value']))
    return ', '.join(parts)


def refresh_queue():
    QtBind.clear(gui, lst_queue)
    for index, item in enumerate(queued_items):
        marker = '>' if is_running and index == current_item_index else ' '
        QtBind.append(gui, lst_queue, '%s Slot %d | %s | %s' % (
            marker, item['slot'], target_summary(item), item['name']))


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
    global pending_timer
    token = timer_token
    def callback():
        if is_running and token == timer_token:
            send_pen_request()
    pending_timer = Timer(delay, callback)
    pending_timer.daemon = True
    pending_timer.start()


def active_item():
    return queued_items[current_item_index] if 0 <= current_item_index < len(queued_items) else None


def send_request_for(item):
    pen_slot = get_pen_slot()
    if pen_slot is None:
        return False, 'Feather Pen of Fortune not found'
    if item['slot'] > 255 or pen_slot > 255:
        return False, 'Inventory slot is outside packet range'
    inject_joymax(OPCODE_PEN_REQUEST,
                  b'\x02\x19\x02' + bytes([item['slot'], pen_slot]), False)
    return True, ''


def send_pen_request():
    global awaiting_response
    if not is_running or awaiting_response:
        return
    item = active_item()
    if not item:
        stop_automation('All Pen targets reached', COLOR_SUCCESS)
        return
    live_item = find_inventory_item(item['slot'])
    if not live_item or live_item.get('model') != item['model']:
        stop_automation('Item moved or changed at slot %d' % item['slot'], COLOR_ERROR)
        return
    ok, error = send_request_for(item)
    if not ok:
        stop_automation(error, COLOR_ERROR)
        return
    awaiting_response = True
    set_status('Applying Feather Pen to %s...' % item['name'], COLOR_WARNING)


def test_one_roll():
    global single_roll_item, awaiting_response
    if is_running or awaiting_response:
        set_status('Stop or wait for the current request first', COLOR_WARNING)
        return
    item = selected_inventory_item()
    if not item:
        set_status('Select an inventory item first', COLOR_WARNING)
        return
    single_roll_item = {'slot': item['slot'], 'model': item['model'], 'name': item.get('name', 'Unknown')}
    ok, error = send_request_for(single_roll_item)
    if not ok:
        single_roll_item = None
        set_status(error, COLOR_ERROR)
        return
    awaiting_response = True
    set_status('One-roll Pen test sent; waiting for 0xB151...', COLOR_WARNING)


def start_automation():
    global is_running, current_item_index
    if is_running or awaiting_response:
        set_status('Automation is running or a response is pending', COLOR_WARNING)
        return
    if not queued_items:
        set_status('Add at least one item to the queue', COLOR_WARNING)
        return
    for item in queued_items:
        live = find_inventory_item(item['slot'])
        if not live or live.get('model') != item['model']:
            set_status('Queued item is no longer at slot %d' % item['slot'], COLOR_ERROR)
            return
    if get_pen_slot() is None:
        set_status('Feather Pen of Fortune not found', COLOR_ERROR)
        return
    current_item_index = 0
    is_running = True
    invalidate_timer()
    refresh_queue()
    set_status('Pen automation started', COLOR_SUCCESS)
    send_pen_request()


def stop_automation(message='Automation stopped', color=COLOR_WARNING):
    global is_running
    is_running = False
    invalidate_timer()
    refresh_queue()
    set_status(message, color)


def parse_change_header(data):
    # Live layout: 01 02 01 02, uint16 ASCII length, key, uint32 old/new.
    if len(data) < 14 or data[:4] != b'\x01\x02\x01\x02':
        return None
    length = struct.unpack_from('<H', data, 4)[0]
    end = 6 + length
    if length < 1 or end + 8 > len(data):
        return None
    try:
        key = bytes(data[6:end]).decode('ascii')
    except Exception:
        return None
    return {'key': key, 'old': struct.unpack_from('<I', data, end)[0],
            'new': struct.unpack_from('<I', data, end + 4)[0], 'end': end + 8}


def parse_stat_records(data, header):
    # In every supplied Pen response the item section relative to header.end is:
    # slot(1), item header(21), record count(1), seven zero bytes, internal 0x40,
    # then count-1 visible 8-byte records. Reject unknown/truncated records so an
    # incomplete total can never keep spending Pens.
    count_position = header['end'] + 22
    internal_position = header['end'] + 30
    records_start = header['end'] + 31
    if internal_position >= len(data) or data[internal_position] != 0x40:
        return []
    record_count = data[count_position]
    visible_count = record_count - 1
    if record_count < 2 or visible_count > 32:
        return []
    if records_start + (visible_count * 8) > len(data):
        return []
    records = []
    for index in range(visible_count):
        cursor = records_start + (index * 8)
        group = data[cursor:cursor + 8]
        if (group[1] != 0x02 or group[2] != 0 or group[3] != 0 or
                group[5] != 0 or group[6] != 0 or group[7] != 0 or group[4] == 0):
            return []
        name = STAT_CODES.get(group[0])
        if not name:
            plugin_log('Unknown Pen stat code 0x%02X at response offset %d' % (
                group[0], cursor))
            return []
        records.append({'code': group[0], 'name': name,
                        'value': group[4], 'offset': cursor})
    return records


def aggregate_totals(records):
    totals = {}
    for record in records:
        totals[record['name']] = totals.get(record['name'], 0) + record['value']
    return totals


def format_totals(totals):
    return ', '.join('%s=%d' % pair for pair in sorted(totals.items()))


def response_slot(data, header):
    return data[header['end']] if header and header['end'] < len(data) else None


def decode_response(data):
    header = parse_change_header(data)
    if not header:
        return None
    records = parse_stat_records(data, header)
    if not records:
        return None
    return header, records, aggregate_totals(records), response_slot(data, header)


def targets_met(totals, targets):
    return all(totals.get(target['name'], 0) >= target['value'] for target in targets)


def log_raw(label, data):
    plugin_log('%s 0xB151 raw (%d bytes): %s%s' % (
        label, len(data), ' '.join('%02X' % value for value in data[:512]),
        ' ...' if len(data) > 512 else ''))


def process_one_roll(data):
    global single_roll_item, awaiting_response
    item = single_roll_item
    single_roll_item = None
    awaiting_response = False
    decoded = decode_response(data)
    log_raw('One-roll', data)
    if not item or not decoded:
        set_result('0xB151 layout could not be verified; raw packet logged', COLOR_ERROR)
        set_status('One-roll response rejected', COLOR_ERROR)
        return
    header, records, totals, slot = decoded
    if slot != item['slot']:
        set_status('One-roll response item slot did not match', COLOR_ERROR)
        return
    set_result('%s: %d -> %d | totals: %s' % (
        header['key'], header['old'], header['new'], format_totals(totals)), COLOR_SUCCESS)
    plugin_log('Slot %d one-roll totals: %s' % (item['slot'], format_totals(totals)))
    set_status('One-roll test completed; no repeat was scheduled', COLOR_SUCCESS)


def process_response(data):
    global current_item_index, awaiting_response
    item = active_item()
    awaiting_response = False
    decoded = decode_response(data)
    if not item or not decoded:
        log_raw('Automation decode failure', data)
        stop_automation('Response layout could not be verified; automation stopped', COLOR_ERROR)
        return
    header, records, totals, slot = decoded
    if slot != item['slot']:
        log_raw('Unexpected-slot response', data)
        stop_automation('Response item slot did not match; automation stopped', COLOR_ERROR)
        return
    item['totals'] = totals
    set_result('%s: %d -> %d | totals: %s' % (
        header['key'], header['old'], header['new'], format_totals(totals)), COLOR_SUCCESS)
    plugin_log('Slot %d totals: %s | targets: %s' % (
        item['slot'], format_totals(totals), target_summary(item)))
    if targets_met(totals, item['targets']):
        current_item_index += 1
        refresh_queue()
        if current_item_index >= len(queued_items):
            stop_automation('All Pen targets reached', COLOR_SUCCESS)
        else:
            set_status('Targets reached; moving to the next item', COLOR_SUCCESS)
            schedule_request(NEXT_ITEM_DELAY)
    else:
        refresh_queue()
        schedule_request(ROLL_DELAY)


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
        if opcode == OPCODE_PEN_RESPONSE:
            if single_roll_item is not None:
                process_one_roll(data)
            elif is_running and awaiting_response:
                process_response(data)
    except Exception as error:
        plugin_log('Packet processing error for 0x%04X: %s' % (opcode, error))
        if opcode == OPCODE_PEN_RESPONSE and (is_running or awaiting_response):
            stop_automation('Packet processing failed; automation stopped', COLOR_ERROR)
    return True


def move_page(widgets, visible):
    for widget, x, y in widgets:
        QtBind.move(gui, widget, x if visible else OFFSCREEN_X, y)


def show_queue_page():
    move_page(setup_widgets, False)
    move_page(queue_widgets, True)
    QtBind.move(gui, btn_queue_page, OFFSCREEN_X, 6)
    QtBind.move(gui, btn_setup_page, 350, 6)
    refresh_queue()


def show_setup_page():
    move_page(queue_widgets, False)
    move_page(setup_widgets, True)
    QtBind.move(gui, btn_setup_page, OFFSCREEN_X, 6)
    QtBind.move(gui, btn_queue_page, 350, 6)


gui = QtBind.init(__name__, pName)
QtBind.createLabel(gui, '<font color="%s" size="4"><b>✦ %s</b></font>' % (COLOR_PRIMARY, pName), 12, 6)
QtBind.createLabel(gui, '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion), 185, 12)
btn_queue_page = QtBind.createButton(gui, 'show_queue_page', 'Queue & Start →', 350, 6)
btn_setup_page = QtBind.createButton(gui, 'show_setup_page', '← Item Setup', OFFSCREEN_X, 6)
QtBind.createButton(gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(gui, u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' % COLOR_PRIMARY, 565, 11)
QtBind.createLineEdit(gui, '', 12, 30, 716, 1)

setup_widgets = []
queue_widgets = []

lbl_inventory_header = QtBind.createLabel(gui, '<font color="%s"><b>1. ELIGIBLE INVENTORY</b></font>' % COLOR_PRIMARY, 12, 44)
btn_refresh = QtBind.createButton(gui, 'refresh_inventory', '↻ Refresh', 12, 66)
btn_select = QtBind.createButton(gui, 'show_selected_item', 'Select Item', 105, 66)
btn_test = QtBind.createButton(gui, 'test_one_roll', 'Test One Roll', 205, 66)
lst_inventory = QtBind.createList(gui, 12, 94, 360, 150)
lbl_selected = QtBind.createLabel(gui, fixed_width_text('<font color="%s"><b>No item selected</b></font>' % COLOR_MUTED, 350), 12, 256)
divider = QtBind.createLineEdit(gui, '', 385, 44, 1, 244)
lbl_stats_header = QtBind.createLabel(gui, '<font color="%s"><b>2. TOTAL STAT TARGETS</b></font>' % COLOR_PRIMARY, 400, 44)
lst_stats = QtBind.createList(gui, 400, 66, 145, 142)
for _stat_name in STAT_NAMES:
    QtBind.append(gui, lst_stats, _stat_name)
lst_targets = QtBind.createList(gui, 558, 66, 158, 142)
lbl_minimum_total = QtBind.createLabel(gui, 'Minimum total', 400, 222)
txt_target_value = QtBind.createLineEdit(gui, '10', 482, 218, 55, 20)
btn_add_target = QtBind.createButton(gui, 'add_target', 'Add / Update', 548, 215)
btn_remove_target = QtBind.createButton(gui, 'remove_target', 'Remove Target', 558, 246)
btn_add_queue = QtBind.createButton(gui, 'add_to_queue', 'Add Item to Queue', 400, 246)

setup_widgets.extend([
    (lbl_inventory_header, 12, 44), (btn_refresh, 12, 66), (btn_select, 105, 66),
    (btn_test, 205, 66), (lst_inventory, 12, 94), (lbl_selected, 12, 256),
    (divider, 385, 44), (lbl_stats_header, 400, 44), (lst_stats, 400, 66),
    (lst_targets, 558, 66), (lbl_minimum_total, 400, 222),
    (txt_target_value, 482, 218),
    (btn_add_target, 548, 215), (btn_remove_target, 558, 246),
    (btn_add_queue, 400, 246)])

lbl_queue_header = QtBind.createLabel(gui, '<font color="%s"><b>3. PEN AUTOMATION QUEUE</b></font>' % COLOR_PRIMARY, OFFSCREEN_X, 48)
lbl_queue_help = QtBind.createLabel(gui, fixed_width_text('<font color="%s">Repeated stat rows are summed; every configured minimum must be reached.</font>' % COLOR_MUTED, 650), OFFSCREEN_X, 70)
lst_queue = QtBind.createList(gui, OFFSCREEN_X, 94, 535, 118)
btn_remove_queue = QtBind.createButton(gui, 'remove_queued_item', 'Remove Item', OFFSCREEN_X, 94)
btn_clear_queue = QtBind.createButton(gui, 'clear_queue', 'Clear Queue', OFFSCREEN_X, 126)
btn_start = QtBind.createButton(gui, 'start_automation', '▶ START', OFFSCREEN_X, 226)
btn_stop = QtBind.createButton(gui, 'stop_automation', '■ STOP', OFFSCREEN_X, 226)
lbl_result = QtBind.createLabel(gui, fixed_width_text('<font color="%s">No verified Pen result yet</font>' % COLOR_MUTED, 470), OFFSCREEN_X, 232)
lbl_status = QtBind.createLabel(gui, fixed_width_text('<font color="%s"><b>Ready</b></font>' % COLOR_MUTED, 680), OFFSCREEN_X, 272)

queue_widgets.extend([
    (lbl_queue_header, 12, 48), (lbl_queue_help, 12, 70), (lst_queue, 12, 94),
    (btn_remove_queue, 560, 94), (btn_clear_queue, 560, 126),
    (btn_start, 12, 226), (btn_stop, 108, 226), (lbl_result, 210, 232),
    (lbl_status, 12, 272)])

refresh_inventory()
set_result('Use Test One Roll to verify the first Pen response', COLOR_WARNING)

log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
