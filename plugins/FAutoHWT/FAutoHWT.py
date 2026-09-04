# -*- coding: utf-8 -*-
from phBot import *
import QtBind
import phBotChat
import datetime
import json
import os
import time
import webbrowser


pName = 'FAutoHWT'
pVersion = '0.7.2'
LEGACY_PLUGIN_NAME = 'FHWTGate'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

CHAT_PRIVATE = 2
PROTOCOL = '#FHWTG'
PROTOCOL_VERSION = '6'

GATE_REGION = 19019
GATE_SERVERNAME = 'GATE_TOMB_GATE_IN'
GATE_MODEL = 25593
DEFAULT_GATE_DISTANCE = 50.0
PREPARE_RETRY_SECONDS = 4.0
PREPARE_MAX_ATTEMPTS = 3
ENTRY_TIMEOUT_SECONDS = 120
FCONTROL_ENTRY_GRACE_SECONDS = 8.0
TRACE_WAIT_SECONDS = 10.0
EXIT_TIMEOUT_SECONDS = 120.0
FINALIZE_TIMEOUT_SECONDS = 90.0
DEBUG_ENABLED = True

COLOR_PRIMARY = '#5b57e0'
COLOR_TEXT = '#2b3038'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#d93a4d'

STATE_IDLE = 'IDLE'
STATE_TRAVEL_PROFILE = 'TRAVEL_PROFILE'
STATE_TRAVELING = 'TRAVELING'
STATE_GATE_PROFILE = 'GATE_PROFILE'
STATE_GATE_READY = 'GATE_READY'
STATE_WAITING_PARTY = 'WAITING_PARTY'
STATE_LEADER_ENTERING = 'LEADER_ENTERING'
STATE_MEMBER_ENTERING = 'MEMBER_ENTERING'
STATE_WAITING_INSIDE = 'WAITING_INSIDE'
STATE_TRACE_WAIT = 'TRACE_WAIT'
STATE_RUNNING_HWT = 'RUNNING_HWT'
STATE_SCRIPT_FINISHED = 'SCRIPT_FINISHED'
STATE_WAITING_DUNGEON = 'WAITING_DUNGEON'
STATE_LEADER_EXITING = 'LEADER_EXITING'
STATE_WAITING_EXIT = 'WAITING_EXIT'
STATE_RETURNING_GATE = 'RETURNING_GATE'
STATE_FINALIZING = 'FINALIZING'
STATE_COMPLETE = 'COMPLETE'
STATE_FAILED = 'FAILED'

state = STATE_IDLE
active_run_id = ''
active_leader = ''
expected_members = set()
gate_ready_members = set()
inside_ready_members = set()
pending_prepare = []
prepare_acks = set()
prepare_attempts = {}
prepare_next_at = {}
deadline = 0.0
party_stable_since = 0.0
last_ready_send_at = 0.0
last_config_key = ''
last_validation_detail = ''
last_gate_debug = ''
last_party_debug = ''
pending_gate_detail = ''
profile_deadline = 0.0
schedule_screen = False
last_schedule_key = ''
schedule_next_check_at = 0.0
profile_candidates = []
inside_region = 0
last_inside_send_at = 0.0
last_enter_send_at = 0.0
active_difficulty = ''
active_teleport_language = ''
member_entry_command_at = 0.0
member_entry_command_started = False
active_start_mode = 'TRAVEL'
trace_start_at = 0.0
dungeon_ready_members = set()
outside_ready_members = set()
entry_blocked_members = set()
completed_runs = 0
leader_outside_ready = False
finalize_profile_deadline = 0.0
finalize_return_started = False
finalize_town_since = 0.0
early_finish_reason = ''

OFFSCREEN_X = 2000
SCHEDULE_MODES = ('Disabled', 'Daily', 'Selected days', 'One time')
DAY_KEYS = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
HWT_DIFFICULTIES = ('Beginner', 'Intermediate', 'Advanced')
TELEPORT_LANGUAGES = ('Auto', 'English', 'Turkish')


def fixed_width_text(content, width):
    return (
        '<table width="{0}" cellspacing="0" cellpadding="0">'
        '<tr><td>{1}</td></tr></table>'
    ).format(width, content)


def _safe_name(value):
    value = str(value or '').strip()
    for character in '<>:"/\\|?*':
        value = value.replace(character, '_')
    return value.strip(' .') or 'Unknown'


def _own_name():
    return str((get_character_data() or {}).get('name') or '').strip()


def _config_key():
    data = get_character_data() or {}
    server = str(data.get('server') or '').strip()
    name = str(data.get('name') or '').strip()
    return server + '|' + name if server and name else ''


def _base_path():
    return os.path.join(get_config_dir(), pName)


def _scripts_path():
    return os.path.join(_base_path(), 'Scripts')


def _legacy_base_path():
    return os.path.join(get_config_dir(), LEGACY_PLUGIN_NAME)


def _legacy_scripts_path():
    return os.path.join(_legacy_base_path(), 'Scripts')


def _config_path():
    data = get_character_data() or {}
    return os.path.join(
        _base_path(), 'Servers', _safe_name(data.get('server')),
        _safe_name(data.get('name')) + '.json')


def _legacy_config_path():
    data = get_character_data() or {}
    return os.path.join(
        _legacy_base_path(), 'Servers', _safe_name(data.get('server')),
        _safe_name(data.get('name')) + '.json')


def _script_path(file_name):
    current = os.path.join(_scripts_path(), file_name)
    if os.path.isfile(current):
        return current
    return os.path.join(_legacy_scripts_path(), file_name)


def _ensure_folders():
    for folder in (_base_path(), _scripts_path(), os.path.dirname(_config_path())):
        if not os.path.isdir(folder):
            os.makedirs(folder)


def _is_leader_role():
    return QtBind.isChecked(gui, cbxLeader)


def _is_solo_role():
    return QtBind.isChecked(gui, cbxSolo)


def _is_controller_role():
    return _is_leader_role() or _is_solo_role()


def _is_member_role():
    return QtBind.isChecked(gui, cbxMember)


def _leader_name():
    return QtBind.text(gui, tbxLeaderName).strip()


def _member_names():
    if _is_solo_role():
        return []
    names = []
    seen = set()
    own = _own_name().lower()
    leader = _leader_name().lower()
    for item in QtBind.getItems(gui, lstMembers):
        name = str(item or '').strip()
        lowered = name.lower()
        if name and lowered not in seen and lowered not in (own, leader):
            names.append(name)
            seen.add(lowered)
    return names


def _active_member_names():
    return [name for name in _member_names()
            if name.lower() not in entry_blocked_members]


def _selected_script():
    value = QtBind.text(gui, cmbScript).strip()
    return '' if value.startswith('--') else value


def _selected_inside_script():
    value = QtBind.text(gui, cmbInsideScript).strip()
    return '' if value.startswith('--') else value


def _selected_return_script():
    value = QtBind.text(gui, cmbReturnScript).strip()
    return '' if value.startswith('--') else value


def _runs_per_cycle():
    try:
        return max(1, min(20, int(QtBind.text(gui, tbxRuns).strip())))
    except Exception:
        return 5


def _timeout_seconds():
    try:
        return max(60, min(1800, int(QtBind.text(gui, tbxTimeout).strip())))
    except Exception:
        return 900


def _stable_seconds():
    try:
        return max(2, min(30, int(QtBind.text(gui, tbxStable).strip())))
    except Exception:
        return 5


def _max_distance():
    try:
        return max(10.0, min(150.0, float(QtBind.text(gui, tbxDistance).strip())))
    except Exception:
        return DEFAULT_GATE_DISTANCE


def _travel_profile():
    return _selected_phbot_profile(cmbTravelProfile)


def _gate_profile():
    return _selected_phbot_profile(cmbGateProfile)


def _after_profile():
    return _selected_phbot_profile(cmbAfterProfile)


def _selected_phbot_profile(widget):
    selected = str(QtBind.text(gui, widget) or '').strip()
    for candidate in profile_candidates:
        if candidate['label'] == selected:
            return candidate['name']
    return None


def _fill_profile_combobox(widget, wanted):
    values = list(profile_candidates)
    if wanted not in [item['name'] for item in values]:
        wanted = None
    values.sort(key=lambda item: (
        0 if item['name'] == wanted else 1,
        item['label'].lower()))
    QtBind.clear(gui, widget)
    for candidate in values:
        QtBind.append(gui, widget, candidate['label'])


def _refresh_profiles(wanted_travel=None, wanted_gate=None, wanted_after=None):
    global profile_candidates
    character = get_character_data() or {}
    server = str(character.get('server') or '').strip()
    name = str(character.get('name') or '').strip()
    root = get_config_dir()
    if not server or not name or not root:
        profile_candidates = [{'name': None, 'label': 'Keep current'}]
        for widget in (cmbTravelProfile, cmbGateProfile, cmbAfterProfile):
            _fill_profile_combobox(widget, None)
        return False

    prefix = '%s_%s' % (server, name)
    found = {'': 'Default'}
    try:
        for file_name in os.listdir(root):
            if file_name == prefix + '.json':
                found[''] = 'Default'
                continue
            marker = prefix + '.'
            if not file_name.startswith(marker) or not file_name.endswith('.json'):
                continue
            profile = file_name[len(marker):-5]
            if profile:
                found[profile] = profile
    except Exception as error:
        log('[%s] phBot profile scan error: %s' % (pName, error))
        return False

    profile_candidates = [{'name': None, 'label': 'Keep current'}]
    profile_candidates.extend(
        {'name': profile, 'label': label}
        for profile, label in sorted(found.items(), key=lambda item: item[1].lower()))
    _fill_profile_combobox(cmbTravelProfile, wanted_travel)
    _fill_profile_combobox(cmbGateProfile, wanted_gate)
    _fill_profile_combobox(cmbAfterProfile, wanted_after)
    return True


def _schedule_mode():
    value = QtBind.text(gui, cmbScheduleMode).strip()
    return value if value in SCHEDULE_MODES else 'Disabled'


def _schedule_time():
    value = QtBind.text(gui, tbxScheduleTime).strip()
    try:
        return datetime.datetime.strptime(value, '%H:%M').time()
    except Exception:
        return None


def _schedule_date():
    value = QtBind.text(gui, tbxScheduleDate).strip()
    try:
        return datetime.datetime.strptime(value, '%Y-%m-%d').date()
    except Exception:
        return None


def _schedule_tolerance():
    try:
        return max(0, min(60, int(QtBind.text(gui, tbxTolerance).strip())))
    except Exception:
        return 2


def _selected_days():
    return [key for key, widget in zip(DAY_KEYS, schedule_day_widgets)
            if QtBind.isChecked(gui, widget)]


def _hwt_difficulty():
    value = QtBind.text(gui, cmbDifficulty).strip()
    return value if value in HWT_DIFFICULTIES else 'Beginner'


def _teleport_language():
    value = QtBind.text(gui, cmbTeleportLanguage).strip()
    return value if value in TELEPORT_LANGUAGES else 'Auto'


def _resolved_teleport_language():
    configured = _teleport_language()
    if configured != 'Auto':
        return configured
    for npc in (get_npcs() or {}).values():
        name = str(npc.get('name') or '').lower()
        if 'krallar vadisi' in name:
            return 'Turkish'
        if 'kings valley' in name:
            return 'English'
    return 'English'


def _entry_command(difficulty):
    language = _resolved_teleport_language()
    english = {
        'Beginner': 'teleport,Kings Valley,Pharaoh tomb (beginner)',
        'Intermediate': 'teleport,Kings Valley,Pharaoh tomb (intermediate)',
        'Advanced': 'teleport,Kings Valley,Pharaoh tomb (advance)'
    }
    turkish = {
        'Beginner': "teleport,Krallar Vadisi,Pharaoh'nun mezarı (düşük)",
        'Intermediate': "teleport,Krallar Vadisi,Pharaoh'nun mezarı (orta)"
    }
    if language == 'Turkish' and difficulty == 'Advanced':
        return '', language, 'Turkish Advanced teleport text is not configured'
    command = (turkish if language == 'Turkish' else english).get(difficulty, '')
    if not command:
        return '', language, 'No teleport command for %s/%s' % (language, difficulty)
    return command, language, ''


def _exit_command(difficulty):
    language = active_teleport_language or _resolved_teleport_language()
    english = {
        'Beginner': 'teleport,Pharaoh tomb (beginner),Kings Valley',
        'Intermediate': 'teleport,Pharaoh tomb (intermediate),Kings Valley',
        'Advanced': 'teleport,Pharaoh tomb (advance),Kings Valley'
    }
    turkish = {
        'Beginner': "teleport,Pharaoh'nun mezarı (düşük),Krallar Vadisi",
        'Intermediate': "teleport,Pharaoh'nun mezarı (orta),Krallar Vadisi"
    }
    if language == 'Turkish' and difficulty == 'Advanced':
        return '', language, 'Turkish Advanced exit text is not configured'
    command = (turkish if language == 'Turkish' else english).get(difficulty, '')
    return (command, language, '') if command else (
        '', language, 'No exit command for %s/%s' % (language, difficulty))


def _start_entry_teleport(difficulty, target_state):
    global active_teleport_language
    command, language, error = _entry_command(difficulty)
    if error:
        _fail(error)
        return False
    active_teleport_language = language
    stop_bot()
    stop_script()
    result = start_script(command + '\n')
    if result is False:
        _fail('phBot could not start the HWT teleport command')
        return False
    _set_status(target_state, 'Entering HWT %s (%s)' % (difficulty, language),
                COLOR_WARNING)
    _debug('Entry teleport started: difficulty=%s language=%s command=%s' %
           (difficulty, language, command))
    return True


def _confirm_member_inside(position):
    global last_inside_send_at
    stop_script()
    inside_ready_members.add(_own_name().lower())
    _send_private(active_leader, 'INSIDE_READY', _own_name())
    last_inside_send_at = time.time()
    _set_status(STATE_WAITING_INSIDE,
                'Inside region %s; waiting for party' % inside_region,
                COLOR_SUCCESS)
    _debug('Member entry confirmed: position=%s npcs=%s' %
           (position, get_npcs()))


def _party_type():
    try:
        value = get_party_type() or {}
        return int(value.get('type', -1))
    except Exception:
        return -1


def _debug(message):
    if DEBUG_ENABLED:
        log('[%s][DEBUG] %s' % (pName, message))


def _party_debug_snapshot():
    party = get_party() or {}
    rows = []
    leader = ''
    for party_id, member in sorted(party.items(), key=lambda item: str(item[0])):
        name = str(member.get('name') or '?')
        if bool(member.get('leader')):
            leader = name
        rows.append('%s{id=%s,leader=%s,uid=%s,r=%s,x=%.1f,y=%.1f}' % (
            name, party_id, bool(member.get('leader')),
            member.get('player_id', 0), member.get('region', 0),
            float(member.get('x', 0.0)), float(member.get('y', 0.0))))
    return 'type=%s leader=%s members=[%s]' % (
        _party_type(), leader or '-', '; '.join(rows))


def _distance(x1, y1, x2, y2):
    return ((float(x2) - float(x1)) ** 2 +
            (float(y2) - float(y1)) ** 2) ** 0.5


def _gate_evidence():
    position = get_position() or {}
    try:
        if int(position.get('region', 0)) != GATE_REGION:
            return False, 'Region %s; waiting for gate region %s' % (
                position.get('region', '?'), GATE_REGION)
        nearest = None
        for npc in (get_npcs() or {}).values():
            servername = str(npc.get('servername') or '')
            model = int(npc.get('model', 0) or 0)
            if servername != GATE_SERVERNAME and model != GATE_MODEL:
                continue
            if int(npc.get('region', GATE_REGION)) != GATE_REGION:
                continue
            distance = _distance(position['x'], position['y'], npc['x'], npc['y'])
            if nearest is None or distance < nearest:
                nearest = distance
        if nearest is None:
            return False, 'Gate NPC not visible'
        if nearest > _max_distance():
            return False, 'Gate NPC is %.1f units away' % nearest
        return True, 'Gate confirmed (NPC %.1f units)' % nearest
    except Exception as error:
        return False, 'Gate validation error: %s' % error


def _set_status(new_state, detail, color):
    global state
    state = new_state
    QtBind.setText(
        gui, lblStatus,
        fixed_width_text(
            '<font color="{0}"><b>{1}</b></font><br>'
            '<font color="{2}">{3}</font>'.format(
                color, new_state, COLOR_TEXT, detail),
            285))
    log('[%s] %s - %s' % (pName, new_state, detail))
    _update_live()


def _update_live():
    party = get_party() or {}
    party_names = set()
    for member in party.values():
        name = str(member.get('name') or '').strip().lower()
        if name:
            party_names.add(name)
    own = _own_name().lower()
    expected = set(expected_members)
    expected.add(own) if own else None
    ready_total = len(gate_ready_members)
    inside_total = len(inside_ready_members)
    expected_total = len(expected)
    party_total = len(party_names.intersection(expected))
    QtBind.setText(
        gui, lblReady,
        fixed_width_text(
            '<font color="{0}"><b>Gate:</b> {1}/{2} · <b>Inside:</b> {3}/{2}</font>'.format(
                COLOR_TEXT, ready_total, expected_total, inside_total), 285))
    QtBind.setText(
        gui, lblParty,
        fixed_width_text(
            '<font color="{0}"><b>Party:</b> {1}/{2} · <b>Run:</b> {3}/{4}</font>'.format(
                COLOR_TEXT, party_total, expected_total, completed_runs,
                _runs_per_cycle()), 285))


def _send_private(target, command, argument=''):
    if not active_run_id or not target:
        return False
    message = '%s|%s|%s|%s' % (
        PROTOCOL, PROTOCOL_VERSION, active_run_id, command)
    if argument:
        message += '|' + str(argument)
    result = phBotChat.Private(target, message)
    log('[%s] Private protocol -> %s: %s (result=%s)' %
        (pName, target, command, result))
    return result


def _run_gate_script():
    file_name = _selected_script()
    if not file_name or os.path.basename(file_name) != file_name:
        _fail('Select a valid gate script')
        return False
    path = _script_path(file_name)
    try:
        _debug('Gate script requested: character=%s path=%s region=%s position=%s' % (
            _own_name(), path, (get_position() or {}).get('region'), get_position()))
        with open(path, 'r', encoding='utf-8-sig') as handle:
            script = handle.read()
        if not script.strip():
            _fail('Gate script is empty')
            return False
        if 'FHWTG_GATE_READY' not in script:
            log('[%s] Gate script has no callback; automatic region/NPC detection will be used.' % pName)
        stop_bot()
        stop_script()
        if start_script(script) is False:
            _fail('phBot could not start the gate script')
            return False
        _set_status(STATE_TRAVELING, 'Running city-to-gate script', COLOR_WARNING)
        _debug('Gate script accepted by phBot: %s (%d chars)' % (file_name, len(script)))
        return True
    except Exception as error:
        _fail('Gate script error: %s' % error)
        return False


def _run_inside_script():
    global deadline
    file_name = _selected_inside_script()
    if not file_name or os.path.basename(file_name) != file_name:
        _fail('Select a valid HWT inside script')
        return False
    path = _script_path(file_name)
    try:
        with open(path, 'r', encoding='utf-8-sig') as handle:
            script = handle.read()
        if not script.strip():
            _fail('HWT inside script is empty')
            return False
        stop_bot()
        stop_script()
        if start_script(script) is False:
            _fail('phBot could not start the HWT inside script')
            return False
        deadline = 0.0
        _set_status(STATE_RUNNING_HWT,
                    'Running HWT script: %s' % file_name, COLOR_SUCCESS)
        _debug('HWT inside script accepted: character=%s file=%s chars=%s region=%s' %
               (_own_name(), file_name, len(script),
                (get_position() or {}).get('region')))
        return True
    except Exception as error:
        _fail('HWT inside script error: %s' % error)
        return False


def _run_return_script():
    file_name = _selected_return_script()
    if not file_name or os.path.basename(file_name) != file_name:
        _fail('Select a valid leader return script')
        return False
    try:
        with open(_script_path(file_name), 'r',
                  encoding='utf-8-sig') as handle:
            script = handle.read()
        if not script.strip() or start_script(script) is False:
            _fail('Leader return script could not be started')
            return False
        _set_status(STATE_RETURNING_GATE, 'Leader returning to HWT gate',
                    COLOR_WARNING)
        return True
    except Exception as error:
        _fail('Leader return script error: %s' % error)
        return False


def _begin_finalize():
    global finalize_profile_deadline, finalize_return_started, deadline
    global finalize_town_since
    stop_bot()
    stop_script()
    stop_trace()
    profile = _travel_profile()
    if profile is None:
        _fail('Select a Slot Profile for final completion')
        return False
    if str(get_profile() or '') != profile and set_profile(profile) is False:
        _fail('Could not switch to Slot Profile')
        return False
    finalize_profile_deadline = time.time() + 30.0
    finalize_return_started = False
    finalize_town_since = 0.0
    deadline = time.time() + FINALIZE_TIMEOUT_SECONDS
    _set_status(STATE_FINALIZING, 'Loading Slot Profile', COLOR_WARNING)
    return True


def _finish_early(reason):
    global early_finish_reason, deadline
    if not active_run_id:
        return
    early_finish_reason = reason
    stop_script()
    if _is_member_role():
        _send_private(active_leader, 'ENTRY_BLOCKED', reason)
        deadline = 0.0
        _set_status(STATE_WAITING_EXIT,
                    '%s; waiting outside while party continues' % reason,
                    COLOR_WARNING)
        return

    current_region = int((get_position() or {}).get('region', 0) or 0)
    if _is_leader_role():
        for member in _member_names():
            _send_private(member, 'ENTRY_ABORT', reason)
    if current_region > 0 and current_region != GATE_REGION:
        dungeon_ready_members.add(_own_name().lower())
        deadline = time.time() + EXIT_TIMEOUT_SECONDS
        _set_status(STATE_WAITING_DUNGEON,
                    '%s; exiting HWT safely' % reason,
                    COLOR_WARNING)
        return
    if _is_leader_role():
        for member in _member_names():
            _send_private(member, 'FINALIZE_EARLY', reason)
    _begin_finalize()


def _apply_profile(profile_name, target_state, detail):
    global profile_deadline
    if profile_name is None:
        return False
    current = str(get_profile() or '')
    if current == profile_name:
        _debug('Profile already active: %s' % profile_name)
        return False
    stop_bot()
    stop_script()
    if set_profile(profile_name) is False:
        _fail('Could not switch to profile: %s' % profile_name)
        return True
    profile_deadline = time.time() + 30.0
    _set_status(target_state, detail, COLOR_WARNING)
    _debug('Profile switch requested: current=%s target=%s' % (current, profile_name))
    return True


def _start_travel_flow():
    if _apply_profile(_travel_profile(), STATE_TRAVEL_PROFILE,
                      'Switching to slot profile'):
        return
    _run_gate_script()


def _finish_gate_confirmation(detail):
    global deadline, last_ready_send_at, pending_gate_detail
    own = _own_name().lower()
    pending_gate_detail = ''
    deadline = time.time() + _timeout_seconds()
    gate_ready_members.add(own)
    if _is_controller_role():
        _set_status(STATE_WAITING_PARTY,
                    ('%s; preparing solo entry' % detail if _is_solo_role()
                     else '%s; waiting for members and Auto Party' % detail),
                    COLOR_WARNING)
    else:
        _send_private(active_leader, 'GATE_READY', _own_name())
        last_ready_send_at = time.time()
        _set_status(STATE_GATE_READY,
                    '%s; waiting for Auto Party' % detail, COLOR_SUCCESS)


def _apply_after_profile():
    profile = _after_profile()
    if not QtBind.isChecked(gui, cbxApplyAfter) or profile is None:
        return
    try:
        if str(get_profile() or '') != profile:
            stop_bot()
            stop_script()
            result = set_profile(profile)
            _debug('After-completion profile requested: %s result=%s' %
                   (profile, result))
    except Exception as error:
        log('[%s] After-completion profile error: %s' % (pName, error))


def _begin_run(run_id, leader):
    global active_run_id, active_leader, deadline, party_stable_since
    active_run_id = run_id
    active_leader = leader
    deadline = time.time() + _timeout_seconds()
    party_stable_since = 0.0
    gate_ready_members.clear()
    if _is_controller_role():
        expected_members.clear()
        expected_members.update(name.lower() for name in _member_names())
    else:
        expected_members.clear()
    _start_travel_flow()


def _fail(reason):
    global deadline, party_stable_since
    deadline = 0.0
    party_stable_since = 0.0
    stop_script()
    _set_status(STATE_FAILED, reason, COLOR_ERROR)


def _reset(detail='Ready'):
    global active_run_id, active_leader, deadline, party_stable_since
    global last_ready_send_at, last_validation_detail
    global last_gate_debug, last_party_debug, pending_gate_detail, profile_deadline
    global inside_region, last_inside_send_at, last_enter_send_at, active_difficulty
    global member_entry_command_at, member_entry_command_started
    global active_start_mode
    global trace_start_at
    global completed_runs, leader_outside_ready, finalize_profile_deadline
    global finalize_return_started, finalize_town_since, active_teleport_language
    global early_finish_reason
    stop_script()
    active_run_id = ''
    active_leader = ''
    deadline = 0.0
    party_stable_since = 0.0
    last_ready_send_at = 0.0
    last_validation_detail = ''
    last_gate_debug = ''
    last_party_debug = ''
    pending_gate_detail = ''
    profile_deadline = 0.0
    inside_region = 0
    last_inside_send_at = 0.0
    last_enter_send_at = 0.0
    active_difficulty = ''
    member_entry_command_at = 0.0
    member_entry_command_started = False
    active_start_mode = 'TRAVEL'
    trace_start_at = 0.0
    completed_runs = 0
    leader_outside_ready = False
    finalize_profile_deadline = 0.0
    finalize_return_started = False
    finalize_town_since = 0.0
    active_teleport_language = ''
    early_finish_reason = ''
    pending_prepare[:] = []
    prepare_acks.clear()
    prepare_attempts.clear()
    prepare_next_at.clear()
    expected_members.clear()
    gate_ready_members.clear()
    inside_ready_members.clear()
    dungeon_ready_members.clear()
    outside_ready_members.clear()
    entry_blocked_members.clear()
    _set_status(STATE_IDLE, detail, COLOR_MUTED)


def save_config():
    try:
        if not _config_key():
            _set_status(STATE_FAILED, 'Join the game before saving', COLOR_ERROR)
            return False
        _ensure_folders()
        data = {
            'role': ('solo' if _is_solo_role() else
                     ('leader' if _is_leader_role() else 'member')),
            'leader': _leader_name(),
            'members': _member_names(),
            'script': _selected_script(),
            'inside_script': _selected_inside_script(),
            'return_script': _selected_return_script(),
            'runs_per_cycle': _runs_per_cycle(),
            'start_bot_after_hwt': QtBind.isChecked(gui, cbxStartBotAfter),
            'timeout': _timeout_seconds(),
            'stable_seconds': _stable_seconds(),
            'max_distance': _max_distance(),
            'travel_profile': _travel_profile(),
            'gate_profile': _gate_profile(),
            'after_profile': _after_profile(),
            'profile_selection_v2': True,
            'apply_after': QtBind.isChecked(gui, cbxApplyAfter),
            'hwt_difficulty': _hwt_difficulty(),
            'teleport_language': _teleport_language(),
            'schedule_mode': _schedule_mode(),
            'schedule_time': QtBind.text(gui, tbxScheduleTime).strip(),
            'schedule_date': QtBind.text(gui, tbxScheduleDate).strip(),
            'schedule_days': _selected_days(),
            'schedule_tolerance': _schedule_tolerance(),
            'last_schedule_key': last_schedule_key,
            'armed': QtBind.isChecked(gui, cbxArmed)
        }
        with open(_config_path(), 'w', encoding='utf-8') as handle:
            json.dump(data, handle, indent=4)
        _set_status(STATE_IDLE, 'Settings saved', COLOR_SUCCESS)
        return True
    except Exception as error:
        _set_status(STATE_FAILED, 'Settings could not be saved', COLOR_ERROR)
        log('[%s] Config save error: %s' % (pName, error))
        return False


def load_config():
    global last_config_key, last_schedule_key
    key = _config_key()
    if not key:
        return
    last_config_key = key
    try:
        _ensure_folders()
        config_path = _config_path()
        if not os.path.isfile(config_path) and os.path.isfile(_legacy_config_path()):
            config_path = _legacy_config_path()
            _debug('Loading legacy %s settings for migration' % LEGACY_PLUGIN_NAME)
        if not os.path.isfile(config_path):
            refresh_scripts()
            _refresh_profiles(get_profile(), None, None)
            return
        with open(config_path, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
        role = data.get('role', 'member')
        QtBind.setChecked(gui, cbxLeader, role == 'leader')
        QtBind.setChecked(gui, cbxMember, role == 'member')
        QtBind.setChecked(gui, cbxSolo, role == 'solo')
        QtBind.setChecked(gui, cbxArmed, bool(data.get('armed', True)))
        QtBind.setText(gui, tbxLeaderName, str(data.get('leader') or ''))
        QtBind.setText(gui, tbxTimeout, str(data.get('timeout') or 900))
        QtBind.setText(gui, tbxStable, str(data.get('stable_seconds') or 5))
        QtBind.setText(gui, tbxDistance, str(data.get('max_distance') or 50))
        QtBind.setText(gui, tbxRuns, str(data.get('runs_per_cycle') or 5))
        QtBind.setChecked(gui, cbxStartBotAfter,
                          bool(data.get('start_bot_after_hwt', False)))
        profile_v2 = bool(data.get('profile_selection_v2', False))
        travel_profile = data.get('travel_profile')
        gate_profile = data.get('gate_profile')
        after_profile = data.get('after_profile')
        if not profile_v2:
            travel_profile = travel_profile or None
            gate_profile = gate_profile or None
            after_profile = after_profile or None
        _refresh_profiles(travel_profile, gate_profile, after_profile)
        QtBind.setChecked(gui, cbxApplyAfter, bool(data.get('apply_after', False)))
        QtBind.setText(gui, cmbDifficulty,
                       str(data.get('hwt_difficulty') or 'Beginner'))
        QtBind.setText(gui, cmbTeleportLanguage,
                       str(data.get('teleport_language') or 'Auto'))
        QtBind.setText(gui, cmbScheduleMode, str(data.get('schedule_mode') or 'Disabled'))
        QtBind.setText(gui, tbxScheduleTime, str(data.get('schedule_time') or '05:00'))
        QtBind.setText(gui, tbxScheduleDate, str(data.get('schedule_date') or ''))
        QtBind.setText(gui, tbxTolerance, str(data.get('schedule_tolerance', 2)))
        selected_days = set(data.get('schedule_days') or [])
        for key_name, widget in zip(DAY_KEYS, schedule_day_widgets):
            QtBind.setChecked(gui, widget, key_name in selected_days)
        last_schedule_key = str(data.get('last_schedule_key') or '')
        QtBind.clear(gui, lstMembers)
        for name in data.get('members', []):
            QtBind.append(gui, lstMembers, str(name))
        refresh_scripts(str(data.get('script') or ''),
                        str(data.get('inside_script') or ''),
                        str(data.get('return_script') or ''))
        _set_status(STATE_IDLE, 'Settings loaded', COLOR_MUTED)
    except Exception as error:
        refresh_scripts()
        _refresh_profiles(get_profile(), None, None)
        log('[%s] Config load error: %s' % (pName, error))


def refresh_scripts(preferred=None, preferred_inside=None, preferred_return=None):
    selected = preferred if preferred is not None else _selected_script()
    selected_inside = (preferred_inside if preferred_inside is not None
                       else _selected_inside_script())
    selected_return = (preferred_return if preferred_return is not None
                       else _selected_return_script())
    scripts = []
    try:
        _ensure_folders()
        for scripts_folder in (_scripts_path(), _legacy_scripts_path()):
            if not os.path.isdir(scripts_folder):
                continue
            for file_name in os.listdir(scripts_folder):
                path = os.path.join(scripts_folder, file_name)
                if (os.path.isfile(path) and file_name.lower().endswith('.txt')
                        and file_name not in scripts):
                    scripts.append(file_name)
        scripts.sort(key=lambda value: value.lower())
        QtBind.clear(gui, cmbScript)
        QtBind.append(gui, cmbScript, '-- Select gate script --')
        for file_name in scripts:
            QtBind.append(gui, cmbScript, file_name)
        QtBind.setText(gui, cmbScript,
                       selected if selected in scripts else '-- Select gate script --')
        QtBind.clear(gui, cmbInsideScript)
        QtBind.append(gui, cmbInsideScript, '-- Select HWT inside script --')
        for file_name in scripts:
            QtBind.append(gui, cmbInsideScript, file_name)
        QtBind.setText(
            gui, cmbInsideScript,
            selected_inside if selected_inside in scripts
            else '-- Select HWT inside script --')
        QtBind.clear(gui, cmbReturnScript)
        QtBind.append(gui, cmbReturnScript, '-- Select leader return script --')
        for file_name in scripts:
            QtBind.append(gui, cmbReturnScript, file_name)
        QtBind.setText(gui, cmbReturnScript,
                       selected_return if selected_return in scripts
                       else '-- Select leader return script --')
    except Exception as error:
        log('[%s] Script refresh error: %s' % (pName, error))
    return scripts


def role_leader_changed(checked):
    if checked:
        QtBind.setChecked(gui, cbxMember, False)
        QtBind.setChecked(gui, cbxSolo, False)


def role_member_changed(checked):
    if checked:
        QtBind.setChecked(gui, cbxLeader, False)
        QtBind.setChecked(gui, cbxSolo, False)


def role_solo_changed(checked):
    if checked:
        QtBind.setChecked(gui, cbxLeader, False)
        QtBind.setChecked(gui, cbxMember, False)


def armed_changed(checked):
    # The value is persisted with the Save button. Keeping this callback
    # explicit avoids relying on an undocumented empty QtBind callback.
    pass


def schedule_mode_changed(*args):
    _update_schedule_labels()


def schedule_setting_changed(checked):
    _update_schedule_labels()


def refresh_profiles_clicked():
    travel = _travel_profile()
    gate = _gate_profile()
    after = _after_profile()
    if _refresh_profiles(travel, gate, after):
        _set_status(state, '%d phBot profile(s) found' % (len(profile_candidates) - 1),
                    COLOR_SUCCESS)
    else:
        _set_status(state, 'No phBot profiles found for this character', COLOR_ERROR)


def show_schedule_clicked():
    global schedule_screen
    schedule_screen = True
    for widget, x, y in gate_screen_widgets:
        QtBind.move(gui, widget, OFFSCREEN_X, y)
    for widget, x, y in schedule_screen_widgets:
        QtBind.move(gui, widget, x, y)
    QtBind.move(gui, btnSchedule, OFFSCREEN_X, 6)
    QtBind.move(gui, btnGateBack, 350, 6)
    _update_schedule_labels()


def show_gate_clicked():
    global schedule_screen
    schedule_screen = False
    for widget, x, y in schedule_screen_widgets:
        QtBind.move(gui, widget, OFFSCREEN_X, y)
    for widget, x, y in gate_screen_widgets:
        QtBind.move(gui, widget, x, y)
    QtBind.move(gui, btnGateBack, OFFSCREEN_X, 6)
    QtBind.move(gui, btnSchedule, 345, 6)


def add_member_clicked():
    name = QtBind.text(gui, tbxMemberName).strip()
    existing = set(item.lower() for item in QtBind.getItems(gui, lstMembers))
    if name and name.lower() not in existing:
        QtBind.append(gui, lstMembers, name)
        QtBind.setText(gui, tbxMemberName, '')


def remove_member_clicked():
    selected = QtBind.text(gui, lstMembers).strip()
    if selected:
        QtBind.remove(gui, lstMembers, selected)


def _active_profile_path():
    character = get_character_data() or {}
    server = str(character.get('server') or '').strip()
    name = str(character.get('name') or '').strip()
    if not server or not name:
        return ''
    profile = str(get_profile() or '').strip()
    file_name = '%s_%s.%s.json' % (server, name, profile) if profile else '%s_%s.json' % (server, name)
    return os.path.join(get_config_dir(), file_name)


def import_party_clicked():
    if not _is_leader_role():
        _set_status(STATE_FAILED, 'Auto Party import is available on the leader', COLOR_ERROR)
        return
    path = _active_profile_path()
    try:
        if not path or not os.path.isfile(path):
            raise IOError('Active phBot profile JSON was not found')
        with open(path, 'r', encoding='utf-8-sig') as handle:
            data = json.load(handle)
        party_data = data.get('Party') or {}
        imported = []
        seen = set()
        own = _own_name().lower()
        for value in (party_data.get('InviteList') or [])[:7]:
            name = str(value or '').strip()
            if name.endswith('$'):
                name = name[:-1]
            lowered = name.lower()
            if name and lowered != own and lowered not in seen:
                imported.append(name)
                seen.add(lowered)
        if not imported:
            raise ValueError('The active profile has no Auto Party invite list')
        QtBind.clear(gui, lstMembers)
        for name in imported:
            QtBind.append(gui, lstMembers, name)
        _debug('Auto Party import path=%s invite_type=%s members=%s' % (
            path, party_data.get('PartyInviteType', 'unknown'), ','.join(imported)))
        _set_status(STATE_IDLE, 'Imported %d Auto Party member(s)' % len(imported), COLOR_SUCCESS)
    except Exception as error:
        _set_status(STATE_FAILED, 'Auto Party import failed', COLOR_ERROR)
        log('[%s] Auto Party import error: %s' % (pName, error))


def refresh_clicked():
    scripts = refresh_scripts()
    _set_status(STATE_IDLE, '%d gate script(s) found' % len(scripts), COLOR_MUTED)


def save_clicked():
    save_config()


def _start_run(start_mode):
    global active_run_id, active_leader, deadline, party_stable_since
    global last_validation_detail, last_gate_debug, last_party_debug
    global pending_gate_detail, profile_deadline
    global inside_region, last_inside_send_at, last_enter_send_at, active_difficulty
    global member_entry_command_at, member_entry_command_started
    global active_start_mode
    global trace_start_at
    global completed_runs, leader_outside_ready, finalize_profile_deadline
    global finalize_return_started, finalize_town_since, active_teleport_language
    global early_finish_reason
    if not _is_controller_role():
        _set_status(STATE_FAILED, 'Only Party Leader or Solo can start', COLOR_ERROR)
        return
    own = _own_name()
    leader = own if _is_solo_role() else _leader_name()
    members = [] if _is_solo_role() else _member_names()
    if not own or (not _is_solo_role() and own.lower() != leader.lower()):
        _set_status(STATE_FAILED, 'Leader name must match this character', COLOR_ERROR)
        return
    if not _is_solo_role() and not members:
        _set_status(STATE_FAILED, 'Add at least one party member', COLOR_ERROR)
        return
    if not _selected_inside_script():
        _set_status(STATE_FAILED, 'Select an HWT inside script', COLOR_ERROR)
        return
    if _travel_profile() is None:
        _set_status(STATE_FAILED, 'Select a Slot Profile', COLOR_ERROR)
        return
    if _runs_per_cycle() > 1 and not _selected_return_script():
        _set_status(STATE_FAILED, 'Select a leader return script', COLOR_ERROR)
        return
    if state not in (STATE_IDLE, STATE_COMPLETE, STATE_FAILED):
        _set_status(state, 'A gate run is already active', COLOR_WARNING)
        return
    if not save_config():
        return
    gate_detail = ''
    if start_mode == 'GATE':
        gate_confirmed, gate_detail = _gate_evidence()
        if not gate_confirmed:
            _set_status(STATE_FAILED,
                        'Start From Gate rejected: %s' % gate_detail,
                        COLOR_ERROR)
            return
    active_run_id = '%s-%d' % (own.lower(), int(time.time()))
    active_leader = own
    party_stable_since = 0.0
    last_validation_detail = ''
    last_gate_debug = ''
    last_party_debug = ''
    pending_gate_detail = ''
    profile_deadline = 0.0
    inside_region = 0
    last_inside_send_at = 0.0
    last_enter_send_at = 0.0
    active_difficulty = ''
    member_entry_command_at = 0.0
    member_entry_command_started = False
    active_start_mode = start_mode
    trace_start_at = 0.0
    completed_runs = 0
    leader_outside_ready = False
    finalize_profile_deadline = 0.0
    finalize_return_started = False
    finalize_town_since = 0.0
    active_teleport_language = ''
    early_finish_reason = ''
    expected_members.clear()
    expected_members.update(name.lower() for name in members)
    pending_prepare[:] = list(members)
    prepare_acks.clear()
    prepare_attempts.clear()
    prepare_next_at.clear()
    for member in members:
        prepare_attempts[member.lower()] = 0
        prepare_next_at[member.lower()] = time.time()
    deadline = time.time() + _timeout_seconds()
    gate_ready_members.clear()
    inside_ready_members.clear()
    dungeon_ready_members.clear()
    outside_ready_members.clear()
    entry_blocked_members.clear()
    _debug('Run started: id=%s mode=%s leader=%s members=%s script=%s timeout=%s stable=%s distance=%s' % (
        active_run_id, active_start_mode, active_leader, ','.join(members), _selected_script(),
        _timeout_seconds(), _stable_seconds(), _max_distance()))
    if active_start_mode == 'GATE':
        _confirm_gate(gate_detail)
    else:
        _start_travel_flow()


def start_clicked():
    _start_run('TRAVEL')


def start_from_gate_clicked():
    _start_run('GATE')


def stop_clicked():
    if active_run_id and _is_leader_role():
        for member in _member_names():
            _send_private(member, 'ABORT')
    _reset('Stopped manually')


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        _set_status(state, 'Opening Discord invite...', COLOR_SUCCESS)
    except Exception as error:
        _set_status(state, 'Could not open Discord invite', COLOR_ERROR)
        log('[%s] Discord link error: %s' % (pName, error))


# Add this command as the final line of every city-to-gate walk script.
def FHWTG_GATE_READY(args):
    global deadline, last_ready_send_at
    if not active_run_id or state not in (STATE_TRAVELING, STATE_GATE_READY,
                                          STATE_WAITING_PARTY):
        return 0
    confirmed, detail = _gate_evidence()
    if not confirmed:
        _set_status(STATE_TRAVELING, 'Script ended; %s' % detail, COLOR_WARNING)
        return 1000
    _confirm_gate(detail)
    return 0


def FHWTG_DUNGEON_COMPLETE(args):
    global deadline, last_inside_send_at
    if not active_run_id or state not in (STATE_RUNNING_HWT,
                                          STATE_SCRIPT_FINISHED):
        return 0
    if not _is_controller_role():
        log('[%s] Dungeon completion callback ignored on a party member' % pName)
        return 0
    stop_script()
    dungeon_ready_members.add(_own_name().lower())
    deadline = time.time() + EXIT_TIMEOUT_SECONDS
    _set_status(STATE_WAITING_DUNGEON,
                'Leader route finished; preparing exit', COLOR_WARNING)
    return 0


def _confirm_gate(detail):
    global pending_gate_detail
    own = _own_name().lower()
    if own in gate_ready_members:
        return
    stop_script()
    _debug('Gate confirmation accepted: character=%s detail=%s position=%s npcs=%s' % (
        _own_name(), detail, get_position(), get_npcs()))
    pending_gate_detail = detail
    if _apply_profile(_gate_profile(), STATE_GATE_PROFILE,
                      'Switching to HWT profile'):
        return
    _finish_gate_confirmation(detail)


def handle_chat(t, player, msg):
    global active_run_id, active_leader, deadline, last_ready_send_at
    global inside_region, last_inside_send_at, active_difficulty
    global member_entry_command_at, member_entry_command_started
    global active_start_mode
    global completed_runs
    global early_finish_reason
    if t != CHAT_PRIVATE or not player or not msg or not msg.startswith(PROTOCOL + '|'):
        return False
    parts = msg.split('|', 4)
    if len(parts) < 4 or parts[1] != PROTOCOL_VERSION:
        return True
    run_id = parts[2]
    command = parts[3].upper()
    argument = parts[4] if len(parts) > 4 else ''
    _debug('Protocol received: sender=%s run=%s command=%s argument=%s state=%s' % (
        player, run_id, command, argument or '-', state))
    configured_leader = _leader_name()

    if command == 'PREPARE':
        if (not QtBind.isChecked(gui, cbxArmed) or _is_controller_role() or
                not configured_leader or player.lower() != configured_leader.lower()):
            return True
        if active_run_id == run_id and active_leader.lower() == player.lower():
            _send_private(active_leader, 'PREPARE_ACK', _own_name())
            return True
        if state not in (STATE_IDLE, STATE_COMPLETE, STATE_FAILED):
            return True
        requested_mode = argument.upper() if argument else 'TRAVEL'
        if requested_mode not in ('TRAVEL', 'GATE'):
            _fail('Unsupported start mode: %s' % requested_mode)
            return True
        if _travel_profile() is None:
            _set_status(STATE_FAILED, 'Select a Slot Profile', COLOR_ERROR)
            return True
        active_run_id = run_id
        active_leader = player
        active_start_mode = requested_mode
        deadline = time.time() + _timeout_seconds()
        gate_ready_members.clear()
        inside_ready_members.clear()
        inside_region = 0
        last_inside_send_at = 0.0
        member_entry_command_at = 0.0
        member_entry_command_started = False
        _send_private(active_leader, 'PREPARE_ACK', _own_name())
        if active_start_mode == 'GATE':
            gate_confirmed, gate_detail = _gate_evidence()
            if not gate_confirmed:
                _fail('Start From Gate rejected: %s' % gate_detail)
                return True
            _confirm_gate(gate_detail)
        else:
            _start_travel_flow()
        return True

    if not active_run_id or run_id != active_run_id:
        return True
    if command == 'GATE_READY' and _is_leader_role():
        sender = player.lower()
        if sender in expected_members:
            gate_ready_members.add(sender)
            _update_live()
    elif command == 'PREPARE_ACK' and _is_leader_role():
        if player.lower() in expected_members:
            prepare_acks.add(player.lower())
        log('[%s] Prepare acknowledged by %s' % (pName, player))
    elif command == 'ENTER' and player.lower() == active_leader.lower():
        if _is_leader_role():
            return True
        try:
            difficulty, region_text = argument.split(';', 1)
            expected_region = int(region_text)
        except Exception:
            _fail('Invalid ENTER protocol data')
            return True
        if difficulty not in HWT_DIFFICULTIES or expected_region <= 0:
            _fail('Unsupported ENTER protocol data')
            return True
        if state == STATE_WAITING_INSIDE and inside_region == expected_region:
            _send_private(active_leader, 'INSIDE_READY', _own_name())
            last_inside_send_at = time.time()
            return True
        if state == STATE_MEMBER_ENTERING and inside_region == expected_region:
            return True
        inside_region = expected_region
        active_difficulty = difficulty
        deadline = time.time() + ENTRY_TIMEOUT_SECONDS
        position = get_position() or {}
        current_region = int(position.get('region', 0) or 0)
        if current_region == inside_region:
            _confirm_member_inside(position)
            return True
        member_entry_command_at = time.time() + FCONTROL_ENTRY_GRACE_SECONDS
        member_entry_command_started = False
        _set_status(STATE_MEMBER_ENTERING,
                    'Waiting 8 sec for FControl entry', COLOR_WARNING)
        _debug('FControl entry grace started: current_region=%s target_region=%s' %
               (current_region, inside_region))
    elif command == 'INSIDE_READY' and _is_leader_role():
        sender = player.lower()
        if sender in expected_members:
            inside_ready_members.add(sender)
            _update_live()
    elif command == 'TRACE_PREPARE' and player.lower() == active_leader.lower():
        deadline = 0.0
        _set_status(STATE_WAITING_DUNGEON,
                    'Following leader inside HWT', COLOR_SUCCESS)
    elif command == 'EXIT_MEMBERS' and player.lower() == active_leader.lower():
        deadline = time.time() + EXIT_TIMEOUT_SECONDS
        _set_status(STATE_WAITING_EXIT,
                    'Waiting to leave party and return outside', COLOR_WARNING)
    elif command == 'OUTSIDE_READY' and _is_leader_role():
        if player.lower() in expected_members:
            outside_ready_members.add(player.lower())
    elif command == 'NEXT_RUN' and player.lower() == active_leader.lower():
        try:
            completed_runs = int(argument)
        except Exception:
            pass
        gate_ready_members.clear()
        inside_ready_members.clear()
        dungeon_ready_members.clear()
        confirmed, detail = _gate_evidence()
        if not confirmed:
            _fail('Next run gate check failed: %s' % detail)
        else:
            _confirm_gate(detail)
    elif command == 'FINALIZE' and player.lower() == active_leader.lower():
        try:
            completed_runs = int(argument)
        except Exception:
            pass
        _begin_finalize()
    elif command == 'ENTRY_BLOCKED' and _is_leader_role():
        entry_blocked_members.add(player.lower())
        early_finish_reason = argument or 'HWT entry could not be confirmed'
        deadline = time.time() + ENTRY_TIMEOUT_SECONDS
        _set_status(STATE_WAITING_INSIDE,
                    '%s; continuing with entered members' % early_finish_reason,
                    COLOR_WARNING)
        _debug('Entry-blocked member excluded from current run: %s' % player)
    elif command == 'ENTRY_ABORT' and player.lower() == active_leader.lower():
        early_finish_reason = argument or 'HWT entry stopped by leader'
        deadline = time.time() + EXIT_TIMEOUT_SECONDS
        _set_status(STATE_WAITING_EXIT,
                    '%s; waiting to return outside' % early_finish_reason,
                    COLOR_WARNING)
    elif command == 'FINALIZE_EARLY' and player.lower() == active_leader.lower():
        early_finish_reason = argument or 'HWT entry stopped'
        _begin_finalize()
    elif command == 'ABORT' and player.lower() == active_leader.lower():
        _reset('Leader aborted the gate run')
    return True


def handle_joymax(opcode, data):
    if (opcode == 0xB05A and len(data) >= 3 and
            data[0] == 0x02 and data[1] == 0x27 and data[2] == 0x1C and
            state in (STATE_LEADER_ENTERING, STATE_MEMBER_ENTERING,
                      STATE_WAITING_INSIDE)):
        _debug('HWT entry-limit response captured: 0xB05A %s' %
               ' '.join('%02X' % value for value in data))
        _finish_early('HWT entry limit reached')
    return True


def _party_validation():
    own = _own_name().lower()
    required = set(expected_members)
    required.add(own)
    party = get_party() or {}
    actual = set()
    leaders = []
    by_name = {}
    for member in party.values():
        name = str(member.get('name') or '').strip().lower()
        if name:
            actual.add(name)
            by_name[name] = member
            if bool(member.get('leader')):
                leaders.append(name)
    if actual != required:
        missing = sorted(required - actual)
        extra = sorted(actual - required)
        return False, 'Roster mismatch · missing=%s extra=%s' % (
            ','.join(missing) or '-', ','.join(extra) or '-')
    if len(leaders) != 1 or leaders[0] != active_leader.lower():
        return False, 'Wrong party leader: %s' % (leaders[0] if leaders else 'unknown')
    leader = by_name.get(active_leader.lower())
    if not leader:
        return False, 'Configured leader is missing'
    if int(leader.get('region', 0)) != GATE_REGION:
        return False, 'Leader is outside the HWT gate region'
    for name in sorted(required):
        member = by_name[name]
        if int(member.get('region', 0)) != GATE_REGION:
            return False, '%s is in region %s' % (member.get('name'), member.get('region'))
        if int(member.get('player_id', 0) or 0) <= 0:
            return False, '%s is not visible near the leader' % member.get('name')
        distance = _distance(leader['x'], leader['y'], member['x'], member['y'])
        if distance > _max_distance():
            return False, '%s is %.1f units from leader' % (member.get('name'), distance)
    return True, 'Leader, roster, region, visibility and distance verified'


def _inside_party_validation(expected_region):
    required = set(expected_members) - set(entry_blocked_members)
    required.add(_own_name().lower())
    allowed = required | set(entry_blocked_members)
    party = get_party() or {}
    actual = set()
    leaders = []
    by_name = {}
    for member in party.values():
        name = str(member.get('name') or '').strip().lower()
        if not name:
            continue
        actual.add(name)
        by_name[name] = member
        if bool(member.get('leader')):
            leaders.append(name)
    if not required.issubset(actual) or not actual.issubset(allowed):
        return False, 'Inside roster mismatch'
    if len(leaders) != 1 or leaders[0] != active_leader.lower():
        return False, 'Wrong party leader inside HWT'
    for name in sorted(required):
        member = by_name[name]
        if int(member.get('region', 0) or 0) != expected_region:
            return False, '%s is not in inside region %s' % (
                member.get('name'), expected_region)
        if int(member.get('player_id', 0) or 0) <= 0:
            return False, '%s is not visible inside HWT' % member.get('name')
    return True, 'Inside roster, leader, region and visibility verified'


def _schedule_due(now):
    mode = _schedule_mode()
    target_time = _schedule_time()
    if mode == 'Disabled' or target_time is None:
        return False, ''
    if mode == 'Selected days' and DAY_KEYS[now.weekday()] not in _selected_days():
        return False, ''
    if mode == 'One time':
        target_date = _schedule_date()
        if target_date is None or now.date() != target_date:
            return False, ''
    scheduled = datetime.datetime.combine(now.date(), target_time)
    delta_seconds = (now - scheduled).total_seconds()
    tolerance_seconds = _schedule_tolerance() * 60
    if delta_seconds < 0 or delta_seconds > tolerance_seconds:
        return False, ''
    key = '%s|%s|%s' % (mode, now.date().isoformat(), target_time.strftime('%H:%M'))
    return key != last_schedule_key, key


def _next_schedule_text(now=None):
    now = now or datetime.datetime.now()
    mode = _schedule_mode()
    target_time = _schedule_time()
    if mode == 'Disabled':
        return 'Disabled'
    if target_time is None:
        return 'Invalid time'
    if mode == 'One time':
        target_date = _schedule_date()
        return ('Invalid date' if target_date is None else
                '%s %s' % (target_date.isoformat(), target_time.strftime('%H:%M')))
    for offset in range(0, 8):
        date_value = now.date() + datetime.timedelta(days=offset)
        candidate = datetime.datetime.combine(date_value, target_time)
        if candidate <= now:
            continue
        if mode == 'Selected days' and DAY_KEYS[candidate.weekday()] not in _selected_days():
            continue
        return candidate.strftime('%Y-%m-%d %H:%M')
    return 'No selected day'


def _update_schedule_labels():
    QtBind.setText(
        gui, lblNextRun,
        fixed_width_text('<font color="%s"><b>Next:</b> %s</font>' %
                         (COLOR_TEXT, _next_schedule_text()), 288))
    QtBind.setText(
        gui, lblLastRun,
        fixed_width_text('<font color="%s"><b>Last key:</b> %s</font>' %
                         (COLOR_MUTED, last_schedule_key or '-'), 288))


def event_loop():
    global deadline, party_stable_since, last_ready_send_at
    global last_config_key, last_validation_detail
    global last_gate_debug, last_party_debug, profile_deadline
    global last_schedule_key, schedule_next_check_at
    global inside_region, last_inside_send_at, last_enter_send_at, active_difficulty
    global member_entry_command_at, member_entry_command_started
    global trace_start_at
    global completed_runs, leader_outside_ready
    global finalize_profile_deadline, finalize_return_started, finalize_town_since
    global early_finish_reason
    now = time.time()

    key = _config_key()
    if key and key != last_config_key and state == STATE_IDLE:
        load_config()

    if now >= schedule_next_check_at:
        schedule_next_check_at = now + 1.0
        _update_schedule_labels()
        if (_is_controller_role() and QtBind.isChecked(gui, cbxArmed) and
                state in (STATE_IDLE, STATE_COMPLETE, STATE_FAILED)):
            due, schedule_key = _schedule_due(datetime.datetime.now())
            if due:
                last_schedule_key = schedule_key
                _debug('Scheduled run triggered: %s' % schedule_key)
                save_config()
                start_clicked()

    if state == STATE_TRAVEL_PROFILE:
        if str(get_profile() or '') == _travel_profile():
            profile_deadline = 0.0
            _debug('Slot profile confirmed: %s' % _travel_profile())
            _run_gate_script()
        elif profile_deadline and now >= profile_deadline:
            profile_deadline = 0.0
            _fail('Slot profile switch timed out: %s' % _travel_profile())

    if state == STATE_GATE_PROFILE:
        if str(get_profile() or '') == _gate_profile():
            profile_deadline = 0.0
            _debug('HWT profile confirmed: %s' % _gate_profile())
            _finish_gate_confirmation(pending_gate_detail or 'Gate confirmed')
        elif profile_deadline and now >= profile_deadline:
            profile_deadline = 0.0
            _fail('HWT profile switch timed out: %s' % _gate_profile())

    if _is_leader_role() and active_run_id:
        for target in list(pending_prepare):
            lowered = target.lower()
            if lowered in prepare_acks:
                pending_prepare.remove(target)
                continue
            attempts = prepare_attempts.get(lowered, 0)
            if attempts >= PREPARE_MAX_ATTEMPTS:
                continue
            if now >= prepare_next_at.get(lowered, 0.0):
                _send_private(target, 'PREPARE', active_start_mode)
                prepare_attempts[lowered] = attempts + 1
                prepare_next_at[lowered] = now + PREPARE_RETRY_SECONDS
                break

    if active_run_id and state == STATE_TRAVELING:
        confirmed, detail = _gate_evidence()
        gate_debug = '%s|%s' % (confirmed, detail)
        if gate_debug != last_gate_debug:
            last_gate_debug = gate_debug
            _debug('Gate probe changed: %s position=%s' % (gate_debug, get_position()))
        if confirmed:
            _confirm_gate(detail)

    if (_is_member_role() and active_run_id and
            state == STATE_GATE_READY and now - last_ready_send_at >= 5.0):
        _send_private(active_leader, 'GATE_READY', _own_name())
        last_ready_send_at = now

    if (_is_controller_role() and active_run_id and
            state == STATE_WAITING_PARTY):
        party_debug = _party_debug_snapshot()
        if party_debug != last_party_debug:
            last_party_debug = party_debug
            _debug('Party snapshot changed: %s' % party_debug)
        own = _own_name().lower()
        all_ready = expected_members.issubset(gate_ready_members) and own in gate_ready_members
        party_valid, validation_detail = ((True, 'Solo gate verified')
                                           if _is_solo_role()
                                           else _party_validation())
        if all_ready and party_valid:
            if not party_stable_since:
                party_stable_since = now
                _set_status(STATE_WAITING_PARTY,
                            'Party verified; checking %d sec stability' % _stable_seconds(),
                            COLOR_WARNING)
            elif now - party_stable_since >= _stable_seconds():
                party_stable_since = 0.0
                inside_ready_members.clear()
                inside_region = 0
                active_difficulty = _hwt_difficulty()
                deadline = now + ENTRY_TIMEOUT_SECONDS
                _debug('Gate assembly complete; leader entry starting: difficulty=%s' %
                       active_difficulty)
                _start_entry_teleport(active_difficulty, STATE_LEADER_ENTERING)
        else:
            party_stable_since = 0.0
            detail = ('Waiting for gate confirmations' if not all_ready
                      else validation_detail)
            if detail != last_validation_detail:
                last_validation_detail = detail
                log('[%s] Assembly check: %s' % (pName, detail))

    if (_is_controller_role() and active_run_id and
            state == STATE_LEADER_ENTERING):
        position = get_position() or {}
        current_region = int(position.get('region', 0) or 0)
        if current_region > 0 and current_region != GATE_REGION:
            stop_script()
            inside_region = current_region
            inside_ready_members.add(_own_name().lower())
            deadline = now + ENTRY_TIMEOUT_SECONDS
            argument = '%s;%s' % (active_difficulty, inside_region)
            for member in _member_names():
                _send_private(member, 'ENTER', argument)
            last_enter_send_at = now
            _set_status(STATE_WAITING_INSIDE,
                        'Leader inside region %s; waiting for members' % inside_region,
                        COLOR_WARNING)
            _debug('Leader entry confirmed: position=%s npcs=%s' %
                   (position, get_npcs()))

    if (_is_member_role() and active_run_id and
            state == STATE_MEMBER_ENTERING):
        position = get_position() or {}
        current_region = int(position.get('region', 0) or 0)
        if inside_region > 0 and current_region == inside_region:
            _confirm_member_inside(position)
        elif (not member_entry_command_started and member_entry_command_at and
              now >= member_entry_command_at):
            if current_region == GATE_REGION:
                gate_confirmed, gate_detail = _gate_evidence()
                if gate_confirmed:
                    member_entry_command_started = True
                    _debug('FControl grace expired at stable gate; starting FAutoHWT fallback entry')
                    _start_entry_teleport(active_difficulty, STATE_MEMBER_ENTERING)
                else:
                    _debug('Fallback entry deferred; gate scene is not stable: %s' %
                           gate_detail)
                    member_entry_command_at = now + 1.0
            elif current_region <= 0:
                # A zero/unknown region commonly means the teleport scene is loading.
                # Never issue a second teleport until a stable region is available.
                pass

    if (_is_member_role() and active_run_id and
            state == STATE_WAITING_INSIDE and
            now - last_inside_send_at >= 5.0):
        _send_private(active_leader, 'INSIDE_READY', _own_name())
        last_inside_send_at = now

    if (_is_controller_role() and active_run_id and
            state == STATE_WAITING_INSIDE):
        required = set(expected_members) - set(entry_blocked_members)
        required.add(_own_name().lower())
        if now - last_enter_send_at >= 5.0:
            argument = '%s;%s' % (active_difficulty, inside_region)
            for member in _active_member_names():
                if member.lower() not in inside_ready_members:
                    _send_private(member, 'ENTER', argument)
            last_enter_send_at = now
        all_inside_ready = required.issubset(inside_ready_members)
        party_valid, validation_detail = ((True, 'Solo inside region verified')
                                           if _is_solo_role()
                                           else _inside_party_validation(inside_region))
        if all_inside_ready and party_valid:
            if not party_stable_since:
                party_stable_since = now
                _set_status(STATE_WAITING_INSIDE,
                            'Inside party verified; checking %d sec stability' %
                            _stable_seconds(), COLOR_WARNING)
            elif now - party_stable_since >= _stable_seconds():
                party_stable_since = 0.0
                if _is_solo_role():
                    _debug('Solo inside verification complete; starting HWT script')
                    _run_inside_script()
                else:
                    for member in _active_member_names():
                        _send_private(member, 'TRACE_PREPARE')
                    trace_result = phBotChat.Party('T')
                    if trace_result is False:
                        for member in _member_names():
                            _send_private(member, 'ABORT')
                        _fail('FControl trace command could not be sent')
                        return
                    trace_start_at = now + TRACE_WAIT_SECONDS
                    deadline = trace_start_at + 30.0
                    _set_status(STATE_TRACE_WAIT,
                                'Trace sent; starting HWT scripts in 10 sec',
                                COLOR_WARNING)
                    _debug('FControl trace command sent: channel=Party result=%s region=%s' %
                           (trace_result, inside_region))
        else:
            party_stable_since = 0.0
            detail = ('Waiting for inside confirmations' if not all_inside_ready
                      else validation_detail)
            if detail != last_validation_detail:
                last_validation_detail = detail
                log('[%s] Inside check: %s' % (pName, detail))

    if (_is_leader_role() and active_run_id and state == STATE_TRACE_WAIT and
            trace_start_at and now >= trace_start_at):
        trace_start_at = 0.0
        _run_inside_script()

    if (_is_controller_role() and active_run_id and
            state == STATE_WAITING_DUNGEON):
        if _own_name().lower() in dungeon_ready_members:
            command, language, error = _exit_command(active_difficulty)
            if error:
                _fail(error)
            else:
                stop_script()
                if start_script(command + '\n') is False:
                    _fail('Leader exit teleport could not be started')
                else:
                    deadline = now + EXIT_TIMEOUT_SECONDS
                    _set_status(STATE_LEADER_EXITING,
                                'Leader exiting HWT (%s)' % language,
                                COLOR_WARNING)
                    _debug('Leader exit command started: %s' % command)

    if (_is_controller_role() and active_run_id and state == STATE_LEADER_EXITING):
        current_region = int((get_position() or {}).get('region', 0) or 0)
        if current_region == GATE_REGION:
            stop_script()
            leader_outside_ready = True
            outside_ready_members.clear()
            for member in _member_names():
                _send_private(member, 'EXIT_MEMBERS')
            lp_result = True if _is_solo_role() else phBotChat.Party('LP')
            deadline = now + EXIT_TIMEOUT_SECONDS
            _debug('Member leave-party command sent: result=%s' % lp_result)
            if early_finish_reason or completed_runs + 1 >= _runs_per_cycle():
                _set_status(STATE_WAITING_EXIT,
                            ('%s; waiting for members outside' % early_finish_reason
                             if early_finish_reason else
                             'Final run; waiting for members outside'),
                            COLOR_WARNING)
            else:
                _run_return_script()

    if (_is_member_role() and active_run_id and
            state == STATE_WAITING_EXIT):
        current_region = int((get_position() or {}).get('region', 0) or 0)
        if current_region == GATE_REGION and now - last_inside_send_at >= 5.0:
            _send_private(active_leader, 'OUTSIDE_READY', _own_name())
            last_inside_send_at = now

    if (_is_controller_role() and active_run_id and state == STATE_RETURNING_GATE):
        confirmed, detail = _gate_evidence()
        if confirmed:
            stop_script()
            leader_outside_ready = True
            _set_status(STATE_WAITING_EXIT,
                        'Leader at gate; waiting for members outside',
                        COLOR_WARNING)

    if (_is_controller_role() and active_run_id and state == STATE_WAITING_EXIT):
        if (leader_outside_ready and
                expected_members.issubset(outside_ready_members)):
            if not early_finish_reason:
                completed_runs += 1
            _debug('HWT run completed: %s/%s' %
                   (completed_runs, _runs_per_cycle()))
            if early_finish_reason or completed_runs >= _runs_per_cycle():
                for member in _member_names():
                    if early_finish_reason:
                        _send_private(member, 'FINALIZE_EARLY', early_finish_reason)
                    else:
                        _send_private(member, 'FINALIZE', str(completed_runs))
                _begin_finalize()
            else:
                gate_ready_members.clear()
                inside_ready_members.clear()
                dungeon_ready_members.clear()
                outside_ready_members.clear()
                leader_outside_ready = False
                for member in _member_names():
                    _send_private(member, 'NEXT_RUN', str(completed_runs))
                confirmed, detail = _gate_evidence()
                if confirmed:
                    _finish_gate_confirmation(detail)
                else:
                    _fail('Leader next-run gate check failed: %s' % detail)

    if state == STATE_FINALIZING:
        slot_profile = _travel_profile()
        if str(get_profile() or '') == slot_profile:
            finalize_profile_deadline = 0.0
            if not finalize_return_started:
                result = use_return_scroll()
                if result is False:
                    _fail('Return Scroll could not be used')
                else:
                    finalize_return_started = True
                    _set_status(STATE_FINALIZING,
                                'Return Scroll used; waiting for town',
                                COLOR_WARNING)
            else:
                current_region = int((get_position() or {}).get('region', 0) or 0)
                if current_region > 0 and current_region != GATE_REGION:
                    if not finalize_town_since:
                        finalize_town_since = now
                    elif now - finalize_town_since >= 5.0:
                        deadline = 0.0
                        if QtBind.isChecked(gui, cbxStartBotAfter):
                            start_bot()
                        completion_detail = (early_finish_reason or
                                             'HWT cycle complete: %s/%s' %
                                             (completed_runs, _runs_per_cycle()))
                        _set_status(STATE_COMPLETE, completion_detail,
                                    COLOR_SUCCESS)
                else:
                    finalize_town_since = 0.0
        elif finalize_profile_deadline and now >= finalize_profile_deadline:
            _fail('Slot Profile switch timed out after HWT')

    if deadline and now >= deadline and state not in (STATE_IDLE, STATE_COMPLETE, STATE_FAILED):
        if state in (STATE_LEADER_ENTERING, STATE_MEMBER_ENTERING):
            _finish_early('HWT entry timed out after 120 sec')
        elif state == STATE_WAITING_INSIDE and _is_controller_role():
            missing_members = (set(expected_members) -
                               set(inside_ready_members))
            if missing_members:
                entry_blocked_members.update(missing_members)
                early_finish_reason = 'HWT entry timed out after 120 sec'
                deadline = 0.0
                party_stable_since = 0.0
                _set_status(STATE_WAITING_INSIDE,
                            'Entry timeout; continuing with entered members',
                            COLOR_WARNING)
                _debug('Timed-out members excluded from current run: %s' %
                       ','.join(sorted(missing_members)))
            else:
                _finish_early('HWT entry timed out after 120 sec')
        elif state in (STATE_LEADER_EXITING,
                     STATE_WAITING_EXIT, STATE_RETURNING_GATE):
            _fail('HWT entry timed out')
        elif state == STATE_TRACE_WAIT:
            _fail('HWT trace/script start timed out')
        elif state == STATE_WAITING_DUNGEON:
            _fail('Dungeon completion synchronization timed out')
        elif state == STATE_FINALIZING:
            _fail('Final Slot Profile/Return Scroll timed out')
        else:
            _fail('Gate assembly timed out')
    _update_live()


def joined_game():
    load_config()


def disconnected():
    if state not in (STATE_IDLE, STATE_COMPLETE):
        _fail('Disconnected')


def finished():
    if state == STATE_TRAVELING:
        stop_script()
    elif state == STATE_RUNNING_HWT:
        _fail('HWT script ended without FHWTG_DUNGEON_COMPLETE')


gui = QtBind.init(__name__, pName)
gate_screen_widgets = []
schedule_screen_widgets = []
schedule_day_widgets = []

QtBind.createLabel(
    gui, '<font color="%s" size="4"><b>🏺 %s</b></font>' % (COLOR_PRIMARY, pName),
    12, 6)
QtBind.createLabel(
    gui, '<font color="%s">v%s · HWT flow</font>' % (COLOR_MUTED, pVersion),
    145, 12)
btnSchedule = QtBind.createButton(gui, 'show_schedule_clicked', 'Schedule & Profiles', 345, 6)
btnGateBack = QtBind.createButton(gui, 'show_gate_clicked', '← Gate Setup', OFFSCREEN_X, 6)
QtBind.createButton(gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(
    gui, u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' % COLOR_PRIMARY,
    565, 11)
QtBind.createLineEdit(gui, '', 12, 30, 696, 1)

lblRoleHeader = QtBind.createLabel(gui, '<font color="%s"><b>RUN MODE & LEADER</b></font>' % COLOR_PRIMARY, 12, 42)
cbxArmed = QtBind.createCheckBox(gui, 'armed_changed', 'Armed (accept leader start)', 12, 62)
cbxLeader = QtBind.createCheckBox(gui, 'role_leader_changed', 'Party Leader', 12, 84)
cbxMember = QtBind.createCheckBox(gui, 'role_member_changed', 'Party Member', 120, 84)
cbxSolo = QtBind.createCheckBox(gui, 'role_solo_changed', 'Solo', 235, 84)
QtBind.setChecked(gui, cbxMember, True)
QtBind.setChecked(gui, cbxArmed, True)
lblLeaderName = QtBind.createLabel(gui, '<font color="%s">Leader name</font>' % COLOR_MUTED, 12, 108)
tbxLeaderName = QtBind.createLineEdit(gui, '', 95, 104, 190, 20)

lblScriptHeader = QtBind.createLabel(gui, '<font color="%s"><b>GATE SCRIPT</b></font>' % COLOR_PRIMARY, 12, 140)
cmbScript = QtBind.createCombobox(gui, 12, 160, 220, 20)
btnRefresh = QtBind.createButton(gui, 'refresh_clicked', '↻ Refresh', 238, 158)
lblTimeout = QtBind.createLabel(gui, '<font color="%s">Timeout</font>' % COLOR_MUTED, 12, 190)
tbxTimeout = QtBind.createLineEdit(gui, '900', 72, 186, 55, 20)
lblSeconds = QtBind.createLabel(gui, '<font color="%s">sec</font>' % COLOR_MUTED, 132, 190)
lblStable = QtBind.createLabel(gui, '<font color="%s">Party stable</font>' % COLOR_MUTED, 172, 190)
tbxStable = QtBind.createLineEdit(gui, '5', 254, 186, 35, 20)

lblMembersHeader = QtBind.createLabel(gui, '<font color="%s"><b>EXPECTED MEMBERS</b></font>' % COLOR_PRIMARY, 312, 42)
tbxMemberName = QtBind.createLineEdit(gui, '', 312, 62, 165, 20)
btnAddMember = QtBind.createButton(gui, 'add_member_clicked', '+ Add', 482, 60)
btnRemoveMember = QtBind.createButton(gui, 'remove_member_clicked', '− Remove', 545, 60)
lstMembers = QtBind.createList(gui, 312, 88, 300, 91)
btnImportParty = QtBind.createButton(gui, 'import_party_clicked', 'Import Auto Party', 312, 184)
lblDistance = QtBind.createLabel(gui, '<font color="%s">Max distance</font>' % COLOR_MUTED, 442, 190)
tbxDistance = QtBind.createLineEdit(gui, '50', 525, 186, 35, 20)
lblTypeInfo = QtBind.createLabel(gui, '<font color="%s">Type: info only</font>' % COLOR_MUTED, 570, 190)

lineVertical = QtBind.createLineEdit(gui, '', 300, 42, 1, 174)
lineControls = QtBind.createLineEdit(gui, '', 12, 218, 696, 1)
btnSave = QtBind.createButton(gui, 'save_clicked', '💾 Save', 12, 232)
btnStart = QtBind.createButton(gui, 'start_clicked', '▶ Leader Start', 90, 232)
btnStartFromGate = QtBind.createButton(
    gui, 'start_from_gate_clicked', '▶ Start From Gate', 195, 232)
btnStop = QtBind.createButton(gui, 'stop_clicked', '■ Stop', 320, 232)

lblStatus = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s"><b>IDLE</b></font><br>'
                          '<font color="%s">Ready</font>' % (COLOR_MUTED, COLOR_TEXT), 285),
    405, 226)
lblReady = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s"><b>Gate ready:</b> 0/0</font>' % COLOR_TEXT, 285),
    405, 266)
lblParty = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s"><b>Expected party:</b> 0/0</font>' % COLOR_TEXT, 285),
    405, 284)

gate_screen_widgets.extend([
    (lblRoleHeader, 12, 42), (cbxArmed, 12, 62), (cbxLeader, 12, 84),
    (cbxMember, 120, 84), (cbxSolo, 235, 84),
    (lblLeaderName, 12, 108), (tbxLeaderName, 95, 104),
    (lblScriptHeader, 12, 140), (cmbScript, 12, 160), (btnRefresh, 238, 158),
    (lblTimeout, 12, 190), (tbxTimeout, 72, 186), (lblSeconds, 132, 190),
    (lblStable, 172, 190), (tbxStable, 254, 186), (lblMembersHeader, 312, 42),
    (tbxMemberName, 312, 62), (btnAddMember, 482, 60), (btnRemoveMember, 545, 60),
    (lstMembers, 312, 88), (btnImportParty, 312, 184), (lblDistance, 442, 190),
    (tbxDistance, 525, 186), (lblTypeInfo, 570, 190), (lineVertical, 300, 42),
    (lineControls, 12, 218), (btnSave, 12, 232), (btnStart, 90, 232),
    (btnStartFromGate, 195, 232), (btnStop, 320, 232),
    (lblStatus, 405, 226), (lblReady, 405, 266),
    (lblParty, 405, 284)
])

# Schedule & Profiles screen (created offscreen, shown with QtBind.move).
lblProfilesHeader = QtBind.createLabel(gui, '<font color="%s"><b>PROFILES</b></font>' % COLOR_PRIMARY, OFFSCREEN_X, 42)
btnRefreshProfiles = QtBind.createButton(gui, 'refresh_profiles_clicked', '↻ Profiles', OFFSCREEN_X, 38)
lblTravelProfile = QtBind.createLabel(gui, '<font color="%s">Slot profile</font>' % COLOR_MUTED, OFFSCREEN_X, 70)
cmbTravelProfile = QtBind.createCombobox(gui, OFFSCREEN_X, 66, 180, 20)
lblGateProfile = QtBind.createLabel(gui, '<font color="%s">HWT profile</font>' % COLOR_MUTED, OFFSCREEN_X, 104)
cmbGateProfile = QtBind.createCombobox(gui, OFFSCREEN_X, 100, 180, 20)
lblAfterProfile = QtBind.createLabel(gui, '<font color="%s">After HWT</font>' % COLOR_MUTED, OFFSCREEN_X, 138)
cmbAfterProfile = QtBind.createCombobox(gui, OFFSCREEN_X, 134, 180, 20)
cbxApplyAfter = QtBind.createCheckBox(gui, 'schedule_setting_changed', 'Apply after dungeon (future)', OFFSCREEN_X, 166)
lblInsideScript = QtBind.createLabel(gui, '<font color="%s">Leader HWT</font>' % COLOR_MUTED, OFFSCREEN_X, 170)
cmbInsideScript = QtBind.createCombobox(gui, OFFSCREEN_X, 164, 180, 20)
lblReturnScript = QtBind.createLabel(gui, '<font color="%s">Leader return</font>' % COLOR_MUTED, OFFSCREEN_X, 170)
cmbReturnScript = QtBind.createCombobox(gui, OFFSCREEN_X, 164, 180, 20)
lblEntryHeader = QtBind.createLabel(gui, '<font color="%s"><b>HWT ENTRY</b></font>' % COLOR_PRIMARY, OFFSCREEN_X, 194)
lblRuns = QtBind.createLabel(gui, '<font color="%s">Runs</font>' % COLOR_MUTED, OFFSCREEN_X, 198)
tbxRuns = QtBind.createLineEdit(gui, '5', OFFSCREEN_X, 194, 35, 20)
lblDifficulty = QtBind.createLabel(gui, '<font color="%s">Difficulty</font>' % COLOR_MUTED, OFFSCREEN_X, 220)
cmbDifficulty = QtBind.createCombobox(gui, OFFSCREEN_X, 216, 100, 20)
for difficulty in HWT_DIFFICULTIES:
    QtBind.append(gui, cmbDifficulty, difficulty)
QtBind.setText(gui, cmbDifficulty, 'Beginner')
lblTeleportLanguage = QtBind.createLabel(gui, '<font color="%s">Language</font>' % COLOR_MUTED, OFFSCREEN_X, 220)
cmbTeleportLanguage = QtBind.createCombobox(gui, OFFSCREEN_X, 216, 85, 20)
for teleport_language in TELEPORT_LANGUAGES:
    QtBind.append(gui, cmbTeleportLanguage, teleport_language)
QtBind.setText(gui, cmbTeleportLanguage, 'Auto')
cbxStartBotAfter = QtBind.createCheckBox(
    gui, 'schedule_setting_changed', 'Start bot after HWT completion',
    OFFSCREEN_X, 246)

lblScheduleHeader = QtBind.createLabel(gui, '<font color="%s"><b>SCHEDULE</b></font>' % COLOR_PRIMARY, OFFSCREEN_X, 42)
lblScheduleMode = QtBind.createLabel(gui, '<font color="%s">Mode</font>' % COLOR_MUTED, OFFSCREEN_X, 70)
cmbScheduleMode = QtBind.createCombobox(gui, OFFSCREEN_X, 66, 150, 20)
for schedule_mode in SCHEDULE_MODES:
    QtBind.append(gui, cmbScheduleMode, schedule_mode)
QtBind.setText(gui, cmbScheduleMode, 'Disabled')
lblScheduleTime = QtBind.createLabel(gui, '<font color="%s">Time</font>' % COLOR_MUTED, OFFSCREEN_X, 104)
tbxScheduleTime = QtBind.createLineEdit(gui, '05:00', OFFSCREEN_X, 100, 65, 20)
lblTolerance = QtBind.createLabel(gui, '<font color="%s">Tolerance</font>' % COLOR_MUTED, OFFSCREEN_X, 104)
tbxTolerance = QtBind.createLineEdit(gui, '2', OFFSCREEN_X, 100, 35, 20)
lblToleranceMin = QtBind.createLabel(gui, '<font color="%s">min</font>' % COLOR_MUTED, OFFSCREEN_X, 104)
lblScheduleDate = QtBind.createLabel(gui, '<font color="%s">One-time date</font>' % COLOR_MUTED, OFFSCREEN_X, 138)
tbxScheduleDate = QtBind.createLineEdit(gui, '', OFFSCREEN_X, 134, 105, 20)
lblDays = QtBind.createLabel(gui, '<font color="%s">Selected days</font>' % COLOR_MUTED, OFFSCREEN_X, 170)
for day_key in DAY_KEYS:
    schedule_day_widgets.append(QtBind.createCheckBox(
        gui, 'schedule_setting_changed', day_key, OFFSCREEN_X, 190))
lblNextRun = QtBind.createLabel(gui, fixed_width_text('<font color="%s"><b>Next:</b> Disabled</font>' % COLOR_TEXT, 288), OFFSCREEN_X, 222)
lblLastRun = QtBind.createLabel(gui, fixed_width_text('<font color="%s"><b>Last key:</b> -</font>' % COLOR_MUTED, 288), OFFSCREEN_X, 244)
btnScheduleSave = QtBind.createButton(gui, 'save_clicked', '💾 Save Schedule & Profiles', OFFSCREEN_X, 272)

schedule_screen_widgets.extend([
    (lblProfilesHeader, 12, 42), (btnRefreshProfiles, 205, 38),
    (lblTravelProfile, 12, 70), (cmbTravelProfile, 112, 66),
    (lblGateProfile, 12, 104), (cmbGateProfile, 112, 100),
    (lblInsideScript, 12, 138), (cmbInsideScript, 112, 134),
    (lblReturnScript, 12, 170), (cmbReturnScript, 112, 164),
    (lblEntryHeader, 12, 194), (lblRuns, 205, 198), (tbxRuns, 250, 194),
    (lblDifficulty, 12, 220),
    (cmbDifficulty, 75, 216), (lblTeleportLanguage, 175, 220),
    (cmbTeleportLanguage, 237, 216), (cbxStartBotAfter, 12, 246),
    (lblScheduleHeader, 342, 42),
    (lblScheduleMode, 342, 70), (cmbScheduleMode, 397, 66),
    (lblScheduleTime, 342, 104), (tbxScheduleTime, 397, 100),
    (lblTolerance, 482, 104), (tbxTolerance, 547, 100),
    (lblToleranceMin, 586, 104), (lblScheduleDate, 342, 138),
    (tbxScheduleDate, 442, 134), (lblDays, 342, 170),
    (lblNextRun, 342, 222), (lblLastRun, 342, 244),
    (btnScheduleSave, 342, 272)
])
for index, widget in enumerate(schedule_day_widgets):
    schedule_screen_widgets.append((widget, 342 + index * 50, 188))

refresh_scripts()
_refresh_profiles(get_profile(), None, None)
log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
