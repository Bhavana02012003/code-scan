import csv, json, os, sys

out_dir = sys.argv[1]
out_file = sys.argv[2]

rows = []

def add(tool, file, line, severity, rule, message):
    rows.append({
        "Tool": tool or "",
        "File": file or "",
        "Line": line or "",
        "Severity": severity or "",
        "Rule": rule or "",
        "Message": (message or "").replace("\n", " ")
    })

# ---- PMD ----
pmd_file = os.path.join(out_dir, "pmd.csv")
if os.path.exists(pmd_file):
    with open(pmd_file, encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for r in reader:
            add("PMD(Apex)", r.get("File"), r.get("Line"), r.get("Priority"), r.get("Rule"), r.get("Problem"))

# ---- ESLint ----
eslint_file = os.path.join(out_dir, "eslint.json")
if os.path.exists(eslint_file) and os.path.getsize(eslint_file) > 0:
    try:
        data = json.load(open(eslint_file))
        if isinstance(data, dict): data = [data]
        for file_entry in data:
            for m in file_entry.get("messages", []):
                add("ESLint", file_entry.get("filePath"), m.get("line"), str(m.get("severity")),
                    m.get("ruleId"), m.get("message"))
    except Exception as e:
        print("ESLint parse error:", e)

# ---- Python Bandit ----
bandit_file = os.path.join(out_dir, "bandit.json")
if os.path.exists(bandit_file):
    data = json.load(open(bandit_file))
    for r in data.get("results", []):
        add("Bandit", r.get("filename"), r.get("line_number"), r.get("issue_severity"), r.get("test_id"), r.get("issue_text"))

# ---- Python Pylint ----
pylint_file = os.path.join(out_dir, "pylint.json")
if os.path.exists(pylint_file):
    try:
        data = json.load(open(pylint_file))
        for r in data:
            add("Pylint", r.get("path"), r.get("line"), r.get("type"), r.get("message-id"), r.get("message"))
    except Exception as e:
        print("Pylint parse error:", e)

# ---- Python Flake8 ----
flake8_file = os.path.join(out_dir, "flake8.json")
if os.path.exists(flake8_file):
    try:
        data = json.load(open(flake8_file))
        for file_path, issues in data.items():
            for i in issues:
                add("Flake8", file_path, i.get("line_number"), i.get("code"), i.get("code"), i.get("text"))
    except Exception as e:
        print("Flake8 parse error:", e)

# ---- Write final CSV ----
os.makedirs(os.path.dirname(out_file), exist_ok=True)
with open(out_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Tool","File","Line","Severity","Rule","Message"])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print(f"✅ Wrote {len(rows)} violations to {out_file}")
