# quanquan — 互动机械臂原型

RRR 型三关节机械臂，Arduino Mega 2560 + RAMPS 1.5 下位机，Windows 上位机通过串口 G-code 控制。目标是让 quanquan 听懂语音、识别手势，做可爱的互动动作。

---

## 项目结构

```
quanquan/
├── quanquan_plan.html              ← 完整项目计划与硬件信息
├── stage1_pc_controller/           ← 阶段一：电脑端 G-code 控制
│   ├── app.py                      #   Tkinter 主界面
│   ├── serial_link.py              #   串口连接层（支持 mock 离线模式）
│   ├── gcode.py                    #   G-code 生成（G1/G28/G90/M114/M18 等）
│   ├── motion_scripts.py           #   动作脚本（握手/开心/害羞/睡觉/醒来）
│   ├── poses.json                  #   动作坐标点（实机回来校准）
│   ├── config.py                   #   串口号/波特率/轴限制配置
│   └── requirements.txt
│
└── stage2_voice/                   ← 阶段二：语音互动
    ├── app.py                      #   继承阶段一 UI，增加语音面板
    ├── voice.py                    #   麦克风录音 + Vosk 离线语音识别
    ├── voice_controller.py         #   主控：监听→匹配→说话→发送 G-code
    ├── speech_out.py               #   TTS 文字转语音（pyttsx3，离线）
    ├── intent.py                   #   英文短句关键词匹配
    ├── voice_config.py             #   语音参数配置
    ├── setup_models.py             #   一键下载 Vosk 识别模型
    ├── requirements.txt
    └── README.md
```

---

## 硬件

| 组件 | 型号 |
|------|------|
| 机械结构 | RRR 型三关节机械臂 |
| 主控 | Arduino Mega 2560 |
| 扩展板 | RAMPS 1.5 |
| 驱动 | TMC2209 ×3 |
| 电机 | 步进电机 ×3（接 X/Y/Z 轴） |
| 通信 | USB 串口，115200 baud，`\r` 行尾 |
| 固件 | 已有（正/逆运动学、回零、限位由固件处理，不改） |

---

## 各阶段功能

| 阶段 | 输入 | 输出 | 状态 |
|------|------|------|------|
| 一 | 按钮点击 | G-code 发送至 Arduino | ✅ |
| 二 | 麦克风英文口令 | 扬声器英文回应 + 机械臂动作 | ✅ 已实现 |
| 三 | USB 摄像头手势识别 | 视觉触发动作 | 🔜 计划中 |

---

## 快速开始

### 阶段一（基础控制）

```bash
cd stage1_pc_controller
pip install -r requirements.txt
python app.py
```

保持 mock 模式勾选即可离线测试。实机连接时取消勾选、选 COM 口、点 Connect。

### 阶段二（语音互动）

```bash
cd stage2_voice
pip install -r requirements.txt
python setup_models.py download    # 首次需要网络，下载 ~40MB Vosk 模型
python app.py
```

点 **Start Voice** 后对着电脑麦克风说英文。可用口令：

| 你说 | quanquan 回应 | 动作 |
|------|---------------|------|
| `Shake hand` | Okay, hand please. | 握手 |
| `Good boy` | Hehe. | 开心摇摆 |
| `Be shy` | Oh no. | 害羞后退 |
| `Go to sleep` | Good night. | 趴下睡觉 |
| `Wake up` | I am here. | 醒来 |
| `Again` | Again! | 再握一次 |

听不懂时 quanquan 会自动做 happy 动作 + 说 Hehe.，不傻站。

---

## 环境要求

- **Python 3.10+**
- Windows 10 / 11
- 阶段一可选 `pyserial`
- 阶段二需要 `vosk`、`pyttsx3`、`pyaudio`（全部 pip 安装）
- 语音识别和 TTS 均离线运行，不需要网络

---

## 实机接上后的步骤

1. 打开 Arduino 或设备管理器，确认 COM 口编号
2. 取消 Mock mode 勾选，填正确 COM 口
3. 波特率 115200，行尾 CR
4. 点 Connect → 先点 Status 确认通信
5. 用 Move XYZ 小范围测试安全坐标
6. 校准 `poses.json` 里的 9 个动作坐标点
