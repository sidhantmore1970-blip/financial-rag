# Financial Document Management API

FastAPI + SQLite + Gemini AI + FAISS — financial document management with semantic RAG search.



## Quick Start


### 2. Install dependencies

python -m venv venv

pip install -r requirements.txt

### 3. Configure environment

```

# create .env — add your GEMINI_API_KEY and SECRET_KEY
```

Get a free Gemini API key at: https://aistudio.google.com/app/apikey

### 4. Create default roles

```bash
python seed_roles.py
```

### 5. Run the server

```bash
uvicorn main:app --reload
```

Open http://localhost:8000/docs for the interactive Swagger UI.

---

## API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login → JWT token |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/documents/upload` | Upload document (multipart/form-data) |
| GET | `/documents` | List all documents |
| GET | `/documents/{id}` | Get document metadata |
| DELETE | `/documents/{id}` | Delete document + embeddings |
| GET | `/documents/search` | Filter by title/company/type |

### Roles & Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/roles/create` | Create a role (Admin only) |
| POST | `/users/assign-role` | Assign role to user (Admin only) |
| GET | `/users/{id}/roles` | List user's roles |
| GET | `/users/{id}/permissions` | List user's merged permissions |

### RAG / Semantic Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rag/index-document?document_id=1` | Index a document into FAISS |
| DELETE | `/rag/remove-document/{id}` | Remove document embeddings |
| POST | `/rag/search` | Semantic search with reranking |
| GET | `/rag/context/{id}` | Get stored chunks for a document |

---

## Permissions Model

| Role | Permissions |
|------|-------------|
| Admin | `full_access` (everything) |
| Financial Analyst | `upload`, `view`, `edit` |
| Auditor | `view` |
| Client | `view` |

---

## RAG Pipeline

```
Document File
    ↓
Text Extraction (PyMuPDF for PDF, UTF-8 for .txt)
    ↓
Chunking (LangChain RecursiveCharacterTextSplitter, 800 chars, 100 overlap)
    ↓
Gemini Embeddings (models/embedding-001, 768-dim, L2-normalised)
    ↓
FAISS IndexFlatIP (cosine similarity via inner product on normalised vectors)
    ↓  [persisted to vector_store/index.faiss + metadata.pkl]
    ↓
User Query → Gemini Embedding → FAISS top-20
    ↓
Gemini Reranker (gemini-1.5-flash scores each chunk 0-10)
    ↓
Top-5 Most Relevant Chunks
```

