# FAutoCaptcha Changelog

## v1.0.1

### Improved
- Added a prominent GUI notice and documentation stating that the plugin is intended only for MaxiGuard-protected servers.

## v1.0.0

### Added
- Added automatic capture and 30-second replay of server-specific `0xC011` packets.
- Added controls for enabling replay and clearing the captured packet.
- Added live packet, send-count, and connection status indicators.

### Improved
- Added safe timer cleanup during disable, disconnect, and plugin unload.
- Prevented captured packet data from being reused across disconnected sessions.
