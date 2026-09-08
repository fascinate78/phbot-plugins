from phBot import *
import QtBind
import webbrowser
from threading import Timer


pName = 'FAutoCaptcha'
pVersion = '1.0.1'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

CAPTCHA_OPCODE = 0xC011
REPLAY_INTERVAL_SECONDS = 30.0

COLOR_PRIMARY = '#5b57e0'
COLOR_TEXT = '#2b3038'
COLOR_MUTED = '#9aa0ac'
COLOR_SUCCESS = '#1f9d63'
COLOR_WARNING = '#c98a1a'
COLOR_ERROR = '#d93a4d'

enabled = True
captured_payload = None
replay_timer = None
replay_count = 0


def fixed_width_text(content, width):
    return (
        '<table width="{0}" cellspacing="0" cellpadding="0">'
        '<tr><td>{1}</td></tr></table>'
    ).format(width, content)


def html_escape(text):
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def set_status(message, color=COLOR_MUTED):
    QtBind.setText(
        gui,
        status_value_label,
        fixed_width_text(
            '<font color="{0}"><b>{1}</b></font>'.format(
                color, html_escape(message)
            ),
            300
        )
    )


def set_packet_status(source='Waiting for 0xC011 packet'):
    QtBind.setText(
        gui,
        packet_value_label,
        fixed_width_text(
            '<font color="{0}">{1}</font>'.format(
                COLOR_TEXT, html_escape(source)
            ),
            300
        )
    )


def set_replay_count():
    QtBind.setText(
        gui,
        replay_value_label,
        fixed_width_text(
            '<font color="{0}"><b>{1}</b></font>'.format(
                COLOR_PRIMARY, replay_count
            ),
            300
        )
    )


def cancel_replay_timer():
    global replay_timer
    if replay_timer is not None:
        replay_timer.cancel()
        replay_timer = None


def schedule_replay():
    global replay_timer
    cancel_replay_timer()
    if not enabled or captured_payload is None:
        return
    replay_timer = Timer(REPLAY_INTERVAL_SECONDS, replay_captcha_packet)
    replay_timer.daemon = True
    replay_timer.start()


def send_captcha_packet(reason):
    global replay_count
    if not enabled or captured_payload is None:
        return False
    try:
        inject_joymax(CAPTCHA_OPCODE, captured_payload, False)
        replay_count += 1
        set_replay_count()
        set_status('%s sent to server' % reason, COLOR_SUCCESS)
        return True
    except Exception as error:
        set_status('Could not send 0xC011 packet', COLOR_ERROR)
        log('[%s] Packet send error: %s' % (pName, error))
        return False


def replay_captcha_packet():
    global replay_timer
    replay_timer = None
    if send_captcha_packet('Scheduled replay'):
        schedule_replay()


def capture_captcha_packet(data, source):
    global captured_payload
    try:
        payload = bytes(bytearray(data))
    except Exception as error:
        set_status('Invalid 0xC011 packet data', COLOR_ERROR)
        log('[%s] Packet capture error: %s' % (pName, error))
        return

    if not payload or payload == captured_payload:
        return

    captured_payload = payload
    set_packet_status('%s (%d bytes)' % (source, len(payload)))
    if enabled:
        send_captcha_packet('Captured packet')
        schedule_replay()
    else:
        set_status('Packet captured while disabled', COLOR_WARNING)


def enabled_changed(checked):
    global enabled
    enabled = bool(checked)
    if enabled:
        if captured_payload is None:
            set_status('Enabled - waiting for 0xC011', COLOR_WARNING)
        else:
            set_status('Enabled - replay scheduled', COLOR_SUCCESS)
            schedule_replay()
    else:
        cancel_replay_timer()
        set_status('Automatic replay disabled', COLOR_MUTED)


def clear_captured_packet():
    global captured_payload, replay_count
    cancel_replay_timer()
    captured_payload = None
    replay_count = 0
    set_packet_status()
    set_replay_count()
    set_status('Captured packet cleared', COLOR_MUTED)


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        set_status('Opening Discord invite...', COLOR_SUCCESS)
    except Exception as error:
        set_status('Could not open Discord invite', COLOR_ERROR)
        log('[%s] Discord link error: %s' % (pName, error))


gui = QtBind.init(__name__, pName)

QtBind.createLabel(
    gui,
    u'<font color="%s" size="4"><b>FAutoCaptcha</b></font>' % COLOR_PRIMARY,
    12,
    6
)
QtBind.createLabel(
    gui,
    '<font color="%s">v%s</font>' % (COLOR_MUTED, pVersion),
    205,
    12
)
QtBind.createButton(gui, 'discord_clicked', u'\U0001f4ac Discord', 462, 6)
QtBind.createLabel(
    gui,
    u'<font color="%s"><b>⚜ Made By FascinaTe</b></font>' % COLOR_PRIMARY,
    565,
    11
)
QtBind.createLineEdit(gui, '', 12, 30, 716, 1)

QtBind.createLabel(
    gui,
    '<font color="%s"><b>Automatic Packet Replay</b></font>' % COLOR_PRIMARY,
    12,
    52
)
QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s">Captures the server-specific 0xC011 packet and replays it every 30 seconds.</font>' % COLOR_MUTED,
        690
    ),
    12,
    74
)
QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s"><b>MAXIGUARD SERVERS ONLY</b></font>' % COLOR_WARNING,
        690
    ),
    12,
    96
)
QtBind.createLineEdit(gui, '', 12, 119, 716, 1)

enabled_checkbox = QtBind.createCheckBox(
    gui, 'enabled_changed', 'Enable automatic replay', 12, 137
)
QtBind.createButton(gui, 'clear_captured_packet', 'Clear Captured Packet', 195, 133)

QtBind.createLineEdit(gui, '', 12, 168, 716, 1)
QtBind.createLabel(
    gui,
    '<font color="%s"><b>Live Status</b></font>' % COLOR_PRIMARY,
    12,
    187
)

QtBind.createLabel(gui, '<font color="%s">Status</font>' % COLOR_MUTED, 12, 217)
status_value_label = QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s"><b>Enabled - waiting for 0xC011</b></font>' % COLOR_WARNING,
        300
    ),
    120,
    217
)
QtBind.createLabel(gui, '<font color="%s">Last packet</font>' % COLOR_MUTED, 12, 247)
packet_value_label = QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s">Waiting for 0xC011 packet</font>' % COLOR_TEXT,
        300
    ),
    120,
    247
)
QtBind.createLabel(gui, '<font color="%s">Packets sent</font>' % COLOR_MUTED, 12, 277)
replay_value_label = QtBind.createLabel(
    gui,
    fixed_width_text(
        '<font color="%s"><b>0</b></font>' % COLOR_PRIMARY,
        300
    ),
    120,
    277
)
QtBind.setChecked(gui, enabled_checkbox, True)


def connected():
    if enabled:
        set_status('Connected - waiting for 0xC011', COLOR_WARNING)


def disconnected():
    clear_captured_packet()
    set_status('Disconnected - cached packet cleared', COLOR_MUTED)


def handle_joymax(opcode, data):
    if opcode == CAPTCHA_OPCODE and data:
        capture_captcha_packet(data, 'Server packet captured')
    return True


def handle_silkroad(opcode, data):
    if opcode == CAPTCHA_OPCODE and data:
        capture_captcha_packet(data, 'Client packet captured')
    return True


def finished():
    cancel_replay_timer()


log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
