# IMDB Scraper - Refactored Version

A modular, maintainable IMDB scraping tool that extracts movie ratings, user data, and streaming platform information.

## 🏗️ Project Structure

The project has been refactored into a clean, modular architecture:

```
scrape_imdb/
├── main.py                 # Main entry point (simplified)
├── imdb_scraper.py         # Main orchestrator class
├── config.py              # Configuration and constants
├── logger.py              # Logging setup and utilities
├── browser_manager.py     # Playwright browser automation
├── imdb_api_client.py     # IMDB API client
├── data_processor.py      # Data processing and transformation
├── file_manager.py        # File operations
├── sheets_upload_download.py  # Google Sheets integration
├── .env                   # Environment variables
└── README.md             # This file
```

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install playwright pandas requests python-dotenv
   playwright install chromium
   ```

2. **Set up environment variables in `.env`:**
   ```env
   imdb_login=your_imdb_email
   imdb_pass=your_imdb_password
   spreadsheet_id=your_google_sheets_id
   service_account_path=path_to_service_account.json
   ```

3. **Run the scraper:**
   ```bash
   python main.py
   ```

## 📋 Features

- **Modular Design**: Each component has a single responsibility
- **Type Hints**: Full type annotations for better IDE support
- **Error Handling**: Comprehensive error handling and logging
- **Configuration Management**: Centralized configuration
- **Anti-Detection**: Stealth browser with anti-detection measures
- **Data Processing**: Clean data transformation pipeline
- **Google Sheets Integration**: Automatic upload to Google Sheets

## 🔧 Module Overview

### `config.py`
- `IMDBConfig`: Configuration dataclass loaded from environment
- `IMDBConstants`: All constants and magic numbers
- `RequestConfig`: HTTP request templates

### `logger.py`
- Centralized logging setup
- File and console output
- Configurable log levels

### `browser_manager.py`
- `BrowserManager`: Handles Playwright browser automation
- Stealth browser creation with anti-detection
- Cookie extraction and login automation

### `imdb_api_client.py`
- `IMDBAPIClient`: Handles all IMDB API requests
- Ratings data extraction
- User data retrieval
- Platform/streaming data collection

### `data_processor.py`
- `DataProcessor`: Data transformation utilities
- JSON to DataFrame conversion
- Dataset merging and cleaning

### `file_manager.py`
- `FileManager`: File operation utilities
- JSON/CSV save/load operations
- Temporary file cleanup

### `imdb_scraper.py`
- `IMDBScraper`: Main orchestrator class
- Coordinates all scraping operations
- Error handling and logging

## 🔄 Workflow

1. **Environment Setup**: Install dependencies and configure logging
2. **Browser Automation**: Create stealth browser and login to IMDB
3. **Cookie Extraction**: Get authentication cookies
4. **Data Collection**:
   - Fetch base ratings data
   - Get user-specific ratings
   - Collect streaming platform information
5. **Data Processing**: Merge and clean all datasets
6. **Upload**: Send data to Google Sheets
7. **Cleanup**: Remove temporary files

## 🛠️ Benefits of Refactoring

### Before (Original `main.py`)
- 551 lines of mixed concerns
- Hardcoded values throughout
- Difficult to test individual components
- Poor error handling
- No type hints

### After (Modular Structure)
- **Separation of Concerns**: Each module has one clear purpose
- **Testability**: Each component can be unit tested independently
- **Maintainability**: Changes to one area don't affect others
- **Reusability**: Components can be reused in other scripts
- **Readability**: Much easier to understand the flow
- **Configuration Management**: All settings in one place
- **Error Handling**: Centralized and consistent error handling
- **Type Safety**: Full type annotations for better development experience

## 🧪 Testing

Each module can be tested independently:

```python
# Test API client
from imdb_api_client import IMDBAPIClient
from config import IMDBConfig

config = IMDBConfig.from_env()
client = IMDBAPIClient(config)
# Test methods...

# Test data processor
from data_processor import DataProcessor
# Test processing methods...

# Test file manager
from file_manager import FileManager
# Test file operations...
```

## 📝 Logging

Logs are saved to `logs/app.log` and also displayed in the console. The logging system:
- Captures all operations with timestamps
- Suppresses verbose HTTP request logs
- Provides clear error messages
- Tracks performance metrics

## 🔒 Security

- Credentials stored in environment variables
- No hardcoded secrets in code
- Secure cookie handling
- Anti-detection measures for web scraping

## 🚀 Future Improvements

- Add unit tests for each module
- Implement retry logic for failed requests
- Add data validation
- Create CLI interface with options
- Add progress bars for long operations
- Implement caching for API responses
- Add support for different output formats

## 📄 License

This project is for educational purposes. Please respect IMDB's terms of service when using this scraper. 