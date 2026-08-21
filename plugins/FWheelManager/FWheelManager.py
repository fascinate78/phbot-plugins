from phBot import *
import QtBind
import struct
import webbrowser
from threading import Timer


pName = 'FWheelManager'
pVersion = '1.0.1'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

OPCODE_REQUEST = 0x7151
OPCODE_RESPONSE = 0xB151
COLOR_PRIMARY = '#5b57e0'
COLOR_TEXT = '#2b3038'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#d93a4d'
OFFSCREEN_X = 3000
MAX_LINES = 32
MAX_TARGET_VALUE = 2147483647

MODES = ('fate', 'fortune', 'pen')
MODE_LABELS = {'fate': 'Fate', 'fortune': 'Fortune', 'pen': 'Pen'}
MODE_DELAYS = {'fate': 0.55, 'fortune': 0.45, 'pen': 1.55}
NEXT_ITEM_DELAY = 0.85
CONSUMABLE_NAMES = {
    'fate': ('Wheel of Fate', 'Wheel of Fortune'),
    'fortune': ('Wheel of Fortune',),
    'pen': ('Feather Pen of Fortune',)
}

WEAPON_STATS = ['STR', 'INT', 'Durability', 'Attack Rate', 'Evade Block', 'Critical']
SHIELD_STATS = ['STR', 'INT', 'Durability', 'Evade Critical', 'Block']
ARMOR_STATS = {
    1: ['STR', 'INT', 'Durability', 'Parry Ratio', 'HP', 'MP'],
    2: ['STR', 'INT', 'Durability', 'Parry Ratio'],
    3: ['STR', 'INT', 'Durability', 'Parry Ratio', 'HP', 'MP', 'HP/MP Recovery'],
    4: ['STR', 'INT', 'Durability', 'Parry Ratio', 'HP', 'MP'],
    5: ['STR', 'INT', 'Durability', 'Parry Ratio'],
    6: ['STR', 'INT', 'Durability', 'Parry Ratio']
}
ACCESSORY_BASE_STATS = [
    'STR', 'INT', 'Frostbite Resist', 'Fire Resist', 'Lightning Resist',
    'Poison Resist', 'Zombie Resist'
]
ACCESSORY_STATS = {
    1: ACCESSORY_BASE_STATS + ['CSMP Resist', 'Sleep Resist'],
    2: ACCESSORY_BASE_STATS + ['Stun Resist'],
    3: ACCESSORY_BASE_STATS + ['Disease Resist', 'Fear Resist']
}
WEAPON_NAMES = {
    2: 'Sword', 3: 'Blade', 4: 'Spear', 5: 'Glaive', 6: 'Bow',
    7: 'One-handed Sword', 8: 'Two-handed Sword', 9: 'Axe',
    10: 'Warlock Rod', 11: 'Staff', 12: 'Crossbow', 13: 'Dagger',
    14: 'Harp', 15: 'Cleric Rod'
}
ARMOR_NAMES = {1: 'Head', 2: 'Shoulder', 3: 'Chest', 4: 'Legs', 5: 'Hands', 6: 'Foot'}
ACCESSORY_NAMES = {1: 'Earring', 2: 'Necklace', 3: 'Ring'}

CLASSIC_CODES = {
    0x0A: 'STR', 0x0B: 'INT', 0x0C: 'Durability', 0x0F: 'Evade Critical',
    0x10: 'Parry Ratio', 0x11: 'HP', 0x12: 'MP', 0x13: 'Frostbite Resist',
    0x14: 'Lightning Resist', 0x15: 'Fire Resist', 0x16: 'Poison Resist',
    0x17: 'Zombie Resist', 0x19: 'Block', 0x1A: 'Stun Resist',
    0x1C: 'CSMP Resist', 0x1D: 'Disease Resist', 0x1E: 'Sleep Resist',
    0x1F: 'Fear Resist', 0x39: 'STR', 0x53: 'STR', 0x54: 'STR',
    0x55: 'STR', 0x3A: 'INT', 0x56: 'INT', 0x57: 'INT', 0x58: 'INT',
    0x3B: 'Durability', 0x59: 'Durability', 0x5A: 'Durability',
    0x47: 'Critical', 0x7D: 'Critical', 0x7E: 'Critical',
    0x3C: 'Attack Rate', 0x5C: 'Attack Rate', 0x3D: 'Block Rate',
    0x5F: 'Block Rate', 0x40: 'HP', 0x68: 'HP', 0x41: 'MP', 0x6B: 'MP',
    0x49: 'Stun', 0x4A: 'HP/MP Recovery', 0x4B: 'Combustion',
    0x4C: 'Disease', 0x4D: 'Sleep', 0x4E: 'Fear'
}
# High-degree weapon family verified from this server's Fortune responses.
# These codes overlap with classic meanings, so they must only be applied
# after the selected item has been classified as a weapon.
WEAPON_CONTEXT_CODES = {
    0x69: 'STR', 0x6A: 'INT', 0x6B: 'Durability',
    0x6C: 'Attack Rate', 0x6D: 'Evade Block', 0x77: 'Critical'
}
DG12_CODES = {
    0x0049: 'STR', 0x004F: 'INT', 0x0067: 'Attack Rate',
    0x0073: 'Evade Block', 0x008B: 'HP', 0x0097: 'MP', 0x010C: 'Critical'
}
IGNORED_RESPONSE_STATS = {'Athanasia', 'Solid', 'Luck', 'Repair'}
PEN_STAT_CODES = {
    0x39: 'STR', 0x53: 'STR', 0x54: 'STR', 0x55: 'STR',
    0x3A: 'INT', 0x56: 'INT', 0x57: 'INT', 0x58: 'INT',
    0x3B: 'Durability', 0x59: 'Durability', 0x5A: 'Durability',
    0x3C: 'Attack Rate', 0x5C: 'Attack Rate', 0x3D: 'Evade Block',
    0x5F: 'Evade Block', 0x3E: 'Evade Critical', 0x3F: 'Parry Ratio',
    0x65: 'Parry Ratio', 0x40: 'HP', 0x68: 'HP', 0x41: 'MP', 0x6B: 'MP',
    0x42: 'Frostbite Resist', 0x43: 'Lightning Resist', 0x44: 'Fire Resist',
    0x45: 'Poison Resist', 0x46: 'Zombie Resist', 0x47: 'Critical',
    0x7D: 'Critical', 0x7E: 'Critical', 0x48: 'Block', 0x49: 'Stun Resist',
    0x4A: 'HP/MP Recovery', 0x4B: 'Combustion Resist', 0x4C: 'Disease Resist',
    0x4D: 'Sleep Resist', 0x4E: 'Fear Resist'
}
PEN_STATS = []
for _name in PEN_STAT_CODES.values():
    if _name not in PEN_STATS:
        PEN_STATS.append(_name)

states = {}
for _mode in MODES:
    states[_mode] = {
        'inventory': [], 'queue': [], 'targets': [], 'available': [],
        'selected': None, 'index': 0, 'last_result': None
    }
test_items = {mode: None for mode in MODES}

visible_mode = 'fate'
visible_page = 'setup'
active_mode = None
awaiting_response = False
single_roll = False
timer_token = 0
pending_timer = None


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


def set_result(mode, message, color=COLOR_MUTED):
    states[mode]['last_result'] = message
    QtBind.setText(gui, result_labels[mode], fixed_width_text(
        '<font color="%s">%s</font>' % (color, html_safe(message)), 680))


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        set_status('Opening Discord invite...', COLOR_SUCCESS)
    except Exception as error:
        plugin_log('Discord link error: %s' % error)
        set_status('Could not open Discord invite', COLOR_ERROR)


def item_classification(item):
    try:
        data = get_item(int(item.get('model', 0)))
    except Exception:
        data = None
    if not data or int(data.get('tid1', 0)) != 1:
        return None
    tid2 = int(data.get('tid2', 0))
    tid3 = int(data.get('tid3', 0))
    if tid2 == 6 and tid3 in WEAPON_NAMES:
        return ('Weapon', WEAPON_NAMES[tid3], list(WEAPON_STATS))
    if tid2 == 4 and tid3 in (1, 2):
        return ('Shield', 'Chinese Shield' if tid3 == 1 else 'European Shield', list(SHIELD_STATS))
    if tid2 in (1, 2, 3, 9, 10, 11) and tid3 in ARMOR_STATS:
        family = {1: 'Garment', 2: 'Protector', 3: 'Armor', 9: 'Robe', 10: 'Light Armor', 11: 'Heavy Armor'}[tid2]
        return ('Armor', '%s %s' % (family, ARMOR_NAMES[tid3]), list(ARMOR_STATS[tid3]))
    if tid2 in (5, 12) and tid3 in ACCESSORY_STATS:
        race = 'Chinese' if tid2 == 5 else 'European'
        return ('Accessory', '%s %s' % (race, ACCESSORY_NAMES[tid3]), list(ACCESSORY_STATS[tid3]))
    return None


def inventory_snapshot(mode):
    inventory = get_inventory()
    if not inventory or 'items' not in inventory:
        return []
    result = []
    for slot, item in enumerate(inventory['items']):
        if slot < 13 or not item:
            continue
        classification = item_classification(item)
        if not classification:
            continue
        copied = dict(item)
        copied['slot'] = slot
        copied['subtype'] = classification[1]
        copied['available_stats'] = classification[2]
        result.append(copied)
    return result


def find_inventory_item(slot):
    inventory = get_inventory()
    items = inventory.get('items', []) if inventory else []
    return items[slot] if 0 <= slot < len(items) else None


def find_consumable_slot(mode):
    inventory = get_inventory()
    if not inventory or 'items' not in inventory:
        return None
    names = CONSUMABLE_NAMES[mode]
    for slot, item in enumerate(inventory['items']):
        item_name = str(item.get('name', '')) if item else ''
        if any(name in item_name for name in names):
            return slot
    return None


def selected_item(mode):
    widget = inventory_lists[mode]
    index = QtBind.currentIndex(gui, widget)
    values = states[mode]['inventory']
    return values[index] if 0 <= index < len(values) else None


def format_item(item):
    return 'Slot %d | +%s | %s' % (item['slot'], item.get('plus', 0), item.get('name', 'Unknown'))


def refresh_inventory(mode):
    state = states[mode]
    state['inventory'] = inventory_snapshot(mode)
    QtBind.clear(gui, inventory_lists[mode])
    for item in state['inventory']:
        suffix = ' | %s' % item['subtype'] if mode == 'fortune' else ''
        QtBind.append(gui, inventory_lists[mode], format_item(item) + suffix)
    set_status('%s: %d eligible inventory item(s) found' % (
        MODE_LABELS[mode], len(state['inventory'])),
        COLOR_SUCCESS if state['inventory'] else COLOR_WARNING)


def fate_refresh_inventory(): refresh_inventory('fate')
def fortune_refresh_inventory(): refresh_inventory('fortune')
def pen_refresh_inventory(): refresh_inventory('pen')


def inspect_item(mode):
    state = states[mode]
    item = selected_item(mode)
    if not item:
        set_status('Select an inventory item first', COLOR_WARNING)
        return
    state['selected'] = {'slot': item['slot'], 'model': item['model']}
    QtBind.setText(gui, selected_labels[mode], fixed_width_text(
        '<font color="%s"><b>%s</b></font>' % (COLOR_TEXT, html_safe(format_item(item))), 350))
    if mode == 'fortune':
        state['available'] = list(item['available_stats'])
        state['targets'] = []
        QtBind.clear(gui, stat_lists[mode])
        QtBind.clear(gui, target_lists[mode])
        for name in state['available']:
            QtBind.append(gui, stat_lists[mode], name)
    set_status('%s item selected; configure its target' % MODE_LABELS[mode], COLOR_MUTED)


def fate_inspect(): inspect_item('fate')
def fortune_inspect(): inspect_item('fortune')
def pen_inspect(): inspect_item('pen')


def refresh_targets(mode):
    QtBind.clear(gui, target_lists[mode])
    for target in states[mode]['targets']:
        if mode == 'fortune':
            text = '%s x%d' % (target['name'], target['count'])
        else:
            text = '%s >= %d total' % (target['name'], target['value'])
        QtBind.append(gui, target_lists[mode], text)


def add_stat_target(mode):
    name = QtBind.text(gui, stat_lists[mode])
    if not name:
        set_status('Select a stat first', COLOR_WARNING)
        return
    try:
        value = int(QtBind.text(gui, target_inputs[mode]).strip())
    except Exception:
        value = 0
    maximum = MAX_LINES if mode == 'fortune' else MAX_TARGET_VALUE
    if value < 1 or value > maximum:
        set_status('Target value is outside the allowed range', COLOR_ERROR)
        return
    key = 'count' if mode == 'fortune' else 'value'
    for target in states[mode]['targets']:
        if target['name'] == name:
            target[key] = value
            refresh_targets(mode)
            set_status('Target updated: %s' % name, COLOR_SUCCESS)
            return
    states[mode]['targets'].append({'name': name, key: value})
    refresh_targets(mode)
    set_status('Target added: %s' % name, COLOR_SUCCESS)


def fortune_add_target(): add_stat_target('fortune')
def pen_add_target(): add_stat_target('pen')


def remove_stat_target(mode):
    index = QtBind.currentIndex(gui, target_lists[mode])
    if index < 0 or index >= len(states[mode]['targets']):
        set_status('Select a target to remove', COLOR_WARNING)
        return
    removed = states[mode]['targets'].pop(index)
    refresh_targets(mode)
    set_status('Removed %s target' % removed['name'], COLOR_MUTED)


def fortune_remove_target(): remove_stat_target('fortune')
def pen_remove_target(): remove_stat_target('pen')


def queue_item(mode):
    state = states[mode]
    item = selected_item(mode)
    if not item:
        set_status('Select an inventory item first', COLOR_WARNING)
        return
    queued = {'slot': item['slot'], 'model': item['model'], 'name': item.get('name', 'Unknown')}
    if mode == 'fate':
        try:
            target = int(QtBind.text(gui, target_inputs[mode]).strip())
        except Exception:
            target = 0
        if target < 1 or target > MAX_LINES:
            set_status('Blue-line target must be between 1 and 32', COLOR_ERROR)
            return
        queued.update({'target': target, 'last_count': None})
    else:
        if not state['targets']:
            set_status('Add at least one stat target', COLOR_WARNING)
            return
        queued['targets'] = [dict(value) for value in state['targets']]
        if mode == 'pen':
            queued['totals'] = {}
    for index, existing in enumerate(state['queue']):
        if existing['slot'] == queued['slot']:
            state['queue'][index] = queued
            refresh_queue(mode)
            set_status('%s queue target updated' % MODE_LABELS[mode], COLOR_SUCCESS)
            return
    state['queue'].append(queued)
    refresh_queue(mode)
    set_status('Item added to the %s queue' % MODE_LABELS[mode], COLOR_SUCCESS)


def fate_queue_item(): queue_item('fate')
def fortune_queue_item(): queue_item('fortune')
def pen_queue_item(): queue_item('pen')


def target_summary(mode, item):
    if mode == 'fate':
        current = '?' if item['last_count'] is None else item['last_count']
        return 'blue %s/%d' % (current, item['target'])
    if mode == 'fortune':
        return ', '.join('%s x%d' % (x['name'], x['count']) for x in item['targets'])
    return ', '.join('%s %s/%d' % (
        x['name'], item['totals'].get(x['name'], '?'), x['value']) for x in item['targets'])


def refresh_queue(mode):
    QtBind.clear(gui, queue_lists[mode])
    state = states[mode]
    for index, item in enumerate(state['queue']):
        marker = '>' if active_mode == mode and index == state['index'] else ' '
        QtBind.append(gui, queue_lists[mode], '%s Slot %d | %s | %s' % (
            marker, item['slot'], target_summary(mode, item), item['name']))


def remove_queue_item(mode):
    if active_mode is not None:
        set_status('Stop the active operation before editing a queue', COLOR_WARNING)
        return
    index = QtBind.currentIndex(gui, queue_lists[mode])
    if index < 0 or index >= len(states[mode]['queue']):
        set_status('Select a queued item first', COLOR_WARNING)
        return
    del states[mode]['queue'][index]
    refresh_queue(mode)
    set_status('Queued item removed', COLOR_MUTED)


def clear_queue(mode):
    if active_mode is not None:
        set_status('Stop the active operation before clearing a queue', COLOR_WARNING)
        return
    states[mode]['queue'][:] = []
    refresh_queue(mode)
    set_status('%s queue cleared' % MODE_LABELS[mode], COLOR_MUTED)


def fate_remove_queue(): remove_queue_item('fate')
def fortune_remove_queue(): remove_queue_item('fortune')
def pen_remove_queue(): remove_queue_item('pen')
def fate_clear_queue(): clear_queue('fate')
def fortune_clear_queue(): clear_queue('fortune')
def pen_clear_queue(): clear_queue('pen')


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


def schedule_request(delay, mode):
    global pending_timer
    token = timer_token
    def callback():
        if active_mode == mode and token == timer_token:
            send_request(mode)
    pending_timer = Timer(delay, callback)
    pending_timer.daemon = True
    pending_timer.start()


def active_item(mode):
    if single_roll and test_items.get(mode):
        return test_items[mode]
    state = states[mode]
    return state['queue'][state['index']] if 0 <= state['index'] < len(state['queue']) else None


def send_request(mode):
    global awaiting_response
    if active_mode != mode or awaiting_response:
        return
    item = active_item(mode)
    if not item:
        stop_operation('All %s targets reached' % MODE_LABELS[mode], COLOR_SUCCESS)
        return
    live = find_inventory_item(item['slot'])
    if not live or live.get('model') != item['model']:
        stop_operation('Item moved or changed at slot %d' % item['slot'], COLOR_ERROR)
        return
    consumable_slot = find_consumable_slot(mode)
    if consumable_slot is None:
        stop_operation('%s consumable not found' % MODE_LABELS[mode], COLOR_ERROR)
        return
    if item['slot'] > 255 or consumable_slot > 255:
        stop_operation('Inventory slot is outside packet range', COLOR_ERROR)
        return
    awaiting_response = True
    inject_joymax(OPCODE_REQUEST, b'\x02\x19\x02' + bytes([item['slot'], consumable_slot]), False)
    set_status('%s is rolling slot %d...' % (MODE_LABELS[mode], item['slot']), COLOR_WARNING)


def start_mode(mode):
    global active_mode, single_roll
    if active_mode is not None:
        set_status('%s operation is already active' % MODE_LABELS[active_mode], COLOR_WARNING)
        return
    state = states[mode]
    if not state['queue']:
        set_status('Add at least one item to the %s queue' % MODE_LABELS[mode], COLOR_WARNING)
        return
    for item in state['queue']:
        live = find_inventory_item(item['slot'])
        if not live or live.get('model') != item['model']:
            set_status('Queued item changed at slot %d' % item['slot'], COLOR_ERROR)
            return
    if find_consumable_slot(mode) is None:
        set_status('%s consumable not found' % MODE_LABELS[mode], COLOR_ERROR)
        return
    state['index'] = 0
    active_mode = mode
    single_roll = False
    invalidate_timer()
    refresh_all_queues()
    set_status('%s automation started' % MODE_LABELS[mode], COLOR_SUCCESS)
    send_request(mode)


def test_mode(mode):
    global active_mode, single_roll
    if active_mode is not None:
        set_status('%s operation is already active' % MODE_LABELS[active_mode], COLOR_WARNING)
        return
    item = selected_item(mode)
    if not item:
        set_status('Select an inventory item first', COLOR_WARNING)
        return
    test_items[mode] = {
        'slot': item['slot'], 'model': item['model'], 'name': item.get('name', 'Unknown'),
        'target': 1, 'last_count': None, 'targets': [], 'totals': {}
    }
    active_mode = mode
    single_roll = True
    invalidate_timer()
    send_request(mode)
    set_status('One-roll %s test sent; waiting for 0xB151...' % MODE_LABELS[mode], COLOR_WARNING)


def fate_start(): start_mode('fate')
def fortune_start(): start_mode('fortune')
def pen_start(): start_mode('pen')
def fate_test(): test_mode('fate')
def fortune_test(): test_mode('fortune')
def pen_test(): test_mode('pen')


def stop_operation(message='Operation stopped', color=COLOR_WARNING):
    global active_mode, single_roll
    old_mode = active_mode
    if old_mode:
        test_items[old_mode] = None
    active_mode = None
    single_roll = False
    invalidate_timer()
    if old_mode:
        refresh_queue(old_mode)
    set_status(message, color)


def stop_clicked():
    if active_mode is None:
        set_status('No operation is running', COLOR_MUTED)
    else:
        stop_operation()


def parse_fate(data):
    if len(data) < 43 or data[0] != 1 or data[2] != 1:
        return None
    count = data[26]
    if count < 1 or count > MAX_LINES + 1:
        return None
    blue_count = count - 1
    return (data[4], blue_count) if len(data) >= 43 + blue_count * 8 else None


def parse_fortune(data, item=None):
    classification = None
    if item is not None:
        live_item = find_inventory_item(item['slot'])
        classification = item_classification(live_item) if live_item else None
    candidates = []
    for start in range(max(0, len(data) - 7)):
        cursor = start
        options = []
        while cursor + 8 <= len(data):
            group = data[cursor:cursor + 8]
            if (group[0] == 0 or group[1] != 2 or group[2] != 0 or group[3] != 0 or
                    group[4] == 0 or group[5] != 0 or group[6] != 0 or group[7] != 0):
                break
            name = CLASSIC_CODES.get(group[0])
            if classification and classification[0] == 'Weapon':
                name = WEAPON_CONTEXT_CODES.get(group[0], name)
            options.append({'name': name or 'Unknown code 0x%02X' % group[0],
                            'value': group[4]})
            cursor += 8
        if options:
            candidates.append((start, options))
    if candidates:
        candidates.sort(key=lambda entry: (-len(entry[1]), entry[0]))
        return candidates[0][1]
    if len(data) >= 35:
        options = []
        for index in range(len(data[35:]) // 8):
            group = data[35 + index * 8:43 + index * 8]
            code = struct.unpack_from('<I', group, 0)[0]
            if code in DG12_CODES:
                options.append({'name': DG12_CODES[code], 'value': struct.unpack_from('<I', group, 4)[0]})
        return options
    return []


def normalize_fortune_options(item, options):
    classification = item_classification(find_inventory_item(item['slot']))
    if not classification:
        return False, 'Item classification is unavailable'
    available = classification[2]
    for option in options:
        if option['name'] == 'Block Rate' and 'Evade Block' in available:
            option['name'] = 'Evade Block'
        elif option['name'] == 'Block Rate' and 'Block' in available:
            option['name'] = 'Block'
    invalid = sorted(set(option['name'] for option in options
                         if option['name'] not in available and option['name'] not in IGNORED_RESPONSE_STATS))
    if invalid:
        return False, 'Impossible stat(s): %s' % ', '.join(invalid)
    return True, ''


def parse_pen(data):
    if len(data) < 14 or data[:4] != b'\x01\x02\x01\x02':
        return None
    length = struct.unpack_from('<H', data, 4)[0]
    end = 6 + length
    if length < 1 or end + 31 > len(data):
        return None
    count_position = end + 22
    internal_position = end + 30
    records_start = end + 31
    count = data[count_position]
    visible = count - 1
    if count < 2 or visible > MAX_LINES or data[internal_position] != 0x40:
        return None
    if records_start + visible * 8 > len(data):
        return None
    totals = {}
    for index in range(visible):
        group = data[records_start + index * 8:records_start + (index + 1) * 8]
        if (group[1] != 2 or group[2] != 0 or group[3] != 0 or group[4] == 0 or
                group[5] != 0 or group[6] != 0 or group[7] != 0):
            return None
        name = PEN_STAT_CODES.get(group[0])
        if not name:
            return None
        totals[name] = totals.get(name, 0) + group[4]
    return data[end], totals


def process_response(data):
    global awaiting_response, single_roll
    mode = active_mode
    if not mode or not awaiting_response:
        return
    awaiting_response = False
    item = active_item(mode)
    if not item:
        stop_operation('No active item; operation stopped', COLOR_ERROR)
        return
    reached = False
    if mode == 'fate':
        parsed = parse_fate(data)
        if not parsed or parsed[0] != item['slot']:
            stop_operation('Fate response could not be verified', COLOR_ERROR)
            return
        item['last_count'] = parsed[1]
        reached = parsed[1] >= item.get('target', 1)
        set_result(mode, 'Slot %d: %d blue line(s)' % (item['slot'], parsed[1]), COLOR_SUCCESS)
    elif mode == 'fortune':
        options = parse_fortune(data, item)
        if not options:
            stop_operation('Fortune response had no verified stats', COLOR_ERROR)
            return
        valid, reason = normalize_fortune_options(item, options)
        if not valid:
            plugin_log('Fortune unsafe layout 0xB151 raw (%d bytes): %s%s' % (
                len(data), ' '.join('%02X' % value for value in data[:512]),
                ' ...' if len(data) > 512 else ''))
            stop_operation(reason, COLOR_ERROR)
            return
        counts = {}
        for option in options:
            counts[option['name']] = counts.get(option['name'], 0) + 1
        reached = all(counts.get(x['name'], 0) >= x['count'] for x in item.get('targets', []))
        set_result(mode, ', '.join('%s x%d' % pair for pair in sorted(counts.items())), COLOR_SUCCESS)
    else:
        parsed = parse_pen(data)
        if not parsed or parsed[0] != item['slot']:
            stop_operation('Pen response could not be verified', COLOR_ERROR)
            return
        item['totals'] = parsed[1]
        reached = all(parsed[1].get(x['name'], 0) >= x['value'] for x in item.get('targets', []))
        set_result(mode, ', '.join('%s=%d' % pair for pair in sorted(parsed[1].items())), COLOR_SUCCESS)
    plugin_log('%s slot %d response processed' % (MODE_LABELS[mode], item['slot']))
    if single_roll:
        single_roll = False
        stop_operation('One-roll %s test completed' % MODE_LABELS[mode], COLOR_SUCCESS)
        return
    if reached:
        states[mode]['index'] += 1
        refresh_queue(mode)
        if states[mode]['index'] >= len(states[mode]['queue']):
            stop_operation('All %s targets reached' % MODE_LABELS[mode], COLOR_SUCCESS)
        else:
            schedule_request(NEXT_ITEM_DELAY, mode)
    else:
        refresh_queue(mode)
        schedule_request(MODE_DELAYS[mode], mode)


def handle_joymax(opcode, data):
    try:
        if opcode == OPCODE_RESPONSE and active_mode is not None:
            process_response(data)
    except Exception as error:
        plugin_log('Packet processing error for 0x%04X: %s' % (opcode, error))
        if opcode == OPCODE_RESPONSE and active_mode is not None:
            stop_operation('Packet processing failed; operation stopped', COLOR_ERROR)
    return True


def disconnected():
    if active_mode is not None or awaiting_response:
        stop_operation('Disconnected; operation stopped', COLOR_ERROR)
    else:
        invalidate_timer()
        set_status('Disconnected', COLOR_MUTED)


def move_widgets(widgets, visible):
    for widget, x, y in widgets:
        QtBind.move(gui, widget, x if visible else OFFSCREEN_X, y)


def show_view(mode, page='setup'):
    global visible_mode, visible_page
    visible_mode = mode
    visible_page = page
    for current_mode in MODES:
        move_widgets(setup_widgets[current_mode], current_mode == mode and page == 'setup')
        move_widgets(queue_widgets[current_mode], current_mode == mode and page == 'queue')
    QtBind.setText(gui, lbl_view, fixed_width_text(
        '<font color="%s"><b>%s / %s</b></font>' % (
            COLOR_PRIMARY, MODE_LABELS[mode].upper(), page.upper()), 160))
    refresh_queue(mode)


def show_fate(): show_view('fate', 'setup')
def show_fortune(): show_view('fortune', 'setup')
def show_pen(): show_view('pen', 'setup')
def fate_setup(): show_view('fate', 'setup')
def fortune_setup(): show_view('fortune', 'setup')
def pen_setup(): show_view('pen', 'setup')
def fate_queue(): show_view('fate', 'queue')
def fortune_queue(): show_view('fortune', 'queue')
def pen_queue(): show_view('pen', 'queue')


def refresh_all_queues():
    for mode in MODES:
        refresh_queue(mode)


gui = QtBind.init(__name__, pName)
QtBind.createLabel(gui, '<font color="%s" size="4"><b>✦ %s</b></font>' % (COLOR_PRIMARY, pName), 12, 6)
QtBind.createLabel(gui, '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion), 175, 12)
QtBind.createButton(gui, 'show_fate', 'Fate', 245, 6)
QtBind.createButton(gui, 'show_fortune', 'Fortune', 300, 6)
QtBind.createButton(gui, 'show_pen', 'Pen', 370, 6)
QtBind.createButton(gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(gui, u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' % COLOR_PRIMARY, 565, 11)
QtBind.createLineEdit(gui, '', 12, 30, 716, 1)
lbl_view = QtBind.createLabel(gui, fixed_width_text('<font color="%s"><b>FATE / SETUP</b></font>' % COLOR_PRIMARY, 160), 12, 42)
lbl_status = QtBind.createLabel(gui, fixed_width_text('<font color="%s"><b>Ready</b></font>' % COLOR_MUTED, 680), 12, 294)

setup_widgets = {mode: [] for mode in MODES}
queue_widgets = {mode: [] for mode in MODES}
inventory_lists = {}
selected_labels = {}
stat_lists = {}
target_lists = {}
target_inputs = {}
queue_lists = {}
result_labels = {}

for _mode_index, _mode in enumerate(MODES):
    _hidden = _mode != 'fate'
    _x = OFFSCREEN_X if _hidden else 12
    _title = QtBind.createLabel(gui, '<font color="%s"><b>%s ITEM SETUP</b></font>' % (COLOR_PRIMARY, MODE_LABELS[_mode].upper()), _x, 66)
    _refresh = QtBind.createButton(gui, _mode + '_refresh_inventory', '↻ Refresh', _x, 86)
    _inspect = QtBind.createButton(gui, _mode + '_inspect', 'Select Item', OFFSCREEN_X if _hidden else 105, 86)
    _test = QtBind.createButton(gui, _mode + '_test', 'Test One Roll', OFFSCREEN_X if _hidden else 205, 86)
    _queue_page = QtBind.createButton(gui, _mode + '_queue', 'Queue & Start →', OFFSCREEN_X if _hidden else 610, 42)
    _list = QtBind.createList(gui, _x, 114, 360, 130)
    _selected = QtBind.createLabel(gui, fixed_width_text('<font color="%s">No item selected</font>' % COLOR_MUTED, 350), _x, 252)
    inventory_lists[_mode] = _list
    selected_labels[_mode] = _selected
    setup_widgets[_mode].extend([
        (_title, 12, 66), (_refresh, 12, 86), (_inspect, 105, 86), (_test, 205, 86),
        (_queue_page, 610, 42), (_list, 12, 114), (_selected, 12, 252)
    ])
    if _mode == 'fate':
        _target_label = QtBind.createLabel(gui, '<font color="%s"><b>TARGET BLUE LINES</b></font>' % COLOR_PRIMARY, 400 if not _hidden else OFFSCREEN_X, 70)
        _input = QtBind.createLineEdit(gui, '6', 400 if not _hidden else OFFSCREEN_X, 94, 48, 20)
        _add = QtBind.createButton(gui, 'fate_queue_item', 'Add Item to Queue', 460 if not _hidden else OFFSCREEN_X, 90)
        target_inputs[_mode] = _input
        setup_widgets[_mode].extend([(_target_label, 400, 70), (_input, 400, 94), (_add, 460, 90)])
    else:
        _stats_label = QtBind.createLabel(gui, '<font color="%s"><b>AVAILABLE STATS</b></font>' % COLOR_PRIMARY, OFFSCREEN_X, 70)
        _targets_label = QtBind.createLabel(gui, '<font color="%s"><b>ITEM TARGETS</b></font>' % COLOR_PRIMARY, OFFSCREEN_X, 70)
        _stats = QtBind.createList(gui, OFFSCREEN_X, 92, 145, 120)
        _targets = QtBind.createList(gui, OFFSCREEN_X, 92, 155, 120)
        _input = QtBind.createLineEdit(gui, '1' if _mode == 'fortune' else '10', OFFSCREEN_X, 222, 50, 20)
        _add_target = QtBind.createButton(gui, _mode + '_add_target', 'Add / Update', OFFSCREEN_X, 218)
        _remove_target = QtBind.createButton(gui, _mode + '_remove_target', 'Remove Target', OFFSCREEN_X, 248)
        _add_queue = QtBind.createButton(gui, _mode + '_queue_item', 'Add Item to Queue', OFFSCREEN_X, 248)
        stat_lists[_mode] = _stats
        target_lists[_mode] = _targets
        target_inputs[_mode] = _input
        setup_widgets[_mode].extend([
            (_stats_label, 400, 70), (_targets_label, 560, 70), (_stats, 400, 92),
            (_targets, 560, 92), (_input, 400, 222), (_add_target, 460, 218),
            (_remove_target, 560, 218), (_add_queue, 400, 248)
        ])

for _name in PEN_STATS:
    QtBind.append(gui, stat_lists['pen'], _name)

for _mode in MODES:
    _back = QtBind.createButton(gui, _mode + '_setup', '← Item Setup', OFFSCREEN_X, 42)
    _header = QtBind.createLabel(gui, '<font color="%s"><b>%s AUTOMATION QUEUE</b></font>' % (COLOR_PRIMARY, MODE_LABELS[_mode].upper()), OFFSCREEN_X, 70)
    _queue = QtBind.createList(gui, OFFSCREEN_X, 94, 535, 118)
    _remove = QtBind.createButton(gui, _mode + '_remove_queue', 'Remove Item', OFFSCREEN_X, 94)
    _clear = QtBind.createButton(gui, _mode + '_clear_queue', 'Clear Queue', OFFSCREEN_X, 126)
    _start = QtBind.createButton(gui, _mode + '_start', '▶ START', OFFSCREEN_X, 224)
    _stop = QtBind.createButton(gui, 'stop_clicked', '■ STOP', OFFSCREEN_X, 224)
    _result = QtBind.createLabel(gui, fixed_width_text('<font color="%s">No verified result yet</font>' % COLOR_MUTED, 680), OFFSCREEN_X, 260)
    queue_lists[_mode] = _queue
    result_labels[_mode] = _result
    queue_widgets[_mode].extend([
        (_back, 610, 42), (_header, 12, 70), (_queue, 12, 94), (_remove, 560, 94),
        (_clear, 560, 126), (_start, 12, 224), (_stop, 105, 224), (_result, 12, 260)
    ])

log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
