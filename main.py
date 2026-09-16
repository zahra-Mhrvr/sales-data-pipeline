"""
Usage:
    python main.py --input data/raw/sales_2026_q1.csv --output output/
"""

import argparse
import pandas as pd

from pipeline.clean import clean_sales_data
from pipeline.report import generate_report


def main():
    parser = argparse.ArgumentParser(description="Clean sales data and generate a report.")
    parser.add_argument("--input", default="data/raw/sales_2026_q1.csv", help="Path to raw CSV")
    parser.add_argument("--output", default="output", help="Directory for the report")
    parser.add_argument(
        "--save-clean",
        default=None,
        help="Optional path to also save the cleaned CSV (e.g. data/processed/clean.csv)",
    )
    args = parser.parse_args()

    print(f"reading {args.input}...")
    raw_df = pd.read_csv(args.input)
    print(f"  {len(raw_df)} raw rows")

    clean_df = clean_sales_data(raw_df)
    dropped = len(raw_df) - len(clean_df)
    print(f"  {len(clean_df)} rows after cleaning ({dropped} dropped: dupes/missing/invalid)")

    if args.save_clean:
        clean_df.to_csv(args.save_clean, index=False)
        print(f"  saved cleaned data to {args.save_clean}")

    summary = generate_report(clean_df, args.output)
    print(f"\ntotal revenue: ${summary['total_revenue']:,.2f}")
    print(f"total orders: {summary['total_orders']}")
    print(f"report saved to {args.output}/")


if __name__ == "__main__":
    main()
