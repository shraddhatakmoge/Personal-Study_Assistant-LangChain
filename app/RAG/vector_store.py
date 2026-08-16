import hashlib
import os

from dotenv import load_dotenv
from pinecone import Pinecone


load_dotenv()


# ============================================================
# CONFIG
# ============================================================

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")


if not PINECONE_API_KEY:
    raise ValueError(
        "PINECONE_API_KEY is missing from .env"
    )


if not PINECONE_INDEX_NAME:
    raise ValueError(
        "PINECONE_INDEX_NAME is missing from .env"
    )


# ============================================================
# PINECONE
# ============================================================

pc = Pinecone(
    api_key=PINECONE_API_KEY
)

index = pc.Index(
    PINECONE_INDEX_NAME
)


# ============================================================
# EMBEDDING CONFIG
# ============================================================

# This MUST match the model configured for your Pinecone index.
EMBEDDING_MODEL = "llama-text-embed-v2"

# Your existing Pinecone index is configured for 384 dimensions.
EMBEDDING_DIMENSION = 384


# ============================================================
# EMBED DOCUMENTS
# ============================================================

def embed_documents(texts):
    """
    Generate embeddings for document chunks using
    Pinecone's hosted embedding model.

    No Hugging Face model, sentence-transformers,
    or PyTorch is loaded locally.
    """

    if not texts:
        return []

    result = pc.inference.embed(
        model=EMBEDDING_MODEL,
        inputs=texts,
        parameters={
            "input_type": "passage",
            "truncate": "END",
            "dimension": EMBEDDING_DIMENSION,
        },
    )

    return [
        embedding.values
        for embedding in result.data
    ]


# ============================================================
# EMBED QUERY
# ============================================================

def embed_query(text):
    """
    Generate an embedding for a user's question.
    """

    if not text or not text.strip():
        raise ValueError(
            "Query text cannot be empty."
        )

    result = pc.inference.embed(
        model=EMBEDDING_MODEL,
        inputs=[text],
        parameters={
            "input_type": "query",
            "truncate": "END",
            "dimension": EMBEDDING_DIMENSION,
        },
    )

    return result.data[0].values


# ============================================================
# CREATE STABLE VECTOR ID
# ============================================================

def _make_vector_id(
    namespace: str,
    text: str,
    metadata: dict,
) -> str:

    """
    Creates a deterministic ID for each chunk.

    Re-uploading the same PDF/chunk therefore produces
    the same vector ID instead of creating random IDs.
    """

    page = metadata.get(
        "page",
        "",
    )

    chunk_id = metadata.get(
        "chunk_id",
        "",
    )

    raw = (
        f"{namespace}|"
        f"{page}|"
        f"{chunk_id}|"
        f"{text}"
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


# ============================================================
# INDEX DOCUMENTS
# ============================================================

def index_documents(
    documents,
    namespace: str,
):

    if not documents:
        raise ValueError(
            "No documents were provided for indexing."
        )


    # ========================================================
    # CLEAR EXISTING NAMESPACE
    # ========================================================

    try:

        print(
            f"Clearing existing namespace: {namespace}"
        )

        index.delete(
            delete_all=True,
            namespace=namespace,
        )

    except Exception as e:

        print(
            f"Warning: Could not clear namespace: {e}"
        )


    # ========================================================
    # PREPARE UNIQUE CHUNKS
    # ========================================================

    valid_documents = []

    seen_text = set()


    for document in documents:

        text = document.page_content.strip()

        if not text:
            continue


        # ----------------------------------------------------
        # REMOVE DUPLICATE CHUNKS
        # ----------------------------------------------------

        normalized_text = " ".join(
            text.split()
        ).lower()


        if normalized_text in seen_text:
            continue


        seen_text.add(
            normalized_text
        )

        valid_documents.append(
            document
        )


    if not valid_documents:

        raise ValueError(
            "No valid text chunks were generated."
        )


    # ========================================================
    # EXTRACT TEXT
    # ========================================================

    texts = [
        document.page_content.strip()
        for document in valid_documents
    ]


    print(
        f"Generating Pinecone embeddings for "
        f"{len(texts)} unique chunks..."
    )


    # ========================================================
    # GENERATE EMBEDDINGS
    # ========================================================

    vectors_values = embed_documents(
        texts
    )


    if len(vectors_values) != len(
        valid_documents
    ):

        raise ValueError(
            "Number of embeddings does not match "
            "number of documents."
        )


    # ========================================================
    # CREATE PINECONE VECTORS
    # ========================================================

    vectors = []


    for document, vector in zip(
        valid_documents,
        vectors_values,
    ):

        text = document.page_content.strip()


        # ----------------------------------------------------
        # METADATA
        # ----------------------------------------------------

        metadata = {

            "text": text,

            "filename": document.metadata.get(
                "filename",
                "unknown",
            ),

            "page": document.metadata.get(
                "page",
                None,
            ),

            "page_label": document.metadata.get(
                "page_label",
                None,
            ),

            "chunk_id": document.metadata.get(
                "chunk_id",
                None,
            ),

        }


        # ----------------------------------------------------
        # STABLE VECTOR ID
        # ----------------------------------------------------

        vector_id = _make_vector_id(
            namespace=namespace,
            text=text,
            metadata=metadata,
        )


        vectors.append(
            {
                "id": vector_id,
                "values": vector,
                "metadata": metadata,
            }
        )


    if not vectors:

        raise ValueError(
            "No valid vectors were generated."
        )


    # ========================================================
    # UPSERT IN BATCHES
    # ========================================================

    batch_size = 50


    print(
        f"Uploading {len(vectors)} chunks to Pinecone..."
    )


    for i in range(
        0,
        len(vectors),
        batch_size,
    ):

        batch = vectors[
            i:i + batch_size
        ]


        index.upsert(
            vectors=batch,
            namespace=namespace,
        )


    print(
        "Documents successfully indexed."
    )


    return len(vectors)


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve_documents(
    question: str,
    namespace: str,
    k: int = 6,
):

    # ========================================================
    # VALIDATE QUESTION
    # ========================================================

    if not question or not question.strip():

        raise ValueError(
            "Question cannot be empty."
        )


    # ========================================================
    # EMBED QUESTION
    # ========================================================

    query_vector = embed_query(
        question
    )


    # ========================================================
    # SEARCH MORE THAN REQUIRED
    # ========================================================

    search_k = max(
        k * 4,
        20,
    )


    result = index.query(
        vector=query_vector,
        top_k=search_k,
        namespace=namespace,
        include_metadata=True,
    )


    matches = result.get(
        "matches",
        [],
    )


    documents = []


    # ========================================================
    # DUPLICATE DETECTION
    # ========================================================

    seen_text = set()


    for match in matches:

        metadata = match.get(
            "metadata",
            {},
        )


        text = metadata.get(
            "text",
            "",
        )


        if not text:
            continue


        # ----------------------------------------------------
        # NORMALIZE TEXT
        # ----------------------------------------------------

        normalized_text = " ".join(
            text.split()
        ).lower()


        if normalized_text in seen_text:
            continue


        seen_text.add(
            normalized_text
        )


        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        score = match.get(
            "score",
            0,
        )


        # ----------------------------------------------------
        # STORE RESULT
        # ----------------------------------------------------

        documents.append(
            {
                "text": text,

                "score": float(
                    score
                ),

                "filename": metadata.get(
                    "filename",
                    "unknown",
                ),

                "page": metadata.get(
                    "page",
                    None,
                ),

                "page_label": metadata.get(
                    "page_label",
                    None,
                ),

                "chunk_id": metadata.get(
                    "chunk_id",
                    None,
                ),
            }
        )


        # ----------------------------------------------------
        # STOP AFTER K UNIQUE RESULTS
        # ----------------------------------------------------

        if len(documents) >= k:
            break


    # ========================================================
    # DEBUG OUTPUT
    # ========================================================

    print()
    print("=" * 60)
    print("RETRIEVED UNIQUE CHUNKS")
    print("=" * 60)


    for i, document in enumerate(
        documents,
        start=1,
    ):

        print(
            f"\n--- CHUNK {i} ---"
        )

        print(
            f"Score: {document['score']}"
        )

        print(
            f"Filename: {document['filename']}"
        )

        print(
            f"Page: {document['page']}"
        )

        print(
            f"Chunk ID: {document['chunk_id']}"
        )

        print(
            f"Text:\n{document['text'][:1000]}"
        )


    print(
        "=" * 60
    )


    return documents