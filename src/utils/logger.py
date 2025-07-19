import os
import logging
import inspect
from typing import Optional
from logging.handlers import RotatingFileHandler
from . import config

# Configuration via environment variables
LOG_DIR = config.LOG_DIR
MAX_BYTES = config.MAX_BYTES
BACKUP_COUNT = config.BACKUP_COUNT
LOG_LEVEL = config.LOG_LEVEL

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Returns a logger instance. If name is not provided, it infers the name
    from the calling module's filename.
    Logs are written to logs/<module_basename>.log and also output to console.
    """
    if name is None:
        # Inspect the caller to infer module name
        caller_frame = inspect.stack()[1]
        module = inspect.getmodule(caller_frame[0])
        if module:
            file_path: Optional[str] = getattr(module, "__file__", None)
            if file_path:
                name = os.path.splitext(os.path.basename(file_path))[0]
            else:
                name = "__main__"
        else:
            name = "__main__"

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)

    # File handler with rotation
    log_file = os.path.join(LOG_DIR, f"{name}.log")
    file_handler = RotatingFileHandler(log_file, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT)
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
