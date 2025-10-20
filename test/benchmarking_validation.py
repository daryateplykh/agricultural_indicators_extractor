import pandas as pd

def benchmarking_validation():
    try:
        results_df = pd.read_csv("data_comparison_duplicate_handling.csv")
    except FileNotFoundError:
        return
    
    country_stats = results_df.groupby('Country').agg({
        'Comparison_Result': 'count'
    }).rename(columns={'Comparison_Result': 'Total_Matches'})
    
    country_stats['Exact_Matches'] = results_df.groupby('Country')['Comparison_Result'].apply(
        lambda x: sum(1 for r in x if 'All exact matches' in r)
    )
    
    country_stats['Accuracy_Percent'] = (country_stats['Exact_Matches'] / country_stats['Total_Matches'] * 100).round(1)
    
    country_stats = country_stats.sort_index()
    
    total_comparisons = len(results_df)
    total_exact_matches = sum(1 for r in results_df['Comparison_Result'] if 'All exact matches' in r)
    overall_accuracy = (total_exact_matches / total_comparisons * 100) if total_comparisons > 0 else 0
    

if __name__ == "__main__":
    benchmarking_validation()
