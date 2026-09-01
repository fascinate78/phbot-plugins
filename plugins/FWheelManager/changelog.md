# FWheelManager Changelog

## v1.3.0

### Added
- Added automatic discovery of phBot's active private-server database, including servers reporting locale 22 or 65, with read-only server-specific Fortune and Pen stat decoding.
- Added database-backed Available Stats for Fortune and Pen based on the selected item's equipment category, subtype, and degree.

### Improved
- Improved cross-server safety with verified full-ID response parsing, built-in layout fallbacks, and bounded diagnostics for unrecognized Fortune or Pen responses.

### Fixed
- Fixed valid server-specific Fortune and Pen responses being rejected because of database-ID, locale, installation-path, or Pen record-offset differences.

## v1.0.1

### Added
- Added context-aware decoding for the verified high-degree weapon Fortune stat-code family.

### Improved
- Added bounded raw packet diagnostics when a Fortune response contains stats that are unsafe for the selected item.

## v1.0.0

### Added
- Added Fate, Fortune, and Pen modes in one page-switched interface with the requested Fate, Fortune, Pen order.
- Added independent per-mode queues, targets, one-roll tests, results, and setup screens.
- Added exclusive operation ownership for the shared `0x7151` request and `0xB151` response flow.
- Added response validation, inventory slot/model checks, cancellable request scheduling, and disconnect safety handling.
