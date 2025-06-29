import streamlit as st
from pathlib import Path
import subprocess
import yt_dlp
import pyttsx3
import random
import os
import io
import zipfile
from datetime import datetime

# Configure page
st.set_page_config(page_title="🏴‍☠️ YouTube Bulk Downloader", layout="centered")

# Make all Streamlit buttons wide enough to keep text on one line
st.markdown(
    """
    <style>
    /* Try to target all buttons, including inside columns */
    button[kind="primary"], button[kind="secondary"], div.stButton > button {
        min-width: 6vw !important;
        max-width: 100vw !important;
        white-space: nowrap !important;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Convert to mp4 using ffmpeg

def convert_to_mp4(input_path: Path, log_func):
    output_path = input_path.with_suffix(".converted.mp4")
    log_func(f"🔄 Converting {input_path.name} to MP4 with ffmpeg...")
    try:
        subprocess.run([
            'ffmpeg', '-i', str(input_path), '-c:v', 'libx264', '-c:a', 'aac',
            '-y', str(output_path)
        ], check=True)
        output_path.replace(input_path)
        log_func(f"✅ Converted: {input_path.name}")
    except Exception as e:
        log_func(f"❌ Conversion failed: {e}")

# Convert to mp3 using ffmpeg

def convert_to_mp3(input_path: Path, log_func):
    output_path = input_path.with_suffix(".mp3")
    log_func(f"🎧 Extracting MP3 from {input_path.name} with ffmpeg...")
    try:
        subprocess.run([
            'ffmpeg', '-i', str(input_path), '-q:a', '0', '-map', 'a', '-y', str(output_path)
        ], check=True)
        log_func(f"✅ MP3 created: {output_path.name}")
    except Exception as e:
        log_func(f"❌ MP3 conversion failed: {e}")

# Download and convert with progress update
def download_and_process(urls, output_dir: Path, log_func, progress_updater, download_mp3=True):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best',
        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
    }
    log_func(f"📁 Downloading to: {output_dir}\n")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for i, url in enumerate(urls, start=1):
                log_func(f"⬇️ Downloading: {url}")
                ydl.download([url])
                progress_updater(int((i - 0.5) / len(urls) * 100))
    except Exception as e:
        log_func(f"❌ Download failed: {e}")
        return

    VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.webm', '.avi', '.mov']

    video_files = [f for f in output_dir.glob('*.*') if f.suffix.lower() in VIDEO_EXTENSIONS]
    total_files = len(video_files)
    for i, file in enumerate(video_files, start=1):
        convert_to_mp4(file, log_func)
        if download_mp3:
            convert_to_mp3(file, log_func)
        progress_updater(int((0.5 + i / total_files * 0.5) * 100))

# Pirate message
def save_pirate_message(folder: Path, log_func):
    messages = [
        "☠️ Ahoy matey! Ye be done plunderin'.",
        "🏴‍☠️ Yo-ho-ho and a bottle o' success!",
        "🦜 Arr! Loot's all gathered, Cap'n!",
        "💰 Shiver me timbers! The downloads be finished!",
        "⚓ Ye've conquered the YouTube seas!"
    ]
    message = random.choice(messages)
    with open(folder / "pirate_message.txt", "w") as f:
        f.write(message)
    log_func(f"📜 Pirate message: {message}")
    return message

# Speak it!
def text_to_speech(text, log_func):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        log_func("🗣️ Spoken message complete.")
    except Exception as e:
        log_func(f"❌ TTS failed: {e}")

# SESSION INIT
if "url_list" not in st.session_state:
    st.session_state.url_list = [""]
if "download_triggered" not in st.session_state:
    st.session_state.download_triggered = False

# ==== UI TOP SECTION ====

st.title("🏴‍☠️ YouTube Bulk Downloader")

# Multi-URL text area
if "multi_url_text" not in st.session_state:
    st.session_state.multi_url_text = ""



multi_url_text = st.text_area(
    "Enter YouTube URLs (one per line or separated by commas):",
    value=st.session_state.multi_url_text,
    key="multi_url_text_area",
    height=150
)
st.session_state.multi_url_text = multi_url_text

# Start Download and Cancel buttons
_, col2, col3, _ = st.columns([4, 2, 2, 4])
with col2:
    if st.button("⬇️ Download", help="Start downloading and converting all listed YouTube URLs"):
        st.session_state.download_triggered = True
with col3:
    if st.button("❌ Cancel", help="Cancel the current download/conversion process"):
        st.session_state.cancel_download = True
        
    # Add toggle for MP3 extraction (default ON)
_, col4, _ = st.columns([3.5,2,3])
with col4:
    download_mp3 = st.checkbox("MP3 audio", value=True)
    
# ==== PROCESSING & LOGS AT THE BOTTOM ====

progress_bar = st.progress(0)  # progress bar at the top of logs

# Logger setup — define BEFORE log_func
logs = []
log_box_placeholder = st.empty()

def log_func(message):
    logs.append(message)
    log_box_placeholder.markdown(
        f"""
        <div id='log-box' style='height: 200px; overflow-y: auto; background: #18191A; color: #fafafa; padding: 10px; border-radius: 6px; font-size: 14px; margin-top: 1em;'>
        {'<br>'.join(logs[-100:])}
        </div>
        <script>
        var logBox = document.getElementById('log-box');
        if (logBox) {{ logBox.scrollTop = logBox.scrollHeight; }}
        </script>
        """,
        unsafe_allow_html=True
    )

def zip_converted_files(folder: Path, include_mp3=True) -> bytes:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in folder.glob("*.*"):
            if file.suffix.lower() == ".mp4" or (include_mp3 and file.suffix.lower() == ".mp3"):
                zipf.write(file, arcname=file.name)
    zip_buffer.seek(0)
    return zip_buffer.read()

if "cancel_download" not in st.session_state:
    st.session_state.cancel_download = False

if st.session_state.download_triggered:
    st.session_state.download_triggered = False  # Reset trigger
    st.session_state.cancel_download = False  # Reset cancel

    # Split URLs by newlines or commas, strip whitespace, and filter out empty
    raw_urls = st.session_state.multi_url_text.split('\n')
    valid_urls = [u.strip() for u in raw_urls if u.strip()]
    
    if not valid_urls:
        st.error("⚠️ Please enter at least one valid YouTube URL.")
        progress_bar.progress(0)  # reset progress
    else:
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdirname:
            output_dir = Path(tmpdirname)
            output_dir.mkdir(parents=True, exist_ok=True)

            def update_progress(percent):
                progress_bar.progress(percent)
                if st.session_state.cancel_download:
                    raise Exception("Download cancelled by user.")

            try:
                download_and_process(valid_urls, output_dir, log_func, update_progress, download_mp3)
                if st.session_state.cancel_download:
                    st.warning("⛔ Download cancelled.")
                else:
                    pirate_msg = save_pirate_message(output_dir, log_func)
                    text_to_speech(pirate_msg, log_func)
                    progress_bar.progress(100)
                    st.balloons()
                    st.success("🏁 All downloads complete!")

                    # Zip all converted files
                    zip_bytes = zip_converted_files(output_dir, download_mp3)
                    dt_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    zip_name = f"YT_Booty_{dt_str}.zip"
                    st.write("## Download your booty:")
                    st.download_button(
                        label=f"💾 Download {zip_name}",
                        data=zip_bytes,
                        file_name=zip_name,
                        mime="application/zip"
                    )
            except Exception as e:
                if str(e) == "Download cancelled by user.":
                    st.warning("⛔ Download cancelled by user.")
                else:
                    st.error(f"❌ Error: {e}")

    # Clear the text area after download or cancel
    st.session_state.multi_url_text = ""

