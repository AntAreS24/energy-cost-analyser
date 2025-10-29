# Energy Usage Cost Calculator

A Python utility for calculating electricity costs from meter data, with integrated support for AEMO (Australian Energy Market Operator) data import.

## Features

- **📊 Energy Analysis**: Usage and solar feed-in calculations
- **💰 Cost Calculation**: Time-of-use pricing (peak/off-peak/shoulder)
- **🏢 Multi-Vendor**: Multiple vendor rate structures
- **📅 Detailed Billing**: Daily supply charges and cost breakdowns
- **🇦🇺 AEMO Integration**: Direct import from NEM12 files (Australia)
- **🔄 Data Management**: Automatic deduplication and incremental updates

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd energy-calculator
```

1. Create virtual environment

```bash
pyenv install 3.12
pyenv shell 3.12
python -m venv venv
source venv/bin/activate  # On Mac/Linux
```

1. Install dependencies

```bash
pip install -r requirements.txt
```

## Data Sources

### Option 1: AEMO Integration (Recommended for Australian Users) 🇦🇺

For Australian electricity customers, you can import data directly from NEM12 files:

1. **Get NEM12 files** from your retailer (AGL, Origin, EnergyAustralia, etc.)
2. **Import automatically** with built-in conversion and deduplication

```bash
# Check what NMIs are in your file
python example_nem12_import.py --file your_nem12_data.csv --list-nmis

# Import data for your NMI
python example_nem12_import.py --nmi YOUR_NMI --file your_nem12_data.csv
```

### Option 2: Manual CSV Data

You can also provide data in this CSV format:

```csv
AccountNumber,NMI,DeviceNumber,DeviceType,RegisterCode,RateTypeDescription,StartDate,Start Day,Start Month,Start Quarter,Start Year,EndDate,ProfileReadValue,RegisterReadValue,QualityFlag
```

## Configuration

Create a pricing config file. Check the example in `/data/pricing_config.json`.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Import Your Data (Australian Users)

```bash
# Get NEM12 file from your retailer, then:
python example_nem12_import.py --nmi YOUR_NMI --file path/to/nem12_file.csv
```

### 3. Run Analysis

```python
from datetime import datetime
from src.main import MeterDataParser

# Initialize parser with your data
parser = MeterDataParser('data/Energy Providers - Raw Data.csv')

# Calculate costs for a date range
start_date = datetime(2023, 11, 1)
end_date = datetime(2023, 11, 30)
results = parser.calculate_cost_range(start_date, end_date, 'vendor_1')

print(f"Net cost: ${results['net_cost']:.2f}")
```

### Detailed Cost Breakdown

```python
breakdown = parser.calculate_detailed_breakdown(start_date, end_date, 'vendor_1') # the name of the vendor MUST match the name in the pricing_config file.
parser.print_cost_breakdown(breakdown)
```

Sample output:

```bash
Cost Breakdown for vendor_1
Period: 2023-11-01 to 2023-11-30 (30 days)

Usage Breakdown:
Period     | Usage (kWh) | Rate ($) | Cost ($)
---------------------------------------------
peak       |     150.20 |   0.4500 |   67.59
shoulder   |     220.30 |   0.2500 |   55.08
off_peak   |     180.50 |   0.1500 |   27.08
---------------------------------------------
Supply Charge 30 days          |    28.50
Solar Feed-in 85.20 kWh        |   -12.78
---------------------------------------------
Net Total                      |   165.47
```

## 🇦🇺 AEMO Data Integration

### Getting Your Data

For Australian users, contact your electricity retailer to request **NEM12 files**:

| Retailer        | How to Request                    |
| --------------- | --------------------------------- |
| AGL             | Online portal or customer service |
| Origin Energy   | Customer portal or phone          |
| EnergyAustralia | Online account or support         |
| Red Energy      | Customer service                  |
| Simply Energy   | Online portal                     |

**What to Ask For:**

- "NEM12 interval data files"
- Your NMI number (from your electricity bill)
- Date range you need
- 30-minute interval data

### Import Process

```bash
# 1. Check what's in your NEM12 file
python example_nem12_import.py --file your_nem12_data.csv --list-nmis

# 2. Import data for your specific NMI
python example_nem12_import.py --nmi YOUR_NMI --file your_nem12_data.csv --verbose

# 3. Run analysis with updated data
python demo_integration.py
```

### Incremental Updates

The system automatically handles:

- **Duplicate Prevention**: Won't import the same data twice
- **Incremental Updates**: Only imports new data after your last entry
- **Data Validation**: Maintains data quality and format consistency

```python
from src.aemo_data_downloader import AEMODataDownloader

# Check your current data status
downloader = AEMODataDownloader()
last_date = downloader.get_last_entry_date("YOUR_NMI")
print(f"Data available until: {last_date}")

# Import new data (will only add new records)
success, message = downloader.download_and_update_data(
    nmi="YOUR_NMI",
    nem12_file_path="new_data.csv"
)
```

### Data Format Conversion

NEM12 files are automatically converted to the system's format:

| NEM12 Field     | System Field      | Description                |
| --------------- | ----------------- | -------------------------- |
| NMI             | NMI               | Direct mapping             |
| Channel (E1/B1) | RegisterCode      | Usage/Solar classification |
| Reading Time    | StartDate/EndDate | 30-minute intervals        |
| Reading Value   | ProfileReadValue  | Energy amount (kWh)        |
| Quality Flag    | QualityFlag       | Data quality indicator     |

**Channel Types:**

- `E1, E2, etc.` → Usage (electricity consumed)
- `B1, B2, etc.` → Solar (electricity exported)
- `Q1, Q2, etc.` → Reactive power

## Files

- `src/main.py` - Main analysis engine
- `src/pricing.py` - Pricing calculation logic
- `src/aemo_data_downloader.py` - AEMO/NEM12 data integration
- `example_nem12_import.py` - Command-line import tool
- `demo_integration.py` - Full integration demonstration
- `docs/AEMO_DATA_GUIDE.md` - Detailed AEMO integration guide
