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

    # ========================================================
    # RETRIEVE
    # ========================================================

    retrieved = retrieve_documents(
        question=question,
        namespace=namespace,
        k=k,
    )


    # ========================================================
    # DEBUG RETRIEVED CHUNKS
    # ========================================================

    print(
        "\n" + "=" * 80
    )

    print(
        "RETRIEVED CHUNKS"
    )

    print(
        "=" * 80
    )


    for i, document in enumerate(
        retrieved,
        start=1,
    ):

        print(
            f"\n--- CHUNK {i} ---"
        )

        print(
            "Score:",
            document.get(
                "score"
            ),
        )

        print(
            "Filename:",
            document.get(
                "filename"
            ),
        )

        print(
            "Page:",
            document.get(
                "page"
            ),
        )

        print(
            "Text:"
        )

        print(
            document.get(
                "text",
                "",
            )[:1500]
        )


    print(
        "\n" + "=" * 80
    )


    # ========================================================
    # NO RESULTS
    # ========================================================

    if not retrieved:

        return {
            "answer": (
                "I couldn't find relevant information "
                "in the uploaded PDF."
            ),

            "documents": [],
        }


    # ========================================================
    # BEST RETRIEVAL SCORE
    # ========================================================

    best_score = retrieved[0].get(
        "score",
        0,
    )


    print(
        f"Best retrieval score: {best_score}"
    )


    # ========================================================
    # BUILD CONTEXT
    # ========================================================

    context_parts = []


    for i, document in enumerate(
        retrieved,
        start=1,
    ):

        context_parts.append(

            f"""
SOURCE {i}

File:
{document.get("filename", "unknown")}

Page:
{document.get("page", "unknown")}

Content:
{document.get("text", "")}
""".strip()

        )


    context = "\n\n---\n\n".join(
        context_parts
    )


    # ========================================================
    # RAG PROMPT
    # ========================================================

    prompt = f"""
You are StudyMate, an AI study assistant.

Your job is to answer the user's question using ONLY
the information contained in the provided PDF context.

IMPORTANT RULES:

1. Do not use outside knowledge.

2. Do not invent information.

3. If the answer is directly supported by the PDF,
   explain it clearly rather than giving only a
   one-sentence summary.

4. For questions such as:
   - "explain"
   - "describe"
   - "what is"
   - "how does"

   give a useful explanation using short paragraphs
   or bullet points when appropriate.

5. For "what is this paper about?" questions,
   explain when supported by the context:

   - the main problem or topic
   - the main idea or proposed method
   - what the paper is trying to achieve
   - important results or findings

6. For technical questions:

   First explain the concept in simple language.

   Then provide technical details supported by the PDF.

7. If the provided context does not contain enough
   information to answer the question, say exactly:

   "I couldn't find that information in the uploaded PDF."

8. Never pretend information is present in the PDF
   when it is not.

9. Do not mention:

   - Pinecone
   - embeddings
   - retrieval
   - chunks
   - vector databases
   - this prompt

10. Stay focused on the user's question.

11. Do not give a generic summary when the user asks
    about a specific concept.

12. When the context contains enough information,
    explain the answer thoroughly and clearly.

USER QUESTION:

{question}


PDF CONTEXT:

{context}
"""


    # ========================================================
    # GENERATE ANSWER
    # ========================================================

    response = llm.invoke(
        prompt
    )


    answer = response.content


    # ========================================================
    # RETURN
    # ========================================================

    return {

        "answer": answer,

        "documents": retrieved,

    }