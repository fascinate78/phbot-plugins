from phBot import *
import QtBind
import json
import os
import re
import struct
import time
import webbrowser
from threading import Timer


pName = 'FPvpHelperV2'
pVersion = '1.2.0'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

COLOR_PRIMARY = '#5b57e0'
COLOR_MUTED = '#9aa0ac'
COLOR_TEXT = '#2b3038'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#d93a4d'

WEAPON_SLOT = 6
SHIELD_SLOT = 7
EQUIP_COOLDOWN = 0.20
SHIELD_EQUIP_DELAY = 0.15
OFFSCREEN_X = 3000
GROUP_COUNT = 4


def fixed_width_text(content, width):
    return (
        '<table width="{0}" cellspacing="0" cellpadding="0">'
        '<tr><td>{1}</td></tr></table>'
    ).format(width, content)


def safe_html(value):
    return str(value).replace('&', '&amp;').replace('<', '&lt;').replace(
        '>', '&gt;').replace('"', '&quot;')


gui = QtBind.init(__name__, pName)

QtBind.createLabel(
    gui,
    u'<font color="%s" size="4"><b>⚔ %s</b></font>' %
    (COLOR_PRIMARY, pName),
    12, 6)
QtBind.createLabel(
    gui, '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion),
    205, 12)
chk_enabled = QtBind.createCheckBox(
    gui, 'enabled_changed', 'Enable', 250, 10)
btn_discord = QtBind.createButton(
    gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(
    gui, u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' %
    COLOR_PRIMARY,
    565, 11)
QtBind.createLineEdit(gui, '', 12, 30, 716, 1)


weapon_groups = []
weapons_12_widgets = []
weapons_34_widgets = []
shield_widgets = []
weapon_choices = {}
shield_choices = {}
skill_choices = {}
selected_weapons = [None for _ in range(GROUP_COUNT)]
selected_skills = [{} for _ in range(GROUP_COUNT)]
config_loaded = False
last_equip_time = 0.0
last_equip_key = None
current_view = 'weapons12'
equip_generation = 0


def create_weapon_group(index, x, widget_collection):
    number = index + 1
    title_label = QtBind.createLabel(
        gui,
        '<font color="%s"><b>WEAPON %d</b></font>' %
        (COLOR_PRIMARY, number),
        x, 42)
    weapon_combo = QtBind.createCombobox(gui, x, 62, 255, 22)
    select_button = QtBind.createButton(
        gui, 'select_weapon_%d' % number, u'✓ Select', x, 89)
    clear_button = QtBind.createButton(
        gui, 'clear_weapon_%d' % number, u'× Clear', x + 92, 89)
    selected_label = QtBind.createLabel(
        gui,
        fixed_width_text(
            '<font color="%s">Selected: none</font>' % COLOR_WARNING,
            250),
        x, 118)
    shield_checkbox = QtBind.createCheckBox(
        gui, 'shield_changed_%d' % number, 'Equip shield too', x, 140)
    trigger_label = QtBind.createLabel(
        gui, '<font color="%s">Trigger skill</font>' % COLOR_MUTED,
        x, 164)
    skill_combo = QtBind.createCombobox(gui, x, 181, 255, 22)
    add_button = QtBind.createButton(
        gui, 'add_skill_%d' % number, '+ Add Skill', x, 207)
    remove_button = QtBind.createButton(
        gui, 'remove_skill_%d' % number, u'− Remove', x + 105, 207)
    skill_list = QtBind.createList(gui, x, 235, 255, 54)
    widgets = [
        (title_label, x, 42),
        (weapon_combo, x, 62),
        (select_button, x, 89),
        (clear_button, x + 92, 89),
        (selected_label, x, 118),
        (shield_checkbox, x, 140),
        (trigger_label, x, 164),
        (skill_combo, x, 181),
        (add_button, x, 207),
        (remove_button, x + 105, 207),
        (skill_list, x, 235)
    ]
    widget_collection.extend(widgets)
    return {
        'weapon_combo': weapon_combo,
        'selected_label': selected_label,
        'shield_checkbox': shield_checkbox,
        'skill_combo': skill_combo,
        'skill_list': skill_list
    }


weapon_groups.append(create_weapon_group(0, 12, weapons_12_widgets))
weapon_groups.append(create_weapon_group(1, 286, weapons_12_widgets))
separator_12 = QtBind.createLineEdit(gui, '', 274, 42, 1, 247)
bottom_12 = QtBind.createLineEdit(gui, '', 12, 298, 529, 1)
weapons_12_widgets.extend([(separator_12, 274, 42), (bottom_12, 12, 298)])

weapon_groups.append(create_weapon_group(2, 12, weapons_34_widgets))
weapon_groups.append(create_weapon_group(3, 286, weapons_34_widgets))
separator_34 = QtBind.createLineEdit(gui, '', OFFSCREEN_X, 42, 1, 247)
bottom_34 = QtBind.createLineEdit(gui, '', OFFSCREEN_X, 298, 529, 1)
weapons_34_widgets.extend([(separator_34, 274, 42), (bottom_34, 12, 298)])
for hidden_widget, _, hidden_y in weapons_34_widgets:
    QtBind.move(gui, hidden_widget, OFFSCREEN_X, hidden_y)

settings_title = QtBind.createLabel(
    gui, '<font color="%s"><b>SHIELD</b></font>' % COLOR_PRIMARY,
    OFFSCREEN_X, 48)
settings_description = QtBind.createLabel(
    gui,
    '<font color="%s">Choose the shared shield for enabled weapon groups.</font>' % COLOR_MUTED,
    OFFSCREEN_X, 70)
cmb_shields = QtBind.createCombobox(gui, OFFSCREEN_X, 94, 330, 22)
btn_select_shield = QtBind.createButton(
    gui, 'select_shield_clicked', u'✓ Select Shield', OFFSCREEN_X, 124)
btn_clear_shield = QtBind.createButton(
    gui, 'clear_shield_clicked', u'× Clear Shield', OFFSCREEN_X, 124)
lbl_selected_shield = QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s">Selected shield: none</font>' % COLOR_WARNING,
        520),
    OFFSCREEN_X, 160)
shield_help = QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s">The selected shield is used only for weapon groups '
        'with Equip shield too enabled.</font>' % COLOR_MUTED,
        520),
    OFFSCREEN_X, 185)
shield_bottom = QtBind.createLineEdit(gui, '', OFFSCREEN_X, 298, 529, 1)

shield_widgets.extend([
    (settings_title, 12, 48),
    (settings_description, 12, 70),
    (cmb_shields, 12, 94),
    (btn_select_shield, 12, 124),
    (btn_clear_shield, 140, 124),
    (lbl_selected_shield, 12, 160),
    (shield_help, 12, 175),
    (shield_bottom, 12, 298)
])

# Fixed right navigation and actions panel
QtBind.createLineEdit(gui, '', 560, 42, 1, 256)
QtBind.createLabel(
    gui, '<font color="%s"><b>NAVIGATION</b></font>' % COLOR_PRIMARY,
    575, 42)
btn_weapons_12 = QtBind.createButton(
    gui, 'show_weapons_12_clicked', u'● Weapons 1-2', 575, 62)
btn_weapons_34 = QtBind.createButton(
    gui, 'show_weapons_34_clicked', u'○ Weapons 3-4', 575, 91)
btn_shield_view = QtBind.createButton(
    gui, 'show_shield_clicked', u'○ Shield', 575, 120)
QtBind.createLineEdit(gui, '', 575, 153, 150, 1)
QtBind.createLabel(
    gui, '<font color="%s"><b>ACTIONS</b></font>' % COLOR_PRIMARY,
    575, 164)
btn_refresh_all = QtBind.createButton(
    gui, 'refresh_all_clicked', u'↻ Refresh All', 575, 184)
btn_save_main = QtBind.createButton(
    gui, 'save_settings_clicked', u'💾 Save Settings', 575, 213)
QtBind.createLineEdit(gui, '', 575, 246, 150, 1)
QtBind.createLabel(
    gui, '<font color="%s"><b>LIVE STATUS</b></font>' % COLOR_PRIMARY,
    575, 252)
lbl_status = QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s"><b>READY</b><br>&nbsp;</font>' % COLOR_SUCCESS,
        145),
    575, 268)

selected_shield = None


def set_status(message, color=COLOR_SUCCESS):
    QtBind.setText(
        gui,
        lbl_status,
        fixed_width_text(
            '<font color="%s"><b>%s</b></font>' %
            (color, safe_html(message)),
            145))


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        set_status('Opening Discord invite...', COLOR_SUCCESS)
    except Exception as error:
        log('[%s] Discord link error: %s' % (pName, error))
        set_status('Could not open Discord invite', COLOR_ERROR)


def move_widgets(widgets, visible):
    for widget, x, y in widgets:
        QtBind.move(gui, widget, x if visible else OFFSCREEN_X, y)


def show_view(view):
    global current_view
    current_view = view
    move_widgets(weapons_12_widgets, view == 'weapons12')
    move_widgets(weapons_34_widgets, view == 'weapons34')
    move_widgets(shield_widgets, view == 'shield')
    QtBind.setText(
        gui, btn_weapons_12,
        u'● Weapons 1-2' if view == 'weapons12' else u'○ Weapons 1-2')
    QtBind.setText(
        gui, btn_weapons_34,
        u'● Weapons 3-4' if view == 'weapons34' else u'○ Weapons 3-4')
    QtBind.setText(
        gui, btn_shield_view,
        u'● Shield' if view == 'shield' else u'○ Shield')


def show_weapons_12_clicked():
    show_view('weapons12')


def show_weapons_34_clicked():
    show_view('weapons34')


def show_shield_clicked():
    show_view('shield')
    set_status('Shield selection and settings.')


def character_key():
    try:
        character = get_character_data()
        if character and character.get('name'):
            raw = '%s_%s' % (
                character.get('server', 'server'),
                character.get('name', 'character'))
            return re.sub(r'[<>:"/\\|?*]', '_', str(raw))
    except Exception:
        pass
    return 'default'


def config_path():
    try:
        base = get_config_dir()
    except Exception:
        base = ''
    if not base:
        base = os.path.dirname(os.path.realpath(__file__))
    folder = os.path.join(base, pName)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    return os.path.join(folder, character_key() + '.json')


def item_descriptor(item, display):
    return {
        'model': int(item.get('model', 0)),
        'servername': item.get('servername', ''),
        'plus': int(item.get('plus', 0)),
        'display': display
    }


def inventory_items():
    inventory = get_inventory()
    if not inventory or not inventory.get('items'):
        return []
    return [(slot, item) for slot, item in enumerate(inventory['items']) if item]


def item_type(item):
    try:
        data = get_item(int(item.get('model', 0)))
        if not data or int(data.get('tid1', 0)) != 1:
            return None
        tid2 = int(data.get('tid2', 0))
        if tid2 == 6:
            return 'weapon'
        if tid2 == 4:
            return 'shield'
    except Exception:
        pass
    return None


def item_display(item, slot):
    return '+%d %s - Slot %d' % (
        int(item.get('plus', 0)), item.get('name', 'Unknown item'), slot)


def refresh_items():
    global shield_choices
    weapon_choices.clear()
    shield_choices.clear()
    for group in weapon_groups:
        QtBind.clear(gui, group['weapon_combo'])
    QtBind.clear(gui, cmb_shields)
    try:
        for slot, item in inventory_items():
            kind = item_type(item)
            if kind not in ('weapon', 'shield'):
                continue
            display = item_display(item, slot)
            descriptor = item_descriptor(item, display)
            if kind == 'weapon':
                weapon_choices[display] = descriptor
                for group in weapon_groups:
                    QtBind.append(gui, group['weapon_combo'], display)
            else:
                shield_choices[display] = descriptor
                QtBind.append(gui, cmb_shields, display)
        set_status('%d weapons and %d shields found.' %
                   (len(weapon_choices), len(shield_choices)))
    except Exception as error:
        log('[%s] Equipment refresh error: %s' % (pName, error))
        set_status('Equipment could not be loaded.', COLOR_ERROR)


def refresh_skills():
    skill_choices.clear()
    for group in weapon_groups:
        QtBind.clear(gui, group['skill_combo'])
    try:
        rows = []
        for raw_id, info in (get_skills() or {}).items():
            skill_id = int(raw_id)
            display = '%s (Lv.%s) [ID: %d]' % (
                info.get('name', 'Skill'), info.get('level', 0), skill_id)
            rows.append((info.get('name', '').lower(), skill_id, display))
        for _, skill_id, display in sorted(rows):
            skill_choices[display] = skill_id
            for group in weapon_groups:
                QtBind.append(gui, group['skill_combo'], display)
        set_status('%d skills loaded.' % len(rows))
    except Exception as error:
        log('[%s] Skill refresh error: %s' % (pName, error))
        set_status('Skills could not be loaded.', COLOR_ERROR)


def update_weapon_label(index):
    weapon = selected_weapons[index]
    if weapon:
        display = weapon.get('display', 'Unknown weapon').rsplit(
            ' - Slot ', 1)[0]
        content = '<font color="%s"><b>Selected:</b> %s</font>' % (
            COLOR_SUCCESS, safe_html(display))
    else:
        content = '<font color="%s"><b>Selected:</b> none</font>' % \
            COLOR_WARNING
    QtBind.setText(
        gui, weapon_groups[index]['selected_label'],
        fixed_width_text(content, 250))


def update_shield_label():
    if selected_shield:
        display = selected_shield.get('display', 'Unknown shield').rsplit(
            ' - Slot ', 1)[0]
        content = '<font color="%s"><b>Shield:</b> %s</font>' % (
            COLOR_SUCCESS, safe_html(display))
    else:
        content = '<font color="%s"><b>Shield:</b> none</font>' % \
            COLOR_WARNING
    QtBind.setText(
        gui, lbl_selected_shield, fixed_width_text(content, 520))


def redraw_skill_list(index):
    widget = weapon_groups[index]['skill_list']
    QtBind.clear(gui, widget)
    for skill_id in sorted(selected_skills[index]):
        QtBind.append(gui, widget, selected_skills[index][skill_id])


def save_config():
    if not config_loaded:
        return False
    data = {
        'enabled': QtBind.isChecked(gui, chk_enabled),
        'shield': selected_shield,
        'groups': []
    }
    for index, group in enumerate(weapon_groups):
        data['groups'].append({
            'weapon': selected_weapons[index],
            'skills': list(selected_skills[index].keys()),
            'equip_shield': QtBind.isChecked(
                gui, group['shield_checkbox'])
        })
    try:
        path = config_path()
        temp_path = path + '.tmp'
        with open(temp_path, 'w', encoding='utf-8') as config_file:
            json.dump(data, config_file, ensure_ascii=False, indent=2)
        os.replace(temp_path, path)
        return True
    except Exception as error:
        log('[%s] Settings save error: %s' % (pName, error))
        set_status('Settings could not be saved.', COLOR_ERROR)
        return False


def load_config():
    global config_loaded, selected_shield
    config_loaded = False
    selected_shield = None
    for index in range(GROUP_COUNT):
        selected_weapons[index] = None
        selected_skills[index].clear()
        QtBind.setChecked(gui, weapon_groups[index]['shield_checkbox'], False)
    QtBind.setChecked(gui, chk_enabled, False)
    try:
        path = config_path()
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as config_file:
                data = json.load(config_file)
            QtBind.setChecked(gui, chk_enabled, bool(data.get('enabled', False)))
            shield = data.get('shield')
            if isinstance(shield, dict):
                selected_shield = shield
            groups = data.get('groups', [])
            for index in range(min(GROUP_COUNT, len(groups))):
                saved_group = groups[index]
                weapon = saved_group.get('weapon')
                if isinstance(weapon, dict):
                    selected_weapons[index] = weapon
                QtBind.setChecked(
                    gui, weapon_groups[index]['shield_checkbox'],
                    bool(saved_group.get('equip_shield', False)))
                for raw_id in saved_group.get('skills', []):
                    skill_id = int(raw_id)
                    info = get_skill(skill_id)
                    name = info.get('name', 'Skill') if info else 'Skill'
                    level = info.get('level', 0) if info else 0
                    selected_skills[index][skill_id] = \
                        '%s (Lv.%s) [ID: %d]' % (name, level, skill_id)
    except Exception as error:
        log('[%s] Settings load error: %s' % (pName, error))
        set_status('Settings could not be loaded.', COLOR_ERROR)
    config_loaded = True
    for index in range(GROUP_COUNT):
        update_weapon_label(index)
        redraw_skill_list(index)
    update_shield_label()


def select_weapon(index):
    display = QtBind.text(gui, weapon_groups[index]['weapon_combo'])
    weapon = weapon_choices.get(display)
    if not weapon:
        set_status('Select a weapon for Weapon %d.' % (index + 1), COLOR_WARNING)
        return
    signature = (weapon.get('model'), weapon.get('servername'), weapon.get('plus'))
    for other_index, other_weapon in enumerate(selected_weapons):
        if other_index == index or not other_weapon:
            continue
        other_signature = (
            other_weapon.get('model'), other_weapon.get('servername'),
            other_weapon.get('plus'))
        if signature == other_signature:
            set_status(
                'This weapon is already assigned to Weapon %d.' %
                (other_index + 1),
                COLOR_ERROR)
            return
    selected_weapons[index] = dict(weapon)
    update_weapon_label(index)
    save_config()
    set_status('Weapon %d selected.' % (index + 1))


def clear_weapon(index):
    selected_weapons[index] = None
    update_weapon_label(index)
    save_config()
    set_status('Weapon %d selection cleared.' % (index + 1))


def add_skill(index):
    display = QtBind.text(gui, weapon_groups[index]['skill_combo'])
    skill_id = skill_choices.get(display)
    if skill_id is None:
        set_status('Select a skill first.', COLOR_WARNING)
        return
    for other_index in range(GROUP_COUNT):
        if other_index != index and skill_id in selected_skills[other_index]:
            set_status(
                'Skill is already assigned to Weapon %d.' % (other_index + 1),
                COLOR_ERROR)
            return
    selected_skills[index][skill_id] = display
    redraw_skill_list(index)
    save_config()
    set_status('Skill added to Weapon %d.' % (index + 1))


def remove_skill(index):
    display = QtBind.text(gui, weapon_groups[index]['skill_list'])
    if not display:
        set_status('Select a skill to remove.', COLOR_WARNING)
        return
    removed = False
    for skill_id, saved_display in list(selected_skills[index].items()):
        if saved_display == display:
            del selected_skills[index][skill_id]
            removed = True
            break
    if not removed:
        set_status('Selected skill could not be matched.', COLOR_ERROR)
        return
    redraw_skill_list(index)
    save_config()
    set_status('Skill removed from Weapon %d.' % (index + 1))


def find_selected_item(descriptor, expected_type):
    if not descriptor:
        return None
    exact = []
    model_matches = []
    for slot, item in inventory_items():
        if item_type(item) != expected_type:
            continue
        if int(item.get('model', 0)) != int(descriptor.get('model', 0)):
            continue
        model_matches.append((slot, item))
        if (item.get('servername', '') == descriptor.get('servername', '') and
                int(item.get('plus', 0)) == int(descriptor.get('plus', 0))):
            exact.append((slot, item))
    if exact:
        return exact[0]
    return model_matches[0] if model_matches else None


def inject_item_move(source_slot, target_slot):
    packet = struct.pack('<BBBH', 0, int(source_slot), int(target_slot), 0)
    inject_joymax(0x7034, packet, False)


def delayed_shield_move(generation, source_slot, shield_name):
    if generation != equip_generation:
        return
    inject_item_move(source_slot, SHIELD_SLOT)
    log('[%s] Delayed shield request: %s [slot %d -> %d]' % (
        pName, shield_name, source_slot, SHIELD_SLOT))


def equip_group(index, skill_id):
    global last_equip_time, last_equip_key, equip_generation
    weapon = selected_weapons[index]
    if not weapon:
        set_status('Weapon %d has no selected weapon.' % (index + 1), COLOR_ERROR)
        return
    found_weapon = find_selected_item(weapon, 'weapon')
    if not found_weapon:
        set_status('Weapon %d was not found in inventory.' % (index + 1), COLOR_ERROR)
        return

    use_shield = QtBind.isChecked(
        gui, weapon_groups[index]['shield_checkbox'])
    found_shield = None
    if use_shield:
        if not selected_shield:
            set_status('Weapon %d requires a selected shield.' % (index + 1),
                       COLOR_ERROR)
            return
        found_shield = find_selected_item(selected_shield, 'shield')
        if not found_shield:
            set_status('Selected shield was not found in inventory.', COLOR_ERROR)
            return

    weapon_slot, weapon_item = found_weapon
    shield_slot = found_shield[0] if found_shield else None
    equip_key = (index, weapon_slot, shield_slot)
    now = time.time()
    if equip_key == last_equip_key and now - last_equip_time < EQUIP_COOLDOWN:
        return

    equip_generation += 1
    current_generation = equip_generation
    changed = False
    if weapon_slot != WEAPON_SLOT:
        inject_item_move(weapon_slot, WEAPON_SLOT)
        changed = True
    if found_shield and shield_slot != SHIELD_SLOT:
        shield_timer = Timer(
            SHIELD_EQUIP_DELAY,
            delayed_shield_move,
            (current_generation, shield_slot,
             found_shield[1].get('name', 'Shield')))
        shield_timer.daemon = True
        shield_timer.start()
        changed = True

    last_equip_key = equip_key
    last_equip_time = now
    skill_name = selected_skills[index].get(skill_id, str(skill_id))
    if changed:
        set_status('Weapon %d equipment requested.' % (index + 1))
        log('[%s] Trigger %s -> Weapon %d: %s%s' % (
            pName, skill_name, index + 1,
            weapon_item.get('name', 'Weapon'),
            ' + shield' if found_shield else ''))
    else:
        set_status('Weapon %d is already equipped.' % (index + 1))


def refresh_all_clicked():
    refresh_items()
    refresh_skills()


def select_weapon_1():
    select_weapon(0)


def select_weapon_2():
    select_weapon(1)


def select_weapon_3():
    select_weapon(2)


def select_weapon_4():
    select_weapon(3)


def clear_weapon_1():
    clear_weapon(0)


def clear_weapon_2():
    clear_weapon(1)


def clear_weapon_3():
    clear_weapon(2)


def clear_weapon_4():
    clear_weapon(3)


def add_skill_1():
    add_skill(0)


def add_skill_2():
    add_skill(1)


def add_skill_3():
    add_skill(2)


def add_skill_4():
    add_skill(3)


def remove_skill_1():
    remove_skill(0)


def remove_skill_2():
    remove_skill(1)


def remove_skill_3():
    remove_skill(2)


def remove_skill_4():
    remove_skill(3)


def shield_changed_1(checked):
    save_config()
    set_status('Weapon 1 shield option updated.')


def shield_changed_2(checked):
    save_config()
    set_status('Weapon 2 shield option updated.')


def shield_changed_3(checked):
    save_config()
    set_status('Weapon 3 shield option updated.')


def shield_changed_4(checked):
    save_config()
    set_status('Weapon 4 shield option updated.')


def select_shield_clicked():
    global selected_shield
    display = QtBind.text(gui, cmb_shields)
    shield = shield_choices.get(display)
    if not shield:
        set_status('Select a shield first.', COLOR_WARNING)
        return
    selected_shield = dict(shield)
    update_shield_label()
    save_config()
    set_status('Shield selected.')


def clear_shield_clicked():
    global selected_shield
    selected_shield = None
    update_shield_label()
    save_config()
    set_status('Shield selection cleared.')


def enabled_changed(checked):
    global equip_generation
    if not checked:
        equip_generation += 1
    save_config()
    set_status('Enabled.' if checked else 'Disabled.',
               COLOR_SUCCESS if checked else COLOR_MUTED)


def save_settings_clicked():
    if save_config():
        set_status('Settings saved for this character.')


def handle_silkroad(opcode, data):
    if opcode != 0x7074 or not QtBind.isChecked(gui, chk_enabled):
        return True
    try:
        if len(data) >= 6 and data[0] == 1 and data[1] == 4:
            skill_id = struct.unpack_from('<I', data, 2)[0]
            for index in range(GROUP_COUNT):
                if skill_id in selected_skills[index]:
                    equip_group(index, skill_id)
                    break
    except Exception as error:
        log('[%s] Skill packet processing error: %s' % (pName, error))
        set_status('Skill packet could not be processed.', COLOR_ERROR)
    return True


def teleported():
    global equip_generation
    equip_generation += 1
    load_config()
    refresh_items()
    refresh_skills()


def finished():
    global equip_generation
    equip_generation += 1


load_config()
log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
