"""
Publishable website for the personality quiz (Groq API).

  python app.py

Then open http://127.0.0.1:5000
Set GROQ_API_KEY in .env (or host secrets).
"""

from __future__ import annotations

import os
import random
import secrets
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

load_dotenv(Path(__file__).with_name(".env"))

from quiz_core import (  # noqa: E402
    DIM_LABELS,
    QUESTIONS,
    attach_ai,
    experiment_summary,
    formula_snapshot,
    load_results,
    ollama_status,
)
from personalities_data import enrich_type_page, group_blocks, load_catalog  # noqa: E402
from types_meta import type_payload, types_by_role  # noqa: E402

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(16)
JOBS: dict[str, dict] = {}
JOB_LOCK = threading.Lock()


def current_status() -> dict:
    return ollama_status()


@app.context_processor
def inject_status() -> dict:
    return {"ollama": {"ok": True, "error": None}}


def question_at(index: int) -> dict | None:
    order = session.get("order")
    if not order or index < 0 or index >= len(order):
        return None
    text, dim, sign = QUESTIONS[order[index]]
    return {"text": text, "dim": dim, "sign": sign}


def collected_answers() -> list[dict]:
    order = session.get("order") or []
    ratings = session.get("ratings") or []
    out = []
    for qid, rating in zip(order, ratings):
        text, dim, sign = QUESTIONS[qid]
        out.append({"text": text, "dim": dim, "sign": sign, "rating": rating})
    return out


def run_job(job_id: str, answers: list[dict], open_text: str) -> None:
    with JOB_LOCK:
        snapshot = JOBS[job_id]
    try:
        attach_ai(snapshot, answers)
    except Exception as exc:
        snapshot["report_error"] = str(exc)
        snapshot["ai_done"] = True
        snapshot["ai_step"] = "Something went wrong writing the report. Your type is still valid."


@app.get("/")
def home():
    return render_template(
        "home.html",
        ollama=current_status(),
        roles=types_by_role(),
    )


@app.post("/start")
def start():
    status = current_status()
    if not status["ok"]:
        return redirect(url_for("home"))
    order = list(range(len(QUESTIONS)))
    random.shuffle(order)
    session.clear()
    session["order"] = order
    session["ratings"] = []
    session["index"] = 0
    return redirect(url_for("quiz"))


@app.get("/quiz")
def quiz():
    order = session.get("order")
    if not order:
        return redirect(url_for("home"))
    index = session.get("index", 0)
    if index >= len(order):
        return redirect(url_for("describe"))
    q = question_at(index)
    return render_template(
        "quiz.html",
        number=index + 1,
        total=len(order),
        text=q["text"],
        progress=round(100 * index / len(order)),
    )


@app.post("/quiz")
def quiz_answer():
    order = session.get("order")
    if not order:
        return redirect(url_for("home"))
    index = session.get("index", 0)
    if index >= len(order):
        return redirect(url_for("describe"))
    rating = request.form.get("rating", "")
    if rating not in {"1", "2", "3", "4", "5"}:
        return redirect(url_for("quiz"))
    ratings = session.get("ratings") or []
    if len(ratings) == index:
        ratings.append(int(rating))
        session["ratings"] = ratings
        session["index"] = index + 1
    if session["index"] >= len(order):
        return redirect(url_for("describe"))
    return redirect(url_for("quiz"))


@app.get("/describe")
def describe():
    order = session.get("order")
    ratings = session.get("ratings") or []
    if not order or len(ratings) != len(order):
        return redirect(url_for("home"))
    return render_template("describe.html")


@app.post("/describe")
def describe_save():
    order = session.get("order")
    ratings = session.get("ratings") or []
    if not order or len(ratings) != len(order):
        return redirect(url_for("home"))
    text = (request.form.get("open_text") or "").strip() or "(no self-description given)"
    answers = collected_answers()
    snapshot = formula_snapshot(answers, text)
    job_id = secrets.token_hex(8)
    with JOB_LOCK:
        JOBS[job_id] = snapshot
    session["job_id"] = job_id
    thread = threading.Thread(
        target=run_job,
        args=(job_id, answers, text),
        daemon=True,
    )
    thread.start()
    return redirect(url_for("result"))


@app.get("/result")
def result():
    job_id = session.get("job_id", "")
    with JOB_LOCK:
        data = JOBS.get(job_id)
    if not data:
        return redirect(url_for("home"))
    return render_template("result.html", r=data, job_id=job_id)


@app.get("/job-status")
def job_status():
    job_id = session.get("job_id", "")
    with JOB_LOCK:
        data = JOBS.get(job_id)
    if not data:
        return jsonify({"ok": False, "error": "No result in this session."}), 404
    return jsonify({"ok": True, "job": data})


DIM_COLUMNS = [
    ("EI", "EI_pct_toward_E"),
    ("SN", "SN_pct_toward_S"),
    ("TF", "TF_pct_toward_T"),
    ("JP", "JP_pct_toward_J"),
]


def friendly_time(stamp: str) -> str:
    try:
        return datetime.fromisoformat(stamp).strftime("%d %b %Y, %H:%M UTC")
    except ValueError:
        return stamp


def safe_int(value, default: int = 50) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def enrich_row(row: dict) -> dict:
    quiz_type = (row.get("formula_type") or "").upper()
    ai_type = (row.get("ai_type") or "").upper()
    valid_ai = len(ai_type) == 4 and ai_type.isalpha()
    dims = []
    for index, (key, column) in enumerate(DIM_COLUMNS):
        left, right, ltr, rtl = DIM_LABELS[key]
        pct = safe_int(row.get(column), 50)
        quiz_letter = quiz_type[index] if len(quiz_type) == 4 else ""
        ai_letter = ai_type[index] if valid_ai else ""
        dims.append(
            {
                "left": left,
                "right": right,
                "left_letter": ltr,
                "right_letter": rtl,
                "pct": pct,
                "quiz_letter": quiz_letter,
                "ai_letter": ai_letter,
                "agree": bool(quiz_letter and ai_letter and quiz_letter == ai_letter),
            }
        )
    about = row.get("self_description")
    reason = row.get("ai_reason")
    return {
        "when": friendly_time(row.get("timestamp_utc") or ""),
        "quiz": type_payload(quiz_type),
        "quiz_code": quiz_type,
        "ai": type_payload(ai_type),
        "ai_code": ai_type if valid_ai else "",
        "match": (row.get("match") or "").lower() == "true",
        "letters_same": sum(1 for d in dims if d["agree"]),
        "dims": dims,
        "about": (about or "").strip() if isinstance(about, str) else "",
        "reason": (reason or "").strip() if isinstance(reason, str) else "",
    }


def letter_agreement(rows: list[dict]) -> list[dict]:
    out = []
    for key, _ in DIM_COLUMNS:
        left, right, ltr, rtl = DIM_LABELS[key]
        out.append({"name": f"{ltr} / {rtl}", "label": f"{left} vs {right}", "agree": 0, "total": 0})
    for row in rows:
        if not row["ai_code"]:
            continue
        for slot, d in zip(out, row["dims"]):
            slot["total"] += 1
            slot["agree"] += 1 if d["agree"] else 0
    for slot in out:
        slot["pct"] = round(100 * slot["agree"] / slot["total"]) if slot["total"] else 0
    return out


@app.get("/research")
def research():
    raw = load_results()
    summary = experiment_summary(raw)
    rows = [enrich_row(r) for r in raw]
    summary["different"] = summary["total"] - summary["matches"]
    summary["avg_letters"] = (
        round(sum(r["letters_same"] for r in rows) / len(rows), 1) if rows else 0
    )
    return render_template(
        "research.html",
        rows=list(reversed(rows)),
        summary=summary,
        letters=letter_agreement(rows),
    )


@app.get("/personalities")
def personalities():
    catalog = load_catalog()
    return render_template(
        "personalities.html",
        groups=group_blocks(catalog),
        how_quizzes=catalog.get("how_quizzes_work", {}),
        how_ai=catalog.get("how_ai_detects", {}),
        meta=catalog.get("meta", {}),
    )


@app.get("/personalities/<slug>")
def personality_detail(slug: str):
    page = enrich_type_page(slug)
    if not page:
        return render_template("404.html", message="That personality type was not found."), 404
    return render_template("personality.html", p=page)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    print(f"Open http://127.0.0.1:{port}  (Groq API)")
    # 0.0.0.0 so LAN / deploy health checks work; production uses gunicorn.
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
