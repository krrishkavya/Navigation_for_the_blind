import json

with open(r'C:\Users\DELL\.gemini\antigravity\brain\83647f14-b378-4023-b2d3-de099f25eed9\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            obj = json.loads(line)
            if obj.get('step_index') == 2232:
                print("Content of step 2232:")
                print(obj.get('content'))
                break
        except Exception:
            pass
