import json, os, collections

roots = [
    r"C:\Users\capatino\AppData\Local\Temp\pbi_scan2\sistema\Report\definition\pages",
    r"C:\Users\capatino\Documents\Caracterización de aprendices\Dashboard_Aprendices_SENA\tmp_validation\Test.Report\definition\pages",
]
by_type = collections.defaultdict(list)
for root in roots:
    for dirpath, dirnames, filenames in os.walk(root):
        if "visual.json" in filenames:
            fp = os.path.join(dirpath, "visual.json")
            try:
                d = json.load(open(fp, encoding="utf-8-sig"))
            except Exception as e:
                print("ERR", fp, e)
                continue
            t = d.get("visual", {}).get("visualType", "?")
            by_type[t].append((fp, d))
for t, items in sorted(by_type.items(), key=lambda kv: (-len(kv[1]), kv[0])):
    print(f"{t}: {len(items)}")
    for fp, d in items[:3]:
        print("   ", fp.replace(r"C:\Users\capatino\AppData\Local\Temp\pbi_scan2\sistema\Report\definition\pages\\", "scan:").replace(r"C:\Users\capatino\Documents\Caracterización de aprendices\Dashboard_Aprendices_SENA\tmp_validation\Test.Report\definition\pages\\", "test:"))
