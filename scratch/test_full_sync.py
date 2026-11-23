import urllib.request
import json
import time

SYNC_TOPIC = "iitg_5g_wearable_nav_sync_9169957"

def publish_tunnel_url(url: str):
    """Called by laptop edge_server when cloudflared starts."""
    try:
        req = urllib.request.Request(
            f"https://ntfy.sh/{SYNC_TOPIC}",
            data=url.strip().encode('utf-8'),
            headers={'Title': 'Active5GTunnelURL', 'User-Agent': '5G-Edge-Server'},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                print(f"✅ Published tunnel URL to Cloud Sync: {url}")
                return True
    except Exception as e:
        print(f"⚠️ Failed to publish tunnel URL: {e}")
    return False

def fetch_active_tunnel_url(timeout=5):
    """Called by wearable_client/python/main.py to auto-discover server."""
    try:
        req = urllib.request.Request(
            f"https://ntfy.sh/{SYNC_TOPIC}/json?poll=1",
            headers={'User-Agent': 'Wearable-Arduino-Client'}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8').strip()
            # Each line is a JSON message
            lines = body.split('\n')
            for line in reversed(lines):
                if not line.strip():
                    continue
                data = json.loads(line)
                if data.get("event") == "message":
                    url = data.get("message", "").strip()
                    if url.startswith("http://") or url.startswith("https://"):
                        return url
    except Exception as e:
        print(f"⚠️ Cloud sync lookup note: {e}")
    return None

# Test:
test_url = "https://numerical-formation-gilbert-tree.trycloudflare.com"
publish_tunnel_url(test_url)
time.sleep(0.5)
discovered = fetch_active_tunnel_url()
print(f"🎉 Discovered URL: {discovered}")
assert discovered == test_url, "URL mismatch!"
print("Test Passed 100%!")
