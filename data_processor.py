import pandas as pd
from typing import Dict, Any, List
from config import IMDBConstants
from logger import get_logger

logger = get_logger(__name__)

class DataProcessor:
    @staticmethod
    def process_ratings_response(response_data: Dict[str, Any]) -> pd.DataFrame:
        """Process the ratings API response into a DataFrame"""
        # Check for API errors
        if 'errors' in response_data:
            error_msg = response_data['errors'][0]['message'] if response_data['errors'] else 'Unknown API error'
            raise Exception(f"API Error: {error_msg}")
        
        if 'data' not in response_data:
            raise Exception("API response missing 'data' key")
        
        cols = ['title', 'id', 'release_year', 'genres']
        df = pd.DataFrame(columns=cols)

        r = response_data['data']['advancedTitleSearch']['edges']

        for i in range(len(r)):
            id = r[i]['node']['title']['id']
            title = r[i]['node']['title']['titleText']['text']
            year = r[i]['node']['title']['releaseYear']['year']
            genre = ", ".join([genre['genre']['text'] for genre in r[i]['node']['title']['titleGenres']['genres']])
            df.loc[i] = [title, id, year, genre]

        return df
    
    @staticmethod
    def process_user_data_response(response_data: Dict[str, Any]) -> pd.DataFrame:
        """Process the user data API response into a DataFrame"""
        # Check for API errors
        if 'errors' in response_data:
            error_msg = response_data['errors'][0]['message'] if response_data['errors'] else 'Unknown API error'
            raise Exception(f"API Error: {error_msg}")
        
        if 'data' not in response_data:
            raise Exception("API response missing 'data' key")
        
        df = pd.DataFrame(columns=['id', 'user_rating'])

        base_json = response_data['data']['titles']

        for i in range(len(base_json)):
            id = base_json[i]['id']
            user_rating = base_json[i]['userRating']['value']
            df.loc[i] = [id, user_rating]

        return df
    
    @staticmethod
    def merge_datasets(base_df: pd.DataFrame, user_df: pd.DataFrame) -> pd.DataFrame:
        """Merge base data and user ratings data"""
        # Drop the user_rating column from base_df if it exists (since we'll get it from user_df)
        if 'user_rating' in base_df.columns:
            base_df = base_df.drop('user_rating', axis=1)

        # Merge the dataframes
        df = pd.merge(base_df, user_df, on='id', how='left')

        # Reorder columns to have a logical order
        column_order = ['title', 'id', 'user_rating', 'platforms']
        # Only include columns that exist
        final_columns = [col for col in column_order if col in df.columns]
        # Add any remaining columns
        remaining_columns = [col for col in df.columns if col not in final_columns]
        final_columns.extend(remaining_columns)
        
        df = df[final_columns]

        return df
    
    @staticmethod
    def extract_platforms_from_response(response_data: Dict[str, Any]) -> List[str]:
        """Extract platform information from API response"""
        if response_data['data']['title']['watchOptionsByCategory']['categorizedWatchOptionsList']:   
            # Get the first streaming option's provider name
            watch_options = response_data['data']['title']['watchOptionsByCategory']['categorizedWatchOptionsList'][0]['watchOptions']
            if watch_options:
                # Extract provider names and join them
                providers = [option['provider']['name']['value'] for option in watch_options]
                return providers
        return [] 