# FDevilAwakener Changelog

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
