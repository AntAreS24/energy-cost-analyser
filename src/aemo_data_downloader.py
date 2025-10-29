"""
AEMO Data Downloader Module

This module provides functionality to:
1. Parse NEM12 files (AEMO's standard meter data format) 
2. Convert NEM12 data to the project's CSV format
3. Handle incremental updates and duplicate prevention
4. Provide a framework for future API integration

Note: AEMO doesn't provide a public API for individual customer meter data.
Customers typically need to request NEM12 files from their retailer/distributor.
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import logging

try:
    from nemreader import NEMFile
    NEM_READER_AVAILABLE = True
except ImportError:
    NEM_READER_AVAILABLE = False

logger = logging.getLogger(__name__)


class AEMODataDownloader:
    """
    Class for downloading and processing AEMO meter data
    """
    
    def __init__(self, data_folder: str = "data"):
        self.data_folder = Path(data_folder)
        self.csv_file_path = self.data_folder / "Energy Providers - Raw Data.csv"
        
        # Expected CSV columns based on existing data
        self.csv_columns = [
            'AccountNumber', 'NMI', 'DeviceNumber', 'DeviceType', 'RegisterCode',
            'RateTypeDescription', 'StartDate', 'Start Day', 'Start Month', 
            'Start Quarter', 'Start Year', 'EndDate', 'ProfileReadValue', 
            'RegisterReadValue', 'QualityFlag'
        ]
    
    def check_requirements(self) -> bool:
        """Check if required libraries are installed"""
        if not NEM_READER_AVAILABLE:
            logger.error("nemreader library is not installed. Install with: pip install nemreader")
            return False
        return True
    
    def get_last_entry_date(self, nmi: str) -> Optional[datetime]:
        """
        Get the date of the last entry for a specific NMI in the CSV
        
        Args:
            nmi: The NMI to check for
            
        Returns:
            The datetime of the last entry, or None if no entries exist
        """
        try:
            if not self.csv_file_path.exists():
                return None
                
            df = pd.read_csv(self.csv_file_path)
            # Parse dates manually with correct format
            df['StartDate'] = pd.to_datetime(df['StartDate'], format='%d/%m/%Y %H:%M:%S')
            df['EndDate'] = pd.to_datetime(df['EndDate'], format='%d/%m/%Y %H:%M:%S')
            
            if df.empty or str(nmi) not in df['NMI'].astype(str).values:
                return None
                
            # Convert NMI to string for comparison (handles both string and int NMI formats)
            nmi_str = str(nmi)
            nmi_data = df[df['NMI'].astype(str) == nmi_str]
            if nmi_data.empty:
                return None
                
            return nmi_data['EndDate'].max()
            
        except Exception as e:
            logger.error(f"Error reading last entry date: {e}")
            return None
    
    def parse_nem12_file(self, nem12_file_path: str, target_nmi: Optional[str] = None) -> pd.DataFrame:
        """
        Parse a NEM12 file and convert it to the project's CSV format
        
        Args:
            nem12_file_path: Path to the NEM12 file
            target_nmi: Optional NMI to filter for (if None, processes all NMIs)
            
        Returns:
            DataFrame in the project's CSV format
        """
        if not self.check_requirements():
            raise ImportError("Required libraries not available")
        
        try:
            # Parse the NEM12 file
            nem_file = NEMFile(nem12_file_path)
            df = nem_file.get_data_frame()
            
            if df is None or df.empty:
                logger.warning("No data found in NEM12 file")
                return pd.DataFrame(columns=self.csv_columns)
            
            # Filter for target NMI if specified
            if target_nmi:
                df = df[df['nmi'] == target_nmi]
                if df.empty:
                    logger.warning(f"No data found for NMI {target_nmi}")
                    return pd.DataFrame(columns=self.csv_columns)
            
            # Convert to project format
            converted_df = self._convert_nem12_to_csv_format(df)
            return converted_df
            
        except Exception as e:
            logger.error(f"Error parsing NEM12 file: {e}")
            raise
    
    def _convert_nem12_to_csv_format(self, nem12_df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert NEM12 DataFrame to project CSV format
        
        Args:
            nem12_df: DataFrame from nem-reader
            
        Returns:
            DataFrame in project CSV format
        """
        converted_rows = []
        
        for _, row in nem12_df.iterrows():
            # Map device type and register code from suffix
            suffix = row.get('suffix', 'E1')
            if suffix.startswith('E'):
                rate_type = 'Usage'
                register_code = f"{row.get('serno', 'UNKNOWN')}#{suffix}"
            elif suffix.startswith('B'):
                rate_type = 'Solar'
                register_code = f"{row.get('serno', 'UNKNOWN')}#{suffix}"
            else:
                rate_type = 'Other'
                register_code = f"{row.get('serno', 'UNKNOWN')}#{suffix}"
            
            # Convert timestamps
            start_date = pd.to_datetime(row['t_start'])
            end_date = pd.to_datetime(row['t_end'])
            
            # Create row in project format
            converted_row = {
                'AccountNumber': '',  # Not available in NEM12, would need from retailer
                'NMI': row['nmi'],
                'DeviceNumber': row.get('serno', 'UNKNOWN'),
                'DeviceType': 'COMMS4D',  # Standard type, may vary
                'RegisterCode': register_code,
                'RateTypeDescription': rate_type,
                'StartDate': start_date.strftime('%d/%m/%Y %H:%M:%S'),
                'Start Day': start_date.day,
                'Start Month': start_date.month,
                'Start Quarter': (start_date.month - 1) // 3 + 1,
                'Start Year': start_date.year,
                'EndDate': end_date.strftime('%d/%m/%Y %H:%M:%S'),
                'ProfileReadValue': row.get('value', 0.0),
                'RegisterReadValue': 0,  # Usually 0 for interval data
                'QualityFlag': row.get('quality', 'A')
            }
            converted_rows.append(converted_row)
        
        return pd.DataFrame(converted_rows, columns=self.csv_columns)
    
    def download_and_update_data(self, nmi: str, nem12_file_path: Optional[str] = None, 
                                from_date: Optional[datetime] = None) -> Tuple[bool, str]:
        """
        Download/parse meter data and update the CSV file
        
        Args:
            nmi: The NMI to download data for
            nem12_file_path: Path to NEM12 file (if you have one)
            from_date: Optional start date (if None, uses last entry date + 1)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Determine start date
            if from_date is None:
                last_date = self.get_last_entry_date(nmi)
                if last_date:
                    from_date = last_date + timedelta(minutes=30)  # Next 30-min interval
                    logger.info(f"Continuing from last entry: {last_date}")
                else:
                    # If no existing data, we need a NEM12 file or manual date
                    if nem12_file_path is None:
                        return False, "No existing data found and no NEM12 file provided. Please specify a from_date or provide a NEM12 file."
            
            # If NEM12 file provided, parse it
            if nem12_file_path:
                if not Path(nem12_file_path).exists():
                    return False, f"NEM12 file not found: {nem12_file_path}"
                
                logger.info(f"Parsing NEM12 file: {nem12_file_path}")
                new_data = self.parse_nem12_file(nem12_file_path, nmi)
                
                if new_data.empty:
                    return False, "No data found in NEM12 file for the specified NMI"
                
                # Filter for new data only (after from_date if specified)
                if from_date:
                    new_data['StartDate_dt'] = pd.to_datetime(new_data['StartDate'], format='%d/%m/%Y %H:%M:%S')
                    new_data = new_data[new_data['StartDate_dt'] >= from_date]
                    new_data = new_data.drop('StartDate_dt', axis=1)
                
                if new_data.empty:
                    return True, "No new data to add (all data already exists)"
                
                # Append to existing CSV
                success, message = self._append_to_csv(new_data)
                if success:
                    return True, f"Successfully added {len(new_data)} new records from NEM12 file"
                else:
                    return False, message
            
            else:
                # This is where API integration would go in the future
                return False, "Direct AEMO API download not yet implemented. Please provide a NEM12 file from your retailer."
        
        except Exception as e:
            logger.error(f"Error in download_and_update_data: {e}")
            return False, f"Error: {str(e)}"
    
    def _append_to_csv(self, new_data: pd.DataFrame) -> Tuple[bool, str]:
        """
        Append new data to the CSV file, preventing duplicates
        
        Args:
            new_data: DataFrame with new data to append
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Ensure data folder exists
            self.data_folder.mkdir(exist_ok=True)
            
            # Load existing data if file exists
            if self.csv_file_path.exists():
                existing_data = pd.read_csv(self.csv_file_path)
                # Parse dates manually with correct format
                existing_data['StartDate'] = pd.to_datetime(existing_data['StartDate'], format='%d/%m/%Y %H:%M:%S')
                existing_data['EndDate'] = pd.to_datetime(existing_data['EndDate'], format='%d/%m/%Y %H:%M:%S')
                
                # Create a key for duplicate detection
                existing_data['_key'] = (existing_data['NMI'].astype(str) + '_' + 
                                       existing_data['RegisterCode'].astype(str) + '_' + 
                                       existing_data['StartDate'].dt.strftime('%Y%m%d%H%M'))
                
                new_data['StartDate_dt'] = pd.to_datetime(new_data['StartDate'], format='%d/%m/%Y %H:%M:%S')
                new_data['_key'] = (new_data['NMI'].astype(str) + '_' + 
                                   new_data['RegisterCode'].astype(str) + '_' + 
                                   new_data['StartDate_dt'].dt.strftime('%Y%m%d%H%M'))
                
                # Remove duplicates
                new_data = new_data[~new_data['_key'].isin(existing_data['_key'])]
                new_data = new_data.drop(['_key', 'StartDate_dt'], axis=1)
                
                if new_data.empty:
                    return True, "No new unique records to add"
                
                # Combine data
                combined_data = pd.concat([existing_data.drop('_key', axis=1), new_data], ignore_index=True)
            else:
                combined_data = new_data
            
            # Sort by NMI and StartDate
            combined_data['StartDate_dt'] = pd.to_datetime(combined_data['StartDate'], format='%d/%m/%Y %H:%M:%S')
            combined_data = combined_data.sort_values(['NMI', 'RegisterCode', 'StartDate_dt'])
            combined_data = combined_data.drop('StartDate_dt', axis=1)
            
            # Save to CSV
            combined_data.to_csv(self.csv_file_path, index=False)
            
            return True, f"Successfully saved {len(new_data)} new records"
            
        except Exception as e:
            logger.error(f"Error appending to CSV: {e}")
            return False, f"Error saving data: {str(e)}"
    
    def get_available_nmis_in_file(self, nem12_file_path: str) -> List[Tuple[str, List[str]]]:
        """
        Get list of NMIs and their channels available in a NEM12 file
        
        Args:
            nem12_file_path: Path to the NEM12 file
            
        Returns:
            List of tuples (nmi, channels)
        """
        if not self.check_requirements():
            raise ImportError("Required libraries not available")
        
        try:
            from nemreader.outputs import nmis_in_file
            return list(nmis_in_file(nem12_file_path))
        except Exception as e:
            logger.error(f"Error reading NMIs from file: {e}")
            return []


def install_requirements():
    """
    Helper function to install required packages
    """
    import subprocess
    import sys
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "nemreader"])
        print("Successfully installed nemreader package")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install nemreader: {e}")
        return False


# Example usage function
def example_usage():
    """
    Example of how to use the AEMODataDownloader
    """
    # Initialize downloader
    downloader = AEMODataDownloader()
    
    # Example NMI (replace with your actual NMI)
    my_nmi = "41032871534"
    
    # Example 1: Check what NMIs are in a NEM12 file
    nem12_file = "path/to/your/nem12_file.csv"  # Replace with actual path
    try:
        available_nmis = downloader.get_available_nmis_in_file(nem12_file)
        print(f"Available NMIs in file: {available_nmis}")
    except Exception as e:
        print(f"Could not read NEM12 file: {e}")
    
    # Example 2: Download/parse data for specific NMI
    success, message = downloader.download_and_update_data(
        nmi=my_nmi,
        nem12_file_path=nem12_file  # Provide NEM12 file
    )
    
    print(f"Download result: {success} - {message}")
    
    # Example 3: Check last entry date
    last_date = downloader.get_last_entry_date(my_nmi)
    if last_date:
        print(f"Last entry date for {my_nmi}: {last_date}")
    else:
        print(f"No existing data for {my_nmi}")


if __name__ == "__main__":
    # Check if requirements are installed
    if not NEM_READER_AVAILABLE:
        print("Required package 'nemreader' is not installed.")
        print("Would you like to install it now? (y/n)")
        if input().lower().startswith('y'):
            install_requirements()
        else:
            print("Please install nemreader manually: pip install nemreader")
    else:
        print("All requirements are available!")
        example_usage()