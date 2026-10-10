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
  return []


def main():
  tickers = load_halal_tickers()
  results = []

  print(
      f"Scanning {len(tickers)} stocks for strict 3-rule strategy confluences..."
  )

  for item in tickers:
    # Safely handle whether item is a dict, list, or string
    if isinstance(item, dict):
      symbol = item.get("symbol")
      name = item.get("name", symbol)
      exchange = item.get("exchange", "NSE")
      sector = item.get("sector", "General")
    elif isinstance(item, (list, tuple)):
      symbol = item[0] if len(item) > 0 else None
      name = item[1] if len(item) > 1 else symbol
      exchange = item[2] if len(item) > 2 else "NSE"
      sector = item[3] if len(item) > 3 else "General"
    elif isinstance(item, str):
      symbol = item
      name = item
      exchange = "NSE"
      sector = "General"
    else:
      continue

    if not symbol:
      continue

    try:
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
      high_30d = float(df["High_30D"].iloc[-2])

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

  os.makedirs("data", exist_ok=True)
  with open("data/stocks.json", "w") as f:
    json.dump(results, f, indent=4)

  print(
      f"Scan complete. Found {len(results)} matching stocks. Saved to"
      " data/stocks.json."
  )


if __name__ == "__main__":
  main()
