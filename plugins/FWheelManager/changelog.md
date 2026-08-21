# FWheelManager Changelog

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
