# Drift Dataset Manifest

## Overview
This document describes the intentional drifts introduced in the test datasets.

## Reference Dataset: reference_data.csv
- Source: food_delivery.csv
- Rows: 45,584
- Columns: 20
- Purpose: Baseline for all drift comparisons

### Reference Statistics:
- **GPS Precision:** 6 decimal places (~0.11 meter precision)
  - Example: 30.327968, 78.046106
- **Traffic Distribution:**
  - Low: ~34%
  - Medium: ~24%
  - High: ~10%
  - Jam: ~31%
- **Vehicle Condition Type:** integer (0, 1, 2, 3)
- **Columns:** Does NOT contain 'delivery_category'

---

## Drifted Dataset: new_data_with_drift.csv
Contains FOUR types of drift across SCHEMA, NUMERICAL, and CATEGORICAL dimensions:

### Drift 1: GPS Coordinate Precision Loss (Numerical Distribution Drift)

**Type:** Numerical Distribution Drift
**Columns Affected:**
- Restaurant_latitude
- Restaurant_longitude
- Delivery_location_latitude
- Delivery_location_longitude

**Change:**
- Before: 6 decimal places (e.g., 30.327968)
- After: 2 decimal places (e.g., 30.33)
- Precision loss: 1000× (0.11m → 1.1km)

**Root Cause Simulation:**
- Database column type change (DECIMAL(10,6) → DECIMAL(4,2))
- CSV export/import truncation
- Type conversion bug in data pipeline

**Expected Detection:**
- Variance collapse (values cluster on fewer decimal places)
- KS test detects distribution shape change
- Decimal place counting shows reduction
- Histogram shows unnatural clustering

**Business Impact:**
- Distance calculations wrong (1km precision vs 0.1m)
- Route optimization breaks
- Delivery zone assignment incorrect
- SLA calculations inaccurate

---

### Drift 2: Traffic Density Distribution Skew (Categorical Distribution Drift)

**Type:** Categorical Distribution Drift
**Column Affected:** Road_traffic_density

**Change:**
| Category | Reference | Drifted | Change |
|----------|-----------|---------|--------|
| Low      | ~20%      | ~10%    | -50%   |
| Medium   | ~30%      | 0%      | -100% ❌ |
| High     | ~30%      | 0%      | -100% ❌ |
| Jam      | ~20%      | ~80%    | +300%  |

**Root Cause Simulation:**
- Data source change (different city or time period)
- Filtering bug (WHERE traffic IN ('Low', 'Jam') accidentally added)
- Geographic sampling bias (only congested areas)
- Temporal sampling bias (only peak hours)

**Expected Detection:**
- Chi-square test: p-value < 0.0001
- PSI (Population Stability Index) > 0.25 (critical threshold)
- Category disappearance: Medium and High → 0%
- Cardinality reduction: 4 active categories → 2 active

**Business Impact:**
- Text2SQL queries: `WHERE traffic = 'Medium'` returns 0 rows
- Historical comparison impossible (different populations)
- Average delivery time biased toward Jam conditions
- Query optimization degrades (Jam selectivity 20% → 80%)

---

### Drift 3: New Column Addition (Schema Drift)

**Type:** Schema Drift - Column Addition
**Column Added:** delivery_category

**Change:**
- Reference dataset: No 'delivery_category' column
- Drifted dataset: New column 'delivery_category' with values 'Food' and 'Grocery'

**Logic:**
- For 'Drinks' orders: 50% → 'Grocery'
- All other orders: → 'Food'

**Distribution:**
- Food: ~93% (all non-Drinks + 50% of Drinks)
- Grocery: ~7% (50% of Drinks orders)

**Root Cause Simulation:**
- Schema evolution: Product team added delivery categorization
- New feature: Separate grocery deliveries from food
- Upstream system change: Different warehouses for Food vs Grocery

**Expected Detection:**
- Column count: 20 → 21
- New column name: 'delivery_category'
- Column not present in reference schema
- Type: string/object
- Cardinality: 2 unique values

**Business Impact:**
- Queries may fail if column not expected
- ETL pipelines may break if schema validation strict
- Downstream systems may not know how to handle new column
- Data warehouse schema needs updating

---

### Drift 4: Column Type Change (Schema Drift)

**Type:** Schema Drift - Data Type Change
**Column Affected:** Vehicle_condition

**Change:**
| Value | Reference Type | Drifted Type |
|-------|---------------|--------------|
| 0 | int64 | "00" (string/object) |
| 1 | int64 | "01" (string/object) |
| 2 | int64 | "02" (string/object) |
| 3 | int64 | "03" (string/object) |

**Root Cause Simulation:**
- Database migration: INT → VARCHAR
- Export format change: Numbers exported with leading zeros
- System integration: New system sends zero-padded strings
- CSV export quirk: Excel formatting causing type change

**Expected Detection:**
- Type change: int64/float64 → object/string
- Values semantically same but syntactically different
- Comparisons break: `WHERE vehicle_condition = 0` fails (0 != "00")
- Aggregations fail: `AVG(vehicle_condition)` breaks on strings

**Business Impact:**
- Queries with numeric comparisons fail: `WHERE vehicle_condition > 1`
- Aggregations impossible: `AVG(vehicle_condition)`
- Sorting changes: String sort ("00", "01", "02", "03") vs numeric sort (0, 1, 2, 3)
- Type casting required in all downstream code
- Historical comparisons need type conversion

---

## Statistical Tests to Apply

### For GPS Precision Loss:
1. **Kolmogorov-Smirnov Test:** Compare distributions
2. **Variance Test:** Reference variance >> Drifted variance
3. **Decimal Analysis:** Count significant digits
4. **Clustering Detection:** Check if values cluster on 0.01 intervals

### For Traffic Density Skew:
1. **Chi-square Test:** Test distribution differences
2. **PSI Calculation:** Should exceed 0.25
3. **Category Disappearance:** Flag Medium and High → 0%
4. **Frequency Comparison:** Per-category before/after

### For Schema Drifts:
1. **Column Comparison:** Reference columns vs New columns
2. **Type Comparison:** Compare dtypes for each column
3. **Column Addition Detection:** New columns not in reference
4. **Column Removal Detection:** Reference columns not in new
5. **Type Change Detection:** Same column, different dtype

---

## Summary of All Drifts

| # | Drift Type | Affected Column(s) | Detection Method |
|---|------------|-------------------|------------------|
| 1 | Numerical Distribution | GPS coordinates (4 columns) | KS Test, Variance |
| 2 | Categorical Distribution | Road_traffic_density | Chi-square, PSI |
| 3 | Schema - Column Addition | delivery_category (NEW) | Column comparison |
| 4 | Schema - Type Change | Vehicle_condition | Type comparison |

**Total Columns Affected:** 6 out of 20 (30% of schema)
**Drift Types:** 3 (Schema, Numerical, Categorical)
**Severity:** Critical (2 categories disappeared, precision loss, schema changes)

---

## Usage

```bash
# Run drift detection
python driftwatch_cli.py --reference reference_data.csv --new new_data_with_drift.csv --output report.json

# Expected detections:
# 1. Schema drift: Column addition (delivery_category)
# 2. Schema drift: Type change (Vehicle_condition: int → string)
# 3. Numerical drift: GPS columns (4 columns, KS test p-value < 0.05)
# 4. Categorical drift: Road_traffic_density (PSI > 0.25, 2 categories disappeared)
```

---

## Validation Checklist

### Schema Drift:
- [ ] Drifted data has 21 columns (Reference has 20)
- [ ] New column 'delivery_category' exists in drifted data
- [ ] 'delivery_category' has values 'Food' and 'Grocery'
- [ ] Vehicle_condition type is object/string in drifted data (was numeric)
- [ ] Vehicle_condition values are "00", "01", "02", "03" (was 0, 1, 2, 3)

### Numerical Drift:
- [ ] GPS coordinates have exactly 2 decimal places in drifted data
- [ ] Reference GPS has 6 decimal places

### Categorical Drift:
- [ ] Medium traffic records = 0 in drifted data
- [ ] High traffic records = 0 in drifted data
- [ ] Jam traffic ~90% in drifted data
- [ ] Low traffic ~10% in drifted data

### Data Integrity:
- [ ] Row count unchanged (45,584 rows in both)
- [ ] ID column unchanged
- [ ] No unexpected nulls introduced

