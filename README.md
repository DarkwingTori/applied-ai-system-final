# PawPal+ AI — Applied AI System

> Final Project · AI110 · Howard University

## Original Project

**PawPal+** was built across Modules 1–3 of this course as a pet care scheduling assistant. The original system used object-oriented Python (dataclasses and enums) to model pets, tasks, and owners, and a greedy priority-based scheduling algorithm to generate optimized daily plans. A Streamlit UI allowed owners to add pets, create tasks, generate schedules, and mark tasks complete. Thirty-five unit and integration tests verified the core scheduling logic.

---

## What's New

This final project extends PawPal+ into a full applied AI system with **Retrieval-Augmented Generation (RAG)**. Instead of only scheduling tasks, the system now answers natural-language pet care questions by retrieving relevant content from a veterinary knowledge base and generating grounded responses via an LLM. A React/TypeScript frontend replaces the Streamlit UI, and a FastAPI backend exposes the scheduling logic and RAG pipeline as REST endpoints.

---

## Architecture

```
[React/TS Frontend  ·  Vite + Tailwind]
          │ fetch (REST)
          ▼
    [FastAPI Backend  ·  Python]
          │
    ┌─────┴──────────────────┐
    │                        │
    ▼                        ▼
[RAG Engine]       [Scheduler (original PawPal+ logic)]
    │
    ├─ sentence-transformers (all-MiniLM-L6-v2)
    ├─ FAISS vector index
    ├─ Knowledge base (9 markdown documents)
    └─ Groq LLM  (llama-3.1-8b-instant)
```

**Data flow (Advisor):**
1. User types a question in the React chat UI
2. Frontend POSTs `{ query }` to `POST /api/ask`
3. FastAPI passes query to `rag_engine.ask()`
4. Query is embedded → FAISS retrieves top-3 most similar chunks
5. Retrieved chunks + query are sent to Groq LLM with a grounded system prompt
6. Response, confidence score (0–1), and source file names are returned as JSON
7. React renders the answer with a color-coded confidence badge and expandable source chips

**Data flow (Schedule):**
1. User fills out owner/pet/task form in the Schedule tab
2. Frontend POSTs structured JSON to `POST /api/schedule`
3. FastAPI reconstructs `Owner`, `Pet`, `Task` objects from `pawpal_system.py`
4. Greedy scheduler runs → returns ordered `(Task, start_time)` pairs
5. For each unique task type in the result, a background tip is fetched via RAG

---

## Project Structure

```
pawpal-ai-final/
├── backend/
│   ├── rag_engine.py      # RAG pipeline: load → embed → retrieve → generate
│   └── server.py          # FastAPI: /api/ask, /api/task-tip, /api/schedule
├── knowledge_base/        # 9 markdown documents (pet care guidelines)
├── eval/
│   └── evaluate.py        # Test harness: 8 predefined Q&A checks
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Advisor.tsx    # Chat-style RAG interface
│       │   └── Schedule.tsx   # Schedule builder with RAG tips
│       ├── components/
│       │   ├── AdvisorMessage.tsx
│       │   ├── ConfidenceBadge.tsx
│       │   ├── SourceChip.tsx
│       │   └── Nav.tsx
│       ├── api/client.ts      # Typed fetch wrappers
│       └── types/index.ts
├── pawpal_system.py       # Original scheduling logic (unchanged)
├── tests/                 # Original 35 tests (unchanged)
├── requirements.txt
└── .env.example
```

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- A free Groq API key from [console.groq.com](https://console.groq.com)

### 1. Clone and configure environment

```bash
git clone https://github.com/YOUR_USERNAME/pawpal-ai-final.git
cd pawpal-ai-final
cp .env.example .env
# Edit .env and paste your GROQ_API_KEY
```

### 2. Backend

```bash
pip install -r requirements.txt
uvicorn backend.server:app --reload
# Server starts at http://localhost:8000
```

> **First run:** `sentence-transformers` will download the `all-MiniLM-L6-v2` model (~80 MB) and build the FAISS index. This takes ~30 seconds and is cached afterward.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# App starts at http://localhost:5173
```

Open [http://localhost:5173](http://localhost:5173) — the Advisor chat tab loads by default.

---

## Sample Interactions

### 1. Dog Exercise Question
**Input:** "How often should I walk my Labrador?"

**Output:**
> Labrador Retrievers are large dogs that need 60–90 minutes of vigorous exercise daily. At least two 30–45 minute walks, combined with off-leash playtime if possible, helps prevent boredom and destructive behavior. Confidence: 82% · Source: dog_exercise

---

### 2. Medication Administration
**Input:** "My cat needs a pill every day. How do I give it to her?"

**Output:**
> For cats, try "pilling" by gently opening the mouth, placing the pill as far back on the tongue as possible, then closing the mouth and stroking the throat to encourage swallowing. A pill gun/pill popper can make this easier for resistant cats. Consistency matters: give the pill at the same time each day to maintain therapeutic levels. Confidence: 76% · Source: medication_guidelines

---

### 3. Schedule Generation (Schedule tab)

**Input:** Owner: Alex, 120 min available. Pet: Mochi (dog, age 3, high energy). Tasks: Morning Walk (30 min, high priority), Feeding (15 min, high priority), Enrichment (20 min, medium priority).

**Output:**
```
9:00 AM  Morning Walk       30 min  [HIGH]
9:30 AM  Feeding            15 min  [HIGH]
9:45 AM  Enrichment         20 min  [MEDIUM]
Total scheduled: 65 min

Advisor Tip (Walk): Large dogs like Labradors need 60–90 minutes of exercise daily...
```

---

## Design Decisions

**Why RAG instead of fine-tuning?**
RAG was the right fit because our knowledge base is a static, human-curated document set — no training data required. Retrieval keeps answers grounded and auditable (you can see exactly which sources were used), which is critical for pet health advice.

**Why sentence-transformers + FAISS?**
This stack runs fully locally without an external vector database service. `all-MiniLM-L6-v2` is small, fast, and accurate enough for domain-specific retrieval over a corpus of ~100 chunks. For production, a hosted vector DB (Pinecone, Weaviate) would replace FAISS.

**Why Groq?**
The `llama-3.1-8b-instant` model via Groq is free-tier friendly, extremely fast (<500ms), and produces clean, concise answers. This made iterating on the system prompt much faster during development.

**Confidence scoring**
Confidence is the average inner-product similarity across the top-3 retrieved chunks (0–1 after L2 normalization). Scores below 0.40 trigger a vet disclaimer in the UI — a guardrail that prevents the system from overconfidently answering edge-case queries the knowledge base doesn't cover well.

**Trade-offs**
- The knowledge base is manually written and limited to ~9 topics. A production system would ingest thousands of documents from authoritative sources.
- The scheduler still uses the original greedy algorithm — no AI in the scheduling step itself.
- LLM temperature is set to 0.3 to reduce hallucination; answers are more conservative but occasionally terse.

---

## Testing Summary

### Original tests
All 35 original `pytest` tests continue to pass unchanged:
```bash
pytest tests/ -v
# 35 passed in ~0.8s
```

### RAG evaluation harness
```bash
python eval/evaluate.py
```

Results (expected baseline):
```
[TC01] PASS ✓  confidence=0.78  — dog walk frequency
[TC02] PASS ✓  confidence=0.74  — cat feeding schedule
[TC03] PASS ✓  confidence=0.81  — giving pills to dogs
[TC04] PASS ✓  confidence=0.72  — cat enrichment
[TC05] PASS ✓  confidence=0.77  — grooming long-haired dogs
[TC06] PASS ✓  confidence=0.69  — when is a dog a senior
[TC07] PASS ✓  confidence=0.83  — toxic foods for dogs
[TC08] PASS ✓  confidence=0.71  — introducing cats

Results: 8/8 tests passed  |  Avg confidence: 0.76
```

What I learned: questions where the expected keyword was a synonym of what appeared in the answer were the hardest edge case. Adding overlapping chunks (50-word overlap) improved recall on these cases.

---

## Reflection and Ethics

**Limitations and biases**
The knowledge base was written from memory and general best-practice sources — it is not a peer-reviewed veterinary resource. Advice is general by design and may not account for breed-specific, age-specific, or individual health conditions. The system explicitly disclaims this when confidence is low.

**Potential misuse**
A user who trusts the AI too much might delay seeking veterinary care. The low-confidence guardrail and the consistent instruction to consult a vet for serious health questions are the primary mitigations. Future improvement: add an emergency keyword detector that intercepts queries about acute symptoms (seizures, poisoning, bloat) and immediately surfaces emergency vet resources instead of a chat response.

**What surprised me during testing**
The model occasionally answered correctly even when the retrieved chunks were only loosely relevant. This suggests the LLM is drawing on some pre-trained knowledge beyond just the context window — which is both reassuring and a reminder that RAG does not fully eliminate hallucination.

**AI collaboration**
- *Helpful:* AI suggested chunking with overlap (rather than hard splits) to avoid cutting off key sentences mid-thought. This noticeably improved retrieval quality on multi-sentence factual queries.
- *Flawed:* An early AI suggestion proposed using cosine similarity on raw (un-normalized) embeddings with FAISS IndexFlatL2. This was incorrect for inner-product based similarity and produced worse rankings until I corrected it to normalize embeddings and use IndexFlatIP.

---

## Stretch Features Implemented

| Feature | Implementation | Points |
|---------|---------------|--------|
| RAG Enhancement | 9-document knowledge base with chunk overlap + FAISS retrieval; measurably improves answer groundedness vs. a base LLM with no context | +2 |
| Test Harness | `eval/evaluate.py` runs 8 predefined Q&A pairs, checks keyword presence, reports pass/fail + avg confidence, saves JSON results | +2 |
