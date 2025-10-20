import pandas as pd
import numpy as np
import re
import yaml
import os

class DataNormalizer:
    
    def __init__(self, config_file=None):
        if config_file is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(current_dir, 'indicator_mapping.yaml')
        
        self.config = self._load_config(config_file)
        
        self.unit_mappings = self.config.get('unit_mappings', {})
        self.conversions = self.config.get('unit_conversions', {})
        self.crop_mappings = self.config.get('crop_mappings', {})
    
    def _load_config(self, config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                return config if config else {}
        except:
            return {}
    
    def clean_value(self, value):
        if pd.isna(value) or value == '':
            return None
        
        value_str = str(value).strip()
        value_str = value_str.replace(' ', '')
        value_str = value_str.replace(',', '')
        
        try:
            return float(value_str)
        except ValueError:
            return None
    
    def extract_year_from_string(self, year_str):
        if pd.isna(year_str):
            return None
        
        year_str = str(year_str).strip()
        
        try:
            return int(year_str)
        except ValueError:
            pass
        
        match = re.search(r'(\d{4})', year_str)
        if match:
            return int(match.group(1))
        
        return None
    
    def normalize_unit(self, unit_str):
        if pd.isna(unit_str):
            return None
        
        unit_str = str(unit_str).lower().strip()
        
        for key, value in self.unit_mappings.items():
            if key in unit_str:
                return value
        
        return unit_str
    
    def convert_to_reference_unit(self, value, from_unit, to_unit):
        if pd.isna(value) or from_unit == to_unit:
            return value
        
        conversion_key = f"{from_unit}_to_{to_unit}"
        
        if conversion_key in self.conversions:
            return value * self.conversions[conversion_key]
        
        return value
    
    def extract_crop_and_type_from_indicator(self, indicator):
        if pd.isna(indicator):
            return None, None
        
        indicator = str(indicator).lower().strip()
        
        data_type = None
        if 'hectares' in indicator or 'area' in indicator:
            data_type = 'Area'
        elif 'metric tons' in indicator or 'production' in indicator or 'tons' in indicator:
            data_type = 'Production'
        
        crop_name = None
        
        for key, value in self.crop_mappings.items():
            if key in indicator:
                crop_name = value
                break
        
        return crop_name, data_type
    
    def normalize_single_test_record(self, test_row, reference_df):
        ref_data = reference_df[
            (reference_df['Country'] == test_row['Country']) & 
            (reference_df['Category'] == test_row['Category']) &
            (reference_df['Indicator'] == test_row['Indicator'])
        ]
        
        if len(ref_data) > 0:
            ref_unit = ref_data['Unit'].mode().iloc[0] if len(ref_data['Unit'].mode()) > 0 else ref_data['Unit'].iloc[0]
            
            converted_value = self.convert_to_reference_unit(
                test_row['Value'], 
                test_row['Unit'], 
                ref_unit
            )
            
            normalized_row = test_row.copy()
            normalized_row['Value'] = converted_value
            normalized_row['Unit'] = ref_unit
            normalized_row['Unit_Converted'] = test_row['Unit'] != ref_unit
            
            return normalized_row
        else:
            normalized_row = test_row.copy()
            normalized_row['Unit_Converted'] = False
            return normalized_row
    
    def normalize_test_data_to_reference(self, test_df, reference_df):
        normalized_data = []
        
        for _, test_row in test_df.iterrows():
            normalized_row = self.normalize_single_test_record(test_row, reference_df)
            normalized_data.append(normalized_row)
        
        return pd.DataFrame(normalized_data)
    
    def compare_test_data_with_reference(self, test_data, ref_data):
        exact_matches = 0
        total_test_values = len(test_data)
        avg_deviation = 0
        
        for _, test_row in test_data.iterrows():
            test_year = test_row['Year']
            test_value = test_row['Value']
            test_unit = test_row['Unit']
            
            ref_data_year = ref_data[ref_data['Year'] == test_year]
            
            if len(ref_data_year) > 0:
                best_match, deviation, match_type = find_best_reference_match(ref_data_year, test_value, test_unit)
                
                if best_match is not None:
                    if deviation <= 1:
                        exact_matches += 1
                    avg_deviation += deviation
                else:
                    avg_deviation += 100
            else:
                if len(ref_data) >= 2:
                    within_range, deviation, interpolated, status = check_value_between_points(ref_data, test_value, test_year)
                    if within_range:
                        exact_matches += 1
                    avg_deviation += deviation
                else:
                    avg_deviation += 100
        
        avg_deviation = avg_deviation / total_test_values if total_test_values > 0 else 0
        
        return exact_matches, total_test_values, avg_deviation
    
    def determine_comparison_result(self, exact_matches, total_test_values, avg_deviation):
        if exact_matches == total_test_values:
            result = "All exact matches"
        elif exact_matches > total_test_values * 0.7:
            result = "Mostly exact matches"
        elif exact_matches > 0:
            result = "Some exact matches"
        else:
            result = "No exact matches"
        
        return f"{result} ({exact_matches}/{total_test_values}, avg dev: {avg_deviation:.1f}%)"


def find_best_reference_match(ref_data, test_value, test_unit):
    if len(ref_data) == 0:
        return None, None, None
    
    if len(ref_data) == 1:
        return ref_data.iloc[0], 0, "Single match"
    
    temp_normalizer = DataNormalizer()
    
    ref_data_copy = ref_data.copy()
    ref_data_copy['Converted_Value'] = ref_data_copy.apply(
        lambda row: temp_normalizer.convert_to_reference_unit(row['Value'], row['Unit'], test_unit), 
        axis=1
    )
    
    ref_data_copy['Deviation'] = abs(ref_data_copy['Converted_Value'] - test_value)
    ref_data_copy['Deviation_Percent'] = ref_data_copy.apply(
        lambda row: abs((row['Converted_Value'] - test_value) / test_value * 100) if test_value != 0 else float('inf'),
        axis=1
    )
    
    ref_data_copy = ref_data_copy.sort_values('Deviation_Percent')
    
    best_match = ref_data_copy.iloc[0]
    deviation_percent = best_match['Deviation_Percent']
    
    if deviation_percent == 0:
        match_type = "Exact match"
    elif deviation_percent <= 1:
        match_type = "Very close"
    elif deviation_percent <= 5:
        match_type = "Close"
    elif deviation_percent <= 20:
        match_type = "Reasonable"
    else:
        match_type = "Far"
    
    return best_match, deviation_percent, match_type


def interpolate_between_points(ref_data, test_year):
    if len(ref_data) < 2:
        return None, None, None
    
    ref_sorted = ref_data.sort_values('Year')
    
    years = ref_sorted['Year'].values
    values = ref_sorted['Value'].values
    
    if test_year in years:
        idx = np.where(years == test_year)[0][0]
        return values[idx], test_year, 0
    
    if test_year < years[0]:
        return None, None, None
    elif test_year > years[-1]:
        return None, None, None
    else:
        for i in range(len(years) - 1):
            if years[i] <= test_year <= years[i + 1]:
                year1, year2 = years[i], years[i + 1]
                value1, value2 = values[i], values[i + 1]
                
                if year2 != year1:
                    interpolated_value = value1 + (value2 - value1) * (test_year - year1) / (year2 - year1)
                else:
                    interpolated_value = value1
                
                return interpolated_value, test_year, abs(test_year - year1)
    
    return None, None, None


def check_value_between_points(ref_data, test_value, test_year, tolerance_percent=20):
    if len(ref_data) < 2:
        return False, 0, 0, "Insufficient reference data"
    
    interpolated_value, interpolated_year, year_diff = interpolate_between_points(ref_data, test_year)
    
    if interpolated_value is None:
        return False, 0, 0, "Test year outside reference range"
    
    if interpolated_value != 0:
        deviation_percent = abs((test_value - interpolated_value) / interpolated_value) * 100
    else:
        deviation_percent = float('inf') if test_value != 0 else 0
    
    within_tolerance = deviation_percent <= tolerance_percent
    
    return within_tolerance, deviation_percent, interpolated_value, f"Interpolated from reference data"
