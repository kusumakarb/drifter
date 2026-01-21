# DriftWatch Architecture

## System Overview

DriftWatch is built on **Great Expectations 1.x** using its class-based API and file-based context for persistent state management.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DRIFTWATCH FRAMEWORK                             │
│                                                                       │
│  Built on Great Expectations 1.x - Class-Based API                   │
└─────────────────────────────────────────────────────────────────────┘

                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
            ┌───────▼────────┐         ┌────────▼───────┐
            │   CLI Entry    │         │  Python API    │
            │ (cli.py)       │         │    Entry       │
            └───────┬────────┘         └────────┬───────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │   DriftWatch Core         │
                    │  ┌──────────────────────┐ │
                    │  │ DriftWatchConfig     │ │
                    │  │ (config.py)          │ │
                    │  └──────────┬───────────┘ │
                    │             │             │
                    │  ┌──────────▼───────────┐ │
                    │  │ DriftWatchGXContext  │ │
                    │  │ (gx_context.py)      │ │
                    │  └──────────┬───────────┘ │
                    │             │             │
                    │  ┌──────────▼───────────┐ │
                    │  │ ExpectationSuite     │ │
                    │  │ Builder              │ │
                    │  │ (expectation_suite_  │ │
                    │  │  builder.py)         │ │
                    │  └──────────────────────┘ │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │  Great Expectations 1.x   │
                    │                           │
                    │  Built-in Expectations:   │
                    │  • ExpectColumnToExist    │
                    │  • ExpectColumnMean...    │
                    │  • ExpectColumnStdev...   │
                    │                           │
                    │  Custom Expectations:     │
                    │  • GPS Precision          │
                    │  • Categorical PSI        │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │   GX Validation Engine    │
                    │                           │
                    │  • Runs expectations      │
                    │  • Stores results         │
                    │  • Generates Data Docs    │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │      Output Layer         │
                    │                           │
                    │  • Expectation Suites     │
                    │    (gx/expectations/)     │
                    │  • Validation Results     │
                    │    (gx/uncommitted/       │
                    │     validations/)         │
                    │  • Data Docs (HTML)       │
                    │    (gx/uncommitted/       │
                    │     data_docs/)           │
                    └───────────────────────────┘
```

---

## Component Details

### 1. Entry Points

#### CLI (driftwatch/cli.py)

**Purpose:** Command-line interface for profiling and evaluation

**Commands:**
- `profile` - Build GX expectation suite from reference data
- `evaluate` - Validate new data against expectation suite

**Example:**
```bash
# Profile reference data (one-time setup)
python -m driftwatch.cli profile \
  --reference data/ref.csv \
  --config driftwatch_config.yaml

# Evaluate new data (no config needed - suite is self-contained)
python -m driftwatch.cli evaluate \
  --new data/new.csv
```

**Key Design:**
- `profile`: Requires config to build suite with correct thresholds
- `evaluate`: No config needed - loads suite from `gx/expectations/`
- Suite stores all configurations (thresholds, column groups, etc.)

#### Python API

**Purpose:** Programmatic access for integration

**Example:**
```python
from driftwatch.core.config import DriftWatchConfig
from driftwatch.core.gx_context import DriftWatchGXContext
from driftwatch.core.expectation_suite_builder import ExpectationSuiteBuilder
import pandas as pd

# Load config and data
config = DriftWatchConfig('driftwatch_config.yaml')
ref_df = pd.read_csv('data/ref.csv')

# Build GX suite
context_manager = DriftWatchGXContext()
context = context_manager.get_context()
builder = ExpectationSuiteBuilder()

suite = builder.build_from_reference_data(
    context=context,
    ref_df=ref_df,
    config=config,
    suite_name="my_suite"
)

# Validate new data
new_df = pd.read_csv('data/new.csv')
validator = context.get_validator(
    batch_request=batch_request,
    expectation_suite_name="my_suite"
)
results = validator.validate()
```

---

### 2. Core Components

#### DriftWatchConfig (driftwatch/core/config.py)

**Purpose:** YAML configuration loader and accessor

**Responsibilities:**
- Load and parse `driftwatch_config.yaml`
- Provide column group definitions
- Provide detector configuration
- Provide threshold values

**Key Methods:**
```python
def __init__(self, config_path: str)
def get_column_group(self, group_name: str) -> List[str]
def is_detector_enabled(self, detector_name: str) -> bool
def get_detector_config(self, detector_name: str) -> Dict
```

**Example Configuration:**
```yaml
# Simplified direct expectation configuration
expectations:
  - column: Time_taken(min)
    expectation: ExpectColumnStdevToBeBetween
    values:
      min_value: 8.5
      max_value: 11.5

  - column: Restaurant_latitude
    expectation: ExpectColumnValuesToHaveDecimalPrecision
    values:
      precision: 6
      mostly: 0.95
```

---

#### DriftWatchGXContext (driftwatch/core/gx_context.py)

**Purpose:** Persistent GX file context manager

**Responsibilities:**
- Initialize GX file context in `gx/` directory
- Provide access to GX context for suite building and validation
- Manage GX state (suites, data sources, validations)

**Key Features:**
- **Persistent Storage**: All GX state stored in `gx/` directory
- **Singleton Pattern**: Single context instance per run
- **Auto-Initialization**: Creates `gx/` directory if not exists

**Key Methods:**
```python
def get_context(self) -> gx.DataContext
```

**Directory Structure:**
```
gx/
├── expectations/
│   └── driftwatch_reference_suite.json
├── uncommitted/
│   ├── validations/
│   │   └── drift_eval_20260118_120000/
│   │       └── validation_result.json
│   └── data_docs/
│       └── local_site/
│           └── index.html
└── great_expectations.yml
```

---

#### ExpectationSuiteBuilder (driftwatch/core/expectation_suite_builder.py)

**Purpose:** Build GX expectation suites from reference data + configuration

**Responsibilities:**
- Read reference data statistics
- Map config to GX expectations
- Instantiate expectations using GX 1.x class-based API
- Build and save expectation suite

**Key Method:**
```python
def build_from_reference_data(
    context: gx.DataContext,
    ref_df: pd.DataFrame,
    config: DriftWatchConfig,
    suite_name: str
) -> gx.ExpectationSuite
```

**Expectations Generated:**

1. **Schema Expectations** (always):
   ```python
   suite.add_expectation(
       ExpectColumnToExist(column=col)
   )
   ```

2. **Statistical Expectations** (from config):
   ```python
   # Delivery ratings quality
   suite.add_expectation(
       ExpectColumnMeanToBeBetween(
           column="Delivery_person_Ratings",
           min_value=3.5,
           max_value=5.0
       )
   )

   # Delivery time consistency
   suite.add_expectation(
       ExpectColumnStdevToBeBetween(
           column="Time_taken(min)",
           min_value=8.5,
           max_value=11.5
       )
   )
   ```

3. **GPS Precision Expectations** (custom, representative check):
   ```python
   suite.add_expectation(
       ExpectColumnValuesToHaveDecimalPrecision(
           column="Restaurant_latitude",
           precision=6,
           mostly=0.95
       )
   )
   ```

4. **Categorical Distribution Expectations** (custom):
   ```python
   suite.add_expectation(
       ExpectColumnCategoriesToMatchDistribution(
           column=col,
           reference_distribution=ref_dist,
           psi_threshold=0.25
       )
   )
   ```

---

#### ValidationResultEnricher (driftwatch/core/validation_result_enricher.py)

**Purpose:** Add DriftWatch-specific metadata to GX validation results

**Responsibilities:**
- Calculate overall severity (CRITICAL, MAJOR, MINOR, CLEAN)
- Add DriftWatch metadata to validation results
- Provide summary statistics

**Key Methods:**
```python
def enrich_result(
    validation_result: gx.ValidationResult,
    config_file: str,
    duration_seconds: float
) -> gx.ValidationResult

def get_enriched_metadata(
    validation_result: gx.ValidationResult
) -> Dict[str, Any]
```

**Enriched Metadata:**
```python
{
    'severity': 'CRITICAL',
    'driftwatch': {
        'config_file': 'driftwatch_config.yaml',
        'duration_seconds': 1.23,
        'total_drifts': 6
    }
}
```

---

### 3. Custom Expectations

DriftWatch implements two custom GX 1.x expectations for specialized drift detection.

#### ExpectColumnValuesToHaveDecimalPrecision

**File:** `driftwatch/expectations/expect_column_values_to_have_decimal_precision.py`

**Purpose:** Detect GPS coordinate precision loss

**Implementation:**
```python
class ColumnDecimalPrecision(ColumnAggregateMetricProvider):
    """Metric: Calculate average decimal precision."""
    condition_metric_name = "column.decimal_precision"
    value_keys = ("precision",)

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column, precision, **kwargs):
        # Calculate decimal places for each value
        decimal_places = column.apply(lambda x: ...)
        avg_precision = decimal_places.mean()
        return float(avg_precision)

class ExpectColumnValuesToHaveDecimalPrecision(ColumnAggregateExpectation):
    """Expectation: Values should have specified decimal precision."""
    metric_dependencies = ("column.decimal_precision",)
    precision: int = pydantic.Field(...)
    mostly: float = pydantic.Field(default=1.0)

    def _validate(self, metrics):
        return {
            "success": metrics["column.decimal_precision"] >= self.precision
        }
```

**Usage:**
```python
suite.add_expectation(
    ExpectColumnValuesToHaveDecimalPrecision(
        column="Restaurant_latitude",
        precision=6,
        mostly=0.95  # 95% of values must meet precision
    )
)
```

---

#### ExpectColumnCategoriesToMatchDistribution

**File:** `driftwatch/expectations/expect_column_categories_to_match_distribution.py`

**Purpose:** Detect categorical distribution drift using PSI

**Implementation:**
```python
class ColumnCategoricalDistributionPSI(ColumnAggregateMetricProvider):
    """Metric: Calculate Population Stability Index."""
    condition_metric_name = "column.categorical_distribution_psi"
    value_keys = ("reference_distribution",)

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column, reference_distribution, **kwargs):
        # Calculate observed proportions
        observed_dist = column.value_counts(normalize=True).to_dict()

        # Calculate PSI
        psi = 0.0
        for category in all_categories:
            ref_p = reference_distribution.get(category, 0.0001)
            obs_p = observed_dist.get(category, 0.0001)
            psi += (obs_p - ref_p) * np.log(obs_p / ref_p)

        return float(psi)

class ExpectColumnCategoriesToMatchDistribution(ColumnAggregateExpectation):
    """Expectation: Distribution should match reference using PSI."""
    metric_dependencies = ("column.categorical_distribution_psi",)
    reference_distribution: Dict[str, float] = pydantic.Field(...)
    psi_threshold: float = pydantic.Field(default=0.25)

    def _validate(self, metrics):
        return {
            "success": metrics["column.categorical_distribution_psi"] < self.psi_threshold
        }
```

**Usage:**
```python
suite.add_expectation(
    ExpectColumnCategoriesToMatchDistribution(
        column="Road_traffic_density",
        reference_distribution={
            "Jam": 0.314,
            "Low": 0.344,
            "Medium": 0.243,
            "High": 0.098
        },
        psi_threshold=0.25
    )
)
```

---

## Data Flow

### Profile Command (One-Time)

```
1. Load Configuration
   ├─> DriftWatchConfig('driftwatch_config.yaml')
   └─> Get column groups, detector settings

2. Load Reference Data
   ├─> pd.read_csv('data/reference.csv')
   └─> Calculate statistics (mean, std, precision, distributions)

3. Build Expectation Suite
   ├─> Create GX context (DriftWatchGXContext)
   ├─> Instantiate ExpectationSuiteBuilder
   └─> Generate expectations:
       ├─> Schema: ExpectColumnToExist (all columns)
       ├─> Stats: ExpectColumnMeanToBeBetween, etc. (numerical)
       ├─> GPS: ExpectColumnValuesToHaveDecimalPrecision (GPS columns)
       └─> Categorical: ExpectColumnCategoriesToMatchDistribution (categorical)

4. Save Suite
   └─> gx/expectations/driftwatch_reference_suite.json (~10KB)
```

### Evaluate Command (Repeated)

```
1. Load Configuration
   └─> DriftWatchConfig('driftwatch_config.yaml')

2. Load GX Context & Suite
   ├─> DriftWatchGXContext().get_context()
   └─> context.suites.get('driftwatch_reference_suite')

3. Load New Data
   └─> pd.read_csv('data/new.csv')

4. Create Validator
   ├─> Create pandas datasource
   ├─> Add dataframe asset
   ├─> Build batch request
   └─> Get validator with suite

5. Run Validation
   ├─> validator.validate()
   └─> GX runs all 61 expectations

6. Enrich Results
   ├─> ValidationResultEnricher.enrich_result()
   └─> Add severity, metadata

7. Store Results
   ├─> GX stores validation result
   │   └─> gx/uncommitted/validations/drift_eval_*/
   └─> GX builds Data Docs
       └─> gx/uncommitted/data_docs/local_site/
```

---

## Design Decisions

### Why GX 1.x Class-Based API?

**Correct Pattern (GX 1.x):**
```python
suite = gx.ExpectationSuite(name="my_suite")
suite.add_expectation(
    ExpectColumnToExist(column="age")
)
context.suites.add(suite)
```

**Deprecated Pattern (GX 0.x):**
```python
validator = context.get_validator(
    batch_request=batch_request,
    create_expectation_suite_with_name="my_suite"
)
validator.expect_column_to_exist(column="age")
```

**Why GX 1.x is Better:**
- ✅ Type-safe (IDE autocomplete, type checking)
- ✅ Official pattern in GX 1.x documentation
- ✅ Clear separation: suite building vs validation
- ✅ Future-proof (0.x pattern being deprecated)

---

### Why File Context over Ephemeral Context?

**File Context (Production):**
```python
context = gx.get_context(mode="file")
# State stored in gx/ directory
# Suites persist across runs
# Validation history maintained
```

**Ephemeral Context (Legacy):**
```python
context = gx.get_context(mode="ephemeral")
# State lost after run
# No persistence
```

**Benefits:**
- ✅ Persistent state across runs
- ✅ Validation history tracking
- ✅ Data Docs generation
- ✅ Audit trail

---

### Why Custom Expectations?

Built-in GX expectations don't cover:
1. **GPS Decimal Precision**: No built-in way to check decimal places
2. **Population Stability Index**: Industry-standard categorical drift metric

Custom expectations:
- ✅ Fill gaps in GX built-ins
- ✅ Follow GX 1.x patterns (`ColumnAggregateExpectation`)
- ✅ Integrate seamlessly with GX ecosystem
- ✅ Appear in Data Docs alongside built-ins

---

## Performance

```
Profile Generation (one-time):
  45,584 rows × 20 columns → ~3 seconds
  Output: ~10KB expectation suite JSON

Drift Evaluation (repeated):
  ~25 expectations × 45,584 rows → ~1-2 seconds total

  Breakdown:
    - Schema expectations (20):      ~200ms
    - Statistical expectations (2):  ~100ms
    - GPS precision (1):             ~80ms
    - Categorical (2):               ~120ms
    - GX validation overhead:        ~200ms
```

---

## Extensibility

### Adding a Custom Expectation

```python
# File: driftwatch/expectations/expect_column_values_to_be_outlier_free.py

from great_expectations.expectations import ColumnAggregateExpectation
from great_expectations.expectations.metrics import (
    ColumnAggregateMetricProvider,
    column_aggregate_value
)
from great_expectations.execution_engine import PandasExecutionEngine
import pydantic

class ColumnOutlierRate(ColumnAggregateMetricProvider):
    """Metric: Calculate outlier rate."""
    condition_metric_name = "column.outlier_rate"
    value_keys = ()

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column, **kwargs):
        q1 = column.quantile(0.25)
        q3 = column.quantile(0.75)
        iqr = q3 - q1
        outliers = ((column < q1 - 1.5*iqr) | (column > q3 + 1.5*iqr)).sum()
        return float(outliers / len(column))

class ExpectColumnValuesToBeOutlierFree(ColumnAggregateExpectation):
    """Expectation: Outlier rate should be below threshold."""
    metric_dependencies = ("column.outlier_rate",)
    outlier_threshold: float = pydantic.Field(default=0.05)

    def _validate(self, metrics):
        return {
            "success": metrics["column.outlier_rate"] < self.outlier_threshold,
            "result": {
                "observed_value": metrics["column.outlier_rate"]
            }
        }
```

**Usage in ExpectationSuiteBuilder:**
```python
from driftwatch.expectations import ExpectColumnValuesToBeOutlierFree

suite.add_expectation(
    ExpectColumnValuesToBeOutlierFree(
        column="Delivery_person_Age",
        outlier_threshold=0.05
    )
)
```

---

## Summary

**DriftWatch Architecture:**
- ✅ Built on **Great Expectations 1.x** class-based API
- ✅ Uses **persistent file context** for state management
- ✅ Provides **ExpectationSuiteBuilder** for config-driven suite creation
- ✅ Implements **custom expectations** for GPS and categorical drift
- ✅ Leverages **GX validation engine** and **Data Docs**
- ✅ Stores **complete audit trail** in GX validation results
- ✅ **Extensible** through custom expectation pattern

**Key Files:**
- `driftwatch/cli.py` - CLI entry point
- `driftwatch/core/expectation_suite_builder.py` - Suite builder
- `driftwatch/core/gx_context.py` - GX context manager
- `driftwatch/expectations/expect_column_values_to_have_decimal_precision.py`
- `driftwatch/expectations/expect_column_categories_to_match_distribution.py`
