import os, json

JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'
files = os.listdir(JSON_DIR)[:200]

wrapper_keys = set()
inner_keys = set()

for f in files:
    if not f.endswith('.json'):
        continue
    with open(os.path.join(JSON_DIR, f), 'r', encoding='utf-8') as fp:
        try:
            d = json.load(fp)
        except:
            continue
    for g in d.get('detail', {}).get('groups', []):
        for e in g.get('data', {}).get('events', []):
            wrapper_keys.update(e.keys())
            ev = e.get('event', {})
            if isinstance(ev, dict):
                inner_keys.update(ev.keys())

print("Wrapper keys:", sorted(list(wrapper_keys)))
print("Inner event keys:", sorted(list(inner_keys)))
