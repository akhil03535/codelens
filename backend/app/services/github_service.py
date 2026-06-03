import io
import logging
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import List, Tuple

from app.config.settings import settings
from app.utils.helpers import is_binary_file

logger = logging.getLogger(__name__)


import io
import logging
import shutil
import subprocess
import time
import zipfile
from pathlib import Path
from typing import List, Tuple

from app.config.settings import settings
from app.utils.helpers import is_binary_file

logger = logging.getLogger(__name__)


def clone_github_repo(github_url: str, repo_id: str, retry_count: int = 0) -> Path:
    """Clone a GitHub repository with Windows compatibility and retry logic."""
    repo_dir = settings.REPOSITORIES_PATH / repo_id
    if repo_dir.exists():
        shutil.rmtree(repo_dir, ignore_errors=True)
    repo_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Use --bare and --mirror for better Windows compatibility
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--single-branch", "--no-tags", "--quiet", github_url, str(repo_dir)],
            capture_output=True, text=True, timeout=180, cwd=str(settings.REPOSITORIES_PATH)
        )
        
        # Even if returncode != 0, check if files were actually cloned
        if result.returncode != 0:
            # Check if repository has any files (cloning succeeded despite warning)
            files_exist = any(repo_dir.iterdir())
            if not files_exist:
                err = result.stderr.strip() or result.stdout.strip()
                # Retry once on transient failures
                if retry_count < 1 and ("timeout" in err.lower() or "connection" in err.lower()):
                    time.sleep(1)
                    logger.warning(f"Retrying clone for {repo_id} after transient error")
                    return clone_github_repo(github_url, repo_id, retry_count + 1)
                raise RuntimeError(f"Git clone failed: {err[:200]}")
            else:
                logger.warning(f"Clone had warnings but files exist: {result.stderr[:100]}")
        
        # Verify repository is valid (has .git or files)
        if not any(repo_dir.iterdir()):
            raise RuntimeError("Clone succeeded but repository is empty")
            
    except subprocess.TimeoutExpired:
        cleanup_repo(repo_id)
        raise RuntimeError("Clone timed out (3 min limit). Repository may be too large.")
    except FileNotFoundError:
        raise RuntimeError("Git not found in PATH. Please install Git.")
    except Exception as e:
        cleanup_repo(repo_id)
        raise

    return repo_dir


def extract_zip(zip_bytes: bytes, repo_id: str) -> Path:
    repo_dir = settings.REPOSITORIES_PATH / repo_id
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    repo_dir.mkdir(parents=True)

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            # Security: check for path traversal
            for member in zf.namelist():
                if ".." in member or member.startswith("/"):
                    raise ValueError(f"Unsafe zip path: {member}")
            zf.extractall(repo_dir)
    except zipfile.BadZipFile:
        raise ValueError("Invalid ZIP file")

    # If zip contains a single top-level folder, use it as root
    entries = list(repo_dir.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]

    return repo_dir


def scan_files(repo_dir: Path) -> List[Tuple[str, str]]:
    """Scan repo for supported source files. Returns (relative_path, content) tuples."""
    supported = set(settings.SUPPORTED_EXTENSIONS)
    ignored = set(settings.IGNORED_DIRS)
    results = []

    for fpath in repo_dir.rglob("*"):
        if not fpath.is_file():
            continue

        rel = fpath.relative_to(repo_dir)
        # Skip if any directory component is in ignored list
        if any(part in ignored for part in rel.parts):
            continue

        if fpath.suffix.lower() not in supported:
            continue

        if is_binary_file(fpath):
            continue

        size = fpath.stat().st_size
        if size > settings.MAX_FILE_SIZE_KB * 1024:
            logger.warning(f"Skipping large file ({size//1024}KB): {rel}")
            continue

        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
            if content.strip():
                results.append((str(rel).replace("\\", "/"), content))
        except (IOError, OSError) as e:
            logger.warning(f"Cannot read {rel}: {e}")

    logger.info(f"Scanned {len(results)} source files in {repo_dir}")
    return results


def cleanup_repo(repo_id: str) -> None:
    """Clean up repository directory. Handles Windows file locking."""
    path = settings.REPOSITORIES_PATH / repo_id
    if path.exists():
        try:
            shutil.rmtree(path, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Failed to clean up {path}: {e}. Will retry on next cleanup.")
            # On Windows, sometimes need to wait for file locks to release
            try:
                time.sleep(0.5)
                shutil.rmtree(path, ignore_errors=True)
            except Exception as e2:
                logger.warning(f"Retry cleanup also failed: {e2}")
