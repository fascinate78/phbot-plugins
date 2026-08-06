from phBot import *
import QtBind
import json
import os
import struct
import time


pName = 'FSroRAutoTrade'
pVersion = '2.0.1'
pUrl = ''

EVENT_TRANSPORT_DIED = 3
EVENT_DIED = 7

STATE_IDLE = 'IDLE'
STATE_RETURNING = 'RETURNING'
STATE_LEAVING_PARTY = 'LEAVING_PARTY'
STATE_EQUIPPING = 'EQUIPPING'
STATE_RUNNING_TRADE = 'RUNNING_TRADE'
STATE_PREPARING_GRIND = 'PREPARING_GRIND'
STATE_UNEQUIPPING = 'UNEQUIPPING'
STATE_WAITING_ACTION = 'WAITING_ACTION'
STATE_SETTLING_POUCH = 'SETTLING_POUCH'
STATE_DEATH_RECOVERY = 'DEATH_RECOVERY'
STATE_ERROR = 'ERROR'

POLL_SECONDS = 1.0
RETURN_TIMEOUT = 90.0
PARTY_TIMEOUT = 20.0
EQUIP_TIMEOUT = 20.0
TRADE_TIMEOUT = 1800.0
CITY_CONFIRM_TIMEOUT = 90.0
DEATH_RECOVERY_TIMEOUT = 60.0
RESPAWN_RETRY_SECONDS = 5.0
RESPAWN_MAX_ATTEMPTS = 3
RESPAWN_FINAL_WAIT_SECONDS = 10.0
POUCH_SETTLE_TIMEOUT = 30.0
POUCH_SETTLE_INTERVAL = 2.0
POUCH_STABLE_READS = 3
ACTION_RETRY_SECONDS = 3.0
TRANSPORT_DEATH_CONFIRM_SECONDS = 5.0
TRANSPORT_TELEPORT_GRACE_SECONDS = 5.0
TRANSPORT_SNAPSHOT_MAX_AGE = 10.0

state = STATE_IDLE
state_since = time.time()
last_poll = 0.0
last_action = 0.0
cycle_active = False
cycle_armed = True
trade_command_received = False
trade_settled_received = False
trade_complete_time = 0.0
profile_name = 'default'
settings_loading = False
job_candidates = []
script_candidates = []
training_inside_streak = 0
pending_action = None
pouch_settle_started = 0.0
pouch_last_poll = 0.0
pouch_last_count = None
pouch_stable_reads = 0
death_teleport_received = False
respawn_attempts = 0
last_respawn_request = 0.0
last_box_count = None
status_panel_open = False
STATUS_OFFSCREEN_X = 3000
pending_transport_death_time = 0.0
pending_transport_death_region = 0
last_teleport_time = 0.0
tracked_transport_id = 0
transport_load_seen = False
transport_unloaded_after_load = False
last_transport_box_count = None
last_transport_snapshot_time = 0.0


def _config_directory():
    try:
        root = get_config_dir()
    except Exception:
        root = None
    if not root:
        root = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root, pName)


def _scripts_directory():
    return os.path.join(_config_directory(), 'scripts')


def _settings_path():
    return os.path.join(_config_directory(), 'settings.json')


def _ensure_directories():
    try:
        if not os.path.isdir(_scripts_directory()):
            os.makedirs(_scripts_directory())
        return True
    except Exception as ex:
        log('[%s] Config klasoru olusturulamadi: %s' % (pName, ex))
        return False


gui = QtBind.init(__name__, pName)

QtBind.createLabel(
    gui, '<font color="#FF0000" size="4"><b>🐫 FSRO-R AUTO TRADE</b></font>', 10, 6
)
QtBind.createLabel(gui, '<font color="#9aa0ac">v%s</font>' % pVersion, 205, 12)
QtBind.createLabel(
    gui, '<font color="#FF0000"><b>♥ Made By FascinaTe</b></font>', 430, 11
)
btn_status_tab = QtBind.createButton(gui, 'btn_status_tab_clicked', '📊  Status', 310, 3)
QtBind.createLineEdit(gui, '', 10, 30, 560, 1)

QtBind.createLabel(gui, '<font color="#FF0000"><b>📦 KUTU KONTROLÜ</b></font>', 10, 38)
chk_enabled = QtBind.createCheckBox(gui, 'chk_enabled_changed', 'Plugin aktif', 10, 58)

QtBind.createLabel(gui, '<font color="#6b7280"><b>Toplam kutu:</b></font>', 10, 83)
lbl_box_count = QtBind.createLabel(gui, '<font color="#FF0000"><b>0</b></font>', 125, 83)
QtBind.createLabel(gui, '<font color="#6b7280"><b>Kervan hedefi:</b></font>', 10, 111)
txt_target = QtBind.createLineEdit(gui, '80', 125, 107, 70, 22)
QtBind.createLabel(gui, '<font color="#6b7280"><b>Guvenlik siniri (&lt;):</b></font>', 10, 139)
txt_safety = QtBind.createLineEdit(gui, '5', 125, 135, 70, 22)
QtBind.createLabel(gui, '<font color="#6b7280"><b>Komut gecikmesi:</b></font>', 10, 167)
txt_action_delay = QtBind.createLineEdit(gui, '2000', 125, 163, 70, 22)
QtBind.createLabel(gui, '<font color="#9aa0ac">ms</font>', 198, 167)
btn_check = QtBind.createButton(gui, 'btn_check_clicked', '↻  Kutuyu Kontrol Et', 10, 192)

QtBind.createLabel(gui, '<font color="#FF0000"><b>🥷 JOB ITEMİ</b></font>', 240, 38)
cmb_job_item = QtBind.createCombobox(gui, 240, 63, 330, 22)
btn_refresh_jobs = QtBind.createButton(gui, 'btn_refresh_jobs_clicked', '↻  Job Itemlerini Yenile', 240, 95)
chk_grind_with_job = QtBind.createCheckBox(
    gui, 'chk_grind_with_job_changed', 'Kasarken job itemi giyili kalsin', 240, 130
)
QtBind.createLabel(
    gui, '<font color="#FF0000"><b>⚠ Scriptte ZORUNLU komutlar:</b></font>', 240, 155
)
QtBind.createLabel(
    gui, '<font color="#FF0000"><b>Trade sonrasi: FSroRAutoTrade_settled</b></font>', 240, 175
)
QtBind.createLabel(
    gui, '<font color="#FF0000"><b>Script sonunda: FSroRAutoTrade_complete</b></font>', 240, 195
)

QtBind.createLabel(
    gui, '<font color="#FF0000"><b>📜 KERVAN SCRIPTİ</b></font>'
         ' <font color="#9aa0ac">Config/FSroRAutoTrade/scripts</font>', 10, 220
)
cmb_script = QtBind.createCombobox(gui, 10, 237, 400, 22)
btn_refresh_scripts = QtBind.createButton(gui, 'btn_refresh_scripts_clicked', '↻  Scriptleri Yenile', 425, 236)

btn_save = QtBind.createButton(gui, 'btn_save_clicked', '💾  Ayarlari Kaydet', 10, 280)
btn_manual = QtBind.createButton(gui, 'btn_manual_clicked', '▶  Kervani Manuel Baslat', 145, 280)
btn_abort = QtBind.createButton(gui, 'btn_abort_clicked', '■  Islemi Iptal Et', 330, 280)

QtBind.createLabel(gui, '<font color="#FF0000"><b>● CANLI DURUM</b></font>', 10, 320)
QtBind.createLabel(gui, '<font color="#6b7280"><b>Durum:</b></font>', 10, 345)
lbl_state = QtBind.createLabel(gui, '<font color="#c98a1a"><b>Hazir</b></font>', 70, 345)
lbl_message = QtBind.createLabel(gui, '<font color="#9aa0ac">Config klasoru hazirlaniyor...</font>', 10, 372)
QtBind.createLabel(gui, '<font color="#6b7280"><b>Training Area:</b></font>', 10, 400)
lbl_training = QtBind.createLabel(gui, '<font color="#9aa0ac">Kontrol bekleniyor.</font>', 105, 400)
lst_status_panel = QtBind.createList(gui, STATUS_OFFSCREEN_X, 55, 560, 255)


def _html_escape(value):
    return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _set_message(message, write_log=False):
    QtBind.setText(gui, lbl_message,
                   '<font color="#9aa0ac">%s</font>' % _html_escape(message))
    if write_log:
        log('[%s] %s' % (pName, message))


def _set_state(new_state, message):
    global state, state_since, last_action
    state = new_state
    state_since = time.time()
    last_action = 0.0
    color = '#CC0000' if new_state == STATE_ERROR else '#c98a1a'
    if new_state == STATE_IDLE:
        color = '#1f9d63'
    QtBind.setText(gui, lbl_state,
                   '<font color="%s"><b>● %s</b></font>' % (color, new_state))
    _set_message(message, True)


def _action_delay_seconds():
    value = _number(txt_action_delay, 0, 'Komut gecikmesi')
    if value is None:
        return 2.0
    return min(value, 60000) / 1000.0


def _schedule_action(action, message):
    global pending_action
    pending_action = action
    _set_state(STATE_WAITING_ACTION, '%s (%d ms bekleniyor)' % (
        message, int(_action_delay_seconds() * 1000)))


def _fail(message):
    global cycle_active, pending_action, pending_transport_death_time
    cycle_active = False
    pending_action = None
    pending_transport_death_time = 0.0
    try:
        stop_script()
    except Exception:
        pass
    try:
        stop_bot()
    except Exception:
        pass
    _set_state(STATE_ERROR, message)


def _recover_error_at_training():
    """Kullanici botu manuel baslatip slota donunce gecici hatayi temizler."""
    global cycle_active, cycle_armed, pending_action
    global trade_command_received, trade_settled_received, trade_complete_time
    global pending_transport_death_time, pending_transport_death_region
    global pouch_settle_started, pouch_last_poll
    global pouch_last_count, pouch_stable_reads, death_teleport_received
    global respawn_attempts, last_respawn_request

    cycle_active = False
    cycle_armed = True
    pending_action = None
    trade_command_received = False
    trade_settled_received = False
    trade_complete_time = 0.0
    pending_transport_death_time = 0.0
    _reset_transport_tracking()
    pending_transport_death_region = 0
    pouch_settle_started = 0.0
    pouch_last_poll = 0.0
    pouch_last_count = None
    pouch_stable_reads = 0
    death_teleport_received = False
    respawn_attempts = 0
    last_respawn_request = 0.0
    _set_state(STATE_IDLE,
               'Training area 3/3 dogrulandi; hata sifirlandi ve kontrol yeniden basladi.')


def _iter_items(value):
    if value is None:
        return
    if isinstance(value, (list, tuple)):
        for entry in value:
            for item in _iter_items(entry):
                yield item
        return
    if not isinstance(value, dict):
        return
    if ('name' in value or 'servername' in value or 'model' in value):
        yield value
        return
    if 'items' in value:
        for item in _iter_items(value.get('items')):
            yield item
        return
    for entry in value.values():
        for item in _iter_items(entry):
            yield item


def _quantity(item):
    try:
        value = int(item.get('quantity', 1) or 1)
        return value if value > 0 else 0
    except (TypeError, ValueError):
        return 1


def _is_specialty_box(item):
    name = str(item.get('name') or '').strip().lower()
    servername = str(item.get('servername') or '').strip().lower()
    if 'specialty goods box' in name:
        return True
    return ('specialty' in servername and
            ('goods' in servername or 'box' in servername))


def _read_box_count(show_error=False):
    global last_box_count
    try:
        pouch = get_job_pouch()
    except Exception as ex:
        if show_error:
            _set_message('Job pouch okunamadi: %s' % ex, True)
        return None
    if pouch is None:
        if show_error:
            _set_message('Job pouch verisi henuz hazir degil.', True)
        return None
    total = sum(_quantity(item) for item in _iter_items(pouch)
                if _is_specialty_box(item))
    last_box_count = total
    QtBind.setText(gui, lbl_box_count,
                   '<font color="#FF0000"><b>%d</b></font>' % total)
    return total


def _training_debug_snapshot():
    result = {
        'status': 'Bilinmiyor', 'position_region': '-', 'training_region': '-',
        'distance': '-', 'radius': '-', 'inside': False
    }
    try:
        area = get_training_area()
        position = get_position()
    except Exception as ex:
        result['status'] = 'API hatasi: %s' % ex
        return result
    if not area:
        result['status'] = 'Aktif training area yok'
        return result
    if not position:
        result['status'] = 'Karakter konumu hazir degil'
        return result
    try:
        area_region = int(area.get('region', 0) or 0)
        position_region = int(position.get('region', 0) or 0)
        radius = float(area.get('radius', 50.0) or 50.0)
        dx = float(position.get('x', 0.0)) - float(area.get('x', 0.0))
        dy = float(position.get('y', 0.0)) - float(area.get('y', 0.0))
        distance = (dx * dx + dy * dy) ** 0.5
        same_region = not (area_region and position_region and
                           area_region != position_region)
        inside = same_region and distance <= radius
        result.update({
            'status': 'Iceride' if inside else
                      ('Farkli region' if not same_region else 'Disarida'),
            'position_region': position_region,
            'training_region': area_region,
            'distance': '%.1f' % distance,
            'radius': '%.1f' % radius,
            'inside': inside
        })
    except (TypeError, ValueError, KeyError) as ex:
        result['status'] = 'Gecersiz veri: %s' % ex
    return result


def _refresh_status_panel():
    if not status_panel_open:
        return
    training = _training_debug_snapshot()
    target_text = QtBind.text(gui, txt_target) or '-'
    safety_text = QtBind.text(gui, txt_safety) or '-'
    delay_text = QtBind.text(gui, txt_action_delay) or '-'
    job = _selected_job() or {}
    script_name = _selected_script_name() or '-'
    action_name = '-'
    if pending_action:
        action_name = getattr(pending_action, '__name__', str(pending_action))

    blockers = []
    if not QtBind.isChecked(gui, chk_enabled):
        blockers.append('Plugin pasif')
    if state == STATE_ERROR:
        blockers.append('ERROR durumu')
    if cycle_active:
        blockers.append('Aktif dongu var')
    if training_inside_streak < 3:
        blockers.append('Training 3/3 degil')
    if not cycle_armed:
        blockers.append('Cycle armed kapali')
    try:
        if last_box_count is None or int(last_box_count) < int(target_text):
            blockers.append('Kutu hedefin altinda')
    except Exception:
        blockers.append('Kutu/hedef gecersiz')

    rows = [
        '=== FSroRAutoTrade CANLI STATUS ===',
        'Plugin enabled       : %s' % QtBind.isChecked(gui, chk_enabled),
        'State                : %s' % state,
        'Cycle active         : %s' % cycle_active,
        'Cycle armed          : %s' % cycle_armed,
        'Bekleyen aksiyon     : %s' % action_name,
        'Kutu / hedef         : %s / %s' % (
            '-' if last_box_count is None else last_box_count, target_text),
        'Guvenlik siniri      : <%s' % safety_text,
        'Komut gecikmesi      : %s ms' % delay_text,
        'Training status      : %s' % training['status'],
        'Training streak      : %d/3' % training_inside_streak,
        'Position region      : %s' % training['position_region'],
        'Training region      : %s' % training['training_region'],
        'Mesafe / radius      : %s / %s' % (
            training['distance'], training['radius']),
        'Secili job itemi     : %s' % (
            job.get('name') or job.get('servername') or '-'),
        'Secili script        : %s' % script_name,
        'Trade settled alindi : %s' % trade_settled_received,
        'Trade complete alindi: %s' % trade_command_received,
        'Transport event bekliyor: %s' % (pending_transport_death_time > 0),
        'Transport son yuku  : %s' % (
            '-' if last_transport_box_count is None else last_transport_box_count),
        'Transport yuk goruldu: %s' % transport_load_seen,
        'Transport teslim edildi: %s' % transport_unloaded_after_load,
        'Otomatik tetik engeli: %s' % (
            ', '.join(blockers) if blockers else 'YOK - tetiklemeye hazir'),
        'Son guncelleme       : %s' % time.strftime('%H:%M:%S')
    ]
    QtBind.clear(gui, lst_status_panel)
    for row in rows:
        QtBind.append(gui, lst_status_panel, row)


def _update_training_status():
    """Karakterin aktif training radius'u icinde oldugunu dogrular."""
    global training_inside_streak
    try:
        area = get_training_area()
        position = get_position()
    except Exception as ex:
        training_inside_streak = 0
        QtBind.setText(gui, lbl_training, 'Konum okunamadi: %s' % ex)
        return False

    if not area:
        training_inside_streak = 0
        QtBind.setText(gui, lbl_training, 'Aktif training area yok.')
        return False
    if not position:
        training_inside_streak = 0
        QtBind.setText(gui, lbl_training, 'Karakter konumu hazir degil.')
        return False

    try:
        area_region = int(area.get('region', 0) or 0)
        position_region = int(position.get('region', 0) or 0)
        if area_region and position_region and area_region != position_region:
            training_inside_streak = 0
            QtBind.setText(gui, lbl_training, 'Disarida (farkli region).')
            return False

        radius = float(area.get('radius', 50.0) or 50.0)
        dx = float(position.get('x', 0.0)) - float(area.get('x', 0.0))
        dy = float(position.get('y', 0.0)) - float(area.get('y', 0.0))
        distance_squared = dx * dx + dy * dy
        inside = distance_squared <= radius * radius
        distance = distance_squared ** 0.5
    except (TypeError, ValueError, KeyError) as ex:
        training_inside_streak = 0
        QtBind.setText(gui, lbl_training, 'Training verisi gecersiz: %s' % ex)
        return False

    if inside:
        training_inside_streak = min(3, training_inside_streak + 1)
        QtBind.setText(gui, lbl_training, 'Iceride %.1fm/%.1fm (%d/3)' % (
            distance, radius, training_inside_streak))
        return training_inside_streak >= 3

    training_inside_streak = 0
    QtBind.setText(gui, lbl_training, 'Disarida %.1fm/%.1fm' % (distance, radius))
    return False


def _is_in_town():
    """Resmi city API'si olmadigi icin yakin sehir NPC'leriyle dogrular."""
    try:
        position = get_position()
        npcs = get_npcs()
    except Exception:
        return False
    if not position or not npcs:
        return False

    keywords = (
        'STORE', 'WAREHOUSE', 'BLACKSMITH', 'POTION', 'GROCERY',
        'STABLE', 'SMITH', 'ARMOR', 'WEAPON', 'ACCESSORY'
    )
    nearby_count = 0
    for npc in npcs.values():
        try:
            npc_region = int(npc.get('region', 0) or 0)
            position_region = int(position.get('region', 0) or 0)
            if npc_region and position_region and npc_region != position_region:
                continue
            dx = float(position.get('x', 0.0)) - float(npc.get('x', 0.0))
            dy = float(position.get('y', 0.0)) - float(npc.get('y', 0.0))
            if dx * dx + dy * dy > 120.0 * 120.0:
                continue
            nearby_count += 1
            text = ('%s %s' % (
                npc.get('name', ''), npc.get('servername', ''))).upper()
            if any(keyword in text for keyword in keywords):
                return True
        except (TypeError, ValueError):
            continue
    # Return noktalarinda genellikle birden fazla sabit NPC gorunur.
    return nearby_count >= 2


def _transport_is_alive():
    try:
        pets = get_pets()
        if not isinstance(pets, dict):
            return False
        for pet in pets.values():
            if not isinstance(pet, dict):
                continue
            if pet.get('type') not in ('transport', 'horse'):
                continue
            try:
                if float(pet.get('hp', 1) or 0) > 0:
                    return True
            except (TypeError, ValueError):
                return True
    except Exception as ex:
        log('[%s] Transport kontrol edilemedi: %s' % (pName, ex))
    return False


def _reset_transport_tracking():
    global tracked_transport_id, transport_load_seen
    global transport_unloaded_after_load, last_transport_box_count
    global last_transport_snapshot_time
    tracked_transport_id = 0
    transport_load_seen = False
    transport_unloaded_after_load = False
    last_transport_box_count = None
    last_transport_snapshot_time = 0.0


def _poll_transport_load(now):
    """Ayni transport petindeki yuklu kutularin teslimatta bosaldigini izler."""
    global tracked_transport_id, transport_load_seen
    global transport_unloaded_after_load, last_transport_box_count
    global last_transport_snapshot_time
    try:
        pets = get_pets()
    except Exception:
        return
    if not isinstance(pets, dict):
        return

    selected_id = 0
    selected_pet = None
    for pet_id, pet in pets.items():
        if not isinstance(pet, dict):
            continue
        if pet.get('type') == 'transport':
            selected_id, selected_pet = pet_id, pet
            break
        if selected_pet is None and pet.get('type') == 'horse':
            selected_id, selected_pet = pet_id, pet
    if selected_pet is None:
        return

    count = sum(_quantity(item) for item in _iter_items(selected_pet.get('items'))
                if _is_specialty_box(item))
    try:
        selected_id = int(selected_id)
    except (TypeError, ValueError):
        selected_id = str(selected_id)

    # Teleport sonrasi yeni entity ID gelirse onceki petin sifirlanmasi teslimat
    # sayilmaz; yeni pet icin temiz bir snapshot serisi baslatilir.
    if selected_id != tracked_transport_id:
        tracked_transport_id = selected_id
        last_transport_box_count = count
        last_transport_snapshot_time = now
        if count > 0:
            transport_load_seen = True
            transport_unloaded_after_load = False
        return

    previous = last_transport_box_count
    if count > 0:
        transport_load_seen = True
        transport_unloaded_after_load = False
    elif transport_load_seen and previous is not None and previous > 0:
        transport_unloaded_after_load = True
        log('[%s] Transport yuku teslimat sonrasi bosaldi (%d -> 0).' %
            (pName, previous))
    last_transport_box_count = count
    last_transport_snapshot_time = now


def _confirm_pending_transport_death(now):
    global pending_transport_death_time, pending_transport_death_region
    if pending_transport_death_time <= 0:
        return
    if now - pending_transport_death_time < TRANSPORT_DEATH_CONFIRM_SECONDS:
        return

    event_time = pending_transport_death_time
    event_region = pending_transport_death_region
    pending_transport_death_time = 0.0
    pending_transport_death_region = 0
    if not cycle_active:
        return

    if (last_teleport_time and
            abs(last_teleport_time - event_time) <= TRANSPORT_TELEPORT_GRACE_SECONDS):
        _set_message('Transport event teleport kaynakli; yok sayildi.', True)
        return

    try:
        position = get_position()
        current_region = int(position.get('region', 0) or 0) if position else 0
    except Exception:
        current_region = 0
    if event_region and current_region and event_region != current_region:
        _set_message('Transport event region gecisi kaynakli; yok sayildi.', True)
        return

    if _transport_is_alive():
        _set_message('Transport halen canli; olum eventi yok sayildi.', True)
        return

    if trade_settled_received:
        _set_message('Trade teslimati isaretlendi; pet termination eventi yok sayildi.', True)
        return

    snapshot_fresh = (last_transport_snapshot_time > 0 and
                      now - last_transport_snapshot_time <= TRANSPORT_SNAPSHOT_MAX_AGE)
    if (snapshot_fresh and transport_load_seen and
            transport_unloaded_after_load and last_transport_box_count == 0):
        _set_message('Yuk teslim edilip transport kapatildi; event yok sayildi.', True)
        return

    if snapshot_fresh and last_transport_box_count is not None and last_transport_box_count > 0:
        _fail('Transport olumu dogrulandi; son gorulen yuk %d kutu.' %
              last_transport_box_count)
        return

    # Pet yuk snapshot'i yoksa despawn ile gercek olumu guvenilir bicimde
    # ayiramayiz. Yanlis pozitif ile tamamlanan kervani kesmek yerine script
    # watchdog'una birak.
    _set_message('Transport eventi yuk snapshoti olmadigi icin yok sayildi.', True)


def _number(widget, minimum, label):
    try:
        value = int(QtBind.text(gui, widget).strip())
    except Exception:
        _set_message('%s tam sayi olmali.' % label, True)
        return None
    if value < minimum:
        _set_message('%s en az %d olmali.' % (label, minimum), True)
        return None
    return value


def _character_name():
    try:
        data = get_character_data()
        if data and data.get('name'):
            return str(data.get('name'))
    except Exception:
        pass
    return 'default'


def _read_settings_file():
    try:
        with open(_settings_path(), 'r') as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _selected_job():
    try:
        selected_label = QtBind.text(gui, cmb_job_item)
        for item in job_candidates:
            if item.get('label') == selected_label:
                return item
    except Exception:
        pass
    return None


def _selected_script_name():
    try:
        selected = QtBind.text(gui, cmb_script)
        if selected in script_candidates:
            return selected
    except Exception:
        pass
    return ''


def _read_script_text(path):
    """Walk scriptini Windows varsayilan codec'inden bagimsiz olarak okur."""
    with open(path, 'rb') as handle:
        raw = handle.read()

    if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        return raw.decode('utf-16')

    encodings = ('utf-8-sig', 'cp1254', 'cp1256', 'cp1251', 'latin-1')

    last_error = None
    for encoding in encodings:
        try:
            return raw.decode(encoding)
        except (LookupError, UnicodeDecodeError) as ex:
            last_error = ex
    raise UnicodeDecodeError(
        'unknown', raw, 0, len(raw),
        'Desteklenen script kodlamalariyla okunamadi: %s' % last_error)


def _profile_values():
    job = _selected_job() or {}
    return {
        'enabled': bool(QtBind.isChecked(gui, chk_enabled)),
        'target': _number(txt_target, 1, 'Kervan hedefi'),
        'safety': _number(txt_safety, 1, 'Guvenlik siniri'),
        'action_delay_ms': _number(txt_action_delay, 0, 'Komut gecikmesi'),
        'grind_with_job': bool(QtBind.isChecked(gui, chk_grind_with_job)),
        'job_model': int(job.get('model', 0) or 0),
        'job_servername': str(job.get('servername') or ''),
        'script': _selected_script_name()
    }


def _save_settings(silent=False):
    values = _profile_values()
    if (values['target'] is None or values['safety'] is None or
            values['action_delay_ms'] is None):
        return False
    data = _read_settings_file()
    profiles = data.get('profiles')
    if not isinstance(profiles, dict):
        profiles = {}
    profiles[profile_name] = values
    data['profiles'] = profiles
    try:
        _ensure_directories()
        with open(_settings_path(), 'w') as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
        if not silent:
            _set_message('Ayarlar kaydedildi: %s' % profile_name, True)
        return True
    except Exception as ex:
        _set_message('Ayarlar kaydedilemedi: %s' % ex, True)
        return False


def _fill_combobox(widget, values):
    QtBind.clear(gui, widget)
    for value in values:
        QtBind.append(gui, widget, value.get('label', '') if isinstance(value, dict) else value)


def _inventory_items():
    try:
        inventory = get_inventory()
    except Exception:
        return []
    if not inventory:
        return []
    result = []
    for slot, item in enumerate(inventory.get('items') or []):
        if item:
            copy = dict(item)
            copy['slot'] = slot
            result.append(copy)
    return result


def _is_job_item(item):
    text = ('%s %s' % (item.get('name', ''), item.get('servername', ''))).upper()
    if 'OUTFIT' in text:
        return True
    try:
        data = get_item(int(item.get('model', 0)))
        return bool(data and int(data.get('tid2', -1)) == 7)
    except Exception:
        return False


def _refresh_jobs(wanted_servername='', wanted_model=0):
    global job_candidates
    candidates = []
    seen = set()
    for item in _inventory_items():
        if not _is_job_item(item):
            continue
        identity = (int(item.get('model', 0) or 0), str(item.get('servername') or ''))
        if identity in seen:
            continue
        seen.add(identity)
        entry = dict(item)
        entry['label'] = '%s [%s]' % (
            item.get('name') or item.get('servername') or 'Job item', item.get('model', '?'))
        candidates.append(entry)
    wanted = wanted_servername
    if not wanted and wanted_model:
        for item in candidates:
            if int(item.get('model', 0) or 0) == int(wanted_model):
                wanted = item.get('servername', '')
                break
    # QtBind combobox icin secim ayarlama API'si yoktur. Kayitli secimi
    # listenin basina tasimak reload sonrasi ayni itemi secili tutar.
    if wanted:
        candidates.sort(key=lambda item: 0 if str(item.get('servername') or '') == str(wanted) else 1)
    job_candidates = candidates
    _fill_combobox(cmb_job_item, job_candidates)
    return bool(job_candidates)


def _refresh_scripts(wanted=''):
    global script_candidates
    _ensure_directories()
    try:
        names = [name for name in os.listdir(_scripts_directory())
                 if os.path.isfile(os.path.join(_scripts_directory(), name)) and
                 not name.startswith('.')]
        names.sort(key=lambda value: value.lower())
    except Exception:
        names = []
    if wanted in names:
        names.remove(wanted)
        names.insert(0, wanted)
    script_candidates = names
    _fill_combobox(cmb_script, script_candidates)
    return bool(script_candidates)


def _load_profile():
    global profile_name, settings_loading
    settings_loading = True
    profile_name = _character_name()
    data = _read_settings_file().get('profiles', {}).get(profile_name, {})
    QtBind.setText(gui, txt_target, str(data.get('target', 80)))
    QtBind.setText(gui, txt_safety, str(data.get('safety', 5)))
    QtBind.setText(gui, txt_action_delay, str(data.get('action_delay_ms', 2000)))
    QtBind.setChecked(gui, chk_grind_with_job, bool(data.get('grind_with_job', False)))
    _refresh_jobs(data.get('job_servername', ''), data.get('job_model', 0))
    _refresh_scripts(data.get('script', ''))
    QtBind.setChecked(gui, chk_enabled, bool(data.get('enabled', False)))
    settings_loading = False
    _set_message('Profil yuklendi: %s' % profile_name, True)


def _job_identity():
    selected = _selected_job()
    if not selected:
        return None
    return (int(selected.get('model', 0) or 0), str(selected.get('servername') or ''))


def _same_job(item, identity):
    if not item or not identity:
        return False
    model, servername = identity
    if model and int(item.get('model', 0) or 0) == model:
        return True
    return bool(servername and str(item.get('servername') or '') == servername)


def _find_job(identity):
    for item in _inventory_items():
        if _same_job(item, identity):
            return item
    return None


def _empty_inventory_slot():
    try:
        inventory = get_inventory()
        items = inventory.get('items') or []
        size = int(inventory.get('size', len(items)))
        for slot in range(13, min(size, len(items))):
            if items[slot] is None:
                return slot
    except Exception:
        pass
    return -1


def _move_item(source, destination):
    packet = struct.pack('<BBBH', 0, int(source), int(destination), 0)
    inject_joymax(0x7034, packet, False)


def _begin_cycle(manual=False):
    global cycle_active, cycle_armed
    global trade_command_received, trade_settled_received
    global trade_complete_time, pending_transport_death_time
    if cycle_active:
        _set_message('Zaten aktif bir kervan islemi var.', True)
        return False
    if not QtBind.isChecked(gui, chk_enabled):
        _set_message('Kervan baslatmak icin once Plugin aktif secenegini acin.', True)
        return False
    if not manual and training_inside_streak < 3:
        _set_message('Otomatik kervan icin karakter training area icinde olmali.', True)
        return False
    target = _number(txt_target, 1, 'Kervan hedefi')
    safety = _number(txt_safety, 1, 'Guvenlik siniri')
    if target is None or safety is None:
        return False
    if not _selected_job():
        _set_message('Once kullanilacak job itemini secin.', True)
        return False
    script_name = _selected_script_name()
    if not script_name:
        _set_message('Once kervan scriptini secin.', True)
        return False
    script_path = os.path.join(_scripts_directory(), script_name)
    if not os.path.isfile(script_path):
        _set_message('Secilen kervan scripti bulunamadi.', True)
        return False
    count = _read_box_count(True)
    if count is None:
        return False
    if not manual and count < target:
        return False
    _save_settings(True)
    cycle_active = True
    cycle_armed = False
    trade_command_received = False
    trade_settled_received = False
    trade_complete_time = 0.0
    pending_transport_death_time = 0.0
    try:
        stop_script()
    except Exception:
        pass
    try:
        stop_bot()
    except Exception:
        pass
    _schedule_action(_use_initial_return_scroll,
                     'Bot ve walking durduruldu; return scroll hazirlaniyor.')
    return True


def _use_initial_return_scroll():
    _set_state(STATE_RETURNING, 'Return scroll kullaniliyor.')
    try:
        if not use_return_scroll():
            _fail('Return scroll kullanilamadi veya bulunamadi.')
            return False
    except Exception as ex:
        _fail('Return scroll hatasi: %s' % ex)
        return False
    return True


def _begin_party_leave_or_equip():
    try:
        party = get_party()
    except Exception as ex:
        _fail('Party bilgisi okunamadi: %s' % ex)
        return
    if party:
        inject_joymax(0x7061, b'', False)
        _set_state(STATE_LEAVING_PARTY, 'Sehre varildi; partyden cikiliyor.')
    else:
        _begin_equip()


def _begin_equip():
    identity = _job_identity()
    item = _find_job(identity)
    if not item:
        _fail('Secilen job itemi envanterde bulunamadi.')
        return
    if int(item.get('slot', -1)) == 8:
        _schedule_action(_start_trade_script,
                         'Job itemi zaten giyili; kervan scripti hazirlaniyor.')
        return
    _move_item(item.get('slot'), 8)
    _set_state(STATE_EQUIPPING, 'Job itemi giyiliyor: %s' % item.get('name', '?'))


def _start_trade_script():
    global trade_command_received, trade_settled_received, trade_complete_time
    name = _selected_script_name()
    path = os.path.join(_scripts_directory(), name)
    try:
        script_text = _read_script_text(path)
    except Exception as ex:
        _fail('Kervan scripti okunamadi: %s' % ex)
        return
    if not script_text.strip():
        _fail('Kervan scripti bos.')
        return
    if 'FSroRAutoTrade_complete' not in script_text:
        _fail('Script sonunda FSroRAutoTrade_complete komutu bulunmuyor.')
        return
    if 'FSroRAutoTrade_settled' not in script_text:
        _fail('Trade komutundan sonra FSroRAutoTrade_settled komutu bulunmuyor.')
        return
    trade_command_received = False
    trade_settled_received = False
    trade_complete_time = 0.0
    try:
        result = start_script(script_text)
    except Exception as ex:
        _fail('Kervan scripti baslatilamadi: %s' % ex)
        return
    if result is False:
        _fail('phBot kervan scriptini baslatmayi reddetti.')
        return
    _set_state(STATE_RUNNING_TRADE, 'Kervan scripti calisiyor: %s' % name)


def _try_finish_trade():
    if state != STATE_RUNNING_TRADE:
        return
    if not trade_command_received:
        return
    if not _is_in_town():
        _set_message('Tamamlama komutu alindi; karakterin sehirde oldugu dogrulaniyor.')
        if trade_complete_time and time.time() - trade_complete_time > CITY_CONFIRM_TIMEOUT:
            _fail('Karakterin sehirde oldugu %d saniyede dogrulanamadi.' % CITY_CONFIRM_TIMEOUT)
        return
    _begin_pouch_settle()


def _begin_pouch_settle():
    global pouch_settle_started, pouch_last_poll
    global pouch_last_count, pouch_stable_reads
    pouch_settle_started = time.time()
    pouch_last_poll = 0.0
    pouch_last_count = None
    pouch_stable_reads = 0
    _set_state(STATE_SETTLING_POUCH,
               'Sehir dogrulandi; teslim sonrasi job pouch guncellenmesi bekleniyor.')


def _poll_pouch_settle(now):
    global pouch_last_poll, pouch_last_count, pouch_stable_reads
    if now - pouch_last_poll < POUCH_SETTLE_INTERVAL:
        return
    pouch_last_poll = now

    count = _read_box_count(False)
    safety = _number(txt_safety, 1, 'Guvenlik siniri')
    if safety is None:
        _fail('Kutu guvenlik siniri gecersiz.')
        return

    if count is not None:
        if count == pouch_last_count:
            pouch_stable_reads += 1
        else:
            pouch_last_count = count
            pouch_stable_reads = 1
        _set_message('Pouch sabitleniyor: %d kutu (%d/%d), gerekli: <%d' % (
            count, pouch_stable_reads, POUCH_STABLE_READS, safety))

        # Yalnizca guvenli dusuk deger kararlı hale gelirse devam et. Yuksek
        # deger stale olabilir; timeout dolana kadar guncellenmesini bekle.
        if count < safety and pouch_stable_reads >= POUCH_STABLE_READS:
            _set_message('Pouch dogrulandi: %d kutu kaldi.' % count, True)
            if QtBind.isChecked(gui, chk_grind_with_job):
                _schedule_action(_start_grinding, 'Botun baslatilmasi hazirlaniyor.')
            else:
                _schedule_action(_begin_unequip,
                                 'Job iteminin cikarilmasi hazirlaniyor.')
            return

    if now - pouch_settle_started >= POUCH_SETTLE_TIMEOUT:
        if pouch_last_count is None:
            _fail('Teslim sonrasi job pouch %d saniyede okunamadi.' % POUCH_SETTLE_TIMEOUT)
        else:
            _fail('Teslim sonrasi %d kutu kaldi; guvenli kosul <%d saglanmadi.' % (
                pouch_last_count, safety))


def _begin_unequip():
    identity = _job_identity()
    item = _find_job(identity)
    if not item or int(item.get('slot', -1)) != 8:
        _start_grinding()
        return
    destination = _empty_inventory_slot()
    if destination < 0:
        _fail('Job itemi cikarilamadi: envanterde bos slot yok.')
        return
    _move_item(8, destination)
    _set_state(STATE_UNEQUIPPING, 'Job itemi cikariliyor.')


def _start_grinding():
    global cycle_active
    try:
        result = start_bot()
    except Exception as ex:
        _fail('Bot baslatilamadi: %s' % ex)
        return
    if result is False:
        _fail('phBot botu baslatmayi reddetti.')
        return
    cycle_active = False
    _set_state(STATE_IDLE, 'Kervan tamamlandi; bot bir kez baslatildi.')


def _send_respawn_request(now=None):
    """Olum ekranindaki sehirde yeniden dogma secenegini sunucuya gonderir."""
    global respawn_attempts, last_respawn_request
    if now is None:
        now = time.time()
    if respawn_attempts >= RESPAWN_MAX_ATTEMPTS:
        return False
    try:
        inject_joymax(0x3053, b'\x01', False)
    except Exception as ex:
        _fail('Sehirde yeniden dogma istegi gonderilemedi: %s' % ex)
        return False
    respawn_attempts += 1
    last_respawn_request = now
    _set_message('Sehirde yeniden dogma istegi gonderildi (%d/%d).' % (
        respawn_attempts, RESPAWN_MAX_ATTEMPTS), True)
    return True


def FSroRAutoTrade_settled(arguments):
    global trade_settled_received, pending_transport_death_time
    if not cycle_active or state != STATE_RUNNING_TRADE:
        log('[%s] Teslimat komutu aktif kervan disinda yok sayildi.' % pName)
        return 0
    trade_settled_received = True
    if pending_transport_death_time > 0:
        pending_transport_death_time = 0.0
        _set_message('Trade teslim edildi; bekleyen pet termination eventi yok sayildi.', True)
    else:
        _set_message('Trade teslimat komutu alindi.', True)
    return 0


def FSroRAutoTrade_complete(arguments):
    global trade_command_received, trade_complete_time
    if not cycle_active or state != STATE_RUNNING_TRADE:
        log('[%s] Tamamlama komutu aktif kervan disinda yok sayildi.' % pName)
        return 0
    trade_command_received = True
    trade_complete_time = time.time()
    _set_message('Kervan tamamlama komutu alindi; sehir kontrol ediliyor.', True)
    _try_finish_trade()
    return 0


def teleported():
    global death_teleport_received, last_teleport_time
    last_teleport_time = time.time()
    if not cycle_active:
        return
    if state == STATE_RETURNING:
        _schedule_action(_begin_party_leave_or_equip,
                         'Sehre varildi; sonraki islem hazirlaniyor.')
    elif state == STATE_DEATH_RECOVERY:
        death_teleport_received = True
        _set_message('Olum sonrasi teleport algilandi; sehir dogrulaniyor.', True)


def joined_game():
    global profile_name
    profile_name = 'default'


def handle_event(event_type, data):
    global pending_action, cycle_armed, death_teleport_received
    global pending_transport_death_time, pending_transport_death_region
    global respawn_attempts, last_respawn_request
    if not cycle_active:
        return
    if event_type == EVENT_DIED:
        pending_action = None
        cycle_armed = True
        death_teleport_received = False
        respawn_attempts = 0
        last_respawn_request = 0.0
        pending_transport_death_time = 0.0
        pending_transport_death_region = 0
        _reset_transport_tracking()
        try:
            stop_script()
        except Exception:
            pass
        try:
            stop_bot()
        except Exception:
            pass
        _set_state(STATE_DEATH_RECOVERY,
                   'Karakter oldu; sehirde yeniden dogma hazirlaniyor.')
        try:
            character = get_character_data()
        except Exception:
            character = None
        if character and character.get('dead'):
            _send_respawn_request()
    elif event_type == EVENT_TRANSPORT_DIED:
        pending_transport_death_time = time.time()
        try:
            position = get_position()
            pending_transport_death_region = int(
                position.get('region', 0) or 0) if position else 0
        except Exception:
            pending_transport_death_region = 0
        _set_message('Transport eventi alindi (ID: %s); dogrulama bekleniyor.' % data,
                     True)


def disconnected():
    if cycle_active:
        _fail('Kervan dongusu sirasinda baglanti kesildi; otomatik devam iptal edildi.')


def finished():
    """Plugin reload/kapanisinda yarim kalan otomasyonu guvenli durdurur."""
    if not cycle_active:
        return
    try:
        stop_script()
    except Exception:
        pass
    try:
        stop_bot()
    except Exception:
        pass
    log('[%s] Plugin kapatildi/reload edildi; aktif kervan islemi durduruldu.' % pName)


def btn_check_clicked():
    count = _read_box_count(True)
    if count is not None:
        _set_message('Specialty Goods Box toplam: %d' % count, True)


def btn_status_tab_clicked():
    global status_panel_open
    status_panel_open = not status_panel_open
    if status_panel_open:
        _read_box_count(False)
        QtBind.move(gui, lst_status_panel, 10, 55)
        QtBind.setText(gui, btn_status_tab, '←  Ana Ekran')
        _refresh_status_panel()
    else:
        QtBind.move(gui, lst_status_panel, STATUS_OFFSCREEN_X, 55)
        QtBind.setText(gui, btn_status_tab, '📊  Status')


def btn_refresh_jobs_clicked():
    current = _selected_job() or {}
    if _refresh_jobs(current.get('servername', ''), current.get('model', 0)):
        _set_message('%d job itemi bulundu.' % len(job_candidates), True)
    else:
        _set_message('OUTFIT/job itemi bulunamadi.', True)


def btn_refresh_scripts_clicked():
    current = _selected_script_name()
    if _refresh_scripts(current):
        _set_message('%d script bulundu.' % len(script_candidates), True)
    else:
        _set_message('Script bulunamadi: %s' % _scripts_directory(), True)


def btn_save_clicked():
    _save_settings(False)


def btn_manual_clicked():
    _begin_cycle(True)


def btn_abort_clicked():
    global cycle_active, cycle_armed, pending_action, pending_transport_death_time
    cycle_active = False
    cycle_armed = False
    pending_action = None
    pending_transport_death_time = 0.0
    try:
        stop_script()
    except Exception:
        pass
    _set_state(STATE_IDLE, 'Aktif islem kullanici tarafindan iptal edildi; bot baslatilmadi.')


def chk_enabled_changed(checked):
    if settings_loading:
        return
    if not checked and cycle_active:
        btn_abort_clicked()
    _save_settings(True)
    _set_message('Plugin %s.' % ('aktif' if checked else 'pasif'), True)


def chk_grind_with_job_changed(checked):
    if not settings_loading:
        _save_settings(True)


def _poll_state(now):
    global last_action, pending_action
    global respawn_attempts, last_respawn_request
    elapsed = now - state_since
    identity = _job_identity()

    if state == STATE_WAITING_ACTION:
        if elapsed >= _action_delay_seconds():
            action = pending_action
            pending_action = None
            if action:
                action()
            else:
                _fail('Bekleyen komut bulunamadi.')
    elif state == STATE_RETURNING:
        if elapsed > RETURN_TIMEOUT:
            _fail('Sehre donus zaman asimina ugradi.')
    elif state == STATE_LEAVING_PARTY:
        try:
            party = get_party()
        except Exception:
            party = None
        if not party:
            _schedule_action(_begin_equip, 'Partyden cikildi; job itemi hazirlaniyor.')
        elif elapsed > PARTY_TIMEOUT:
            _fail('Partyden cikis zaman asimina ugradi.')
        elif now - last_action >= max(ACTION_RETRY_SECONDS, _action_delay_seconds()):
            last_action = now
            inject_joymax(0x7061, b'', False)
    elif state == STATE_EQUIPPING:
        item = _find_job(identity)
        if item and int(item.get('slot', -1)) == 8:
            _schedule_action(_start_trade_script,
                             'Job itemi giyildi; kervan scripti hazirlaniyor.')
        elif elapsed > EQUIP_TIMEOUT:
            _fail('Job itemi giyme zaman asimina ugradi.')
    elif state == STATE_RUNNING_TRADE:
        if trade_command_received:
            _try_finish_trade()
        elif elapsed > TRADE_TIMEOUT:
            _fail('Kervan scripti zaman asimina ugradi.')
    elif state == STATE_SETTLING_POUCH:
        _poll_pouch_settle(now)
    elif state == STATE_DEATH_RECOVERY:
        if elapsed > DEATH_RECOVERY_TIMEOUT:
            _fail('Olum sonrasi sehre donus %d saniyede tamamlanmadi.' %
                  DEATH_RECOVERY_TIMEOUT)
            return
        try:
            character = get_character_data()
        except Exception:
            character = None
        if not character:
            return
        if character.get('dead'):
            if (respawn_attempts < RESPAWN_MAX_ATTEMPTS and
                    now - last_respawn_request >= RESPAWN_RETRY_SECONDS):
                _send_respawn_request(now)
                return
            if (respawn_attempts >= RESPAWN_MAX_ATTEMPTS and
                    now - last_respawn_request >= RESPAWN_FINAL_WAIT_SECONDS):
                _fail('Sehirde yeniden dogma basarisiz: %d deneme cevapsiz kaldi.' %
                      RESPAWN_MAX_ATTEMPTS)
            return
        if not death_teleport_received or not _is_in_town():
            return
        _set_message('Karakter sehirde ve canli; kasilma duzeni hazirlaniyor.', True)
        if QtBind.isChecked(gui, chk_grind_with_job):
            _schedule_action(_start_grinding,
                             'Olum sonrasi sehir dogrulandi; bot hazirlaniyor.')
        else:
            _schedule_action(_begin_unequip,
                             'Olum sonrasi sehir dogrulandi; job itemi kontrol ediliyor.')
    elif state == STATE_UNEQUIPPING:
        item = _find_job(identity)
        if not item or int(item.get('slot', -1)) != 8:
            _schedule_action(_start_grinding,
                             'Job itemi cikarildi; bot hazirlaniyor.')
        elif elapsed > EQUIP_TIMEOUT:
            _fail('Job itemi cikarma zaman asimina ugradi.')


def event_loop():
    global last_poll, cycle_armed, profile_name, training_inside_streak
    now = time.time()
    if now - last_poll < POLL_SECONDS:
        return
    last_poll = now

    current_profile = _character_name()
    if current_profile != profile_name:
        _load_profile()

    _refresh_status_panel()
    if cycle_active and state == STATE_RUNNING_TRADE:
        _poll_transport_load(now)
    _confirm_pending_transport_death(now)

    if cycle_active:
        _poll_state(now)
        return

    if not QtBind.isChecked(gui, chk_enabled):
        training_inside_streak = 0
        QtBind.setText(gui, lbl_training, 'Plugin pasif.')
        return

    training_ready = _update_training_status()

    if state == STATE_ERROR:
        if not training_ready:
            return
        _recover_error_at_training()

    count = _read_box_count(False)
    if count is None:
        return
    target = _number(txt_target, 1, 'Kervan hedefi')
    if target is None:
        return
    if count < target:
        cycle_armed = True
    if training_ready and cycle_armed and count >= target:
        _begin_cycle(False)


_ensure_directories()
_refresh_jobs()
_refresh_scripts()
_load_profile()
log('[%s] Loaded' % __name__)
