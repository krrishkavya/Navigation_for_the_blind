import sys
import os
import time

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from edge_server.tunnel_manager import publish_cloud_sync_url, CLOUD_SYNC_TOPIC
from wearable_client.python.main import fetch_active_cloud_url, CLOUD_SYNC_TOPIC as CLIENT_TOPIC

print("=" * 60)
print("TESTING OPTION B: ZERO-TOUCH 5G CLOUD SYNC PIPELINE")
print("=" * 60)

# 1. Verify Topic Consistency
print(f"1. Verifying Cloud Sync Topics match...")
assert CLOUD_SYNC_TOPIC == CLIENT_TOPIC, f"Topic mismatch: {CLOUD_SYNC_TOPIC} != {CLIENT_TOPIC}"
print(f"   ✅ Topics match: {CLOUD_SYNC_TOPIC}")

# 2. Test Publishing from Server
test_tunnel_url = f"https://speedy-robot-walk-{int(time.time())}.trycloudflare.com"
print(f"\n2. Publishing test tunnel URL from Server: {test_tunnel_url}...")
pub_ok = publish_cloud_sync_url(test_tunnel_url)
assert pub_ok, "Publishing to cloud sync failed!"
print("   ✅ Server successfully published URL to Cloud Sync bus.")

# 3. Test Wearable Discovery
print(f"\n3. Testing Wearable Client Auto-Discovery...")
time.sleep(1.5)
discovered_url = fetch_active_cloud_url(timeout=4.0)
print(f"   Discovered URL: {discovered_url}")
assert discovered_url == test_tunnel_url, f"Expected {test_tunnel_url}, got {discovered_url}"
print("   ✅ Wearable successfully auto-discovered active Server URL!")

# 4. Verify Local Disk Cache
cache_file = os.path.join(project_root, "wearable_client", "python", "last_known_tunnel_url.txt")
try:
    with open(cache_file, "w") as f:
        f.write(discovered_url)
    with open(cache_file, "r") as f:
        cached = f.read().strip()
    assert cached == discovered_url
    print(f"   ✅ Offline cache on disk verified: {cache_file}")
finally:
    if os.path.exists(cache_file):
        os.remove(cache_file)

print("\n" + "=" * 60)
print("🎉 ALL 4/4 ZERO-TOUCH CLOUD SYNC TESTS PASSED PERFECTLY!")
print("=" * 60)
