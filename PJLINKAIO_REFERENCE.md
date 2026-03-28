# PJLink AIO - Home Assistant Integration Reference

## Overview

PJLink AIO (`pjlinkaio`) is a Home Assistant custom integration for controlling PJLink-compatible projectors and displays. It uses the `aiopjlink` library and supports both **PJLink Class 1** and **Class 2** commands.

The integration domain is `pjlinkaio`. All entity IDs follow the pattern `<platform>.pjlinkaio_<entity_name>`.

---

## Entities

### media_player

One entity per projector. This is the primary control entity.

| Entity ID pattern | `media_player.pjlinkaio_<projector_name>` |
|---|---|
| **States** | `on`, `off` |

#### Supported features

| Feature | Description |
|---|---|
| `turn_on` | Power the projector on |
| `turn_off` | Power the projector off |
| `volume_mute` | Toggle audio mute on/off |
| `select_source` | Switch input source |

#### Services

```yaml
# Power on
service: media_player.turn_on
target:
  entity_id: media_player.pjlinkaio_<name>

# Power off
service: media_player.turn_off
target:
  entity_id: media_player.pjlinkaio_<name>

# Mute / unmute audio
service: media_player.mute_volume
target:
  entity_id: media_player.pjlinkaio_<name>
data:
  is_volume_muted: true  # or false

# Select input source
service: media_player.select_source
target:
  entity_id: media_player.pjlinkaio_<name>
data:
  source: "HDMI 1"  # use value from source_list attribute
```

#### Attributes

| Attribute | Type | Description |
|---|---|---|
| `source` | string | Current input source name (e.g. `"DIGITAL 1"`, or a custom name if Class 2) |
| `source_list` | list[string] | All available input sources |
| `is_volume_muted` | bool | Whether audio is currently muted |
| `video_muted` | bool | Whether video output is blanked |
| `pjlink_class` | string | `"1"` or `"2"` |

---

### sensor (Diagnostic)

All sensors have `entity_category: diagnostic`.

#### Power state

| Entity ID pattern | `sensor.pjlinkaio_<name>_power_state` |
|---|---|
| **Values** | `Off`, `On`, `Cooling`, `Warming` |
| **Icon** | `mdi:power` |

More granular than the media_player state. Shows transitional states (warming/cooling) that the media_player maps to on/off.

#### Lamp hours (per lamp)

| Entity ID pattern | `sensor.pjlinkaio_<name>_lamp_<N>_hours` |
|---|---|
| **Value** | integer (hours) |
| **Device class** | `duration` |
| **Unit** | `h` |
| **Icon** | `mdi:lightbulb-on-outline` |

One sensor per lamp. Most projectors have 1 lamp; some have up to 8. The value is cumulative usage hours since last reset/replacement.

#### Lamp status (per lamp)

| Entity ID pattern | `sensor.pjlinkaio_<name>_lamp_<N>_status` |
|---|---|
| **Values** | `On`, `Off` |
| **Icon** | `mdi:lightbulb` |

#### Error status (per category)

Six sensors, one for each PJLink error category:

| Entity ID pattern | Values | Description |
|---|---|---|
| `sensor.pjlinkaio_<name>_fan_status` | `OK`, `Warning`, `Error` | Fan error status |
| `sensor.pjlinkaio_<name>_lamp_status` | `OK`, `Warning`, `Error` | Lamp error status |
| `sensor.pjlinkaio_<name>_temperature_status` | `OK`, `Warning`, `Error` | Temperature error status |
| `sensor.pjlinkaio_<name>_cover_status` | `OK`, `Warning`, `Error` | Cover error status |
| `sensor.pjlinkaio_<name>_filter_status` | `OK`, `Warning`, `Error` | Filter error status |
| `sensor.pjlinkaio_<name>_other_status` | `OK`, `Warning`, `Error` | Other error status |

Icons change dynamically: `mdi:check-circle-outline` (OK), `mdi:alert` (Warning), `mdi:alert-circle` (Error).

#### Filter hours (Class 2 only)

| Entity ID pattern | `sensor.pjlinkaio_<name>_filter_hours` |
|---|---|
| **Value** | integer (hours) |
| **Device class** | `duration` |
| **Unit** | `h` |
| **Icon** | `mdi:air-filter` |

#### Input resolution (Class 2 only)

| Entity ID pattern | `sensor.pjlinkaio_<name>_input_resolution` |
|---|---|
| **Value** | string, e.g. `"1920x1080"` |
| **Icon** | `mdi:monitor` |

Only populated when the projector is on and receiving a signal. `None` when off or no signal.

#### Recommended resolution (Class 2 only)

| Entity ID pattern | `sensor.pjlinkaio_<name>_recommended_resolution` |
|---|---|
| **Value** | string, e.g. `"1920x1200"` |
| **Icon** | `mdi:monitor-star` |

The native/optimal resolution reported by the projector.

#### PJLink class

| Entity ID pattern | `sensor.pjlinkaio_<name>_pjlink_class` |
|---|---|
| **Value** | `"1"` or `"2"` |
| **Icon** | `mdi:information-outline` |

---

### switch

#### Video mute (all classes)

| Entity ID pattern | `switch.pjlinkaio_<name>_video_mute` |
|---|---|
| **States** | `on` (screen blanked), `off` (showing image) |
| **Icon** | `mdi:projector-off` |
| **Availability** | Only when projector is on |

```yaml
service: switch.turn_on  # blank screen
target:
  entity_id: switch.pjlinkaio_<name>_video_mute

service: switch.turn_off  # show image
target:
  entity_id: switch.pjlinkaio_<name>_video_mute
```

#### Freeze frame (Class 2 only)

| Entity ID pattern | `switch.pjlinkaio_<name>_freeze` |
|---|---|
| **States** | `on` (frozen), `off` (live) |
| **Icon** | `mdi:pause-box` |
| **Availability** | Only when projector is on |

```yaml
service: switch.turn_on  # freeze frame
target:
  entity_id: switch.pjlinkaio_<name>_freeze

service: switch.turn_off  # resume live
target:
  entity_id: switch.pjlinkaio_<name>_freeze
```

---

### button (Class 2 only)

PJLink has no absolute volume get/set -- only step increment/decrement. These are exposed as buttons.

| Entity ID pattern | Icon | Description |
|---|---|---|
| `button.pjlinkaio_<name>_speaker_volume_up` | `mdi:volume-plus` | Increase speaker volume by one step |
| `button.pjlinkaio_<name>_speaker_volume_down` | `mdi:volume-minus` | Decrease speaker volume by one step |
| `button.pjlinkaio_<name>_microphone_volume_up` | `mdi:microphone-plus` | Increase microphone volume by one step |
| `button.pjlinkaio_<name>_microphone_volume_down` | `mdi:microphone-minus` | Decrease microphone volume by one step |

All buttons are only available when the projector is on.

```yaml
service: button.press
target:
  entity_id: button.pjlinkaio_<name>_speaker_volume_up
```

---

## Device Info

Each projector registers as a device in HA's device registry with the following fields (populated from PJLink queries):

| Field | PJLink command | Example |
|---|---|---|
| Name | `NAME` | `"Optoma UHD38"` |
| Manufacturer | `INF1` | `"Optoma"` |
| Model | `INF2` | `"UHD38"` |
| Serial number | `SNUM` (Class 2) | `"ABC12345"` |
| Firmware version | `SVER` (Class 2) | `"1.03"` |

---

## Dashboard Card Reference

Use the entity IDs and services above to build a projector control dashboard. Below are example card configurations matching the layout style in the reference screenshot.

### Power toggle

```yaml
type: entities
title: Projector
entities:
  - entity: media_player.pjlinkaio_<name>
    name: Projector Power
    icon: mdi:power
    tap_action:
      action: toggle
```

### Source selector

```yaml
type: entities
entities:
  - entity: media_player.pjlinkaio_<name>
    type: attribute
    attribute: source_list
```

Or use a full media control card which provides a source dropdown:

```yaml
type: media-control
entity: media_player.pjlinkaio_<name>
```

### Volume controls (3-button row: Mute, Vol Down, Vol Up)

```yaml
type: horizontal-stack
cards:
  - type: button
    name: Mute
    icon: mdi:volume-off
    entity: media_player.pjlinkaio_<name>
    tap_action:
      action: call-service
      service: media_player.mute_volume
      service_data:
        is_volume_muted: true
      target:
        entity_id: media_player.pjlinkaio_<name>
    hold_action:
      action: call-service
      service: media_player.mute_volume
      service_data:
        is_volume_muted: false
      target:
        entity_id: media_player.pjlinkaio_<name>
  - type: button
    name: Vol Down
    icon: mdi:volume-minus
    entity: button.pjlinkaio_<name>_speaker_volume_down
    tap_action:
      action: call-service
      service: button.press
      target:
        entity_id: button.pjlinkaio_<name>_speaker_volume_down
  - type: button
    name: Vol Up
    icon: mdi:volume-plus
    entity: button.pjlinkaio_<name>_speaker_volume_up
    tap_action:
      action: call-service
      service: button.press
      target:
        entity_id: button.pjlinkaio_<name>_speaker_volume_up
```

### Lamp hours (numeric)

```yaml
type: entity
entity: sensor.pjlinkaio_<name>_lamp_1_hours
name: Projector Lamp Hours
icon: mdi:lightbulb-on-outline
```

### Lamp hours (gauge)

```yaml
type: gauge
entity: sensor.pjlinkaio_<name>_lamp_1_hours
name: Projector Lamp Hours
min: 0
max: 10000
severity:
  green: 0
  yellow: 5000
  red: 8000
```

### Video mute / Freeze switches

```yaml
type: horizontal-stack
cards:
  - type: button
    name: Video Mute
    icon: mdi:projector-off
    entity: switch.pjlinkaio_<name>_video_mute
    tap_action:
      action: toggle
  - type: button
    name: Freeze
    icon: mdi:pause-box
    entity: switch.pjlinkaio_<name>_freeze
    tap_action:
      action: toggle
```

### Error status overview

```yaml
type: entities
title: Projector Status
entities:
  - entity: sensor.pjlinkaio_<name>_power_state
    name: Power
  - entity: sensor.pjlinkaio_<name>_pjlink_class
    name: PJLink Class
  - entity: sensor.pjlinkaio_<name>_fan_status
    name: Fan
  - entity: sensor.pjlinkaio_<name>_lamp_status
    name: Lamp
  - entity: sensor.pjlinkaio_<name>_temperature_status
    name: Temperature
  - entity: sensor.pjlinkaio_<name>_cover_status
    name: Cover
  - entity: sensor.pjlinkaio_<name>_filter_status
    name: Filter
```

### Resolution info (Class 2)

```yaml
type: entities
title: Signal Info
entities:
  - entity: sensor.pjlinkaio_<name>_input_resolution
    name: Input Resolution
  - entity: sensor.pjlinkaio_<name>_recommended_resolution
    name: Recommended Resolution
```

### Filter hours (Class 2)

```yaml
type: entity
entity: sensor.pjlinkaio_<name>_filter_hours
name: Filter Hours
icon: mdi:air-filter
```

---

## Full Dashboard Example

A two-column layout combining all sections:

```yaml
type: vertical-stack
title: Projector Control
cards:
  - type: horizontal-stack
    cards:
      # Left column: Power + Sources
      - type: vertical-stack
        cards:
          - type: button
            name: Projector Power
            icon: mdi:power
            entity: media_player.pjlinkaio_<name>
            show_state: true
            tap_action:
              action: toggle
          - type: media-control
            entity: media_player.pjlinkaio_<name>
      # Right column: Volume + Diagnostics
      - type: vertical-stack
        cards:
          - type: horizontal-stack
            cards:
              - type: button
                name: Mute
                icon: mdi:volume-off
                entity: media_player.pjlinkaio_<name>
                tap_action:
                  action: call-service
                  service: media_player.mute_volume
                  service_data:
                    is_volume_muted: true
                  target:
                    entity_id: media_player.pjlinkaio_<name>
                hold_action:
                  action: call-service
                  service: media_player.mute_volume
                  service_data:
                    is_volume_muted: false
                  target:
                    entity_id: media_player.pjlinkaio_<name>
              - type: button
                name: Vol Down
                icon: mdi:volume-minus
                entity: button.pjlinkaio_<name>_speaker_volume_down
                tap_action:
                  action: call-service
                  service: button.press
                  target:
                    entity_id: button.pjlinkaio_<name>_speaker_volume_down
              - type: button
                name: Vol Up
                icon: mdi:volume-plus
                entity: button.pjlinkaio_<name>_speaker_volume_up
                tap_action:
                  action: call-service
                  service: button.press
                  target:
                    entity_id: button.pjlinkaio_<name>_speaker_volume_up
          - type: entity
            entity: sensor.pjlinkaio_<name>_lamp_1_hours
            name: Projector Lamp Hours
          - type: gauge
            entity: sensor.pjlinkaio_<name>_lamp_1_hours
            name: Lamp Hours
            min: 0
            max: 10000
            severity:
              green: 0
              yellow: 5000
              red: 8000
          - type: horizontal-stack
            cards:
              - type: button
                name: Video Mute
                icon: mdi:projector-off
                entity: switch.pjlinkaio_<name>_video_mute
                tap_action:
                  action: toggle
              - type: button
                name: Freeze
                icon: mdi:pause-box
                entity: switch.pjlinkaio_<name>_freeze
                tap_action:
                  action: toggle
```

---

## Notes

- **Polling interval**: 30 seconds. State updates are not instant after commands; a refresh is triggered after each command but the projector may take a moment to change state.
- **Connection model**: Each poll opens a new TCP connection, sends queries, and closes. This is by design -- PJLink is a session-based protocol.
- **Class 2 entities**: Freeze switch, filter hours sensor, resolution sensors, and volume buttons are only created if the projector reports PJLink Class 2 support.
- **Volume limitation**: PJLink does not expose an absolute volume level. Volume can only be stepped up/down by one unit per button press. There is no way to read the current volume level. A volume slider is not possible with PJLink.
- **Entity availability**: Volume buttons, freeze switch, and video mute switch are marked unavailable when the projector is off or cooling down.
