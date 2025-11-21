import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, time

# ---------------- USER INPUTS -------------------
START_DATE = "2025-11-14"
END_DATE   = "2025-11-19"
TICKER     = "SBIN.NS" #which stock (SBIN.NS)

ENTRY_TIME = "09:30"      # HH:MM when buy happens
EXIT_TIME  = "15:00"      # HH:MM  when sell happens
PRICE_ON   = "close"      # open / close
QTY        = 1 #shares per trade
OUTPUT_CSV = "intraday_results_sbin.csv"
# -------------------------------------------------

# Convert time string → time object
def parse_time(t):
    h, m = map(int, t.split(":"))
    return time(h, m)

entry_t = parse_time(ENTRY_TIME)
exit_t  = parse_time(EXIT_TIME)

# yfinance needs end+1 day to include last date
start = pd.to_datetime(START_DATE)
end   = pd.to_datetime(END_DATE) + pd.Timedelta(days=1)

print("Downloading data...")
df = yf.download(
    TICKER,
    start=start.strftime("%Y-%m-%d"),
    end=end.strftime("%Y-%m-%d"),
    interval="1m",
    progress=False
)

if df.empty:
    print("No data downloaded. 1m data only available for last ~7 days.")
    exit()

# clean columns
df = df.rename(columns={"Open":"open","Close":"close"})
df["date"] = df.index.date #Add column "date"
df.index = df.index.tz_localize(None) #Remove timezone so comparison becomes easier.

# function → get price at specific time
def get_price(rows, ts, field):
    """tries exact → next minute → last available"""
    if ts in rows.index:
        return rows.loc[ts, field]

    later = rows[rows.index >= ts]
    if not later.empty:
        return later.iloc[0][field]

    return rows.iloc[-1][field]

results = []
current = start.date()
end_date = pd.to_datetime(END_DATE).date()

while current <= end_date:
    today = df[df["date"] == current]

    if today.empty:
        results.append([current, None, None, None, None, "no data"])
    else:
        entry_ts = datetime.combine(current, entry_t)
        exit_ts  = datetime.combine(current, exit_t)

        entry_price = get_price(today, entry_ts, PRICE_ON)
        exit_price  = get_price(today, exit_ts, PRICE_ON)

        pnl_per_share = exit_price - entry_price
        pnl_total = pnl_per_share * QTY

        results.append([
            current,
            float(entry_price),
            float(exit_price),
            float(pnl_per_share),
            float(pnl_total),
            ""
        ])

    current += timedelta(days=1)

# make dataframe
res = pd.DataFrame(results, columns=[
    "date", "entry_price", "exit_price",
    "pnl_per_share", "pnl_total", "note"
])

print("\n--- RESULTS ---")
print(res.to_string(index=False))

print(f"\nTotal P/L: {res['pnl_total'].dropna().sum()}  (Qty={QTY})")

res.to_csv(OUTPUT_CSV, index=False)
print("\nCSV saved:", OUTPUT_CSV)
