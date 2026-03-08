import os
import re
import shutil
from urllib.parse import parse_qs, urlparse

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


def validate_youtube_url(url):
    """檢查 URL 是否包含可用的 YouTube 影片 ID。"""
    if not url or not url.strip():
        return False, "錯誤: 請輸入 YouTube URL"

    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")

    is_short_host = host == "youtu.be" or host.endswith(".youtu.be")
    is_youtube_host = host == "youtube.com" or host.endswith(".youtube.com")

    if is_short_host:
        if not path:
            return False, "錯誤: YouTube 短網址缺少影片 ID"
        return True, ""

    if is_youtube_host:
        query = parse_qs(parsed.query)
        vid = query.get("v", [""])[0].strip()
        if parsed.path == "/watch" and not vid:
            return False, "錯誤: 你輸入的是空的 watch URL，缺少影片 ID"
        return True, ""

    # 非 YouTube 網址交給 yt-dlp 嘗試，避免過度擋掉可用來源。
    return True, ""


def download_youtube_music(
    url,
    output_path="downloads",
    keep_original=True,
    mp3_quality="320",
    prefer_opus=False,
    show_audio_info=False,
    status_callback=None,
    output_codec=None,
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
        status_callback: 可選，接收狀態訊息的函式
        output_codec: 轉檔格式，可為 "mp3" 或 "flac"，None 則保留原始音訊
    """
    is_valid, error_message = validate_youtube_url(url)
    if not is_valid:
        message = error_message
        print(message)
        if status_callback:
            status_callback(message)
        return {"success": False, "error": "invalid_url"}

    def emit(message):
        print(message)
        if status_callback:
            status_callback(message)

    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)

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

        codec = output_codec
        if codec is None and not keep_original:
            codec = "mp3"
        if codec in ("mp3", "flac"):
            if shutil.which("ffmpeg") is None:
                emit("錯誤: 找不到 ffmpeg，無法轉檔。請先安裝 ffmpeg 後再試。")
                return {"success": False, "error": "missing_ffmpeg"}

            postprocessor = {
                "key": "FFmpegExtractAudio",
                "preferredcodec": codec,
            }
            if codec == "mp3":
                postprocessor["preferredquality"] = mp3_quality
            ydl_opts["postprocessors"] = [postprocessor]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            emit(f"正在下載: {url}")
            info = ydl.extract_info(url, download=True)

            result = {"success": True, "filename_base": unique_title}
            if show_audio_info:
                requested = info.get("requested_downloads") or []
                audio_info = requested[0] if requested else info
                codec = audio_info.get("acodec") or info.get("acodec") or "unknown"
                abr = audio_info.get("abr") or info.get("abr")
                ext = audio_info.get("ext") or info.get("ext") or "unknown"
                result["audio_info"] = {"codec": codec, "ext": ext, "abr": abr}
                emit(f"音訊資訊: codec={codec}, ext={ext}, abr={abr if abr else 'N/A'} kbps")

            emit(f"下載完成！檔名: {unique_title}")
            return result
    except Exception as e:
        emit(f"錯誤: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    url = input("請輸入 YouTube URL: ").strip()
    is_valid, error_message = validate_youtube_url(url)
    if not is_valid:
        print(error_message)
        raise SystemExit(1)

    mode = input(
        "模式 1=原始最佳音質, 2=轉 MP3 320kbps(預設), 3=優先 Opus + 顯示實際音訊資訊, 4=轉 FLAC [Enter=2]: "
    ).strip()
    if mode == "":
        mode = "2"
    if mode not in {"1", "2", "3", "4"}:
        print("警告: 無效模式，已改用預設模式 2 (MP3 320kbps)。")
        mode = "2"

    if mode == "2":
        download_youtube_music(url, keep_original=False, mp3_quality="320", output_codec="mp3")
    elif mode == "3":
        download_youtube_music(url, keep_original=True, prefer_opus=True, show_audio_info=True)
    elif mode == "4":
        download_youtube_music(url, keep_original=False, output_codec="flac", show_audio_info=True)
    else:
        download_youtube_music(url, keep_original=True)
