#!/usr/bin/env python3
import json
import os
import sys

# CLI args: patch_file output_file
patch_file = sys.argv[1] if len(sys.argv) > 1 else "out/fixes.patch"
output_file = sys.argv[2] if len(sys.argv) > 2 else "out/fixes.json"
eslint_fixes_file = "out/eslint-fixes.json"

fixes = {
    "raw_patch": "",
    "eslint_suggestions": []
}

# 1️⃣ If patch exists — use it
if os.path.exists(patch_file) and os.path.getsize(patch_file) > 0:
    with open(patch_file, "r", encoding="utf-8", errors="ignore") as f:
        patch = f.read().strip()
        if patch:
            fixes["raw_patch"] = patch

# 2️⃣ If ESLint suggestions exist (React / JS projects)
if os.path.exists(eslint_fixes_file) and os.path.getsize(eslint_fixes_file) > 0:
    try:
        with open(eslint_fixes_file, "r", encoding="utf-8", errors="ignore") as f:
            eslint_data = json.load(f)
            for file_entry in eslint_data:
                file_path = file_entry.get("filePath", "")
                for msg in file_entry.get("messages", []):
                    if msg.get("fix"):
                        fixes["eslint_suggestions"].append({
                            "file": file_path,
                            "line": msg.get("line"),
                            "rule": msg.get("ruleId"),
                            "message": msg.get("message"),
                            "fix": msg.get("fix")
                        })
    except Exception as e:
        print(f"⚠️ ESLint parse error: {e}", file=sys.stderr)

# 3️⃣ Ensure output folder exists
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# 4️⃣ Write output JSON
with open(output_file, "w", encoding="utf-8") as out:
    json.dump(fixes, out, indent=2)

print(f"✅ Wrote fixes to {output_file}")
if fixes["raw_patch"]:
    print(f"  🧩 Patch included ({len(fixes['raw_patch'])} chars)")
if fixes["eslint_suggestions"]:
    print(f"  🧠 ESLint suggestions: {len(fixes['eslint_suggestions'])}")
if not fixes["raw_patch"] and not fixes["eslint_suggestions"]:
    print("⚠️ No fixes found.")
