"""Command-line interface for DriftWatch."""

import argparse
import logging
import sys
import time

import pandas as pd

from driftwatch.core.config import DriftWatchConfig
from driftwatch.core.expectation_suite_builder import ExpectationSuiteBuilder
from driftwatch.core.gx_context import DriftWatchGXContext
from driftwatch.core.validation_result_enricher import ValidationResultEnricher

logger = logging.getLogger(__name__)


def profile_command(args):
    """Handle 'profile' command - Generate GX Expectation Suite."""
    print("=" * 70)
    print("DRIFTWATCH - EXPECTATION SUITE GENERATION")
    print("=" * 70)

    try:
        # Load configuration
        logger.info(f"Loading configuration from: {args.config}")
        config = DriftWatchConfig(args.config)
        print(f"✓ Configuration loaded from: {args.config}")

        # Load reference dataset if provided
        ref_df = None
        if args.reference:
            logger.info(f"Loading reference dataset from: {args.reference}")
            print(f"\n✓ Loading reference dataset: {args.reference}")
            ref_df = pd.read_csv(args.reference)
            print(f"  Loaded {len(ref_df):,} rows, {len(ref_df.columns)} columns")
        else:
            logger.info("No reference dataset provided - schema check will fail if enabled")
            print("\n⚠ No reference dataset provided - schema check will fail if enabled")

        # Build GX expectation suite
        logger.info("Building GX expectation suite")
        print("\n✓ Building GX expectation suite...")
        context_manager = DriftWatchGXContext()
        context = context_manager.get_context()
        builder = ExpectationSuiteBuilder()

        suite_name = "delivery_data_reference_suite"
        suite = builder.build_suite(
            context=context,
            config=config,
            suite_name=suite_name,
            ref_df=ref_df
        )
        logger.info(
            f"Expectation suite generation complete: {len(suite.expectations)} expectations"
        )

        print(f"\n✓ Suite saved: gx/expectations/{suite_name}.json")
        print(f"  Total expectations: {len(suite.expectations)}")

        # Count schema expectations
        schema_count = sum(1 for e in suite.expectations
                          if 'ExpectColumnToExist' in str(type(e).__name__))
        if schema_count > 0:
            print(f"  - Schema expectations: {schema_count}")

        # Count column-level expectations
        column_count = len(suite.expectations) - schema_count
        if column_count > 0:
            print(f"  - Column-level expectations: {column_count}")

        print("\n" + "=" * 70)
        print("✓ EXPECTATION SUITE GENERATION COMPLETE")
        print("=" * 70)

    except Exception as e:
        logger.error(f"Expectation suite generation failed: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e!s}", file=sys.stderr)
        sys.exit(1)


def evaluate_command(args):
    """Handle 'evaluate' command - Run GX validation."""
    print("=" * 70)
    print("DRIFTWATCH - DRIFT EVALUATION (GX)")
    print("=" * 70)

    start_time = time.time()

    try:
        # Import custom expectations BEFORE loading suite
        # GX needs them registered to deserialize the suite
        import driftwatch.expectations  # noqa: F401
        import great_expectations as gx

        # Initialize GX context
        logger.info("Loading GX context and expectation suite")
        print("\n✓ Loading GX expectation suite...")
        context_manager = DriftWatchGXContext()
        context = context_manager.get_context()

        # Get expectation suite (default name from profile command)
        suite_name = "delivery_data_reference_suite"
        try:
            suite = context.suites.get(suite_name)
            print(f"  Suite: {suite_name}")
            print(f"  Expectations: {len(suite.expectations)}")
        except Exception as e:
            logger.error(f"Failed to load expectation suite '{suite_name}': {e}")
            print(f"\n❌ ERROR: Expectation suite '{suite_name}' not found.", file=sys.stderr)
            print("   Run 'driftwatch profile' first to generate the suite.", file=sys.stderr)
            sys.exit(1)

        # Load new dataset
        logger.info(f"Loading new dataset from: {args.new}")
        print(f"\n✓ Loading new dataset: {args.new}")
        new_df = pd.read_csv(args.new)
        print(f"  Loaded {len(new_df):,} rows, {len(new_df.columns)} columns")

        # Create validation using Checkpoint (proper GX 1.x approach)
        logger.info("Setting up GX Checkpoint for validation")
        print("\n✓ Running GX validation via Checkpoint...")

        # 1. Setup Datasource and Asset
        import uuid
        datasource_name = f"evaluation_{uuid.uuid4().hex[:8]}"
        datasource = context.data_sources.add_pandas(datasource_name)
        asset = datasource.add_dataframe_asset(name="new_data")
        batch_def = asset.add_batch_definition_whole_dataframe("batch")

        # 2. Create a Validation Definition
        # This ties the Batch Definition to the Expectation Suite
        validation_def_name = f"val_def_{uuid.uuid4().hex[:8]}"
        validation_definition = context.validation_definitions.add(
            gx.ValidationDefinition(
                name=validation_def_name,
                data=batch_def,
                suite=suite
            )
        )

        # 3. Create and configure Checkpoint with actions
        # Validation results are stored automatically
        # We only need UpdateDataDocsAction to rebuild HTML
        checkpoint_name = f"checkpoint_{uuid.uuid4().hex[:8]}"
        checkpoint = context.checkpoints.add(
            gx.Checkpoint(
                name=checkpoint_name,
                validation_definitions=[validation_definition],
                actions=[
                    # Rebuild HTML Data Docs to include new validation results
                    gx.checkpoint.actions.UpdateDataDocsAction(
                        name="update_data_docs"
                    ),
                ],
            )
        )

        # 4. Run the Checkpoint with the dataframe
        logger.info("Running checkpoint to validate data and persist results")
        run_name = f"drift_eval_{time.strftime('%Y%m%d_%H%M%S')}"

        from great_expectations.core import RunIdentifier
        run_id = RunIdentifier(run_name=run_name)

        checkpoint_result = checkpoint.run(
            batch_parameters={"dataframe": new_df},
            run_id=run_id
        )

        # Extract validation result from checkpoint result
        # checkpoint_result.run_results is a dict with one entry
        validation_result_id, validation_result = list(
            checkpoint_result.run_results.items()
        )[0]

        # Enrich with DriftWatch metadata
        duration = time.time() - start_time
        enricher = ValidationResultEnricher()
        validation_result = enricher.enrich_result(
            validation_result,
            config_file=None,  # Config not needed during evaluation
            duration_seconds=duration
        )

        logger.info(f"Validation complete with run_name: {run_name}")

        # Extract metrics
        total_drifts = sum(1 for r in validation_result.results if not r.success)
        driftwatch_meta = enricher.get_enriched_metadata(validation_result)
        overall_severity = driftwatch_meta.get('severity', 'UNKNOWN')

        logger.info(
            f"Validation complete: {total_drifts} drift(s) found, severity={overall_severity}"
        )
        print(f"\n✓ Validation complete - {total_drifts} drift(s) detected")
        print(f"  Severity: {overall_severity}")
        print(f"  Run name: {run_name}")

        # Build Data Docs (GX HTML reports)
        logger.info("Building Data Docs")
        try:
            context.build_data_docs()
            logger.info("Data Docs built successfully")
            print("\n✓ Data Docs generated:")
            print("  Location: gx/uncommitted/data_docs/local_site/")
            print("  Index: gx/uncommitted/data_docs/local_site/index.html")
        except Exception as e:
            logger.warning(f"Failed to build Data Docs: {e}")
            print("  Note: Data Docs generation skipped (no validation results stored)")

        # Validation results info
        print("\n✓ Validation metadata:")
        print(f"  Run ID: {run_name}")
        print("  Storage: gx/uncommitted/validations/")

        # Show summary of failed expectations
        if total_drifts > 0:
            print(f"\n  Failed expectations ({total_drifts}):")
            for result in validation_result.results:
                if not result.success:
                    exp_type = result.expectation_config.type
                    column = result.expectation_config.kwargs.get('column', 'N/A')
                    print(f"    - {exp_type} (column: {column})")

        # Duration tracking
        duration = time.time() - start_time

        logger.info(
            f"Evaluation complete: severity={overall_severity}, "
            f"drifts={total_drifts}, duration={duration:.2f}s"
        )
        print("\n" + "=" * 70)
        print("✓ EVALUATION COMPLETE")
        print("=" * 70)
        print(f"  Severity: {overall_severity}")
        print(f"  Drifts: {total_drifts}")
        print(f"  Duration: {duration:.2f}s")
        print("=" * 70)

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e!s}", file=sys.stderr)
        sys.exit(1)


def list_expectations_command(args):
    """Handle 'list-expectations' command - Show all available expectations."""
    from driftwatch.core.expectation_registry import get_registry

    print("=" * 70)
    print("DRIFTWATCH - AVAILABLE EXPECTATIONS")
    print("=" * 70)

    registry = get_registry()
    expectations = registry.list_available()

    # Group by type
    builtin = [e for e in expectations
               if not e.startswith('ExpectColumnValuesToHave')
               and not e.startswith('ExpectColumnCategories')]
    custom = [e for e in expectations if e not in builtin]

    print(f"\nBuilt-in GX Expectations ({len(builtin)}):")
    for exp in builtin:
        info = registry.get_expectation_info(exp)
        params = info.get('parameters', [])
        if params:
            param_names = ', '.join([p['name'] for p in params])
            print(f"  - {exp}")
            print(f"    Parameters: {param_names}")
        else:
            print(f"  - {exp}")

    print(f"\nCustom DriftWatch Expectations ({len(custom)}):")
    for exp in custom:
        info = registry.get_expectation_info(exp)
        params = info.get('parameters', [])
        if params:
            param_names = ', '.join([p['name'] for p in params])
            print(f"  - {exp}")
            print(f"    Parameters: {param_names}")
        else:
            print(f"  - {exp}")

    print(f"\nTotal: {len(expectations)} expectations available")
    print("\nExample usage in config:")
    print("  expectations:")
    print("    - column: my_column")
    print("      expectation: ExpectColumnMaxToBeBetween")
    print("      values:")
    print("        min_value: 1.0")
    print("        max_value: 5.0")
    print("")
    print("    - column: my_category")
    print("      expectation: ExpectColumnValuesToBeInSet")
    print("      values:")
    print("        value_set: [\"A\", \"B\", \"C\"]")
    print("=" * 70)


def main():
    """Main CLI entry point."""
    # Setup logging early
    from driftwatch.utils.logging_config import setup_logging
    setup_logging(level="INFO")

    parser = argparse.ArgumentParser(
        description="DriftWatch - Automated Data Drift Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Profile command
    profile_parser = subparsers.add_parser(
        'profile',
        help='Generate GX expectation suite from config'
    )
    profile_parser.add_argument(
        '--reference',
        required=False,
        help='Path to reference dataset (CSV) - required for schema check'
    )
    profile_parser.add_argument(
        '--config',
        default='driftwatch_config.yaml',
        help='Path to configuration file (default: driftwatch_config.yaml)'
    )

    # Evaluate command
    evaluate_parser = subparsers.add_parser(
        'evaluate',
        help='Validate new dataset against GX expectation suite'
    )
    evaluate_parser.add_argument(
        '--new',
        required=True,
        help='Path to new dataset to evaluate (CSV)'
    )

    # List expectations command
    subparsers.add_parser(
        'list-expectations',
        help='List all available expectation classes'
    )

    args = parser.parse_args()

    if args.command == 'profile':
        profile_command(args)
    elif args.command == 'evaluate':
        evaluate_command(args)
    elif args.command == 'list-expectations':
        list_expectations_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
