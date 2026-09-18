"""
Cleaning steps for the raw sales export.

The raw file comes out of the ops team's system looking rough: dates in
three different formats, prices sometimes with a $ sign, region names typed
in whatever case someone felt like, a handful of duplicate rows from
double-clicked submissions, and occasional missing values.

Each function here handles one specific mess so it's obvious what's going
on and easy to test in isolation.
"""

import pandas as pd


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """The date column shows up as YYYY-MM-DD, MM/DD/YYYY, or DD-MM-YYYY
    depending on which report it came from. pandas can't guess a mixed
    column reliably, so we try each format in turn."""
    df = df.copy()

    def _parse_one(value):
        if pd.isna(value):
            return pd.NaT
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"):
            try:
                return pd.to_datetime(value, format=fmt)
            except ValueError:
                continue
        return pd.NaT

    df["date"] = df["date"].apply(_parse_one)
    return df


def clean_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Strip the $ sign (when it's there) and make sure unit_price is numeric."""
    df = df.copy()
    df["unit_price"] = (
        df["unit_price"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.strip()
    )
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    return df


def normalize_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Region shows up as 'North', 'north', 'NORTH', even 'N.' — title-case
    everything and fix the abbreviation. Product names occasionally come
    through in all caps from one of the source systems."""
    df = df.copy()

    region_fixes = {"n.": "north"}
    df["region"] = (
        df["region"]
        .astype(str)
        .str.strip()
        .str.lower()
        .replace(region_fixes)
        .str.title()
    )
    df.loc[df["region"] == "Nan", "region"] = pd.NA

    df["product"] = df["product"].astype(str).str.strip().str.title()
    # .title() turns "USB-C Cable" into "Usb-C Cable", which looks like a typo
    # in every report it ends up in. Patch known acronyms back up.
    df["product"] = df["product"].str.replace("Usb-C", "USB-C", regex=False)
    df["product"] = df["product"].str.replace("12Pk", "12pk", regex=False)
    df["category"] = df["category"].astype(str).str.strip().str.title()

    return df


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """order_id should be unique — if the same order_id + full row shows up
    twice, it's a double submission, not two separate orders."""
    return df.drop_duplicates(subset="order_id", keep="first").copy()


def handle_missing_and_invalid(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows we can't trust: missing price/quantity/date (can't compute
    revenue without them), and negative quantities (data entry errors, not
    real returns — those go through a separate returns process)."""
    df = df.copy()
    df = df.dropna(subset=["unit_price", "quantity", "date"])
    df = df[df["quantity"] > 0]
    return df


def add_revenue_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["revenue"] = df["unit_price"] * df["quantity"]
    return df


def clean_sales_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Run the full cleaning pipeline in order. Order matters here — prices
    need to be numeric before we can drop invalid rows, dates need parsing
    before we can filter on them, etc."""
    df = raw_df.copy()
    df = parse_dates(df)
    df = clean_prices(df)
    df = normalize_text_columns(df)
    df = drop_duplicates(df)
    df = handle_missing_and_invalid(df)
    df = add_revenue_column(df)
    return df.reset_index(drop=True)
