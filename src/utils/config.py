from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Base project root (2 levels above this file)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Environment variables
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10 * 1024 * 1024))
BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Langsmith vriables
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT")

# Groq environmental variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME")


_PDF_RELATIVE_DIR = Path(os.getenv("PDF_DIRECTORY", "data/pdfs"))
_DB_RELATIVE_DIR = Path(os.getenv("DB_DIRECTORY", "db"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "my_rag_collection")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DB_NAME = os.getenv("DB_NAME", "showroom_management.db")

# Absolute paths
PDF_DIRECTORY = PROJECT_ROOT / _PDF_RELATIVE_DIR
DB_DIRECTORY = PROJECT_ROOT / _DB_RELATIVE_DIR
DB_PATH = DB_DIRECTORY / DB_NAME

# Create directories if they don’t exist
for directory in [LOG_DIR, PDF_DIRECTORY, DB_DIRECTORY]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {directory}: {e}")

# Langchain env vars
os.environ["LANGCHAIN_TRACING_V2"] = str(LANGSMITH_TRACING).lower()
os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY or ""
os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT or ""
os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT or ""
os.environ["TF_ENABLE_ONEDNN_OPTS"] = '0'
