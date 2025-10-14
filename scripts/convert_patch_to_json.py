import sys, json, os

if len(sys.argv) < 3:
    print("Usage: convert_patch_to_json.py <input.patch> <output.json>")
    sys.exit(1)

patch_file = sys.argv[1]
out_file = sys.argv[2]

fixes = {}
if os.path.exists(patch_file) and os.path.getsize(patch_file) > 0:
    with open(patch_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    fixes["raw_patch"] = "".join(lines)
else:
    fixes["raw_patch"] = ""

os.makedirs(os.path.dirname(out_file), exist_ok=True)
with open(out_file, "w", encoding="utf-8") as out:
    json.dump(fixes, out, indent=2)

print(f"✅ Wrote fixes to {out_file}")
