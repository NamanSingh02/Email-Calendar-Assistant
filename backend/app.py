from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
import os, uuid
from typing import List, Dict

from db import init_db, get_session
from models import Message, Task, Evidence
from oauth import start_auth, finish_auth
from gmail_api import gmail_query_between, list_message_ids, get_message_meta
from calendar_api import list_events
from llm import tldr, summarize_threads


load_dotenv()

app = FastAPI(title="Email-Calendar-Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGIN", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

@app.get("/health")
def health():
    return {"ok": True}

# ---- OAuth ----
@app.get("/auth/google/start")
def auth_start():
    auth_url, state = start_auth()
    return {"auth_url": auth_url, "state": state}

@app.get("/auth/google/callback")
def auth_callback(request: Request):
    params = dict(request.query_params)
    if "state" not in params or "code" not in params:
        raise HTTPException(400, "Missing state or code")
    finish_auth(params["state"], params["code"])
    return RedirectResponse(url=os.getenv("ALLOWED_ORIGIN"))
@app.get("/auth/status")
def auth_status():
    from oauth import is_connected
    return {"connected": is_connected()}

@app.post("/auth/logout")
def auth_logout():
    from oauth import logout
    logout()
    return {"ok": True}

# ---- Milestone 1: basic pulls ----
@app.get("/calendar/sample")
def cal_sample():
    return {"events": list_events()}

# ---- Milestone 2: per-email tl;dr + date-range summary ----
@app.get("/emails/range")
def emails_in_range(start: str, end: str, max_results: int = 50):
    q = gmail_query_between(start, end)
    ids = list_message_ids(q, max_results or 200)
    msgs = [get_message_meta(i) for i in ids]
    # store minimal copy
    with get_session() as s:
        for m in msgs:
            if not m.get("id"): continue
            row = Message(
                id=m["id"], thread_id=m.get("thread_id"), subject=m.get("subject"),
                from_email=m.get("from_email"), body_text=m.get("body_text")
            )
            s.merge(row)
        s.commit()
    # include body_text so the UI can summarize without prompting
    return {
        "count": len(msgs),
        "messages": [
            {
                "id": m.get("id"),
                "thread_id": m.get("thread_id"),
                "subject": m.get("subject"),
                "from_email": m.get("from_email"),
                "body_text": (m.get("body_text") or "")[:20000]  # safety cap
            }
            for m in msgs
        ]
    }

    

@app.post("/summarize/email")
def summarize_email(payload: Dict[str, str]):
    text = payload.get("text")
    if not text:
        raise HTTPException(400, "Missing 'text'")
    return {"tldr": tldr(text)}

@app.get("/summary")
def date_range_summary(start: str, end: str, max_results: int = 50):
    q = gmail_query_between(start, end)
    ids = list_message_ids(q, max_results)
    msgs = [get_message_meta(i) for i in ids]
    bullets = []
    for m in msgs:
        tl = tldr(m.get("body_text") or (m.get("subject") or ""))
        subj = m.get("subject") or "(no subject)"
        bullets.append(f"{tl} — {subj}")
    highlights = summarize_threads(bullets)
    return {"highlights": highlights, "count": len(msgs)}

# ---- Milestone 3: action-item extraction (lightweight) ----
@app.post("/extract/actions")
def extract_actions(payload: Dict[str, str]):
    import re, uuid
    from datetime import datetime, timedelta

    text = (payload.get("text") or "").strip()
    if not text:
        return {"tasks": []}

    # --- helpers ---
    def clean(txt: str) -> str:
        lines = [ln.strip() for ln in txt.splitlines()]
        out = []
        for ln in lines:
            low = ln.lower()
            if low.startswith(">"):  # quoted
                continue
            if low in ("thanks", "thanks,", "regards,", "best,", "--"):
                break
            out.append(ln)
        return " ".join(" ".join(out).split())

    def find_due(txt: str) -> str | None:
        # by Oct 7 / by 10/07 / by 2025-10-07 / by friday / by tomorrow
        m = re.search(r"\bby\s+([A-Za-z]{3,9}\s+\d{1,2}|\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2}|tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|eod|eow)\b", txt, re.I)
        return m.group(1) if m else None

    def find_time(txt: str) -> str | None:
        m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s?(am|pm)\b", txt, re.I)  # 12h
        if m: return f"{m.group(1)}:{m.group(2) or '00'}{m.group(3).lower()}"
        m = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", txt)             # 24h
        if m: return f"{m.group(1)}:{m.group(2)}"
        return None

    txt = clean(text)

    tasks = []

    # ---- 1) Request-type tasks (send/share/provide/attach/etc.) ----
    # Capture verb + short object phrase (until punctuation or "by")
    req = re.finditer(r"\b(send|share|deliver|provide|attach|update|review|confirm|approve|upload)\b\s+([^.;:\n]{3,80})", txt, re.I)
    for m in req:
        verb = m.group(1).lower()
        obj = " ".join(m.group(2).split())
        # If phrase contains 'by ...', trim object at 'by'
        obj = re.split(r"\bby\b", obj, flags=re.I)[0].strip()
        due = find_due(txt)
        title = f"{verb.capitalize()} {obj}".strip()
        if due:
            title = f"{title} by {due}"
        # Confidence heuristic: +0.15 if due date present
        conf = 0.6 + (0.15 if due else 0.0)
        tasks.append({
            "id": str(uuid.uuid4()),
            "title": title[:120],
            "assignee": "me",
            "due_iso": due,
            "confidence": round(min(conf, 0.95), 2),
        })

    # ---- 2) Meeting/scheduling tasks ----
    if re.search(r"\b(meet|meeting|sync|chat|call|review|catch[- ]?up|discuss)\b", txt, re.I):
        when = None
        # relative phrases or dates
        m_rel = re.search(r"\b(tomorrow|today|tonight|monday|tuesday|wednesday|thursday|friday|saturday|sunday|next week|this week)\b", txt, re.I)
        if m_rel: when = m_rel.group(1).lower()
        # explicit dates (Oct 7 / 10/07 / 2025-10-07)
        if not when:
            m_date = re.search(r"\b((jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2}|\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2})\b", txt, re.I)
            if m_date: when = m_date.group(1)
        tm = find_time(txt)
        purpose = None
        m_purp = re.search(r"\b(discuss|review)\s+([^.;:\n]{3,60})", txt, re.I)
        if m_purp: purpose = m_purp.group(2).strip()
        title_parts = ["Schedule meeting"]
        if when: title_parts.append(when)
        if tm:   title_parts.append(f"at {tm}")
        if purpose: title_parts.append(f"to {purpose}")
        title = " ".join(title_parts)
        tasks.append({
            "id": str(uuid.uuid4()),
            "title": title[:120],
            "assignee": "me",
            "due_iso": when,  # keep as phrase for MVP
            "confidence": 0.6 + (0.1 if tm else 0.0),
        })

    return {"tasks": tasks}

