import csv, sys, os

out_rows = []
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
                "Message": row.get("Description", "")   # 👈 key fix here
            })

with open(sys.argv[2], "w", newline='', encoding='utf-8') as out:
    writer = csv.DictWriter(out, fieldnames=["Tool","File","Line","Severity","Rule","Message"])
    writer.writeheader()
    writer.writerows(out_rows)
