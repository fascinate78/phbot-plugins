from phBot import *
import QtBind
import struct
import threading
import time
import webbrowser


pName = 'FShining'
pVersion = '1.3.0'

DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

RECIPE_ID = 29
RECIPE_NAME = 'MK_RC_TRADE_MATERIAL_LIGHTSTONE'
REQUEST_OPCODE = 0x7538
RESPONSE_OPCODE = 0xB538
SPLIT_REQUEST_OPCODE = 0x7034
SPLIT_RESPONSE_OPCODE = 0xB034

DEFAULT_DELAY_MS = 250
MIN_DELAY_MS = 100
MAX_DELAY_MS = 60000
RESPONSE_TIMEOUT_SECONDS = 30.0
SPLIT_TIMEOUT_SECONDS = 10.0
INVENTORY_RETRY_LIMIT = 30
MATERIAL_RETRY_LIMIT = 10
RETRY_DELAY_SECONDS = 0.5

COLOR_PRIMARY = '#5b57e0'
COLOR_TEXT = '#2b3038'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#d93a4d'

state_lock = threading.Lock()
worker_generation = 0
active_session = None
active_split = None
active_split_job = None
runtime = {
    'running': False,
    'status': 'READY',
    'status_color': COLOR_MUTED,
    'detail': 'Enter a delay and press Start.',
    'requested_delay_ms': DEFAULT_DELAY_MS,
    'blue_slot': None,
    'black_slot': None,
    'sent_count': 0,
    'response_count': 0,
    'timeout_count': 0,
    'last_response_ms': None,
    'response_total_ms': 0.0,
    'split_status': 'Ready',
    'split_color': COLOR_MUTED
}


def fixed_width_text(content, width):
    return (
        '<table width="{0}" cellspacing="0" cellpadding="0">'
        '<tr><td>{1}</td></tr></table>'
    ).format(width, content)


# ______________________________ GUI ______________________________ #

gui = QtBind.init(__name__, pName)

QtBind.createLabel(
    gui,
    u'<font color="%s" size="4"><b>✨ %s</b></font>' %
    (COLOR_PRIMARY, pName),
    12,
    6
)
QtBind.createLabel(
    gui,
    '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion),
    158,
    12
)
discord_button = QtBind.createButton(
    gui,
    'discord_clicked',
    u'\U0001f4ac Discord',
    462,
    6
)
QtBind.createLabel(
    gui,
    u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' % COLOR_PRIMARY,
    565,
    11
)
QtBind.createLineEdit(gui, '', 12, 30, 716, 1)

QtBind.createLabel(
    gui,
    '<font color="%s"><b>CRAFT CONTROLS</b></font>' % COLOR_PRIMARY,
    12,
    43
)
QtBind.createLabel(
    gui,
    '<font color="%s">Sends one request at a time and waits for the server response.</font>' %
    COLOR_MUTED,
    12,
    64
)
QtBind.createLabel(gui, '<b>Requested delay</b>', 12, 96)
delay_edit = QtBind.createLineEdit(
    gui, str(DEFAULT_DELAY_MS), 132, 92, 78, 20
)
QtBind.createLabel(gui, 'ms', 216, 96)

start_button = QtBind.createButton(gui, 'start_clicked', 'Start Crafting', 12, 126)
stop_button = QtBind.createButton(gui, 'stop_clicked', 'Stop', 130, 126)

QtBind.createLineEdit(gui, '', 12, 164, 368, 1)
QtBind.createLabel(
    gui,
    '<font color="%s"><b>STACK SPLITTER</b></font>' % COLOR_PRIMARY,
    12,
    176
)
QtBind.createLabel(gui, '<b>Stone type</b>', 12, 205)
stone_type_combo = QtBind.createCombobox(gui, 88, 201, 112, 20)
QtBind.append(gui, stone_type_combo, 'Blue Stone')
QtBind.append(gui, stone_type_combo, 'Black Stone')
QtBind.setText(gui, stone_type_combo, 'Blue Stone')
QtBind.createLabel(gui, '<b>Amount</b>', 216, 205)
split_amount_edit = QtBind.createLineEdit(gui, '250', 272, 201, 68, 20)
split_button = QtBind.createButton(gui, 'split_clicked', 'Split Stack', 12, 234)
split_status_label = QtBind.createLabel(
    gui,
    fixed_width_text('<font color="%s">Ready</font>' % COLOR_MUTED, 250),
    128,
    238
)

QtBind.createLineEdit(gui, '', 400, 43, 1, 222)
QtBind.createLabel(
    gui,
    '<font color="%s"><b>LIVE STATUS</b></font>' % COLOR_PRIMARY,
    420,
    43
)

QtBind.createLabel(gui, '<font color="%s"><b>State</b></font>' % COLOR_MUTED, 420, 70)
state_label = QtBind.createLabel(gui, fixed_width_text('READY', 180), 540, 70)
QtBind.createLabel(gui, '<font color="%s"><b>Material slots</b></font>' % COLOR_MUTED, 420, 94)
slots_label = QtBind.createLabel(
    gui, fixed_width_text('Blue: - | Black: -', 180), 540, 94
)
QtBind.createLabel(gui, '<font color="%s"><b>Requested</b></font>' % COLOR_MUTED, 420, 118)
requested_label = QtBind.createLabel(gui, fixed_width_text('250 ms', 180), 540, 118)
QtBind.createLabel(gui, '<font color="%s"><b>Last response</b></font>' % COLOR_MUTED, 420, 142)
last_response_label = QtBind.createLabel(gui, fixed_width_text('-', 180), 540, 142)
QtBind.createLabel(gui, '<font color="%s"><b>Average</b></font>' % COLOR_MUTED, 420, 166)
average_response_label = QtBind.createLabel(gui, fixed_width_text('-', 180), 540, 166)
QtBind.createLabel(gui, '<font color="%s"><b>Effective interval</b></font>' % COLOR_MUTED, 420, 190)
effective_interval_label = QtBind.createLabel(
    gui, fixed_width_text('250 ms', 180), 540, 190
)
QtBind.createLabel(gui, '<font color="%s"><b>Requests</b></font>' % COLOR_MUTED, 420, 214)
request_count_label = QtBind.createLabel(
    gui, fixed_width_text('Sent: 0 | Responses: 0', 180), 540, 214
)
QtBind.createLabel(gui, '<font color="%s"><b>Timeouts</b></font>' % COLOR_MUTED, 420, 238)
timeout_label = QtBind.createLabel(gui, fixed_width_text('0', 180), 540, 238)

QtBind.createLineEdit(gui, '', 12, 278, 716, 1)
notice_label = QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s">Ready. No request has been sent.</font>' % COLOR_MUTED,
        700
    ),
    12,
    291
)


# ______________________________ Helpers ______________________________ #

def format_milliseconds(value):
    if value is None:
        return '-'
    if value >= 1000.0:
        return '{0:.3f} sec'.format(value / 1000.0)
    return '{0:.0f} ms'.format(value)


def runtime_snapshot():
    with state_lock:
        return dict(runtime)


def update_runtime(values):
    with state_lock:
        runtime.update(values)


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        update_runtime({
            'status': 'DISCORD',
            'status_color': COLOR_SUCCESS,
            'detail': 'Opening Discord invite...'
        })
    except Exception as error:
        log('[%s] Discord link error: %s' % (pName, error))
        update_runtime({
            'status': 'DISCORD ERROR',
            'status_color': COLOR_ERROR,
            'detail': 'Could not open Discord invite.'
        })
    refresh_gui()


def refresh_gui():
    snapshot = runtime_snapshot()
    requested = float(snapshot['requested_delay_ms'])
    last_response = snapshot['last_response_ms']
    response_count = snapshot['response_count']

    average = None
    if response_count > 0:
        average = snapshot['response_total_ms'] / response_count

    effective = requested
    if last_response is not None:
        effective = max(requested, last_response)

    blue_slot = snapshot['blue_slot']
    black_slot = snapshot['black_slot']
    blue_text = '-' if blue_slot is None else str(blue_slot)
    black_text = '-' if black_slot is None else str(black_slot)

    QtBind.setText(
        gui,
        state_label,
        fixed_width_text(
            '<font color="{0}"><b>{1}</b></font>'.format(
                snapshot['status_color'], snapshot['status']
            ),
            180
        )
    )
    QtBind.setText(
        gui,
        slots_label,
        fixed_width_text(
            'Blue: {0} | Black: {1}'.format(blue_text, black_text), 180
        )
    )
    QtBind.setText(
        gui, requested_label,
        fixed_width_text(format_milliseconds(requested), 180)
    )
    QtBind.setText(
        gui, last_response_label,
        fixed_width_text(format_milliseconds(last_response), 180)
    )
    QtBind.setText(
        gui, average_response_label,
        fixed_width_text(format_milliseconds(average), 180)
    )
    QtBind.setText(
        gui, effective_interval_label,
        fixed_width_text(format_milliseconds(effective), 180)
    )
    QtBind.setText(
        gui,
        request_count_label,
        fixed_width_text(
            'Sent: {0} | Responses: {1}'.format(
                snapshot['sent_count'], response_count
            ),
            180
        )
    )
    QtBind.setText(
        gui, timeout_label,
        fixed_width_text(str(snapshot['timeout_count']), 180)
    )
    QtBind.setText(
        gui,
        split_status_label,
        fixed_width_text(
            '<font color="{0}">{1}</font>'.format(
                snapshot['split_color'], snapshot['split_status']
            ),
            250
        )
    )

    if last_response is not None and last_response > requested:
        notice = (
            '<font color="{0}"><b>Server synchronization active:</b> '
            'requested {1}, server response {2}. No extra requests are sent '
            'while a response is pending.</font>'
        ).format(
            COLOR_WARNING,
            format_milliseconds(requested),
            format_milliseconds(last_response)
        )
    else:
        notice = '<font color="{0}">{1}</font>'.format(
            snapshot['status_color'], snapshot['detail']
        )
    QtBind.setText(gui, notice_label, fixed_width_text(notice, 700))


def read_requested_delay():
    try:
        delay_ms = int(QtBind.text(gui, delay_edit).strip())
    except Exception:
        return None
    if delay_ms < MIN_DELAY_MS or delay_ms > MAX_DELAY_MS:
        return None
    return delay_ms


def find_material_slots():
    inventory = get_inventory()
    if not isinstance(inventory, dict):
        return None
    items = inventory.get('items')
    if not isinstance(items, list):
        return None

    blue_slot = None
    black_slot = None
    for slot in range(13, len(items)):
        item = items[slot]
        if not isinstance(item, dict):
            continue
        try:
            quantity = int(item.get('quantity', 0))
        except Exception:
            quantity = 0
        if quantity <= 0:
            continue

        servername = str(item.get('servername') or '').upper()
        if blue_slot is None and (
            'BLUESTONE' in servername or 'BLUE_STONE' in servername
        ):
            blue_slot = slot
        if black_slot is None and (
            'BLACKSTONE' in servername or 'BLACK_STONE' in servername
        ):
            black_slot = slot
        if blue_slot is not None and black_slot is not None:
            break
    return blue_slot, black_slot


def stone_matches(servername, stone_type):
    name = str(servername or '').upper()
    if stone_type == 'Blue Stone':
        return 'BLUESTONE' in name or 'BLUE_STONE' in name
    if stone_type == 'Black Stone':
        return 'BLACKSTONE' in name or 'BLACK_STONE' in name
    return False


def inventory_item_is_empty(item):
    if not item:
        return True
    if not isinstance(item, dict):
        return False

    servername = str(item.get('servername') or '').strip()
    try:
        model = int(item.get('model') or 0)
    except Exception:
        model = 0
    return model == 0 and not servername


def find_split_plan(stone_type, amount, source_slot=None):
    inventory = get_inventory()
    if not isinstance(inventory, dict):
        return None, 'Inventory is not available.'
    items = inventory.get('items')
    if not isinstance(items, list):
        return None, 'Inventory is not available.'

    candidates = []
    empty_slots = []
    for slot in range(13, len(items)):
        item = items[slot]
        if inventory_item_is_empty(item):
            empty_slots.append(slot)
            continue
        if not isinstance(item, dict):
            continue
        try:
            quantity = int(item.get('quantity', 0))
        except Exception:
            quantity = 0
        if (
            quantity > amount
            and stone_matches(item.get('servername'), stone_type)
            and (source_slot is None or slot == source_slot)
        ):
            candidates.append((quantity, slot))

    # Some phBot builds omit trailing empty entries from the items list while
    # still reporting the complete inventory capacity in the size field.
    try:
        inventory_size = int(inventory.get('size', len(items)))
    except Exception:
        inventory_size = len(items)
    inventory_size = min(256, max(len(items), inventory_size))
    for slot in range(max(13, len(items)), inventory_size):
        empty_slots.append(slot)

    if not candidates:
        return None, 'No {0} stack larger than {1} was found.'.format(
            stone_type, amount
        )
    if not empty_slots:
        return None, 'No empty inventory slot is available.'

    candidates.sort(reverse=True)
    quantity, source_slot = candidates[0]
    destination_slot = empty_slots[0]
    if source_slot > 255 or destination_slot > 255:
        return None, 'The selected inventory slot is outside the packet range.'

    return {
        'stone_type': stone_type,
        'amount': amount,
        'source_quantity': quantity,
        'source_slot': source_slot,
        'destination_slot': destination_slot
    }, None


def build_split_packet(source_slot, destination_slot, amount):
    return bytearray(struct.pack(
        '<BBBH', 0x00, source_slot, destination_slot, amount
    ))


def build_craft_packet(blue_slot, black_slot):
    recipe_name = RECIPE_NAME.encode('ascii')
    packet = bytearray()
    packet.append(0x01)
    packet.extend(struct.pack('<I', RECIPE_ID))
    packet.extend(struct.pack('<H', len(recipe_name)))
    packet.extend(recipe_name)
    packet.append(0x02)
    packet.append(blue_slot)
    packet.append(black_slot)
    packet.append(0x01)
    return packet


def session_is_active(generation, session):
    with state_lock:
        return (
            runtime['running']
            and worker_generation == generation
            and active_session is session
        )


def stop_session(
    status,
    detail,
    color,
    log_message=None,
    expected_generation=None,
    expected_session=None
):
    global worker_generation
    global active_session

    with state_lock:
        if expected_generation is not None and (
            worker_generation != expected_generation
            or active_session is not expected_session
        ):
            return False
        session = active_session
        runtime['running'] = False
        runtime['status'] = status
        runtime['status_color'] = color
        runtime['detail'] = detail
        worker_generation += 1
        active_session = None

    if session is not None:
        session['stop_event'].set()
        session['response_event'].set()
    if log_message:
        log('[%s] %s' % (pName, log_message))
    return True


# ______________________________ Worker ______________________________ #

def crafting_worker(generation, session):
    inventory_retries = 0
    material_retries = 0

    while session_is_active(generation, session):
        try:
            slots = find_material_slots()
        except Exception as error:
            inventory_retries += 1
            update_runtime({
                'status': 'WAITING FOR INVENTORY',
                'status_color': COLOR_WARNING,
                'detail': 'Inventory read failed ({0}/{1}).'.format(
                    inventory_retries, INVENTORY_RETRY_LIMIT
                )
            })
            if inventory_retries >= INVENTORY_RETRY_LIMIT:
                stop_session(
                    'ERROR',
                    'Inventory could not be read.',
                    COLOR_ERROR,
                    'Stopped because inventory could not be read: {0}'.format(error),
                    generation,
                    session
                )
                return
            session['stop_event'].wait(RETRY_DELAY_SECONDS)
            continue

        if slots is None:
            inventory_retries += 1
            update_runtime({
                'status': 'WAITING FOR INVENTORY',
                'status_color': COLOR_WARNING,
                'detail': 'Inventory is not available ({0}/{1}).'.format(
                    inventory_retries, INVENTORY_RETRY_LIMIT
                )
            })
            if inventory_retries >= INVENTORY_RETRY_LIMIT:
                stop_session(
                    'ERROR', 'Inventory is not available.', COLOR_ERROR,
                    'Stopped because inventory was not available.',
                    generation,
                    session
                )
                return
            session['stop_event'].wait(RETRY_DELAY_SECONDS)
            continue

        inventory_retries = 0
        blue_slot, black_slot = slots
        update_runtime({'blue_slot': blue_slot, 'black_slot': black_slot})

        if blue_slot is None or black_slot is None:
            material_retries += 1
            update_runtime({
                'status': 'SEARCHING MATERIALS',
                'status_color': COLOR_WARNING,
                'detail': 'Blue or Black Stone is missing ({0}/{1}).'.format(
                    material_retries, MATERIAL_RETRY_LIMIT
                )
            })
            if material_retries >= MATERIAL_RETRY_LIMIT:
                stop_session(
                    'MATERIALS DEPLETED',
                    'Blue or Black Stone could not be found.',
                    COLOR_WARNING,
                    'Stopped because Blue or Black Stone could not be found.',
                    generation,
                    session
                )
                return
            session['stop_event'].wait(RETRY_DELAY_SECONDS)
            continue

        material_retries = 0
        if not session_is_active(generation, session):
            return

        session['response_event'].clear()
        session['response_time_ms'] = None
        session['sent_at'] = time.monotonic()
        session['awaiting_response'] = True

        try:
            inject_joymax(
                REQUEST_OPCODE,
                build_craft_packet(blue_slot, black_slot),
                False
            )
        except Exception as error:
            session['awaiting_response'] = False
            stop_session(
                'ERROR', 'The craft request could not be sent.', COLOR_ERROR,
                'Craft request failed: {0}'.format(error),
                generation,
                session
            )
            return

        with state_lock:
            runtime['sent_count'] += 1
            runtime['status'] = 'WAITING FOR SERVER'
            runtime['status_color'] = COLOR_WARNING
            runtime['detail'] = 'One request is pending. No additional packet will be sent.'

        response_received = session['response_event'].wait(
            RESPONSE_TIMEOUT_SECONDS
        )
        if not session_is_active(generation, session):
            return

        if not response_received or session['response_time_ms'] is None:
            session['awaiting_response'] = False
            with state_lock:
                runtime['timeout_count'] += 1
            stop_session(
                'RESPONSE TIMEOUT',
                'No server response was received within {0:.0f} seconds.'.format(
                    RESPONSE_TIMEOUT_SECONDS
                ),
                COLOR_ERROR,
                'Stopped after waiting {0:.0f} seconds for opcode 0x{1:04X}.'.format(
                    RESPONSE_TIMEOUT_SECONDS, RESPONSE_OPCODE
                ),
                generation,
                session
            )
            return

        elapsed_seconds = session['response_time_ms'] / 1000.0
        requested_seconds = session['requested_delay_ms'] / 1000.0
        remaining_delay = max(0.0, requested_seconds - elapsed_seconds)

        update_runtime({
            'status': 'SYNCHRONIZED',
            'status_color': COLOR_SUCCESS,
            'detail': 'Server response received. Preparing the next request.'
        })
        if remaining_delay > 0:
            session['stop_event'].wait(remaining_delay)


# ______________________________ GUI callbacks ______________________________ #

def set_split_status(message, color):
    update_runtime({'split_status': message, 'split_color': color})
    refresh_gui()


def send_split_plan(plan, job):
    global active_split
    global active_split_job

    with state_lock:
        if (
            runtime['running']
            or active_split is not None
            or active_split_job is not job
        ):
            return False
        plan['sent_at'] = time.monotonic()
        active_split = plan
        runtime['split_status'] = 'Waiting: split #{0} | Slot {1} -> {2}'.format(
            job['completed_count'] + 1,
            plan['source_slot'],
            plan['destination_slot']
        )
        runtime['split_color'] = COLOR_WARNING

    try:
        inject_joymax(
            SPLIT_REQUEST_OPCODE,
            build_split_packet(
                plan['source_slot'], plan['destination_slot'], plan['amount']
            ),
            False
        )
    except Exception as error:
        with state_lock:
            if active_split is plan:
                active_split = None
            if active_split_job is job:
                active_split_job = None
            runtime['split_status'] = 'Split request could not be sent.'
            runtime['split_color'] = COLOR_ERROR
        log('[%s] Split request failed: %s' % (pName, error))
        return False

    log(
        '[%s] Split request #%d sent: %s x%d, slot %d -> %d.' % (
            pName,
            job['completed_count'] + 1,
            plan['stone_type'],
            plan['amount'],
            plan['source_slot'],
            plan['destination_slot']
        )
    )
    return True


def split_clicked():
    global active_split
    global active_split_job

    stone_type = QtBind.text(gui, stone_type_combo).strip()
    if stone_type not in ('Blue Stone', 'Black Stone'):
        set_split_status('Select Blue Stone or Black Stone.', COLOR_ERROR)
        return

    try:
        amount = int(QtBind.text(gui, split_amount_edit).strip())
    except Exception:
        set_split_status('Amount must be a whole number.', COLOR_ERROR)
        return
    if amount < 1 or amount > 65535:
        set_split_status('Amount must be between 1 and 65535.', COLOR_ERROR)
        return

    with state_lock:
        if runtime['running']:
            busy_message = 'Stop crafting before splitting a stack.'
        elif active_split is not None or active_split_job is not None:
            busy_message = 'A split operation is already active.'
        else:
            busy_message = None
    if busy_message:
        set_split_status(busy_message, COLOR_WARNING)
        return

    try:
        plan, error_message = find_split_plan(stone_type, amount)
    except Exception as error:
        set_split_status('Inventory could not be read.', COLOR_ERROR)
        log('[%s] Split inventory error: %s' % (pName, error))
        return
    if plan is None:
        set_split_status(error_message, COLOR_ERROR)
        return

    with state_lock:
        if runtime['running'] or active_split is not None or active_split_job is not None:
            job = None
        else:
            job = {
                'stone_type': stone_type,
                'amount': amount,
                'source_slot': plan['source_slot'],
                'completed_count': 0,
                'next_attempt_at': 0.0
            }
            active_split_job = job

    if job is None:
        set_split_status('Another operation started. Try again.', COLOR_WARNING)
        return

    send_split_plan(plan, job)
    refresh_gui()


def start_clicked():
    global worker_generation
    global active_session

    delay_ms = read_requested_delay()
    if delay_ms is None:
        update_runtime({
            'status': 'INVALID DELAY',
            'status_color': COLOR_ERROR,
            'detail': 'Delay must be a whole number between {0} and {1} ms.'.format(
                MIN_DELAY_MS, MAX_DELAY_MS
            )
        })
        refresh_gui()
        return

    with state_lock:
        if runtime['running']:
            return
        if active_split is not None or active_split_job is not None:
            runtime['status'] = 'SPLIT IN PROGRESS'
            runtime['status_color'] = COLOR_WARNING
            runtime['detail'] = 'Wait for the pending split request to finish.'
            refresh_required = True
        else:
            refresh_required = False
        if refresh_required:
            generation = None
            session = None
        else:
            worker_generation += 1
            generation = worker_generation
            session = {
                'stop_event': threading.Event(),
                'response_event': threading.Event(),
                'requested_delay_ms': delay_ms,
                'sent_at': None,
                'response_time_ms': None,
                'awaiting_response': False
            }
            active_session = session
            runtime.update({
                'running': True,
                'status': 'STARTING',
                'status_color': COLOR_WARNING,
                'detail': 'Reading inventory and locating materials.',
                'requested_delay_ms': delay_ms,
                'blue_slot': None,
                'black_slot': None,
                'sent_count': 0,
                'response_count': 0,
                'timeout_count': 0,
                'last_response_ms': None,
                'response_total_ms': 0.0
            })

    if refresh_required:
        refresh_gui()
        return

    worker = threading.Thread(target=crafting_worker, args=(generation, session))
    worker.daemon = True
    worker.start()
    log('[%s] Crafting started with a requested delay of %d ms.' % (pName, delay_ms))
    refresh_gui()


def stop_clicked():
    snapshot = runtime_snapshot()
    if not snapshot['running']:
        return
    stop_session(
        'STOPPED', 'Crafting was stopped by the user.', COLOR_MUTED,
        'Crafting stopped. Sent: {0}, responses: {1}.'.format(
            snapshot['sent_count'], snapshot['response_count']
        )
    )
    refresh_gui()


# ______________________________ phBot events ______________________________ #

def handle_joymax(opcode, data):
    global active_split
    global active_split_job

    if opcode == SPLIT_RESPONSE_OPCODE:
        try:
            response = bytearray(data)
        except Exception:
            return True

        with state_lock:
            plan = active_split
            if plan is None or len(response) < 6:
                return True

            response_operation = response[1]
            response_source = response[2]
            response_destination = response[3]
            response_amount = struct.unpack_from('<H', response, 4)[0]
            if (
                response_operation != 0x00
                or response_source != plan['source_slot']
                or response_destination != plan['destination_slot']
                or response_amount != plan['amount']
            ):
                return True

            success = response[0] == 0x01
            active_split = None
            if success:
                job = active_split_job
                if job is not None and job['source_slot'] == plan['source_slot']:
                    job['completed_count'] += 1
                    job['next_attempt_at'] = time.monotonic() + RETRY_DELAY_SECONDS
                    completed_count = job['completed_count']
                else:
                    completed_count = 1
                runtime['split_status'] = 'Split #{0} completed. Checking source...'.format(
                    completed_count
                )
                runtime['split_color'] = COLOR_SUCCESS
            else:
                active_split_job = None
                runtime['split_status'] = 'Split rejected by the server.'
                runtime['split_color'] = COLOR_ERROR

        if success:
            log('[%s] Stack split completed.' % pName)
        else:
            log('[%s] Stack split was rejected by the server.' % pName)
        return True

    if opcode != RESPONSE_OPCODE:
        return True

    with state_lock:
        session = active_session
        if (
            not runtime['running']
            or session is None
            or not session['awaiting_response']
            or session['sent_at'] is None
        ):
            return True

        response_ms = max(0.0, (time.monotonic() - session['sent_at']) * 1000.0)
        session['response_time_ms'] = response_ms
        session['awaiting_response'] = False
        runtime['last_response_ms'] = response_ms
        runtime['response_total_ms'] += response_ms
        runtime['response_count'] += 1
        response_event = session['response_event']

    response_event.set()
    return True


def event_loop():
    global active_split
    global active_split_job

    with state_lock:
        plan = active_split
        if (
            plan is not None
            and time.monotonic() - plan['sent_at'] >= SPLIT_TIMEOUT_SECONDS
        ):
            active_split = None
            active_split_job = None
            runtime['split_status'] = 'Split timed out after {0:.0f} seconds.'.format(
                SPLIT_TIMEOUT_SECONDS
            )
            runtime['split_color'] = COLOR_ERROR
            split_timed_out = True
        else:
            split_timed_out = False
        if (
            not split_timed_out
            and active_split is None
            and active_split_job is not None
            and time.monotonic() >= active_split_job['next_attempt_at']
        ):
            continuation_job = active_split_job
        else:
            continuation_job = None

    if split_timed_out:
        log('[%s] Split request timed out.' % pName)

    if continuation_job is not None:
        try:
            next_plan, error_message = find_split_plan(
                continuation_job['stone_type'],
                continuation_job['amount'],
                continuation_job['source_slot']
            )
        except Exception as error:
            next_plan = None
            error_message = 'Inventory could not be read.'
            log('[%s] Split continuation inventory error: %s' % (pName, error))

        if next_plan is not None:
            send_split_plan(next_plan, continuation_job)
        else:
            with state_lock:
                if active_split_job is continuation_job and active_split is None:
                    active_split_job = None
                    if error_message.startswith('No '):
                        runtime['split_status'] = (
                            'Completed: {0} split(s); source is now x{1} or less.'
                        ).format(
                            continuation_job['completed_count'],
                            continuation_job['amount']
                        )
                        runtime['split_color'] = COLOR_SUCCESS
                        split_finished = True
                    else:
                        runtime['split_status'] = error_message
                        runtime['split_color'] = COLOR_ERROR
                        split_finished = False
                else:
                    split_finished = False
            if split_finished:
                log(
                    '[%s] Automatic splitting completed after %d split(s).' % (
                        pName, continuation_job['completed_count']
                    )
                )
    refresh_gui()


def cancel_split(message):
    global active_split
    global active_split_job

    with state_lock:
        if active_split is None and active_split_job is None:
            return False
        active_split = None
        active_split_job = None
        runtime['split_status'] = message
        runtime['split_color'] = COLOR_ERROR
    return True


def disconnected():
    cancel_split('Split cancelled: connection lost.')
    if runtime_snapshot()['running']:
        stop_session(
            'DISCONNECTED', 'Crafting stopped because the connection was lost.',
            COLOR_ERROR, 'Crafting stopped after disconnect.'
        )


def finished():
    cancel_split('Split cancelled: plugin unloaded.')
    if runtime_snapshot()['running']:
        stop_session(
            'STOPPED', 'Plugin unloaded.', COLOR_MUTED,
            'Crafting stopped because the plugin was unloaded.'
        )


refresh_gui()
log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
