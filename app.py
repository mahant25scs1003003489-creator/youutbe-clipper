from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def time_to_seconds(t):
    parts = t.strip().split(":")

    if len(parts) == 1:
        return int(parts[0])

    if len(parts) == 2:
        minutes, seconds = map(int, parts)
        return minutes * 60 + seconds

    if len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds

    raise ValueError("Invalid timestamp")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():

    url = request.form.get("url", "").strip()
    start = request.form.get("start", "").strip()
    end = request.form.get("end", "").strip()
    quality = request.form.get("quality", "1080")

    try:
        start_seconds = time_to_seconds(start)
        end_seconds = time_to_seconds(end)

        if end_seconds <= start_seconds:
            return "End time must be greater than start time."

        if not url:
            return "Please enter a YouTube URL."

        if quality == "720":
            height = 720
        else:
            height = 1080

        file_id = str(uuid.uuid4())

        output_template = os.path.join(
            DOWNLOAD_DIR,
            file_id + ".%(ext)s"
        )

        def download_range(info_dict, ydl):
            return [{
                "start_time": start_seconds,
                "end_time": end_seconds
            }]

        ydl_opts = {
            "format": (
                f"bestvideo[height<={height}]+bestaudio/"
                f"best[height<={height}]"
            ),

            "outtmpl": output_template,

            "merge_output_format": "mp4",

            "download_ranges": download_range,

            "force_keyframes_at_cuts": True,

            "noplaylist": True,

            "quiet": False
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        files = [
            os.path.join(DOWNLOAD_DIR, f)
            for f in os.listdir(DOWNLOAD_DIR)
            if f.startswith(file_id)
        ]

        if not files:
            return "Video processing failed."

        output_file = files[0]

        return send_file(
            output_file,
            as_attachment=True,
            download_name="youtube_clip.mp4"
        )

    except Exception as e:
        return f"Error: {str(e)}", 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)