#!/usr/bin/env python3
"""
Complete demonstration of AEMO data integration

This script shows how to integrate the AEMO data downloader with your existing energy analysis system.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the src directory to Python path
sys.path.append('src')

from aemo_data_downloader import AEMODataDownloader
from main import MeterDataParser
from pricing import PricingManager


def demonstrate_integration():
    """
    Demonstrate the complete integration workflow
    """
    print("=" * 70)
    print("🚀 AEMO Data Integration Demonstration")
    print("=" * 70)
    
    # Initialize components
    downloader = AEMODataDownloader()
    
    print("\n1. 📊 Checking Current Data Status")
    print("-" * 40)
    
    # Check what data we currently have
    nmi = "41032871534"  # The NMI from our sample data
    last_date = downloader.get_last_entry_date(nmi)
    
    if last_date:
        print(f"✅ Found existing data for NMI {nmi}")
        print(f"📅 Data available until: {last_date}")
        
        # Calculate data age
        now = datetime.now()
        if last_date.tzinfo is None:
            last_date = last_date.replace(tzinfo=None)
            now = now.replace(tzinfo=None)
        
        age = now - last_date
        print(f"⏰ Data age: {age.days} days, {age.seconds // 3600} hours")
        
        if age.days > 7:
            print(f"⚠️  Data is more than a week old - consider updating")
        else:
            print(f"✅ Data is relatively recent")
    else:
        print(f"❌ No existing data found for NMI {nmi}")
        print("   You would need to import NEM12 files from your retailer")
    
    print(f"\n2. 🔧 Testing Existing Energy Analysis")
    print("-" * 40)
    
    # Test with existing analysis system
    csv_file = "data/Energy Providers - Raw Data.csv"
    
    if Path(csv_file).exists():
        try:
            # Use existing meter data parser
            parser = MeterDataParser(csv_file)
            
            # Test some analysis functions
            test_date = datetime(2021, 11, 4)  # Date from our sample data
            
            usage = parser.get_usage_by_date(test_date)
            solar = parser.get_solar_by_date(test_date)
            
            print(f"📊 Analysis for {test_date.strftime('%Y-%m-%d')}:")
            print(f"   ⚡ Total usage: {usage:.3f} kWh")
            print(f"   ☀️  Solar generation: {solar:.3f} kWh")
            print(f"   🌐 Net usage: {usage - solar:.3f} kWh")
            
            # Test cost calculation
            try:
                cost = parser.calculate_cost(test_date, "default")
                print(f"   💰 Estimated cost: ${cost:.2f}")
            except Exception as e:
                print(f"   ⚠️  Cost calculation: {e}")
            
        except Exception as e:
            print(f"❌ Error with existing analysis: {e}")
    else:
        print("❌ No CSV data file found")
    
    print(f"\n3. 📥 Data Import Workflow")
    print("-" * 40)
    
    print("To import new data from AEMO:")
    print("1. 📞 Contact your electricity retailer")
    print("   - AGL, Origin Energy, EnergyAustralia, etc.")
    print("   - Request 'NEM12 interval data files'")
    print("   - Provide your NMI and date range")
    
    print(f"\n2. 💾 Import the NEM12 file:")
    print(f"   python example_nem12_import.py --nmi {nmi} --file path/to/nem12_file.csv")
    
    print(f"\n3. ✅ The data will be automatically:")
    print("   - Converted to the existing CSV format")
    print("   - Merged with existing data")
    print("   - Deduplicated to prevent duplicates") 
    print("   - Available for your existing analysis tools")
    
    print(f"\n4. 📈 Suggested Update Schedule")
    print("-" * 40)
    
    if last_date:
        # Calculate when next update should be
        next_update = last_date + timedelta(days=30)  # Monthly updates
        days_until_update = (next_update - datetime.now()).days
        
        if days_until_update > 0:
            print(f"📅 Next suggested update: {next_update.strftime('%Y-%m-%d')}")
            print(f"⏰ Days until update needed: {days_until_update}")
        else:
            print(f"🔄 Update recommended now (data is {-days_until_update} days overdue)")
    
    print(f"\n💡 Tips for Best Results:")
    print("   • Request monthly NEM12 files for regular updates")
    print("   • Keep the original NEM12 files for backup")
    print("   • Monitor for data quality issues in the QualityFlag column")
    print("   • Consider automating the import process for regular updates")
    
    print(f"\n🎯 Example Commands:")
    print(f"   # List what's in a NEM12 file:")
    print(f"   python example_nem12_import.py --file nem12_data.csv --list-nmis")
    print(f"   ")
    print(f"   # Import data for your NMI:")
    print(f"   python example_nem12_import.py --nmi {nmi} --file nem12_data.csv")
    print(f"   ")
    print(f"   # Run your existing analysis:")
    print(f"   python src/main.py")
    
    print("\n" + "=" * 70)
    print("🚀 Ready to integrate AEMO data with your energy analysis!")
    print("=" * 70)


def show_data_format_comparison():
    """
    Show how NEM12 data maps to the CSV format
    """
    print("\n📋 Data Format Mapping (NEM12 → CSV):")
    print("-" * 50)
    
    mapping = [
        ("NMI", "NMI", "Direct mapping"),
        ("Meter Serial", "DeviceNumber", "Device identifier"),
        ("Channel (E1/B1)", "RegisterCode", "Usage/Solar type"),
        ("Reading Time", "StartDate/EndDate", "30-min intervals"),
        ("Reading Value", "ProfileReadValue", "Energy amount (kWh)"),
        ("Quality Flag", "QualityFlag", "Data quality indicator"),
    ]
    
    for nem12, csv, desc in mapping:
        print(f"   {nem12:<15} → {csv:<20} ({desc})")
    
    print(f"\n🔍 Channel Types:")
    print("   E1, E2, etc. → Usage (electricity consumed)")
    print("   B1, B2, etc. → Solar (electricity exported)")
    print("   Q1, Q2, etc. → Reactive power")


if __name__ == "__main__":
    try:
        demonstrate_integration()
        show_data_format_comparison()
    except KeyboardInterrupt:
        print("\n🛑 Demonstration interrupted by user")
    except Exception as e:
        print(f"\n💥 Error during demonstration: {e}")
        print("This might indicate missing dependencies or data files.")