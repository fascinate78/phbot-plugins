from phBot import *
import phBotChat
import QtBind
import json
import os
import re
import time


pName = 'FUniqueNotifier'
pVersion = '1.0.0'

EVENT_UNIQUE_SPAWN = 0
MESSAGE_INTERVAL = 1.0

recipients = []
message_queue = []
last_message_time = 0.0


# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------
gui = QtBind.init(__name__, 'FUniqueNotifier')

QtBind.createLabel(gui, u'✨ FUniqueNotifier  v%s' % pVersion, 5, 2)
QtBind.createLabel(gui, u'⚜ Made By FascinaTe', 565, 2)
QtBind.createLabel(gui, u'Share unique spawn alerts with your team quickly and reliably.', 5, 24)
QtBind.createLabel(gui, u'─' * 90, 5, 40)

QtBind.createLabel(gui, u'👥 Notification Recipients', 5, 57)
QtBind.createLabel(gui, 'Player name (use commas to add multiple players):', 5, 78)
recipient_input = QtBind.createLineEdit(gui, '', 5, 98, 300, 22)
add_recipient_button = QtBind.createButton(gui, 'add_recipients', u'➕ Add', 315, 97)
remove_recipient_button = QtBind.createButton(gui, 'remove_recipient', u'➖ Remove Selected', 395, 97)
clear_recipients_button = QtBind.createButton(gui, 'clear_recipients', u'🧹 Clear List', 530, 97)

recipient_list = QtBind.createList(gui, 5, 127, 690, 65)
recipient_count_label = QtBind.createLabel(gui, 'Total recipients: 0', 5, 197)

QtBind.createLabel(gui, u'📣 Notification Channels', 5, 220)
notify_party_checkbox = QtBind.createCheckBox(gui, '', u'👥 Send to party', 5, 243)
notify_guild_checkbox = QtBind.createCheckBox(gui, '', u'🏰 Send to guild', 165, 243)

QtBind.createLabel(gui, u'ℹ Messages are sent from a safe queue at 1-second intervals.', 5, 270)
save_button = QtBind.createButton(gui, 'save_settings', u'💾 Save Settings', 445, 240)
status_label = QtBind.createLabel(gui, u'⚠ Settings could not be read; using defaults', 445, 272)
QtBind.setText(gui, status_label, u'● Ready')


def set_status(text):
    QtBind.setText(gui, status_label, text)


def refresh_recipient_list():
    QtBind.clear(gui, recipient_list)
    for index, name in enumerate(recipients):
        QtBind.append(gui, recipient_list, '%02d. %s' % (index + 1, name))
    QtBind.setText(gui, recipient_count_label, 'Total recipients: %d' % len(recipients))


def normalize_names(text):
    names = []
    for value in re.split(r'[,;\r\n]+', text):
        name = value.strip()
        if name:
            names.append(name)
    return names


def add_recipients():
    entered_names = normalize_names(QtBind.text(gui, recipient_input))
    if not entered_names:
        set_status(u'⚠ Enter at least one player name')
        return

    existing = set(name.lower() for name in recipients)
    added = 0
    for name in entered_names:
        if name.lower() not in existing:
            recipients.append(name)
            existing.add(name.lower())
            added += 1

    QtBind.clear(gui, recipient_input)
    refresh_recipient_list()
    if added:
        set_status(u'✔ Added %d recipient(s)' % added)
    else:
        set_status(u'⚠ These players are already listed')


def remove_recipient():
    index = QtBind.currentIndex(gui, recipient_list)
    if index < 0 or index >= len(recipients):
        set_status(u'⚠ Select a recipient to remove')
        return

    removed = recipients.pop(index)
    refresh_recipient_list()
    set_status(u'✔ Removed %s' % removed)


def clear_recipients():
    del recipients[:]
    refresh_recipient_list()
    set_status(u'✔ Recipient list cleared')


def get_character():
    data = get_character_data()
    if data and data.get('name'):
        return data
    return None


def get_config_path():
    character = get_character()
    if not character:
        return None

    folder = os.path.join(get_config_dir(), pName)
    server = str(character.get('server', 'UnknownServer'))
    name = str(character.get('name', 'UnknownCharacter'))
    safe_file = re.sub(r'[<>:"/\\|?*]', '_', server + '_' + name) + '.json'
    return os.path.join(folder, safe_file)


def save_settings():
    config_path = get_config_path()
    if not config_path:
        set_status(u'⚠ Join the game before saving settings')
        log('[%s] Settings could not be saved: character is not in game.' % pName)
        return

    data = {
        'recipients': list(recipients),
        'notify_party': QtBind.isChecked(gui, notify_party_checkbox),
        'notify_guild': QtBind.isChecked(gui, notify_guild_checkbox)
    }

    folder = os.path.dirname(config_path)
    temp_path = config_path + '.tmp'
    try:
        if not os.path.isdir(folder):
            os.makedirs(folder)
        with open(temp_path, 'w') as config_file:
            json.dump(data, config_file, indent=4, sort_keys=True)
        os.replace(temp_path, config_path)
        set_status(u'✔ Settings saved')
        log('[%s] Settings saved.' % pName)
    except (OSError, IOError, ValueError) as error:
        set_status(u'❌ Settings could not be saved')
        log('[%s] Settings save error: %s' % (pName, error))


def load_default_settings():
    del recipients[:]
    del message_queue[:]
    QtBind.setChecked(gui, notify_party_checkbox, False)
    QtBind.setChecked(gui, notify_guild_checkbox, False)
    QtBind.clear(gui, recipient_input)
    refresh_recipient_list()


def load_settings():
    load_default_settings()
    config_path = get_config_path()
    if not config_path or not os.path.isfile(config_path):
        set_status(u'● New character settings')
        return

    try:
        with open(config_path, 'r') as config_file:
            data = json.load(config_file)

        if not isinstance(data, dict):
            raise ValueError('Settings root must be a JSON object.')

        saved_recipients = data.get('recipients', [])
        if isinstance(saved_recipients, list):
            existing = set()
            for value in saved_recipients:
                name = str(value).strip()
                if name and name.lower() not in existing:
                    recipients.append(name)
                    existing.add(name.lower())

        QtBind.setChecked(gui, notify_party_checkbox, bool(data.get('notify_party', False)))
        QtBind.setChecked(gui, notify_guild_checkbox, bool(data.get('notify_guild', False)))
        refresh_recipient_list()
        set_status(u'✔ Settings loaded')
        log('[%s] Settings loaded.' % pName)
    except (OSError, IOError, ValueError, TypeError) as error:
        set_status(u'⚠ Settings could not be read; using defaults')
        log('[%s] Settings load error: %s' % (pName, error))


def joined_game():
    load_settings()


def disconnected():
    del message_queue[:]
    set_status(u'● Waiting for connection')


def queue_notification(channel, target, text):
    message_queue.append((channel, target, text))


def handle_event(t, data):
    if t != EVENT_UNIQUE_SPAWN:
        return

    unique_name = str(data).strip()
    if not unique_name:
        return

    party_message = 'Unique [ %s ] is HERE' % unique_name
    private_message = 'Unique [ %s ] is next to me' % unique_name

    if QtBind.isChecked(gui, notify_party_checkbox):
        queue_notification('party', None, party_message)
    if QtBind.isChecked(gui, notify_guild_checkbox):
        queue_notification('guild', None, party_message)
    for recipient in list(recipients):
        queue_notification('private', recipient, private_message)

    queued = int(QtBind.isChecked(gui, notify_party_checkbox))
    queued += int(QtBind.isChecked(gui, notify_guild_checkbox))
    queued += len(recipients)
    if queued:
        set_status(u'📨 %d message(s) queued for %s' % (queued, unique_name))
        log('[%s] %d notification(s) queued for %s.' % (pName, queued, unique_name))
    else:
        set_status(u'⚠ %s found; no notification targets' % unique_name)


def event_loop():
    global last_message_time

    if not message_queue:
        return

    now = time.time()
    if now - last_message_time < MESSAGE_INTERVAL:
        return

    channel, target, text = message_queue.pop(0)
    try:
        if channel == 'party':
            phBotChat.Party(text)
        elif channel == 'guild':
            phBotChat.Guild(text)
        elif channel == 'private' and target:
            phBotChat.Private(target, text)
        last_message_time = now
        if message_queue:
            set_status(u'📨 %d message(s) remaining' % len(message_queue))
        else:
            set_status(u'✔ All notifications sent')
    except Exception as error:
        last_message_time = now
        log('[%s] Chat send error: %s' % (pName, error))
        set_status(u'❌ A notification could not be sent')


log('[%s] Loaded - ⚜ Made By FascinaTe' % pName)
