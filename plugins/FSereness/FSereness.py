from phBot import *
import QtBind
import json
import math
import os
import random
import struct
import time
import webbrowser


pName = 'FSereness'
pVersion = '2.6.2'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'
ACTION_PREFIX = b'\x01\x00\x30'
PETRIFY_BAD_EFFECT = 1 << 12
VERIFIED_PETRIFY_EFFECT_IDS = {91781}
# Known ATTACK03 IDs observed in standard vSRO-derived media sets. These are
# used only when get_skill() cannot resolve an identity; a resolved non-
# ATTACK03 identity is never accepted merely because its numeric ID is known.
KNOWN_PETRIFY_SKILL_IDS = set(range(32843, 32856))

COLOR_PRIMARY = '#5b57e0'
COLOR_TEXT = '#2b3038'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#d93a4d'

STATE_IDLE = 'IDLE'
STATE_EVADING = 'EVADING'
STATE_WAITING = 'WAITING'

POLL_SECONDS = 0.20
MOVE_RETRY_SECONDS = 0.40
MOVE_TIMEOUT_SECONDS = 3.50
NO_PROGRESS_SECONDS = 1.50
ARRIVAL_DISTANCE = 2.5
CAST_CONFIRM_WINDOW = 3.0
CAST_COOLDOWN_SECONDS = 6.0
LEARN_CONFIRMATIONS = 2
MAX_RECENT_CASTS = 12

gui = QtBind.init(__name__, pName)


def fixed_width_text(content, width):
    return (
        '<table width="{0}" cellspacing="0" cellpadding="0">'
        '<tr><td>{1}</td></tr></table>'
    ).format(width, content)


# Header
QtBind.createLabel(
    gui, '<font color="{0}" size="4"><b>FSereness</b></font>'.format(
        COLOR_PRIMARY), 12, 6)
QtBind.createLabel(
    gui, '<font color="{0}">v{1}</font>'.format(COLOR_MUTED, pVersion), 150, 12)
QtBind.createButton(gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(
    gui, u'<font color="{0}"><b>⚜ Made By FascinaTe</b></font>'.format(
        COLOR_PRIMARY), 565, 11)
QtBind.createLineEdit(gui, '', 12, 30, 716, 1)

# Detection panel
QtBind.createLabel(
    gui, '<font color="{0}"><b>DETECTION</b></font>'.format(COLOR_PRIMARY), 12, 42)
cbxActive = QtBind.createCheckBox(gui, 'active_changed', 'Enable plugin', 12, 62)
cbxAutoLearn = QtBind.createCheckBox(
    gui, 'option_changed', 'Fallback learn after 2 petrifies', 130, 62)
cbxDebug = QtBind.createCheckBox(gui, 'option_changed', 'Debug log', 350, 62)

QtBind.createLabel(gui, 'Boss name', 12, 91)
tbxTargetMob = QtBind.createLineEdit(gui, 'Ghost Sereness', 105, 88, 160, 20)
QtBind.createLabel(gui, 'Manual Skill ID', 285, 91)
tbxManualSkillID = QtBind.createLineEdit(gui, '', 395, 88, 80, 20)
QtBind.createLabel(
    gui, '<font color="{0}">Empty = automatic game-data detection</font>'.format(
        COLOR_MUTED),
    485, 91)

QtBind.createLabel(
    gui, '<font color="{0}">Verified packet prefix: 01 00 30 | Skill: uint16 LE @ offset 3 | Caster UID @ offset 7</font>'.format(
        COLOR_MUTED), 12, 120)

QtBind.createLineEdit(gui, '', 12, 148, 716, 1)

# Evasion panel
QtBind.createLabel(
    gui, '<font color="{0}"><b>EVASION</b></font>'.format(COLOR_PRIMARY), 12, 160)
QtBind.createLabel(gui, 'Move distance', 12, 185)
tbxRadius = QtBind.createLineEdit(gui, '12', 105, 182, 55, 20)
QtBind.createLabel(gui, 'units', 165, 185)
QtBind.createLabel(gui, 'Resume delay', 220, 185)
tbxDelay = QtBind.createLineEdit(gui, '5.0', 310, 182, 55, 20)
QtBind.createLabel(gui, 'sec', 370, 185)
QtBind.createLabel(gui, 'Petrify wait', 420, 185)
tbxStoneDelay = QtBind.createLineEdit(gui, '5.0', 505, 182, 55, 20)
QtBind.createLabel(gui, 'sec', 565, 185)

btnSave = QtBind.createButton(gui, 'save_config', 'Save Settings', 12, 216)
btnReset = QtBind.createButton(gui, 'reset_learning', 'Reset Learned ID', 125, 216)
cbxTempTraining = QtBind.createCheckBox(
    gui, 'option_changed', 'Temporary training center', 285, 216)
QtBind.createLabel(gui, 'Trace target', 480, 220)
tbxTraceTarget = QtBind.createLineEdit(gui, '', 555, 216, 145, 20)

QtBind.createLineEdit(gui, '', 12, 250, 716, 1)

# Live status panel
QtBind.createLabel(
    gui, '<font color="{0}"><b>LIVE STATUS</b></font>'.format(COLOR_PRIMARY), 12, 262)
QtBind.createLabel(gui, 'State', 12, 287)
lblState = QtBind.createLabel(
    gui, fixed_width_text('<font color="{0}"><b>DISABLED</b></font>'.format(
        COLOR_MUTED), 190), 105, 287)
QtBind.createLabel(gui, 'Effective Skill', 315, 287)
lblSkill = QtBind.createLabel(
    gui, fixed_width_text('<font color="{0}">Not configured</font>'.format(
        COLOR_MUTED), 270), 420, 287)

QtBind.createLabel(gui, 'Learning', 12, 314)
lblLearning = QtBind.createLabel(
    gui, fixed_width_text('<font color="{0}">Waiting for petrify 0/2</font>'.format(
        COLOR_MUTED), 190), 105, 314)
QtBind.createLabel(gui, 'Last event', 315, 314)
lblEvent = QtBind.createLabel(
    gui, fixed_width_text('<font color="{0}">Ready</font>'.format(COLOR_MUTED), 270),
    420, 314)


# Runtime state
state = STATE_IDLE
state_since = 0.0
last_poll = 0.0
last_move = 0.0
move_target = None
resume_deadline = 0.0
resume_mode = ''
loaded_profile = ''
training_backup = None

learned_skill_id = 0
learning_counts = {}
recent_boss_casts = []
last_confirmation_time = 0.0
active_skill_snapshot = set()
previous_bad_effects = 0
last_cast_trigger_time = 0.0
evasion_targets = []
evasion_target_index = 0
best_target_distance = None
last_progress_time = 0.0
skill_identity_cache = {}


def plugin_log(message):
    log('[%s] %s' % (pName, message))


def debug_log(message):
    if QtBind.isChecked(gui, cbxDebug):
        plugin_log('DEBUG: %s' % message)


def set_state_label(text, color):
    QtBind.setText(
        gui, lblState,
        fixed_width_text('<font color="{0}"><b>{1}</b></font>'.format(
            color, text), 190))


def set_event(message, color=COLOR_MUTED):
    QtBind.setText(
        gui, lblEvent,
        fixed_width_text('<font color="{0}">{1}</font>'.format(
            color, str(message)), 270))


def set_learning(message, color=COLOR_MUTED):
    QtBind.setText(
        gui, lblLearning,
        fixed_width_text('<font color="{0}">{1}</font>'.format(
            color, str(message)), 190))


def update_skill_label():
    manual = read_optional_int(tbxManualSkillID)
    if manual:
        text = 'Manual: %d (0x%04X)' % (manual, manual)
        color = COLOR_SUCCESS
    elif learned_skill_id:
        text = 'Learned: %d (0x%04X)' % (learned_skill_id, learned_skill_id)
        color = COLOR_SUCCESS
    else:
        text = 'Automatic game-data detection'
        color = COLOR_SUCCESS
    QtBind.setText(
        gui, lblSkill,
        fixed_width_text('<font color="{0}">{1}</font>'.format(color, text), 270))


def notify(message, color=COLOR_MUTED):
    plugin_log(message)
    set_event(message, color)


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        set_event('Opening Discord invite...', COLOR_SUCCESS)
    except Exception as error:
        plugin_log('Discord link error: %s' % error)
        set_event('Could not open Discord invite', COLOR_ERROR)


def read_float(widget, default, minimum, maximum):
    try:
        value = float(QtBind.text(gui, widget).strip())
        if not math.isfinite(value):
            raise ValueError('not finite')
        return max(minimum, min(maximum, value))
    except Exception:
        return default


def read_optional_int(widget):
    raw = QtBind.text(gui, widget).strip()
    if not raw:
        return 0
    try:
        value = int(raw, 0)
        if 1 <= value <= 0xFFFF:
            return value
    except Exception:
        pass
    return 0


def get_effective_skill_id(boss=None):
    manual = read_optional_int(tbxManualSkillID)
    if manual:
        return manual
    if learned_skill_id:
        return learned_skill_id
    return 0


def skill_identity(skill_id):
    if skill_id in skill_identity_cache:
        return skill_identity_cache[skill_id]
    try:
        info = get_skill(skill_id) or {}
    except Exception as error:
        debug_log('get_skill(%d) failed: %s' % (skill_id, error))
        info = {}
    identity = str(info.get('servername', '') or '').strip().upper()
    skill_identity_cache[skill_id] = identity
    return identity


def is_game_data_petrify_skill(skill_id):
    identity = skill_identity(skill_id)
    return (identity.startswith('MSKILL_GOD_GHOST_UNDINE_') and
            identity.endswith('_ATTACK03'))


def accept_petrify_skill(skill_id, boss):
    global learned_skill_id
    manual = read_optional_int(tbxManualSkillID)
    if manual:
        return skill_id == manual

    if is_game_data_petrify_skill(skill_id):
        if learned_skill_id != skill_id:
            learned_skill_id = skill_id
            update_skill_label()
            save_config(True)
            plugin_log(
                'Petrify recognized from game data: %d (%s)' % (
                    skill_id, skill_identity(skill_id)))
        return True

    if learned_skill_id:
        return skill_id == learned_skill_id
    identity = skill_identity(skill_id)
    if not identity and skill_id in KNOWN_PETRIFY_SKILL_IDS:
        plugin_log('Known petrify ID fallback used: %d' % skill_id)
        return True
    return False


def character_profile():
    try:
        character = get_character_data()
    except Exception:
        character = None
    if character and character.get('server') and character.get('name'):
        return '%s_%s' % (character['server'], character['name'])
    return ''


def config_path(profile=None):
    if profile is None:
        profile = character_profile()
    if not profile:
        return None
    folder = os.path.join(get_config_dir(), pName)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    return os.path.join(folder, '%s.json' % profile)


def validate_settings(show_error=True):
    manual_raw = QtBind.text(gui, tbxManualSkillID).strip()
    if manual_raw and not read_optional_int(tbxManualSkillID):
        if show_error:
            set_event('Skill ID must be 1-65535', COLOR_ERROR)
        return False
    return True


def save_config(silent=False):
    global learned_skill_id
    if not validate_settings(not silent):
        return False
    path = config_path()
    if not path:
        if not silent:
            set_event('Enter the game before saving', COLOR_ERROR)
        return False
    data = {
        'schema_version': 3,
        'active': QtBind.isChecked(gui, cbxActive),
        'auto_learn': QtBind.isChecked(gui, cbxAutoLearn),
        'debug': QtBind.isChecked(gui, cbxDebug),
        'temporary_training': QtBind.isChecked(gui, cbxTempTraining),
        'trace_target': QtBind.text(gui, tbxTraceTarget).strip(),
        'target_mob': QtBind.text(gui, tbxTargetMob).strip(),
        'manual_skill_id': QtBind.text(gui, tbxManualSkillID).strip(),
        'learned_skill_id': learned_skill_id,
        'radius': str(read_float(tbxRadius, 12.0, 3.0, 30.0)),
        'delay': str(read_float(tbxDelay, 5.0, 0.0, 30.0)),
        'stone_delay': str(read_float(tbxStoneDelay, 5.0, 0.0, 30.0))
    }
    try:
        with open(path, 'w', encoding='utf-8') as config_file:
            json.dump(data, config_file, ensure_ascii=False, indent=2)
        if not silent:
            notify('Settings saved', COLOR_SUCCESS)
        update_skill_label()
        return True
    except Exception as error:
        plugin_log('Config save error: %s' % error)
        if not silent:
            set_event('Settings could not be saved', COLOR_ERROR)
        return False


def load_config(profile):
    global learned_skill_id, learning_counts
    path = config_path(profile)
    if not path or not os.path.isfile(path):
        update_skill_label()
        return
    try:
        with open(path, 'r', encoding='utf-8') as config_file:
            data = json.load(config_file)
        QtBind.setChecked(gui, cbxActive, bool(data.get('active', False)))
        QtBind.setChecked(gui, cbxAutoLearn, bool(data.get('auto_learn', True)))
        QtBind.setChecked(gui, cbxDebug, bool(data.get('debug', False)))
        QtBind.setChecked(
            gui, cbxTempTraining, bool(data.get('temporary_training', False)))
        QtBind.setText(gui, tbxTraceTarget, str(data.get('trace_target', '')))
        QtBind.setText(gui, tbxTargetMob, str(data.get('target_mob', 'Ghost Sereness')))
        QtBind.setText(gui, tbxManualSkillID, str(data.get('manual_skill_id', '')))
        QtBind.setText(gui, tbxRadius, str(data.get('radius', '12')))
        QtBind.setText(gui, tbxDelay, str(data.get('delay', '5.0')))
        QtBind.setText(gui, tbxStoneDelay, str(data.get('stone_delay', '5.0')))
        learned_skill_id = int(data.get('learned_skill_id', 0) or 0)
        if not 0 <= learned_skill_id <= 0xFFFF:
            learned_skill_id = 0
        learning_counts = {}
        update_skill_label()
        if QtBind.isChecked(gui, cbxActive):
            set_state_label('MONITORING', COLOR_SUCCESS)
        else:
            set_state_label('DISABLED', COLOR_MUTED)
        if learned_skill_id:
            set_learning('Learned ID ready', COLOR_SUCCESS)
        notify('Settings loaded', COLOR_SUCCESS)
    except Exception as error:
        plugin_log('Config load error: %s' % error)
        set_event('Config invalid; defaults kept', COLOR_ERROR)


def reset_learning():
    global learned_skill_id, learning_counts, recent_boss_casts
    learned_skill_id = 0
    learning_counts = {}
    recent_boss_casts = []
    set_learning('Waiting for petrify 0/2', COLOR_MUTED)
    update_skill_label()
    save_config(True)
    notify('Learned Skill ID reset', COLOR_WARNING)


def option_changed(checked):
    update_skill_label()


def active_changed(checked):
    if not checked:
        cancel_automation('Plugin disabled', False)
        set_state_label('DISABLED', COLOR_MUTED)
    else:
        set_state_label('MONITORING', COLOR_SUCCESS)
        set_event('Monitoring Ghost Sereness', COLOR_SUCCESS)


def find_boss():
    target = QtBind.text(gui, tbxTargetMob).strip().lower()
    if not target:
        return None
    try:
        monsters = get_monsters() or {}
        for uid, monster in monsters.items():
            if str(monster.get('name', '')).strip().lower() == target:
                return int(uid), monster
    except Exception as error:
        debug_log('get_monsters failed: %s' % error)
    return None


def active_skill_ids():
    return set(active_skills().keys())


def active_skills():
    try:
        return dict((int(skill_id), info)
                    for skill_id, info in (get_active_skills() or {}).items())
    except Exception as error:
        debug_log('get_active_skills failed: %s' % error)
        return {}


def remember_boss_cast(skill_id, now):
    global recent_boss_casts
    recent_boss_casts.append({'skill_id': skill_id, 'time': now})
    recent_boss_casts = [
        cast for cast in recent_boss_casts
        if now - cast['time'] <= CAST_CONFIRM_WINDOW
    ][-MAX_RECENT_CASTS:]
    debug_log('Boss cast: skill=%d (0x%04X)' % (skill_id, skill_id))


def latest_unambiguous_cast(now):
    valid = [cast for cast in recent_boss_casts
             if 0 <= now - cast['time'] <= CAST_CONFIRM_WINDOW]
    if not valid:
        return 0
    # A confirmation is accepted only when the latest short window points to one ID.
    ids = set(cast['skill_id'] for cast in valid)
    return valid[-1]['skill_id'] if len(ids) == 1 else 0


def confirm_petrify(now, source):
    global learned_skill_id, last_confirmation_time, learning_counts
    if now - last_confirmation_time < 1.5:
        return
    skill_id = latest_unambiguous_cast(now)
    if not skill_id:
        debug_log('Petrify confirmation ignored: no unambiguous recent boss cast')
        return
    last_confirmation_time = now

    if QtBind.isChecked(gui, cbxAutoLearn) and not read_optional_int(tbxManualSkillID):
        count = min(LEARN_CONFIRMATIONS, learning_counts.get(skill_id, 0) + 1)
        learning_counts[skill_id] = count
        set_learning('Candidate %d: %d/%d' % (
            skill_id, count, LEARN_CONFIRMATIONS), COLOR_WARNING)
        plugin_log('Petrify confirmed by %s: Skill ID %d (%d/%d)' % (
            source, skill_id, count, LEARN_CONFIRMATIONS))
        if count >= LEARN_CONFIRMATIONS:
            learned_skill_id = skill_id
            learning_counts = {}
            update_skill_label()
            set_learning('Skill %d learned' % skill_id, COLOR_SUCCESS)
            save_config(True)
            notify('Petrify Skill ID learned: %d' % skill_id, COLOR_SUCCESS)

    handle_petrified(now)


def current_run_mode():
    try:
        status = str(get_status()).strip().lower()
    except Exception:
        status = ''
    if status in ('botting', 'training'):
        return 'bot'
    if status == 'tracing':
        return 'trace'
    return ''


def calculate_evasion_targets():
    position = get_position()
    if not position:
        return []
    cx, cy, cz = position['x'], position['y'], position['z']
    radius = read_float(tbxRadius, 12.0, 3.0, 30.0)
    boss = find_boss()
    if boss:
        monster = boss[1]
        dx = float(monster['x']) - cx
        dy = float(monster['y']) - cy
        distance = math.hypot(dx, dy)
        if distance > 0.01:
            ux, uy = dx / distance, dy / distance
            sides = [(-uy, ux), (uy, -ux)]
            random.shuffle(sides)
            return [
                (cx + side[0] * radius, cy + side[1] * radius, cz)
                for side in sides
            ]
    angle = random.uniform(0.0, math.pi * 2.0)
    notify('Boss position unavailable; using circular fallback', COLOR_WARNING)
    return [
        (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius, cz),
        (cx - math.cos(angle) * radius, cy - math.sin(angle) * radius, cz)
    ]


def apply_temporary_training(target):
    global training_backup
    training_backup = None
    if not QtBind.isChecked(gui, cbxTempTraining):
        return
    try:
        area = get_training_area()
        if not area:
            return
        training_backup = {
            'region': int(area.get('region', 0) or 0),
            'x': float(area.get('x', 0.0)),
            'y': float(area.get('y', 0.0)),
            'z': float(area.get('z', 0.0))
        }
        set_training_position(0, target[0], target[1], target[2])
        debug_log('Temporary training center applied')
    except Exception as error:
        training_backup = None
        debug_log('Temporary training center failed: %s' % error)


def restore_training():
    global training_backup
    backup = training_backup
    training_backup = None
    if not backup:
        return
    try:
        set_training_position(
            backup['region'], backup['x'], backup['y'], backup['z'])
        debug_log('Training center restored')
    except Exception as error:
        plugin_log('Training center restore error: %s' % error)


def begin_evasion(skill_id, now):
    global state, state_since, move_target, last_move, resume_mode
    global evasion_targets, evasion_target_index, best_target_distance
    global last_progress_time
    if state != STATE_IDLE:
        return False
    mode = current_run_mode()
    if not mode:
        mode = 'stopped'
    if mode == 'trace' and not QtBind.text(gui, tbxTraceTarget).strip():
        set_event('Trace target required for safe restoration', COLOR_ERROR)
        return False
    targets = calculate_evasion_targets()
    if not targets:
        set_event('Position unavailable; evasion cancelled', COLOR_ERROR)
        return False
    resume_mode = mode
    if mode == 'bot':
        stop_bot()
    elif mode == 'trace':
        stop_trace()
    state = STATE_EVADING
    state_since = now
    last_move = 0.0
    last_progress_time = now
    best_target_distance = None
    evasion_targets = targets
    evasion_target_index = 0
    move_target = targets[0]
    if mode == 'bot':
        apply_temporary_training(move_target)
    set_state_label('EVADING', COLOR_WARNING)
    notify('Petrify cast %d detected; moving to X:%d Y:%d' % (
        skill_id, int(move_target[0]), int(move_target[1])), COLOR_WARNING)
    return True


def begin_wait(now, delay, message):
    global state, state_since, resume_deadline, move_target
    state = STATE_WAITING
    state_since = now
    resume_deadline = now + delay
    move_target = None
    restore_training()
    set_state_label('WAITING TO RESUME', COLOR_WARNING)
    notify(message, COLOR_WARNING)


def handle_petrified(now):
    global resume_mode
    if state == STATE_IDLE:
        resume_mode = current_run_mode()
        if resume_mode == 'bot':
            stop_bot()
        elif resume_mode == 'trace':
            if not QtBind.text(gui, tbxTraceTarget).strip():
                resume_mode = ''
            else:
                stop_trace()
    delay = read_float(tbxStoneDelay, 5.0, 0.0, 30.0)
    begin_wait(now, delay, 'Petrified; waiting %.1f sec' % delay)


def cancel_automation(message, log_message=True):
    global state, move_target, resume_deadline, resume_mode
    state = STATE_IDLE
    move_target = None
    resume_deadline = 0.0
    resume_mode = ''
    restore_training()
    if log_message:
        notify(message, COLOR_WARNING)


def poll_evasion(now):
    global last_move, state_since, move_target, evasion_target_index
    global best_target_distance, last_progress_time
    if not move_target:
        begin_wait(now, 0.0, 'Movement target lost')
        return
    position = get_position()
    if position:
        distance = math.hypot(move_target[0] - position['x'],
                              move_target[1] - position['y'])
        if distance <= ARRIVAL_DISTANCE:
            delay = read_float(tbxDelay, 5.0, 0.0, 30.0)
            begin_wait(now, delay, 'Safe position reached; resume in %.1f sec' % delay)
            return
        if best_target_distance is None or distance < best_target_distance - 0.5:
            best_target_distance = distance
            last_progress_time = now
    phase_failed = (now - state_since >= MOVE_TIMEOUT_SECONDS or
                    now - last_progress_time >= NO_PROGRESS_SECONDS)
    if phase_failed and evasion_target_index + 1 < len(evasion_targets):
        evasion_target_index += 1
        move_target = evasion_targets[evasion_target_index]
        state_since = now
        last_progress_time = now
        best_target_distance = None
        last_move = 0.0
        if resume_mode == 'bot' and QtBind.isChecked(gui, cbxTempTraining):
            try:
                set_training_position(0, move_target[0], move_target[1], move_target[2])
            except Exception as error:
                debug_log('Alternate training center failed: %s' % error)
        notify('Primary path blocked; trying opposite side', COLOR_WARNING)
        return
    if phase_failed:
        delay = read_float(tbxDelay, 5.0, 0.0, 30.0)
        begin_wait(now, delay, 'Both paths timed out; resume in %.1f sec' % delay)
        return
    if now - last_move >= MOVE_RETRY_SECONDS:
        last_move = now
        move_to(move_target[0], move_target[1], move_target[2])


def poll_resume(now):
    global state, resume_mode
    if now < resume_deadline:
        return
    mode = resume_mode if QtBind.isChecked(gui, cbxActive) else ''
    resume_mode = ''
    state = STATE_IDLE
    if mode == 'stopped':
        notify('Evasion complete; bot remains stopped', COLOR_SUCCESS)
    elif mode:
        character = get_character_data()
        if character and not character.get('dead') and not current_run_mode():
            if mode == 'bot':
                result = start_bot()
                label = 'Bot'
            else:
                result = start_trace(QtBind.text(gui, tbxTraceTarget).strip())
                label = 'Trace'
            if result:
                notify('%s resumed' % label, COLOR_SUCCESS)
            else:
                notify('phBot rejected %s resume' % label.lower(), COLOR_ERROR)
        else:
            notify('Resume cancelled: character unavailable or dead', COLOR_ERROR)
    set_state_label('MONITORING', COLOR_SUCCESS)


def poll_active_skill_confirmation(now):
    global active_skill_snapshot
    current = active_skills()
    current_ids = set(current.keys())
    added = current_ids - active_skill_snapshot
    active_skill_snapshot = current_ids
    if not added or not recent_boss_casts:
        return

    candidate = latest_unambiguous_cast(now)
    keywords = ('petrif', 'stone', 'paraly', 'tas ol', 'taş ol')
    relevant = bool(candidate in added or
                    VERIFIED_PETRIFY_EFFECT_IDS.intersection(added))
    if not relevant:
        for skill_id in added:
            info = current.get(skill_id) or {}
            identity = '%s %s' % (info.get('name', ''), info.get('servername', ''))
            if any(keyword in identity.lower() for keyword in keywords):
                relevant = True
                break
    debug_log('New active effects: %s; relevant=%s' % (sorted(added), relevant))
    if relevant:
        confirm_petrify(now, 'active debuff')


def poll_bad_effect_confirmation(now):
    global previous_bad_effects
    try:
        character = get_character_data()
    except Exception as error:
        debug_log('bad_effects read failed: %s' % error)
        return
    if not character or 'bad_effects' not in character:
        return
    try:
        current = int(character.get('bad_effects', 0) or 0)
    except Exception:
        return
    started = current & ~previous_bad_effects
    previous_bad_effects = current
    if started & PETRIFY_BAD_EFFECT:
        confirm_petrify(now, 'bad_effects petrify bit')


def handle_joymax(opcode, data):
    global last_cast_trigger_time
    now = time.time()
    try:
        if opcode != 0xB070 or not QtBind.isChecked(gui, cbxActive):
            return True
        if len(data) < 11 or not validate_settings(False):
            return True
        if data[:3] != ACTION_PREFIX:
            return True

        skill_id = struct.unpack_from('<H', data, 3)[0]
        caster_uid = struct.unpack_from('<I', data, 7)[0]
        boss = find_boss()
        if not boss or caster_uid != boss[0]:
            return True

        remember_boss_cast(skill_id, now)
        effective_skill = get_effective_skill_id(boss)
        identity = skill_identity(skill_id) or 'unknown'
        debug_log('Boss model=%s; cast=%d (%s); effective=%d' % (
            boss[1].get('model', '?'), skill_id, identity, effective_skill))
        if (accept_petrify_skill(skill_id, boss) and
                now - last_cast_trigger_time >= CAST_COOLDOWN_SECONDS):
            if begin_evasion(skill_id, now):
                last_cast_trigger_time = now
    except Exception as error:
        plugin_log('Packet processing error: %s' % error)
        set_event('Packet processing error', COLOR_ERROR)
    return True


def event_loop():
    global last_poll, loaded_profile, active_skill_snapshot, recent_boss_casts
    global previous_bad_effects
    now = time.time()
    if now - last_poll < POLL_SECONDS:
        return
    last_poll = now

    profile = character_profile()
    if profile and profile != loaded_profile:
        loaded_profile = profile
        load_config(profile)
        active_skill_snapshot = active_skill_ids()
        character = get_character_data() or {}
        previous_bad_effects = int(character.get('bad_effects', 0) or 0)

    recent_boss_casts = [cast for cast in recent_boss_casts
                         if now - cast['time'] <= CAST_CONFIRM_WINDOW]
    if not QtBind.isChecked(gui, cbxActive):
        return
    poll_bad_effect_confirmation(now)
    poll_active_skill_confirmation(now)
    if state == STATE_EVADING:
        poll_evasion(now)
    elif state == STATE_WAITING:
        poll_resume(now)


def teleported():
    global loaded_profile, active_skill_snapshot, previous_bad_effects
    cancel_automation('Teleport detected; pending automation cancelled', False)
    loaded_profile = ''
    previous_bad_effects = 0
    active_skill_snapshot = active_skill_ids()


def disconnected():
    global loaded_profile, previous_bad_effects
    cancel_automation('Disconnected; pending automation cancelled', True)
    loaded_profile = ''
    previous_bad_effects = 0
    set_state_label('DISCONNECTED', COLOR_ERROR)


def finished():
    cancel_automation('Plugin unloaded; pending automation cancelled', True)


QtBind.setChecked(gui, cbxAutoLearn, True)
active_skill_snapshot = active_skill_ids()
set_event('Enter the game to load settings', COLOR_MUTED)
log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
