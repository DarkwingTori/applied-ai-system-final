"""
PawPal+ RAG Engine
Retrieval-Augmented Generation for pet care advice.
"""

import os
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── Logging ──────────────────────────────────────────────────────────────────

log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "advisor.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent / "knowledge_base"
EMBED_MODEL_NAME = "multi-qa-mpnet-base-dot-v1"
CHUNK_SIZE = 400          # approximate words per chunk
CHUNK_OVERLAP = 80        # words of overlap between chunks
TOP_K = 5
LOW_CONFIDENCE_THRESHOLD = 0.30
VET_DISCLAIMER = (
    "\n\n> **Note:** Confidence in retrieved sources is low. "
    "Please consult your veterinarian for personalized guidance."
)

# ── Globals (populated on first load) ────────────────────────────────────────

_model: Optional[SentenceTransformer] = None
_index: Optional[faiss.IndexFlatIP] = None
_chunks: list[dict] = []   # [{text, source, chunk_id}]


# ── Text chunking ─────────────────────────────────────────────────────────────

def _chunk_text(text: str, source: str) -> list[dict]:
    """Split a document into overlapping word-based chunks."""
    words = text.split()
    results = []
    start = 0
    chunk_id = 0
    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))
        chunk_text = " ".join(words[start:end])
        results.append({"text": chunk_text, "source": source, "chunk_id": chunk_id})
        chunk_id += 1
        if end == len(words):
            break
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return results


# ── Knowledge base loading ────────────────────────────────────────────────────

def load_knowledge_base(path: Path = KNOWLEDGE_BASE_DIR) -> list[dict]:
    """Read all markdown files in the knowledge base directory and chunk them."""
    all_chunks: list[dict] = []
    for md_file in sorted(path.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        chunks = _chunk_text(text, source=md_file.stem)
        all_chunks.extend(chunks)
        logger.info("Loaded %d chunks from %s", len(chunks), md_file.name)
    logger.info("Total chunks loaded: %d", len(all_chunks))
    return all_chunks


# ── Vector store ──────────────────────────────────────────────────────────────

def build_vector_store(chunks: list[dict]) -> tuple[faiss.IndexFlatIP, SentenceTransformer]:
    """Create FAISS inner-product index from chunks using sentence-transformers."""
    model = SentenceTransformer(EMBED_MODEL_NAME)
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    embeddings = np.array(embeddings, dtype="float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)   # cosine similarity via inner product on L2-normed vecs
    index.add(embeddings)
    logger.info("FAISS index built: %d vectors, dim=%d", index.ntotal, dim)
    return index, model


# ── Init (lazy singleton) ─────────────────────────────────────────────────────

def _ensure_loaded() -> None:
    """Load knowledge base and build vector store on first call."""
    global _model, _index, _chunks
    if _index is not None:
        return
    _chunks = load_knowledge_base()
    if not _chunks:
        raise RuntimeError("Knowledge base is empty — check the knowledge_base/ directory.")
    _index, _model = build_vector_store(_chunks)


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve(query: str, top_k: int = TOP_K) -> tuple[list[dict], float]:
    """
    Embed the query and return the top-k most similar chunks.

    Returns:
        (chunks, confidence)  where confidence is the average similarity score (0–1).
    """
    _ensure_loaded()
    query_vec = _model.encode([query], normalize_embeddings=True)
    query_vec = np.array(query_vec, dtype="float32")

    scores, indices = _index.search(query_vec, top_k)
    scores = scores[0]   # shape (top_k,)
    indices = indices[0]

    retrieved = []
    for score, idx in zip(scores, indices):
        if idx == -1:
            continue
        chunk = dict(_chunks[idx])
        chunk["score"] = float(score)
        retrieved.append(chunk)

    confidence = float(np.mean([c["score"] for c in retrieved])) if retrieved else 0.0
    return retrieved, confidence


# ── Generation ────────────────────────────────────────────────────────────────

def generate_response(
    query: str,
    retrieved_chunks: list[dict],
    pet_name: str = "",
    task_type: str = "",
) -> str:
    """
    Call Groq LLM with retrieved context injected as system knowledge.
    Returns the model's response string.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY not set in environment / .env file")

    client = Groq(api_key=api_key)

    # Build context block from retrieved chunks
    context_lines = []
    for chunk in retrieved_chunks:
        context_lines.append(f"[Source: {chunk['source']}]\n{chunk['text']}")
    context_block = "\n\n---\n\n".join(context_lines)

    pet_ctx = f" for {pet_name}" if pet_name else ""
    task_ctx = f" regarding a {task_type} task" if task_type else ""

    system_prompt = (
        "You are PawPal+, a knowledgeable and caring pet care assistant. "
        "Answer questions about pet care using ONLY the reference material provided below. "
        "Be concise, warm, and practical. If the reference material does not contain "
        "enough information to answer confidently, say so and suggest consulting a vet. "
        "Do not invent facts beyond what is in the reference material.\n\n"
        f"REFERENCE MATERIAL:\n{context_block}"
    )

    user_message = f"Question{pet_ctx}{task_ctx}: {query}"

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=512,
    )

    return completion.choices[0].message.content


# ── Public API ────────────────────────────────────────────────────────────────

def ask(query: str, pet_name: str = "", task_type: str = "") -> dict:
    """
    Full RAG pipeline: retrieve → generate → log → return.

    Returns:
        {
            "answer": str,
            "confidence": float,
            "sources": [str, ...],
            "low_confidence": bool,
        }
    """
    _ensure_loaded()

    chunks, confidence = retrieve(query)
    sources = list(dict.fromkeys(c["source"] for c in chunks))  # deduplicated, ordered

    try:
        answer = generate_response(query, chunks, pet_name=pet_name, task_type=task_type)
    except Exception as exc:
        logger.error("LLM generation failed: %s", exc)
        answer = (
            "I'm unable to retrieve an answer right now. "
            "Please consult your veterinarian for personalized guidance."
        )

    low_confidence = confidence < LOW_CONFIDENCE_THRESHOLD
    if low_confidence:
        answer += VET_DISCLAIMER

    # Log the interaction
    logger.info(
        json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "pet_name": pet_name,
            "task_type": task_type,
            "sources": sources,
            "confidence": round(confidence, 4),
            "low_confidence": low_confidence,
        })
    )

    return {
        "answer": answer,
        "confidence": round(confidence, 4),
        "sources": sources,
        "low_confidence": low_confidence,
    }


# ── Task-type tip helper ──────────────────────────────────────────────────────

TASK_TYPE_QUERIES = {
    "walk": "How often and how long should I walk my dog?",
    "feeding": "What is the best feeding schedule for my pet?",
    "medication": "What are the best practices for giving my pet medication?",
    "enrichment": "What enrichment activities are best for my pet?",
    "grooming": "How often should I groom my pet?",
}


def get_task_tip(task_type: str) -> dict:
    """Return a short RAG-grounded tip for a given task type."""
    query = TASK_TYPE_QUERIES.get(task_type.lower(), f"Tips for {task_type} pet care task")
    return ask(query, task_type=task_type)
