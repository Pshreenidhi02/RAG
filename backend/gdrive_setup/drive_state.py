
import json
import threading
 
from gdrive_setup.google_drive import PROJECT_ROOT
 
 
STATE_FILE = PROJECT_ROOT / "data" / "state" / "drive_state.json"
 
_lock = threading.Lock()
 
_EMPTY = {"channel": None, "files": {}}
 
 
def _read():
    if not STATE_FILE.exists():
        return dict(_EMPTY)
 
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        print("Drive state unreadable, starting fresh:", error)
        return dict(_EMPTY)
 
    for key, value in _EMPTY.items():
        data.setdefault(key, value)
 
    return data
 
 
def _write(data):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
 
    temp_file = STATE_FILE.with_suffix(".tmp")
    temp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
 
    # Atomic on POSIX: a crash mid-write cannot leave truncated JSON.
    temp_file.replace(STATE_FILE)
 
 
def get_state():
    with _lock:
        return _read()
 
 
def set_channel(channel):
    with _lock:
        data = _read()
        data["channel"] = channel
        _write(data)
 
 
def get_channel():
    return get_state().get("channel")
 
 
def fingerprint(drive_file):
    """md5 changes only when the bytes change, so a rename does not
    trigger re-ingestion. Google-native files have no md5, hence the
    fallback."""
    return (
        drive_file.get("md5Checksum")
        or drive_file.get("modifiedTime")
        or ""
    )
 
 
def is_new_or_updated(drive_file):
    file_id = drive_file.get("id")
 
    if not file_id:
        return False
 
    known = get_state()["files"].get(file_id)
 
    if not known:
        return True
 
    return known.get("fingerprint") != fingerprint(drive_file)
 
 
def mark_processed(drive_file):
    file_id = drive_file.get("id")
 
    if not file_id:
        return
 
    with _lock:
        data = _read()
        data["files"][file_id] = {
            "name": drive_file.get("name"),
            "fingerprint": fingerprint(drive_file),
            "modifiedTime": drive_file.get("modifiedTime"),
        }
        _write(data)
 
 
def forget(file_id):
    """Drop a file's record so re-adding it to Drive ingests it again."""
    with _lock:
        data = _read()
        data["files"].pop(file_id, None)
        _write(data)