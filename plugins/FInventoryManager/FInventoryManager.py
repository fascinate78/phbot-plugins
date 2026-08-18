from phBot import *
import QtBind
import json
import os
import struct
import time
import webbrowser


pName = 'FInventoryManager'
pVersion = '3.0.2'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'
LEGACY_CONFIG_DIRECTORY = 'InventoryManagerV1'

# Verified on the target vSRO environment by FInventoryProtocolTester.
OPCODE_INVENTORY_OPERATION = 0x7034
OPCODE_INVENTORY_RESPONSE = 0xB034
OP_INVENTORY_MOVE = 0x00
INVENTORY_PACKET_ENCRYPTED = False
DEFAULT_BAG_START_SLOT = 13
ISRO_BAG_START_SLOT = 17
ISRO_LOCALE = 18

QUIET_PERIOD_SECONDS = 1.0
RESPONSE_TIMEOUT_SECONDS = 3.0
SNAPSHOT_TIMEOUT_SECONDS = 3.0
MAX_REPLANS = 3
STORAGE_SESSION_DATA = b'\xFF\x00\x00\x00'

STATE_IDLE = 'IDLE'
STATE_PREVIEW_READY = 'PREVIEW_READY'
STATE_PREPARING = 'PREPARING'
STATE_SORTING = 'SORTING'
STATE_WAITING_RESPONSE = 'WAITING_RESPONSE'
STATE_WAITING_SNAPSHOT = 'WAITING_SNAPSHOT'
STATE_VERIFYING = 'VERIFYING'
STATE_REPLANNING = 'REPLANNING'
STATE_DONE = 'DONE'
STATE_CANCELLED = 'CANCELLED'
STATE_ERROR = 'ERROR'

COLOR_PRIMARY = '#5b57e0'
COLOR_MUTED = '#6b7280'
COLOR_SUCCESS = '#22863a'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#c62828'

DEFAULT_CATEGORY_ORDER = [
    'Potion', 'Pill', 'Ammo', 'Weapon', 'Armor', 'Accessory',
    'Other Equipment', 'Alchemy Material', 'Elixir', 'Stone',
    'Quest', 'Return Scroll', 'Scroll', 'Pet Item', 'Trade Item', 'Misc'
]

# Exact overrides are intentionally empty in V1. They provide safe extension points
# for verified custom-server items without changing classifier code.
MODEL_CATEGORY_OVERRIDES = {}
SERVERNAME_CATEGORY_OVERRIDES = {}

# Stable internal-name rules. Order matters: specific categories precede broad ones.
SERVERNAME_RULES = [
    ('Return Scroll', ('RETURN_SCROLL', 'SCROLL_RETURN', 'RETURNSCROLL')),
    ('Potion', ('_POTION_', 'POTION_HP', 'POTION_MP', 'RECOVERY_POTION',
                'HP_SUPERSET', 'MP_SUPERSET')),
    ('Pill', ('_PILL_', 'CURE_PILL')),
    ('Ammo', ('_ARROW_', '_BOLT_', 'QUIVER')),
    ('Elixir', ('ELIXIR', 'ENHANCER')),
    ('Stone', ('_STONE_', 'MAGICSTONE', 'ATTRSTONE')),
    ('Alchemy Material', ('ITEM_ETC_ARCHEMY_', 'ALCHEMY_MATERIAL', '_ELEMENT_')),
    ('Quest', ('ITEM_QSP_', '_QUEST_', 'QUEST_ITEM')),
    ('Pet Item', ('ITEM_COS_', '_PET_', 'PET_ITEM')),
    ('Trade Item', ('ITEM_TRADE_', '_TRADE_')),
    ('Scroll', ('_SCROLL_', 'ITEM_ETC_SCROLL', 'GLOBAL_CHATTING'))
]

category_order = list(DEFAULT_CATEGORY_ORDER)
enabled_categories = dict((name, True) for name in DEFAULT_CATEGORY_ORDER)
storage_category_order = list(DEFAULT_CATEGORY_ORDER)
storage_enabled_categories = dict((name, True) for name in DEFAULT_CATEGORY_ORDER)
state = STATE_IDLE
last_snapshot = None
last_observed_fingerprint = None
last_inventory_change_time = 0.0
preview_snapshot = None
preview_plan = []
pending_operation = None
cancel_requested = False
replan_count = 0
completed_operations = 0
planned_total = 0
connected_to_game = False
inventory_quick_mode = False
current_page = 'dashboard'
OFFSCREEN_X = 3000

STORAGE_UNKNOWN = 'UNKNOWN'
STORAGE_SNAPSHOT_AVAILABLE = 'SNAPSHOT_AVAILABLE'
STORAGE_PACKET_SEEN = 'PACKET_SEEN'
STORAGE_RESPONSE_SEEN = 'RESPONSE_SEEN'
STORAGE_VERIFIED = 'VERIFIED'
STORAGE_ERROR = 'ERROR'

storage_state = STORAGE_UNKNOWN
storage_snapshot = None
storage_preview_snapshot = None
storage_preview_plan = []
storage_pending = None
storage_cancel_requested = False
storage_replan_count = 0
storage_completed_operations = 0
storage_planned_total = 0
storage_quick_mode = False


def fixed_width_text(content, width):
    return ('<table width="%d" cellspacing="0" cellpadding="0">'
            '<tr><td>%s</td></tr></table>') % (width, content)


def config_path():
    root = get_config_dir()
    if not root:
        return None
    return os.path.join(root, pName, 'settings.json')


def legacy_config_path():
    root = get_config_dir()
    if not root:
        return None
    return os.path.join(root, LEGACY_CONFIG_DIRECTORY, 'settings.json')


def plugin_log(message):
    log('[%s][Inventory] %s' % (pName, message))


class InventoryItem(object):
    def __init__(self, slot, raw_item):
        self.slot = slot
        self.model = int(raw_item.get('model', 0) or 0)
        self.servername = str(raw_item.get('servername', '') or '')
        self.name = str(raw_item.get('name', '') or '')
        self.quantity = int(raw_item.get('quantity', 0) or 0)
        self.plus = int(raw_item.get('plus', 0) or 0)
        self.durability = int(raw_item.get('durability', 0) or 0)
        metadata = get_item(self.model) or {}
        self.max_stack = int(metadata.get('max_stack', 1) or 1)
        self.tid1 = int(metadata.get('tid1', 0) or 0)
        self.tid2 = int(metadata.get('tid2', 0) or 0)
        self.tid3 = int(metadata.get('tid3', 0) or 0)
        self.level = int(metadata.get('level', 0) or 0)
        self.category = classify_item(self)

    def fingerprint(self):
        return (self.model, self.quantity, self.plus, self.durability)

    def equivalent_key(self):
        # Quantities are deliberately ignored for stackable items. This prevents
        # cosmetic reordering of two stacks from accidentally merging them.
        if self.max_stack > 1:
            return ('stack', self.model)
        return ('item', self.model, self.plus, self.durability)

    def sort_key(self, priorities):
        return (priorities.get(self.category, len(priorities)), self.model,
                self.servername, self.slot)

    def display_name(self):
        return self.name or self.servername or ('Model %d' % self.model)


class InventorySnapshot(object):
    def __init__(self, size, gold, items, bag_start):
        self.size = size
        self.gold = gold
        self.items = items
        self.bag_start = bag_start

    def fingerprint(self):
        values = []
        for slot, item in enumerate(self.items):
            values.append((slot, None) if item is None else
                          (slot, item.model, item.quantity, item.plus, item.durability))
        return tuple(values)

    def occupied_bag_count(self):
        return sum(1 for item in self.items[self.bag_start:] if item is not None)


class MoveOperation(object):
    def __init__(self, source, destination, quantity, kind='move'):
        self.source = source
        self.destination = destination
        self.requested_quantity = quantity
        self.kind = kind


def classify_item(item):
    if item.model in MODEL_CATEGORY_OVERRIDES:
        return MODEL_CATEGORY_OVERRIDES[item.model]
    if item.servername in SERVERNAME_CATEGORY_OVERRIDES:
        return SERVERNAME_CATEGORY_OVERRIDES[item.servername]

    # tid1=1 and these tid2 branches are established by local equip logic.
    if item.tid1 == 1:
        if item.tid2 == 6:
            return 'Weapon'
        if item.tid2 in (1, 2, 3, 4, 9, 10, 11):
            return 'Armor'
        if item.tid2 in (5, 12):
            return 'Accessory'
        return 'Other Equipment'

    internal = item.servername.upper()
    for category, tokens in SERVERNAME_RULES:
        if any(token in internal for token in tokens):
            return category
    return 'Misc'


def get_bag_start_slot():
    try:
        return ISRO_BAG_START_SLOT if get_locale() == ISRO_LOCALE else DEFAULT_BAG_START_SLOT
    except Exception:
        return DEFAULT_BAG_START_SLOT


def take_snapshot():
    raw = get_inventory()
    if not raw or not isinstance(raw.get('items'), list):
        return None
    items = []
    for slot, raw_item in enumerate(raw['items']):
        if raw_item is None or int(raw_item.get('model', 0) or 0) == 0:
            items.append(None)
        else:
            items.append(InventoryItem(slot, raw_item))
    return InventorySnapshot(int(raw.get('size', len(items)) or len(items)),
                             int(raw.get('gold', 0) or 0), items,
                             get_bag_start_slot())


def take_storage_snapshot():
    raw = get_storage()
    if not raw or not isinstance(raw.get('items'), list):
        return None
    items = []
    for slot, raw_item in enumerate(raw['items']):
        if raw_item is None or int(raw_item.get('model', 0) or 0) == 0:
            items.append(None)
        else:
            items.append(InventoryItem(slot, raw_item))
    return InventorySnapshot(int(raw.get('size', len(items)) or len(items)),
                             int(raw.get('gold', 0) or 0), items, 0)


def enabled_priority_map(order=None, enabled_map=None):
    if order is None:
        order = category_order
    if enabled_map is None:
        enabled_map = enabled_categories
    enabled = [name for name in order if enabled_map.get(name, True)]
    disabled = [name for name in order if not enabled_map.get(name, True)]
    ordered = enabled + disabled
    return dict((name, index) for index, name in enumerate(ordered))


def build_desired_layout(snapshot, order=None, enabled_map=None):
    priorities = enabled_priority_map(order, enabled_map)
    bag_items = [item for item in snapshot.items[snapshot.bag_start:] if item is not None]
    bag_items.sort(key=lambda item: item.sort_key(priorities))
    desired = list(snapshot.items[:snapshot.bag_start])
    desired.extend(bag_items)
    desired.extend([None] * (len(snapshot.items) - len(desired)))
    return desired


def equivalent(current, desired):
    if current is None or desired is None:
        return current is None and desired is None
    return current.equivalent_key() == desired.equivalent_key()


def create_plan(snapshot, order=None, enabled_map=None):
    desired = build_desired_layout(snapshot, order, enabled_map)
    working = list(snapshot.items)
    operations = []

    for destination in range(snapshot.bag_start, len(working)):
        target = desired[destination]
        if equivalent(working[destination], target):
            continue
        source = None
        for candidate in range(destination + 1, len(working)):
            if equivalent(working[candidate], target):
                source = candidate
                break
        if source is None:
            # A None target is naturally pushed backwards by earlier swaps.
            if target is None:
                continue
            raise ValueError('Could not locate desired item for slot %d.' % destination)
        source_item = working[source]
        if source_item is None:
            continue
        operations.append(MoveOperation(source, destination, source_item.quantity))
        working[source], working[destination] = working[destination], working[source]
    return desired, operations


def create_storage_plan(snapshot):
    """Plan safe full-source merges first, then category-order swaps."""
    working = []
    for item in snapshot.items:
        if item is None:
            working.append(None)
        else:
            working.append({'item': item, 'quantity': item.quantity})
    operations = []

    # Consolidate matching stacks toward the lowest occupied slot. Every request carries
    # the complete current source quantity; B034 decides how much fits.
    for destination in range(len(working)):
        target = working[destination]
        if target is None or target['item'].max_stack <= 1:
            continue
        for source in range(destination + 1, len(working)):
            candidate = working[source]
            if candidate is None or candidate['item'].model != target['item'].model:
                continue
            capacity = target['item'].max_stack - target['quantity']
            if capacity <= 0:
                break
            requested = candidate['quantity']
            applied = min(requested, capacity)
            operations.append(MoveOperation(source, destination, requested, 'merge'))
            target['quantity'] += applied
            candidate['quantity'] -= applied
            if candidate['quantity'] == 0:
                working[source] = None

    priorities = enabled_priority_map(storage_category_order, storage_enabled_categories)
    occupied = [entry for entry in working if entry is not None]
    occupied.sort(key=lambda entry: (
        priorities.get(entry['item'].category, len(priorities)),
        entry['item'].model, entry['item'].servername,
        -entry['quantity'], entry['item'].slot))
    desired = occupied + [None] * (len(working) - len(occupied))
    for destination in range(len(working)):
        target = desired[destination]
        current = working[destination]
        current_key = None if current is None else (
            current['item'].equivalent_key(), current['quantity'])
        target_key = None if target is None else (
            target['item'].equivalent_key(), target['quantity'])
        if current_key == target_key:
            continue
        source = None
        for candidate_slot in range(destination + 1, len(working)):
            candidate = working[candidate_slot]
            candidate_key = None if candidate is None else (
                candidate['item'].equivalent_key(), candidate['quantity'])
            if candidate_key == target_key:
                source = candidate_slot
                break
        if source is None:
            if target is None:
                continue
            raise ValueError('Could not locate desired storage item for slot %d.' % destination)
        source_entry = working[source]
        kind = 'move' if working[destination] is None else 'swap'
        operations.append(MoveOperation(
            source, destination, source_entry['quantity'], kind))
        working[source], working[destination] = working[destination], working[source]
    return desired, operations


def changed_slots(before, after):
    result = []
    if before is None or after is None:
        return result
    count = max(len(before.items), len(after.items))
    for slot in range(count):
        old = before.items[slot] if slot < len(before.items) else None
        new = after.items[slot] if slot < len(after.items) else None
        old_key = None if old is None else old.fingerprint()
        new_key = None if new is None else new.fingerprint()
        if old_key != new_key:
            result.append(slot)
    return result


def build_move_payload(operation):
    return struct.pack('<BBBH', OP_INVENTORY_MOVE, operation.source,
                       operation.destination, operation.requested_quantity)


def decode_b034(data):
    raw = bytes(data or b'')
    if not raw:
        return {'success': False, 'supported': False, 'raw': raw}
    if raw[0] == 0x01 and len(raw) >= 7:
        return {
            'success': True, 'supported': True, 'operation': raw[1],
            'source': raw[2], 'destination': raw[3],
            'applied_quantity': struct.unpack_from('<H', raw, 4)[0],
            'trailing': raw[6], 'raw': raw
        }
    if raw[0] == 0x02:
        return {'success': False, 'supported': True, 'error_data': raw[1:], 'raw': raw}
    return {'success': False, 'supported': False, 'raw': raw}


def safe_item_text(item):
    return 'EMPTY' if item is None else '%s x%d [%s]' % (
        item.display_name(), item.quantity, item.category)


def packet_hex(data):
    return ' '.join('%02X' % value for value in bytearray(data or b'')) or '<EMPTY>'


def decode_observed_storage_response(data):
    raw = bytes(data or b'')
    if len(raw) < 4:
        return None
    result = {'success_byte': raw[0], 'operation': raw[1],
              'source': raw[2], 'destination': raw[3], 'trailing': raw[4:]}
    if raw[0] == 0x01 and raw[1] == 0x01 and len(raw) >= 6:
        result['applied_quantity'] = struct.unpack_from('<H', raw, 4)[0]
        result['trailing'] = raw[6:]
    return result


def settings_data():
    return {
        'version': 2,
        'inventory_rules': {
            'category_order': list(category_order),
            'enabled_categories': dict(enabled_categories)
        },
        'storage_rules': {
            'category_order': list(storage_category_order),
            'enabled_categories': dict(storage_enabled_categories)
        }
    }


def save_settings():
    path = config_path()
    if not path:
        plugin_log('Settings could not be saved: config directory unavailable.')
        return False
    folder = os.path.dirname(path)
    temp_path = path + '.tmp'
    try:
        if not os.path.isdir(folder):
            os.makedirs(folder)
        with open(temp_path, 'w') as output:
            json.dump(settings_data(), output, indent=2, sort_keys=True)
        os.replace(temp_path, path)
        return True
    except (OSError, IOError, ValueError, TypeError) as error:
        plugin_log('Settings save error: %s' % error)
        return False


def normalize_rules(data):
    if not isinstance(data, dict):
        raise ValueError('rules must be an object')
    saved_order = data.get('category_order', [])
    if not isinstance(saved_order, list):
        raise ValueError('category_order must be a list')
    clean_order = [name for name in saved_order if name in DEFAULT_CATEGORY_ORDER]
    clean_order.extend(name for name in DEFAULT_CATEGORY_ORDER if name not in clean_order)
    saved_enabled = data.get('enabled_categories', {})
    if not isinstance(saved_enabled, dict):
        raise ValueError('enabled_categories must be an object')
    clean_enabled = dict((name, bool(saved_enabled.get(name, True)))
                         for name in DEFAULT_CATEGORY_ORDER)
    return clean_order, clean_enabled


def load_settings():
    global category_order, enabled_categories
    global storage_category_order, storage_enabled_categories
    path = config_path()
    migration = False
    if not path:
        return
    source_path = path
    if not os.path.isfile(source_path):
        old_path = legacy_config_path()
        if not old_path or not os.path.isfile(old_path):
            return
        source_path = old_path
        migration = True
    try:
        with open(source_path, 'r') as source:
            data = json.load(source)
        if 'inventory_rules' in data:
            category_order, enabled_categories = normalize_rules(data.get('inventory_rules'))
            storage_category_order, storage_enabled_categories = normalize_rules(
                data.get('storage_rules', data.get('inventory_rules')))
        else:
            category_order, enabled_categories = normalize_rules(data)
            storage_category_order = list(category_order)
            storage_enabled_categories = dict(enabled_categories)
            migration = True
        if migration and save_settings():
            plugin_log('Existing sorting rules migrated to the production configuration.')
    except (OSError, IOError, ValueError, TypeError) as error:
        category_order = list(DEFAULT_CATEGORY_ORDER)
        enabled_categories = dict((name, True) for name in DEFAULT_CATEGORY_ORDER)
        storage_category_order = list(DEFAULT_CATEGORY_ORDER)
        storage_enabled_categories = dict((name, True) for name in DEFAULT_CATEGORY_ORDER)
        plugin_log('Invalid settings ignored: %s' % error)


def status_html(text, color):
    return fixed_width_text('<font color="%s"><b>%s</b></font>' % (color, text), 205)


gui = QtBind.init(__name__, pName)
QtBind.createLabel(gui, '<font color="%s" size="4"><b>FInventoryManager</b></font>' % COLOR_PRIMARY, 12, 6)
QtBind.createLabel(gui, '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion), 205, 12)
btn_dashboard_page = QtBind.createButton(gui, 'show_dashboard_page', 'Dashboard', 270, 6)
btn_rules_page = QtBind.createButton(gui, 'show_rules_page', 'Inventory', 350, 6)
btn_storage_page = QtBind.createButton(gui, 'show_storage_page', 'Storage', 420, 6)
btn_discord = QtBind.createButton(gui, 'discord_clicked', u'\U0001f4ac Discord', 485, 6)
QtBind.createLabel(gui, u'<font color="%s"><b>\u269c Made By FascinaTe</b></font>' % COLOR_PRIMARY, 580, 11)
QtBind.createLineEdit(gui, '', 12, 30, 716, 1)

lbl_dashboard_section = QtBind.createLabel(
    gui, '<font color="%s"><b>QUICK SORT DASHBOARD</b></font>' % COLOR_PRIMARY, 12, 48)
lbl_dashboard_help = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s">One click refreshes, plans, and safely executes. Open personal storage before Storage Quick Sort.</font>' %
                          COLOR_MUTED, 700), 12, 70)
lbl_dash_inventory_title = QtBind.createLabel(
    gui, '<font color="%s"><b>INVENTORY</b></font>' % COLOR_PRIMARY, 55, 112)
lbl_dash_inventory_status = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s"><b>Ready</b></font>' % COLOR_SUCCESS, 275), 55, 140)
btn_quick_inventory = QtBind.createButton(
    gui, 'quick_sort_inventory_clicked', 'Quick Sort Inventory', 55, 178)
btn_open_inventory = QtBind.createButton(
    gui, 'show_rules_page', 'Inventory Details', 190, 178)
line_dashboard = QtBind.createLineEdit(gui, '', 364, 105, 1, 125)
lbl_dash_storage_title = QtBind.createLabel(
    gui, '<font color="%s"><b>PERSONAL STORAGE</b></font>' % COLOR_PRIMARY, 405, 112)
lbl_dash_storage_status = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s"><b>Open storage first</b></font>' % COLOR_WARNING, 275),
    405, 140)
btn_quick_storage = QtBind.createButton(
    gui, 'quick_sort_storage_clicked', 'Quick Sort Storage', 405, 178)
btn_open_storage = QtBind.createButton(
    gui, 'show_storage_page', 'Storage Details', 535, 178)
lbl_dashboard_last = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s">Last result: Ready</font>' % COLOR_MUTED, 680),
    30, 250)

lbl_rules_section = QtBind.createLabel(
    gui, '<font color="%s"><b>SORTING RULES</b></font>' % COLOR_PRIMARY, 12, 42)
lst_categories = QtBind.createList(gui, 12, 62, 295, 155)
btn_up = QtBind.createButton(gui, 'move_category_up', 'Move Up', 12, 225)
btn_down = QtBind.createButton(gui, 'move_category_down', 'Move Down', 82, 225)
btn_toggle = QtBind.createButton(gui, 'toggle_category', 'Enable / Disable', 167, 225)
btn_reset = QtBind.createButton(gui, 'reset_categories', 'Reset Default', 12, 255)
btn_save = QtBind.createButton(gui, 'save_categories_clicked', 'Save Rules', 105, 255)

line_columns = QtBind.createLineEdit(gui, '', 320, 42, 1, 245)
lbl_status_section = QtBind.createLabel(
    gui, '<font color="%s"><b>INVENTORY STATUS</b></font>' % COLOR_PRIMARY, 335, 42)
lbl_items_title = QtBind.createLabel(gui, '<font color="%s"><b>Items:</b></font>' % COLOR_MUTED, 335, 68)
lbl_items = QtBind.createLabel(gui, fixed_width_text('0 / 0', 205), 420, 68)
lbl_state_title = QtBind.createLabel(gui, '<font color="%s"><b>State:</b></font>' % COLOR_MUTED, 335, 94)
lbl_state = QtBind.createLabel(gui, status_html('Ready', COLOR_SUCCESS), 420, 94)
lbl_planned_title = QtBind.createLabel(gui, '<font color="%s"><b>Planned:</b></font>' % COLOR_MUTED, 335, 120)
lbl_planned = QtBind.createLabel(gui, fixed_width_text('-', 205), 420, 120)
lbl_completed_title = QtBind.createLabel(gui, '<font color="%s"><b>Completed:</b></font>' % COLOR_MUTED, 335, 146)
lbl_completed = QtBind.createLabel(gui, fixed_width_text('-', 205), 420, 146)
lbl_current_title = QtBind.createLabel(gui, '<font color="%s"><b>Current:</b></font>' % COLOR_MUTED, 335, 172)
lbl_current = QtBind.createLabel(gui, fixed_width_text('-', 205), 420, 172)
lbl_requested_title = QtBind.createLabel(gui, '<font color="%s"><b>Requested:</b></font>' % COLOR_MUTED, 335, 198)
lbl_requested = QtBind.createLabel(gui, fixed_width_text('-', 205), 420, 198)
lbl_applied_title = QtBind.createLabel(gui, '<font color="%s"><b>Applied:</b></font>' % COLOR_MUTED, 335, 224)
lbl_applied = QtBind.createLabel(gui, fixed_width_text('-', 205), 420, 224)
lbl_response_title = QtBind.createLabel(gui, '<font color="%s"><b>Last response:</b></font>' % COLOR_MUTED, 335, 250)
lbl_response = QtBind.createLabel(gui, fixed_width_text('-', 205), 420, 250)

btn_refresh = QtBind.createButton(gui, 'refresh_clicked', 'Refresh', 335, 278)
btn_preview = QtBind.createButton(gui, 'preview_clicked', 'Preview Sort', 400, 278)
btn_sort = QtBind.createButton(gui, 'sort_clicked', 'Start Sort', 12, 265)
btn_cancel = QtBind.createButton(gui, 'cancel_clicked', 'Cancel', 90, 265)

lbl_preview_section = QtBind.createLabel(
    gui, '<font color="%s"><b>PREVIEW / UNCLASSIFIED ITEMS</b></font>' % COLOR_PRIMARY, 12, 42)
lbl_preview_help = QtBind.createLabel(
    gui, '<font color="%s">Preview sends no packets. Review changes before starting.</font>' % COLOR_MUTED, 12, 62)
lst_preview = QtBind.createList(gui, 12, 82, 716, 170)

btn_storage_refresh = QtBind.createButton(gui, 'storage_refresh_clicked', 'Refresh', 12, 90)
btn_storage_preview = QtBind.createButton(gui, 'storage_preview_clicked', 'Preview Sort', 115, 90)
btn_storage_start = QtBind.createButton(gui, 'storage_sort_clicked', 'Start Sort', 250, 90)
btn_storage_cancel_sort = QtBind.createButton(gui, 'storage_cancel_clicked', 'Cancel', 335, 90)

lbl_storage_rules = QtBind.createLabel(
    gui, '<font color="%s"><b>STORAGE RULES</b></font>' % COLOR_PRIMARY, 12, 125)
lst_storage_categories = QtBind.createList(gui, 12, 145, 295, 155)
btn_storage_up = QtBind.createButton(gui, 'storage_move_up', 'Up', 12, 258)
btn_storage_down = QtBind.createButton(gui, 'storage_move_down', 'Down', 52, 258)
btn_storage_toggle = QtBind.createButton(gui, 'storage_toggle_category', 'Enable / Disable', 102, 258)
btn_storage_reset = QtBind.createButton(gui, 'storage_reset_categories', 'Reset', 12, 288)
btn_storage_save = QtBind.createButton(gui, 'storage_save_rules', 'Save', 65, 288)

lbl_storage_items = QtBind.createLabel(
    gui, '<font color="%s"><b>STORAGE ITEMS / PREVIEW</b></font>' % COLOR_PRIMARY, 285, 125)
lst_storage_items = QtBind.createList(gui, 285, 145, 716, 170)
lbl_storage_lock = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s">Preview first, or use Quick Sort from Dashboard.</font>' %
                          COLOR_MUTED, 430), 285, 296)

line_storage_columns = QtBind.createLineEdit(gui, '', 320, 42, 1, 245)
lbl_storage_status_section = QtBind.createLabel(
    gui, '<font color="%s"><b>PERSONAL STORAGE STATUS</b></font>' % COLOR_PRIMARY, 335, 42)
lbl_storage_count_title = QtBind.createLabel(
    gui, '<font color="%s"><b>Items:</b></font>' % COLOR_MUTED, 335, 68)
lbl_storage_count = QtBind.createLabel(gui, fixed_width_text('0 / 0', 205), 420, 68)
lbl_storage_detail_state_title = QtBind.createLabel(
    gui, '<font color="%s"><b>State:</b></font>' % COLOR_MUTED, 335, 94)
lbl_storage_detail_state = QtBind.createLabel(
    gui, status_html('Open storage first', COLOR_WARNING), 420, 94)
lbl_storage_planned_title = QtBind.createLabel(
    gui, '<font color="%s"><b>Planned:</b></font>' % COLOR_MUTED, 335, 120)
lbl_storage_planned = QtBind.createLabel(gui, fixed_width_text('-', 205), 420, 120)
lbl_storage_completed_title = QtBind.createLabel(
    gui, '<font color="%s"><b>Completed:</b></font>' % COLOR_MUTED, 335, 146)
lbl_storage_completed = QtBind.createLabel(gui, fixed_width_text('-', 205), 420, 146)
lbl_storage_current_title = QtBind.createLabel(
    gui, '<font color="%s"><b>Current:</b></font>' % COLOR_MUTED, 335, 172)
lbl_storage_current = QtBind.createLabel(gui, fixed_width_text('-', 205), 420, 172)
lbl_storage_requested_title = QtBind.createLabel(
    gui, '<font color="%s"><b>Requested:</b></font>' % COLOR_MUTED, 335, 198)
lbl_storage_requested = QtBind.createLabel(gui, fixed_width_text('-', 205), 420, 198)
lbl_storage_applied_title = QtBind.createLabel(
    gui, '<font color="%s"><b>Applied:</b></font>' % COLOR_MUTED, 335, 224)
lbl_storage_applied = QtBind.createLabel(gui, fixed_width_text('-', 205), 420, 224)
lbl_storage_response_title = QtBind.createLabel(
    gui, '<font color="%s"><b>Last response:</b></font>' % COLOR_MUTED, 335, 250)
lbl_storage_response = QtBind.createLabel(gui, fixed_width_text('-', 205), 420, 250)

RULES_PAGE_WIDGETS = (
    (lbl_rules_section, 12, 42), (lst_categories, 12, 62),
    (btn_up, 12, 225), (btn_down, 82, 225), (btn_toggle, 167, 225),
    (btn_reset, 12, 255), (btn_save, 105, 255), (line_columns, 320, 42),
    (lbl_status_section, 335, 42), (lbl_items_title, 335, 68), (lbl_items, 420, 68),
    (lbl_state_title, 335, 94), (lbl_state, 420, 94),
    (lbl_planned_title, 335, 120), (lbl_planned, 420, 120),
    (lbl_completed_title, 335, 146), (lbl_completed, 420, 146),
    (lbl_current_title, 335, 172), (lbl_current, 420, 172),
    (lbl_requested_title, 335, 198), (lbl_requested, 420, 198),
    (lbl_applied_title, 335, 224), (lbl_applied, 420, 224),
    (lbl_response_title, 335, 250), (lbl_response, 420, 250),
    (btn_refresh, 335, 278), (btn_preview, 400, 278)
)

DASHBOARD_PAGE_WIDGETS = (
    (lbl_dashboard_section, 12, 48), (lbl_dashboard_help, 12, 70),
    (lbl_dash_inventory_title, 55, 112), (lbl_dash_inventory_status, 55, 140),
    (btn_quick_inventory, 55, 178), (btn_open_inventory, 190, 178),
    (line_dashboard, 364, 105), (lbl_dash_storage_title, 405, 112),
    (lbl_dash_storage_status, 405, 140), (btn_quick_storage, 405, 178),
    (btn_open_storage, 535, 178), (lbl_dashboard_last, 30, 250)
)

PREVIEW_PAGE_WIDGETS = (
    (lbl_preview_section, 12, 42), (lbl_preview_help, 12, 62),
    (lst_preview, 12, 82), (btn_sort, 12, 265), (btn_cancel, 90, 265)
)

STORAGE_PAGE_WIDGETS = (
    (lbl_storage_rules, 12, 42), (lst_storage_categories, 12, 62),
    (btn_storage_up, 12, 225), (btn_storage_down, 82, 225),
    (btn_storage_toggle, 167, 225), (btn_storage_reset, 12, 255),
    (btn_storage_save, 105, 255), (line_storage_columns, 320, 42),
    (lbl_storage_status_section, 335, 42),
    (lbl_storage_count_title, 335, 68), (lbl_storage_count, 420, 68),
    (lbl_storage_detail_state_title, 335, 94), (lbl_storage_detail_state, 420, 94),
    (lbl_storage_planned_title, 335, 120), (lbl_storage_planned, 420, 120),
    (lbl_storage_completed_title, 335, 146), (lbl_storage_completed, 420, 146),
    (lbl_storage_current_title, 335, 172), (lbl_storage_current, 420, 172),
    (lbl_storage_requested_title, 335, 198), (lbl_storage_requested, 420, 198),
    (lbl_storage_applied_title, 335, 224), (lbl_storage_applied, 420, 224),
    (lbl_storage_response_title, 335, 250), (lbl_storage_response, 420, 250),
    (btn_storage_refresh, 335, 278), (btn_storage_preview, 440, 278)
)

STORAGE_PREVIEW_PAGE_WIDGETS = (
    (lbl_storage_items, 12, 42), (lbl_storage_lock, 12, 62),
    (lst_storage_items, 12, 82), (btn_storage_start, 12, 265),
    (btn_storage_cancel_sort, 90, 265)
)

def move_page(widgets, visible):
    for widget, x, y in widgets:
        QtBind.move(gui, widget, x if visible else OFFSCREEN_X, y)


def show_rules_page():
    global current_page
    current_page = 'rules'
    move_page(DASHBOARD_PAGE_WIDGETS, False)
    move_page(PREVIEW_PAGE_WIDGETS, False)
    move_page(STORAGE_PAGE_WIDGETS, False)
    move_page(STORAGE_PREVIEW_PAGE_WIDGETS, False)
    move_page(RULES_PAGE_WIDGETS, True)


def show_preview_page():
    global current_page
    current_page = 'preview'
    move_page(DASHBOARD_PAGE_WIDGETS, False)
    move_page(RULES_PAGE_WIDGETS, False)
    move_page(STORAGE_PAGE_WIDGETS, False)
    move_page(STORAGE_PREVIEW_PAGE_WIDGETS, False)
    move_page(PREVIEW_PAGE_WIDGETS, True)


def show_storage_page():
    global current_page
    current_page = 'storage'
    move_page(DASHBOARD_PAGE_WIDGETS, False)
    move_page(RULES_PAGE_WIDGETS, False)
    move_page(PREVIEW_PAGE_WIDGETS, False)
    move_page(STORAGE_PREVIEW_PAGE_WIDGETS, False)
    move_page(STORAGE_PAGE_WIDGETS, True)


def show_storage_preview_page():
    global current_page
    current_page = 'storage_preview'
    move_page(DASHBOARD_PAGE_WIDGETS, False)
    move_page(RULES_PAGE_WIDGETS, False)
    move_page(PREVIEW_PAGE_WIDGETS, False)
    move_page(STORAGE_PAGE_WIDGETS, False)
    move_page(STORAGE_PREVIEW_PAGE_WIDGETS, True)


def show_dashboard_page():
    global current_page
    current_page = 'dashboard'
    move_page(RULES_PAGE_WIDGETS, False)
    move_page(PREVIEW_PAGE_WIDGETS, False)
    move_page(STORAGE_PAGE_WIDGETS, False)
    move_page(STORAGE_PREVIEW_PAGE_WIDGETS, False)
    move_page(DASHBOARD_PAGE_WIDGETS, True)


show_dashboard_page()


def set_state(new_state, message=None, color=None):
    global state
    state = new_state
    if message is None:
        message = new_state
    if color is None:
        color = COLOR_WARNING
        if new_state in (STATE_IDLE, STATE_DONE, STATE_PREVIEW_READY):
            color = COLOR_SUCCESS
        elif new_state in (STATE_ERROR, STATE_CANCELLED):
            color = COLOR_ERROR
    QtBind.setText(gui, lbl_state, status_html(message, color))
    QtBind.setText(gui, lbl_dash_inventory_status,
                   fixed_width_text('<font color="%s"><b>%s</b></font>' %
                                    (color, message), 275))
    busy = new_state in (STATE_PREPARING, STATE_SORTING, STATE_WAITING_RESPONSE,
                         STATE_WAITING_SNAPSHOT, STATE_VERIFYING, STATE_REPLANNING)
    QtBind.setEnabled(gui, btn_sort, new_state == STATE_PREVIEW_READY)
    QtBind.setEnabled(gui, btn_preview, not busy)
    QtBind.setEnabled(gui, btn_cancel, busy)
    QtBind.setEnabled(gui, btn_up, not busy)
    QtBind.setEnabled(gui, btn_down, not busy)
    QtBind.setEnabled(gui, btn_toggle, not busy)
    QtBind.setEnabled(gui, btn_reset, not busy)
    QtBind.setEnabled(gui, btn_quick_inventory, not busy and storage_pending is None)


def refresh_category_list():
    QtBind.clear(gui, lst_categories)
    for index, name in enumerate(category_order):
        marker = '[x]' if enabled_categories.get(name, True) else '[ ]'
        QtBind.append(gui, lst_categories, '%02d. %s %s' % (index + 1, marker, name))


def selected_category_index():
    index = QtBind.currentIndex(gui, lst_categories)
    return index if 0 <= index < len(category_order) else -1


def invalidate_preview():
    global preview_snapshot, preview_plan
    preview_snapshot = None
    preview_plan = []
    if state == STATE_PREVIEW_READY:
        set_state(STATE_IDLE, 'Ready', COLOR_SUCCESS)
    QtBind.setText(gui, lbl_planned, fixed_width_text('-', 205))


def move_category_up():
    index = selected_category_index()
    if index <= 0:
        return
    category_order[index - 1], category_order[index] = category_order[index], category_order[index - 1]
    refresh_category_list()
    invalidate_preview()


def move_category_down():
    index = selected_category_index()
    if index < 0 or index >= len(category_order) - 1:
        return
    category_order[index + 1], category_order[index] = category_order[index], category_order[index + 1]
    refresh_category_list()
    invalidate_preview()


def toggle_category():
    index = selected_category_index()
    if index < 0:
        return
    name = category_order[index]
    enabled_categories[name] = not enabled_categories.get(name, True)
    refresh_category_list()
    invalidate_preview()


def reset_categories():
    global category_order, enabled_categories
    category_order = list(DEFAULT_CATEGORY_ORDER)
    enabled_categories = dict((name, True) for name in DEFAULT_CATEGORY_ORDER)
    refresh_category_list()
    invalidate_preview()


def save_categories_clicked():
    if save_settings():
        plugin_log('Sorting rules saved.')


def storage_log(message):
    log('[%s][Storage] %s' % (pName, message))


def set_storage_state(new_state, message, color):
    global storage_state
    storage_state = new_state
    QtBind.setText(gui, lbl_storage_detail_state, status_html(message, color))
    QtBind.setText(gui, lbl_dash_storage_status,
                   fixed_width_text('<font color="%s"><b>%s</b></font>' %
                                    (color, message), 275))
    busy = storage_pending is not None
    QtBind.setEnabled(gui, btn_storage_start,
                      not busy and storage_preview_snapshot is not None)
    QtBind.setEnabled(gui, btn_storage_cancel_sort, busy)
    QtBind.setEnabled(gui, btn_storage_preview, not busy)
    QtBind.setEnabled(gui, btn_storage_refresh, not busy)
    QtBind.setEnabled(gui, btn_quick_storage, not busy and pending_operation is None)
    QtBind.setEnabled(gui, btn_quick_inventory, not busy and pending_operation is None)


def update_storage_status(snapshot):
    if snapshot is None:
        QtBind.setText(gui, lbl_storage_count, fixed_width_text('Unavailable', 205))
        return
    occupied = sum(1 for item in snapshot.items if item is not None)
    QtBind.setText(gui, lbl_storage_count,
                   fixed_width_text('%d / %d' % (occupied, len(snapshot.items)), 205))


def refresh_storage_category_list():
    QtBind.clear(gui, lst_storage_categories)
    for index, name in enumerate(storage_category_order):
        marker = '[x]' if storage_enabled_categories.get(name, True) else '[ ]'
        QtBind.append(gui, lst_storage_categories, '%02d. %s %s' %
                      (index + 1, marker, name))


def selected_storage_category_index():
    index = QtBind.currentIndex(gui, lst_storage_categories)
    return index if 0 <= index < len(storage_category_order) else -1


def invalidate_storage_preview():
    global storage_preview_snapshot, storage_preview_plan
    storage_preview_snapshot = None
    storage_preview_plan = []


def storage_move_up():
    index = selected_storage_category_index()
    if index <= 0:
        return
    storage_category_order[index - 1], storage_category_order[index] = (
        storage_category_order[index], storage_category_order[index - 1])
    refresh_storage_category_list()
    invalidate_storage_preview()


def storage_move_down():
    index = selected_storage_category_index()
    if index < 0 or index >= len(storage_category_order) - 1:
        return
    storage_category_order[index + 1], storage_category_order[index] = (
        storage_category_order[index], storage_category_order[index + 1])
    refresh_storage_category_list()
    invalidate_storage_preview()


def storage_toggle_category():
    index = selected_storage_category_index()
    if index < 0:
        return
    name = storage_category_order[index]
    storage_enabled_categories[name] = not storage_enabled_categories.get(name, True)
    refresh_storage_category_list()
    invalidate_storage_preview()


def storage_reset_categories():
    global storage_category_order, storage_enabled_categories
    storage_category_order = list(DEFAULT_CATEGORY_ORDER)
    storage_enabled_categories = dict((name, True) for name in DEFAULT_CATEGORY_ORDER)
    refresh_storage_category_list()
    invalidate_storage_preview()


def storage_save_rules():
    if save_settings():
        storage_log('Storage sorting rules saved.')


def render_storage_items(snapshot):
    QtBind.clear(gui, lst_storage_items)
    if snapshot is None:
        QtBind.append(gui, lst_storage_items,
                      'Personal storage is unavailable. Open it manually, then refresh.')
        return
    occupied = 0
    for slot, item in enumerate(snapshot.items):
        if item is None:
            QtBind.append(gui, lst_storage_items, '%03d | EMPTY' % slot)
        else:
            occupied += 1
            QtBind.append(gui, lst_storage_items, '%03d | %-18s | x%-6d | %s' %
                          (slot, item.category[:18], item.quantity,
                           item.display_name()[:35]))
    storage_log('Snapshot captured: %d item(s), %d slot(s).' %
                (occupied, len(snapshot.items)))


def storage_refresh_clicked():
    global storage_snapshot
    snapshot = take_storage_snapshot()
    if snapshot is None:
        storage_snapshot = None
        render_storage_items(None)
        set_storage_state(STORAGE_UNKNOWN,
                          'Unavailable; open personal storage manually.', COLOR_ERROR)
        update_storage_status(None)
        storage_log('get_storage() is unavailable or has no loaded snapshot.')
        return
    storage_snapshot = snapshot
    invalidate_storage_preview()
    render_storage_items(snapshot)
    update_storage_status(snapshot)
    set_storage_state(STORAGE_SNAPSHOT_AVAILABLE,
                      'Snapshot available', COLOR_SUCCESS)


def storage_preview_clicked():
    global storage_preview_snapshot, storage_preview_plan, storage_snapshot
    global storage_planned_total
    if storage_pending is not None:
        return
    snapshot = take_storage_snapshot()
    if snapshot is None:
        storage_refresh_clicked()
        return
    try:
        _, operations = create_storage_plan(snapshot)
    except ValueError as error:
        set_storage_state(STORAGE_ERROR, 'Planning failed', COLOR_ERROR)
        storage_log('Planning error: %s' % error)
        return
    storage_snapshot = snapshot
    storage_preview_snapshot = snapshot
    storage_preview_plan = operations
    storage_planned_total = len(operations)
    update_storage_status(snapshot)
    QtBind.clear(gui, lst_storage_items)
    QtBind.append(gui, lst_storage_items, 'Preview only - zero packets sent.')
    QtBind.append(gui, lst_storage_items, 'Planned operations: %d' % len(operations))
    for index, operation in enumerate(operations[:35]):
        QtBind.append(gui, lst_storage_items, '%02d. %s %d -> %d (qty=%d)' %
                      (index + 1, operation.kind.upper(), operation.source,
                       operation.destination, operation.requested_quantity))
    if len(operations) > 35:
        QtBind.append(gui, lst_storage_items, '... %d more operation(s)' %
                      (len(operations) - 35))
    set_storage_state(STORAGE_SNAPSHOT_AVAILABLE,
                      'Preview ready: %d operation(s).' % len(operations), COLOR_SUCCESS)
    QtBind.setText(gui, lbl_storage_planned, fixed_width_text(str(len(operations)), 205))
    QtBind.setText(gui, lbl_storage_completed, fixed_width_text('0', 205))
    QtBind.setText(gui, lbl_storage_current, fixed_width_text('-', 205))
    QtBind.setText(gui, lbl_storage_requested, fixed_width_text('-', 205))
    QtBind.setText(gui, lbl_storage_applied, fixed_width_text('-', 205))
    QtBind.setText(gui, lbl_storage_response, fixed_width_text('-', 205))
    storage_log('Storage preview created: %d operation(s), zero packets sent.' %
                len(operations))
    show_storage_preview_page()


def finish_storage_run(final_state, message, color):
    global storage_pending, storage_cancel_requested, storage_snapshot
    global storage_quick_mode, storage_preview_snapshot, storage_preview_plan
    was_quick = storage_quick_mode
    storage_pending = None
    storage_cancel_requested = False
    storage_quick_mode = False
    storage_preview_snapshot = None
    storage_preview_plan = []
    storage_snapshot = take_storage_snapshot()
    update_storage_status(storage_snapshot)
    set_storage_state(final_state, message, color)
    storage_log(message)
    QtBind.setText(gui, lbl_dashboard_last,
                   fixed_width_text('<font color="%s">Last result: %s</font>' %
                                    (color, message), 680))
    if was_quick:
        show_dashboard_page()
    else:
        show_storage_page()


def fail_storage_run(message):
    finish_storage_run(STORAGE_ERROR, message, COLOR_ERROR)


def storage_sort_clicked():
    global storage_cancel_requested, storage_replan_count
    global storage_completed_operations, storage_planned_total
    if storage_pending is not None or storage_preview_snapshot is None:
        return
    if pending_operation is not None:
        set_storage_state(STORAGE_ERROR, 'Inventory sorting is active.', COLOR_ERROR)
        return
    current = take_storage_snapshot()
    if current is None:
        fail_storage_run('Open personal storage and try again.')
        return
    if current.fingerprint() != storage_preview_snapshot.fingerprint():
        set_storage_state(STORAGE_ERROR, 'Preview is stale; preview again.', COLOR_ERROR)
        storage_log('Storage changed after preview. Create a new preview.')
        return
    storage_cancel_requested = False
    storage_replan_count = 0
    storage_completed_operations = 0
    storage_planned_total = len(storage_preview_plan)
    storage_log('Sorting started from preview: %d operation(s).' % storage_planned_total)
    storage_replan_and_continue(current, False)


def quick_sort_storage_clicked():
    global storage_preview_snapshot, storage_preview_plan, storage_snapshot
    global storage_quick_mode, storage_planned_total
    if pending_operation is not None or storage_pending is not None:
        return
    snapshot = take_storage_snapshot()
    if snapshot is None:
        set_storage_state(STORAGE_ERROR, 'Open personal storage and try again.', COLOR_ERROR)
        return
    try:
        _, operations = create_storage_plan(snapshot)
    except ValueError as error:
        fail_storage_run('Storage planning failed: %s' % error)
        return
    storage_snapshot = snapshot
    storage_preview_snapshot = snapshot
    storage_preview_plan = operations
    storage_planned_total = len(operations)
    storage_quick_mode = True
    storage_log('Quick Sort prepared: %d operation(s).' % len(operations))
    if not operations:
        finish_storage_run(STORAGE_VERIFIED, 'Storage already sorted.', COLOR_SUCCESS)
        return
    storage_sort_clicked()


def storage_cancel_clicked():
    global storage_cancel_requested
    if storage_pending is None:
        return
    storage_cancel_requested = True
    storage_log('Cancel requested; no new storage operation will be sent.')


def storage_replan_and_continue(snapshot, count_replan):
    global storage_replan_count, storage_preview_plan, storage_planned_total
    if storage_cancel_requested:
        finish_storage_run(STATE_CANCELLED, 'Storage sorting cancelled.', COLOR_ERROR)
        return
    if count_replan:
        storage_replan_count += 1
        if storage_replan_count > MAX_REPLANS:
            fail_storage_run('Storage is unstable. Sorting cancelled.')
            return
    try:
        _, operations = create_storage_plan(snapshot)
    except ValueError as error:
        fail_storage_run('Storage replanning failed: %s' % error)
        return
    storage_preview_plan = operations
    if not operations:
        finish_storage_run(STORAGE_VERIFIED, 'Storage sorting completed.', COLOR_SUCCESS)
        return
    if count_replan:
        storage_planned_total = storage_completed_operations + len(operations)
        storage_log('New storage plan: %d remaining operation(s).' % len(operations))
    storage_send_next_operation(snapshot, operations[0])


def storage_send_next_operation(snapshot, operation):
    global storage_pending
    fresh = take_storage_snapshot()
    if fresh is None:
        fail_storage_run('Open personal storage and try again.')
        return
    if fresh.fingerprint() != snapshot.fingerprint():
        storage_log('Storage changed before injection; replanning without sending.')
        storage_replan_and_continue(fresh, True)
        return
    if operation.source >= len(fresh.items) or operation.destination >= len(fresh.items):
        fail_storage_run('Planned slot is outside personal storage.')
        return
    source_item = fresh.items[operation.source]
    if source_item is None:
        storage_replan_and_continue(fresh, True)
        return
    operation.requested_quantity = source_item.quantity
    payload = (struct.pack('<BBBH', 0x01, operation.source,
                           operation.destination, operation.requested_quantity) +
               STORAGE_SESSION_DATA)
    storage_pending = {
        'production': True, 'move': operation, 'baseline': fresh,
        'source': operation.source, 'destination': operation.destination,
        'quantity': operation.requested_quantity, 'kind': operation.kind,
        'payload': payload, 'sent_at': time.time(), 'response_at': None,
        'response': None
    }
    set_storage_state(STORAGE_PACKET_SEEN,
                      'Sorting %d/%d: %d -> %d' %
                      (storage_completed_operations + 1, storage_planned_total,
                      operation.source, operation.destination), COLOR_WARNING)
    QtBind.setText(gui, lbl_storage_current,
                   fixed_width_text('%d -> %d' %
                                    (operation.source, operation.destination), 205))
    QtBind.setText(gui, lbl_storage_requested,
                   fixed_width_text(str(operation.requested_quantity), 205))
    QtBind.setText(gui, lbl_storage_applied, fixed_width_text('-', 205))
    QtBind.setText(gui, lbl_storage_response, fixed_width_text('Pending', 205))
    QtBind.setText(gui, lbl_storage_completed,
                   fixed_width_text('%d / %d' %
                                    (storage_completed_operations, storage_planned_total), 205))
    storage_log('Executing %d/%d: %s %d -> %d qty=%d' %
                (storage_completed_operations + 1, storage_planned_total,
                 operation.kind, operation.source, operation.destination,
                 operation.requested_quantity))
    try:
        inject_joymax(OPCODE_INVENTORY_OPERATION, payload, INVENTORY_PACKET_ENCRYPTED)
    except Exception as error:
        fail_storage_run('Storage packet injection failed: %s' % error)


def poll_storage_injection():
    global storage_snapshot, storage_pending, storage_completed_operations
    if storage_pending is None:
        return
    now = time.time()
    pending = storage_pending
    if pending['response'] is None:
        if now - pending['sent_at'] >= RESPONSE_TIMEOUT_SECONDS:
            fail_storage_run('Storage response timed out. Open storage and try again.')
        return
    current = take_storage_snapshot()
    if current is None:
        fail_storage_run('Storage became unavailable after B034.')
        return
    if current.fingerprint() != pending['baseline'].fingerprint():
        changes = changed_slots(pending['baseline'], current)
        unexpected = [slot for slot in changes
                      if slot not in (pending['source'], pending['destination'])]
        old_source = pending['baseline'].items[pending['source']]
        old_destination = pending['baseline'].items[pending['destination']]
        new_source = current.items[pending['source']]
        new_destination = current.items[pending['destination']]
        applied = pending['response']['applied_quantity']
        if pending['kind'] == 'merge':
            expected_source_quantity = old_source.quantity - applied
            source_matches = (
                (expected_source_quantity == 0 and new_source is None) or
                (expected_source_quantity > 0 and new_source is not None and
                 new_source.model == old_source.model and
                 new_source.quantity == expected_source_quantity))
            destination_matches = (
                old_destination is not None and new_destination is not None and
                new_destination.model == old_destination.model and
                new_destination.quantity == old_destination.quantity + applied)
        else:
            source_matches = (
                (old_destination is None and new_source is None) or
                (old_destination is not None and new_source is not None and
                 old_destination.fingerprint() == new_source.fingerprint()))
            destination_matches = (
                new_destination is not None and
                old_source.fingerprint() == new_destination.fingerprint())
        storage_pending = None
        storage_snapshot = current
        if not changes or not source_matches or not destination_matches:
            fail_storage_run('Storage snapshot did not match the server response.')
            return
        storage_completed_operations += 1
        QtBind.setText(gui, lbl_storage_completed,
                       fixed_width_text('%d / %d' %
                                        (storage_completed_operations,
                                         storage_planned_total), 205))
        storage_log('Snapshot verified for slots %d and %d (applied=%d).' %
                    (pending['source'], pending['destination'], applied))
        storage_replan_and_continue(current, bool(unexpected))
        return
    if now - pending['response_at'] >= SNAPSHOT_TIMEOUT_SECONDS:
        fail_storage_run('Storage snapshot timed out after B034. Open storage and try again.')


def update_inventory_status(snapshot):
    if snapshot is None:
        QtBind.setText(gui, lbl_items, fixed_width_text('Unavailable', 205))
        return
    usable = max(0, len(snapshot.items) - snapshot.bag_start)
    QtBind.setText(gui, lbl_items,
                   fixed_width_text('%d / %d' % (snapshot.occupied_bag_count(), usable), 205))


def populate_preview(snapshot, desired, operations):
    QtBind.clear(gui, lst_preview)
    counts = dict((name, 0) for name in DEFAULT_CATEGORY_ORDER)
    for item in snapshot.items[snapshot.bag_start:]:
        if item is not None:
            counts[item.category] = counts.get(item.category, 0) + 1
    QtBind.append(gui, lst_preview, '--- Category summary ---')
    summary_parts = ['%s: %d' % (name, counts[name]) for name in category_order if counts.get(name, 0)]
    for offset in range(0, len(summary_parts), 4):
        QtBind.append(gui, lst_preview, ' | '.join(summary_parts[offset:offset + 4]))
    QtBind.append(gui, lst_preview, '--- Layout changes ---')
    changes = 0
    for slot in range(snapshot.bag_start, len(snapshot.items)):
        current = snapshot.items[slot]
        target = desired[slot]
        if not equivalent(current, target):
            changes += 1
            QtBind.append(gui, lst_preview, 'Slot %d: %s  ->  %s' %
                          (slot, safe_item_text(current), safe_item_text(target)))
    if changes == 0:
        QtBind.append(gui, lst_preview, 'Inventory already matches the selected category order.')
    else:
        QtBind.append(gui, lst_preview, '--- Planned operations: %d ---' % len(operations))
        for index, operation in enumerate(operations[:25]):
            QtBind.append(gui, lst_preview, '%02d. Slot %d -> %d (qty=%d)' %
                          (index + 1, operation.source, operation.destination,
                           operation.requested_quantity))
        if len(operations) > 25:
            QtBind.append(gui, lst_preview, '... %d more operation(s)' % (len(operations) - 25))

    unknown = [item for item in snapshot.items[snapshot.bag_start:]
               if item is not None and item.category == 'Misc']
    if unknown:
        QtBind.append(gui, lst_preview, '--- Misc / unclassified: %d ---' % len(unknown))
        for item in unknown[:15]:
            QtBind.append(gui, lst_preview, 'Slot %d: %s | %s | model=%d' %
                          (item.slot, item.name, item.servername, item.model))


def refresh_clicked():
    global last_snapshot, last_observed_fingerprint, last_inventory_change_time
    snapshot = take_snapshot()
    if snapshot is None:
        set_state(STATE_ERROR, 'Inventory unavailable', COLOR_ERROR)
        update_inventory_status(None)
        return
    last_snapshot = snapshot
    last_observed_fingerprint = snapshot.fingerprint()
    last_inventory_change_time = time.time()
    update_inventory_status(snapshot)
    invalidate_preview()
    plugin_log('Snapshot captured: %d item(s).' % snapshot.occupied_bag_count())


def preview_clicked():
    global preview_snapshot, preview_plan, planned_total
    if pending_operation is not None:
        return
    snapshot = take_snapshot()
    if snapshot is None:
        set_state(STATE_ERROR, 'Inventory unavailable', COLOR_ERROR)
        return
    try:
        desired, operations = create_plan(snapshot)
    except ValueError as error:
        set_state(STATE_ERROR, 'Planning failed', COLOR_ERROR)
        plugin_log('Planning error: %s' % error)
        return
    preview_snapshot = snapshot
    preview_plan = operations
    planned_total = len(operations)
    update_inventory_status(snapshot)
    populate_preview(snapshot, desired, operations)
    QtBind.setText(gui, lbl_planned, fixed_width_text(str(len(operations)), 205))
    QtBind.setText(gui, lbl_completed, fixed_width_text('0', 205))
    QtBind.setText(gui, lbl_current, fixed_width_text('-', 205))
    QtBind.setText(gui, lbl_requested, fixed_width_text('-', 205))
    QtBind.setText(gui, lbl_applied, fixed_width_text('-', 205))
    QtBind.setText(gui, lbl_response, fixed_width_text('-', 205))
    set_state(STATE_PREVIEW_READY, 'Preview ready', COLOR_SUCCESS)
    plugin_log('Sort preview created: %d operation(s).' % len(operations))
    show_preview_page()


def finish_run(final_state, message, color):
    global pending_operation, cancel_requested, last_snapshot, inventory_quick_mode
    was_quick = inventory_quick_mode
    pending_operation = None
    cancel_requested = False
    last_snapshot = take_snapshot()
    update_inventory_status(last_snapshot)
    set_state(final_state, message, color)
    plugin_log(message)
    QtBind.setText(gui, lbl_dashboard_last,
                   fixed_width_text('<font color="%s">Last result: %s</font>' %
                                    (color, message), 680))
    inventory_quick_mode = False
    show_dashboard_page() if was_quick else show_rules_page()


def fail_run(message):
    finish_run(STATE_ERROR, message, COLOR_ERROR)


def sort_clicked():
    global cancel_requested, replan_count, completed_operations, planned_total
    if state != STATE_PREVIEW_READY or preview_snapshot is None:
        return
    if storage_pending is not None:
        plugin_log('Inventory sorting blocked while a storage operation is active.')
        return
    current = take_snapshot()
    if current is None:
        fail_run('Inventory unavailable. Sorting stopped.')
        return
    if current.fingerprint() != preview_snapshot.fingerprint():
        set_state(STATE_IDLE, 'Preview is stale', COLOR_ERROR)
        plugin_log('Inventory changed after preview. Create a new preview.')
        return
    if time.time() - last_inventory_change_time < QUIET_PERIOD_SECONDS:
        set_state(STATE_PREVIEW_READY, 'Wait for inventory', COLOR_WARNING)
        plugin_log('Inventory quiet period has not elapsed; sort not started.')
        return
    cancel_requested = False
    replan_count = 0
    completed_operations = 0
    planned_total = len(preview_plan)
    set_state(STATE_PREPARING, 'Preparing', COLOR_WARNING)
    plugin_log('Sorting started from preview: %d operation(s).' % planned_total)
    replan_and_continue(current, False)


def quick_sort_inventory_clicked():
    global preview_snapshot, preview_plan, planned_total
    global last_snapshot, last_observed_fingerprint, last_inventory_change_time
    global inventory_quick_mode
    if pending_operation is not None or storage_pending is not None:
        return
    snapshot = take_snapshot()
    if snapshot is None:
        set_state(STATE_ERROR, 'Inventory unavailable', COLOR_ERROR)
        return
    try:
        _, operations = create_plan(snapshot)
    except ValueError as error:
        fail_run('Inventory planning failed: %s' % error)
        return
    last_snapshot = snapshot
    last_observed_fingerprint = snapshot.fingerprint()
    last_inventory_change_time = time.time() - QUIET_PERIOD_SECONDS - 0.1
    preview_snapshot = snapshot
    preview_plan = operations
    planned_total = len(operations)
    inventory_quick_mode = True
    update_inventory_status(snapshot)
    plugin_log('Quick Sort prepared: %d operation(s).' % len(operations))
    if not operations:
        finish_run(STATE_DONE, 'Inventory already sorted.', COLOR_SUCCESS)
        return
    set_state(STATE_PREVIEW_READY, 'Quick Sort ready', COLOR_SUCCESS)
    sort_clicked()


def cancel_clicked():
    global cancel_requested
    if state not in (STATE_PREPARING, STATE_SORTING, STATE_WAITING_RESPONSE,
                     STATE_WAITING_SNAPSHOT, STATE_VERIFYING, STATE_REPLANNING):
        return
    cancel_requested = True
    plugin_log('Cancel requested; no new operation will be sent.')
    if pending_operation is None:
        finish_run(STATE_CANCELLED, 'Sorting cancelled.', COLOR_ERROR)


def replan_and_continue(snapshot, count_replan):
    global replan_count, preview_plan, planned_total
    if cancel_requested:
        finish_run(STATE_CANCELLED, 'Sorting cancelled.', COLOR_ERROR)
        return
    if count_replan:
        replan_count += 1
        if replan_count > MAX_REPLANS:
            fail_run('Inventory is unstable. Sorting cancelled.')
            return
        set_state(STATE_REPLANNING, 'Replanning %d/%d' % (replan_count, MAX_REPLANS), COLOR_WARNING)
    try:
        desired, operations = create_plan(snapshot)
    except ValueError as error:
        fail_run('Replanning failed: %s' % error)
        return
    preview_plan = operations
    if not operations:
        finish_run(STATE_DONE, 'Inventory sorting completed.', COLOR_SUCCESS)
        return
    if count_replan:
        planned_total = completed_operations + len(operations)
        plugin_log('New plan created: %d remaining operation(s).' % len(operations))
    set_state(STATE_SORTING, 'Sorting', COLOR_WARNING)
    send_next_operation(snapshot, operations[0])


def send_next_operation(snapshot, operation):
    global pending_operation
    if pending_operation is not None:
        fail_run('Internal safety lock prevented multiple pending operations.')
        return
    if cancel_requested:
        finish_run(STATE_CANCELLED, 'Sorting cancelled.', COLOR_ERROR)
        return
    fresh = take_snapshot()
    if fresh is None:
        fail_run('Inventory became unavailable before the next operation.')
        return
    if fresh.fingerprint() != snapshot.fingerprint():
        plugin_log('Inventory changed before packet injection; replanning without sending.')
        replan_and_continue(fresh, True)
        return
    snapshot = fresh
    if operation.source >= len(snapshot.items) or operation.destination >= len(snapshot.items):
        fail_run('Planned slot is outside the inventory.')
        return
    source_item = snapshot.items[operation.source]
    if source_item is None:
        replan_and_continue(snapshot, True)
        return
    operation.requested_quantity = source_item.quantity
    payload = build_move_payload(operation)
    pending_operation = {
        'move': operation, 'baseline': snapshot, 'payload': payload,
        'sent_at': time.time(), 'response_at': None, 'response': None
    }
    set_state(STATE_WAITING_RESPONSE, 'Waiting response', COLOR_WARNING)
    QtBind.setText(gui, lbl_current,
                   fixed_width_text('%d -> %d' % (operation.source, operation.destination), 205))
    QtBind.setText(gui, lbl_requested,
                   fixed_width_text(str(operation.requested_quantity), 205))
    QtBind.setText(gui, lbl_applied, fixed_width_text('-', 205))
    QtBind.setText(gui, lbl_response, fixed_width_text('Pending', 205))
    QtBind.setText(gui, lbl_completed,
                   fixed_width_text('%d / %d' % (completed_operations, planned_total), 205))
    plugin_log('Executing %d/%d: %d -> %d qty=%d' %
               (completed_operations + 1, planned_total, operation.source,
                operation.destination, operation.requested_quantity))
    try:
        inject_joymax(OPCODE_INVENTORY_OPERATION, payload, INVENTORY_PACKET_ENCRYPTED)
    except Exception as error:
        fail_run('Packet injection failed: %s' % error)


def handle_joymax(opcode, data):
    global pending_operation, storage_pending
    if opcode == OPCODE_INVENTORY_RESPONSE and storage_pending is not None:
        decoded_storage = decode_observed_storage_response(data)
        pending_storage = storage_pending
        if decoded_storage is None:
            message = 'Unsupported storage B034 response: %s' % packet_hex(data)
            fail_storage_run(message)
            return True
        if decoded_storage.get('success_byte') != 0x01:
            message = 'Storage move rejected: %s. Open storage and try again.' % packet_hex(data)
            fail_storage_run(message)
            return True
        if (decoded_storage.get('operation') != 0x01 or
                decoded_storage.get('source') != pending_storage['source'] or
                decoded_storage.get('destination') != pending_storage['destination'] or
                'applied_quantity' not in decoded_storage):
            fail_storage_run('B034 did not match the pending storage operation.')
            return True
        pending_storage['response_at'] = time.time()
        pending_storage['response'] = decoded_storage
        QtBind.setText(gui, lbl_storage_applied,
                       fixed_width_text(str(decoded_storage['applied_quantity']), 205))
        QtBind.setText(gui, lbl_storage_response, fixed_width_text('Success', 205))
        message = 'B034 success: requested=%d applied=%d.' % (
            pending_storage['quantity'], decoded_storage['applied_quantity'])
        storage_log(message)
        set_storage_state(STORAGE_RESPONSE_SEEN,
                          'B034 success; verifying snapshot.', COLOR_WARNING)
        if (pending_storage['kind'] == 'merge' and
                decoded_storage['applied_quantity'] < pending_storage['quantity']):
            capacity_message = 'Capacity-limited merge: requested=%d applied=%d.' % (
                pending_storage['quantity'], decoded_storage['applied_quantity'])
            storage_log(capacity_message)
        elif decoded_storage['applied_quantity'] != pending_storage['quantity']:
            warning = 'WARNING: server applied %d although %d was requested.' % (
                decoded_storage['applied_quantity'], pending_storage['quantity'])
            storage_log(warning)
        return True
    if opcode != OPCODE_INVENTORY_RESPONSE or pending_operation is None:
        return True
    decoded = decode_b034(data)
    if not decoded['supported']:
        fail_run('Unsupported B034 response: %s' % ' '.join('%02X' % b for b in bytearray(data)))
        return True
    if not decoded['success']:
        QtBind.setText(gui, lbl_response, fixed_width_text('Rejected', 205))
        fail_run('B034 rejected inventory operation.')
        return True
    move = pending_operation['move']
    if (decoded['operation'] != OP_INVENTORY_MOVE or decoded['source'] != move.source or
            decoded['destination'] != move.destination):
        fail_run('B034 did not match the pending operation.')
        return True
    pending_operation['response_at'] = time.time()
    pending_operation['response'] = decoded
    QtBind.setText(gui, lbl_applied, fixed_width_text(str(decoded['applied_quantity']), 205))
    QtBind.setText(gui, lbl_response, fixed_width_text('Success', 205))
    set_state(STATE_WAITING_SNAPSHOT, 'Waiting snapshot', COLOR_WARNING)
    plugin_log('B034 success: requested=%d applied=%d.' %
               (move.requested_quantity, decoded['applied_quantity']))
    return True


def verify_pending_snapshot(current):
    global pending_operation, completed_operations, last_snapshot
    pending = pending_operation
    if pending is None:
        return
    changes = changed_slots(pending['baseline'], current)
    move = pending['move']
    relevant = set((move.source, move.destination))
    unexpected = [slot for slot in changes if slot not in relevant]
    set_state(STATE_VERIFYING, 'Verifying', COLOR_WARNING)
    pending_operation = None
    last_snapshot = current
    update_inventory_status(current)
    if not changes:
        fail_run('B034 succeeded but inventory snapshot did not change.')
        return
    if unexpected:
        plugin_log('Unexpected inventory changes in slot(s): %s.' %
                   ', '.join(str(slot) for slot in unexpected))
        replan_and_continue(current, True)
        return
    completed_operations += 1
    QtBind.setText(gui, lbl_completed,
                   fixed_width_text('%d / %d' % (completed_operations, planned_total), 205))
    plugin_log('Snapshot verified for slots %d and %d.' % (move.source, move.destination))
    if pending['response']['applied_quantity'] != move.requested_quantity:
        plugin_log('Partial server application detected; replanning from actual snapshot.')
        replan_and_continue(current, True)
    else:
        replan_and_continue(current, False)


def event_loop():
    global last_observed_fingerprint, last_inventory_change_time, last_snapshot
    poll_storage_injection()
    current = take_snapshot()
    if current is None:
        return
    current_fp = current.fingerprint()
    now = time.time()
    if last_observed_fingerprint is None:
        last_observed_fingerprint = current_fp
        last_inventory_change_time = now
        last_snapshot = current
        update_inventory_status(current)
    elif current_fp != last_observed_fingerprint:
        last_observed_fingerprint = current_fp
        last_inventory_change_time = now

    if pending_operation is None:
        last_snapshot = current
        return
    pending = pending_operation
    if pending['response'] is None:
        if now - pending['sent_at'] >= RESPONSE_TIMEOUT_SECONDS:
            if cancel_requested:
                finish_run(STATE_CANCELLED, 'Sorting cancelled after pending response timeout.', COLOR_ERROR)
            else:
                fail_run('Inventory operation response timed out.')
        return
    if current_fp != pending['baseline'].fingerprint():
        verify_pending_snapshot(current)
        return
    if now - pending['response_at'] >= SNAPSHOT_TIMEOUT_SECONDS:
        if cancel_requested:
            finish_run(STATE_CANCELLED, 'Sorting cancelled after pending snapshot timeout.', COLOR_ERROR)
        else:
            fail_run('Inventory snapshot update timed out after B034 success.')


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        set_state(state, 'Opening Discord...', COLOR_WARNING)
    except Exception as error:
        plugin_log('Discord link error: %s' % error)
        set_state(state, 'Discord error', COLOR_ERROR)


def connected():
    global connected_to_game
    connected_to_game = True


def disconnected():
    global connected_to_game, pending_operation, preview_snapshot, preview_plan
    global storage_snapshot, storage_pending, storage_preview_snapshot, storage_preview_plan
    global inventory_quick_mode, storage_quick_mode
    connected_to_game = False
    pending_operation = None
    preview_snapshot = None
    preview_plan = []
    storage_snapshot = None
    storage_pending = None
    storage_preview_snapshot = None
    storage_preview_plan = []
    inventory_quick_mode = False
    storage_quick_mode = False
    set_storage_state(STORAGE_UNKNOWN, 'Disconnected', COLOR_MUTED)
    set_state(STATE_IDLE, 'Disconnected', COLOR_MUTED)


load_settings()
refresh_category_list()
refresh_storage_category_list()
set_state(STATE_IDLE, 'Ready', COLOR_SUCCESS)
set_storage_state(STORAGE_UNKNOWN, 'Open personal storage, then refresh.', COLOR_MUTED)

log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
