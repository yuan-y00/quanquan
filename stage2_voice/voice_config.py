"""
阶段二语音互动专属配置。

注意：本文件名为 voice_config.py，不是 config.py。
因为 stage1_pc_controller/ 下已有 config.py，且 stage1 内部使用
裸 import（import config）而非相对导入。如果 stage2 也有 config.py，
当 stage1 的模块被 stage2 加载时，Python 的 import 系统会混淆两个同名模块。
因此阶段二保持 voice_config.py 这个独立名字，彻底消除冲突风险。
"""

# ── Vosk 离线语音识别 ────────────────────────────────────
# 模型名称（vosk 会自动从 alphacephei.com 下载到本地缓存）
VOSK_MODEL_NAME = "vosk-model-small-en-us-0.15"

# 音频采样率（Hz），Vosk 要求单声道 16kHz
VOSK_SAMPLE_RATE = 16000

# ── 监听参数 ──────────────────────────────────────────────
# 每次监听的最大时长（秒），超时表示没人说话
LISTEN_TIMEOUT: float | None = 5.0

# 一句话的最长录音时间（秒），超过则取部分结果
PHRASE_TIME_LIMIT: float | None = 4.0

# 没听清时自动重听的次数
LISTEN_RETRIES = 2

# ── TTS 语音输出 ──────────────────────────────────────────
# Windows 使用 SAPI5 引擎（offline）；macOS/Linux 可改为 None 自动选择
TTS_ENGINE: str | None = None

# 语速（词/分钟），数值越小越慢越可爱
TTS_RATE = 180

# 音量：0.0 ~ 1.0
TTS_VOLUME = 0.9


# ── UI ─────────────────────────────────────────────────────
VOICE_STATUS_INTERVAL = 100
