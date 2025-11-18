---
date: 2025-10-31T14:27:21+00:00
researcher: Planning Specialist
git_commit: uninitialized
branch: main
repository: jellyfleet
topic: "Jellyfin API capabilities for syncing users, settings, and watch states"
tags: [research, codebase, jellyfin, api]
status: complete
last_updated: 2025-10-31
last_updated_by: Planning Specialist
last_updated_note: "Added follow-up research for cross-instance sync prerequisites"
---

# Research: Jellyfin API capabilities for syncing users, settings, and watch states

**Date**: 2025-10-31T14:27:21+00:00
**Researcher**: Planning Specialist
**Git Commit**: uninitialized
**Branch**: main
**Repository**: jellyfleet

## Research Question
Document the current Jellyfin API surface related to synchronizing user accounts, server and user settings, and playback/watch-state data in order to understand integrations for a settings and state synchronization tool.

## Summary
Jellyfin exposes a REST API documented via Swagger that covers user lifecycle management, authentication, playstate tracking, display preferences, server-wide configuration, and backup/restore flows. Playstate functionality is implemented in `PlaystateController`, user management in `UserController`, and configuration endpoints in `ConfigurationController`, with associated data models in `MediaBrowser.Model`. Backup operations, display preferences, and plugin configuration are provided through dedicated controllers. The API distinguishes between current endpoints and legacy routes retained for backwards compatibility. Most management operations require administrator elevation, while user-specific settings and playstate updates accept authenticated user tokens. Official documentation is primarily available through the hosted Swagger UI at `https://api.jellyfin.org` or a locally running Jellyfin instance; supplemental guidance resides in the Jellyfin docs portal.

## Detailed Findings

### Playstate Management
- `PlaystateController` defines current endpoints for marking media as played/unplayed and for reporting playback lifecycle events, with legacy routes retained for compatibility ([Jellyfin.Api/Controllers/PlaystateController.cs#L67-L344](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/PlaystateController.cs#L67-L344)).
  - Mark item played: `POST /UserPlayedItems/{itemId}` with optional `userId` and `datePlayed` query parameters ([lines 67-95](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/PlaystateController.cs#L67-L95)).
  - Mark item unplayed: `DELETE /UserPlayedItems/{itemId}` ([lines 107-133](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/PlaystateController.cs#L107-L133)).
  - Playback start/report/stop: `POST /Sessions/Playing`, `/Sessions/Playing/Progress`, `/Sessions/Playing/Stopped`, each accepting structured payloads (`PlaybackStartInfo`, `PlaybackProgressInfo`, `PlaybackStopInfo`) and returning `204 No Content` ([lines 144-189](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/PlaystateController.cs#L144-L189)).
  - Session keep-alive: `POST /Sessions/Playing/Ping` with `playSessionId` query parameter ([lines 168-175](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/PlaystateController.cs#L168-L175)).
  - Legacy endpoints under `/Users/{userId}/PlayingItems/...` and `/PlayingItems/...` remain available but are marked `[Obsolete]` ([lines 190-344](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/PlaystateController.cs#L190-L344)).
- Data contracts for playback events reside under `MediaBrowser.Model.Session`, notably `PlaybackProgressInfo`, `PlaybackStartInfo`, and `PlaybackStopInfo` ([MediaBrowser.Model/Session/PlaybackProgressInfo.cs](https://github.com/jellyfin/jellyfin/blob/master/MediaBrowser.Model/Session/PlaybackProgressInfo.cs)).

### User Management and Authentication
- `UserController` centralizes user lifecycle, authentication, configuration, and password flows ([Jellyfin.Api/Controllers/UserController.cs#L95-L433](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/UserController.cs#L95-L433)).
  - Listing users: `GET /Users` (optional filters for hidden/disabled) requires authorization; `GET /Users/Public` exposes public profiles without auth ([lines 95-125](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/UserController.cs#L95-L125)).
  - Retrieve specific user or current user: `GET /Users/{userId}` with parental control bypass policy, and `GET /Users/Me` for token owner ([lines 130-145](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/UserController.cs#L130-L145), [lines 418-435](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/UserController.cs#L418-L435)).
  - Create user: `POST /Users/New` requires elevated privileges, accepting `CreateUserByName` payload ([lines 384-401](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/UserController.cs#L384-L401)).
  - Update profile: `POST /Users` (or legacy `POST /Users/{userId}`) for display name and related fields ([lines 268-312](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/UserController.cs#L268-L312)).
  - Manage policy and configuration: `POST /Users/{userId}/Policy` (requires elevation) and `POST /Users/Configuration` (user or admin) for `UserPolicy` and `UserConfiguration` objects respectively ([lines 317-357](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/UserController.cs#L317-L357)).
  - Authentication: `POST /Users/AuthenticateByName` and `POST /Users/AuthenticateWithQuickConnect` deliver tokens; legacy `POST /Users/{userId}/Authenticate` remains for compatibility ([lines 150-220](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/UserController.cs#L150-L220)).
  - Password management: `POST /Users/Password` (or legacy `POST /Users/{userId}/Password`) updates credentials; `POST /Users/ForgotPassword` and `POST /Users/ForgotPassword/Pin` support reset flow ([lines 225-433](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/UserController.cs#L225-L433)).
  - Deletion: `DELETE /Users/{userId}` requires elevation and removes tokens ([lines 147-170](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/UserController.cs#L147-L170)).
- Authentication responses carry access tokens consumed in `Authorization: MediaBrowser Token="..."` headers, per official guidance ([Jellyfin Docs – API Authentication](https://jellyfin.org/docs/general/administration/rest-api/#authentication)).

### Configuration and Backup Interfaces
- `ConfigurationController` exposes server-level configuration read/write operations ([Jellyfin.Api/Controllers/ConfigurationController.cs](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/ConfigurationController.cs)).
  - Retrieve or update full server configuration via `GET /System/Configuration` and `POST /System/Configuration` (update requires elevation).
  - Named configuration segments available at `GET/POST /System/Configuration/{key}` for targeted settings.
- `BackupController` implements server backups and restores ([Jellyfin.Api/Controllers/BackupController.cs](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/BackupController.cs)).
  - `POST /Backups/Create`: generates backup archives using `BackupOptionsDto` (includes database, metadata, subtitles, trickplay flags).
  - `GET /Backups`: lists existing archives.
  - `POST /Backups/Restore`: triggers restoration from specified archive (requires elevation and results in server restart).
  - `GET /Backups/Manifest`: inspects archive contents via `BackupManifestDto`.
- `DisplayPreferencesController` manages per-user, per-client view settings through `GET/POST /DisplayPreferences/{displayPreferencesId}`, using `DisplayPreferencesDto` payloads ([Jellyfin.Api/Controllers/DisplayPreferencesController.cs](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/DisplayPreferencesController.cs)).
- `PluginsController` covers plugin listings and configuration adjustments, including `GET /Plugins` and `POST /Plugins/{pluginId}/Configuration` for `BasePluginConfiguration` documents ([Jellyfin.Api/Controllers/PluginsController.cs](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/PluginsController.cs)).

### Configuration Data Models
- `ServerConfiguration` encapsulates server-wide settings such as metadata paths, language/country codes, resume thresholds, library monitoring cadence, remote access limits, and image processing constraints ([MediaBrowser.Model/Configuration/ServerConfiguration.cs](https://github.com/jellyfin/jellyfin/blob/master/MediaBrowser.Model/Configuration/ServerConfiguration.cs#L35-L155)).
- `UserConfiguration` stores per-user preferences including audio/subtitle language defaults, auto-play behavior, UI filters (hide played in latest, display collections), grouped folders, and casting settings ([MediaBrowser.Model/Configuration/UserConfiguration.cs](https://github.com/jellyfin/jellyfin/blob/master/MediaBrowser.Model/Configuration/UserConfiguration.cs#L25-L85)).
- `UserPolicy` defines access controls (library access lists, parental restrictions, administrative rights) aiding multi-user synchronization scenarios ([MediaBrowser.Model/Users/UserPolicy.cs](https://github.com/jellyfin/jellyfin/blob/master/MediaBrowser.Model/Users/UserPolicy.cs)).

### Official Documentation Touchpoints
- REST API overview and references: [https://jellyfin.org/docs/general/administration/rest-api/](https://jellyfin.org/docs/general/administration/rest-api/)
- User management guidance (describing that accounts are local to each server instance): [https://jellyfin.org/docs/general/server/users/adding-managing-users](https://jellyfin.org/docs/general/server/users/adding-managing-users)
- Quick Connect feature documentation: [https://jellyfin.org/docs/general/server/quick-connect/](https://jellyfin.org/docs/general/server/quick-connect/)
- Backup and restore documentation: [https://jellyfin.org/docs/general/administration/backup-and-restore](https://jellyfin.org/docs/general/administration/backup-and-restore)

## Code References
- `Jellyfin.Api/Controllers/PlaystateController.cs:67-344` – Current and legacy playstate endpoints.
- `Jellyfin.Api/Controllers/UserController.cs:95-433` – User listing, creation, configuration, authentication, and password flows.
- `Jellyfin.Api/Controllers/ConfigurationController.cs` – Server configuration read/write endpoints.
- `Jellyfin.Api/Controllers/BackupController.cs` – Backup creation, listing, and restore operations.
- `Jellyfin.Api/Controllers/DisplayPreferencesController.cs` – User display preference endpoints.
- `Jellyfin.Api/Controllers/PluginsController.cs` – Plugin configuration management.
- `MediaBrowser.Model/Configuration/ServerConfiguration.cs:35-155` – Server configuration properties relevant to sync.
- `MediaBrowser.Model/Configuration/UserConfiguration.cs:25-85` – User preference properties.
- `MediaBrowser.Model/Users/UserPolicy.cs` – User access policy definition.
- `MediaBrowser.Model/Session/PlaybackProgressInfo.cs` – Playback progress payload definition.

## Architecture Documentation
Jellyfin structures its REST API using ASP.NET controllers grouped by domain (users, playstate, configuration, backups, plugins). Common patterns include:
- Authorization attributes encode role requirements (`RequiresElevation` for administrator-only actions, `IgnoreParentalControl` for unrestricted reads).
- Current endpoints reside alongside `[Obsolete]` legacy routes, enabling clients to transition gradually.
- DTOs under `MediaBrowser.Model` define serialization contracts for both server configuration (`ServerConfiguration`, `MetadataOptions`) and user-centric data (`UserConfiguration`, `UserItemDataDto`).
- Configuration updates follow a full-replacement model, while backups operate via archive manifests referencing filesystem paths and metadata assets.

## Historical Context (from thoughts/)
- No existing thoughts/ documents were located for Jellyfin or API integration topics.

## Related Research
- None recorded yet.

## Open Questions
- Determine how websocket-based session notifications complement REST playstate endpoints for near-real-time sync.
- Clarify API rate limiting or throttling policies, as no explicit limits are documented in the reviewed sources.
- Investigate handling of absolute filesystem paths within backup manifests when synchronizing across heterogeneous environments.

## Follow-up Research 2025-10-31T14:42:33+00:00Z
User asked which additional research areas are needed to plan a scheduled cross-instance Jellyfin sync service. Key investigation themes:
- **Authentication and Permissions**: Confirm administrator token management across instances and audit Quick Connect suitability versus standard token issuance for headless services.
- **Data Reconciliation Workflow**: Understand how Jellyfin represents user identities (GUIDs, names) and watch-state timestamps to design conflict resolution when merging divergent states.
- **Bulk Export Mechanisms**: Explore whether REST endpoints allow enumerating all user settings, policies, and playstate in a single sweep and identify pagination strategies.
- **Change Detection**: Investigate API support for last-modified timestamps or incremental sync markers for users, configurations, and item states to minimize payload size.
- **Display Preferences Scope**: Document how per-client display preferences are keyed (displayPreferencesId, client) to ensure the sync covers client-specific UI settings when desired.
- **Plugin and Server Configuration Dependencies**: Determine the extent of plugin-specific configuration APIs and how plugin availability differences impact cross-instance synchronization.
- **Backup Archive Schema**: Review backup manifest structure (`BackupManifestDto`) to evaluate whether a backup-based approach is viable for transferring configuration/state between servers on a scheduled basis.
- **WebSocket/Real-time Channels**: Clarify whether periodic polling or optional websocket subscriptions are needed for timely watch-state updates when cron frequency is low.
- **User Policy Interactions**: Examine how `UserPolicy` intersects with `UserConfiguration` and library access controls when aligning user permissions between instances.
- **Rate Limiting and Throttling**: Verify Jellyfin server behaviors under repeated API sweeps to plan cron scheduling that avoids overloading instances.
