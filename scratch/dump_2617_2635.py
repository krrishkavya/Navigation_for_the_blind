import json

with open(r'C:\Users\DELL\.gemini\antigravity\brain\83647f14-b378-4023-b2d3-de099f25eed9\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            obj = json.loads(line)
            idx = obj.get('step_index', 0)
            if 2617 <= idx <= 2635:
                print(f"=== STEP {idx} [{obj.get('source')}] ===")
                content = obj.get('content', '')
                if isinstance(content, str):
                    print(content[:1500])
        except Exception:
            pass
