# FControl Changelog

## v1.8.2

### Added
- Added case-insensitive `EQ job` and `UQ job` shortcuts that identify job equipment by item type without requiring its full name.

### Improved
- Preserved iSRO reserved equipment slots when searching the inventory for a job item to equip.

## v1.8.1

### Added
- Added compact Buttons-page shortcuts for bot control, following, leaving the party, character actions, loot, storage, Clock, and Devil extension commands.

### Improved
- Reorganized the Buttons page into a compact two-column layout with shared channel selection, localized labels, and command-send status feedback.

## v1.7.0

### Added
- Added a TR/EN language toggle for GUI text and command descriptions while preserving command syntax, shortcuts, and channel values.

## v1.6.5

### Fixed
- Fixed the `CLOCK` command to build locale-aware targeted item-use packets, including the manually verified locale 22 vSRO format.

## v1.6.4

### Fixed
- Fixed generic `USE` commands on iSRO sending the legacy packed item type instead of the required expanded four-byte item type group.

## v1.6.3

### Fixed
- Fixed iSRO job-item unequip requests selecting reserved equipment slots 13–16 instead of an available inventory slot.

## v1.6.2

### Fixed
- Fixed teleport announcements being silently dropped by waiting for stable destination character and region data before sending from phBot's event loop.

## v1.6.1

### Added
- Added a Discord invite button beside the existing GUI signature.

## v1.6.0

- Added the leader-only `DEVILEXT` command to use exactly one Extension Gear on a Devil, Angel, or Hero Spirit.
- Added response-driven unequip, extension, and conditional re-equip handling using the verified `0x7034`, `0x704C`, `0xB034`, and `0xB04C` packet flows.
- Added support for event, premium, rental, and daily-login Extension Gear variants through the shared `NASRUN_EXTENSION` servername family.

## v1.5.0

- Added the leader-only `CLOCK` command, which safely uses exactly one recognized Clock of Reincarnation on the active pick pet or the sole inactive pick-pet scroll.
- Added pending-operation protection and `0xB04C` server-response handling for Clock requests.

## v1.4.2

- Removed the obsolete `DH` packet command and all related hidden GUI, timer, and command-hook code.

## v1.4.1

- Updated the in-plugin command list to document every available command with concise English descriptions.

## v1.4.0

- Added leader-only `PA` and `SPA` commands to start and stop collecting nearby drops allowed by the phBot pick filter.

## v1.3.1

- Added leader-only `SORT` and safe, locale-aware `REPAIR` inventory commands.

## v1.3.0

- Added leader-authorized `ALeader CharNick` and `RLeader CharNick` chat commands for managing the leader list.

## v1.2.6

- Changelog tracking started for the current version.
