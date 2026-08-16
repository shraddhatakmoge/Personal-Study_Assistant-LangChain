from pathlib import Path

from app.RAG.loader import load_pdf
from app.RAG.vector_store import index_documents
from app.RAG.pipeline import ask_pdf


# ============================================================
# CONFIG
# ============================================================

PDF_PATH = Path("test.pdf")

NAMESPACE = "test-document"


# ============================================================
# 1. LOAD + CHUNK PDF
# ============================================================

pdf_bytes = PDF_PATH.read_bytes()

documents = load_pdf(
    pdf_bytes,
    PDF_PATH.name,
)

print(
    f"Loaded chunks: {len(documents)}"
)


# ============================================================
# 2. INDEX CHUNKS INTO PINECONE
# ============================================================

indexed_chunks = index_documents(
    documents,
    namespace=NAMESPACE,
)

print(
    f"Uploaded to Pinecone: {indexed_chunks} chunks"
)


# ============================================================
# 3. ASK QUESTION
# ============================================================

result = ask_pdf(
    question="What is this document about?",
    namespace=NAMESPACE,
    k=6,
)


# ============================================================
# 4. ANSWER
# ============================================================

print(
    "\nANSWER:"
)

print(
    result.get(
        "answer",
        "",
    )
)


# ============================================================
# 5. SOURCES
# ============================================================

print(
    "\nSOURCES:"
)


for i, document in enumerate(
    result.get(
        "documents",
        [],
    ),
    start=1,
):

    print(
        f"\n--- SOURCE {i} ---"
    )

    print(
        "Filename:",
        document.get(
            "filename",
            "unknown",
        ),
    )

    print(
        "Page:",
        document.get(
            "page",
            "unknown",
        ),
    )

    print(
        "Score:",
        document.get(
            "score",
            0,
        ),
    )

    print(
        "Chunk ID:",
        document.get(
            "chunk_id",
            "unknown",
        ),
    )