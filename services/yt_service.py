import yt_dlp
import os

def download_video(url, output_path="downloads", quality="best", format="mp4"):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # If format is mp3, we need to extract audio
    if format == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{output_path}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'remote_components': ['ejs:github'],
        }
    else:
        format_string = 'bestvideo+bestaudio/best' if quality == 'best' else 'worst'
        ydl_opts = {
            'format': format_string,
            'outtmpl': f'{output_path}/%(title)s.%(ext)s',
            'merge_output_format': format,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'remote_components': ['ejs:github'],
        }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info.get('title', 'Unknown Title')
