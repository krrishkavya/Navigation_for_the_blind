import json

with open(r'C:\Users\DELL\.gemini\antigravity\brain\83647f14-b378-4023-b2d3-de099f25eed9\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            obj = json.loads(line)
            idx = obj.get('step_index', 0)
            if 2610 <= idx <= 2676 and obj.get('source') in ['USER_EXPLICIT', 'MODEL']:
                content = obj.get('content', '')
                if isinstance(content, str) and len(content) > 0:
                    print(f"=== Step {idx} ({obj.get('source')}) ===")
                    print(content[:400])
                    print()
        except Exception:
            pass
