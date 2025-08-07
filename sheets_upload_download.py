"""
Google Sheets Integration Module

This module provides functions to upload and download data from Google Sheets.
Requires a Google Service Account JSON file for authentication.
"""

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from typing import Optional, List
from logger import get_logger

logger = get_logger(__name__)

def upload_to_sheets(worksheet_name: str, spreadsheet_id: str, csv_upload_path: str, service_account_path: str) -> None:
    """
    Upload CSV data to Google Sheets
    
    Args:
        worksheet_name: Name of the worksheet to upload to
        spreadsheet_id: Google Sheets spreadsheet ID
        csv_upload_path: Path to the CSV file to upload
        service_account_path: Path to the Google Service Account JSON file
    """
    try:
        # Set up Google Sheets API credentials
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = Credentials.from_service_account_file(
            service_account_path, 
            scopes=scope
        )
        
        # Create gspread client
        client = gspread.authorize(credentials)
        
        # Open the spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Get or create the worksheet
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            logger.info(f"Using existing worksheet: {worksheet_name}")
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
            logger.info(f"Created new worksheet: {worksheet_name}")
        
        # Read CSV file
        df = pd.read_csv(csv_upload_path)
        
        # Replace NaN values with empty strings to make them JSON compliant
        df = df.fillna('')
        
        # Convert DataFrame to list of lists (including headers)
        data = [df.columns.tolist()] + df.values.tolist()
        
        # Clear existing data and upload new data
        worksheet.clear()
        worksheet.update(data)
        
        logger.info(f"Successfully uploaded {len(df)} rows to Google Sheets")
        
    except Exception as e:
        logger.error(f"Error uploading to Google Sheets: {e}")
        raise

def download_from_sheets(worksheet_name: str, spreadsheet_id: str, service_account_path: str, output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Download data from Google Sheets
    
    Args:
        worksheet_name: Name of the worksheet to download from
        spreadsheet_id: Google Sheets spreadsheet ID
        service_account_path: Path to the Google Service Account JSON file
        output_path: Optional path to save the downloaded data as CSV
    
    Returns:
        DataFrame containing the downloaded data
    """
    try:
        # Set up Google Sheets API credentials
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = Credentials.from_service_account_file(
            service_account_path, 
            scopes=scope
        )
        
        # Create gspread client
        client = gspread.authorize(credentials)
        
        # Open the spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Get the worksheet
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        # Get all values from the worksheet
        data = worksheet.get_all_values()
        
        if not data:
            logger.warning(f"No data found in worksheet: {worksheet_name}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Save to CSV if output path is provided
        if output_path:
            df.to_csv(output_path, index=False)
            logger.info(f"Downloaded data saved to: {output_path}")
        
        logger.info(f"Successfully downloaded {len(df)} rows from Google Sheets")
        return df
        
    except Exception as e:
        logger.error(f"Error downloading from Google Sheets: {e}")
        raise

def list_worksheets(spreadsheet_id: str, service_account_path: str) -> List[str]:
    """
    List all worksheets in a Google Sheets spreadsheet
    
    Args:
        spreadsheet_id: Google Sheets spreadsheet ID
        service_account_path: Path to the Google Service Account JSON file
    
    Returns:
        List of worksheet names
    """
    try:
        # Set up Google Sheets API credentials
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = Credentials.from_service_account_file(
            service_account_path, 
            scopes=scope
        )
        
        # Create gspread client
        client = gspread.authorize(credentials)
        
        # Open the spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Get all worksheet names
        worksheet_names = [worksheet.title for worksheet in spreadsheet.worksheets()]
        
        logger.info(f"Found {len(worksheet_names)} worksheets: {worksheet_names}")
        return worksheet_names
        
    except Exception as e:
        logger.error(f"Error listing worksheets: {e}")
        raise 