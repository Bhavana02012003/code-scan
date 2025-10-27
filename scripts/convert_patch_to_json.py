#!/usr/bin/env python3
import json
import os
import sys
import csv
import re

# CLI args
patch_file = sys.argv[1] if len(sys.argv) > 1 else "out/fixes.patch"
output_file = sys.argv[2] if len(sys.argv) > 2 else "out/fixes.json"

# Violation sources
pmd_file = "out/pmd.csv"
pmd_java_file = "out/pmd_java.csv"
eslint_fixes_file = "out/eslint-fixes.json"

fixes = {
    "raw_patch": "",
    "fix_suggestions": [],
    "eslint_suggestions": []
}

# Load raw patch (unchanged)
if os.path.exists(patch_file) and os.path.getsize(patch_file) > 0:
    with open(patch_file, "r", encoding="utf-8", errors="ignore") as f:
        patch = f.read().strip()
        if patch:
            fixes["raw_patch"] = patch

# Helper
def read_file_lines(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.readlines()
    except:
        return []

# Fallback quick fix templates per rule
RULE_FIX_PATTERNS = {
    "AvoidDebugStatements": lambda old: re.sub(r"System\.debug\(.*\);?", "// removed debug", old),
    "DebugsShouldUseLoggingLevel": lambda old: re.sub(r"System\.debug\((.*)\);?", r"System.debug(LoggingLevel.INFO, \1);", old),
    "no-var": lambda old: old.replace("var ", "let "),
    "semi": lambda old: old.strip() + ";",
    "trailing-whitespace": lambda old: old.rstrip(),
}

def process_pmd_file(pmd_path):
    if not os.path.exists(pmd_path):
        return []
    results = []
    with open(pmd_path, newline='', encoding='utf-8') as vf:
        reader = csv.DictReader(vf)
        for row in reader:
            if row.get("File") and row.get("Line"):
                results.append({
                    "file": row["File"],
                    "line": int(row["Line"]),
                    "rule": row.get("Rule", ""),
                    "message": row.get("Description", "")
                })
    return results

violations = process_pmd_file(pmd_file) + process_pmd_file(pmd_java_file)

# Map code before/after
code_map_before = {}
code_map_after = {}
for v in violations:
    abs_path = os.path.join("target", v["file"].lstrip("./"))
    if abs_path not in code_map_before:
        code_map_before[abs_path] = read_file_lines(abs_path)
        code_map_after[abs_path] = read_file_lines(abs_path)

# Build suggestion for each violation
for v in violations:
    abs_path = os.path.join("target", v["file"].lstrip("./"))
    old_line = ""
    new_line = ""
    if len(code_map_before[abs_path]) >= v["line"]:
        old_line = code_map_before[abs_path][v["line"] - 1].rstrip()
    if len(code_map_after[abs_path]) >= v["line"]:
        new_line = code_map_after[abs_path][v["line"] - 1].rstrip()

    # Step 1: if fixer changed the line
    suggestion = new_line if new_line and new_line != old_line else ""

    # Step 2: fallback rule-based template
    if not suggestion and v["rule"] in RULE_FIX_PATTERNS:
        suggestion = RULE_FIX_PATTERNS[v["rule"]](old_line)

    # Step 3: fallback to original line if nothing else
    if not suggestion:
        suggestion = old_line

    fixes["fix_suggestions"].append({
        "file": v["file"],
        "line": v["line"],
        "rule": v["rule"],
        "old": old_line,
        "suggestion": suggestion,
        "message": v["message"]
    })

# ESLint fixes
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

# Write output
os.makedirs(os.path.dirname(output_file), exist_ok=True)
with open(output_file, "w", encoding="utf-8") as out:
    json.dump(fixes, out, indent=2)

print(f"✅ Wrote fixes to {output_file}")
print(f"  🧩 PMD suggestions: {len(fixes['fix_suggestions'])}")
print(f"  🧠 ESLint suggestions: {len(fixes['eslint_suggestions'])}")
