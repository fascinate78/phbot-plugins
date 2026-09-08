# FDevilAwakener Changelog

## v1.1.2

### Improved
- Added iSRO enhancement-result detection through the Devil's `get_inventory()` `plus` value after a matching successful `0xB04C` scroll response.

### Fixed
- Fixed unrelated slotless iSRO `0xB04C` errors such as `0x183E` and `0x185B` incorrectly stopping an accepted awakening request and interrupting Devil restoration.

## v1.1.1

### Improved
- Updated the iSRO unequip request to calculate its changing final field from the current free normal-inventory slot count instead of using a fixed captured value.
- Added an iSRO-specific item-use encryption profile and a longer post-unequip delay before the first awakening attempt.

### Fixed
- Fixed restoration after an item-use rejection by prioritizing the exact inventory slot reported for the unequipped Devil, including when identical Devils make model-based lookup ambiguous.

## v1.1.0

### Added
- Added iSRO locale 18 support and an `Only use equipped Devil` option that operates exclusively on the Devil in equipment slot 4.
- Added response-driven Devil unequip and restoration using `0x7034` and `0xB034`, including identity checks that prevent another inventory Devil from being equipped.

### Improved
- Added restoration handling after target completion, scroll exhaustion, attempt limits, server errors, timeouts, and user stops.
- Reserved iSRO slots 0-16 from normal inventory Devil selection.

## v1.0.2

### Fixed
- Fixed locale 65 response `0x18DD` being treated as an equipped-Devil rejection; captures verify that it precedes a successful scroll quantity update and represents a consumed attempt without an enhancement result.
- Improved failed-roll handling so awakening continues toward the configured target instead of stopping incorrectly.

## v1.0.1

### Improved
- Restricted automatic and manual selection to normal inventory slots so equipped Devils cannot be targeted.

## v1.0.0

### Added
- Added automatic and explicitly selected Devil's Spirit awakening modes for Silkroad-R locale 65.
- Added configurable target enhancement, maximum-scroll safety limit, and an option to use all available scrolls.
- Added verified parsing of awakening results, three-hour duration data, inactive-Devil rejection, scroll availability, and target completion.
- Added a live status panel with the selected Devil, current result, duration, attempt totals, and remaining scroll count.
