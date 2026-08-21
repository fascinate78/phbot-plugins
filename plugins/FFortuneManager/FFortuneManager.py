from phBot import *
import QtBind
import os
import struct
import time
import webbrowser
from threading import Timer


pName = 'FFortuneManager'
pVersion = '1.2.6'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

OPCODE_FORTUNE_REQUEST = 0x7151
OPCODE_FORTUNE_RESPONSE = 0xB151
OPCODE_CHARACTER_DATA = 0x3013

COLOR_PRIMARY = '#5b57e0'
COLOR_TEXT = '#2b3038'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#d93a4d'

FORTUNE_REQUEST_DELAY = 0.45
NEXT_ITEM_DELAY = 0.80
MAX_MAGIC_OPTIONS = 32
OFFSCREEN_X = 3000

is_running = False
current_item_index = 0
selected_inventory = []
target_items = []
current_available_stats = []
current_targets = []
captured_items = {}
capture_generation = 0
last_capture_time = 0.0
pending_timer_token = 0
pending_character_data = None
pending_character_data_time = 0.0
pending_character_data_attempts = 0
single_roll_item = None


# Media.pk2: refrnd_magicopt.txt, with the explicitly excluded options removed.
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


# Magic option signatures exported from this server's magicoption_all.txt.
SIGNATURE_NAMES = {
    7566450: 'STR',
    6909556: 'INT',
    1685418613: 'Durability',
    26738: 'Attack Rate',
    1702257260: 'Evade Block',
    6517353: 'Critical',
    6451817: 'Block',
    26736: 'HP',
    28016: 'MP',
    1752198512: 'HP/MP Recovery',
    1919120233: 'CSMP Resist',
    1920167017: 'Sleep Resist',
    1920169065: 'Stun Resist',
    1919183209: 'Disease Resist',
    1919313257: 'Fear Resist',
    # Known but intentionally excluded from target selection.
    1635018849: 'Athanasia',
    1936682089: 'Solid',
    1819632491: 'Luck',
    7497072: 'Repair',
    25970: 'Parry Ratio',
    1702257522: 'Evade Critical',
    26234: 'Frostbite Resist',
    25205: 'Fire Resist',
    25971: 'Lightning Resist',
    28787: 'Poison Resist',
    31330: 'Zombie Resist'
}

# Fortune response codes observed by the original plugin/server implementation.
CLASSIC_CODES = {
    # Armor/accessory family used by this server.
    0x0A: 'STR', 0x0B: 'INT', 0x0C: 'Durability',
    0x0F: 'Evade Critical',
    0x10: 'Parry Ratio', 0x11: 'HP', 0x12: 'MP',
    0x13: 'Frostbite Resist', 0x14: 'Lightning Resist',
    0x15: 'Fire Resist', 0x16: 'Poison Resist',
    0x17: 'Zombie Resist', 0x19: 'Block',
    0x1A: 'Stun Resist', 0x1C: 'CSMP Resist',
    0x1D: 'Disease Resist', 0x1E: 'Sleep Resist',
    0x1F: 'Fear Resist',
    # Weapon/classic family retained from the original server plugin.
    0x39: 'STR', 0x53: 'STR', 0x54: 'STR', 0x55: 'STR',
    0x3A: 'INT', 0x56: 'INT', 0x57: 'INT', 0x58: 'INT',
    0x3B: 'Durability', 0x59: 'Durability', 0x5A: 'Durability',
    0x47: 'Critical', 0x7D: 'Critical', 0x7E: 'Critical',
    0x3C: 'Attack Rate', 0x5C: 'Attack Rate',
    0x3D: 'Block Rate', 0x5F: 'Block Rate',
    0x40: 'HP', 0x68: 'HP', 0x41: 'MP', 0x6B: 'MP',
    0x49: 'Stun', 0x4A: 'HP/MP Recovery', 0x4B: 'Combustion',
    0x4C: 'Disease', 0x4D: 'Sleep', 0x4E: 'Fear'
}
IGNORED_RESPONSE_STATS = {
    'Athanasia', 'Solid', 'Luck', 'Repair'
}
DG12_CODES = {
    0x0049: 'STR', 0x004F: 'INT', 0x0067: 'Attack Rate',
    0x0073: 'Evade Block', 0x008B: 'HP', 0x0097: 'MP',
    0x010C: 'Critical'
}


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
        fixed_width_text('<font color="%s"><b>%s</b></font>' % (color, html_safe(message)), 460)
    )


def set_capture_status(message, color=COLOR_MUTED):
    QtBind.setText(
        gui, lbl_capture,
        fixed_width_text('<font color="%s">%s</font>' % (color, html_safe(message)), 310)
    )


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


def inventory_snapshot():
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
        copy_item = dict(item)
        copy_item['slot'] = slot
        copy_item['category'] = classification[0]
        copy_item['subtype'] = classification[1]
        copy_item['available_stats'] = classification[2]
        result.append(copy_item)
    return result


def get_fortune_slot():
    inventory = get_inventory()
    if not inventory or 'items' not in inventory:
        return None
    for slot, item in enumerate(inventory['items']):
        if item and 'Wheel of Fortune' in str(item.get('name', '')):
            return slot
    return None


def find_inventory_item(slot):
    inventory = get_inventory()
    if not inventory or 'items' not in inventory:
        return None
    items = inventory['items']
    if slot < 0 or slot >= len(items):
        return None
    return items[slot]


def format_inventory_row(item):
    captured = captured_items.get(item['slot'])
    marker = '+' if captured and captured.get('model') == item.get('model') else '?'
    return '%s Slot %d | +%s | %s | %s' % (
        marker, item['slot'], item.get('plus', 0), item['subtype'], item.get('name', 'Unknown'))


def refresh_inventory():
    global selected_inventory
    selected_inventory = inventory_snapshot()
    QtBind.clear(gui, lst_inventory)
    for item in selected_inventory:
        QtBind.append(gui, lst_inventory, format_inventory_row(item))
    set_status('Found %d eligible inventory item(s)' % len(selected_inventory), COLOR_SUCCESS)


def selected_inventory_item():
    text = QtBind.text(gui, lst_inventory)
    if not text:
        return None
    try:
        slot = int(text.split('Slot ', 1)[1].split(' ', 1)[0])
    except Exception:
        return None
    for item in selected_inventory:
        if item['slot'] == slot:
            return item
    return None


def format_raw_value(value):
    return '%d (0x%08X)' % (value, value)


def show_selected_item():
    global current_available_stats, current_targets
    item = selected_inventory_item()
    if not item:
        set_status('Select an inventory item first', COLOR_WARNING)
        return
    current_available_stats = list(item['available_stats'])
    current_targets = []
    QtBind.clear(gui, lst_available_stats)
    QtBind.clear(gui, lst_targets)
    for name in current_available_stats:
        QtBind.append(gui, lst_available_stats, name)
    details = '%s | Slot %d | %s | Lv %s | +%s | Dur %s' % (
        item.get('name', 'Unknown'), item['slot'], item['subtype'],
        get_item(item['model']).get('level', '?'), item.get('plus', 0),
        item.get('durability', '?'))
    QtBind.setText(gui, lbl_selected_item, fixed_width_text(
        '<font color="%s"><b>%s</b></font>' % (COLOR_TEXT, html_safe(details)), 350))
    captured = captured_items.get(item['slot'])
    if not captured or captured.get('model') != item.get('model'):
        set_capture_status('Current stats not observed yet; use Test One Roll', COLOR_WARNING)
        return
    options = captured.get('options', [])
    set_capture_status(
        'Verified from %s: %d option(s)' % (captured.get('source', 'packet'), len(options)),
        COLOR_SUCCESS)


def add_target():
    stat = QtBind.text(gui, lst_available_stats)
    if not stat:
        set_status('Select an available stat', COLOR_WARNING)
        return
    try:
        count = int(QtBind.text(gui, txt_target_count))
    except Exception:
        count = 0
    if count <= 0 or count > 32:
        set_status('Target line count must be between 1 and 32', COLOR_ERROR)
        return
    for target in current_targets:
        if target['name'] == stat:
            target['count'] = count
            refresh_targets()
            set_status('Updated target: %s x%d' % (stat, count), COLOR_SUCCESS)
            return
    current_targets.append({'name': stat, 'count': count})
    refresh_targets()
    set_status('Added target: %s x%d' % (stat, count), COLOR_SUCCESS)


def remove_target():
    text = QtBind.text(gui, lst_targets)
    if not text:
        set_status('Select a target to remove', COLOR_WARNING)
        return
    name = text.split(' x', 1)[0]
    current_targets[:] = [target for target in current_targets if target['name'] != name]
    refresh_targets()
    set_status('Removed target: %s' % name, COLOR_SUCCESS)


def refresh_targets():
    QtBind.clear(gui, lst_targets)
    for target in current_targets:
        QtBind.append(gui, lst_targets, '%s x%d' % (target['name'], target['count']))


def queue_selected_item():
    item = selected_inventory_item()
    if not item:
        set_status('Select an inventory item first', COLOR_WARNING)
        return
    if not current_targets:
        set_status('Add at least one stat target', COLOR_WARNING)
        return
    for queued in target_items:
        if queued['slot'] == item['slot']:
            set_status('This inventory slot is already queued', COLOR_WARNING)
            return
    target_items.append({
        'slot': item['slot'], 'model': item['model'], 'name': item.get('name', 'Unknown'),
        'subtype': item['subtype'], 'targets': [dict(target) for target in current_targets]
    })
    refresh_queue()
    set_status('Queued %s' % item.get('name', 'Unknown'), COLOR_SUCCESS)


def refresh_queue():
    QtBind.clear(gui, lst_queue)
    for index, item in enumerate(target_items):
        marker = '>' if is_running and index == current_item_index else '-'
        targets = ', '.join('%s x%d' % (x['name'], x['count']) for x in item['targets'])
        QtBind.append(gui, lst_queue, '%s %d) Slot %d | %s | %s' % (
            marker, index + 1, item['slot'], item['name'], targets))


def remove_queued_item():
    if is_running:
        set_status('Stop automation before changing the queue', COLOR_WARNING)
        return
    text = QtBind.text(gui, lst_queue)
    if not text:
        set_status('Select a queued item', COLOR_WARNING)
        return
    try:
        index = int(text.split(')', 1)[0].replace('-', '').replace('>', '').strip()) - 1
    except Exception:
        set_status('Could not read queued item', COLOR_ERROR)
        return
    if 0 <= index < len(target_items):
        removed = target_items.pop(index)
        refresh_queue()
        set_status('Removed %s' % removed['name'], COLOR_SUCCESS)


def clear_queue():
    if is_running:
        set_status('Stop automation before clearing the queue', COLOR_WARNING)
        return
    target_items[:] = []
    refresh_queue()
    set_status('Queue cleared', COLOR_SUCCESS)


def active_item():
    if 0 <= current_item_index < len(target_items):
        return target_items[current_item_index]
    return None


def invalidate_timer():
    global pending_timer_token
    pending_timer_token += 1
    return pending_timer_token


def schedule_request(delay):
    token = pending_timer_token
    Timer(delay, scheduled_request, args=[token]).start()


def scheduled_request(token):
    if token == pending_timer_token:
        send_fortune_request()


def send_fortune_request():
    if not is_running:
        return
    item = active_item()
    if not item:
        stop_automation('All queued items completed', COLOR_SUCCESS)
        return
    live_item = find_inventory_item(item['slot'])
    if not live_item or live_item.get('model') != item['model']:
        stop_automation('Item moved or changed at slot %d' % item['slot'], COLOR_ERROR)
        return
    fortune_slot = get_fortune_slot()
    if fortune_slot is None:
        stop_automation('Wheel of Fortune not found', COLOR_ERROR)
        return
    if item['slot'] > 255 or fortune_slot > 255:
        stop_automation('Inventory slot is outside packet range', COLOR_ERROR)
        return
    packet = b'\x02\x19\x02' + bytes([item['slot'], fortune_slot])
    inject_joymax(OPCODE_FORTUNE_REQUEST, packet, False)
    set_status('Rolling %s...' % item['name'], COLOR_WARNING)


def test_one_roll():
    global single_roll_item
    if is_running:
        set_status('Stop automation before running a one-roll test', COLOR_WARNING)
        return
    if single_roll_item is not None:
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
    fortune_slot = get_fortune_slot()
    if fortune_slot is None:
        set_status('Wheel of Fortune not found', COLOR_ERROR)
        return
    if item['slot'] > 255 or fortune_slot > 255:
        set_status('Inventory slot is outside packet range', COLOR_ERROR)
        return
    single_roll_item = {
        'slot': item['slot'], 'model': item['model'],
        'name': item.get('name', 'Unknown')
    }
    packet = b'\x02\x19\x02' + bytes([item['slot'], fortune_slot])
    inject_joymax(OPCODE_FORTUNE_REQUEST, packet, False)
    set_status('One-roll test sent for %s; waiting for 0xB151...' % (
        single_roll_item['name']), COLOR_WARNING)


def start_automation():
    global is_running, current_item_index
    if is_running:
        set_status('Automation is already running', COLOR_WARNING)
        return
    if not target_items:
        set_status('Queue at least one item', COLOR_WARNING)
        return
    for item in target_items:
        live_item = find_inventory_item(item['slot'])
        if not live_item or live_item.get('model') != item['model']:
            set_status('Queued item is no longer at slot %d' % item['slot'], COLOR_ERROR)
            return
    if get_fortune_slot() is None:
        set_status('Wheel of Fortune not found', COLOR_ERROR)
        return
    current_item_index = 0
    is_running = True
    invalidate_timer()
    refresh_queue()
    set_status('Automation started', COLOR_SUCCESS)
    send_fortune_request()


def stop_automation(message='Automation stopped', color=COLOR_WARNING):
    global is_running
    is_running = False
    invalidate_timer()
    refresh_queue()
    set_status(message, color)


def decode_fortune_group(group):
    if len(group) != 8:
        return None
    full_code = struct.unpack_from('<I', bytes(group), 0)[0]
    if full_code in DG12_CODES:
        return {'code': full_code, 'name': DG12_CODES[full_code],
                'value': struct.unpack_from('<I', bytes(group), 4)[0], 'format': '12DG'}
    code = group[0]
    if code in CLASSIC_CODES:
        return {'code': code, 'name': CLASSIC_CODES[code], 'value': group[4], 'format': 'classic'}
    return None


def parse_fortune_response(data, item=None):
    # The header length is not stable across every item/slot on this server.
    # Locate contiguous classic records by their verified wire shape instead:
    # [type][02 00 00][uint32 value].
    candidates = []
    packet_length = len(data)
    for start in range(max(0, packet_length - 7)):
        cursor = start
        options = []
        while cursor + 8 <= packet_length:
            group = data[cursor:cursor + 8]
            if (group[0] == 0 or group[1] != 0x02 or
                    group[2] != 0 or group[3] != 0 or
                    group[5] != 0 or group[6] != 0 or group[7] != 0):
                break
            value = group[4]
            if value <= 0:
                break
            options.append({
                'code': group[0],
                'name': CLASSIC_CODES.get(
                    group[0], 'Unknown code 0x%02X' % group[0]),
                'value': value, 'format': 'classic-scan', 'offset': cursor
            })
            cursor += 8
        if options:
            candidates.append((start, options))

    if candidates:
        # Sub-offsets of the same run are also candidates; the longest run is
        # the complete stat section. Earlier offset wins an equal-length tie.
        candidates.sort(key=lambda entry: (-len(entry[1]), entry[0]))
        return candidates[0][1]

    # Retain the known 12DG fallback for packets using four-byte option IDs.
    if packet_length >= 35:
        options = []
        blue_section = data[35:]
        for index in range(len(blue_section) // 8):
            group = list(blue_section[index * 8:(index + 1) * 8])
            full_code = struct.unpack_from('<I', bytes(group), 0)[0]
            if full_code not in DG12_CODES:
                continue
            options.append({
                'code': full_code, 'name': DG12_CODES[full_code],
                'value': struct.unpack_from('<I', bytes(group), 4)[0],
                'format': '12DG'
            })
        return options
    return []


def targets_met(options, targets):
    counts = {}
    for option in options:
        counts[option['name']] = counts.get(option['name'], 0) + 1
    return all(counts.get(target['name'], 0) >= target['count'] for target in targets)


def response_matches_item(item, options):
    live_item = find_inventory_item(item['slot'])
    classification = item_classification(live_item) if live_item else None
    if not classification:
        return False, 'Selected item classification is unavailable'
    available = classification[2]
    invalid_names = []
    for option in options:
        name = option['name']
        if name in available:
            continue
        if name in IGNORED_RESPONSE_STATS:
            continue
        if name == 'Block Rate' and 'Evade Block' in available:
            continue
        if name == 'Block Rate' and 'Block' in available:
            continue
        if name == 'Evade Block' and 'Block Rate' in available:
            continue
        invalid_names.append(name)
    invalid = sorted(set(invalid_names))
    if invalid:
        return False, 'Impossible stat(s) for %s: %s' % (
            classification[1], ', '.join(invalid))
    return True, ''


def log_fortune_raw(label, data):
    plugin_log('%s 0xB151 raw (%d bytes): %s%s' % (
        label, len(data), ' '.join('%02X' % value for value in data[:512]),
        ' ...' if len(data) > 512 else ''))


def cache_and_show_response(item, options, source):
    live_item = find_inventory_item(item['slot'])
    classification = item_classification(live_item) if live_item else None
    available = classification[2] if classification else []
    # This server reuses the classic block-related response code. Resolve it
    # against the selected item's Media target group.
    for option in options:
        if option['name'] == 'Block Rate' and 'Evade Block' in available:
            option['name'] = 'Evade Block'
        elif option['name'] == 'Block Rate' and 'Block' in available:
            option['name'] = 'Block'
        elif option['name'] == 'Evade Block' and 'Block Rate' in available:
            option['name'] = 'Block Rate'
    captured_items[item['slot']] = {
        'model': item['model'], 'options': options, 'source': source,
        'captured_at': time.time()
    }
    counts = {}
    for option in options:
        counts[option['name']] = counts.get(option['name'], 0) + 1
    set_capture_status('Verified from %s: %d option(s)' % (
        source, len(options)), COLOR_SUCCESS)
    plugin_log('Slot %d result: %s' % (
        item['slot'], ', '.join('%s x%d' % pair for pair in counts.items())))
    return counts


def process_single_roll_response(data):
    global single_roll_item
    item = single_roll_item
    single_roll_item = None
    if not item:
        return
    log_fortune_raw('One-roll', data)
    options = parse_fortune_response(data, item)
    if not options:
        set_status('One-roll response received, but no known stats were decoded', COLOR_ERROR)
        set_capture_status('0xB151 received; stat format needs diagnostics', COLOR_ERROR)
        plugin_log('One-roll 0xB151 decode failed: %d bytes' % len(data))
        return
    valid, reason = response_matches_item(item, options)
    if not valid:
        set_status('One-roll response rejected: %s' % reason, COLOR_ERROR)
        set_capture_status('Unsafe 0xB151 layout; raw response logged', COLOR_ERROR)
        plugin_log('One-roll response rejected: %s' % reason)
        return
    cache_and_show_response(item, options, '0xB151 one-roll test')
    set_status('One-roll test completed; no repeat was scheduled', COLOR_SUCCESS)


def process_fortune_response(data):
    global current_item_index
    item = active_item()
    if not item:
        return
    options = parse_fortune_response(data, item)
    if not options:
        log_fortune_raw('Automation decode failure', data)
        stop_automation('Response had no verified stats; automation stopped', COLOR_ERROR)
        return
    valid, reason = response_matches_item(item, options)
    if not valid:
        log_fortune_raw('Automation unsafe layout', data)
        plugin_log('Automation response rejected: %s' % reason)
        stop_automation('%s; automation stopped' % reason, COLOR_ERROR)
        return
    cache_and_show_response(item, options, '0xB151 Fortune response')
    if targets_met(options, item['targets']):
        set_status('Target reached for %s' % item['name'], COLOR_SUCCESS)
        current_item_index += 1
        refresh_queue()
        if current_item_index >= len(target_items):
            stop_automation('All targets reached', COLOR_SUCCESS)
        else:
            schedule_request(NEXT_ITEM_DELAY)
    else:
        schedule_request(FORTUNE_REQUEST_DELAY)


def option_name_from_signature(signature):
    return SIGNATURE_NAMES.get(signature, 'Unknown 0x%08X' % signature)


def parse_equip_payload(data, item_id_position):
    # vSRO equip record after RefObjID: plus(1), variance(8), durability(4), optionCount(1).
    base = item_id_position + 4
    if base + 14 > len(data):
        return None
    plus = data[base]
    if plus > 100:
        return None
    option_count_position = base + 13
    option_count = data[option_count_position]
    if option_count > MAX_MAGIC_OPTIONS:
        return None
    cursor = option_count_position + 1
    options = []
    for unused in range(option_count):
        if cursor + 9 > len(data):
            return None
        signature = struct.unpack_from('<I', data, cursor)[0]
        value = struct.unpack_from('<I', data, cursor + 4)[0]
        marker = data[cursor + 8]
        if marker not in (0, 1, 2):
            return None
        options.append({
            'code': signature, 'name': option_name_from_signature(signature),
            'value': value, 'format': 'inventory'
        })
        cursor += 9
    return {'plus': plus, 'options': options, 'record_end': cursor}


def locate_item_record(data, slot, model):
    needle = struct.pack('<I', int(model))
    positions = []
    start = 0
    while True:
        position = data.find(needle, start)
        if position < 0:
            break
        positions.append(position)
        start = position + 1
    candidates = []
    for position in positions:
        anchors = []
        if position >= 5 and data[position - 5] == slot and data[position - 4:position] == b'\x00\x00\x00\x00':
            anchors.append('slot+rent')
        if position >= 9 and data[position - 9] == slot:
            anchors.append('slot+extended')
        if not anchors:
            continue
        parsed = parse_equip_payload(data, position)
        if parsed:
            parsed['item_id_position'] = position
            parsed['anchor'] = anchors[0]
            candidates.append(parsed)
    if len(candidates) == 1:
        return candidates[0]
    return None


def hex_window(data, position, before=16, after=36):
    start = max(0, position - before)
    end = min(len(data), position + after)
    return '%d..%d: %s' % (
        start, end, ' '.join('%02X' % value for value in data[start:end]))


def log_capture_diagnostics(data, items):
    plugin_log('0x3013 diagnostics: packet=%d bytes, eligible inventory=%d' % (
        len(data), len(items)))
    if not items:
        plugin_log('0x3013 diagnostics: get_inventory returned no eligible bag items')
        return
    for item in items[:12]:
        model = int(item.get('model', 0))
        needle = struct.pack('<I', model)
        offsets = []
        start = 0
        while len(offsets) < 4:
            position = data.find(needle, start)
            if position < 0:
                break
            offsets.append(position)
            start = position + 1
        plugin_log('0x3013 item slot=%d model=%d name=%s offsets=%s' % (
            item['slot'], model, item.get('name', 'Unknown'),
            ','.join(str(value) for value in offsets) if offsets else 'NOT_FOUND'))
        for position in offsets:
            plugin_log('0x3013 model context slot=%d modelOffset=%d %s' % (
                item['slot'], position, hex_window(data, position)))


def capture_character_inventory(data, quiet=False, diagnostics=False):
    global capture_generation, last_capture_time
    items = inventory_snapshot()
    verified = 0
    ambiguous = 0
    new_cache = {}
    for item in items:
        record = locate_item_record(data, item['slot'], item['model'])
        if not record:
            ambiguous += 1
            continue
        new_cache[item['slot']] = {
            'model': item['model'], 'options': record['options'],
            'plus': record['plus'], 'source': '0x3013 character data',
            'anchor': record['anchor'], 'captured_at': time.time()
        }
        verified += 1
    if verified:
        captured_items.clear()
        captured_items.update(new_cache)
        capture_generation += 1
        last_capture_time = time.time()
        set_capture_status('0x3013 captured: %d verified, %d unresolved' % (
            verified, ambiguous), COLOR_SUCCESS if ambiguous == 0 else COLOR_WARNING)
        if not quiet:
            plugin_log('0x3013 inventory capture: %d verified, %d unresolved' % (
                verified, ambiguous))
        refresh_inventory()
    else:
        if not quiet:
            set_capture_status('0x3013 received, but no item record was verified', COLOR_ERROR)
            plugin_log('0x3013 received (%d bytes), no eligible item record was verified' % len(data))
        if diagnostics:
            log_capture_diagnostics(data, items)


def teleported():
    if not last_capture_time or time.time() - last_capture_time > 5.0:
        set_capture_status('Teleport completed; waiting for verified 0x3013 data...', COLOR_WARNING)


def disconnected():
    global pending_character_data, pending_character_data_attempts
    global single_roll_item
    if is_running:
        stop_automation('Disconnected; automation stopped', COLOR_ERROR)
    captured_items.clear()
    pending_character_data = None
    pending_character_data_attempts = 0
    single_roll_item = None
    set_capture_status('Disconnected; inventory capture cleared', COLOR_MUTED)


def event_loop():
    global pending_character_data, pending_character_data_attempts
    # handle_joymax can run before phBot publishes its refreshed get_inventory()
    # snapshot. Retry the last character-data packet briefly from the normal loop.
    if pending_character_data is None:
        return
    if time.time() - pending_character_data_time < 0.20:
        return
    data = pending_character_data
    pending_character_data_attempts += 1
    before_generation = capture_generation
    final_attempt = pending_character_data_attempts >= 6
    capture_character_inventory(data, quiet=not final_attempt, diagnostics=final_attempt)
    if capture_generation != before_generation or pending_character_data_attempts >= 6:
        pending_character_data = None
        pending_character_data_attempts = 0


def handle_joymax(opcode, data):
    global pending_character_data, pending_character_data_time
    global pending_character_data_attempts
    try:
        if opcode == OPCODE_CHARACTER_DATA:
            pending_character_data = bytes(data)
            pending_character_data_time = time.time()
            pending_character_data_attempts = 0
            set_capture_status('0x3013 received; verifying inventory records...', COLOR_WARNING)
        elif opcode == OPCODE_FORTUNE_RESPONSE:
            if single_roll_item is not None:
                process_single_roll_response(data)
            elif is_running:
                process_fortune_response(data)
    except Exception as error:
        plugin_log('Packet processing error for 0x%04X: %s' % (opcode, error))
        if opcode == OPCODE_CHARACTER_DATA:
            set_capture_status('0x3013 parse error; see phBot log', COLOR_ERROR)
    return True


def move_page(widgets, visible):
    for widget, x, y in widgets:
        QtBind.move(gui, widget, x if visible else OFFSCREEN_X, y)


def show_queue_page():
    move_page(setup_page_widgets, False)
    move_page(queue_page_widgets, True)
    QtBind.move(gui, btn_show_queue, OFFSCREEN_X, 6)
    QtBind.move(gui, btn_show_setup, 345, 6)
    refresh_queue()
    set_status('Queue controls ready', COLOR_MUTED)


def show_setup_page():
    move_page(queue_page_widgets, False)
    move_page(setup_page_widgets, True)
    QtBind.move(gui, btn_show_setup, OFFSCREEN_X, 6)
    QtBind.move(gui, btn_show_queue, 345, 6)


# GUI
gui = QtBind.init(__name__, pName)

QtBind.createLabel(gui, '<font color="%s" size="4"><b>✦ %s</b></font>' % (
    COLOR_PRIMARY, pName), 12, 6)
QtBind.createLabel(gui, '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion), 205, 12)
btn_show_queue = QtBind.createButton(gui, 'show_queue_page', 'Queue & Start →', 345, 6)
btn_show_setup = QtBind.createButton(gui, 'show_setup_page', '← Item Setup', OFFSCREEN_X, 6)
QtBind.createButton(gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(gui, u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' % COLOR_PRIMARY, 565, 11)
QtBind.createLineEdit(gui, '', 12, 30, 716, 1)

setup_page_widgets = []
queue_page_widgets = []

lbl_inventory_header = QtBind.createLabel(gui, '<font color="%s"><b>1. ELIGIBLE INVENTORY</b></font>' % COLOR_PRIMARY, 12, 42)
btn_refresh = QtBind.createButton(gui, 'refresh_inventory', '↻ Refresh', 12, 62)
btn_inspect = QtBind.createButton(gui, 'show_selected_item', 'Inspect Selected', 105, 62)
btn_test_roll = QtBind.createButton(gui, 'test_one_roll', 'Test One Roll', 225, 62)
lst_inventory = QtBind.createList(gui, 12, 88, 360, 160)
lbl_selected_header = QtBind.createLabel(gui, '<font color="%s"><b>SELECTED ITEM</b></font>' % COLOR_PRIMARY, 12, 260)
lbl_selected_item = QtBind.createLabel(gui, fixed_width_text(
    '<font color="%s"><b>No item selected</b></font>' % COLOR_MUTED, 350), 12, 282)

line_vertical = QtBind.createLineEdit(gui, '', 385, 42, 1, 264)
lbl_stats_header = QtBind.createLabel(gui, '<font color="%s"><b>2. AVAILABLE STATS</b></font>' % COLOR_PRIMARY, 400, 42)
lst_available_stats = QtBind.createList(gui, 400, 65, 140, 180)
lbl_targets_header = QtBind.createLabel(gui, '<font color="%s"><b>ITEM TARGETS</b></font>' % COLOR_PRIMARY, 555, 42)
lst_targets = QtBind.createList(gui, 555, 65, 160, 145)
btn_remove_target = QtBind.createButton(gui, 'remove_target', 'Remove Target', 555, 216)
btn_queue_item = QtBind.createButton(gui, 'queue_selected_item', 'Add Item to Queue', 575, 248)
lbl_required = QtBind.createLabel(gui, 'Required lines', 400, 258)
txt_target_count = QtBind.createLineEdit(gui, '1', 400, 279, 45, 20)
btn_add_target = QtBind.createButton(gui, 'add_target', 'Add / Update', 455, 275)

setup_page_widgets.extend([
    (lbl_inventory_header, 12, 42), (btn_refresh, 12, 62),
    (btn_inspect, 105, 62), (btn_test_roll, 225, 62),
    (lst_inventory, 12, 88), (lbl_selected_header, 12, 260),
    (lbl_selected_item, 12, 282), (line_vertical, 385, 42),
    (lbl_stats_header, 400, 42), (lst_available_stats, 400, 65),
    (lbl_targets_header, 555, 42), (lst_targets, 555, 65),
    (btn_remove_target, 555, 216), (btn_queue_item, 575, 248),
    (lbl_required, 400, 258), (txt_target_count, 400, 279),
    (btn_add_target, 455, 275)
])

lbl_queue_header = QtBind.createLabel(gui, '<font color="%s"><b>4. AUTOMATION QUEUE</b></font>' % COLOR_PRIMARY, OFFSCREEN_X, 48)
lbl_queue_help = QtBind.createLabel(gui, fixed_width_text('<font color="%s">Review every item and target before starting.</font>' % COLOR_MUTED, 500), OFFSCREEN_X, 70)
lst_queue = QtBind.createList(gui, OFFSCREEN_X, 92, 535, 120)
btn_remove_queue = QtBind.createButton(gui, 'remove_queued_item', 'Remove Item', OFFSCREEN_X, 92)
btn_clear_queue = QtBind.createButton(gui, 'clear_queue', 'Clear Queue', OFFSCREEN_X, 124)
btn_start = QtBind.createButton(gui, 'start_automation', '▶ START', OFFSCREEN_X, 228)
btn_stop = QtBind.createButton(gui, 'stop_automation', '■ STOP', OFFSCREEN_X, 228)
lbl_capture = QtBind.createLabel(gui, fixed_width_text('<font color="%s">Waiting for a verified Fortune response...</font>' % COLOR_WARNING, 480), OFFSCREEN_X, 262)
lbl_status = QtBind.createLabel(gui, fixed_width_text('<font color="%s"><b>Ready</b></font>' % COLOR_MUTED, 680), OFFSCREEN_X, 292)

queue_page_widgets.extend([
    (lbl_queue_header, 12, 48), (lbl_queue_help, 12, 70),
    (lst_queue, 12, 92), (btn_remove_queue, 560, 92),
    (btn_clear_queue, 560, 124), (btn_start, 12, 228),
    (btn_stop, 115, 228), (lbl_capture, 225, 232),
    (lbl_status, 12, 272)
])

refresh_inventory()
set_capture_status('Current stats appear after the first verified Fortune response', COLOR_WARNING)

log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
