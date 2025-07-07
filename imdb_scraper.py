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
            cookies = await self._get_cookies()
            
            # Get base ratings data
            base_df = self._get_base_data(cookies)
            
            # Get user-specific data
            user_df = self._get_user_data(cookies, base_df['id'].to_list())
            
            # Get platform data
            platform_df = self._get_platform_data(cookies, base_df['id'].to_list())
            
            # Process and merge all data
            final_df = self._process_data(base_df, user_df)
            
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
        # Update playwright
        import os
        os.system('playwright install chromium')
        
        # Setup logging
        setup_logger()
        logger.info("Environment setup completed")
    
    async def _get_cookies(self) -> Dict[str, str]:
        """Get authentication cookies via browser automation"""
        logger.info("Starting browser automation to get cookies...")
        await self.browser_manager.create_stealth_browser()
        cookies = await self.browser_manager.get_cookies(self.config)
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
        """Clean up temporary files"""
        logger.info("Cleaning up temporary files...")
        FileManager.cleanup_temp_files()
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