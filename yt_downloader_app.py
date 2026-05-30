import streamlit as st
from services.yt_service import download_video

st.set_page_config(page_title="YouTube Downloader", page_icon="📺")

st.title("📺 YouTube Video Downloader")

url = st.text_input("Paste YouTube URL:")

col1, col2 = st.columns(2)
with col1:
    quality = st.selectbox("Quality", ["best", "worst"])
with col2:
    fmt = st.selectbox("Format", ["mp4", "mkv", "webm", "mp3"])

if st.button("Download"):
    if url:
        with st.spinner("Downloading..."):
            try:
                title = download_video(url, quality=quality, format=fmt)
                st.success(f"Successfully downloaded: {title}")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please enter a URL.")
