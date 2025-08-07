#!/usr/bin/env python3
"""
Test script to run only the get_cookies function from browser_manager.py
"""

import asyncio
import sys
import os
import logging

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_cookies.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from browser_manager import BrowserManager
from config import IMDBConfig, IMDBConstants
from file_manager import FileManager

async def main():
    logger.info("Starting get_cookies test...")
    
    try:
        # Create config instance from environment variables
        logger.info("Loading configuration from environment...")
        config = IMDBConfig.from_env()
        logger.info("Configuration loaded successfully")
        
        # Create browser manager
        logger.info("Creating browser manager...")
        browser_manager = BrowserManager()
        
        # Create stealth browser
        logger.info("Creating stealth browser...")
        await browser_manager.create_stealth_browser()
        logger.info("Stealth browser created successfully")
        
        # Run the playwright data collection
        logger.info("Running playwright data collection...")
        await browser_manager.get_playwright_data(config)
        logger.info("Playwright data collection completed successfully!")
        
        # Load cookies from file to verify
        try:
            cookies = FileManager.load_json(IMDBConstants.COOKIES_FILE)
            logger.info(f"Cookies loaded from file! Found {len(cookies)} cookies")
            
            # Log cookie names for debugging
            cookie_names = list(cookies.keys())
            logger.info(f"Cookie names: {cookie_names}")
            
            # Check for important cookies
            important_cookies = ['ci', 'session-id', 'at-main']
            for cookie in important_cookies:
                if cookie in cookies:
                    logger.info(f"✓ Found {cookie} cookie")
                else:
                    logger.warning(f"✗ Missing {cookie} cookie")
            
            print("Cookies retrieved successfully:", cookies)
        except Exception as e:
            logger.error(f"Error loading cookies from file: {e}")
            print("Cookies could not be loaded from file")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    finally:
        # Clean up
        logger.info("Cleaning up browser resources...")
        await browser_manager.close()
        logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(main()) 