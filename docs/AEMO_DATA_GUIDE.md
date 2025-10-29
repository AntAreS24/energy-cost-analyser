# AEMO Data Integration Guide

This guide explains how to download and integrate electricity meter data from AEMO (Australian Energy Market Operator) into your energy cost analyzer.

## Overview

**Important**: AEMO does not provide a public API for individual customer meter data. You need to obtain NEM12 files from your electricity retailer or distributor.

## What is NEM12?

NEM12 is the standard file format used by AEMO for interval meter data (typically 30-minute readings). It contains:

- NMI (National Meter Identifier)
- Interval readings (usually every 30 minutes)
- Quality flags
- Usage and solar generation data

## How to Get Your Data

1. **Contact Your Retailer**: Contact your electricity retailer (e.g., AGL, Origin Energy, EnergyAustralia)
2. **Request NEM12 Files**: Ask for NEM12 interval data files for your NMI
3. **Specify Date Range**: Provide the date range you need
4. **Provide NMI**: Give them your NMI number (found on your electricity bill)

## Installation

First, install the required packages:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install nemreader pandas numpy requests
```

## Usage Examples

### 1. Basic Setup

```python
from src.aemo_data_downloader import AEMODataDownloader

# Initialize the downloader
downloader = AEMODataDownloader()

# Your NMI from your electricity bill
my_nmi = "41032871534"  # Replace with your actual NMI
```

### 2. Check What's in a NEM12 File

```python
# Check what NMIs are available in your NEM12 file
nem12_file_path = "path/to/your_nem12_file.csv"
available_nmis = downloader.get_available_nmis_in_file(nem12_file_path)

print("Available NMIs and channels:")
for nmi, channels in available_nmis:
    print(f"  {nmi}: {channels}")
```

### 3. Import NEM12 Data (First Time)

```python
# Import data from NEM12 file for the first time
success, message = downloader.download_and_update_data(
    nmi=my_nmi,
    nem12_file_path="path/to/your_nem12_file.csv"
)

print(f"Import result: {message}")
```

### 4. Update with New NEM12 Data

```python
# The system automatically detects the last entry and only imports new data
success, message = downloader.download_and_update_data(
    nmi=my_nmi,
    nem12_file_path="path/to/new_nem12_file.csv"
)

print(f"Update result: {message}")
```

### 5. Check Last Entry Date

```python
# Check when your data was last updated
last_date = downloader.get_last_entry_date(my_nmi)
if last_date:
    print(f"Data available until: {last_date}")
else:
    print("No data found for this NMI")
```

## Data Format

The system converts NEM12 data to match your existing CSV format:

| Column              | Description                   | Example             |
| ------------------- | ----------------------------- | ------------------- |
| AccountNumber       | Account number (not in NEM12) | 56185416            |
| NMI                 | National Meter Identifier     | 41032871534         |
| DeviceNumber        | Meter serial number           | 700813815           |
| DeviceType          | Device type                   | COMMS4D             |
| RegisterCode        | Register and suffix           | 13815#E1            |
| RateTypeDescription | Usage or Solar                | Usage/Solar         |
| StartDate           | Reading start time            | 04/11/2021 00:00:00 |
| StartDay            | Day of month                  | 4                   |
| StartMonth          | Month number                  | 11                  |
| StartQuarter        | Quarter (1-4)                 | 4                   |
| StartYear           | Year                          | 2021                |
| EndDate             | Reading end time              | 04/11/2021 00:29:59 |
| ProfileReadValue    | Energy value (kWh)            | 0.174               |
| RegisterReadValue   | Usually 0 for interval        | 0                   |
| QualityFlag         | Data quality                  | A                   |

## Channel Types

- **E1, E2, etc.**: Electricity usage (import)
- **B1, B2, etc.**: Solar generation (export)
- **Q1, Q2, etc.**: Reactive power

## Duplicate Prevention

The system automatically prevents duplicates by:

1. Checking existing data for the same NMI, register, and timestamp
2. Only importing new records
3. Maintaining chronological order

## Error Handling

Common issues and solutions:

### "nemreader library not installed"

```bash
pip install nemreader
```

### "NEM12 file not found"

- Check the file path
- Ensure the file exists and is accessible

### "No data found for NMI"

- Verify the NMI number
- Check if the NMI exists in the NEM12 file

### "No new data to add"

- The system detected all data already exists
- This is normal when re-running with the same file

## Complete Example Script

```python
#!/usr/bin/env python3
"""
Example script for importing AEMO meter data
"""

from src.aemo_data_downloader import AEMODataDownloader
from pathlib import Path

def main():
    # Configuration
    MY_NMI = "41032871534"  # Replace with your NMI
    NEM12_FILE = "data/my_meter_data.csv"  # Path to your NEM12 file

    # Initialize downloader
    downloader = AEMODataDownloader()

    # Check if NEM12 file exists
    if not Path(NEM12_FILE).exists():
        print(f"NEM12 file not found: {NEM12_FILE}")
        print("Please obtain a NEM12 file from your electricity retailer")
        return

    # Check what's in the file
    print("Checking available NMIs in file...")
    try:
        nmis = downloader.get_available_nmis_in_file(NEM12_FILE)
        print(f"Found NMIs: {[nmi for nmi, _ in nmis]}")

        # Check if our NMI is in the file
        our_nmi_found = any(nmi == MY_NMI for nmi, _ in nmis)
        if not our_nmi_found:
            print(f"Warning: NMI {MY_NMI} not found in file")
            print("Available NMIs:", [nmi for nmi, _ in nmis])
            return

    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Import the data
    print(f"Importing data for NMI {MY_NMI}...")
    success, message = downloader.download_and_update_data(
        nmi=MY_NMI,
        nem12_file_path=NEM12_FILE
    )

    if success:
        print(f"✅ {message}")

        # Check the results
        last_date = downloader.get_last_entry_date(MY_NMI)
        print(f"Data now available until: {last_date}")

    else:
        print(f"❌ {message}")

if __name__ == "__main__":
    main()
```

## Integration with Existing Code

Your existing `main.py` will continue to work unchanged. The new data will be automatically available in the same CSV format.

## Getting NEM12 Files from Retailers

### Major Australian Retailers

| Retailer        | Contact Method                    |
| --------------- | --------------------------------- |
| AGL             | Online portal or customer service |
| Origin Energy   | Customer portal or phone          |
| EnergyAustralia | Online account or support         |
| Red Energy      | Customer service                  |
| Simply Energy   | Online portal                     |
| Alinta Energy   | Customer portal                   |

### What to Request

- "NEM12 interval data files"
- Your NMI number
- Date range needed
- Specify you need 30-minute interval data

### Typical Response Time

- 1-5 business days
- Some retailers provide instant downloads
- Files are usually emailed or available in customer portal

## Future Enhancements

This framework is designed to be extensible for:

- Real-time data APIs (when available)
- Multiple NMI support
- Automated scheduling
- Data validation and quality checks
- Integration with solar inverter APIs
