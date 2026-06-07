"""
一键下载 Vosk 英文语音识别模型。
运行一次即可，之后完全离线使用。

用法：
    python setup_models.py download       # 下载英文小模型（~40MB）
    python setup_models.py check          # 检查模型是否已就绪
"""

from __future__ import annotations

import sys


MODEL_NAME = "vosk-model-small-en-us-0.15"


def download() -> None:
    """下载模型到本地缓存（~/.cache/vosk/ 或 %LOCALAPPDATA%/vosk/）。"""
    print(f"Downloading Vosk model: {MODEL_NAME}")
    print("This is ~40MB and only needed once. Please wait...")
    print()

    try:
        import vosk
    except ImportError:
        print("ERROR: vosk is not installed. Run: pip install vosk")
        sys.exit(1)

    try:
        model = vosk.Model(model_name=MODEL_NAME, lang="en-us")
        print(f"✓ Model ready!")
        print(f"  Path: {model.path}")
    except Exception as exc:
        print(f"ERROR: Failed to download model: {exc}")
        print("Check your network connection and try again.")
        sys.exit(1)


def check() -> None:
    """检查模型是否已在本地缓存中。"""
    print(f"Checking for Vosk model: {MODEL_NAME}")
    try:
        import vosk
    except ImportError:
        print("✗ vosk is not installed. Run: pip install vosk")
        sys.exit(1)

    try:
        model = vosk.Model(model_name=MODEL_NAME, lang="en-us")
        print(f"✓ Model found at: {model.path}")
    except Exception as exc:
        print(f"✗ Model not found: {exc}")
        print("Run: python setup_models.py download")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()
    if command == "download":
        download()
    elif command == "check":
        check()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)
