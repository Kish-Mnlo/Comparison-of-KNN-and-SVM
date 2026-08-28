import pandas as pd

# Load original CSV
df = pd.read_csv("psei_real.csv")

# Rename columns to match features3.py
df.rename(columns={
    "Price": "Close",
    "Vol.": "Volume"
}, inplace=True)

# Convert price columns
price_columns = ["Close", "Open", "High", "Low"]

for col in price_columns:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .astype(float)
    )

    # Convert Volume
def convert_volume(value):
    value = str(value).replace(",", "").strip()

    if value.endswith("K"):
        return float(value[:-1]) * 1_000
    elif value.endswith("M"):
        return float(value[:-1]) * 1_000_000
    else:
        return float(value)

df["Volume"] = df["Volume"].apply(convert_volume)

# Convert Date to datetime
df["Date"] = pd.to_datetime(df["Date"])

# Sort chronologically: 2016 → 2025
df = df.sort_values("Date", ascending=True)

# Save the cleaned and sorted CSV
df.to_csv("psei_real_sorted.csv", index=False)

print("CSV successfully prepared.")
print("\nColumns:")
print(df.columns.tolist())

print("\nFirst 5 rows:")
print(df.head())

print("\nLast 5 rows:")
print(df.tail())