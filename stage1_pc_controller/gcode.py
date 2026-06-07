from __future__ import annotations


class GCodeError(ValueError):
    pass


def _num(value: float | int) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.3f}".rstrip("0").rstrip(".")


def home() -> str:
    return "G28"


def absolute() -> str:
    return "G90"


def move(
    x: float | int | None = None,
    y: float | int | None = None,
    z: float | int | None = None,
    f: float | int | None = None,
) -> str:
    parts = ["G1"]
    if x is not None:
        parts.append(f"X{_num(x)}")
    if y is not None:
        parts.append(f"Y{_num(y)}")
    if z is not None:
        parts.append(f"Z{_num(z)}")
    if f is not None:
        parts.append(f"F{_num(f)}")

    if len(parts) == 1:
        raise GCodeError("Move command needs at least one axis or feed rate.")
    return " ".join(parts)


def dwell(seconds: float | int) -> str:
    if float(seconds) < 0:
        raise GCodeError("Dwell time cannot be negative.")
    return f"G4 S{_num(seconds)}"


def status() -> str:
    return "M114"


def endstop_status() -> str:
    return "M119"


def motors_off() -> str:
    return "M18"
