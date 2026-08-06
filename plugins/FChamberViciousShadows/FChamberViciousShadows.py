# -*- coding: utf-8 -*-
from phBot import *
import QtBind
import phBotChat
import json
import os
import struct
import time


pName = 'FChamberViciousShadows'
pVersion = '1.6.0'

COLOR_PRIMARY = '#6C5CE7'
COLOR_INFO = '#3498DB'
COLOR_SUCCESS = '#1F9D63'
COLOR_WARNING = '#D68910'
COLOR_DANGER = '#E74C3C'
COLOR_MUTED = '#7F8C8D'
COLOR_TEXT = '#2B3038'

CHAT_PARTY = 4
PROTOCOL = '#FCVS'

STATE_IDLE = 'IDLE'
STATE_LEADER_ENTERING = 'LEADER_ENTERING'
STATE_MEMBER_WAITING = 'MEMBER_WAITING'
STATE_MEMBER_ENTERING = 'MEMBER_ENTERING'
STATE_WAITING_MEMBERS = 'WAITING_MEMBERS'
STATE_ACTIVATING = 'ACTIVATING'
STATE_COMBAT = 'COMBAT'
STATE_LOOTING = 'LOOTING'
STATE_EXIT_PREP = 'EXIT_PREP'
STATE_EXITING = 'EXITING'
STATE_WAITING_PARTY = 'WAITING_PARTY'
STATE_DONE = 'DONE'
STATE_FAILED = 'FAILED'

CHAMBER_REGION = -32742
EXIT_REGION = 23687
EXIT_SERVERNAME = 'NPC_BOSS_DUNGEON_TELE'
LOOT_WAIT_SECONDS = 30
UNIQUE_NAMES = (
    'shadow tigerwoman',
    'shadow cerberus',
    'shadow captain ivy',
    'shadow uruchi',
    'shadow isyutaru'
)
DIRECT_TELEPORT_SCRIPT = 'teleport,Mysterious Priest,Sealed Dungeon of Vicious Shadows'

language = 'en'

TEXT = {
    'en': {
        'subtitle': 'v%s · Party dungeon coordinator',
        'language_switch': '🇹🇷 Türkçe',
        'party_settings': '⚙ PARTY SETTINGS',
        'leader': '👑 Leader character',
        'timeout': '⏱ Timeout',
        'seconds': 'seconds',
        'save': '💾 Save',
        'entry_script': '📜 Entry script',
        'refresh': '↻ Refresh',
        'select_script': '-- Select script --',
        'loop_enable': '🔁 Enable loop',
        'total_loops': 'Total loops',
        'minimum_characters': 'Minimum total characters',
        'stable_party': '30 sec stable party',
        'controls': '🎮 RUN CONTROLS',
        'start_script': '▶ Start with Script',
        'ticket_ready': '⚡ Ticket Ready',
        'stop': '⏹ Stop',
        'flow': 'Leader enters → members enter → Trace → center → 6 seals',
        'live_status': '📡 LIVE STATUS',
        'ready': 'Ready',
        'inside': '👥 Inside: %d / %d',
        'loop': '🔁 Loop: %d/%d',
        'loop_off': '🔁 Loop disabled',
        'loop_ready_timer': '🔁 %d/%d ready · %d/30 sec',
        'loop_party_verified': '🔁 Party: %d/%d verified',
        'setup_note_title': 'ℹ Setup note:',
        'setup_note': 'Install the plugin on every party character and save the same leader name on each client.',
        'settings_saved': 'Settings saved.',
        'settings_save_failed': 'Settings could not be saved: %s',
        'settings_load_failed': 'Settings could not be loaded: %s',
        'scripts_found': '%d entry scripts found: %s',
        'manual_stop': 'Stopped manually',
        'leader_entering': 'Leader is entering via %s',
        'entry_script_mode': 'entry script',
        'direct_mode': 'direct teleport',
        'leader_inside': 'Leader is inside; waiting for members',
        'activating': 'Members are tracing; leader is activating the seals',
        'combat': 'Seals activated; tracking 5 uniques',
        'unique_dead': 'Unique defeated: %d/5',
        'looting': '5/5 uniques defeated; waiting 30 sec for loot',
        'exit_prep': 'Moving to the exit stone',
        'exit_wait_leader': 'At the exit position; waiting for leader',
        'exit_selected': 'Teleport Stone selected; waiting for confirmation',
        'exit_confirm': 'Preparing exit confirmation',
        'exit_sent': 'Exit confirmation sent',
        'member_waiting': 'Waiting for leader; mode: %s',
        'member_entering': 'Member is entering the dungeon',
        'member_inside': 'Inside; preparing INSIDE confirmation',
        'tracing': 'Tracing leader: %s',
        'waiting_party': 'Reforming party for the next loop',
        'loop_direct': 'Loop %d/%d direct entry',
        'loop_exit_done': 'Loop %d exit complete; waiting for party',
        'loop_done': 'Loops completed: %d/%d',
        'dungeon_done': 'Dungeon exit completed',
        'leader_abort': 'Leader cancelled the operation',
        'timeout_failed': 'Timed out',
        'disconnected': 'Disconnected',
        'script_required': 'Select a valid entry script first',
        'script_missing': 'Entry script not found: %s',
        'script_empty': 'Entry script is empty: %s',
        'script_invalid': 'Invalid entry script path',
        'script_start_failed': '%s entry script could not be started',
        'script_error': 'Entry script error: %s',
        'direct_failed': '%s direct teleport could not be started',
        'npc_script_failed': 'NPC script could not be started',
        'exit_walk_failed': 'Could not start walking to the exit stone',
        'exit_stone_missing': 'Teleport Stone was not found nearby',
        'trace_failed': 'Could not start leader tracing',
        'role_leader': 'Leader',
        'role_member': 'Member'
    },
    'tr': {
        'subtitle': 'v%s · Parti dungeon koordinatörü',
        'language_switch': '🇬🇧 English',
        'party_settings': '⚙ PARTİ AYARLARI',
        'leader': '👑 Lider karakter', 'timeout': '⏱ Zaman aşımı',
        'seconds': 'saniye', 'save': '💾 Kaydet',
        'entry_script': '📜 Giriş scripti', 'refresh': '↻ Yenile',
        'select_script': '-- Script seç --', 'loop_enable': '🔁 Loop etkinleştir',
        'total_loops': 'Toplam loop', 'minimum_characters': 'Minimum toplam karakter',
        'stable_party': '30 sn kararlı parti', 'controls': '🎮 ÇALIŞMA KONTROLLERİ',
        'start_script': '▶ Script ile Başlat', 'ticket_ready': '⚡ Ticket Hazır',
        'stop': '⏹ Durdur',
        'flow': 'Lider girer → üyeler girer → Trace → orta nokta → 6 mühür',
        'live_status': '📡 CANLI DURUM', 'ready': 'Hazır',
        'inside': '👥 İçeride: %d / %d', 'loop': '🔁 Loop: %d/%d',
        'loop_off': '🔁 Loop kapalı', 'setup_note_title': 'ℹ Kurulum notu:',
        'loop_ready_timer': '🔁 %d/%d hazır · %d/30 sn',
        'loop_party_verified': '🔁 Parti: %d/%d doğrulandı',
        'setup_note': 'Plugin tüm parti karakterlerinde yüklü olmalı ve her karakterde aynı lider adı kaydedilmelidir.',
        'settings_saved': 'Ayarlar kaydedildi.', 'settings_save_failed': 'Ayarlar kaydedilemedi: %s',
        'settings_load_failed': 'Ayarlar okunamadı: %s', 'scripts_found': '%d giriş scripti bulundu: %s',
        'manual_stop': 'Manuel durduruldu', 'leader_entering': 'Lider %s ile giriyor',
        'entry_script_mode': 'giriş scripti', 'direct_mode': 'direkt teleport',
        'leader_inside': 'Lider içeride; üyeler bekleniyor',
        'activating': 'Üyeler takipte; lider mühürleri etkinleştiriyor',
        'combat': 'Mühürler açıldı; 5 unique izleniyor',
        'unique_dead': 'Unique öldü: %d/5', 'looting': '5/5 unique öldü; 30 sn loot bekleniyor',
        'exit_prep': 'Çıkış taşına yaklaşılıyor', 'exit_wait_leader': 'Çıkış konumunda; lider bekleniyor',
        'exit_selected': 'Teleport Stone seçildi; onay bekleniyor',
        'exit_confirm': 'Çıkış onayı hazırlanıyor', 'exit_sent': 'Çıkış onayı gönderildi',
        'member_waiting': 'Lider bekleniyor; mod: %s', 'member_entering': 'Üye dungeon girişi yapılıyor',
        'member_inside': 'İçeride; INSIDE onayı hazırlanıyor', 'tracing': 'Lider takip ediliyor: %s',
        'waiting_party': 'Sonraki loop için parti yeniden kuruluyor',
        'loop_direct': 'Loop %d/%d direkt giriş', 'loop_exit_done': 'Loop %d çıkışı tamam; parti bekleniyor',
        'loop_done': 'Loop tamamlandı: %d/%d', 'dungeon_done': 'Dungeon çıkışı tamamlandı',
        'leader_abort': 'Lider işlemi iptal etti', 'timeout_failed': 'Zaman aşımı',
        'disconnected': 'Bağlantı kesildi', 'script_required': 'Önce geçerli bir giriş scripti seçin',
        'script_missing': 'Giriş scripti bulunamadı: %s', 'script_empty': 'Giriş scripti boş: %s',
        'script_invalid': 'Geçersiz giriş scripti yolu',
        'script_start_failed': '%s giriş scripti başlatılamadı', 'script_error': 'Giriş scripti hatası: %s',
        'direct_failed': '%s direkt teleport başlatılamadı', 'npc_script_failed': 'NPC scripti başlatılamadı',
        'exit_walk_failed': 'Çıkış taşına yürüyüş başlatılamadı',
        'exit_stone_missing': 'Teleport Stone yakında bulunamadı',
        'trace_failed': 'Lider takibi başlatılamadı', 'role_leader': 'Lider', 'role_member': 'Üye'
    }
}


def tr(key, *args):
    value = TEXT.get(language, TEXT['en']).get(key, TEXT['en'].get(key, key))
    return value % args if args else value

ACTIVATION_SCRIPT = '''FCVS_DELAY
walk,-32742,-19486,98,-134
npc,Sacrificed Slave
FCVS_DELAY
npc,Sealing Stone of Tigerwoman
FCVS_DELAY
npc,Sealing Stone of Cerberus
FCVS_DELAY
npc,Sealing Stone of Captain Ivy
FCVS_DELAY
npc,Sealing Stone of Uruchi
FCVS_DELAY
npc,Sealing Stone of Isyutaru
FCVS_FINISHED'''
EXIT_WALK_SCRIPT = '''walk,-32742,-19488,113,-134
FCVS_EXIT_READY'''

state = STATE_IDLE
run_id = ''
active_leader = ''
expected_members = set()
inside_members = set()
entry_region = None
deadline = 0.0
loot_exit_at = 0.0
unique_uids = {}
dead_uniques = set()
exit_ready_members = set()
exit_npc_uid = 0
exit_select_pending = False
exit_confirm_at = 0.0
direct_entry_mode = False
ready_retry_at = 0.0
ready_retry_count = 0
inside_retry_at = 0.0
inside_retry_count = 0
loop_active = False
loop_session_id = ''
current_loop = 0
completed_loops = 0
loop_target = 1
exit_verified_loop = 0
loop_ready_members = set()
party_stable_since = 0.0
loop_sync_at = 0.0

STATE_COLORS = {
    STATE_IDLE: COLOR_INFO,
    STATE_LEADER_ENTERING: COLOR_WARNING,
    STATE_MEMBER_WAITING: COLOR_WARNING,
    STATE_MEMBER_ENTERING: COLOR_WARNING,
    STATE_WAITING_MEMBERS: COLOR_INFO,
    STATE_ACTIVATING: COLOR_PRIMARY,
    STATE_COMBAT: COLOR_SUCCESS,
    STATE_LOOTING: COLOR_WARNING,
    STATE_EXIT_PREP: COLOR_WARNING,
    STATE_EXITING: COLOR_PRIMARY,
    STATE_WAITING_PARTY: COLOR_WARNING,
    STATE_DONE: COLOR_SUCCESS,
    STATE_FAILED: COLOR_DANGER
}

STATE_ICONS = {
    STATE_IDLE: '●',
    STATE_LEADER_ENTERING: '🚪',
    STATE_MEMBER_WAITING: '⏳',
    STATE_MEMBER_ENTERING: '🚪',
    STATE_WAITING_MEMBERS: '👥',
    STATE_ACTIVATING: '⚡',
    STATE_COMBAT: '⚔',
    STATE_LOOTING: '⏳',
    STATE_EXIT_PREP: '🚶',
    STATE_EXITING: '🚪',
    STATE_WAITING_PARTY: '👥',
    STATE_DONE: '✅',
    STATE_FAILED: '❌'
}


def _own_name():
    return (get_character_data() or {}).get('name', '')


def _config_path():
    character = get_character_data() or {}
    server = str(character.get('server') or 'Unknown')
    name = str(character.get('name') or 'Unknown')
    for invalid in '<>:"/\\|?*':
        server = server.replace(invalid, '_')
        name = name.replace(invalid, '_')
    return os.path.join(get_config_dir(), pName, server, name + '.json')


def _scripts_path():
    return os.path.join(get_config_dir(), pName, 'Script')


def _leader_name():
    return QtBind.text(gui, tbxLeader).strip()


def _entry_script_name():
    return QtBind.text(gui, cmbEntryScript).strip()


def _entry_script_selected():
    value = _entry_script_name()
    return bool(value and value not in (TEXT['en']['select_script'],
                                        TEXT['tr']['select_script']))


def _timeout_seconds():
    try:
        return max(15, min(600, int(QtBind.text(gui, tbxTimeout).strip())))
    except Exception:
        return 120


def _loop_count_setting():
    try:
        return max(1, min(5, int(QtBind.text(gui, tbxLoopCount).strip())))
    except Exception:
        return 5


def _min_total_setting():
    try:
        return max(1, min(8, int(QtBind.text(gui, tbxMinTotal).strip())))
    except Exception:
        return 4


def _set_status(new_state, detail):
    global state
    state = new_state
    color = STATE_COLORS.get(new_state, COLOR_INFO)
    icon = STATE_ICONS.get(new_state, '●')
    QtBind.setText(gui, lblStatus,
        '<table width="440" cellspacing="0" cellpadding="0"><tr><td>'
        '<font color="%s"><b>%s %s</b></font>'
        '<font color="%s"> · %s</font></td></tr></table>' %
        (color, icon, new_state, COLOR_TEXT, detail))
    _update_counts()
    log('[%s] %s - %s' % (pName, new_state, detail))


def _update_counts():
    complete = bool(expected_members) and expected_members.issubset(inside_members)
    color = COLOR_SUCCESS if complete else COLOR_INFO
    QtBind.setText(gui, lblCounts,
        '<font color="%s"><b>%s</b></font>' %
        (color, tr('inside', len(inside_members), len(expected_members))))
    if loop_active:
        QtBind.setText(gui, lblLoop,
            '<font color="%s"><b>%s</b></font>' %
            (COLOR_PRIMARY, tr('loop', completed_loops, loop_target)))
    else:
        QtBind.setText(gui, lblLoop,
            '<font color="%s">%s</font>' % (COLOR_MUTED, tr('loop_off')))


def _send(command, argument=''):
    if not run_id:
        return False
    message = '%s|%s|%s' % (PROTOCOL, run_id, command)
    if argument:
        message += '|' + str(argument)
    result = phBotChat.Party(message)
    log('[%s] Party protocol sent: %s (result=%s)' %
        (pName, command, result))
    return result


def _position_region():
    position = get_position() or {}
    return position.get('region')


def _party_member_names():
    own = _own_name().lower()
    names = set()
    for member in (get_party() or {}).values():
        name = str(member.get('name') or '').strip()
        if name and name.lower() != own:
            names.add(name.lower())
    return names


def _reset(detail=None):
    global run_id, active_leader, entry_region, deadline, loot_exit_at
    global exit_npc_uid, exit_select_pending, exit_confirm_at, direct_entry_mode
    global ready_retry_at, ready_retry_count, inside_retry_at, inside_retry_count
    global loop_active, loop_session_id, current_loop, completed_loops
    global loop_target, exit_verified_loop, party_stable_since, loop_sync_at
    stop_script()
    stop_trace()
    run_id = ''
    active_leader = ''
    entry_region = None
    deadline = 0.0
    loot_exit_at = 0.0
    exit_npc_uid = 0
    exit_select_pending = False
    exit_confirm_at = 0.0
    direct_entry_mode = False
    ready_retry_at = 0.0
    ready_retry_count = 0
    inside_retry_at = 0.0
    inside_retry_count = 0
    loop_active = False
    loop_session_id = ''
    current_loop = 0
    completed_loops = 0
    loop_target = 1
    exit_verified_loop = 0
    party_stable_since = 0.0
    loop_sync_at = 0.0
    expected_members.clear()
    inside_members.clear()
    unique_uids.clear()
    dead_uniques.clear()
    exit_ready_members.clear()
    loop_ready_members.clear()
    _set_status(STATE_IDLE, detail or tr('ready'))


def save_config():
    try:
        path = _config_path()
        folder = os.path.dirname(path)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(path, 'w', encoding='utf-8') as handle:
            json.dump({'leader': _leader_name(),
                       'timeout': _timeout_seconds(),
                       'entry_script': _entry_script_name(),
                       'loop_enabled': QtBind.isChecked(gui, cbxLoopEnabled),
                       'loop_count': _loop_count_setting(),
                       'min_total': _min_total_setting(),
                       'language': language}, handle, indent=4)
        log('[%s] %s' % (pName, tr('settings_saved')))
    except Exception as ex:
        log('[%s] %s' % (pName, tr('settings_save_failed', ex)))


def load_config():
    global language
    try:
        path = _config_path()
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
        language = data.get('language', 'en')
        if language not in ('en', 'tr'):
            language = 'en'
        QtBind.setText(gui, tbxLeader, str(data.get('leader') or ''))
        QtBind.setText(gui, tbxTimeout, str(data.get('timeout') or 120))
        QtBind.setChecked(gui, cbxLoopEnabled, bool(data.get('loop_enabled', False)))
        QtBind.setText(gui, tbxLoopCount, str(data.get('loop_count') or 5))
        QtBind.setText(gui, tbxMinTotal, str(data.get('min_total') or 4))
        selected_script = str(data.get('entry_script') or '')
        refresh_scripts(selected_script)
        apply_gui_language()
    except Exception as ex:
        log('[%s] %s' % (pName, tr('settings_load_failed', ex)))


def btnSave_clicked():
    save_config()


def btnLanguage_clicked():
    global language
    language = 'tr' if language == 'en' else 'en'
    apply_gui_language()
    save_config()


def _ensure_scripts_folder():
    try:
        folder = _scripts_path()
        if not os.path.exists(folder):
            os.makedirs(folder)
        return True
    except Exception as ex:
        log('[%s] Script klasoru olusturulamadi: %s' % (pName, ex))
        return False


def refresh_scripts(preferred=None):
    selected = preferred or _entry_script_name()
    scripts = []
    try:
        _ensure_scripts_folder()
        for file_name in os.listdir(_scripts_path()):
            full_path = os.path.join(_scripts_path(), file_name)
            if os.path.isfile(full_path) and file_name.lower().endswith('.txt'):
                scripts.append(file_name)
        scripts.sort(key=lambda value: value.lower())
        QtBind.clear(gui, cmbEntryScript)
        QtBind.append(gui, cmbEntryScript, tr('select_script'))
        for file_name in scripts:
            QtBind.append(gui, cmbEntryScript, file_name)
        if selected in scripts:
            QtBind.setText(gui, cmbEntryScript, selected)
        else:
            QtBind.setText(gui, cmbEntryScript, tr('select_script'))
    except Exception as ex:
        log('[%s] Script listesi okunamadi: %s' % (pName, ex))
    return scripts


def btnRefreshScripts_clicked():
    scripts = refresh_scripts()
    log('[%s] %s' % (pName, tr('scripts_found', len(scripts), _scripts_path())))


def _start_entry_script(role):
    file_name = _entry_script_name()
    if not _entry_script_selected():
        _set_status(STATE_FAILED, tr('script_required'))
        return False
    if os.path.basename(file_name) != file_name:
        _set_status(STATE_FAILED, tr('script_invalid'))
        return False
    full_path = os.path.join(_scripts_path(), file_name)
    try:
        if not os.path.isfile(full_path):
            _set_status(STATE_FAILED, tr('script_missing', file_name))
            return False
        with open(full_path, 'r', encoding='utf-8-sig') as handle:
            content = handle.read()
        if not content.strip():
            _set_status(STATE_FAILED, tr('script_empty', file_name))
            return False
        stop_bot()
        stop_script()
        if start_script(content) is False:
            _set_status(STATE_FAILED, tr('script_start_failed', role))
            return False
        log('[%s] %s giris scripti baslatildi: %s' % (pName, role, full_path))
        return True
    except Exception as ex:
        _set_status(STATE_FAILED, tr('script_error', ex))
        return False


def _start_direct_entry(role):
    stop_bot()
    stop_script()
    if start_script(DIRECT_TELEPORT_SCRIPT) is False:
        _set_status(STATE_FAILED, tr('direct_failed', role))
        return False
    log('[%s] %s direkt Chamber teleportu baslatildi.' % (pName, role))
    return True


def _loop_metadata():
    if not loop_active:
        return '0,,1,1'
    return '1,%s,%d,%d' % (loop_session_id, current_loop, loop_target)


def _start_run(use_direct_entry):
    global run_id, active_leader, entry_region, deadline, direct_entry_mode
    global loop_active, loop_session_id, current_loop, completed_loops
    global loop_target, exit_verified_loop, party_stable_since, loop_sync_at
    own = _own_name()
    leader = _leader_name()
    if not own:
        log('[%s] Karakter verisi henuz hazir degil.' % pName)
        return
    if not leader:
        log('[%s] Once lider adini girin.' % pName)
        return
    if own.lower() != leader.lower():
        log('[%s] Baslat dugmesini yalnizca ayarlanan lider kullanabilir.' % pName)
        return
    if state not in (STATE_IDLE, STATE_DONE, STATE_FAILED):
        log('[%s] Zaten aktif bir calisma var.' % pName)
        return

    if (not use_direct_entry and
            (not _entry_script_selected() or
             not os.path.isfile(os.path.join(_scripts_path(), _entry_script_name())))):
        _set_status(STATE_FAILED, tr('script_required'))
        return
    stop_bot()
    stop_script()
    expected_members.clear()
    expected_members.update(_party_member_names())
    inside_members.clear()
    run_id = '%s-%d' % (own.lower(), int(time.time()))
    active_leader = own
    loop_active = QtBind.isChecked(gui, cbxLoopEnabled)
    loop_session_id = run_id if loop_active else ''
    current_loop = 1
    completed_loops = 0
    loop_target = _loop_count_setting() if loop_active else 1
    exit_verified_loop = 0
    party_stable_since = 0.0
    loop_sync_at = 0.0
    loop_ready_members.clear()
    direct_entry_mode = bool(use_direct_entry)
    entry_region = _position_region()
    deadline = time.time() + _timeout_seconds()
    mode_text = tr('direct_mode') if direct_entry_mode else tr('entry_script_mode')
    _set_status(STATE_LEADER_ENTERING, tr('leader_entering', mode_text))
    _send('START_DIRECT' if direct_entry_mode else 'START', _loop_metadata())
    started = (_start_direct_entry(tr('role_leader')) if direct_entry_mode
               else _start_entry_script(tr('role_leader')))
    if not started:
        _send('ABORT')


def btnStart_clicked():
    _start_run(False)


def btnDirectStart_clicked():
    _start_run(True)


def btnStop_clicked():
    if run_id and _own_name().lower() == active_leader.lower():
        _send('ABORT')
    _reset(tr('manual_stop'))


def _begin_waiting_party():
    global deadline, party_stable_since, loop_sync_at
    deadline = 0.0
    party_stable_since = 0.0
    loop_sync_at = time.time() + 1.0
    loop_ready_members.clear()
    _set_status(STATE_WAITING_PARTY, tr('waiting_party'))


def _start_next_loop():
    global run_id, direct_entry_mode, entry_region, deadline, current_loop
    global party_stable_since, loop_sync_at
    own = _own_name()
    current_loop = completed_loops + 1
    run_id = '%s-%d-%d' % (own.lower(), int(time.time()), current_loop)
    direct_entry_mode = True
    expected_members.clear()
    expected_members.update(_party_member_names())
    inside_members.clear()
    unique_uids.clear()
    dead_uniques.clear()
    exit_ready_members.clear()
    loop_ready_members.clear()
    party_stable_since = 0.0
    loop_sync_at = 0.0
    entry_region = _position_region()
    deadline = time.time() + _timeout_seconds()
    _set_status(STATE_LEADER_ENTERING, tr('loop_direct', current_loop, loop_target))
    _send('START_DIRECT', _loop_metadata())
    if not _start_direct_entry(tr('role_leader')):
        _send('ABORT')


def _apply_loop_metadata(argument):
    global loop_active, loop_session_id, current_loop, loop_target
    try:
        values = argument.split(',')
        loop_active = len(values) >= 1 and values[0] == '1'
        if loop_active:
            loop_session_id = values[1]
            current_loop = int(values[2])
            loop_target = int(values[3])
        else:
            loop_session_id = ''
            current_loop = 1
            loop_target = 1
        return True
    except Exception:
        loop_active = False
        loop_session_id = ''
        current_loop = 1
        loop_target = 1
        return False


def _leader_inside():
    global deadline, ready_retry_at, ready_retry_count
    stop_script()
    deadline = time.time() + _timeout_seconds()
    ready_retry_at = time.time() + 1.5
    ready_retry_count = 0
    _set_status(STATE_WAITING_MEMBERS, tr('leader_inside'))
    if not expected_members:
        ready_retry_at = 0.0
        _start_activation()


def _start_activation():
    global deadline
    stop_script()
    deadline = 0.0
    unique_uids.clear()
    dead_uniques.clear()
    _set_status(STATE_ACTIVATING, tr('activating'))
    _send('TRACE')
    if start_script(ACTIVATION_SCRIPT) is False:
        _set_status(STATE_FAILED, tr('npc_script_failed'))


# Walk script callback: bir sonraki satirdan once 2000 ms bekletir.
def FCVS_DELAY(args):
    return 2000


def FCVS_FINISHED(args):
    global deadline
    deadline = 0.0
    _set_status(STATE_COMBAT, tr('combat'))
    return 0


def _start_loot_wait():
    global loot_exit_at
    if state not in (STATE_ACTIVATING, STATE_COMBAT):
        return
    loot_exit_at = time.time() + LOOT_WAIT_SECONDS
    _set_status(STATE_LOOTING, tr('looting'))


def _run_exit_walk():
    stop_bot()
    stop_trace()
    stop_script()
    if start_script(EXIT_WALK_SCRIPT) is False:
        _set_status(STATE_FAILED, tr('exit_walk_failed'))
        return False
    return True


def _begin_exit_prep():
    global deadline, loot_exit_at
    loot_exit_at = 0.0
    exit_ready_members.clear()
    deadline = time.time() + _timeout_seconds()
    _set_status(STATE_EXIT_PREP, tr('exit_prep'))
    _send('EXIT_PREP')
    _run_exit_walk()


def FCVS_EXIT_READY(args):
    if state != STATE_EXIT_PREP:
        return 0
    if _own_name().lower() == active_leader.lower():
        exit_ready_members.add('__leader__')
        _leader_check_exit_ready()
    else:
        _send('EXIT_READY')
        _set_status(STATE_EXIT_PREP, tr('exit_wait_leader'))
    return 0


def _leader_check_exit_ready():
    if (_own_name().lower() == active_leader.lower() and
            '__leader__' in exit_ready_members and
            expected_members.issubset(exit_ready_members)):
        _send('EXIT_NOW')
        _select_exit_stone()


def _select_exit_stone():
    global exit_npc_uid, exit_select_pending, exit_confirm_at, deadline
    position = get_position() or {}
    nearest_uid = 0
    nearest_distance = None
    for uid, npc in (get_npcs() or {}).items():
        if str(npc.get('servername') or '') != EXIT_SERVERNAME:
            continue
        try:
            distance = GetDistance(position['x'], position['y'], npc['x'], npc['y'])
        except Exception:
            distance = 0.0
        if nearest_distance is None or distance < nearest_distance:
            nearest_uid = int(uid)
            nearest_distance = distance
    if not nearest_uid:
        _set_status(STATE_FAILED, tr('exit_stone_missing'))
        return False
    stop_bot()
    stop_trace()
    stop_script()
    exit_npc_uid = nearest_uid
    exit_select_pending = True
    exit_confirm_at = 0.0
    deadline = time.time() + 20.0
    _set_status(STATE_EXITING, tr('exit_selected'))
    inject_joymax(0x7045, struct.pack('<I', exit_npc_uid), False)
    return True


def handle_chat(t, player, msg):
    global run_id, active_leader, entry_region, deadline, direct_entry_mode
    global inside_retry_at, completed_loops
    if t != CHAT_PARTY or not player or not msg or not msg.startswith(PROTOCOL + '|'):
        return False
    parts = msg.split('|', 3)
    if len(parts) < 3:
        return True
    incoming_run = parts[1]
    command = parts[2].upper()
    argument = parts[3] if len(parts) == 4 else ''
    configured_leader = _leader_name()

    if command in ('START', 'START_DIRECT'):
        if not configured_leader or player.lower() != configured_leader.lower():
            return True
        if _own_name().lower() == player.lower():
            return True
        stop_bot()
        stop_script()
        run_id = incoming_run
        active_leader = player
        direct_entry_mode = command == 'START_DIRECT'
        _apply_loop_metadata(argument)
        completed_loops = max(0, current_loop - 1)
        entry_region = _position_region()
        deadline = time.time() + _timeout_seconds()
        expected_members.clear()
        inside_members.clear()
        mode_text = tr('direct_mode') if direct_entry_mode else tr('entry_script_mode')
        _set_status(STATE_MEMBER_WAITING, tr('member_waiting', mode_text))
        return True

    if not run_id or incoming_run != run_id:
        return True
    if command in ('READY', 'TRACE', 'EXIT_PREP', 'EXIT_NOW', 'LOOP_SYNC', 'ABORT') and player.lower() != active_leader.lower():
        return True

    if command == 'READY' and state == STATE_MEMBER_WAITING:
        entry_region = _position_region()
        deadline = time.time() + _timeout_seconds()
        _set_status(STATE_MEMBER_ENTERING, tr('member_entering'))
        if direct_entry_mode:
            _start_direct_entry(tr('role_member'))
        else:
            _start_entry_script(tr('role_member'))
    elif command == 'INSIDE' and state == STATE_WAITING_MEMBERS:
        sender = player.lower()
        if sender in expected_members:
            inside_members.add(sender)
            _update_counts()
            if expected_members.issubset(inside_members):
                _start_activation()
    elif command == 'TRACE' and _own_name().lower() != active_leader.lower():
        inside_retry_at = 0.0
        stop_bot()
        if start_trace(active_leader):
            _set_status(STATE_COMBAT, tr('tracing', active_leader))
        else:
            _set_status(STATE_FAILED, tr('trace_failed'))
    elif command == 'EXIT_PREP' and _own_name().lower() != active_leader.lower():
        deadline = time.time() + _timeout_seconds()
        _set_status(STATE_EXIT_PREP, tr('exit_prep'))
        _run_exit_walk()
    elif command == 'EXIT_READY' and _own_name().lower() == active_leader.lower():
        sender = player.lower()
        if sender in expected_members:
            exit_ready_members.add(sender)
            _leader_check_exit_ready()
    elif command == 'EXIT_NOW' and _own_name().lower() != active_leader.lower():
        _select_exit_stone()
    elif command == 'LOOP_SYNC' and _own_name().lower() != active_leader.lower():
        try:
            sync_session, sync_loop = argument.split(',', 1)
            sync_loop = int(sync_loop)
            if (loop_active and sync_session == loop_session_id and
                    exit_verified_loop >= sync_loop and
                    _position_region() == EXIT_REGION):
                _send('LOOP_READY', '%s,%d' % (loop_session_id, sync_loop))
        except Exception:
            pass
    elif command == 'LOOP_READY' and _own_name().lower() == active_leader.lower():
        try:
            ready_session, ready_loop = argument.split(',', 1)
            if (state == STATE_WAITING_PARTY and
                    ready_session == loop_session_id and
                    int(ready_loop) == completed_loops):
                loop_ready_members.add(player.lower())
        except Exception:
            pass
    elif command == 'ABORT':
        _reset(tr('leader_abort'))
    return True


def handle_event(t, data):
    if (t == 0 and state in (STATE_ACTIVATING, STATE_COMBAT) and
            _own_name().lower() == active_leader.lower()):
        name = str(data or '').strip().lower()
        if name in UNIQUE_NAMES:
            log('[%s] Unique spawn: %s' % (pName, data))


def handle_joymax(opcode, data):
    global exit_select_pending, exit_confirm_at
    if (opcode == 0x30BF and len(data) >= 6 and
            state in (STATE_ACTIVATING, STATE_COMBAT) and
            _own_name().lower() == active_leader.lower() and
            data[4] == 0 and data[5] == 2):
        try:
            uid = struct.unpack_from('<I', data, 0)[0]
            for name, tracked_uid in list(unique_uids.items()):
                if tracked_uid == uid and name not in dead_uniques:
                    dead_uniques.add(name)
                    _set_status(state, tr('unique_dead', len(dead_uniques)))
                    if len(dead_uniques) == len(UNIQUE_NAMES):
                        _start_loot_wait()
                    break
        except Exception as ex:
            log('[%s] Unique olum paketi okunamadi: %s' % (pName, ex))

    if opcode == 0xB045 and state == STATE_EXITING and exit_select_pending:
        try:
            if len(data) >= 5 and data[0] == 1:
                selected_uid = struct.unpack_from('<I', data, 1)[0]
                if selected_uid == exit_npc_uid:
                    exit_select_pending = False
                    exit_confirm_at = time.time() + 0.5
                    _set_status(STATE_EXITING, tr('exit_confirm'))
        except Exception as ex:
            log('[%s] Cikis NPC cevabi okunamadi: %s' % (pName, ex))
    return True


def teleported():
    global deadline, inside_retry_at, inside_retry_count
    global exit_verified_loop, completed_loops
    current_region = _position_region()
    if state == STATE_EXITING:
        if current_region == EXIT_REGION:
            deadline = 0.0
            exit_verified_loop = current_loop
            completed_loops = max(completed_loops, current_loop)
            if loop_active and current_loop < loop_target:
                if _own_name().lower() == active_leader.lower():
                    _begin_waiting_party()
                else:
                    _set_status(STATE_DONE, tr('loop_exit_done', current_loop))
            elif loop_active:
                _set_status(STATE_DONE, tr('loop_done', completed_loops, loop_target))
            else:
                _set_status(STATE_DONE, tr('dungeon_done'))
        return
    if state not in (STATE_LEADER_ENTERING, STATE_MEMBER_ENTERING):
        return
    if current_region != CHAMBER_REGION:
        return
    if state == STATE_LEADER_ENTERING:
        _leader_inside()
    else:
        stop_script()
        deadline = 0.0
        inside_retry_at = time.time() + 1.5
        inside_retry_count = 0
        _set_status(STATE_DONE, tr('member_inside'))


def event_loop():
    global deadline, exit_confirm_at, ready_retry_at, ready_retry_count
    global inside_retry_at, inside_retry_count
    global party_stable_since, loop_sync_at
    now = time.time()

    if (state == STATE_WAITING_PARTY and loop_active and
            _own_name().lower() == active_leader.lower()):
        party_names = _party_member_names()
        if party_names and now >= loop_sync_at:
            _send('LOOP_SYNC', '%s,%d' % (loop_session_id, completed_loops))
            loop_sync_at = now + 2.0
        verified_names = loop_ready_members.intersection(party_names)
        verified_total = 1 + len(verified_names)
        required_total = _min_total_setting()
        if verified_total >= required_total:
            if not party_stable_since:
                party_stable_since = now
                log('[%s] Loop partisi yeterli: %d/%d; 30 sn sayac basladi.' %
                    (pName, verified_total, required_total))
            stable_seconds = int(now - party_stable_since)
            QtBind.setText(gui, lblLoop,
                '<font color="%s"><b>%s</b></font>' %
                (COLOR_WARNING, tr('loop_ready_timer', verified_total,
                                   required_total, min(30, stable_seconds))))
            if stable_seconds >= 30:
                _start_next_loop()
                return
        else:
            if party_stable_since:
                log('[%s] Loop parti sayaci sifirlandi: %d/%d.' %
                    (pName, verified_total, required_total))
            party_stable_since = 0.0
            QtBind.setText(gui, lblLoop,
                '<font color="%s"><b>%s</b></font>' %
                (COLOR_WARNING, tr('loop_party_verified', verified_total,
                                   required_total)))

    if (state == STATE_WAITING_MEMBERS and ready_retry_at and
            now >= ready_retry_at and ready_retry_count < 5):
        _send('READY')
        ready_retry_count += 1
        ready_retry_at = now + 2.0 if ready_retry_count < 5 else 0.0

    if (inside_retry_at and now >= inside_retry_at and inside_retry_count < 5):
        _send('INSIDE')
        inside_retry_count += 1
        inside_retry_at = now + 2.0 if inside_retry_count < 5 else 0.0

    if (state in (STATE_ACTIVATING, STATE_COMBAT) and
            _own_name().lower() == active_leader.lower()):
        for uid, monster in (get_monsters() or {}).items():
            name = str(monster.get('name') or '').strip().lower()
            if name in UNIQUE_NAMES and name not in unique_uids:
                unique_uids[name] = int(uid)
                log('[%s] Unique UID kaydedildi: %s=%s' % (pName, name, uid))

    if (state == STATE_LOOTING and loot_exit_at and now >= loot_exit_at and
            _own_name().lower() == active_leader.lower()):
        _begin_exit_prep()

    if state == STATE_EXITING and exit_confirm_at and now >= exit_confirm_at:
        exit_confirm_at = 0.0
        inject_joymax(0x766A, b'\x03', False)
        _set_status(STATE_EXITING, tr('exit_sent'))

    if deadline and now >= deadline:
        deadline = 0.0
        if run_id and _own_name().lower() == active_leader.lower():
            _send('ABORT')
        stop_script()
        _set_status(STATE_FAILED, tr('timeout_failed'))


def joined_game():
    load_config()


def disconnected():
    if state not in (STATE_IDLE, STATE_DONE, STATE_FAILED):
        _set_status(STATE_FAILED, tr('disconnected'))


def finished():
    stop_script()


gui = QtBind.init(__name__, pName)
QtBind.createLabel(gui,
    '<font color="%s" size="4"><b>🏰 CHAMBER OF VICIOUS SHADOWS</b></font>' %
    COLOR_PRIMARY, 12, 8)
lblSubtitle = QtBind.createLabel(gui,
    '<font color="%s">v%s · Party dungeon coordinator</font>' %
    (COLOR_MUTED, pVersion), 325, 14)
QtBind.createLabel(gui, u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' %
                   COLOR_PRIMARY, 510, 13)
btnLanguage = QtBind.createButton(gui, 'btnLanguage_clicked', '', 650, 8)
QtBind.createLineEdit(gui, '', 12, 34, 716, 1)

lblPartySettings = QtBind.createLabel(gui,
    '<font color="%s"><b>⚙ PARTİ AYARLARI</b></font>' % COLOR_PRIMARY, 12, 45)
lblLeader = QtBind.createLabel(gui, '<font color="%s"><b>👑 Lider karakter</b></font>' %
                   COLOR_MUTED, 12, 72)
tbxLeader = QtBind.createLineEdit(gui, '', 125, 67, 170, 22)
lblTimeout = QtBind.createLabel(gui, '<font color="%s"><b>⏱ Timeout</b></font>' %
                   COLOR_MUTED, 320, 72)
tbxTimeout = QtBind.createLineEdit(gui, '120', 400, 67, 48, 22)
lblSeconds = QtBind.createLabel(gui, '<font color="%s">saniye</font>' % COLOR_MUTED, 454, 72)
btnSave = QtBind.createButton(gui, 'btnSave_clicked', '💾 Kaydet', 535, 66)
lblEntryScript = QtBind.createLabel(gui, '<font color="%s"><b>📜 Giriş scripti</b></font>' %
                   COLOR_MUTED, 12, 105)
cmbEntryScript = QtBind.createCombobox(gui, 125, 100, 360, 22)
btnRefresh = QtBind.createButton(gui, 'btnRefreshScripts_clicked', '↻ Yenile', 500, 99)
cbxLoopEnabled = QtBind.createCheckBox(gui, 'noop_checked', '🔁 Loop etkinleştir', 12, 132)
lblTotalLoops = QtBind.createLabel(gui, '<font color="%s">Toplam loop</font>' % COLOR_MUTED, 185, 136)
tbxLoopCount = QtBind.createLineEdit(gui, '5', 260, 131, 35, 22)
lblMinTotal = QtBind.createLabel(gui, '<font color="%s">Minimum toplam karakter</font>' %
                   COLOR_MUTED, 320, 136)
tbxMinTotal = QtBind.createLineEdit(gui, '4', 465, 131, 35, 22)
lblStableParty = QtBind.createLabel(gui, '<font color="%s">30 sn kararlı parti</font>' %
                   COLOR_MUTED, 525, 136)
QtBind.createLineEdit(gui, '', 12, 161, 716, 1)

lblControls = QtBind.createLabel(gui,
    '<font color="%s"><b>🎮 ÇALIŞMA KONTROLLERİ</b></font>' % COLOR_PRIMARY,
    12, 173)
btnStart = QtBind.createButton(gui, 'btnStart_clicked', '▶ Script ile Başlat', 12, 198)
btnDirectStart = QtBind.createButton(gui, 'btnDirectStart_clicked', '⚡ Ticket Hazır', 155, 198)
btnStop = QtBind.createButton(gui, 'btnStop_clicked', '⏹ Durdur', 280, 198)
lblFlow = QtBind.createLabel(gui,
    '<font color="%s">Lider girer → üyeler girer → Trace → orta nokta → 6 mühür</font>' %
    COLOR_MUTED, 380, 204)
QtBind.createLineEdit(gui, '', 12, 234, 716, 1)

lblLiveStatus = QtBind.createLabel(gui,
    '<font color="%s"><b>📡 CANLI DURUM</b></font>' % COLOR_PRIMARY, 12, 247)
lblStatus = QtBind.createLabel(gui,
    '<table width="440" cellspacing="0" cellpadding="0"><tr><td>'
    '<font color="%s"><b>● IDLE</b></font>'
    '<font color="%s"> · Hazır</font></td></tr></table>' %
    (COLOR_INFO, COLOR_TEXT), 12, 275)
lblCounts = QtBind.createLabel(gui,
    '<font color="%s"><b>👥 İçeride: 0 / 0</b></font>' % COLOR_INFO, 510, 275)
lblLoop = QtBind.createLabel(gui,
    '<font color="%s">🔁 Loop kapalı</font>' % COLOR_MUTED, 510, 298)

lblSetupNote = QtBind.createLabel(gui,
    '<table width="700" cellspacing="0" cellpadding="4"><tr><td>'
    '<font color="%s"><b>ℹ Kurulum notu:</b></font> '
    '<font color="%s">Plugin tüm parti karakterlerinde yüklü olmalı ve '
    'her karakterde aynı lider adı kaydedilmelidir.</font>'
    '</td></tr></table>' % (COLOR_INFO, COLOR_TEXT), 12, 315)


def apply_gui_language():
    QtBind.setText(gui, lblSubtitle,
                   '<font color="%s">%s</font>' %
                   (COLOR_MUTED, tr('subtitle', pVersion)))
    QtBind.setText(gui, btnLanguage, tr('language_switch'))
    QtBind.setText(gui, lblPartySettings,
                   '<font color="%s"><b>%s</b></font>' % (COLOR_PRIMARY, tr('party_settings')))
    QtBind.setText(gui, lblLeader, '<font color="%s"><b>%s</b></font>' % (COLOR_MUTED, tr('leader')))
    QtBind.setText(gui, lblTimeout, '<font color="%s"><b>%s</b></font>' % (COLOR_MUTED, tr('timeout')))
    QtBind.setText(gui, lblSeconds, '<font color="%s">%s</font>' % (COLOR_MUTED, tr('seconds')))
    QtBind.setText(gui, btnSave, tr('save'))
    QtBind.setText(gui, lblEntryScript, '<font color="%s"><b>%s</b></font>' % (COLOR_MUTED, tr('entry_script')))
    QtBind.setText(gui, btnRefresh, tr('refresh'))
    QtBind.setText(gui, cbxLoopEnabled, tr('loop_enable'))
    QtBind.setText(gui, lblTotalLoops, '<font color="%s">%s</font>' % (COLOR_MUTED, tr('total_loops')))
    QtBind.setText(gui, lblMinTotal, '<font color="%s">%s</font>' % (COLOR_MUTED, tr('minimum_characters')))
    QtBind.setText(gui, lblStableParty, '<font color="%s">%s</font>' % (COLOR_MUTED, tr('stable_party')))
    QtBind.setText(gui, lblControls, '<font color="%s"><b>%s</b></font>' % (COLOR_PRIMARY, tr('controls')))
    QtBind.setText(gui, btnStart, tr('start_script'))
    QtBind.setText(gui, btnDirectStart, tr('ticket_ready'))
    QtBind.setText(gui, btnStop, tr('stop'))
    QtBind.setText(gui, lblFlow, '<font color="%s">%s</font>' % (COLOR_MUTED, tr('flow')))
    QtBind.setText(gui, lblLiveStatus, '<font color="%s"><b>%s</b></font>' % (COLOR_PRIMARY, tr('live_status')))
    QtBind.setText(gui, lblSetupNote,
        '<table width="700" cellspacing="0" cellpadding="4"><tr><td>'
        '<font color="%s"><b>%s</b></font> <font color="%s">%s</font>'
        '</td></tr></table>' % (COLOR_INFO, tr('setup_note_title'), COLOR_TEXT, tr('setup_note')))
    selected = _entry_script_name()
    if selected in (TEXT['en']['select_script'], TEXT['tr']['select_script']):
        refresh_scripts()
    _update_counts()
    if state == STATE_IDLE:
        _set_status(STATE_IDLE, tr('ready'))


def noop_checked(checked):
    pass

refresh_scripts()
apply_gui_language()
load_config()
log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
