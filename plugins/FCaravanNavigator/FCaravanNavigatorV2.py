from phBot import *
import phBotChat
import QtBind
import json
import math
import os
import time


pName = "FCaravanNavigator V2"
pVersion = "2.0.0"
pUrl = ""

PATHFINDING_COOLDOWN = 6.0
ARRIVAL_DISTANCE = 20.0
C_ACCENT = "#5b57e0"
C_LABEL = "#6b7280"
C_VALUE = "#2b3038"
C_SUCCESS = "#1f9d63"
C_ERROR = "#d93a4d"
C_MUTED = "#9aa0ac"
C_WARNING = "#c98a1a"
C_BLUE = "#2b8fd6"
OFFSCREEN_X = 3000
EVENT_TRANSPORT_DIED = 3
EVENT_PLAYER_ATTACKING = 4
EVENT_DIED = 7
TRANSPORT_DEATH_CONFIRM_SECONDS = 1.5
SETTINGS_DEFAULTS = {
    "schema_version": 1,
    "arrival_sound_enabled": True,
    "arrival_sound": "",
    "stop_on_character_death": True,
    "stop_on_transport_death": True,
    "attacker_tracking_enabled": True,
    "attacker_memory_seconds": 15
}
locations = [
    {
        "name": "Roc Special",
        "category": "special",
        "region": 23411,
        "x": -3798,
        "y": -190,
        "z": 2626
    },
    {
        "name": "Bandit Special",
        "category": "special",
        "region": 23712,
        "x": 4840,
        "y": 140,
        "z": 1384
    },
    {
        "name": "Taklamakan Special",
        "category": "special",
        "region": 26753,
        "x": -1134,
        "y": 2458,
        "z": 112
    },
    {
        "name": "Jangan",
        "category": "town",
        "region": 25000,
        "x": 6504,
        "y": 1004,
        "z": 0
    },
    {
        "name": "Donwhang",
        "category": "town",
        "region": 26265,
        "x": 3502,
        "y": 2081,
        "z": -106
    },
    {
        "name": "Hotan",
        "category": "town",
        "region": 23687,
        "x": 148,
        "y": 82,
        "z": 243
    }
]
location_buttons = []
location_callback_names = []
location_group_widgets = []
destination_widgets = []
last_pathfinding_time = 0.0
navigation_active = False
current_location = None
navigation_start_time = None
settings = dict(SETTINGS_DEFAULTS)
settings_mode = False
settings_widgets = []
available_sounds = []
last_player_attacker = None
last_player_attack_time = 0.0
pending_transport_death_time = 0.0
pending_transport_death_region = 0

gui = QtBind.init(__name__, pName)
title_label = QtBind.createLabel(
    gui,
    '<font color="#5b57e0" size="4"><b>❖ FCARAVAN NAVIGATOR</b></font>',
    12,
    6
)
version_label = QtBind.createLabel(
    gui,
    '<font color="#9aa0ac">v{0}</font>'.format(pVersion),
    205,
    12
)
author_label = QtBind.createLabel(
    gui,
    '<font color="#5b57e0"><b>♥ Made By FascinaTe</b></font>',
    585,
    11
)
separator_line = QtBind.createLineEdit(gui, "", 12, 30, 716, 1)
section_label = QtBind.createLabel(
    gui,
    '<font color="#5b57e0"><b>🚦 ROUTE CONTROLS</b></font>',
    12,
    40
)
reload_button = QtBind.createButton(
    gui, "reload_config", "↻  Reload Locations", 12, 62
)
stop_button = QtBind.createButton(
    gui, "stop_navigation", "⏹️  Stop Navigation", 165, 62
)
settings_button = QtBind.createButton(
    gui, "show_settings", "⚙  Settings", 310, 62
)
destinations_button = QtBind.createButton(
    gui, "show_destinations", "←  Destinations", OFFSCREEN_X, 62
)
status_label = QtBind.createLabel(
    gui,
    '<table width="280" cellspacing="0" cellpadding="0"><tr><td>'
    '<font color="#9aa0ac">Loading destinations...</font>'
    '</td></tr></table>',
    440,
    68
)
controls_separator_line = QtBind.createLineEdit(gui, "", 12, 106, 716, 1)
panel_separator_line = QtBind.createLineEdit(gui, "", 408, 120, 1, 160)
live_header_label = QtBind.createLabel(
    gui,
    '<font color="#5b57e0"><b>● LIVE NAVIGATION</b></font>',
    428,
    122
)
live_header_line = QtBind.createLineEdit(gui, "", 428, 142, 298, 1)
QtBind.createLabel(
    gui, '<font color="#6b7280"><b>Destination</b></font>', 428, 154
)
navigation_label = QtBind.createLabel(
    gui,
    '<table width="190" cellspacing="0" cellpadding="0"><tr><td>'
    '<font color="#2b3038">➤ Taklamakan Special</font>'
    '</td></tr></table>',
    520,
    154
)
QtBind.createLabel(
    gui, '<font color="#6b7280"><b>Status</b></font>', 428, 180
)
navigation_state_label = QtBind.createLabel(
    gui,
    '<table width="190" cellspacing="0" cellpadding="0"><tr><td>'
    '<font color="#c98a1a"><b>● PREPARING</b></font>'
    '</td></tr></table>',
    520,
    180
)
QtBind.createLabel(
    gui, '<font color="#6b7280"><b>Travel Time</b></font>', 428, 206
)
duration_label = QtBind.createLabel(
    gui, '<font color="#2b3038">⏱ 00:00:00</font>', 520, 206
)
QtBind.createLabel(
    gui, '<font color="#6b7280"><b>Route Type</b></font>', 428, 232
)
route_label = QtBind.createLabel(
    gui,
    '<table width="190" cellspacing="0" cellpadding="0"><tr><td>'
    '<font color="#1f9d63"><b>🐫 CARAVAN / FERRY</b></font>'
    '</td></tr></table>',
    520,
    232
)
QtBind.createLabel(
    gui, '<font color="#6b7280"><b>Last Attacker</b></font>', 428, 258
)
attacker_label = QtBind.createLabel(
    gui,
    '<table width="190" cellspacing="0" cellpadding="0"><tr><td>'
    '<font color="#9aa0ac">⚔ None</font>'
    '</td></tr></table>',
    520,
    258
)


def plugin_log(message):
    log("[FCaravanNavigator V2] {0}".format(message))


def client_notice(message):
    try:
        phBotChat.ClientNotice(
            "[FCaravanNavigator | Made by FascinaTe] {0}".format(message)
        )
    except Exception as error:
        plugin_log("Could not display client notice: {0}".format(error))


def fixed_width_text(content, width):
    return (
        '<table width="{0}" cellspacing="0" cellpadding="0">'
        '<tr><td>{1}</td></tr></table>'
    ).format(width, content)


def set_status(message, color=C_MUTED):
    QtBind.setText(
        gui,
        status_label,
        fixed_width_text(
            '<font color="{0}">{1}</font>'.format(color, str(message)),
            190
        )
    )


def set_navigation_status(state, color):
    if current_location is None:
        target_name = "None"
    else:
        target_name = current_location["name"]

    QtBind.setText(
        gui,
        navigation_label,
        fixed_width_text(
            '<font color="#2b3038">➤ {0}</font>'.format(target_name),
            190
        )
    )
    QtBind.setText(
        gui,
        navigation_state_label,
        fixed_width_text(
            '<b><font color="{0}">● {1}</font></b>'.format(color, state),
            280
        )
    )


def format_duration(total_seconds):
    total_seconds = max(0, int(total_seconds))
    hours = total_seconds // 3600
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    if hours > 0:
        minutes = minutes % 60
        return "{0:02d}:{1:02d}:{2:02d}".format(hours, minutes, seconds)
    return "{0:02d}:{1:02d}".format(minutes, seconds)


def set_duration_status(prefix, elapsed_seconds):
    text = '<font color="#2b3038">⏱ {0}</font>'.format(
        format_duration(elapsed_seconds)
    )
    QtBind.setText(gui, duration_label, text)


def set_route_status(route_name, color):
    text = '<b><font color="{0}">🐫 {1}</font></b>'.format(color, route_name)
    QtBind.setText(gui, route_label, fixed_width_text(text, 190))


def set_attacker_status(name, color=C_MUTED):
    if not name:
        name = "None"
    text = '<font color="{0}">⚔ {1}</font>'.format(color, name)
    QtBind.setText(gui, attacker_label, fixed_width_text(text, 190))


def get_settings_directory():
    try:
        base_directory = get_config_dir()
    except Exception:
        base_directory = None
    if not base_directory:
        base_directory = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_directory, pName)


def get_settings_path():
    return os.path.join(get_settings_directory(), "settings.json")


def get_sounds_directory():
    return os.path.join(get_settings_directory(), "Sounds")


def ensure_settings_directories():
    try:
        settings_directory = get_settings_directory()
        sounds_directory = get_sounds_directory()
        if not os.path.isdir(settings_directory):
            os.makedirs(settings_directory)
        if not os.path.isdir(sounds_directory):
            os.makedirs(sounds_directory)
        return True
    except Exception as error:
        plugin_log("Could not create settings directories: {0}".format(error))
        return False


def load_settings():
    global settings

    settings = dict(SETTINGS_DEFAULTS)
    ensure_settings_directories()
    path = get_settings_path()
    if not os.path.isfile(path):
        save_settings_file()
        return

    try:
        with open(path, "r", encoding="utf-8") as settings_file:
            loaded = json.load(settings_file)
        if not isinstance(loaded, dict):
            raise ValueError("settings root must be an object")
        for key in SETTINGS_DEFAULTS:
            if key in loaded:
                settings[key] = loaded[key]
        settings["arrival_sound_enabled"] = bool(settings["arrival_sound_enabled"])
        settings["stop_on_character_death"] = bool(settings["stop_on_character_death"])
        settings["stop_on_transport_death"] = bool(settings["stop_on_transport_death"])
        settings["attacker_tracking_enabled"] = bool(settings["attacker_tracking_enabled"])
        settings["arrival_sound"] = os.path.basename(str(settings["arrival_sound"]))
        memory_seconds = int(settings["attacker_memory_seconds"])
        settings["attacker_memory_seconds"] = max(1, min(300, memory_seconds))
        plugin_log("Settings loaded")
    except Exception as error:
        settings = dict(SETTINGS_DEFAULTS)
        plugin_log("Could not load settings; defaults restored: {0}".format(error))


def save_settings_file():
    if not ensure_settings_directories():
        return False
    try:
        with open(get_settings_path(), "w", encoding="utf-8") as settings_file:
            json.dump(settings, settings_file, ensure_ascii=False, indent=2)
            settings_file.write("\n")
        return True
    except Exception as error:
        plugin_log("Could not save settings: {0}".format(error))
        return False


def selected_sound_name():
    try:
        selected = QtBind.text(gui, sound_combobox).strip()
    except Exception:
        return ""
    if selected.startswith("("):
        return ""
    return os.path.basename(selected)


def refresh_sounds():
    global available_sounds

    ensure_settings_directories()
    selected = settings.get("arrival_sound", "")
    try:
        current = selected_sound_name()
        if current:
            selected = current
    except Exception:
        pass

    try:
        available_sounds = sorted(
            filename for filename in os.listdir(get_sounds_directory())
            if filename.lower().endswith(".wav")
            and os.path.isfile(os.path.join(get_sounds_directory(), filename))
        )
    except Exception as error:
        available_sounds = []
        plugin_log("Could not scan sound files: {0}".format(error))

    QtBind.clear(gui, sound_combobox)
    if not available_sounds:
        QtBind.append(gui, sound_combobox, "(No WAV files found)")
        return

    for filename in available_sounds:
        QtBind.append(gui, sound_combobox, filename)
    if selected in available_sounds:
        QtBind.setText(gui, sound_combobox, selected)


def play_selected_sound():
    sound_name = selected_sound_name()
    if not sound_name:
        set_status("No WAV sound selected", C_WARNING)
        return False
    sound_path = os.path.join(get_sounds_directory(), sound_name)
    if not os.path.isfile(sound_path):
        set_status("Sound file not found", C_ERROR)
        return False
    try:
        play_wav(sound_path)
        plugin_log("Playing sound: {0}".format(sound_name))
        return True
    except Exception as error:
        plugin_log("Could not play sound: {0}".format(error))
        set_status("Could not play sound", C_ERROR)
        return False


def convert_number(value, field_name):
    if isinstance(value, bool):
        raise ValueError("{0} must be numeric".format(field_name))

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("{0} must be finite".format(field_name))
        if value.is_integer():
            return int(value)
        return value

    if isinstance(value, str):
        value = value.strip()
        if not value:
            raise ValueError("{0} must not be empty".format(field_name))
        try:
            return int(value)
        except ValueError:
            number = float(value)
            if not math.isfinite(number):
                raise ValueError("{0} must be finite".format(field_name))
            if number.is_integer():
                return int(number)
            return number

    raise ValueError("{0} must be an integer or float".format(field_name))


def validate_location(record, index):
    if not isinstance(record, dict):
        plugin_log("Skipping location {0}: record is not an object".format(index))
        return None

    name = record.get("name")
    if not isinstance(name, str) or not name.strip():
        plugin_log("Skipping location {0}: name must be a non-empty string".format(index))
        return None

    category = record.get("category")
    if not isinstance(category, str) or not category.strip():
        plugin_log(
            "Skipping location {0} ({1}): category must be town or special".format(
                index, name.strip()
            )
        )
        return None

    category = category.strip().lower()
    if category not in ("town", "special"):
        plugin_log(
            "Skipping location {0} ({1}): unsupported category {2}".format(
                index, name.strip(), category
            )
        )
        return None

    missing_fields = []
    for field_name in ("region", "x", "y", "z"):
        if field_name not in record:
            missing_fields.append(field_name)

    if missing_fields:
        plugin_log(
            "Skipping location {0} ({1}): missing {2}".format(
                index, name.strip(), ", ".join(missing_fields)
            )
        )
        return None

    try:
        return {
            "name": name.strip(),
            "category": category,
            "region": convert_number(record["region"], "region"),
            "x": convert_number(record["x"], "x"),
            "y": convert_number(record["y"], "y"),
            "z": convert_number(record["z"], "z")
        }
    except (TypeError, ValueError, OverflowError) as error:
        plugin_log(
            "Skipping location {0} ({1}): {2}".format(index, name.strip(), error)
        )
        return None


def load_locations():
    valid_locations = []
    for index, record in enumerate(locations):
        location = validate_location(record, index)
        if location is not None:
            valid_locations.append(location)
    return valid_locations


def clear_location_buttons():
    global location_buttons
    global location_callback_names
    global location_group_widgets
    global destination_widgets

    for button in location_buttons:
        try:
            QtBind.destroy(gui, button)
        except Exception as error:
            plugin_log("Could not remove a location button: {0}".format(error))

    for widget in location_group_widgets:
        try:
            QtBind.destroy(gui, widget)
        except Exception as error:
            plugin_log("Could not remove a location group widget: {0}".format(error))

    for callback_name in location_callback_names:
        if callback_name in globals():
            del globals()[callback_name]

    location_buttons = []
    location_callback_names = []
    location_group_widgets = []
    destination_widgets = []


def make_location_callback(location_index):
    def location_callback():
        navigate_to_location(location_index)
    return location_callback


def create_location_buttons():
    global location_buttons
    global location_callback_names
    global location_group_widgets
    global destination_widgets

    category_settings = (
        ("town", "🏙️ TOWNS", C_BLUE, "🏛️"),
        ("special", "⭐ SPECIAL LOCATIONS", C_ACCENT, "📍")
    )
    current_y = 122

    for category, title, color, button_icon in category_settings:
        category_locations = [
            (index, location)
            for index, location in enumerate(locations)
            if location["category"] == category
        ]
        if not category_locations:
            continue

        group_label = QtBind.createLabel(
            gui,
            '<font color="{0}"><b>{1}</b></font>'.format(color, title),
            12,
            current_y
        )
        group_line = QtBind.createLineEdit(gui, "", 12, current_y + 19, 374, 1)
        location_group_widgets.append(group_label)
        location_group_widgets.append(group_line)
        destination_widgets.append((group_label, 12, current_y))
        destination_widgets.append((group_line, 12, current_y + 19))
        current_y += 28

        for group_index, item in enumerate(category_locations):
            location_index, location = item
            callback_name = "navigate_location_{0}".format(location_index)
            callback = make_location_callback(location_index)
            callback.__name__ = callback_name
            globals()[callback_name] = callback

            column = group_index % 2
            row = group_index // 2
            button = QtBind.createButton(
                gui,
                callback_name,
                "{0}  {1}".format(button_icon, location["name"]),
                12 + (column * 190),
                current_y + (row * 30)
            )
            location_buttons.append(button)
            location_callback_names.append(callback_name)
            destination_widgets.append(
                (button, 12 + (column * 190), current_y + (row * 30))
            )

        row_count = int(math.ceil(len(category_locations) / 2.0))
        current_y += (row_count * 30) + 10


def create_settings_gui():
    global settings_widgets
    global sound_enabled_checkbox
    global sound_combobox
    global stop_character_checkbox
    global stop_transport_checkbox
    global attacker_tracking_checkbox
    global attacker_seconds_edit

    settings_widgets = []

    def add_widget(widget, x, y):
        settings_widgets.append((widget, x, y))
        return widget

    add_widget(
        QtBind.createLabel(
            gui,
            '<font color="#5b57e0"><b>🔔 ARRIVAL NOTIFICATION</b></font>',
            12,
            122
        ),
        12,
        122
    )
    add_widget(QtBind.createLineEdit(gui, "", 12, 142, 374, 1), 12, 142)
    sound_enabled_checkbox = add_widget(
        QtBind.createCheckBox(
            gui, "settings_changed", "Enable arrival sound", 12, 150
        ),
        12,
        150
    )
    add_widget(QtBind.createLabel(gui, "Sound:", 12, 178), 12, 178)
    sound_combobox = add_widget(
        QtBind.createCombobox(gui, 65, 174, 220, 22), 65, 174
    )
    add_widget(
        QtBind.createButton(gui, "refresh_sounds", "↻ Refresh", 12, 202),
        12,
        202
    )
    add_widget(
        QtBind.createButton(gui, "test_sound", "▶ Test Sound", 112, 202),
        112,
        202
    )
    add_widget(
        QtBind.createButton(gui, "save_settings", "💾 Save Settings", 232, 202),
        232,
        202
    )
    add_widget(
        QtBind.createLabel(
            gui, '<font color="#5b57e0"><b>🛡 SAFETY</b></font>', 12, 238
        ),
        12,
        238
    )
    add_widget(QtBind.createLineEdit(gui, "", 12, 258, 374, 1), 12, 258)
    stop_character_checkbox = add_widget(
        QtBind.createCheckBox(
            gui, "settings_changed", "Stop on character death", 12, 266
        ),
        12,
        266
    )
    stop_transport_checkbox = add_widget(
        QtBind.createCheckBox(
            gui, "settings_changed", "Stop on transport death", 200, 266
        ),
        200,
        266
    )
    attacker_tracking_checkbox = add_widget(
        QtBind.createCheckBox(
            gui, "settings_changed", "Track last player attacker", 12, 292
        ),
        12,
        292
    )
    add_widget(QtBind.createLabel(gui, "Memory (sec):", 200, 295), 200, 295)
    attacker_seconds_edit = add_widget(
        QtBind.createLineEdit(gui, "15", 290, 291, 50, 20), 290, 291
    )

    for widget, x, y in settings_widgets:
        QtBind.move(gui, widget, OFFSCREEN_X, y)


def apply_settings_to_gui():
    QtBind.setChecked(gui, sound_enabled_checkbox, settings["arrival_sound_enabled"])
    QtBind.setChecked(gui, stop_character_checkbox, settings["stop_on_character_death"])
    QtBind.setChecked(gui, stop_transport_checkbox, settings["stop_on_transport_death"])
    QtBind.setChecked(gui, attacker_tracking_checkbox, settings["attacker_tracking_enabled"])
    QtBind.setText(
        gui, attacker_seconds_edit, str(settings["attacker_memory_seconds"])
    )


def settings_changed(checked=False):
    return


def show_settings():
    global settings_mode

    settings_mode = True
    for widget, x, y in destination_widgets:
        QtBind.move(gui, widget, OFFSCREEN_X, y)
    for widget, x, y in settings_widgets:
        QtBind.move(gui, widget, x, y)
    QtBind.move(gui, settings_button, OFFSCREEN_X, 62)
    QtBind.move(gui, destinations_button, 310, 62)
    apply_settings_to_gui()
    refresh_sounds()
    set_status("Settings", C_ACCENT)


def show_destinations():
    global settings_mode

    settings_mode = False
    for widget, x, y in settings_widgets:
        QtBind.move(gui, widget, OFFSCREEN_X, y)
    for widget, x, y in destination_widgets:
        QtBind.move(gui, widget, x, y)
    QtBind.move(gui, destinations_button, OFFSCREEN_X, 62)
    QtBind.move(gui, settings_button, 310, 62)
    set_status("Loaded {0} locations".format(len(locations)), C_MUTED)


def save_settings():
    try:
        memory_seconds = int(QtBind.text(gui, attacker_seconds_edit).strip())
        memory_seconds = max(1, min(300, memory_seconds))
    except Exception:
        set_status("Attacker memory must be 1-300", C_ERROR)
        return

    settings["arrival_sound_enabled"] = QtBind.isChecked(
        gui, sound_enabled_checkbox
    )
    settings["arrival_sound"] = selected_sound_name()
    settings["stop_on_character_death"] = QtBind.isChecked(
        gui, stop_character_checkbox
    )
    settings["stop_on_transport_death"] = QtBind.isChecked(
        gui, stop_transport_checkbox
    )
    settings["attacker_tracking_enabled"] = QtBind.isChecked(
        gui, attacker_tracking_checkbox
    )
    settings["attacker_memory_seconds"] = memory_seconds
    QtBind.setText(gui, attacker_seconds_edit, str(memory_seconds))

    if save_settings_file():
        plugin_log("Settings saved: {0}".format(get_settings_path()))
        set_status("Settings saved", C_SUCCESS)
    else:
        set_status("Could not save settings", C_ERROR)


def test_sound():
    play_selected_sound()



def reload_config():
    global locations

    clear_location_buttons()
    locations = load_locations()
    create_location_buttons()
    if settings_mode:
        show_settings()
    plugin_log("Loaded {0} locations".format(len(locations)))
    set_status("Loaded {0} locations".format(len(locations)))


def navigate_to_location(location_index):
    global last_pathfinding_time
    global navigation_active
    global current_location
    global navigation_start_time
    global last_player_attacker
    global last_player_attack_time
    global pending_transport_death_time
    global pending_transport_death_region

    if location_index < 0 or location_index >= len(locations):
        plugin_log("Invalid location selection: {0}".format(location_index))
        set_status("Invalid location selection")
        return

    location = locations[location_index]
    stop_script()
    navigation_active = False
    navigation_start_time = None
    current_location = location
    set_navigation_status("PREPARING", C_WARNING)
    set_route_status("ANALYZING", C_WARNING)
    QtBind.setText(gui, duration_label, "")

    current_time = time.time()
    elapsed = current_time - last_pathfinding_time
    if elapsed < PATHFINDING_COOLDOWN:
        remaining = int(math.ceil(PATHFINDING_COOLDOWN - elapsed))
        plugin_log(
            "Pathfinding cooldown active. Try again in {0} second(s)".format(remaining)
        )
        set_status("Please wait {0} second(s)".format(remaining))
        set_navigation_status("WAITING", C_WARNING)
        return

    last_pathfinding_time = current_time
    plugin_log("Generating route to: {0}".format(location["name"]))
    plugin_log(
        "Target: region={0}, x={1}, y={2}, z={3}".format(
            location["region"], location["x"], location["y"], location["z"]
        )
    )
    set_status("Generating route...", C_WARNING)

    try:
        commands = generate_script(
            location["region"], location["x"], location["y"], location["z"]
        )
    except Exception as error:
        plugin_log("Pathfinding error for {0}: {1}".format(location["name"], error))
        set_status("Pathfinding error")
        set_navigation_status("ERROR", C_ERROR)
        return

    if commands is None:
        plugin_log("No route found for: {0}".format(location["name"]))
        set_status("No route found")
        set_navigation_status("NO ROUTE", C_ERROR)
        return

    if commands is False:
        plugin_log("Pathfinding call failed for: {0}".format(location["name"]))
        set_status("Pathfinding call failed")
        set_navigation_status("FAILED", C_ERROR)
        return

    if not isinstance(commands, list):
        plugin_log(
            "Unexpected pathfinding result for {0}: expected a list".format(
                location["name"]
            )
        )
        set_status("Invalid pathfinding result")
        set_navigation_status("ERROR", C_ERROR)
        return

    try:
        script_text = "\n".join(commands)
    except (TypeError, ValueError) as error:
        plugin_log("Invalid route commands for {0}: {1}".format(location["name"], error))
        set_status("Invalid route commands")
        set_navigation_status("ERROR", C_ERROR)
        return

    if not script_text:
        plugin_log("Pathfinding returned an empty route for: {0}".format(location["name"]))
        set_status("Empty route returned")
        set_navigation_status("NO ROUTE", C_ERROR)
        return

    try:
        teleport_commands = [
            command for command in commands if command.startswith("teleport,")
        ]
        if any("FERRY" in command for command in teleport_commands):
            set_route_status("CARAVAN / FERRY", C_SUCCESS)
        elif teleport_commands:
            set_route_status("TELEPORT ROUTE", C_BLUE)
        else:
            set_route_status("WALK ONLY", C_SUCCESS)

        start_script(script_text)
        navigation_active = True
        navigation_start_time = time.time()
        last_player_attacker = None
        last_player_attack_time = 0.0
        pending_transport_death_time = 0.0
        pending_transport_death_region = 0
        set_attacker_status(None, C_MUTED)
        plugin_log("Navigation started: {0}".format(location["name"]))
        plugin_log("Route contains {0} commands".format(len(commands)))
        client_notice("Journey started towards {0}.".format(location["name"]))
        set_status("Route started", C_SUCCESS)
        set_navigation_status("WALKING", C_SUCCESS)
        set_duration_status("Elapsed time", 0)
    except Exception as error:
        navigation_active = False
        navigation_start_time = None
        plugin_log("Could not start navigation to {0}: {1}".format(location["name"], error))
        set_status("Could not start navigation")
        set_navigation_status("ERROR", C_ERROR)


def stop_navigation():
    global navigation_active
    global navigation_start_time
    global pending_transport_death_time
    global pending_transport_death_region

    try:
        stop_script()
        if navigation_start_time is not None:
            set_duration_status("Stopped after", time.time() - navigation_start_time)
        navigation_active = False
        navigation_start_time = None
        pending_transport_death_time = 0.0
        pending_transport_death_region = 0
        plugin_log("Navigation stopped")
        set_status("Navigation stopped")
        set_navigation_status("STOPPED", C_ERROR)
    except Exception as error:
        plugin_log("Could not stop navigation: {0}".format(error))
        set_status("Could not stop navigation")


def get_recent_attacker():
    if not settings.get("attacker_tracking_enabled", True):
        return None
    if not last_player_attacker or last_player_attack_time <= 0:
        return None
    memory_seconds = settings.get("attacker_memory_seconds", 15)
    if time.time() - last_player_attack_time > memory_seconds:
        return None
    return last_player_attacker


def stop_for_incident(incident_name):
    global navigation_active
    global navigation_start_time
    global pending_transport_death_time
    global pending_transport_death_region

    if not navigation_active:
        return

    elapsed_time = 0
    if navigation_start_time is not None:
        elapsed_time = time.time() - navigation_start_time

    try:
        stop_script()
    except Exception as error:
        plugin_log("Could not stop script after incident: {0}".format(error))

    navigation_active = False
    navigation_start_time = None
    pending_transport_death_time = 0.0
    pending_transport_death_region = 0

    attacker = get_recent_attacker()
    if attacker:
        set_attacker_status(attacker, C_ERROR)
        plugin_log("Last player attacker: {0}".format(attacker))
    else:
        set_attacker_status("Unknown / NPC", C_MUTED)
        plugin_log("No recent player attacker was detected")

    plugin_log("{0}; navigation stopped for safety".format(incident_name))
    set_status("Navigation stopped for safety", C_ERROR)
    set_navigation_status(incident_name.upper(), C_ERROR)
    set_duration_status("Travel time", elapsed_time)


def transport_is_alive():
    try:
        pets = get_pets()
        if not isinstance(pets, dict):
            return False
        for pet in pets.values():
            if not isinstance(pet, dict):
                continue
            if pet.get("type") == "transport":
                try:
                    return float(pet.get("hp", 1)) > 0
                except Exception:
                    return True
    except Exception as error:
        plugin_log("Could not inspect transport: {0}".format(error))
    return False


def confirm_pending_transport_death():
    global pending_transport_death_time
    global pending_transport_death_region

    if pending_transport_death_time <= 0:
        return
    if time.time() - pending_transport_death_time < TRANSPORT_DEATH_CONFIRM_SECONDS:
        return

    original_region = pending_transport_death_region
    pending_transport_death_time = 0.0
    pending_transport_death_region = 0

    current_region = 0
    try:
        position = get_position()
        if isinstance(position, dict):
            current_region = position.get("region", 0)
    except Exception:
        pass

    if transport_is_alive():
        plugin_log("Transport death event ignored: transport is still active")
        return
    if original_region and current_region and original_region != current_region:
        plugin_log("Transport death event ignored: region transition detected")
        return
    stop_for_incident("Transport died")


def handle_event(t, data):
    global last_player_attacker
    global last_player_attack_time
    global pending_transport_death_time
    global pending_transport_death_region

    if t == EVENT_PLAYER_ATTACKING:
        if navigation_active and settings.get("attacker_tracking_enabled", True):
            attacker = str(data).strip()
            if attacker:
                last_player_attacker = attacker
                last_player_attack_time = time.time()
                set_attacker_status(attacker, C_WARNING)
                plugin_log("Player attacker detected: {0}".format(attacker))
        return

    if not navigation_active:
        return

    if t == EVENT_DIED and settings.get("stop_on_character_death", True):
        stop_for_incident("Character died")
    elif t == EVENT_TRANSPORT_DIED and settings.get("stop_on_transport_death", True):
        pending_transport_death_time = time.time()
        try:
            position = get_position()
            if isinstance(position, dict):
                pending_transport_death_region = position.get("region", 0)
            else:
                pending_transport_death_region = 0
        except Exception:
            pending_transport_death_region = 0
        plugin_log("Transport death event received; waiting for confirmation")


def event_loop():
    global navigation_active
    global navigation_start_time

    confirm_pending_transport_death()

    if not navigation_active or current_location is None:
        return

    try:
        if navigation_start_time is not None:
            set_duration_status("Elapsed time", time.time() - navigation_start_time)

        position = get_position()
        if not isinstance(position, dict):
            return

        if position.get("region") != current_location["region"]:
            return

        delta_x = float(position.get("x", 0)) - float(current_location["x"])
        delta_y = float(position.get("y", 0)) - float(current_location["y"])
        distance = math.sqrt((delta_x * delta_x) + (delta_y * delta_y))
        if distance <= ARRIVAL_DISTANCE:
            elapsed_time = 0
            if navigation_start_time is not None:
                elapsed_time = time.time() - navigation_start_time
            navigation_active = False
            navigation_start_time = None
            plugin_log("Destination reached: {0}".format(current_location["name"]))
            plugin_log("Travel time: {0}".format(format_duration(elapsed_time)))
            client_notice("Arrived at destination: {0}.".format(current_location["name"]))
            set_status("Destination reached: {0}".format(current_location["name"]))
            set_navigation_status("ARRIVED", C_BLUE)
            set_duration_status("Travel time", elapsed_time)
            if settings.get("arrival_sound_enabled", True):
                play_selected_sound()
    except Exception as error:
        plugin_log("Could not update navigation status: {0}".format(error))


def finished():
    clear_location_buttons()


plugin_log("Plugin loaded")
load_settings()
create_settings_gui()
apply_settings_to_gui()
refresh_sounds()
reload_config()
set_navigation_status("IDLE", C_MUTED)
set_duration_status("Travel time", 0)
set_route_status("NOT GENERATED", C_MUTED)
set_attacker_status(None, C_MUTED)
