"""Create a fictional sales dataset so the demo runs out of the box."""

from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
REGIONS = ["North", "South", "East", "West", "Center"]
PRODUCTS = ["Sensor Kit", "Control Unit", "Cable Set", "Power Supply", "Display Module"]
REPS = ["A. Diaz", "B. Rossi", "C. Nguyen", "D. Keller", "E. Moreau"]


def build() -> pd.DataFrame:
    n = 220
    dates = pd.to_datetime("2026-01-01") + pd.to_timedelta(RNG.integers(0, 240, n), unit="D")
    qty = RNG.integers(1, 25, n)
    unit_price = RNG.uniform(80, 1400, n).round(2)
    df = pd.DataFrame(
        {
            "Date": dates,
            "Region": RNG.choice(REGIONS, n),
            "Product": RNG.choice(PRODUCTS, n),
            "Sales Rep": RNG.choice(REPS, n),
            "Quantity": qty,
            "Unit Price": unit_price,
        }
    )
    df["Revenue"] = (df["Quantity"] * df["Unit Price"]).round(2)
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    return df.sort_values("Date").reset_index(drop=True)


if __name__ == "__main__":
    out = Path(__file__).with_name("sample_sales.xlsx")
    build().to_excel(out, index=False, sheet_name="Sales")
    print(f"Sample data written to {out}")
