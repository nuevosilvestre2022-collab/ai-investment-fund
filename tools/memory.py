import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
# En Render el disco es efímero. Usamos /tmp que sobrevive reinicios de proceso (no de deploy).
# Localmente usamos config/memory.json como siempre.
_IS_RENDER = os.environ.get("RENDER") == "true"
MEMORY_FILE = Path("/tmp/memory.json") if _IS_RENDER else BASE_DIR / "config" / "memory.json"
MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)


def get_memory() -> list:
    """Returns a list of learned facts/preferences."""
    if not MEMORY_FILE.exists():
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def add_memory(fact: str) -> bool:
    """Appends a new fact to the long-term memory JSON."""
    mem = get_memory()
    if fact not in mem:
        mem.append(fact)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, indent=4, ensure_ascii=False)
        return True
    return False

def clear_memory():
    if MEMORY_FILE.exists():
        MEMORY_FILE.unlink()
