# Financial Document Management API

FastAPI project with RAG (semantic search) for financial documents.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file and add your keys:
```
GEMINI_API_KEY=your_key
SECRET_KEY=any_random_string
```

## Run

```bash
cd myapp
uvicorn main:app --reload
```

## Seed default roles

```bash
python seed_roles.py
```

## API Docs

Open http://127.0.0.1:8000/docs

## Endpoints

### Auth
- POST /auth/register
- POST /auth/login

### Documents
- POST /documents/upload
- GET /documents
- GET /documents/{document_id}
- DELETE /documents/{document_id}
- GET /documents/search

### Roles & Users
- POST /roles/create
- POST /users/assign-role
- GET /users/{id}/roles
- GET /users/{id}/permissions

### RAG
- POST /rag/index-document
- DELETE /rag/remove-document/{id}
- POST /rag/search
- GET /rag/context/{document_id}
