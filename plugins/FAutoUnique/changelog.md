# FAutoUnique V2 Changelog

## v2.7.1

### Improved
- Replaced fixed town region-ID checks with normalized `get_zone_name(region)` detection for cities spanning multiple regions.
- Added verified `Hotan Kingdom` and `Western China Donwhang` aliases alongside plain English and known Chinese Media.pk2 city names.

## v2.7.0

### Added
- Added persistent English and Turkish language selection for GUI controls, headings, filters, and user-facing status messages.

### Improved
- Kept technical phBot logs and game-data names unchanged while allowing the visible interface language to update without recreating widgets.
- Redesigned coordinate-route editing into a dedicated Coordinate Editor screen within the existing QtBind interface.
- Increased saved-coordinate visibility and replaced the compressed Unique Manager list with a per-unique saved-point summary.
- Moved manual entry, current-position capture, nearby-unique capture, and point removal controls into the focused editor while keeping script and Reverse settings in Unique Manager.

## v2.5.0

### Added
- Added per-unique First Reverse settings with a Media-derived location selector for coordinate routes.
- Added deferred coordinate-route startup after the Reverse teleport completes, including a 30-second failure timeout.

### Improved
- Kept failed or timed-out Reverse hunts queued and cancelled pending continuations when monitoring stops, the target dies, or the route is otherwise cancelled.
- Skipped the configured Reverse when the target is already visible, allowing immediate engagement instead of abandoning a nearby unique.

## v2.4.1

### Fixed
- Fixed visible coordinate-route uniques unnecessarily triggering a town return; targets already visible at the grind slot are now engaged directly after preserving the saved slot.
- Fixed cancelled or failed return scrolls being treated as successful town arrivals; the queue now remains pending until a real town teleport is detected.
- Fixed corrupted arrow and dash characters in user-facing plugin log messages.

## v2.4.0

### Added
- Added ordered coordinate-route hunts with generated phBot paths, two-second point scans, and immediate engagement when the target becomes visible.
- Added manual coordinate entry, current-position capture, nearby-unique capture, optional automatic coordinate learning, and duplicate-point protection within 30 meters.
- Added four focused GUI pages: Dashboard, Unique Manager, Hunt Settings, and Logs, using the existing QtBind off-screen navigation architecture.
- Added a searchable, status-filtered unique browser with a unified detail panel for script routes, coordinate routes, saved points, priority, queueing, and manual hunts.
- Added a bounded 100-entry activity viewer for important unique detection, queue, route, kill, timeout, return, and hunt-completion events.
- Added a compact Dashboard configuration-health summary for total, ready, script-route, coordinate-route, and needs-setup counts.

### Improved
- Integrated coordinate routes into the existing prioritized hunt queue while preserving script mappings and the existing configuration format.
- Improved coordinate hunting reliability with guarded route monitoring, immediate repeated-spawn handling, and a 50-meter engagement training area.
- Improved runtime visibility with separate plugin, bot-state, target, route, action, queue, and needs-setup displays.
- Improved large unique-set management with explicit Load Selected behavior and immediate detail, script, and coordinate refreshes.
- Separated script-mapping removal from coordinate-point removal while preserving inactive route data when switching route modes.
- Reduced unchanged Dashboard updates during the high-frequency event loop by refreshing QtBind labels only when runtime state changes.
- Compressed every page to keep all interactive controls within the real phBot plugin viewport without scrolling or additional windows.

### Fixed
- Fixed active coordinate hunts not reacting to repeated native spawn events and protected the route monitor from stopping after transient API errors.
- Fixed manual coordinate hunts reporting a successful start while monitoring was disabled.
- Removed unsupported direct-target API calls and now lets phBot select and attack the unique after configuring its real position as the training area.
- Fixed the bot restoring the previous grind slot after a completed hunt; an empty queue now leaves monitoring active with the bot stopped in town.
- Ensured scripts and botting stop before the post-hunt return begins.
- Fixed stale route modes causing GUI readiness to disagree with actual hunt-route availability.
- Fixed removing the final coordinate from an active coordinate route; the unique now falls back to its script route when available or becomes Needs Setup when no route remains.
- Fixed removing a script mapping leaving an invalid route mode when no coordinate route remains.
- Fixed clipped Unique Manager controls that prevented loading a selected unique, displaying saved coordinates, editing coordinates, or using manual queue and hunt actions.
- Fixed the Dashboard Configuration Health summary and lower Hunt Settings and Logs controls being placed outside the usable phBot viewport.

## v2.2.3

### Improved
- Moved packet, event, and chat spawn/death trace messages behind the existing Detailed log option to prevent routine log spam.

## v2.2.2

### Improved
- Clarified the Manual Hunt selection/action grouping and separated the current-hunt stop action.
- Improved mapping-row spacing and consolidated diagnostics into a compact secondary block.

## v2.2.1

### Improved
- Compressed both GUI screens to keep all queue, manual hunt, mapping, and diagnostic controls visible in the phBot viewport.
- Improved control alignment and moved script refresh closer to the primary mapping workflow.

## v2.2.0

### Improved
- Reorganized the interface into separate Monitor and Settings screens while preserving existing control behavior and selections.
- Grouped live status, queue, unmapped uniques, mapping controls, and diagnostics by workflow with clearer action labels.
- Improved behavior-setting alignment and widened the hunt-timeout selector to display all values fully.

## v2.1.0

- Rebuilt the interface in English using the shared modern plugin layout.
- Added the standard Discord button, author signature, section styling, and bounded live labels.
- Kept all controls within the standard phBot plugin width.

## v2.0.0

- Changelog tracking started for the current version.
