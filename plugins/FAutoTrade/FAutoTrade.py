from phBot import *

import QtBind

import ctypes, ctypes.wintypes

import time, threading, json, os, struct
import webbrowser
import urllib.request, urllib.parse


pName    = 'FAutoTrade'
pVersion = '2.2.0'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'


WM_MOUSEMOVE   = 0x0200

WM_LBUTTONDOWN = 0x0201

WM_LBUTTONUP   = 0x0202

MK_LBUTTON     = 0x0001

user32   = ctypes.windll.user32



# ============================================================



# ============================================================

_input_blocked  = False

_input_lock     = threading.Lock()

GWL_STYLE       = -16

WS_DISABLED     = 0x08000000



def _block_input(block: bool):


    global _input_blocked

    with _input_lock:

        if block == _input_blocked:

            return

        hwnd = _get_hwnd()

        if not hwnd:

            return

        try:

            style = user32.GetWindowLongW(hwnd, GWL_STYLE)

            if block:

                new_style = style | WS_DISABLED

            else:

                new_style = style & ~WS_DISABLED

            user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)

            _input_blocked = block

            state = 'BLOCKED 🔒' if block else 'RELEASED 🔓'

            log(f'[AutoTrade] Game window input {state}')

        except Exception as e:

            log(f'[AutoTrade] ❌ block_input error: {e}')





# ============================================================

#  GUI

# ============================================================

gui = QtBind.init(__name__, pName)



# ── Dummy vars ──────────────────────────────────────────────

tbx_cmd = tbx_npc = btn_load_npcs = None

tbx_npc_x = tbx_npc_y = btn_cap_npc = None

tbx_max_trips = lbl_trips_done = None

tbx_x1 = tbx_y1 = tbx_d1 = tbx_r1 = None

tbx_x2 = tbx_y2 = tbx_d2 = tbx_r2 = None

tbx_x3 = tbx_y3 = tbx_d3 = tbx_r3 = None

tbx_x4 = tbx_y4 = tbx_d4 = tbx_r4 = None

tbx_x5 = tbx_y5 = tbx_d5 = tbx_r5 = None

tbx_x6 = tbx_y6 = tbx_d6 = tbx_r6 = None

tbx_x7 = tbx_y7 = tbx_d7 = tbx_r7 = None

btn_cap1 = btn_cap2 = btn_cap3 = btn_cap4 = btn_cap5 = None

tbx_x8 = tbx_y8 = tbx_d8 = tbx_r8 = None

btn_cap6 = btn_cap7 = btn_cap8 = None

btn_add = btn_del = None

chk_pairs = btn_refresh_scripts = btn_save_pairs = None

tbx_town1 = tbx_pc1 = tbx_ps1 = None

tbx_town2 = tbx_pc2 = tbx_ps2 = None

lbl_status = lbl_char = lbl_window = None



QtBind.createLabel(gui, '<font color="#FF0000"><b>Command:</b></font>', 8, 7)

tbx_cmd = QtBind.createLineEdit(gui, '', 68, 3, 110, 22)

QtBind.createLabel(gui, '<font color="#FF0000"><b>NPC:</b></font>', 185, 7)

tbx_npc = QtBind.createCombobox(gui, 210, 3, 130, 22)

btn_load_npcs = QtBind.createButton(gui, 'btn_load_npcs_cb', 'Load NPC', 345, 3)



# NPC Stop Position

QtBind.createLabel(gui, '<font color="#FF0000"><b>NPC  X:</b></font>', 8, 35)

tbx_npc_x = QtBind.createLineEdit(gui, '0', 70, 30, 50, 22)

QtBind.createLabel(gui, '<font color="#FF0000"><b>Y:</b></font>', 126, 35)

tbx_npc_y = QtBind.createLineEdit(gui, '0', 136, 30, 50, 22)

btn_cap_npc = QtBind.createButton(gui, 'btn_cap_npc_cb', '🎯Get Position Npc', 192, 30)



# Clicks

QtBind.createLabel(gui, '<font color="#FF0000">#   X      Y     Delay Rep Cap</font>', 8, 60)



tbx_x1=QtBind.createLineEdit(gui,'0',  20,80,45,18)

tbx_y1=QtBind.createLineEdit(gui,'0',  70,80,45,18)

tbx_d1=QtBind.createLineEdit(gui,'1.0',120,80,35,18)

tbx_r1=QtBind.createLineEdit(gui,'1',  160,80,25,18)

QtBind.createLabel(gui,'<font color="#FF0000"><b>1:</b></font>',8,82)

btn_cap1=QtBind.createButton(gui,'btn_cap1_cb','🦋Cap Oppen Npc',190,77)



tbx_x2=QtBind.createLineEdit(gui,'0',  20,102,45,18)

tbx_y2=QtBind.createLineEdit(gui,'0',  70,102,45,18)

tbx_d2=QtBind.createLineEdit(gui,'1.0',120,102,35,18)

tbx_r2=QtBind.createLineEdit(gui,'1',  160,102,25,18)

QtBind.createLabel(gui,'<font color="#FF0000"><b>2:</b></font>',8,104)

btn_cap2=QtBind.createButton(gui,'btn_cap2_cb','🦋Cap Sell Gods',190,99)



tbx_x3=QtBind.createLineEdit(gui,'0',  20,124,45,18)

tbx_y3=QtBind.createLineEdit(gui,'0',  70,124,45,18)

tbx_d3=QtBind.createLineEdit(gui,'1.0',120,124,35,18)

tbx_r3=QtBind.createLineEdit(gui,'1',  160,124,25,18)

QtBind.createLabel(gui,'<font color="#FF0000"><b>3:</b></font>',8,126)

btn_cap3=QtBind.createButton(gui,'btn_cap3_cb','🦋Cap Yes Sell Gods',190,121)



tbx_x4=QtBind.createLineEdit(gui,'0',  20,146,45,18)

tbx_y4=QtBind.createLineEdit(gui,'0',  70,146,45,18)

tbx_d4=QtBind.createLineEdit(gui,'1.0',120,146,35,18)

tbx_r4=QtBind.createLineEdit(gui,'1',  160,146,25,18)

QtBind.createLabel(gui,'<font color="#FF0000"><b>4:</b></font>',8,148)

btn_cap4=QtBind.createButton(gui,'btn_cap4_cb','🦋Select Goods',190,143)



tbx_x5=QtBind.createLineEdit(gui,'0',  20,168,45,18)

tbx_y5=QtBind.createLineEdit(gui,'0',  70,168,45,18)

tbx_d5=QtBind.createLineEdit(gui,'1.0',120,168,35,18)

tbx_r5=QtBind.createLineEdit(gui,'1',  160,168,25,18)

QtBind.createLabel(gui,'<font color="#FF0000"><b>5:</b></font>',8,170)

btn_cap5=QtBind.createButton(gui,'btn_cap5_cb','🦋Trade Pet Slot',190,165)



tbx_x6=QtBind.createLineEdit(gui,'0',  20,190,45,18)

tbx_y6=QtBind.createLineEdit(gui,'0',  70,190,45,18)

tbx_d6=QtBind.createLineEdit(gui,'1.0',120,190,35,18)

tbx_r6=QtBind.createLineEdit(gui,'1',  160,190,25,18)

QtBind.createLabel(gui,'<font color="#FF0000"><b>6:</b></font>',8,192)

btn_cap6=QtBind.createButton(gui,'btn_cap6_cb','🦋Scale Button',190,187)



tbx_x7=QtBind.createLineEdit(gui,'0',  20,212,45,18)

tbx_y7=QtBind.createLineEdit(gui,'0',  70,212,45,18)

tbx_d7=QtBind.createLineEdit(gui,'1.0',120,212,35,18)

tbx_r7=QtBind.createLineEdit(gui,'1',  160,212,25,18)

QtBind.createLabel(gui,'<font color="#FF0000"><b>7:</b></font>',8,214)

btn_cap7=QtBind.createButton(gui,'btn_cap7_cb','🦋Star Select',190,209)



tbx_x8=QtBind.createLineEdit(gui,'0',  20,234,45,18)

tbx_y8=QtBind.createLineEdit(gui,'0',  70,234,45,18)

tbx_d8=QtBind.createLineEdit(gui,'1.0',120,234,35,18)

tbx_r8=QtBind.createLineEdit(gui,'1',  160,234,25,18)

QtBind.createLabel(gui,'<font color="#FF0000"><b>8:</b></font>',8,236)

btn_cap8=QtBind.createButton(gui,'btn_cap8_cb','🦋Confirm',190,231)





btn_add  =QtBind.createButton(gui,'btn_add_cb',        '➕Add/Update', 8,   258)

btn_del  =QtBind.createButton(gui,'btn_del_cb',        '🗑️ Delete',    100, 258)

QtBind.createButton(gui,       'btn_edit_cmd_cb',      '✏️ Edit',       185, 258)

btn_auto_start = QtBind.createButton(gui,'btn_auto_start_cb','▶️ Auto Start',270,258)

btn_stop_auto  = QtBind.createButton(gui,'_stop_auto_action','⏹️ Stop', 360,258)




_rx = 360



# Saved Commands list

QtBind.createLabel(gui, '<font color="#FF0000"><b>Saved Commands:</b></font>', 470, 7)

lst_cmds = QtBind.createList(gui, 470, 20, 250, 100)



chk_pairs = None

btn_refresh_scripts=QtBind.createButton(gui,'btn_refresh_scripts_cb','🔄 Refresh Scripts',_rx+85,258)

btn_save_pairs=QtBind.createButton(gui,'btn_save_pairs_cb','💾 Save',_rx+195,258)



QtBind.createLabel(gui,'<font color="#FF0000"><b>  Town➡️</b></font>',_rx+15,170)

QtBind.createLabel(gui,'<font color="#FF0000"><b>Command➡️</b></font>',_rx+120,170)

QtBind.createLabel(gui,'<font color="#FF0000"><b>Script➡️</b></font>',_rx+220,170)



tbx_town1=QtBind.createCombobox(gui,_rx+15,188,95,22)

for _t in ['Jangan','Donwhang','Hotan']: QtBind.append(gui,tbx_town1,_t)

tbx_pc1=QtBind.createCombobox(gui,_rx+115,188,95,22)

tbx_ps1=QtBind.createCombobox(gui,_rx+215,188,145,22)



tbx_town2=QtBind.createCombobox(gui,_rx+15,214,95,22)

for _t in ['Jangan','Donwhang','Hotan']: QtBind.append(gui,tbx_town2,_t)

tbx_pc2=QtBind.createCombobox(gui,_rx+115,214,95,22)

tbx_ps2=QtBind.createCombobox(gui,_rx+215,214,145,22)




QtBind.createLabel(gui, '<font color="#FF0000"><b>Limit Trade:</b></font>', 8, 291)

tbx_max_trips = QtBind.createLineEdit(gui, '0', 78, 289, 30, 18)

QtBind.createLabel(gui, '<font color="#FF0000"><b>Done:</b></font>', 110, 291)

lbl_trips_done = QtBind.createLabel(gui, '<font color="#FF0000"><b>0</b></font>', 148, 292)



QtBind.createLabel(gui, '<font color="#FF0000"><b>🐫Pet:</b></font>', 170, 291)

cbx_pet = QtBind.createCombobox(gui, 210, 289, 130, 22)

QtBind.createButton(gui, 'btn_load_pets_g1_cb', '🐫 Pet Load',_rx+280, 258)



QtBind.createLabel(gui, '<font color="#FF0000"><b>Script DeaTH:</b></font>', 350, 293)

tbx_death_scr = QtBind.createCombobox(gui, 430, 289, 130, 22)



chk_char_death = QtBind.createCheckBox(gui, 'chk_char_death_cb', 'Char Death', 560, 289)

chk_pet_death  = QtBind.createCheckBox(gui, 'chk_pet_death_cb',  'Pet Death',  640, 289)

QtBind.setChecked(gui, chk_char_death, True)

QtBind.setChecked(gui, chk_pet_death,  True)



lbl_death_status = QtBind.createLabel(gui, '<font color="#FF0000">Idle</font>', 8, 316)

lbl_pet_status   = QtBind.createLabel(gui, '<font color="#FF0000">—</font>',   200, 316)



# ── Status ───────────────────────────────────────────────────

QtBind.createLabel(gui,'<font color="#FF0000">Status:</font>',8,335)

lbl_status=QtBind.createLabel(gui,'<font color="#FF0000">Idle</font>',55,335)

QtBind.createLabel(gui,'<font color="#FF0000">Char:</font>',160,335)

lbl_char=QtBind.createLabel(gui,'<font color="#FF0000">—</font>',195,335)

QtBind.createLabel(gui,'<font color="#FF0000">Window:</font>',260,335)

lbl_window=QtBind.createLabel(gui,'<font color="#FF0000">—</font>',310,335)

btn_notifications = QtBind.createButton(
    gui, 'show_notifications_cb', '🔔 Notifications', 470, 123
)
btn_discord = QtBind.createButton(
    gui, 'discord_clicked', u'\U0001f4ac Discord', 610, 123
)
QtBind.createLabel(
    gui, u'<font color="#FF0000"><b>⚜ Made By FascinaTe</b></font>', 565, 150
)

# Notification settings open as a page inside this tab. The list is an opaque
# backdrop, keeping the original (already crowded) AutoTrade UI unchanged.
_NOTIFY_OFFSCREEN_X = 1200
_notification_widgets = []

def _notification_widget(widget, x, y):
    _notification_widgets.append((widget, x, y))
    QtBind.move(gui, widget, _NOTIFY_OFFSCREEN_X, y)
    return widget

_notification_widget(QtBind.createList(gui, _NOTIFY_OFFSCREEN_X, 0, 720, 350), 0, 0)
_notification_widget(
    QtBind.createLabel(gui, '<font color="#FF0000"><b>FAutoTrade Notifications</b></font>',
                       _NOTIFY_OFFSCREEN_X, 10), 15, 10)
_notification_widget(
    QtBind.createButton(gui, 'hide_notifications_cb', '↩ Back', _NOTIFY_OFFSCREEN_X, 5),
    640, 5)

chk_notify_discord = _notification_widget(
    QtBind.createCheckBox(gui, 'notification_setting_changed_cb', 'Enable Discord',
                          _NOTIFY_OFFSCREEN_X, 45), 15, 45)
_notification_widget(
    QtBind.createLabel(gui, 'Webhook URL:', _NOTIFY_OFFSCREEN_X, 75), 15, 75)
tbx_notify_discord_webhook = _notification_widget(
    QtBind.createLineEdit(gui, '', _NOTIFY_OFFSCREEN_X, 70, 430, 22), 105, 70)
_notification_widget(
    QtBind.createButton(gui, 'test_discord_notification_cb', '🧪 Test Discord',
                        _NOTIFY_OFFSCREEN_X, 68), 550, 68)

chk_notify_telegram = _notification_widget(
    QtBind.createCheckBox(gui, 'notification_setting_changed_cb', 'Enable Telegram',
                          _NOTIFY_OFFSCREEN_X, 110), 15, 110)
_notification_widget(
    QtBind.createLabel(gui, 'Bot Token:', _NOTIFY_OFFSCREEN_X, 140), 15, 140)
tbx_notify_telegram_token = _notification_widget(
    QtBind.createLineEdit(gui, '', _NOTIFY_OFFSCREEN_X, 135, 330, 22), 105, 135)
_notification_widget(
    QtBind.createLabel(gui, 'Chat ID:', _NOTIFY_OFFSCREEN_X, 170), 15, 170)
tbx_notify_telegram_chat_id = _notification_widget(
    QtBind.createLineEdit(gui, '', _NOTIFY_OFFSCREEN_X, 165, 180, 22), 105, 165)
_notification_widget(
    QtBind.createButton(gui, 'test_telegram_notification_cb', '🧪 Test Telegram',
                        _NOTIFY_OFFSCREEN_X, 133), 550, 133)

_notification_widget(
    QtBind.createLabel(gui, '<font color="#FF0000"><b>Notify me about</b></font>',
                       _NOTIFY_OFFSCREEN_X, 195), 15, 195)
chk_notify_start_stop = _notification_widget(
    QtBind.createCheckBox(gui, 'notification_setting_changed_cb', 'Start / Stop',
                          _NOTIFY_OFFSCREEN_X, 218), 15, 218)
chk_notify_trips = _notification_widget(
    QtBind.createCheckBox(gui, 'notification_setting_changed_cb', 'Trip completed / limit',
                          _NOTIFY_OFFSCREEN_X, 218), 145, 218)
chk_notify_deaths = _notification_widget(
    QtBind.createCheckBox(gui, 'notification_setting_changed_cb',
                          'Character / transport death', _NOTIFY_OFFSCREEN_X, 218),
    330, 218)
chk_notify_errors = _notification_widget(
    QtBind.createCheckBox(gui, 'notification_setting_changed_cb', 'Script / pet errors',
                          _NOTIFY_OFFSCREEN_X, 245), 15, 245)

_notification_widget(
    QtBind.createButton(gui, 'save_notification_settings_cb', '💾 Save Notifications',
                        _NOTIFY_OFFSCREEN_X, 270), 15, 270)
lbl_notification_status = _notification_widget(
    QtBind.createLabel(gui,
                       '<font color="#FF0000">Settings are stored per character.</font>',
                       _NOTIFY_OFFSCREEN_X, 278), 170, 278)

# ── Click fields list (used by form helpers & cap callbacks) ──
_CLICK_FIELDS = None  # will be set after GUI creation



# Constant click groups — defined once at module level

_CLICK_GROUPS = [(0, 3), (3, 8)]



QtBind.append(gui, cbx_pet, '')




_CLICK_FIELDS = [

    (tbx_x1,tbx_y1,tbx_d1,tbx_r1),

    (tbx_x2,tbx_y2,tbx_d2,tbx_r2),

    (tbx_x3,tbx_y3,tbx_d3,tbx_r3),

    (tbx_x4,tbx_y4,tbx_d4,tbx_r4),

    (tbx_x5,tbx_y5,tbx_d5,tbx_r5),

    (tbx_x6,tbx_y6,tbx_d6,tbx_r6),

    (tbx_x7,tbx_y7,tbx_d7,tbx_r7),

    (tbx_x8,tbx_y8,tbx_d8,tbx_r8),

]



# ============================================================

#  State — single definition (no duplicates)

# ============================================================

_stop_flag           = False

_running             = False

_commands            = {}

_current_pair        = 0

_trips_done          = 0

_pair_running        = False

_auto_running        = False

_bot_was_running     = False

_bot_start_time      = 0.0

_death_triggered     = False

_pet_death_triggered = False

_transport_died_flag = False

_was_auto_running    = False

_death_script_running = False

_teleport_time           = 0.0

_last_transport_seen     = time.time()

_transport_missing_count = 0

_TRANSPORT_MISSING_THRESHOLD = 12

_TRANSPORT_TELEPORT_GRACE   = 45

_script_teleporting      = False

_script_teleport_time    = 0.0

_SCRIPT_TELEPORT_GUARD   = 60

_script_pause_flag   = False

_pending_pair_idx    = -1

_pair_lock           = threading.Lock()

_death_lock          = threading.Lock()

_teleporting_now     = False

_gate_crossing       = False

_gold_before_teleport = -1

_notification_settings = {
    'discord_enabled': False,
    'discord_webhook': '',
    'telegram_enabled': False,
    'telegram_bot_token': '',
    'telegram_chat_id': '',
    'notify_start_stop': True,
    'notify_trips': True,
    'notify_deaths': True,
    'notify_errors': True,
}
_notification_last_sent = {}
_notification_lock = threading.Lock()

# ============================================================

#  Transport Pet

# ============================================================

_PET_TYPE_IDS = {0x11EC, 0x11ED}



_PET_NAME_TYPE_MAP = [

    (['elephant', 'white_elephant', 'cos_t_elephant'], 0x11ED),

    (['fire_bull', 'firebull', 'bull'],                0x11EC),

    (['donkey',   'cos_t_donkey'],                     0x11EC),

    (['horse',    'cos_t_horse'],                      0x11EC),

    (['camel',    'cos_t_camel'],                      0x11EC),

]



def _pet_get_type_id(item):

    for key in ('id', 'model', 'type_id', 'object_id'):

        val = item.get(key)

        if val and isinstance(val, int) and val in _PET_TYPE_IDS:

            return val

    sn   = item.get('servername', '').lower()

    name = item.get('name', '').lower()

    combined = sn + ' ' + name

    for keywords, type_id in _PET_NAME_TYPE_MAP:

        if any(kw in combined for kw in keywords):

            return type_id

    log(f'[AutoTrade] ⚠️ WARNING: unknown pet type for "{item.get("name","?")}" — using 0x11EC')

    return 0x11EC



def _pet_find_slot():

    try:

        name_filter = QtBind.text(gui, cbx_pet).strip().lower()

        if not name_filter: return -1, None

        inv = get_inventory()

        if not inv: return -1, None

        items = inv.get('items', [])

        for idx, item in enumerate(items):

            if not item: continue

            item_name  = item.get('name', '').lower()

            servername = item.get('servername', '').lower()

            type_id    = item.get('id') or item.get('model') or 0

            name_match = name_filter in item_name or name_filter in servername

            type_match = type_id in _PET_TYPE_IDS

            kw_match   = any(x in servername for x in [

                'cos_t_', 'cos_p_', 'transport', 'donkey', 'horse', 'camel', 'elephant', 'bull'

            ])

            if (name_match and (type_match or kw_match)) or type_match:

                return idx, item

        return -1, None

    except Exception as e:

        log(f'[AutoTrade] pet_find_slot error: {e}')

        return -1, None



def _pet_get_active():

    try:

        pets = get_pets()

        if not pets: return None

        for pet_id, pet in pets.items():

            if pet.get('type') in ('transport', 'horse'):

                return pet_id, pet

        return None

    except: return None



def _pet_summon_with_retry(max_tries=3, wait=5):


    for attempt in range(1, max_tries + 1):

        if _pet_get_active():

            return True

        _pet_summon_once()

        time.sleep(wait)

    if _pet_get_active():

        log('[AutoTrade] ✅ Pet summoned successfully.')

        return True

    log('[AutoTrade] ❌ Pet summon failed after all retries!')
    _queue_notification('Transport pet could not be summoned.', 'errors')
    return False



def _pet_summon_once():


    if _pet_get_active():

        return True


    try:

        import AutoTransportPet as _atp

        pet_name = QtBind.text(gui, cbx_pet).strip()

        if pet_name:

            QtBind.setText(_atp.gui, _atp.tbx_name, pet_name)

        _atp.btn_find_cb()

        time.sleep(0.3)

        _atp.btn_summon_cb()

        return True

    except ImportError: pass

    except Exception as e: log(f'[AutoTrade] ❌ AutoTransportPet error: {e}')

    # inject packet

    slot, item = _pet_find_slot()

    if slot == -1:

        log('[AutoTrade] ❌ Pet not found in bag!')

        return False

    try:

        type_id = _pet_get_type_id(item)

        data = struct.pack('<B', slot) + struct.pack('<H', type_id)

        inject_joymax(0x704C, data, False)

        return True

    except Exception as e:

        log(f'[AutoTrade] ❌ Pet summon error: {e}')

        return False



# Keep old name as alias for backward compat with GUI buttons

_pet_summon = _pet_summon_once



def _pet_dismiss():

    result = _pet_get_active()

    if not result:

        return

    pet_id, pet = result

    try:

        inject_joymax(0x7061, struct.pack('<I', pet_id), False)

    except Exception as e:

        log(f'[AutoTrade] ❌ pet dismiss error: {e}')



def _populate_pet_combobox():


    try:

        inv = get_inventory()

        if not inv or not cbx_pet: return

        items = [i for i in inv.get('items', []) if i]

        if not items: return

        cur = ''

        try: cur = QtBind.text(gui, cbx_pet).strip()

        except: pass

        QtBind.clear(gui, cbx_pet)

        QtBind.append(gui, cbx_pet, '')

        added = set()

        for it in items:

            sn   = it.get('servername', '').upper()

            name = it.get('name', '')

            if not name: continue

            is_transport = ('COS_T' in sn or

                            any(x in sn for x in ['DONKEY','HORSE','CAMEL','ELEPHANT',

                                                    'BULL','KUNLUN','RHINOCEROS','BEHEMOTH',

                                                    'BUFFALO','LIZARD','MAHRAGA']))

            if is_transport and name not in added:

                QtBind.append(gui, cbx_pet, name)

                added.add(name)

        if cur and cur in added:

            try: QtBind.setText(gui, cbx_pet, cur)

            except: pass

        elif added:

            try: QtBind.setText(gui, cbx_pet, list(added)[0])

            except: pass

    except Exception as e:

        pass



# ============================================================

#  Scripts Helper

# ============================================================

def _get_available_scripts():

    scripts = []

    try:

        plugin_dir = os.path.dirname(os.path.realpath(__file__))


        default_scripts_dir = os.path.join(plugin_dir, 'scripts')

        if not os.path.exists(default_scripts_dir):

            os.makedirs(default_scripts_dir)

        possible_paths = [

            default_scripts_dir,

            os.path.join(plugin_dir, 'Scripts'),

            get_config_dir() + "Scripts\\",

            os.path.join(plugin_dir, 'AutoTrade', 'Script'),

        ]

        for d in possible_paths:

            try:

                d = os.path.abspath(d)

                if os.path.exists(d):

                    for f in os.listdir(d):

                        if f.endswith('.txt') or f.endswith('.py'):

                            if f not in scripts:

                                scripts.append(f)

            except:

                pass

    except: pass

    return sorted(scripts)



def _refresh_scripts_comboboxes():

    scripts = _get_available_scripts()

    for cb in [tbx_ps1, tbx_ps2]:

        _refill_combobox(cb, scripts)



def _refresh_cmd_comboboxes():

    cmds = list(_commands.keys())

    for cb in [tbx_pc1, tbx_pc2]:

        _refill_combobox(cb, cmds)



def _refill_combobox(cb, items):


    try:

        cur = QtBind.text(gui, cb)

        QtBind.clear(gui, cb)

        QtBind.append(gui, cb, '')

        for item in items:

            QtBind.append(gui, cb, item)

        if cur:

            QtBind.setText(gui, cb, cur)

    except:

        pass



# ============================================================

#  Config

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

        if c and c.get('name') and c.get('server'):

            name   = c['name'].strip()

            server = c['server'].strip()


            p1 = os.path.join(_cfg_dir(), f"{server}_{name}.json")

            p2 = os.path.join(_cfg_dir(), f"{name}_{server}.json")

            if os.path.exists(p2) and not os.path.exists(p1):

                return p2

            return p1

    except: pass

    return os.path.join(_cfg_dir(), 'default.json')



def _save_config():

    path = _cfg_path()

    if not path: _set_status('Not in game!'); return

    pairs = []

    for town_tbx,pc,ps in [(tbx_town1,tbx_pc1,tbx_ps1),(tbx_town2,tbx_pc2,tbx_ps2)]:

        pairs.append({'town':QtBind.text(gui,town_tbx).strip(),

                      'cmd':QtBind.text(gui,pc).strip(),

                      'scr':QtBind.text(gui,ps).strip()})

    data = {'commands':_commands,'pairs':pairs,'pairs_enabled':_auto_running,

            'death_script':QtBind.text(gui,tbx_death_scr).strip(),

            'death_enabled': True,

            'char_death_enabled': QtBind.isChecked(gui, chk_char_death),

            'pet_death_enabled':  QtBind.isChecked(gui, chk_pet_death),

            'pet_name':QtBind.text(gui,cbx_pet).strip(),

            'limit_trade':QtBind.text(gui,tbx_max_trips).strip() if tbx_max_trips else '0',
            'notifications':dict(_notification_settings)}
    try:

        with open(path,'w',encoding='utf-8') as f: json.dump(data,f,indent=2,ensure_ascii=False)

        _set_status('Saved!')

    except Exception as e: log(f'[AutoTrade] ❌ save error: {e}')



def _load_config():
    global _commands, _notification_settings
    path = _cfg_path()

    if not path or not os.path.exists(path): return

    try:

        with open(path,'r',encoding='utf-8') as f: data = json.load(f)

        _commands = data.get('commands',{})

        _refresh_list(); _refresh_cmd_comboboxes()

        pairs = data.get('pairs',[])

        for i,(town_tbx,pc,ps) in enumerate([(tbx_town1,tbx_pc1,tbx_ps1),(tbx_town2,tbx_pc2,tbx_ps2)]):

            if i<len(pairs):

                QtBind.setText(gui,town_tbx,pairs[i].get('town',''))

                QtBind.setText(gui,pc,pairs[i].get('cmd',''))

                QtBind.setText(gui,ps,pairs[i].get('scr',''))

        try: QtBind.setText(gui,tbx_death_scr,data.get('death_script',''))

        except: pass

        try: QtBind.setChecked(gui, chk_char_death, data.get('char_death_enabled', True))

        except: pass

        try: QtBind.setChecked(gui, chk_pet_death,  data.get('pet_death_enabled',  True))

        except: pass

        try: QtBind.setText(gui,cbx_pet,data.get('pet_name',''))

        except: pass

        try: QtBind.setText(gui,tbx_max_trips,data.get('limit_trade','0'))
        except: pass
        loaded_notifications = data.get('notifications', {})
        if isinstance(loaded_notifications, dict):
            for key in _notification_settings:
                if key in loaded_notifications:
                    _notification_settings[key] = loaded_notifications[key]
        _apply_notification_settings_to_gui()
        log(f'[AutoTrade] Loaded: {os.path.basename(path)}')
    except Exception as e: log(f'[AutoTrade] ❌ load error: {e}')

# ============================================================

#  Helpers

# ============================================================

def _set_status(txt):

    try: QtBind.setText(gui,lbl_status,str(txt))

    except: pass



def _set_pet_status(txt):
    try: QtBind.setText(gui,lbl_pet_status,str(txt))
    except: pass

def _set_notification_status(txt):
    try: QtBind.setText(gui, lbl_notification_status, str(txt))
    except: pass

def _apply_notification_settings_to_gui():
    try:
        QtBind.setChecked(gui, chk_notify_discord,
                          bool(_notification_settings['discord_enabled']))
        QtBind.setText(gui, tbx_notify_discord_webhook,
                       str(_notification_settings['discord_webhook']))
        QtBind.setChecked(gui, chk_notify_telegram,
                          bool(_notification_settings['telegram_enabled']))
        QtBind.setText(gui, tbx_notify_telegram_token,
                       str(_notification_settings['telegram_bot_token']))
        QtBind.setText(gui, tbx_notify_telegram_chat_id,
                       str(_notification_settings['telegram_chat_id']))
        QtBind.setChecked(gui, chk_notify_start_stop,
                          bool(_notification_settings['notify_start_stop']))
        QtBind.setChecked(gui, chk_notify_trips,
                          bool(_notification_settings['notify_trips']))
        QtBind.setChecked(gui, chk_notify_deaths,
                          bool(_notification_settings['notify_deaths']))
        QtBind.setChecked(gui, chk_notify_errors,
                          bool(_notification_settings['notify_errors']))
    except Exception:
        pass

def _discord_webhook_valid(url):
    url = (url or '').strip().lower()
    return (url.startswith('https://discord.com/api/webhooks/') or
            url.startswith('https://discordapp.com/api/webhooks/'))

def _telegram_credentials_valid(token, chat_id):
    token = (token or '').strip()
    chat_id = (chat_id or '').strip()
    return bool(token and ':' in token and chat_id)

def _notification_title():
    try:
        ch = get_character_data()
        if ch and ch.get('name'):
            return 'FAutoTrade - %s' % ch.get('name')
    except Exception:
        pass
    return 'FAutoTrade'

def _send_discord_worker(webhook, title, message):
    try:
        payload = json.dumps({
            'username': 'FAutoTrade',
            'embeds': [{
                'title': title,
                'description': message,
                'color': 15158332,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            }]
        }).encode('utf-8')
        request = urllib.request.Request(
            webhook, data=payload,
            headers={'Content-Type': 'application/json',
                     'User-Agent': 'FAutoTrade/2.1'},
            method='POST')
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read(1)
    except Exception as error:
        # Never include exception text: HTTP errors may expose credential URLs.
        log('[FAutoTrade] Discord notification failed (%s).' %
            type(error).__name__)

def _send_telegram_worker(token, chat_id, title, message):
    try:
        url = 'https://api.telegram.org/bot%s/sendMessage' % token
        payload = urllib.parse.urlencode({
            'chat_id': chat_id,
            'text': '%s\n%s' % (title, message),
            'disable_web_page_preview': 'true'
        }).encode('utf-8')
        request = urllib.request.Request(
            url, data=payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded',
                     'User-Agent': 'FAutoTrade/2.1'},
            method='POST')
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read(1)
    except Exception as error:
        # The Telegram token is part of the URL, so only log the error type.
        log('[FAutoTrade] Telegram notification failed (%s).' %
            type(error).__name__)

def _queue_notification(message, event='errors', force_discord=False,
                        force_telegram=False):
    option_key = {
        'start_stop': 'notify_start_stop',
        'trips': 'notify_trips',
        'deaths': 'notify_deaths',
        'errors': 'notify_errors'
    }.get(event, 'notify_errors')

    with _notification_lock:
        settings = dict(_notification_settings)
        if not force_discord and not force_telegram:
            if not settings.get(option_key, True):
                return False
            dedupe_key = '%s:%s' % (event, message)
            now = time.time()
            if now - _notification_last_sent.get(dedupe_key, 0) < 3:
                return False
            _notification_last_sent[dedupe_key] = now

    title = _notification_title()
    queued = False
    webhook = settings.get('discord_webhook', '').strip()
    token = settings.get('telegram_bot_token', '').strip()
    chat_id = settings.get('telegram_chat_id', '').strip()

    if ((force_discord or
         (settings.get('discord_enabled') and not force_telegram)) and
            _discord_webhook_valid(webhook)):
        threading.Thread(target=_send_discord_worker,
                         args=(webhook, title, message), daemon=True).start()
        queued = True
    if ((force_telegram or
         (settings.get('telegram_enabled') and not force_discord)) and
            _telegram_credentials_valid(token, chat_id)):
        threading.Thread(target=_send_telegram_worker,
                         args=(token, chat_id, title, message), daemon=True).start()
        queued = True
    return queued

def show_notifications_cb():
    _apply_notification_settings_to_gui()
    for widget, x, y in _notification_widgets:
        QtBind.move(gui, widget, x, y)
    _set_notification_status('Settings are stored per character.')

def hide_notifications_cb():
    for widget, x, y in _notification_widgets:
        QtBind.move(gui, widget, _NOTIFY_OFFSCREEN_X, y)

def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        _set_status('Opening Discord invite...')
    except Exception as error:
        log('[%s] Discord link error: %s' % (pName, error))
        _set_status('Could not open Discord invite')

def notification_setting_changed_cb(checked=False):
    _set_notification_status('Unsaved changes.')

def _read_notification_settings_from_gui():
    webhook = QtBind.text(gui, tbx_notify_discord_webhook).strip()
    token = QtBind.text(gui, tbx_notify_telegram_token).strip()
    chat_id = QtBind.text(gui, tbx_notify_telegram_chat_id).strip()
    discord_enabled = QtBind.isChecked(gui, chk_notify_discord)
    telegram_enabled = QtBind.isChecked(gui, chk_notify_telegram)

    if discord_enabled and not _discord_webhook_valid(webhook):
        _set_notification_status('Enter a valid Discord webhook URL.')
        return False
    if telegram_enabled and not _telegram_credentials_valid(token, chat_id):
        _set_notification_status('Enter a valid Telegram token and Chat ID.')
        return False

    with _notification_lock:
        _notification_settings.update({
            'discord_enabled': discord_enabled,
            'discord_webhook': webhook,
            'telegram_enabled': telegram_enabled,
            'telegram_bot_token': token,
            'telegram_chat_id': chat_id,
            'notify_start_stop': QtBind.isChecked(gui, chk_notify_start_stop),
            'notify_trips': QtBind.isChecked(gui, chk_notify_trips),
            'notify_deaths': QtBind.isChecked(gui, chk_notify_deaths),
            'notify_errors': QtBind.isChecked(gui, chk_notify_errors),
        })
    return True

def save_notification_settings_cb():
    if not _read_notification_settings_from_gui():
        return
    _save_config()
    _set_notification_status('Notification settings saved.')

def test_discord_notification_cb():
    webhook = QtBind.text(gui, tbx_notify_discord_webhook).strip()
    if not _discord_webhook_valid(webhook):
        _set_notification_status('Enter a valid Discord webhook URL.')
        return
    with _notification_lock:
        _notification_settings['discord_webhook'] = webhook
    _queue_notification('Discord test notification is working.',
                        force_discord=True)
    _set_notification_status('Discord test queued.')

def test_telegram_notification_cb():
    token = QtBind.text(gui, tbx_notify_telegram_token).strip()
    chat_id = QtBind.text(gui, tbx_notify_telegram_chat_id).strip()
    if not _telegram_credentials_valid(token, chat_id):
        _set_notification_status('Enter a valid Telegram token and Chat ID.')
        return
    with _notification_lock:
        _notification_settings['telegram_bot_token'] = token
        _notification_settings['telegram_chat_id'] = chat_id
    _queue_notification('Telegram test notification is working.',
                        force_telegram=True)
    _set_notification_status('Telegram test queued.')

def _get_hwnd():
    try:

        c=get_client()

        if c and c.get('window') and c['window']!=0: return c['window']

    except: pass

    try:

        h=user32.FindWindowW('Silkroad Online Application',None)

        if h: return h

    except: pass

    return None



def _make_lparam(x,y): return (y<<16)|(x&0xFFFF)



def _post_click_no_ctrl(hwnd, x, y):

    pt = ctypes.wintypes.POINT(x, y)

    user32.ScreenToClient(hwnd, ctypes.byref(pt))

    lp = _make_lparam(pt.x, pt.y)

    user32.PostMessageW(hwnd, WM_MOUSEMOVE,   0,         lp)

    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)

    time.sleep(0.05)

    user32.PostMessageW(hwnd, WM_LBUTTONUP,   0,         lp)



def _capture_pos(num,tbx_x,tbx_y):

    _set_status(f'Move mouse to Click {num}... (3s)')

    time.sleep(3)

    try:

        pt=ctypes.wintypes.POINT(); user32.GetCursorPos(ctypes.byref(pt))

        QtBind.setText(gui,tbx_x,str(pt.x)); QtBind.setText(gui,tbx_y,str(pt.y))

        _set_status(f'Click {num}: {pt.x},{pt.y}')

        log(f'[AutoTrade] Click {num}: x={pt.x} y={pt.y}')

    except Exception as e: log(f'[AutoTrade] cap error: {e}')



def _refresh_list():

    try:

        QtBind.clear(gui,lst_cmds)

        for cmd,entry in _commands.items():

            n=len([c for c in entry.get('clicks',[]) if c['x']!=0 or c['y']!=0])

            QtBind.append(gui,lst_cmds,f"{cmd}  [{n} clicks] NPC:{entry.get('npc','—')}")

    except: pass



def _form_to_entry():

    clicks = []

    for tx, ty, td, tr in _CLICK_FIELDS:

        try:

            clicks.append({

                'x': int(QtBind.text(gui, tx)),

                'y': int(QtBind.text(gui, ty)),

                'd': float(QtBind.text(gui, td)),

                'r': max(1, int(QtBind.text(gui, tr)))

            })

        except:

            clicks.append({'x': 0, 'y': 0, 'd': 1.0, 'r': 1})

    try:

        npc_stop_x = int(QtBind.text(gui, tbx_npc_x))

        npc_stop_y = int(QtBind.text(gui, tbx_npc_y))

    except:

        npc_stop_x = npc_stop_y = 0

    return {

        'npc': QtBind.text(gui, tbx_npc).strip(),

        'npc_stop_x': npc_stop_x,

        'npc_stop_y': npc_stop_y,

        'clicks': clicks

    }



def _entry_to_form(entry):

    QtBind.setText(gui, tbx_npc, entry.get('npc', ''))

    try: QtBind.setText(gui, tbx_npc_x, str(entry.get('npc_stop_x', 0)))

    except: pass

    try: QtBind.setText(gui, tbx_npc_y, str(entry.get('npc_stop_y', 0)))

    except: pass

    for i, c in enumerate(entry.get('clicks', [])):

        if i >= len(_CLICK_FIELDS): break

        tx, ty, td, tr = _CLICK_FIELDS[i]

        QtBind.setText(gui, tx, str(c.get('x', 0)))

        QtBind.setText(gui, ty, str(c.get('y', 0)))

        QtBind.setText(gui, td, str(c.get('d', 1.0)))

        QtBind.setText(gui, tr, str(c.get('r', 1)))



# ============================================================

#  Cap + GUI Callbacks

# ============================================================


def _make_cap_cb(num, tx, ty):

    def _cb():

        threading.Thread(target=_capture_pos, args=(num, tx, ty), daemon=True).start()

    _cb.__name__ = f'btn_cap{num}_cb'

    return _cb



btn_cap1_cb = _make_cap_cb(1, tbx_x1, tbx_y1)

btn_cap2_cb = _make_cap_cb(2, tbx_x2, tbx_y2)

btn_cap3_cb = _make_cap_cb(3, tbx_x3, tbx_y3)

btn_cap4_cb = _make_cap_cb(4, tbx_x4, tbx_y4)

btn_cap5_cb = _make_cap_cb(5, tbx_x5, tbx_y5)

btn_cap6_cb = _make_cap_cb(6, tbx_x6, tbx_y6)

btn_cap7_cb = _make_cap_cb(7, tbx_x7, tbx_y7)

btn_cap8_cb = _make_cap_cb(8, tbx_x8, tbx_y8)



def _capture_game_pos(tbx_x, tbx_y):


    _set_status('Reading in-game position...')

    try:

        pos = get_position()

        if pos:

            gx = int(pos.get('x', 0))

            gy = int(pos.get('y', 0))

            QtBind.setText(gui, tbx_x, str(gx))

            QtBind.setText(gui, tbx_y, str(gy))

            _set_status(f'NPC Stop pos: {gx},{gy}')

        else:

            _set_status('Not in game!')

    except Exception as e:

        log(f'[AutoTrade] cap_game_pos error: {e}')



def btn_cap_npc_cb():

    threading.Thread(target=_capture_game_pos, args=(tbx_npc_x, tbx_npc_y), daemon=True).start()

def btn_auto_start_cb():

    global _pair_running, _auto_running, _trips_done, _last_transport_seen, _teleport_time, _transport_missing_count

    if _auto_running:

        return


    _trips_done = 0

    try: QtBind.setText(gui, lbl_trips_done, '0')

    except: pass


    _last_transport_seen     = time.time()

    _teleport_time           = time.time()

    _transport_missing_count = 0

    _auto_running = True

    _pair_running = False

    try:

        import phBotChat

        phBotChat.ClientNotice('AutoTrade Made by FascinaTe discord: mrfascinate')

    except: pass

    pairs = _get_pairs()

    if not pairs:

        _set_status('No pairs configured!')

        _auto_running = False

        return


    current_town = _get_current_town()

    matched_idx = 0

    for i, (town, cmd, scr) in enumerate(pairs):

        if town and (town in current_town or current_town in town):

            matched_idx = i

            break

    log(f'[AutoTrade] Auto Start → pair {matched_idx + 1} (town="{current_town}")')

    _set_status('Auto Start!')
    _queue_notification('AutoTrade started (pair %s).' % (matched_idx + 1),
                        'start_stop')
    threading.Thread(target=_run_pair, args=(matched_idx,), daemon=True).start()



def _stop_auto_action():

    global _pair_running, _auto_running, _bot_was_running, _stop_flag

    global _pet_death_triggered, _transport_died_flag, _was_auto_running, _death_triggered

    global _transport_missing_count, _running, _script_pause_flag, _pending_pair_idx

    global _npc_triggered_cmd, _death_script_running




    _auto_running            = False

    _was_auto_running        = False

    _pair_running            = False

    _bot_was_running         = False

    _stop_flag               = True

    _running                 = False

    _pet_death_triggered     = False

    _transport_died_flag     = False

    _death_triggered         = False

    _death_script_running    = False

    _transport_missing_count = 0

    _script_pause_flag       = False

    _pending_pair_idx        = -1

    _resurrecting            = False



    _set_status('⏹️ Stopped.')




    def _bg_stop():

        global _stop_flag




        _party_members_before = []

        try:

            pm = get_party()

            if pm:

                for mid, mdata in pm.items():

                    n = mdata.get('name', '')

                    if n:

                        _party_members_before.append(n)

        except: pass




        try: stop_bot()

        except Exception as e: log(f'[AutoTrade] stop_bot error: {e}')




        try: inject_joymax(0x704B, b'\x92\x00\x00\x00', False)

        except: pass




        time.sleep(0.3)

        _stop_flag = False



        log('[AutoTrade] ⏹️ Auto Stop — everything halted.')
        _queue_notification('AutoTrade stopped.', 'start_stop')



        if _party_members_before:

            time.sleep(3)

            try:

                pm_after = get_party()

                current = set()

                if pm_after:

                    for mid, mdata in pm_after.items():

                        current.add(mdata.get('name', ''))

                missing = [m for m in _party_members_before if m not in current]

                if missing:

                    log(f'[AutoTrade] ⚠️ Party left after stop: {missing}')

                    _set_status('Stopped. ⚠️ Party left — disable "Leave Party on Stop" in phBot!')

            except: pass



    threading.Thread(target=_bg_stop, daemon=True).start()



def btn_refresh_scripts_cb():

    _refresh_scripts_comboboxes()

    _refresh_cmd_comboboxes()

    _refresh_death_scripts()

    _set_status('Refreshed!')



def btn_load_pets_g1_cb():


    _populate_pet_combobox()

    _set_status('Pets loaded!')




_KNOWN_NPCS = [

    'Specialty Trader Jodaesan',

    'Specialty Shop Elder Leegak',

    'Specialty Trader Sanmok',

]



def _refresh_npc_combobox():

    try:

        cur = QtBind.text(gui, tbx_npc)

        QtBind.clear(gui, tbx_npc)

        QtBind.append(gui, tbx_npc, '')

        added = set()

        for n in _KNOWN_NPCS:

            QtBind.append(gui, tbx_npc, n)

            added.add(n.lower())

        try:

            npcs = get_npcs()

            if npcs:

                for npc_id, info in npcs.items():

                    name = info.get('name', '')

                    sname = info.get('servername', '').upper()

                    if not name: continue

                    if any(x in sname for x in ('GATE','WAREHOUSE','STORAGE')): continue

                    if name.lower() not in added:

                        QtBind.append(gui, tbx_npc, name)

                        added.add(name.lower())

        except: pass

        if cur: QtBind.setText(gui, tbx_npc, cur)

    except: pass



def chk_char_death_cb(checked=False):

    _save_config()



def chk_pet_death_cb(checked=False):

    _save_config()



def btn_load_npcs_cb():

    _refresh_npc_combobox()

    _set_status('NPCs loaded!')



def _refresh_death_scripts():

    _refill_combobox(tbx_death_scr, _get_available_scripts())



def _set_death_status(txt):

    try: QtBind.setText(gui, lbl_death_status, str(txt))

    except: pass



def btn_save_pairs_cb():

    _save_config()

    _auto_append_par_to_scripts()



def _auto_append_par_to_scripts():


    try:

        pairs = _get_pairs()

        total = len(pairs)

        if total == 0: return

        for i, (town, cmd, scr) in enumerate(pairs):

            if not scr: continue

            scr_path = _resolve_script_path(scr)

            if not scr_path or not os.path.exists(scr_path): continue

            next_idx = (i + 1) % total

            par_line = f'par,{next_idx + 1}'

            with open(scr_path, 'r', encoding='utf-8', errors='ignore') as f:

                content = f.read()


            clean_lines = [l for l in content.splitlines() if not l.strip().lower().startswith('par,')]


            result = '\n'.join(clean_lines).rstrip() + f'\n{par_line}\n'

            with open(scr_path, 'w', encoding='utf-8') as f:

                f.write(result)

        _set_status('Saved + Scripts updated!')

    except Exception as e:

        log(f'[AutoTrade] _auto_append_par error: {e}')



def btn_add_cb():

    cmd = QtBind.text(gui, tbx_cmd).strip().lower()

    if not cmd: _set_status('Enter command!'); return

    _commands[cmd] = _form_to_entry()

    _refresh_list(); _refresh_cmd_comboboxes(); _save_config()

    _set_status(f'Saved: {cmd}')



def btn_del_cb():

    try:

        idx = QtBind.currentIndex(gui, lst_cmds)

        keys = list(_commands.keys())

        if idx < 0 or idx >= len(keys): return

        del _commands[keys[idx]]

        _refresh_list(); _refresh_cmd_comboboxes(); _save_config()

    except: pass



def lst_cmds_cb(v):

    try:

        idx=QtBind.currentIndex(gui,lst_cmds); keys=list(_commands.keys())

        if idx<0 or idx>=len(keys): return

        cmd=keys[idx]; QtBind.setText(gui,tbx_cmd,cmd); _entry_to_form(_commands[cmd])

    except: pass



def btn_edit_cmd_cb():


    try:

        idx = QtBind.currentIndex(gui, lst_cmds)

        keys = list(_commands.keys())

        if idx < 0 or idx >= len(keys):

            _set_status('Select a command first!')

            return

        cmd = keys[idx]

        QtBind.setText(gui, tbx_cmd, cmd)

        _entry_to_form(_commands[cmd])

        _set_status(f'Editing: {cmd}')

    except Exception as e:

        log(f'[AutoTrade] ❌ btn_edit_cmd_cb error: {e}')



# ============================================================

#  Run Logic

# ============================================================

def _do_run(cmd_name):

    global _running, _stop_flag

    cmd = cmd_name.strip().lower()

    if cmd not in _commands:

        log(f'[AutoTrade] Not found: {cmd}'); return

    if _running: return

    entry      = _commands[cmd]

    npc_filter = entry.get('npc','').lower()

    clicks_raw = entry.get('clicks',[])

    hwnd       = _get_hwnd()

    if not hwnd: _set_status('No game window!'); return

    _stop_flag = False

    _running   = True



    def _run():

        global _running, _stop_flag


        try:

            pet_name = QtBind.text(gui, cbx_pet).strip() if cbx_pet else ''

            if pet_name and not _pet_get_active():

                _set_pet_status('Summoning...')

                ok = _pet_summon_with_retry(max_tries=3, wait=5)

                _set_pet_status('Active' if ok else 'Failed')

        except Exception as e:

            log(f'[AutoTrade] pet check error: {e}')



        # ── Walk to NPC (stop near NPC, not on top of it) ──

        try:

            npcs = get_npcs()

            if npcs and npc_filter:

                for npc_id, info in npcs.items():

                    name  = info.get('name','').lower()

                    sname = info.get('servername','').upper()

                    if npc_filter not in name: continue

                    if any(x in sname for x in ('GATE','WAREHOUSE','STORAGE')): continue

                    nx, ny = info.get('x',0), info.get('y',0)




                    npc_stop_x = entry.get('npc_stop_x', 0)

                    npc_stop_y = entry.get('npc_stop_y', 0)

                    if npc_stop_x != 0 or npc_stop_y != 0:

                        tx, ty = npc_stop_x, npc_stop_y

                    else:


                        _STOP_DIST = 120

                        try:

                            cur_pos = get_position()

                            if cur_pos:

                                cx, cy = cur_pos.get('x', nx), cur_pos.get('y', ny)

                                dx, dy = nx - cx, ny - cy

                                dist = (dx**2 + dy**2) ** 0.5

                                if dist > _STOP_DIST:

                                    ratio = (dist - _STOP_DIST) / dist

                                    tx = int(cx + dx * ratio)

                                    ty = int(cy + dy * ratio)

                                else:

                                    tx, ty = cx, cy

                            else:

                                tx, ty = nx, ny

                        except:

                            tx, ty = nx, ny



                    _set_status(f'Walking near {info.get("name")}...')

                    move_to(tx, ty, 0)


                    dl = time.time() + 30

                    while time.time() < dl:

                        pos = get_position()

                        if pos:

                            px, py = pos.get('x',0), pos.get('y',0)


                            if abs(px - tx) < 80 and abs(py - ty) < 80: break


                            if abs(px - nx) < 150 and abs(py - ny) < 150: break

                        time.sleep(0.5)

                    time.sleep(0.5)

                    inject_joymax(0x7045, struct.pack('<I',npc_id), False)

                    time.sleep(5)

                    break

        except Exception as e: log(f'[AutoTrade] walk error: {e}')



        # ── Clicks ──

        def _do_group(start, end):


            for _repeat in range(2):

                for c in clicks_raw[start:end]:

                    if _stop_flag or not _running: return

                    x, y, d, r = c['x'], c['y'], c.get('d', 1.0), c.get('r', 1)

                    if x == 0 and y == 0: continue

                    for _ in range(r):

                        if _stop_flag or not _running: return

                        _post_click_no_ctrl(hwnd, x, y)

                        time.sleep(d)



        _set_status(f'Clicking ({cmd})...')

        _block_input(True)

        try:

            for (gs, ge) in _CLICK_GROUPS:

                if _stop_flag or not _running: break


                group_clicks = clicks_raw[gs:ge]

                if any(c['x'] != 0 or c['y'] != 0 for c in group_clicks):

                    _do_group(gs, ge)

        finally:

            _block_input(False)




        for _ in range(3):

            try: inject_joymax(0x704B, b'\x92\x00\x00\x00', False)

            except: pass

            time.sleep(0.3)

        _running   = False

        _stop_flag = False

        _set_status('Done')



    threading.Thread(target=_run, daemon=True).start()



# ============================================================

#  Script Pairs

# ============================================================

def _get_pairs():

    pairs = []

    for town_tbx,pc,ps in [(tbx_town1,tbx_pc1,tbx_ps1),(tbx_town2,tbx_pc2,tbx_ps2)]:

        try:

            town = QtBind.text(gui,town_tbx).strip().lower()

            cmd  = QtBind.text(gui,pc).strip().lower()

            scr  = QtBind.text(gui,ps).strip()

            if cmd and scr: pairs.append((town,cmd,scr))

        except: pass

    return pairs



def _resolve_script_path(scr):


    plugin_dir = os.path.dirname(os.path.realpath(__file__))

    candidates = [

        scr,

        os.path.join(plugin_dir, 'scripts', scr),

        os.path.join(plugin_dir, 'Scripts', scr),

        os.path.join(plugin_dir, 'AutoTrade', 'Script', scr),

    ]


    try:

        cfg = get_config_dir()

        if cfg:

            candidates.append(os.path.join(cfg, 'Scripts', scr))

            candidates.append(os.path.join(cfg, 'scripts', scr))

            candidates.append(cfg + 'Scripts\\' + scr)

    except:

        pass

    for p in candidates:

        try:

            if os.path.exists(p):

                return p

        except:

            pass

    return None



def _run_pair(idx):

    global _current_pair, _pair_running, _bot_was_running, _running, _stop_flag, _bot_start_time

    with _pair_lock:

        if _pair_running:

            return

        _pair_running = True



    try:


        _stop_flag = True

        deadline   = time.time() + 3

        while _running and time.time() < deadline:

            time.sleep(0.1)

        _running   = False

        _stop_flag = False



        if not _auto_running:

            _pair_running = False

            return



        pairs = _get_pairs()

        if not pairs:

            _pair_running = False

            return

        idx           = idx % len(pairs)

        _current_pair = idx

        town, cmd, scr = pairs[idx]

        log(f'[AutoTrade] Pair {idx+1}: town="{town}" cmd="{cmd}" scr="{scr}"')

        _set_status(f'Pair {idx+1}: {cmd}...')

        _bot_start_time = time.time()



        _do_run(cmd)

        dl = time.time() + 120

        while _running and time.time() < dl:

            if not _auto_running:

                _pair_running = False

                return

            time.sleep(0.5)




        if not _auto_running:

            _pair_running = False

            return



        time.sleep(1)




        if not _auto_running:

            _pair_running = False

            return



        scr_path = _resolve_script_path(scr)

        if not scr_path:

            log(f'[AutoTrade] Script not found: {scr}')
            _queue_notification('Training script was not found: %s' % scr,
                                'errors')
            _pair_running = False

            return



        log(f'[AutoTrade] Starting script "{scr}"')

        try:

            set_training_script(scr_path)

            _bot_was_running = True

            _bot_start_time  = time.time()

            start_bot()

            _set_status(f'Bot started: {scr}')

        except Exception as e:

            log(f'[AutoTrade] start error: {e}')
            _queue_notification('Training script could not be started: %s' % scr,
                                'errors')
            _bot_was_running = False

            _pair_running    = False

            return



        _pair_running = False



    except Exception as e:

        log(f'[AutoTrade] _run_pair error: {e}')

        _pair_running = False



def bot_stopped():

    global _pair_running, _bot_was_running, _was_auto_running, _pending_pair_idx, _script_pause_flag

    _bot_was_running  = False

    _pair_running     = False


    if _pending_pair_idx >= 0:

        return


    _was_auto_running = False



def script_finished():

    global _pair_running, _bot_was_running, _pet_death_triggered, _was_auto_running, _trips_done

    global _death_script_running


    _death_script_running = False

    if not _auto_running and not _was_auto_running:

        return


    if _pending_pair_idx >= 0:

        return

    _bot_was_running  = False

    _pair_running     = False

    _was_auto_running = False




    _trips_done += 1
    try: QtBind.setText(gui, lbl_trips_done, str(_trips_done))
    except: pass
    _queue_notification('Trip #%s completed.' % _trips_done, 'trips')



    try:

        max_t = int(QtBind.text(gui, tbx_max_trips).strip()) if tbx_max_trips else 0

    except:

        max_t = 0

    if max_t > 0 and _trips_done >= max_t:

        log(f'[AutoTrade] ✅ Reached {_trips_done}/{max_t} trips → Auto Stop!')
        _queue_notification(
            'Trade limit reached: %s/%s trips.' % (_trips_done, max_t), 'trips')
        _set_status(f'Done! {_trips_done} trips completed.')

        _stop_auto_action()

        return



    def _check_and_restart():

        global _pet_death_triggered

        try: set_training_script('')

        except: pass

        time.sleep(2)



        pairs = _get_pairs()

        if not pairs: return



        next_idx = (_current_pair + 1) % len(pairs)

        next_town, next_cmd, next_scr = pairs[next_idx]




        transport_died = _transport_died_flag



        scr_death = ''

        try:

            scr_death = QtBind.text(gui, tbx_death_scr).strip()

        except:

            pass



        if transport_died and scr_death:

            log(f'[AutoTrade] Transport died → death script: {scr_death}')

            _set_death_status(f'Transport died → starting: {scr_death}')

            _pet_death_triggered = False

            time.sleep(3)

            scr_path = _resolve_script_path(scr_death)

            if scr_path:

                try:

                    set_training_script(scr_path)

                    start_bot()

                    log(f'[AutoTrade] Death script started: {scr_death}')

                    _set_death_status(f'Bot started: {scr_death}')

                except Exception as e:

                    log(f'[AutoTrade] death script error: {e}')

            return




        _pet_death_triggered = False

        _set_status(f'Waiting for {next_town}...')



        if next_town:

            deadline = time.time() + 90

            arrived  = False

            while time.time() < deadline:

                try:

                    current = _get_current_town()

                    if next_town in current or current in next_town:

                        arrived = True

                        break

                except: pass

                time.sleep(2)

            if not arrived:

                log(f'[AutoTrade] Timeout waiting for "{next_town}" — starting Pair {next_idx+1} anyway')



        time.sleep(3)

        if not _auto_running: return

        threading.Thread(target=_run_pair, args=(next_idx,), daemon=True).start()



    threading.Thread(target=_check_and_restart, daemon=True).start()



def _get_current_town():


    try:

        pos = get_position()

        if not pos: return ''

        region = pos.get('region', 0)

        if not region: return ''


        try:

            name = get_zone_name(region)

            return name.lower() if name else ''

        except:

            pass


        return {

            25000: 'jangan', 25257: 'donwhang',

            25514: 'hotan',  24832: 'samarkand',

        }.get(region, '')

    except:

        return ''



def handle_joymax(opcode, data):

    global _gate_crossing, _teleport_time, _script_teleport_time, _script_teleporting

    global _death_triggered, _resurrecting, _was_auto_running

    global _auto_running, _bot_was_running, _pair_running



    if opcode == 0x30BF:

        if not data or data[-1] != 0x02: return True

        if _resurrecting: return True

        if not _auto_running and not _bot_was_running and not _pair_running: return True

        if time.time() - _script_teleport_time < 30: return True


        try:

            if chk_char_death and not QtBind.isChecked(gui, chk_char_death): return True

        except: pass

        try:

            ch = get_character_data()

            if ch:

                char_id   = ch.get('player_id', -1)

                packet_id = int.from_bytes(data[:4], 'little')

                if char_id != -1 and packet_id != char_id: return True

        except: pass



        scr = ''

        try: scr = QtBind.text(gui, tbx_death_scr).strip()

        except: pass

        _death_triggered  = True

        _was_auto_running = _auto_running or _bot_was_running or _pair_running

        _auto_running     = False

        _bot_was_running  = False

        _pair_running     = False



        def _char_death_joymax(_scr=scr):

            global _resurrecting, _death_script_running, _auto_running, _bot_was_running, _death_triggered

            try:

                if _stop_flag: return

                _resurrecting = True

                log('[AutoTrade] Died → starting death sequence')
                _queue_notification(
                    'Character died; recovery sequence started.', 'deaths')
                _set_death_status('Died — starting death sequence...')

                try: inject_joymax(0x3053, b'\x01', True)

                except: pass

                try: stop_bot()

                except: pass

                time.sleep(2)

                if _stop_flag: return

                if _scr:

                    scr_path = _resolve_script_path(_scr)

                    if scr_path:

                        set_training_script(scr_path)

                        _death_script_running = True

                        _auto_running         = True

                        _bot_was_running      = True

                        start_bot()

                        log(f'[AutoTrade] Death script started: {_scr}')
                        _queue_notification(
                            'Character recovery script started: %s' % _scr,
                            'deaths')
                        _set_death_status(f'Bot started: {_scr}')

                    else:
                        log(f'[AutoTrade] Death script not found: {_scr}')
                        _queue_notification(
                            'Recovery script was not found: %s' % _scr,
                            'errors')
                        threading.Thread(target=btn_auto_start_cb, daemon=True).start()

                else:

                    threading.Thread(target=btn_auto_start_cb, daemon=True).start()

            except Exception as e:

                log(f'[AutoTrade] ❌ char death error: {e}')

            finally:

                _death_triggered      = False

                _death_script_running = False

                _resurrecting         = False



        threading.Thread(target=_char_death_joymax, daemon=True).start()



    return True



# ============================================================

#  Chat + Script Commands

# ============================================================

def handle_chat(t, player, msg):

    if not msg: return

    global _pair_running, _bot_was_running


    try:

        me = get_character_data()

        if me and player and player.strip().lower() != me.get('name','').strip().lower():

            return

    except: pass

    cmd = msg.strip().lower()



    if cmd == 'next_pair':

        if _auto_running:

            _bot_was_running = False

            _pair_running    = False

            pairs = _get_pairs()

            if pairs:

                next_idx = (_current_pair + 1) % len(pairs)

                def _delayed_next(_idx=next_idx):

                    try: stop_bot()

                    except: pass

                    time.sleep(1)

                    threading.Thread(target=_run_pair, args=(_idx,), daemon=True).start()

                threading.Thread(target=_delayed_next, daemon=True).start()

        return



    # par 1, par 2...

    if cmd.startswith('par ') and cmd[4:].isdigit():

        idx = int(cmd[4:]) - 1

        _pair_running = False

        pairs = _get_pairs()

        if pairs and 0 <= idx < len(pairs):

            def _delayed_pair(_idx=idx):

                try: stop_bot()

                except: pass

                time.sleep(3)

                threading.Thread(target=_run_pair, args=(_idx,), daemon=True).start()

            threading.Thread(target=_delayed_pair, daemon=True).start()

        return



    if cmd in _commands:

        def _chat_run(_cmd=cmd):

            try: stop_bot()

            except: pass

            time.sleep(1.0)

            _do_run(_cmd)

            deadline = time.time() + 5

            while not _running and time.time() < deadline:

                time.sleep(0.2)

            deadline = time.time() + 120

            while _running and time.time() < deadline:

                time.sleep(0.5)

            _set_status('Starting bot...')

            try:

                start_bot()

                _set_status('Bot started!')

            except Exception as e:

                log(f'[AutoTrade] start error: {e}')

        threading.Thread(target=_chat_run, daemon=True).start()



def handle_script(command, args):

    global _pair_running, _bot_was_running, _script_pause_flag, _teleport_time, _transport_missing_count

    global _script_teleporting, _script_teleport_time, _last_transport_seen



    cmd = command.strip().lower()




    if cmd == 'teleporting' or 'teleport' in cmd:

        global _teleporting_now, _gate_crossing, _gold_before_teleport

        _teleport_time           = time.time()

        _script_teleport_time    = time.time()

        _script_teleporting      = True

        _last_transport_seen     = time.time()

        _transport_missing_count = 0

        _teleporting_now         = True

        _gate_crossing           = True


        try:

            ch = get_character_data()

            _gold_before_teleport = ch.get('gold', -1) if ch else -1

        except:

            _gold_before_teleport = -1


        def _clear_teleporting():

            global _teleporting_now, _script_teleporting

            time.sleep(15)

            _teleporting_now   = False

            _script_teleporting = False

        threading.Thread(target=_clear_teleporting, daemon=True).start()

        return False



    # ── stuck recovery — reset missing counter ──

    if 'stuck' in cmd:

        _last_transport_seen     = time.time()

        _transport_missing_count = 0






    # ── pause ──

    if cmd == 'pause':

        _script_pause_flag = True

        return True




    if cmd in ('nextpar', 'next', 'next_pair'):

        if _auto_running:

            _script_pause_flag = True

            _bot_was_running   = False

            _pair_running      = False

            pairs = _get_pairs()

            if pairs:


                target_idx = (_current_pair + 1) % len(pairs)

                if cmd == 'nextpar' and args and args[0].strip().isdigit():

                    target_idx = (int(args[0].strip()) - 1) % len(pairs)

                elif cmd == 'next' and args and args[0].strip().lower() == 'par':

                    if len(args) >= 2 and args[1].strip().isdigit():

                        target_idx = int(args[1].strip()) - 1

                    target_idx = target_idx % len(pairs)

                def _go_next(_idx=target_idx):

                    try: stop_bot()

                    except: pass

                    time.sleep(1)

                    if _auto_running:

                        threading.Thread(target=_run_pair, args=(_idx,), daemon=True).start()

                threading.Thread(target=_go_next, daemon=True).start()

        return True



    # ── direct command ──

    if cmd in _commands:

        threading.Thread(target=_do_run, args=(cmd,), daemon=True).start()

        return True



    return False



# ── Script command: par <n> ─────────────────────────────────

def par(arguments):


    global _pair_running, _bot_was_running, _script_pause_flag, _auto_running, _pending_pair_idx, _trips_done

    try:

        idx_str = ''

        for a in arguments:

            if a.strip().isdigit():

                idx_str = a.strip()

                break

        if not idx_str:

            log(f'[AutoTrade] par: no digit found in arguments {arguments}')

            return 0

        idx = int(idx_str) - 1

        pairs = _get_pairs()

        if not pairs or idx < 0 or idx >= len(pairs):

            log(f'[AutoTrade] par {idx+1}: invalid pair index')

            return 0




        _trips_done += 1
        try: QtBind.setText(gui, lbl_trips_done, str(_trips_done))
        except: pass
        log(f'[AutoTrade] Trip #{_trips_done} done → par {idx+1}')
        _queue_notification(
            'Trip #%s completed; moving to pair %s.' % (_trips_done, idx + 1),
            'trips')



        try:

            max_t = int(QtBind.text(gui, tbx_max_trips).strip()) if tbx_max_trips else 0

        except:

            max_t = 0

        if max_t > 0 and _trips_done >= max_t:

            log(f'[AutoTrade] ✅ Reached {_trips_done}/{max_t} trips → Auto Stop!')
            _queue_notification(
                'Trade limit reached: %s/%s trips.' % (_trips_done, max_t),
                'trips')
            _set_status(f'Done! {_trips_done} trips completed.')

            threading.Thread(target=_stop_auto_action, daemon=True).start()

            return 0



        log(f'[AutoTrade] Script: par {idx+1} → waiting for bot stop then town arrival')

        _pending_pair_idx  = idx

        _auto_running      = True

        _script_pause_flag = True

        _pair_running      = False

        _bot_was_running   = False



        def _wait_and_run(_i=idx):

            global _pending_pair_idx, _script_pause_flag




            target_town = pairs[_i][0] if pairs and 0 <= _i < len(pairs) else ''

            deadline_stop = time.time() + 30

            while time.time() < deadline_stop:

                time.sleep(0.5)




                if not _bot_was_running:

                    break

            time.sleep(1)



            if not _auto_running:

                _pending_pair_idx  = -1

                _script_pause_flag = False

                return




            if target_town:

                log(f'[AutoTrade] par {_i+1}: waiting for town "{target_town}"...')

                _set_status(f'Waiting for {target_town}...')

                deadline_town = time.time() + 120

                arrived = False

                while time.time() < deadline_town:

                    if not _auto_running:

                        _pending_pair_idx  = -1

                        _script_pause_flag = False

                        return

                    try:

                        current = _get_current_town()

                        if target_town in current or current in target_town:

                            arrived = True

                            break

                    except:

                        pass

                    time.sleep(2)

                if not arrived:

                    log(f'[AutoTrade] par {_i+1}: timeout waiting for "{target_town}" — starting anyway')

                else:

                    log(f'[AutoTrade] par {_i+1}: arrived at "{target_town}"')



            time.sleep(2)



            _script_pause_flag = False

            _pending_pair_idx  = -1



            if _auto_running:

                threading.Thread(target=_run_pair, args=(_i,), daemon=True).start()



        threading.Thread(target=_wait_and_run, daemon=True).start()

    except Exception as e:

        log(f'[AutoTrade] ❌ par error: {e}')

    return 0



# ============================================================

#  phBot Events

# ============================================================

def joined_game():

    try:

        c = get_client()

        if c and c.get('window'):

            try: QtBind.setText(gui, lbl_window, str(c['window']))

            except: pass

        ch = get_character_data()

        if ch:

            try: QtBind.setText(gui, lbl_char, ch.get('name','—'))

            except: pass

    except: pass


    def _delayed_load():

        time.sleep(1.5)

        _load_config()

        _refresh_scripts_comboboxes()

        _refresh_death_scripts()

        _refresh_npc_combobox()

    threading.Thread(target=_delayed_load, daemon=True).start()


    def _fill_pet_combobox():

        time.sleep(3)

        _populate_pet_combobox()

    threading.Thread(target=_fill_pet_combobox, daemon=True).start()

    _set_status('Ready')

    log(f'[{pName}] v{pVersion} — Ready.')



# ============================================================




# ============================================================

_resurrecting = False



def _handle_death(scr_name, was_auto, wait_sec=5):


    global _resurrecting, _pet_death_triggered, _death_script_running

    global _auto_running, _bot_was_running, _transport_died_flag



    if _resurrecting:

        return

    _resurrecting = True



    def _run():

        global _resurrecting, _pet_death_triggered, _death_script_running

        global _auto_running, _bot_was_running, _transport_died_flag

        try:


            try: stop_bot()

            except: pass

            time.sleep(1)



            if _stop_flag or not _was_auto_running:

                _set_death_status('Stopped by user.')

                return




            log(f'[AutoTrade] Death detected — waiting {wait_sec}s...')

            _set_death_status(f'Died — waiting {wait_sec}s...')

            for _ in range(wait_sec * 2):

                if _stop_flag: return

                time.sleep(0.5)



            if _stop_flag:

                _set_death_status('Stopped by user.')

                return




            try:

                use_return_scroll()

                log('[AutoTrade] Return scroll used → waiting 5s...')

                _set_death_status('Return scroll used → waiting 5s...')

                for _ in range(10):

                    if _stop_flag: return

                    time.sleep(0.5)

                inject_joymax(0x3053, b'\x01', True)

            except:

                pass



            if _stop_flag:

                _set_death_status('Stopped by user.')

                return




            if not was_auto:

                _set_death_status('Stopped by user.')

                return



            if scr_name:

                scr_path = _resolve_script_path(scr_name)

                if scr_path:

                    try:

                        set_training_script(scr_path)

                        _death_script_running = True

                        _auto_running         = True

                        _bot_was_running      = True

                        start_bot()

                        log(f'[AutoTrade] Death script started: {scr_name}')

                        _set_death_status(f'Bot started: {scr_name}')

                    except Exception as e:
                        log(f'[AutoTrade] ❌ death script error: {e}')
                        _queue_notification(
                            'Recovery script could not be started: %s' %
                            scr_name, 'errors')
                        _auto_running = False

                else:

                    log(f'[AutoTrade] Death script not found: {scr_name}')

                    _auto_running = False

                    threading.Thread(target=btn_auto_start_cb, daemon=True).start()

            else:

                log('[AutoTrade] No death script → restarting auto...')

                _auto_running = False

                threading.Thread(target=btn_auto_start_cb, daemon=True).start()

        finally:

            _pet_death_triggered  = False

            _transport_died_flag  = False

            _death_script_running = False

            _resurrecting         = False



    threading.Thread(target=_run, daemon=True).start()





def teleported():

    global _teleport_time, _script_teleporting, _script_teleport_time, _gate_crossing

    _teleport_time        = time.time()

    _script_teleport_time = time.time()

    _script_teleporting   = False

    _gate_crossing        = False



def event_loop():

    pass



def handle_event(t, data):

    global _death_triggered, _pet_death_triggered

    global _bot_was_running, _pair_running, _auto_running

    global _transport_died_flag, _was_auto_running




    if t == 7:

        if _resurrecting: return

        # AutoTrade calisiyor mu? Calismiyorsa (elle PvP vb.) tamamen yoksay.

        # handle_joymax(0x30BF)'deki ile ayni guard - yoksa normal olumde de sehre donuyordu.

        if not _auto_running and not _bot_was_running and not _pair_running: return

        try:

            if not QtBind.isChecked(gui, chk_char_death): return

        except: return

        try: inject_joymax(0x3053, b'\x01', True)

        except: pass

        scr = ''

        try: scr = QtBind.text(gui, tbx_death_scr).strip()

        except: pass

        log('[AutoTrade] Died → starting death sequence')
        _queue_notification(
            'Character died; recovery sequence started.', 'deaths')
        _set_death_status('Died — starting death sequence...')

        _death_triggered  = True

        _was_auto_running = _auto_running

        _auto_running     = False

        _bot_was_running  = False

        _pair_running     = False

        _handle_death(scr, _was_auto_running, wait_sec=20)




    elif t == 3:

        if _resurrecting: return

        if _death_script_running: return


        try:

            if not QtBind.isChecked(gui, chk_pet_death):

                return

        except:

            return



        current_region = 0

        try:

            pos = get_position()

            if pos: current_region = pos.get('region', 0)

        except: pass



        def _confirm_transport_death(_region=current_region):

            global _pet_death_triggered, _transport_died_flag, _was_auto_running

            global _bot_was_running, _pair_running, _auto_running



            time.sleep(1.0)



            if not _auto_running or _death_script_running or _stop_flag or _transport_died_flag or _resurrecting:

                return



            try:

                pos = get_position()

                new_region = pos.get('region', 0) if pos else 0

                if new_region != _region and _region != 0:

                    return

            except: pass



            if not _auto_running and not _was_auto_running:

                return



            with _death_lock:

                if _pet_death_triggered or _transport_died_flag or _resurrecting:

                    return

                log('[AutoTrade] ⚡ Transport died → starting death sequence')
                _queue_notification(
                    'Transport died; recovery sequence started.', 'deaths')
                _set_death_status('Transport died → returning to town...')

                _pet_death_triggered = True

                _transport_died_flag = True

                _was_auto_running    = _auto_running

                _bot_was_running     = False

                _pair_running        = False

                _auto_running        = False



            scr = ''

            try: scr = QtBind.text(gui, tbx_death_scr).strip()

            except: pass

            _handle_death(scr, _was_auto_running, wait_sec=20)



        threading.Thread(target=_confirm_transport_death, daemon=True).start()





# ============================================================

#  Startup

# ============================================================

_load_config()

_refresh_scripts_comboboxes()

_refresh_death_scripts()

log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
