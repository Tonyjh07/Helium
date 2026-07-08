# Helium

一个基于 FFmpeg `rubberband` 滤波器的高质量音频变速变调工具，提供简洁的 Web 界面。

## 功能

- **独立控制**：速度和音高可分别独立调整，互不影响
- **高质量处理**：基于 `librubberband` 相位声码器 + 瞬态保护算法
- **灵活操作**：滑块快速定位 + 文本自由输入 + 预设按钮一键切换
- **在线预览**：处理完成后直接在浏览器中试听并下载
- **覆盖上传**：支持拖入新文件替换当前音频，反复调整参数无需刷新

## 快速开始

### 1. 安装依赖

```bash
pip install flask
```

### 2. 放置 FFmpeg

项目目录下的 `ffmpeg/bin/` 需包含 `ffmpeg.exe` 和 `ffprobe.exe`（推荐 [gyan.dev 完整构建版](https://www.gyan.dev/ffmpeg/builds/)，已内置 `librubberband`）。

目录结构：

```
Helium/
├── ffmpeg/
│   └── bin/
│       ├── ffmpeg.exe
│       ├── ffprobe.exe
│       └── ...
├── app.py
└── ...
```

### 3. 启动

```bash
python app.py
```

访问 `http://127.0.0.1:5566`

## 技术原理

使用 FFmpeg 的 `rubberband` 音频滤镜：

```
rubberband=tempo=<速度倍率>:pitch=<音高倍率>:transients=crisp
```

- `tempo`：速度缩放因子（0.01 ~ 100）
- `pitch`：音高缩放因子（0.01 ~ 100）
- `transients=crisp`：保持打击类瞬态信号的清晰度

支持格式：MP3 / WAV / FLAC / OGG / M4A / AAC / OPUS / WMA

## 参数范围

| 参数 | 滑块范围 | 文本输入范围 |
|------|---------|------------|
| 速度 | 0.25x ~ 4.0x | 0.1x ~ 10.0x |
| 音高 | -24 ~ +24 半音 | 0.25x ~ 4.0x 倍率 |

## License

MIT
