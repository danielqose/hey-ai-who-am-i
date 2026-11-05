"""Shared quiz scoring, Groq API calls, and experiment logging."""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

from types_meta import type_payload

load_dotenv(Path(__file__).with_name(".env"))

MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
RESULTS_CSV = Path(__file__).with_name("results.csv")


def groq_api_key() -> str:
    return (os.getenv("GROQ_API_KEY") or "").strip()

QUESTIONS = [
    ("I feel energized after spending time with a large group of people.", "EI", +1),
    ("I need time alone to recharge after a busy day.", "EI", -1),
    ("I start conversations with strangers easily.", "EI", +1),
    ("I prefer one-on-one talks over group discussions.", "EI", -1),
    ("I think out loud rather than keeping my thoughts to myself.", "EI", +1),
    ("I often prefer to observe before joining in.", "EI", -1),
    ("I focus more on facts and details than on big ideas.", "SN", +1),
    ("I enjoy imagining future possibilities.", "SN", -1),
    ("I trust practical experience more than theories.", "SN", +1),
    ("I often notice hidden patterns or connections between things.", "SN", -1),
    ("I prefer clear step-by-step instructions.", "SN", +1),
    ("I get bored with routine and want to try new approaches.", "SN", -1),
    ("In decisions, logic matters more to me than feelings.", "TF", +1),
    ("I often think about how a decision will affect others' emotions.", "TF", -1),
    ("I value honesty more than politeness.", "TF", +1),
    ("I find it hard to stay detached when a friend is upset.", "TF", -1),
    ("I'm more convinced by arguments than by personal stories.", "TF", +1),
    ("Being kind matters more to me than being right.", "TF", -1),
    ("I like to plan my work well before the deadline.", "JP", +1),
    ("I prefer to keep my options open instead of deciding early.", "JP", -1),
    ("A messy desk or schedule bothers me.", "JP", +1),
    ("I often work best in a last-minute rush.", "JP", -1),
    ("I make to-do lists and follow them.", "JP", +1),
    ("I'd rather improvise than follow a plan.", "JP", -1),
]

LETTERS = {"EI": "EI", "SN": "SN", "TF": "TF", "JP": "JP"}
DIM_LABELS = {
    "EI": ("Extraversion", "Introversion", "E", "I"),
    "SN": ("Sensing", "Intuition", "S", "N"),
    "TF": ("Thinking", "Feeling", "T", "F"),
    "JP": ("Judging", "Perceiving", "J", "P"),
}
MAX_PER_DIM = 12


def ai_status() -> dict:
    """Same shape as the old ollama_status() so templates keep working."""
    if not groq_api_key():
        return {
            "ok": False,
            "error": "GROQ_API_KEY is missing. Add it to the .env file (or host secrets), then restart.",
            "models": [],
        }
    return {"ok": True, "error": None, "models": [MODEL]}


def ollama_status() -> dict:
    """Backward-compatible alias used by app.py / CLI."""
    return ai_status()


def parse_json(raw: str) -> dict:
    text = (raw or "").strip()
    # Models sometimes wrap JSON in fences or think-tags.
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].lstrip()
    for tag in ("</think>", "</reasoning>"):
        if tag in text:
            text = text.split(tag, 1)[-1].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise
        data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("AI did not return a JSON object")
    return data


def _groq_chat(messages: list[dict]) -> str:
    """Call Groq without strict JSON mode (it often fails with empty failed_generation)."""
    key = groq_api_key()
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set")
    body = {
        "model": MODEL,
        "temperature": 0.2,
        "max_tokens": 2500,
        "messages": messages,
    }
    r = requests.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=90,
    )
    payload = r.json() if r.content else {}
    if r.status_code >= 400:
        raise RuntimeError(f"Groq API error {r.status_code}: {r.text[:500]}")
    if payload.get("error"):
        raise RuntimeError(str(payload["error"]))
    try:
        msg = payload["choices"][0]["message"]
        content = msg.get("content") or ""
        # Some models put the answer in reasoning fields; fall back if content empty.
        if not str(content).strip():
            content = msg.get("reasoning") or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected Groq response: {payload}") from exc
    return str(content or "")


def ask_ai(prompt: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": (
                "Reply with one JSON object only. "
                "No markdown fences, no extra text before or after the JSON."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    last_err: Exception | None = None
    for _ in range(2):
        try:
            content = _groq_chat(messages)
            if not content.strip():
                raise ValueError("Empty model response")
            return parse_json(content)
        except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
            last_err = exc
    assert last_err is not None
    raise last_err


def score(answers: list) -> tuple[str, dict[str, int]]:
    raw = {dim: 0 for dim in LETTERS}
    for item in answers:
        if isinstance(item, dict):
            dim, sign, answer = item["dim"], item["sign"], item["rating"]
        else:
            _text, dim, sign, answer = item
        raw[dim] += (answer - 3) * sign
    result = ""
    pcts = {}
    for dim, letters in LETTERS.items():
        pct = raw[dim] / MAX_PER_DIM * 50 + 50
        pcts[dim] = round(pct)
        result += letters[0] if raw[dim] >= 0 else letters[1]
    return result, pcts


def is_borderline(pct: int) -> bool:
    return 45 <= pct <= 55


def as_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if value:
        return [str(value)]
    return []


def ai_explain(mtype: str, pcts: dict[str, int], open_text: str) -> dict:
    borderline = [
        f"{dim} ({pct}% toward {dim[0]})"
        for dim, pct in pcts.items()
        if is_borderline(pct)
    ]
    borderline_note = (
        "These dimensions are borderline (near 50%): " + ", ".join(borderline) + "."
        if borderline
        else "No dimension is borderline."
    )
    prompt = f"""You are a friendly personality-test assistant.
This is an MBTI-style quiz, not the official MBTI instrument.
The formula result is {mtype}.
Scores (percent toward the first letter): {pcts}
EI: E is first, I is second. SN: S first, N second. TF: T first, F second. JP: J first, P second.
{borderline_note}
The person also wrote: {open_text!r}

Write a personalized result. Speak to the person as "you".
If any score is close to 50%, say that letter is borderline and not a strong preference.
Tips must be practical and modest. Label them as suggestions, not facts or a diagnosis.

Keep every list to 3 short phrases. Keep the description to 3 sentences.
Output only JSON with keys:
"title", "description", "strengths", "weaknesses", "careers",
"tips_study", "tips_work", "tips_watch"."""
    data = ask_ai(prompt)
    for key in ("strengths", "weaknesses", "careers", "tips_study", "tips_work", "tips_watch"):
        data[key] = as_list(data.get(key))
    data["title"] = str(data.get("title") or f"{mtype} profile")
    data["description"] = str(data.get("description") or "")
    return data


def ai_guess(answers: list, open_text: str) -> dict:
    lines = []
    for item in answers:
        if isinstance(item, dict):
            lines.append(f"- {item['text']} -> {item['rating']}/5")
        else:
            text, _dim, _sign, rating = item
            lines.append(f"- {text} -> {rating}/5")
    prompt = f"""Based only on these quiz answers (1 = strongly disagree, 5 = strongly agree)
and the self-description, guess the person's MBTI-style type (four letters).
Do not mention that a formula already scored this.

Answers:
{chr(10).join(lines)}

Self-description: {open_text!r}

Return ONLY this JSON shape (no other keys):
{{"type":"XXXX","reason":"one short sentence"}}
XXXX must be one of: INTJ INTP ENTJ ENTP INFJ INFP ENFJ ENFP ISTJ ISFJ ESTJ ESFJ ISTP ISFP ESTP ESFP"""
    data = ask_ai(prompt)
    guessed = str(data.get("type", "")).upper().replace(" ", "")
    if len(guessed) > 4:
        guessed = guessed[:4]
    data["type"] = guessed
    data["reason"] = str(data.get("reason") or "")
    return data


def save_result(mtype: str, pcts: dict[str, int], guess: dict, open_text: str) -> None:
    new_file = not RESULTS_CSV.exists()
    with RESULTS_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(
                [
                    "timestamp_utc",
                    "formula_type",
                    "ai_type",
                    "match",
                    "EI_pct_toward_E",
                    "SN_pct_toward_S",
                    "TF_pct_toward_T",
                    "JP_pct_toward_J",
                    "self_description",
                    "ai_reason",
                ]
            )
        writer.writerow(
            [
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                mtype,
                guess.get("type", ""),
                str(guess.get("type", "") == mtype).lower(),
                pcts["EI"],
                pcts["SN"],
                pcts["TF"],
                pcts["JP"],
                open_text,
                guess.get("reason", ""),
            ]
        )


def load_results() -> list[dict]:
    if not RESULTS_CSV.exists():
        return []
    with RESULTS_CSV.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def experiment_summary(rows: list[dict]) -> dict:
    total = len(rows)
    matches = sum(1 for row in rows if row.get("match", "").lower() == "true")
    return {
        "total": total,
        "matches": matches,
        "rate": round(100 * matches / total) if total else 0,
    }


def empty_report(mtype: str) -> dict:
    meta = type_payload(mtype) or {}
    return {
        "title": meta.get("nickname") or mtype,
        "description": "",
        "strengths": [],
        "weaknesses": [],
        "careers": [],
        "tips_study": [],
        "tips_work": [],
        "tips_watch": [],
    }


def formula_snapshot(answers: list, open_text: str) -> dict:
    mtype, pcts = score(answers)
    meta = type_payload(mtype)
    dimensions = []
    for dim, (left, right, ltr, rtl) in DIM_LABELS.items():
        pct = pcts[dim]
        dimensions.append(
            {
                "id": dim,
                "left": left,
                "right": right,
                "left_letter": ltr,
                "right_letter": rtl,
                "pct_left": pct,
                "pct_right": 100 - pct,
                "borderline": is_borderline(pct),
            }
        )
    return {
        "formula_type": mtype,
        "type_meta": meta,
        "guess_meta": None,
        "pcts": pcts,
        "dimensions": dimensions,
        "open_text": open_text,
        "ai_done": False,
        "ai_step": "Writing your personal report…",
        "report": empty_report(mtype),
        "report_error": None,
        "guess_type": "",
        "guess_reason": "",
        "guess_error": None,
        "match": False,
    }


def attach_ai(snapshot: dict, answers: list) -> dict:
    mtype = snapshot["formula_type"]
    pcts = snapshot["pcts"]
    open_text = snapshot["open_text"]
    snapshot["ai_step"] = "Writing your personal report…"
    try:
        snapshot["report"] = ai_explain(mtype, pcts, open_text)
    except (requests.RequestException, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        snapshot["report"] = empty_report(mtype)
        snapshot["report"]["description"] = "The report could not be written this time. Your type below is still valid."
        snapshot["report_error"] = str(exc)
    snapshot["ai_step"] = "Comparing with an independent type guess…"
    try:
        guess = ai_guess(answers, open_text)
    except (requests.RequestException, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        guess = {"type": "", "reason": str(exc)}
        snapshot["guess_error"] = str(exc)
    snapshot["guess_type"] = guess.get("type", "")
    snapshot["guess_reason"] = guess.get("reason", "")
    snapshot["guess_meta"] = type_payload(snapshot["guess_type"])
    snapshot["match"] = bool(snapshot["guess_type"]) and snapshot["guess_type"] == mtype
    save_result(mtype, pcts, guess, open_text)
    snapshot["ai_done"] = True
    snapshot["ai_step"] = "Done"
    return snapshot


def run_analysis(answers: list, open_text: str) -> dict:
    snapshot = formula_snapshot(answers, open_text)
    return attach_ai(snapshot, answers)
