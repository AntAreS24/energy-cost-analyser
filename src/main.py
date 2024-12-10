import pandas as pd
from datetime import datetime
from typing import Dict, List
from pricing import PricingManager

class MeterDataParser:
    def __init__(self, file_path: str):
      """Initialize the parser with CSV file path"""
      try:
        self.df = pd.read_csv(
          file_path, 
          parse_dates=['StartDate', 'EndDate'],
          dayfirst=True,
          date_format='%d/%m/%Y %H:%M:%S'
        )
        self.pricing_manager = PricingManager('data/pricing_config.json')
      except Exception as e:
          raise Exception(f"Error loading CSV file: {str(e)}")
    
    def get_usage_by_date(self, date: datetime) -> float:
      """Get total usage for a specific date"""
      date_data = self.df[self.df['StartDate'].dt.date == date.date()]
      return date_data[date_data['RateTypeDescription'] == 'Usage']['ProfileReadValue'].sum()
    
    def get_solar_by_date(self, date: datetime) -> float:
      """Get total solar generation for a specific date"""
      date_data = self.df[self.df['StartDate'].dt.date == date.date()]
      return date_data[date_data['RateTypeDescription'] == 'Solar']['ProfileReadValue'].sum()
    
    def get_device_info(self, nmi: str) -> Dict:
      """Get device information for a specific NMI"""
      device_data = self.df[self.df['NMI'] == nmi].iloc[0]
      return {
          'DeviceNumber': device_data['DeviceNumber'],
          'DeviceType': device_data['DeviceType'],
          'AccountNumber': device_data['AccountNumber']
      }
    
    def calculate_cost(self, date: datetime, vendor: str) -> float:
      """Calculate cost for a specific date using vendor rates"""
      date_data = self.df[self.df['StartDate'].dt.date == date.date()]
      total_cost = 0.0
      
      for _, row in date_data.iterrows():
          if row['RateTypeDescription'] == 'Usage':
              rate = self.pricing_manager.get_rate(vendor, row['StartDate'])
              total_cost += row['ProfileReadValue'] * rate
      
      return total_cost
    
    # def calculate_cost_range(self, start_date: datetime, end_date: datetime, vendor: str) -> Dict:
    #   """Calculate costs for a date range using vendor rates"""
    #   daily_costs = {}
    #   total_cost = 0.0
      
    #   # Create date range
    #   date_range = pd.date_range(start=start_date, end=end_date, freq='D')
      
    #   # Calculate cost for each day
    #   for date in date_range:
    #       daily_cost = self.calculate_cost(date, vendor)
    #       daily_costs[date.date()] = daily_cost
    #       total_cost += daily_cost
      
    #   return {
    #       'daily_costs': daily_costs,
    #       'total_cost': total_cost,
    #       'start_date': start_date.date(),
    #       'end_date': end_date.date(),
    #       'vendor': vendor
    #   }
    def calculate_solar_feedin(self, date: datetime, vendor: str) -> float:
        """Calculate solar feed-in credit for a specific date"""
        date_data = self.df[self.df['StartDate'].dt.date == date.date()]
        total_credit = 0.0
        
        for _, row in date_data.iterrows():
            if row['RateTypeDescription'] == 'Solar':
                rate = self.pricing_manager.get_solar_rate(vendor, row['StartDate'])
                total_credit += row['ProfileReadValue'] * rate
        
        return total_credit

    def calculate_cost_range(self, start_date: datetime, end_date: datetime, vendor: str) -> Dict:
        """Calculate costs and solar credits for a date range"""
        daily_costs = {}
        daily_solar = {}
        total_cost = 0.0
        total_solar = 0.0
        total_supply_charges = 0.0
        total_days = 0
        
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        for date in date_range:
            total_days += 1
            usage_cost = self.calculate_cost(date, vendor)
            solar_credit = self.calculate_solar_feedin(date, vendor)
            supply_charges = self.pricing_manager.get_supply_charge(vendor)
            
            daily_costs[date.date()] = usage_cost
            daily_solar[date.date()] = solar_credit
            
            total_cost += usage_cost
            total_solar += solar_credit
            total_supply_charges += supply_charges
        
        net_cost = total_cost - total_solar + total_supply_charges
        
        return {
            'daily_costs': daily_costs,
            'daily_solar': daily_solar,
            'total_usage_cost': total_cost,
            'total_solar_credit': total_solar,
            'total_supply_charges': total_supply_charges,
            'net_cost': net_cost,
            'start_date': start_date.date(),
            'end_date': end_date.date(),
            'total_days': total_days,
            'vendor': vendor
        }

    def calculate_detailed_breakdown(self, start_date: datetime, end_date: datetime, vendor: str) -> Dict:
        """Calculate detailed cost breakdown including peak/off-peak/shoulder periods"""
        usage_breakdown = {
            'peak': {'kwh': 0.0, 'cost': 0.0},
            'off_peak': {'kwh': 0.0, 'cost': 0.0},
            'shoulder': {'kwh': 0.0, 'cost': 0.0},
            'solar': {'kwh': 0.0, 'credit': 0.0}
        }
        
        total_supply_charges = 0.0
        total_days = 0
        
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        for date in date_range:
            total_days += 1
            date_data = self.df[self.df['StartDate'].dt.date == date.date()]
            supply_charge = self.pricing_manager.get_supply_charge(vendor)
            total_supply_charges += supply_charge
            
            for _, row in date_data.iterrows():
                if row['RateTypeDescription'] == 'Usage':
                    rate = self.pricing_manager.get_rate(vendor, row['StartDate'])
                    rate_type = self.pricing_manager.get_rate_type(vendor, row['StartDate'])
                    
                    usage_breakdown[rate_type]['kwh'] += row['ProfileReadValue']
                    usage_breakdown[rate_type]['cost'] += row['ProfileReadValue'] * rate
                
                elif row['RateTypeDescription'] == 'Solar':
                    solar_rate = self.pricing_manager.get_solar_rate(vendor, row['StartDate'])
                    usage_breakdown['solar']['kwh'] += row['ProfileReadValue']
                    usage_breakdown['solar']['credit'] += row['ProfileReadValue'] * solar_rate
        
        total_usage = sum(period['kwh'] for period in usage_breakdown.values() if period != usage_breakdown['solar'])
        total_cost = sum(period['cost'] for period in usage_breakdown.values() if period != usage_breakdown['solar'])
        sub_total_cost = total_cost + total_supply_charges
        net_cost = sub_total_cost - usage_breakdown['solar']['credit']
        
        return {
            'breakdown': usage_breakdown,
            'total_usage': total_usage,
            'total_cost': total_cost,
            'total_supply_charges': total_supply_charges,
            'sub_total_cost': sub_total_cost,
            'net_cost': net_cost,
            'total_days': total_days,
            'start_date': start_date.date(),
            'end_date': end_date.date(),
            'vendor': vendor
        }

    def print_cost_breakdown(self, breakdown: Dict):
        """Print detailed cost breakdown in tabular format"""
        print(f"\nCost Breakdown for {breakdown['vendor']}")
        print(f"Period: {breakdown['start_date']} to {breakdown['end_date']} ({breakdown['total_days']} days)\n")
        
        print("Usage Breakdown:")
        print("Period     | Usage (kWh) | Rate ($) | Cost ($)")
        print("-" * 45)
        
        for period, data in breakdown['breakdown'].items():
            if period != 'solar':
                rate = data['cost'] / data['kwh'] if data['kwh'] > 0 else 0
                print(f"{period:10} | {data['kwh']:10.2f} | {rate:8.4f} | {data['cost']:8.2f}")
        
        print("-" * 45)
        print(f"Supply Charge {breakdown['total_days']} days            | {breakdown['total_supply_charges']:8.2f}")
        print("-" * 45)
        print(f"Sub total Costs                  | {breakdown['sub_total_cost']:8.2f}")
        print("-" * 45)
        print(f"Solar Feed-in {breakdown['breakdown']['solar']['kwh']:6.2f} kWh         | {-breakdown['breakdown']['solar']['credit']:8.2f}")
        print(f"Net Total                        | {breakdown['net_cost']:8.2f}")
        print("-" * 45)
    
# Example usage
if __name__ == "__main__":
    parser = MeterDataParser('data/Energy Providers - Raw Data.csv')
    
    # Test date range
    # start = datetime(2023, 11, 14)
    # end = datetime(2024, 11, 13)
    start = datetime(2024, 10, 11)
    end = datetime(2024, 11, 10)
    
    # prodivers = ['ampol', 'agl-value-saver-tou']
    prodivers = ['agl-value-saver-fixed']

    print(f"Cost analysis for {start} to {end}:")
    for provider in prodivers:
      # Calculate costs
      print(f"-----------------------------------")
      print(f"Calculating costs for {provider}...")
      costs = parser.calculate_cost_range(start, end, provider)
      
      # Print results
      print(f"\tTotal cost: ${costs['total_usage_cost']:.2f}")
      print(f"\tTotal solar credit: ${costs['total_solar_credit']:.2f}")
      print(f"\tTotal supply charges ({costs['total_days']} days): ${costs['total_supply_charges']:.2f}")
      print(f"\tNet cost: ${costs['net_cost']:.2f}")

      breakdown = parser.calculate_detailed_breakdown(start, end, provider)
      parser.print_cost_breakdown(breakdown)