import os
import sys
import json
import shutil

# Put workspace in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backend.account_manager import AccountManager
from backend.google_flow_engine import GoogleFlowEngine, PROJECTS_DIR
from backend.video_assembler import VideoAssembler


def run_full_architecture_check():
    print("=" * 60)
    print("🔍 RUNNING FULL ARCHITECTURE & PIPELINE HEALTH CHECK")
    print("=" * 60)

    # 1. Check Video Assembler / FFmpeg
    print("\n[1/4] Checking Video Assembler & FFmpeg...")
    assembler = VideoAssembler()
    ffmpeg_ok = assembler.check_ffmpeg()
    print(f"  • FFmpeg binary: {assembler.ffmpeg_path}")
    print(f"  • FFmpeg working: {'✅ YES' if ffmpeg_ok else '❌ NO'}")
    assert ffmpeg_ok, "FFmpeg is required but not operational"

    # 2. Check Multi-Account Manager
    print("\n[2/4] Testing Multi-Account Manager Vault...")
    mgr = AccountManager()

    # Clean test state
    gpt1 = mgr.add_chatgpt_account("Agency GPT-4o", "sk-proj-test1234567890", "gpt-4o", set_active=True)
    gpt2 = mgr.add_chatgpt_account("Backup GPT-4o-Mini", "sk-proj-backup987654", "gpt-4o-mini", set_active=False)
    assert gpt1["is_active"] is True
    assert gpt2["is_active"] is False

    # Switch active
    mgr.set_active_chatgpt_account(gpt2["id"])
    active_gpt = mgr.get_active_chatgpt_account()
    assert active_gpt["id"] == gpt2["id"]
    print("  • Multiple ChatGPT accounts & switching: ✅ PASS")

    flow1 = mgr.add_google_flow_account("Studio Google Flow #1", "studio@gmail.com", "session_cookie", "tok_session_1", "", 50, set_active=True)
    flow2 = mgr.add_google_flow_account("Backup Flow Account", "backup@gmail.com", "api_key", "", "AIzaSy_test", 100, set_active=False)
    assert flow1["is_active"] is True
    print("  • Multiple Google Flow accounts & vault: ✅ PASS")

    # 3. Test Multi-Character Storyboard & Google Flow Manifest Engine
    print("\n[3/4] Testing Multi-Character Google Flow Engine...")
    sample_storyboard = {
        "project_title": "Neon Syndicate",
        "aspect_ratio": "9:16",
        "style": "Cyberpunk Neo-Noir",
        "characters": [
            {
                "name": "Detective Jax",
                "role": "Lead Investigator",
                "appearance_prompt": "Mid-30s detective, trench coat, glowing blue cybernetic eye",
                "voice_tone": "Deep and gritty"
            },
            {
                "name": "Aria Cross",
                "role": "Android Specialist",
                "appearance_prompt": "Late-20s specialist, silver bob cut, glowing neural circuitry",
                "voice_tone": "Analytical and crisp"
            }
        ],
        "scenes": [
            {
                "scene_number": 1,
                "speaker": "Detective Jax",
                "featured_characters": ["Detective Jax"],
                "narration": "The rain in Sector 4 washes away everything except the truth.",
                "flow_veo_prompt": "Cinematic low angle tracking shot of Detective Jax walking in neon rain",
                "camera_motion": "Forward Dolly",
                "duration_seconds": 3
            },
            {
                "scene_number": 2,
                "speaker": "Aria Cross",
                "featured_characters": ["Detective Jax", "Aria Cross"],
                "narration": "Then look closer, Jax. The data doesn't lie.",
                "flow_veo_prompt": "Two-shot medium angle of Aria showing Jax the glowing encrypted holographic shard",
                "camera_motion": "Slow Orbit",
                "duration_seconds": 3
            }
        ]
    }

    flow_engine = GoogleFlowEngine(flow1)
    project = flow_engine.create_flow_project(sample_storyboard)
    project_id = project["project_id"]
    print(f"  • Created Google Flow Project: {project_id}")
    print(f"  • Registered Character Arcs: {len(project['character_arcs'])} characters ({[c['name'] for c in project['character_arcs']]})")
    assert len(project["character_arcs"]) == 2
    assert len(project["scenes"]) == 2
    print("  • Multi-Character Google Flow manifest generation: ✅ PASS")

    # 4. Test Video Assembly & Stitching with FFmpeg
    print("\n[4/4] Testing Video Assembly & MP4 Rendering Pipeline...")
    project_dir = os.path.join(PROJECTS_DIR, project_id)
    clip_paths = []

    for sc in project["scenes"]:
        sc_num = sc["scene_number"]
        clip_file = os.path.join(project_dir, f"scene_{sc_num}.mp4")
        speaker = sc.get("speaker", "Host")
        text = f"Scene {sc_num} [{speaker}]\n{sc['narration'][:40]}..."
        created = assembler.create_placeholder_clip(text, clip_file, duration=sc["duration_seconds"], aspect_ratio="9:16")
        assert created and os.path.exists(clip_file), f"Failed to generate clip for scene {sc_num}"
        clip_paths.append(clip_file)
        print(f"  • Rendered Scene {sc_num} MP4 clip ({os.path.getsize(clip_file)} bytes)")

    final_mp4 = os.path.join(project_dir, "final_video.mp4")
    concat_ok = assembler.concatenate_clips(clip_paths, final_mp4)
    assert concat_ok and os.path.exists(final_mp4), "Failed to concatenate video"
    final_size = os.path.getsize(final_mp4)
    print(f"  • Assembled Final Video: {final_mp4} ({final_size} bytes)")
    print("  • Video Assembly Engine: ✅ PASS")

    # Cleanup test project
    shutil.rmtree(project_dir, ignore_errors=True)
    mgr.delete_chatgpt_account(gpt1["id"])
    mgr.delete_chatgpt_account(gpt2["id"])
    mgr.delete_google_flow_account(flow1["id"])
    mgr.delete_google_flow_account(flow2["id"])

    print("\n" + "=" * 60)
    print("🎉 ALL ARCHITECTURAL LAYERS & PIPELINE COMPONENTS FUNCTIONAL!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    run_full_architecture_check()
