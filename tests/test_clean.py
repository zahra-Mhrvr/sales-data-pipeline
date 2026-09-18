import pandas as pd

from pipeline.clean import clean_sales_data


def make_raw_df(rows):
    """Helper — fills in sane defaults so each test only has to specify the
    field it actually cares about."""
    defaults = {
        "order_id": 1,
        "date": "2026-01-15",
        "product": "Widget",
        "category": "misc",
        "region": "north",
        "quantity": 2,
        "unit_price": "$10.00",
        "customer_email": "a@example.com",
    }
    full_rows = []
    for i, row in enumerate(rows):
        merged = {**defaults, **row, "order_id": row.get("order_id", 1000 + i)}
        full_rows.append(merged)
    return pd.DataFrame(full_rows)


def test_parses_multiple_date_formats():
    raw = make_raw_df([
        {"date": "2026-03-05"},
        {"date": "03/05/2026"},
        {"date": "05-03-2026"},
    ])
    clean = clean_sales_data(raw)
    assert clean["date"].nunique() == 1
    assert clean["date"].iloc[0] == pd.Timestamp("2026-03-05")


def test_strips_dollar_sign_from_price():
    raw = make_raw_df([{"unit_price": "$14.50"}, {"unit_price": "14.50"}])
    clean = clean_sales_data(raw)
    assert (clean["unit_price"] == 14.50).all()


def test_normalizes_region_casing():
    raw = make_raw_df([
        {"region": "north"}, {"region": "NORTH"}, {"region": "N."}, {"region": "North"},
    ])
    clean = clean_sales_data(raw)
    assert set(clean["region"].unique()) == {"North"}


def test_drops_exact_duplicate_order_ids():
    raw = make_raw_df([{"order_id": 5}, {"order_id": 5}, {"order_id": 6}])
    clean = clean_sales_data(raw)
    assert len(clean) == 2


def test_drops_negative_quantity_rows():
    raw = make_raw_df([{"quantity": 3}, {"quantity": -2}])
    clean = clean_sales_data(raw)
    assert (clean["quantity"] > 0).all()
    assert len(clean) == 1


def test_drops_rows_missing_required_fields():
    raw = make_raw_df([
        {"unit_price": None},
        {"quantity": None},
        {"quantity": 5, "unit_price": "$5.00"},
    ])
    clean = clean_sales_data(raw)
    assert len(clean) == 1


def test_revenue_is_price_times_quantity():
    raw = make_raw_df([{"unit_price": "$10.00", "quantity": 3}])
    clean = clean_sales_data(raw)
    assert clean["revenue"].iloc[0] == 30.0


def test_usb_c_is_not_mangled_by_title_case():
    raw = make_raw_df([{"product": "usb-c cable"}])
    clean = clean_sales_data(raw)
    assert clean["product"].iloc[0] == "USB-C Cable"
