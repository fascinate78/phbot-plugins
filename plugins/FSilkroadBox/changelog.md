# FSilkroadBox Changelog

## v1.1.2

### Added
- Added a `Buy Only` action that purchases exactly the configured quantity of iSRO Silkroad Boxes, then stops without opening them.

### Removed
- Removed the checkbox-controlled purchase-only setting in favor of the dedicated `Buy Only` action.

## v1.1.1

### Added
- Added an iSRO purchase-only mode that continues after each confirmed F10 purchase without opening the purchased boxes.

## v1.1.0

### Added
- Added an iSRO-only F10 purchase-and-open loop with configurable boxes per cycle and optional infinite cycling.

### Improved
- Added purchase response, timeout, and inventory-change checks before opening newly purchased boxes or continuing the loop.

## v1.0.0

### Added
- Added automatic discovery and opening of `ITEM_PRE_MALL_SILKROAD_BOX` items.
- Added inventory page selection for all available pages or one specific page.
- Added sequential and random opening modes.
- Added a configurable opening delay with a default of 250 ms.
- Added live progress, activity logging, manual stop, and disconnect-safe cancellation.
