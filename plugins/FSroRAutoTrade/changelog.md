# FSroRAutoTrade Changelog

## v3.6.1

### Fixed

- Fixed the saved trade script not being explicitly restored in the script
  combobox after a relog or plugin reload.

## v3.6.0

### Added

- Added `Re-arm This Client` for safely returning an individually repaired client
  to normal synchronization without restarting phBot or the plugin.

### Improved

- Improved `Abort Local` to stop the local walking script and bot, restore the
  Farm Profile when needed, and leave the client explicitly unarmed.

### Removed

- Removed the party-wide ABORT broadcast from the user abort button so healthy
  clients are not changed when repairing one client locally.

## v3.5.0

### Added

- Added independent per-character trade targets to party synchronization; the
  coordinator now waits until every required character reaches its own target.

## v3.4.0

### Added

- Added a per-character `CHECK interval` setting for coordinator synchronization
  retries, with a 10-second default and a 2-second minimum.

## v3.3.0

### Fixed

- Fixed party synchronization for job-suited characters by identifying clients
  with their real character names while retaining observed job aliases for the
  final party-presence check.

### Improved

- Improved synchronization messages to carry an explicit real-character identity;
  all participating clients must use v3.3.0 or later.

## v3.2.4

- Aligned empty inventory slot selection with FControl's proven implementation.
- Kept the existing 20-second job-item unequip retry and verification flow.

## v3.2.3

- Fixed training-area detection near region boundaries by using the active
  training radius and coordinate distance instead of requiring identical region IDs.
- Kept the three consecutive inside-area checks before automatic trade starts.

## v3.2.2

- Fixed empty inventory slot detection for phBot versions that return empty slots as `{}` instead of `None`.
- Kept the timed inventory refresh and job-item unequip retry behavior introduced in v3.2.1.
