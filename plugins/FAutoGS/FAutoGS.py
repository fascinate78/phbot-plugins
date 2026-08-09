from phBot import *
import phBotChat
import QtBind
import json
import os
import time


pName = "FAutoGS"
pVersion = "1.0.0"
pUrl = ""

CHAT_PARTY = 4
PROTOCOL = "$FGS"
DEFAULT_TIMEOUT = 120
MIN_TIMEOUT = 15
MAX_TIMEOUT = 900
INVENTORY_SYNC_DELAY = 5.0

C_PRIMARY = "#5b57e0"
C_MUTED = "#9aa0ac"
C_TEXT = "#2b3038"
C_SUCCESS = "#1f9d63"
C_WARNING = "#c98a1a"
C_ERROR = "#d93a4d"

settings = {
    "script": "",
    "timeout": DEFAULT_TIMEOUT,
    "continue_on_error": True
}

# Coordinator state
mission_active = False
mission_id = ""
mission_queue = []
mission_index = -1
mission_current = ""
mission_deadline = 0.0
mission_results = []

# Worker state
worker_active = False
worker_job_id = ""
worker_coordinator = ""
worker_script = ""
worker_script_content = ""
worker_start_at = 0.0


gui = QtBind.init(__name__, pName)

QtBind.createLabel(
    gui,
    '<font color="{0}" size="4"><b>🏰 FAUTO GS</b></font>'.format(C_PRIMARY),
    12, 7
)
QtBind.createLabel(
    gui,
    '<font color="{0}">Guild Storage Mission Coordinator</font>'.format(C_MUTED),
    12, 31
)
QtBind.createLabel(
    gui,
    '<font color="{0}"><b>⚜ Made By FascinaTe</b></font>'.format(C_PRIMARY),
    548, 12
)
QtBind.createLineEdit(gui, "", 12, 52, 716, 1)

QtBind.createLabel(
    gui, '<font color="{0}"><b>📜 MISSION SETUP</b></font>'.format(C_PRIMARY),
    12, 65
)
QtBind.createLabel(gui, "Guild storage script:", 12, 91)
cmb_script = QtBind.createCombobox(gui, 140, 87, 290, 22)
btn_refresh = QtBind.createButton(gui, "refresh_scripts", "↻  Refresh Scripts", 440, 86)
QtBind.createLabel(gui, "Timeout:", 12, 121)
txt_timeout = QtBind.createLineEdit(gui, str(DEFAULT_TIMEOUT), 72, 117, 55, 22)
QtBind.createLabel(gui, "seconds per character", 135, 121)
chk_continue = QtBind.createCheckBox(
    gui, "continue_changed", "⚠ Continue with next character after fail / timeout", 315, 119
)
btn_start = QtBind.createButton(gui, "start_mission", "▶  Start Mission", 12, 153)
btn_stop = QtBind.createButton(gui, "stop_mission_clicked", "⏹  Stop Mission", 145, 153)
btn_save = QtBind.createButton(gui, "save_settings_clicked", "💾  Save Settings", 280, 153)

QtBind.createLineEdit(gui, "", 12, 189, 716, 1)
QtBind.createLabel(
    gui, '<font color="{0}"><b>● LIVE MISSION</b></font>'.format(C_PRIMARY),
    12, 202
)
QtBind.createLabel(gui, '<font color="{0}"><b>Status</b></font>'.format(C_MUTED), 12, 231)
lbl_status = QtBind.createLabel(gui, "", 105, 231)
QtBind.createLabel(gui, '<font color="{0}"><b>Current</b></font>'.format(C_MUTED), 12, 257)
lbl_current = QtBind.createLabel(gui, "", 105, 257)
QtBind.createLabel(gui, '<font color="{0}"><b>Progress</b></font>'.format(C_MUTED), 12, 283)
lbl_progress = QtBind.createLabel(gui, "", 105, 283)

QtBind.createLineEdit(gui, "", 352, 211, 1, 115)
QtBind.createLabel(
    gui, '<font color="{0}"><b>👥 MISSION RESULTS</b></font>'.format(C_PRIMARY),
    372, 202
)
lst_results = QtBind.createList(gui, 372, 228, 356, 98)
QtBind.createLabel(
    gui,
    '<font color="{0}">Scripts folder: Config/FAutoGS/script</font>'.format(C_MUTED),
    12, 335
)


def plugin_log(message):
    log("[{0}] {1}".format(pName, message))


def fixed_text(text, width=225):
    return '<table width="{0}" cellspacing="0" cellpadding="0"><tr><td>{1}</td></tr></table>'.format(
        width, text
    )


def set_status(text, color=C_MUTED):
    QtBind.setText(
        gui, lbl_status,
        fixed_text('<font color="{0}"><b>{1}</b></font>'.format(color, text))
    )


def set_current(text, color=C_TEXT):
    QtBind.setText(
        gui, lbl_current,
        fixed_text('<font color="{0}">{1}</font>'.format(color, text))
    )


def update_progress():
    total = len(mission_queue)
    done = len(mission_results)
    QtBind.setText(
        gui, lbl_progress,
        '<font color="{0}"><b>{1}/{2}</b></font>'.format(C_TEXT, done, total)
    )


def get_plugin_directory():
    base = None
    try:
        base = get_config_dir()
    except Exception:
        pass
    if not base:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, pName)


def get_scripts_directory():
    return os.path.join(get_plugin_directory(), "script")


def get_settings_path():
    return os.path.join(get_plugin_directory(), "settings.json")


def ensure_directories():
    try:
        folder = get_scripts_directory()
        if not os.path.isdir(folder):
            os.makedirs(folder)
        return True
    except Exception as error:
        plugin_log("Could not create config folders: {0}".format(error))
        return False


def safe_script_name(value):
    value = str(value or "").strip()
    if not value or value != os.path.basename(value):
        return ""
    if "|" in value or not value.lower().endswith(".txt"):
        return ""
    return value


def script_path(filename):
    filename = safe_script_name(filename)
    if not filename:
        return ""
    return os.path.join(get_scripts_directory(), filename)


def available_scripts():
    ensure_directories()
    try:
        names = []
        for name in os.listdir(get_scripts_directory()):
            path = os.path.join(get_scripts_directory(), name)
            if os.path.isfile(path) and safe_script_name(name):
                names.append(name)
        return sorted(names, key=lambda value: value.casefold())
    except Exception as error:
        plugin_log("Could not list scripts: {0}".format(error))
        return []


def refresh_scripts():
    selected = safe_script_name(QtBind.text(gui, cmb_script)) or settings["script"]
    names = available_scripts()
    QtBind.clear(gui, cmb_script)
    for name in names:
        QtBind.append(gui, cmb_script, name)
    if selected in names:
        QtBind.setText(gui, cmb_script, selected)
    elif names:
        QtBind.setText(gui, cmb_script, names[0])
    if names:
        set_status("Ready — {0} script(s) found".format(len(names)), C_SUCCESS)
    else:
        set_status("No .txt scripts found", C_WARNING)


def read_timeout():
    try:
        value = int(QtBind.text(gui, txt_timeout).strip())
    except Exception:
        value = DEFAULT_TIMEOUT
    value = max(MIN_TIMEOUT, min(MAX_TIMEOUT, value))
    QtBind.setText(gui, txt_timeout, str(value))
    return value


def save_settings():
    settings["script"] = safe_script_name(QtBind.text(gui, cmb_script))
    settings["timeout"] = read_timeout()
    settings["continue_on_error"] = bool(QtBind.isChecked(gui, chk_continue))
    if not ensure_directories():
        return False
    try:
        with open(get_settings_path(), "w", encoding="utf-8") as output:
            json.dump(settings, output, indent=2, sort_keys=True)
        return True
    except Exception as error:
        plugin_log("Could not save settings: {0}".format(error))
        return False


def load_settings():
    ensure_directories()
    path = get_settings_path()
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as source:
                loaded = json.load(source)
            settings["script"] = safe_script_name(loaded.get("script", ""))
            settings["timeout"] = max(
                MIN_TIMEOUT, min(MAX_TIMEOUT, int(loaded.get("timeout", DEFAULT_TIMEOUT)))
            )
            settings["continue_on_error"] = bool(loaded.get("continue_on_error", True))
        except Exception as error:
            plugin_log("Could not load settings; defaults used: {0}".format(error))
    QtBind.setText(gui, txt_timeout, str(settings["timeout"]))
    QtBind.setChecked(gui, chk_continue, settings["continue_on_error"])


def save_settings_clicked():
    if save_settings():
        set_status("Settings saved", C_SUCCESS)
    else:
        set_status("Settings could not be saved", C_ERROR)


def continue_changed(checked):
    settings["continue_on_error"] = bool(checked)


def my_name():
    try:
        data = get_character_data()
        if data:
            return str(data.get("name", ""))
    except Exception:
        pass
    return ""


def get_member_queue():
    own = my_name().casefold()
    try:
        party = get_party() or {}
    except Exception:
        party = {}
    members = []
    for party_id, data in party.items():
        name = str((data or {}).get("name", "")).strip()
        if name and name.casefold() != own:
            try:
                order = int(party_id)
            except Exception:
                order = 0
            members.append((order, name))
    members.sort(key=lambda entry: (entry[0], entry[1].casefold()))
    return [entry[1] for entry in members]


def send_party(parts):
    message = PROTOCOL + "|" + "|".join([str(part) for part in parts])
    try:
        return bool(phBotChat.Party(message))
    except Exception as error:
        plugin_log("Party message failed: {0}".format(error))
        return False


def add_result(name, result, color=None):
    icon = "✅" if result == "DONE" else ("⏱" if result == "TIMEOUT" else "❌")
    QtBind.append(gui, lst_results, "{0}  {1} — {2}".format(icon, name, result))


def start_mission():
    global mission_active, mission_id, mission_queue, mission_index
    global mission_current, mission_deadline, mission_results

    if mission_active:
        set_status("A mission is already running", C_WARNING)
        return
    if worker_active:
        set_status("This character is running a remote mission", C_WARNING)
        return
    coordinator = my_name()
    if not coordinator:
        set_status("Character data is not available", C_ERROR)
        return
    filename = safe_script_name(QtBind.text(gui, cmb_script))
    path = script_path(filename)
    if not filename or not path or not os.path.isfile(path):
        set_status("Select an existing .txt script", C_ERROR)
        return
    queue = get_member_queue()
    if not queue:
        set_status("No other party members found", C_WARNING)
        return

    save_settings()
    mission_id = str(int(time.time() * 1000))
    mission_queue = queue
    mission_index = -1
    mission_current = ""
    mission_deadline = 0.0
    mission_results = []
    mission_active = True
    QtBind.clear(gui, lst_results)
    set_status("Mission started", C_SUCCESS)
    update_progress()
    plugin_log("Mission {0} started with {1} member(s) using {2}".format(
        mission_id, len(queue), filename
    ))
    dispatch_next()


def dispatch_next():
    global mission_index, mission_current, mission_deadline

    if not mission_active:
        return
    mission_index += 1
    if mission_index >= len(mission_queue):
        finish_mission()
        return

    mission_current = mission_queue[mission_index]
    mission_deadline = time.time() + settings["timeout"]
    filename = safe_script_name(QtBind.text(gui, cmb_script)) or settings["script"]
    set_status("Waiting for character", C_WARNING)
    set_current("▶ {0}".format(mission_current), C_PRIMARY)
    update_progress()
    if not send_party(["RUN", mission_id, mission_current, my_name(), filename]):
        process_result(mission_current, "FAIL", "SEND_ERROR")


def process_result(name, result, reason=""):
    global mission_results
    if not mission_active or name.casefold() != mission_current.casefold():
        return
    if result == "TIMEOUT":
        # Party chat preserves message order, so the worker receives ABORT before
        # the coordinator dispatches the next RUN command.
        send_party(["ABORT", mission_id, name, my_name()])
    mission_results.append({"name": name, "result": result, "reason": reason})
    add_result(name, result)
    update_progress()
    if result != "DONE" and not settings["continue_on_error"]:
        finish_mission("Stopped after {0}: {1}".format(name, result), True)
        return
    dispatch_next()


def finish_mission(message="", cancelled=False):
    global mission_active, mission_current, mission_deadline
    done = len([item for item in mission_results if item["result"] == "DONE"])
    total = len(mission_queue)
    mission_active = False
    mission_current = ""
    mission_deadline = 0.0
    set_current("—")
    if cancelled:
        set_status(message or "Mission stopped", C_ERROR)
        return
    failures = total - done
    if failures:
        summary = "Mission completed: {0}/{1} done, {2} failed".format(done, total, failures)
        set_status(summary, C_WARNING)
    else:
        summary = "Mission completed: {0}/{1}".format(done, total)
        set_status(summary, C_SUCCESS)
    send_party(["COMPLETE", mission_id, "{0}/{1}".format(done, total)])
    plugin_log(summary)


def stop_mission_clicked():
    global mission_active, worker_active
    if mission_active:
        send_party(["CANCEL", mission_id, my_name()])
        finish_mission("Mission stopped by coordinator", True)
        return
    if worker_active:
        clear_worker()
        try:
            stop_script()
        except Exception:
            pass
        set_status("Remote mission stopped locally", C_WARNING)
        return
    set_status("No active mission", C_MUTED)


def clear_worker():
    global worker_active, worker_job_id, worker_coordinator, worker_script
    global worker_script_content, worker_start_at
    worker_active = False
    worker_job_id = ""
    worker_coordinator = ""
    worker_script = ""
    worker_script_content = ""
    worker_start_at = 0.0


def start_worker(job_id, target, coordinator, filename, sender):
    global worker_active, worker_job_id, worker_coordinator, worker_script
    global worker_script_content, worker_start_at

    if target.casefold() != my_name().casefold():
        return
    if not sender or sender.casefold() != coordinator.casefold():
        plugin_log("Rejected RUN with invalid coordinator identity")
        return
    if worker_active or mission_active:
        send_party(["FAIL", job_id, my_name(), "BUSY"])
        return
    filename = safe_script_name(filename)
    path = script_path(filename)
    if not filename or not path or not os.path.isfile(path):
        send_party(["FAIL", job_id, my_name(), "SCRIPT_NOT_FOUND"])
        set_status("Requested script was not found", C_ERROR)
        return
    try:
        with open(path, "r", encoding="utf-8-sig") as source:
            content = source.read()
        if not content.strip():
            raise ValueError("script is empty")
        worker_active = True
        worker_job_id = job_id
        worker_coordinator = coordinator
        worker_script = filename
        worker_script_content = content.rstrip() + "\nFAutoGS_complete\n"
        worker_start_at = time.time() + INVENTORY_SYNC_DELAY
        set_status("Syncing inventory — 5 seconds", C_WARNING)
        set_current("🔄 {0}".format(filename), C_PRIMARY)
        try:
            sync_result = sort_inventory()
            if sync_result is False:
                plugin_log("sort_inventory() was rejected; inventory will still be validated")
        except Exception as sync_error:
            plugin_log("sort_inventory() failed; inventory will still be validated: {0}".format(
                sync_error
            ))
        plugin_log("Remote mission {0}: inventory sync requested; waiting 5 seconds".format(
            job_id
        ))
    except Exception as error:
        plugin_log("Could not start script: {0}".format(error))
        send_party(["FAIL", job_id, my_name(), "START_ERROR"])
        clear_worker()
        set_status("Script could not be started", C_ERROR)
        set_current("—")


def launch_prepared_worker():
    global worker_start_at
    if not worker_active or not worker_start_at:
        return
    worker_start_at = 0.0
    try:
        inventory = get_inventory()
        if not inventory or not isinstance(inventory.get("items"), list):
            job_id = worker_job_id
            clear_worker()
            send_party(["FAIL", job_id, my_name(), "INVENTORY_NOT_READY"])
            set_status("Inventory is not ready", C_ERROR)
            set_current("—")
            plugin_log("Inventory validation failed after the 5-second sync delay")
            return

        content = worker_script_content
        filename = worker_script
        coordinator = worker_coordinator
        job_id = worker_job_id
        set_status("Remote mission running", C_WARNING)
        set_current("▶ {0}".format(filename), C_PRIMARY)
        result = start_script(content)
        if result is False:
            raise RuntimeError("phBot rejected start_script")
        plugin_log("Remote mission {0} started by {1}: {2}".format(
            job_id, coordinator, filename
        ))
    except Exception as error:
        job_id = worker_job_id
        plugin_log("Could not start prepared script: {0}".format(error))
        clear_worker()
        send_party(["FAIL", job_id, my_name(), "START_ERROR"])
        set_status("Script could not be started", C_ERROR)
        set_current("—")


def handle_chat(t, player, msg):
    if t != CHAT_PARTY or not msg or not str(msg).startswith(PROTOCOL + "|"):
        return False
    parts = str(msg).split("|")
    if len(parts) < 3 or parts[0] != PROTOCOL:
        return False
    command = parts[1].upper()

    if command == "RUN" and len(parts) == 6:
        start_worker(parts[2], parts[3], parts[4], parts[5], player)
        return True

    if command in ("DONE", "FAIL") and len(parts) >= 4:
        if not mission_active or parts[2] != mission_id:
            return True
        name = parts[3]
        if not player or player.casefold() != name.casefold():
            return True
        reason = parts[4] if len(parts) > 4 else ""
        process_result(name, command, reason)
        return True

    if command == "CANCEL" and len(parts) >= 4:
        if worker_active and parts[2] == worker_job_id:
            coordinator = parts[3]
            if player and player.casefold() == coordinator.casefold() and coordinator.casefold() == worker_coordinator.casefold():
                clear_worker()
                try:
                    stop_script()
                except Exception:
                    pass
                set_status("Mission cancelled by coordinator", C_WARNING)
                set_current("—")
        return True

    if command == "ABORT" and len(parts) >= 5:
        target = parts[3]
        coordinator = parts[4]
        if (worker_active and parts[2] == worker_job_id and
                target.casefold() == my_name().casefold() and player and
                player.casefold() == coordinator.casefold() and
                coordinator.casefold() == worker_coordinator.casefold()):
            clear_worker()
            try:
                stop_script()
            except Exception:
                pass
            set_status("Remote mission timed out", C_ERROR)
            set_current("—")
        return True
    return False


def complete_worker(source):
    if not worker_active:
        return False
    job_id = worker_job_id
    coordinator = worker_coordinator
    filename = worker_script
    clear_worker()
    set_status("Remote mission completed", C_SUCCESS)
    set_current("✅ {0}".format(filename), C_SUCCESS)
    send_party(["DONE", job_id, my_name()])
    plugin_log("Remote mission {0} completed for {1} via {2}".format(
        job_id, coordinator, source
    ))
    return True


def FAutoGS_complete(arguments):
    complete_worker("FAutoGS_complete")
    return 0


def script_finished():
    # Kept as a fallback for phBot builds that do emit this callback.
    complete_worker("script_finished")


def event_loop():
    if worker_active and worker_start_at and time.time() >= worker_start_at:
        launch_prepared_worker()
    if mission_active and mission_deadline and time.time() >= mission_deadline:
        name = mission_current
        plugin_log("Mission timeout while waiting for {0}".format(name))
        process_result(name, "TIMEOUT", "NO_RESPONSE")


load_settings()
refresh_scripts()
set_current("—")
update_progress()

log('[{0}] Loaded v{1} - ⚜ Made By FascinaTe'.format(pName, pVersion))
