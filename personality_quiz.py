"""
Terminal version of the MBTI-style quiz.

  python personality_quiz.py

For the website version:

  python app.py
"""

from __future__ import annotations

import json
import random
import sys

import requests

from quiz_core import (
    QUESTIONS,
    ai_explain,
    ai_guess,
    is_borderline,
    ollama_status,
    save_result,
    score,
)


def run_quiz() -> list[tuple[str, str, int, int]]:
    qs = QUESTIONS[:]
    random.shuffle(qs)
    answers = []
    print("\nRate each statement 1-5")
    print("1 = strongly disagree, 3 = mixed, 5 = strongly agree\n")
    for i, (text, dim, sign) in enumerate(qs, 1):
        while True:
            a = input(f"{i}/{len(qs)}. {text}\n   > ").strip()
            if a in {"1", "2", "3", "4", "5"}:
                break
            print("   Please enter a number from 1 to 5.")
        answers.append((text, dim, sign, int(a)))
    return answers


def print_report(info: dict) -> None:
    print(f"\n{info.get('title', 'Your result')}")
    print(info.get("description", ""))
    for label in ("strengths", "weaknesses", "careers"):
        value = info.get(label, [])
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        print(f"{label.capitalize()}: {value}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    status = ollama_status()
    if not status["ok"]:
        sys.exit(status["error"])
    print("This is an MBTI-style quiz (not the official MBTI).")
    print("Your 4-letter type is scored by a formula. The local AI only writes the report")
    print("and then makes its own guess for the experiment.")
    answers = run_quiz()
    open_text = input("\nDescribe yourself in 2-3 sentences:\n> ").strip()
    if not open_text:
        open_text = "(no self-description given)"

    mtype, pcts = score(answers)
    print(f"\nYour type (formula): {mtype}")
    for dim, pct in pcts.items():
        note = "  [borderline]" if is_borderline(pct) else ""
        print(f"  {dim}: {pct}% toward {dim[0]}, {100 - pct}% toward {dim[1]}{note}")

    print("\nAI is writing your result (this can take 1-2 minutes on this laptop)...")
    try:
        info = ai_explain(mtype, pcts, open_text)
        print_report(info)
    except (requests.RequestException, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        print(f"\nCould not write the AI report: {exc}")

    print("\nAI is guessing your type from the raw answers (experiment)...")
    try:
        guess = ai_guess(answers, open_text)
    except (requests.RequestException, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        guess = {"type": "", "reason": str(exc)}

    guessed = guess.get("type", "")
    print(f"\n[Experiment] AI's own guess: {guessed} ({guess.get('reason', '')})")
    print(f"[Experiment] Formula type:    {mtype}")
    print(f"[Experiment] Match:           {guessed == mtype}")
    save_result(mtype, pcts, guess, open_text)
    print("\nSaved this run to results.csv")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nQuiz cancelled.")
        sys.exit(130)
