#!/usr/bin/env python3
"""
Example script for importing AEMO meter data from NEM12 files

This script demonstrates how to:
1. Import NEM12 data files from your electricity retailer
2. Convert them to the project's CSV format
3. Handle incremental updates and duplicates

Usage:
    python example_nem12_import.py --nmi YOUR_NMI --file path/to/nem12_file.csv
"""

import argparse
import sys
from pathlib import Path
from src.aemo_data_downloader import AEMODataDownloader


def main():
    parser = argparse.ArgumentParser(description='Import AEMO NEM12 meter data')
    parser.add_argument('--nmi', required=True, help='Your NMI number (from electricity bill)')
    parser.add_argument('--file', required=True, help='Path to NEM12 file from your retailer')
    parser.add_argument('--list-nmis', action='store_true', help='List available NMIs in the file and exit')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Check if file exists
    nem12_file = Path(args.file)
    if not nem12_file.exists():
        print(f"❌ Error: NEM12 file not found: {args.file}")
        print("\nTo get NEM12 files:")
        print("1. Contact your electricity retailer (AGL, Origin, EnergyAustralia, etc.)")
        print("2. Request 'NEM12 interval data files' for your NMI")
        print("3. Provide your NMI number and desired date range")
        sys.exit(1)
    
    # Initialize downloader
    downloader = AEMODataDownloader()
    
    # Check if required packages are installed
    if not downloader.check_requirements():
        print("❌ Error: Required packages not installed")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    
    print(f"📄 Processing NEM12 file: {nem12_file}")
    
    # List available NMIs if requested
    try:
        available_nmis = downloader.get_available_nmis_in_file(str(nem12_file))
        
        if args.list_nmis:
            print("\n📋 Available NMIs in file:")
            for nmi, channels in available_nmis:
                print(f"  • {nmi} (channels: {', '.join(channels)})")
            return
        
        if args.verbose:
            print(f"📋 Found {len(available_nmis)} NMI(s) in file:")
            for nmi, channels in available_nmis:
                print(f"  • {nmi}: {', '.join(channels)}")
        
        # Check if requested NMI is in the file
        nmi_found = any(nmi == args.nmi for nmi, _ in available_nmis)
        if not nmi_found:
            print(f"\n⚠️  Warning: NMI {args.nmi} not found in file")
            print("Available NMIs:")
            for nmi, _ in available_nmis:
                print(f"  • {nmi}")
            
            response = input("\nContinue anyway? (y/N): ")
            if not response.lower().startswith('y'):
                print("Operation cancelled")
                sys.exit(0)
        
    except Exception as e:
        print(f"❌ Error reading NEM12 file: {e}")
        sys.exit(1)
    
    # Check current data status
    print(f"\n🔍 Checking existing data for NMI: {args.nmi}")
    last_date = downloader.get_last_entry_date(args.nmi)
    
    if last_date:
        print(f"📅 Last entry found: {last_date}")
        print("   Will import only new data after this date")
    else:
        print("📅 No existing data found - will import all data from file")
    
    # Import the data
    print(f"\n⬇️  Importing data for NMI {args.nmi}...")
    
    success, message = downloader.download_and_update_data(
        nmi=args.nmi,
        nem12_file_path=str(nem12_file)
    )
    
    if success:
        print(f"✅ Success: {message}")
        
        # Show updated status
        new_last_date = downloader.get_last_entry_date(args.nmi)
        if new_last_date:
            print(f"📊 Data now available until: {new_last_date}")
            
            # Show data range
            if last_date and new_last_date > last_date:
                duration = new_last_date - last_date
                print(f"📈 Added {duration.days} days and {duration.seconds // 3600} hours of new data")
        
        print(f"\n💾 Data saved to: data/Energy Providers - Raw Data.csv")
        print("   You can now use this data with your existing energy analysis tools")
        
    else:
        print(f"❌ Failed: {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()