# DriftWatch - Automated Data Drift Detection Framework

**Version:** 0.1.0
**Author:** Kusumakar

A production-ready Python framework for detecting data drift using **Great Expectations 1.x**. Built for ML pipelines, data quality monitoring, and ensuring data consistency over time.

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Drift Detection Types](#drift-detection-types)
5. [Statistical Methods & Justification](#statistical-methods--justification)
6. [Configuration](#configuration)
7. [Usage Examples](#usage-examples)
8. [Design Decisions](#design-decisions)
9. [Extending the Framework](#extending-the-framework)
10. [Sample Data](#sample-data)
11. [Test Cases](#test-cases)
12. [Project Structure](#project-structure)

---

## Installation

### Prerequisites

- Python 3.12+
- `uv` package manager (recommended) or `pip`

### Step 1: Create Virtual Environment

```bash
# Create a virtual environment (use python3 on Linux/Mac)
python3 -m venv venv

# Activate the virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows (use 'python' instead of 'python3'):
# python -m venv venv
venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install great-expectations pandas pyyaml
```

---

## Quick Start

### Step 1: Profile Reference Dataset

```bash
python -m driftwatch.cli profile \
    --reference data/reference/reference_data.csv \
    --config driftwatch_config.yaml
```

**Output:**
```
======================================================================
DRIFTWATCH - EXPECTATION SUITE GENERATION (GX)
======================================================================
✓ Configuration loaded from: driftwatch_config.yaml

✓ Loading reference dataset: data/reference/reference_data.csv
  Loaded 45,584 rows, 20 columns

✓ Building GX expectation suite...

✓ Suite saved: gx/expectations/driftwatch_reference_suite.json
  Total expectations: 61
  - Schema expectations (column existence): 20
  - Statistical expectations: 36
  - Custom expectations: 5

======================================================================
✓ EXPECTATION SUITE GENERATION COMPLETE
======================================================================
```

### Step 2: Evaluate New Dataset

```bash
python -m driftwatch.cli evaluate \
    --new data/new/january_batch.csv
```

**Output:**
```
======================================================================
DRIFTWATCH - DRIFT EVALUATION (GX)
======================================================================
✓ Loading GX expectation suite...
  Suite: driftwatch_reference_suite
  Expectations: 61

✓ Loading new dataset: january_batch.csv
  Loaded 45,584 rows, 20 columns

✓ Running GX validation...

✓ Validation complete - 5 drift(s) detected
  Severity: CRITICAL
  Run name: drift_eval_20260118_224707

✓ Data Docs generated:
  Location: gx/uncommitted/data_docs/local_site/
  Index: gx/uncommitted/data_docs/local_site/index.html

✓ Validation metadata:
  Run ID: drift_eval_20260118_224707
  Storage: gx/uncommitted/validations/

  Failed expectations (5):
    - expect_column_values_to_have_decimal_precision (column: Restaurant_latitude)
    - expect_column_values_to_have_decimal_precision (column: Restaurant_longitude)
    - expect_column_values_to_have_decimal_precision (column: Delivery_location_latitude)
    - expect_column_values_to_have_decimal_precision (column: Delivery_location_longitude)
    - expect_column_categories_to_match_distribution (column: Road_traffic_density)

✓ Validation results saved to: gx/uncommitted/validations/
  (GX stores complete validation history with metadata)

======================================================================
✓ EVALUATION COMPLETE
======================================================================
  Severity: CRITICAL
  Drifts: 5
  Duration: 0.74s
======================================================================
```

### Step 3: View Results

**Data Docs (GX HTML Reports):**
```bash
open gx/uncommitted/data_docs/local_site/index.html
```

**Validation Results (JSON):**
```bash
# View latest validation result
ls -t gx/uncommitted/validations/ | head -1
```

---

## Docker Usage

DriftWatch can be easily run using Docker, eliminating the need for local Python 3.12 installation. The Docker image includes all dependencies and sample data for quick testing.

### Quick Start with Docker

#### 1. Build the Image

```bash
docker build -t driftwatch .
```

#### 2. Test with Built-In Sample Data

```bash
# Create output directory
mkdir -p docker-outputs

# Profile reference data
docker run --rm \
  -v $(pwd)/docker-outputs:/app/gx/uncommitted \
  driftwatch profile \
    --reference data/reference/reference_data.csv \
    --config driftwatch_config.yaml

# Evaluate drifted data
docker run --rm \
  -v $(pwd)/docker-outputs:/app/gx/uncommitted \
  driftwatch evaluate \
    --new data/drifted/new_data_with_drift.csv

# View HTML reports
# Linux:
xdg-open docker-outputs/data_docs/local_site/index.html

# macOS:
open docker-outputs/data_docs/local_site/index.html

# Windows:
start docker-outputs\data_docs\local_site\index.html
```

#### 3. Use with Your Own Data

```bash
# Profile your reference dataset
docker run --rm \
  -v /path/to/your/data.csv:/app/user_data/data.csv:ro \
  -v /path/to/your/config.yaml:/app/user_config.yaml:ro \
  -v $(pwd)/docker-outputs:/app/gx/uncommitted \
  driftwatch profile \
    --reference /app/user_data/data.csv \
    --config /app/user_config.yaml

# Evaluate new data
docker run --rm \
  -v /path/to/your/new_data.csv:/app/user_data/new_data.csv:ro \
  -v $(pwd)/docker-outputs:/app/gx/uncommitted \
  driftwatch evaluate \
    --new /app/user_data/new_data.csv
```

### Using Docker Compose

Docker Compose simplifies command execution with pre-configured volume mounts.

#### 1. Profile and Evaluate with Built-In Data

```bash
# Profile with sample data
docker-compose run --rm driftwatch profile \
  --reference data/reference/reference_data.csv \
  --config driftwatch_config.yaml

# Evaluate with sample data
docker-compose run --rm driftwatch evaluate \
  --new data/drifted/new_data_with_drift.csv
```

#### 2. Use with Your Own Data

**Option A**: Edit `docker-compose.yml` volumes section:
```yaml
volumes:
  - /your/path/data.csv:/app/user_data/data.csv:ro
  - /your/path/config.yaml:/app/user_config.yaml:ro
  - ./docker-outputs:/app/gx/uncommitted
```

**Option B**: Mount on-the-fly:
```bash
docker-compose run --rm \
  -v /path/to/your/data.csv:/app/user_data/data.csv:ro \
  driftwatch profile \
    --reference /app/user_data/data.csv \
    --config driftwatch_config.yaml
```

### Docker Output Locations

After running drift detection, outputs are written to your host filesystem:

- **Validation Results (JSON)**: `docker-outputs/validations/`
- **HTML Reports**: `docker-outputs/data_docs/local_site/index.html`
- **Custom Reports**: `docker-outputs/reports/`

### Troubleshooting

#### Permission Errors on Outputs

If you encounter permission errors when writing outputs:

```bash
# Run container as your user
docker run --rm --user $(id -u):$(id -g) \
  -v $(pwd)/docker-outputs:/app/gx/uncommitted \
  driftwatch evaluate --new data/drifted/new_data_with_drift.csv
```

Or fix permissions after:
```bash
sudo chown -R $(id -u):$(id -g) docker-outputs/
```

#### Interactive Debugging

```bash
# Start interactive shell
docker run --rm -it --entrypoint /bin/bash driftwatch

# Inside container, you can run commands directly:
# python -m driftwatch list-expectations
# python -m driftwatch profile --reference data/reference/reference_data.csv --config driftwatch_config.yaml
```

#### Check Container Logs

```bash
docker logs driftwatch
```

### Platform-Specific Notes

**Linux**:
- Native Docker support with optimal performance
- All features work out of the box

**macOS**:
- Requires Docker Desktop
- Volume mounts may be slower (use `:delegated` flag for better performance)
- Use `open` command to view HTML reports

**Windows**:
- Requires Docker Desktop with WSL2 backend recommended
- **Best performance**: Use WSL2 paths (`/mnt/c/Users/...`)
- Alternative: Windows paths work but slower (`C:\Users\...`)
- Use `start` command to view HTML reports

---

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                      DriftWatch CLI                         │
├─────────────────────────────────────────────────────────────┤
│  profile command                evaluate command            │
│  └─> Build GX Suite        └─> Validate against Suite      │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Components                          │
├─────────────────────────────────────────────────────────────┤
│  • DriftWatchConfig (YAML configuration loader)             │
│  • DriftWatchGXContext (persistent GX context manager)      │
│  • ExpectationSuiteBuilder (builds GX suites from data)     │
│  • ValidationResultEnricher (adds DriftWatch metadata)      │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Great Expectations 1.x Layer                   │
├─────────────────────────────────────────────────────────────┤
│  Built-in Expectations:                                     │
│  • ExpectColumnToExist (schema validation)                  │
│  • ExpectColumnMeanToBeBetween (statistical checks)         │
│  • ExpectColumnStdevToBeBetween                             │
│  • ExpectColumnMinToBeBetween                               │
│  • ExpectColumnMaxToBeBetween                               │
│                                                             │
│  Custom Expectations (GX 1.x class-based):                  │
│  • ExpectColumnValuesToHaveDecimalPrecision (GPS)           │
│  • ExpectColumnCategoriesToMatchDistribution (PSI)          │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  GX Outputs                                 │
├─────────────────────────────────────────────────────────────┤
│  • Expectation Suites (gx/expectations/)                    │
│  • Validation Results (gx/uncommitted/validations/)         │
│  • Data Docs (gx/uncommitted/data_docs/local_site/)         │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Patterns

1. **Great Expectations 1.x Class-Based API**: All expectations instantiated as classes
2. **Expectation Suite Builder**: Builds GX suites from reference data + config
3. **Persistent GX Context**: File-based context in `gx/` directory
4. **Validation Results Store**: GX automatically stores validation history
5. **Custom Expectations**: Follow GX 1.x `ColumnAggregateExpectation` pattern

---

## Drift Detection Types

### 1. Schema Drift (ALWAYS ENABLED)

**What We Want to Detect:**

The structure of the data changed - columns disappeared, new columns appeared, or data types changed.

**Example Problem:**
```
Reference data has: restaurant_id, latitude, longitude, delivery_time
New data arrives with: restaurant_id, lat, long, delivery_time

Problem: Column names changed! (latitude → lat, longitude → long)
Your code doing data["latitude"] will crash.
```

**Why This Matters:**
- **Column removed**: Code will crash trying to access missing column
- **Column added**: Might indicate new data source or schema version
- **Type changed**: Integer → String breaks calculations silently

---

**Detection Method: Direct Comparison**

No statistics needed - we just check:
1. Are all expected columns present?
2. Do column data types match?

**Why This Works:**
- Schema changes are binary: column exists or it doesn't
- No ambiguity - no need for thresholds or statistical tests
- Immediate detection - fails on first row if column missing

**Always Enabled:**
This check runs automatically for all columns. No configuration needed - if reference data has 20 columns, we expect new data to have the same 20 columns with same types.

---

### 2. Numerical Statistical Drift

**What We Want to Detect:**

For numerical columns, we want to catch two different problems:

**Problem A: Overall quality changed**
```
Delivery Ratings (Reference): Average = 4.63 (mostly 4.5-5.0 stars)
New data: Average = 2.1 (mostly 1.5-2.5 stars)

Problem: Most ratings are now terrible!
Impact: Service quality collapsed, customer satisfaction dropped
```

**Problem B: Consistency changed**
```
Delivery Time (Reference): Average = 26 min, ranges 16-36 min (predictable)
New data: Average = 26 min, but ranges 5-60 min (wild swings!)

Problem: Delivery times became unpredictable!
Impact: Can't give customers reliable ETAs
```

---

**Available Methods:**

1. **Mean (Average)**: Detects if values shifted higher or lower
   - Good for: "Did quality go down?" or "Did prices increase?"
   - Example: Average rating dropped from 4.6 → 2.1

2. **Standard Deviation (Spread)**: Detects if values became more scattered
   - Good for: "Did consistency change?" or "More outliers appearing?"
   - Example: Delivery times now vary wildly (std dev: 9.75 → 18 min)

3. **Min/Max (Range)**: Detects new extreme values
   - Good for: "Did impossible values appear?"
   - Example: Delivery time = -5 minutes (impossible!)

4. **Percentiles (Median, 95th%)**: Like mean but less sensitive to outliers
   - Good for: Similar to mean, but ignores extreme values
   - Problem: Great Expectations doesn't have built-in percentile checks

---

**Methods Used:**

**A. Mean - For Quality Monitoring**

**Column:** `Delivery_person_Ratings`
**Current State:** Mean = 4.63/5.0 (excellent quality)
**Threshold:** Min = 3.5, Max = 5.0

**Why Mean (not Median or Std Dev)?**
- **Mean answers**: "What's the overall quality?"
- If most ratings shift to < 2.0, mean will drop to ~1.8 (catches the problem)
- **Std dev wouldn't work**: Std dev only measures spread, not whether ratings are LOW
  - All ratings could be consistently terrible (mean=2.0, low std dev) ✅ Passes std dev check ❌ But quality is awful!

**Is 3.5 the right threshold?**
- Somewhat arbitrary - we chose it based on: mean < 3.5 means most ratings are below "acceptable"
- Alternative: Could use 4.0 (stricter) or 3.0 (more lenient)
- **Critical thinking**: This threshold assumes ratings are normally distributed, which may not be true

---

**B. Standard Deviation - For Consistency Monitoring**

**Column:** `Time_taken(min)`
**Current State:** Mean = 26.14 min, Std Dev = 9.75 min
**Threshold:** Min = 8.5, Max = 11.5

**Why Std Dev (not Mean)?**
- **Std dev answers**: "How predictable are delivery times?"
- Low std dev (< 8.5) = Too consistent (might indicate data filtering)
- High std dev (> 11.5) = Unpredictable (operational problems)

**What Std Dev Values Mean:**
- Std dev = 9.75 (current): Most deliveries 16-36 min (moderate variation)
- Std dev = 7.0 (low): Most deliveries 19-33 min (very consistent)
- Std dev = 15.0 (high): Deliveries range 5-60 min (wildly inconsistent)

**Is Std Dev the best choice?**
- **Limitation**: Std dev can be misleading if distribution is skewed
  - Example: 90% of deliveries are 25 min, 10% are 90 min → high std dev, but most customers experience consistency
- **Alternative**: Could use Interquartile Range (IQR) - measures spread without being affected by extreme outliers
  - But GX doesn't have built-in IQR expectations

---

**Why Not Use All Statistics?**

We ONLY monitor mean and std dev for specific columns, not all numerical columns. Why?

- **Avoiding Alert Fatigue**: If we check mean/std/min/max for every column, we'd get 80+ alerts
- **Business Priority**: We care about ratings quality and delivery consistency, not every single number
- **Simpler = Better**: Easier to understand "ratings dropped below 3.5" than tracking 20 different metrics

**Configuration:**
```yaml
expectations:
  # Ratings quality - detect if most ratings drop to poor range
  - column: Delivery_person_Ratings
    expectation: ExpectColumnMeanToBeBetween
    values:
      min_value: 3.5  # Most ratings still acceptable
      max_value: 5.0

  # Delivery time consistency - detect unpredictable service
  - column: Time_taken(min)
    expectation: ExpectColumnStdevToBeBetween
    values:
      min_value: 8.5   # Not too consistent (might be filtered data)
      max_value: 11.5  # Not too chaotic (operational issues)
```

---

### 3. GPS Precision Drift (Custom Expectation)

**What We Want to Detect:**

GPS coordinates lost precision due to data pipeline bugs.

**Example Problem:**
```
Reference data:
  Restaurant_latitude: 12.934523  (6 decimal places = ~10 cm accuracy)

New data arrives:
  Restaurant_latitude: 12.93      (2 decimal places = ~1 km accuracy!)

Problem: Coordinates were truncated somewhere in the pipeline!
Impact: Delivery routing breaks, distances calculated incorrectly
```

**Why This Matters:**

GPS decimal places directly determine accuracy:
- **6 decimals** (12.934523) = ~11 cm precision → Can identify specific building entrance
- **5 decimals** (12.93452) = ~1.1 meters → Building-level accuracy
- **4 decimals** (12.9345) = ~11 meters → Street-level
- **2 decimals** (12.93) = ~1.1 kilometers → City neighborhood level

**Business Impact:**
- Route optimization needs < 10 meter accuracy
- Distance-based pricing becomes wrong (could charge based on wrong distance)
- "Closest restaurant" search returns incorrect results

---

**Available Methods:**

1. **Count Decimal Places**: Simply count digits after decimal point
   - Check if value is "12.934523" (6 decimals) vs "12.93" (2 decimals)
   - Direct and simple

2. **Check Variance**: Truncated coordinates cluster on grid points, reducing variance
   - Example: 12.93, 12.93, 12.93 (low variance) vs 12.934523, 12.934891, 12.935102 (normal variance)
   - Problem: Variance can drop for legitimate reasons (e.g., all restaurants in same area)

3. **Range Check**: Truncated values have smaller range
   - Problem: Similar to variance - legitimate data could have small range

---

**Method Used: Count Decimal Places**

**Why Decimal Counting:**
- **Direct detection**: Catches exact failure mode (truncation)
- **No ambiguity**: Either has 6 decimals or it doesn't
- **Clear signal**: Variance/range can drop for many reasons, but decimal places only drop due to truncation

**How It Works:**
- Convert number to string: `12.934523` → "12.934523"
- Count characters after decimal point: 6
- Alert if most values have < 6 decimals

**Threshold: 95% of values must have 6 decimals**

**Why 95% (not 100%)?**
- Allows for some null values or data quality issues
- If 95% have 2 decimals, that's clearly a pipeline issue (not random noise)

**Is This the Best Method?**

**Pros:**
- ✅ Simple and direct
- ✅ Catches exact problem we care about (truncation)
- ✅ No false positives from legitimate data patterns

**Cons:**
- ❌ Doesn't catch OTHER GPS problems:
  - Coordinates completely wrong (wrong restaurant)
  - Coordinates swapped (latitude ↔ longitude)
  - Coordinates outside valid range (latitude > 90°)

**Alternative Approach:**
For complete GPS validation, could also check:
- Are coordinates within valid ranges? (lat: -90 to 90, lon: -180 to 180)
- Are coordinates in expected geographic region? (e.g., all India locations should be in India)
- But these are different problems - we're specifically monitoring for precision loss

**Single Column Check:**

We only check `Restaurant_latitude`, not all 4 GPS columns (restaurant lat/lon, delivery lat/lon).

**Why?**
- If there's a pipeline bug (database type change, CSV export issue), it affects ALL GPS columns uniformly
- Checking one column is sufficient to detect systematic precision loss
- Reduces alert fatigue (4 alerts → 1 alert for same issue)

**Configuration:**
```yaml
expectations:
  # GPS precision check (detects truncation/rounding bugs)
  - column: Restaurant_latitude
    expectation: ExpectColumnValuesToHaveDecimalPrecision
    values:
      precision: 6      # Require 6 decimal places
      mostly: 0.95      # 95% of values must meet this
```

---

### 4. Categorical Distribution Drift (Custom Expectation)

**Detects:**
- ✅ Distribution shifts using Population Stability Index (PSI)
- ✅ Category disappearance (Medium: 24% → 0%)
- ✅ Category explosions (Jam: 31% → 90%)

**Implementation:**
- Custom GX 1.x expectation: `ExpectColumnCategoriesToMatchDistribution`
- Calculates PSI between reference and observed distributions
- PSI thresholds:
  - PSI < 0.1: No drift
  - 0.1 ≤ PSI < 0.2: Minor drift
  - 0.2 ≤ PSI < 0.25: Major drift
  - PSI ≥ 0.25: **Critical drift**

**Current Configuration:**
```yaml
expectations:
  # Categorical value set expectation
  - column: Type_of_order
    expectation: ExpectColumnValuesToBeInSet
    values:
      value_set: ["Snack", "Meal", "Drinks", "Buffet"]

  # Categorical distribution expectation
  - column: Road_traffic_density
    expectation: ExpectColumnCategoriesToMatchDistribution
    values:
      reference_distribution:
        Jam: 0.314
        Low: 0.344
        Medium: 0.243
        High: 0.098
      psi_threshold: 0.25
```

**Why These Columns:**
- **Type_of_order**: Validates category values remain in expected set
- **Road_traffic_density**: Monitors traffic pattern distribution shifts (PSI-based)

**Why This Matters (Text2SQL Context):**
- Queries like `WHERE traffic = 'Medium'` return 0 rows (unexpected)
- Query optimizer degrades (selectivity changes from 20% → 90%)
- LLM doesn't know categories disappeared
- Historical comparisons impossible

---

## Statistical Methods & Justification

### Overview of Implemented Drift Types

DriftWatch implements **4 types of drift detection** as required by the case study:

1. **Schema Drift** (Column Addition/Removal, Type Changes)
2. **Numerical Statistical Drift** (Mean, Std Dev shifts)
3. **GPS Precision Drift** (Numerical Distribution - Custom)
4. **Categorical Distribution Drift** (PSI-based - Custom)

### 1. Schema Drift Detection

**Implementation:**
- Uses GX built-in `ExpectColumnToExist` for all columns
- Type checking using pandas dtype comparison

**Justification:**
- **No statistical test needed** - Schema changes are binary (column exists or not)
- Column removal = CRITICAL (breaks downstream queries)
- Column addition = MAJOR (indicates schema evolution)
- Type changes = CRITICAL (breaks type-dependent operations)

**Why This Approach:**
- Direct column set comparison is deterministic and reliable
- No false positives - either the column exists or it doesn't
- Type comparison catches silent data corruption (int → string)

---

### 2. Numerical Statistical Drift

**Statistical Tests Used:**
1. **Mean Test**: Detects distribution shifts (e.g., most ratings drop to < 2.0)
2. **Standard Deviation Test**: Detects consistency changes (e.g., delivery times become unpredictable)

**Justification:**

**A. Delivery Ratings - Mean Test:**

**Column:** `Delivery_person_Ratings`
**Metric:** `ExpectColumnMeanToBeBetween(min_value: 3.5, max_value: 5.0)`

**Current State:**
- Mean: 4.63 / 5.0 (excellent quality)
- 75% of ratings ≥ 4.5
- Only 0.09% of ratings < 2.0

**What It Detects:**
- **Distribution shift toward low ratings**: If most ratings drop to < 2.0, mean would drop to ~1.9
- **Threshold at 3.5**: Indicates majority of ratings have shifted to poor quality range

**Why Mean (not Median or Std Dev)?**
- **Median**: Great Expectations doesn't have built-in median expectation (would require custom implementation)
- **Std Dev**: Measures consistency, NOT absolute quality level (all ratings could be consistently terrible with low std dev!)
- **Mean**: Direct measure of overall quality, built-in support, stakeholder-friendly

**Business Impact:**
- Mean < 3.5 = Service quality crisis, immediate investigation required
- Catches systemic quality degradation, not just isolated incidents

---

**B. Delivery Time - Standard Deviation Test:**

**Column:** `Time_taken(min)`
**Metric:** `ExpectColumnStdevToBeBetween(min_value: 8.5, max_value: 11.5)`

**Current State:**
- Mean: 26.14 minutes
- Std Dev: 9.75 minutes
- Range: 10-54 minutes (moderate spread)

**What It Detects:**
- **Std Dev < 8.5 (too consistent)**:
  - Possible data filtering/sampling bias
  - Geographic restriction (only urban deliveries)
  - Missing data for slow deliveries
- **Std Dev > 11.5 (too inconsistent)**:
  - Unpredictable delivery times
  - Operational problems (staffing, routing failures)
  - Service area expansion without adjustment

**Why Std Dev (not Mean)?**
- **Mean**: Measures average speed, not consistency
- **Std Dev**: Measures predictability - critical for customer satisfaction
- **Business Impact**: Customers care about consistency as much as speed

**Threshold Justification:**
- 8.5 = ~87% of reference std dev (allows efficiency improvements)
- 11.5 = ~118% of reference std dev (flags unpredictability)
- Based on reference data analysis (std dev: 9.75)

---

**Alternative Considered:**
- **Kolmogorov-Smirnov (KS) Test**: Rejected because:
  - Too sensitive for large datasets (always significant with N > 10k)
  - Requires choosing arbitrary p-value threshold
  - Doesn't provide actionable thresholds (what does p=0.03 mean for operations?)
  - Mean/Std tests directly answer: "How much did quality/consistency change?"

---

### 3. GPS Precision Drift (Custom Expectation)

**Statistical Test:**
- **Custom Metric**: Decimal place counting using string analysis
- **Threshold**: Precision must be ≥ 6 decimal places for 99.9% of values

**Justification:**

**Why Decimal Place Counting?**
- **Direct Detection**: Precision loss is deterministic (6 decimals → 2 decimals)
- **No Statistical Test Needed**: Precision is a property of the data representation, not distribution
- **High Specificity**: Catches exact failure mode (database truncation, type conversion)
- **Implementation**: String analysis to count decimal places

**Why 6 Decimal Places?**
- **Geographic Precision**:
  - 6 decimals = ~0.11 meters (street address accuracy)
  - 5 decimals = ~1.1 meters (building-level accuracy)
  - 2 decimals = ~1.1 kilometers (city-level only)
- **Business Requirements**:
  - Delivery routing needs street-level precision (< 10 meters)
  - Distance-based pricing breaks with kilometer-level precision
  - Route optimization requires accurate coordinates between restaurant and delivery location

**Why 95% Threshold (`mostly=0.95`)?**
- Allows for some null values or data quality issues
- Still catches systematic precision loss affecting majority of column
- Balances detection sensitivity with real-world data quality

**Alternative Considered:**
- **Variance Test**: Rejected because:
  - Truncated values cluster on grid points → variance drops
  - But variance drop could be caused by other factors (legitimate data change)
  - Decimal counting is more direct and interpretable

**Real-World Example:**
- PostgreSQL: `DECIMAL(10,6)` → `DECIMAL(4,2)` migration bug
- CSV export: Excel auto-formatting removes trailing decimals
- API change: New vendor returns 2 decimals instead of 6

---

### 4. Categorical Distribution Drift (Custom Expectation)

**What We Want to Detect:**

We need to catch when the **proportions of categories change** in our data. For example:

```
Road Traffic Density (Reference data):
  Low: 34%    Medium: 24%    High: 10%    Jam: 31%

New data arrives with very different proportions:
  Low: 10%    Medium: 0%     High: 0%     Jam: 90%

Problem: "Medium" traffic disappeared! Queries like WHERE traffic='Medium'
will return 0 rows unexpectedly.
```

**Why This Matters:**
- LLMs generate queries assuming old category distributions
- Models trained on "Medium=24%" now see "Medium=0%"
- Business logic breaks (e.g., "send alert if Medium traffic > 30%")

---

**Available Methods:**

1. **Chi-Square Test**: Statistical test that checks "are these distributions different?"
   - Problem: With 45k+ rows, it ALWAYS says "yes, they're different" (too sensitive)
   - Gives p-value (0.001) but not "how different" or "how bad is it?"

2. **Simple Percentage Difference**: Compare each category (|new% - old%|)
   - Example: Medium went from 24% → 0%, difference = 24%
   - Problem: How do we combine differences across all categories into one decision?

3. **Population Stability Index (PSI)**: Combines all category changes into single number
   - Formula: For each category, calculate: `(new% - old%) × ln(new% / old%)`
   - Sum across all categories to get one drift score
   - PSI = 0.1 means "small shift", PSI = 0.5 means "huge shift"

---

**Method Used: PSI**

**Why PSI:**
- **Single number**: PSI = 0.3 immediately tells you severity (vs tracking 4 separate percentages)
- **Handles disappearing categories**: When Medium drops to 0%, PSI captures this correctly
- **Balanced**: Treats "category growing" and "category shrinking" equally important

**Limitations of PSI:**
- **Arbitrary threshold**: Why is 0.25 "critical"? This is somewhat arbitrary (borrowed from credit scoring)
- **Hard to interpret**: What does PSI = 0.3 actually mean? Not as intuitive as "Medium traffic dropped 24%"
- **Overkill for simple cases**: If you only care about ONE category disappearing, checking `Medium% > 5%` is simpler

**Is PSI the best choice?**

For our use case (monitoring 4-5 categories, need automated alerts), PSI works well because:
- ✅ Automates the decision: PSI > 0.25 → alert (vs manually checking 4 percentages)
- ✅ Handles multiple simultaneous changes (e.g., Medium↓ AND Jam↑)

But for simpler monitoring, you could just track:
- "Are any categories below 5%?" (catches disappearing categories)
- "Did any category change by more than 20%?" (catches big shifts)

**PSI Thresholds Used:**

| PSI Value | What It Means | Action |
|-----------|---------------|--------|
| < 0.1 | Categories shifted < 10% on average | Monitor |
| 0.1 - 0.2 | Moderate shifts | Investigate |
| 0.2 - 0.25 | Large shifts | Review data pipeline |
| ≥ 0.25 | Categories drastically changed | **Stop processing** |

**Real Example from Our Data:**

```
Traffic Density Drift:
  Reference:    Low=34%, Medium=24%, High=10%, Jam=31%
  New Dataset:  Low=10%, Medium=0%,  High=0%,  Jam=90%

  Changes:
    - "Jam" exploded: 31% → 90% (+59%)
    - "Medium" and "High" disappeared completely
    - "Low" dropped significantly

  PSI Calculation: 3.43 (very high!)
  Verdict: CRITICAL - distribution has fundamentally changed
```

**What This Drift Means:**
- Traffic patterns completely different (mostly jammed now)
- Models trained on old data will perform poorly
- Business rules may not apply (e.g., "avoid High traffic routes")

---

### Summary Table

| Drift Type | Column | Statistical Method | Threshold | What It Detects |
|------------|--------|-------------------|-----------|-----------------|
| Schema | All columns | Deterministic set comparison | N/A | Column addition/removal |
| Numerical (Mean) | Delivery_person_Ratings | Mean | 3.5 - 5.0 | Distribution shift to low ratings |
| Numerical (Std Dev) | Time_taken(min) | Std Dev | 8.5 - 11.5 min | Delivery time consistency changes |
| GPS Precision | Restaurant_latitude | Decimal place counting | ≥6 decimals, 95% | GPS truncation/rounding bugs |
| Categorical (Value Set) | Type_of_order | Set membership | Fixed set | New/removed order types |
| Categorical (PSI) | Road_traffic_density | Population Stability Index | PSI < 0.25 | Traffic pattern distribution shifts |

**Key Design Principles:**
- **Column selection**: Business-critical metrics with clear interpretation
- **Mean for quality**: Detects distribution shifts (e.g., most ratings drop to < 2.0)
- **Std Dev for consistency**: Detects variability changes (e.g., unpredictable delivery times)
- **Representative GPS check**: Single column sufficient (pipeline issues affect all GPS columns)
- **Actionable thresholds**: Direct business meaning (mean < 3.5 = quality crisis)

---

## Configuration

### Configuration File: `driftwatch_config.yaml`

DriftWatch uses a simplified YAML configuration with direct column-level expectations:

```yaml
# DriftWatch Configuration - Simplified

# Schema check (automated from reference data)
schema:
  enabled: true

# Column-level expectations (user-provided values)
expectations:
  # Statistical expectation for delivery time consistency
  - column: Time_taken(min)
    expectation: ExpectColumnStdevToBeBetween
    values:
      min_value: 8.5
      max_value: 11.5

  # Delivery ratings quality - detect distribution shift to low ratings
  - column: Delivery_person_Ratings
    expectation: ExpectColumnMeanToBeBetween
    values:
      min_value: 3.5
      max_value: 5.0

  # GPS precision expectation (representative check)
  - column: Restaurant_latitude
    expectation: ExpectColumnValuesToHaveDecimalPrecision
    values:
      precision: 6
      mostly: 0.95

  # Categorical value set expectation
  - column: Type_of_order
    expectation: ExpectColumnValuesToBeInSet
    values:
      value_set: ["Snack", "Meal", "Drinks", "Buffet"]

  # Categorical distribution expectation
  - column: Road_traffic_density
    expectation: ExpectColumnCategoriesToMatchDistribution
    values:
      reference_distribution:
        Jam: 0.314
        Low: 0.344
        Medium: 0.243
        High: 0.098
      psi_threshold: 0.25

reporting:
  format: json
  output_dir: outputs

logging:
  level: INFO
```

**Key Features:**
- **Schema drift**: Always enabled (automated)
- **Direct expectations**: Specify exactly which columns and thresholds to monitor
- **Minimal configuration**: Only 5 expectations covering 4 drift types
- **Representative checks**: Single GPS column (applies to all if pipeline issue)

---

## Usage Examples

### Monthly Batch Processing

```bash
# Profile reference once
python -m driftwatch.cli profile \
    --reference data/reference/baseline.csv \
    --config driftwatch_config.yaml

# Evaluate each month (reuses same suite from gx/expectations/)
python -m driftwatch.cli evaluate \
    --new data/january/batch.csv

python -m driftwatch.cli evaluate \
    --new data/february/batch.csv
```

### View Validation History

```bash
# List all validation runs
ls -lt gx/uncommitted/validations/

# View specific validation result
cat gx/uncommitted/validations/drift_eval_20260118_120000/*.json | jq .
```

### Generate Data Docs

```bash
# Data Docs are auto-generated during evaluation
# To manually rebuild:
python -c "from driftwatch.core.gx_context import DriftWatchGXContext; \
           ctx = DriftWatchGXContext().get_context(); \
           ctx.build_data_docs()"

# View in browser
open gx/uncommitted/data_docs/local_site/index.html
```

---

## Design Decisions

### Why Great Expectations 1.x?

1. **Class-Based API**: Type-safe, IDE-friendly expectation instantiation
2. **Built-in Validation Engine**: Battle-tested, production-grade
3. **Persistent State**: File-based context stores suites and results
4. **Data Docs**: Automatic HTML report generation
5. **Extensibility**: Custom expectations using well-defined patterns
6. **Validation Results Store**: Built-in audit trail

### Why Custom Expectations?

Built-in GX expectations don't cover:
- GPS decimal precision checking
- Population Stability Index (PSI) for categorical drift

Custom expectations fill these gaps while maintaining GX ecosystem benefits.

### Key Design Principles

1. **GX-First**: Use GX built-ins wherever possible
2. **Class-Based API**: Follow GX 1.x patterns (not deprecated 0.x validator methods)
3. **Persistent Context**: File-based `gx/` directory for state management
4. **Separation of Concerns**: Config defines WHAT to monitor, data defines normal values

---

## Project Structure

```
driftwatch/
├── __init__.py
├── cli.py                              # Command-line interface
├── core/
│   ├── config.py                       # YAML configuration loader
│   ├── expectation_suite_builder.py   # Builds GX suites from data + config
│   ├── gx_context.py                   # GX file context manager
│   └── validation_result_enricher.py  # Adds DriftWatch metadata to results
├── expectations/
│   ├── expect_column_values_to_have_decimal_precision.py  # GPS precision
│   └── expect_column_categories_to_match_distribution.py  # PSI-based drift
└── utils/
    └── logging_config.py               # Logging setup

gx/                                     # GX state directory (persistent)
├── expectations/
│   └── driftwatch_reference_suite.json (~10KB, not 3.7MB!)
├── uncommitted/
│   ├── validations/                   # Validation results (audit trail)
│   └── data_docs/                     # HTML reports
└── great_expectations.yml              # GX config
```

---

## Performance

**Suite Building:**
- 45k rows, 20 columns: ~3 seconds
- Output size: ~10KB (vs 3.7MB for old custom profiles!)

**Validation:**
- 45k rows, 61 expectations: ~1-2 seconds
- Results stored automatically by GX

**Storage:**
- Expectation suite: ~10KB
- Validation result: ~50KB per run
- Complete audit trail maintained

---

## Testing

### Run Against Sample Data

```bash
# 1. Profile reference
python -m driftwatch.cli profile \
    --reference data/reference/reference_data.csv \
    --config driftwatch_config.yaml

# 2. Evaluate drifted data
python -m driftwatch.cli evaluate \
    --new data/drifted/new_data_with_drift.csv

# Expected: Multiple drifts detected
```

---

## Migration from Legacy

The `legacy/` folder contains the pre-GX 1.x implementation with:
- Custom profiler (3.7MB JSON files)
- Old detector wrappers
- CSV audit logging

See `legacy/README.md` for details on what changed and why.

---

## License

MIT License - See LICENSE file

---

## Development

### Code Quality Tools

**Linting with Ruff:**
```bash
# Check all code
ruff check driftwatch/

# Auto-fix issues
ruff check driftwatch/ --fix

# Check with unsafe fixes
ruff check driftwatch/ --fix --unsafe-fixes
```

**Ruff Configuration:**
- **Line length**: 100 characters
- **Target**: Python 3.12
- **Enabled rules**: E, F, I, N, W, UP, B, C4, SIM, RET, ARG, PTH, PL, RUF
- **Per-file ignores**: Custom patterns for CLI, expectations, tests

See `pyproject.toml` for complete configuration.

### Type Checking

```bash
# Run mypy type checker
mypy driftwatch/
```

### Running Tests

```bash
# Run pytest (when tests are added)
pytest
```

---

## Extending the Framework

### How to Add a New Drift Detection Rule

DriftWatch is designed to be easily extensible. You can add drift detection rules in two ways:

#### Option 1: Use Existing Great Expectations

Great Expectations provides 50+ built-in expectations. To use an existing GX expectation:

**Step 1: Find the Expectation**

Browse available expectations in the [GX Expectation Gallery](https://greatexpectations.io/expectations/) or check the [GX 1.x documentation](https://docs.greatexpectations.io/docs/core/introduction/gx_overview).

Common examples:
- `ExpectColumnValuesToBeBetween` - Values in a range
- `ExpectColumnValuesToBeUnique` - Uniqueness check
- `ExpectColumnValuesToNotBeNull` - Null check
- `ExpectColumnDistinctValuesToBeInSet` - Category whitelist
- `ExpectTableRowCountToBeBetween` - Row count bounds

**Step 2: Register in Expectation Registry** (if not already registered)

Check if the expectation is already in `driftwatch/core/expectation_registry.py`. If not, add it:

```python
from great_expectations.expectations import (
    ExpectColumnValuesToBeBetween,
    ExpectColumnValuesToBeUnique,
    ExpectColumnDistinctValuesToBeInSet,
)

EXPECTATION_REGISTRY = {
    # ... existing expectations ...

    "ExpectColumnValuesToBeBetween": {
        "class": ExpectColumnValuesToBeBetween,
        "params": ["min_value", "max_value", "mostly"]
    },
    "ExpectColumnValuesToBeUnique": {
        "class": ExpectColumnValuesToBeUnique,
        "params": []
    },
    "ExpectColumnDistinctValuesToBeInSet": {
        "class": ExpectColumnDistinctValuesToBeInSet,
        "params": ["value_set"]
    },
}
```

> **Note:** DriftWatch includes many common GX expectations by default. Only add to the registry if you're using an expectation that isn't already there.

**Step 3: Add to Configuration**

Add the expectation to your `driftwatch_config.yaml`:

```yaml
expectations:
  - column: age
    expectation: ExpectColumnValuesToBeBetween
    values:
      min_value: 18
      max_value: 100
      mostly: 0.95  # 95% of values must be in range

  - column: user_id
    expectation: ExpectColumnValuesToBeUnique
    values: {}

  - column: status
    expectation: ExpectColumnDistinctValuesToBeInSet
    values:
      value_set: ["active", "inactive", "pending"]
```

**Step 4: Test**

```bash
# Profile with new expectation
python -m driftwatch.cli profile \
    --reference your_data.csv \
    --config driftwatch_config.yaml

# Evaluate
python -m driftwatch.cli evaluate --new new_data.csv
```

---

#### Option 2: Create Custom Expectation

For specialized drift detection logic not covered by GX built-ins, create a custom expectation.

**Step 1: Create Custom Expectation Class**

Create a new file in `driftwatch/expectations/` following GX 1.x patterns:

```python
# driftwatch/expectations/expect_column_custom_check.py
from great_expectations.expectations import ColumnAggregateExpectation
from great_expectations.render import RenderedStringTemplateContent
from great_expectations.execution_engine import PandasExecutionEngine

class ExpectColumnCustomCheck(ColumnAggregateExpectation):
    """Custom expectation for detecting specific drift pattern."""

    metric_dependencies = ("column.custom_metric",)

    def _validate(
        self,
        metrics: dict,
        custom_threshold: float = 0.1,
    ):
        """Validation logic.

        Args:
            metrics: Dictionary containing computed metrics
            custom_threshold: Threshold for drift detection

        Returns:
            Dictionary with success status and result details
        """
        metric_value = metrics.get("column.custom_metric")

        success = metric_value <= custom_threshold

        return {
            "success": success,
            "result": {
                "observed_value": metric_value,
                "threshold": custom_threshold,
            }
        }
```

#### Step 2: Register in Expectation Registry

Add your expectation to `driftwatch/core/expectation_registry.py`:

```python
# Import your custom expectation
from driftwatch.expectations import (
    ExpectColumnCategoriesToMatchDistribution,
    ExpectColumnValuesToHaveDecimalPrecision,
    ExpectColumnCustomCheck,  # Add this
)

# Add to EXPECTATION_REGISTRY
EXPECTATION_REGISTRY = {
    # ... existing expectations ...

    # Your custom expectation
    "ExpectColumnCustomCheck": {
        "class": ExpectColumnCustomCheck,
        "params": ["custom_threshold"]
    },
}
```

#### Step 3: Use in Configuration

Add to your `driftwatch_config.yaml`:

```yaml
expectations:
  - column: YourColumn
    expectation: ExpectColumnCustomCheck
    values:
      custom_threshold: 0.1
```

#### Step 4: Test Your Expectation

```bash
# Profile with new expectation
python -m driftwatch.cli profile \
    --reference your_data.csv \
    --config driftwatch_config.yaml

# Evaluate
python -m driftwatch.cli evaluate \
    --new new_data.csv
```

**Key Points:**
- Extend `ColumnAggregateExpectation` for column-level metrics
- Extend `TableExpectation` for table-level checks
- Follow GX 1.x patterns (not 0.x validator methods)
- Add to registry with accurate parameter list
- Write clear docstrings and error messages

---

## Sample Data

The project includes sample datasets for testing:

**Reference Dataset:**
- `data/reference/reference_data.csv` - 1,000 rows, 20 columns
- Food delivery order data including:
  - GPS coordinates (Restaurant and Delivery locations)
  - Delivery person ratings and age
  - Traffic density and weather conditions
  - Order timestamps and vehicle information

**Columns:**
- ID, Delivery_person_ID, Delivery_person_Age, Delivery_person_Ratings
- Restaurant_latitude, Restaurant_longitude
- Delivery_location_latitude, Delivery_location_longitude
- Order_Date, Time_Orderd, Time_Order_picked
- Weather_conditions, Road_traffic_density, Vehicle_condition
- Type_of_order, Type_of_vehicle, multiple_deliveries
- Festival, City, Time_taken(min)

**Creating Test Data with Drift:**
To create datasets with specific drift patterns for testing:

```python
import pandas as pd
import numpy as np

# Load reference
df = pd.read_csv('data/reference/reference_data.csv')

# Example: GPS precision drift (truncate coordinates)
df['Restaurant_latitude'] = df['Restaurant_latitude'].round(2)
df['Restaurant_longitude'] = df['Restaurant_longitude'].round(2)
df.to_csv('gps_drift_test.csv', index=False)

# Example: Categorical distribution drift
# Replace 50% of 'Low' traffic with 'Jam'
mask = df['Road_traffic_density'] == 'Low'
change_indices = df[mask].sample(frac=0.5).index
df.loc[change_indices, 'Road_traffic_density'] = 'Jam'
df.to_csv('categorical_drift_test.csv', index=False)
```

---

## Test Cases

### End-to-End Test Scenarios

#### Test 1: No Drift Detection
```bash
# Profile reference
python -m driftwatch.cli profile \
    --reference data/reference/reference_data.csv \
    --config driftwatch_config.yaml

# Evaluate against same data
python -m driftwatch.cli evaluate --new data/reference/reference_data.csv

# Expected: 0 drifts, severity: CLEAN
```

#### Test 2: GPS Precision Drift
```bash
# Generate drift data with truncated GPS coordinates
python generate_drift_datasets.py

# Evaluate
python -m driftwatch.cli evaluate --new data/gps_precision_drift.csv

# Expected: 4 drifts (4 GPS columns), severity: CRITICAL
```

#### Test 3: Categorical Distribution Drift
```bash
# Evaluate traffic distribution shift
python -m driftwatch.cli evaluate --new data/categorical_drift.csv

# Expected: 1 drift (Road_traffic_density), severity: CRITICAL
# PSI > 0.25 indicates significant distribution change
```

#### Test 4: Statistical Drift
```bash
# Evaluate rating outliers
python -m driftwatch.cli evaluate --new data/statistical_drift.csv

# Expected: Multiple drifts in Delivery_person_Ratings
# Mean, stdev, min, or max outside expected ranges
```

#### Test 5: Schema Drift
```bash
# Test column removal
# Manually remove a column from CSV and evaluate

# Expected: Schema drift detected, missing column flagged
```

#### Test 6: Invalid Configuration
```bash
# Test with invalid config
python -m driftwatch.cli profile \
    --reference data/reference/reference_data.csv \
    --config invalid_config.yaml

# Expected: Validation errors showing:
# - Missing required fields
# - Invalid column names
# - Invalid expectation names
# - Invalid parameters
```

### Automated Test Script

The simplest test validates that the same dataset has no drift:

```bash
#!/bin/bash
# test_no_drift.sh

echo "DriftWatch - No Drift Test"
echo "==========================="

# Step 1: Profile reference
echo "Step 1: Profiling reference dataset..."
python -m driftwatch.cli profile \
    --reference data/reference/reference_data.csv \
    --config driftwatch_config.yaml

# Step 2: Evaluate against itself (should have no drift)
echo -e "\nStep 2: Evaluating against same dataset..."
python -m driftwatch.cli evaluate --new data/reference/reference_data.csv

echo -e "\n✓ Test complete!"
echo "Expected: 0 drifts, severity: CLEAN"
```

**Test with config validation:**
```bash
# Create invalid config to test validation
cat > test_invalid.yaml << 'EOF'
suite_name: "test"
schema_check:
  enabled: true
expectations:
  - expectation: ExpectColumnMeanToBeBetween  # Missing 'column'
    values:
      min_value: 1.0
EOF

# Test - should show validation errors
python -m driftwatch.cli profile \
    --reference data/reference/reference_data.csv \
    --config test_invalid.yaml

# Expected: Configuration validation error listing all issues
```

---

## Contributing

This is a case study project. For production use, consider:
- Adding unit tests (pytest)
- Adding CI/CD pipeline
- Adding more custom expectations
- Adding alert integrations (Slack, email)

---

## Acknowledgments

- **Great Expectations**: For the excellent data validation framework
- **Statistical Methods**: PSI for categorical drift, mean/std dev for numerical drift
- **Case Study Source**: Backend Engineering Assessment

---

## Contact

For questions or feedback, please open an issue on GitHub.

---

**Powered by Great Expectations 1.x** 🚀
