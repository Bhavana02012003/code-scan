import sys, json, re

patch_file = sys.argv[1]
out_file = sys.argv[2]

fixes = {}
current_file = None
current_line = None
patch_block = []

with open(patch_file, encoding="utf-8") as f:
    for line in f:
        if line.startswith('+++ b/'):
            if current_file and patch_block:
                fixes[current_file] = fixes.get(current_file, []) + patch_block
            current_file = line.strip().replace('+++ b/', '')
            patch_block = []
        elif line.startswith('@@'):
            m = re.search(r'\+(\d+)', line)
            if m:
                current_line = int(m.group(1))
        elif line.startswith('+') or line.startswith('-'):
            patch_block.append({
                "line": current_line,
                "patch": line.strip()
            })
        elif current_file and patch_block and line.strip() == '':
            fixes[current_file] = fixes.get(current_file, []) + patch_block
            patch_block = []

if current_file and patch_block:
    fixes[current_file] = fixes.get(current_file, []) + patch_block

with open(out_file, "w", encoding="utf-8") as f:
    json.dump(fixes, f, indent=2)
