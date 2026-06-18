#!/usr/bin/env python3
"""Move all temporary scripts to _archive/ folder."""
import os, shutil, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.path.join(BASE, "_archive")
os.makedirs(ARCHIVE, exist_ok=True)

# Files that ARE part of the project - DO NOT MOVE
KEEP = {
    ".clinerules",
    "INFRASTRUCTURE_MAP.md",
    "MODEL_CATALOG.md",
    "PROJECT_REGISTRY.md",
    "SERVER_GPU_MAP.md",
    "package.json",
    "README.md",
    "ai-hub-studio",
    "ai-hub-gateway",
    "clinerules-templates",
    "_archive",
    ".git",
    ".gitignore",
    "node_modules",
    "__pycache__",
}

moved = 0
for item in os.listdir(BASE):
    if item in KEEP:
        continue
    src = os.path.join(BASE, item)
    dst = os.path.join(ARCHIVE, item)
    if os.path.isfile(src) or os.path.isdir(src):
        # Skip this script itself
        if item == os.path.basename(__file__):
            continue
        try:
            shutil.move(src, dst)
            moved += 1
            print(f"  Moved: {item}")
        except Exception as e:
            print(f"  SKIP {item}: {e}")

print(f"\nMoved {moved} items to _archive/")
print("Remaining in root:")
for item in sorted(os.listdir(BASE)):
    print(f"  {item}")