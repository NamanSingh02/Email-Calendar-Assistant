from googleapiclient.discovery import build
from oauth import get_creds
from datetime import datetime, timedelta


def list_message_ids(q: str, max_results: int = 200):
    """
    Fetches up to max_results message IDs across pages.
    """
    service = build("gmail", "v1", credentials=get_creds())
    ids = []
    page_token = None
    while True:
        call = service.users().messages().list(
            userId="me",
            q=q,
            maxResults=min(100, max_results - len(ids)),  # Gmail page cap
            pageToken=page_token,
            includeSpamTrash=False,
        )
        res = call.execute()
        ids.extend([m["id"] for m in res.get("messages", [])])
        page_token = res.get("nextPageToken")
        if not page_token or len(ids) >= max_results:
            break
    return ids[:max_results]



def get_message_meta(msg_id: str):
    service = build("gmail", "v1", credentials=get_creds())
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    payload = msg.get("payload", {})
    headers = payload.get("headers", [])
    h = {x["name"].lower(): x["value"] for x in headers}
    subject = h.get("subject")
    from_email = h.get("from")
    date = h.get("date")
    # naive body extraction (MVP)
    body = ""
    if payload.get("parts"):
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                import base64
                body += base64.urlsafe_b64decode(part["body"]["data"]).decode(errors="ignore") + "\n"
    else:
        if payload.get("body", {}).get("data"):
            import base64
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode(errors="ignore")
    return {
        "id": msg_id,
        "thread_id": msg.get("threadId"),
        "subject": subject,
        "from_email": from_email,
        "sent_at": date,
        "body_text": body,
    }



def gmail_query_between(start_yyyy_mm_dd: str, end_yyyy_mm_dd: str):
    """
    Gmail uses before: (exclusive). We add +1 day to end to make it inclusive.
    """
    start = start_yyyy_mm_dd.replace("-", "/")
    # add one day to end so emails on the end date are included
    end_dt = datetime.strptime(end_yyyy_mm_dd, "%Y-%m-%d") + timedelta(days=1)
    end_inc = end_dt.strftime("%Y/%m/%d")
    return f"after:{start} before:{end_inc}"

