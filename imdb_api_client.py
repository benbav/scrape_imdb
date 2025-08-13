import requests
import time
import os
import pandas as pd
from typing import Dict, Any, List
from config import IMDBConfig, IMDBConstants, RequestConfig, SCRIPT_DIR
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

        # Try to get the current hash from the extracted file
        hash_value = "52aeb10821503d123f19bdd9207be68fa8163178c9ffc450d577d5c4baabe307"  # fallback
        
        if os.path.exists(IMDBConstants.GRAPHQL_HASH_FILE):
            try:
                hash_data = FileManager.load_json(IMDBConstants.GRAPHQL_HASH_FILE)
                if 'ratings_hash' in hash_data:
                    hash_value = hash_data['ratings_hash']
                    logger.info(f"Using extracted hash: {hash_value}")
            except Exception as e:
                logger.warning(f"Could not load hash file: {e}")
        

        params = {
            'operationName': 'RatingsPage',
            'variables': '{"filter":{"certificateConstraint":{},"explicitContentConstraint":{"explicitContentFilter":"INCLUDE_ADULT"},"genreConstraint":{},"keywordConstraint":{},"releaseDateConstraint":{"releaseDateRange":{}},"singleUserRatingConstraint":{"filterType":"INCLUDE","userId":"ur155626863"},"titleTextConstraint":{"searchTerm":""},"titleTypeConstraint":{"anyTitleTypeIds":["movie"]},"userRatingsConstraint":{"aggregateRatingRange":{},"ratingsCountRange":{}},"watchOptionsConstraint":{}},"first":250,"isInPace":false,"jumpToPosition":1,"locale":"en-US","sort":{"sortBy":"SINGLE_USER_RATING_DATE","sortOrder":"ASC"}}',
            'extensions': f'{{"persistedQuery":{{"sha256Hash":"{hash_value}","version":1}}}}',
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
    
    def get_platform_data(self, cookies_dict: Dict[str, str], ids: List[str] = None) -> pd.DataFrame:
        """Get platform/streaming data for all movies in the CSV file or specified IDs"""
        # Try to load imdb_cleaned_upload.csv first, if it doesn't exist, try base_data.csv, otherwise create new DataFrame
        try:
            df = FileManager.load_csv(IMDBConstants.CLEANED_UPLOAD_FILE)
            logger.info(f"Loaded existing data from {IMDBConstants.CLEANED_UPLOAD_FILE}")
        except FileNotFoundError:
            try:
                df = FileManager.load_csv(IMDBConstants.BASE_DATA_FILE)
                logger.info(f"Loaded existing data from {IMDBConstants.BASE_DATA_FILE}")
            except FileNotFoundError:
                if ids:
                    logger.warning(f"No existing data files found, creating new DataFrame with provided IDs")
                    df = pd.DataFrame({'id': ids})
                else:
                    raise FileNotFoundError("No data files found and no IDs provided")
        
        # If no IDs provided, use all IDs from the Const column
        if ids is None:
            id_column = 'id' if 'id' in df.columns else 'Const'
            all_ids = df[id_column].dropna().unique().tolist()
            logger.info(f"Found {len(all_ids)} unique IDs from {id_column} column")
            
            # Process in smaller batches to avoid rate limiting
            batch_size = 10
            ids = all_ids[:batch_size]  # Start with first 10 movies
            logger.info(f"Processing first {len(ids)} movies to avoid rate limiting")
            logger.info(f"Remaining {len(all_ids) - len(ids)} movies can be processed in subsequent calls")
        
        # Add platforms column if it doesn't exist
        if 'platforms' not in df.columns:
            df['platforms'] = None
        
        # Ensure platforms column is string type to avoid pandas warnings
        df['platforms'] = df['platforms'].astype('object')

        # Handle different column names for ID
        id_column = 'id' if 'id' in df.columns else 'Const'
        logger.info(f"Using '{id_column}' column for movie IDs")

        cookies = RequestConfig.get_cookies_template(cookies_dict)
        headers = RequestConfig.get_headers()

        # Load hashes to try
        try:
            hash_data = FileManager.load_json(IMDBConstants.GRAPHQL_HASH_FILE)
            hashes_to_try = hash_data.get('graphql_hashes', [])
            logger.info(f"Loaded {len(hashes_to_try)} hashes to try for platform data")
        except Exception as e:
            logger.warning(f"Could not load hashes file: {e}")
            hashes_to_try = ["8b4249ea40b309e5bc4f32ae7e618c77c9da1ed155ffd584b3817f980fb29dd3"]  # fallback
        
        # Remove duplicates
        unique_hashes = list(dict.fromkeys(hashes_to_try))
        logger.info(f"Testing {len(unique_hashes)} unique hashes for platform data")

        for i, id in enumerate(ids):
            # Try each hash until one works
            working_hash = None
            max_retries = 3
            
            for retry in range(max_retries):
                for hash_idx, hash_value in enumerate(unique_hashes):
                    try:
                        params = {
                            'operationName': 'Title_Summary_Prompt_From_Base',
                            'variables': f'{{"id":"{id}","includeUserPreferredServices":false,"isInPace":false,"isProPage":false,"locale":"en-US","location":{{"postalCodeLocation":{{"country":"US","postalCode":"30004"}}}}}}',
                            'extensions': f'{{"persistedQuery":{{"sha256Hash":"{hash_value}","version":1}}}}',
                        }

                        response = self.session.get(IMDBConstants.CACHING_ENDPOINT, params=params, cookies=cookies, headers=headers)
                        
                        if response.status_code == 200:
                            response_data = response.json()
                            # Check if response contains actual data (not an error)
                            if 'data' in response_data and 'title' in response_data['data']:
                                working_hash = hash_value
                                logger.info(f"✓ Hash {hash_value} worked for {id}")
                                break
                            else:
                                logger.warning(f"✗ Hash {hash_value} returned error for {id}")
                        elif response.status_code == 429:  # Rate limited
                            logger.warning(f"Rate limited for {id}, waiting 5 seconds...")
                            time.sleep(5)
                            continue
                        else:
                            # logger.warning(f"✗ Hash {hash_value} failed with status {response.status_code} for {id}")
                            pass
                            
                    except Exception as e:
                        logger.warning(f"✗ Hash {hash_value} failed with error for {id}: {e}")
                    
                    # Small delay between hash attempts
                    time.sleep(0.5)
                
                if working_hash:
                    break
                elif retry < max_retries - 1:
                    logger.warning(f"Retry {retry + 1}/{max_retries} for {id}")
                    time.sleep(2)  # Wait 2 seconds before retry
            
            if working_hash:
                logger.info(f"Working hash found for {id}: {working_hash}")
                response_data = response.json()
                providers = DataProcessor.extract_platforms_from_response(response_data)
                
                if providers:
                    df.loc[df[id_column] == id, 'platforms'] = ', '.join(providers)
                else:
                    df.loc[df[id_column] == id, 'platforms'] = None
                    
                logger.info(f"Successfully processed {id} with hash {working_hash}")
            else:
                logger.error(f"✗ No working hash found for {id}")
                df.loc[df[id_column] == id, 'platforms'] = None
            
            # Save after each movie is processed
            FileManager.save_csv(df, IMDBConstants.CLEANED_UPLOAD_FILE)
            logger.info(f"Saved progress after processing {id} ({i + 1}/{len(ids)} movies completed)")
            
            # Log progress every 10 items or on the last item
            if (i + 1) % 10 == 0 or (i + 1) == len(ids):
                logger.info(f"Platform data progress: {i + 1}/{len(ids)} movies processed")

            # Longer delay between movies to avoid rate limiting
            time.sleep(1.0)  # 1 second delay between movies

        logger.info(f"Platform data collection completed for {len(ids)} movies")

        return df
    
    def test_graphql_hashes(self, cookies_dict: Dict[str, str]) -> Dict[str, bool]:
        """Test each GraphQL hash from the scraped hashes file until one works"""
        cookies = RequestConfig.get_cookies_template(cookies_dict)
        headers = RequestConfig.get_headers()
        
        # Load the hashes from the file
        try:
            hash_data = FileManager.load_json(IMDBConstants.GRAPHQL_HASH_FILE)
            hashes = hash_data.get('graphql_hashes', [])
            logger.info(f"Loaded {len(hashes)} hashes to test")
        except Exception as e:
            logger.error(f"Could not load hashes file: {e}")
            hashes = []
        
        # Add some known working hashes as fallbacks
        fallback_hashes = [
            "52aeb10821503d123f19bdd9207be68fa8163178c9ffc450d577d5c4baabe307",  # Original fallback
            "8b4249ea40b309e5bc4f32ae7e618c77c9da1ed155ffd584b3817f980fb29dd3",  # Platform data hash
            "afebb5841a7a0072bc4d4c3eb29c64832e531a0846c564caf482f814e8ce12c7",  # User data hash
        ]
        
        # Combine scraped hashes with fallback hashes
        all_hashes = hashes + fallback_hashes
        logger.info(f"Testing {len(all_hashes)} total hashes (including {len(fallback_hashes)} fallbacks)")
        
        # Remove duplicates while preserving order
        unique_hashes = list(dict.fromkeys(all_hashes))
        logger.info(f"Testing {len(unique_hashes)} unique hashes")
        
        results = {}
        
        for i, hash_value in enumerate(unique_hashes):
            logger.info(f"Testing hash {i+1}/{len(unique_hashes)}: {hash_value}")
            
            try:
                params = {
                    'operationName': 'RatingsPage',
                    'variables': '{"filter":{"certificateConstraint":{},"explicitContentConstraint":{"explicitContentFilter":"INCLUDE_ADULT"},"genreConstraint":{},"keywordConstraint":{},"releaseDateConstraint":{"releaseDateRange":{}},"singleUserRatingConstraint":{"filterType":"INCLUDE","userId":"ur155626863"},"titleTextConstraint":{"searchTerm":""},"titleTypeConstraint":{"anyTitleTypeIds":["movie"]},"userRatingsConstraint":{"aggregateRatingRange":{},"ratingsCountRange":{}},"watchOptionsConstraint":{}},"first":10,"isInPace":false,"jumpToPosition":1,"locale":"en-US","sort":{"sortBy":"SINGLE_USER_RATING_DATE","sortOrder":"ASC"}}',
                    'extensions': f'{{"persistedQuery":{{"sha256Hash":"{hash_value}","version":1}}}}',
                }

                response = self.session.get(IMDBConstants.GRAPHQL_ENDPOINT, params=params, cookies=cookies, headers=headers)
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # Check if the response contains actual data
                    if 'data' in response_data and 'advancedTitleSearch' in response_data['data']:
                        edges = response_data['data']['advancedTitleSearch'].get('edges', [])
                        if len(edges) > 0:
                            logger.info(f"✓ Hash {hash_value} WORKED! Found {len(edges)} results")
                            results[hash_value] = True
                            
                            # Save the working hash for future use
                            working_hash_data = {
                                'ratings_hash': hash_value,
                                'timestamp': time.time(),
                                'tested_hashes': results
                            }
                            FileManager.save_json(working_hash_data, IMDBConstants.GRAPHQL_HASH_FILE)
                            logger.info(f"Saved working hash to {IMDBConstants.GRAPHQL_HASH_FILE}")
                            
                            return results
                        else:
                            # logger.warning(f"✗ Hash {hash_value} returned empty results")
                            results[hash_value] = False
                    else:
                        # logger.warning(f"✗ Hash {hash_value} returned invalid response structure")
                        results[hash_value] = False
                else:
                    # logger.warning(f"✗ Hash {hash_value} failed with status {response.status_code}")
                    results[hash_value] = False
                    
            except Exception as e:
                logger.error(f"✗ Hash {hash_value} failed with error: {e}")
                results[hash_value] = False
            
            # Small delay between requests
            time.sleep(0.5)
        
        logger.error("No working hash found!")
        return results 