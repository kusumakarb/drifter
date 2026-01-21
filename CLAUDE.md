# Development Guidelines for Claude Code

## Error Handling

**CRITICAL RULE: Never catch exceptions and silently continue unless specifically requested.**

### ❌ Bad - Silent error swallowing:
```python
try:
    result = risky_operation()
except Exception:
    pass  # BAD: Silent failure

try:
    data = process_data(col)
except (ValueError, KeyError):
    continue  # BAD: Skips without logging or informing
```

### ✅ Good - Proper error handling:
```python
# Option 1: Log and re-raise (for unexpected errors)
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Failed to perform operation: {e}")
    raise

# Option 2: Collect all errors, then fail (BEST for loops)
missing_items = []
valid_items = []

for item in items:
    try:
        data = process_item(item)
        valid_items.append((item, data))
    except (ValueError, KeyError) as e:
        missing_items.append({'item': item, 'reason': str(e)})

# Fail if any items had errors
if missing_items:
    error_details = ', '.join([f"{m['item']} ({m['reason']})" for m in missing_items])
    logger.error(f"Failed to process items: {error_details}")
    raise ValueError(f"Configuration error: {len(missing_items)} item(s) failed: {error_details}")

# Process all valid items
for item, data in valid_items:
    # ... process ...

# Option 3: Handle specific expected errors with fallback
try:
    value = compute_metric(data)
except ZeroDivisionError:
    logger.warning("Division by zero, using fallback value")
    value = 0.0
except Exception as e:
    logger.error(f"Unexpected error computing metric: {e}")
    raise
```

### Why this matters:

1. **Debugging**: Silent errors make bugs impossible to track down
2. **Data Quality**: Users need to know when drift detection fails
3. **Production Reliability**: Silent failures can corrupt results without warning
4. **Observability**: Logs are essential for monitoring and troubleshooting

### When to catch and continue:

Only when:
1. The error is expected and documented
2. There's a clear fallback or skip strategy
3. The error is logged with appropriate severity
4. The user is aware of the behavior (documented)

### Implementation checklist:

- [ ] Use Python's `logging` module instead of silent errors
- [ ] Catch specific exceptions, not bare `except Exception`
- [ ] Always log at appropriate level (ERROR, WARNING, INFO)
- [ ] Include context in error messages (column names, values, etc.)
- [ ] Document expected errors in docstrings
- [ ] Re-raise unexpected errors
- [ ] Test error paths explicitly

---

## Logging

**CRITICAL RULE: Always use Python's logging module. Never use print() statements.**

### ❌ Bad - Using print():
```python
print("Processing data...")
print(f"Found {count} items")
print("ERROR: Something went wrong")
```

### ✅ Good - Using logger:
```python
import logging

logger = logging.getLogger(__name__)

logger.info("Processing data...")
logger.info(f"Found {count} items")
logger.error("Something went wrong")
```

### Log Levels (when to use each):

- **`logger.debug()`** - Detailed diagnostic information, usually only interesting when diagnosing problems
  - Example: `logger.debug(f"Processing column {col} with {len(data)} rows")`

- **`logger.info()`** - General informational messages about normal operation
  - Example: `logger.info("Successfully loaded configuration")`
  - Example: `logger.info(f"Detected {drift_count} drifts")`

- **`logger.warning()`** - Something unexpected but not critical happened
  - Example: `logger.warning("Column not found in profile, skipping")`
  - Example: `logger.warning("Using default threshold")`

- **`logger.error()`** - An error occurred, but the program can continue
  - Example: `logger.error(f"Failed to calculate metric: {e}")`
  - Example: `logger.error("Configuration validation failed")`

- **`logger.critical()`** - A critical error, program may not be able to continue
  - Example: `logger.critical("Database connection failed, cannot proceed")`

### Why this matters:

1. **Configurability**: Logging can be configured, print() cannot
2. **Filtering**: Can set different log levels for different modules
3. **Output control**: Logs can go to files, syslog, cloud services, etc.
4. **Structured logging**: Can add timestamps, module names, severity automatically
5. **Production ready**: Proper logging is essential for production systems
6. **Testing**: Logs can be captured and tested, prints cannot

### Implementation:

```python
import logging

# At the top of every module
logger = logging.getLogger(__name__)

# Then use throughout the file
logger.info("Module initialized")
```

### Exception: CLI output for users

The ONLY acceptable use of print() is in CLI tools (`cli.py`) for **direct user-facing output** that is not logging:
- Progress indicators
- Final results/summaries
- Formatted tables/reports

Even in CLI, errors should use `logger.error()` AND `sys.stderr`.

---

## Great Expectations Usage

**CRITICAL RULE: Great Expectations 1.x uses CLASS-BASED approach for building expectation suites.**

### GX 1.x API Pattern (Correct Approach)

In GX 1.x (1.10.0+), the official pattern is to:
1. Create ExpectationSuite objects directly
2. Instantiate Expectation classes
3. Add expectations to suite using `suite.add_expectation()`
4. Validate using validator with the suite

### ✅ Correct - Class-Based Approach (GX 1.x):
```python
import great_expectations as gx
from great_expectations.expectations import (
    ExpectColumnToExist,
    ExpectColumnMeanToBeBetween,
    ExpectColumnStdevToBeBetween
)

# Create expectation suite
suite = gx.ExpectationSuite(name="my_suite")

# Add expectations using class instantiation
suite.add_expectation(
    ExpectColumnToExist(column="age")
)

suite.add_expectation(
    ExpectColumnMeanToBeBetween(
        column="age",
        min_value=18,
        max_value=65
    )
)

suite.add_expectation(
    ExpectColumnStdevToBeBetween(
        column="age",
        min_value=1.0,
        max_value=10.0
    )
)

# Save suite to context
context = gx.get_context(mode="file")
context.suites.add(suite)

# Validate using the suite
datasource = context.data_sources.add_pandas("data_source")
asset = datasource.add_dataframe_asset(name="data")
batch_def = asset.add_batch_definition_whole_dataframe("batch")
batch_request = batch_def.build_batch_request({"dataframe": df})

validator = context.get_validator(
    batch_request=batch_request,
    expectation_suite_name="my_suite"
)

results = validator.validate()
```

**Why this is correct:**
- This is the official GX 1.x pattern per documentation
- Expectation classes are the public API in GX 1.x
- Type-safe and IDE-friendly
- Clear separation between suite building and validation

### ❌ Incorrect - Validator Methods (GX 0.x pattern):
```python
# This was the old GX 0.x pattern - DON'T USE in GX 1.x
validator = context.get_validator(
    batch_request=batch_request,
    create_expectation_suite_with_name="my_suite"
)

validator.expect_column_mean_to_be_between(
    column="age",
    min_value=18,
    max_value=65
)
```

**Why this is wrong for GX 1.x:**
- Validator methods are deprecated in GX 1.x
- Creates confusion between suite building and validation
- Not the documented pattern for GX 1.x
- May be removed in future versions

### Custom Expectations

**Implementing custom expectations:**
1. Create a class extending `ColumnExpectation`, `TableExpectation`, etc.
2. Implement required methods (`_validate`, metric dependencies, etc.)
3. Import and use like built-in expectations

**Example:**
```python
from great_expectations.expectations import ColumnExpectation

class ExpectColumnValuesToHaveDecimalPrecision(ColumnExpectation):
    """Custom expectation for decimal precision."""

    def _validate(self, metrics, precision, mostly=1.0):
        # Implementation here
        pass

# Usage (same as built-in expectations)
suite.add_expectation(
    ExpectColumnValuesToHaveDecimalPrecision(
        column="latitude",
        precision=6,
        mostly=0.99
    )
)
```

### Pattern Summary

| Use Case | GX 1.x Approach |
|----------|-----------------|
| Building expectation suites | ✅ Class instantiation + `suite.add_expectation()` |
| Validating data | ✅ `validator.validate()` with suite name |
| Custom expectations | ✅ Class-based (extend ColumnExpectation, etc.) |
| Saving suites | ✅ `context.suites.add(suite)` |

---

## Additional Guidelines

*(Add more rules as needed)*
