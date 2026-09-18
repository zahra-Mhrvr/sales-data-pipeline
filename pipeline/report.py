"""
Turns the cleaned dataframe into the numbers and charts I actually care
about: revenue by category, the monthly trend, and top products.
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # no display in this environment, just save to file
import matplotlib.pyplot as plt
import pandas as pd


def revenue_by_category(df: pd.DataFrame) -> pd.Series:
    return df.groupby("category")["revenue"].sum().sort_values(ascending=False)


def revenue_by_month(df: pd.DataFrame) -> pd.Series:
    monthly = df.copy()
    monthly["month"] = monthly["date"].dt.to_period("M")
    return monthly.groupby("month")["revenue"].sum().sort_index()


def top_products(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    grouped = (
        df.groupby("product")
        .agg(units_sold=("quantity", "sum"), revenue=("revenue", "sum"))
        .sort_values("revenue", ascending=False)
    )
    return grouped.head(n)


def revenue_by_region(df: pd.DataFrame) -> pd.Series:
    return df.groupby("region")["revenue"].sum().sort_values(ascending=False)


def build_summary(df: pd.DataFrame) -> dict:
    by_category = revenue_by_category(df)
    by_month = revenue_by_month(df)
    top = top_products(df)

    return {
        "total_revenue": round(df["revenue"].sum(), 2),
        "total_orders": int(len(df)),
        "date_range": {
            "start": df["date"].min().strftime("%Y-%m-%d"),
            "end": df["date"].max().strftime("%Y-%m-%d"),
        },
        "revenue_by_category": {k: round(v, 2) for k, v in by_category.items()},
        "revenue_by_month": {str(k): round(v, 2) for k, v in by_month.items()},
        "top_products": top.reset_index().to_dict(orient="records"),
    }


def save_summary_json(summary: dict, path: str | Path) -> None:
    Path(path).write_text(json.dumps(summary, indent=2))


def plot_revenue_by_category(df: pd.DataFrame, path: str | Path) -> None:
    data = revenue_by_category(df)
    fig, ax = plt.subplots(figsize=(8, 5))
    data.plot(kind="bar", ax=ax, color="#4c78a8")
    ax.set_ylabel("Revenue ($)")
    ax.set_title("Revenue by Category")
    ax.set_xlabel("")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_monthly_trend(df: pd.DataFrame, path: str | Path) -> None:
    data = revenue_by_month(df)
    fig, ax = plt.subplots(figsize=(8, 5))
    data.plot(kind="line", marker="o", ax=ax, color="#e45756")
    ax.set_ylabel("Revenue ($)")
    ax.set_title("Monthly Revenue Trend")
    ax.set_xlabel("Month")
    plt.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def generate_report(df: pd.DataFrame, output_dir: str | Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = build_summary(df)
    save_summary_json(summary, output_dir / "summary.json")
    plot_revenue_by_category(df, output_dir / "revenue_by_category.png")
    plot_monthly_trend(df, output_dir / "monthly_trend.png")

    return summary
