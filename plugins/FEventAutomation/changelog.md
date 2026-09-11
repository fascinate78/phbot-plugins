# FEventAutomation Changelog

## v1.0.4

### Fixed
- Fixed Pledge of Love leaving Event So-Ok open by applying the same close and event-cleanup packet sequence used by Jewel Box automation.

## v1.0.3

### Improved
- Added one delayed inventory-sort retry when the normal post-exchange sort leaves no free slot, allowing automation to continue if the retry frees space.

## v1.0.2

### Added
- Added up to two safe retries when a Pledge of Love exchange produces no Left/Right quantity change.

## v1.0.1

### Fixed
- Fixed intermittent Pledge of Love timeouts by using capture-matched delays between NPC packets.
- Fixed inventory sorting being requested while the Event So-Ok conversation was still open.

## v1.0.0

### Added
- Added Event So-Ok automation for Jewel Boxes and matched Pledge of Love Left and Right pairs.
- Added automatic Silkroad Box opening, live item counts, detailed activity logging, and an optional packet recorder.
