import os
from typing import List

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Fallback: simple rule-based summary if no API key set

def simple_tldr(text: str) -> str:
    import re
    txt = " ".join(text.split())[:500]
    # naive meeting pattern
    if "meet" in txt.lower():
        who = None
        m = re.search(r"(?:I'm|I am|This is|Hi,? my name is)\s+([A-Za-z][A-Za-z .'-]{1,40})", txt, re.I)
        if m:
            who = m.group(1).strip()
        tm = re.search(r"(\d{1,2})(?::(\d{2}))?\s?(am|pm)?", txt, re.I)
        when = "tomorrow" if "tomorrow" in txt.lower() else None
        if who and tm and when:
            hh = tm.group(1)
            mm = tm.group(2) or "00"
            ampm = tm.group(3) or ""
            return f"Meeting with {who} {when} at {hh}:{mm}{ampm}".strip()
    # default: first sentence
    s = re.split(r"[.!?]", txt)
    return (s[0].strip() or txt[:80])[:120]


def tldr(text: str) -> str:
    if not OPENAI_API_KEY:
        return simple_tldr(text)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = (
            "Summarize this email in 1 short, specific bullet (<=18 words). "
            "Prefer who+what+when. If a meeting is proposed, format like 'Meeting with <name> <date/relative> at <time>'.\n\n" + text
        )
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=80,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return simple_tldr(text)


def summarize_threads(bullets: List[str]) -> List[str]:
    # simple reduce: deduplicate by lowercase and keep top 8
    seen = set()
    out = []
    for b in bullets:
        k = b.lower()
        if k in seen: continue
        seen.add(k)
        out.append(b)
        if len(out) >= 8: break
    return out
