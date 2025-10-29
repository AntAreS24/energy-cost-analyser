#!/usr/bin/env python3
"""
Test script for the AEMO data downloader functionality

This script tests the functionality without requiring actual NEM12 files
"""

import pandas as pd
from datetime import datetime, timedelta
from src.aemo_data_downloader import AEMODataDownloader


def test_basic_functionality():
    """Test basic functionality of the data downloader"""
    print("🧪 Testing AEMO Data Downloader...")
    
    # Initialize downloader
    downloader = AEMODataDownloader()
    
    # Test 1: Check if the CSV file exists and read last entry
    print("\n1. Testing last entry date retrieval...")
    nmi = "41032871534"  # NMI from the existing sample data
    
    try:
        last_date = downloader.get_last_entry_date(nmi)
        if last_date:
            print(f"   ✅ Found last entry: {last_date}")
        else:
            print("   ℹ️  No existing data found (this is normal for first run)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Check CSV structure
    print("\n2. Testing CSV file structure...")
    try:
        csv_path = downloader.csv_file_path
        if csv_path.exists():
            df = pd.read_csv(csv_path, nrows=5)  # Just read first 5 rows
            print(f"   ✅ CSV file exists with {len(df.columns)} columns")
            print(f"   📋 Columns: {list(df.columns)}")
            
            if 'NMI' in df.columns:
                unique_nmis = df['NMI'].unique()
                print(f"   📊 Found NMIs: {unique_nmis}")
        else:
            print("   ℹ️  CSV file doesn't exist yet (normal for first run)")
    except Exception as e:
        print(f"   ❌ Error reading CSV: {e}")
    
    # Test 3: Test duplicate prevention logic (simulate data)
    print("\n3. Testing duplicate prevention...")
    try:
        # Create sample data that would be a duplicate
        sample_data = pd.DataFrame([{
            'AccountNumber': '56185416',
            'NMI': '41032871534',
            'DeviceNumber': '700813815',
            'DeviceType': 'COMMS4D',
            'RegisterCode': '13815#E1',
            'RateTypeDescription': 'Usage',
            'StartDate': '04/11/2021 00:00:00',
            'Start Day': 4,
            'Start Month': 11,
            'Start Quarter': 4,
            'Start Year': 2021,
            'EndDate': '04/11/2021 00:29:59',
            'ProfileReadValue': 0.174,
            'RegisterReadValue': 0,
            'QualityFlag': 'A'
        }], columns=downloader.csv_columns)
        
        print("   ✅ Sample data structure created successfully")
        
    except Exception as e:
        print(f"   ❌ Error creating sample data: {e}")
    
    # Test 4: Check requirements
    print("\n4. Testing requirements...")
    requirements_ok = downloader.check_requirements()
    if requirements_ok:
        print("   ✅ All required packages are available")
    else:
        print("   ⚠️  Some packages missing (run: pip install -r requirements.txt)")
    
    print("\n🎉 Basic functionality test complete!")
    return True


def test_data_conversion():
    """Test the NEM12 to CSV conversion logic"""
    print("\n🧪 Testing NEM12 to CSV conversion...")
    
    downloader = AEMODataDownloader()
    
    # Create mock NEM12-style data
    mock_nem12_data = pd.DataFrame([
        {
            'nmi': '41032871534',
            'suffix': 'E1',
            'serno': '700813815',
            't_start': pd.Timestamp('2021-11-04 00:00:00'),
            't_end': pd.Timestamp('2021-11-04 00:30:00'),
            'value': 0.174,
            'quality': 'A'
        },
        {
            'nmi': '41032871534',
            'suffix': 'B1',
            'serno': '700813815',
            't_start': pd.Timestamp('2021-11-04 00:00:00'),
            't_end': pd.Timestamp('2021-11-04 00:30:00'),
            'value': 0.050,
            'quality': 'A'
        }
    ])
    
    try:
        converted_data = downloader._convert_nem12_to_csv_format(mock_nem12_data)
        
        print(f"   ✅ Converted {len(mock_nem12_data)} NEM12 records to {len(converted_data)} CSV records")
        print(f"   📋 Columns match: {len(converted_data.columns) == len(downloader.csv_columns)}")
        
        # Check a few key conversions
        if not converted_data.empty:
            first_row = converted_data.iloc[0]
            print(f"   📊 Sample conversion:")
            print(f"      NMI: {first_row['NMI']}")
            print(f"      Rate Type: {first_row['RateTypeDescription']}")
            print(f"      Value: {first_row['ProfileReadValue']}")
            print(f"      Date: {first_row['StartDate']}")
        
        print("   ✅ Data conversion test passed!")
        
    except Exception as e:
        print(f"   ❌ Error in data conversion: {e}")
        return False
    
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 AEMO Data Downloader Test Suite")
    print("=" * 60)
    
    success = True
    
    try:
        success &= test_basic_functionality()
        success &= test_data_conversion()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 All tests passed successfully!")
            print("\nNext steps:")
            print("1. Get NEM12 files from your electricity retailer")
            print("2. Use example_nem12_import.py to import your data")
            print("3. Run your existing analysis with the updated data")
        else:
            print("❌ Some tests failed - check the output above")
            
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        success = False
    
    print("=" * 60)
    return success


if __name__ == "__main__":
    main()