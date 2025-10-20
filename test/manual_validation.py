import pandas as pd
import os
import glob
from data_normalizer import DataNormalizer

normalizer = DataNormalizer()

def merge_files_in_country_folder(country_folder_path):
    all_data = []
    csv_files = glob.glob(os.path.join(country_folder_path, "*.csv"))
    
    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            for _, row in df.iterrows():
                value = normalizer.clean_value(row['Value'])
                year = normalizer.extract_year_from_string(row['Year'])
                
                if value is None or year is None:
                    continue
                
                crop_name, data_type = normalizer.extract_crop_and_type_from_indicator(row['Indicator'])
                
                if crop_name and data_type:
                    normalized_unit = normalizer.normalize_unit(row['Unit'])
                    
                    all_data.append({
                        'Country': row['Country'],
                        'Year': year,
                        'Category': crop_name,
                        'Indicator': data_type,
                        'Value': value,
                        'Unit': normalized_unit if normalized_unit else 'Unknown'
                    })
        except Exception as e:
            continue
    
    return pd.DataFrame(all_data)

def compare_dataframes_correctly(gold_df, test_df):
    if len(gold_df) == 0 and len(test_df) == 0:
        return {'total_combinations': 0, 'matches': 0, 'differences': 0, 'accuracy': 100.0}
    
    gold_keys = set()
    test_keys = set()
    
    gold_data = {}
    test_data = {}
    
    for _, row in gold_df.iterrows():
        key = f"{row['Country']},{row['Year']},{row['Category']},{row['Indicator']}"
        gold_keys.add(key)
        gold_data[key] = f"{row['Value']},{row['Unit']}"
    
    for _, row in test_df.iterrows():
        key = f"{row['Country']},{row['Year']},{row['Category']},{row['Indicator']}"
        test_keys.add(key)
        test_data[key] = f"{row['Value']},{row['Unit']}"
    
    common_keys = gold_keys.intersection(test_keys)
    total_combinations = len(common_keys)
    
    matches = 0
    differences = []
    
    for key in common_keys:
        gold_value_unit = gold_data[key]
        test_value_unit = test_data[key]
        
        if gold_value_unit == test_value_unit:
            matches += 1
        else:
            differences.append({
                'combination': key,
                'gold_value_unit': gold_value_unit,
                'test_value_unit': test_value_unit
            })
    
    accuracy = (matches / total_combinations * 100) if total_combinations > 0 else 0
    
    return {
        'total_combinations': total_combinations,
        'matches': matches,
        'differences': len(differences),
        'accuracy': accuracy,
        'differences_details': differences,
        'gold_only': len(gold_keys - test_keys),
        'test_only': len(test_keys - gold_keys)
    }

def manual_validation():
    gold_dir = r"C:\Users\alexe\IdeaProjects\Rag_Pipline_Thesis_Teplykh\test\goldValue"
    test_dir = r"C:\Users\alexe\IdeaProjects\Rag_Pipline_Thesis_Teplykh\test\valueForTest"
    
    gold_countries = set()
    test_countries = set()
    
    for item in os.listdir(gold_dir):
        item_path = os.path.join(gold_dir, item)
        if os.path.isdir(item_path):
            gold_countries.add(item)
    
    for item in os.listdir(test_dir):
        item_path = os.path.join(test_dir, item)
        if os.path.isdir(item_path):
            test_countries.add(item)
    
    matching_countries = gold_countries.intersection(test_countries)
    
    results = []
    total_matches = 0
    total_combinations = 0
    total_differences = 0
    
    for country in matching_countries:
        gold_country_path = os.path.join(gold_dir, country)
        test_country_path = os.path.join(test_dir, country)
        
        gold_df = merge_files_in_country_folder(gold_country_path)
        test_df = merge_files_in_country_folder(test_country_path)
        
        comparison_result = compare_dataframes_correctly(gold_df, test_df)
        
        results.append({
            'country': country,
            'total_combinations': comparison_result['total_combinations'],
            'matches': comparison_result['matches'],
            'differences': comparison_result['differences'],
            'accuracy': comparison_result['accuracy'],
            'gold_only': comparison_result.get('gold_only', 0),
            'test_only': comparison_result.get('test_only', 0),
            'gold_files_count': len(glob.glob(os.path.join(gold_country_path, "*.csv"))),
            'test_files_count': len(glob.glob(os.path.join(test_country_path, "*.csv")))
        })
        
        total_matches += comparison_result['matches']
        total_combinations += comparison_result['total_combinations']
        total_differences += comparison_result['differences']
    
    overall_accuracy = (total_matches / total_combinations * 100) if total_combinations > 0 else 0
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('accuracy', ascending=False)
    results_df.to_csv("manual_validation_results.csv", index=False)
    
    print(f"Overall accuracy: {overall_accuracy:.1f}%")
    
    return results_df

if __name__ == "__main__":
    manual_validation()
