import hashlib
import re
from pathlib import Path


def extract_repo_name(github_url: str) -> str:
    cleaned = github_url.rstrip("/").rstrip(".git")
    parts = cleaned.split("/")
    return "/".join(parts[-2:]) if len(parts) >= 2 else parts[-1]


def generate_repo_id(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


def is_binary_file(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return b"\x00" in f.read(8192)
    except (IOError, OSError):
        return True


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", text.lower().strip())[:50]
