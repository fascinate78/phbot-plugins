from phBot import *
import QtBind
import builtins
import json
import os
import re
import sys
import traceback
import webbrowser


pName = 'FCharacterPluginManager'
pVersion = '1.0.0'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

COLOR_PRIMARY = '#5b57e0'
COLOR_TEXT = '#2b3038'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#d93a4d'

HOOKS = (
    'connected', 'disconnected', 'joined_game', 'teleported', 'event_loop',
    'handle_chat', 'handle_event', 'handle_joymax', 'handle_silkroad',
    'handle_script', 'bot_started', 'bot_stopped', 'script_finished',
    'finished'
)

PLUGIN_FILE = os.path.abspath(__file__)
PLUGIN_ROOT = os.path.dirname(PLUGIN_FILE)
MANAGED_ROOT = os.path.join(PLUGIN_ROOT, pName)

_available = {}
_enabled_names = []
_contexts = {}
_namespaces = {}
_callback_aliases = {}
_active_character = ''
_profile_loaded = False
_loading = False


def fixed_width_text(content, width):
    return (
        '<table width="{0}" cellspacing="0" cellpadding="0">'
        '<tr><td>{1}</td></tr></table>'
    ).format(width, content)


gui = QtBind.init(__name__, pName)
QtBind.createLabel(
    gui,
    u'<font color="%s" size="4"><b>⚙ %s</b></font>' % (COLOR_PRIMARY, pName),
    12, 6
)
QtBind.createLabel(
    gui, '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion), 255, 12
)
btn_discord = QtBind.createButton(
    gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6
)
QtBind.createLabel(
    gui, u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' % COLOR_PRIMARY,
    565, 11
)
QtBind.createLineEdit(gui, '', 12, 30, 716, 1)

QtBind.createLabel(gui, '<font color="%s"><b>AVAILABLE PLUGINS</b></font>' % COLOR_PRIMARY, 12, 44)
QtBind.createLabel(gui, '<font color="%s"><b>ENABLED FOR CHARACTER</b></font>' % COLOR_PRIMARY, 374, 44)
lst_available = QtBind.createList(gui, 12, 66, 340, 176)
lst_enabled = QtBind.createList(gui, 374, 66, 340, 176)

btn_refresh = QtBind.createButton(gui, 'refresh_clicked', 'Refresh', 12, 252)
btn_add = QtBind.createButton(gui, 'add_clicked', 'Add  >', 126, 252)
btn_remove = QtBind.createButton(gui, 'remove_clicked', '<  Remove', 374, 252)
btn_save_apply = QtBind.createButton(gui, 'save_apply_clicked', 'Save && Apply', 554, 252)

QtBind.createLineEdit(gui, '', 12, 286, 716, 1)
QtBind.createLabel(gui, '<font color="%s"><b>ACTIVE CHARACTER</b></font>' % COLOR_PRIMARY, 12, 300)
lbl_character = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s">Waiting for character...</font>' % COLOR_WARNING, 330), 150, 300
)
QtBind.createLabel(gui, '<font color="%s"><b>STATUS</b></font>' % COLOR_PRIMARY, 12, 326)
lbl_status = QtBind.createLabel(
    gui, fixed_width_text('<font color="%s">Ready</font>' % COLOR_MUTED, 560), 150, 326
)
QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s">Move plugin .py files/folders into Plugins\\%s\\, then press Refresh.</font>' %
        (COLOR_MUTED, pName), 700
    ),
    12, 354
)


def plugin_log(message):
    log('[%s] %s' % (pName, message))


def set_status(message, color=COLOR_MUTED):
    QtBind.setText(
        gui, lbl_status,
        fixed_width_text('<font color="%s">%s</font>' % (color, str(message)), 560)
    )


def _safe_name(value):
    return re.sub(r'[^A-Za-z0-9_]+', '_', str(value))


def _settings_directory():
    base = get_config_dir()
    return os.path.join(base, pName)


def _profiles_path():
    return os.path.join(_settings_directory(), 'profiles.json')


def _load_profiles():
    try:
        with open(_profiles_path(), 'r', encoding='utf-8') as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (IOError, OSError, ValueError):
        return {}


def _save_profile(character_key, plugin_names):
    directory = _settings_directory()
    if not os.path.isdir(directory):
        os.makedirs(directory)
    profiles = _load_profiles()
    profiles[character_key] = list(plugin_names)
    with open(_profiles_path(), 'w', encoding='utf-8') as handle:
        json.dump(profiles, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write('\n')


def _character_key():
    try:
        character = get_character_data() or {}
        server = str(character.get('server') or '').strip()
        name = str(character.get('name') or '').strip()
        if server and name:
            return '%s_%s' % (server, name)
    except Exception:
        pass
    return ''


def _entry_name(path):
    relative = os.path.relpath(path, MANAGED_ROOT).replace('\\', '/')
    if relative.lower().endswith('.py'):
        relative = relative[:-3]
    if relative.endswith('/__init__'):
        relative = relative[:-9]
    return relative.strip('/')


def _scan_plugins():
    result = {}
    if not os.path.isdir(MANAGED_ROOT):
        os.makedirs(MANAGED_ROOT)
    for root, directories, files in os.walk(MANAGED_ROOT):
        directories[:] = [item for item in directories if item != '__pycache__' and not item.startswith('.')]
        candidates = []
        if '__init__.py' in files:
            candidates.append(os.path.join(root, '__init__.py'))
        else:
            folder_name = os.path.basename(root)
            preferred = folder_name + '.py'
            if preferred in files:
                candidates.append(os.path.join(root, preferred))
            else:
                candidates.extend(
                    os.path.join(root, item) for item in files
                    if item.lower().endswith('.py') and not item.startswith('_')
                )
        for path in candidates:
            name = _entry_name(path)
            if name and name not in result:
                result[name] = path
        if candidates and root != MANAGED_ROOT:
            directories[:] = []
    return result


def _refresh_lists():
    global _available
    _available = _scan_plugins()
    QtBind.clear(gui, lst_available)
    QtBind.clear(gui, lst_enabled)
    for name in sorted(_available, key=str.lower):
        if name not in _enabled_names:
            QtBind.append(gui, lst_available, name)
    for name in _enabled_names:
        QtBind.append(gui, lst_enabled, name)


def _make_gui_callback(plugin_id, callback_name):
    def callback(*args):
        namespace = _namespaces.get(plugin_id, {})
        target = namespace.get(callback_name)
        if callable(target):
            try:
                return target(*args)
            except Exception as error:
                plugin_log('%s GUI callback %s failed: %s' % (plugin_id, callback_name, error))
        return None
    return callback


class _QtBindProxy(object):
    def __init__(self, plugin_id):
        self.plugin_id = plugin_id

    def __getattr__(self, name):
        return getattr(QtBind, name)

    def _alias(self, callback_name):
        callback_name = str(callback_name)
        alias = '_fcpm_%s_%s' % (_safe_name(self.plugin_id), _safe_name(callback_name))
        if alias not in _callback_aliases:
            globals()[alias] = _make_gui_callback(self.plugin_id, callback_name)
            _callback_aliases[alias] = self.plugin_id
        return alias

    def createButton(self, target_gui, callback_name, text, x, y):
        return QtBind.createButton(target_gui, self._alias(callback_name), text, x, y)

    def createCheckBox(self, target_gui, callback_name, text, x, y):
        return QtBind.createCheckBox(target_gui, self._alias(callback_name), text, x, y)


def _plugin_builtins(plugin_id):
    values = dict(vars(builtins))
    original_import = builtins.__import__
    qt_proxy = _QtBindProxy(plugin_id)

    def managed_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'QtBind':
            return qt_proxy
        return original_import(name, globals, locals, fromlist, level)

    values['__import__'] = managed_import
    return values


def _load_plugin(plugin_id, path):
    if plugin_id in _contexts:
        return True
    try:
        with open(path, 'r', encoding='utf-8-sig') as handle:
            source = handle.read()
        namespace = {
            '__name__': __name__,
            '__file__': path,
            '__package__': None,
            '__builtins__': _plugin_builtins(plugin_id)
        }
        _namespaces[plugin_id] = namespace
        plugin_directory = os.path.dirname(path)
        inserted_path = plugin_directory not in sys.path
        if inserted_path:
            sys.path.insert(0, plugin_directory)
        try:
            exec(compile(source, path, 'exec'), namespace)
        finally:
            if inserted_path:
                try:
                    sys.path.remove(plugin_directory)
                except ValueError:
                    pass
        context = {}
        for hook in HOOKS:
            target = namespace.get(hook)
            if callable(target):
                context[hook] = target
        _contexts[plugin_id] = context
        plugin_log('Loaded managed plugin: %s' % plugin_id)
        return True
    except Exception as error:
        _namespaces.pop(plugin_id, None)
        plugin_log('Could not load %s: %s' % (plugin_id, error))
        plugin_log(traceback.format_exc())
        return False


def _stop_plugin(plugin_id):
    context = _contexts.pop(plugin_id, {})
    callback = context.get('finished')
    if callable(callback):
        try:
            callback()
        except Exception as error:
            plugin_log('%s cleanup failed: %s' % (plugin_id, error))
    _namespaces.pop(plugin_id, None)
    for alias, owner in list(_callback_aliases.items()):
        if owner == plugin_id:
            _callback_aliases.pop(alias, None)
            globals().pop(alias, None)


def _apply_enabled_plugins():
    global _loading
    if _loading:
        return
    _loading = True
    try:
        for plugin_id in list(_contexts):
            if plugin_id not in _enabled_names:
                _stop_plugin(plugin_id)
        loaded = 0
        failed = []
        for plugin_id in _enabled_names:
            path = _available.get(plugin_id)
            if not path:
                failed.append(plugin_id)
            elif _load_plugin(plugin_id, path):
                loaded += 1
            else:
                failed.append(plugin_id)
        if failed:
            set_status('Loaded %d plugin(s); failed/missing: %s' % (loaded, ', '.join(failed)), COLOR_ERROR)
        else:
            set_status('Loaded %d plugin(s) for %s' % (loaded, _active_character), COLOR_SUCCESS)
    finally:
        _loading = False


def _activate_character_profile():
    global _active_character, _profile_loaded, _enabled_names
    character_key = _character_key()
    if not character_key or (_profile_loaded and character_key == _active_character):
        return False
    for plugin_id in list(_contexts):
        _stop_plugin(plugin_id)
    _active_character = character_key
    _profile_loaded = True
    profiles = _load_profiles()
    saved = profiles.get(character_key, [])
    _enabled_names = [str(item) for item in saved if isinstance(item, str)]
    QtBind.setText(
        gui, lbl_character,
        fixed_width_text('<font color="%s"><b>%s</b></font>' % (COLOR_TEXT, character_key), 330)
    )
    _refresh_lists()
    _apply_enabled_plugins()
    return True


def _dispatch(name, *args):
    results = []
    for plugin_id, context in list(_contexts.items()):
        callback = context.get(name)
        if callable(callback):
            try:
                results.append(callback(*args))
            except Exception as error:
                plugin_log('%s hook %s failed: %s' % (plugin_id, name, error))
    return results


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        set_status('Opening Discord invite...', COLOR_SUCCESS)
    except Exception as error:
        plugin_log('Discord link error: %s' % error)
        set_status('Could not open Discord invite', COLOR_ERROR)


def refresh_clicked():
    _refresh_lists()
    set_status('Found %d managed plugin(s)' % len(_available), COLOR_SUCCESS)


def add_clicked():
    selected = str(QtBind.text(gui, lst_available) or '')
    if selected and selected in _available and selected not in _enabled_names:
        _enabled_names.append(selected)
        _refresh_lists()


def remove_clicked():
    selected = str(QtBind.text(gui, lst_enabled) or '')
    if selected in _enabled_names:
        _enabled_names.remove(selected)
        _refresh_lists()


def save_apply_clicked():
    if not _active_character:
        set_status('Enter the game with a character first', COLOR_WARNING)
        return
    try:
        _save_profile(_active_character, _enabled_names)
        _apply_enabled_plugins()
    except Exception as error:
        plugin_log('Could not save profile: %s' % error)
        set_status('Could not save character profile', COLOR_ERROR)


def connected():
    _dispatch('connected')


def disconnected():
    _dispatch('disconnected')


def joined_game():
    _dispatch('joined_game')


def teleported():
    newly_loaded = _activate_character_profile()
    if newly_loaded:
        _dispatch('joined_game')
    _dispatch('teleported')


def event_loop():
    _activate_character_profile()
    _dispatch('event_loop')


def handle_chat(t, player, msg):
    _dispatch('handle_chat', t, player, msg)


def handle_event(t, data):
    _dispatch('handle_event', t, data)


def handle_joymax(opcode, data):
    return False not in _dispatch('handle_joymax', opcode, data)


def handle_silkroad(opcode, data):
    return False not in _dispatch('handle_silkroad', opcode, data)


def handle_script(command, args):
    return True in _dispatch('handle_script', command, args)


def bot_started():
    _dispatch('bot_started')


def bot_stopped():
    _dispatch('bot_stopped')


def script_finished():
    _dispatch('script_finished')


def finished():
    for plugin_id in list(_contexts):
        _stop_plugin(plugin_id)


_refresh_lists()
log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
