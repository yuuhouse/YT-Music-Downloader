# YTDL Music Downloader

![Project Preview](assets/preview.svg)

YouTube 音訊下載工具（Python + `yt-dlp`）。

## 實際執行畫面

![Terminal Screenshot](assets/run-screenshot.svg)

## 功能
- 下載 YouTube 最佳音訊
- 模式 1：原始最佳音質（推薦）
- 模式 2：轉 MP3 320kbps
- 模式 3：優先 Opus + 顯示實際音訊資訊
- 同檔名自動改名（`(1)`, `(2)`...），不覆蓋舊檔

## 環境需求
- Python 3.9+
- `yt-dlp`
- `ffmpeg`（只有模式 2 轉 MP3 時需要）

## 安裝
```bash
pip install yt-dlp
```

## 使用
```bash
python yt_music_dl.py
```

## 輸出
- 預設資料夾：`downloads/`

## 注意
- YouTube 音訊來源有上限，轉高碼率不會創造新音質。
- 想保留最高可得品質，建議使用模式 1 或模式 3。
