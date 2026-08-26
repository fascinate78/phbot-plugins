# ============================================================
#  FTarget - phBot plugin
#  Sends a key combo (key + Ctrl/Alt/Shift) then a follow-up
#  single key. Method: keybd_event (requires window focus).
#
#  Triggers: Global hotkey / Chat command / Loop
#  Master "Enable" switch + per-character settings save.
#
#  NOTE: GUI text is ASCII-only on purpose. The phBot QtBind
#  bridge garbles non-ASCII (emoji/unicode) into mojibake.
# ============================================================
from phBot import *
import QtBind
import phBotChat
import ctypes
import ctypes.wintypes as wt
import time, threading, json, os
import webbrowser

pName    = 'FTarget'
pVersion = '3.5.1'

CHAT_CMD = 'tg'   # fixed chat command word
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

COLOR_PRIMARY = '#5b57e0'
COLOR_LABEL = '#6b7280'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_ERROR = '#d93a4d'

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# -- Win32 constants ----------------------------------------
KEYEVENTF_KEYUP = 0x0002
MAPVK_VK_TO_VSC = 0

VK_CONTROL = 0x11
VK_MENU    = 0x12   # ALT
VK_SHIFT   = 0x10

user32.MapVirtualKeyW.argtypes = [wt.UINT, wt.UINT]
user32.MapVirtualKeyW.restype  = wt.UINT
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype  = ctypes.c_short

# -- Named keys (function keys, special keys) ---------------
_NAMED_KEYS = {
    'F1':0x70,'F2':0x71,'F3':0x72,'F4':0x73,'F5':0x74,'F6':0x75,
    'F7':0x76,'F8':0x77,'F9':0x78,'F10':0x79,'F11':0x7A,'F12':0x7B,
    'SPACE':0x20,'ENTER':0x0D,'RETURN':0x0D,'TAB':0x09,'ESC':0x1B,'ESCAPE':0x1B,
    'INSERT':0x2D,'DELETE':0x2E,'HOME':0x24,'END':0x23,
    'PAGEUP':0x21,'PAGEDOWN':0x22,'BACKSPACE':0x08,
    'UP':0x26,'DOWN':0x28,'LEFT':0x25,'RIGHT':0x27,
    'LSHIFT':0xA0,'RSHIFT':0xA1,'LCTRL':0xA2,'RCTRL':0xA3,'LALT':0xA4,'RALT':0xA5,
}

# ============================================================
#  GUI
# ============================================================
gui = QtBind.init(__name__, pName)

def fixed_width_text(content, width):
    return (
        '<table width="{0}" cellspacing="0" cellpadding="0">'
        '<tr><td>{1}</td></tr></table>'
    ).format(width, content)


def _section(text):
    return '<font color="%s"><b>%s</b></font>' % (COLOR_PRIMARY, text)


QtBind.createLabel(
    gui, u'<font color="%s" size="4"><b>FTARGET</b></font>' % COLOR_PRIMARY,
    12, 6)
QtBind.createLabel(
    gui, '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion), 125, 12)
QtBind.createButton(gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(
    gui, u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' % COLOR_PRIMARY,
    565, 11)
QtBind.createLineEdit(gui, '', 12, 30, 716, 1)

QtBind.createLabel(gui, _section('KEY SEQUENCE'), 12, 43)
QtBind.createLabel(
    gui,
    '<font color="%s">Configure the combo and follow-up key.</font>' % COLOR_MUTED,
    12, 63)
chk_enable = QtBind.createCheckBox(gui, 'chk_changed_cb', 'Enable plugin', 12, 86)

QtBind.createLabel(gui, '<font color="%s"><b>Combo key</b></font>' % COLOR_LABEL, 12, 118)
tbx_key = QtBind.createLineEdit(gui, '2', 112, 114, 55, 22)
chk_ctrl = QtBind.createCheckBox(gui, 'chk_changed_cb', 'Ctrl', 182, 114)
chk_alt = QtBind.createCheckBox(gui, 'chk_changed_cb', 'Alt', 242, 114)
chk_shift = QtBind.createCheckBox(gui, 'chk_changed_cb', 'Shift', 297, 114)

QtBind.createLabel(gui, '<font color="%s"><b>Follow-up key</b></font>' % COLOR_LABEL, 12, 150)
tbx_key2 = QtBind.createLineEdit(gui, 'r', 112, 146, 55, 22)
QtBind.createLabel(gui, '<font color="%s"><b>Delay</b></font>' % COLOR_LABEL, 182, 150)
tbx_gap = QtBind.createLineEdit(gui, '100', 230, 146, 55, 22)
QtBind.createLabel(gui, '<font color="%s">ms</font>' % COLOR_MUTED, 292, 150)

QtBind.createLineEdit(gui, '', 12, 181, 360, 1)
QtBind.createLabel(gui, _section('TRIGGERS'), 12, 194)
chk_hotkey = QtBind.createCheckBox(gui, 'chk_changed_cb', 'Global hotkey', 12, 218)
tbx_hotkey = QtBind.createLineEdit(gui, 'F8', 132, 216, 65, 22)
chk_chat = QtBind.createCheckBox(
    gui, 'chk_changed_cb', "Chat command ('%s')" % CHAT_CMD, 12, 248)
QtBind.createLabel(gui, '<font color="%s"><b>Sender</b></font>' % COLOR_LABEL, 182, 252)
tbx_sender = QtBind.createLineEdit(gui, '', 238, 248, 134, 22)
QtBind.createLabel(gui, '<font color="%s"><b>Loop interval</b></font>' % COLOR_LABEL, 12, 282)
tbx_interval = QtBind.createLineEdit(gui, '5', 112, 278, 55, 22)
QtBind.createLabel(gui, '<font color="%s">sec</font>' % COLOR_MUTED, 174, 282)
QtBind.createButton(gui, 'btn_loop_start_cb', 'Start Loop', 220, 278)
QtBind.createButton(gui, 'btn_loop_stop_cb', 'Stop', 310, 278)

QtBind.createLabel(gui, _section('PARTY MESSAGE'), 412, 148)
chk_pchat = QtBind.createCheckBox(
    gui, 'chk_changed_cb', 'Send party message on key', 412, 174)
QtBind.createLabel(gui, '<font color="%s"><b>Key</b></font>' % COLOR_LABEL, 412, 206)
tbx_pckey = QtBind.createLineEdit(gui, 'LSHIFT', 452, 202, 82, 22)
QtBind.createLabel(gui, '<font color="%s"><b>Message</b></font>' % COLOR_LABEL, 548, 206)
tbx_pcmsg = QtBind.createLineEdit(gui, 'tg', 613, 202, 100, 22)
QtBind.createButton(gui, 'btn_save_cb', 'Save Settings', 412, 272)

QtBind.createLineEdit(gui, '', 392, 43, 1, 258)
QtBind.createLabel(gui, _section('LIVE STATUS'), 412, 43)
QtBind.createLabel(gui, '<font color="%s"><b>State</b></font>' % COLOR_LABEL, 412, 72)
lbl_status = QtBind.createLabel(
    gui,
    fixed_width_text('<font color="%s">Ready.</font>' % COLOR_MUTED, 294),
    412, 94)
QtBind.createLineEdit(gui, '', 412, 133, 304, 1)
QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s">Party message uses its own hotkey and checkbox.</font>' %
        COLOR_MUTED,
        294),
    412, 238)

# ============================================================
#  State
# ============================================================
_send_lock    = threading.Lock()
_loop_running = False
_loaded       = False   # don't save while loading

# ============================================================
#  Helpers
# ============================================================
def _set_status(txt, color=COLOR_MUTED):
    try:
        QtBind.setText(
            gui, lbl_status,
            fixed_width_text('<font color="%s">%s</font>' % (color, txt), 294))
    except: pass

def _enabled():
    try: return QtBind.isChecked(gui, chk_enable)
    except: return False

def _get_hwnd():
    try:
        c = get_client()
        if c and c.get('window') and c['window'] != 0:
            return c['window']
    except: pass
    try:
        h = user32.FindWindowW('Silkroad Online Application', None)
        if h: return h
    except: pass
    return None

def _parse_vk(widget):
    """Parse a key field to a VK code. '0x41'->0x41, '2'->0x32, 'a'->0x41, 'F8'->0x77"""
    s = QtBind.text(gui, widget).strip()
    if not s:
        return None
    up = s.upper()
    if up in _NAMED_KEYS:
        return _NAMED_KEYS[up]
    if up.startswith('0X'):
        try: return int(s, 16)
        except: return None
    res = user32.VkKeyScanW(ord(s[0]))
    if res == -1:
        return None
    return res & 0xFF

def _modifiers():
    mods = []
    try:
        if QtBind.isChecked(gui, chk_ctrl):  mods.append(VK_CONTROL)
        if QtBind.isChecked(gui, chk_alt):   mods.append(VK_MENU)
        if QtBind.isChecked(gui, chk_shift): mods.append(VK_SHIFT)
    except: pass
    return mods

def _scan(vk):
    return user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC)

def _focus_window(hwnd):
    """Bring the game window to front (keybd_event is global, so the right window must be focused)"""
    try:
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        fg = user32.GetForegroundWindow()
        cur_tid = kernel32.GetCurrentThreadId()
        fg_tid  = user32.GetWindowThreadProcessId(fg, None)
        tgt_tid = user32.GetWindowThreadProcessId(hwnd, None)
        user32.AttachThreadInput(cur_tid, fg_tid, True)
        user32.AttachThreadInput(cur_tid, tgt_tid, True)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        user32.SetFocus(hwnd)
        user32.AttachThreadInput(cur_tid, fg_tid, False)
        user32.AttachThreadInput(cur_tid, tgt_tid, False)
        time.sleep(0.15)
        return True
    except Exception as e:
        log('[%s] focus error: %s' % (pName, e))
        return False

# ============================================================
#  Config (per-character JSON)
# ============================================================
def _cfg_dir():
    try:
        base = get_config_dir()
        if base:
            d = os.path.join(base, pName)
            if not os.path.exists(d): os.makedirs(d)
            return d
    except: pass
    d = os.path.join(os.path.dirname(os.path.realpath(__file__)), pName)
    if not os.path.exists(d): os.makedirs(d)
    return d

def _cfg_path():
    try:
        c = get_character_data()
        if c and c.get('name'):
            name   = c.get('name', '').strip()
            server = c.get('server', '').strip()
            return os.path.join(_cfg_dir(), '%s_%s.json' % (server, name))
    except: pass
    return os.path.join(_cfg_dir(), 'default.json')

def _collect():
    return {
        'enabled':   QtBind.isChecked(gui, chk_enable),
        'key':       QtBind.text(gui, tbx_key).strip(),
        'ctrl':      QtBind.isChecked(gui, chk_ctrl),
        'alt':       QtBind.isChecked(gui, chk_alt),
        'shift':     QtBind.isChecked(gui, chk_shift),
        'key2':      QtBind.text(gui, tbx_key2).strip(),
        'gap':       QtBind.text(gui, tbx_gap).strip(),
        'hotkey_on': QtBind.isChecked(gui, chk_hotkey),
        'hotkey':    QtBind.text(gui, tbx_hotkey).strip(),
        'chat_on':   QtBind.isChecked(gui, chk_chat),
        'sender':    QtBind.text(gui, tbx_sender).strip(),
        'interval':  QtBind.text(gui, tbx_interval).strip(),
        'pchat_on':  QtBind.isChecked(gui, chk_pchat),
        'pchat_key': QtBind.text(gui, tbx_pckey).strip(),
        'pchat_msg': QtBind.text(gui, tbx_pcmsg).strip(),
    }

def _save_config():
    if not _loaded:
        return
    path = _cfg_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(_collect(), f, indent=2, ensure_ascii=False)
        _set_status('Saved: %s' % os.path.basename(path), COLOR_SUCCESS)
    except Exception as e:
        log('[%s] save error: %s' % (pName, e))
        _set_status('Could not save settings', COLOR_ERROR)

def _apply(d):
    try: QtBind.setChecked(gui, chk_enable, bool(d.get('enabled', False)))
    except: pass
    try: QtBind.setText(gui, tbx_key, str(d.get('key', '2')))
    except: pass
    try: QtBind.setChecked(gui, chk_ctrl,  bool(d.get('ctrl', False)))
    except: pass
    try: QtBind.setChecked(gui, chk_alt,   bool(d.get('alt', False)))
    except: pass
    try: QtBind.setChecked(gui, chk_shift, bool(d.get('shift', False)))
    except: pass
    try: QtBind.setText(gui, tbx_key2, str(d.get('key2', 'r')))
    except: pass
    try: QtBind.setText(gui, tbx_gap, str(d.get('gap', '100')))
    except: pass
    try: QtBind.setChecked(gui, chk_hotkey, bool(d.get('hotkey_on', False)))
    except: pass
    try: QtBind.setText(gui, tbx_hotkey, str(d.get('hotkey', 'F8')))
    except: pass
    try: QtBind.setChecked(gui, chk_chat, bool(d.get('chat_on', False)))
    except: pass
    try: QtBind.setText(gui, tbx_sender, str(d.get('sender', '')))
    except: pass
    try: QtBind.setText(gui, tbx_interval, str(d.get('interval', '5')))
    except: pass
    try: QtBind.setChecked(gui, chk_pchat, bool(d.get('pchat_on', False)))
    except: pass
    try: QtBind.setText(gui, tbx_pckey, str(d.get('pchat_key', 'LSHIFT')))
    except: pass
    try: QtBind.setText(gui, tbx_pcmsg, str(d.get('pchat_msg', 'tg')))
    except: pass

def _load_config():
    global _loaded
    path = _cfg_path()
    if path and os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                _apply(json.load(f))
            log('[%s] Loaded: %s' % (pName, os.path.basename(path)))
        except Exception as e:
            log('[%s] load error: %s' % (pName, e))
    _loaded = True

# ============================================================
#  Send (keybd_event)
# ============================================================
def _send_combo(vk, mods):
    for m in mods:
        user32.keybd_event(m, _scan(m), 0, 0)
    time.sleep(0.03)
    user32.keybd_event(vk, _scan(vk), 0, 0)
    time.sleep(0.05)
    user32.keybd_event(vk, _scan(vk), KEYEVENTF_KEYUP, 0)
    time.sleep(0.03)
    for m in reversed(mods):
        user32.keybd_event(m, _scan(m), KEYEVENTF_KEYUP, 0)

def _send_key(vk):
    user32.keybd_event(vk, _scan(vk), 0, 0)
    time.sleep(0.05)
    user32.keybd_event(vk, _scan(vk), KEYEVENTF_KEYUP, 0)

# ============================================================
#  Core: combo + follow-up key (lock + master enable)
# ============================================================
def _fire(source='?'):
    if not _enabled():
        return
    if not _send_lock.acquire(False):
        log('[%s] busy, skipped (%s)' % (pName, source))
        return
    try:
        vk1 = _parse_vk(tbx_key)
        if vk1 is None:
            _set_status('Invalid combo key!', '#CC0000'); return
        vk2 = _parse_vk(tbx_key2)
        if vk2 is None:
            _set_status('Invalid 2nd key!', '#CC0000'); return
        mods = _modifiers()
        hwnd = _get_hwnd()
        if not hwnd:
            _set_status('Game window not found!', '#CC0000'); return

        try: gap_ms = float(QtBind.text(gui, tbx_gap).strip())
        except: gap_ms = 100.0

        combo_txt = '+'.join([{VK_CONTROL:'Ctrl', VK_MENU:'Alt', VK_SHIFT:'Shift'}[m] for m in mods] +
                             [QtBind.text(gui, tbx_key).strip()])
        key2_txt = QtBind.text(gui, tbx_key2).strip()

        _focus_window(hwnd)
        _send_combo(vk1, mods)
        if gap_ms > 0:
            time.sleep(gap_ms / 1000.0)
        _send_key(vk2)
        _set_status('[%s] Sent: %s -> %s' % (source, combo_txt, key2_txt), '#009900')
        log('[%s] %s: %s -> %s (hwnd=%s)' % (pName, source, combo_txt, key2_txt, hwnd))
    except Exception as e:
        _set_status('ERROR: %s' % e, '#CC0000')
        log('[%s] fire error: %s' % (pName, e))
    finally:
        _send_lock.release()

# ============================================================
#  GUI callbacks
# ============================================================
def btn_save_cb():
    _save_config()

def chk_changed_cb(checked=False):
    _save_config()

def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        _set_status('Opening Discord invite...', COLOR_SUCCESS)
    except Exception as error:
        log('[%s] Discord link error: %s' % (pName, error))
        _set_status('Could not open Discord invite', COLOR_ERROR)

# ============================================================
#  Trigger: Global hotkey (GetAsyncKeyState polling)
# ============================================================
def _send_party_msg():
    msg = ''
    try: msg = QtBind.text(gui, tbx_pcmsg).strip()
    except: pass
    if not msg:
        return
    try:
        phBotChat.Party(msg)
        _set_status('Party msg sent: %s' % msg, '#009900')
        log('[%s] party msg: %s' % (pName, msg))
    except Exception as e:
        _set_status('party msg error: %s' % e, '#CC0000')
        log('[%s] party msg error: %s' % (pName, e))

def _hotkey_thread():
    prev_down = False   # combo trigger key
    prev_pc   = False   # party-chat key
    while True:
        # -- combo trigger (gated by master enable + its checkbox) --
        try:
            active = _enabled() and QtBind.isChecked(gui, chk_hotkey)
        except:
            active = False
        if active:
            vk = _parse_vk(tbx_hotkey)
            if vk:
                down = bool(user32.GetAsyncKeyState(vk) & 0x8000)
                if down and not prev_down:
                    threading.Thread(target=_fire, args=('hotkey',), daemon=True).start()
                prev_down = down
            else:
                prev_down = False
        else:
            prev_down = False

        # -- party chat sender (independent, own checkbox only) --
        try:
            pc_active = QtBind.isChecked(gui, chk_pchat)
        except:
            pc_active = False
        if pc_active:
            pvk = _parse_vk(tbx_pckey)
            if pvk:
                pdown = bool(user32.GetAsyncKeyState(pvk) & 0x8000)
                if pdown and not prev_pc:
                    threading.Thread(target=_send_party_msg, daemon=True).start()
                prev_pc = pdown
            else:
                prev_pc = False
        else:
            prev_pc = False

        time.sleep(0.03)

threading.Thread(target=_hotkey_thread, daemon=True).start()

# ============================================================
#  Trigger: Chat command (fixed 'tg')
# ============================================================
def handle_chat(t, player, msg):
    if not msg or not _enabled():
        return
    try:
        if not QtBind.isChecked(gui, chk_chat):
            return
    except:
        return

    player_l = (player or '').strip().lower()

    # Sender filter:
    #  - if 'Sender' is set: only accept the command from that character
    #  - if empty: only accept from own character (safe default)
    sender = ''
    try: sender = QtBind.text(gui, tbx_sender).strip().lower()
    except: pass
    if sender:
        if player_l != sender:
            return
    else:
        try:
            me = get_character_data()
            if me and player_l != me.get('name', '').strip().lower():
                return
        except:
            return

    if msg.strip().lower() == CHAT_CMD:
        threading.Thread(target=_fire, args=('chat:%s' % player_l,), daemon=True).start()

# ============================================================
#  Trigger: Loop
# ============================================================
def _loop_thread():
    global _loop_running
    while _loop_running:
        _fire('loop')
        try: interval = float(QtBind.text(gui, tbx_interval).strip())
        except: interval = 5.0
        if interval < 0.5:
            interval = 0.5
        waited = 0.0
        while _loop_running and waited < interval:
            time.sleep(0.1)
            waited += 0.1

def btn_loop_start_cb():
    global _loop_running
    if not _enabled():
        _set_status('Enable the plugin first!', '#CC0000')
        return
    if _loop_running:
        return
    _loop_running = True
    _set_status('Loop started.', '#009900')
    threading.Thread(target=_loop_thread, daemon=True).start()

def btn_loop_stop_cb():
    global _loop_running
    _loop_running = False
    _set_status('Loop stopped.')

# ============================================================
#  phBot Events
# ============================================================
def joined_game():
    def _delayed():
        time.sleep(1.5)
        _load_config()
    threading.Thread(target=_delayed, daemon=True).start()

# initial load (outside game) if default.json exists
_load_config()

log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
