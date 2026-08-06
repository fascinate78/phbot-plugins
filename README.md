# FascinaTe phBot Plugins

The official home of FascinaTe phBot plugins. All plugins published in this
repository are completely free to download and use.

[![Join our Discord](https://img.shields.io/badge/Discord-Join%20Our%20Server-5865F2?logo=discord&logoColor=white)](https://discord.gg/eB9sGSMYBg)

Join our [Discord server](https://discord.gg/eB9sGSMYBg) for announcements,
plugin updates, support, and community discussion.

## Installation

You only need to install **FaaUpdater** manually. All other available plugins
can then be installed and updated directly through FaaUpdater.

1. Download `FaaUpdater.py` from the `plugins/FaaUpdater` directory.
2. Copy it into the phBot `Plugins` directory.
3. Reload the plugin list or restart phBot.
4. Open **FascinaTe Plugin Updater** and use it to install or update any
   available plugin.

There is no need to manually download each plugin or replace plugin files when
an update is released; FaaUpdater handles both installation and updates.

## Free plugins

This repository is where FascinaTe phBot plugins will be published. Every
plugin shared here is completely free—no purchase or paid subscription is
required.

## Repository structure

```text
phbot-plugins/
|-- manifest.json
|-- README.md
`-- plugins/
    `-- FaaUpdater/
        `-- FaaUpdater.py
```

The updater reads `manifest.json` to discover available plugins, versions,
download locations, and SHA-256 integrity hashes.

## Update policy

- Plugin files are downloaded over HTTPS from this repository.
- Downloads are verified using the SHA-256 value in `manifest.json`.
- Existing plugin files are replaced only after a complete and valid download.
- No backup copy is created during an update.
- A phBot plugin reload or restart may be required after installation.

## Author

Made by FascinaTe.
