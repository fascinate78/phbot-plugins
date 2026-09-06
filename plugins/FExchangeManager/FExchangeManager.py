from phBot import *
import phBotChat
import QtBind

import json
import os
import re
import struct
import time
import webbrowser


pName = 'FExchangeManager'
pVersion = '1.7.1'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

SERVER_GAME_PETITION_REQUEST = 0x3080
CLIENT_GAME_PETITION_RESPONSE = 0x3080
SERVER_EXCHANGE_STARTED = 0x3085
SERVER_EXCHANGE_REMOTE_CONFIRMED = 0x3086
SERVER_EXCHANGE_COMPLETED = 0x3087
SERVER_EXCHANGE_CANCELED = 0x3088
SERVER_INVENTORY_OPERATION_RESPONSE = 0xB034
SERVER_EXCHANGE_CONFIRM_RESPONSE = 0xB082
SERVER_EXCHANGE_APPROVE_RESPONSE = 0xB083
SERVER_EXCHANGE_EXIT_RESPONSE = 0xB084
CLIENT_INVENTORY_OPERATION = 0x7034
CLIENT_EXCHANGE_CONFIRM_REQUEST = 0x7082
CLIENT_EXCHANGE_APPROVE_REQUEST = 0x7083
CLIENT_EXCHANGE_CANCEL_REQUEST = 0x7084
EXCHANGE_PETITION_TYPE = 1
CHAT_PRIVATE = 2
EXCHANGE_ADD_ITEM = 4
MAX_EXCHANGE_ITEM_SLOTS = 12
COMMAND_TIMEOUT_SECONDS = 60.0
ACTION_DELAY_SECONDS = 0.65
ACTION_TIMEOUT_SECONDS = 5.0

COLOR_PRIMARY = '#5b57e0'
COLOR_TEXT = '#2b3038'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#d93a4d'
OFFSCREEN_X = 3000

allowed_players = []
item_filters = []
list_mode = 'players'
copy_target_paths = []
pending_requester_uid = 0
pending_requester_name = ''
active_requester_uid = 0
active_requester_name = ''
command_sender = ''
command_item_name = ''
command_expires_at = 0.0
transfer_slots = []
awaiting_inventory_slot = -1
next_action_at = 0.0
action_deadline = 0.0
automatic_transfer = False
local_confirm_sent = False
local_confirmed = False
remote_confirmed = False
approve_sent = False
added_stack_count = 0
skipped_stack_count = 0


def fixed_width_text(content, width):
    return (
        '<table width="{0}" cellspacing="0" cellpadding="0">'
        '<tr><td>{1}</td></tr></table>'
    ).format(width, content)


gui = QtBind.init(__name__, pName)
QtBind.createLabel(
    gui,
    u'<font color="%s" size="4"><b>⇄ %s</b></font>' %
    (COLOR_PRIMARY, pName),
    12,
    6
)
QtBind.createLabel(
    gui, '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion), 205, 12)
btn_discord = QtBind.createButton(
    gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(
    gui, u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' %
    COLOR_PRIMARY, 565, 11)
QtBind.createLineEdit(gui, '', 12, 30, 696, 1)

list_header_label = QtBind.createLabel(
    gui, fixed_width_text(
        '<font color="%s"><b>ALLOWED PLAYERS</b></font>' % COLOR_PRIMARY,
        385),
    12, 43)
list_help_label = QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s">Listed nearby players are always trusted.</font>' %
        COLOR_MUTED, 385),
    12,
    63
)
player_input = QtBind.createLineEdit(gui, '', 12, 87, 210, 22)
btn_add = QtBind.createButton(gui, 'add_player_clicked', 'Add Player', 232, 85)
btn_remove = QtBind.createButton(
    gui, 'remove_player_clicked', 'Remove Selected', 310, 85)
item_manual_input = QtBind.createLineEdit(gui, '', OFFSCREEN_X, 87, 245, 22)
inventory_combo = QtBind.createCombobox(gui, OFFSCREEN_X, 116, 220, 22)
btn_refresh_inventory = QtBind.createButton(
    gui, 'refresh_inventory_clicked', 'Refresh', OFFSCREEN_X, 114)
btn_add_inventory = QtBind.createButton(
    gui, 'add_inventory_item_clicked', 'Add', OFFSCREEN_X, 114)
player_list = QtBind.createList(gui, 12, 116, 385, 115)
item_filter_list = QtBind.createList(gui, OFFSCREEN_X, 145, 385, 86)
btn_save = QtBind.createButton(gui, 'save_clicked', 'Save Settings', 12, 242)
btn_reload = QtBind.createButton(gui, 'reload_clicked', 'Reload', 120, 242)
btn_list_mode = QtBind.createButton(gui, 'list_mode_clicked', 'Item Filters', 180, 242)
btn_copy_mode = QtBind.createButton(
    gui, 'copy_mode_clicked', 'Copy Filters', OFFSCREEN_X, 242)
copy_target_combo = QtBind.createCombobox(gui, OFFSCREEN_X, 87, 285, 22)
btn_copy_confirm = QtBind.createButton(
    gui, 'copy_filters_clicked', 'Copy', OFFSCREEN_X, 85)
accept_guild_checkbox = QtBind.createCheckBox(
    gui, 'accept_guild_changed', 'Accept all nearby guild members', 12, 274)
reject_unauthorized_checkbox = QtBind.createCheckBox(
    gui, 'reject_unauthorized_changed', 'Reject unauthorized requests', 230, 274)

QtBind.createLineEdit(gui, '', 414, 43, 1, 242)
QtBind.createLabel(
    gui, '<font color="%s"><b>LIVE STATUS</b></font>' % COLOR_PRIMARY,
    432, 43)
QtBind.createLabel(gui, '<font color="%s"><b>State</b></font>' % COLOR_MUTED,
                   432, 72)
state_label = QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s"><b>READY</b></font>' % COLOR_SUCCESS, 258),
    432,
    91
)
QtBind.createLabel(
    gui, '<font color="%s"><b>Last requester</b></font>' % COLOR_MUTED,
    432, 126)
requester_label = QtBind.createLabel(
    gui,
    fixed_width_text('<font color="%s">-</font>' % COLOR_TEXT, 258),
    432,
    145
)
QtBind.createLabel(
    gui, '<font color="%s"><b>Authorization</b></font>' % COLOR_MUTED,
    432, 180)
authorization_label = QtBind.createLabel(
    gui,
    fixed_width_text('<font color="%s">Waiting for a request</font>' %
                     COLOR_MUTED, 258),
    432,
    199
)
status_label = QtBind.createLabel(
    gui,
    fixed_width_text('<font color="%s">Ready</font>' % COLOR_MUTED, 258),
    432,
    250
)


def set_status(message, color=COLOR_MUTED):
    QtBind.setText(
        gui, status_label,
        fixed_width_text('<font color="%s">%s</font>' % (color, message), 258))


def set_state(message, color):
    QtBind.setText(
        gui, state_label,
        fixed_width_text('<font color="%s"><b>%s</b></font>' %
                         (color, message), 258))


def set_requester(name, authorization, color):
    QtBind.setText(
        gui, requester_label,
        fixed_width_text('<font color="%s">%s</font>' % (COLOR_TEXT, name), 258))
    QtBind.setText(
        gui, authorization_label,
        fixed_width_text('<font color="%s">%s</font>' %
                         (color, authorization), 258))


def normalize_name(value):
    return str(value).strip()


def refresh_player_list():
    QtBind.clear(gui, player_list)
    QtBind.clear(gui, item_filter_list)
    for value in allowed_players:
        QtBind.append(gui, player_list, value)
    for value in item_filters:
        QtBind.append(gui, item_filter_list, value)


def refresh_list_mode():
    if list_mode == 'players':
        QtBind.setText(
            gui, list_header_label,
            fixed_width_text(
                '<font color="%s"><b>ALLOWED PLAYERS</b></font>' %
                COLOR_PRIMARY, 385))
        QtBind.setText(
            gui, list_help_label,
            fixed_width_text(
                '<font color="%s">Listed nearby players are always trusted.</font>' %
                COLOR_MUTED, 385))
        QtBind.setText(gui, btn_add, 'Add Player')
        QtBind.setText(gui, btn_remove, 'Remove Selected')
        QtBind.setText(gui, btn_list_mode, 'Item Filters')
        QtBind.move(gui, player_input, 12, 87)
        QtBind.move(gui, item_manual_input, OFFSCREEN_X, 87)
        QtBind.move(gui, inventory_combo, OFFSCREEN_X, 87)
        QtBind.move(gui, btn_refresh_inventory, OFFSCREEN_X, 85)
        QtBind.move(gui, btn_add_inventory, OFFSCREEN_X, 114)
        QtBind.move(gui, btn_add, 232, 85)
        QtBind.move(gui, btn_remove, 310, 85)
        QtBind.move(gui, btn_reload, 120, 242)
        QtBind.move(gui, btn_list_mode, 180, 242)
        QtBind.move(gui, player_list, 12, 116)
        QtBind.move(gui, item_filter_list, OFFSCREEN_X, 145)
        QtBind.move(gui, btn_copy_mode, OFFSCREEN_X, 242)
        QtBind.move(gui, copy_target_combo, OFFSCREEN_X, 87)
        QtBind.move(gui, btn_copy_confirm, OFFSCREEN_X, 85)
    elif list_mode == 'items':
        QtBind.setText(
            gui, list_header_label,
            fixed_width_text(
                '<font color="%s"><b>AUTO ITEM FILTERS</b></font>' %
                COLOR_PRIMARY, 385))
        QtBind.setText(
            gui, list_help_label,
            fixed_width_text(
                '<font color="%s">Type an item or select it from inventory.</font>' %
                COLOR_MUTED, 385))
        QtBind.setText(gui, btn_add, 'Add Typed')
        QtBind.setText(gui, btn_remove, 'Remove')
        QtBind.setText(gui, btn_list_mode, 'Players')
        QtBind.move(gui, player_input, OFFSCREEN_X, 87)
        QtBind.move(gui, item_manual_input, 12, 87)
        QtBind.move(gui, inventory_combo, 12, 116)
        QtBind.move(gui, btn_refresh_inventory, 240, 114)
        QtBind.move(gui, btn_add_inventory, 310, 114)
        QtBind.move(gui, btn_add, 265, 85)
        QtBind.move(gui, btn_reload, OFFSCREEN_X, 242)
        QtBind.move(gui, btn_list_mode, 110, 242)
        QtBind.move(gui, btn_remove, 190, 242)
        QtBind.move(gui, player_list, OFFSCREEN_X, 116)
        QtBind.move(gui, item_filter_list, 12, 145)
        QtBind.move(gui, btn_copy_mode, 270, 242)
        QtBind.move(gui, copy_target_combo, OFFSCREEN_X, 87)
        QtBind.move(gui, btn_copy_confirm, OFFSCREEN_X, 85)
        refresh_inventory_items()
    else:
        QtBind.setText(
            gui, list_header_label,
            fixed_width_text(
                '<font color="%s"><b>COPY ITEM FILTERS</b></font>' %
                COLOR_PRIMARY, 385))
        QtBind.setText(
            gui, list_help_label,
            fixed_width_text(
                '<font color="%s">Select another character config as the target.</font>' %
                COLOR_MUTED, 385))
        QtBind.setText(gui, btn_list_mode, 'Back to Items')
        QtBind.move(gui, player_input, OFFSCREEN_X, 87)
        QtBind.move(gui, item_manual_input, OFFSCREEN_X, 87)
        QtBind.move(gui, inventory_combo, OFFSCREEN_X, 87)
        QtBind.move(gui, btn_refresh_inventory, OFFSCREEN_X, 85)
        QtBind.move(gui, btn_add_inventory, OFFSCREEN_X, 114)
        QtBind.move(gui, btn_add, OFFSCREEN_X, 85)
        QtBind.move(gui, btn_remove, OFFSCREEN_X, 85)
        QtBind.move(gui, btn_reload, OFFSCREEN_X, 242)
        QtBind.move(gui, player_list, OFFSCREEN_X, 116)
        QtBind.move(gui, item_filter_list, OFFSCREEN_X, 145)
        QtBind.move(gui, copy_target_combo, 12, 87)
        QtBind.move(gui, btn_copy_confirm, 307, 85)
        QtBind.move(gui, btn_copy_mode, OFFSCREEN_X, 242)
        refresh_copy_targets()
        return
    QtBind.clear(gui, player_input)
    refresh_player_list()


def get_config_path():
    character = get_character_data()
    if not character or not character.get('name'):
        return None
    folder = os.path.join(get_config_dir(), pName)
    identity = '%s_%s' % (
        character.get('server', 'UnknownServer'), character.get('name'))
    filename = re.sub(r'[<>:"/\\|?*]', '_', str(identity)) + '.json'
    return os.path.join(folder, filename)


def save_settings():
    path = get_config_path()
    if not path:
        set_status('Join the game before saving', COLOR_WARNING)
        return False
    try:
        folder = os.path.dirname(path)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        with open(path, 'w') as config_file:
            json.dump({
                'allowed_players': allowed_players,
                'item_filters': item_filters,
                'accept_guild_members': QtBind.isChecked(
                    gui, accept_guild_checkbox),
                'reject_unauthorized': QtBind.isChecked(
                    gui, reject_unauthorized_checkbox)
            }, config_file, indent=4, sort_keys=True)
        set_status('Settings saved', COLOR_SUCCESS)
        log('[%s] Settings saved.' % pName)
        return True
    except (OSError, IOError, ValueError, TypeError) as error:
        set_status('Settings could not be saved', COLOR_ERROR)
        log('[%s] Settings save error: %s' % (pName, error))
        return False


def load_settings():
    del allowed_players[:]
    del item_filters[:]
    QtBind.setChecked(gui, accept_guild_checkbox, False)
    QtBind.setChecked(gui, reject_unauthorized_checkbox, False)
    path = get_config_path()
    if path and os.path.isfile(path):
        try:
            with open(path, 'r') as config_file:
                data = json.load(config_file)
            values = data.get('allowed_players', [])
            if not isinstance(values, list):
                raise ValueError('allowed_players must be a list')
            seen = set()
            for value in values:
                name = normalize_name(value)
                key = name.lower()
                if name and key not in seen:
                    allowed_players.append(name)
                    seen.add(key)
            saved_filters = data.get('item_filters', [])
            if not isinstance(saved_filters, list):
                raise ValueError('item_filters must be a list')
            seen_filters = set()
            for value in saved_filters:
                item_name = normalize_name(value)
                key = item_name.lower()
                if item_name and key not in seen_filters:
                    item_filters.append(item_name)
                    seen_filters.add(key)
            QtBind.setChecked(
                gui, accept_guild_checkbox,
                bool(data.get('accept_guild_members', False)))
            QtBind.setChecked(
                gui, reject_unauthorized_checkbox,
                bool(data.get('reject_unauthorized', False)))
            set_status('Settings loaded', COLOR_SUCCESS)
        except (OSError, IOError, ValueError, TypeError) as error:
            set_status('Settings could not be loaded', COLOR_ERROR)
            log('[%s] Settings load error: %s' % (pName, error))
    else:
        set_status('New character settings', COLOR_MUTED)
    refresh_list_mode()


def party_name_from_uid(player_uid):
    party = get_party() or {}
    for member in party.values():
        try:
            if int(member.get('player_id', 0)) == player_uid:
                return normalize_name(member.get('name', ''))
        except (TypeError, ValueError):
            continue
    return ''


def nearby_player_name_from_uid(player_uid):
    players = get_players() or {}
    player = players.get(str(player_uid))
    if player is None:
        player = players.get(player_uid)
    if isinstance(player, dict):
        return normalize_name(player.get('name', ''))
    return ''


def guild_contains_name(name):
    key = name.lower()
    guild = get_guild() or {}
    for member in guild.values():
        if normalize_name(member.get('name', '')).lower() == key:
            return True
    return False


def is_command_authorized(name):
    if is_allowed(name):
        return True
    return (QtBind.isChecked(gui, accept_guild_checkbox) and
            guild_contains_name(name))


def resolve_requester(player_uid):
    party_name = party_name_from_uid(player_uid)
    if party_name:
        return party_name

    nearby_name = nearby_player_name_from_uid(player_uid)
    return nearby_name


def is_allowed(name):
    key = name.lower()
    return any(value.lower() == key for value in allowed_players)


def add_player_clicked():
    if list_mode == 'players':
        value = normalize_name(QtBind.text(gui, player_input))
    else:
        value = normalize_name(QtBind.text(gui, item_manual_input))
    if not value:
        set_status('Enter a player or item name', COLOR_WARNING)
        return
    values = allowed_players if list_mode == 'players' else item_filters
    if any(existing.lower() == value.lower() for existing in values):
        set_status('Entry is already listed', COLOR_WARNING)
        return
    values.append(value)
    if list_mode == 'players':
        QtBind.clear(gui, player_input)
    else:
        QtBind.clear(gui, item_manual_input)
    refresh_player_list()
    set_status('Added %s' % value, COLOR_SUCCESS)


def remove_player_clicked():
    list_widget = player_list if list_mode == 'players' else item_filter_list
    index = QtBind.currentIndex(gui, list_widget)
    values = allowed_players if list_mode == 'players' else item_filters
    if index < 0 or index >= len(values):
        set_status('Select an entry to remove', COLOR_WARNING)
        return
    name = values.pop(index)
    refresh_player_list()
    set_status('Removed %s' % name, COLOR_SUCCESS)


def save_clicked():
    save_settings()


def list_mode_clicked():
    global list_mode
    if list_mode == 'players':
        list_mode = 'items'
    elif list_mode == 'items':
        list_mode = 'players'
    else:
        list_mode = 'items'
    refresh_list_mode()
    set_status('Editing %s' %
               ('item filters' if list_mode == 'items' else 'allowed players'),
               COLOR_MUTED)


def copy_mode_clicked():
    global list_mode
    list_mode = 'copy'
    refresh_list_mode()


def refresh_copy_targets():
    del copy_target_paths[:]
    QtBind.clear(gui, copy_target_combo)
    current_path = get_config_path()
    folder = os.path.join(get_config_dir(), pName)
    if not os.path.isdir(folder):
        set_status('No character configs found', COLOR_WARNING)
        return
    current_normalized = os.path.normcase(os.path.abspath(current_path)) \
        if current_path else ''
    for filename in sorted(os.listdir(folder)):
        if not filename.lower().endswith('.json'):
            continue
        path = os.path.abspath(os.path.join(folder, filename))
        if os.path.normcase(path) == current_normalized:
            continue
        copy_target_paths.append(path)
        QtBind.append(gui, copy_target_combo, os.path.splitext(filename)[0])
    if copy_target_paths:
        set_status('%d copy target(s) available' % len(copy_target_paths),
                   COLOR_SUCCESS)
    else:
        set_status('No other character configs found', COLOR_WARNING)


def copy_filters_clicked():
    index = QtBind.currentIndex(gui, copy_target_combo)
    if index < 0 or index >= len(copy_target_paths):
        set_status('Select a target character config', COLOR_WARNING)
        return
    target_path = copy_target_paths[index]
    try:
        with open(target_path, 'r') as config_file:
            target_data = json.load(config_file)
        if not isinstance(target_data, dict):
            raise ValueError('Target settings root must be an object')
        target_data['item_filters'] = list(item_filters)
        temp_path = target_path + '.tmp'
        with open(temp_path, 'w') as config_file:
            json.dump(target_data, config_file, indent=4, sort_keys=True)
        os.replace(temp_path, target_path)
        target_name = os.path.splitext(os.path.basename(target_path))[0]
        set_status('Filters copied to %s' % target_name, COLOR_SUCCESS)
        log('[%s] Copied %d item filter(s) to config [%s].' %
            (pName, len(item_filters), target_name))
    except (OSError, IOError, ValueError, TypeError) as error:
        set_status('Item filters could not be copied', COLOR_ERROR)
        log('[%s] Item filter copy error: %s' % (pName, error))


def refresh_inventory_items():
    QtBind.clear(gui, inventory_combo)
    inventory = get_inventory() or {}
    items = inventory.get('items') or []
    size = min(int(inventory.get('size', len(items))), len(items))
    names = {}
    for slot in range(13, size):
        item = items[slot]
        if not item:
            continue
        name = normalize_name(item.get('name', ''))
        if name:
            names.setdefault(name.lower(), name)
    for key in sorted(names):
        QtBind.append(gui, inventory_combo, names[key])
    set_status('%d inventory item name(s) loaded' % len(names), COLOR_SUCCESS)


def refresh_inventory_clicked():
    refresh_inventory_items()


def add_inventory_item_clicked():
    value = normalize_name(QtBind.text(gui, inventory_combo))
    if not value:
        set_status('Select an inventory item', COLOR_WARNING)
        return
    if any(existing.lower() == value.lower() for existing in item_filters):
        set_status('Item is already listed', COLOR_WARNING)
        return
    item_filters.append(value)
    refresh_player_list()
    set_status('Added %s' % value, COLOR_SUCCESS)


def accept_guild_changed(checked):
    if checked:
        set_status('Nearby guild members will be accepted', COLOR_SUCCESS)
    else:
        set_status('Guild-wide acceptance disabled', COLOR_MUTED)


def reject_unauthorized_changed(checked):
    if checked:
        set_status('Unauthorized requests will be rejected', COLOR_WARNING)
    else:
        set_status('Unauthorized requests remain manual', COLOR_MUTED)


def reload_clicked():
    load_settings()


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        set_status('Opening Discord invite...', COLOR_SUCCESS)
    except Exception as error:
        set_status('Could not open Discord invite', COLOR_ERROR)
        log('[%s] Discord link error: %s' % (pName, error))


def send_private(player, message):
    try:
        phBotChat.Private(player, message)
    except Exception as error:
        log('[%s] Private message error: %s' % (pName, error))


def clear_command():
    global command_sender, command_item_name, command_expires_at
    command_sender = ''
    command_item_name = ''
    command_expires_at = 0.0


def clear_transfer_state():
    global pending_requester_name, active_requester_name
    global transfer_slots, awaiting_inventory_slot
    global next_action_at, action_deadline, automatic_transfer
    global local_confirm_sent, local_confirmed, remote_confirmed, approve_sent
    global added_stack_count, skipped_stack_count
    pending_requester_name = ''
    active_requester_name = ''
    del transfer_slots[:]
    awaiting_inventory_slot = -1
    next_action_at = 0.0
    action_deadline = 0.0
    automatic_transfer = False
    local_confirm_sent = False
    local_confirmed = False
    remote_confirmed = False
    approve_sent = False
    added_stack_count = 0
    skipped_stack_count = 0


def reset_exchange_state(message='Ready'):
    global pending_requester_uid, active_requester_uid
    pending_requester_uid = 0
    active_requester_uid = 0
    clear_transfer_state()
    clear_command()
    set_state('READY', COLOR_SUCCESS)
    set_status(message, COLOR_MUTED)


def cancel_automatic_exchange(reason):
    global automatic_transfer, awaiting_inventory_slot
    automatic_transfer = False
    awaiting_inventory_slot = -1
    inject_joymax(CLIENT_EXCHANGE_CANCEL_REQUEST, b'', False)
    set_state('TRANSFER CANCELLED', COLOR_ERROR)
    set_status(reason, COLOR_ERROR)
    log('[%s] Automatic exchange cancelled: %s' % (pName, reason))
    if active_requester_name:
        send_private(active_requester_name, 'Exchange cancelled: %s' % reason)
    clear_command()


def matching_inventory_slots(item_names):
    inventory = get_inventory() or {}
    items = inventory.get('items') or []
    size = min(int(inventory.get('size', len(items))), len(items))
    wanted = set(name.lower() for name in item_names)
    result = []
    for slot in range(13, size):
        item = items[slot]
        if item and normalize_name(item.get('name', '')).lower() in wanted:
            result.append(slot)
    return result


def prepare_automatic_transfer(requested_items, cancel_if_empty):
    global automatic_transfer, transfer_slots, next_action_at
    global added_stack_count, skipped_stack_count
    slots = matching_inventory_slots(requested_items)
    if not slots:
        missing = ', '.join(requested_items)
        if cancel_if_empty:
            cancel_automatic_exchange('Item not found: %s' % missing)
        else:
            set_state('EXCHANGE OPEN', COLOR_SUCCESS)
            set_status('No filtered items are available', COLOR_WARNING)
            log('[%s] No inventory items matched configured filters.' % pName)
        return
    added_stack_count = 0
    skipped_stack_count = max(0, len(slots) - MAX_EXCHANGE_ITEM_SLOTS)
    transfer_slots[:] = slots[:MAX_EXCHANGE_ITEM_SLOTS]
    automatic_transfer = True
    next_action_at = time.time() + ACTION_DELAY_SECONDS
    set_state('ADDING ITEMS', COLOR_WARNING)
    display_items = ', '.join(requested_items)
    set_status('%d item slot(s) queued' % len(transfer_slots),
               COLOR_WARNING)
    log('[%s] Queued %d inventory item slot(s) matching [%s] for %s; %d remain '
        'beyond the 12-item exchange window.' %
        (pName, len(transfer_slots), display_items,
         active_requester_name, skipped_stack_count))


def continue_with_added_stacks(reason):
    global awaiting_inventory_slot, action_deadline, next_action_at
    global skipped_stack_count
    remaining = len(transfer_slots)
    if remaining:
        del transfer_slots[:]
        skipped_stack_count += remaining
    awaiting_inventory_slot = -1
    action_deadline = 0.0
    next_action_at = time.time() + ACTION_DELAY_SECONDS
    set_state('PARTIAL TRANSFER', COLOR_WARNING)
    set_status('%d item slot(s) added; continuing exchange' % added_stack_count,
               COLOR_WARNING)
    log('[%s] %s; continuing with %d successfully added item slot(s).' %
        (pName, reason, added_stack_count))


def maybe_send_approve():
    global approve_sent, action_deadline
    if (automatic_transfer and local_confirmed and remote_confirmed and
            not approve_sent):
        inject_joymax(CLIENT_EXCHANGE_APPROVE_REQUEST, b'', False)
        approve_sent = True
        action_deadline = time.time() + ACTION_TIMEOUT_SECONDS
        set_state('APPROVING', COLOR_WARNING)
        set_status('Both players confirmed; approving exchange', COLOR_WARNING)


def handle_chat(t, player, msg):
    global command_sender, command_item_name, command_expires_at
    if t != CHAT_PRIVATE or not player or not msg:
        return
    text = normalize_name(msg)
    command_match = re.match(r'^EXC\s+(.+)$', text, re.IGNORECASE)
    if not command_match:
        return
    item_name = command_match.group(1).strip()
    sender = normalize_name(player)
    if not item_name:
        send_private(sender, 'Usage: EXC <Item Name>')
        return
    if not is_command_authorized(sender):
        log('[%s] Ignored unauthorized EXC command from %s.' % (pName, sender))
        send_private(sender, 'Exchange command denied: you are not authorized.')
        return
    if active_requester_uid:
        if sender.lower() != active_requester_name.lower():
            send_private(sender, 'Exchange command busy: another player is active.')
            return
        if automatic_transfer or local_confirm_sent:
            send_private(sender, 'Exchange command busy: transfer already started.')
            return
        command_sender = sender
        command_item_name = item_name
        command_expires_at = time.time() + COMMAND_TIMEOUT_SECONDS
        prepare_automatic_transfer([item_name], True)
        send_private(sender, 'Adding %s to the open exchange.' % item_name)
        return
    if pending_requester_uid:
        send_private(sender, 'Exchange command busy: another exchange is active.')
        return
    command_sender = sender
    command_item_name = item_name
    command_expires_at = time.time() + COMMAND_TIMEOUT_SECONDS
    set_state('COMMAND READY', COLOR_SUCCESS)
    set_status('Waiting for %s to request exchange' % sender, COLOR_WARNING)
    log('[%s] EXC command accepted from %s for item [%s].' %
        (pName, sender, item_name))
    send_private(sender, 'Exchange ready for %s. Send exchange request.' % item_name)


def event_loop():
    global command_expires_at, awaiting_inventory_slot
    global action_deadline, next_action_at, local_confirm_sent
    now = time.time()
    if command_expires_at and now >= command_expires_at and not automatic_transfer:
        expired_sender = command_sender
        clear_command()
        set_state('READY', COLOR_SUCCESS)
        set_status('EXC command expired', COLOR_WARNING)
        if expired_sender:
            send_private(expired_sender, 'Exchange command expired.')

    if not automatic_transfer:
        return
    if awaiting_inventory_slot >= 0:
        if action_deadline and now >= action_deadline:
            cancel_automatic_exchange('Timed out while adding an item')
        return
    if local_confirm_sent and not local_confirmed:
        if action_deadline and now >= action_deadline:
            cancel_automatic_exchange('Timed out while confirming exchange')
        return
    if approve_sent:
        if action_deadline and now >= action_deadline:
            cancel_automatic_exchange('Timed out while approving exchange')
        return
    if next_action_at and now < next_action_at:
        return
    if transfer_slots:
        slot = transfer_slots[0]
        inject_joymax(
            CLIENT_INVENTORY_OPERATION,
            struct.pack('BB', EXCHANGE_ADD_ITEM, slot),
            False
        )
        awaiting_inventory_slot = slot
        action_deadline = now + ACTION_TIMEOUT_SECONDS
        next_action_at = 0.0
        set_status('Adding inventory slot %d' % slot, COLOR_WARNING)
        return
    if not local_confirm_sent:
        inject_joymax(CLIENT_EXCHANGE_CONFIRM_REQUEST, b'', False)
        local_confirm_sent = True
        action_deadline = now + ACTION_TIMEOUT_SECONDS
        set_state('CONFIRMING', COLOR_WARNING)
        set_status('All stacks added; confirming exchange', COLOR_WARNING)


def handle_unauthorized_request(log_message):
    if QtBind.isChecked(gui, reject_unauthorized_checkbox):
        inject_joymax(CLIENT_GAME_PETITION_RESPONSE, b'\x01\x00', False)
        set_state('REQUEST REJECTED', COLOR_ERROR)
        set_status('Unauthorized exchange request rejected', COLOR_ERROR)
        log('[%s] Rejected exchange request: %s' % (pName, log_message))
        return False

    set_status('Exchange request left for manual handling', COLOR_WARNING)
    log('[%s] Exchange request left for manual handling: %s' %
        (pName, log_message))
    return True


def teleported():
    load_settings()
    reset_exchange_state('Ready for exchange requests')


def disconnected():
    reset_exchange_state('Waiting for connection')
    set_state('DISCONNECTED', COLOR_MUTED)


def handle_joymax(opcode, data):
    global pending_requester_uid, pending_requester_name
    global active_requester_uid, active_requester_name
    global awaiting_inventory_slot, next_action_at, action_deadline
    global local_confirmed, remote_confirmed
    global added_stack_count
    global command_sender, command_item_name, command_expires_at

    if opcode == SERVER_GAME_PETITION_REQUEST:
        if len(data) < 5 or data[0] != EXCHANGE_PETITION_TYPE:
            return True

        pending_requester_uid = 0
        pending_requester_name = ''
        requester_uid = struct.unpack_from('<I', data, 1)[0]
        requester_name = resolve_requester(requester_uid)
        if not requester_name:
            set_requester('UID %u' % requester_uid,
                          'Nearby player name not found', COLOR_WARNING)
            return handle_unauthorized_request(
                'UID %u could not be resolved' % requester_uid)

        authorization = ''
        if is_allowed(requester_name):
            authorization = 'Allowed player'
        elif (QtBind.isChecked(gui, accept_guild_checkbox) and
              guild_contains_name(requester_name)):
            authorization = 'Guild member option enabled'

        if not authorization:
            set_requester(requester_name, 'Not authorized', COLOR_WARNING)
            return handle_unauthorized_request(
                '%s is not authorized' % requester_name)

        pending_requester_uid = requester_uid
        pending_requester_name = requester_name
        inject_joymax(CLIENT_GAME_PETITION_RESPONSE, b'\x01\x01', False)
        set_requester(requester_name, authorization, COLOR_SUCCESS)
        set_state('ACCEPTING REQUEST', COLOR_WARNING)
        set_status('Accepting exchange from %s' % requester_name, COLOR_SUCCESS)
        log('[%s] Auto-accepted exchange request from %s (UID %u).' %
            (pName, requester_name, requester_uid))

    elif opcode == SERVER_EXCHANGE_STARTED:
        if len(data) >= 4:
            requester_uid = struct.unpack_from('<I', data, 0)[0]
            if pending_requester_uid and requester_uid == pending_requester_uid:
                active_requester_uid = requester_uid
                active_requester_name = pending_requester_name
                pending_requester_uid = 0
                pending_requester_name = ''
                set_state('EXCHANGE OPEN', COLOR_SUCCESS)
                set_status('Authorized exchange is open', COLOR_SUCCESS)
                if (command_sender and
                        command_sender.lower() == active_requester_name.lower() and
                        time.time() < command_expires_at):
                    prepare_automatic_transfer([command_item_name], True)
                elif item_filters:
                    command_sender = active_requester_name
                    command_item_name = ', '.join(item_filters)
                    command_expires_at = 0.0
                    prepare_automatic_transfer(list(item_filters), False)

    elif opcode == SERVER_INVENTORY_OPERATION_RESPONSE:
        if automatic_transfer and awaiting_inventory_slot >= 0:
            if (len(data) >= 4 and data[0] == 1 and
                    data[1] == EXCHANGE_ADD_ITEM and
                    data[2] == awaiting_inventory_slot):
                completed_slot = transfer_slots.pop(0)
                added_stack_count += 1
                awaiting_inventory_slot = -1
                action_deadline = 0.0
                next_action_at = time.time() + ACTION_DELAY_SECONDS
                log('[%s] Added inventory slot %d to exchange slot %d.' %
                    (pName, completed_slot, data[3]))
            elif data and data[0] == 2:
                if added_stack_count:
                    continue_with_added_stacks(
                        'Receiver inventory rejected the next stack')
                else:
                    cancel_automatic_exchange(
                        'Item rejected; receiver inventory may be full')

    elif opcode == SERVER_EXCHANGE_CONFIRM_RESPONSE:
        if automatic_transfer and data and data[0] == 1:
            local_confirmed = True
            action_deadline = 0.0
            set_state('WAITING FOR PLAYER', COLOR_WARNING)
            set_status('Waiting for the other player to confirm', COLOR_WARNING)
            maybe_send_approve()

    elif opcode == SERVER_EXCHANGE_REMOTE_CONFIRMED:
        if automatic_transfer:
            remote_confirmed = True
            maybe_send_approve()

    elif opcode == SERVER_EXCHANGE_APPROVE_RESPONSE:
        if automatic_transfer and data and data[0] == 1:
            action_deadline = 0.0
            set_state('APPROVED', COLOR_SUCCESS)
            set_status('Waiting for exchange completion', COLOR_SUCCESS)

    elif opcode == SERVER_EXCHANGE_COMPLETED:
        completed_player = active_requester_name
        completed_item = command_item_name
        completed_stacks = added_stack_count
        remaining_stacks = skipped_stack_count
        reset_exchange_state('Exchange completed')
        if completed_player and completed_item:
            message = 'Exchange completed: %s (%d item slot(s))' % (
                completed_item, completed_stacks)
            if remaining_stacks:
                message += '; %d item slot(s) remain' % remaining_stacks
            send_private(completed_player, message)

    elif opcode == SERVER_EXCHANGE_CANCELED:
        reset_exchange_state('Exchange cancelled')

    elif opcode == SERVER_EXCHANGE_EXIT_RESPONSE:
        if data and data[0] in (1, 2):
            reset_exchange_state('Exchange closed')

    return True


if get_config_path():
    load_settings()

log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
