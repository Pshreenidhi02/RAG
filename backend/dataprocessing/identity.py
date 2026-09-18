import hashlib
import re
from pathlib import Path


def default_source_id(file_path):
    """Stable id for a document on disk, derived from its filename."""
    name = Path(file_path).name
    slug = re.sub(r"[^a-zA-Z0-9._-]", "_", name).strip("_")
    return slug or hashlib.sha1(str(file_path).encode()).hexdigest()[:16]