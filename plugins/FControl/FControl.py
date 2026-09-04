from phBot import *
import QtBind
import json
import os
from threading import Timer
import struct
import phBotChat
import random
import time
import webbrowser

pName = 'FControl'
pVersion = '1.9.1'
DISCORD_URL = 'https://discord.gg/eB9sGSMYBg'

plugin_dir = os.path.dirname(os.path.abspath(__file__))

# ______________________________ Initializing ______________________________ #
gui = QtBind.init(__name__, pName)
lblInject = QtBind.createLabel(gui, '<font color="#00d2ff"><b>⚜ Made By FascinaTe</b></font>', 4, 9)
btnDiscord = QtBind.createButton(gui, 'discord_clicked', u'\U0001f4ac Discord', 185, 5)

# QtBind does not expose native child tabs. As in FCaravanNavigator, pages are
# implemented by moving each page's widgets on/off screen.
OFFSCREEN_X = 3000
active_page = 'control'
control_widgets = []
buttons_widgets = []

btnControlPage = QtBind.createButton(gui, 'show_control_page', 'Control', 300, 5)
btnButtonsPage = QtBind.createButton(gui, 'show_buttons_page', 'Buttons', 370, 5)
btnLanguage = QtBind.createButton(gui, 'toggle_language', 'TR', 440, 5)

current_language = 'en'

GUI_TEXT = {
    'en': {
        'control': 'Control',
        'buttons': 'Buttons',
        'commands_title': 'Available Commands',
        'show_client_packets': 'Show Client Packets',
        'show_server_packets': 'Show Server Packets',
        'ignore_set_leader': 'Ignore SETFCONTROLLEADER command',
        'leaders': 'Leaders',
        'add': 'Add',
        'remove': 'Remove',
        'announce_tps': 'Auto-announce my own TPs',
        'announce_channel': 'Announce Channel:',
        'buttons_title': 'BUTTONS',
        'chat_type': 'Chat Type:',
        'job_suit_group': 'Job Suit',
        'equip_job': 'EQ Job',
        'unequip_job': 'UQ Job',
        'set_radius_group': 'Set Radius',
        'radius': 'Radius:',
        'set_radius': 'Set Radius',
        'set_profile_group': 'Set Profile',
        'profile_name': 'Profile Name:',
        'set_profile': 'Set Profile',
        'job_suit_initial': 'Send an automatic job suit command.',
        'radius_initial': 'Enter the training radius to send.',
        'radius_required': 'Enter a numeric radius first.',
        'sent_command': 'Sent on %s: %s',
        'send_failed': 'Could not send: %s',
        'profile_initial': 'Enter a phBot profile name.',
        'profile_required': 'Enter a profile name first.',
        'quick_control': 'Quick Control',
        'actions': 'Actions',
        'special': 'Special',
        'start': 'Start',
        'stop': 'Stop',
        'trace': 'Trace',
        'stop_trace': 'Stop Trace',
        'follow': 'Follow',
        'stop_follow': 'Stop Follow',
        'return': 'Return',
        'come': 'Come',
        'leave_party': 'Leave Party',
        'mount': 'Mount',
        'dismount': 'Dismount',
        'sit': 'Sit',
        'berserk': 'Berserk',
        'pick_all': 'Pick All',
        'stop_pick': 'Stop Pick',
        'sort': 'Sort',
        'repair': 'Repair',
        'storage': 'Storage',
        'clock': 'Clock',
        'devil_ext': 'Devil Ext',
        'quick_ready': 'Select a channel, then send a quick command.',
    },
    'tr': {
        'control': 'Kontrol',
        'buttons': 'Butonlar',
        'commands_title': 'Kullanılabilir Komutlar',
        'show_client_packets': 'İstemci Paketlerini Göster',
        'show_server_packets': 'Sunucu Paketlerini Göster',
        'ignore_set_leader': 'SETFCONTROLLEADER komutunu yok say',
        'leaders': 'Liderler',
        'add': 'Ekle',
        'remove': 'Kaldır',
        'announce_tps': 'Kendi ışınlanmalarımı otomatik duyur',
        'announce_channel': 'Duyuru Kanalı:',
        'buttons_title': 'BUTONLAR',
        'chat_type': 'Sohbet Türü:',
        'job_suit_group': 'Meslek Kıyafeti',
        'equip_job': 'EQ Job',
        'unequip_job': 'UQ Job',
        'set_radius_group': 'Radius Ayarla',
        'radius': 'Radius:',
        'set_radius': 'Radius Ayarla',
        'set_profile_group': 'Profil Ayarla',
        'profile_name': 'Profil Adı:',
        'set_profile': 'Profili Ayarla',
        'job_suit_initial': 'Otomatik meslek kıyafeti komutu gönderin.',
        'radius_initial': 'Gönderilecek training radius değerini girin.',
        'radius_required': 'Önce sayısal bir radius değeri girin.',
        'sent_command': '%s kanalında gönderildi: %s',
        'send_failed': 'Gönderilemedi: %s',
        'profile_initial': 'Bir phBot profil adı girin.',
        'profile_required': 'Önce bir profil adı girin.',
        'quick_control': 'Hızlı Kontrol',
        'actions': 'İşlemler',
        'special': 'Özel',
        'start': 'Başlat',
        'stop': 'Durdur',
        'trace': 'İzle',
        'stop_trace': 'İzlemeyi Durdur',
        'follow': 'Takip Et',
        'stop_follow': 'Takibi Durdur',
        'return': 'Dön',
        'come': 'Lidere Gel',
        'leave_party': 'Partiden Ayrıl',
        'mount': 'Bin',
        'dismount': 'İn',
        'sit': 'Otur/Kalk',
        'berserk': 'Berserk',
        'pick_all': 'Topla',
        'stop_pick': 'Toplamayı Durdur',
        'sort': 'Sırala',
        'repair': 'Tamir',
        'storage': 'Depo',
        'clock': 'Clock',
        'devil_ext': 'Devil Uzat',
        'quick_ready': 'Bir kanal seçin ve hızlı komutu gönderin.',
    },
}


def _text(key):
    return GUI_TEXT[current_language][key]


def discord_clicked():
    try:
        webbrowser.open(DISCORD_URL)
        log('[%s] Opening Discord invite...' % pName)
    except Exception as error:
        log('[%s] Discord link error: %s' % (pName, error))

# Globals
inGame = None
current_character_name = "Unknown"
current_account_name = None

# xControlAttack globals
followActivated = False
followPlayer = ''
followDistance = 0
attackMode = False
targetX = 0
targetY = 0
targetZ = 0

# Leader TP announce globals
announce_own_teleports = False
ignore_setfcontrolleader = True
_pending_tp_source = None
_pending_tp_destination_id = None
_pending_tp_armed_at = None
_pending_tp_is_runtime = False
_pending_tp_origin_region = None
_runtime_tp_command_until = 0.0
_suppress_runtime_announce_until = 0.0
_last_seen_announce_channel = None
_announce_settings_loaded_for = None
_leaders_loaded_for = None
_last_selected_tp_uid = None
_last_selected_tp_source = None
_last_selected_tp_at = 0.0
_queued_tp_announcement = None

# Item Storage (TIS) command state
tis_active = False
tis_claim_pending = False
tis_item_count = 0
tis_deadline = 0.0

# Pick-pet Clock command state
clock_pending = False
clock_pending_slot = None
clock_pending_pet_slot = None
clock_previous_remaining = None
clock_deadline = 0.0

# Devil/Nasrun Extension Gear command state
devilext_state = None
devilext_gear_slot = None
devilext_devil_slot = None
devilext_was_equipped = False
devilext_deadline = 0.0

# Pick All (PA/SPA) command state
pick_all_active = False
pick_all_target_id = None
pick_all_last_request_at = 0.0

PICK_ALL_RANGE_METERS = 4.0
PICK_ALL_REQUEST_INTERVAL = 1.0

TELEPORT_PROXIMITY_METERS = 45  # FControl portunda aynı sabit 45m olarak tutuldu
TP_ANNOUNCE_TIMEOUT = 60  # saniye; ışınlanma başarısız olursa eski duyuru gönderilmesin diye
TP_SCENE_STABLE_CHECKS = 3
TP_SCENE_SAFETY_DELAY = 1.0
TP_SCENE_FALLBACK_DELAY = 8.0

# Karakterin dinlediği (hedef gerektirmeyen, broadcast) chat kanalları - chat-api.md'de belgelenen
# phBotChat fonksiyonlarıyla birebir eşleşiyor
ANNOUNCE_CHANNEL_ORDER = ('All', 'Party', 'Guild', 'Union')
ANNOUNCE_CHANNELS = {
    'All': phBotChat.All,
    'Party': phBotChat.Party,
    'Guild': phBotChat.Guild,
    'Union': phBotChat.Union,
}

# phBot chat type IDs
CHAT_PARTY = 4
CHAT_GUILD = 5

def get_game_name():
    global inGame
    if not inGame:
        isJoined()
    if inGame and "server" in inGame and inGame["server"]:
        return inGame["server"]
    return "Unknown Server"


def update_account_info():
    global current_account_name
    profile = get_profile()
    current_account_name = profile if profile else read_account_from_ini()


def read_account_from_ini():
    ini_path = get_config_dir() + "phBot.ini"
    if not ini_path or not os.path.exists(ini_path):
        return None
    try:
        with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.strip().lower().startswith("username"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        return parts[1].strip()
    except Exception:
        pass
    return None


# Commands section - right under title
_x_cmd = 6
_y_cmd = 30
lblCommands = QtBind.createLabel(gui, '<font color="#ffd86b"><b>Available Commands</b></font>', _x_cmd, _y_cmd)
_y_cmd += 18
lstCommands = QtBind.createList(gui, _x_cmd, _y_cmd, 500, 200)
COMMAND_DESCRIPTIONS = [
    ('S', 'Start the bot', 'Botu başlat'),
    ('SS', 'Stop the bot', 'Botu durdur'),
    ('T [Player]', 'Trace the leader or a player', 'Lideri veya bir oyuncuyu izle'),
    ('N', 'Stop tracing', 'İzlemeyi durdur'),
    ('FL [Player] [Distance]', 'Follow a party member', 'Bir parti üyesini takip et'),
    ('NF', 'Stop following', 'Takip etmeyi durdur'),
    ('M', 'Mount a transport pet', 'Bir taşıma petine bin'),
    ('D / DS', 'Dismount the current pet', 'Binili petten in'),
    ('SIT', 'Toggle sit or stand', 'Oturma veya ayağa kalkma durumunu değiştir'),
    ('ZK', 'Activate Berserker mode', 'Berserker modunu etkinleştir'),
    ('RE', 'Use a return scroll or revive in town', 'Return scroll kullan veya şehirde diril'),
    ('COME', 'Reverse-return to the leader', 'Reverse ile lidere git'),
    ('REVERSE Type [Name]', 'Reverse to return, death, player, or zone', 'Return, ölüm, oyuncu veya bölge konumuna reverse kullan'),
    ('Q1 / Q2 / Q3', 'Use a predefined teleport route', 'Önceden tanımlı bir ışınlanma rotası kullan'),
    ('TP Source DestinationID', 'Use a standard teleporter', 'Standart bir ışınlayıcı kullan'),
    ('TPR Source', 'Use a runtime portal', 'Runtime portalı kullan'),
    ('RC Town', 'Set recall at a nearby town portal', 'Yakındaki şehir portalında recall ayarla'),
    ('LP', 'Leave the party', 'Partiden ayrıl'),
    ('DC', 'Disconnect from the server', 'Sunucu bağlantısını kes'),
    ('SP [X Y Region Z]', 'Set the training position', 'Eğitim konumunu ayarla'),
    ('SR [Radius]', 'Set the training radius', 'Eğitim yarıçapını ayarla'),
    ('!C AreaName/ID', 'Select a training area and start the bot', 'Eğitim alanını seç ve botu başlat'),
    ('SETSCRIPT [Path]', 'Set or clear the training script', 'Eğitim scriptini ayarla veya temizle'),
    ('MOVE X Y [Z]', 'Move without attacking', 'Saldırmadan hareket et'),
    ('MOVEATTACK X Y [Z]', 'Move, set the area, and start botting', 'Hareket et, alanı ayarla ve botu başlat'),
    ('MOVEON [Radius]', 'Move to a random nearby point', 'Yakındaki rastgele bir noktaya git'),
    ('GETPOS', 'Send the current position by private message', 'Mevcut konumu özel mesajla gönder'),
    ('EQ ItemName', 'Equip an inventory item', 'Envanterdeki bir eşyayı kuşan'),
    ('UQ ItemName', 'Unequip an equipped item', 'Kuşanılmış bir eşyayı çıkar'),
    ('USE ItemName', 'Use an inventory item', 'Envanterdeki bir eşyayı kullan'),
    ('SORT', 'Sort the inventory', 'Envanteri sırala'),
    ('REPAIR', 'Use one Repair Hammer', 'Bir Repair Hammer kullan'),
    ('PA', 'Pick all nearby drops allowed by the pick filter', 'Pick filtresinin izin verdiği yakındaki eşyaları topla'),
    ('SPA', 'Stop Pick All', 'Pick All işlemini durdur'),
    ('TIS', 'Claim all available Item Storage items', 'Mevcut Item Storage eşyalarının tümünü al'),
    ('CLOCK', 'Use exactly one Clock of Reincarnation on the pick pet', 'Pick pet üzerinde tam bir Clock of Reincarnation kullan'),
    ('DEVILEXT', 'Extend one Devil/Nasrun and restore it if it was equipped', 'Bir Devil/Nasrun süresini uzat ve kuşanılmışsa geri kuşan'),
    ('CHAT Type Message', 'Send a chat message', 'Sohbet mesajı gönder'),
    ('INJECT Opcode [Encrypted] [Data]', 'Inject a packet', 'Paket enjekte et'),
    ('FSH [true|false] Name', 'Play an FScriptHelper recording', 'Bir FScriptHelper kaydını oynat'),
    ('SETPROFILE [Name]', 'Load a phBot profile', 'Bir phBot profili yükle'),
    ('PROFILE [Name]', 'Alias for SETPROFILE', 'SETPROFILE için alternatif komut'),
    ('ALEADER CharNick', 'Add an authorized leader', 'Yetkili bir lider ekle'),
    ('RLEADER CharNick', 'Remove an authorized leader', 'Yetkili bir lideri kaldır'),
    ('SETFCONTROLLEADER', 'Request leader access (normally disabled)', 'Lider erişimi iste (normalde devre dışı)'),
]


def _refresh_command_list():
    QtBind.clear(gui, lstCommands)
    description_index = 1 if current_language == 'en' else 2
    for command, english, turkish in COMMAND_DESCRIPTIONS:
        descriptions = (command, english, turkish)
        QtBind.append(gui, lstCommands, '- %s : %s' % (command, descriptions[description_index]))


_refresh_command_list()

# Leaders section data
lstLeadersData = []

# ______________________________ Methods ______________________________ #

# Check if character is ingame
def isJoined():
    global inGame
    inGame = get_character_data()
    if not (inGame and "name" in inGame and inGame["name"]):
        inGame = None
    return inGame

# Return plugin folder path
def getPath():
    return get_config_dir() + pName + "\\"

# Return character configs path (JSON)
def getConfig():
    isJoined()
    if inGame:
        return getPath() + inGame['server'] + "_" + inGame['name'] + ".json"
    return getPath() + "default_leaders.json"


# Character-specific announce settings path. None until character data is ready.
def getAnnounceConfig():
    character = get_character_data() or {}
    server = character.get('server')
    name = character.get('name')
    if not server or not name:
        return None
    return getPath() + server + "_" + name + ".json"

# Add leader to the list
def btnAddLeader_clicked():
    player = QtBind.text(gui, tbxLeaders)
    if player and not lstLeaders_exist(player):
        if not os.path.exists(getPath()):
            os.makedirs(getPath())
        data = {}
        config_path = getConfig()
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
            except:
                data = {}
        if not "Leaders" in data:
            data['Leaders'] = []
        data['Leaders'].append(player)
        try:
            with open(config_path, "w") as f:
                f.write(json.dumps(data, indent=4, sort_keys=True))
        except Exception as e:
            log('Plugin: Error saving config - ' + str(e))
            return
        name_file_path = getPath() + "name.txt"
        try:
            with open(name_file_path, "a") as f:
                f.write(player + "\n")
        except Exception as e:
            log('Plugin: Error saving name.txt - ' + str(e))
        QtBind.append(gui, lstLeaders, player)
        QtBind.setText(gui, tbxLeaders, "")
        # Update in-memory list immediately so commands work without restart
        if player not in lstLeadersData:
            lstLeadersData.append(player)
        log('Plugin: Leader added [' + player + ']')
    else:
        if not player:
            log('Plugin: Enter leader name first')
        else:
            log('Plugin: This leader already exists')

# Remove leader from the list
def btnRemLeader_clicked():
    selectedItem = QtBind.text(gui, lstLeaders)
    if selectedItem:
        if os.path.exists(getConfig()):
            data = {"Leaders":[]}
            with open(getConfig(), 'r') as f:
                data = json.load(f)
            try:
                data["Leaders"].remove(selectedItem)
                with open(getConfig(),"w") as f:
                    f.write(json.dumps(data, indent=4, sort_keys=True))
            except:
                pass
        QtBind.remove(gui, lstLeaders, selectedItem)
        # Remove from in-memory list immediately
        try:
            lstLeadersData.remove(selectedItem)
        except ValueError:
            pass
        log('Plugin: Leader removed [' + selectedItem + ']')

# Return True if nickname exist at the leader list
def lstLeaders_exist(nickname):
    nickname = nickname.lower()
    players = QtBind.getItems(gui, lstLeaders)
    for i in range(len(players)):
        if players[i].lower() == nickname:
            return True
    return False


def add_chat_leader(nickname):
    """Add and persist a leader received through an authorized chat channel."""
    if not nickname or lstLeaders_exist(nickname):
        return False

    if not os.path.exists(getPath()):
        os.makedirs(getPath())

    config_path = getConfig()
    data = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            log('Plugin: Error loading config while adding chat leader - ' + str(e))

    leaders = data.setdefault('Leaders', [])
    if not any(name.lower() == nickname.lower() for name in leaders):
        leaders.append(nickname)

    try:
        with open(config_path, 'w') as f:
            f.write(json.dumps(data, indent=4, sort_keys=True))
    except Exception as e:
        log('Plugin: Error saving chat leader - ' + str(e))
        return False

    QtBind.append(gui, lstLeaders, nickname)
    if not any(name.lower() == nickname.lower() for name in lstLeadersData):
        lstLeadersData.append(nickname)
    log('Plugin: Leader added via chat [' + nickname + ']')
    return True


def remove_chat_leader(nickname):
    """Remove and persist a leader requested by an authorized leader."""
    if not nickname:
        return False

    config_path = getConfig()
    if not os.path.exists(config_path):
        return False

    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        log('Plugin: Error loading config while removing chat leader - ' + str(e))
        return False

    leaders = data.get('Leaders', [])
    stored_name = next(
        (name for name in leaders if name.lower() == nickname.lower()),
        None
    )
    if stored_name is None:
        return False

    data['Leaders'] = [
        name for name in leaders if name.lower() != nickname.lower()
    ]
    try:
        with open(config_path, 'w') as f:
            f.write(json.dumps(data, indent=4, sort_keys=True))
    except Exception as e:
        log('Plugin: Error saving chat leader removal - ' + str(e))
        return False

    for gui_name in QtBind.getItems(gui, lstLeaders):
        if gui_name.lower() == nickname.lower():
            QtBind.remove(gui, lstLeaders, gui_name)
    lstLeadersData[:] = [
        name for name in lstLeadersData if name.lower() != nickname.lower()
    ]
    log('Plugin: Leader removed via chat [' + stored_name + ']')
    return True


def is_own_character(nickname):
    if not nickname:
        return False
    character = get_character_data() or {}
    own_name = character.get('name') or current_character_name
    return bool(own_name and own_name != "Unknown" and own_name.lower() == nickname.lower())


# Teleport helpers
def inject_teleport(source, destination):
    t = get_teleport_data(source, destination)
    if t:
        npcs = get_npcs()
        for key, npc in npcs.items():
            if npc['name'] == source or npc['servername'] == source:
                log("Plugin: Selecting teleporter [" + source + "]")
                inject_joymax(0x7045, struct.pack('<I', key), False)
                Timer(2.0, inject_joymax, (0x705A, struct.pack('<IBI', key, 2, t[1]), False)).start()
                Timer(2.0, log, ("Plugin: Teleporting to [" + destination + "]",)).start()
                return
        log('Plugin: NPC not found. Wrong NPC name or servername')
    else:
        log('Plugin: Teleport data not found. Wrong teleport name or servername')


def _leader_teleport_sequence(name, routes):
    log(f"Plugin: Teleport sequence [{name}] started...")
    for src, dst in routes:
        inject_teleport(src, dst)


Q1_ROUTES = [
    ("Ferry Ticket Seller Doji", "Boat Ticket Seller Rahan"),
    ("Boat Ticket Seller Rahan", "Ferry Ticket Seller Doji"),
    ("Harbor Manager Marwa", "Pirate Morgun"),
    ("Pirate Morgun", "Harbor Manager Gale"),
    ("Harbor Manager Gale", "Pirate Morgun"),
    ("Priate Blackbeard", "Harbor Manager Gale"),
    ("Aircraft Ticket Seller Shard", "Aircraft Ticket Seller Sangnia"),
    ("Aircraft Ticket Seller Sangnia", "Aircraft Ticket Seller Shard"),
    ("Tunnel Manager Salhap", "Tunnel Manager Maryokuk"),
    ("Tunnel Manager Maryokuk", "Tunnel Manager Salhap"),
    ("Tunnel Manager Topni", "Tunnel Manager Asui"),
    ("Tunnel Manager Asui", "Tunnel Manager Topni"),
    ("Aircraft Ticket Seller Saena", "Aircraft Ticket Seller Ajati"),
    ("Aircraft Ticket Seller Ajati", "Airship Ticket Seller Dawari"),
    ("Airship Ticket Seller Dawari", "Aircraft Ticket Seller Ajati"),
    ("Aircraft Ticket Seller Sayun", "Airship Ticket Seller Dawari"),
    ("Airship Ticket Seller Poy", "Aircraft Ticket Seller Ajati"),
    ("Boat Ticket Seller Rahan", "Boat Ticket Seller Salmai"),
    ("Boat Ticket Seller Salmai", "Boat Ticket Seller Rahan"),
    ("Boat Ticket Seller Asimo", "Boat Ticket Seller Asa"),
    ("Boat Ticket Seller Asa", "Boat Ticket Seller Asimo"),
    ("Ferry Ticket Seller Tayun", "Ferry Ticket Seller Doji"),
    ("Ferry Ticket Seller Doji", "Ferry Ticket Seller Tayun"),
    ("Ferry Ticket Seller Hageuk", "Ferry Ticket Seller Chau"),
    ("Ferry Ticket Seller Chau", "Ferry Ticket Seller Hageuk"),
    ("forbidden plain", "Kings Valley"),
    ("Kings Valley", "forbidden plain"),
    ("abundance ground", "Storm and cloud Desert"),
    ("Storm and cloud Desert", "abundance ground"),
    ("Boat Ticket Seller Rahan", "Ferry Ticket Seller Chau"),
    ("Ferry Ticket Seller Chau", "Boat Ticket Seller Rahan")
]

Q2_ROUTES = [
    ("Harbor Manager Marwa", "Priate Blackbeard"),
    ("Harbor Manager Gale", "Priate Blackbeard"),
    ("Pirate Morgun", "Harbor Manager Marwa"),
    ("Priate Blackbeard", "Harbor Manager Marwa"),
    ("Aircraft Ticket Seller Saena", "Airship Ticket Seller Dawari"),
    ("Airship Ticket Seller Dawari", "Aircraft Ticket Seller Sayun"),
    ("Aircraft Ticket Seller Sayun", "Aircraft Ticket Seller Poy"),
    ("Airship Ticket Seller Poy", "Aircraft Ticket Seller Sayun"),
    ("Aircraft Ticket Seller Ajati", "Airship Ticket Seller Poy")
]

Q3_ROUTES = [
    ("Harbor Manager Marwa", "Harbor Manager Gale"),
    ("Harbor Manager Gale", "Harbor Manager Marwa"),
    ("Aircraft Ticket Seller Ajati", "Aircraft Ticket Seller Saena"),
    ("Airship Ticket Seller Dawari", "Aircraft Ticket Seller Saena")
]


# Load default configs for leaders
def loadDefaultLeadersConfig():
    QtBind.clear(gui, lstLeaders)

# Loads all leader configs previously saved
def loadLeadersConfigs():
    global lstLeadersData, _leaders_loaded_for
    loadDefaultLeadersConfig()
    config_file = getConfig()
    if os.path.exists(config_file):
        try:
            data = {}
            with open(config_file,"r") as f:
                data = json.load(f)
            if "Leaders" in data:
                lstLeadersData = data["Leaders"]
                for nickname in lstLeadersData:
                    QtBind.append(gui, lstLeaders, nickname)
        except Exception as e:
            log('Plugin: Error loading config - ' + str(e))
    _leaders_loaded_for = config_file

# Check if player is in leaders list
def isLeader(player_name):
    return lstLeaders_exist(player_name)

# Filter section
_x = 720 - 176
_y = 12
separatorMain = QtBind.createLineEdit(gui, "", _x - 26, _y, 1, 265)  # Separator line

cbxSro = QtBind.createCheckBox(gui, 'cbxShowClient_checked', _text('show_client_packets'), _x + 10, _y)
cbxShowClient = False
_y += 20
cbxJmx = QtBind.createCheckBox(gui, 'cbxShowServer_checked', _text('show_server_packets'), _x + 10, _y)
cbxShowServer = False
cbxIgnoreSetLeader = QtBind.createCheckBox(
    gui,
    'cbxIgnoreSetLeader_clicked',
    _text('ignore_set_leader'),
    _x,
    _y + 20
)
QtBind.setChecked(gui, cbxIgnoreSetLeader, False)

_y += 40
# Leaders section
lblLeaders = QtBind.createLabel(gui, '<font color="#3cff7a"><b>Leaders</b></font>', _x, _y)
_y += 18
tbxLeaders = QtBind.createLineEdit(gui, "", _x, _y, 100, 20)
btnAddLeader = QtBind.createButton(gui, 'btnAddLeader_clicked', _text('add'), _x + 100 + 2, _y - 2)
_y += 20
lstLeaders = QtBind.createList(gui, _x, _y, 176, 80)
btnRemLeader = QtBind.createButton(gui, 'btnRemLeader_clicked', _text('remove'), _x + 88 - 32, _y - 1 + 80)

_y += 115  # lstLeaders + btnRemLeader yüksekliği + boşluk (Remove butonunun altında kalmaması için)
cbxAnnounceOwnTp = QtBind.createCheckBox(gui, 'cbxAnnounceOwnTp_clicked', _text('announce_tps'), _x, _y)
_y += 20
lblAnnounceChannel = QtBind.createLabel(gui, _text('announce_channel'), _x, _y)
_y += 16
cbxAnnounceChannel = QtBind.createCombobox(gui, _x, _y, 90, 20)
for _channel_name in ANNOUNCE_CHANNEL_ORDER:
    QtBind.append(gui, cbxAnnounceChannel, _channel_name)


# Control page widgets and their original positions.
control_widgets = [
    (lblCommands, _x_cmd, 30),
    (lstCommands, _x_cmd, 48),
    (separatorMain, 518, 12),
    (cbxSro, 554, 12),
    (cbxJmx, 554, 32),
    (cbxIgnoreSetLeader, 544, 52),
    (lblLeaders, 544, 72),
    (tbxLeaders, 544, 90),
    (btnAddLeader, 646, 88),
    (lstLeaders, 544, 110),
    (btnRemLeader, 600, 189),
    (cbxAnnounceOwnTp, 544, 225),
    (lblAnnounceChannel, 544, 245),
    (cbxAnnounceChannel, 544, 261),
]


# ______________________________ Buttons page ______________________________ #

def _add_buttons_widget(widget, x, y):
    buttons_widgets.append((widget, x, y))
    QtBind.move(gui, widget, OFFSCREEN_X, y)
    return widget


lblButtonsTitle = _add_buttons_widget(
    QtBind.createLabel(gui, '<font color="#00d2ff" size="4"><b>BUTTONS</b></font>', 12, 38),
    12, 38
)
lblButtonsChannel = _add_buttons_widget(
    QtBind.createLabel(gui, '<b>%s</b>' % _text('chat_type'), 12, 70), 12, 70
)
cbxButtonsChannel = _add_buttons_widget(
    QtBind.createCombobox(gui, 85, 66, 100, 22), 85, 66
)
for _channel_name in ANNOUNCE_CHANNEL_ORDER:
    QtBind.append(gui, cbxButtonsChannel, _channel_name)
QtBind.setText(gui, cbxButtonsChannel, 'All')

lblJobSuitGroup = _add_buttons_widget(
    QtBind.createLabel(gui, '<font color="#3cff7a"><b>Job Suit</b></font>', 12, 92),
    12, 92
)
lineJobSuitGroup = _add_buttons_widget(
    QtBind.createLineEdit(gui, '', 12, 110, 266, 1), 12, 110
)
btnEquipJobSuit = _add_buttons_widget(
    QtBind.createButton(gui, 'btnEquipJobSuit_clicked', _text('equip_job'), 12, 115), 12, 115
)
btnUnequipJobSuit = _add_buttons_widget(
    QtBind.createButton(gui, 'btnUnequipJobSuit_clicked', _text('unequip_job'), 112, 115), 112, 115
)
lblJobSuitStatus = _add_buttons_widget(
    QtBind.createLabel(gui, '<table width="266"><tr><td><font color="#9aa0ac">%s</font></td></tr></table>' % _text('job_suit_initial'), 12, 137),
    12, 137
)

lblSetRadiusGroup = _add_buttons_widget(
    QtBind.createLabel(gui, '<font color="#3cff7a"><b>Set Radius</b></font>', 12, 157), 12, 157
)
lineSetRadiusGroup = _add_buttons_widget(
    QtBind.createLineEdit(gui, '', 12, 175, 266, 1), 12, 175
)
lblRadius = _add_buttons_widget(
    QtBind.createLabel(gui, _text('radius'), 12, 186), 12, 186
)
tbxRadius = _add_buttons_widget(
    QtBind.createLineEdit(gui, '', 72, 182, 78, 22), 72, 182
)
btnSetRadius = _add_buttons_widget(
    QtBind.createButton(gui, 'btnSetRadius_clicked', _text('set_radius'), 155, 180), 155, 180
)
lblSetRadiusStatus = _add_buttons_widget(
    QtBind.createLabel(gui, '<table width="266"><tr><td><font color="#9aa0ac">%s</font></td></tr></table>' % _text('radius_initial'), 12, 207), 12, 207
)

lblSetProfileGroup = _add_buttons_widget(
    QtBind.createLabel(gui, '<font color="#3cff7a"><b>Set Profile</b></font>', 12, 225), 12, 225
)
lineSetProfileGroup = _add_buttons_widget(
    QtBind.createLineEdit(gui, '', 12, 243, 266, 1), 12, 243
)
lblProfileName = _add_buttons_widget(
    QtBind.createLabel(gui, _text('profile_name'), 12, 254), 12, 254
)
tbxProfileName = _add_buttons_widget(
    QtBind.createLineEdit(gui, '', 92, 250, 118, 22), 92, 250
)
btnSetProfile = _add_buttons_widget(
    QtBind.createButton(gui, 'btnSetProfile_clicked', _text('set_profile'), 215, 248), 215, 248
)
lblSetProfileStatus = _add_buttons_widget(
    QtBind.createLabel(gui, '<table width="266"><tr><td><font color="#9aa0ac">%s</font></td></tr></table>' % _text('profile_initial'), 12, 277), 12, 277
)

lblQuickControlGroup = _add_buttons_widget(
    QtBind.createLabel(gui, '<font color="#3cff7a"><b>Quick Control</b></font>', 300, 82), 300, 82
)

QUICK_BUTTON_SPECS = [
    ('start', 'btnQuickStart_clicked', 'S', 300, 100),
    ('stop', 'btnQuickStop_clicked', 'SS', 435, 100),
    ('trace', 'btnQuickTrace_clicked', 'T', 570, 100),
    ('stop_trace', 'btnQuickStopTrace_clicked', 'N', 300, 122),
    ('follow', 'btnQuickFollow_clicked', 'FL', 435, 122),
    ('stop_follow', 'btnQuickStopFollow_clicked', 'NF', 570, 122),
    ('return', 'btnQuickReturn_clicked', 'RE', 300, 144),
    ('come', 'btnQuickCome_clicked', 'COME', 435, 144),
    ('leave_party', 'btnQuickLeaveParty_clicked', 'LP', 570, 144),
]
quick_control_buttons = {}
for _key, _callback, _command, _button_x, _button_y in QUICK_BUTTON_SPECS:
    quick_control_buttons[_key] = _add_buttons_widget(
        QtBind.createButton(gui, _callback, _text(_key), _button_x, _button_y),
        _button_x, _button_y
    )

lblActionsGroup = _add_buttons_widget(
    QtBind.createLabel(gui, '<font color="#3cff7a"><b>Actions</b></font>', 300, 170), 300, 170
)

ACTION_BUTTON_SPECS = [
    ('mount', 'btnQuickMount_clicked', 'M', 300, 188),
    ('dismount', 'btnQuickDismount_clicked', 'D', 435, 188),
    ('sit', 'btnQuickSit_clicked', 'SIT', 570, 188),
    ('berserk', 'btnQuickBerserk_clicked', 'ZK', 300, 210),
    ('pick_all', 'btnQuickPickAll_clicked', 'PA', 435, 210),
    ('stop_pick', 'btnQuickStopPick_clicked', 'SPA', 570, 210),
    ('sort', 'btnQuickSort_clicked', 'SORT', 300, 232),
    ('repair', 'btnQuickRepair_clicked', 'REPAIR', 435, 232),
]
action_buttons = {}
for _key, _callback, _command, _button_x, _button_y in ACTION_BUTTON_SPECS:
    action_buttons[_key] = _add_buttons_widget(
        QtBind.createButton(gui, _callback, _text(_key), _button_x, _button_y),
        _button_x, _button_y
    )

lblSpecialGroup = _add_buttons_widget(
    QtBind.createLabel(gui, '<font color="#3cff7a"><b>Special</b></font>', 300, 258), 300, 258
)

SPECIAL_BUTTON_SPECS = [
    ('storage', 'btnQuickStorage_clicked', 'TIS', 300, 276),
    ('clock', 'btnQuickClock_clicked', 'CLOCK', 435, 276),
    ('devil_ext', 'btnQuickDevilExt_clicked', 'DEVILEXT', 570, 276),
]
special_buttons = {}
for _key, _callback, _command, _button_x, _button_y in SPECIAL_BUTTON_SPECS:
    special_buttons[_key] = _add_buttons_widget(
        QtBind.createButton(gui, _callback, _text(_key), _button_x, _button_y),
        _button_x, _button_y
    )

lblQuickStatus = _add_buttons_widget(
    QtBind.createLabel(gui, '<font color="#9aa0ac">%s</font>' % _text('quick_ready'), 300, 62),
    300, 62
)

_job_suit_status = ('job_suit_initial', (), '#9aa0ac')
_radius_status = ('radius_initial', (), '#9aa0ac')
_profile_status = ('profile_initial', (), '#9aa0ac')
_quick_status = ('quick_ready', (), '#9aa0ac')


def _format_gui_text(key, args=()):
    value = _text(key)
    return value % args if args else value


def _render_status(widget, status, width=250):
    key, args, color = status
    QtBind.setText(
        gui,
        widget,
        '<table width="%d" cellspacing="0" cellpadding="0"><tr><td>'
        '<font color="%s">%s</font></td></tr></table>' %
        (width, color, _format_gui_text(key, args))
    )


def _apply_gui_language():
    QtBind.setText(gui, btnControlPage, _text('control'))
    QtBind.setText(gui, btnButtonsPage, _text('buttons'))
    QtBind.setText(gui, btnLanguage, 'TR' if current_language == 'en' else 'EN')
    QtBind.setText(gui, lblCommands, '<font color="#ffd86b"><b>%s</b></font>' % _text('commands_title'))
    QtBind.setText(gui, cbxSro, _text('show_client_packets'))
    QtBind.setText(gui, cbxJmx, _text('show_server_packets'))
    QtBind.setText(gui, cbxIgnoreSetLeader, _text('ignore_set_leader'))
    QtBind.setText(gui, lblLeaders, '<font color="#3cff7a"><b>%s</b></font>' % _text('leaders'))
    QtBind.setText(gui, btnAddLeader, _text('add'))
    QtBind.setText(gui, btnRemLeader, _text('remove'))
    QtBind.setText(gui, cbxAnnounceOwnTp, _text('announce_tps'))
    QtBind.setText(gui, lblAnnounceChannel, _text('announce_channel'))
    QtBind.setText(gui, lblButtonsTitle, '<font color="#00d2ff" size="4"><b>%s</b></font>' % _text('buttons_title'))
    QtBind.setText(gui, lblButtonsChannel, '<b>%s</b>' % _text('chat_type'))
    QtBind.setText(gui, lblJobSuitGroup, '<font color="#3cff7a"><b>%s</b></font>' % _text('job_suit_group'))
    QtBind.setText(gui, btnEquipJobSuit, _text('equip_job'))
    QtBind.setText(gui, btnUnequipJobSuit, _text('unequip_job'))
    QtBind.setText(gui, lblSetRadiusGroup, '<font color="#3cff7a"><b>%s</b></font>' % _text('set_radius_group'))
    QtBind.setText(gui, lblRadius, _text('radius'))
    QtBind.setText(gui, btnSetRadius, _text('set_radius'))
    QtBind.setText(gui, lblSetProfileGroup, '<font color="#3cff7a"><b>%s</b></font>' % _text('set_profile_group'))
    QtBind.setText(gui, lblProfileName, _text('profile_name'))
    QtBind.setText(gui, btnSetProfile, _text('set_profile'))
    QtBind.setText(gui, lblQuickControlGroup, '<font color="#3cff7a"><b>%s</b></font>' % _text('quick_control'))
    QtBind.setText(gui, lblActionsGroup, '<font color="#3cff7a"><b>%s</b></font>' % _text('actions'))
    QtBind.setText(gui, lblSpecialGroup, '<font color="#3cff7a"><b>%s</b></font>' % _text('special'))
    for key, widget in quick_control_buttons.items():
        QtBind.setText(gui, widget, _text(key))
    for key, widget in action_buttons.items():
        QtBind.setText(gui, widget, _text(key))
    for key, widget in special_buttons.items():
        QtBind.setText(gui, widget, _text(key))
    _refresh_command_list()
    _render_status(lblJobSuitStatus, _job_suit_status)
    _render_status(lblSetRadiusStatus, _radius_status)
    _render_status(lblSetProfileStatus, _profile_status)
    _render_status(lblQuickStatus, _quick_status, 400)


def toggle_language():
    global current_language
    current_language = 'tr' if current_language == 'en' else 'en'
    _apply_gui_language()


def _set_job_suit_status(key, args=(), color='#9aa0ac'):
    global _job_suit_status
    _job_suit_status = (key, args, color)
    _render_status(lblJobSuitStatus, _job_suit_status)


def _send_job_suit_command(command):
    channel = QtBind.text(gui, cbxButtonsChannel) or 'All'
    if channel not in ANNOUNCE_CHANNELS:
        channel = 'All'
    message = '%s job' % command
    sent = ANNOUNCE_CHANNELS[channel](message)
    if sent:
        _set_job_suit_status('sent_command', (channel, message), '#3cff7a')
        log('Plugin: Buttons: Sent on %s: %s' % (channel, message))
    else:
        _set_job_suit_status('send_failed', (message,), '#ff4b5c')
        log('Plugin: Buttons: Chat send failed on %s: %s' % (channel, message))
    return sent


def btnEquipJobSuit_clicked():
    return _send_job_suit_command('EQ')


def btnUnequipJobSuit_clicked():
    return _send_job_suit_command('UQ')


def _set_radius_status(key, args=(), color='#9aa0ac'):
    global _radius_status
    _radius_status = (key, args, color)
    _render_status(lblSetRadiusStatus, _radius_status)


def btnSetRadius_clicked():
    value = (QtBind.text(gui, tbxRadius) or '').strip()
    try:
        radius = abs(int(float(value)))
    except (ValueError, OverflowError):
        _set_radius_status('radius_required', (), '#ff4b5c')
        log('Plugin: Buttons: Radius must be a finite numeric value')
        return False

    channel = QtBind.text(gui, cbxButtonsChannel) or 'All'
    if channel not in ANNOUNCE_CHANNELS:
        channel = 'All'
    message = 'SR %d' % radius
    sent = ANNOUNCE_CHANNELS[channel](message)
    if sent:
        _set_radius_status('sent_command', (channel, message), '#3cff7a')
        log('Plugin: Buttons: Sent on %s: %s' % (channel, message))
    else:
        _set_radius_status('send_failed', (message,), '#ff4b5c')
        log('Plugin: Buttons: Chat send failed on %s: %s' % (channel, message))
    return sent


def _set_profile_status(key, args=(), color='#9aa0ac'):
    global _profile_status
    _profile_status = (key, args, color)
    _render_status(lblSetProfileStatus, _profile_status)


def btnSetProfile_clicked():
    profile_name = (QtBind.text(gui, tbxProfileName) or '').strip()
    if not profile_name:
        _set_profile_status('profile_required', (), '#ff4b5c')
        log('Plugin: Buttons: Profile name is empty')
        return False

    channel = QtBind.text(gui, cbxButtonsChannel) or 'All'
    if channel not in ANNOUNCE_CHANNELS:
        channel = 'All'
    message = 'SETPROFILE ' + profile_name
    sent = ANNOUNCE_CHANNELS[channel](message)
    if sent:
        _set_profile_status('sent_command', (channel, message), '#3cff7a')
        log('Plugin: Buttons: Sent on %s: %s' % (channel, message))
    else:
        _set_profile_status('send_failed', (message,), '#ff4b5c')
        log('Plugin: Buttons: Chat send failed on %s: %s' % (channel, message))
    return sent


def _send_button_command(command):
    global _quick_status
    channel = QtBind.text(gui, cbxButtonsChannel) or 'All'
    if channel not in ANNOUNCE_CHANNELS:
        channel = 'All'
    sent = ANNOUNCE_CHANNELS[channel](command)
    if sent:
        _quick_status = ('sent_command', (channel, command), '#3cff7a')
        log('Plugin: Buttons: Sent on %s: %s' % (channel, command))
    else:
        _quick_status = ('send_failed', (command,), '#ff4b5c')
        log('Plugin: Buttons: Chat send failed on %s: %s' % (channel, command))
    _render_status(lblQuickStatus, _quick_status, 400)
    return sent


def btnQuickStart_clicked():
    return _send_button_command('S')


def btnQuickStop_clicked():
    return _send_button_command('SS')


def btnQuickTrace_clicked():
    return _send_button_command('T')


def btnQuickStopTrace_clicked():
    return _send_button_command('N')


def btnQuickFollow_clicked():
    return _send_button_command('FL')


def btnQuickStopFollow_clicked():
    return _send_button_command('NF')


def btnQuickReturn_clicked():
    return _send_button_command('RE')


def btnQuickCome_clicked():
    return _send_button_command('COME')


def btnQuickLeaveParty_clicked():
    return _send_button_command('LP')


def btnQuickMount_clicked():
    return _send_button_command('M')


def btnQuickDismount_clicked():
    return _send_button_command('D')


def btnQuickSit_clicked():
    return _send_button_command('SIT')


def btnQuickBerserk_clicked():
    return _send_button_command('ZK')


def btnQuickPickAll_clicked():
    return _send_button_command('PA')


def btnQuickStopPick_clicked():
    return _send_button_command('SPA')


def btnQuickSort_clicked():
    return _send_button_command('SORT')


def btnQuickRepair_clicked():
    return _send_button_command('REPAIR')


def btnQuickStorage_clicked():
    return _send_button_command('TIS')


def btnQuickClock_clicked():
    return _send_button_command('CLOCK')


def btnQuickDevilExt_clicked():
    return _send_button_command('DEVILEXT')


_apply_gui_language()


def show_control_page():
    global active_page
    active_page = 'control'
    for widget, x, y in buttons_widgets:
        QtBind.move(gui, widget, OFFSCREEN_X, y)
    for widget, x, y in control_widgets:
        QtBind.move(gui, widget, x, y)


def show_buttons_page():
    global active_page
    active_page = 'buttons'
    for widget, x, y in control_widgets:
        QtBind.move(gui, widget, OFFSCREEN_X, y)
    for widget, x, y in buttons_widgets:
        QtBind.move(gui, widget, x, y)


def cbxAnnounceOwnTp_clicked(checked):
    global announce_own_teleports
    announce_own_teleports = checked
    save_announce_settings()


def cbxIgnoreSetLeader_clicked(checked):
    global ignore_setfcontrolleader
    ignore_setfcontrolleader = bool(checked)
    save_announce_settings()


def get_announce_channel():
    """Read the selected announce channel directly because QtBind has no documented
    combobox change callback."""
    try:
        value = QtBind.text(gui, cbxAnnounceChannel)
        return value if value in ANNOUNCE_CHANNELS else 'All'
    except Exception:
        return 'All'


def save_announce_settings():
    """Save teleport announcement settings for the current character."""
    data = {}
    config_path = getAnnounceConfig()
    if not config_path:
        log('Plugin: Character data is not ready; announce settings were not saved yet')
        return False
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
        except Exception:
            data = {}
    data['AnnounceOwnTeleports'] = announce_own_teleports
    data['AnnounceChannel'] = get_announce_channel()
    data['IgnoreSetFControlLeader'] = ignore_setfcontrolleader
    if not os.path.exists(getPath()):
        os.makedirs(getPath())
    try:
        with open(config_path, "w") as f:
            f.write(json.dumps(data, indent=4, sort_keys=True))
    except Exception as e:
        log('Plugin: Error saving announce settings - ' + str(e))
        return False
    return True


def load_announce_settings():
    """Load teleport announcement settings for the current character."""
    global announce_own_teleports, ignore_setfcontrolleader
    global _last_seen_announce_channel, _announce_settings_loaded_for
    config_file = getAnnounceConfig()
    if not config_file:
        return False
    saved_channel = 'All'
    announce_own_teleports = False
    ignore_setfcontrolleader = True
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                data = json.load(f)
            announce_own_teleports = bool(data.get("AnnounceOwnTeleports", False))
            ignore_setfcontrolleader = bool(data.get("IgnoreSetFControlLeader", True))
            saved_channel = data.get("AnnounceChannel", "All")
            if saved_channel not in ANNOUNCE_CHANNELS:
                saved_channel = 'All'
        except Exception as e:
            log('Plugin: Error loading announce settings - ' + str(e))
            return False
    QtBind.setChecked(gui, cbxAnnounceOwnTp, announce_own_teleports)
    QtBind.setChecked(gui, cbxIgnoreSetLeader, ignore_setfcontrolleader)
    QtBind.setText(gui, cbxAnnounceChannel, saved_channel)
    _last_seen_announce_channel = saved_channel
    _announce_settings_loaded_for = config_file
    return True


cbxDontShow_checked = True
lstOpcodesData = []


# ______________________________ Methods ______________________________ #

# Return plugin configs path (JSON)
def getPluginConfig():
    return get_config_dir() + pName + ".json"

# Load default configs for opcodes
def loadDefaultOpcodeConfig():
    global lstOpcodesData
    lstOpcodesData = []

# Load the list of opcodes with the config file
def loadOpcodeConfigs():
    loadDefaultOpcodeConfig()
    if os.path.exists(getPluginConfig()):
        data = {}
        with open(getPluginConfig(), "r") as f:
            data = json.load(f)
        if "FilteredOpcodes" in data:
            global lstOpcodesData
            lstOpcodesData = data["FilteredOpcodes"]
        if "DontShow" in data:
            global cbxDontShow_checked
            cbxDontShow_checked = data["DontShow"]

# Save all config
def saveConfigs():
    data = {}
    data['DontShow'] = cbxDontShow_checked
    data['FilteredOpcodes'] = lstOpcodesData
    with open(getPluginConfig(), "w") as f:
        f.write(json.dumps(data, indent=4, sort_keys=True))

# Checkbox "Show Client Packets" checked
def cbxShowClient_checked(checked):
    global cbxShowClient
    cbxShowClient = checked

# Checkbox "Show Server Packets" checked
def cbxShowServer_checked(checked):
    global cbxShowServer
    cbxShowServer = checked

# return True if can log/show the packet
def CanShowPacket(opcode):
    if opcode in lstOpcodesData:
        if not cbxDontShow_checked:
            return True
    elif cbxDontShow_checked:
        return True
    return False

def inject(args):
    argCount = len(args)
    if argCount < 2:
        log("Plugin: Incorrect structure to inject packet")
        return 0
    opcode = int(args[1], 16)
    data = bytearray()
    encrypted = False
    dataIndex = 2
    if argCount >= 3:
        enc = args[2].lower()
        if enc == 'true' or enc == 'false':
            encrypted = enc == "true"
            dataIndex += 1
    for i in range(dataIndex, argCount):
        data.append(int(args[i], 16))
    log("Plugin: Injecting packet" + (' (Encrypted)' if encrypted else '') + " :")
    log("(Opcode) 0x" + '{:02X}'.format(opcode) + " (Data) " + ("None" if not data else ' '.join(
        '{:02X}'.format(x) for x in data)))
    inject_joymax(opcode, data, encrypted)
    return 0


def handle_training_area_command(player, text):
    parts = text.split()
    if len(parts) < 2:
        log(f"Plugin: !C command from {player} missing area name or ID")
        return False
    area_name = " ".join(parts[1:])
    success = set_training_area(area_name)
    if success:
        area_info = get_training_area() or {}
        radius = area_info.get("radius", "unknown")
        log(f"Plugin: {player} switched training area to '{area_name}' (radius {radius})")
        log("Plugin: Starting bot after training area change...")
        start_bot()
    else:
        log(f"Plugin: Failed to change training area to '{area_name}' requested by {player}")
    return success

def GetItemByExpression(_lambda, start=0, end=0):
    """Search an item by name or servername through lambda expression and return its information"""
    inventory = get_inventory()
    items = inventory['items']
    if end == 0:
        end = inventory['size']
    for slot, item in enumerate(items):
        if start <= slot and slot <= end:
            if item:
                if _lambda(item['name'], item['servername']):
                    item['slot'] = slot
                    return item
    return None


def GetJobItem(start, end=0):
    """Return the first real job item in the requested inventory/equipment range."""
    inventory = get_inventory() or {}
    items = inventory.get('items') or []
    if end == 0:
        end = len(items) - 1
    for slot, item in enumerate(items):
        if slot < start or slot > end or not item:
            continue
        item_data = get_item(item.get('model'))
        if item_data and item_data.get('tid1') == 1 and item_data.get('tid2') == 7:
            item['slot'] = slot
            return item
    return None

# Gets the NPC unique ID if the specified name is found near
def GetNPCUniqueID(name):
    NPCs = get_npcs()
    if NPCs:
        name = name.lower()
        for UniqueID, NPC in NPCs.items():
            if NPC['name'].lower() == name:
                return UniqueID
    return 0

# Finds an empty inventory slot; iSRO reserves equipment slots 13-16 as well.
def GetEmptySlot():
    inventory = get_inventory() or {}
    items = inventory.get('items') or []
    first_inventory_slot = 17 if get_locale() == 18 else 13
    for slot in range(first_inventory_slot, len(items)):
        if not items[slot]:
            return slot
    return -1

# Injects item movement on inventory (equip/unequip/avatar slots)
def Inject_InventoryMovement(movementType, slotInitial, slotFinal, logItemName, quantity=0):
    p = struct.pack('<B', movementType)
    p += struct.pack('<B', slotInitial)
    p += struct.pack('<B', slotFinal)
    p += struct.pack('<H', quantity)
    log('Plugin: Moving item "' + logItemName + '"...')
    # CLIENT_INVENTORY_ITEM_MOVEMENT
    inject_joymax(0x7034, p, False)

# Try to equip item, based on its tid1/tid2/tid3 classification (get_item())
def EquipItem(item):
    itemData = get_item(item['model'])
    if not itemData or itemData['tid1'] != 1:
        log('Plugin: ' + item['name'] + ' cannot be equipped!')
        return
    t = itemData['tid2']
    # garment, protector, armor, robe, light, heavy
    if t == 1 or t == 2 or t == 3 or t == 9 or t == 10 or t == 11:
        t = itemData['tid3']
        if t == 1:  # head
            Inject_InventoryMovement(0, item['slot'], 0, item['name'])
        elif t == 2:  # shoulders
            Inject_InventoryMovement(0, item['slot'], 2, item['name'])
        elif t == 3:  # chest
            Inject_InventoryMovement(0, item['slot'], 1, item['name'])
        elif t == 4:  # pants
            Inject_InventoryMovement(0, item['slot'], 4, item['name'])
        elif t == 5:  # gloves
            Inject_InventoryMovement(0, item['slot'], 3, item['name'])
        elif t == 6:  # boots
            Inject_InventoryMovement(0, item['slot'], 5, item['name'])
    elif t == 4:  # shields
        Inject_InventoryMovement(0, item['slot'], 7, item['name'])
    elif t == 5 or t == 12:  # accessories ch/eu
        t = itemData['tid3']
        if t == 1:  # earring
            Inject_InventoryMovement(0, item['slot'], 9, item['name'])
        elif t == 2:  # necklace
            Inject_InventoryMovement(0, item['slot'], 10, item['name'])
        elif t == 3:  # ring
            if not GetItemByExpression(lambda n, s: True, 11):
                Inject_InventoryMovement(0, item['slot'], 12, item['name'])
            else:
                Inject_InventoryMovement(0, item['slot'], 11, item['name'])
    elif t == 6:  # weapon ch/eu
        Inject_InventoryMovement(0, item['slot'], 6, item['name'])
    elif t == 7:  # job
        Inject_InventoryMovement(0, item['slot'], 8, item['name'])
    elif t == 13:  # avatar
        t = itemData['tid3']
        if t == 1:  # hat
            Inject_InventoryMovement(36, item['slot'], 0, item['name'])
        elif t == 2:  # dress
            Inject_InventoryMovement(36, item['slot'], 1, item['name'])
        elif t == 3:  # accessory
            Inject_InventoryMovement(36, item['slot'], 2, item['name'])
        elif t == 4:  # flag
            Inject_InventoryMovement(36, item['slot'], 3, item['name'])
    elif t == 14:  # devil spirit
        Inject_InventoryMovement(36, item['slot'], 4, item['name'])

# Try to unequip item
def UnequipItem(item):
    slot = GetEmptySlot()
    if slot != -1:
        Inject_InventoryMovement(0, item['slot'], slot, item['name'])
    else:
        log('Plugin: Inventory is full, cannot unequip ' + item['name'])

# Get Type ID from item - game-data.md'deki resmi get_item() üzerinden hesaplanıyor,
# xControl.py'deki sqlite3/vSRO.json tabanlı GetDatabaseConnection() zincirine hiç gerek yok
def GetTIDFromItem(itemId):
    itemData = get_item(itemId)
    if not itemData:
        return None
    return itemData['cash_item'] + (3 * 4) + (itemData['tid1'] * 32) + (itemData['tid2'] * 128) + (itemData['tid3'] * 2048)

# Try to use the item specified
def UseItem(item):
    try:
        item_data = get_item(item['model'])
        if not item_data:
            log('Plugin: Item data not found for "' + item.get('name', 'Unknown') + '"')
            return False
        p = struct.pack('<B', item['slot'])
        loc = get_locale()
        if loc in (18, 65):  # iSRO and locale 65 use the expanded four-byte item type group.
            p += struct.pack(
                '<BBBB',
                (3 << 4) + int(bool(item_data.get('cash_item'))),
                int(item_data.get('tid1', 0)) * 4,
                int(item_data.get('tid2', 0)),
                int(item_data.get('tid3', 0))
            )
        else:
            tid = GetTIDFromItem(item['model'])
            if tid is None:
                log('Plugin: Item type data not found for "' + item.get('name', 'Unknown') + '"')
                return False
        if loc == 22:  # vSRO
            p += struct.pack('<H', tid)
        elif loc not in (18, 65):
            p += struct.pack('<I', tid)
        log('Plugin: Using item "' + item['name'] + '"...')
        # CLIENT_INVENTORY_ITEM_USE
        inject_joymax(0x704C, p, True)
        return True
    except Exception as e:
        log('Plugin: Failed to use item "' + item.get('name', 'Unknown') + '" - ' + str(e))
        return False

def DismountPet():
    """Try to dismount any mounted pet, return success"""
    try:
        pets = get_pets()
        if pets:
            for uid, pet in pets.items():
                if 'mounted' in pet and pet['mounted']:
                    p = b'\x00'
                    p += struct.pack('I', uid)
                    inject_joymax(0x70CB, p, False)
                    log(f"Plugin: Sending dismount packet for {pet.get('name', 'unknown')} (UID: {uid})")
                    return True
        return False
    except Exception as e:
        log(f'Plugin ERROR in DismountPet: {str(e)}')
        return False

def MountPet(pet_type):
    """Try to mount a pet by type, return success"""
    try:
        pet_type = pet_type.lower()
        if pet_type == 'horse':
            items = get_inventory()['items']
            for slot, item in enumerate(items):
                if item:
                    sn = item['servername']
                    if 'ITEM_COS' in sn and 'SCROLL' in sn:
                        log(f"Plugin: Using mount item at slot {slot}: {sn}")
                        packet = struct.pack('B', slot)
                        packet += struct.pack('H', 4588 + (1 if sn.endswith('_SCROLL') else 0))
                        inject_joymax(0x704C, packet, True)
                        return True
            log('Plugin: Mount scroll not found in inventory')
            return False
        pets = get_pets()
        if pets:
            for uid, pet in pets.items():
                if pet['type'] == pet_type:
                    p = b'\x01'
                    p += struct.pack('I', uid)
                    inject_joymax(0x70CB, p, False)
                    return True
        return False
    except Exception as e:
        log(f'Plugin ERROR in MountPet: {str(e)}')
        return False


# ______________________________ xControlAttack Methods ______________________________ #

def GetDistance(ax, ay, bx, by):
    return ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5

# Return True if the player is in the party
def party_player(player):
    players = get_party()
    if players:
        for p in players:
            if players[p]['name'] == player:
                return True
    return False

# Return point (dict with 'x'/'y') if player is in the party and near, otherwise None
def near_follow_player(player):
    # Prefer party data because it includes a reliable visibility/player_id flag.
    players = get_party()
    if players:
        for p in players:
            if players[p]['name'].lower() == player.lower() and players[p]['player_id'] > 0:
                return players[p]

    # FL is also allowed for non-party players when phBot exposes nearby players.
    players = get_players() or {}
    for player_data in players.values():
        if player_data.get('name', '').lower() == player.lower():
            return player_data
    return None

# Start following a party player using distance. Return success
def start_follow(player, distance):
    global followActivated, followPlayer, followDistance
    followPlayer = player
    followDistance = distance
    followActivated = True
    return True

# Stop follow player, return whether it was active
def stop_follow():
    global followActivated, followPlayer, followDistance
    result = followActivated
    followActivated = False
    followPlayer = ""
    followDistance = 0
    return result

def get_region_from_coords(x, y):
    if x < 0 and y < 0:
        return 'Jangan'
    elif x >= 0 and y < 0:
        return 'Donwhang'
    elif x >= 0 and y >= 0:
        return 'Hotan'
    elif x < 0 and y >= 0:
        return 'Samarkand'
    return None

def find_nearby_monsters(max_distance=30):
    monsters = get_monsters()
    nearby = []
    if monsters:
        current_pos = get_position()
        for uid, monster in monsters.items():
            if monster['hp'] > 0:
                distance = GetDistance(current_pos['x'], current_pos['y'], monster['x'], monster['y'])
                if distance <= max_distance:
                    nearby.append({'uid': uid, 'distance': distance, 'monster': monster})
    nearby.sort(key=lambda x: x['distance'])
    return nearby

def attack_monster(uid):
    log('Plugin: Attacking monster UID: ' + str(uid))
    inject_joymax(0x7075, struct.pack('<I', uid), False)

def move_and_attack(x, y, z=0):
    global attackMode, targetX, targetY, targetZ
    targetX = x
    targetY = y
    targetZ = z
    attackMode = True
    log('Plugin: Walking to (X:%.1f,Y:%.1f)' % (x, y))
    current_pos = get_position()
    script = generate_script(current_pos['region'], x, y, z)
    if script:
        script_str = '\n'.join(script)
        start_script(script_str)
    else:
        log('Plugin: Could not generate path, using direct movement')
        move_to(x, y, z)


def handle_tp_command(player, text):
    """Handle 'TP SourceNPC DestinationID' after confirming that the source NPC is nearby."""
    rest = text[2:].strip()
    if not rest:
        log("Plugin: Invalid TP command format; command skipped.")
        return

    last_space = rest.rfind(' ')
    if last_space <= 0:
        log("Plugin: Invalid TP command format; command skipped.")
        return

    source_name = rest[:last_space].strip()
    dest_text = rest[last_space + 1:].strip()

    try:
        destination_id = int(dest_text)
    except ValueError:
        log(f"Plugin: TP command has an invalid destination ID: '{dest_text}'")
        return

    npcs = get_npcs() or {}
    current_pos = get_position()

    nearest_uid = None
    nearest_distance = None
    for uid, npc in npcs.items():
        if npc.get('name') == source_name or npc.get('servername') == source_name:
            distance = GetDistance(current_pos['x'], current_pos['y'], npc['x'], npc['y'])
            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest_uid = uid

    if nearest_uid is None:
        log(f"Plugin: TP: Teleporter '{source_name}' was not found nearby; command skipped (Leader: {player}).")
        return

    if nearest_distance > TELEPORT_PROXIMITY_METERS:
        log(f"Plugin: TP: Teleporter is too far away ({nearest_distance:.1f}m > {TELEPORT_PROXIMITY_METERS}m); command skipped.")
        return

    log(f"Plugin: TP: Selecting teleporter [{source_name}] (Leader: {player})")
    inject_joymax(0x7045, struct.pack('<I', nearest_uid), False)
    Timer(2.0, inject_joymax, (0x705A, struct.pack('<IBI', nearest_uid, 2, destination_id), False)).start()
    Timer(2.0, log, (f"Plugin: TP: Teleporting -> {source_name}",)).start()


def handle_runtime_tp_command(player, text):
    """'TPR <source>' finds the nearby runtime portal and replays its type-3 teleport flow."""
    global _runtime_tp_command_until, _suppress_runtime_announce_until

    source_name = text[4:].strip()
    if not source_name:
        log(f"Plugin: TPR: Portal name is required (Leader: {player})")
        return

    now = time.time()
    if _runtime_tp_command_until > now:
        log(f"Plugin: TPR: A runtime portal operation is already running (Leader: {player})")
        return

    npcs = get_npcs() or {}
    current_pos = get_position()
    nearest_uid = None
    nearest_distance = None

    for uid, npc in npcs.items():
        if npc.get('servername') != source_name and npc.get('name') != source_name:
            continue
        if 'x' not in npc or 'y' not in npc:
            continue
        distance = GetDistance(current_pos['x'], current_pos['y'], npc['x'], npc['y'])
        if nearest_distance is None or distance < nearest_distance:
            nearest_uid = uid
            nearest_distance = distance

    if nearest_uid is None:
        log(f"Plugin: TPR: Runtime portal '{source_name}' was not found nearby (Leader: {player})")
        return

    if nearest_distance > TELEPORT_PROXIMITY_METERS:
        log(f"Plugin: TPR: Portal is too far away ({nearest_distance:.1f}m > {TELEPORT_PROXIMITY_METERS}m)")
        return

    # Suppress the outgoing type-3 packet generated below so followers do not
    # announce TPR again and create a command loop.
    _runtime_tp_command_until = now + 15.0
    _suppress_runtime_announce_until = now + 10.0
    uid_data = struct.pack('<I', nearest_uid)
    runtime_data = struct.pack('<IBB', nearest_uid, 3, 0)

    log(f"Plugin: TPR: Selecting runtime portal [{source_name}] (Leader: {player})")
    inject_joymax(0x7045, uid_data, False)
    Timer(1.5, inject_joymax, (0x704B, uid_data, False)).start()
    Timer(1.7, inject_joymax, (0x705A, runtime_data, False)).start()
    Timer(1.7, log, (f"Plugin: TPR: Teleporting through [{source_name}]",)).start()


def handle_reverse_command(player, text):
    """Handle reverse return commands for return, death, player, and zone targets."""
    rest = text[8:].strip()
    if not rest:
        log("Plugin: Invalid REVERSE command format; command skipped.")
        return

    parts = rest.split(' ', 1)
    sub_type = parts[0].lower()

    if sub_type == 'return':
        if reverse_return(0, ''):
            log(f"Plugin: REVERSE: Using reverse to the last return scroll location (Leader: {player})")
        else:
            log(f"Plugin: REVERSE: No reverse return scroll available (Leader: {player})")
    elif sub_type == 'death':
        if reverse_return(1, ''):
            log(f"Plugin: REVERSE: Using reverse to the last death location (Leader: {player})")
        else:
            log(f"Plugin: REVERSE: No reverse death scroll available (Leader: {player})")
    elif sub_type == 'player':
        if len(parts) < 2 or not parts[1].strip():
            log(f"Plugin: REVERSE player command requires a player name (Leader: {player}).")
            return
        target_name = parts[1].strip()
        if reverse_return(2, target_name):
            log(f"Plugin: REVERSE: Using reverse to player \"{target_name}\" location (Leader: {player})")
        else:
            log(f"Plugin: REVERSE: No reverse scroll available for player \"{target_name}\" (Leader: {player})")
    elif sub_type == 'zone':
        if len(parts) < 2 or not parts[1].strip():
            log(f"Plugin: REVERSE zone command requires a zone name (Leader: {player}).")
            return
        zone_name = parts[1].strip()
        if reverse_return(3, zone_name):
            log(f"Plugin: REVERSE: Using reverse to zone \"{zone_name}\" location (Leader: {player})")
        else:
            log(f"Plugin: REVERSE: No reverse scroll available for zone \"{zone_name}\" (Leader: {player})")
    else:
        log(f"Plugin: REVERSE command has an unknown type: '{sub_type}' (expected return/death/player/zone) (Leader: {player}).")


def handle_setpos_command(player, text):
    """Set the training position from arguments or use the character's current position."""
    rest = text[2:].strip()
    if not rest:
        p = get_position()
        set_training_position(p['region'], p['x'], p['y'], p['z'])
        log(f"Plugin: SP: Training area set to current position (X:{p['x']:.1f},Y:{p['y']:.1f}) (Leader: {player})")
        return
    try:
        parts = rest.split()
        x = float(parts[0])
        y = float(parts[1])
        region = int(parts[2]) if len(parts) >= 3 else 0
        z = float(parts[3]) if len(parts) >= 4 else 0
        set_training_position(region, x, y, z)
        log(f"Plugin: SP: Training area set to (X:{x:.1f},Y:{y:.1f}) (Leader: {player})")
    except (IndexError, ValueError):
        log(f"Plugin: SP: Wrong training area coordinates! (Leader: {player})")


def handle_setradius_command(player, text):
    """Set the training radius, using 35 meters when no value is supplied."""
    rest = text[2:].strip()
    if not rest:
        radius = 35
        set_training_radius(radius)
        log(f"Plugin: SR: Training radius reset to {radius} m. (Leader: {player})")
        return
    try:
        radius = abs(int(float(rest.split()[0])))
        set_training_radius(radius)
        log(f"Plugin: SR: Training radius set to {radius} m. (Leader: {player})")
    except (IndexError, ValueError):
        log(f"Plugin: SR: Wrong training radius value! (Leader: {player})")


def handle_follow_command(player, text):
    """Follow a party member at the requested distance; movement runs in event_loop()."""
    rest = text[2:].strip()
    char_name = player
    distance = 10
    if rest:
        parts = rest.split()
        try:
            if len(parts) >= 1:
                char_name = parts[0]
            if len(parts) >= 2:
                distance = float(parts[1])
        except ValueError:
            log(f"Plugin: FL: Follow distance incorrect (Leader: {player})")
            return
    start_follow(char_name, distance)
    log(f"Plugin: FL: Starting to follow [{char_name}] using [{distance}] as distance (Leader: {player})")


def handle_trace_command(player, text):
    """Trace a specified player; the bare T command traces the authorized leader."""
    target = text[2:].strip()
    if not target:
        target = player
    if start_trace(target):
        log(f"Plugin: T: Starting trace to [{target}] (Leader: {player})")


def handle_equip_command(player, text):
    """Equip the first matching item found in inventory slots 13 and above."""
    item_name = text[3:].strip()
    if not item_name:
        log(f"Plugin: EQ command requires an item name (Leader: {player}).")
        return
    if item_name.lower() == 'job':
        first_inventory_slot = 17 if get_locale() == 18 else 13
        item = GetJobItem(first_inventory_slot)
    else:
        item = GetItemByExpression(lambda n, s: item_name in n or item_name == s, 13)
    if item:
        EquipItem(item)
    else:
        log(f"Plugin: EQ: Item '{item_name}' was not found in the inventory (Leader: {player}).")


def handle_unequip_command(player, text):
    """Unequip the first matching item found in equipment slots 0 through 12."""
    item_name = text[3:].strip()
    if not item_name:
        log(f"Plugin: UQ command requires an item name (Leader: {player}).")
        return
    if item_name.lower() == 'job':
        item = GetJobItem(8, 8)
    else:
        item = GetItemByExpression(lambda n, s: item_name in n or item_name == s, 0, 12)
    if item:
        UnequipItem(item)
    else:
        log(f"Plugin: UQ: Equipped item '{item_name}' was not found (Leader: {player}).")


def handle_use_command(player, text):
    """Use the first matching item found in inventory slots 13 and above."""
    item_name = text[4:].strip()
    if not item_name:
        log(f"Plugin: USE command requires an item name (Leader: {player}).")
        return
    item = GetItemByExpression(lambda n, s: item_name in n or item_name == s, 13)
    if item:
        UseItem(item)
    else:
        log(f"Plugin: USE: Item '{item_name}' was not found in the inventory (Leader: {player}).")


def handle_sort_command(player):
    """Request phBot's documented asynchronous inventory sort operation."""
    try:
        if sort_inventory():
            log(f"Plugin: SORT: Inventory sorting requested (Leader: {player})")
        else:
            log(f"Plugin: SORT: Inventory sorting request was rejected (Leader: {player})")
    except Exception as e:
        log(f"Plugin: SORT: Inventory sorting failed (Leader: {player}) - {e}")


def handle_repair_command(player):
    """Use one Repair Hammer through the existing locale-aware item-use path."""
    try:
        inventory = get_inventory() or {}
    except Exception as e:
        log(f"Plugin: REPAIR: Inventory could not be read (Leader: {player}) - {e}")
        return
    items = inventory.get('items')
    if not isinstance(items, list):
        log(f"Plugin: REPAIR: Inventory is not ready (Leader: {player})")
        return

    repair_hammer = None
    for slot, item in enumerate(items):
        if slot < 13 or not item:
            continue
        display_name = (item.get('name') or '').strip().lower()
        servername = (item.get('servername') or '').upper()
        if display_name == 'repair hammer' or ('REPAIR' in servername and 'HAMMER' in servername):
            repair_hammer = dict(item)
            repair_hammer['slot'] = slot
            break

    if not repair_hammer:
        log(f"Plugin: REPAIR: Repair Hammer was not found in the inventory (Leader: {player})")
        return

    if UseItem(repair_hammer):
        log(f"Plugin: REPAIR: Repair Hammer use requested from slot {repair_hammer['slot']} (Leader: {player})")
    else:
        log(f"Plugin: REPAIR: Repair Hammer could not be used (Leader: {player})")


def _is_pick_pet_scroll(item):
    """Identify a pick-pet summon scroll without relying on its display name."""
    servername = str(item.get('servername') or '').upper()
    return ('COS_P_' in servername and 'SCROLL' in servername
            and 'COS_P_EXTENSION' not in servername)


def _clock_priority(item):
    """Prefer the shortest explicitly named Clock duration, then the base Clock."""
    servername = str(item.get('servername') or '').upper()
    for days in (1, 3, 7, 15, 30):
        if '_%dD' % days in servername:
            return days
    return 9999


def handle_clock_command(player):
    """Use exactly one Clock of Reincarnation on the active or sole pick-pet scroll."""
    global clock_pending, clock_pending_slot, clock_pending_pet_slot
    global clock_previous_remaining, clock_deadline

    now = time.time()
    if clock_pending and now <= clock_deadline:
        log(f"Plugin: CLOCK: A Clock operation is already pending (Leader: {player})")
        return

    inventory = get_inventory() or {}
    items = inventory.get('items') or []
    clocks = []
    pick_scrolls = []

    for slot, item in enumerate(items):
        if slot < 13 or not item:
            continue
        servername = str(item.get('servername') or '').upper()
        entry = dict(item)
        entry['slot'] = slot
        if 'COS_P_EXTENSION' in servername:
            clocks.append(entry)
        elif _is_pick_pet_scroll(item):
            pick_scrolls.append(entry)

    if not clocks:
        log(f"Plugin: CLOCK: No Clock of Reincarnation was found (Leader: {player})")
        return

    active_pick_pets = [
        pet for pet in (get_pets() or {}).values()
        if pet and pet.get('type') == 'pick'
    ]
    target = None
    previous_remaining = None

    if active_pick_pets:
        active_pet = active_pick_pets[0]
        pet_servername = str(active_pet.get('servername') or '').upper()
        matches = [item for item in pick_scrolls
                   if pet_servername and pet_servername in
                   str(item.get('servername') or '').upper()]
        if len(matches) == 1:
            target = matches[0]
            previous_remaining = active_pet.get('remaining')
        else:
            log("Plugin: CLOCK: The active pick pet could not be matched uniquely "
                f"to its summon scroll (matches: {len(matches)}); command cancelled")
            return
    elif len(pick_scrolls) == 1:
        target = pick_scrolls[0]
        previous_remaining = target.get('expiration')
    else:
        log("Plugin: CLOCK: No active pick pet and the inventory does not contain "
            f"exactly one pick-pet scroll (found: {len(pick_scrolls)}); command cancelled")
        return

    # One command deliberately selects and injects one Clock only.
    clock = sorted(clocks, key=lambda item: (_clock_priority(item), item['slot']))[0]
    clock_slot = int(clock['slot'])
    pet_slot = int(target['slot'])
    if clock_slot > 255 or pet_slot > 255:
        log("Plugin: CLOCK: Inventory slot is outside the one-byte packet range; command cancelled")
        return

    clock_data = get_item(clock.get('model'))
    if not clock_data:
        log("Plugin: CLOCK: Static Clock item data is unavailable; command cancelled")
        return

    locale = get_locale()
    if locale == 18:
        packet = struct.pack(
            '<BBBBBB',
            clock_slot,
            (3 << 4) + int(bool(clock_data.get('cash_item'))),
            int(clock_data.get('tid1', 0)) * 4,
            int(clock_data.get('tid2', 0)),
            int(clock_data.get('tid3', 0)),
            pet_slot
        )
    else:
        use_tid = GetTIDFromItem(clock.get('model'))
        if use_tid is None:
            log("Plugin: CLOCK: Clock item-use TID is unavailable; command cancelled")
            return
        if locale == 22:
            # Verified vSRO capture:
            # [Clock slot][two-byte item-use TID][Pick Pet scroll slot].
            packet = struct.pack('<BHB', clock_slot, use_tid, pet_slot)
        else:
            packet = struct.pack('<BIB', clock_slot, use_tid, pet_slot)
    clock_pending = True
    clock_pending_slot = clock_slot
    clock_pending_pet_slot = pet_slot
    clock_previous_remaining = previous_remaining
    clock_deadline = now + 10.0
    inject_joymax(0x704C, packet, True)
    log("Plugin: CLOCK: Requested one [%s] from slot %d for pet scroll slot %d "
        "using locale %s packet [%s] (Leader: %s)" %
        (clock.get('name') or clock.get('servername'), clock_slot, pet_slot,
         locale, ' '.join('%02X' % value for value in packet), player))


def _is_devil_item(item):
    """Identify Devil, Angel, and Hero Spirit avatar items by stable servername families."""
    servername = str(item.get('servername') or '').upper()
    if 'AVATAR' not in servername:
        return False
    return any(marker in servername for marker in
               ('NASRUN', 'AMALRUN', 'LEGIONNASRUN', '_DEVIL'))


def _devilext_priority(item):
    """Prefer the shortest explicitly named Extension Gear duration."""
    servername = str(item.get('servername') or '').upper()
    for days in (3, 7, 15, 28, 30):
        if ('_%dD' % days) in servername or ('_%dDAY' % days) in servername:
            return days
    return 9999


def _reset_devilext_state():
    global devilext_state, devilext_gear_slot, devilext_devil_slot
    global devilext_was_equipped, devilext_deadline
    devilext_state = None
    devilext_gear_slot = None
    devilext_devil_slot = None
    devilext_was_equipped = False
    devilext_deadline = 0.0


def _use_devilext_gear():
    """Send one verified Extension Gear use request for the selected Devil slot."""
    global devilext_state, devilext_deadline
    if devilext_gear_slot is None or devilext_devil_slot is None:
        log("Plugin: DEVILEXT: Required inventory slots are unavailable; operation cancelled")
        _reset_devilext_state()
        return
    packet = (bytes([devilext_gear_slot]) + b'\x31\x0C\x0D\x10'
              + bytes([devilext_devil_slot]))
    devilext_state = 'using'
    devilext_deadline = time.time() + 10.0
    inject_joymax(0x704C, packet, True)
    log("Plugin: DEVILEXT: Requested exactly one Extension Gear from slot %d "
        "for Devil slot %d" % (devilext_gear_slot, devilext_devil_slot))


def _reequip_devilext_devil():
    """Restore a Devil that this command removed from equipment slot 4."""
    global devilext_state, devilext_deadline
    if devilext_devil_slot is None:
        log("Plugin: DEVILEXT: Devil slot is unknown; automatic re-equip is not possible")
        _reset_devilext_state()
        return
    devilext_state = 'equipping'
    devilext_deadline = time.time() + 10.0
    inject_joymax(0x7034, bytes([0x24, devilext_devil_slot, 0x04]), False)
    log("Plugin: DEVILEXT: Restoring Devil from slot %d" % devilext_devil_slot)


def handle_devilext_command(player):
    """Use one Extension Gear and preserve the Devil's initial equipped state."""
    global devilext_state, devilext_gear_slot, devilext_devil_slot
    global devilext_was_equipped, devilext_deadline

    if devilext_state:
        log(f"Plugin: DEVILEXT: An operation is already running (Leader: {player})")
        return

    items = (get_inventory() or {}).get('items') or []
    gears = []
    devils = []
    for slot, item in enumerate(items):
        if slot < 13 or not item:
            continue
        servername = str(item.get('servername') or '').upper()
        entry = dict(item)
        entry['slot'] = slot
        if 'NASRUN_EXTENSION' in servername:
            gears.append(entry)
        elif _is_devil_item(item):
            devils.append(entry)

    if not gears:
        log(f"Plugin: DEVILEXT: No Extension Gear was found (Leader: {player})")
        return
    if len(devils) > 1:
        log("Plugin: DEVILEXT: Multiple Devil/Nasrun items were found in inventory; "
            "target is ambiguous and the command was cancelled")
        return

    gear = sorted(gears, key=lambda item: (_devilext_priority(item), item['slot']))[0]
    devilext_gear_slot = int(gear['slot'])
    devilext_deadline = time.time() + 10.0

    if len(devils) == 1:
        devilext_devil_slot = int(devils[0]['slot'])
        devilext_was_equipped = False
        log("Plugin: DEVILEXT: Using the sole inventory Devil/Nasrun; it will remain unequipped")
        _use_devilext_gear()
        return

    # No Devil item is present in normal inventory. Ask the server to remove
    # the equipped Devil; its assigned inventory slot comes from 0xB034.
    devilext_was_equipped = True
    devilext_state = 'unequipping'
    inject_joymax(0x7034, bytes([0x23, 0x04, 0x23]), False)
    log(f"Plugin: DEVILEXT: Removing the equipped Devil (Leader: {player})")


def handle_recall_command(player, text):
    """Set recall at the named nearby town portal NPC."""
    town = text[3:].strip()
    if not town:
        log(f"Plugin: RC command requires a town name (Leader: {player}).")
        return
    npc_uid = GetNPCUniqueID(town)
    if npc_uid > 0:
        log(f"Plugin: RC: Designating recall to \"{town.title()}\"... (Leader: {player})")
        inject_joymax(0x7059, struct.pack('I', npc_uid), False)
    else:
        log(f"Plugin: RC: NPC '{town}' was not found nearby (Leader: {player}).")


# ______________________________ xControl.py'den Port Edilen Ek Komutlar ______________________________ #

def handle_chat_send_command(player, text):
    """Send a message through an All, Private, Party, Guild, Union, Note, Stall, or Global channel."""
    rest = text[4:].strip()
    args = rest.split(' ', 1)
    if len(args) != 2 or not args[0] or not args[1]:
        log(f"Plugin: Invalid CHAT command format; command skipped (Leader: {player}).")
        return

    t = args[0].lower()
    message = args[1]

    if t in ('private', 'note'):
        args_extra = message.split(' ', 1)
        if len(args_extra) != 2 or not args_extra[0] or not args_extra[1]:
            log(f"Plugin: CHAT {t} command requires a target and message (Leader: {player}).")
            return
        target, message = args_extra[0], args_extra[1]

    sent = False
    if t == 'all':
        sent = phBotChat.All(message)
    elif t == 'private':
        sent = phBotChat.Private(target, message)
    elif t == 'party':
        sent = phBotChat.Party(message)
    elif t == 'guild':
        sent = phBotChat.Guild(message)
    elif t == 'union':
        sent = phBotChat.Union(message)
    elif t == 'note':
        sent = phBotChat.Note(target, message)
    elif t == 'stall':
        sent = phBotChat.Stall(message)
    elif t == 'global':
        sent = phBotChat.Global(message)
    else:
        log(f"Plugin: CHAT command has an unknown channel type: '{t}' (Leader: {player}).")
        return

    if sent:
        log(f"Plugin: CHAT: Message sent ({t}) (Leader: {player})")
    else:
        log(f"Plugin: CHAT: Failed to send message ({t}) (Leader: {player})")


def handle_inject_command(player, text):
    """Run the existing packet injector from an authorized leader chat command."""
    rest = text[7:].strip()
    if not rest:
        log(f"Plugin: Invalid INJECT command format; command skipped (Leader: {player}).")
        return
    args = ['INJECT'] + rest.split()
    try:
        inject(args)
    except (ValueError, IndexError) as e:
        log(f"Plugin: Invalid INJECT command: {e} (Leader: {player}).")


def handle_moveon_command(player, text):
    """Move to a random point within the supplied radius, defaulting to 10 meters."""
    rest = text[6:].strip()
    radius = 10
    if rest:
        try:
            radius = abs(int(float(rest.split()[0])))
        except (IndexError, ValueError):
            log(f"Plugin: MOVEON radius value is invalid (Leader: {player}).")
            return
    p_x = random.uniform(-radius, radius)
    p_y = random.uniform(-radius, radius)
    p = get_position()
    dest_x = p_x + p['x']
    dest_y = p_y + p['y']
    move_to(dest_x, dest_y, p['z'])
    log(f"Plugin: MOVEON: Moving to a random position (X:{dest_x:.1f},Y:{dest_y:.1f}) (Leader: {player})")


def handle_setscript_command(player, text):
    """Set the training script path, or clear it when no path is supplied."""
    rest = text[9:].strip()
    if not rest:
        set_training_script('')
        log(f"Plugin: SETSCRIPT: Training script reset (Leader: {player})")
        return
    set_training_script(rest)
    log(f"Plugin: SETSCRIPT: Training script set to '{rest}' (Leader: {player})")


def handle_fsh_command(player, text):
    """Run an FScriptHelper recording through phBot's walk-script command bridge."""
    rest = text[3:].strip()
    if not rest:
        log("Plugin: FSH: Usage: FSH [true|false] command_name")
        return

    stop_during = True
    parts = rest.split(None, 1)
    first = parts[0].lower()
    if first in ('true', 'false'):
        if len(parts) < 2 or not parts[1].strip():
            log("Plugin: FSH: Command name is required. Usage: FSH [true|false] command_name")
            return
        stop_during = first == 'true'
        command_name = parts[1].strip()
    else:
        command_name = rest

    if ',' in command_name or '\r' in command_name or '\n' in command_name:
        log(f"Plugin: FSH: Invalid command name '{command_name}'; commas and line breaks are not allowed.")
        return

    stop_text = 'true' if stop_during else 'false'
    script_line = 'FSH_NPC,%s,%s' % (command_name, stop_text)
    log(f"Plugin: FSH requested by Leader [{player}]: {command_name} (stop_bot={stop_text})")
    start_script(script_line)


def handle_profile_command(player, text):
    """Handle SETPROFILE (and legacy PROFILE) using phBot's set_profile API."""
    if text.upper().startswith('SETPROFILE'):
        rest = text[10:].strip()
    else:
        rest = text[7:].strip()
    profile_name = rest if rest else 'Default'
    if set_profile(profile_name):
        log(f"Plugin: SETPROFILE: Switched to profile '{profile_name}' (Leader: {player})")
    else:
        log(f"Plugin: SETPROFILE: Failed to switch to profile '{profile_name}' (Leader: {player}).")


def start_pick_all(player):
    global pick_all_active, pick_all_target_id, pick_all_last_request_at

    if pick_all_active:
        log(f"Plugin: PA: Pick All is already active (Leader: {player})")
        return

    drops = get_drops() or {}
    if not drops:
        log(f"Plugin: PA: No nearby drops match the phBot pick filter (Leader: {player})")
        return

    pick_all_active = True
    pick_all_target_id = None
    pick_all_last_request_at = 0.0
    log(f"Plugin: PA: Pick All started for [{len(drops)}] nearby drop(s) (Leader: {player})")


def stop_pick_all(player=None, reason=None):
    global pick_all_active, pick_all_target_id, pick_all_last_request_at

    was_active = pick_all_active
    pick_all_active = False
    pick_all_target_id = None
    pick_all_last_request_at = 0.0

    if reason and was_active:
        log("Plugin: PA: Pick All stopped - " + reason)
    elif was_active:
        log(f"Plugin: SPA: Pick All stopped (Leader: {player})")
    elif not reason:
        log(f"Plugin: SPA: Pick All was not active (Leader: {player})")


def process_pick_all():
    global pick_all_target_id, pick_all_last_request_at

    if not pick_all_active:
        return

    character = get_character_data()
    if not character or character.get('hp', 0) <= 0:
        stop_pick_all(reason="character is unavailable or dead")
        return

    drops = get_drops() or {}
    eligible = []
    position = get_position()
    for drop_id, drop in drops.items():
        if not isinstance(drop, dict) or drop.get('can_pick') is False:
            continue
        try:
            distance = GetDistance(position['x'], position['y'], float(drop['x']), float(drop['y']))
            eligible.append((distance, drop_id, drop))
        except (KeyError, TypeError, ValueError):
            continue

    if not eligible:
        stop_pick_all(reason="no nearby drops remain")
        return

    distance, drop_id, drop = min(eligible, key=lambda entry: entry[0])
    if pick_all_target_id != drop_id:
        pick_all_target_id = drop_id
        pick_all_last_request_at = 0.0
        log(f"Plugin: PA: Moving to [{drop.get('name', 'Unknown drop')}]")

    if distance > PICK_ALL_RANGE_METERS:
        move_to(float(drop['x']), float(drop['y']), float(drop.get('z') or 0.0))
        return

    now = time.time()
    if now - pick_all_last_request_at < PICK_ALL_REQUEST_INTERVAL:
        return

    packet = b'\x01\x02\x01' + struct.pack('<I', int(drop_id))
    inject_joymax(0x7074, packet, False)
    pick_all_last_request_at = now
    log(f"Plugin: PA: Pickup requested for [{drop.get('name', 'Unknown drop')}]")


def start_item_storage_claim(player):
    """Start the asynchronous Item Storage list -> claim-all flow."""
    global tis_active, tis_claim_pending, tis_item_count, tis_deadline

    if tis_active or tis_claim_pending:
        log(f"Plugin: TIS: An Item Storage operation is already running (Leader: {player})")
        return

    tis_active = True
    tis_claim_pending = False
    tis_item_count = 0
    tis_deadline = time.time() + 15.0
    log(f"Plugin: TIS: Checking Item Storage (Leader: {player})")
    inject_joymax(0x7557, struct.pack('<B', 1), False)


def handle_item_storage_packet(opcode, data):
    """Handle Item Storage list/claim replies. Returns True when consumed by TIS."""
    global tis_active, tis_claim_pending, tis_item_count, tis_deadline

    if opcode == 0xB557 and tis_active:
        if len(data) < 4:
            log("Plugin: TIS: Invalid Item Storage list response; operation cancelled")
            tis_active = False
            tis_deadline = 0.0
            return True

        if data[0] != 1:
            log(f"Plugin: TIS: Item Storage list request failed (status: {data[0]})")
            tis_active = False
            tis_deadline = 0.0
            return True

        page_count = data[1]
        current_page = data[2]
        page_item_count = data[3]
        tis_item_count += page_item_count
        tis_deadline = time.time() + 15.0
        log(f"Plugin: TIS: Page {current_page}/{page_count}, items on page: {page_item_count}")

        if current_page < page_count:
            Timer(1.0, inject_joymax, (0x7557, struct.pack('<B', current_page + 1), False)).start()
            return True

        tis_active = False
        if tis_item_count == 0:
            tis_deadline = 0.0
            log("Plugin: TIS: Item Storage is empty; nothing to claim")
            return True

        tis_claim_pending = True
        tis_deadline = time.time() + 15.0
        log(f"Plugin: TIS: List complete ({tis_item_count} items); sending Claim All")
        inject_joymax(0x7558, b'\x00\x00\x00\x00\x00\x00\x00\x00', False)
        return True

    if opcode == 0xB558 and tis_claim_pending:
        tis_claim_pending = False
        tis_deadline = 0.0
        if not data:
            log("Plugin: TIS: Empty Claim All response received")
        elif data[0] == 2:
            log("Plugin: TIS: Claim All failed; inventory may be full")
        else:
            log(f"Plugin: TIS: Claim All response received (status: {data[0]})")
        return True

    return False


# ______________________________ Events ______________________________ #

def handle_chat(t, player, msg):
    if not msg:
        return False

    if t == 11:
        msg = msg.split(': ', 1)[1]

    text = msg.strip()
    msg_upper = text.upper()

    # Some phBot builds echo the character's own party message through this
    # callback. Treat that as delivery evidence, without relying on it for retry.
    if (_queued_tp_announcement and
            t == CHAT_PARTY and
            text == _queued_tp_announcement.get('message') and
            (not player or is_own_character(player))):
        _queued_tp_announcement['confirmed'] = True

    # Allow party/guild members to register themselves as an FControl leader.
    if t in (CHAT_PARTY, CHAT_GUILD) and msg_upper == "SETFCONTROLLEADER":
        if ignore_setfcontrolleader:
            log(f"Plugin: SETFCONTROLLEADER ignored because the command is disabled (Sender: {player})")
            return True
        if player:
            if is_own_character(player):
                log(f"Plugin: SETFControlLeader ignored; [{player}] is this character")
            elif add_chat_leader(player):
                log(f"Plugin: SETFControlLeader accepted from [{player}]")
            else:
                log(f"Plugin: SETFControlLeader ignored; [{player}] is already a leader or could not be saved")
        return True

    is_leader = bool(lstLeadersData and player and isLeader(player))

    # Only an already-authorized leader can grant or revoke leader access.
    command_parts = text.split()
    if command_parts and command_parts[0].upper() in ('ALEADER', 'RLEADER'):
        leader_command = command_parts[0].upper()
        if not is_leader:
            log(f"Plugin: {leader_command} ignored; sender [{player}] is not an authorized leader")
            return True
        if len(command_parts) != 2:
            log(f"Plugin: Usage: {command_parts[0]} CharNick (Leader: {player})")
            return True

        target_name = command_parts[1]
        if leader_command == 'ALEADER':
            if is_own_character(target_name):
                log(f"Plugin: ALEADER ignored; [{target_name}] is this character (Leader: {player})")
            elif add_chat_leader(target_name):
                log(f"Plugin: ALEADER accepted for [{target_name}] (Leader: {player})")
            else:
                log(f"Plugin: ALEADER ignored; [{target_name}] already exists or could not be saved (Leader: {player})")
        elif remove_chat_leader(target_name):
            log(f"Plugin: RLEADER accepted for [{target_name}] (Leader: {player})")
        else:
            log(f"Plugin: RLEADER ignored; [{target_name}] was not found or could not be saved (Leader: {player})")
        return True

    if msg_upper.startswith("TPR"):
        log(f"Plugin: TPR chat received | channel={t} | sender={player} | authorized={bool(is_leader)} | message={text}")

    # Handle !c command
    if text.lower().startswith("!c"):
        if not is_leader:
            return True
        return handle_training_area_command(player, text)

    # Handle other leader commands
    leader_commands = {"DS", "T", "SIT", "N", "S", "SS", "Q1", "Q2", "Q3", "RE", "D", "M", "COME", "NF", "ZK", "DC", "LP", "TIS", "SORT", "REPAIR", "CLOCK", "DEVILEXT", "PA", "SPA"}
    if msg_upper in leader_commands:
        if not is_leader:
            return True
        if msg_upper == "DS":
            log("Plugin: Attempting dismount from Leader [" + str(player) + "]")
            if DismountPet():
                log("Plugin: Sent dismount command for mounted pet")
            else:
                log("Plugin: No mounted pet found to dismount")
            return True
        elif msg_upper == "M":
            log("Plugin: Mounting pet from Leader [" + str(player) + "]")
            pet_type = "transport"
            if len(text) > 1:
                parts = text.split()
                if len(parts) > 1:
                    pet_type = parts[1].lower()
            if MountPet(pet_type):
                log("Plugin: Mounted pet [" + pet_type + "]")
            else:
                log("Plugin: Could not mount pet [" + pet_type + "]")
            return True
        elif msg_upper == "D":
            log("Plugin: Dismounting pet from Leader [" + str(player) + "]")
            if DismountPet():
                log("Plugin: Dismounted pet")
            else:
                log("Plugin: No mounted pet to dismount")
            return True
        elif msg_upper == "T":
            log("Plugin: Start trace from Leader [" + str(player) + "]")
            start_trace(player)
        elif msg_upper == "SIT":
            log("Plugin: Sit/Stand from Leader [" + str(player) + "]")
            inject_joymax(0x704F, b'\x04', False)
        elif msg_upper == "N":
            log("Plugin: Stop trace from Leader [" + str(player) + "]")
            stop_trace()
        elif msg_upper == "S":
            log("Plugin: Start bot from Leader [" + str(player) + "]")
            start_bot()
        elif msg_upper == "SS":
            log("Plugin: Stop bot from Leader [" + str(player) + "]")
            stop_bot()
        elif msg_upper == "Q1":
            _leader_teleport_sequence("Q1", Q1_ROUTES)
        elif msg_upper == "Q2":
            _leader_teleport_sequence("Q2", Q2_ROUTES)
        elif msg_upper == "Q3":
            _leader_teleport_sequence("Q3", Q3_ROUTES)
        elif msg_upper == "RE":
            log("Plugin: Return scroll from Leader [" + str(player) + "]")
            character = get_character_data()
            if character['hp'] == 0:
                log('Plugin: Resurrecting at town...')
                inject_joymax(0x3053, b'\x01', False)
            else:
                log('Plugin: Using return scroll...')
                use_return_scroll()
        elif msg_upper == "COME":
            log("Plugin: COME command from Leader [" + str(player) + "] - using reverse return scroll")
            if reverse_return(2, player):
                log("Plugin: Reverse return scroll used, returning to Leader [" + str(player) + "]")
            else:
                log("Plugin: No reverse return scroll available for Leader [" + str(player) + "]")
        elif msg_upper == "NF":
            if stop_follow():
                log(f"Plugin: NF: Following stopped (Leader: {player})")
            else:
                log(f"Plugin: NF: Following was not active (Leader: {player})")
        elif msg_upper == "ZK":
            log(f"Plugin: ZK: Using Berserker mode (Leader: {player})")
            inject_joymax(0x70A7, b'\x01', False)
        elif msg_upper == "DC":
            log(f"Plugin: DC: Disconnecting... (Leader: {player})")
            disconnect()
        elif msg_upper == "LP":
            if get_party():
                log(f"Plugin: LP: Leaving the party... (Leader: {player})")
                inject_joymax(0x7061, b'', False)
            else:
                log(f"Plugin: LP: Not in a party (Leader: {player})")
        elif msg_upper == "TIS":
            start_item_storage_claim(player)
        elif msg_upper == "SORT":
            handle_sort_command(player)
        elif msg_upper == "REPAIR":
            handle_repair_command(player)
        elif msg_upper == "CLOCK":
            handle_clock_command(player)
        elif msg_upper == "DEVILEXT":
            handle_devilext_command(player)
        elif msg_upper == "PA":
            start_pick_all(player)
        elif msg_upper == "SPA":
            stop_pick_all(player=player)
        return True

    if is_leader and msg_upper.startswith("TP "):
        handle_tp_command(player, text)
        return True

    if is_leader and msg_upper.startswith("TPR "):
        handle_runtime_tp_command(player, text)
        return True

    if is_leader and msg_upper.startswith("REVERSE "):
        handle_reverse_command(player, text)
        return True

    if is_leader and msg_upper.startswith("SP"):
        handle_setpos_command(player, text)
        return True

    if is_leader and msg_upper.startswith("SR"):
        handle_setradius_command(player, text)
        return True

    if is_leader and msg_upper.startswith("FL"):
        handle_follow_command(player, text)
        return True

    if is_leader and msg_upper.startswith("T "):
        handle_trace_command(player, text)
        return True

    if is_leader and msg_upper.startswith("EQ "):
        handle_equip_command(player, text)
        return True

    if is_leader and msg_upper.startswith("UQ "):
        handle_unequip_command(player, text)
        return True

    if is_leader and msg_upper.startswith("USE "):
        handle_use_command(player, text)
        return True

    if is_leader and msg_upper.startswith("RC "):
        handle_recall_command(player, text)
        return True

    if is_leader and msg_upper.startswith("CHAT "):
        handle_chat_send_command(player, text)
        return True

    if is_leader and msg_upper.startswith("INJECT "):
        handle_inject_command(player, text)
        return True

    if is_leader and msg_upper.startswith("MOVEON"):
        handle_moveon_command(player, text)
        return True

    if is_leader and msg_upper.startswith("SETSCRIPT"):
        handle_setscript_command(player, text)
        return True

    if is_leader and (msg_upper == "FSH" or msg_upper.startswith("FSH ")):
        handle_fsh_command(player, text)
        return True

    if is_leader and (msg_upper == "SETPROFILE" or msg_upper.startswith("SETPROFILE ")):
        handle_profile_command(player, text)
        return True

    if is_leader and (msg_upper == "PROFILE" or msg_upper.startswith("PROFILE ")):
        handle_profile_command(player, text)
        return True

    # Handle MOVEATTACK / GETPOS / MOVE commands (leaders only)
    if is_leader or t == 100:
        msg_stripped = text.rstrip()
        if msg_stripped.startswith("MOVEATTACK"):
            try:
                parts = msg_stripped[10:].split()
                if len(parts) >= 2:
                    x = float(parts[0])
                    y = float(parts[1])
                    z = float(parts[2]) if len(parts) >= 3 else 0
                    move_and_attack(x, y, z)
                else:
                    log("Plugin: Usage: MOVEATTACK X Y [Z]")
            except Exception as e:
                log("Plugin: Invalid coordinates! Error: " + str(e))
            return True
        elif msg_stripped == "GETPOS":
            pos = get_position()
            phBotChat.Private(player, 'My position is (X:%.1f,Y:%.1f,Z:%.1f,Region:%d)' % (pos['x'], pos['y'], pos['z'], pos['region']))
            return True
        elif msg_stripped.startswith("MOVE"):
            try:
                parts = msg_stripped[4:].split()
                if len(parts) >= 2:
                    x = float(parts[0])
                    y = float(parts[1])
                    z = float(parts[2]) if len(parts) >= 3 else 0
                    log('Plugin: Walking to (X:%.1f,Y:%.1f)' % (x, y))
                    current_pos = get_position()
                    script = generate_script(current_pos['region'], x, y, z)
                    if script:
                        start_script('\n'.join(script))
                    else:
                        log('Plugin: Could not generate path, using direct movement')
                        move_to(x, y, z)
                else:
                    log("Plugin: Usage: MOVE X Y [Z]")
            except Exception as e:
                log("Plugin: Invalid coordinates! Error: " + str(e))
            return True

    return False


def handle_silkroad(opcode, data):
    if cbxShowClient:
        if CanShowPacket(opcode):
            log("Client: (Opcode) 0x" + '{:02X}'.format(opcode) + " (Data) " + ("None" if not data else ' '.join(
                '{:02X}'.format(x) for x in data)))

    if opcode == 0x7045 and announce_own_teleports:
        try:
            _capture_selected_teleporter(data)
        except Exception as e:
            log(f"Plugin: TP source cache error: {e}")

    if opcode == 0x705A and announce_own_teleports:
        try:
            _capture_own_teleport_request(data)
        except Exception as e:
            log(f"Plugin: TP announcement capture error: {e}")

    return True


def _capture_selected_teleporter(data):
    """Cache the selected NPC before a runtime portal disappears during scene transition."""
    global _last_selected_tp_uid, _last_selected_tp_source, _last_selected_tp_at

    if len(data) < 4:
        return

    uid = struct.unpack_from('<I', data, 0)[0]
    npc = (get_npcs() or {}).get(uid)
    if not npc:
        return

    source_name = npc.get('servername') or npc.get('name')
    if not source_name:
        return

    _last_selected_tp_uid = uid
    _last_selected_tp_source = source_name
    _last_selected_tp_at = time.time()


def _capture_own_teleport_request(data):
    """Capture standard type-2 and six-byte runtime-portal type-3 teleport requests."""
    global _pending_tp_source, _pending_tp_destination_id, _pending_tp_armed_at
    global _pending_tp_is_runtime, _pending_tp_origin_region
    global _suppress_runtime_announce_until

    if len(data) < 5:
        return

    teleporter_uid = struct.unpack_from('<I', data, 0)[0]
    teleport_type = data[4]

    if teleport_type == 3:
        if len(data) < 6:
            return
        if time.time() <= _suppress_runtime_announce_until:
            _suppress_runtime_announce_until = 0.0
            log("Plugin: TPR: Automatic follower teleport captured; repeat announcement suppressed")
            return
        destination_id = None
        is_runtime = True
    elif teleport_type == 2:
        if len(data) < 9:
            return
        destination_id = struct.unpack_from('<I', data, 5)[0]
        is_runtime = False
    else:
        return

    npcs = get_npcs() or {}
    npc = npcs.get(teleporter_uid)
    source_name = (npc.get('servername') or npc.get('name')) if npc else None

    # Runtime portals can disappear from get_npcs() as soon as teleport begins.
    # Fall back to the matching NPC cached from the immediately preceding 0x7045.
    if (not source_name and is_runtime and
            _last_selected_tp_uid == teleporter_uid and
            (time.time() - _last_selected_tp_at) <= 10.0):
        source_name = _last_selected_tp_source

    if not source_name:
        log(f"Plugin: TP announcement skipped; no source name found for UID [{teleporter_uid}]")
        return

    _pending_tp_source = source_name
    _pending_tp_destination_id = destination_id
    _pending_tp_armed_at = time.time()
    _pending_tp_is_runtime = is_runtime
    position = get_position() or {}
    _pending_tp_origin_region = position.get('region')

    if is_runtime:
        log(f"Plugin: Runtime portal captured -> Source: '{source_name}'. "
            f"The announcement will be sent via {get_announce_channel()} after teleportation is confirmed.")
    else:
        log(f"Plugin: Teleport captured -> Source: '{source_name}' | Destination ID: {destination_id}. "
            f"The announcement will be sent via {get_announce_channel()} after teleportation is confirmed.")


def handle_joymax(opcode, data):
    global clock_pending, clock_pending_slot, clock_pending_pet_slot
    global clock_previous_remaining, clock_deadline
    global devilext_state, devilext_devil_slot, devilext_deadline

    handle_item_storage_packet(opcode, data)
    if opcode == 0xB04C and clock_pending and data:
        if len(data) >= 2 and data[1] == clock_pending_slot:
            if data[0] == 1:
                log("Plugin: CLOCK: Server accepted the Clock use request; "
                    "pet duration update is expected")
            else:
                log("Plugin: CLOCK: Server rejected the Clock use request "
                    "(status: %d)" % data[0])
            clock_pending = False
            clock_pending_slot = None
            clock_pending_pet_slot = None
            clock_previous_remaining = None
            clock_deadline = 0.0

    if opcode == 0xB034 and devilext_state == 'unequipping' and data:
        if len(data) >= 4 and data[1] == 0x23:
            if data[0] == 1:
                devilext_devil_slot = data[3]
                log("Plugin: DEVILEXT: Devil moved to inventory slot %d" % devilext_devil_slot)
                devilext_state = 'use_pending'
                Timer(0.5, _use_devilext_gear).start()
            else:
                log("Plugin: DEVILEXT: Could not remove an equipped Devil (status: %d)" % data[0])
                _reset_devilext_state()

    elif opcode == 0xB04C and devilext_state == 'using' and data:
        if len(data) >= 2 and data[1] == devilext_gear_slot:
            if data[0] == 1:
                log("Plugin: DEVILEXT: Server accepted the Extension Gear use request")
            else:
                log("Plugin: DEVILEXT: Server rejected the Extension Gear request "
                    "(status: %d)" % data[0])
            if devilext_was_equipped:
                devilext_state = 'restore_pending'
                Timer(0.5, _reequip_devilext_devil).start()
            else:
                _reset_devilext_state()

    elif opcode == 0xB034 and devilext_state == 'equipping' and data:
        if len(data) >= 4 and data[1] == 0x24 and data[2] == devilext_devil_slot:
            if data[0] == 1:
                log("Plugin: DEVILEXT: Devil restored successfully; operation complete")
            else:
                log("Plugin: DEVILEXT: Extension finished, but Devil could not be restored "
                    "(status: %d, inventory slot: %d)" %
                    (data[0], devilext_devil_slot))
            _reset_devilext_state()
    if cbxShowServer:
        if CanShowPacket(opcode):
            log("Server: (Opcode) 0x" + '{:02X}'.format(opcode) + " (Data) " + ("None" if not data else ' '.join(
                '{:02X}'.format(x) for x in data)))
    return True


def format_bytes(value):
    if not value:
        return ""
    return ' '.join('{:02X}'.format(x) for x in value)


def refresh_display_fields():
    pass


def _process_queued_tp_announcement():
    """Wait for stable post-teleport character data before sending chat."""
    global _queued_tp_announcement

    pending = _queued_tp_announcement
    if not pending:
        return

    now = time.time()
    if pending.get('sent'):
        if pending.get('confirmed'):
            log("Plugin: TP announcement observed in Party chat.")
            _queued_tp_announcement = None
        elif now - pending.get('sent_at', now) >= 5.0:
            # Own-message echoes are not guaranteed by every phBot build.
            _queued_tp_announcement = None
        return

    if now > pending['deadline']:
        log("Plugin: TP announcement canceled; the destination scene did not become ready in time.")
        _queued_tp_announcement = None
        return

    character = get_character_data() or {}
    position = get_position() or {}
    region = position.get('region')
    data_ready = bool(
        character.get('name') and
        region is not None and
        position.get('x') is not None and
        position.get('y') is not None
    )

    if not data_ready:
        pending['saw_unready'] = True
        pending['stable_region'] = None
        pending['stable_checks'] = 0
        pending['ready_at'] = None
        return

    origin_region = pending.get('origin_region')
    transition_observed = (
        pending['saw_unready'] or
        origin_region is None or
        region != origin_region or
        now >= pending['fallback_at']
    )
    if not transition_observed:
        return

    if region == pending.get('stable_region'):
        pending['stable_checks'] += 1
    else:
        pending['stable_region'] = region
        pending['stable_checks'] = 1
        pending['ready_at'] = None

    if pending['stable_checks'] < TP_SCENE_STABLE_CHECKS:
        return

    if pending['ready_at'] is None:
        pending['ready_at'] = now + TP_SCENE_SAFETY_DELAY
        return
    if now < pending['ready_at']:
        return

    if pending['is_runtime']:
        sent = _send_runtime_tp_announcement(pending['source'])
    else:
        sent = _send_tp_announcement(pending['source'], pending['destination_id'])
    if not sent:
        pending['attempts'] += 1
        if pending['attempts'] >= 3:
            _queued_tp_announcement = None
        else:
            pending['ready_at'] = now + 2.0
        return
    pending['sent'] = True
    pending['sent_at'] = now


# Called every 500ms
def event_loop():
    global attackMode, targetX, targetY, targetZ, _last_seen_announce_channel
    global tis_active, tis_claim_pending, tis_deadline
    global clock_pending, clock_pending_slot, clock_pending_pet_slot
    global clock_previous_remaining, clock_deadline
    global devilext_state, devilext_deadline
    global _runtime_tp_command_until, _suppress_runtime_announce_until
    global _announce_settings_loaded_for
    global _leaders_loaded_for, _queued_tp_announcement

    _process_queued_tp_announcement()

    process_pick_all()

    if (tis_active or tis_claim_pending) and tis_deadline and time.time() > tis_deadline:
        tis_active = False
        tis_claim_pending = False
        tis_deadline = 0.0
        log("Plugin: TIS: Timed out waiting for the Item Storage server response")

    if clock_pending and clock_deadline and time.time() > clock_deadline:
        clock_pending = False
        clock_pending_slot = None
        clock_pending_pet_slot = None
        clock_previous_remaining = None
        clock_deadline = 0.0
        log("Plugin: CLOCK: Timed out waiting for the server response")

    if devilext_state and devilext_deadline and time.time() > devilext_deadline:
        timed_out_state = devilext_state
        if timed_out_state == 'using' and devilext_was_equipped and devilext_devil_slot is not None:
            log("Plugin: DEVILEXT: Extension response timed out; attempting to restore Devil")
            _reequip_devilext_devil()
        else:
            log("Plugin: DEVILEXT: Timed out during [%s]; operation stopped" % timed_out_state)
            _reset_devilext_state()

    now = time.time()
    if _runtime_tp_command_until and now > _runtime_tp_command_until:
        _runtime_tp_command_until = 0.0
    if _suppress_runtime_announce_until and now > _suppress_runtime_announce_until:
        _suppress_runtime_announce_until = 0.0

    # Combobox için "değişti" event'i phBot'ta belgeli olmadığından, seçili kanalı burada
    # (zaten var olan 500ms event_loop() hook'unda) yoklayıp değiştiyse config'e kaydediyoruz.
    # isJoined() kontrolü, karaktere özel config dosyası (getConfig()) henüz belli değilken
    # yanlışlıkla "default_leaders.json"a yazmayı önlüyor.
    if isJoined():
        leader_config = getConfig()
        if leader_config and leader_config != _leaders_loaded_for:
            loadLeadersConfigs()
        announce_config = getAnnounceConfig()
        if announce_config and announce_config != _announce_settings_loaded_for:
            load_announce_settings()
        current_announce_channel = get_announce_channel()
        if current_announce_channel != _last_seen_announce_channel:
            _last_seen_announce_channel = current_announce_channel
            save_announce_settings()

    # FL/NF komutlarıyla başlatılan takip hareketi - attackMode bloğundan önce çalıştırılıyor
    # çünkü o blok içindeki erken "return" bu koda hiç ulaşılmamasına sebep olabilir.
    if followActivated:
        player_pos = near_follow_player(followPlayer)
        if player_pos:
            if followDistance > 0:
                p = get_position()
                playerDistance = round(GetDistance(p['x'], p['y'], player_pos['x'], player_pos['y']), 2)
                if followDistance < playerDistance:
                    x_unit = (player_pos['x'] - p['x']) / playerDistance
                    y_unit = (player_pos['y'] - p['y']) / playerDistance
                    movementDistance = playerDistance - followDistance
                    log("Plugin: Following " + followPlayer + "...")
                    move_to(movementDistance * x_unit + p['x'], movementDistance * y_unit + p['y'], 0)
            else:
                log("Plugin: Following " + followPlayer + "...")
                move_to(player_pos['x'], player_pos['y'], 0)

    if attackMode:
        character = get_character_data()
        if character and character.get('hp', 0) > 0:
            current_pos = get_position()
            if targetX != 0 or targetY != 0:
                distance = GetDistance(current_pos['x'], current_pos['y'], targetX, targetY)
                if distance > 2:
                    return
                log('Plugin: Reached target position, setting training area...')
                set_training_position(current_pos['region'], targetX, targetY, targetZ)
                log('Plugin: Training area set to (X:%.1f,Y:%.1f)' % (targetX, targetY))
                log('Plugin: Starting bot...')
                start_bot()
                attackMode = False
                targetX = 0
                targetY = 0
                targetZ = 0


# Called when the bot successfully connects to the game server
def connected():
    global inGame, _announce_settings_loaded_for, _leaders_loaded_for
    global _queued_tp_announcement
    inGame = None
    _announce_settings_loaded_for = None
    _leaders_loaded_for = None
    _queued_tp_announcement = None
    stop_pick_all(reason="connection changed")

# Called when the character enters the game world
def joined_game():
    global current_character_name
    character_data = get_character_data()
    if character_data and isinstance(character_data, dict) and "name" in character_data:
        current_character_name = character_data.get("name", "Unknown")
    update_account_info()
    loadLeadersConfigs()
    load_announce_settings()
    loadOpcodeConfigs()


def teleported():
    """Send any pending teleport announcement after phBot reports a completed teleport."""
    global _pending_tp_source, _pending_tp_destination_id, _pending_tp_armed_at
    global _pending_tp_is_runtime, _pending_tp_origin_region
    global _runtime_tp_command_until, _suppress_runtime_announce_until
    global _queued_tp_announcement

    source = _pending_tp_source
    destination_id = _pending_tp_destination_id
    armed_at = _pending_tp_armed_at
    is_runtime = _pending_tp_is_runtime
    origin_region = _pending_tp_origin_region

    _pending_tp_source = None
    _pending_tp_destination_id = None
    _pending_tp_armed_at = None
    _pending_tp_is_runtime = False
    _pending_tp_origin_region = None
    _runtime_tp_command_until = 0.0
    _suppress_runtime_announce_until = 0.0

    if source is None:
        return

    if armed_at is not None and (time.time() - armed_at) > TP_ANNOUNCE_TIMEOUT:
        return

    # Sahne geçişi tam oturmadan gönderilen chat paketleri sunucu tarafından sessizce
    # yutulabiliyor (phBotChat True dönse bile mesaj partiye ulaşmıyor) - inject_teleport()
    # akışındaki 2 saniyelik bekleme ile aynı sebeple burada da kısa bir gecikme kullanıyoruz.
    # Wait for post-teleport character/position data to become stable. The
    # fallback covers same-region teleports where no region change is visible.
    if is_runtime or destination_id is not None:
        now = time.time()
        message = "TPR %s" % source if is_runtime else "TP %s %s" % (source, destination_id)
        _queued_tp_announcement = {
            'source': source,
            'destination_id': destination_id,
            'is_runtime': is_runtime,
            'origin_region': origin_region,
            'created_at': now,
            'deadline': now + TP_ANNOUNCE_TIMEOUT,
            'fallback_at': now + TP_SCENE_FALLBACK_DELAY,
            'saw_unready': False,
            'stable_region': None,
            'stable_checks': 0,
            'ready_at': None,
            'message': message,
            'attempts': 0,
            'sent': False,
            'sent_at': None,
            'confirmed': False,
        }


def _send_tp_announcement(source, destination_id):
    channel = get_announce_channel()
    message = f"TP {source} {destination_id}"

    sent = ANNOUNCE_CHANNELS.get(channel, phBotChat.All)(message)

    if sent:
        log(f"Plugin: TP announcement sent ({channel}): {message}")
        save_announce_settings()
    else:
        log("Plugin: Failed to send TP announcement (phBotChat reported a message send failure).")
    return sent


def _send_runtime_tp_announcement(source):
    channel = get_announce_channel()
    message = f"TPR {source}"
    sent = ANNOUNCE_CHANNELS.get(channel, phBotChat.All)(message)

    if sent:
        log(f"Plugin: TPR announcement sent ({channel}): {message}")
        save_announce_settings()
    else:
        log("Plugin: Failed to send TPR announcement (phBotChat reported a message send failure).")
    return sent

if os.path.exists(getPath()):
    loadLeadersConfigs()
    loadOpcodeConfigs()
else:
    os.makedirs(getPath())
    log('Plugin: ' + pName + ' folder has been created')
update_account_info()
refresh_display_fields()

# Plugin loaded
log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
