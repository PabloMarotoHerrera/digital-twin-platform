from __future__ import annotations

import omni.ui as ui


def build_telemetry_section(ext):
    with ui.CollapsableFrame("Telemetry / Data Ingestion", collapsed=False):
        with ui.VStack(spacing=6):
            ext._telemetry_status_label = ui.Label("")
            ext._mqtt_status_label = ui.Label("")
            with ui.HStack():
                ui.Label("Mode", width=135)
                mode_combo = ui.ComboBox(ext._telemetry_mode_index, "Playback", "Live")
                ext._telemetry_mode_model = mode_combo.model
                ext._telemetry_mode_model.add_item_changed_fn(ext._on_telemetry_mode_changed)
            with ui.HStack():
                ui.Label("Sensor ID", width=135)
                sensor_field = ui.StringField()
                ext._telemetry_sensor_model = sensor_field.model
                ext._telemetry_sensor_model.set_value(ext._telemetry_sensor_id)
            with ui.HStack():
                ui.Label("Channel", width=135)
                channel_field = ui.StringField()
                ext._telemetry_channel_model = channel_field.model
                ext._telemetry_channel_model.set_value(ext._telemetry_channel)
            with ui.HStack():
                ui.Label("Local File", width=135)
                file_field = ui.StringField()
                ext._telemetry_path_model = file_field.model
                ext._telemetry_path_model.set_value(ext._telemetry_path)
            with ui.HStack():
                ui.Label("MQTT Host", width=135)
                host_field = ui.StringField()
                ext._mqtt_host_model = host_field.model
                ext._mqtt_host_model.set_value(ext._mqtt_host)
            with ui.HStack():
                ui.Label("MQTT Port", width=135)
                port_field = ui.IntField()
                ext._mqtt_port_model = port_field.model
                ext._mqtt_port_model.set_value(ext._mqtt_port)
            with ui.HStack():
                ui.Label("MQTT Topic", width=135)
                topic_field = ui.StringField()
                ext._mqtt_topic_model = topic_field.model
                ext._mqtt_topic_model.set_value(ext._mqtt_topic)
            with ui.HStack():
                ui.Spacer()
                ui.Button("Load CSV", width=110, clicked_fn=ext._load_csv_for_selected_zone)
                ui.Button("Load JSON", width=110, clicked_fn=ext._load_json_for_selected_zone)
                ui.Button("Bind Live Stub", width=110, clicked_fn=ext._generate_live_stub_for_selected_zone)
            with ui.HStack():
                ui.Spacer()
                ui.Button("Bind MQTT", width=110, clicked_fn=ext._bind_mqtt_for_selected_zone)
                ui.Button("Connect MQTT", width=110, clicked_fn=ext._connect_mqtt)
                ui.Button("Disconnect", width=110, clicked_fn=ext._disconnect_mqtt)
            ui.Label(
                "Expected CSV: timestamp,value or timestamp,temp,humidity. "
                "timestamp can be HH:MM[:SS], seconds, or epoch.",
                word_wrap=True,
            )
            ui.Label(
                "Playback mode reuses imported full-day series. "
                "Live mode appends samples in real time from the stub or MQTT.",
                word_wrap=True,
            )
