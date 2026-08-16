from io import BytesIO

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_pdf(file_bytes: bytes, filename: str):

    # ---------------------------------------------------------
    # Save uploaded bytes temporarily because PyPDFLoader
    # expects a file path.
    # ---------------------------------------------------------

    import tempfile
    import os

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf",
    ) as temp_file:

        temp_file.write(file_bytes)
        temp_path = temp_file.name

    try:

        # -----------------------------------------------------
        # LOAD PDF
        # -----------------------------------------------------

        loader = PyPDFLoader(temp_path)

        pages = loader.load()

    finally:

        if os.path.exists(temp_path):
            os.remove(temp_path)

    if not pages:
        return []

    # ---------------------------------------------------------
    # CLEAN METADATA
    # ---------------------------------------------------------

    for page in pages:

        page.metadata["filename"] = filename

        # PyPDFLoader uses zero-based page numbers.
        page_number = page.metadata.get("page")

        if page_number is not None:
            page.metadata["page"] = int(page_number) + 1
            page.metadata["page_label"] = str(
                int(page_number) + 1
            )

        # Remove unnecessary metadata that can pollute
        # Pinecone records.
        page.metadata.pop("producer", None)
        page.metadata.pop("creator", None)
        page.metadata.pop("creationdate", None)
        page.metadata.pop("moddate", None)

    # ---------------------------------------------------------
    # CHUNKING
    # ---------------------------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    chunks = splitter.split_documents(pages)

    # ---------------------------------------------------------
    # ADD CHUNK IDS
    # ---------------------------------------------------------

    for i, chunk in enumerate(chunks):

        chunk.metadata["chunk_id"] = i

        chunk.metadata["text"] = chunk.page_content

    return chunks