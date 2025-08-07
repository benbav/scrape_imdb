import json
import os
import shutil
import pandas as pd
from typing import Dict, Any, Optional
from config import IMDBConstants, SCRIPT_DIR
from logger import get_logger

logger = get_logger(__name__)

class FileManager:
    @staticmethod
    def save_json(data: Dict[str, Any], filename: str) -> None:
        """Save data to JSON file"""
        try:
            # Ensure filename is an absolute path
            if not os.path.isabs(filename):
                filename = os.path.join(SCRIPT_DIR, filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
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
            # Ensure filename is an absolute path
            if not os.path.isabs(filename):
                filename = os.path.join(SCRIPT_DIR, filename)
            
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            raise
    
    @staticmethod
    def save_csv(df: pd.DataFrame, filename: str, index: bool = False) -> None:
        """Save DataFrame to CSV file"""
        try:
            # Ensure filename is an absolute path
            if not os.path.isabs(filename):
                filename = os.path.join(SCRIPT_DIR, filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            df.to_csv(filename, index=index)
            logger.info(f"Data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")
            raise
    
    @staticmethod
    def load_csv(filename: str) -> pd.DataFrame:
        """Load DataFrame from CSV file"""
        try:
            # Ensure filename is an absolute path
            if not os.path.isabs(filename):
                filename = os.path.join(SCRIPT_DIR, filename)
            
            return pd.read_csv(filename)
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            raise
    
    @staticmethod
    def file_exists(filename: str) -> bool:
        """Check if file exists"""
        # Ensure filename is an absolute path
        if not os.path.isabs(filename):
            filename = os.path.join(SCRIPT_DIR, filename)
        return os.path.exists(filename)
    
    @staticmethod
    def cleanup_temp_files() -> None:
        """Clean up temporary files and directories"""
        files_to_remove = [
            'tempCodeRunnerFile.py',
            # IMDBConstants.RATINGS_FILE,
            # IMDBConstants.USER_DATA_FILE,
            # IMDBConstants.BASE_DATA_FILE,
            # IMDBConstants.USER_RATINGS_FILE,
            # IMDBConstants.CLEANED_UPLOAD_FILE,
            # IMDBConstants.GRAPHQL_HASH_FILE
        ]
        
        dirs_to_remove = ['__pycache__']
        
        for file in files_to_remove:
            try:
                if os.path.exists(file):
                    os.remove(file)
                    # logger.info(f"Removed {file}")
            except Exception as e:
                logger.warning(f"Could not remove {file}: {e}")
        
        for dir_name in dirs_to_remove:
            try:
                dir_path = os.path.join(SCRIPT_DIR, dir_name)
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                    logger.info(f"Removed directory {dir_path}")
            except Exception as e:
                logger.warning(f"Could not remove directory {dir_name}: {e}")

        def clear_tmp():
            # Instead of os.system with sudo (which can leave orphaned processes)
            tmp_dir = os.path.expanduser('~/tmp')
            try:
                for item in os.listdir(tmp_dir):
                    if item.startswith('playwright') or 'Temp' in item:
                        try:
                            item_path = os.path.join(tmp_dir, item)
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path, ignore_errors=True)
                            else:
                                os.remove(item_path)
                        except Exception as e:
                            logger.warning(f"Failed to remove {item}: {e}")
            except Exception as e:
                print('no tmp dir found')
                logger.info('no tmp dir found')
                pass

        clear_tmp()

    @staticmethod
    def cleanup_environment() -> None:
        """Clean up environment: kill playwright processes and remove __pycache__ folders"""
        import subprocess
        import signal
        
        # Kill all playwright processes
        try:
            # Find and kill playwright processes
            result = subprocess.run(['pgrep', '-f', 'playwright'], capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid.strip():
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                            logger.info(f"Killed playwright process {pid}")
                        except (ValueError, ProcessLookupError, PermissionError) as e:
                            logger.warning(f"Could not kill process {pid}: {e}")
            else:
                logger.info("No playwright processes found")
        except Exception as e:
            logger.warning(f"Error killing playwright processes: {e}")
        
        # Remove all __pycache__ folders recursively
        try:
            cache_count = 0
            for root, dirs, files in os.walk(SCRIPT_DIR):
                for dir_name in dirs:
                    if dir_name == '__pycache__':
                        cache_path = os.path.join(root, dir_name)
                        try:
                            shutil.rmtree(cache_path)
                            cache_count += 1
                        except Exception as e:
                            logger.warning(f"Could not remove __pycache__ folder {cache_path}: {e}")
            if cache_count > 0:
                logger.info(f"Removed {cache_count} __pycache__ folders")
        except Exception as e:
            logger.warning(f"Error removing __pycache__ folders: {e}")
        
        # Clean up temp directory
        try:
            tmp_dir = os.path.expanduser('~/tmp')
            temp_count = 0
            if os.path.exists(tmp_dir):
                for item in os.listdir(tmp_dir):
                    if item.startswith('playwright') or 'Temp' in item or '__pycache__' in item:
                        try:
                            item_path = os.path.join(tmp_dir, item)
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path, ignore_errors=True)
                            else:
                                os.remove(item_path)
                            temp_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to remove temp item {item}: {e}")
            if temp_count > 0:
                logger.info(f"Removed {temp_count} temp files/folders")
        except Exception as e:
            logger.warning(f"Error cleaning temp directory: {e}")
        
        logger.info("Environment cleanup completed")
