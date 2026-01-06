import argparse
import json
from pathlib import Path
from typing import Optional

import pandas as pd

# Attempt to import tabulate for nicer tables; fallback if not available
try:
    import tabulate  # type: ignore

    HAS_TABULATE = True
except ImportError:
    # If tabulate is not installed, pandas uses a simpler text format, or we can use to_string()
    HAS_TABULATE = False


def load_run_data(logdir: Path, exclude_suites: list[str] | None = None) -> pd.DataFrame:
    """
    Loads run data from the directory structure:
    logdir / config_name / model_name / suite_name / user_task_id / attack_name / injection_task_id.json
    """
    if exclude_suites is None:
        exclude_suites = ["travel"]

    records = []

    if not logdir.exists():
        print(f"Error: Log directory '{logdir}' does not exist.")
        return pd.DataFrame()

    print(f"Scanning {logdir}...")

    # Level 1: Configuration (e.g., config_1)
    for config_dir in logdir.iterdir():
        if not config_dir.is_dir() or config_dir.name.startswith("__"):
            continue
        config_name = config_dir.name

        # Level 2: Model (e.g., gpt-4o)
        for model_dir in config_dir.iterdir():
            if not model_dir.is_dir():
                continue
            model_name = model_dir.name

            # Level 3: Suite (e.g., banking, slack)
            for suite_dir in model_dir.iterdir():
                if not suite_dir.is_dir():
                    continue
                suite_name = suite_dir.name

                if suite_name in exclude_suites:
                    continue

                # Level 4: User Task (e.g., 1, 2, 3...)
                for task_dir in suite_dir.iterdir():
                    if not task_dir.is_dir():
                        continue
                    user_task_id = task_dir.name

                    # We are looking for base performance results: attack="none", injection="none"
                    result_file = task_dir / "none" / "none.json"

                    if not result_file.exists():
                        continue

                    try:
                        with open(result_file, encoding="utf-8") as f:
                            data = json.load(f)

                        usage = data.get("usage") or {}
                        # Handle potential Nones in usage
                        if not usage:
                            usage = {}

                        records.append(
                            {
                                "configuration": config_name,
                                "model": model_name,
                                "suite": suite_name,
                                "task_id": user_task_id,
                                "utility": float(data.get("utility", 0.0)),
                                "duration": float(data.get("duration", 0.0)),
                                "prompt_tokens": int(usage.get("prompt_tokens", 0)),
                                "completion_tokens": int(usage.get("completion_tokens", 0)),
                                "total_tokens": int(usage.get("total_tokens", 0)),
                            }
                        )
                    except Exception:
                        # minimal error logging to avoid clutter
                        pass

    return pd.DataFrame(records)


def print_summary(df: pd.DataFrame):
    if df.empty:
        print("No run data found in the specified directory.")
        return

    # 1. Overall Summary by Configuration
    # Aggregating across all suites and tasks
    grouped_config = df.groupby(["configuration", "model"]).agg(
        {"utility": "mean", "duration": "mean", "total_tokens": "mean", "task_id": "count"}
    )

    grouped_config.columns = ["Avg Utility", "Avg Duration (s)", "Avg Total Tokens", "Count"]
    # Reorder
    grouped_config = grouped_config[["Count", "Avg Utility", "Avg Duration (s)", "Avg Total Tokens"]]

    print("\n" + "=" * 80)
    print(" OVERALL SUMMARY (By Configuration & Model)")
    print("=" * 80)
    if HAS_TABULATE:
        # Check if to_markdown is available on the dataframe (requires tabulate installed)
        try:
            print(grouped_config.to_markdown(floatfmt=".4f"))
        except ImportError:
            print(grouped_config.to_string(float_format="{:.4f}".format))
    else:
        print(grouped_config.to_string(float_format="{:.4f}".format))
    print("\n")

    # 2. Breakdown by Suite
    grouped_suite = df.groupby(["configuration", "suite"]).agg(
        {"utility": "mean", "duration": "mean", "total_tokens": "mean", "task_id": "count"}
    )
    grouped_suite.columns = ["Avg Utility", "Avg Duration", "Avg Tokens", "Count"]

    print("\n" + "=" * 80)
    print(" BREAKDOWN BY SUITE")
    print("=" * 80)
    if HAS_TABULATE:
        try:
            print(grouped_suite.to_markdown(floatfmt=".4f"))
        except ImportError:
            print(grouped_suite.to_string(float_format="{:.4f}".format))
    else:
        print(grouped_suite.to_string(float_format="{:.4f}".format))
    print("\n")


def main():
    parser = argparse.ArgumentParser(description="Analyze AgentDojo benchmark runs.")
    parser.add_argument("--logdir", type=str, default="all_runs", help="Directory containing run logs.")
    parser.add_argument("--csv-output", type=str, help="Optional path to save dataset as CSV.")

    args = parser.parse_args()
    logdir = Path(args.logdir)

    df = load_run_data(logdir)

    if args.csv_output:
        df.to_csv(args.csv_output, index=False)
        print(f"Full dataset saved to {args.csv_output}")

    print_summary(df)


if __name__ == "__main__":
    main()
