import yt_dlp
import os

def download_youtube_music(url, output_path="downloads"):
    """
    下載 YouTube 音樂
    
    Args:
        url: YouTube 視頻 URL
        output_path: 輸出資料夾路徑
    """
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"正在下載: {url}")
            ydl.download([url])
            print("下載完成！")
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    url = input("請輸入 YouTube URL: ")
    download_youtube_music(url)