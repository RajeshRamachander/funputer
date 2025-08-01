"""
Outlier detection and handling strategies.
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
from scipy import stats

from .models import OutlierAnalysis, OutlierHandling, ColumnMetadata, AnalysisConfig


def detect_outliers_iqr(
    series: pd.Series, 
    iqr_multiplier: float = 1.5
) -> Tuple[List[float], float, float]:
    """
    Detect outliers using IQR method.
    
    Args:
        series: Pandas series to analyze
        iqr_multiplier: Multiplier for IQR calculation
        
    Returns:
        Tuple of (outlier_values, lower_bound, upper_bound)
    """
    # Remove NaN values for calculation
    clean_series = series.dropna()
    
    if len(clean_series) == 0:
        return [], np.nan, np.nan
    
    # Calculate quartiles and IQR
    q1 = clean_series.quantile(0.25)
    q3 = clean_series.quantile(0.75)
    iqr = q3 - q1
    
    # Calculate bounds
    lower_bound = q1 - iqr_multiplier * iqr
    upper_bound = q3 + iqr_multiplier * iqr
    
    # Find outliers
    outliers = clean_series[(clean_series < lower_bound) | (clean_series > upper_bound)]
    
    return outliers.tolist(), lower_bound, upper_bound


def detect_outliers_zscore(
    series: pd.Series, 
    threshold: float = 3.0
) -> List[float]:
    """
    Detect outliers using Z-score method.
    
    Args:
        series: Pandas series to analyze
        threshold: Z-score threshold for outlier detection
        
    Returns:
        List of outlier values
    """
    clean_series = series.dropna()
    
    if len(clean_series) == 0:
        return []
    
    z_scores = np.abs(stats.zscore(clean_series))
    outliers = clean_series[z_scores > threshold]
    
    return outliers.tolist()


def suggest_outlier_handling(
    outlier_analysis: dict,
    metadata: ColumnMetadata,
    config: AnalysisConfig
) -> Tuple[OutlierHandling, str]:
    """
    Suggest outlier handling strategy based on analysis and metadata.
    
    Args:
        outlier_analysis: Dictionary with outlier analysis results
        metadata: Column metadata
        config: Analysis configuration
        
    Returns:
        Tuple of (handling_strategy, rationale)
    """
    outlier_count = outlier_analysis['outlier_count']
    outlier_percentage = outlier_analysis['outlier_percentage']
    
    # No outliers detected
    if outlier_count == 0:
        return OutlierHandling.LEAVE_AS_IS, "No outliers detected"
    
    # High percentage of outliers - likely data quality issue
    if outlier_percentage > 0.2:  # More than 20% are outliers
        return (
            OutlierHandling.LEAVE_AS_IS,
            f"High outlier percentage ({outlier_percentage:.1%}) suggests "
            "potential data distribution issue - investigate before handling"
        )
    
    # Unique identifier columns - never modify
    if metadata.unique_flag:
        return (
            OutlierHandling.LEAVE_AS_IS,
            "Unique identifier column - outliers should not be modified"
        )
    
    # Categorical data - leave as is
    if metadata.data_type == 'categorical':
        return (
            OutlierHandling.LEAVE_AS_IS,
            "Categorical data - outliers represent valid categories"
        )
    
    # Has business bounds defined
    if metadata.min_value is not None or metadata.max_value is not None:
        # Check if outliers violate business rules
        lower_bound = outlier_analysis.get('lower_bound')
        upper_bound = outlier_analysis.get('upper_bound')
        
        violates_business_rules = False
        if metadata.min_value is not None and lower_bound < metadata.min_value:
            violates_business_rules = True
        if metadata.max_value is not None and upper_bound > metadata.max_value:
            violates_business_rules = True
            
        if violates_business_rules:
            return (
                OutlierHandling.CAP_TO_BOUNDS,
                f"Outliers violate business rules (min: {metadata.min_value}, "
                f"max: {metadata.max_value}) - cap to valid range"
            )
    
    # Low percentage of outliers
    if outlier_percentage < config.outlier_threshold:
        if metadata.data_type in ['integer', 'float']:
            return (
                OutlierHandling.CAP_TO_BOUNDS,
                f"Low outlier percentage ({outlier_percentage:.1%}) - "
                "cap to statistical bounds to preserve data distribution"
            )
    
    # Medium percentage of outliers
    if outlier_percentage < 0.1:  # Less than 10%
        return (
            OutlierHandling.CONVERT_TO_NAN,
            f"Medium outlier percentage ({outlier_percentage:.1%}) - "
            "convert to NaN for imputation to avoid bias"
        )
    
    # Default case
    return (
        OutlierHandling.LEAVE_AS_IS,
        f"Outlier percentage ({outlier_percentage:.1%}) requires manual review"
    )


def analyze_outliers(
    series: pd.Series,
    metadata: ColumnMetadata,
    config: AnalysisConfig
) -> OutlierAnalysis:
    """
    Perform comprehensive outlier analysis for a column.
    
    Args:
        series: Pandas series to analyze
        metadata: Column metadata
        config: Analysis configuration
        
    Returns:
        OutlierAnalysis object with results and recommendations
    """
    # Skip outlier detection for non-numeric data types
    if metadata.data_type not in ['integer', 'float']:
        return OutlierAnalysis(
            outlier_count=0,
            outlier_percentage=0.0,
            lower_bound=None,
            upper_bound=None,
            outlier_values=[],
            handling_strategy=OutlierHandling.LEAVE_AS_IS,
            rationale=f"Non-numeric data type ({metadata.data_type}) - no outlier detection"
        )
    
    # Detect outliers using IQR method
    outlier_values, lower_bound, upper_bound = detect_outliers_iqr(
        series, config.iqr_multiplier
    )
    
    outlier_count = len(outlier_values)
    total_non_null = series.count()
    outlier_percentage = outlier_count / total_non_null if total_non_null > 0 else 0.0
    
    # Prepare analysis results for strategy suggestion
    outlier_analysis_dict = {
        'outlier_count': outlier_count,
        'outlier_percentage': outlier_percentage,
        'lower_bound': lower_bound,
        'upper_bound': upper_bound
    }
    
    # Get handling strategy suggestion
    handling_strategy, rationale = suggest_outlier_handling(
        outlier_analysis_dict, metadata, config
    )
    
    return OutlierAnalysis(
        outlier_count=outlier_count,
        outlier_percentage=outlier_percentage,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        outlier_values=outlier_values[:10],  # Limit to first 10 for storage
        handling_strategy=handling_strategy,
        rationale=rationale
    )
