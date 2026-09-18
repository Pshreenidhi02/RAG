 
import datetime as dt
import os
import uuid
 
from gdrive_setup import drive_state
from gdrive_setup.google_drive import (
    credentials_available,
    folder_id,
    get_drive_service,
    service_account_email,
)
 
 
def public_base_url():
    return (os.getenv("GOOGLE_DRIVE_PUBLIC_BASE_URL") or "").strip().rstrip("/")
 
 
def webhook_token():
    return (os.getenv("GOOGLE_DRIVE_WEBHOOK_TOKEN") or "").strip()
 
 
def webhook_url():
    """Built in one place, so the URL registered with Google and the route
    the app serves cannot drift apart."""
    return f"{public_base_url()}/webhooks/google-drive?token={webhook_token()}"
 
 
def _expiration_iso(expiration):
    """Google returns expiration as epoch milliseconds, as a string."""
    if not expiration:
        return None
 
    try:
        seconds = int(expiration) / 1000
    except (TypeError, ValueError):
        return str(expiration)
 
    return dt.datetime.fromtimestamp(seconds, tz=dt.timezone.utc).isoformat()
 
 
def _seconds_left(expiration):
    if not expiration:
        return None
 
    try:
        seconds = int(expiration) / 1000
    except (TypeError, ValueError):
        return None
 
    now = dt.datetime.now(tz=dt.timezone.utc).timestamp()
    return int(seconds - now)
 
 
def setup_drive_watch():
    base = public_base_url()
    token = webhook_token()
 
    missing = [
        name
        for name, value in (
            ("GOOGLE_DRIVE_PUBLIC_BASE_URL", base),
            ("GOOGLE_DRIVE_WEBHOOK_TOKEN", token),
        )
        if not value
    ]
 
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")
 
    # Google validates the URL synchronously during registration. It must be
    # publicly reachable over HTTPS with a valid certificate - localhost and
    # self-signed certs are both rejected.
    if not base.startswith("https://"):
        raise RuntimeError(
            "GOOGLE_DRIVE_PUBLIC_BASE_URL must be an https origin "
            "(use ngrok or a real domain). Google will not deliver "
            "webhooks to http or localhost."
        )
 
    target = folder_id()
 
    service = get_drive_service()
 
    # Mark our position in the changes feed now, so the channel reports only
    # what happens from here on.
    start_token = (
        service.changes()
        .getStartPageToken(supportsAllDrives=True)
        .execute()["startPageToken"]
    )
 
    channel_id = str(uuid.uuid4())
 
    body = {
        "id": channel_id,
        "type": "web_hook",
        "address": webhook_url(),
        "token": token,
    }
 
    result = (
        service.changes()
        .watch(
            pageToken=start_token,
            body=body,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
 
    channel = {
        "channel_id": result.get("id", channel_id),
        # resourceId is REQUIRED to stop the channel later.
        "resource_id": result.get("resourceId"),
        "expiration": result.get("expiration"),
        "expiration_iso": _expiration_iso(result.get("expiration")),
        "address": webhook_url(),
        "folder_id": target,
        "created_at": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
    }
 
    drive_state.set_channel(channel)
 
    print("Google Drive watch created:", channel["channel_id"])
 
    return {"status": "subscribed", "channel": channel}
 
 
def stop_drive_watch():
    channel = drive_state.get_channel()
 
    if not channel:
        return {"status": "no active channel"}
 
    try:
        get_drive_service().channels().stop(
            body={
                "id": channel["channel_id"],
                "resourceId": channel.get("resource_id"),
            }
        ).execute()
    except Exception as error:
        print("Channel stop failed (clearing state anyway):", error)
 
    drive_state.set_channel(None)
 
    return {"status": "stopped", "channel_id": channel["channel_id"]}
 
 
def drive_status():
    channel = drive_state.get_channel()
    state = drive_state.get_state()
 
    remaining = _seconds_left((channel or {}).get("expiration"))
 
    return {
        "config": {
            "folder_id": (os.getenv("GOOGLE_DRIVE_FOLDER_ID") or "").strip()
            or None,
            "credentials_found": credentials_available(),
            # Share the Drive folder with THIS address.
            "service_account_email": service_account_email(),
            "public_base_url": public_base_url() or None,
            # A boolean, never the token itself - status output gets pasted
            # into tickets and screenshots.
            "webhook_token_set": bool(webhook_token()),
        },
        "watch_active": bool(channel) and (remaining or 0) > 0,
        "channel": channel,
        "expires_in_hours": (
            round(remaining / 3600, 1) if remaining is not None else None
        ),
        "tracked_files": len(state.get("files") or {}),
        "note": (
            "Channels last about 7 days. POST /admin/google-drive/watch "
            "again to renew."
        ),
    }
 