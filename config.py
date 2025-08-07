import os
import time
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv
import time

# Get the directory where the script is located - scraped_data
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "scraped_data")

@dataclass
class IMDBConfig:
    login: str
    password: str
    spreadsheet_id: str
    service_account_path: str
    
    @classmethod
    def from_env(cls):
        load_dotenv()
        
        login = os.getenv('imdb_login')
        password = os.getenv('imdb_pass')
        spreadsheet_id = os.getenv('spreadsheet_id')
        service_account_path = os.getenv('service_account_path')
        
        # Validate required environment variables
        if not login:
            raise ValueError("Environment variable 'imdb_login' is not set")
        if not password:
            raise ValueError("Environment variable 'imdb_pass' is not set")
        if not spreadsheet_id:
            raise ValueError("Environment variable 'spreadsheet_id' is not set")
        if not service_account_path:
            raise ValueError("Environment variable 'service_account_path' is not set")
        
        return cls(
            login=login,
            password=password,
            spreadsheet_id=spreadsheet_id,
            service_account_path=service_account_path
        )

class IMDBConstants:
    SESSION_ID_TIME_SUFFIX = "l"
    DEFAULT_LOCALE = "en-US"
    DEFAULT_COUNTRY = "US"
    DEFAULT_POSTAL_CODE = "30004"
    REQUEST_DELAY = 0.5
    MAX_COOKIE_RETRIES = 20
    COOKIE_RETRY_DELAY = 2
    
    # API endpoints
    GRAPHQL_ENDPOINT = "https://api.graphql.imdb.com/"
    CACHING_ENDPOINT = "https://caching.graphql.imdb.com/"
    
    # File names with absolute paths
    SCRAPED_DATA_DIR = os.path.join(SCRIPT_DIR, "scraped_data")
    COOKIES_FILE = os.path.join(SCRAPED_DATA_DIR, "cookies.json")
    RATINGS_FILE = os.path.join(SCRAPED_DATA_DIR, "imdb_ratings.json")
    USER_DATA_FILE = os.path.join(SCRAPED_DATA_DIR, "user_data.json")
    BASE_DATA_FILE = os.path.join(SCRAPED_DATA_DIR, "base_data.csv")
    USER_RATINGS_FILE = os.path.join(SCRAPED_DATA_DIR, "user_ratings.csv")
    CLEANED_UPLOAD_FILE = os.path.join(SCRAPED_DATA_DIR, "imdb_cleaned_upload.csv")
    GRAPHQL_HASH_FILE = os.path.join(SCRAPED_DATA_DIR, "graphql_hash.json")

@dataclass
class RequestConfig:
    @staticmethod
    def get_headers() -> Dict[str, str]:
        return {
            'accept': 'application/graphql+json, application/json',
            'accept-language': 'en-US,en;q=0.6',
            'content-type': 'application/json',
            'dnt': '1',
            'origin': 'https://www.imdb.com',
            'priority': 'u=1, i',
            'referer': 'https://www.imdb.com/',
            'sec-ch-ua': '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
            'x-amzn-sessionid': '145-8382313-6076133',
            'x-imdb-client-name': 'imdb-web-next-localized',
            'x-imdb-client-rid': 'BJ8WQBM1FPS50N4FSAPE',
            'x-imdb-user-country': 'US',
            'x-imdb-user-language': 'en-US',
            'x-imdb-weblab-treatment-overrides': '{"IMDB_NAV_PRO_FLY_OUT_1254137":"T1"}',
        }
    
    @staticmethod
    def get_cookies_template(cookies_dict: Dict[str, str]) -> Dict[str, str]:
        # Define required cookies and their fallback values
        required_cookies = {
            'session-id': '',
            'ubid-main': '',
            'ad-oo': '',
            'ci': '',
            'at-main': '',
            'sess-at-main': '',
            'uu': '',  # This might not always be present
            'x-main': '',
            'session-token': ''
        }
        
        # Build cookies dict with fallbacks for missing cookies
        cookies = {}
        for cookie_name, fallback_value in required_cookies.items():
            cookies[cookie_name] = cookies_dict.get(cookie_name, fallback_value)
        
        # Add computed cookies
        cookies['session-id-time'] = f"{int(time.time())}{IMDBConstants.SESSION_ID_TIME_SUFFIX}"
        cookies['gpc-cache'] = '1'
        
        return cookies 
