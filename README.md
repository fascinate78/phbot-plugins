# FasscinaTe phBot Plugins

Public plugin catalog and update source for FasscinaTe phBot plugins.

## Installation

1. Download `FaaUpdater.py` from the `plugins/FaaUpdater` directory.
2. Copy it into the phBot `Plugins` directory.
3. Reload the plugin list or restart phBot.
4. Open **FasscinaTe Plugin Updater** to install or update available plugins.

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

Made by FasscinaTe.

