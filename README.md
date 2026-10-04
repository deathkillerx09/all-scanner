# All Scanner — setup guide

This turns the site from a preview into something that runs on its own, every weekday,
with your laptop closed. It's free, using GitHub's servers instead of yours.

## What's in this folder
- `index.html` — the site itself
- `manifest.webmanifest` — lets you add it to your phone's home screen like an app
- `data/halal_list.json` — **the master list of stocks.** Edit this file to add or remove stocks.
- `data/stocks.json` — generated automatically; you don't edit this by hand
- `scan.py` — fetches prices and works out the strategy signal for each Indian stock
- `.github/workflows/scan.yml` — the robot that runs `scan.py` every weekday and
  re-publishes the site, automatically, forever

## Step 1 — Put this on GitHub (free account)
1. Go to github.com and sign up if you don't have an account.
2. Click **New repository**. Name it anything, e.g. `all-scanner`. Keep it **Public**
   (Pages needs that on a free account). Create it.
3. On the new repo's page, click **Add file → Upload files**, and drag in every file
   and folder from this kit (keep the folder structure — `data/` and `.github/` must
   stay as folders). Commit the changes.

## Step 2 — Turn on GitHub Pages (this is what hosts it 24/7)
1. In your repo, go to **Settings → Pages**.
2. Under "Build and deployment", set **Source** to **GitHub Actions**.
3. That's it — no server to rent, no laptop needed. GitHub hosts the page for free.

## Step 3 — Let the scan run automatically
The workflow in `.github/workflows/scan.yml` is already set to run every weekday
at 18:00 India time, right after NSE closes, and to publish the result.
1. Go to the **Actions** tab in your repo. If asked, click "I understand my workflows,
   enable them".
2. Click **Scan and publish → Run workflow** once, to generate `data/stocks.json`
   for the first time instead of waiting for tomorrow evening.
3. After it finishes (green check), go back to **Settings → Pages** — your live
   URL is shown at the top, something like:
   `https://YOUR-USERNAME.github.io/all-scanner/`

From now on it re-runs itself every weekday evening — you never have to touch it.

## Step 4 — View it on your phone
1. Open the `github.io` link from Step 3 in your phone's browser.
2. **iPhone (Safari):** tap the Share icon → **Add to Home Screen**.
   **Android (Chrome):** tap the ⋮ menu → **Add to Home screen** / **Install app**.
3. It now opens full-screen like a normal app, with its own icon — that's what
   `manifest.webmanifest` is for.

## Adding more stocks
Open `data/halal_list.json`. Each stock is one line:
```
["SYMBOL", "Company name", "Industry", "NSE", "IN", "n"]
```
Exchange is `NSE`, `BSE`, `DFM` or `ADX`. Country is `IN` or `AE`. The last letter
is just a note-to-self about where you got it (`n` = NSE index, `m` = Musaffa, `s` =
Solactive index, `a` = you checked it yourself, `u` = added by a visitor). Save the
file, commit it, and the next scan picks it up automatically.

**On "every single halal stock":** this kit ships with about 185 stocks (roughly
150 from NSE's own Nifty500 Shariah index, the rest from published UAE Shariah
indices). NSE's full Shariah universe is bigger than that, and Musaffa's paid
screener covers thousands more worldwide — I can't fabricate a complete list without
a live, licensed screening feed. The honest path to "every one": export the full
list from NSE's Shariah index page or Musaffa's screener (their free plan lets you
browse; a paid plan unlocks bulk export) and paste the rows into `halal_list.json`.
The script doesn't care how many you give it.

## Re-checking which stocks are still halal (every ~30 days)
`scan.py` only refreshes **prices**. It does not — and safely can't — decide whether
a company is still Shariah-compliant, because that needs financial-ratio data
(debt, cash, interest income vs. market cap) that a free price feed doesn't carry.
Once a month:
1. Open [Musaffa's screener](https://musaffa.com/stock-screener/in/) (India) and
   [UAE screener](https://musaffa.com/stock-screener/ae/), or NSE's own
   [Nifty500 Shariah page](https://niftyindices.com/indices/equity/thematic-indices/nifty500-shariah)
   (NSE reviews it monthly).
2. Remove anything that dropped off, add anything new, in `halal_list.json`.
3. Commit. If you want a reminder, GitHub can email you: add a second `schedule`
   line to `scan.yml` with `cron: '0 6 1 * *'` (the 1st of each month) that just
   opens an issue reminding you to check — ask me and I'll wire that up.

## About the UAE stocks
Yahoo Finance (what `scan.py` uses for free) doesn't reliably carry DFM/ADX prices,
so UAE stocks currently show **"Not scanned yet"** instead of a fake number — that's
intentional, not a bug. If you get access to a UAE data feed, that's the one function
to edit in `scan.py`.

## Not financial or religious advice
Halal status comes from third-party screens and changes over time. Please confirm
with your own scholar or Musaffa before investing — this is a research tool, not advice.
