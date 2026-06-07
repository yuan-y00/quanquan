from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import config
import gcode


class PoseError(ValueError):
    pass


def load_poses(path: str | Path | None = None) -> dict[str, dict[str, float]]:
    pose_path = Path(path or config.POSE_FILE)
    if not pose_path.is_absolute():
        pose_path = Path(__file__).with_name(str(pose_path))
    with pose_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return {name: _normalize_pose(name, pose) for name, pose in data.items()}


def _normalize_pose(name: str, pose: dict[str, Any]) -> dict[str, float]:
    required = ("x", "y", "z")
    missing = [key for key in required if key not in pose]
    if missing:
        raise PoseError(f"Pose '{name}' is missing: {', '.join(missing)}")
    return {
        "x": float(pose["x"]),
        "y": float(pose["y"]),
        "z": float(pose["z"]),
        "f": float(pose.get("f", config.DEFAULT_FEED_RATE)),
    }


def _validate_pose(name: str, pose: dict[str, float]) -> None:
    for axis, key in (("X", "x"), ("Y", "y"), ("Z", "z")):
        low, high = config.AXIS_LIMITS[axis]
        value = pose[key]
        if value < low or value > high:
            raise PoseError(f"Pose '{name}' {axis}={value} is outside {low}..{high}.")

    feed_low, feed_high = config.FEED_RATE_LIMITS
    if pose["f"] < feed_low or pose["f"] > feed_high:
        raise PoseError(f"Pose '{name}' F={pose['f']} is outside {feed_low}..{feed_high}.")


def _go(name: str, poses: dict[str, dict[str, float]]) -> str:
    if name not in poses:
        raise PoseError(f"Pose '{name}' does not exist in poses.json.")
    pose = poses[name]
    _validate_pose(name, pose)
    return gcode.move(pose["x"], pose["y"], pose["z"], pose["f"])


def _sequence(*items: str | float, poses: dict[str, dict[str, float]]) -> list[str]:
    commands = [gcode.absolute()]
    for item in items:
        if isinstance(item, (int, float)):
            commands.append(gcode.dwell(item))
        else:
            commands.append(_go(item, poses))
    return commands


def wake(poses: dict[str, dict[str, float]] | None = None) -> list[str]:
    poses = poses or load_poses()
    return _sequence("wake", 0.2, "idle", poses=poses)


def handshake(poses: dict[str, dict[str, float]] | None = None) -> list[str]:
    poses = poses or load_poses()
    return _sequence(
        "idle",
        0.2,
        "hand_ready",
        0.25,
        "shake_up",
        0.18,
        "shake_down",
        0.18,
        "shake_up",
        0.18,
        "shake_down",
        0.18,
        "hand_ready",
        0.2,
        "idle",
        poses=poses,
    )


def happy(poses: dict[str, dict[str, float]] | None = None) -> list[str]:
    poses = poses or load_poses()
    return _sequence(
        "idle",
        0.15,
        "happy_left",
        0.18,
        "happy_right",
        0.18,
        "happy_left",
        0.18,
        "happy_right",
        0.18,
        "idle",
        poses=poses,
    )


def shy(poses: dict[str, dict[str, float]] | None = None) -> list[str]:
    poses = poses or load_poses()
    return _sequence("idle", 0.15, "shy_back", 0.45, "idle", poses=poses)


def sleep(poses: dict[str, dict[str, float]] | None = None) -> list[str]:
    poses = poses or load_poses()
    return _sequence("sleep", poses=poses)


SCRIPTS = {
    "Wake": wake,
    "Handshake": handshake,
    "Happy": happy,
    "Shy": shy,
    "Sleep": sleep,
}
