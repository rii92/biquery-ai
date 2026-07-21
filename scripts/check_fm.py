import json
with open("prompts/intents.json", encoding="utf-8") as f:
    intents = json.load(f)
for intent in intents:
    fm = intent.get("filter_mappings")
    if fm:
        print(f'{intent["id"]}: {len(fm)} keys - {list(fm.keys())}')
    else:
        print(f'{intent["id"]}: NO filter_mappings')
