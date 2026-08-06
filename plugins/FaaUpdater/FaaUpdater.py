# -*- coding: utf-8 -*-

from phBot import *
import QtBind

import hashlib
import json
import os
import re
import textwrap
import threading
import urllib.parse
import urllib.request


pName = 'FaaUpdater'
pVersion = '1.0.5'

MANIFEST_URL = (
    'https://raw.githubusercontent.com/'
    'fascinate78/phbot-plugins/main/manifest.json'
)
ALLOWED_RAW_PREFIX = (
    'https://raw.githubusercontent.com/'
    'fascinate78/phbot-plugins/'
)
NETWORK_TIMEOUT = 15
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_PLUGIN_BYTES = 5 * 1024 * 1024

COLOR_PRIMARY = '#5b57e0'
COLOR_DARK = '#30323a'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#238636'
COLOR_WARNING = '#d97706'
COLOR_ERROR = '#dc2626'

_catalog = []
_display_to_plugin = {}
_busy = [False]
_auto_refresh_started = [False]
_last_selected_display = ['']


def _html_escape(value):
    return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _fixed_label_html(text, color, minimum_chars=38, bold=False):
    value = str(text or '')
    padding = '&nbsp;' * max(0, minimum_chars - len(value))
    content = _html_escape(value) + padding
    if bold:
        content = '<b>%s</b>' % content
    return '<font color="%s">%s</font>' % (color, content)


gui = QtBind.init(__name__, pName)

QtBind.createLabel(
    gui,
    u'<font color="%s" size="4"><b>↻ F Plugin Manager</b></font>' %
    COLOR_PRIMARY,
    12,
    6
)
QtBind.createLabel(
    gui,
    '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion),
    300,
    12
)
QtBind.createLabel(
    gui,
    u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' % COLOR_PRIMARY,
    565,
    11
)
QtBind.createLineEdit(gui, '', 12, 30, 716, 1)

QtBind.createLabel(
    gui,
    '<font color="%s"><b>AVAILABLE PLUGINS</b></font>' % COLOR_PRIMARY,
    12,
    43
)
QtBind.createLabel(
    gui,
    '<font color="%s">Select a plugin to install or update.</font>' % COLOR_MUTED,
    12,
    62
)

lst_plugins = QtBind.createList(gui, 12, 84, 430, 170)
QtBind.createLineEdit(gui, '', 455, 43, 1, 211)

QtBind.createLabel(
    gui,
    '<font color="%s"><b>LIVE STATUS</b></font>' % COLOR_PRIMARY,
    472,
    43
)
lbl_status = QtBind.createLabel(
    gui,
    '<font color="%s"><b>Waiting for catalog operation</b></font>' % COLOR_SUCCESS,
    472,
    66
)
QtBind.setText(
    gui,
    lbl_status,
    '<font color="%s"><b>Ready</b></font>' % COLOR_SUCCESS
)
lbl_summary = QtBind.createLabel(
    gui,
    '<font color="%s">Catalog has not been checked yet.</font>' % COLOR_MUTED,
    472,
    91
)
QtBind.createLabel(
    gui,
    '<font color="%s">Source:</font>' % COLOR_DARK,
    472,
    127
)
QtBind.createLabel(
    gui,
    '<font color="%s">fascinate78/phbot-plugins</font>' % COLOR_MUTED,
    472,
    147
)
QtBind.createLabel(
    gui,
    '<font color="%s"><b>SELECTED PLUGIN</b></font>' % COLOR_PRIMARY,
    472,
    157
)
lbl_selected_name = QtBind.createLabel(
    gui,
    _fixed_label_html('No plugin selected', COLOR_DARK, bold=True),
    472,
    179
)
lbl_selected_version = QtBind.createLabel(
    gui,
    _fixed_label_html('Choose a catalog item.', COLOR_MUTED),
    472,
    201
)
lbl_selected_description_1 = QtBind.createLabel(
    gui,
    _fixed_label_html('Plugin details will appear here.', COLOR_MUTED),
    472,
    223
)
lbl_selected_description_2 = QtBind.createLabel(
    gui,
    _fixed_label_html('Select an item from the catalog.', COLOR_MUTED),
    472,
    241
)
lbl_selected_description_3 = QtBind.createLabel(
    gui,
    _fixed_label_html('', COLOR_MUTED),
    472,
    259
)

btn_refresh = QtBind.createButton(gui, 'refresh_catalog_clicked', u'↻  Refresh Catalog', 12, 270)
btn_selected = QtBind.createButton(gui, 'install_selected_clicked', 'Install / Update Selected', 160, 270)
btn_all = QtBind.createButton(gui, 'update_all_clicked', 'Update All', 380, 270)

QtBind.createLineEdit(gui, '', 12, 310, 716, 1)
QtBind.createLabel(
    gui,
    '<font color="%s">Updates replace the existing plugin only after a complete, verified download.</font>' %
    COLOR_MUTED,
    12,
    322
)


def _set_status(message, color=COLOR_MUTED):
    try:
        QtBind.setText(
            gui,
            lbl_status,
            '<font color="%s"><b>%s</b></font>' % (color, _html_escape(message))
        )
    except Exception:
        pass


def _set_summary(message):
    try:
        QtBind.setText(
            gui,
            lbl_summary,
            '<font color="%s">%s</font>' % (COLOR_MUTED, _html_escape(message))
        )
    except Exception:
        pass


def _plugin_root():
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    if os.path.basename(current_dir).lower() == pName.lower():
        return os.path.dirname(current_dir)
    return current_dir


def _safe_target(plugin):
    if plugin.get('id') == pName:
        return os.path.abspath(__file__)

    install_path = str(plugin.get('install_path', '')).strip()
    if not install_path or os.path.isabs(install_path):
        raise ValueError('Invalid install path')

    normalized_relative = os.path.normpath(install_path.replace('/', os.sep))
    if normalized_relative == '..' or normalized_relative.startswith('..' + os.sep):
        raise ValueError('Install path leaves the Plugins directory')

    root = os.path.abspath(_plugin_root())
    target = os.path.abspath(os.path.join(root, normalized_relative))
    root_case = os.path.normcase(root)
    target_case = os.path.normcase(target)
    if target_case != root_case and not target_case.startswith(root_case + os.sep):
        raise ValueError('Install path leaves the Plugins directory')
    return target


def _validate_download_url(url):
    value = str(url).strip()
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != 'https' or parsed.netloc.lower() != 'raw.githubusercontent.com':
        raise ValueError('Only HTTPS GitHub downloads are allowed')
    if not value.startswith(ALLOWED_RAW_PREFIX):
        raise ValueError('Download is outside the trusted repository')
    return value


def _download(url, maximum_bytes):
    request = urllib.request.Request(
        url,
        headers={'User-Agent': '%s/%s' % (pName, pVersion)}
    )
    response = urllib.request.urlopen(request, timeout=NETWORK_TIMEOUT)
    try:
        final_url = response.geturl()
        if url != MANIFEST_URL:
            _validate_download_url(final_url)
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > maximum_bytes:
            raise ValueError('Download is larger than allowed')
        data = response.read(maximum_bytes + 1)
        if len(data) > maximum_bytes:
            raise ValueError('Download is larger than allowed')
        return data
    finally:
        response.close()


def _parse_version(value):
    text = str(value or '0').strip()
    parts = re.split(r'[._+-]', text)
    result = []
    for part in parts:
        match = re.match(r'^(\d+)', part)
        result.append(int(match.group(1)) if match else 0)
    while len(result) < 3:
        result.append(0)
    return tuple(result)


def _read_installed_version(target):
    if not os.path.isfile(target):
        return None
    try:
        with open(target, 'rb') as plugin_file:
            source = plugin_file.read(512 * 1024).decode('utf-8-sig', 'replace')
        match = re.search(
            r'^\s*pVersion\s*=\s*[\'\"]([^\'\"]+)[\'\"]',
            source,
            re.MULTILINE
        )
        return match.group(1).strip() if match else 'unknown'
    except Exception:
        return 'unknown'


def _plugin_state(plugin):
    target = _safe_target(plugin)
    installed = _read_installed_version(target)
    latest = str(plugin.get('version', '0')).strip()
    if installed is None:
        return 'install', installed, latest
    if installed == 'unknown':
        return 'update', installed, latest
    if _parse_version(installed) < _parse_version(latest):
        return 'update', installed, latest
    if _parse_version(installed) > _parse_version(latest):
        return 'newer', installed, latest
    return 'current', installed, latest


def _validate_manifest(payload):
    if not isinstance(payload, dict) or payload.get('schema_version') != 1:
        raise ValueError('Unsupported manifest format')
    plugins = payload.get('plugins')
    if not isinstance(plugins, list):
        raise ValueError('Manifest plugin list is invalid')

    seen_ids = set()
    validated = []
    for plugin in plugins:
        if not isinstance(plugin, dict):
            raise ValueError('Invalid plugin entry')
        plugin_id = str(plugin.get('id', '')).strip()
        if not re.match(r'^[A-Za-z0-9_-]+$', plugin_id):
            raise ValueError('Invalid plugin id')
        if plugin_id in seen_ids:
            raise ValueError('Duplicate plugin id: ' + plugin_id)
        seen_ids.add(plugin_id)

        version = str(plugin.get('version', '')).strip()
        sha256 = str(plugin.get('sha256', '')).strip().lower()
        if not version or not re.match(r'^[0-9A-Za-z._+-]+$', version):
            raise ValueError('Invalid version for ' + plugin_id)
        if not re.match(r'^[0-9a-f]{64}$', sha256):
            raise ValueError('Invalid SHA-256 for ' + plugin_id)
        _validate_download_url(plugin.get('download_url', ''))
        _safe_target(plugin)
        validated.append(plugin)
    return validated


def _display_text(plugin):
    state, installed, latest = _plugin_state(plugin)
    name = str(plugin.get('name') or plugin.get('id'))
    if state == 'install':
        return '[INSTALL] %s | v%s' % (name, latest)
    if state == 'update':
        return '[UPDATE] %s | %s -> %s' % (name, installed, latest)
    if state == 'newer':
        return '[LOCAL NEWER] %s | %s' % (name, installed)
    return '[CURRENT] %s | v%s' % (name, installed)


def _set_selected_plugin(plugin):
    if not plugin:
        QtBind.setText(
            gui,
            lbl_selected_name,
            _fixed_label_html('No plugin selected', COLOR_DARK, bold=True)
        )
        QtBind.setText(
            gui,
            lbl_selected_version,
            _fixed_label_html('Choose a catalog item.', COLOR_MUTED)
        )
        QtBind.setText(
            gui,
            lbl_selected_description_1,
            _fixed_label_html('Plugin details will appear here.', COLOR_MUTED)
        )
        QtBind.setText(
            gui,
            lbl_selected_description_2,
            _fixed_label_html('Select an item from the catalog.', COLOR_MUTED)
        )
        QtBind.setText(gui, lbl_selected_description_3, _fixed_label_html('', COLOR_MUTED))
        return

    state, installed, latest = _plugin_state(plugin)
    name = str(plugin.get('name') or plugin.get('id'))
    if state == 'install':
        version_text = 'Not installed | Latest: %s' % latest
    elif state == 'update':
        version_text = 'Installed: %s | Latest: %s' % (installed, latest)
    elif state == 'newer':
        version_text = 'Local: %s | Catalog: %s' % (installed, latest)
    else:
        version_text = 'Installed: %s | Up to date' % installed

    description = str(plugin.get('description') or 'No description is available.').strip()
    wrapped = textwrap.wrap(description, width=38)[:3]
    while len(wrapped) < 3:
        wrapped.append('')

    QtBind.setText(
        gui,
        lbl_selected_name,
        _fixed_label_html(name, COLOR_DARK, bold=True)
    )
    QtBind.setText(
        gui,
        lbl_selected_version,
        _fixed_label_html(version_text, COLOR_MUTED)
    )
    QtBind.setText(
        gui,
        lbl_selected_description_1,
        _fixed_label_html(wrapped[0], COLOR_MUTED)
    )
    QtBind.setText(
        gui,
        lbl_selected_description_2,
        _fixed_label_html(wrapped[1], COLOR_MUTED)
    )
    QtBind.setText(
        gui,
        lbl_selected_description_3,
        _fixed_label_html(wrapped[2], COLOR_MUTED)
    )


def _refresh_selected_plugin():
    selected = QtBind.text(gui, lst_plugins)
    if selected == _last_selected_display[0]:
        return
    _last_selected_display[0] = selected
    _set_selected_plugin(_display_to_plugin.get(selected))


def _render_catalog():
    global _display_to_plugin
    mapping = {}
    install_count = 0
    update_count = 0
    current_count = 0
    QtBind.clear(gui, lst_plugins)

    for plugin in _catalog:
        display = _display_text(plugin)
        mapping[display] = plugin
        QtBind.append(gui, lst_plugins, display)
        state = _plugin_state(plugin)[0]
        if state == 'install':
            install_count += 1
        elif state == 'update':
            update_count += 1
        else:
            current_count += 1

    _display_to_plugin = mapping
    _last_selected_display[0] = ''
    _set_selected_plugin(None)
    _set_summary(
        '%d available | %d updates | %d not installed' %
        (len(_catalog), update_count, install_count)
    )
    if not _catalog:
        _set_summary('No plugins are published yet.')


def _refresh_worker():
    global _catalog
    try:
        _set_status('Checking GitHub catalog...', COLOR_WARNING)
        raw = _download(MANIFEST_URL, MAX_MANIFEST_BYTES)
        payload = json.loads(raw.decode('utf-8-sig'))
        _catalog = _validate_manifest(payload)
        _render_catalog()
        _set_status('Catalog is ready', COLOR_SUCCESS)
    except Exception as error:
        log('[%s] Catalog error: %s' % (pName, error))
        _set_status('Catalog check failed', COLOR_ERROR)
        _set_summary(str(error))
    finally:
        _busy[0] = False


def _start_refresh():
    if _busy[0]:
        _set_status('Another operation is running', COLOR_WARNING)
        return
    _busy[0] = True
    threading.Thread(target=_refresh_worker, daemon=True).start()


def refresh_catalog_clicked():
    _start_refresh()


def _install_plugin(plugin):
    plugin_id = str(plugin.get('id'))
    url = _validate_download_url(plugin.get('download_url', ''))
    expected_hash = str(plugin.get('sha256', '')).lower()
    target = _safe_target(plugin)

    _set_status('Downloading %s...' % plugin_id, COLOR_WARNING)
    data = _download(url, MAX_PLUGIN_BYTES)
    actual_hash = hashlib.sha256(data).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError('%s failed SHA-256 verification' % plugin_id)

    target_dir = os.path.dirname(target)
    if not os.path.isdir(target_dir):
        os.makedirs(target_dir)

    temporary = target + '.tmp'
    try:
        with open(temporary, 'wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.isfile(temporary):
            try:
                os.remove(temporary)
            except Exception:
                pass
    return plugin_id


def _install_worker(plugins):
    installed = []
    try:
        for plugin in plugins:
            installed.append(_install_plugin(plugin))
        _render_catalog()
        if installed:
            _set_status('Update completed', COLOR_SUCCESS)
            _set_summary('Reload plugins or restart phBot to apply changes.')
            log('[%s] Installed/updated: %s' % (pName, ', '.join(installed)))
        else:
            _set_status('Everything is up to date', COLOR_SUCCESS)
    except Exception as error:
        log('[%s] Install error: %s' % (pName, error))
        _set_status('Install failed', COLOR_ERROR)
        _set_summary(str(error))
    finally:
        _busy[0] = False


def _start_install(plugins):
    if _busy[0]:
        _set_status('Another operation is running', COLOR_WARNING)
        return
    if not plugins:
        _set_status('Nothing selected for update', COLOR_WARNING)
        return
    _busy[0] = True
    threading.Thread(target=_install_worker, args=(plugins,), daemon=True).start()


def install_selected_clicked():
    selected = QtBind.text(gui, lst_plugins)
    plugin = _display_to_plugin.get(selected)
    if not plugin:
        _set_status('Select a plugin first', COLOR_WARNING)
        return
    state = _plugin_state(plugin)[0]
    if state in ('current', 'newer'):
        _set_status('Selected plugin is already current', COLOR_SUCCESS)
        return
    _start_install([plugin])


def update_all_clicked():
    pending = []
    for plugin in _catalog:
        if _plugin_state(plugin)[0] == 'update':
            pending.append(plugin)
    _start_install(pending)


def event_loop():
    if not _auto_refresh_started[0]:
        _auto_refresh_started[0] = True
        _start_refresh()
    _refresh_selected_plugin()


log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
