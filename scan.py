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
import json, sys, datetime
import yfinance as yf

SRC = "data/halal_list.json"
OUT = "data/stocks.json"

SUFFIX = {"NSE": ".NS", "BSE": ".BO"}


def ema(vals, span):
    k = 2 / (span + 1)
    e = vals[0]
    out = [e]
    for v in vals[1:]:
        e = v * k + e * (1 - k)
        out.append(e)
    return out


def order_block(highs, lows):
    """Crude swing-based order block: the lowest low in the last 20 sessions,
    plus the high of the bounce that followed it."""
    n = len(lows)
    if n < 20:
        return None
    window = range(n - 20, n)
    lo_i = min(window, key=lambda i: lows[i])
    hi = max(highs[lo_i:min(lo_i + 5, n)])
    return {"lo": round(lows[lo_i], 2), "hi": round(hi, 2)}


def signal(yf_symbol):
    t = yf.Ticker(yf_symbol)
    h = t.history(period="13mo", interval="1d", auto_adjust=True)
    if h.empty or len(h) < 60:
        return None
    closes = h["Close"].tolist()
    highs, lows, vols = h["High"].tolist(), h["Low"].tolist(), h["Volume"].tolist()
    c, prev = closes[-1], closes[-2]

    e200 = ema(closes, 200)[-1] if len(closes) >= 200 else None
    e9, e20 = ema(closes, 9)[-1], ema(closes, 20)[-1]
    avgvol = (sum(vols[-25:-5]) / 20) if len(vols) >= 25 else (sum(vols) / len(vols))
    volnow = sum(vols[-5:]) / 5
    hi52 = max(closes[-252:]) if len(closes) >= 252 else max(closes)
    ob = order_block(highs, lows)

    above200 = bool(e200 and c > e200)
    trend = bool(e9 > e20)
    vsurge = bool(avgvol and volnow > 2 * avgvol)
    near_ob = bool(ob and ob["lo"] * 0.98 <= c <= ob["hi"] * 1.02)
    dist_hi = (1 - abs(hi52 - c) / hi52) if hi52 else 0

    score = round(100 * (0.30 * above200 + 0.25 * trend + 0.20 * near_ob
                          + 0.15 * vsurge + 0.10 * max(0, dist_hi)), 1)
    tier = None
    if above200 and trend and near_ob:
        tier = "SPV" if (score >= 70 and vsurge) else "PV"

    return {
        "c": round(c, 2),
        "p": round((c - prev) / prev * 100, 2) if prev else 0,
        "sp": [round(x, 2) for x in closes[-20:]],
        "a": above200, "t": trend, "vs": vsurge, "r": near_ob,
        "ob": ({"lo": ob["lo"], "hi": ob["hi"], "t": h.index[-1].strftime("%d %b")} if ob else None),
        "sc": score, "tier": tier,
    }


def main():
    with open(SRC) as f:
        base = json.load(f)  # [symbol, name, industry, exchange, country, source]

    out = []
    scanned, skipped = 0, 0
    for sym, name, ind, exch, country, src in base:
        rec = {"s": sym, "n": name, "i": ind, "x": exch, "c": country, "r": src}
        suf = SUFFIX.get(exch)
        if suf:
            try:
                sig = signal(sym + suf)
                if sig:
                    rec["sig"] = sig
                    scanned += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"skip {sym}: {e}", file=sys.stderr)
                skipped += 1
        out.append(rec)

    today = datetime.date.today().strftime("%d %b %Y")
    payload = {"stocks": out, "meta": {"asof": today, "screened": today}}
    with open(OUT, "w") as f:
        json.dump(payload, f)

    print(f"Done. {scanned} scanned, {skipped} skipped, {len(out)} total written to {OUT}.")


if __name__ == "__main__":
    main()
