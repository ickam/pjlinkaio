# PJLink AIO

A Home Assistant custom integration for PJLink-compatible projectors and displays, built on the async [aiopjlink](https://pypi.org/project/aiopjlink/) library. Supports both **PJLink Class 1** and **Class 2** commands.

This is a modern replacement for the legacy [built-in PJLink integration](https://www.home-assistant.io/integrations/pjlink/) which uses the abandoned synchronous `pypjlink2` library and only supports Class 1.

## Features

- **Async** -- native `asyncio`, no blocking I/O
- **PJLink Class 1 + Class 2** -- all standard commands supported
- **Config flow** -- UI-based setup via Settings > Integrations
- **4 entity platforms**:
  - `media_player` -- power on/off, audio mute, input source selection
  - `sensor` -- power state, lamp hours/status, error categories, filter hours, resolution, PJLink class (all diagnostic)
  - `switch` -- video mute (blank screen), freeze frame (Class 2)
  - `button` -- speaker/microphone volume up/down (Class 2)
- **DataUpdateCoordinator** -- efficient polling with connect-per-poll model
- **Class 2 auto-detection** -- extra entities only created when the projector reports Class 2 support
- **Device registry** -- manufacturer, model, serial number, firmware version populated from PJLink queries

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click the three-dot menu in the top right and select **Custom repositories**
3. Add `https://github.com/ickam/pjlinkaio` with category **Integration**
4. Search for "PJLink AIO" and install it
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/pjlinkaio/` directory into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for **PJLink AIO**
3. Enter the projector's IP address (or hostname), port (default 4352), and password (if set)
4. The integration will connect, detect the PJLink class, and create all applicable entities

## Entities

### media_player

Primary control entity. Supports power on/off, audio mute toggle, and input source selection.

| Feature | Service |
|---|---|
| Power on | `media_player.turn_on` |
| Power off | `media_player.turn_off` |
| Audio mute | `media_player.mute_volume` |
| Source select | `media_player.select_source` |

### sensor (diagnostic)

| Sensor | Description | Notes |
|---|---|---|
| Power state | `Off`, `On`, `Cooling`, `Warming` | More granular than media_player state |
| Lamp N hours | Cumulative lamp usage in hours | One per lamp (most projectors have 1) |
| Lamp N status | `On` / `Off` | One per lamp |
| Fan status | `OK` / `Warning` / `Error` | |
| Lamp error status | `OK` / `Warning` / `Error` | |
| Temperature status | `OK` / `Warning` / `Error` | |
| Cover status | `OK` / `Warning` / `Error` | |
| Filter status | `OK` / `Warning` / `Error` | |
| Other status | `OK` / `Warning` / `Error` | |
| Filter hours | Filter usage in hours | Class 2 only |
| Input resolution | e.g. `1920x1080` | Class 2 only |
| Recommended resolution | e.g. `1920x1200` | Class 2 only |
| PJLink class | `1` or `2` | |

### switch

| Switch | Description | Notes |
|---|---|---|
| Video mute | Blank/unblank the projected image | Available when projector is on |
| Freeze | Freeze/unfreeze the frame | Class 2 only, available when projector is on |

### button

| Button | Description | Notes |
|---|---|---|
| Speaker volume up | Step speaker volume up | Class 2 only |
| Speaker volume down | Step speaker volume down | Class 2 only |
| Microphone volume up | Step microphone volume up | Class 2 only |
| Microphone volume down | Step microphone volume down | Class 2 only |

> PJLink does not support absolute volume levels -- only step increment/decrement. There is no way to read the current volume, so a volume slider is not possible.

## Technical Notes

- **Polling interval**: 30 seconds
- **Connection model**: Each poll cycle opens a new TCP connection, queries the projector, and closes. PJLink is a session-based protocol -- this is by design.
- **Port**: PJLink standard port is TCP 4352
- **Authentication**: Supports PJLink password authentication (optional)
- **Entity availability**: Volume buttons, freeze switch, and video mute switch are marked unavailable when the projector is off or cooling

## About the Two Variants

This repo contains two copies of the integration:

| Directory | Domain | Purpose |
|---|---|---|
| `custom_components/pjlinkaio/` | `pjlinkaio` | **Test variant** -- safe to run alongside the built-in `pjlink` integration |
| `custom_components/pjlink/` | `pjlink` | **Final variant** -- replaces the built-in integration entirely (includes YAML import) |

For initial testing, use the `pjlinkaio` variant. When you're ready to replace the legacy integration, switch to the `pjlink` variant.

## License

MIT
