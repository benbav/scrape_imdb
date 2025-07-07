import requests
import time
import pandas as pd
from typing import Dict, Any, List
from config import IMDBConfig, IMDBConstants, RequestConfig
from logger import get_logger
from file_manager import FileManager
from data_processor import DataProcessor

logger = get_logger(__name__)

class IMDBAPIClient:
    def __init__(self, config: IMDBConfig):
        self.config = config
        self.session = requests.Session()
    
    def get_ratings_data(self, cookies_dict: Dict[str, str]) -> pd.DataFrame:
        """Get base ratings data from IMDB"""
        cookies = RequestConfig.get_cookies_template(cookies_dict)
        headers = RequestConfig.get_headers()

        params = {
            'operationName': 'RatingsPage',
            'variables': '{"filter":{"certificateConstraint":{},"explicitContentConstraint":{"explicitContentFilter":"INCLUDE_ADULT"},"genreConstraint":{},"keywordConstraint":{},"releaseDateConstraint":{"releaseDateRange":{}},"singleUserRatingConstraint":{"filterType":"INCLUDE","userId":"ur155626863"},"titleTextConstraint":{"searchTerm":""},"titleTypeConstraint":{"anyTitleTypeIds":["movie"]},"userRatingsConstraint":{"aggregateRatingRange":{},"ratingsCountRange":{}},"watchOptionsConstraint":{}},"first":250,"isInPace":false,"jumpToPosition":1,"locale":"en-US","sort":{"sortBy":"SINGLE_USER_RATING_DATE","sortOrder":"ASC"}}',
            'extensions': '{"persistedQuery":{"sha256Hash":"52aeb10821503d123f19bdd9207be68fa8163178c9ffc450d577d5c4baabe307","version":1}}',
        }

        response = self.session.get(IMDBConstants.GRAPHQL_ENDPOINT, params=params, cookies=cookies, headers=headers)

        if response.status_code != 200:
            logger.error(f"Error: {response.status_code}, exiting...")
            raise Exception(f"API request failed with status {response.status_code}")
        
        response_data = response.json()
        FileManager.save_json(response_data, IMDBConstants.RATINGS_FILE)
        logger.info("Ratings data saved to file")

        if FileManager.file_exists(IMDBConstants.RATINGS_FILE):
            return DataProcessor.process_ratings_response(response_data)
        else:
            raise Exception('Error downloading base data (imdb_ratings.json)')
    
    def get_user_data(self, cookies_dict: Dict[str, str], ids: List[str]) -> pd.DataFrame:
        """Get user-specific data for the given IDs"""
        cookies = RequestConfig.get_cookies_template(cookies_dict)
        headers = RequestConfig.get_headers()

        json_data = {
            'operationName': 'PersonalizedUserData',
            'variables': {
                'locale': IMDBConstants.DEFAULT_LOCALE,
                'idArray': ids,
                'includeUserData': True,
                'location': {
                    'postalCodeLocation': {
                        'country': IMDBConstants.DEFAULT_COUNTRY,
                        'postalCode': IMDBConstants.DEFAULT_POSTAL_CODE,
                    },
                },
                'fetchOtherUserRating': False,
            },
            'extensions': {
                'persistedQuery': {
                    'version': 1,
                    'sha256Hash': 'afebb5841a7a0072bc4d4c3eb29c64832e531a0846c564caf482f814e8ce12c7',
                },
            },
        }

        response = self.session.post(IMDBConstants.GRAPHQL_ENDPOINT, cookies=cookies, headers=headers, json=json_data)

        if response.status_code != 200:
            logger.error(f"Error getting user data: {response.status_code}")
            raise Exception(f"User data API request failed with status {response.status_code}")

        response_data = response.json()
        FileManager.save_json(response_data, IMDBConstants.USER_DATA_FILE)

        return DataProcessor.process_user_data_response(response_data)
    
    def get_platform_data(self, cookies_dict: Dict[str, str], ids: List[str]) -> pd.DataFrame:
        """Get platform/streaming data for the given IDs"""
        df = FileManager.load_csv(IMDBConstants.BASE_DATA_FILE)
        
        # Add platforms column if it doesn't exist
        if 'platforms' not in df.columns:
            df['platforms'] = None

        cookies = RequestConfig.get_cookies_template(cookies_dict)
        headers = RequestConfig.get_headers()

        for i, id in enumerate(ids):
            params = {
                'operationName': 'Title_Summary_Prompt_From_Base',
                'variables': f'{{"id":"{id}","includeUserPreferredServices":false,"isInPace":false,"isProPage":false,"locale":"en-US","location":{{"postalCodeLocation":{{"country":"US","postalCode":"30004"}}}}}}',
                'extensions': '{"persistedQuery":{"sha256Hash":"8b4249ea40b309e5bc4f32ae7e618c77c9da1ed155ffd584b3817f980fb29dd3","version":1}}',
            }

            response = self.session.get(IMDBConstants.CACHING_ENDPOINT, params=params, cookies=cookies, headers=headers)
            
            if response.status_code != 200:
                logger.warning(f"Error getting platform data for {id}: {response.status_code}")
                continue
                
            response_data = response.json()
            providers = DataProcessor.extract_platforms_from_response(response_data)
            
            if providers:
                df.loc[df['id'] == id, 'platforms'] = ', '.join(providers)
            else:
                df.loc[df['id'] == id, 'platforms'] = None

            # Log progress every 10 items or on the last item
            if (i + 1) % 10 == 0 or (i + 1) == len(ids):
                logger.info(f"Platform data progress: {i + 1}/{len(ids)} movies processed")

            time.sleep(IMDBConstants.REQUEST_DELAY)

        # Save only once at the end
        FileManager.save_csv(df, IMDBConstants.BASE_DATA_FILE)
        logger.info(f"Platform data collection completed for {len(ids)} movies")

        return df 