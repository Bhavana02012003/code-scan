import csv
import sys
import os
import json
import re

# =======================================================
# Initialize combined results
# =======================================================
out_rows = []

# =======================================================
# 1. Parse Salesforce PMD (Apex)
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
# 2. Parse Salesforce LWC ESLint
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
# 3. Parse .NET dotnet-format results
# =======================================================
dotnet_format = os.path.join(sys.argv[1], "dotnet-format.json")
if os.path.exists(dotnet_format):
    try:
        data = json.load(open(dotnet_format, encoding="utf-8"))
    except Exception as e:
        data = None
        print("dotnet-format parse error:", e)

    def field(d, *names, default=None):
        for n in names:
            if isinstance(d, dict) and n in d:
                return d.get(n)
        return default

    def add_diag(v):
        out_rows.append({
            "Tool": ".NET(format)",
            "File": field(v, "FilePath", "file", "Document"),
            "Line": field(v, "LineNumber", "line", "StartLine"),
            "Severity": field(v, "Severity", "severity", "Category"),
            "Rule": field(v, "RuleId", "id", "DiagnosticId", "rule"),
            "Message": field(v, "Message", "message", "Title")
        })

    if isinstance(data, dict):
        for v in (data.get("Diagnostics") or data.get("violations") or data.get("results") or []):
            add_diag(v)
    elif isinstance(data, list):
        for v in data:
            add_diag(v)

# =======================================================
# 4. Parse .NET build_output.txt
# =======================================================
build_output = os.path.join(sys.argv[1], "build_output.txt")
if os.path.exists(build_output):
    rx = re.compile(r'(.+\.cs)\((\d+),\d+\): (warning|error) (\w+): (.+?) \[')
    for line in open(build_output, encoding="utf-8", errors="ignore"):
        m = rx.search(line)
        if m:
            file, l, sev, rule, msg = m.groups()
            out_rows.append({
                "Tool": ".NET(build)",
                "File": file,
                "Line": l,
                "Severity": sev.capitalize(),
                "Rule": rule,
                "Message": msg
            })

# =======================================================
# 5. Parse .NET NuGet vulnerability packages
# =======================================================
dotnet_pkg = os.path.join(sys.argv[1], "dotnet-packages.json")
if os.path.exists(dotnet_pkg):
    try:
        data = json.load(open(dotnet_pkg, encoding="utf-8"))
        for proj in data.get("projects", []):
            for fw in proj.get("frameworks", []):
                for section in ("topLevelPackages", "transitivePackages"):
                    for pkg in fw.get(section, []) or []:
                        for v in (pkg.get("vulnerabilities") or []):
                            out_rows.append({
                                "Tool": ".NET(pkg)",
                                "File": f'{pkg.get("id")}@{pkg.get("requestedVersion") or pkg.get("resolvedVersion")}',
                                "Line": "",
                                "Severity": v.get("severity"),
                                "Rule": v.get("advisoryUrl") or ",".join(v.get("advisoryIds") or []),
                                "Message": v.get("description") or "NuGet dependency vulnerability"
                            })
    except Exception as e:
        print("dotnet-packages parse error:", e)

# =======================================================
# 6. Parse Python Bandit
# =======================================================
bandit_file = os.path.join(sys.argv[1], "bandit.json")
if os.path.exists(bandit_file):
    try:
        data = json.load(open(bandit_file, encoding="utf-8"))
        for result in data.get("results", []):
            out_rows.append({
                "Tool": "Bandit",
                "File": result.get("filename", ""),
                "Line": result.get("line_number", ""),
                "Severity": result.get("issue_severity", ""),
                "Rule": result.get("test_id", ""),
                "Message": result.get("issue_text", "")
            })
    except Exception as e:
        print("bandit parse error:", e)

# =======================================================
# 7. Parse Python Pylint
# =======================================================
pylint_file = os.path.join(sys.argv[1], "pylint.json")
if os.path.exists(pylint_file):
    try:
        data = json.load(open(pylint_file, encoding="utf-8"))
        if isinstance(data, list):
            for it in data:
                out_rows.append({
                    "Tool": "Pylint",
                    "File": it.get("path", ""),
                    "Line": it.get("line", ""),
                    "Severity": (it.get("type") or "").capitalize(),
                    "Rule": it.get("message-id", ""),
                    "Message": it.get("message", "")
                })
    except Exception as e:
        print("pylint parse error:", e)

# =======================================================
# 8. Parse Python Flake8
# =======================================================
flake8_file = os.path.join(sys.argv[1], "flake8.json")
if os.path.exists(flake8_file):
    try:
        data = json.load(open(flake8_file, encoding="utf-8"))
        for file, issues in data.items():
            for i in issues:
                out_rows.append({
                    "Tool": "Flake8",
                    "File": file,
                    "Line": i.get("line_number", ""),
                    "Severity": i.get("code", ""),
                    "Rule": i.get("code", ""),
                    "Message": i.get("text", "")
                })
    except Exception as e:
        print("flake8 parse error:", e)

# =======================================================
# 9. Write Final Combined CSV
# =======================================================
output_path = sys.argv[2]
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w", newline='', encoding='utf-8') as out:
    writer = csv.DictWriter(out, fieldnames=["Tool", "File", "Line", "Severity", "Rule", "Message"])
    writer.writeheader()
    writer.writerows(out_rows)

print(f"✅ Normalized report written: {output_path} ({len(out_rows)} rows)")

# =======================================================
# 10. Parse Java PMD
# =======================================================
pmd_java_file = os.path.join(sys.argv[1], "pmd_java.csv")
if os.path.exists(pmd_java_file):
    with open(pmd_java_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            out_rows.append({
                "Tool": "PMD(Java)",
                "File": row.get("File", ""),
                "Line": row.get("Line", ""),
                "Severity": row.get("Priority", ""),
                "Rule": row.get("Rule", ""),
                "Message": row.get("Description", "")
            })


# =======================================================
# 11. Parse React ESLint
# =======================================================
eslint_react_file = os.path.join(sys.argv[1], "eslint.json")
if os.path.exists(eslint_react_file):
    try:
        data = json.load(open(eslint_react_file, encoding="utf-8"))
        if isinstance(data, dict):
            data = [data]
        for f in data:
            fn = f.get("filePath")
            for m in f.get("messages", []):
                sev = "Error" if m.get("severity") == 2 else "Warning"
                out_rows.append({
                    "Tool": "ESLint(React)",
                    "File": fn,
                    "Line": m.get("line", ""),
                    "Severity": sev,
                    "Rule": m.get("ruleId", ""),
                    "Message": m.get("message", "")
                })
    except Exception as e:
        print("eslint-react parse error:", e)

# =======================================================
# 12. Parse React TSC output
# =======================================================
tsc_file = os.path.join(sys.argv[1], "tsc-output.txt")
if os.path.exists(tsc_file):
    rx = re.compile(r"(.+\.(?:ts|tsx|js|jsx))\((\d+),\d+\): (error|warning) (TS\d+): (.+)")
    for line in open(tsc_file, encoding="utf-8", errors="ignore"):
        m = rx.search(line)
        if m:
            file, l, sev, code, msg = m.groups()
            out_rows.append({
                "Tool": "TSC",
                "File": file,
                "Line": l,
                "Severity": sev.capitalize(),
                "Rule": code,
                "Message": msg
            })

# =======================================================
# 13. Parse npm-audit vulnerabilities
# =======================================================
audit_file = os.path.join(sys.argv[1], "audit.json")
if os.path.exists(audit_file):
    try:
        data = json.load(open(audit_file, encoding="utf-8"))
        for pkg, v in (data.get("vulnerabilities") or {}).items():
            for via in v.get("via", []):
                if isinstance(via, dict):
                    out_rows.append({
                        "Tool": "npm-audit",
                        "File": pkg,
                        "Line": "",
                        "Severity": v.get("severity", ""),
                        "Rule": via.get("name") or via.get("title"),
                        "Message": via.get("title") or ""
                    })
    except Exception as e:
        print("npm-audit parse error:", e)

