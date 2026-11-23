import urllib.request
import urllib.parse
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

print("Testing services...")

# 1. dpaste.org
try:
    data = urllib.parse.urlencode({'content': 'https://my-test.trycloudflare.com', 'expiry_days': 1}).encode('utf-8')
    req = urllib.request.Request('https://dpaste.org/api/', data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as r:
        paste_url = r.read().decode('utf-8').strip().strip('"')
        print("dpaste OK! Paste URL:", paste_url)
        raw_url = paste_url + "/raw"
        req_raw = urllib.request.Request(raw_url, headers=headers)
        with urllib.request.urlopen(req_raw, timeout=5) as gr:
            print("dpaste read back:", gr.read().decode('utf-8').strip())
except Exception as e:
    print("dpaste failed:", e)

# 2. cl1p.net (internet clipboard with named URLs e.g. cl1p.net/iitg_5g_nav_sync)
try:
    clip_url = "https://cl1p.net/iitg_5g_nav_sync_test"
    req = urllib.request.Request(clip_url, data=b"https://my-test-tunnel.trycloudflare.com", headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        print("cl1p.net POST status:", r.status)
    req_get = urllib.request.Request(clip_url, headers=headers)
    with urllib.request.urlopen(req_get, timeout=5) as gr:
        print("cl1p.net read back:", gr.read().decode('utf-8')[:100])
except Exception as e:
    print("cl1p.net failed:", e)

# 3. ntfy.sh with cache
try:
    topic = "iitg_5g_nav_tunnel_sync"
    req = urllib.request.Request(f"https://ntfy.sh/{topic}", data=b"https://live-test.trycloudflare.com", headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        print("ntfy POST status:", r.status)
    # ntfy /json?poll=1&since=all
    req_get = urllib.request.Request(f"https://ntfy.sh/{topic}/json?poll=1&since=10m", headers=headers)
    with urllib.request.urlopen(req_get, timeout=5) as gr:
        lines = gr.read().decode('utf-8').strip().split('\n')
        for l in reversed(lines):
            try:
                obj = json.loads(l)
                if obj.get("event") == "message":
                    print("ntfy retrieved message:", obj.get("message"))
                    break
            except Exception:
                pass
except Exception as e:
    print("ntfy failed:", e)
