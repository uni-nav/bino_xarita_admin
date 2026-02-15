
import logging
import sys
from app.core.config import settings

def setup_logging():
    """
    Configure logging for the application.
    JSON formatting could be added here for better production log parsing.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            # File handler can be added if needed, but stdout is best for Docker
        ]
    )
    
    # Set levels for third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # If DEBUG is on, set lower level
    if settings.DEBUG:
        logging.getLogger("app").setLevel(logging.DEBUG)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
