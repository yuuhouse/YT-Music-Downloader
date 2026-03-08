import os
import re

import yt_dlp


def sanitize_filename(name):
    """移除 Windows 不允許的檔名字元。"""
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", name).strip()
    return sanitized or "audio"


def get_unique_basename(output_path, base_name):
    """
    回傳不重複的檔名基底。
    例如 song, song (1), song (2) ...
    """
    candidate = base_name
    counter = 1
    while True:
        # 只要同名基底的任一副檔名已存在，就往下找下一個編號
        exists = any(
            os.path.isfile(os.path.join(output_path, f"{candidate}.{ext}"))
            for ext in ("webm", "m4a", "mp3", "opus", "ogg", "wav", "flac")
        )
        if not exists:
            return candidate
        candidate = f"{base_name} ({counter})"
        counter += 1


def download_youtube_music(
    url,
    output_path="downloads",
    keep_original=True,
    mp3_quality="320",
    prefer_opus=False,
    show_audio_info=False,
):
    """
    下載 YouTube 音訊

    Args:
        url: YouTube 影片 URL
        output_path: 輸出資料夾路徑
        keep_original: True 時保留來源最佳音訊(推薦)
        mp3_quality: 轉 mp3 時的碼率 (例如 320 / 256 / 192)
        prefer_opus: True 時優先抓 Opus 音軌
        show_audio_info: 下載後顯示實際音訊格式資訊
    """
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    try:
        metadata_opts = {
            "format": "bestaudio[acodec=opus]/bestaudio/best" if prefer_opus else "bestaudio/best",
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(metadata_opts) as meta_ydl:
            info = meta_ydl.extract_info(url, download=False)
            base_title = sanitize_filename(info.get("title", "audio"))
            unique_title = get_unique_basename(output_path, base_title)

        ydl_opts = {
            "format": "bestaudio[acodec=opus]/bestaudio/best" if prefer_opus else "bestaudio/best",
            "outtmpl": os.path.join(output_path, f"{unique_title}.%(ext)s"),
        }

        if not keep_original:
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": mp3_quality,
                }
            ]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"正在下載: {url}")
            info = ydl.extract_info(url, download=True)
            if show_audio_info:
                requested = info.get("requested_downloads") or []
                audio_info = requested[0] if requested else info
                codec = audio_info.get("acodec") or info.get("acodec") or "unknown"
                abr = audio_info.get("abr") or info.get("abr")
                ext = audio_info.get("ext") or info.get("ext") or "unknown"
                print(f"音訊資訊: codec={codec}, ext={ext}, abr={abr if abr else 'N/A'} kbps")
            print(f"下載完成！檔名: {unique_title}")
    except Exception as e:
        print(f"錯誤: {e}")


if __name__ == "__main__":
    url = input("請輸入 YouTube URL: ").strip()
    mode = input(
        "模式 1=原始最佳音質(推薦), 2=轉 MP3 320kbps, 3=優先 Opus + 顯示實際音訊資訊: "
    ).strip()

    if mode == "2":
        download_youtube_music(url, keep_original=False, mp3_quality="320")
    elif mode == "3":
        download_youtube_music(url, keep_original=True, prefer_opus=True, show_audio_info=True)
    else:
        download_youtube_music(url, keep_original=True)
