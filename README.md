# FascinaTe phBot Plugins

The official home of FascinaTe phBot plugins. Every plugin published in this
repository is completely free to download and use.

[![Join our Discord](https://img.shields.io/badge/Discord-Join%20Our%20Server-5865F2?logo=discord&logoColor=white)](https://discord.gg/eB9sGSMYBg)

Join our [Discord server](https://discord.gg/eB9sGSMYBg) for announcements,
plugin updates, support, and community discussion.

> 📖 **Documentation:** See the [GitHub Wiki](https://github.com/fascinate78/phbot-plugins/wiki) for installation guides, plugin settings, usage instructions, and troubleshooting.

## Contents

- [Installation with FaaUpdater](#installation-with-faaupdater)
- [Manual installation](#manual-installation)
- [Available plugins](#available-plugins)
- [Repository structure](#repository-structure)
- [Update policy](#update-policy)
- [Author](#author)

## Installation with FaaUpdater

FaaUpdater is the recommended way to install and update the plugins in this
repository.

1. Right-click [`FaaUpdater.py`](https://raw.githubusercontent.com/fascinate78/phbot-plugins/main/plugins/FaaUpdater/FaaUpdater.py) and select **Save link as**.
2. Copy `FaaUpdater.py` into the phBot `Plugins` directory.
3. Reload the plugin list or restart phBot.
4. Open **F Plugin Manager**.
5. Select the plugins you want to install or update.

After the initial setup, FaaUpdater handles downloading, verifying, installing,
and updating the available plugins.

## Manual installation

If you prefer not to use FaaUpdater:

1. Open the desired plugin folder under [`plugins`](https://github.com/fascinate78/phbot-plugins/tree/main/plugins).
2. Download the plugin's `.py` file.
3. Copy the file into the phBot `Plugins` directory.
4. Reload the plugin list or restart phBot.

When updating manually, replace the existing plugin file with the newly
downloaded version.

## Available plugins

<!-- PLUGIN_TABLE_START -->
| Plugin | Version | Description |
|---|---:|---|
| [FaaUpdater](plugins/FaaUpdater/) | 1.2.0 | Manages installation and updates for FascinaTe phBot plugins from the trusted GitHub catalog. |
| [FAutoGS](plugins/FAutoGS/) | 1.1.0 | Coordinates guild-storage scripts across party characters. |
| [FAutoPetClock](plugins/FAutoPetClock/) | 1.5.0 | Monitors Pick Pets and safely renews expired or expiring pets with available clocks. |
| [FAutoUnique V2](plugins/FAutoUnique/) | 2.7.2 | Hunts unique monsters through prioritized script or learned coordinate routes. |
| [FCaravanNavigator V3](plugins/FCaravanNavigator/) | 3.1.1 | Navigates caravan routes and recovers interrupted travel. |
| [FChamberViciousShadows](plugins/FChamberViciousShadows/) | 1.6.1 | Coordinates party entry, combat, exit, and repeat runs for the Vicious Shadows dungeon. |
| [FCharacterPluginManager](plugins/FCharacterPluginManager/) | 1.0.0 | Loads a separate set of local phBot plugins for each server and character. |
| [FControl](plugins/FControl/) | 1.9.0 | Remotely controls phBot characters through authorized in-game chat commands and synchronized actions. |
| [FFateManager](plugins/FFateManager/) | 1.0.1 | Automatically applies Wheel of Fate until each queued equipment item reaches its configured blue-line count. |
| [FFortuneManager](plugins/FFortuneManager/) | 1.2.7 | Automatically rolls eligible equipment until every configured per-stat line target is reached. |
| [FInventoryManager](plugins/FInventoryManager/) | 3.0.4 | Sorts character inventory and personal storage with configurable category rules. |
| [FPenManager](plugins/FPenManager/) | 1.0.0 | Automatically applies Feather Pen of Fortune until each queued equipment item reaches its configured total stat values. |
| [FPvpHelperV2](plugins/FPvpHelperV2/) | 1.2.0 | Switches configured weapons, shields, and skill groups during PvP. |
| [FScriptHelper](plugins/FScriptHelper/) | 1.1.1 | Records and replays NPC interactions as reusable script commands. |
| [FSereness](plugins/FSereness/) | 2.6.2 | Detects boss petrification and temporarily moves the character to avoid it. |
| [FShining](plugins/FShining/) | 1.3.0 | Automates lightstone crafting and required material-stack splitting. |
| [FSroRAutoTrade](plugins/FSroRAutoTrade/) | 4.1.0 | Automatically starts and manages trade runs when the configured Specialty Goods Box target is reached. |
| [FTarget](plugins/FTarget/) | 3.5.1 | Sends a configurable key combination and follow-up key through hotkey, chat, or timed-loop triggers. |
| [FUniqueNotifier](plugins/FUniqueNotifier/) | 1.0.0 | Notifies you when configured unique monsters appear. |
| [FWheelManager](plugins/FWheelManager/) | 1.3.0 | Combines Fate, Fortune, and Pen equipment rolling into one safely coordinated phBot plugin. |
<!-- PLUGIN_TABLE_END -->

Plugin availability, versions, download locations, integrity hashes, and release
notes are maintained in [`manifest.json`](manifest.json).

## Repository structure

```text
phbot-plugins/
|-- manifest.json
|-- README.md
`-- plugins/
    |-- FaaUpdater/
    |-- FAutoGS/
    |-- FCaravanNavigator/
    |-- ...
    `-- FUniqueNotifier/
```

Each published plugin directory contains the installable plugin file and its
`changelog.md`.

## Update policy

- Plugin files are downloaded over HTTPS from this repository.
- Downloads are verified using the SHA-256 value in `manifest.json`.
- Every published plugin includes `changelog.md`; its latest matching version
  notes are also recorded in `manifest.json`.
- Existing plugin files are replaced only after a complete and valid download.
- No backup copy is created during an update.
- A phBot plugin reload or restart may be required after installation.

## Author

Made by FascinaTe.
