# Energy Usage Cost Calculator

A Python utility for calculating electricity costs from meter data, supporting:

- Usage and solar feed-in calculations
- Time-of-use pricing (peak/off-peak/shoulder)
- Multiple vendor rate structures
- Daily supply charges
- Detailed cost breakdowns

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

## Usage

You're expected to download the raw data from your energy supplier. The CSV should have the following columns:

```csv
AccountNumber,NMI,DeviceNumber,DeviceType,RegisterCode,RateTypeDescription,StartDate,Start Day,Start Month,Start Quarter,Start Year,EndDate,ProfileReadValue,RegisterReadValue,QualityFlag
```

Then, you need to create a pricing config. Check out the exammple in `/data/pricing_config.json`.

### Basic Usage

```python
from datetime import datetime
from meter_parser import MeterDataParser

# Initialize parser with meter data
parser = MeterDataParser('data/Energy Providers - Raw Data.csv')

# Calculate costs for a date range
start_date = datetime(2023, 11, 1)
end_date = datetime(2023, 11, 30)
results = parser.calculate_cost_range(start_date, end_date, 'vendor_1') # the name of the vendor MUST match the name in the pricing_config file.

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
