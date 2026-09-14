# FScriptHelper Changelog

## v1.2.2

### Fixed
- Restored NPC verification for the first recorded selection; unknown targets and unavailable NPC data now leave recording waiting for a valid NPC instead of creating a raw-UID recording.

## v1.2.1

### Fixed
- Fixed consecutive `FSH_NPC,...,true` commands replaying earlier commands by waiting within the script instead of stopping and restarting the bot. Both boolean values remain accepted; GUI playback retains its bot pause option.
- Included the per-packet playback tick in script wait times to prevent the next command from arriving before longer recordings finish.

## v1.2.0

### Added
- Added recording triggers for `0x7C45` selections and original-UID replay when NPC metadata is unavailable.

### Fixed
- Removed the default opcode filter so outgoing NPC dialog and other interaction packets are captured without enabling advanced recording.

## v1.1.1

- Improved header spacing and shortened translated text to prevent clipping.
- Aligned the record and command action buttons into consistent columns.
- Wrapped the recording instructions and simplified nearby NPC rows for readability.

## v1.1.0

- Added complete English and Turkish GUI translations with English as the default.
- Added a persistent language switch and translated live status/list text.
- Added the standard Discord header button and load signature.

## v1.0.0

- Changelog tracking started for the current version.
