import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr, kendalltau, ttest_ind, f_oneway, chi2_contingency
import matplotlib.pyplot as plt
import seaborn as sns

def load_comparison_data():
    try:
        df = pd.read_csv("data_comparison_duplicate_handling.csv")
        return df
    except FileNotFoundError:
        return None

def prepare_analysis_data(df):
    analysis_data = []
    
    for _, row in df.iterrows():
        year_range = str(row['Reference_Years'])
        if '-' in year_range:
            start_year = int(year_range.split('-')[0])
        else:
            start_year = int(year_range) if year_range.isdigit() else None
        
        analysis_data.append({
            'Country': row['Country'],
            'Category': row['Category'],
            'Indicator': row['Indicator'],
            'Start_Year': start_year,
            'Test_Data_Points': row['Test_Data_Points'],
            'Reference_Data_Points': row['Reference_Data_Points'],
            'Years_In_Range_Percent': row['Years_In_Range_Percent'],
            'Is_Exact_Match': 'All exact matches' in row['Comparison_Result'] or 'Some exact matches' in row['Comparison_Result'],
            'Is_All_Exact': 'All exact matches' in row['Comparison_Result'],
            'Unit_Compatibility': row['Unit_Compatibility'],
            'Time_Overlap': row['Time_Overlap']
        })
    
    analysis_df = pd.DataFrame(analysis_data)
    analysis_df = analysis_df.dropna(subset=['Start_Year'])
    
    return analysis_df

def correlation_analysis(df):
    numeric_cols = ['Start_Year', 'Test_Data_Points', 'Reference_Data_Points', 'Years_In_Range_Percent']
    
    corr_matrix = df[numeric_cols].corr()
    
    correlations = []
    
    if len(df) > 1:
        year_test_corr, year_test_p = pearsonr(df['Start_Year'], df['Test_Data_Points'])
        correlations.append(('Year vs Test Data', year_test_corr, year_test_p))
        
        ref_test_corr, ref_test_p = pearsonr(df['Reference_Data_Points'], df['Test_Data_Points'])
        correlations.append(('Reference vs Test Data', ref_test_corr, ref_test_p))
        
        range_accuracy_corr, range_accuracy_p = spearmanr(df['Years_In_Range_Percent'], df['Is_Exact_Match'].astype(int))
        correlations.append(('Temporal Overlap vs Accuracy', range_accuracy_corr, range_accuracy_p))
        
        ref_accuracy_corr, ref_accuracy_p = spearmanr(df['Reference_Data_Points'], df['Is_Exact_Match'].astype(int))
        correlations.append(('Reference Data vs Accuracy', ref_accuracy_corr, ref_accuracy_p))
    
    return correlations

def statistical_tests(df):
    exact_group = df[df['Is_Exact_Match'] == True]['Reference_Data_Points']
    inexact_group = df[df['Is_Exact_Match'] == False]['Reference_Data_Points']
    
    t_stat, t_p = None, None
    if len(exact_group) > 0 and len(inexact_group) > 0:
        t_stat, t_p = ttest_ind(exact_group, inexact_group)
    
    exact_range = df[df['Is_Exact_Match'] == True]['Years_In_Range_Percent']
    inexact_range = df[df['Is_Exact_Match'] == False]['Years_In_Range_Percent']
    
    t_stat2, t_p2 = None, None
    if len(exact_range) > 0 and len(inexact_range) > 0:
        t_stat2, t_p2 = ttest_ind(exact_range, inexact_range)
    
    crop_groups = [group['Is_Exact_Match'].astype(int).values for name, group in df.groupby('Category') if len(group) >= 3]
    f_stat, f_p = None, None
    if len(crop_groups) >= 2:
        f_stat, f_p = f_oneway(*crop_groups)
    
    contingency_table = pd.crosstab(df['Indicator'], df['Is_Exact_Match'])
    chi2_stat, chi2_p, dof, expected = None, None, None, None
    if contingency_table.shape[0] >= 2 and contingency_table.shape[1] >= 2:
        chi2_stat, chi2_p, dof, expected = chi2_contingency(contingency_table)
    
    return {
        't_test_ref': (t_stat, t_p),
        't_test_range': (t_stat2, t_p2),
        'anova_crops': (f_stat, f_p),
        'chi2_indicator': (chi2_stat, chi2_p, dof, expected)
    }

def descriptive_statistics(df):
    total_comparisons = len(df)
    exact_matches = df['Is_Exact_Match'].sum()
    accuracy_rate = (exact_matches / total_comparisons * 100) if total_comparisons > 0 else 0
    
    country_stats = df.groupby('Country').agg({
        'Test_Data_Points': 'mean',
        'Reference_Data_Points': 'mean',
        'Years_In_Range_Percent': 'mean',
        'Is_Exact_Match': 'mean'
    }).round(2)
    
    crop_stats = df.groupby('Category').agg({
        'Test_Data_Points': 'mean',
        'Reference_Data_Points': 'mean',
        'Is_Exact_Match': 'mean'
    }).round(2)
    
    indicator_stats = df.groupby('Indicator').agg({
        'Test_Data_Points': 'mean',
        'Reference_Data_Points': 'mean',
        'Is_Exact_Match': 'mean'
    }).round(2)
    
    return {
        'total_comparisons': total_comparisons,
        'exact_matches': exact_matches,
        'accuracy_rate': accuracy_rate,
        'country_stats': country_stats,
        'crop_stats': crop_stats,
        'indicator_stats': indicator_stats
    }

def main():
    df = load_comparison_data()
    if df is None:
        return
    
    analysis_df = prepare_analysis_data(df)
    
    if len(analysis_df) == 0:
        return
    
    descriptive_statistics(analysis_df)
    correlations = correlation_analysis(analysis_df)
    statistical_tests(analysis_df)

if __name__ == "__main__":
    main()