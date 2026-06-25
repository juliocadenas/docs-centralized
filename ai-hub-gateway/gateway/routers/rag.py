"""
AI Hub Gateway - RAG Router
Endpoints for Retrieval-Augmented Generation using ChromaDB + nomic-embed-text.

Features:
- Upload documents (txt, md, pdf text) -> chunk -> embed -> store
- Query with natural language -> semantic search -> LLM augmented answer
- Manage multiple knowledge collections
- OpenAI-compatible embeddings via Ollama
"""
import os
import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
import httpx

from ..config import OLLAMA_BASE_URL, SEAGATE_ROOT

logger = logging.getLogger("ai-hub-gateway.rag")

router = APIRouter(prefix="/v1/rag", tags=["RAG"])

# ChromaDB will be lazily initialized
_chroma_client = None
_chroma_persist_dir = str(SEAGATE_ROOT / "chromadb")

# Default embedding model
EMBEDDING_MODEL = "nomic-embed-text"

# ============================================================
# ChromaDB initialization (lazy)
# ============================================================
def get_chroma_client():
    """Initialize ChromaDB client lazily."""
    global _chroma_client
    if _chroma_client is None:
        try:
            import chromadb
            os.makedirs(_chroma_persist_dir, exist_ok=True)
            _chroma_client = chromadb.PersistentClient(path=_chroma_persist_dir)
            logger.info(f"ChromaDB initialized at {_chroma_persist_dir}")
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="ChromaDB no instalado. Ejecuta: pip install chromadb"
            )
    return _chroma_client


# ============================================================
# Helper: generate embeddings via Ollama
# ============================================================
async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts using nomic-embed-text via Ollama."""
    embeddings = []
    async with httpx.AsyncClient() as client:
        for text in texts:
            try:
                resp = await client.post(
                    f"{OLLAMA_BASE_URL}/api/embeddings",
                    json={"model": EMBEDDING_MODEL, "prompt": text},
                    timeout=30.0
                )
                resp.raise_for_status()
                data = resp.json()
                embeddings.append(data["embedding"])
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}")
                raise HTTPException(status_code=500, detail=f"Error generando embeddings: {e}")
    return embeddings


# ============================================================
# Helper: chunk text into smaller pieces
# ============================================================
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks for better retrieval."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks


# ============================================================
# Helper: extract text from file
# ============================================================
def extract_text(content: bytes, filename: str) -> str:
    """Extract text from various file formats."""
    if filename.endswith('.txt') or filename.endswith('.md'):
        return content.decode('utf-8', errors='ignore')
    elif filename.endswith('.pdf'):
        # Try PyMuPDF (fitz) first, then pdfplumber, then plain text
        try:
            import fitz  # PyMuPDF
            import io
            doc = fitz.open(stream=content, filetype="pdf")
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            return text
        except ImportError:
            pass
        # Fallback: return raw (may be garbled but better than nothing)
        return content.decode('utf-8', errors='ignore')
    elif filename.endswith('.json'):
        return content.decode('utf-8', errors='ignore')
    else:
        return content.decode('utf-8', errors='ignore')


# ============================================================
# Models
# ============================================================
class QueryRequest(BaseModel):
    """RAG query request."""
    query: str
    collection: str = "default"
    n_results: int = 5
    model: str = "qwen2.5:7b"  # LLM for generating answer
    system_prompt: Optional[str] = None


class CreateCollectionRequest(BaseModel):
    """Create a new knowledge collection."""
    name: str
    description: str = ""


# ============================================================
# Endpoints
# ============================================================

@router.get("/collections")
async def list_collections():
    """List all knowledge collections."""
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        result = []
        for col in collections:
            c = client.get_collection(col)
            result.append({
                "name": col,
                "count": c.count(),
                "metadata": c.metadata
            })
        return {"collections": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections")
async def create_collection(request: CreateCollectionRequest):
    """Create a new knowledge collection."""
    try:
        client = get_chroma_client()
        col = client.get_or_create_collection(
            name=request.name,
            metadata={"description": request.description}
        )
        return {"status": "created", "collection": request.name, "count": col.count()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collections/{name}")
async def delete_collection(name: str):
    """Delete a knowledge collection."""
    try:
        client = get_chroma_client()
        client.delete_collection(name)
        return {"status": "deleted", "collection": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form("default"),
    chunk_size: int = Form(500)
):
    """
    Upload a document to a knowledge collection.
    Supports: .txt, .md, .pdf, .json
    The text is chunked, embedded, and stored in ChromaDB.
    """
    try:
        content = await file.read()
        text = extract_text(content, file.filename or "document.txt")
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="El documento no contiene texto extraible")
        
        # Chunk the text
        chunks = chunk_text(text, chunk_size=chunk_size)
        
        # Generate embeddings
        embeddings = await generate_embeddings(chunks)
        
        # Store in ChromaDB
        client = get_chroma_client()
        col = client.get_or_create_collection(name=collection)
        
        # Generate unique IDs
        import uuid
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [{"source": file.filename, "chunk": i, "chars": len(c)} for i, c in enumerate(chunks)]
        
        col.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        
        return {
            "status": "success",
            "filename": file.filename,
            "collection": collection,
            "chunks_created": len(chunks),
            "total_in_collection": col.count()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def rag_query(request: QueryRequest):
    """
    Query the knowledge base using RAG:
    1. Embed the query
    2. Search for similar chunks in ChromaDB
    3. Use the retrieved context to generate an answer with the LLM
    """
    try:
        # Step 1: Search relevant chunks
        query_embedding = (await generate_embeddings([request.query]))[0]
        
        client = get_chroma_client()
        try:
            col = client.get_collection(request.collection)
        except Exception:
            raise HTTPException(
                status_code=404,
                detail=f"Colección '{request.collection}' no encontrada. Sube documentos primero."
            )
        
        results = col.query(
            query_embeddings=[query_embedding],
            n_results=request.n_results
        )
        
        # Extract context from results
        context_chunks = results.get("documents", [[]])[0]
        if not context_chunks:
            return {
                "answer": "No se encontraron documentos relevantes en la colección.",
                "sources": [],
                "query": request.query
            }
        
        context = "\n\n---\n\n".join(context_chunks)
        
        # Step 2: Generate answer with LLM using the context
        system = request.system_prompt or (
            "Eres un asistente que responde preguntas basándose en el contexto proporcionado. "
            "Si la información no está en el contexto, dilo claramente. "
            "Cita las fuentes cuando sea relevante."
        )
        
        user_message = f"""Contexto de la base de conocimientos:

{context}

---
Pregunta: {request.query}

Responde basándote en el contexto anterior. Sé preciso y cita las fuentes."""

        # Call Ollama for the answer
        async with httpx.AsyncClient() as client_http:
            resp = await client_http.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": request.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_message}
                    ],
                    "stream": False
                },
                timeout=60.0
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("message", {}).get("content", "")
        
        # Prepare sources info
        metadatas = results.get("metadatas", [[]])[0]
        sources = []
        for i, meta in enumerate(metadatas[:request.n_results]):
            sources.append({
                "source": meta.get("source", "unknown"),
                "chunk": meta.get("chunk", 0),
                "preview": context_chunks[i][:150] + "..." if len(context_chunks[i]) > 150 else context_chunks[i],
                "relevance": "high" if i < 2 else "medium" if i < 4 else "low"
            })
        
        return {
            "answer": answer,
            "sources": sources,
            "query": request.query,
            "collection": request.collection,
            "model": request.model,
            "chunks_retrieved": len(context_chunks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{name}/info")
async def collection_info(name: str):
    """Get information about a specific collection."""
    try:
        client = get_chroma_client()
        col = client.get_collection(name)
        
        # Get a sample of documents
        sample = col.peek(limit=5)
        
        return {
            "name": name,
            "count": col.count(),
            "metadata": col.metadata,
            "sample_documents": sample.get("documents", [])[:3]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def rag_health():
    """Check if RAG system is available."""
    try:
        import chromadb
        client = get_chroma_client()
        collections = client.list_collections()
        return {
            "status": "ok",
            "chromadb_version": chromadb.__version__,
            "persist_dir": _chroma_persist_dir,
            "collections": len(collections),
            "embedding_model": EMBEDDING_MODEL
        }
    except ImportError:
        return {
            "status": "not_installed",
            "message": "ChromaDB no instalado. Ejecuta: pip install chromadb pymupdf"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}