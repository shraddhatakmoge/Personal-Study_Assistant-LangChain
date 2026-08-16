from pathlib import Path

from app.RAG.loader import load_pdf
from app.RAG.vector_store import index_documents
from app.RAG.pipeline import ask_pdf


PDF_PATH = Path("test.pdf")

NAMESPACE = "test-document"


# 1. Load + chunk PDF
pdf_bytes = PDF_PATH.read_bytes()

documents = load_pdf(
    pdf_bytes,
    PDF_PATH.name,
)

print(f"Loaded chunks: {len(documents)}")


# 2. Upload chunks to Pinecone
index_documents(
    documents,
    namespace=NAMESPACE,
)

print("Uploaded to Pinecone.")


# 3. Ask question
result = ask_pdf(
    question="What is this document about?",
    namespace=NAMESPACE,
)

print("\nANSWER:")
print(result["answer"])


print("\nSOURCES:")

for document in result["documents"]:

    print(
        "Page:",
        document.metadata.get("page", "unknown") + 1
        if isinstance(document.metadata.get("page"), int)
        else "unknown",
    )