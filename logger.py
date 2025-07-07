import logging
import os
from typing import Optional

def setup_logger(log_file: str = 'app.log', level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging configuration that goes to both file and console
    """
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure main logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join('logs', log_file)),
            logging.StreamHandler()
        ]
    )
    
    # Suppress HTTP request logs from requests library
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger instance
    """
    return logging.getLogger(name) 