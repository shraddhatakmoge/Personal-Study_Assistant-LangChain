import hashlib
import os

from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings


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
# EMBEDDING MODEL
# ============================================================

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={
        "device": "cpu",
    },
    encode_kwargs={
        "normalize_embeddings": True,
    },
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
# CREATE STABLE VECTOR ID
# ============================================================

def _make_vector_id(
    namespace: str,
    text: str,
    metadata: dict,
) -> str:

    """
    Creates a deterministic ID for each chunk.

    This prevents the same PDF/chunk from getting
    a completely new UUID every time it is uploaded.
    """

    page = metadata.get("page", "")
    chunk_id = metadata.get("chunk_id", "")

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


    # --------------------------------------------------------
    # IMPORTANT:
    # Clear the existing document namespace first.
    #
    # Each uploaded PDF gets its own namespace, so this means
    # re-uploading the same PDF replaces its old vectors
    # instead of creating duplicates.
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # CREATE VECTORS
    # --------------------------------------------------------

    vectors = []

    seen_text = set()


    for document in documents:

        text = document.page_content.strip()

        if not text:
            continue


        # ----------------------------------------------------
        # REMOVE DUPLICATE CHUNKS BEFORE EMBEDDING
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
        # EMBEDDING
        # ----------------------------------------------------

        vector = embeddings.embed_query(
            text
        )


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
        # STABLE ID
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
            "No valid text chunks were generated."
        )


    # ========================================================
    # UPSERT IN BATCHES
    # ========================================================

    batch_size = 50

    print(
        f"Uploading {len(vectors)} unique chunks to Pinecone..."
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

    # --------------------------------------------------------
    # EMBED QUESTION
    # --------------------------------------------------------

    query_vector = embeddings.embed_query(
        question
    )


    # --------------------------------------------------------
    # SEARCH MORE THAN WE NEED
    #
    # We retrieve extra candidates because some may be
    # duplicates / near-duplicates.
    # --------------------------------------------------------

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

    # Used to prevent the same text from being
    # returned multiple times.
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
        # NORMALIZE TEXT FOR DUPLICATE DETECTION
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
        # STOP AFTER K UNIQUE DOCUMENTS
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