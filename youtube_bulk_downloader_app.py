import streamlit as st
from pathlib import Path
import subprocess
import yt_dlp
import pyttsx3
import random
import os

# Configure page
st.set_page_config(page_title="🏴‍☠️ YouTube Bulk Downloader", layout="centered")



def log_func(message):
    logs.append(message)
    log_placeholder.text("\n".join(logs[-20:]))

# Convert to mp4
def convert_to_mp4(input_path: Path, log_func):
    output_path = input_path.with_suffix(".converted.mp4")
    log_func(f"🔄 Converting {input_path.name} to MP4...")
    try:
        subprocess.run([
            'ffmpeg', '-i', str(input_path), '-c:v', 'libx264', '-c:a', 'aac',
            '-y', str(output_path)
        ], check=True)
        output_path.replace(input_path)
        log_func(f"✅ Converted: {input_path.name}")
    except Exception as e:
        log_func(f"❌ Conversion failed: {e}")

# Convert to mp3
def convert_to_mp3(input_path: Path, log_func):
    output_path = input_path.with_suffix(".mp3")
    log_func(f"🎧 Extracting MP3 from {input_path.name}...")
    try:
        subprocess.run([
            'ffmpeg', '-i', str(input_path), '-q:a', '0', '-map', 'a', '-y', str(output_path)
        ], check=True)
        log_func(f"✅ MP3 created: {output_path.name}")
    except Exception as e:
        log_func(f"❌ MP3 conversion failed: {e}")

# Download and convert with progress update
def download_and_process(urls, output_dir: Path, log_func, progress_updater):
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

# Dynamic URL input boxes
new_url_list = []
for i, url in enumerate(st.session_state.url_list):
    new_url = st.text_input(f"YouTube URL #{i+1}", value=url, key=f"url_{i}")
    new_url_list.append(new_url)

if new_url_list[-1].strip():
    new_url_list.append("")

st.session_state.url_list = new_url_list

# Folder input
folder_path = st.text_input(
    "📂 Folder to save downloads:",
    value=str(st.session_state.get("folder", Path.home() / "Downloads/yt_pirate_treasure"))
)
st.session_state.folder = folder_path

# Start Download button
if st.button("🚀 Start Download"):
    st.session_state.download_triggered = True

# ==== PROCESSING & LOGS AT THE BOTTOM ====
progress_bar = st.progress(0)  # progress bar at the top of logs
# Logger setup — define BEFORE log_func
logs = []
log_placeholder = st.empty()


if st.session_state.download_triggered:
    st.session_state.download_triggered = False  # Reset trigger

    valid_urls = [u.strip() for u in st.session_state.url_list if u.strip()]
    if not valid_urls:
        st.error("⚠️ Please enter at least one valid YouTube URL.")
        progress_bar.progress(0)  # reset progress
    else:
        output_dir = Path(folder_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        def update_progress(percent):
            progress_bar.progress(percent)

        download_and_process(valid_urls, output_dir, log_func, update_progress)
        pirate_msg = save_pirate_message(output_dir, log_func)
        text_to_speech(pirate_msg, log_func)
        progress_bar.progress(100)
        st.balloons()
        st.success("🏁 All downloads complete!")

# Show logs at the very bottom
log_placeholder.text("\n".join(logs[-20:]))
