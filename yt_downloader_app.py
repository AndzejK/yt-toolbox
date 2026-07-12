import streamlit as st
from services.yt_service import download_transcript, download_video

st.set_page_config(page_title="YouTube Downloader", page_icon="📺")

st.title("📺 YouTube Video Downloader")

url = st.text_input("Paste YouTube URL:")

col1, col2 = st.columns(2)
with col1:
    quality = st.selectbox("Quality", ["best", "worst"])
with col2:
    fmt = st.selectbox("Format", ["mp4", "mkv", "webm", "mp3"])

transcript_only = st.checkbox("Transcript only", value=False)
if transcript_only:
    st.caption("This will download the audio and generate a local transcript with speech-to-text.")

if st.button("Download"):
    if url:
        with st.spinner("Downloading..."):
            try:
                if transcript_only:
                    result = download_transcript(url)
                    st.success(f"Transcript created for: {result['title']}")
                    st.write(f"Saved transcript to: `{result['transcript_path']}`")
                    if result["transcript"]:
                        st.text_area("Transcript", result["transcript"], height=320)
                    else:
                        st.info("The transcript was empty.")
                else:
                    title = download_video(url, quality=quality, format=fmt)
                    st.success(f"Successfully downloaded: {title}")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please enter a URL.")
