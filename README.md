# DigitalMaker.AI (Google Flow + ChatGPT Edition)

An automated video creation studio inspired by **DigitalMaker.AI**, engineered to work directly with **Google Flow** (Veo) and **ChatGPT**.

## Key Capabilities

1. **DigitalMaker.AI-Style Onboarding & Dual Input Modes:**
   - **Mode 1: Concept / Topic Mode:** Generates a viral script and hook from a single prompt idea.
   - **Mode 2: Custom Script Mode:** Paste your own pre-written script or article; ChatGPT refines the pacing, divides it into scenes, invents/matches the Character Arc, and builds the visual camera prompts.
   - Refinement Controls: Choose between *⚡ Enhance Pacing & Viral Flow* or *🔒 Keep Spoken Lines Verbatim*.
   - Visual Style Selector (Cinematic, Cyberpunk, 3D Anime, Dark Fantasy, Documentary).
   - Aspect Ratio Switcher (9:16 Shorts/TikTok vs 16:9 YouTube).

2. **ChatGPT Storytelling & Character Arc Engine:**
   - Takes your topic and invents a consistent protagonist tailored for Google Flow's **Character Arc** tool.
   - Generates scene-by-scene narration and cinematic camera prompts (dolly, tracking, drone, lighting).

3. **Multi-Account Manager:**
   - Connect **multiple ChatGPT accounts / API keys** (e.g. personal, client, or team keys).
   - Connect **multiple Google Flow accounts** (via session tokens or API keys) to distribute generation credits and avoid rate limits.
   - Switch active accounts with 1 click from the top navigation bar.

4. **Automated FFmpeg Assembly:**
   - Stitches scenes together and outputs a ready-to-publish MP4 video.

---

## Quick Start

1. Start the local server:
   ```bash
   ./run.sh
   # or: python3 backend/app.py
   ```
2. Open your browser at:
   ```
   http://localhost:8000
   ```
3. Click **"⚙️ Manage Accounts"**:
   - Add your **ChatGPT** API key (`sk-proj-...`).
   - Add your **Google Flow** account (Session token or Google AI Studio/Cloud API key).
4. Enter your video topic and click **"⚡ Generate Storyboard & Character Arc"**!

---

## Architecture

```
User Topic
    │
    ▼
[ ChatGPT (OpenAI GPT-4o) ]
    ├─► Character Arc Profile (Locks in face/clothing/style)
    └─► Storyboard Scenes with Veo camera directions
    │
    ▼
[ Google Flow Connector ]
    ├─► Character Arc Tool
    └─► Google Veo Video Generation
    │
    ▼
[ FFmpeg Video Assembler ]
    │
    ▼
Final 9:16 or 16:9 MP4
```
