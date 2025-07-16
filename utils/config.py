import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file


# Configuration via environment variables
LOG_DIR = os.getenv("LOG_DIR", "logs")
MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10 * 1024 * 1024))
BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
