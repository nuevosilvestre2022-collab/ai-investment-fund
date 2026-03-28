import os
import shutil
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET_DIR = BASE_DIR / "version_plana"
if TARGET_DIR.exists():
    shutil.rmtree(TARGET_DIR)
TARGET_DIR.mkdir()

# Directories to search
DIRS = ["tools", "reports", "agents", "config", "notifications", "."]

py_files = []
for d in DIRS:
    p = BASE_DIR / d
    if not p.exists(): continue
    for f in os.listdir(p):
        if f.endswith(".py") and f != "flatten_for_github.py":
            py_files.append(p / f)

# Also copy requirements.txt
req_path = BASE_DIR / "requirements.txt"
if req_path.exists():
    shutil.copy(req_path, TARGET_DIR / "requirements.txt")

# Regex to find imports like: from tools.financial_data import ...
# Or: import tools.financial_data
prefix_pattern = re.compile(r'^(from|import)\s+(tools|reports|agents|config|notifications)\.')

for filepath in py_files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Rewrite paths in OS (like BASE_DIR / "output")
    # In flat version, base_dir is just the current directory
    content = content.replace('BASE_DIR = Path(__file__).parent.parent', 'BASE_DIR = Path(__file__).parent')

    new_lines = []
    for line in content.split("\n"):
        if prefix_pattern.search(line):
            # Replace 'from tools.xyz' -> 'from xyz'
            line = re.sub(r'^(from)\s+(?:tools|reports|agents|config|notifications)\.', r'\1 ', line)
            # Replace 'import tools.xyz' -> 'import xyz'
            line = re.sub(r'^(import)\s+(?:tools|reports|agents|config|notifications)\.', r'\1 ', line)
            
            # If the import was aliased or something, the above regex handles the basic cases safely
        new_lines.append(line)
        
    out_path = TARGET_DIR / filepath.name
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))

print(f"Successfully flattened {len(py_files)} files into {TARGET_DIR}")
