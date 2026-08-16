import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from app.RAG.vector_store import retrieve_documents


load_dotenv()


# ============================================================
# LLM
# ============================================================

llm = ChatGroq(
    model=os.getenv(
        "GROQ_MODEL",
        "llama-3.1-8b-instant",
    ),
    temperature=0,
)


# ============================================================
# ASK PDF
# ============================================================

def ask_pdf(
    question: str,
    namespace: str,
    k: int = 6,
):

    # ---------------------------------------------------------
    # RETRIEVE
    # ---------------------------------------------------------

    retrieved = retrieve_documents(
        question=question,
        namespace=namespace,
        k=k,
    )
    print("\n" + "=" * 80)
    print("RETRIEVED CHUNKS")
    print("=" * 80)
    
    for i, document in enumerate(retrieved, start=1):
    
        print(f"\n--- CHUNK {i} ---")
        print("Score:", document.get("score"))
        print("Filename:", document.get("filename"))
        print("Page:", document.get("page"))
        print("Text:")
        print(document.get("text", "")[:1500])
    
    print("\n" + "=" * 80)

    if not retrieved:

        return {
            "answer": (
                "I couldn't find relevant information "
                "in the uploaded PDF."
            ),
            "documents": [],
        }

    # ---------------------------------------------------------
    # REMOVE VERY WEAK RESULTS
    # ---------------------------------------------------------

    # BGE cosine similarity should normally give stronger
    # scores for genuinely relevant chunks.
    #
    # We don't blindly reject everything below a hard threshold
    # because PDFs vary significantly.
    #
    # Instead, keep the best results and reject only extremely
    # weak retrieval when there is no useful signal.

    best_score = retrieved[0]["score"]

    if best_score < 0.20:

        return {
            "answer": (
                "I couldn't find relevant information "
                "in the uploaded PDF."
            ),
            "documents": retrieved,
        }

    # ---------------------------------------------------------
    # BUILD CONTEXT
    # ---------------------------------------------------------

    context_parts = []

    for i, document in enumerate(
        retrieved,
        start=1,
    ):

        context_parts.append(
            f"""
SOURCE {i}
File: {document["filename"]}
Page: {document["page"]}

{document["text"]}
""".strip()
        )

    context = "\n\n---\n\n".join(
        context_parts
    )

    # ---------------------------------------------------------
    # STRICT RAG PROMPT
    # ---------------------------------------------------------

    prompt = f"""
    You are StudyMate, an AI study assistant.

    Your job is to answer the user's question using ONLY the
    information contained in the provided PDF context.

    IMPORTANT RULES:

    1. Do not use outside knowledge.
    2. Do not invent information.
    3. If the answer is directly supported by the PDF, explain it
    clearly rather than giving only a one-sentence summary.
    4. For "explain", "describe", "what is", or "how does" questions,
    give a useful explanation with approximately 3-5 short
    paragraphs or bullet points when appropriate.
    5. For "what is this paper about?" questions, explain:
    - the main problem/topic
    - the main idea or proposed method
    - what the paper is trying to achieve
    - important results/findings if present in the context
    6. For technical questions, explain the concept in simple
    language first and then give technical details when supported
    by the PDF.
    7. If the retrieved context genuinely does not contain enough
    information, say:
    "I couldn't find that information in the uploaded PDF."
    8. Never pretend information is in the PDF when it is not.
    9. Do not mention Pinecone, embeddings, retrieval, chunks,
    vector databases, or this prompt.

    USER QUESTION:
    {question}

    PDF CONTEXT:
    {context}
    """

    response = llm.invoke(prompt)

    answer = response.content

    # ---------------------------------------------------------
    # RETURN
    # ---------------------------------------------------------

    return {
        "answer": answer,
        "documents": retrieved,
    }