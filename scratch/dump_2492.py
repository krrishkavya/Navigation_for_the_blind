import json

with open(r'C:\Users\DELL\.gemini\antigravity\brain\83647f14-b378-4023-b2d3-de099f25eed9\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            obj = json.loads(line)
            idx = obj.get('step_index', 0)
            if idx in [2492, 2495]:
                print(f"=== STEP {idx} ===")
                t_calls = obj.get('tool_calls', [])
                for tc in t_calls:
                    args = tc.get('args', {})
                    rep = str(args.get('Replacement', ''))
                    print("Tool:", tc.get('name'))
                    print("Path:", args.get('Path'))
                    print("Replacement:\n", rep[:2500])
        except Exception:
            pass
