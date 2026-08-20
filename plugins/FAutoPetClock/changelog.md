# FAutoPetClock Changelog

## v1.5.0

### Improved
- Accelerated expired-pet detection by immediately handling the verified locale 22 `02 A4 18` summon rejection instead of waiting for two nine-second timeouts.
- Kept the two-attempt safety check and `get_pets()` confirmation for successful summons.

## v1.4.1

### Fixed
- Fixed locale 22 Clock requests failing with `Unregistered type : pstr` by using the manually verified `ED 66` item-use TID without querying static item data.

## v1.4.0

### Improved
- Removed per-pet manual summon learning and now use the verified common locale 22 Pick Pet summon request for all standard and explicitly allowed custom pets.
- Enabled summon-test expiry verification by default for new character settings.
- Simplified manual test results to alive and expired totals because every recognized pet can now be tested automatically.

## v1.3.1

### Added
- Added a one-click `Test Pets Now` action that verifies learned pets and reports alive, expired, and unlearned totals without consuming a Clock.

### Improved
- Manual pet testing restores the initially active pet and leaves automatic processing paused so the user can review the results before allowing Clock use.

## v1.3.0

### Added
- Added optional summon-test expiry verification with two attempts per learned Pick Pet.
- Added automatic capture and per-character storage of manually observed Pick Pet summon packet data.
- Added automatic closing and restoration of the Pick Pet that was active before a verification cycle.

### Improved
- Limited Clock use to summon-verified expired pets when summon-test mode is enabled, ignoring unreliable inventory expiration values.
- Added post-Clock summon verification and a safety pause if revival cannot be confirmed.
- Added explicit `UNTESTED`, `ALIVE`, `EXPIRED`, and `NEEDS LEARNING` inventory states for summon-test mode.

## v1.2.0

### Added
- Added an optional per-character custom Pick Pet allowlist with exact servername and limited `*` wildcard patterns.
- Added a separate `Custom Pets` settings screen for adding, removing, enabling, and saving custom pet patterns.

### Improved
- Kept nonstandard private-server pets excluded from automatic processing unless they match an explicitly configured pattern.
- Applied custom patterns to active-pet matching so a configured summoned pet is not mistaken for an expired inventory pet when its active servername omits `_SCROLL`.

## v1.1.1

### Improved
- Separated expired and near-expiry pets into explicit processing queues so the expired queue is always completed first when priority is enabled.
- Improved active Pick Pet matching for custom servers by normalizing `COS_P_` server-name families and accepting pets reported with a nonstandard type.

### Fixed
- Fixed some summoned Pick Pets being classified as expired when their custom-server API type or server-name suffix differed from the inventory scroll.

## v1.1.0

### Added
- Added a saved `Prioritize expired Pets first` option, enabled by default, to guarantee expired pets are processed before near-expiry living pets.

### Improved
- Replaced near-black interface text with a blue-violet color that remains visible in both phBot Light and Dark themes.

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
