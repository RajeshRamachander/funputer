# FunPuter - Intelligent Imputation Analysis

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/funputer.svg)](https://pypi.org/project/funputer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Simple, fast, intelligent recommendations for handling missing data.**

FunPuter analyzes your data and suggests the best imputation methods based on:
- **Missing data mechanisms** (MCAR, MAR, MNAR detection)
- **Data types** and statistical properties  
- **Business rules** and column dependencies
- **Adaptive thresholds** based on your dataset characteristics

## 🚀 Quick Start

### Installation
```bash
pip install funputer
```

### Basic Usage

**Python API (Recommended)**
```python
import funimpute

# Analyze your dataset
suggestions = funimpute.analyze_imputation_requirements(
    metadata_path="metadata.csv",
    data_path="data.csv"
)

# Use the suggestions
for suggestion in suggestions:
    print(f"{suggestion.column_name}: {suggestion.proposed_method}")
    print(f"  Rationale: {suggestion.rationale}")
    print(f"  Confidence: {suggestion.confidence_score:.3f}")
```

**Command Line**
```bash
# Analyze and save results
funputer -m metadata.csv -d data.csv -o suggestions.csv

# View results
funputer -m metadata.csv -d data.csv --verbose
```

## 📋 Metadata Format

### CSV Format (Simple)

Create a CSV with your column information:

```csv
column_name,data_type,min_value,max_value,unique_flag,dependent_column,business_rule,description
user_id,integer,1,999999,TRUE,,,User identifier
age,integer,0,120,FALSE,,Must be positive,User age
income,float,0,,FALSE,age,Higher with age,Annual income
category,categorical,,,FALSE,,,User category A/B/C
```

### JSON Format (Enterprise)

For more complex metadata with business rules and governance:

```json
{
  "columns": [
    {
      "name": "user_id",
      "data_type": "integer",
      "unique": true,
      "constraints": {
        "min_value": 1,
        "max_value": 999999
      },
      "description": "User identifier"
    },
    {
      "name": "age",
      "data_type": "integer",
      "constraints": {
        "min_value": 0,
        "max_value": 120
      },
      "business_rules": [
        {
          "description": "Must be positive",
          "expression": "age > 0"
        }
      ]
    },
    {
      "name": "income",
      "data_type": "float",
      "constraints": {
        "min_value": 0
      },
      "relationships": {
        "dependent_columns": ["age"]
      },
      "business_rules": [
        {
          "description": "Higher with age",
          "expression": "income correlation with age"
        }
      ]
    },
    {
      "name": "category",
      "data_type": "categorical",
      "constraints": {
        "allowed_values": ["A", "B", "C"]
      }
    }
  ]
}
```

**Required fields:**
- `name`: Column name in your data
- `data_type`: One of `integer`, `float`, `string`, `categorical`, `datetime`, `boolean`

**Optional fields:**
- `constraints`: Value ranges, allowed values, patterns
- `unique`: Set to `true` for ID columns
- `relationships`: Dependencies between columns
- `business_rules`: Domain-specific validation rules
- `description`: Human-readable description

## 🏗️ Client Application Integration

### Direct DataFrame Analysis
```python
import pandas as pd
import funimpute
from funimpute import ColumnMetadata

# Your data
data = pd.DataFrame({
    'age': [25, None, 35, 42, None],
    'income': [50000, 60000, None, 80000, 45000],
    'category': ['A', 'B', None, 'A', 'C']
})

# Define metadata programmatically
metadata = [
    ColumnMetadata('age', 'integer', min_value=0, max_value=120),
    ColumnMetadata('income', 'float', dependent_column='age', business_rule='Higher with age'),
    ColumnMetadata('category', 'categorical')
]

# Get suggestions
suggestions = funimpute.analyze_dataframe(data, metadata)

# Apply suggestions (your implementation)
for s in suggestions:
    if s.proposed_method == "Median":
        data[s.column_name].fillna(data[s.column_name].median(), inplace=True)
    elif s.proposed_method == "Mode":
        data[s.column_name].fillna(data[s.column_name].mode().iloc[0], inplace=True)
    # ... implement other methods as needed
```

## ⚙️ Configuration Options

### Python API Configuration
```python
from funimpute import AnalysisConfig

# Custom analysis settings
config = AnalysisConfig(
    iqr_multiplier=2.0,                    # Outlier detection sensitivity (default: 1.5)
    correlation_threshold=0.4,             # Relationship detection threshold (default: 0.3)
    skewness_threshold=1.5,                # Mean vs median decision point (default: 2.0)
    missing_percentage_threshold=0.8,      # Max missing % before flagging (default: 0.5)
    outlier_percentage_threshold=0.1       # Max outlier % before flagging (default: 0.05)
)

suggestions = funimpute.analyze_imputation_requirements(
    "metadata.csv", "data.csv", config=config
)
```

### YAML Configuration File
Create a `config.yml` file:

```yaml
# Analysis thresholds
iqr_multiplier: 2.0
correlation_threshold: 0.4
skewness_threshold: 1.5
missing_percentage_threshold: 0.8
outlier_percentage_threshold: 0.1

# Chi-square test parameters
chi_square_alpha: 0.05
point_biserial_threshold: 0.2

# Output settings
output_path: "custom_suggestions.csv"
```

Use with CLI:
```bash
funputer -m metadata.csv -d data.csv -c config.yml
```

### Configuration Parameters Explained

**Outlier Detection:**
- `iqr_multiplier`: Higher = less sensitive to outliers (1.5 = strict, 3.0 = lenient)
- `outlier_percentage_threshold`: Flag columns with more than X% outliers

**Missing Data Analysis:**  
- `correlation_threshold`: Minimum correlation to detect relationships
- `missing_percentage_threshold`: Flag columns with more than X% missing
- `chi_square_alpha`: P-value threshold for statistical tests

**Imputation Method Selection:**
- `skewness_threshold`: When to prefer median over mean (higher = more mean)

## 📊 What You Get

Each suggestion includes:

```python
suggestion.column_name          # 'age'
suggestion.proposed_method      # 'Median'
suggestion.rationale           # 'Numeric data with MCAR mechanism...'
suggestion.confidence_score    # 0.847
suggestion.missing_count       # 15
suggestion.missing_percentage  # 0.075 (7.5%)
```

**Available Methods:**
- `Mean`, `Median`, `Mode` - Statistical imputation
- `Regression`, `kNN` - Predictive imputation  
- `Business Rule` - Domain-specific logic
- `Forward Fill`, `Backward Fill` - Temporal imputation
- `Manual Backfill` - Requires human intervention
- `No action needed` - No missing values

## ✨ Key Features

✅ **Intelligent Analysis** - Detects missing data mechanisms automatically  
✅ **Business Rule Integration** - Uses your domain knowledge  
✅ **Adaptive Thresholds** - Adjusts based on your data characteristics  
✅ **High Performance** - Analyzes 100+ columns in seconds  
✅ **Simple API** - Easy integration with existing workflows  
✅ **Type Safe** - Full type hints and validation  

## 🔧 Real-World Example

```python
# Your existing data pipeline
import pandas as pd
import funimpute

def process_customer_data(df):
    # 1. Define your metadata once
    metadata = [
        funimpute.ColumnMetadata('customer_id', 'integer', unique_flag=True),
        funimpute.ColumnMetadata('age', 'integer', min_value=18, max_value=100),
        funimpute.ColumnMetadata('income', 'float', dependent_column='age'),
        funimpute.ColumnMetadata('segment', 'categorical'),
    ]
    
    # 2. Get intelligent suggestions
    suggestions = funimpute.analyze_dataframe(df, metadata)
    
    # 3. Apply high-confidence suggestions automatically
    for s in suggestions:
        if s.confidence_score > 0.8:
            if s.proposed_method == "Median":
                df[s.column_name].fillna(df[s.column_name].median(), inplace=True)
            elif s.proposed_method == "Mode":
                df[s.column_name].fillna(df[s.column_name].mode().iloc[0], inplace=True)
        else:
            print(f"Manual review needed for {s.column_name}: {s.rationale}")
    
    return df
```

## 📦 Installation & Optional Features

### Basic Installation
```bash
pip install funputer
```

### With Optional Monitoring (Prometheus)
```bash
pip install funputer[monitoring]
```

Then enable monitoring in your code:
```python
from funimpute.metrics import start_metrics_server

# Start Prometheus metrics server on port 8001
start_metrics_server(8001)

# Your analysis code here...
# Metrics will be available at http://localhost:8001/metrics
```

### Development Installation
```bash
git clone https://github.com/RajeshRamachander/funputer
cd funputer
pip install -r requirements.txt
```

**Requirements**: Python 3.9+, pandas, numpy, scipy

## 📄 License

MIT License - Use freely in commercial and open-source projects.

## 🤝 Support

- 🐛 Issues: [GitHub Issues](https://github.com/RajeshRamachander/funputer/issues)
- 📖 Documentation: [GitHub Repository](https://github.com/RajeshRamachander/funputer)

---

**Focus**: Get intelligent imputation recommendations, not complex infrastructure.  
**Philosophy**: Simple tools that scale with your needs.