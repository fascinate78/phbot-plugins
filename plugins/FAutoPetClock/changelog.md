# FAutoPetClock Changelog

## v1.0.4

### Improved
- Changed the empty current-operation status from `None` to the clearer `No active operation` message.

## v1.0.3

### Fixed
- Fixed the locale 22 targeted Clock packet to exactly match the manual game-client capture: Clock slot, two-byte item-use TID, and Pick Pet scroll slot.

## v1.0.2

### Added
- Added raw `0xB04C` response diagnostics and passive capture of manual game-client Clock `0x704C` packets.

### Improved
- Improved Clock response matching to accept either the pending Clock slot or its item-use TID.

## v1.0.1

### Improved
- Added locale-aware targeted Clock packets, including the vSRO locale 22 two-byte item-use TID and Pick Pet target container.
- Added summoned Pick Pet detection to prevent stale inventory expiration values from marking the active pet as expired.
- Added a session safety pause after a rejected, timed-out, or unverified Clock operation.

### Fixed
- Fixed locale 22 Clock requests timing out because the locale 18 four-byte item type was used.
- Fixed automatic processing continuing to another pet immediately after a Clock request failure.

## v1.0.0

### Added
- Added periodic inventory monitoring for expired and near-expiry Pick Pets.
- Added sequential Clock processing with server-response and duration-update verification.
- Added character-specific settings, Clock priority selection, manual scanning, temporary pause, and live status lists.
