import json
import os
import uuid
import time
from typing import Dict, List, Optional, Any
from backend.security import encrypt_secret, decrypt_secret

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")


class AccountManager:
    """
    Manages multiple accounts for both ChatGPT (OpenAI) and Google Flow (Veo/Labs).
    Supports adding, switching, validating, and auto-fallback rotation when limits are reached.
    """

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._ensure_storage()

    def _ensure_storage(self):
        if not os.path.exists(ACCOUNTS_FILE):
            default_data = {
                "chatgpt_accounts": [],
                "google_flow_accounts": [],
                "settings": {
                    "auto_fallback_enabled": True,
                    "default_aspect_ratio": "9:16",
                    "default_style": "Cinematic Realism"
                }
            }
            with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=2)

    def _load_data(self) -> Dict[str, Any]:
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"chatgpt_accounts": [], "google_flow_accounts": [], "settings": {}}

    def _save_data(self, data: Dict[str, Any]):
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ------------------- ChatGPT Account Management -------------------

    def list_chatgpt_accounts(self) -> List[Dict[str, Any]]:
        data = self._load_data()
        accounts = data.get("chatgpt_accounts", [])
        # Mask sensitive keys for frontend display
        sanitized = []
        for acc in accounts:
            copy = dict(acc)
            raw_key = copy.get("api_key", "")
            if len(raw_key) > 8:
                copy["masked_key"] = f"{raw_key[:4]}...{raw_key[-4:]}"
            else:
                copy["masked_key"] = "••••••••"
            sanitized.append(copy)
        return sanitized

    def add_chatgpt_account(self, label: str, api_key: str, model: str = "gpt-4o", set_active: bool = False) -> Dict[str, Any]:
        data = self._load_data()
        account_id = f"gpt_{uuid.uuid4().hex[:8]}"
        is_first = len(data["chatgpt_accounts"]) == 0

        new_account = {
            "id": account_id,
            "label": label.strip() or f"ChatGPT Account ({len(data['chatgpt_accounts']) + 1})",
            "api_key": encrypt_secret(api_key.strip()),
            "model": model or "gpt-4o",
            "is_active": set_active or is_first,
            "status": "Ready",
            "created_at": int(time.time()),
            "usage_count": 0
        }

        if new_account["is_active"]:
            for acc in data["chatgpt_accounts"]:
                acc["is_active"] = False

        data["chatgpt_accounts"].append(new_account)
        self._save_data(data)
        return new_account

    def set_active_chatgpt_account(self, account_id: str) -> bool:
        data = self._load_data()
        found = False
        for acc in data["chatgpt_accounts"]:
            if acc["id"] == account_id:
                acc["is_active"] = True
                found = True
            else:
                acc["is_active"] = False
        if found:
            self._save_data(data)
        return found

    def delete_chatgpt_account(self, account_id: str) -> bool:
        data = self._load_data()
        initial_len = len(data["chatgpt_accounts"])
        data["chatgpt_accounts"] = [a for a in data["chatgpt_accounts"] if a["id"] != account_id]
        if len(data["chatgpt_accounts"]) < initial_len:
            # Ensure at least one is active if available
            if data["chatgpt_accounts"] and not any(a["is_active"] for a in data["chatgpt_accounts"]):
                data["chatgpt_accounts"][0]["is_active"] = True
            self._save_data(data)
            return True
        return False

    def get_active_chatgpt_account(self) -> Optional[Dict[str, Any]]:
        data = self._load_data()
        for acc in data.get("chatgpt_accounts", []):
            if acc.get("is_active"):
                copy = dict(acc)
                copy["api_key"] = decrypt_secret(copy["api_key"])
                return copy
        if data.get("chatgpt_accounts"):
            copy = dict(data["chatgpt_accounts"][0])
            copy["api_key"] = decrypt_secret(copy["api_key"])
            return copy
        return None

    # ------------------- Google Flow Account Management -------------------

    def list_google_flow_accounts(self) -> List[Dict[str, Any]]:
        data = self._load_data()
        accounts = data.get("google_flow_accounts", [])
        sanitized = []
        for acc in accounts:
            copy = dict(acc)
            # Mask sensitive session tokens or keys
            token = copy.get("session_token", "")
            if token and len(token) > 10:
                copy["masked_token"] = f"{token[:6]}...{token[-4:]}"
            else:
                copy["masked_token"] = "••••••••"
            sanitized.append(copy)
        return sanitized

    def add_google_flow_account(
        self,
        label: str,
        email: str = "",
        auth_type: str = "session_cookie",  # "session_cookie" or "api_key"
        session_token: str = "",
        api_key: str = "",
        estimated_credits: int = 50,
        set_active: bool = False
    ) -> Dict[str, Any]:
        data = self._load_data()
        account_id = f"flow_{uuid.uuid4().hex[:8]}"
        is_first = len(data["google_flow_accounts"]) == 0

        new_account = {
            "id": account_id,
            "label": label.strip() or f"Google Flow Account ({len(data['google_flow_accounts']) + 1})",
            "email": email.strip(),
            "auth_type": auth_type,
            "session_token": encrypt_secret(session_token.strip()),
            "api_key": encrypt_secret(api_key.strip()),
            "estimated_credits": estimated_credits,
            "is_active": set_active or is_first,
            "status": "Ready",
            "created_at": int(time.time()),
            "projects_created": 0
        }

        if new_account["is_active"]:
            for acc in data["google_flow_accounts"]:
                acc["is_active"] = False

        data["google_flow_accounts"].append(new_account)
        self._save_data(data)
        return new_account

    def set_active_google_flow_account(self, account_id: str) -> bool:
        data = self._load_data()
        found = False
        for acc in data["google_flow_accounts"]:
            if acc["id"] == account_id:
                acc["is_active"] = True
                found = True
            else:
                acc["is_active"] = False
        if found:
            self._save_data(data)
        return found

    def delete_google_flow_account(self, account_id: str) -> bool:
        data = self._load_data()
        initial_len = len(data["google_flow_accounts"])
        data["google_flow_accounts"] = [a for a in data["google_flow_accounts"] if a["id"] != account_id]
        if len(data["google_flow_accounts"]) < initial_len:
            if data["google_flow_accounts"] and not any(a["is_active"] for a in data["google_flow_accounts"]):
                data["google_flow_accounts"][0]["is_active"] = True
            self._save_data(data)
            return True
        return False

    def get_active_google_flow_account(self) -> Optional[Dict[str, Any]]:
        data = self._load_data()
        for acc in data.get("google_flow_accounts", []):
            if acc.get("is_active"):
                copy = dict(acc)
                copy["session_token"] = decrypt_secret(copy.get("session_token", ""))
                copy["api_key"] = decrypt_secret(copy.get("api_key", ""))
                return copy
        if data.get("google_flow_accounts"):
            copy = dict(data["google_flow_accounts"][0])
            copy["session_token"] = decrypt_secret(copy.get("session_token", ""))
            copy["api_key"] = decrypt_secret(copy.get("api_key", ""))
            return copy
        return None

    def get_next_available_flow_account(self, failed_account_id: str) -> Optional[Dict[str, Any]]:
        """Fallback to the next available Google Flow account if one runs out of credits or encounters an error."""
        data = self._load_data()
        for acc in data.get("google_flow_accounts", []):
            if acc["id"] != failed_account_id and acc.get("status") != "Exhausted":
                self.set_active_google_flow_account(acc["id"])
                return acc
        return None
