# pricing.py
import json
from datetime import datetime
from typing import Dict, Optional

class PricingManager:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.pricing_config = json.load(f)
    
    def get_rate(self, vendor: str, timestamp: datetime) -> float:
        """Get the applicable rate for a given timestamp"""
        season = self._get_season(vendor, timestamp)
        day_type = 'weekend' if timestamp.weekday() >= 5 else 'weekday'
        hour = timestamp.hour
        
        vendor_rates = self.pricing_config[vendor][season][day_type]
        
        for rate_type, details in vendor_rates.items():
            if self._is_hour_in_range(hour, details['hours']):
                return details['rate']
        
        return 0.0

    def get_solar_rate(self, vendor: str, timestamp: datetime) -> Optional[float]:
        """Get the applicable solar feed-in rate for a given timestamp"""
        season = self._get_season(vendor, timestamp)
        day_type = 'weekend' if timestamp.weekday() >= 5 else 'weekday'
        hour = timestamp.hour
        
        vendor_rates = self.pricing_config[vendor][season][day_type]
        
        for rate_type, details in vendor_rates.items():
            if self._is_hour_in_range(hour, details['hours']):
                return details.get('solar_rate', None)
        
        return None
    
    def _get_season(self, vendor: str, timestamp: datetime) -> str:
        periods = self.pricing_config[vendor]['periods']
        month = timestamp.month
        for value, months in periods.items():
            if month in months:
                return value
    
    def _is_hour_in_range(self, hour: int, ranges: list) -> bool:
        """
        Check if hour falls within any of the given ranges
        Handles ranges that cross midnight (e.g. "22-8")
        """
        for hour_range in ranges:
            start, end = map(int, hour_range.split('-'))
            
            if start < end:
                # Normal range (e.g. "9-17")
                if start <= hour < end:
                    return True
            else:
                # Range crosses midnight (e.g. "22-8")
                if hour >= start or hour < end:
                    return True
        return False
    def get_supply_charge(self, vendor: str) -> float:
        """Get daily supply charge for vendor"""
        return self.pricing_config[vendor]['supply_charge']

    def get_rate_type(self, vendor: str, timestamp: datetime) -> str:
        """Get rate type (peak/off_peak/shoulder) for given timestamp"""
        period = self._get_season(vendor, timestamp)
        day_type = 'weekend' if timestamp.weekday() >= 5 else 'weekday'
        hour = timestamp.hour
        
        vendor_rates = self.pricing_config[vendor][period][day_type]
        
        for rate_type, details in vendor_rates.items():
            if self._is_hour_in_range(hour, details['hours']):
                return rate_type
        
        return 'off_peak'  # Default to off_peak if no matching rate found