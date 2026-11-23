import urllib.request
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
topic = "iitg_5g_nav_tunnel_sync"

# Post a message with title
req = urllib.request.Request(
    f"https://ntfy.sh/{topic}", 
    data=b"https://live-test.trycloudflare.com", 
    headers={**headers, 'Title': 'TunnelURL'}, 
    method="POST"
)
with urllib.request.urlopen(req, timeout=5) as r:
    print("ntfy POST:", r.status)

# Now fetch poll=1
req_get = urllib.request.Request(f"https://ntfy.sh/{topic}/json?poll=1", headers=headers)
with urllib.request.urlopen(req_get, timeout=5) as gr:
    raw = gr.read().decode('utf-8')
    print("Raw response from ntfy:", raw)
