from phBot import *
import QtBind

import random
import struct
import threading
import time
import webbrowser


pName = 'FSilkroadBox'
pVersion = '1.0.0'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

COLOR_PRIMARY = '#5b57e0'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#2e9d57'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#d64545'

SILKROAD_BOX_SERVERNAME = 'ITEM_PRE_MALL_SILKROAD_BOX'
SILKROAD_BOX_USE_TAIL = b'\x31\x0C\x0E\x05'
INVENTORY_FIRST_SLOT = 13
INVENTORY_PAGE_SIZE = 32
DEFAULT_DELAY_MS = 250
MIN_DELAY_MS = 50
MAX_DELAY_MS = 60000

PAGE_ALL = 'Open all pages'
ORDER_SEQUENTIAL = 'Sequential'
ORDER_RANDOM = 'Random'


def fixed_width_text(content, width):
    return (
        '<table width="{0}" cellspacing="0" cellpadding="0">'
        '<tr><td>{1}</td></tr></table>'
    ).format(width, content)


gui = QtBind.init(__name__, pName)

QtBind.createLabel(
    gui, u'<font color="%s" size="4"><b>\U0001f4e6 %s</b></font>' %
    (COLOR_PRIMARY, pName), 12, 6)
QtBind.createLabel(
    gui, '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion), 190, 12)
btn_discord = QtBind.createButton(
    gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(
    gui, u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' %
    COLOR_PRIMARY, 565, 11)
QtBind.createLineEdit(gui, '', 12, 32, 696, 1)

QtBind.createLabel(
    gui, '<font color="%s"><b>BOX OPENING</b></font>' % COLOR_PRIMARY,
    12, 52)
QtBind.createLabel(gui, 'Inventory page:', 12, 79)
cmb_page = QtBind.createCombobox(gui, 125, 75, 205, 22)
QtBind.createLabel(gui, 'Opening order:', 12, 109)
cmb_order = QtBind.createCombobox(gui, 125, 105, 205, 22)
QtBind.append(gui, cmb_order, ORDER_SEQUENTIAL)
QtBind.append(gui, cmb_order, ORDER_RANDOM)
QtBind.createLabel(gui, 'Opening delay:', 12, 139)
txt_delay = QtBind.createLineEdit(gui, str(DEFAULT_DELAY_MS), 125, 135, 75, 22)
QtBind.createLabel(gui, '<font color="%s">ms</font>' % COLOR_MUTED, 205, 139)

btn_refresh = QtBind.createButton(
    gui, 'refresh_clicked', 'Refresh Pages', 12, 170)
btn_start = QtBind.createButton(gui, 'start_clicked', 'Start', 125, 170)
btn_stop = QtBind.createButton(gui, 'stop_clicked', 'Stop', 205, 170)

QtBind.createLineEdit(gui, '', 355, 52, 1, 153)
QtBind.createLabel(
    gui, '<font color="%s"><b>LIVE STATUS</b></font>' % COLOR_PRIMARY,
    375, 52)
lbl_status = QtBind.createLabel(
    gui,
    fixed_width_text('<font color="%s">Ready</font>' % COLOR_MUTED, 320),
    375, 79)
lbl_progress = QtBind.createLabel(
    gui, fixed_width_text('Progress: 0 / 0', 320), 375, 106)
lbl_scope = QtBind.createLabel(
    gui, fixed_width_text('Pages: Not scanned', 320), 375, 133)
lbl_boxes = QtBind.createLabel(
    gui, fixed_width_text('Silkroad Boxes: Unknown', 320), 375, 160)
QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s">Only boxes present when Start is pressed are queued.</font>' %
        COLOR_MUTED, 320),
    375, 187)

QtBind.createLineEdit(gui, '', 12, 215, 696, 1)
QtBind.createLabel(
    gui, '<font color="%s"><b>ACTIVITY</b></font>' % COLOR_PRIMARY,
    12, 228)
lst_activity = QtBind.createList(gui, 12, 249, 696, 50)


state_lock = threading.RLock()
run_timer = None
run_generation = 0
running = False
slot_queue = []
queue_index = 0
opened_count = 0
selected_page = None
selected_order = ORDER_SEQUENTIAL
selected_delay_ms = DEFAULT_DELAY_MS
pending_ui = []


def _plain(value):
    return str(value or '').strip().lower()


def _now_text():
    return time.strftime('%H:%M:%S')


def _queue_ui(kind, value):
    with state_lock:
        pending_ui.append((kind, value))


def _set_status(text, color=COLOR_MUTED):
    QtBind.setText(
        gui, lbl_status,
        fixed_width_text('<font color="%s"><b>%s</b></font>' %
                         (color, str(text)), 320))


def _set_progress(current, total):
    QtBind.setText(
        gui, lbl_progress,
        fixed_width_text('Progress: %s / %s' % (current, total), 320))


def _log_activity(text):
    message = str(text)
    log('[%s] %s' % (pName, message))
    QtBind.append(gui, lst_activity, '%s  %s' % (_now_text(), message))
    items = QtBind.getItems(gui, lst_activity)
    if items and len(items) > 80:
        QtBind.removeAt(gui, lst_activity, 0)


def _inventory():
    try:
        inventory = get_inventory()
    except Exception as error:
        _set_status('Inventory could not be read', COLOR_ERROR)
        _log_activity('Inventory read error: %s' % error)
        return None
    if not inventory or not isinstance(inventory.get('items'), list):
        _set_status('Join the game before scanning', COLOR_WARNING)
        return None
    return inventory


def _page_count(inventory):
    size = int(inventory.get('size', 0) or 0)
    usable_slots = max(0, size - INVENTORY_FIRST_SLOT)
    if usable_slots <= 0:
        return 0
    return (usable_slots + INVENTORY_PAGE_SIZE - 1) // INVENTORY_PAGE_SIZE


def _page_for_slot(slot):
    if slot < INVENTORY_FIRST_SLOT:
        return 0
    return ((slot - INVENTORY_FIRST_SLOT) // INVENTORY_PAGE_SIZE) + 1


def _is_silkroad_box(item):
    return (isinstance(item, dict) and
            _plain(item.get('servername')) ==
            _plain(SILKROAD_BOX_SERVERNAME))


def _quantity(item):
    try:
        return max(1, int(item.get('quantity', 1) or 1))
    except Exception:
        return 1


def _box_slots(inventory, page=None):
    slots = []
    for slot, item in enumerate(inventory.get('items', [])):
        if not _is_silkroad_box(item):
            continue
        if page is not None and _page_for_slot(slot) != page:
            continue
        slots.extend([slot] * _quantity(item))
    return slots


def _selected_page_number():
    text = str(QtBind.text(gui, cmb_page) or PAGE_ALL)
    if text == PAGE_ALL:
        return None
    try:
        return int(text.split()[-1])
    except Exception:
        return None


def _read_delay():
    value = str(QtBind.text(gui, txt_delay) or '').strip()
    try:
        delay = int(value)
    except Exception:
        return None
    if delay < MIN_DELAY_MS or delay > MAX_DELAY_MS:
        return None
    return delay


def _refresh_pages(log_result=False):
    inventory = _inventory()
    if inventory is None:
        return False
    pages = _page_count(inventory)
    QtBind.clear(gui, cmb_page)
    QtBind.append(gui, cmb_page, PAGE_ALL)
    for page in range(1, pages + 1):
        QtBind.append(gui, cmb_page, 'Open page %d' % page)
    count = len(_box_slots(inventory))
    QtBind.setText(
        gui, lbl_scope,
        fixed_width_text('Pages: %s available' % pages, 320))
    QtBind.setText(
        gui, lbl_boxes,
        fixed_width_text('Silkroad Boxes: %s' % count, 320))
    if log_result:
        _log_activity('Inventory scanned: %s page(s), %s box(es).' %
                      (pages, count))
    return True


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        _set_status('Opening Discord invite...', COLOR_SUCCESS)
    except Exception as error:
        _set_status('Could not open Discord invite', COLOR_ERROR)
        log('[%s] Discord link error: %s' % (pName, error))


def refresh_clicked():
    if running:
        _set_status('Stop opening before refreshing', COLOR_WARNING)
        return
    _refresh_pages(True)


def _cancel_timer():
    global run_timer
    timer = run_timer
    run_timer = None
    if timer is not None:
        try:
            timer.cancel()
        except Exception:
            pass


def _schedule_next(generation, delay_ms):
    global run_timer
    timer = threading.Timer(delay_ms / 1000.0, _timer_step, (generation,))
    timer.daemon = True
    run_timer = timer
    timer.start()


def _finish_from_timer(message, color):
    global running, run_timer
    running = False
    run_timer = None
    _queue_ui('status', (message, color))
    _queue_ui('log', message)


def _timer_step(generation):
    global queue_index, opened_count, run_timer
    with state_lock:
        if not running or generation != run_generation:
            return
        if queue_index >= len(slot_queue):
            _finish_from_timer(
                'Completed: %s box(es) opened' % opened_count,
                COLOR_SUCCESS)
            return
        slot = slot_queue[queue_index]
        packet = struct.pack('<B', slot) + SILKROAD_BOX_USE_TAIL
        try:
            inject_joymax(0x704C, packet, True)
        except Exception as error:
            _finish_from_timer('Packet error - opening stopped', COLOR_ERROR)
            _queue_ui('log', 'Packet error at slot %s: %s' % (slot, error))
            return

        if not running or generation != run_generation:
            return
        queue_index += 1
        opened_count += 1
        current = opened_count
        total = len(slot_queue)
        _queue_ui('progress', (current, total))
        _queue_ui('status',
                  ('Opening box %s of %s (slot %s)' %
                   (current, total, slot), COLOR_WARNING))
        if queue_index >= total:
            _finish_from_timer(
                'Completed: %s box(es) opened' % opened_count,
                COLOR_SUCCESS)
        else:
            _schedule_next(generation, selected_delay_ms)


def start_clicked():
    global running, slot_queue, queue_index, opened_count
    global selected_page, selected_order, selected_delay_ms
    global run_generation

    with state_lock:
        if running:
            _set_status('Box opening is already running', COLOR_WARNING)
            return

    delay = _read_delay()
    if delay is None:
        _set_status('Delay must be between 50 and 60000 ms', COLOR_ERROR)
        return
    inventory = _inventory()
    if inventory is None:
        return

    selected_page = _selected_page_number()
    pages = _page_count(inventory)
    if selected_page is not None and selected_page > pages:
        _set_status('Selected inventory page is not available', COLOR_ERROR)
        _refresh_pages(False)
        return

    selected_order = str(QtBind.text(gui, cmb_order) or ORDER_SEQUENTIAL)
    selected_delay_ms = delay
    slots = _box_slots(inventory, selected_page)
    if not slots:
        scope = 'all pages' if selected_page is None else 'page %s' % selected_page
        _set_status('No Silkroad Boxes found in %s' % scope, COLOR_WARNING)
        _log_activity('No %s found in %s.' %
                      (SILKROAD_BOX_SERVERNAME, scope))
        return
    if selected_order == ORDER_RANDOM:
        random.shuffle(slots)

    with state_lock:
        _cancel_timer()
        slot_queue = slots
        queue_index = 0
        opened_count = 0
        running = True
        run_generation += 1
        generation = run_generation

    scope = 'all pages' if selected_page is None else 'page %s' % selected_page
    _set_progress(0, len(slots))
    _set_status('Starting box opening...', COLOR_WARNING)
    _log_activity(
        'Started: %s box(es), %s, %s order, %s ms delay.' %
        (len(slots), scope, selected_order.lower(), selected_delay_ms))
    _schedule_next(generation, 0)


def _stop(reason, color=COLOR_WARNING):
    global running, run_generation
    with state_lock:
        was_running = running
        running = False
        run_generation += 1
        _cancel_timer()
    if was_running:
        _set_status(reason, color)
        _log_activity('%s Progress: %s/%s.' %
                      (reason, opened_count, len(slot_queue)))


def stop_clicked():
    if not running:
        _set_status('Nothing is currently running', COLOR_MUTED)
        return
    _stop('Stopped by user')


def event_loop():
    with state_lock:
        updates = list(pending_ui)
        del pending_ui[:]
    for kind, value in updates:
        if kind == 'status':
            _set_status(value[0], value[1])
        elif kind == 'progress':
            _set_progress(value[0], value[1])
        elif kind == 'log':
            _log_activity(value)


def teleported():
    _refresh_pages(False)


def disconnected():
    if running:
        _stop('Disconnected - opening stopped', COLOR_ERROR)


def finished():
    global running, run_generation
    with state_lock:
        running = False
        run_generation += 1
        _cancel_timer()


QtBind.append(gui, cmb_page, PAGE_ALL)
_refresh_pages(False)

log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
