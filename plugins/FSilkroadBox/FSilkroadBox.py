from phBot import *
import QtBind
import random
import struct
import threading
import time
import webbrowser

pName = 'FSilkroadBox'
pVersion = '1.1.2'
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

# Captured from the iSRO F10 flow supplied with this feature request.
ISRO_LOCALE = 18
ISRO_PURCHASE_REQUEST = 0x755D
ISRO_PURCHASE_RESPONSE = 0xB55D
RESPONSE_TIMEOUT_MS = 10000
INVENTORY_SETTLE_MS = 1000
NEXT_PURCHASE_MS = 700
PAGE_ALL = 'Open all pages'
ORDER_SEQUENTIAL = 'Sequential'
ORDER_RANDOM = 'Random'


def fixed_width_text(content, width):
    return ('<table width="{0}" cellspacing="0" cellpadding="0">'
            '<tr><td>{1}</td></tr></table>').format(width, content)


gui = QtBind.init(__name__, pName)
QtBind.createLabel(gui, u'<font color="%s" size="4"><b>\U0001f4e6 %s</b></font>' %
                   (COLOR_PRIMARY, pName), 12, 6)
QtBind.createLabel(gui, '<font color="%s">v%s</font>' %
                   (COLOR_MUTED, pVersion), 190, 12)
QtBind.createButton(gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(gui, u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' %
                   COLOR_PRIMARY, 565, 11)
QtBind.createLineEdit(gui, '', 12, 32, 696, 1)

QtBind.createLabel(gui, '<font color="%s"><b>BOX OPENING</b></font>' %
                   COLOR_PRIMARY, 12, 52)
QtBind.createLabel(gui, 'Inventory page:', 12, 79)
cmb_page = QtBind.createCombobox(gui, 125, 75, 205, 22)
QtBind.createLabel(gui, 'Opening order:', 12, 109)
cmb_order = QtBind.createCombobox(gui, 125, 105, 205, 22)
QtBind.append(gui, cmb_order, ORDER_SEQUENTIAL)
QtBind.append(gui, cmb_order, ORDER_RANDOM)
QtBind.createLabel(gui, 'Opening delay:', 12, 139)
txt_delay = QtBind.createLineEdit(gui, str(DEFAULT_DELAY_MS), 125, 135, 75, 22)
QtBind.createLabel(gui, '<font color="%s">ms</font>' % COLOR_MUTED, 205, 139)
QtBind.createButton(gui, 'refresh_clicked', 'Refresh Pages', 12, 170)
QtBind.createButton(gui, 'start_clicked', 'Start Opening', 125, 170)
QtBind.createButton(gui, 'stop_clicked', 'Stop', 245, 170)

QtBind.createLineEdit(gui, '', 355, 52, 1, 153)
QtBind.createLabel(gui, '<font color="%s"><b>iSRO PURCHASE & OPEN</b></font>' %
                   COLOR_PRIMARY, 375, 52)
QtBind.createLabel(gui, 'Quantity / cycle:', 375, 79)
txt_purchase_count = QtBind.createLineEdit(gui, '1', 505, 75, 70, 22)
QtBind.createLabel(gui, 'Cycle limit:', 375, 109)
txt_cycle_limit = QtBind.createLineEdit(gui, '0', 505, 105, 70, 22)
QtBind.createLabel(gui, '<font color="%s">0 = infinite</font>' % COLOR_MUTED,
                   580, 109)
QtBind.createLabel(gui, 'Opening delay:', 375, 139)
txt_purchase_delay = QtBind.createLineEdit(gui, str(DEFAULT_DELAY_MS), 505, 135, 70, 22)
QtBind.createLabel(gui, '<font color="%s">ms</font>' % COLOR_MUTED, 580, 139)
QtBind.createButton(gui, 'purchase_start_clicked', 'Start Loop', 375, 170)
QtBind.createButton(gui, 'purchase_stop_clicked', 'Stop Loop', 485, 170)
QtBind.createButton(gui, 'purchase_only_clicked', 'Buy Only', 585, 170)

QtBind.createLineEdit(gui, '', 12, 215, 696, 1)
lbl_status = QtBind.createLabel(gui, fixed_width_text(
    '<font color="%s">Ready</font>' % COLOR_MUTED, 696), 12, 226)
lbl_progress = QtBind.createLabel(gui, fixed_width_text(
    'Manual: 0 / 0 | iSRO cycles: 0 | purchases: 0', 696), 12, 248)
lst_activity = QtBind.createList(gui, 12, 270, 696, 29)

state_lock = threading.RLock()
timer = None
generation = 0
running = False
mode = None
slots = []
slot_index = 0
selected_delay_ms = DEFAULT_DELAY_MS
pending_ui = []

purchase_boxes = 0
purchase_limit = 0
purchase_cycle = 0
purchase_in_cycle = 0
purchase_total = 0
purchase_waiting = False
purchase_baseline = {}


def _queue(kind, value):
    with state_lock:
        pending_ui.append((kind, value))


def _set_status(text, color=COLOR_MUTED):
    QtBind.setText(gui, lbl_status, fixed_width_text(
        '<font color="%s"><b>%s</b></font>' % (color, str(text)), 696))


def _set_progress():
    limit = 'infinite' if purchase_limit == 0 else str(purchase_limit)
    QtBind.setText(gui, lbl_progress, fixed_width_text(
        'Manual: %s / %s | iSRO cycles: %s / %s | purchases: %s' %
        (slot_index, len(slots), purchase_cycle, limit, purchase_total), 696))


def _activity(text):
    text = str(text)
    log('[%s] %s' % (pName, text))
    QtBind.append(gui, lst_activity, '%s  %s' % (time.strftime('%H:%M:%S'), text))
    items = QtBind.getItems(gui, lst_activity)
    if items and len(items) > 80:
        QtBind.removeAt(gui, lst_activity, 0)


def _inventory():
    try:
        data = get_inventory()
    except Exception as error:
        _set_status('Inventory could not be read', COLOR_ERROR)
        _activity('Inventory read error: %s' % error)
        return None
    if not data or not isinstance(data.get('items'), list):
        _set_status('Join the game before scanning', COLOR_WARNING)
        return None
    return data


def _quantity(item):
    try:
        return max(1, int(item.get('quantity', 1) or 1))
    except Exception:
        return 1


def _is_box(item):
    return isinstance(item, dict) and str(item.get('servername') or '').lower() == \
        SILKROAD_BOX_SERVERNAME.lower()


def _page_for_slot(slot):
    if slot < INVENTORY_FIRST_SLOT:
        return 0
    return ((slot - INVENTORY_FIRST_SLOT) // INVENTORY_PAGE_SIZE) + 1


def _box_quantities(inventory, page=None):
    result = {}
    for slot, item in enumerate(inventory.get('items', [])):
        if _is_box(item) and (page is None or _page_for_slot(slot) == page):
            result[slot] = _quantity(item)
    return result


def _slots_from_quantities(quantities):
    result = []
    for slot, quantity in quantities.items():
        result.extend([slot] * quantity)
    return result


def _new_box_slots(inventory, baseline):
    result = []
    for slot, quantity in _box_quantities(inventory).items():
        result.extend([slot] * max(0, quantity - baseline.get(slot, 0)))
    return result


def _read_positive(widget, allow_zero=False):
    try:
        value = int(str(QtBind.text(gui, widget) or '').strip())
    except Exception:
        return None
    if value < 0 or (not allow_zero and value == 0):
        return None
    return value


def _read_delay(widget):
    value = _read_positive(widget)
    if value is None or value < MIN_DELAY_MS or value > MAX_DELAY_MS:
        return None
    return value


def _selected_page():
    value = str(QtBind.text(gui, cmb_page) or PAGE_ALL)
    if value == PAGE_ALL:
        return None
    try:
        return int(value.split()[-1])
    except Exception:
        return None


def _refresh_pages(log_result=False):
    inventory = _inventory()
    if inventory is None:
        return False
    usable = max(0, int(inventory.get('size', 0) or 0) - INVENTORY_FIRST_SLOT)
    pages = (usable + INVENTORY_PAGE_SIZE - 1) // INVENTORY_PAGE_SIZE if usable else 0
    QtBind.clear(gui, cmb_page)
    QtBind.append(gui, cmb_page, PAGE_ALL)
    for page in range(1, pages + 1):
        QtBind.append(gui, cmb_page, 'Open page %s' % page)
    if log_result:
        _activity('Inventory scanned: %s page(s), %s box(es).' %
                  (pages, len(_slots_from_quantities(_box_quantities(inventory)))))
    return True


def _cancel_timer():
    global timer
    if timer:
        try:
            timer.cancel()
        except Exception:
            pass
    timer = None


def _schedule(delay_ms, callback, current_generation):
    global timer
    timer = threading.Timer(delay_ms / 1000.0, callback, (current_generation,))
    timer.daemon = True
    timer.start()


def _finish(message, color):
    global running, mode, timer, purchase_waiting
    running = False
    mode = None
    timer = None
    purchase_waiting = False
    _queue('status', (message, color))
    _queue('progress', None)
    _queue('activity', message)


def _open_step(current_generation):
    global slot_index
    with state_lock:
        if not running or current_generation != generation:
            return
        if slot_index >= len(slots):
            if mode == 'purchase':
                _purchase_boxes_opened(current_generation)
            else:
                _finish('Completed: %s box(es) opened' % len(slots), COLOR_SUCCESS)
            return
        slot = slots[slot_index]
        try:
            inject_joymax(0x704C, struct.pack('<B', slot) + SILKROAD_BOX_USE_TAIL, True)
        except Exception as error:
            _finish('Opening packet error - task stopped', COLOR_ERROR)
            _queue('activity', 'Opening packet error at slot %s: %s' % (slot, error))
            return
        slot_index += 1
        _queue('status', ('Opening box %s of %s' % (slot_index, len(slots)), COLOR_WARNING))
        _queue('progress', None)
        _schedule(selected_delay_ms, _open_step, current_generation)


def start_clicked():
    global running, mode, generation, slots, slot_index, selected_delay_ms
    if running:
        _set_status('Another task is already running', COLOR_WARNING)
        return
    delay = _read_delay(txt_delay)
    if delay is None:
        _set_status('Delay must be between 50 and 60000 ms', COLOR_ERROR)
        return
    inventory = _inventory()
    if inventory is None:
        return
    selected = _selected_page()
    opening_slots = _slots_from_quantities(_box_quantities(inventory, selected))
    if not opening_slots:
        _set_status('No Silkroad Boxes found in selected scope', COLOR_WARNING)
        return
    if str(QtBind.text(gui, cmb_order) or ORDER_SEQUENTIAL) == ORDER_RANDOM:
        random.shuffle(opening_slots)
    with state_lock:
        slots, slot_index, selected_delay_ms = opening_slots, 0, delay
        running, mode = True, 'manual'
        generation += 1
        current_generation = generation
    _set_progress()
    _set_status('Starting box opening...', COLOR_WARNING)
    _activity('Started manual opening of %s box(es).' % len(slots))
    _schedule(0, _open_step, current_generation)


def _purchase_request(current_generation):
    global purchase_waiting, purchase_baseline
    with state_lock:
        if (not running or mode not in ('purchase', 'purchase_only') or
                current_generation != generation):
            return
        inventory = _inventory()
        if inventory is None:
            _finish('Inventory unavailable - purchase loop stopped', COLOR_ERROR)
            return
        purchase_baseline = _box_quantities(inventory)
        purchase_waiting = True
        try:
            inject_joymax(ISRO_PURCHASE_REQUEST, b'', True)
        except Exception as error:
            _finish('Purchase packet error - loop stopped', COLOR_ERROR)
            _queue('activity', 'Purchase packet error: %s' % error)
            return
        _queue('status', ('iSRO F10 request %s/%s sent; waiting for response' %
                          (purchase_in_cycle + 1, purchase_boxes), COLOR_WARNING))
        _queue('activity', 'iSRO F10 purchase request sent.')
        _schedule(RESPONSE_TIMEOUT_MS, _purchase_timeout, current_generation)


def _purchase_timeout(current_generation):
    with state_lock:
        if (running and mode in ('purchase', 'purchase_only') and
                current_generation == generation and purchase_waiting):
            _finish('F10 response timed out - loop stopped', COLOR_ERROR)


def _check_purchased_box(current_generation):
    global purchase_waiting, slots, slot_index
    with state_lock:
        if not running or mode != 'purchase' or current_generation != generation:
            return
        purchase_waiting = False
        inventory = _inventory()
        if inventory is None:
            _finish('Inventory unavailable - purchase loop stopped', COLOR_ERROR)
            return
        new_slots = _new_box_slots(inventory, purchase_baseline)
        if not new_slots:
            _finish('No new Silkroad Box found - loop stopped', COLOR_ERROR)
            return
        slots, slot_index = new_slots, 0
        _queue('status', ('Purchase confirmed; opening %s new box(es)' %
                          len(new_slots), COLOR_SUCCESS))
        _queue('progress', None)
        _schedule(selected_delay_ms, _open_step, current_generation)


def _purchase_boxes_opened(current_generation):
    global purchase_in_cycle, purchase_total, purchase_cycle
    purchase_in_cycle += 1
    purchase_total += 1
    if purchase_in_cycle < purchase_boxes:
        _queue('progress', None)
        _schedule(NEXT_PURCHASE_MS, _purchase_request, current_generation)
        return
    purchase_cycle += 1
    purchase_in_cycle = 0
    _queue('progress', None)
    if purchase_limit and purchase_cycle >= purchase_limit:
        _finish('Purchase loop completed', COLOR_SUCCESS)
    else:
        _schedule(NEXT_PURCHASE_MS, _purchase_request, current_generation)


def purchase_start_clicked():
    global running, mode, generation, selected_delay_ms, purchase_boxes
    global purchase_limit, purchase_cycle, purchase_in_cycle, purchase_total
    if get_locale() != ISRO_LOCALE:
        _set_status('Purchase loop requires iSRO locale 18', COLOR_ERROR)
        return
    boxes = _read_positive(txt_purchase_count)
    limit = _read_positive(txt_cycle_limit, True)
    delay = _read_delay(txt_purchase_delay)
    if boxes is None or limit is None:
        _set_status('Boxes must be >= 1; cycle limit must be >= 0', COLOR_ERROR)
        return
    if delay is None:
        _set_status('Delay must be between 50 and 60000 ms', COLOR_ERROR)
        return
    with state_lock:
        if running:
            _set_status('Another task is already running', COLOR_WARNING)
            return
        running, mode = True, 'purchase'
        selected_delay_ms = delay
        purchase_boxes, purchase_limit = boxes, limit
        purchase_cycle, purchase_in_cycle, purchase_total = 0, 0, 0
        generation += 1
        current_generation = generation
    _set_progress()
    _set_status('Starting iSRO F10 purchase loop...', COLOR_WARNING)
    _activity('Started iSRO purchase-and-open loop: %s request(s) per cycle, '
              '%s cycles.' % (boxes, 'infinite' if limit == 0 else limit))
    _schedule(0, _purchase_request, current_generation)


def purchase_only_clicked():
    global running, mode, generation, purchase_boxes, purchase_limit
    global purchase_cycle, purchase_in_cycle, purchase_total
    if get_locale() != ISRO_LOCALE:
        _set_status('Buy Only requires iSRO locale 18', COLOR_ERROR)
        return
    quantity = _read_positive(txt_purchase_count)
    if quantity is None:
        _set_status('Purchase quantity must be at least 1', COLOR_ERROR)
        return
    with state_lock:
        if running:
            _set_status('Another task is already running', COLOR_WARNING)
            return
        running, mode = True, 'purchase_only'
        purchase_boxes, purchase_limit = quantity, 1
        purchase_cycle, purchase_in_cycle, purchase_total = 0, 0, 0
        generation += 1
        current_generation = generation
    _set_progress()
    _set_status('Buying %s iSRO Silkroad Box(es)...' % quantity, COLOR_WARNING)
    _activity('Started iSRO Buy Only for %s purchase request(s).' % quantity)
    _schedule(0, _purchase_request, current_generation)


def _stop(message, color=COLOR_WARNING):
    global running, generation, purchase_waiting, mode
    with state_lock:
        was_running = running
        running, purchase_waiting, mode = False, False, None
        generation += 1
        _cancel_timer()
    if was_running:
        _set_status(message, color)
        _activity(message)


def stop_clicked():
    if running:
        _stop('Stopped by user')
    else:
        _set_status('Nothing is currently running', COLOR_MUTED)


def purchase_stop_clicked():
    stop_clicked()


def refresh_clicked():
    if running:
        _set_status('Stop the active task before refreshing', COLOR_WARNING)
    else:
        _refresh_pages(True)


def handle_joymax(opcode, data):
    global purchase_waiting
    if opcode != ISRO_PURCHASE_RESPONSE:
        return True
    with state_lock:
        if not (running and mode in ('purchase', 'purchase_only') and
                purchase_waiting):
            return True
        if not data or data[0] != 1:
            _finish('F10 purchase was rejected - loop stopped', COLOR_ERROR)
            return True
        current_generation = generation
        purchase_waiting = False
        _cancel_timer()
        if mode == 'purchase_only':
            _queue('status', ('F10 purchase confirmed (%s/%s)' %
                              (purchase_total + 1, purchase_boxes), COLOR_SUCCESS))
            _purchase_boxes_opened(current_generation)
            return True
        _queue('status', ('F10 response received; checking inventory', COLOR_SUCCESS))
        _schedule(INVENTORY_SETTLE_MS, _check_purchased_box, current_generation)
    return True


def event_loop():
    with state_lock:
        updates = list(pending_ui)
        del pending_ui[:]
    for kind, value in updates:
        if kind == 'status':
            _set_status(value[0], value[1])
        elif kind == 'progress':
            _set_progress()
        elif kind == 'activity':
            _activity(value)


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        _set_status('Opening Discord invite...', COLOR_SUCCESS)
    except Exception as error:
        log('[%s] Discord link error: %s' % (pName, error))
        _set_status('Could not open Discord invite', COLOR_ERROR)


def teleported():
    _refresh_pages(False)


def disconnected():
    if running:
        _stop('Disconnected - task stopped', COLOR_ERROR)


def finished():
    global running, generation, purchase_waiting, mode
    with state_lock:
        running, purchase_waiting, mode = False, False, None
        generation += 1
        _cancel_timer()


QtBind.append(gui, cmb_page, PAGE_ALL)
_refresh_pages(False)

log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
