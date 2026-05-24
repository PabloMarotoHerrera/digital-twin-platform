# AEC Thermal / Telemetry

This extension provides:

- synthetic thermal playback for AEC Spaces
- telemetry/data ingestion for zone-linked time series
- viewport coloring + plot playback synchronized by time

## MVP workflow

1. Open `Window -> AEC Thermal`
2. Refresh zones
3. Select a zone
4. In `Telemetry / Data Ingestion`:
   - set `Sensor ID`
   - set `Channel` (for MVP usually `temp`)
   - enter a local CSV or JSON path
   - click `Load CSV` or `Load JSON`
5. Use the existing playback controls to scrub/play the imported series
6. Enable viewport heatmap to visualize the current value per zone

## CSV format

Supported formats:

```csv
timestamp,value
00:00:00,20.1
00:15:00,20.4
00:30:00,20.7
```

or:

```csv
timestamp,temp,humidity
00:00:00,20.1,44.0
00:15:00,20.4,43.5
```

`timestamp` can be:

- `HH:MM`
- `HH:MM:SS`
- seconds
- epoch seconds / epoch milliseconds

For epoch timestamps, the series is normalized internally so playback starts at `0h`.

## JSON format

Example:

```json
[
  {"timestamp": "00:00:00", "temp": 20.1},
  {"timestamp": "00:15:00", "temp": 20.4}
]
```

or:

```json
{
  "samples": [
    {"timestamp": "00:00:00", "temp": 20.1},
    {"timestamp": "00:15:00", "temp": 20.4}
  ]
}
```

## Live mode MVP

Set `Mode = Live`, then click `Bind Live Stub` for the selected zone.

After that:

1. Use the existing `Play / Pause` controls in `Viewport Heatmap`
2. Each update tick appends a new sample into the in-memory time-series store
3. The plot, current value, and viewport update in sync

This is a placeholder for future drivers such as:

- MQTT
- REST polling
- WebSocket

## MQTT live mode

1. Set `Mode = Live`
2. Fill:
   - `Sensor ID`
   - `Channel` (usually `temp`)
   - `MQTT Host`
   - `MQTT Port`
   - `MQTT Topic`
3. Click `Bind MQTT` for the selected zone
4. Click `Connect MQTT`
5. When samples arrive, the plot, current value, and viewport update in real time

Recommended topic:

```text
aec/#
```

Recommended payload:

```json
{
  "sensor_id": "bedroom_sensor_01",
  "zone_id": "Space_01",
  "timestamp": 1777051200,
  "temp": 22.41,
  "humidity": 48.2
}
```

Alternative payload with grouped channels:

```json
{
  "sensor_id": "bedroom_sensor_01",
  "zone_id": "Space_01",
  "timestamp": "12:30:00",
  "channels": {
    "temp": 22.41,
    "humidity": 48.2
  }
}
```
