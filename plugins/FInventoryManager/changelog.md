# FInventoryManager Changelog

## v3.0.4

### Fixed
- Fixed iSRO Personal Storage session detection when the client sends the NPC `0x704B` transition before the matching `0x7046` storage-talk packet.

## v3.0.3

### Improved
- Blocked Personal Storage sorting unless an active storage NPC interaction has been observed, and clear the captured session when the NPC interaction closes or the client disconnects.

### Fixed
- Fixed vSRO Personal Storage moves being rejected with B034 `02 03 00` by sending the runtime NPC entity ID captured from the `0x7045`/`0x7046` interaction instead of a fixed session value.
- Report short B034 failure payloads as server rejections instead of unsupported responses.

## v3.0.2

### Fixed
- Removed obsolete Personal Storage validation/status widgets that remained visible across Dashboard, Inventory, and both preview screens after the v3.0.1 layout redesign.
- Shortened the refreshed Storage state text so it remains inside the fixed-width status column.

## v3.0.1

### Improved
- Redesigned the Personal Storage detail tab to match Inventory's two-column rules and live-status layout, with its preview and execution controls on a separate preview screen.

### Fixed
- Fixed overlapping Personal Storage rule and action buttons by using the same spacing and compact labels as the Inventory tab.

## v3.0.0

### Added
- Added a default Dashboard with one-click Quick Sort actions for inventory and personal storage.
- Added production personal-storage sorting with serialized operations, B034 correlation, snapshot verification, cancellation, timeouts, and bounded replanning.
- Added separate Inventory and Storage detail tabs with independent rules and manual refresh/preview/start controls.

### Improved
- Consolidate matching storage stacks before category-order moves, including server-limited merges that leave a verified remainder in the source slot.
- Replace the visible storage observation and injection-test workflow with production sorting controls.

## v2.3.2

### Added
- Added capacity-limited personal-storage merge validation using the server-reported B034 applied quantity and resulting source/destination stack quantities.

### Improved
- Allow a full-source merge request when only part of the source fits, while continuing to block user-selected partial quantities.

## v2.3.1

### Fixed
- Block partial personal-storage merges after runtime validation showed that the target server ignores the requested partial amount and applies the full source stack.
- Continue to snapshot verification when B034 reports an unexpected applied quantity so the actual server-side change is still assessed and logged.

## v2.3.0

### Added
- Added controlled personal-storage merge injection validation for matching stackable items with source-quantity and destination-capacity checks.

### Improved
- Verify source and destination stack quantities against the B034 applied quantity after an injected merge.

## v2.2.1

### Added
- Added controlled full-stack swap injection validation between different occupied personal-storage items.

### Improved
- Verify both resulting slot contents after injected moves and swaps, while continuing to block same-model occupied targets that could merge.

## v2.2.0

### Added
- Added an explicitly enabled one-move personal-storage injection validator that reuses session bytes captured from a correlated manual move and verifies B034 plus the resulting storage snapshot.

### Improved
- Restricted initial injection validation to a full-stack move into an empty storage slot and cleared captured session data on disconnect.

## v2.1.0

### Added
- Added decoding for the target-verified personal-storage `0x01` request quantity, four-byte session field, and B034 applied quantity.

## v2.0.1

### Improved
- Decode passively observed storage request/response operation, source, destination, and trailing bytes without assigning unverified meanings.
- Report observation correlation without incorrectly claiming that every captured operation is an internal storage move.

## v2.0.0

### Added
- Added a read-only personal-storage viewer with slot, category, quantity, and item details.
- Added separate persistent category rules and zero-packet previews for personal storage.
- Added passive one-operation storage protocol observation correlating `0x7034`, B034, and `get_storage()` changes.
- Added one-way migration of existing inventory sorting rules to the new production configuration.

### Improved
- Renamed the production plugin and all user-facing inventory logs to FInventoryManager.

## v1.1.0

### Improved
- Added locale-aware bag boundaries so iSRO sorting starts at slot 17 while other supported environments retain slot 13.
- Use the snapshot's bag boundary consistently for planning, preview, counters, and unclassified-item reporting.

## v1.0.3

### Added
- Added a category-count summary to sort previews so correctly placed items remain visible for classification review.

## v1.0.2

### Improved
- Added target-server internal-name recognition for `HP_SUPERSET`/`MP_SUPERSET` potions and global chatting scrolls.
- Clear stale operation details whenever a new sort preview is created.

## v1.0.1

### Improved
- Split rules/status and preview/actions into separate pages so all controls remain visible in the phBot plugin area.

## v1.0.0

### Added
- Added manual category-priority inventory previews and conservative swap planning.
- Added configurable category ordering and enabled-category persistence.
- Added serialized `0x7034` execution with B034 decoding and snapshot verification.
- Added bounded replanning for partial or unrelated inventory changes.
- Added safe cancellation, timeout handling, and unclassified-item visibility.
