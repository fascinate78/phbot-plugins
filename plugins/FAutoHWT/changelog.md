# FAutoHWT Changelog

## v0.7.2

### Added
- Added Solo, Party Leader, and Party Member modes for complete HWT automation.
- Added selectable Slot Profile, HWT Profile, leader HWT route, leader return route, difficulty, teleport language, and run count settings.
- Added city-to-gate and manual `Start From Gate` flows with gate NPC, region, distance, roster, leader, and stability validation.
- Added leader-first entry, FControl trace coordination, an eight-second member fallback, and leader-only dungeon route execution.
- Added repeat-run handling with leader return-to-gate routing, member leave-party exit, and final Slot Profile, Return Scroll, town verification, and optional bot restart.
- Added Daily, Selected days, and One time scheduling with missed-trigger tolerance.
- Added immediate HWT entry-limit detection for the verified `0xB05A 02 27 1C` server response.

### Improved
- Entry-limited or timed-out members remain outside while successfully entered characters complete the current run; the cycle then finalizes without attempting another HWT entry.
- Added versioned private coordination, bounded retries and timeouts, detailed diagnostic logging, and backward-compatible loading of legacy `FHWTGate` settings and scripts.
- Refined the two-screen interface to fit the measured phBot viewport without overlapping controls.

### Fixed
- Fixed the leader HWT route failing to start after the FControl trace delay.
- Fixed party members incorrectly requiring and starting their own HWT route scripts.
