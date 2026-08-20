# FascinaTe phBot Plugins

The official home of FascinaTe phBot plugins. Every plugin published in this
repository is completely free to download and use.

[![Join our Discord](https://img.shields.io/badge/Discord-Join%20Our%20Server-5865F2?logo=discord&logoColor=white)](https://discord.gg/eB9sGSMYBg)

Join our [Discord server](https://discord.gg/eB9sGSMYBg) for announcements,
plugin updates, support, and community discussion.

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
| [FaaUpdater](plugins/FaaUpdater/) | 1.2.0 | Installs and updates FascinaTe phBot plugins from GitHub. |
| [FAutoGS](plugins/FAutoGS/) | 1.1.0 | Coordinates guild-storage scripts across party characters. |
| [FAutoPetClock](plugins/FAutoPetClock/) | 1.4.1 | FascinaTe phBot plugin. |
| [FAutoUnique V2](plugins/FAutoUnique/) | 2.2.3 | FascinaTe phBot plugin. |
| [FCaravanNavigator V3](plugins/FCaravanNavigator/) | 3.1.1 | Navigates caravan routes and recovers interrupted travel. |
| [FChamberViciousShadows](plugins/FChamberViciousShadows/) | 1.6.1 | Coordinates party entry, combat, exit, and repeat runs for the Vicious Shadows dungeon. |
| [FCharacterPluginManager](plugins/FCharacterPluginManager/) | 1.0.0 | FascinaTe phBot plugin. |
| [FControl](plugins/FControl/) | 1.6.5 | Provides shared control commands, actions, and teleport handling. |
| [FInventoryManager](plugins/FInventoryManager/) | 3.0.3 | FascinaTe phBot plugin. |
| [FPvpHelperV2](plugins/FPvpHelperV2/) | 1.2.0 | Switches configured weapons, shields, and skill groups during PvP. |
| [FScriptHelper](plugins/FScriptHelper/) | 1.1.1 | Records and replays NPC interactions as reusable script commands. |
| [FSereness](plugins/FSereness/) | 2.6.2 | Detects boss petrification and temporarily moves the character to avoid it. |
| [FShining](plugins/FShining/) | 1.3.0 | Automates lightstone crafting and required material-stack splitting. |
| [FSroRAutoTrade](plugins/FSroRAutoTrade/) | 4.0.0 | Coordinates party-synchronized trade scripts and job-item handling. |
| [FUniqueNotifier](plugins/FUniqueNotifier/) | 1.0.0 | Notifies you when configured unique monsters appear. |
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
