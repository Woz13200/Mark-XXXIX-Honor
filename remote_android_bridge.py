import os
import requests


ANDROID_BRIDGE_URL = os.environ.get("ANDROID_BRIDGE_URL", "").rstrip("/")
ANDROID_BRIDGE_TOKEN = os.environ.get("ANDROID_BRIDGE_TOKEN", "")


def call_remote(action, payload=None):
    if not ANDROID_BRIDGE_URL:
        return {
            "ok": False,
            "error": "ANDROID_BRIDGE_URL manquante. Lance le bridge Termux + Cloudflare sur Honor."
        }

    payload = payload or {}
    payload["action"] = action

    headers = {
        "Content-Type": "application/json",
        "X-Bridge-Token": ANDROID_BRIDGE_TOKEN
    }

    try:
        r = requests.post(
            ANDROID_BRIDGE_URL + "/control",
            json=payload,
            headers=headers,
            timeout=35
        )

        try:
            return r.json()
        except Exception:
            return {
                "ok": False,
                "error": "Réponse non JSON du bridge Android.",
                "status_code": r.status_code,
                "text": r.text[:500]
            }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def android_status():
    return call_remote("status")


def android_vibrate():
    return call_remote("vibrate")


def android_speak(text):
    return call_remote("speak", {"text": text})


def android_open_url(url):
    return call_remote("open_url", {"url": url})


def android_home():
    return call_remote("home")


def android_back():
    return call_remote("back")


def android_recents():
    return call_remote("recents")


def android_tap(x, y):
    return call_remote("tap", {"x": x, "y": y})


def android_text(value):
    return call_remote("text", {"value": value})
