"""
PawPal+ RAG Evaluation Script
Runs the system on predefined test cases and reports pass/fail + confidence metrics.

Usage:
    python eval/evaluate.py

Requirements:
    - Backend dependencies installed (pip install -r requirements.txt)
    - GROQ_API_KEY set in .env or environment
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.rag_engine import ask

# ── Test cases ────────────────────────────────────────────────────────────────
# Each case: query, keywords that must appear in the answer (case-insensitive)

TEST_CASES = [
    {
        "id": "TC01",
        "query": "How often should I walk a large dog like a Labrador?",
        "expected_keywords": ["60", "90", "minutes", "walk"],
        "task_type": "walk",
    },
    {
        "id": "TC02",
        "query": "What is the best feeding schedule for an adult cat?",
        "expected_keywords": ["twice", "morning", "evening"],
        "task_type": "feeding",
    },
    {
        "id": "TC03",
        "query": "How do I give my dog a pill?",
        "expected_keywords": ["peanut butter", "pill", "mouth"],
        "task_type": "medication",
    },
    {
        "id": "TC04",
        "query": "What enrichment activities can I do with my indoor cat?",
        "expected_keywords": ["play", "puzzle", "toy"],
        "task_type": "enrichment",
    },
    {
        "id": "TC05",
        "query": "How often should I brush a long-haired dog?",
        "expected_keywords": ["daily", "brush", "mat"],
        "task_type": "grooming",
    },
    {
        "id": "TC06",
        "query": "When is a dog considered a senior?",
        "expected_keywords": ["year", "senior", "large"],
        "task_type": "",
    },
    {
        "id": "TC07",
        "query": "What foods are toxic to dogs?",
        "expected_keywords": ["chocolate", "xylitol", "grapes"],
        "task_type": "",
    },
    {
        "id": "TC08",
        "query": "How do I introduce a new cat to my existing cat?",
        "expected_keywords": ["separate", "room", "scent"],
        "task_type": "",
    },
]

# ── Runner ────────────────────────────────────────────────────────────────────

def evaluate():
    passed = 0
    total = len(TEST_CASES)
    confidences = []
    failures = []

    print("\n" + "="*60)
    print("  PawPal+ RAG Evaluation")
    print("="*60 + "\n")

    for tc in TEST_CASES:
        result = ask(tc["query"], task_type=tc["task_type"])
        answer_lower = result["answer"].lower()
        confidence = result["confidence"]
        confidences.append(confidence)

        matched = [kw for kw in tc["expected_keywords"] if kw.lower() in answer_lower]
        success = len(matched) == len(tc["expected_keywords"])

        status = "PASS ✓" if success else "FAIL ✗"
        if success:
            passed += 1
        else:
            failures.append({
                "id": tc["id"],
                "query": tc["query"],
                "missing": [kw for kw in tc["expected_keywords"] if kw.lower() not in answer_lower],
            })

        print(f"[{tc['id']}] {status}  confidence={confidence:.2f}")
        print(f"       Query: {tc['query']}")
        if not success:
            missing = [kw for kw in tc["expected_keywords"] if kw.lower() not in answer_lower]
            print(f"       Missing keywords: {missing}")
        print()

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    print("="*60)
    print(f"  Results: {passed}/{total} tests passed")
    print(f"  Avg confidence: {avg_confidence:.2f}")
    if failures:
        print(f"  Failed: {[f['id'] for f in failures]}")
    print("="*60 + "\n")

    # Machine-readable summary
    summary = {
        "passed": passed,
        "total": total,
        "pass_rate": round(passed / total, 2),
        "avg_confidence": round(avg_confidence, 4),
        "failures": failures,
    }
    output_path = Path(__file__).parent / "eval_results.json"
    output_path.write_text(json.dumps(summary, indent=2))
    print(f"Full results saved to {output_path}")

    return passed == total


if __name__ == "__main__":
    success = evaluate()
    sys.exit(0 if success else 1)
