import logging
import sys
from config import LOG_LEVEL, ENVIRONMENT

# Configure logging
logger = logging.getLogger("DIOS")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Console handler
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "[%(levelname)s] %(asctime)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_logger():
    return logger
