import csv
import sys
import os
import json

out_rows = []

# =======================================================
# 1. Parse Apex PMD CSV
# =======================================================
pmd_file = os.path.join(sys.argv[1], "pmd.csv")
if os.path.exists(pmd_file):
    with open(pmd_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            out_rows.append({
                "Tool": "PMD(Apex)",
                "File": row.get("File", ""),
                "Line": row.get("Line", ""),
                "Severity": row.get("Priority", ""),
                "Rule": row.get("Rule", ""),
                "Message": row.get("Description", "")
            })

# =======================================================
# 2. Parse LWC ESLint JSON
# =======================================================
eslint_file = os.path.join(sys.argv[1], "eslint_lwc.json")
if os.path.exists(eslint_file):
    with open(eslint_file, encoding='utf-8') as f:
        try:
            eslint_data = json.load(f)
        except json.JSONDecodeError:
            eslint_data = []

    for file_result in eslint_data:
        file_path = file_result.get("filePath", "")
        for msg in file_result.get("messages", []):
            out_rows.append({
                "Tool": "ESLint(LWC)",
                "File": file_path,
                "Line": msg.get("line", ""),
                "Severity": str(msg.get("severity", "")),
                "Rule": msg.get("ruleId", ""),
                "Message": msg.get("message", "")
            })

# =======================================================
# 3. Write Combined Output
# =======================================================
with open(sys.argv[2], "w", newline='', encoding='utf-8') as out:
    writer = csv.DictWriter(out, fieldnames=["Tool", "File", "Line", "Severity", "Rule", "Message"])
    writer.writeheader()
    writer.writerows(out_rows)



# =======================================================
# 4. Parse DotNet Analyzer JSON
# =======================================================
dotnet_file = os.path.join(sys.argv[1], "dotnet.json")
if os.path.exists(dotnet_file):
    with open(dotnet_file, encoding='utf-8') as f:
        try:
            dotnet_data = json.load(f)
        except json.JSONDecodeError:
            dotnet_data = []

    for entry in dotnet_data:
        out_rows.append({
            "Tool": "DotNetAnalyzer",
            "File": entry.get("File", ""),
            "Line": entry.get("Line", ""),
            "Severity": entry.get("Severity", ""),
            "Rule": entry.get("Rule", ""),
            "Message": entry.get("Message", "")
        })
