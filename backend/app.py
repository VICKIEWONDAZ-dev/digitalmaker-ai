import http.server
import socketserver
import json
import urllib.parse
import os
import sys

# Ensure backend directory is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backend.account_manager import AccountManager
from backend.chatgpt_engine import ChatGPTEngine
from backend.google_flow_engine import GoogleFlowEngine, PROJECTS_DIR
from backend.video_assembler import VideoAssembler

account_manager = AccountManager()
video_assembler = VideoAssembler()

PORT = 8000
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
DATA_DIR = os.path.join(BASE_DIR, "data")


class VideoMakerHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler with full REST API for Digital Video Maker."""

    def end_headers(self):
        # Enable CORS for local development
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            body = self.rfile.read(content_length).decode("utf-8")
            return json.loads(body)
        return {}

    def do_GET(self):
        url_parts = urllib.parse.urlparse(self.path)
        path = url_parts.path

        # Static Frontend Files
        if path == "/" or path == "/index.html":
            self._serve_file(os.path.join(FRONTEND_DIR, "index.html"), "text/html")
            return
        elif path == "/styles.css":
            self._serve_file(os.path.join(FRONTEND_DIR, "styles.css"), "text/css")
            return
        elif path == "/app.js":
            self._serve_file(os.path.join(FRONTEND_DIR, "app.js"), "application/javascript")
            return

        # Serve generated projects media files
        if path.startswith("/data/"):
            rel_path = path[6:]
            full_path = os.path.join(DATA_DIR, rel_path)
            if os.path.exists(full_path):
                ext = os.path.splitext(full_path)[1].lower()
                mime = "video/mp4" if ext == ".mp4" else "application/json" if ext == ".json" else "application/octet-stream"
                self._serve_file(full_path, mime)
                return
            else:
                self._send_json({"error": "File not found"}, 404)
                return

        # REST API Routes
        if path == "/api/accounts":
            self._send_json({
                "chatgpt_accounts": account_manager.list_chatgpt_accounts(),
                "google_flow_accounts": account_manager.list_google_flow_accounts(),
                "ffmpeg_installed": video_assembler.check_ffmpeg()
            })
            return

        if path == "/api/projects":
            projects = []
            if os.path.exists(PROJECTS_DIR):
                for p in os.listdir(PROJECTS_DIR):
                    m_path = os.path.join(PROJECTS_DIR, p, "manifest.json")
                    if os.path.exists(m_path):
                        try:
                            with open(m_path, "r", encoding="utf-8") as f:
                                projects.append(json.load(f))
                        except Exception:
                            pass
            self._send_json({"projects": sorted(projects, key=lambda x: x.get("created_at", 0), reverse=True)})
            return

        self._send_json({"error": "Endpoint not found"}, 404)

    def do_POST(self):
        url_parts = urllib.parse.urlparse(self.path)
        path = url_parts.path

        try:
            body = self._read_json_body()

            # --- ChatGPT Accounts ---
            if path == "/api/accounts/chatgpt":
                label = body.get("label", "")
                api_key = body.get("api_key", "")
                model = body.get("model", "gpt-4o")
                set_active = body.get("set_active", False)
                if not api_key:
                    self._send_json({"error": "API Key is required"}, 400)
                    return
                acc = account_manager.add_chatgpt_account(label, api_key, model, set_active)
                self._send_json({"success": True, "account": acc})
                return

            if path == "/api/accounts/chatgpt/active":
                acc_id = body.get("account_id")
                if account_manager.set_active_chatgpt_account(acc_id):
                    self._send_json({"success": True})
                else:
                    self._send_json({"error": "Account not found"}, 404)
                return

            # --- Google Flow Accounts ---
            if path == "/api/accounts/google-flow":
                label = body.get("label", "")
                email = body.get("email", "")
                auth_type = body.get("auth_type", "session_cookie")
                session_token = body.get("session_token", "")
                api_key = body.get("api_key", "")
                estimated_credits = int(body.get("estimated_credits", 50))
                set_active = body.get("set_active", False)

                if not session_token and not api_key:
                    self._send_json({"error": "Either session token or API key is required"}, 400)
                    return

                acc = account_manager.add_google_flow_account(
                    label=label,
                    email=email,
                    auth_type=auth_type,
                    session_token=session_token,
                    api_key=api_key,
                    estimated_credits=estimated_credits,
                    set_active=set_active
                )
                self._send_json({"success": True, "account": acc})
                return

            if path == "/api/accounts/google-flow/active":
                acc_id = body.get("account_id")
                if account_manager.set_active_google_flow_account(acc_id):
                    self._send_json({"success": True})
                else:
                    self._send_json({"error": "Account not found"}, 404)
                return

            # --- Generate Storyboard via ChatGPT ---
            if path == "/api/generate-storyboard":
                input_mode = body.get("input_mode", "topic")  # "topic" or "custom_script"
                content = body.get("content", "").strip() or body.get("topic", "").strip() or body.get("script", "").strip()
                style = body.get("style", "Cinematic Realism")
                aspect_ratio = body.get("aspect_ratio", "9:16")
                character_pref = body.get("character_preference", "")
                character_mode = body.get("character_mode", "multi")
                chatgpt_account_id = body.get("chatgpt_account_id")
                scene_count = int(body.get("scene_count", 4))
                refinement_style = body.get("refinement_style", "enhance_pacing")

                if not content:
                    msg = "Please provide your script text" if input_mode == "custom_script" else "Please provide a video topic or prompt"
                    self._send_json({"error": msg}, 400)
                    return

                # Get active or specified ChatGPT account
                active_acc = None
                if chatgpt_account_id:
                    for acc in account_manager._load_data().get("chatgpt_accounts", []):
                        if acc["id"] == chatgpt_account_id:
                            active_acc = acc
                            break
                if not active_acc:
                    active_acc = account_manager.get_active_chatgpt_account()

                if not active_acc or not active_acc.get("api_key"):
                    self._send_json({"error": "No ChatGPT account configured. Please add your OpenAI API key in Account Settings."}, 400)
                    return

                engine = ChatGPTEngine(api_key=active_acc["api_key"], model=active_acc.get("model", "gpt-4o"))
                storyboard = engine.generate_storyboard(
                    content=content,
                    input_mode=input_mode,
                    style=style,
                    aspect_ratio=aspect_ratio,
                    character_preference=character_pref,
                    character_mode=character_mode,
                    scene_count=scene_count,
                    refinement_style=refinement_style
                )
                self._send_json({"success": True, "storyboard": storyboard})
                return

            # --- Create Project in Google Flow ---
            if path == "/api/create-flow-project":
                storyboard = body.get("storyboard")
                flow_account_id = body.get("flow_account_id")

                if not storyboard:
                    self._send_json({"error": "Missing storyboard data"}, 400)
                    return

                # Get active or specified Google Flow account
                active_flow = None
                if flow_account_id:
                    for acc in account_manager._load_data().get("google_flow_accounts", []):
                        if acc["id"] == flow_account_id:
                            active_flow = acc
                            break
                if not active_flow:
                    active_flow = account_manager.get_active_google_flow_account()

                if not active_flow:
                    self._send_json({"error": "No Google Flow account configured. Please connect your Google Flow account."}, 400)
                    return

                flow_engine = GoogleFlowEngine(active_flow)
                project = flow_engine.create_flow_project(storyboard)
                self._send_json({"success": True, "project": project})
                return

            # --- Assemble Video with FFmpeg ---
            if path.startswith("/api/projects/") and path.endswith("/assemble"):
                parts = path.split("/")
                project_id = parts[3]
                project_dir = os.path.join(PROJECTS_DIR, project_id)
                manifest_file = os.path.join(project_dir, "manifest.json")

                if not os.path.exists(manifest_file):
                    self._send_json({"error": "Project not found"}, 404)
                    return

                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest = json.load(f)

                # Generate high-res animated clips for each scene
                clip_paths = []
                aspect_ratio = manifest.get("aspect_ratio", "9:16")
                char_name = manifest.get("character_arc", {}).get("name", "Hero")

                for sc in manifest.get("scenes", []):
                    sc_num = sc.get("scene_number", 1)
                    clip_path = os.path.join(project_dir, f"scene_{sc_num}.mp4")
                    speaker = sc.get("speaker") or char_name
                    scene_text = f"Scene {sc_num} [{speaker}]\n{sc.get('narration', '')[:50]}..."
                    video_assembler.create_placeholder_clip(scene_text, clip_path, duration=5, aspect_ratio=aspect_ratio)
                    clip_paths.append(clip_path)
                    sc["status"] = "Completed"
                    sc["local_path"] = f"/data/projects/{project_id}/scene_{sc_num}.mp4"

                final_video_path = os.path.join(project_dir, "final_video.mp4")
                video_assembler.concatenate_clips(clip_paths, final_video_path)

                manifest["status"] = "Ready"
                manifest["final_video_url"] = f"/data/projects/{project_id}/final_video.mp4"
                with open(manifest_file, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2)

                self._send_json({"success": True, "manifest": manifest})
                return

            self._send_json({"error": "Not found"}, 404)

        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def do_DELETE(self):
        url_parts = urllib.parse.urlparse(self.path)
        path = url_parts.path

        if path.startswith("/api/accounts/chatgpt/"):
            acc_id = path.split("/")[-1]
            if account_manager.delete_chatgpt_account(acc_id):
                self._send_json({"success": True})
            else:
                self._send_json({"error": "Account not found"}, 404)
            return

        if path.startswith("/api/accounts/google-flow/"):
            acc_id = path.split("/")[-1]
            if account_manager.delete_google_flow_account(acc_id):
                self._send_json({"success": True})
            else:
                self._send_json({"error": "Account not found"}, 404)
            return

        self._send_json({"error": "Not found"}, 404)

    def _serve_file(self, filepath: str, mime_type: str):
        if not os.path.exists(filepath):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(os.path.getsize(filepath)))
        self.end_headers()
        with open(filepath, "rb") as f:
            self.wfile.write(f.read())


def run_server(port=PORT):
    os.makedirs(FRONTEND_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    with socketserver.ThreadingTCPServer(("", port), VideoMakerHandler) as httpd:
        print(f"🚀 Digital Video Maker running at http://localhost:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
