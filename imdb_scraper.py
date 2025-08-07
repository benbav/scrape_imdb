import asyncio
import time
import sys
import pandas as pd
from typing import Dict, Any
from config import IMDBConfig, IMDBConstants
from logger import setup_logger, get_logger
from browser_manager import BrowserManager
from imdb_api_client import IMDBAPIClient
from data_processor import DataProcessor
from file_manager import FileManager
from sheets_upload_download import upload_to_sheets
from datetime import datetime

logger = get_logger(__name__)

class IMDBScraper:
    def __init__(self, config: IMDBConfig):
        self.config = config
        self.api_client = IMDBAPIClient(config)
        self.browser_manager = BrowserManager()
        self.data_processor = DataProcessor()
    
    async def run_full_scrape(self) -> None:
        """Run the complete IMDB scraping process"""
        start_time = time.time()
        
        try:
            # Setup environment
            self._setup_environment()
            
            # Get cookies via browser automation
            cookies = await self._get_playwright_data()
            
            # Get base ratings data
            # try:
            #     base_df = self._get_base_data(cookies)
            # except Exception as e:
            #     logger.warning(f"Could not get base ratings data: {e}")
            #     logger.info("This is likely due to an outdated GraphQL hash.")
            #     logger.info("The script will continue with other data collection...")
            #     base_df = pd.DataFrame(columns=['title', 'id', 'release_year', 'genres'])
            
            # # Get user-specific data (skip if no base data)
            # if len(base_df) > 0:
            #     user_df = self._get_user_data(cookies, base_df['id'].to_list())
            # else:
            #     logger.warning("Skipping user data collection due to missing base data")
            #     user_df = pd.DataFrame(columns=['id', 'user_rating'])
            
            # # Get platform data (skip if no base data)
            # if len(base_df) > 0:
            #     platform_df = self._get_platform_data(cookies, base_df['id'].to_list())
            # else:
            #     logger.warning("Skipping platform data collection due to missing base data")
            #     platform_df = pd.DataFrame()
            
            # Process and merge all data
            final_df = pd.read_csv(f"{IMDBConstants.SCRAPED_DATA_DIR}/imdb_cleaned_upload.csv")

            # add date updated column
            final_df['date_updated'] = datetime.now().strftime('%Y-%m-%d')

            print(final_df.head())
            input("Press Enter to continue...")

            # if the file is empty, raise an error
            if final_df.empty:
                logger.error("The export.csv file is empty. Please check the browser automation.")
                raise Exception("The export.csv file is empty. Please check the browser automation.")
            
            # Upload to sheets (optional)
            self._upload_to_sheets(final_df)
            
            # Cleanup
            self._cleanup()
            
            elapsed_time = round((time.time() - start_time) / 60, 2)
            logger.info(f"Scraping completed successfully in {elapsed_time} minutes")
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise
        finally:
            await self.browser_manager.close()
    
    def _setup_environment(self) -> None:
        """Setup the environment for scraping"""
        # Install playwright browsers using Python module
        import subprocess
        import sys
        import os

        try:
            # Use the current Python executable to run playwright install
            subprocess.run([
                sys.executable, '-m', 'playwright', 'install', 'chromium'
            ], check=True, capture_output=True, text=True)
            logger.info("Playwright browsers installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Playwright browsers: {e}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error installing Playwright browsers: {e}")
            raise
        
        # Setup logging
        setup_logger()
        logger.info("Environment setup completed")
    
    async def _get_playwright_data(self) -> Dict[str, str]:
        """Get authentication cookies via browser automation"""
        logger.info("Starting browser automation to get cookies...")
        await self.browser_manager.create_stealth_browser()
        cookies = await self.browser_manager.get_playwright_data(self.config)
        logger.info("Successfully obtained cookies")
        return cookies
    
    def _get_base_data(self, cookies: Dict[str, str]) -> pd.DataFrame:
        """Get base ratings data"""
        logger.info("Fetching base ratings data...")
        df = self.api_client.get_ratings_data(cookies)
        FileManager.save_csv(df, IMDBConstants.BASE_DATA_FILE)
        logger.info(f"Base data saved with {len(df)} records")
        return df
    
    def _get_user_data(self, cookies: Dict[str, str], ids: list) -> pd.DataFrame:
        """Get user-specific data"""
        logger.info("Fetching user-specific data...")
        df = self.api_client.get_user_data(cookies, ids)
        FileManager.save_csv(df, IMDBConstants.USER_RATINGS_FILE)
        logger.info(f"User data saved with {len(df)} records")
        return df
    
    def _get_platform_data(self, cookies: Dict[str, str], ids: list) -> pd.DataFrame:
        """Get platform/streaming data"""
        logger.info("Fetching platform data...")
        df = self.api_client.get_platform_data(cookies, ids)
        logger.info("Platform data collection completed")
        return df
    
    def _process_data(self, base_df: pd.DataFrame, user_df: pd.DataFrame) -> pd.DataFrame:
        """Process and merge all datasets"""
        logger.info("Processing and merging datasets...")
        final_df = DataProcessor.merge_datasets(base_df, user_df)
        FileManager.save_csv(final_df, IMDBConstants.CLEANED_UPLOAD_FILE)
        logger.info(f"Final processed data saved with {len(final_df)} records")
        return final_df
    
    def _upload_to_sheets(self, df: pd.DataFrame) -> None:
        """Upload data to Google Sheets"""
        try:
            logger.info("Uploading data to Google Sheets...")
            upload_to_sheets(
                worksheet_name='test',
                spreadsheet_id=self.config.spreadsheet_id,
                csv_upload_path=IMDBConstants.CLEANED_UPLOAD_FILE,
                service_account_path=self.config.service_account_path
            )
            logger.info("Data uploaded to Google Sheets successfully")
        except Exception as e:
            logger.error(f"Failed to upload to Google Sheets: {e}")
    
    def _cleanup(self) -> None:
        """Clean up temporary files and environment"""
        logger.info("Cleaning up temporary files...")
        FileManager.cleanup_temp_files()
        logger.info("Cleaning up environment...")
        FileManager.cleanup_environment()
        logger.info("Cleanup completed")

async def main():
    """Main entry point"""
    try:
        # Load configuration
        config = IMDBConfig.from_env()
        
        # Create scraper instance
        scraper = IMDBScraper(config)
        
        # Run the scraping process
        await scraper.run_full_scrape()
        
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 