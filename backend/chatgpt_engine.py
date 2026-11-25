import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List


class ChatGPTEngine:
    """
    Connects to ChatGPT (OpenAI API) to transform user topics or custom pre-written scripts
    into structured viral video storyboards, complete with Multiple Character Profiles
    and Google Flow / Veo prompts.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model or "gpt-4o"
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def generate_storyboard(
        self,
        content: str,
        input_mode: str = "topic",  # "topic" or "custom_script"
        style: str = "Cinematic Realism",
        aspect_ratio: str = "9:16",
        character_preference: str = "",
        character_mode: str = "multi",  # "single", "multi", or "auto"
        scene_count: int = 4,
        refinement_style: str = "enhance_pacing"  # "enhance_pacing" or "verbatim"
    ) -> Dict[str, Any]:
        """
        Calls ChatGPT to generate a complete video plan with support for multiple characters.
        """
        if input_mode == "custom_script":
            task_description = f"""
The user has provided their own custom script/story below.
Your task is to REFINE, ADAPT, and STRUCTURE their script into a scene-by-scene storyboard
optimized for Google Flow and Google Veo video generation.

REFINEMENT RULES:
1. Preserve the user's core story, tone, and message.
   - Refinement Mode: {"Enhance pacing, cadence, and dialogue flow for viral retention while keeping the core words" if refinement_style == "enhance_pacing" else "Keep the user's narration and dialogue lines as close to verbatim as possible"}.
2. Multiple Character Handling:
   - Identify all distinct characters/speakers present in the script (e.g. Host 1 & Host 2, Protagonist & Antagonist, Narrator & Hero).
   - Create distinct Google Flow "Character Arc" profiles for each character (specifying unique facial features, hair, clothing, signature aesthetic).
3. Scene Breakdown: Divide the script into {scene_count} sequential scenes.
   - Clearly label who is speaking (`speaker`) and who appears in the visual shot (`featured_characters`).
4. Google Flow Veo Prompts: For each scene, create vivid, cinematic prompts tailored for Google Veo.
   - For multi-character shots (two-shots, dialogues, confrontations), explicitly describe the spatial relationship and interaction between the characters.
"""
            user_prompt = f"USER'S CUSTOM SCRIPT:\n\"\"\"\n{content}\n\"\"\""
        else:
            task_description = f"""
Your task is to take a video concept and convert it into a production-ready storyboard
optimized specifically for Google Flow and Google Veo video generation.

CRITICAL INSTRUCTIONS:
1. Pacing & Hook: Craft a viral hook in Scene 1 and maintain strong narrative progression.
2. Multiple Characters Design:
   - Create 1 to 3 distinct, memorable characters suited for Google Flow's "Character Arc" feature (e.g. 2 podcast co-hosts, detective & partner, hero & adversary).
   - Describe each character's exact facial features, clothing, age, and aesthetic so they look visually distinct from each other yet consistent across shots.
3. Multi-Character Interactions:
   - Vary the shots: solo close-ups, medium dialogue exchanges, and dynamic two-shots.
   - Tag each scene with the `speaker` and `featured_characters` array.
4. Google Flow Veo Prompts: Specify camera motion (e.g., slow forward dolly, over-the-shoulder shot, two-shot medium, aerial orbit), lighting, and character interactions.
"""
            user_prompt = f"Video Concept / Topic: {content}"

        system_prompt = f"""
You are an award-winning cinematic director, character designer, and viral video strategist.
{task_description}

Target Video Format: {aspect_ratio} ({'Vertical for TikTok/Shorts/Reels' if aspect_ratio == '9:16' else 'Horizontal for YouTube'})
Visual Style Aesthetic: {style}
Target Scene Count: {scene_count} scenes
Character Mode: {character_mode}

You must respond ONLY with a valid, parseable JSON object adhering strictly to this schema:
{{
  "project_title": "Engaging Short Title",
  "summary": "1-sentence logline",
  "style": "{style}",
  "aspect_ratio": "{aspect_ratio}",
  "characters": [
    {{
      "name": "Character Name",
      "role": "Role (e.g., Lead Investigator, Co-Host, Rival)",
      "appearance_prompt": "Highly detailed visual description for Google Flow character builder (face, hair, attire, signature look)",
      "aesthetic_anchor": "3-5 visual keywords for style consistency",
      "voice_tone": "e.g., Deep gritty storyteller / Energetic analytical"
    }}
  ],
  "character": {{
    "name": "Primary Protagonist Name",
    "role": "Primary Role",
    "appearance_prompt": "Primary character visual description",
    "aesthetic_anchor": "Style keywords"
  }},
  "scenes": [
    {{
      "scene_number": 1,
      "speaker": "Name of the character speaking (or 'Narrator')",
      "featured_characters": ["Character Name 1"],
      "narration": "Spoken voiceover or dialogue line for scene 1",
      "flow_veo_prompt": "Cinematic visual prompt for Google Flow / Veo with camera movement, character positioning, lighting, and action",
      "camera_motion": "e.g., Over-the-shoulder / Slow Two-Shot Dolly",
      "duration_seconds": 5
    }}
  ]
}}
"""

        if character_preference:
            user_prompt += f"\nCharacter Cast / Preferences: {character_preference}"

        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7
        }

        req = urllib.request.Request(
            self.api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                result = json.loads(response.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                # Ensure characters array exists
                if "characters" not in parsed or not parsed["characters"]:
                    if "character" in parsed:
                        parsed["characters"] = [parsed["character"]]
                    else:
                        parsed["characters"] = [{
                            "name": "Protagonist",
                            "role": "Lead",
                            "appearance_prompt": "Cinematic character",
                            "aesthetic_anchor": style
                        }]
                # Ensure primary character fallback exists
                if "character" not in parsed:
                    parsed["character"] = parsed["characters"][0]
                return parsed
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise Exception(f"OpenAI API Error ({e.code}): {err_body}")
        except Exception as e:
            raise Exception(f"Failed to communicate with ChatGPT: {str(e)}")
