# FFortuneManager Changelog

## v1.2.6

### Fixed
- Added the live-verified shield code `0x19` as Block and aligned the selectable shield target name with the game log.

## v1.2.5

### Added
- Added the live-verified shield code `0x0F` as Evade Critical and exposed it as a selectable shield target.

## v1.2.4

### Fixed
- Added the live-verified ring code `0x1F` as Fear Resist, completing the Media-defined special accessory target codes.

## v1.2.3

### Fixed
- Added the live-verified earring code `0x1C` as CSMP Resist and aligned its selectable target name with the game log.

## v1.2.2

### Fixed
- Added the earring code `0x1E` as Sleep Resist based on the live packet, Media assignment, and adjacent verified accessory-code sequence.
- Aligned Combustion, Sleep, Disease, and Fear target names with the game's resistance terminology.

## v1.2.1

### Fixed
- Added the verified necklace code `0x1A` as Stun Resist and aligned the selectable necklace target name with the game log.

## v1.2.0

### Added
- Added Parry Ratio targets to every supported armor piece.
- Added Frostbite, Fire, Lightning, Poison, and Zombie resistance targets to all accessories.
- Exposed the Media-defined Combustion/Sleep, Stun, and Disease/Fear target groups for earrings, necklaces, and rings respectively.

### Improved
- Matched verified accessory resistance names to the terminology shown by the game log.
- Made structurally valid but unknown Fortune stat codes stop automation and produce a diagnostic instead of accepting a partial result.

## v1.1.3

### Fixed
- Added the verified low-code armor/accessory response family for STR, INT, Durability, Parry Ratio, HP, MP, elemental resistances, and Disease.
- Allowed explicitly excluded Media stats to be decoded for packet integrity without exposing them as selectable targets.

## v1.1.2

### Fixed
- Replaced the fixed Fortune-response stat offset with validated contiguous 8-byte record discovery, preventing slot/item header differences from hiding real targets such as Critical.

## v1.1.1

### Fixed
- Fixed unsafe Fortune retries when a response offset produced stats that are impossible for the selected Media item group; automation now stops and logs the bounded raw response for diagnosis.

### Added
- Added a bounded raw `0xB151` log for every one-roll test so server-specific response layouts can be verified even when a false-positive stat was decoded.

## v1.1.0

### Improved
- Redesigned the item setup screen with a taller inventory list, a single-line selected-item summary, and side-by-side available-stat and item-target panels.
- Removed the current-stat list from the setup screen to give item and target selection more usable space.

## v1.0.4

### Fixed
- Fixed the automation queue and START/STOP controls being positioned below phBot's visible plugin area by moving them to a dedicated second screen.

## v1.0.3

### Fixed
- Fixed the shared classic block response code being labeled as Block Rate on weapons instead of Evade Block by resolving it against the selected item's Media group.

## v1.0.2

### Added
- Added a one-roll test that sends exactly one Fortune request and displays the decoded `0xB151` result without repeating.

### Improved
- Updated current-stat guidance after live diagnostics confirmed that this server's return-time `0x3013` packet does not contain inventory model IDs.

## v1.0.1

### Added
- Added bounded `0x3013` item-record diagnostics for unresolved eligible inventory items.

### Improved
- Reduced repeated unresolved-capture messages to one final diagnostic result per packet.

## v1.0.0

### Added
- Added eligible weapon, shield, armor, and accessory filtering using phBot item type data.
- Added server-media-based stat availability groups for each supported equipment subtype.
- Added verified `0x3013` inventory magic-option capture with visible raw option values and capture status.
- Added independent per-stat line targets, multi-item queuing, and response-driven Fortune automation.

### Removed
- Removed Telegram and sound notification dependencies from the original workflow.
