# Case Study: Automated Data Drift & Quality Monitoring Framework

## Objective

Design and build a Python-based framework that automatically analyzes incoming monthly data
batches to detect and report on schema changes and statistical data drift. The framework must be
extensible, allowing new detection rules to be easily added in the future.

## Background

Our platform ingests data from numerous clients, often in the form of Excel/CSV files or direct database exports. We typically define a target schema, but in the real world, the data quality and structure can vary significantly from one month to the next. These variations, or "drifts," can break our data processing pipelines and invalidate our machine learning models. We need a robust, automated system to catch these issues at the source.

Your task is to build a service that takes a "reference" dataset (representing the expected state) and a "new" monthly dataset as input. The service should then compare the two and generate a clear, structured report detailing any significant differences found.

## Core Requirements

### 1. Framework Design

- Create a modular Python project that can be executed from the command line.
- The design should clearly separate the logic for different types of drift detection, making it straightforward for another engineer to add new checks.

### 2. Schema Drift Detection

Implement logic to detect, flag, and quantify the following schema changes:

- **Column Addition/Removal**: Identify which columns have been added or removed in the new dataset compared to the reference.
- **Column Type Change**: Identify columns whose data type has changed (e.g., from `integer` to `string`).

### 3. Data Drift Detection

As part of this case study, you must research and implement at least two of the following
types of data drift. You should be prepared to justify your choice of statistical tests and
thresholds.:

- **Categorical Distribution Drift**: Detect a significant change in the frequency distribution of a key categorical column (e.g., a "Status" column that was previously 90% "Active" is now only 50% "Active").
- **Numerical Distribution Drift**: Detect a significant shift in a numerical column's statistical properties, such as its mean, standard deviation, or overall distribution (e.g., the mean of "Transaction Amount" has shifted by 3 standard deviations).
- **Null Value Drift**: Detect a significant increase or decrease in the percentage of null or missing values within a column.
- **String Pattern Drift**: For a column containing structured strings (e.g., Order IDs like `ORD-2023-XXXX`), detect if the format or pattern of the strings has changed.

### 4. Reporting

- The output of the analysis should be a structured report (e.g., JSON or a well-formatted text/markdown file).
- The report must be human-readable and clearly list every drift that was detected, providing relevant metrics to quantify its severity.

## Technology & Frameworks

The solution must be in Python. To solve this problem, you will need to compare two datasets and check for differences. We recommend using a dedicated data validation framework like **Great Expectations**, as it is purpose-built for this type of task and represents a modern industry standard.

However, you are free to use other libraries (e.g., `pandera`) or build a solution from scratch (e.g., using `pandas`, `scipy`) if you believe it is a better approach. If you choose not to use Great Expectations, please be prepared to justify your architectural decisions in your documentation.

## Deliverables

1. **Source Code**: All source code in a well-organized Python project.
2. **Sample Data**: Include sample data files (`reference_data.csv`, `new_data_with_drift.csv`, etc.) that you used to test your solution and demonstrate its functionality.
3. **Documentation (README.md)**: Your project must include a `README.md` file that explains:
   - A brief overview of your design and architecture.
   - The types of drift you chose to implement and a justification for your methodology and choice of statistical tests.
   - Clear, step-by-step instructions on how to set up the project and run your analysis.
   - A short guide explaining how another developer would add a new drift detection rule to your framework.
4. **AI-generated test cases** for testing end-to-end functionality.

## Evaluation Criteria

- **Problem Solving & Design**: The quality and extensibility of your framework design.
- **Correctness & Robustness**: The accuracy of your drift detection logic and how well it handles edge cases.
- **Research & Justification**: Your ability to research, select, and justify appropriate statistical methods for drift detection.
- **Code Quality & Clarity**: The readability, organization, and documentation of your code.
- **Communication**: The clarity and completeness of your `README.md` file.

Good luck!
