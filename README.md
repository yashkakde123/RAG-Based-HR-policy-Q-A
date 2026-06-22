
### RAG-Based Company Policy Q&A System



---

## 🔍 Project Overview
This application is an internal-use conversational web application designed to ingest corporate policy documents (such as HR manuals, IT security guidelines, and leave policies) and provide employees with a conversational chatbot interface [5]. 

By utilizing **Retrieval-Augmented Generation (RAG)**, the system ensures all answers are strictly grounded in company data, mitigating the risk of LLM hallucinations [5].

### 🛠️ Tech Stack & Architecture
*   **Frontend UI:** Streamlit (Forced Light Theme with custom CSS styling) [1]
*   **Orchestration:** LangChain (Decoupled, modular design) [12]
*   **Vector Database:** ChromaDB (Local, SQLite-backed index) [7]
*   **Embeddings:** Hugging Face `all-MiniLM-L6-v2` (Local, 384-dimensional dense vectors) [7, 10]
*   **Local LLM:** Meta Llama 3.2 (3B Parameters via Ollama) [10]
*   **Authentication:** Firebase Auth (Client-side REST API + Server-side Admin SDK verification)

---

## 🚀 Key Features
*   **Local Data Sovereignty:** All document processing, vector search, and LLM generations occur entirely on local hardware, ensuring private corporate data never leaves the network [8, 12].
*   **Strict Grounding:** Zero-temperature LLM configuration combined with rigid system instructions. If the context does not contain the answer, the model strictly outputs `"I do not know."` [10, 14]
*   **Audit-Ready Citations:** Appends source document metadata (file name and page number) as well as the mathematical vector similarity score [10, 14].
*   **Identity Management:** Secure login, account registration, and password recovery portal powered by Firebase.
*   **Role Segregation:** Restricts the document ingestion pipeline exclusively to verified administrators (e.g., accounts ending in `@cdac.in` or `admin@test.com`) [14].

---

## 📂 Directory Structure
```text
rag-policy-system/
│
├── .streamlit/
│   ├── config.toml             # Forces light theme settings globally
│   └── secrets.toml            # Firebase Web API keys (KEEP PRIVATE - Ignored by Git)
│
├── config/
│   ├── firebase_creds.json.example   # Template for Admin SDK Private Key
│   └── firebase_creds.json           # Firebase Admin SDK Private Key (KEEP PRIVATE - Ignored by Git)
│
├── data/
│   └── documents/              # Place raw policy PDFs here for ingestion
│
├── chroma_db/                  # Automatically generated local vector storage
│
├── modules/
│   ├── __init__.py             # Makes folder a Python package
│   ├── auth_service.py         # Firebase Authentication & Reset handlers
│   ├── ingestion.py            # PDF document parsing and text chunking
│   ├── database.py             # Embedding translation and vector queries
│   └── generation.py           # Grounded Llama 3.2 generation and rewriter
│
├── app.py                      # Streamlit UI & Route controller
├── requirements.txt            # System dependencies
├── .gitignore                  # Keeps private keys out of GitHub
└── README.md                   # Setup and execution guide


⚙️ Setup and Installation Instructions
Follow these steps to set up and run the application on your local machine:
1. Prerequisites
Ensure your computer has the following installed:
Python: Version 3.10 to 3.12 (Verify with python --version)
Git: (Optional, for cloning the repository)
Ollama: (Download and install from ollama.com)
2. Clone and Setup Environment
 Create a Python virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install all system dependencies
pip install -r requirements.txt
3. Setup the Local LLM (Ollama)
With the Ollama app running in your background taskbar, open a terminal and run the following command to download the optimized Llama 3.2 model [10]:
code
Bash
ollama pull llama3.2
(This will download approximately 2.0 GB of model weights. Llama 3.2 is highly optimized to run locally on consumer-grade GPUs like the NVIDIA GTX 1650 Ti) [8, 10].

4. Configure Firebase Credentials (KEEP PRIVATE)
This project uses two sets of credentials. You must set them up manually before running:
Step A: Configure .streamlit/secrets.toml
Create a folder named .streamlit and a file inside it named secrets.toml [12]. Paste your Firebase Web App config parameters [12]:
code
Toml
[firebase]
apiKey = "YOUR_FIREBASE_API_KEY"
authDomain = "your-app-id.firebaseapp.com"
projectId = "your-app-id"
storageBucket = "your-app-id.firebasestorage.app"
messagingSenderId = "1234567890"
appId = "1:1234567890:web:abcde12345"
measurementId = "G-XXXXXXXXXX"
Step B: Configure config/firebase_creds.json
Go to your Firebase Console -> Project Settings -> Service Accounts.
Click Generate New Private Key. A .json file will download to your computer.
Rename this file exactly to firebase_creds.json and place it inside the config/ folder.
Step C: Enable Email Sign-In
In your Firebase Console -> Authentication -> Sign-in method, enable the Email/Password provider.

5. Running the Application
Place 2 or 3 corporate policy PDFs inside the data/documents/ folder.
In your activated terminal, launch the Streamlit frontend:
code
Bash
streamlit run app.py
Your default web browser will automatically open to http://localhost:8501.
