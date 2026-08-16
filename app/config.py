import os

from dotenv import load_dotenv


load_dotenv()


# ============================================================
# MODEL
# ============================================================

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "llama-3.1-8b-instant",
)