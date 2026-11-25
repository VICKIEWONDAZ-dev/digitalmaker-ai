import os
import subprocess
import json
import shutil

FFMPEG_BIN = "/usr/local/bin/ffmpeg" if os.path.exists("/usr/local/bin/ffmpeg") else shutil.which("ffmpeg") or "ffmpeg"


class VideoAssembler:
    """
    Stitches scene video clips, narration voiceover, and captions into a final MP4 video using FFmpeg.
    """

    def __init__(self):
        self.ffmpeg_path = FFMPEG_BIN

    def check_ffmpeg(self) -> bool:
        try:
            res = subprocess.run([self.ffmpeg_path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return res.returncode == 0
        except Exception:
            return False

    def create_placeholder_clip(self, text: str, output_path: str, duration: int = 5, aspect_ratio: str = "9:16"):
        """
        Creates a high-definition placeholder video clip using FFmpeg.
        Gracefully handles environments with or without the optional drawtext filter.
        """
        width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
        escaped_text = text.replace(":", "\\:").replace("'", "\\'")

        # Attempt 1: Try with drawtext filter
        cmd_drawtext = [
            self.ffmpeg_path, "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x0f172a:s={width}x{height}:d={duration}",
            "-vf", f"drawtext=text='{escaped_text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=0x1e293b@0.8:boxborderw=20",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            output_path
        ]
        res = subprocess.run(cmd_drawtext, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0 and os.path.exists(output_path):
            return True

        # Attempt 2 (Universal fallback): Generate high-def gradient without drawtext dependency
        colors = ["0x0f172a", "0x1e1b4b", "0x1e293b", "0x312e81"]
        import zlib
        bg_color = colors[zlib.crc32(text.encode()) % len(colors)]

        cmd_fallback = [
            self.ffmpeg_path, "-y",
            "-f", "lavfi",
            "-i", f"color=c={bg_color}:s={width}x{height}:d={duration}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            output_path
        ]
        subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return os.path.exists(output_path)

    def concatenate_clips(self, clip_paths: list, output_path: str) -> bool:
        """
        Concatenates multiple MP4 clips seamlessly into one final video.
        """
        if not clip_paths:
            return False

        temp_list = output_path + ".list.txt"
        with open(temp_list, "w", encoding="utf-8") as f:
            for p in clip_paths:
                f.write(f"file '{os.path.abspath(p)}'\n")

        cmd = [
            self.ffmpeg_path, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", temp_list,
            "-c", "copy",
            output_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if os.path.exists(temp_list):
            os.remove(temp_list)
        return res.returncode == 0 and os.path.exists(output_path)
