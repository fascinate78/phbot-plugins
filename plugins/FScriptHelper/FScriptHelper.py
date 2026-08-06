# -*- coding: utf-8 -*-
from phBot import *
import QtBind
import binascii
import json
import os
import struct
import time


pName = 'FScriptHelper'
pVersion = '1.0.0'

COLOR_PRIMARY = '#5B57E0'
COLOR_INFO = '#3498DB'
COLOR_SUCCESS = '#1F9D63'
COLOR_WARNING = '#C98A1A'
COLOR_DANGER = '#E74C3C'
COLOR_MUTED = '#7F8C8D'
COLOR_TEXT = '#2B3038'

STATE_IDLE = 'IDLE'
STATE_RECORDING = 'RECORDING'
STATE_PLAYING = 'PLAYING'

# NPC etkileşimlerinde yaygın kullanılan C->S paketleri. "Ham paketler" seçeneği
# kapalıyken hareket, chat ve savaş paketlerinin yanlışlıkla kaydı engellenir.
NPC_OPCODES = set([
    0x7034,                         # inventory operation (buy/sell/move)
    0x7045, 0x7046,                # select / deselect entity
    0x704B, 0x704C, 0x704D, 0x704E, 0x704F,
    0x7050, 0x7051, 0x7052, 0x7053, 0x7054, 0x7055,
    0x7056, 0x7057, 0x7058, 0x7059, 0x705A,
    0x7068, 0x7069, 0x706A,        # storage-related variants
    0x70B1, 0x70B2, 0x70B3, 0x70B4,
    0x70D3, 0x70D4, 0x70D5, 0x70D6,
    0x7112, 0x7113, 0x7114, 0x7115
])
MAX_PACKETS = 100
MAX_PACKET_BYTES = 4096
MAX_DELAY_MS = 10000
DEFAULT_DELAY_MS = 1200
SCRIPT_FINISH_BUFFER_MS = 2000

state = STATE_IDLE
record_name = ''
record_npc = None
recorded_packets = []
record_last_time = 0.0
commands = {}
nearby_rows = []

play_packets = []
play_index = 0
play_next_at = 0.0
play_stop_bot = True
play_bot_was_running = False
play_live_uid = 0
play_recorded_uid = 0
play_command_name = ''
play_started_from_script = False
resume_skip_name = ''


def _log(message):
    log('[%s] %s' % (pName, message))


def _data_dir():
    return os.path.join(get_config_dir(), pName)


def _data_file():
    return os.path.join(_data_dir(), 'npc_commands.json')


def _ensure_dir():
    folder = _data_dir()
    if not os.path.exists(folder):
        os.makedirs(folder)


def _safe_int(value, default_value, minimum, maximum):
    try:
        number = int(str(value).strip())
        return max(minimum, min(maximum, number))
    except Exception:
        return default_value


def _to_hex(data):
    return binascii.hexlify(bytes(data)).decode('ascii').upper()


def _from_hex(value):
    return binascii.unhexlify(str(value).replace(' ', '').encode('ascii'))


def _set_status(title, detail='', color=COLOR_INFO):
    QtBind.setText(
        gui, lblStatus,
        '<table width="310" cellspacing="0" cellpadding="0"><tr><td>'
        '<b><font color="%s">● %s</font></b><font color="%s"> · %s</font>'
        '</td></tr></table>' % (color, title, COLOR_TEXT, detail)
    )


def _selected_command_name():
    row = QtBind.text(gui, lstCommands)
    if not row:
        return ''
    return row.split('  ·  ', 1)[0].strip()


def _selected_npc():
    index = QtBind.currentIndex(gui, lstNpcs)
    if index is None or index < 0 or index >= len(nearby_rows):
        return None
    return nearby_rows[index]


def _npc_identity(uid, npc):
    return {
        'uid': int(uid),
        'name': str(npc.get('name', '')),
        'servername': str(npc.get('servername', '')),
        'model': int(npc.get('model', 0) or 0)
    }


def _find_live_npc(identity):
    npcs = get_npcs() or {}
    best = None
    for uid, npc in npcs.items():
        if identity.get('servername') and npc.get('servername') == identity.get('servername'):
            return int(uid), npc
        if identity.get('model') and int(npc.get('model', 0) or 0) == identity.get('model'):
            best = (int(uid), npc)
        elif not best and identity.get('name') and npc.get('name') == identity.get('name'):
            best = (int(uid), npc)
    return best


def _validate_packet(packet):
    if not isinstance(packet, dict):
        return False
    try:
        opcode = int(packet.get('opcode'))
        delay = int(packet.get('delay_ms', DEFAULT_DELAY_MS))
        raw = _from_hex(packet.get('data', ''))
        return 0 <= opcode <= 0xFFFF and 0 <= delay <= MAX_DELAY_MS and len(raw) <= MAX_PACKET_BYTES
    except Exception:
        return False


def _validate_command(name, command):
    if not name or not isinstance(command, dict):
        return False
    packets = command.get('packets')
    npc = command.get('npc')
    if not isinstance(packets, list) or not packets or len(packets) > MAX_PACKETS:
        return False
    if not isinstance(npc, dict):
        return False
    return all(_validate_packet(packet) for packet in packets)


def _resolve_command_name(name):
    """Return the stored command name using an exact, case-insensitive match."""
    if name in commands:
        return name

    requested = str(name).lower()
    matches = [stored_name for stored_name in commands if stored_name.lower() == requested]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        _log('Aynı isimde birden fazla kayıt bulundu: %s' % name)
    return None


def load_commands():
    global commands
    commands = {}
    try:
        _ensure_dir()
        if os.path.exists(_data_file()):
            with open(_data_file(), 'r', encoding='utf-8') as handle:
                raw = json.load(handle)
            source = raw.get('commands', {}) if isinstance(raw, dict) else {}
            for command_name, command in source.items():
                if _validate_command(command_name, command):
                    commands[command_name] = command
                else:
                    _log('Geçersiz kayıt atlandı: %s' % command_name)
    except Exception as ex:
        _log('Kayıtlar okunamadı: %s' % ex)
    refresh_command_list()


def save_commands():
    _ensure_dir()
    payload = {'schema_version': 1, 'commands': commands}
    target = _data_file()
    temporary = target + '.tmp'
    try:
        with open(temporary, 'w', encoding='utf-8') as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(temporary, target)
        return True
    except Exception as ex:
        _log('Kayıt dosyası yazılamadı: %s' % ex)
        try:
            if os.path.exists(temporary):
                os.remove(temporary)
        except Exception:
            pass
        return False


def refresh_command_list():
    QtBind.clear(gui, lstCommands)
    for command_name in sorted(commands.keys(), key=lambda value: value.lower()):
        command = commands[command_name]
        npc_name = command.get('npc', {}).get('name', '?')
        QtBind.append(gui, lstCommands, '%s  ·  %s paket  ·  %s' %
                      (command_name, len(command.get('packets', [])), npc_name))
    QtBind.setText(gui, lblCount, '%d kayıt' % len(commands))


def refresh_npcs():
    global nearby_rows
    nearby_rows = []
    QtBind.clear(gui, lstNpcs)
    npcs = get_npcs() or {}
    ordered = sorted(npcs.items(), key=lambda pair: str(pair[1].get('name', '')).lower())
    for uid, npc in ordered:
        item = _npc_identity(uid, npc)
        nearby_rows.append(item)
        QtBind.append(gui, lstNpcs, '%s  ·  %s  ·  UID %s' %
                      (item['name'], item['servername'], item['uid']))
    _set_status('NPC LISTESİ', '%d yakındaki NPC bulundu' % len(nearby_rows), COLOR_INFO)


def start_recording():
    global state, record_name, record_npc, recorded_packets, record_last_time
    if state != STATE_IDLE:
        _log('Önce aktif kayıt/oynatma işlemini durdurun.')
        return
    name = QtBind.text(gui, tbxName).strip()
    if not name:
        _set_status('HATA', 'Kayıt adı girin', COLOR_DANGER)
        return
    record_name = name
    record_npc = None
    recorded_packets = []
    record_last_time = time.time()
    state = STATE_RECORDING
    _set_status('NPC BEKLENİYOR', '%s · oyun içinde NPC’ye tıklayın' % name, COLOR_WARNING)
    _log('Kayıt hazır: %s · oyun içinde hedef NPC’ye tıklayın.' % name)


def finish_recording():
    global state, record_name, record_npc, recorded_packets
    if state != STATE_RECORDING:
        _log('Aktif bir kayıt yok.')
        return
    name = record_name
    if record_npc is None:
        _set_status('UYARI', 'Henüz oyun içinde bir NPC seçilmedi', COLOR_WARNING)
        return
    if len(recorded_packets) <= 1:
        _set_status('UYARI', 'NPC seçimi dışında işlem yakalanmadı', COLOR_WARNING)
        return
    commands[name] = {
        'npc': dict(record_npc),
        'packets': list(recorded_packets),
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    if save_commands():
        _log('Kayıt kaydedildi: %s (%d paket)' % (name, len(recorded_packets)))
        _set_status('HAZIR', '%s kaydedildi' % name, COLOR_SUCCESS)
    state = STATE_IDLE
    record_name = ''
    record_npc = None
    recorded_packets = []
    refresh_command_list()


def cancel_action():
    global state, record_name, record_npc, recorded_packets
    global play_packets, play_index, play_next_at
    was_playing = state == STATE_PLAYING
    state = STATE_IDLE
    record_name = ''
    record_npc = None
    recorded_packets = []
    play_packets = []
    play_index = 0
    play_next_at = 0.0
    if was_playing and play_stop_bot and play_bot_was_running:
        start_bot()
    _set_status('İPTAL', 'Aktif işlem durduruldu', COLOR_WARNING)


def delete_command():
    name = _selected_command_name()
    if not name or name not in commands:
        _set_status('HATA', 'Silmek için bir kayıt seçin', COLOR_DANGER)
        return
    del commands[name]
    if save_commands():
        _log('Kayıt silindi: %s' % name)
        _set_status('HAZIR', '%s silindi' % name, COLOR_SUCCESS)
    refresh_command_list()


def _bot_is_running():
    try:
        return str(get_status()).lower() in ('botting', 'training')
    except Exception:
        return False


def play_command(name, stop_during=True, from_script=False):
    global state, play_packets, play_index, play_next_at, play_stop_bot
    global play_bot_was_running, play_live_uid, play_recorded_uid
    global play_command_name, play_started_from_script
    if state != STATE_IDLE:
        _log('Başka bir işlem devam ediyor.')
        return False
    requested_name = name
    name = _resolve_command_name(requested_name)
    if name is None:
        _set_status('HATA', 'Kayıt bulunamadı', COLOR_DANGER)
        _log('Kayıt bulunamadı: %s' % requested_name)
        return False
    command = commands.get(name)
    if not _validate_command(name, command):
        _set_status('HATA', 'Kayıt bulunamadı veya geçersiz', COLOR_DANGER)
        _log('Kayıt geçersiz, çalıştırılamadı: %s' % name)
        return False
    found = _find_live_npc(command['npc'])
    if not found:
        _set_status('HATA', 'Kayıtlı NPC yakında değil', COLOR_DANGER)
        _log('NPC bulunamadı: %s' % command['npc'].get('name', '?'))
        return False
    play_live_uid = found[0]
    play_recorded_uid = int(command['npc'].get('uid', 0) or 0)
    play_command_name = name
    play_started_from_script = bool(from_script)
    play_packets = list(command['packets'])
    play_index = 0
    play_next_at = time.time()
    play_stop_bot = bool(stop_during)
    play_bot_was_running = _bot_is_running()
    if play_stop_bot and play_bot_was_running:
        stop_bot()
    state = STATE_PLAYING
    _set_status('OYNATILIYOR', '%s · %d paket' % (name, len(play_packets)), COLOR_WARNING)
    _log('Komut başladı: %s [%s]' % (name, found[1].get('name', '?')))
    return True


def _replace_npc_uid(data):
    if not play_recorded_uid or play_recorded_uid == play_live_uid:
        return data
    old_uid = struct.pack('<I', play_recorded_uid)
    new_uid = struct.pack('<I', play_live_uid)
    return data.replace(old_uid, new_uid)


def _finish_playback():
    global state, play_packets, play_index, play_next_at
    global resume_skip_name
    state = STATE_IDLE
    play_packets = []
    play_index = 0
    play_next_at = 0.0
    # stop_bot sonrası yürüyüş scripti aynı FSH_NPC satırından devam edebilir.
    # Bir sonraki aynı çağrıyı yalnızca bir kez tüketerek tekrar döngüsünü önle.
    if play_started_from_script and play_stop_bot and play_bot_was_running:
        resume_skip_name = play_command_name
    if play_stop_bot and play_bot_was_running:
        start_bot()
    _set_status('TAMAMLANDI', 'NPC komutu başarıyla oynatıldı', COLOR_SUCCESS)
    _log('NPC komutu tamamlandı.')


def execute_selected():
    name = _selected_command_name()
    if not name:
        _set_status('HATA', 'Oynatmak için kayıt seçin', COLOR_DANGER)
        return
    play_command(name, QtBind.isChecked(gui, cbxStopBot))


def show_packets():
    name = _selected_command_name()
    command = commands.get(name)
    QtBind.clear(gui, lstPackets)
    if not command:
        return
    for index, packet in enumerate(command['packets']):
        QtBind.append(gui, lstPackets, '%02d · 0x%04X · %4d ms · %s' %
                      (index + 1, packet['opcode'], packet['delay_ms'], packet['data']))


def handle_silkroad(opcode, data):
    global record_last_time, record_npc
    if state != STATE_RECORDING or data is None:
        return True
    try:
        raw = bytes(data)

        # Kayıt başladıktan sonra oyun içindeki ilk NPC tıklaması hedefi belirler.
        # Oyuncu/monster gibi NPC listesinde olmayan entity seçimleri yok sayılır.
        if record_npc is None:
            if opcode != 0x7045 or len(raw) < 4:
                return True
            selected_uid = struct.unpack_from('<I', raw, 0)[0]
            npc = (get_npcs() or {}).get(selected_uid)
            if npc is None:
                return True
            record_npc = _npc_identity(selected_uid, npc)
            recorded_packets.append({
                'opcode': 0x7045,
                'data': _to_hex(raw),
                'delay_ms': 0
            })
            record_last_time = time.time()
            _set_status('KAYIT', '%s · %s' % (record_name, record_npc['name']), COLOR_WARNING)
            _log('Hedef NPC yakalandı: %s [%s]' %
                 (record_npc['name'], record_npc['servername']))
            return True

        if len(recorded_packets) >= MAX_PACKETS:
            _log('Paket sınırına ulaşıldı; kayıt otomatik tamamlanıyor.')
            finish_recording()
            return True
        if not QtBind.isChecked(gui, cbxRawPackets) and opcode not in NPC_OPCODES:
            return True
        if len(raw) > MAX_PACKET_BYTES:
            _log('Çok büyük paket atlandı: 0x%04X' % opcode)
            return True
        now = time.time()
        elapsed = int((now - record_last_time) * 1000)
        delay = _safe_int(elapsed, DEFAULT_DELAY_MS, 0, MAX_DELAY_MS)
        recorded_packets.append({
            'opcode': int(opcode),
            'data': _to_hex(raw),
            'delay_ms': delay
        })
        record_last_time = now
        _set_status('KAYIT', '%s · %d paket' % (record_name, len(recorded_packets)), COLOR_WARNING)
    except Exception as ex:
        _log('Paket kaydedilemedi: %s' % ex)
    return True


def event_loop():
    global play_index, play_next_at
    if state != STATE_PLAYING or time.time() < play_next_at:
        return
    if play_index >= len(play_packets):
        _finish_playback()
        return
    try:
        packet = play_packets[play_index]
        opcode = int(packet['opcode'])
        data = _from_hex(packet['data'])
        data = _replace_npc_uid(data)
        inject_joymax(opcode, data, False)
        _log('%d/%d gönderildi: 0x%04X' % (play_index + 1, len(play_packets), opcode))
        play_index += 1
        if play_index >= len(play_packets):
            play_next_at = time.time() + 0.25
        else:
            delay = _safe_int(play_packets[play_index].get('delay_ms'),
                              DEFAULT_DELAY_MS, 0, MAX_DELAY_MS)
            play_next_at = time.time() + (delay / 1000.0)
    except Exception as ex:
        _log('Oynatma durduruldu: %s' % ex)
        cancel_action()


# Script komutları
# FSH_NPC,kayit_adi[,true|false]  -> kaydı oynatır; true botu geçici durdurur.
def FSH_NPC(args):
    global resume_skip_name
    if len(args) < 2 or len(args) > 3:
        _log('Kullanım: FSH_NPC,kayit_adi[,true|false]')
        return 0
    command_name = str(args[1]).strip()
    if resume_skip_name and command_name.lower() == resume_skip_name.lower():
        resume_skip_name = ''
        _log('Script devam çağrısı onaylandı: %s' % command_name)
        return 0
    stop_during = True
    if len(args) == 3:
        stop_during = str(args[2]).strip().lower() not in ('false', '0', 'no', 'off')
    if not play_command(command_name, stop_during, True):
        return 0
    # Bot kapalıysa veya kullanıcı stop_during=false seçtiyse stop_bot çağrılmaz.
    # Yürüyüş scripti, asenkron paket oynatımı tamamlanana kadar bekletilir ve
    # böylece phBot scripti yeniden başlatmadan doğrudan sonraki satıra geçer.
    if not play_bot_was_running or not stop_during:
        total_delay = SCRIPT_FINISH_BUFFER_MS
        for packet in play_packets[1:]:
            total_delay += _safe_int(packet.get('delay_ms'), DEFAULT_DELAY_MS, 0, MAX_DELAY_MS)
        return total_delay
    return 0


def FSH_SELECT(args):
    if len(args) != 2:
        _log('Kullanım: FSH_SELECT,npc_adi_veya_servername')
        return 0
    query = str(args[1]).strip().lower()
    for uid, npc in (get_npcs() or {}).items():
        if query in (str(npc.get('name', '')).lower(), str(npc.get('servername', '')).lower()):
            inject_joymax(0x7045, struct.pack('<I', int(uid)), False)
            _log('NPC seçildi: %s' % npc.get('name', query))
            return 0
    _log('NPC yakında bulunamadı: %s' % args[1])
    return 0


def FSH_DELAY(args):
    if len(args) != 2:
        return DEFAULT_DELAY_MS
    return _safe_int(args[1], DEFAULT_DELAY_MS, 0, 60000)


def noop_checked(checked):
    pass


gui = QtBind.init(__name__, pName)

QtBind.createLabel(gui,
    '<font color="%s" size="4"><b>⚙ FSCRIPT HELPER</b></font>' % COLOR_PRIMARY, 12, 6)
QtBind.createLabel(gui, '<font color="%s">v%s · NPC command recorder</font>' %
    (COLOR_MUTED, pVersion), 195, 12)
QtBind.createLabel(gui,
    '<font color="%s"><b>⚜ Made By FascinaTe</b></font>' % COLOR_PRIMARY, 555, 11)
QtBind.createLineEdit(gui, '', 12, 31, 716, 1)

QtBind.createLabel(gui,
    '<font color="%s"><b>◆ NEARBY NPCS</b></font>' % COLOR_PRIMARY, 12, 40)
QtBind.createButton(gui, 'refresh_npcs', '↻ NPC Listesini Yenile', 12, 60)
QtBind.createLabel(gui, '<font color="%s">Bilgi amaçlı yakındaki NPC listesi</font>' % COLOR_MUTED, 175, 65)
lstNpcs = QtBind.createList(gui, 12, 88, 420, 91)

QtBind.createLabel(gui,
    '<font color="%s"><b>● RECORD</b></font>' % COLOR_PRIMARY, 452, 40)
QtBind.createLabel(gui, '<font color="%s">Kayıt adı</font>' % COLOR_MUTED, 452, 65)
tbxName = QtBind.createLineEdit(gui, '', 515, 60, 208, 22)
QtBind.createButton(gui, 'start_recording', '● Kaydı Başlat', 452, 88)
QtBind.createButton(gui, 'finish_recording', '■ Kaydet & Bitir', 568, 88)
cbxRawPackets = QtBind.createCheckBox(gui, 'noop_checked', 'Gelişmiş: tüm C→S paketlerini kaydet', 452, 119)
QtBind.setChecked(gui, cbxRawPackets, False)
QtBind.createLabel(gui,
    '<table width="270"><tr><td><font color="%s">Kaydı başlatın, ardından oyun içinde '
    'hedef NPC’ye tıklayıp işlemleri yapın.</font></td></tr></table>' % COLOR_MUTED,
    452, 143)

QtBind.createLineEdit(gui, '', 12, 188, 716, 1)
QtBind.createLabel(gui,
    '<font color="%s"><b>▣ SAVED NPC COMMANDS</b></font>' % COLOR_PRIMARY, 12, 197)
lblCount = QtBind.createLabel(gui, '<font color="%s">0 kayıt</font>' % COLOR_MUTED, 195, 199)
lstCommands = QtBind.createList(gui, 12, 220, 420, 100)
QtBind.createButton(gui, 'execute_selected', '▶ Seçileni Oynat', 452, 220)
QtBind.createButton(gui, 'show_packets', '≡ Paketleri Göster', 575, 220)
QtBind.createButton(gui, 'delete_command', '🗑 Kaydı Sil', 452, 249)
QtBind.createButton(gui, 'cancel_action', '■ İşlemi İptal Et', 555, 249)
cbxStopBot = QtBind.createCheckBox(gui, 'noop_checked', 'Oynatırken botu geçici durdur', 452, 281)
QtBind.setChecked(gui, cbxStopBot, True)

QtBind.createLineEdit(gui, '', 12, 329, 716, 1)
QtBind.createLabel(gui,
    '<font color="%s"><b>PACKET PREVIEW</b></font>' % COLOR_PRIMARY, 12, 338)
lstPackets = QtBind.createList(gui, 12, 359, 716, 88)
lblStatus = QtBind.createLabel(gui,
    '<table width="700"><tr><td><b><font color="%s">● HAZIR</font></b>'
    '<font color="%s"> · NPC listesi yenilenebilir</font></td></tr></table>' %
    (COLOR_INFO, COLOR_TEXT), 12, 458)


try:
    _ensure_dir()
    load_commands()
    refresh_npcs()
except Exception as ex:
    _log('Başlatma hatası: %s' % ex)

_log('v%s yüklendi · ⚜ Made By FascinaTe' % pVersion)
