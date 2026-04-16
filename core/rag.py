import os
import numpy as np
import faiss
import google.generativeai as genai
from pathlib import Path

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

EMBED_DIM = 768
faiss_index = faiss.IndexFlatL2(EMBED_DIM)

stored_chunks = []


def get_text_from_file(fpath: str) -> str:
    ext = Path(fpath).suffix.lower()
    if ext == ".pdf":
        import fitz
        doc = fitz.open(fpath)
        txt = ""
        for pg in doc:
            txt += pg.get_text()
        return txt
    else:
        with open(fpath, "r", errors="ignore") as f:
            return f.read()


def split_into_chunks(text: str, size=500, overlap=50):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+size])
        chunks.append(chunk)
        i += size - overlap
    return chunks


def embed_text(text: str):
    result = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document"
    )
    vec = np.array(result["embedding"], dtype=np.float32)
    if len(vec) != EMBED_DIM:
        vec = np.resize(vec, EMBED_DIM)
    return vec


def index_document(doc_id: int, doc_title: str, fpath: str):
    text = get_text_from_file(fpath)
    chunks = split_into_chunks(text)
    vecs = []
    for c in chunks:
        vec = embed_text(c)
        vecs.append(vec)
        stored_chunks.append({
            "document_id": doc_id,
            "title": doc_title,
            "chunk_text": c
        })
    if vecs:
        mat = np.stack(vecs)
        faiss_index.add(mat)


def remove_document(doc_id: int):
    global stored_chunks
    stored_chunks = [c for c in stored_chunks if c["document_id"] != doc_id]


def semantic_search(query: str, top_k: int = 5):
    if faiss_index.ntotal == 0:
        return []

    q_vec = genai.embed_content(
        model="models/embedding-001",
        content=query,
        task_type="retrieval_query"
    )
    q_arr = np.array(q_vec["embedding"], dtype=np.float32)
    if len(q_arr) != EMBED_DIM:
        q_arr = np.resize(q_arr, EMBED_DIM)

    fetch_k = min(20, faiss_index.ntotal)
    dists, idxs = faiss_index.search(q_arr.reshape(1, -1), fetch_k)

    raw_results = []
    for dist, idx in zip(dists[0], idxs[0]):
        if idx < len(stored_chunks):
            item = stored_chunks[idx].copy()
            item["score"] = float(1 / (1 + dist))
            raw_results.append(item)

    reranked = rerank_results(query, raw_results)
    return reranked[:top_k]


def rerank_results(query: str, results: list):
    if not results:
        return []
    model = genai.GenerativeModel("gemini-pro")
    chunks_text = "\n\n".join(
        [f"[{i}] {r['chunk_text'][:300]}" for i, r in enumerate(results)]
    )
    prompt = f"""You are ranking financial document chunks by relevance to a query.
Query: {query}

Chunks:
{chunks_text}

Return a comma-separated list of indices from most to least relevant. Example: 2,0,3,1
Only return the numbers, nothing else."""

    try:
        resp = model.generate_content(prompt)
        order_str = resp.text.strip()
        order = [int(x.strip()) for x in order_str.split(",") if x.strip().isdigit()]
        reranked = []
        seen = set()
        for i in order:
            if 0 <= i < len(results) and i not in seen:
                reranked.append(results[i])
                seen.add(i)
        for i, r in enumerate(results):
            if i not in seen:
                reranked.append(r)
        return reranked
    except Exception:
        return results


def get_document_context(doc_id: int):
    return [c for c in stored_chunks if c["document_id"] == doc_id]
