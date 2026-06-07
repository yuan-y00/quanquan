from __future__ import annotations

import time
from dataclasses import dataclass


class SerialLinkError(RuntimeError):
    pass


@dataclass
class SendResult:
    sent: str
    lines: list[str]


def available_ports() -> list[str]:
    try:
        from serial.tools import list_ports
    except ImportError:
        return []
    return [port.device for port in list_ports.comports()]


class SerialLink:
    def __init__(self) -> None:
        self.mock = True
        self.port = ""
        self.baud_rate = 115200
        self.line_ending = "\r"
        self._serial = None
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(
        self,
        port: str,
        baud_rate: int,
        line_ending: str = "\r",
        mock: bool = True,
    ) -> list[str]:
        self.disconnect()
        self.mock = mock
        self.port = port.strip()
        self.baud_rate = int(baud_rate)
        self.line_ending = line_ending

        if self.mock:
            self._connected = True
            return [f"[MOCK CONNECT] {self.port or 'NO_PORT'} @ {self.baud_rate}"]

        if not self.port:
            raise SerialLinkError("Please enter a COM port, for example COM3.")

        try:
            import serial
        except ImportError as exc:
            raise SerialLinkError("pyserial is not installed. Run: pip install pyserial") from exc

        try:
            self._serial = serial.Serial(
                self.port,
                baudrate=self.baud_rate,
                timeout=0.15,
                write_timeout=1.0,
            )
        except Exception as exc:
            raise SerialLinkError(f"Cannot open {self.port}: {exc}") from exc

        self._connected = True
        time.sleep(0.2)
        return [f"[CONNECTED] {self.port} @ {self.baud_rate}"]

    def disconnect(self) -> list[str]:
        lines: list[str] = []
        if self._serial is not None:
            try:
                self._serial.close()
            finally:
                self._serial = None
                lines.append("[DISCONNECTED]")
        elif self._connected:
            lines.append("[DISCONNECTED]")
        self._connected = False
        return lines

    def send_line(self, command: str) -> SendResult:
        command = command.strip()
        if not command:
            raise SerialLinkError("Cannot send an empty command.")
        if not self._connected:
            raise SerialLinkError("Not connected.")

        if self.mock:
            return SendResult(command, [f"[MOCK SEND] {command}", "ok"])

        if self._serial is None:
            raise SerialLinkError("Serial port is not open.")

        payload = (command + self.line_ending).encode("ascii", errors="strict")
        self._serial.write(payload)
        self._serial.flush()
        lines = [f"> {command}"]
        lines.extend(self.read_available(wait_seconds=0.25))
        return SendResult(command, lines)

    def read_available(self, wait_seconds: float = 0.0) -> list[str]:
        if self.mock or self._serial is None:
            return []
        end_time = time.monotonic() + wait_seconds
        lines: list[str] = []
        while time.monotonic() <= end_time:
            raw = self._serial.readline()
            if raw:
                text = raw.decode("utf-8", errors="replace").strip()
                if text:
                    lines.append(text)
            else:
                time.sleep(0.02)
        return lines
