from __future__ import annotations

import hashlib

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.RAG.loader import load_pdf
from app.RAG.pipeline import ask_pdf
from app.RAG.vector_store import index_documents


# ============================================================
# ENV
# ============================================================

load_dotenv()


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="StudyMate API",
    description="Backend API for StudyMate",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST SCHEMA
# ============================================================

class PDFQuestion(BaseModel):

    document_id: str

    question: str


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():

    return {
        "status": "ok",
        "message": "StudyMate API is running",
    }


@app.get("/health")
def health():

    return {
        "status": "healthy",
    }


# ============================================================
# UPLOAD PDF
# ============================================================

@app.post("/rag/upload")
async def upload_pdf(
    file: UploadFile = File(...)
):

    # --------------------------------------------------------
    # CHECK FILE
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is missing.",
        )

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    # --------------------------------------------------------
    # READ FILE
    # --------------------------------------------------------

    try:

        file_bytes = await file.read()

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Could not read uploaded file: {e}",
        )

    if not file_bytes:

        raise HTTPException(
            status_code=400,
            detail="Uploaded PDF is empty.",
        )

    # --------------------------------------------------------
    # CREATE DOCUMENT ID
    # --------------------------------------------------------

    document_id = hashlib.sha256(
        file_bytes
    ).hexdigest()

    # --------------------------------------------------------
    # PINECONE NAMESPACE
    # --------------------------------------------------------

    namespace = (
        f"document-{document_id[:16]}"
    )

    # --------------------------------------------------------
    # LOAD + CHUNK PDF
    # --------------------------------------------------------

    try:

        documents = load_pdf(
            file_bytes=file_bytes,
            filename=file.filename,
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Could not process PDF: {e}",
        )

    if not documents:

        raise HTTPException(
            status_code=400,
            detail=(
                "No readable text could be extracted "
                "from the PDF."
            ),
        )

    # --------------------------------------------------------
    # INDEX DOCUMENT
    # --------------------------------------------------------

    try:

        indexed_chunks = index_documents(
            documents=documents,
            namespace=namespace,
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Could not index PDF: {e}",
        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {

        "status": "success",

        "message": (
            "PDF uploaded and indexed successfully."
        ),

        "document_id": document_id,

        "filename": file.filename,

        "chunks": indexed_chunks,

    }


# ============================================================
# ASK QUESTION ABOUT PDF
# ============================================================

@app.post("/rag/ask")
def ask_question(
    request: PDFQuestion
):

    # --------------------------------------------------------
    # VALIDATE QUESTION
    # --------------------------------------------------------

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    # --------------------------------------------------------
    # VALIDATE DOCUMENT ID
    # --------------------------------------------------------

    document_id = request.document_id.strip()

    if not document_id:

        raise HTTPException(
            status_code=400,
            detail="Document ID cannot be empty.",
        )

    # --------------------------------------------------------
    # CREATE NAMESPACE
    # --------------------------------------------------------

    namespace = (
        f"document-{document_id[:16]}"
    )

    # --------------------------------------------------------
    # RAG QUERY
    # --------------------------------------------------------

    try:

        result = ask_pdf(
            question=question,
            namespace=namespace,
            k=10,
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"RAG query failed: {e}",
        )

    # --------------------------------------------------------
    # SOURCES
    #
    # ask_pdf() now returns dictionaries:
    #
    # {
    #     "text": "...",
    #     "score": 0.82,
    #     "filename": "test.pdf",
    #     "page": 6,
    #     ...
    # }
    # --------------------------------------------------------

    sources = []

    seen_sources = set()

    for document in result.get(
        "documents",
        [],
    ):

        filename = document.get(
            "filename",
            "unknown",
        )

        page = document.get(
            "page",
            None,
        )

        page_label = document.get(
            "page_label",
            page,
        )

        source_key = (
            filename,
            page,
        )

        # ----------------------------------------------------
        # REMOVE DUPLICATE FILE + PAGE SOURCES
        # ----------------------------------------------------

        if source_key in seen_sources:
            continue

        seen_sources.add(
            source_key
        )

        sources.append(
            {
                "filename": filename,

                "page": page,

                "page_label": page_label,
            }
        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {

        "status": "success",

        "answer": result.get(
            "answer",
            "",
        ),

        "sources": sources,

    }