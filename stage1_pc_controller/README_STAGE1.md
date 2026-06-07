# quanquan 第一阶段电脑控制代码

这个文件夹是一版“先离线跑通”的 Windows 电脑端控制软件。你现在没有机器人，也可以打开界面、点击按钮、查看将来会发送的 G-code。

## 里面有什么

- `app.py`：主界面，负责按钮、输入框、日志。
- `serial_link.py`：串口连接层，支持真实串口，也支持离线模拟。
- `gcode.py`：统一生成 G-code。
- `motion_scripts.py`：把握手、开心、害羞、睡觉、醒来这些动作变成 G-code 序列。
- `poses.json`：动作点位。现在里面是占位坐标，实机回来后要重新校准。
- `config.py`：默认 COM 口、波特率、命令结尾、安全范围。

## 现在怎么运行

在 PowerShell 里进入这个文件夹：

```powershell
cd stage1_pc_controller
pip install -r requirements.txt
python app.py
```

打开后保持 `Offline mock mode` 勾选，然后点：

```text
Connect
Home
Move XYZ
Handshake
Happy
Shy
Sleep
Wake
Status
Motors Off
```

你会在右侧日志里看到类似：

```text
[MOCK SEND] G90
[MOCK SEND] G1 X100 Y80 Z40 F500
ok
```

这说明电脑端流程已经能跑。现在不会真的控制机器人。

## 机器人回来后怎么接实机

先不要直接点动作按钮。按这个顺序来：

1. 打开 Arduino 或设备管理器，找到 Arduino Mega 2560 的 COM 口，比如 `COM3`。
2. 打开 `app.py`。
3. 取消勾选 `Offline mock mode`。
4. 填正确 COM 口，波特率先用 `115200`。
5. 命令结尾先用 `CR`，也就是 `\r`。
6. 点 `Connect`。
7. 先点 `Status`，看日志有没有返回。
8. 再点 `Home`，确认回零正常。
9. 用 `Move XYZ` 小范围慢慢测试，不要一上来点动作。

如果提示没有 `pyserial`，先安装：

```powershell
pip install pyserial
```

## 最重要的安全提醒

`poses.json` 里的坐标现在只是占位，不代表安全。

实机回来以后，你要先用 `Move XYZ` 慢慢找这些点：

```text
idle
wake
hand_ready
shake_up
shake_down
happy_left
happy_right
shy_back
sleep
```

找到一个安全点，就改 `poses.json` 里对应的 `x`、`y`、`z`、`f`。

## 第一阶段完成标准

可以认为第一阶段完成，需要满足这些：

- 软件能连接 Arduino。
- `Home` 能回零。
- `Status` 能返回当前位置。
- `Move XYZ` 能小范围移动。
- `Handshake`、`Happy`、`Shy`、`Sleep`、`Wake` 能按按钮触发。
- 日志里能看见发送的命令和固件返回。
- `Motors Off` 能关闭电机。

## 现在最适合做什么

现在机器人不在身边，你可以先做三件事：

1. 打开离线模式，把所有按钮都点一遍。
2. 看日志里的 G-code 顺序是不是符合你想要的动作节奏。
3. 等机器人回来，只校准 `poses.json`，不要大改程序结构。
