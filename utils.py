import pandas as pd
import numpy as np

def calculate_metrics(df):
    """
    Calculate key performance metrics from the production data.
    
    Args:
        df (pd.DataFrame): Production data DataFrame
        
    Returns:
        dict: Dictionary containing calculated metrics
    """
    if df.empty:
        return {
            'avg_target_uph': 0,
            'avg_actual_uph': 0,
            'total_production': 0,
            'overall_achievement_rate': 0,
            'uph_variance': 0,
            'total_defects': 0,
            'defect_rate': 0
        }
    
    # Basic metrics
    avg_target_uph = df['Target_UPH'].mean()
    avg_actual_uph = df['Actual_UPH'].mean()
    total_production = df['Production_Qty'].sum()
    total_defects = df['Defect_Qty'].sum()
    
    # Achievement rate (weighted by production quantity)
    total_target_production = (df['Target_UPH'] * df['Work_Hours']).sum()
    total_actual_production = df['Production_Qty'].sum()
    
    if total_target_production > 0:
        overall_achievement_rate = (total_actual_production / total_target_production) * 100
    else:
        overall_achievement_rate = 0
    
    # UPH variance
    if avg_target_uph > 0:
        uph_variance = ((avg_actual_uph - avg_target_uph) / avg_target_uph) * 100
    else:
        uph_variance = 0
    
    # Defect rate
    if total_production > 0:
        defect_rate = (total_defects / total_production) * 100
    else:
        defect_rate = 0
    
    return {
        'avg_target_uph': avg_target_uph,
        'avg_actual_uph': avg_actual_uph,
        'total_production': total_production,
        'overall_achievement_rate': overall_achievement_rate,
        'uph_variance': uph_variance,
        'total_defects': total_defects,
        'defect_rate': defect_rate
    }

def format_number(number):
    """
    Format large numbers with appropriate suffixes (K, M, B).
    
    Args:
        number (int/float): Number to format
        
    Returns:
        str: Formatted number string
    """
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}B"
    elif number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    elif number >= 1_000:
        return f"{number / 1_000:.1f}K"
    else:
        return f"{int(number)}"

def get_status_color(achievement_rate):
    """
    Get color code based on achievement rate for visual indicators.
    
    Args:
        achievement_rate (float): Achievement rate percentage
        
    Returns:
        str: Color code (green, yellow, red)
    """
    if achievement_rate >= 100:
        return "green"
    elif achievement_rate >= 90:
        return "yellow" 
    else:
        return "red"

def calculate_line_efficiency(df, line_name):
    """
    Calculate efficiency metrics for a specific production line.
    
    Args:
        df (pd.DataFrame): Production data DataFrame
        line_name (str): Name of the production line
        
    Returns:
        dict: Line-specific efficiency metrics
    """
    line_data = df[df['Line_Name'] == line_name]
    
    if line_data.empty:
        return {
            'line_name': line_name,
            'avg_achievement_rate': 0,
            'total_production': 0,
            'avg_defect_rate': 0,
            'efficiency_score': 0
        }
    
    avg_achievement_rate = (line_data['Actual_UPH'] / line_data['Target_UPH']).mean() * 100
    total_production = line_data['Production_Qty'].sum()
    total_defects = line_data['Defect_Qty'].sum()
    
    if total_production > 0:
        avg_defect_rate = (total_defects / total_production) * 100
    else:
        avg_defect_rate = 0
    
    # Efficiency score combines achievement rate and quality
    quality_factor = max(0, (100 - avg_defect_rate) / 100)
    efficiency_score = (avg_achievement_rate / 100) * quality_factor * 100
    
    return {
        'line_name': line_name,
        'avg_achievement_rate': avg_achievement_rate,
        'total_production': total_production,
        'avg_defect_rate': avg_defect_rate,
        'efficiency_score': efficiency_score
    }

def detect_anomalies(df, threshold_achievement=80, threshold_defect_rate=5):
    """
    Detect production anomalies based on configurable thresholds.
    
    Args:
        df (pd.DataFrame): Production data DataFrame
        threshold_achievement (float): Minimum achievement rate threshold (%)
        threshold_defect_rate (float): Maximum defect rate threshold (%)
        
    Returns:
        pd.DataFrame: DataFrame containing anomaly records
    """
    if df.empty:
        return pd.DataFrame()
    
    # Calculate achievement rate and defect rate
    df_copy = df.copy()
    df_copy['Achievement_Rate'] = (df_copy['Actual_UPH'] / df_copy['Target_UPH']) * 100
    df_copy['Defect_Rate'] = (df_copy['Defect_Qty'] / df_copy['Production_Qty']) * 100
    
    # Identify anomalies
    anomaly_conditions = (
        (df_copy['Achievement_Rate'] < threshold_achievement) |
        (df_copy['Defect_Rate'] > threshold_defect_rate)
    )
    
    anomalies = df_copy[anomaly_conditions].copy()
    
    # Add anomaly type
    anomalies['Anomaly_Type'] = ''
    anomalies.loc[anomalies['Achievement_Rate'] < threshold_achievement, 'Anomaly_Type'] += 'Low Achievement '
    anomalies.loc[anomalies['Defect_Rate'] > threshold_defect_rate, 'Anomaly_Type'] += 'High Defect Rate '
    
    return anomalies

def generate_performance_report(df):
    """
    Generate a comprehensive performance report.
    
    Args:
        df (pd.DataFrame): Production data DataFrame
        
    Returns:
        dict: Performance report dictionary
    """
    if df.empty:
        return {'error': 'No data available for report generation'}
    
    # Overall metrics
    overall_metrics = calculate_metrics(df)
    
    # Line-specific metrics
    lines = df['Line_Name'].unique()
    line_metrics = []
    for line in lines:
        line_metric = calculate_line_efficiency(df, line)
        line_metrics.append(line_metric)
    
    # Company-specific metrics
    company_metrics = df.groupby('Company').agg({
        'Production_Qty': 'sum',
        'Defect_Qty': 'sum',
        'Target_UPH': 'mean',
        'Actual_UPH': 'mean'
    }).reset_index()
    
    company_metrics['Achievement_Rate'] = (company_metrics['Actual_UPH'] / company_metrics['Target_UPH']) * 100
    company_metrics['Defect_Rate'] = (company_metrics['Defect_Qty'] / company_metrics['Production_Qty']) * 100
    
    # Top and bottom performers
    line_performance = pd.DataFrame(line_metrics)
    if not line_performance.empty:
        top_performer = line_performance.loc[line_performance['efficiency_score'].idxmax()]
        bottom_performer = line_performance.loc[line_performance['efficiency_score'].idxmin()]
    else:
        top_performer = None
        bottom_performer = None
    
    # Anomaly detection
    anomalies = detect_anomalies(df)
    
    return {
        'overall_metrics': overall_metrics,
        'line_metrics': line_metrics,
        'company_metrics': company_metrics.to_dict('records'),
        'top_performer': top_performer.to_dict() if top_performer is not None else None,
        'bottom_performer': bottom_performer.to_dict() if bottom_performer is not None else None,
        'anomaly_count': len(anomalies),
        'anomalies': anomalies.to_dict('records') if not anomalies.empty else []
    }

def validate_data_quality(df):
    """
    Validate the quality of production data and return quality metrics.
    
    Args:
        df (pd.DataFrame): Production data DataFrame
        
    Returns:
        dict: Data quality metrics and issues
    """
    if df.empty:
        return {
            'quality_score': 0,
            'issues': ['No data available'],
            'recommendations': ['Please check data source configuration']
        }
    
    issues = []
    recommendations = []
    
    # Check for missing values
    missing_critical = df[['Production_Date', 'Line_Name', 'Production_Qty', 'Target_UPH']].isnull().sum()
    if missing_critical.sum() > 0:
        issues.append(f"Missing critical data: {missing_critical.sum()} records")
        recommendations.append("Review data collection processes for completeness")
    
    # Check for data consistency
    negative_production = (df['Production_Qty'] < 0).sum()
    if negative_production > 0:
        issues.append(f"Negative production quantities: {negative_production} records")
        recommendations.append("Validate production quantity data entry")
    
    zero_work_hours = (df['Work_Hours'] <= 0).sum()
    if zero_work_hours > 0:
        issues.append(f"Zero or negative work hours: {zero_work_hours} records")
        recommendations.append("Ensure work hours are properly recorded")
    
    # Check for unrealistic values
    extreme_uph = ((df['Actual_UPH'] > df['Target_UPH'] * 2) | (df['Actual_UPH'] < df['Target_UPH'] * 0.3)).sum()
    if extreme_uph > 0:
        issues.append(f"Extreme UPH values: {extreme_uph} records")
        recommendations.append("Review UPH calculations and data accuracy")
    
    # Calculate quality score
    total_records = len(df)
    issue_records = missing_critical.sum() + negative_production + zero_work_hours + extreme_uph
    quality_score = max(0, (total_records - issue_records) / total_records * 100)
    
    if not issues:
        issues.append("No data quality issues detected")
        recommendations.append("Continue monitoring data quality regularly")
    
    return {
        'quality_score': quality_score,
        'total_records': total_records,
        'issue_records': issue_records,
        'issues': issues,
        'recommendations': recommendations
    }
