# quanquan 阶段二：语音互动

通过电脑麦克风说英文口令 → 电脑扬声器用英文回应 → 机械臂做动作。

**完全离线**：语音识别用 Vosk 本地引擎，TTS 用 Windows SAPI5，零网络依赖。

---

## 1. 文件结构

```
stage2_voice/
├── app.py                  ← 第二阶段 UI 入口（继承阶段一）
├── voice_controller.py     ← 语音主控：监听→匹配→说话→发 G-code
├── voice.py                ← 麦克风录音 + Vosk 离线语音识别
├── speech_out.py           ← TTS 文字转语音（pyttsx3，离线）
├── intent.py               ← 英文短句 → 动作名匹配
├── voice_config.py         ← 阶段二专属配置
├── setup_models.py         ← 首次运行：下载 Vosk 英文模型（~40MB）
├── requirements.txt        ← Python 依赖
└── README.md               ← 本文件
```

**从 `stage1_pc_controller/` 复用的文件**（不拷贝，通过命名空间 import 引用）：

| 复用文件 | 引用方式 |
|----------|----------|
| `serial_link.py` | `from stage1_pc_controller.serial_link import SerialLink` |
| `motion_scripts.py` | `from stage1_pc_controller.motion_scripts import SCRIPTS` |
| `gcode.py` | motion_scripts 内部引用 |
| `config.py` | motion_scripts 内部引用 |
| `poses.json` | motion_scripts 内部引用 |
| `app.py` | `VoiceApp` 继承 `StageOneApp` |

---

## 2. 前置要求

- **Python 3.10 或以上**
- Windows 10/11（用系统自带 SAPI5 TTS 和麦克风）

---

## 3. 新机器安装步骤

```bash
# 1. 进入文件夹
cd stage2_voice

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 下载 Vosk 英文语音模型（~40MB，仅需一次）
python setup_models.py download

# 4. 运行
python app.py
```

步骤 3 需要网络下载模型。下载完成后，之后每次使用**完全不需要网络**。

> 如果你已经在开发机上 `pip install vosk` 过且用 `vosk.Model(model_name=..., lang=...)` 下载过模型，模型已在 `%USERPROFILE%\.cache\vosk\` 中缓存。
> 新机器上只需运行 `setup_models.py download` 一次即可。

---

## 4. 可识别的口令

对着电脑麦克风说（英语）：

| # | 你说 | quanquan 回答 | 机械臂动作 |
|---|------|---------------|-----------|
| 1 | `Quanquan, wake up` | `I am here.` | wake |
| 2 | `Shake hand` | `Okay, hand please.` | handshake |
| 3 | `Again` | `Again!` | handshake |
| 4 | `Good boy` | `Hehe.` | happy |
| 5 | `Be shy` | `Oh no.` | shy |
| 6 | `Go to sleep` | `Good night.` | sleep |

问候用语（只说话，不动）：

| 你说 | quanquan 回答 |
|------|---------------|
| `Hello` / `Hi` / `Hey` / `Quanquan` | `Hi! I am quanquan.` |

---

## 5. 听不懂时怎么办

Vosk 听到声音但没匹配到口令时，quanquan 会：

- 随机说 `"Hmm?"` / `"What?"` / `"Pardon?"` 之一
- 随机做 `wake` / `happy` / `shy` 之一
- 连续 3 次听不懂后，只说 `"I'm not sure what you mean."` 不再乱动（避免疯了一样）

闲置时（没人说话）静默继续监听，不打扰。

---

## 6. 使用步骤

1. **打开 app**：`python app.py`
2. **选择连接模式**：
   - 取消 "Offline mock mode" + 选 COM 口 + Connect → 真实连接机器人
   - 保持 mock mode 勾选 → 语音正常跑，G-code 不真实发送
3. **点 "Start Voice"**：开始监听麦克风
4. **对着电脑麦克风说英文口令**
5. 日志区会显示 `[HEARD]`、`[VOICE]` 等信息
6. **点 "Stop Voice"**：停止监听

---

## 7. 配置调整

编辑 [voice_config.py](voice_config.py)：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `VOSK_MODEL_NAME` | `vosk-model-small-en-us-0.15` | 模型名（小模型~40MB） |
| `LISTEN_TIMEOUT` | `5.0` 秒 | 无声音超时 |
| `PHRASE_TIME_LIMIT` | `4.0` 秒 | 单句话最长录音时长 |
| `LISTEN_RETRIES` | `2` | 没听清自动重试次数 |
| `TTS_RATE` | `180` | 语速（词/分钟），越小越慢越可爱 |
| `TTS_VOLUME` | `0.9` | 音量 0.0~1.0 |
| `FALLBACK_ACTIONS` | `["wake", "happy", "shy"]` | 听不懂时随机执行的动作 |
| `FALLBACK_REPLIES` | `["Hmm?", "What?", ...]` | 听不懂时随机说的话 |
| `MAX_CONSECUTIVE_FALLBACKS` | `3` | 连续兜底上限 |

---

## 8. 与阶段一的关系

- 阶段二是**叠加扩展**，不是重写
- 阶段一所有功能（手动控制、按钮动作、日志）在阶段二中**完全可用**
- 语音和按钮触发的是**同一套 G-code 序列**
- 语音监听在**后台线程**，不阻塞 UI
- 串口忙时（`[BUSY]`），语音命令被跳过

---

## 9. 常见问题

**Q: "Model missing"？**
A: 运行 `python setup_models.py download` 下载 Vosk 模型。

**Q: "No microphone detected"？**
A: 检查麦克风是否插好，Windows 隐私设置是否允许桌面应用访问麦克风。

**Q: Vosk 识别不准？**
A: Vosk 英文小模型对固定短句准确率较高。如果偏差大，可以换更大的模型：
编辑 `voice_config.py`，把 `VOSK_MODEL_NAME` 改为 `vosk-model-en-us-0.22`（~1.4GB），
重新运行 `python setup_models.py download`。

**Q: TTS 声音太机械？**
A: `pyttsx3` 使用 Windows 系统语音。在 Windows 设置 → 时间和语言 → 语音 里更换语音。
