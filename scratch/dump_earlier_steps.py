import json

with open(r'C:\Users\DELL\.gemini\antigravity\brain\83647f14-b378-4023-b2d3-de099f25eed9\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            obj = json.loads(line)
            idx = obj.get('step_index', 0)
            if idx in [2153, 2232, 2283, 2349]:
                print(f"=== STEP {idx} ===")
                t_calls = obj.get('tool_calls', [])
                for tc in t_calls:
                    print("Tool call:", tc.get('name'))
                    args = tc.get('args', {})
                    if 'Target' in args or 'Replacement' in args:
                        print("Target snippet:", str(args.get('Target'))[:200])
                        print("Replacement snippet:", str(args.get('Replacement'))[:300])
                content = obj.get('content', '')
                if isinstance(content, str) and content:
                    print("Content:", content[:400])
        except Exception:
            pass
