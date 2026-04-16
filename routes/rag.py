from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core import models
from core.schemas import SearchQuery, ChunkOut
from core.auth import get_logged_in_user, check_permission
from core import rag

router = APIRouter()


@router.post("/index-document", status_code=status.HTTP_202_ACCEPTED)
def index_a_document(
    document_id: int,
    db: Session = Depends(get_db),
    curr_user: models.User = Depends(check_permission("upload"))
):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        rag.index_document(doc.id, doc.title, doc.file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")

    return {"message": f"Document '{doc.title}' indexed successfully."}


@router.delete("/remove-document/{document_id}", status_code=status.HTTP_200_OK)
def remove_embeddings(
    document_id: int,
    curr_user: models.User = Depends(check_permission("delete"))
):
    rag.remove_document(document_id)
    return {"message": f"Embeddings removed for document {document_id}"}


@router.post("/search", response_model=list[ChunkOut])
def do_semantic_search(
    body: SearchQuery,
    curr_user: models.User = Depends(get_logged_in_user)
):
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cant be empty")

    results = rag.semantic_search(query=body.query, top_k=body.top_k)
    output = []
    for r in results:
        output.append(ChunkOut(
            document_id=r["document_id"],
            title=r["title"],
            chunk_text=r["chunk_text"],
            score=r["score"]
        ))
    return output


@router.get("/context/{document_id}")
def get_doc_context(
    document_id: int,
    curr_user: models.User = Depends(get_logged_in_user)
):
    chunks = rag.get_document_context(document_id)
    if not chunks:
        return {"document_id": document_id, "chunks": [], "message": "No chunks found. Index the document first."}
    return {"document_id": document_id, "total_chunks": len(chunks), "chunks": chunks}
