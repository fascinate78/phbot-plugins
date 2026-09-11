from phBot import *
import QtBind
import json
import os
import struct
import time
import webbrowser


pName = 'FEventAutomation'
pVersion = '1.0.4'
SHOW_PACKET_RECORDER = False
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

# Automatic Event So-Ok event-item exchange with an optional packet recorder.

gui = QtBind.init(__name__, pName)

COLOR_PRIMARY = '#5b57e0'
COLOR_MUTED = '#9aa0ac'


def fixed_width_text(content, width):
    return (
        '<table width="{0}" cellspacing="0" cellpadding="0">'
        '<tr><td>{1}</td></tr></table>'
    ).format(width, content)

QtBind.createLabel(
    gui, u'<font color="%s" size="4"><b>💎 %s</b></font>' %
    (COLOR_PRIMARY, pName), 12, 6)
QtBind.createLabel(
    gui, '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion), 174, 12)
btnDiscord = QtBind.createButton(
    gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(
    gui, u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' %
    COLOR_PRIMARY, 565, 11)
QtBind.createLineEdit(gui, '', 12, 32, 696, 1)

QtBind.createLabel(
    gui, '<font color="%s"><b>▶ AUTOMATION</b></font>' % COLOR_PRIMARY,
    12, 57)
QtBind.createLabel(gui, 'Event item:', 12, 83)
cmbEventItem = QtBind.createCombobox(gui, 105, 79, 190, 22)
QtBind.append(gui, cmbEventItem, 'Jewel Box')
QtBind.append(gui, cmbEventItem, 'Pledge of Love')
btnAutoStart = QtBind.createButton(
    gui, 'auto_start_clicked', '▶  Start Automatic', 12, 110)
btnAutoStop = QtBind.createButton(
    gui, 'auto_stop_clicked', '■  Stop', 147, 110)
btnSnapshot = QtBind.createButton(
    gui, 'snapshot_clicked', '↻  Inventory Snapshot', 225, 110)
btnOpenSilkroadBox = QtBind.createButton(
    gui, 'open_silkroad_box_clicked', 'Open Silkroad Box', 12, 138)

QtBind.createLineEdit(gui, '', 370, 57, 1, 110)
QtBind.createLabel(
    gui, '<font color="%s"><b>● LIVE STATUS</b></font>' % COLOR_PRIMARY,
    390, 57)
lblStatus = QtBind.createLabel(
    gui, fixed_width_text('<font color="#6f7782">Status: Ready</font>', 318),
    390, 83)
lblCount = QtBind.createLabel(
    gui, fixed_width_text('Event items: Unknown', 318), 390, 106)
QtBind.createLabel(
    gui, '<font color="%s">So-Ok consumes up to the free slots.</font>' %
    COLOR_MUTED, 390, 131)

QtBind.createLineEdit(gui, '', 12, 167, 696, 1)
chkCaptureAll = None
btnRecord = None
btnStop = None

if SHOW_PACKET_RECORDER:
    QtBind.createLabel(
        gui, '<font color="%s"><b>◆ PACKET RECORDER</b></font>' % COLOR_PRIMARY,
        12, 179)
    chkCaptureAll = QtBind.createCheckBox(
        gui, 'capture_all_changed', 'Capture all client packets', 12, 202)
    QtBind.setChecked(gui, chkCaptureAll, True)
    btnRecord = QtBind.createButton(
        gui, 'record_clicked', '●  Start Record', 220, 200)
    btnStop = QtBind.createButton(
        gui, 'stop_clicked', '■  Stop & Save', 330, 200)
    log_header_y = 236
    log_list_y = 258
    log_list_height = 41
    log_checkbox_y = 202
else:
    log_header_y = 179
    log_list_y = 201
    log_list_height = 98
    log_checkbox_y = 177

chkLog = QtBind.createCheckBox(
    gui, 'log_changed', 'Show detailed log', 570, log_checkbox_y)
QtBind.setChecked(gui, chkLog, True)
QtBind.createLabel(
    gui, '<font color="%s"><b>▣ ACTIVITY LOG</b></font>' % COLOR_PRIMARY,
    12, log_header_y)
lstEvents = QtBind.createList(
    gui, 12, log_list_y, 696, log_list_height)


IMPORTANT_CLIENT_OPCODES = set([
    0x7034,  # inventory operation
    0x7045,  # select NPC
    0x7046,  # open NPC/menu
    0x704B,  # close NPC
    0x30D4,  # quest/event talk (can be bidirectional)
    0x3567,  # observed event/quest packet on this server family
    0x70D8, 0x70D9, 0x70DB, 0x7515,
])

IMPORTANT_SERVER_OPCODES = set([
    0xB034, 0x3034, 0x3035, 0x3040, 0xB045, 0xB046, 0xB04B,
    0x30D4, 0x30D5, 0x30D6, 0x30D7, 0x30EC, 0x3514, 0x3515,
    0x3567, 0x3CA2,
])

# Packets that add noise and are not useful for learning an NPC exchange.
NOISY_CLIENT_OPCODES = set([
    0x2002, 0x7021, 0x7024, 0x7025, 0x7074,
])

is_recording = False
recording_mode = 'jewel_box'
session = None
last_inventory = None
last_exchange_state = None
sort_jobs = []
session_number = 0
auto_running = False
auto_stage = 'idle'
auto_due_ms = 0
auto_step = 0
auto_start_state = None
auto_cycles = 0
auto_sort_started_ms = 0
auto_sort_last_activity_ms = 0
auto_sort_signature = None
auto_mode = 'jewel_box'
auto_retry_count = 0
auto_empty_sort_retry_count = 0

JEWEL_SERVERNAME = 'ITEM_ETC_E050618_TREASUREBOX'
PLEDGE_LEFT_SERVERNAME = 'ITEM_ETC_E070523_LEFT_HEART'
PLEDGE_RIGHT_SERVERNAME = 'ITEM_ETC_E070523_RIGHT_HEART'
SOOK_SERVERNAME = 'NPC_CH_EVENT_KISAENG1'
MIN_JEWEL_COUNT = 1
MIN_FREE_SLOTS = 1
AUTO_PACKET_DELAY_MS = 850
PLEDGE_NPC_DELAY_MS = 1300
PLEDGE_CONFIRM_DELAY_MS = 1800
AUTO_RESULT_TIMEOUT_MS = 12000
AUTO_MAX_RETRIES = 2
AUTO_RETRY_CLOSE_DELAY_MS = 2000
AUTO_EMPTY_SORT_RETRY_DELAY_MS = 2000
AUTO_POST_CLOSE_SORT_DELAY_MS = 1200
AUTO_SORT_QUIET_MS = 12000
AUTO_SORT_TIMEOUT_MS = 120000

SILKROAD_BOX_SERVERNAME = 'ITEM_PRE_MALL_SILKROAD_BOX'
SILKROAD_BOX_USE_TAIL = b'\x31\x0C\x0E\x05'
SILKROAD_BOX_NEXT_DELAY_MS = 500

silkroad_box_running = False
silkroad_box_stage = 'idle'
silkroad_box_due_ms = 0
silkroad_box_slots = []
silkroad_box_slot_index = 0
silkroad_box_opened = 0


def _now_ms():
    return int(time.time() * 1000)


def _hex(data):
    if data is None:
        return ''
    try:
        return bytes(data).hex().upper()
    except Exception:
        return ''.join('%02X' % value for value in bytearray(data))


def _plain(value):
    return str(value or '').strip().lower()


def _selected_mode():
    try:
        value = _plain(QtBind.text(gui, cmbEventItem))
    except Exception:
        value = ''
    return 'pledge_of_love' if 'pledge' in value else 'jewel_box'


def _mode_name(mode):
    return 'Pledge of Love' if mode == 'pledge_of_love' else 'Jewel Box'


def _item_quantity(item):
    try:
        return int(item.get('quantity', 1) or 1)
    except Exception:
        return 1


def _is_jewel_box(item):
    if not isinstance(item, dict):
        return False
    return _plain(item.get('servername')) == _plain(JEWEL_SERVERNAME)


def _item_count(snapshot, servername):
    if not snapshot:
        return 0
    return sum(_item_quantity(item) for item in snapshot.get('items', [])
               if _plain(item.get('servername')) == _plain(servername))


def _exchange_state(snapshot, mode=None):
    mode = mode or _selected_mode()
    if mode == 'pledge_of_love':
        return (
            _item_count(snapshot, PLEDGE_LEFT_SERVERNAME),
            _item_count(snapshot, PLEDGE_RIGHT_SERVERNAME),
        )
    return (_jewel_count(snapshot),)


def _exchange_count(state, mode):
    if not state:
        return 0
    if mode == 'pledge_of_love':
        return min(state[0], state[1])
    return state[0]


def _state_consumed(before, after, mode):
    if not before or not after:
        return False
    if mode == 'pledge_of_love':
        return after[0] < before[0] and after[1] < before[1]
    return after[0] < before[0]


def _state_text(state, mode):
    if mode == 'pledge_of_love':
        return 'Left: %s | Right: %s | Pairs: %s' % (
            state[0], state[1], min(state[0], state[1]))
    return 'Jewel Boxes: %s' % state[0]


def _inventory_snapshot():
    try:
        inventory = get_inventory()
    except Exception as ex:
        _event('Inventory could not be read: %s' % ex)
        return None
    if not inventory or not isinstance(inventory.get('items'), list):
        return None

    result = {
        'time_ms': _now_ms(),
        'size': int(inventory.get('size', 0) or 0),
        'gold': int(inventory.get('gold', 0) or 0),
        'items': [],
    }
    for slot, item in enumerate(inventory.get('items', [])):
        if not item:
            continue
        result['items'].append({
            'slot': slot,
            'model': int(item.get('model', 0) or 0),
            'servername': str(item.get('servername', '') or ''),
            'name': str(item.get('name', '') or ''),
            'quantity': _item_quantity(item),
            'plus': int(item.get('plus', 0) or 0),
            'durability': int(item.get('durability', 0) or 0),
        })
    return result


def _jewel_count(snapshot):
    if not snapshot:
        return None
    total = 0
    for item in snapshot.get('items', []):
        if _is_jewel_box(item):
            total += _item_quantity(item)
    return total


def _silkroad_boxes(snapshot):
    if not snapshot:
        return []
    return [item for item in snapshot.get('items', [])
            if _plain(item.get('servername')) ==
            _plain(SILKROAD_BOX_SERVERNAME)]


def _silkroad_box_count(snapshot):
    return sum(_item_quantity(item) for item in _silkroad_boxes(snapshot))


def _npc_snapshot():
    output = []
    try:
        npcs = get_npcs()
    except Exception:
        npcs = None
    if not npcs:
        return output
    for uid, npc in npcs.items():
        if not isinstance(npc, dict):
            continue
        text = (_plain(npc.get('name')) + ' ' +
                _plain(npc.get('servername')))
        if ('so-ok' not in text and 'so ok' not in text and
                'event' not in text and 'kisaeng' not in text):
            continue
        output.append({
            'uid': int(uid),
            'name': str(npc.get('name', '') or ''),
            'servername': str(npc.get('servername', '') or ''),
            'model': int(npc.get('model', 0) or 0),
            'x': npc.get('x'),
            'y': npc.get('y'),
        })
    return output


def _find_sook_uid():
    try:
        npcs = get_npcs()
    except Exception:
        npcs = None
    if not npcs:
        return 0
    fallback = 0
    for uid, npc in npcs.items():
        if not isinstance(npc, dict):
            continue
        servername = _plain(npc.get('servername'))
        name = _plain(npc.get('name'))
        if servername == _plain(SOOK_SERVERNAME):
            return int(uid)
        if name == 'event so-ok' or 'so-ok' in name or 'so ok' in name:
            fallback = int(uid)
    return fallback


def _free_inventory_slots(snapshot=None):
    if snapshot is None:
        snapshot = _inventory_snapshot()
    if not snapshot:
        return 0
    used = set(item.get('slot') for item in snapshot.get('items', [])
               if int(item.get('slot', -1)) >= 13)
    size = int(snapshot.get('size', 0) or 0)
    return sum(1 for slot in range(13, size) if slot not in used)


def _character_snapshot():
    try:
        data = get_character_data()
    except Exception:
        data = None
    if not isinstance(data, dict):
        return {}
    keys = ('name', 'server', 'region', 'x', 'y', 'z')
    return dict((key, data.get(key)) for key in keys if key in data)


def _event(text):
    if is_recording and session is not None:
        session.setdefault('events', []).append({
            'time_ms': _now_ms(), 'text': str(text)
        })
    try:
        logging_enabled = QtBind.isChecked(gui, chkLog)
    except Exception:
        logging_enabled = True
    if not logging_enabled:
        return
    line = time.strftime('%H:%M:%S') + ' ' + str(text)
    log('[%s] %s' % (pName, text))
    try:
        QtBind.append(gui, lstEvents, line)
        items = QtBind.getItems(gui, lstEvents)
        if items and len(items) > 120:
            QtBind.removeAt(gui, lstEvents, 0)
    except Exception:
        pass


def _set_status(text):
    QtBind.setText(
        gui, lblStatus,
        fixed_width_text('Status: ' + str(text), 318))


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        _set_status('Opening Discord invite...')
    except Exception as error:
        log('[%s] Discord link error: %s' % (pName, error))
        _set_status('Could not open Discord invite')


def _update_count(state, mode=None):
    mode = mode or _selected_mode()
    text = 'Unknown' if state is None else _state_text(state, mode)
    QtBind.setText(
        gui, lblCount,
        fixed_width_text(text, 318))


def _record_packet(direction, opcode, data):
    if not is_recording or session is None:
        return
    session['packets'].append({
        'time_ms': _now_ms(),
        'elapsed_ms': _now_ms() - session['started_ms'],
        'direction': direction,
        'opcode': '0x%04X' % opcode,
        'data': _hex(data),
        'length': len(data) if data is not None else 0,
    })


def _config_folder():
    try:
        base = get_config_dir()
    except Exception:
        base = None
    if not base:
        return None
    folder = os.path.join(base, pName)
    if not os.path.isdir(folder):
        try:
            os.makedirs(folder)
        except OSError:
            if not os.path.isdir(folder):
                raise
    return folder


def _save_session():
    if not session:
        return None
    folder = _config_folder()
    if not folder:
        _event('Config folder was not found; recording could not be saved.')
        return None
    char_name = _character_snapshot().get('name') or 'character'
    safe_name = ''.join(c if c.isalnum() or c in '-_' else '_'
                        for c in str(char_name))
    stamp = time.strftime('%Y%m%d_%H%M%S')
    path = os.path.join(
        folder, 'FEventAutomation_%s_%s.json' % (safe_name, stamp))
    session['saved_ms'] = _now_ms()
    session['final_inventory'] = _inventory_snapshot()
    session['nearby_event_npcs_final'] = _npc_snapshot()
    with open(path, 'w') as handle:
        json.dump(session, handle, indent=2, sort_keys=True)
    return path


def capture_all_changed(checked):
    _event('Capture all client packets: %s' % ('enabled' if checked else 'disabled'))


def log_changed(checked):
    # Do not call _event here: disabling the checkbox must be silent by design.
    if checked:
        log('[%s] Detailed logging enabled.' % pName)


def _capture_all_enabled():
    if chkCaptureAll is None:
        return True
    try:
        return QtBind.isChecked(gui, chkCaptureAll)
    except Exception:
        return True


def record_clicked():
    global is_recording, session, last_inventory, last_exchange_state
    global session_number, sort_jobs, recording_mode
    if is_recording:
        _event('Packet recording is already active.')
        return
    snapshot = _inventory_snapshot()
    mode = _selected_mode()
    recording_mode = mode
    last_inventory = snapshot
    last_exchange_state = _exchange_state(snapshot, mode)
    sort_jobs = []
    session_number += 1
    session = {
        'plugin': pName,
        'version': pVersion,
        'session_number': session_number,
        'started_ms': _now_ms(),
        'event_mode': mode,
        'locale': get_locale(),
        'encoding': get_encoding(),
        'character': _character_snapshot(),
        'nearby_event_npcs': _npc_snapshot(),
        'initial_inventory': snapshot,
        'packets': [],
        'inventory_changes': [],
        'events': [],
    }
    is_recording = True
    _update_count(last_exchange_state, mode)
    _set_status('Recording - exchange one %s manually' % _mode_name(mode))
    _event('Recording started. %s' % _state_text(last_exchange_state, mode))


def stop_clicked():
    global is_recording
    if not is_recording:
        _event('No packet recording is active.')
        return
    is_recording = False
    try:
        path = _save_session()
        if path:
            _event('Recording saved: %s' % path)
            _set_status('Recording saved')
        else:
            _set_status('Recording could not be saved')
    except Exception as ex:
        _event('Recording error: %s' % ex)
        _set_status('Recording error')


def _auto_stop(reason):
    global auto_running, auto_stage, auto_due_ms, auto_step
    global auto_sort_started_ms, auto_sort_last_activity_ms
    global auto_sort_signature, auto_retry_count
    global auto_empty_sort_retry_count
    auto_running = False
    auto_stage = 'idle'
    auto_due_ms = 0
    auto_step = 0
    auto_sort_started_ms = 0
    auto_sort_last_activity_ms = 0
    auto_sort_signature = None
    auto_retry_count = 0
    auto_empty_sort_retry_count = 0
    _set_status('Automation stopped: %s' % reason)
    _event('Automation stopped: %s' % reason)


def _silkroad_box_stop(reason):
    global silkroad_box_running, silkroad_box_stage
    global silkroad_box_due_ms
    silkroad_box_running = False
    silkroad_box_stage = 'idle'
    silkroad_box_due_ms = 0
    _set_status('Silkroad Box stopped: %s' % reason)
    _event('Silkroad Box operation stopped: %s' % reason)


def auto_stop_clicked():
    if auto_running:
        _auto_stop('stopped by user')
    if silkroad_box_running:
        _silkroad_box_stop('stopped by user')


def open_silkroad_box_clicked():
    global silkroad_box_running, silkroad_box_stage
    global silkroad_box_due_ms, silkroad_box_slots
    global silkroad_box_slot_index, silkroad_box_opened
    if auto_running:
        _event('Stop Event So-Ok automation first.')
        return
    if silkroad_box_running:
        _event('Silkroad Box opening is already running.')
        return
    snapshot = _inventory_snapshot()
    boxes = _silkroad_boxes(snapshot)
    count = _silkroad_box_count(snapshot)
    if not boxes:
        _set_status('Silkroad Box not found')
        _event('%s was not found in the inventory.' % SILKROAD_BOX_SERVERNAME)
        return
    # Capture the slots only once. A stacked box contributes the same slot to
    # the queue once per quantity, while separate boxes keep their own slots.
    silkroad_box_slots = []
    for item in boxes:
        silkroad_box_slots.extend(
            [int(item['slot'])] * _item_quantity(item))
    silkroad_box_slot_index = 0
    silkroad_box_running = True
    silkroad_box_stage = 'ready'
    silkroad_box_due_ms = _now_ms()
    silkroad_box_opened = 0
    _set_status('Opening Silkroad Boxes: %s' % count)
    _event('Silkroad Box automation started: count=%s, slots=%s.' %
           (count, silkroad_box_slots))


def _run_silkroad_box():
    global silkroad_box_stage, silkroad_box_due_ms
    global silkroad_box_slot_index, silkroad_box_opened
    if not silkroad_box_running or _now_ms() < silkroad_box_due_ms:
        return

    if silkroad_box_slot_index >= len(silkroad_box_slots):
        _silkroad_box_stop('all packets sent (%s total)' %
                           silkroad_box_opened)
        return

    slot = silkroad_box_slots[silkroad_box_slot_index]
    packet = struct.pack('<B', slot) + SILKROAD_BOX_USE_TAIL
    try:
        inject_joymax(0x704C, packet, True)
    except Exception as ex:
        _silkroad_box_stop('packet error: %s' % ex)
        return
    silkroad_box_slot_index += 1
    silkroad_box_opened += 1
    silkroad_box_stage = 'ready'
    silkroad_box_due_ms = _now_ms() + SILKROAD_BOX_NEXT_DELAY_MS
    _set_status('Silkroad Box packets sent: %s/%s' %
                (silkroad_box_opened, len(silkroad_box_slots)))
    _event('Silkroad Box used: slot=%s, packet=%s (%s/%s)' %
           (slot, _hex(packet), silkroad_box_opened,
            len(silkroad_box_slots)))


def auto_start_clicked():
    global auto_running, auto_stage, auto_due_ms, auto_step
    global auto_start_state, auto_cycles, auto_mode, auto_retry_count
    global auto_empty_sort_retry_count
    global last_inventory, last_exchange_state
    if auto_running:
        _event('Automation is already running.')
        return
    snapshot = _inventory_snapshot()
    auto_mode = _selected_mode()
    state = _exchange_state(snapshot, auto_mode)
    count = _exchange_count(state, auto_mode)
    free_slots = _free_inventory_slots(snapshot)
    uid = _find_sook_uid()
    _update_count(state, auto_mode)
    if not uid:
        _set_status('Event So-Ok not found')
        _event('Event So-Ok is not nearby. Move next to the NPC and try again.')
        return
    if count is None or count < MIN_JEWEL_COUNT:
        _set_status('%s pair/item not found' % _mode_name(auto_mode))
        _event('Not enough %s items: %s' %
               (_mode_name(auto_mode), _state_text(state, auto_mode)))
        return
    if free_slots < MIN_FREE_SLOTS:
        _set_status('A free inventory slot is required')
        _event('No free slots. So-Ok exchanges up to the number of free slots.')
        return
    auto_running = True
    auto_stage = 'sending'
    auto_due_ms = _now_ms()
    auto_step = 0
    auto_start_state = state
    auto_cycles = 0
    auto_retry_count = 0
    auto_empty_sort_retry_count = 0
    last_inventory = snapshot
    last_exchange_state = state
    _set_status('Automation started')
    _event('Automation started: mode=%s, UID=%s, %s, free slots=%s' %
           (_mode_name(auto_mode), uid, _state_text(state, auto_mode),
            free_slots))


def _auto_packets(uid, mode):
    # Exact Astyra/SilkroadR sequence learned from the supplied capture.
    if mode == 'pledge_of_love':
        return (
            (0x7045, struct.pack('<I', uid)),
            (0x7046, struct.pack('<IB', uid, 2)),
            (0x30D4, b'\x08'),
            (0x30D4, b'\x05'),
        )
    return (
        (0x3567, b'\x0B\x00'),
        (0x7045, struct.pack('<I', uid)),
        (0x7046, struct.pack('<IB', uid, 2)),
        (0x30D4, b'\x07'),
        (0x3567, b'\x0B\x00'),
        (0x30D4, b'\x05'),
    )


def _auto_packet_delay(mode, sent_index):
    if mode != 'pledge_of_love':
        return AUTO_PACKET_DELAY_MS
    if sent_index == 2:
        return PLEDGE_CONFIRM_DELAY_MS
    return PLEDGE_NPC_DELAY_MS


def _inject_npc_close():
    # Event So-Ok uses the same close/cleanup sequence for all supported
    # exchanges. The 0x3567 packet prevents the conversation from remaining
    # on the End Conversation screen after 0x30D4/05.
    inject_joymax(0x30D4, b'\x05', False)
    inject_joymax(0x3567, b'\x0B\x00', False)


def _run_auto():
    global auto_stage, auto_due_ms, auto_step, auto_start_state
    global auto_cycles, auto_retry_count
    global auto_sort_started_ms, auto_sort_last_activity_ms
    global auto_sort_signature, auto_empty_sort_retry_count
    if not auto_running or _now_ms() < auto_due_ms:
        return

    if auto_stage == 'sending':
        uid = _find_sook_uid()
        if not uid:
            _auto_stop('Event So-Ok left the visible area')
            return
        packets = _auto_packets(uid, auto_mode)
        if auto_step < len(packets):
            sent_index = auto_step
            opcode, data = packets[auto_step]
            try:
                inject_joymax(opcode, data, False)
                _event('AUTO C>S 0x%04X %s' % (opcode, _hex(data)))
            except Exception as ex:
                _auto_stop('packet error: %s' % ex)
                return
            auto_step += 1
            if auto_step >= len(packets):
                auto_stage = 'waiting_result'
                auto_due_ms = _now_ms() + AUTO_RESULT_TIMEOUT_MS
                _set_status('Waiting for reward and inventory update')
            else:
                auto_due_ms = (_now_ms() +
                               _auto_packet_delay(auto_mode, sent_index))
            return

    if auto_stage == 'waiting_result':
        if (auto_mode == 'pledge_of_love' and
                auto_retry_count < AUTO_MAX_RETRIES):
            auto_retry_count += 1
            try:
                _inject_npc_close()
            except Exception as ex:
                _auto_stop('retry close error: %s' % ex)
                return
            auto_stage = 'retry_prepare'
            auto_due_ms = _now_ms() + AUTO_RETRY_CLOSE_DELAY_MS
            _set_status('Retrying Pledge of Love: %s/%s' %
                        (auto_retry_count, AUTO_MAX_RETRIES))
            _event('Pledge of Love did not decrease; retry %s/%s queued.' %
                   (auto_retry_count, AUTO_MAX_RETRIES))
            return
        _auto_stop('%s count did not decrease after %s attempt(s)' %
                   (_mode_name(auto_mode), auto_retry_count + 1))
        return

    if auto_stage == 'retry_prepare':
        snapshot = _inventory_snapshot()
        state = _exchange_state(snapshot, auto_mode)
        # Let event_loop process a reward that arrived just after the timeout.
        if _state_consumed(auto_start_state, state, auto_mode):
            auto_stage = 'waiting_result'
            auto_due_ms = _now_ms() + 1000
            return
        if not _find_sook_uid():
            _auto_stop('Event So-Ok left the visible area before retry')
            return
        count = _exchange_count(state, auto_mode)
        if count < MIN_JEWEL_COUNT:
            _auto_stop('No Pledge of Love pairs remaining before retry')
            return
        free_slots = _free_inventory_slots(snapshot)
        if free_slots < MIN_FREE_SLOTS:
            _auto_stop('not enough free slots before retry (%s/%s)' %
                       (free_slots, MIN_FREE_SLOTS))
            return
        auto_start_state = state
        auto_step = 0
        auto_stage = 'sending'
        auto_due_ms = _now_ms() + 300
        _set_status('Starting Pledge of Love retry %s/%s' %
                    (auto_retry_count, AUTO_MAX_RETRIES))
        return

    if auto_stage == 'closing':
        try:
            _inject_npc_close()
        except Exception as ex:
            _auto_stop('NPC close error: %s' % ex)
            return
        snapshot = _inventory_snapshot()
        result_state = _exchange_state(snapshot, auto_mode)
        _queue_sort_for_break(
            auto_start_state, result_state, auto_mode,
            AUTO_POST_CLOSE_SORT_DELAY_MS)
        auto_stage = 'sorting_wait'
        auto_sort_started_ms = _now_ms()
        auto_sort_last_activity_ms = _now_ms()
        auto_sort_signature = _inventory_signature(_inventory_snapshot())
        auto_due_ms = _now_ms() + 500
        _set_status('NPC closed; waiting to sort inventory')
        return

    if auto_stage == 'sorting_wait':
        now = _now_ms()
        snapshot = _inventory_snapshot()
        signature = _inventory_signature(snapshot)
        if signature != auto_sort_signature:
            auto_sort_signature = signature
            auto_sort_last_activity_ms = now
        if now - auto_sort_started_ms >= AUTO_SORT_TIMEOUT_MS:
            _auto_stop('inventory sorting timeout')
            return
        quiet_ms = now - auto_sort_last_activity_ms
        if quiet_ms < AUTO_SORT_QUIET_MS:
            auto_due_ms = now + 500
            return
        _event('Inventory sorting completed after %s ms of inactivity.' % quiet_ms)
        auto_stage = 'next_cycle'
        auto_due_ms = now

    if auto_stage == 'empty_sort_retry':
        try:
            result = sort_inventory()
            _event('Empty-slot retry sort_inventory(): %s' % result)
        except Exception as ex:
            _auto_stop('empty-slot retry sort error: %s' % ex)
            return
        auto_stage = 'sorting_wait'
        auto_sort_started_ms = _now_ms()
        auto_sort_last_activity_ms = _now_ms()
        auto_sort_signature = _inventory_signature(_inventory_snapshot())
        auto_due_ms = _now_ms() + 500
        _set_status('Waiting for retry inventory sort to finish')
        return

    if auto_stage == 'next_cycle':
        snapshot = _inventory_snapshot()
        state = _exchange_state(snapshot, auto_mode)
        count = _exchange_count(state, auto_mode)
        free_slots = _free_inventory_slots(snapshot)
        if count is None or count < MIN_JEWEL_COUNT:
            _auto_stop('No %s pairs/items remaining' % _mode_name(auto_mode))
            return
        if free_slots < MIN_FREE_SLOTS:
            if auto_empty_sort_retry_count < 1:
                auto_empty_sort_retry_count += 1
                auto_stage = 'empty_sort_retry'
                auto_due_ms = (_now_ms() +
                               AUTO_EMPTY_SORT_RETRY_DELAY_MS)
                _set_status('No free slots; retrying inventory sort')
                _event('No free slots after sorting; a second inventory '
                       'sort will run in 2 seconds.')
                return
            _auto_stop('not enough free slots after retry sort (%s/%s)' %
                       (free_slots, MIN_FREE_SLOTS))
            return
        auto_start_state = state
        auto_retry_count = 0
        auto_empty_sort_retry_count = 0
        auto_step = 0
        auto_stage = 'sending'
        auto_due_ms = _now_ms() + 300
        _set_status('Preparing the next packet sequence')


def snapshot_clicked():
    snapshot = _inventory_snapshot()
    mode = _selected_mode()
    state = _exchange_state(snapshot, mode)
    _update_count(state, mode)
    _event('Snapshot: %s occupied item slots, %s' % (
        len(snapshot.get('items', [])) if snapshot else 0,
        _state_text(state, mode)))
    if is_recording and session is not None:
        session.setdefault('manual_snapshots', []).append(snapshot)


def _inventory_signature(snapshot):
    if not snapshot:
        return None
    return tuple((item['slot'], item['model'], item['quantity'], item['plus'])
                 for item in snapshot.get('items', []))


def _queue_sort_for_break(old_state, new_state, mode, delay_ms=900):
    # One job per observed exchange.  A small delay lets the reward inventory
    # update finish before phBot stacks equal items.
    sort_jobs.append({
        'due_ms': _now_ms() + delay_ms,
        'old_state': old_state,
        'new_state': new_state,
        'mode': mode,
    })
    _event('%s decreased (%s -> %s); inventory sort queued.' %
           (_mode_name(mode), _state_text(old_state, mode),
            _state_text(new_state, mode)))


def _run_due_sort():
    if not sort_jobs or sort_jobs[0]['due_ms'] > _now_ms():
        return
    job = sort_jobs.pop(0)
    try:
        result = sort_inventory()
        _event('Post-exchange sort_inventory(): %s' % result)
        if session is not None:
            session.setdefault('sort_calls', []).append({
                'time_ms': _now_ms(),
                'result': bool(result),
                'event_mode': job['mode'],
                'state_before': job['old_state'],
                'state_after': job['new_state'],
            })
    except Exception as ex:
        _event('sort_inventory error: %s' % ex)


def event_loop():
    global last_inventory, last_exchange_state
    global auto_stage, auto_due_ms, auto_cycles, auto_start_state
    _run_due_sort()
    _run_auto()
    _run_silkroad_box()
    if not is_recording and not auto_running:
        return
    snapshot = _inventory_snapshot()
    if snapshot is None:
        return
    mode = auto_mode if auto_running else recording_mode
    state = _exchange_state(snapshot, mode)
    _update_count(state, mode)
    if _inventory_signature(snapshot) == _inventory_signature(last_inventory):
        return

    old_state = last_exchange_state
    if is_recording and session is not None:
        session['inventory_changes'].append({
            'time_ms': _now_ms(),
            'event_mode': mode,
            'state_before': old_state,
            'state_after': state,
            'before': last_inventory,
            'after': snapshot,
        })
    _event('Inventory changed; %s -> %s' %
           (_state_text(old_state, mode), _state_text(state, mode)))
    auto_result = (
        auto_running and auto_stage in ('waiting_result', 'retry_prepare') and
        auto_start_state is not None and
        _state_consumed(auto_start_state, state, auto_mode)
    )
    queued_sort = _state_consumed(old_state, state, mode) and not auto_result
    if queued_sort:
        _queue_sort_for_break(old_state, state, mode)
    if auto_result:
        consumed = (_exchange_count(auto_start_state, auto_mode) -
                    _exchange_count(state, auto_mode))
        auto_cycles += 1
        _event('AUTO succeeded: %s %s exchanges consumed (cycle %s).' %
               (consumed, _mode_name(auto_mode), auto_cycles))
        auto_stage = 'closing'
        auto_due_ms = _now_ms() + 1700
        _set_status('Exchange complete; closing the NPC')
    last_inventory = snapshot
    last_exchange_state = state


def handle_silkroad(opcode, data):
    if is_recording:
        capture_all = _capture_all_enabled()
        if ((capture_all and opcode not in NOISY_CLIENT_OPCODES) or
                opcode in IMPORTANT_CLIENT_OPCODES):
            _record_packet('client_to_server', opcode, data)
            if opcode in IMPORTANT_CLIENT_OPCODES:
                _event('C>S 0x%04X (%s byte) %s' %
                       (opcode, len(data), _hex(data)))
    return True


def handle_joymax(opcode, data):
    global auto_sort_last_activity_ms
    if auto_running and auto_stage == 'sorting_wait' and opcode == 0xB034:
        auto_sort_last_activity_ms = _now_ms()
    if is_recording:
        # Save known event/inventory replies plus Bxxx replies matching any
        # recorded client opcode. This keeps files useful without logging the
        # entire high-volume server stream.
        wanted = opcode in IMPORTANT_SERVER_OPCODES
        if not wanted and session is not None and (opcode & 0xF000) == 0xB000:
            # Standard response mapping is 0x7xxx -> 0xBxxx.
            request_opcode = opcode - 0x4000
            wanted = any(packet.get('opcode') == '0x%04X' % request_opcode
                         for packet in session.get('packets', []))
        if wanted:
            _record_packet('server_to_client', opcode, data)
            _event('S>C 0x%04X (%s byte) %s' %
                   (opcode, len(data), _hex(data)))
    return True


log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
