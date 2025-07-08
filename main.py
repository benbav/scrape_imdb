#!/usr/bin/env python3
"""
IMDB Scraper - Main Entry Point

This script orchestrates the complete IMDB scraping process using a modular architecture.
The refactored version separates concerns into dedicated modules for better maintainability.

Usage:
    python main.py

Dependencies:
    - All modules in the same directory
    - Environment variables configured in .env file
"""

import asyncio
from imdb_scraper import main
import os
import platform

if __name__ == "__main__":
    if platform.system() == "Linux":
        tmp_dir = os.path.expanduser('~/tmp')
        os.makedirs(tmp_dir, exist_ok=True)  # This will create the directory if it doesn't exist
        os.environ['TMPDIR'] = tmp_dir
    asyncio.run(main())