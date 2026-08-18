**StudyMate — Personal AI Study Assistant**


<img width="1839" height="1010" alt="Screenshot 2026-08-17 082644" src="https://github.com/user-attachments/assets/96bc1dd3-1995-4b36-b7cf-7c20353d85ff" />

<img width="1836" height="1015" alt="Screenshot 2026-08-16 220553" src="https://github.com/user-attachments/assets/6e7a5fe7-9aec-4645-83d1-9cb9941d55c2" />

<img width="1836" height="1005" alt="image" src="https://github.com/user-attachments/assets/32c226d3-7b45-45cd-a4c7-19aaa42eb855" />





StudyMate is a personal AI study companion designed to help students learn, research, solve problems, save knowledge, and revise from one place.

It combines an AI assistant with Retrieval-Augmented Generation (RAG) so users can upload study material such as PDFs and ask questions grounded in their own documents.

✨ Features

📚 Learn

Ask StudyMate to explain difficult concepts clearly and step by step.

🔎 Research

Explore topics and find useful information through the research capability.

🧮 Calculate

Solve numerical and calculation-based problems with the calculator tool.

📄 PDF / Document RAG

Upload study material and ask questions about it.

Document
   ↓
Document Loader
   ↓
Text Splitting
   ↓
Embeddings
   ↓
Vector Store
   ↓
Retriever
   ↓
Relevant Context
   ↓
LLM
   ↓
Grounded Answer

📝 Study Notes

Save useful information for later revision.

Users can:

Save notes

View saved notes

Delete individual notes

Clear all notes

🧠 Revision

Use saved knowledge and study material to reinforce understanding and revise previously learned topics.

🏗️ Architecture

                         ┌─────────────────────┐
                         │     Streamlit UI    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    AI Agent Layer   │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
        ┌───────────┐         ┌───────────┐        ┌───────────┐
        │ Calculator│         │ Research  │        │   Notes   │
        └───────────┘         └───────────┘        └───────────┘

                         ┌─────────────────────┐
                         │      RAG Pipeline   │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │ Document Processing │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │ Embeddings / Vector │
                         │       Store         │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │     Retriever       │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │        LLM          │
                         └─────────────────────┘


🛠️ Tech Stack

Technology

Purpose

Python

LangChain

Agent, tools and RAG orchestration

RAG

Grounded question answering

Vector similarity search

Embeddings

Document representation

Streamlit

Interactive UI

FastAPI

Pydantic

Pytest

Testing

⚙️ How It Works

The user asks a question.

The AI agent determines what capability is needed.

For document questions, the RAG pipeline retrieves relevant chunks.

The retrieved context is provided to the LLM.

StudyMate generates the response using the available context.

Example:

Upload:
Transformers_Notes.pdf

Ask:
"Why is positional encoding required?"

StudyMate retrieves relevant sections from the uploaded material and uses them as context for the response.

🚀 Getting Started

1. Clone the repository

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Personal-Study-Assistant-LangChain

2. Create a virtual environment

Windows:

python -m venv venv
venv\Scripts\activate

macOS / Linux:

python3 -m venv venv
source venv/bin/activate

3. Install dependencies

pip install -r requirements.txt

4. Configure environment variables

Create a .env file in the project root and add the model/provider configuration required by your setup.

Example:

MODEL_NAME=your_model_name

Do not commit .env or API keys to GitHub.

5. Run StudyMate

streamlit run app/UI/streamlit_app.py

📄 Using Document RAG

The document workflow is:

Upload PDF
    ↓
Load document
    ↓
Split text into chunks
    ↓
Create embeddings
    ↓
Store vectors
    ↓
Retrieve relevant chunks
    ↓
Generate answer

This allows questions to be answered using the user's uploaded study material instead of relying only on general model knowledge.

📝 Notes System

StudyMate stores notes locally in:

data/notes.json

The Notes UI supports:

Creating/saving study notes

Viewing saved notes

Deleting a single note

Clearing all notes with confirmation

🔐 Security

Never commit credentials.

Keep sensitive values such as API keys in environment variables and make sure .env is listed in .gitignore.

For deployment, use your hosting platform's secret/environment-variable system.

🎯 Project Goal

StudyMate was built around a simple idea:

Make studying more interactive by combining an AI assistant with the learner's own knowledge.

Instead of switching between separate applications for understanding concepts, researching, calculations, reading PDFs, saving notes, and revision, StudyMate brings these workflows together in one study-focused application.

🔮 Future Improvements

Better conversational memory

More document formats

👩‍💻 Author

Shraddha Takmoge

AI / ML Engineer focused on:

Machine Learning

Deep Learning

Generative AI

Large Language Models

RAG

MLOps
