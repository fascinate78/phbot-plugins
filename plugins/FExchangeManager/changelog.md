# FExchangeManager Changelog

## v1.7.1

### Improved
- Reworked the item-filter layout into separate manual-entry and inventory-selection rows with a wider item selector, dedicated add actions, and non-overlapping controls.

## v1.7.0

### Added
- Added a config target selector for copying the current character's item filters to another existing FExchangeManager character config without replacing its player list or checkbox settings.

## v1.6.1

### Improved
- Added manual item-name entry alongside the inventory selector so filters can be prepared for items not currently in the inventory.

## v1.6.0

### Added
- Added an inventory item selector and refresh action for adding exact item names to the automatic exchange filter without typing them manually.

## v1.5.0

### Added
- Added saved exact-name item filters that automatically load matching inventory items when an authorized exchange opens.
- Added support for using `EXC <Item Name>` after the authorized exchange window is already open.

### Improved
- Reused the list editor for both allowed players and automatic item filters with a dedicated mode switch.

## v1.4.2

### Fixed
- Fixed outgoing private status replies being interpreted as new `EXC` commands and causing a repeated message loop.

## v1.4.1

### Improved
- Limited each automatic delivery to the exchange window's 12 item slots while transferring the full quantity contained in every added inventory slot.
- Changed receiver-inventory-full handling to complete the exchange with successfully added items, while still cancelling when no item could be added.

## v1.4.0

### Added
- Added the private `EXC <Item Name>` command to queue all exact-name matching inventory stacks for the requesting player.
- Added sequential exchange item insertion with server-response validation and automatic confirm and approve handling.

### Improved
- Added command and packet timeouts, stack-capacity validation, and automatic cancellation when an item cannot be added, preventing partial automatic deliveries.

## v1.3.1

### Fixed
- Fixed saved character settings not loading when the plugin is reloaded while already in game.

## v1.3.0

### Added
- Added an optional setting to automatically reject unresolved or unauthorized exchange requests.

## v1.2.0

### Added
- Added an optional setting to accept exchange requests from all nearby guild members without adding their names individually.

### Improved
- Allowed listed nearby players to be accepted without requiring party or guild membership.

## v1.1.0

### Improved
- Improved requester verification to accept allowed nearby guild members by resolving exchange UIDs through `get_players()` and validating their names through `get_guild()`.

## v1.0.0

### Added
- Added automatic exchange-request acceptance for explicitly allowed nearby party members.
- Added per-character allowed-player settings and live authorization status.
