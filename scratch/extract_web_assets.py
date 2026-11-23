import os

source_file = r'2_Edge_Server_AI\mobile_5g_bridge.py'
with open(source_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Line 34 is index 33; Line 301 is index 300
css_lines = lines[33:300]
html_body = lines[301:392]
js_lines = lines[393:1284]

out_dir = r'2_Edge_Server_AI\static_web_client'
os.makedirs(out_dir, exist_ok=True)

with open(os.path.join(out_dir, 'style.css'), 'w', encoding='utf-8') as f:
    f.writelines(css_lines)

with open(os.path.join(out_dir, 'app.js'), 'w', encoding='utf-8') as f:
    f.writelines(js_lines)

head_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>5G Assistive Wearable - Mobile Client</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="theme-color" content="#0a0a12">
  <link rel="stylesheet" href="/style.css">
</head>
"""

tail_html = """
  <script src="/app.js"></script>
</body>
</html>
"""

full_index = head_html + "".join(html_body) + tail_html

with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(full_index)

print("Successfully extracted web client assets to", out_dir)
