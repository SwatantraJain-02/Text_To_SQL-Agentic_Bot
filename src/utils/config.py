import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

LOG_DIR = os.getenv("LOG_DIR", "logs")
MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10 * 1024 * 1024))
BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME")

_PDF_RELATIVE_DIR = os.getenv("PDF_DIRECTORY", "data/pdfs")
_DB_RELATIVE_DIR = os.getenv("DB_DIRECTORY", "db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "my_rag_collection")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Construct absolute paths and normalize them to ensure clean, resolved paths.
PDF_DIRECTORY = os.path.normpath(os.path.join(PROJECT_ROOT, _PDF_RELATIVE_DIR))
DB_DIRECTORY = os.path.normpath(os.path.join(PROJECT_ROOT, _DB_RELATIVE_DIR))

try:
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(PDF_DIRECTORY, exist_ok=True)
    os.makedirs(DB_DIRECTORY, exist_ok=True)
except OSError as e:
    print(f"Error creating directories: {e}")

os.environ["LANGCHAIN_TRACING_V2"] = str(LANGSMITH_TRACING).lower()
os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY if LANGSMITH_API_KEY else ""
os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT if LANGSMITH_PROJECT else ""
os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT if LANGSMITH_ENDPOINT else ""
