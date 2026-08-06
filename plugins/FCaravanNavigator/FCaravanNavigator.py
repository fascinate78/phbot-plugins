from phBot import *
import phBotChat
import QtBind
import math
import time


pName = "FCaravanNavigator"
pVersion = "1.0.0"
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
last_pathfinding_time = 0.0
navigation_active = False
current_location = None
navigation_start_time = None

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
status_label = QtBind.createLabel(
    gui,
    '<table width="300" cellspacing="0" cellpadding="0"><tr><td>'
    '<font color="#9aa0ac">Loading destinations...</font>'
    '</td></tr></table>',
    405,
    68
)
controls_separator_line = QtBind.createLineEdit(gui, "", 12, 106, 716, 1)
panel_separator_line = QtBind.createLineEdit(gui, "", 408, 120, 1, 190)
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
    '<table width="280" cellspacing="0" cellpadding="0"><tr><td>'
    '<font color="#2b3038">➤ Taklamakan Special</font>'
    '</td></tr></table>',
    428,
    171
)
QtBind.createLabel(
    gui, '<font color="#6b7280"><b>Status</b></font>', 428, 193
)
navigation_state_label = QtBind.createLabel(
    gui,
    '<table width="280" cellspacing="0" cellpadding="0"><tr><td>'
    '<font color="#c98a1a"><b>● PREPARING</b></font>'
    '</td></tr></table>',
    428,
    210
)
QtBind.createLabel(
    gui, '<font color="#6b7280"><b>Travel Time</b></font>', 428, 232
)
duration_label = QtBind.createLabel(
    gui, '<font color="#2b3038">⏱ 00:00:00</font>', 428, 249
)
QtBind.createLabel(
    gui, '<font color="#6b7280"><b>Route Type</b></font>', 428, 271
)
route_label = QtBind.createLabel(
    gui,
    '<table width="280" cellspacing="0" cellpadding="0"><tr><td>'
    '<font color="#1f9d63"><b>🐫 CARAVAN / FERRY</b></font>'
    '</td></tr></table>',
    428,
    288
)


def plugin_log(message):
    log("[FCaravanNavigator] {0}".format(message))


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
            300
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
            280
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
    QtBind.setText(gui, route_label, fixed_width_text(text, 280))


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


def make_location_callback(location_index):
    def location_callback():
        navigate_to_location(location_index)
    return location_callback


def create_location_buttons():
    global location_buttons
    global location_callback_names
    global location_group_widgets

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

        row_count = int(math.ceil(len(category_locations) / 2.0))
        current_y += (row_count * 30) + 10



def reload_config():
    global locations

    clear_location_buttons()
    locations = load_locations()
    create_location_buttons()
    plugin_log("Loaded {0} locations".format(len(locations)))
    set_status("Loaded {0} locations".format(len(locations)))


def navigate_to_location(location_index):
    global last_pathfinding_time
    global navigation_active
    global current_location
    global navigation_start_time

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

    try:
        stop_script()
        if navigation_start_time is not None:
            set_duration_status("Stopped after", time.time() - navigation_start_time)
        navigation_active = False
        navigation_start_time = None
        plugin_log("Navigation stopped")
        set_status("Navigation stopped")
        set_navigation_status("STOPPED", C_ERROR)
    except Exception as error:
        plugin_log("Could not stop navigation: {0}".format(error))
        set_status("Could not stop navigation")


def event_loop():
    global navigation_active
    global navigation_start_time

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
    except Exception as error:
        plugin_log("Could not update navigation status: {0}".format(error))


def finished():
    clear_location_buttons()


plugin_log("Plugin loaded")
reload_config()
set_navigation_status("IDLE", C_MUTED)
set_duration_status("Travel time", 0)
set_route_status("NOT GENERATED", C_MUTED)
