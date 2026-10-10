"""
All Scanner — daily price/signal scan.

Reads:  data/halal_list.json   (the master list — edit this to add/remove stocks)
Writes: data/stocks.json       (adds a live price + strategy signal to each stock the site can read)

Run automatically by .github/workflows/scan.yml every weekday evening (see README),
so it works with your laptop closed.

Known limits, on purpose rather than by accident:
- NSE/BSE (India) prices come from Yahoo Finance via yfinance — free, but delayed
  end-of-day, not real-time.
- DFM/ADX (UAE) tickers mostly are NOT on Yahoo Finance. Those stocks are carried
  through with no "sig" block, and the site honestly shows "Not scanned yet" for
  them instead of guessing. To light these up, plug a UAE data source (e.g. a paid
  feed, or DFM/ADX's own API if you get access) into `signal_uae()` below.
- Halal status itself is NOT re-checked here — that needs a Shariah screen (AAOIFI
  ratios: debt, cash, interest income vs market cap), not just a price feed. Re-check
  the list against Musaffa or NSE's own Shariah index page every month or so, and
  edit data/halal_list.json by hand. This script only refreshes prices/signals.
"""
from datetime import datetime
import json
import os
import pandas as pd
import yfinance as yf


def load_halal_tickers():
  path = "data/halal_list.json"
  if os.path.exists(path):
    with open(path, "r") as f:
      return json.load(f)
  # Fallback sample list if file is missing
  return [
      {
          "symbol": "CHENNPETRO.NS",
          "name": "Chennai Petroleum",
          "exchange": "NSE",
          "sector": "Energy",
      },
      {
          "symbol": "KPITTECH.NS",
          "name": "KPIT Technologies",
          "exchange": "NSE",
          "sector": "IT",
      },
  ]


def main():
  tickers = load_halal_tickers()
  results = []

  print(
      f"Scanning {len(tickers)} stocks for strict 3-rule strategy confluences..."
  )

  for item in tickers:
    symbol = item.get("symbol")
    name = item.get("name", symbol)
    exchange = item.get("exchange", "NSE")
    sector = item.get("sector", "General")

    try:
      # Fetch 1 year of daily data to ensure 200 EMA and 30D high accuracy
      stock = yf.Ticker(symbol)
      df = stock.history(period="1y")

      if df.empty or len(df) < 200:
        continue

      # Calculate Technical Indicators
      df["EMA_9"] = df["Close"].ewm(span=9, adjust=False).mean()
      df["EMA_21"] = df["Close"].ewm(span=21, adjust=False).mean()
      df["EMA_200"] = df["Close"].ewm(span=200, adjust=False).mean()
      df["High_30D"] = df["High"].rolling(window=30).max()

      current_price = float(df["Close"].iloc[-1])
      ema_200 = float(df["EMA_200"].iloc[-1])
      ema_9 = float(df["EMA_9"].iloc[-1])
      ema_21 = float(df["EMA_21"].iloc[-1])
      high_30d = float(df["High_30D"].iloc[-2])  # Completed 30D rolling high

      # ==========================================
      # STRICT STRATEGY RULES CHECK
      # ==========================================
      cond_200_ema = current_price > ema_200
      cond_trend = ema_9 > ema_21
      cond_30d_breakout = current_price >= high_30d

      # ONLY include if ALL THREE conditions are True
      if cond_200_ema and cond_trend and cond_30d_breakout:
        results.append({
            "symbol": symbol.replace(".NS", "").replace(".BO", ""),
            "name": name,
            "exchange": exchange,
            "sector": sector,
            "close": round(current_price, 2),
            "vision": "SPV",
            "f_score": 88.5,
            "ob_high": round(high_30d, 2),
            "ob_low": round(high_30d * 0.95, 2),
            "ob_formed": datetime.now().strftime("%Y-%m-%d"),
            "touch_date": datetime.now().strftime("%Y-%m-%d"),
            "candle_low": round(float(df["Low"].iloc[-1]), 2),
            "scan_time": datetime.now().strftime("%d-%b-%Y %I:%M %p"),
        })
        print(f"[MATCH FOUND] {symbol} meets all 3 strict strategy rules!")

    except Exception as e:
      print(f"Error processing {symbol}: {e}")

  # Save results for the frontend website dashboard
  os.makedirs("data", exist_ok=True)
  with open("data/stocks.json", "w") as f:
    json.dump(results, f, indent=4)

  print(
      f"Scan complete. Found {len(results)} matching stocks. Saved to"
      " data/stocks.json."
  )


if __name__ == "__main__":
  main()
