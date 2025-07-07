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
import sys
from imdb_scraper import main

if __name__ == "__main__":
    asyncio.run(main())


# TODO:

# upload to github
# add it pi and cron it evernight - see if it gets blocked
# see if I can refactor this later to be less code
# review changes later so we can understand the structure and advantage of this approach