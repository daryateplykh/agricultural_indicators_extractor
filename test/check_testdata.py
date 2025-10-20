import pandas as pd
import os
import glob
import numpy as np
import re
from data_normalizer import DataNormalizer
from data_normalizer import find_best_reference_match, check_value_between_points
from correlation_analysis import load_comparison_data, prepare_analysis_data, correlation_analysis, descriptive_statistics

normalizer = DataNormalizer()

def extract_testdata_with_units(file_path):
    try:
        df = pd.read_csv(file_path)
        
        data = []
        for _, row in df.iterrows():
            value = normalizer.clean_value(row['Value'])
            year = normalizer.extract_year_from_string(row['Year'])
            
            if value is None or year is None:
                continue
            
            crop_name, data_type = normalizer.extract_crop_and_type_from_indicator(row['Indicator'])
            
            if crop_name and data_type:
                normalized_unit = normalizer.normalize_unit(row['Unit'])
                
                data.append({
                    'Country': row['Country'],
                    'Year': year,
                    'Category': crop_name,
                    'Indicator': data_type,
                    'Value': value,
                    'Unit': normalized_unit if normalized_unit else 'Unknown',
                    'Original_Unit': row['Unit'] if pd.notna(row['Unit']) else 'Unknown'
                })
        
        return data
        
    except Exception as e:
        return []

def merge_testdata_files_with_units(country_folder):
    all_data = []
    
    csv_files = glob.glob(os.path.join(country_folder, "*.csv"))
    
    for file_path in csv_files:
        file_data = extract_testdata_with_units(file_path)
        all_data.extend(file_data)
    
    if all_data:
        return pd.DataFrame(all_data)
    else:
        return pd.DataFrame()


from data_normalizer import find_best_reference_match, check_value_between_points


def find_matching_combinations_with_units(reference_df, test_df):
    matches = []
    
    ref_combinations = set()
    for _, row in reference_df.iterrows():
        ref_combinations.add((row['Country'], row['Category'], row['Indicator']))
    
    test_combinations = set()
    for _, row in test_df.iterrows():
        test_combinations.add((row['Country'], row['Category'], row['Indicator']))
    
    common_combinations = ref_combinations.intersection(test_combinations)
    
    return list(common_combinations)

def compare_values_within_range(ref_data, test_data, year_tolerance=5):
    matches = []
    
    for _, test_row in test_data.iterrows():
        test_year = test_row['Year']
        test_value = test_row['Value']
        
        ref_in_range = ref_data[
            (ref_data['Year'] >= test_year - year_tolerance) & 
            (ref_data['Year'] <= test_year + year_tolerance)
        ]
        
        if len(ref_in_range) > 0:
            ref_in_range = ref_in_range.copy()
            ref_in_range['Year_Diff'] = abs(ref_in_range['Year'] - test_year)
            closest_ref = ref_in_range.loc[ref_in_range['Year_Diff'].idxmin()]
            
            ref_year = closest_ref['Year']
            ref_value = closest_ref['Value']
            
            if ref_value != 0:
                deviation_percent = abs((test_value - ref_value) / ref_value) * 100
            else:
                deviation_percent = float('inf') if test_value != 0 else 0
            
            matches.append({
                'Test_Year': test_year,
                'Test_Value': test_value,
                'Ref_Year': ref_year,
                'Ref_Value': ref_value,
                'Year_Diff': abs(test_year - ref_year),
                'Value_Diff': abs(test_value - ref_value),
                'Deviation_Percent': deviation_percent
            })
    
    return matches

def compare_trends_and_values_with_duplicates(reference_df, test_df, country_name):
    results = []
    
    normalized_test_df = normalizer.normalize_test_data_to_reference(test_df, reference_df)
    
    matching_combinations = find_matching_combinations_with_units(reference_df, normalized_test_df)
    
    unit_conversions = 0
    
    for country, category, indicator in matching_combinations:
        ref_data = reference_df[
            (reference_df['Country'] == country) & 
            (reference_df['Category'] == category) &
            (reference_df['Indicator'] == indicator)
        ].sort_values('Year')
        
        test_data = normalized_test_df[
            (normalized_test_df['Country'] == country) & 
            (normalized_test_df['Category'] == category) &
            (normalized_test_df['Indicator'] == indicator)
        ].sort_values('Year')
        
        if len(ref_data) == 0 or len(test_data) == 0:
            continue
        
        conversions_in_this_comparison = test_data['Unit_Converted'].sum()
        unit_conversions += conversions_in_this_comparison
        
        ref_years = sorted(ref_data['Year'].unique())
        test_years = sorted(test_data['Year'].unique())
        
        ref_min_year = min(ref_years)
        ref_max_year = max(ref_years)
        test_min_year = min(test_years)
        test_max_year = max(test_years)
        
        time_overlap = "No overlap"
        if (test_min_year <= ref_max_year and test_max_year >= ref_min_year):
            time_overlap = "Overlap"
        
        years_in_range = []
        for year in test_years:
            if ref_min_year <= year <= ref_max_year:
                years_in_range.append(year)
        
        years_in_range_percent = len(years_in_range) / len(test_years) * 100 if len(test_years) > 0 else 0
        
        exact_matches, total_test_values, avg_deviation = normalizer.compare_test_data_with_reference(test_data, ref_data)
        
        comparison_result = normalizer.determine_comparison_result(exact_matches, total_test_values, avg_deviation)
        
        ref_unit = ref_data['Unit'].mode().iloc[0] if len(ref_data['Unit'].mode()) > 0 else ref_data['Unit'].iloc[0]
        test_unit = test_data['Unit'].mode().iloc[0] if len(test_data['Unit'].mode()) > 0 else test_data['Unit'].iloc[0]
        
        unit_compatibility = "Compatible" if ref_unit == test_unit else "Converted"
        
        results.append({
            'Country': country_name,
            'Category': category,
            'Indicator': indicator,
            'Comparison_Type': "Exact + Interpolation",
            'Comparison_Result': comparison_result,
            'Reference_Data_Points': len(ref_data),
            'Test_Data_Points': len(test_data),
            'Reference_Years': f"{ref_min_year}-{ref_max_year}",
            'Test_Years': f"{test_min_year}-{test_max_year}",
            'Time_Overlap': time_overlap,
            'Years_In_Range_Percent': years_in_range_percent,
            'Years_In_Range': len(years_in_range),
            'Reference_Unit': ref_unit,
            'Test_Unit': test_unit,
            'Unit_Compatibility': unit_compatibility,
            'Unit_Conversions': conversions_in_this_comparison
        })
    
    return results

def check_testdata_with_duplicate_handling():
    testdata_dir = r"C:\Users\alexe\IdeaProjects\Rag_Pipline_Thesis_Teplykh\test\testData"
    historicaldata_dir = r"C:\Users\alexe\IdeaProjects\Rag_Pipline_Thesis_Teplykh\test\historicalData"
    
    all_results = []
    processed_countries = 0
    total_matches = 0
    total_unit_conversions = 0
    
    country_folders = [f for f in os.listdir(testdata_dir) 
                      if os.path.isdir(os.path.join(testdata_dir, f))]
    
    for country_folder in country_folders:
        country_name = country_folder
        
        test_country_path = os.path.join(testdata_dir, country_folder)
        reference_file = os.path.join(historicaldata_dir, f"{country_name}.csv")
        
        if not os.path.exists(reference_file):
            continue
        
        try:
            reference_df = pd.read_csv(reference_file)
            
            test_df = merge_testdata_files_with_units(test_country_path)
            
            if len(test_df) == 0:
                continue
            
            comparison_results = compare_trends_and_values_with_duplicates(reference_df, test_df, country_name)
            all_results.extend(comparison_results)
            
            processed_countries += 1
            total_matches += len(comparison_results)
            
            country_conversions = sum([r['Unit_Conversions'] for r in comparison_results])
            total_unit_conversions += country_conversions
            
        except Exception as e:
            continue
    
    if all_results:
        results_df = pd.DataFrame(all_results)
        output_file = "data_comparison_duplicate_handling.csv"
        results_df.to_csv(output_file, index=False, encoding='utf-8')
        
        return results_df
    else:
        return pd.DataFrame()

def analyze_results(results_df):
    if len(results_df) == 0:
        return
    
    country_stats = results_df.groupby('Country').agg({
        'Comparison_Result': 'count',
        'Comparison_Result': lambda x: sum(1 for r in x if 'All exact matches' in r)
    }).rename(columns={'Comparison_Result': 'Total_Matches'})
    
    country_stats['Exact_Matches'] = results_df.groupby('Country')['Comparison_Result'].apply(
        lambda x: sum(1 for r in x if 'All exact matches' in r or 'Some exact matches' in r)
    )
    
    country_stats['Accuracy_Percent'] = (country_stats['Exact_Matches'] / country_stats['Total_Matches'] * 100).round(1)
    
    country_stats = country_stats.sort_index()
    
    total_comparisons = len(results_df)
    total_exact_matches = sum(1 for r in results_df['Comparison_Result'] if 'All exact matches' in r or 'Some exact matches' in r)
    overall_accuracy = (total_exact_matches / total_comparisons * 100) if total_comparisons > 0 else 0

def run_correlation_analysis():
    df = load_comparison_data()
    if df is None:
        return
    
    analysis_df = prepare_analysis_data(df)
    if len(analysis_df) == 0:
        return
    
    stats = descriptive_statistics(analysis_df)
    correlations = correlation_analysis(analysis_df)
    
    print(f"Total comparisons: {stats['total_comparisons']}")
    print(f"Exact matches: {stats['exact_matches']}")
    print(f"Overall accuracy: {stats['accuracy_rate']:.1f}%")
    print()
    print("Key correlations:")
    for name, corr, p_val in correlations:
        significance = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else ""
        print(f"  {name}: {corr:.3f} (p={p_val:.3f}) {significance}")

if __name__ == "__main__":
    results_df = check_testdata_with_duplicate_handling()
    analyze_results(results_df)
    run_correlation_analysis()
