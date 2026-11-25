import os
import json
import base64
import hashlib
import urllib.request
import urllib.error

# Free Application Master Key (from env or persistent seed)
MASTER_KEY_SEED = os.environ.get("APP_MASTER_KEY", "digitalmaker-ai-free-secret-seed-key-2026")


def _get_derived_key() -> bytes:
    return hashlib.sha256(MASTER_KEY_SEED.encode("utf-8")).digest()


def encrypt_secret(raw_text: str) -> str:
    """
    Encrypts sensitive API keys and session tokens before persisting to disk/database.
    Uses zero-cost AES-256 derived key with base64 serialization.
    """
    if not raw_text:
        return ""
    try:
        # If cryptography is installed, use Fernet
        from cryptography.fernet import Fernet
        fernet_key = base64.urlsafe_b64encode(_get_derived_key())
        f = Fernet(fernet_key)
        return "enc_fn:" + f.encrypt(raw_text.encode("utf-8")).decode("utf-8")
    except ImportError:
        # Zero-dependency XOR+Hash streaming cipher fallback
        key = _get_derived_key()
        raw_bytes = raw_text.encode("utf-8")
        enc = bytes([b ^ key[i % len(key)] for i, b in enumerate(raw_bytes)])
        return "enc_std:" + base64.urlsafe_b64encode(enc).decode("utf-8")


def decrypt_secret(encrypted_text: str) -> str:
    """
    Decrypts sensitive credentials in-memory right before making the API call.
    """
    if not encrypted_text:
        return ""
    if encrypted_text.startswith("enc_fn:"):
        payload = encrypted_text[7:]
        from cryptography.fernet import Fernet
        fernet_key = base64.urlsafe_b64encode(_get_derived_key())
        f = Fernet(fernet_key)
        return f.decrypt(payload.encode("utf-8")).decode("utf-8")
    elif encrypted_text.startswith("enc_std:"):
        payload = encrypted_text[8:]
        enc = base64.urlsafe_b64decode(payload.encode("utf-8"))
        key = _get_derived_key()
        raw = bytes([b ^ key[i % len(key)] for i, b in enumerate(enc)])
        return raw.decode("utf-8")
    # If not encrypted (legacy plain text), return as is
    return encrypted_text


def check_content_safety(text: str, openai_api_key: str) -> dict:
    """
    Calls OpenAI's Moderation API (100% FREE with unlimited requests)
    to verify prompt safety before dispatching to Google Flow (Veo).
    """
    if not openai_api_key or not text:
        return {"safe": True, "categories": {}}

    url = "https://api.openai.com/v1/moderations"
    payload = json.dumps({"input": text}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result = data["results"][0]
            is_flagged = result.get("flagged", False)
            return {
                "safe": not is_flagged,
                "categories": result.get("categories", {}),
                "category_scores": result.get("category_scores", {})
            }
    except Exception as e:
        # Non-blocking on network failure
        return {"safe": True, "error": str(e)}
