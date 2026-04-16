import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from core.database import get_db
from core import models
from core.schemas import DocOut
from core.auth import get_logged_in_user, check_permission

router = APIRouter()

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

OK_EXTENSIONS = {".pdf", ".txt", ".docx"}


@router.post("/upload", response_model=DocOut, status_code=status.HTTP_201_CREATED)
def upload_doc(
    title: str = Form(...),
    company_name: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    curr_user: models.User = Depends(check_permission("upload"))
):
    ext = Path(file.filename).suffix.lower()
    if ext not in OK_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {ext}")

    fname = f"{curr_user.id}_{file.filename}"
    save_path = UPLOAD_FOLDER / fname

    with open(save_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    doc = models.Document(
        title=title,
        company_name=company_name,
        document_type=document_type,
        file_path=str(save_path),
        uploaded_by=curr_user.id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("", response_model=list[DocOut])
def get_all_docs(
    db: Session = Depends(get_db),
    curr_user: models.User = Depends(get_logged_in_user)
):
    all_docs = db.query(models.Document).all()
    return all_docs


@router.get("/search", response_model=list[DocOut])
def search_docs(
    title: Optional[str] = None,
    company_name: Optional[str] = None,
    document_type: Optional[str] = None,
    db: Session = Depends(get_db),
    curr_user: models.User = Depends(get_logged_in_user)
):
    q = db.query(models.Document)
    if title:
        q = q.filter(models.Document.title.ilike(f"%{title}%"))
    if company_name:
        q = q.filter(models.Document.company_name.ilike(f"%{company_name}%"))
    if document_type:
        q = q.filter(models.Document.document_type == document_type)
    return q.all()


@router.get("/{document_id}", response_model=DocOut)
def get_one_doc(
    document_id: int,
    db: Session = Depends(get_db),
    curr_user: models.User = Depends(get_logged_in_user)
):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doc(
    document_id: int,
    db: Session = Depends(get_db),
    curr_user: models.User = Depends(check_permission("delete"))
):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    p = Path(doc.file_path)
    if p.exists():
        p.unlink()

    from core.rag import remove_document
    remove_document(document_id)

    db.delete(doc)
    db.commit()
