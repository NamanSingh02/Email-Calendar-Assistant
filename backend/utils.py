from datetime import datetime

def to_iso(date_str):
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return None
