from __future__ import annotations

import json
import socket
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class MqttMessage:
    topic: str
    payload_text: str

    def payload_json(self) -> dict | None:
        try:
            payload = json.loads(self.payload_text)
        except Exception:
            return None
        return payload if isinstance(payload, dict) else None


class SimpleMqttClient:
    def __init__(self):
        self._host = "127.0.0.1"
        self._port = 1883
        self._topic = "aec/#"
        self._client_id = f"aec-thermal-{uuid.uuid4().hex[:8]}"
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._messages: deque[MqttMessage] = deque()
        self._lock = threading.Lock()
        self._status = "Disconnected"
        self._connected = False
        self._sock: socket.socket | None = None
        self._packet_id = 1

    @property
    def status(self) -> str:
        with self._lock:
            return self._status

    @property
    def is_connected(self) -> bool:
        with self._lock:
            return self._connected

    @property
    def topic(self) -> str:
        return self._topic

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    def connect(self, host: str, port: int, topic: str):
        self.disconnect()
        self._host = host.strip() or "127.0.0.1"
        self._port = max(1, int(port))
        self._topic = topic.strip() or "aec/#"
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="AEC MQTT", daemon=True)
        self._thread.start()

    def disconnect(self):
        self._stop_event.set()
        sock = self._sock
        self._sock = None
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self._thread = None
        with self._lock:
            self._connected = False
            self._status = "Disconnected"

    def poll_messages(self) -> list[MqttMessage]:
        with self._lock:
            items = list(self._messages)
            self._messages.clear()
        return items

    def _set_status(self, text: str, connected: bool | None = None):
        with self._lock:
            self._status = text
            if connected is not None:
                self._connected = connected

    def _push_message(self, message: MqttMessage):
        with self._lock:
            self._messages.append(message)
            while len(self._messages) > 512:
                self._messages.popleft()

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self._set_status(f"Connecting to {self._host}:{self._port}...", connected=False)
                sock = socket.create_connection((self._host, self._port), timeout=5.0)
                sock.settimeout(0.5)
                self._sock = sock
                self._send_connect(sock)
                packet_type, _flags, payload = self._read_packet(sock)
                if packet_type != 2 or len(payload) < 2 or payload[1] != 0:
                    raise RuntimeError("MQTT CONNACK rejected")
                self._send_subscribe(sock, self._topic)
                self._set_status(f"Connected: {self._host}:{self._port} [{self._topic}]", connected=True)
                last_io = time.time()
                while not self._stop_event.is_set():
                    try:
                        packet_type, flags, payload = self._read_packet(sock)
                        last_io = time.time()
                        if packet_type == 3:
                            topic, message = self._parse_publish(flags, payload)
                            self._push_message(MqttMessage(topic=topic, payload_text=message))
                        elif packet_type == 13:
                            continue
                    except socket.timeout:
                        if time.time() - last_io > 20.0:
                            self._send_ping(sock)
                            last_io = time.time()
                        continue
            except Exception as exc:
                self._set_status(f"MQTT disconnected: {exc}", connected=False)
                time.sleep(2.0)
            finally:
                sock = self._sock
                self._sock = None
                if sock is not None:
                    try:
                        sock.close()
                    except Exception:
                        pass
        self._set_status("Disconnected", connected=False)

    def _next_packet_id(self) -> int:
        self._packet_id = 1 if self._packet_id >= 65535 else self._packet_id + 1
        return self._packet_id

    def _send_connect(self, sock: socket.socket):
        client_id = self._encode_string(self._client_id)
        variable = self._encode_string("MQTT") + bytes([4, 2]) + (30).to_bytes(2, "big")
        payload = client_id
        packet = bytes([0x10]) + self._encode_remaining_length(len(variable) + len(payload)) + variable + payload
        sock.sendall(packet)

    def _send_subscribe(self, sock: socket.socket, topic: str):
        packet_id = self._next_packet_id()
        payload = self._encode_string(topic) + bytes([0])
        variable = packet_id.to_bytes(2, "big")
        packet = bytes([0x82]) + self._encode_remaining_length(len(variable) + len(payload)) + variable + payload
        sock.sendall(packet)

    def _send_ping(self, sock: socket.socket):
        sock.sendall(bytes([0xC0, 0x00]))

    def _read_packet(self, sock: socket.socket) -> tuple[int, int, bytes]:
        header = self._recv_exact(sock, 1)
        first = header[0]
        remaining = self._decode_remaining_length(sock)
        payload = self._recv_exact(sock, remaining) if remaining else b""
        return (first >> 4, first & 0x0F, payload)

    def _parse_publish(self, flags: int, payload: bytes) -> tuple[str, str]:
        topic_len = int.from_bytes(payload[0:2], "big")
        index = 2
        topic = payload[index:index + topic_len].decode("utf-8", errors="replace")
        index += topic_len
        qos = (flags >> 1) & 0x03
        if qos:
            index += 2
        message = payload[index:].decode("utf-8", errors="replace")
        return topic, message

    def _recv_exact(self, sock: socket.socket, size: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < size:
            piece = sock.recv(size - len(chunks))
            if not piece:
                raise ConnectionError("MQTT socket closed")
            chunks.extend(piece)
        return bytes(chunks)

    def _decode_remaining_length(self, sock: socket.socket) -> int:
        multiplier = 1
        value = 0
        while True:
            encoded = self._recv_exact(sock, 1)[0]
            value += (encoded & 127) * multiplier
            if (encoded & 128) == 0:
                return value
            multiplier *= 128
            if multiplier > 128 * 128 * 128:
                raise ValueError("Malformed MQTT remaining length")

    def _encode_remaining_length(self, value: int) -> bytes:
        encoded = bytearray()
        while True:
            digit = value % 128
            value //= 128
            if value > 0:
                digit |= 0x80
            encoded.append(digit)
            if value == 0:
                break
        return bytes(encoded)

    def _encode_string(self, value: str) -> bytes:
        data = value.encode("utf-8")
        return len(data).to_bytes(2, "big") + data
