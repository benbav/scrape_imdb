import json
import os
import pandas as pd
from typing import Dict, Any, Optional
from config import IMDBConstants
from logger import get_logger

logger = get_logger(__name__)

class FileManager:
    @staticmethod
    def save_json(data: Dict[str, Any], filename: str) -> None:
        """Save data to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            logger.info(f"Data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")
            raise
    
    @staticmethod
    def load_json(filename: str) -> Dict[str, Any]:
        """Load data from JSON file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            raise
    
    @staticmethod
    def save_csv(df: pd.DataFrame, filename: str, index: bool = False) -> None:
        """Save DataFrame to CSV file"""
        try:
            df.to_csv(filename, index=index)
            logger.info(f"Data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")
            raise
    
    @staticmethod
    def load_csv(filename: str) -> pd.DataFrame:
        """Load DataFrame from CSV file"""
        try:
            return pd.read_csv(filename)
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            raise
    
    @staticmethod
    def file_exists(filename: str) -> bool:
        """Check if file exists"""
        return os.path.exists(filename)
    
    @staticmethod
    def cleanup_temp_files() -> None:
        """Clean up temporary files and directories"""
        files_to_remove = [
            'tempCodeRunnerFile.py',
            IMDBConstants.RATINGS_FILE,
            IMDBConstants.USER_DATA_FILE,
            IMDBConstants.BASE_DATA_FILE,
            IMDBConstants.USER_RATINGS_FILE,
            IMDBConstants.CLEANED_UPLOAD_FILE
        ]
        
        dirs_to_remove = ['__pycache__']
        
        for file in files_to_remove:
            try:
                if os.path.exists(file):
                    os.remove(file)
                    logger.info(f"Removed {file}")
            except Exception as e:
                logger.warning(f"Could not remove {file}: {e}")
        
        for dir_name in dirs_to_remove:
            try:
                if os.path.exists(dir_name):
                    import shutil
                    shutil.rmtree(dir_name)
                    logger.info(f"Removed directory {dir_name}")
            except Exception as e:
                logger.warning(f"Could not remove directory {dir_name}: {e}") 