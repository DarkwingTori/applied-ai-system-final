# Model Card — PawPal+ AI

> AI110 · Howard University · Final Project

---

## Model Overview

| Field | Details |
|---|---|
| **System Name** | PawPal+ AI |
| **Base Project** | PawPal+ Scheduling Assistant (Modules 1–3) |
| **AI Technique** | Retrieval-Augmented Generation (RAG) |
| **Embedding Model** | `multi-qa-mpnet-base-dot-v1` (sentence-transformers) |
| **LLM** | `llama-3.3-70b-versatile` via Groq API |
| **Vector Store** | FAISS IndexFlatIP (cosine similarity, top-5 retrieval) |
| **Knowledge Base** | 9 curated veterinary markdown documents (~100 chunks) |
| **Intended Use** | General pet care Q&A and daily task scheduling for pet owners |
| **Not Intended For** | Emergency veterinary diagnosis, medical treatment decisions |

---

## Base Project

PawPal+ was originally developed across Modules 1–3 as a pure Python scheduling assistant. The core system (`pawpal_system.py`) models `Owner`, `Pet`, and `Task` objects using dataclasses and enums, and runs a greedy priority-based scheduling algorithm to generate optimized daily care plans. Thirty-five unit and integration tests verified this logic.

The Module 4 final project extends that foundation into a full AI system by adding:
- A RAG pipeline (`backend/rag_engine.py`) for grounded natural-language Q&A
- A FastAPI backend (`backend/server.py`) exposing the scheduler and RAG as REST endpoints
- A React/TypeScript frontend replacing the original Streamlit UI

The original scheduling logic was preserved unchanged — the AI layer was added on top, not as a replacement.

---

## Intended Use

**Primary users:** Pet owners managing daily care routines for dogs, cats, or small animals.

**Supported tasks:**
- Ask natural-language questions about pet care (feeding, medication, exercise, grooming, enrichment)
- Generate optimized daily schedules from a list of pets and tasks
- Receive RAG-grounded tips for each scheduled task type

**Out of scope:**
- Emergency symptom diagnosis (users are directed to consult a vet)
- Breed-specific or age-specific medical advice
- Multi-pet conflict resolution beyond greedy scheduling

---

## AI Collaboration

### How AI Was Used

I used Claude Code throughout all phases of development:

**System Design (Modules 1–3):**
- Brainstormed UML class structure and relationships
- Requested feedback on composition vs. inheritance patterns
- Got examples of Python enum usage for type safety

**RAG Implementation (Module 4):**
- Asked for guidance on embedding model selection and FAISS index setup
- Requested help structuring the FastAPI server and Pydantic models
- Used AI to debug CORS preflight failures between the React frontend and FastAPI backend
- Got suggestions for improving retrieval accuracy (chunk overlap, model upgrades, TOP_K tuning)

**Frontend:**
- Asked for help with React Router setup and typed fetch wrappers
- Requested component structure for the Advisor chat interface

### Exercising Judgment

**Example of accepting an AI suggestion:**
AI suggested using overlapping chunks (50-word overlap) rather than hard word-boundary splits. I evaluated this against the problem (key facts were being cut off mid-sentence) and tested it — retrieval quality measurably improved. I accepted this suggestion.

**Example of rejecting an AI suggestion:**
When implementing conflict detection in the scheduler, AI initially suggested *preventing* conflicting tasks from being scheduled by raising an exception. I rejected this because:
1. Pet owners may intentionally overlap tasks (one person walks the dog while another feeds the cat)
2. Strict prevention removes user autonomy
3. A "detect and warn" approach is more flexible without being less safe

I pushed back and asked AI to revise the approach to return warnings instead of blocking — which is what the final system uses.

**Example of correcting an AI error:**
An early AI suggestion proposed using cosine similarity on raw (un-normalized) embeddings with `faiss.IndexFlatL2`. This was incorrect — `IndexFlatL2` computes Euclidean distance, not cosine similarity. For cosine similarity via inner product, embeddings must be L2-normalized first and the index must be `IndexFlatIP`. I caught this by reading the FAISS documentation, corrected the implementation, and confirmed rankings improved.

---

## Biases and Limitations

### Knowledge Base Bias
The 9 knowledge base documents were written by hand based on general best-practice pet care sources. They are **not peer-reviewed veterinary resources**. This introduces:
- **Coverage bias:** Advice exists only for the 9 covered topics. Unusual queries receive low-confidence responses.
- **Generalization bias:** All advice is breed-agnostic and age-agnostic. A 14-year-old arthritic Labrador has different exercise needs than the "60–90 minutes daily" the knowledge base recommends.
- **Species bias:** Most knowledge base content focuses on dogs and cats. Small animals, birds, and reptiles are underrepresented.

### Model Bias
`llama-3.3-70b-versatile` was pre-trained on broad internet text, which includes inconsistent, sometimes outdated, or culturally specific pet care advice. Even with RAG grounding, the LLM may interpolate from pre-training knowledge when retrieved context is thin.

### Confidence Score Limitations
Confidence is the average cosine similarity of retrieved chunks — not a true probability of correctness. A high-confidence score means the query matched the knowledge base well; it does not guarantee the answer is medically accurate. Users are warned via a vet disclaimer when confidence falls below 0.30.

### Mitigation Strategies
- Low-confidence guardrail: any response below 0.30 similarity appends a vet consultation disclaimer
- System prompt explicitly instructs the LLM to answer from reference material only and to say so when it cannot
- Source chips in the UI show exactly which documents were used, making retrieval auditable

---

## Testing Results

### Original Scheduling Tests (35 tests)
All 35 original pytest tests continue to pass unchanged with the final codebase:
```
pytest tests/ -v
35 passed in 0.8s
```

Tests cover: CRUD operations, priority-based scheduling, time constraint enforcement, recurring task logic, conflict detection, and edge cases (empty lists, zero time, invalid inputs).

### RAG Evaluation Harness (8 tests)
```
python eval/evaluate.py
```

| Test | Topic | Confidence | Result |
|---|---|---|---|
| TC01 | Dog walk frequency | 0.78 | PASS |
| TC02 | Cat feeding schedule | 0.74 | PASS |
| TC03 | Giving pills to dogs | 0.81 | PASS |
| TC04 | Cat enrichment activities | 0.72 | PASS |
| TC05 | Grooming long-haired dogs | 0.77 | PASS |
| TC06 | When is a dog a senior | 0.69 | PASS |
| TC07 | Toxic foods for dogs | 0.83 | PASS |
| TC08 | Introducing cats to each other | 0.71 | PASS |

**Results: 8/8 passed · Average confidence: 0.76**

### What I Learned from Testing
- Questions where the expected keyword was a synonym of what appeared in the answer were the hardest edge case. Adding chunk overlap (80-word overlap) improved recall on these cases.
- The model occasionally answered correctly even when retrieved chunks were loosely relevant, suggesting the LLM draws on some pre-trained knowledge beyond the context window. This is both a strength (robustness) and a risk (potential hallucination).
- Upgrading from `all-MiniLM-L6-v2` to `multi-qa-mpnet-base-dot-v1` improved average confidence scores by ~6–8% on domain-specific Q&A queries.

---

## Multi-Model Prompt Comparison

**Task:** Implement `create_next_occurrence()` — generate the next recurring task instance after completion.

| Model | Approach | Strengths | Weaknesses |
|---|---|---|---|
| **Claude** | Explicit if/elif with clear variable names | Readable, Pythonic, easy to debug | Slightly more lines |
| **GPT-4** | Dict mapping + dict unpacking | Compact, clever | Less readable for beginners |
| **Gemini** | Class-level constants + helper method | Extensible, enterprise-ready | Over-engineered for 2 frequencies |

**Choice:** Claude's approach — this is an educational project where readability matters more than cleverness. The explicit if/elif structure makes the logic immediately clear to anyone reviewing the code.

**Key insight:** Each model optimizes for different values (readability vs. brevity vs. extensibility). The human engineer must evaluate which tradeoff fits the project context — not just accept the first working solution.

---

## Ethical Considerations

**Potential misuse:** A user who trusts the AI's confidence score too much might delay seeking veterinary care for a sick animal. Mitigations:
- Low-confidence vet disclaimer
- System prompt that explicitly says to consult a vet for serious health questions
- Planned future feature: emergency keyword detector that intercepts queries about acute symptoms (seizures, poisoning, bloat) and surfaces emergency vet contacts instead of a chat response

**Data privacy:** No user data, pet names, or queries are stored beyond the session log (`logs/advisor.log`). The log is local only and not transmitted anywhere.

**Transparency:** Source chips in the UI show exactly which knowledge base documents informed each answer, making the system's reasoning auditable rather than a black box.
