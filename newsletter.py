"""
Daily Market Newsletter — Mac version
Sends top/bottom 25 stocks, EUR/USD + major FX rates, and index ETF prices
to your email every weekday morning.

Requirements:
    pip3 install requests

Setup:
    1. Get a free API key from https://alphavantage.co
    2. Fill in the CONFIG section below
    3. Follow README.md to schedule with launchd (Mac's built-in scheduler)
"""

import smtplib
import datetime
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── CONFIG — fill these in ────────────────────────────────────────────────────

ALPHA_VANTAGE_KEY = "{api key here}"  # https://alphavantage.co (free)

SMTP_EMAIL    = "{gmail here}"          # Gmail you'll send FROM
SMTP_PASSWORD = "{app password here}"           # Gmail App Password (not login password)
                                                 # https://myaccount.google.com/apppasswords
TO_EMAIL      = "{email you send to here}"

# ── END CONFIG ────────────────────────────────────────────────────────────────

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

INDEX_ETFS = ["SPY", "VOO", "QQQ"]

FX_PAIRS = [
    ("EUR/USD", "Euro → US Dollar"),
    ("GBP/USD", "British Pound → USD"),
    ("USD/JPY", "US Dollar → Japanese Yen"),
    ("USD/CAD", "US Dollar → Canadian Dollar"),
    ("USD/AUD", "US Dollar → Australian Dollar"),
    ("USD/CNY", "US Dollar → Chinese Yuan"),
]

SP500_SAMPLE = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","JPM","V","XOM",
    "MA","JNJ","AVGO","LLY","UNH","PG","HD","MRK","ABBV","COST","CVX",
    "CRM","PEP","BAC","KO","ACN","WMT","MCD","TMO","AMD","NFLX","ADBE",
    "TXN","DIS","NEE","INTC","HON","AMGN","LOW","QCOM","IBM","CAT","SPGI",
    "GS","ISRG","AXP","BLK","NOW","GILD","SBUX",
]


# ── Data fetchers ─────────────────────────────────────────────────────────────

def fetch_etfs():
    import time
    results = {}
    for sym in INDEX_ETFS:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={sym}&apikey={ALPHA_VANTAGE_KEY}"
        try:
            resp = requests.get(url, timeout=15).json()
            d = resp["Global Quote"]
            price  = float(d["05. price"])
            prev   = float(d["08. previous close"])
            change = price - prev
            pct    = float(d["10. change percent"].replace("%",""))
            results[sym] = {"price": price, "change": change, "pct": pct}
        except Exception:
            results[sym] = {"price": None, "change": 0, "pct": 0}
        time.sleep(1)
    return results


def fetch_fx():
    # Alpha Vantage forex: one call per pair on free tier
    results = []
    for pair, label in FX_PAIRS:
        from_c, to_c = pair.split("/")
        url = (f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE"
               f"&from_currency={from_c}&to_currency={to_c}&apikey={ALPHA_VANTAGE_KEY}")
        try:
            resp = requests.get(url, timeout=15).json()
            rate = float(resp["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
            results.append({"label": label, "pair": pair, "rate": rate, "pct": 0})
        except Exception:
            results.append({"label": label, "pair": pair, "rate": None, "pct": 0})
    return results


def fetch_movers():
    import time
    movers = []
    for sym in SP500_SAMPLE:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={sym}&apikey={ALPHA_VANTAGE_KEY}"
        try:
            resp = requests.get(url, timeout=15).json()
            d = resp["Global Quote"]
            price = float(d["05. price"])
            pct   = float(d["10. change percent"].replace("%",""))
            movers.append({"sym": sym, "price": price, "pct": pct})
        except Exception:
            pass
        time.sleep(1)
    movers.sort(key=lambda x: x["pct"], reverse=True)
    return movers[:25], movers[-25:][::-1]


# ── HTML builder ──────────────────────────────────────────────────────────────

CSS = """
<style>
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;
       background:#f5f5f7;margin:0;padding:20px;}
  .wrap{max-width:640px;margin:0 auto;background:#fff;border-radius:12px;
        overflow:hidden;border:1px solid #e0e0e0;}
  .hdr{background:#1a1a2e;color:#fff;padding:28px 32px 20px;}
  .hdr h1{margin:0;font-size:22px;font-weight:600;}
  .hdr .sub{margin:6px 0 0;font-size:13px;color:#aaa;}
  .body{padding:24px 32px;}
  h2{font-size:11px;font-weight:600;color:#888;text-transform:uppercase;
     letter-spacing:.07em;margin:24px 0 10px;}
  h2:first-child{margin-top:0;}
  .cards{display:flex;gap:12px;}
  .card{flex:1;background:#f8f8f8;border-radius:8px;padding:12px 14px;
        border:1px solid #ebebeb;}
  .card .lbl{font-size:11px;color:#888;margin-bottom:4px;}
  .card .val{font-size:19px;font-weight:600;color:#1a1a2e;}
  .card .chg{font-size:12px;margin-top:3px;}
  .up{color:#1a9e5c;} .dn{color:#d13b3b;}
  table{width:100%;border-collapse:collapse;font-size:13px;margin-top:4px;}
  th{text-align:left;padding:6px 8px;font-size:11px;font-weight:600;
     color:#888;border-bottom:1px solid #ebebeb;}
  th.r{text-align:right;}
  td{padding:7px 8px;border-bottom:1px solid #f2f2f2;color:#222;}
  td.r{text-align:right;font-variant-numeric:tabular-nums;}
  tr:last-child td{border-bottom:none;}
  .sym{font-weight:600;}
  .pill{display:inline-block;padding:2px 8px;border-radius:4px;
        font-size:12px;font-weight:600;}
  .pill-up{background:#e6f7ef;color:#1a9e5c;}
  .pill-dn{background:#fdeaea;color:#d13b3b;}
  .ftr{padding:14px 32px;background:#f8f8f8;border-top:1px solid #ebebeb;
       font-size:11px;color:#aaa;text-align:center;}
</style>
"""


def fmt_pct(pct):
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def arrow(pct):
    return "▲" if pct >= 0 else "▼"


def build_etf_cards(etfs):
    names = {"SPY": "SPDR S&P 500", "VOO": "Vanguard S&P 500", "QQQ": "Nasdaq-100"}
    cards = ""
    for sym, d in etfs.items():
        price = f"${d['price']:,.2f}" if d["price"] else "N/A"
        cls   = "up" if d["pct"] >= 0 else "dn"
        chg   = f"{arrow(d['pct'])} {abs(d['change']):.2f} ({fmt_pct(d['pct'])})"
        cards += f"""
        <div class="card">
          <div class="lbl">{sym} — {names[sym]}</div>
          <div class="val">{price}</div>
          <div class="chg {cls}">{chg}</div>
        </div>"""
    return f'<div class="cards">{cards}</div>'


def build_fx_table(fx):
    rows = ""
    for d in fx:
        rate = f"{d['rate']:.4f}" if d["rate"] else "N/A"
        cls  = "up" if d["pct"] >= 0 else "dn"
        rows += f"""
        <tr>
          <td>{d['label']}</td>
          <td class="r">{rate}</td>
          <td class="r"><span class="{cls}">{fmt_pct(d['pct'])}</span></td>
        </tr>"""
    return f"""
    <table>
      <thead><tr><th>Pair</th><th class="r">Rate</th><th class="r">Day chg</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def build_movers_table(movers, is_gain):
    rows = ""
    for i, d in enumerate(movers, 1):
        pill = "pill-up" if is_gain else "pill-dn"
        rows += f"""
        <tr>
          <td style="color:#bbb;font-size:11px;">{i}</td>
          <td class="sym">{d['sym']}</td>
          <td class="r">${d['price']:,.2f}</td>
          <td class="r"><span class="pill {pill}">{fmt_pct(d['pct'])}</span></td>
        </tr>"""
    return f"""
    <table>
      <thead><tr><th>#</th><th>Symbol</th><th class="r">Price</th><th class="r">% Change</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def build_html(etfs, fx, gainers, losers, date_str):
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8">{CSS}</head>
<body>
<div class="wrap">
  <div class="hdr">
    <h1>Market Daily</h1>
    <div class="sub">{date_str} &nbsp;·&nbsp; Last market close</div>
  </div>
  <div class="body">
    <h2>Index ETFs</h2>
    {build_etf_cards(etfs)}
    <h2>Currency Rates</h2>
    {build_fx_table(fx)}
    <h2>▲ Top 25 Gainers</h2>
    {build_movers_table(gainers, True)}
    <h2>▼ Top 25 Losers</h2>
    {build_movers_table(losers, False)}
  </div>
  <div class="ftr">
    Market Daily &nbsp;·&nbsp; For informational purposes only, not investment advice.<br>
    Data via Twelve Data.
  </div>
</div>
</body></html>"""


# ── Email sender ──────────────────────────────────────────────────────────────

def send_email(html_body, date_str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Market Daily — {date_str}"
    msg["From"]    = SMTP_EMAIL
    msg["To"]      = TO_EMAIL
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, TO_EMAIL, msg.as_string())
    print(f"✓ Newsletter sent to {TO_EMAIL}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    today = datetime.date.today()
    if today.weekday() >= 5:
        print("Weekend — no newsletter today.")
        return

    date_str = today.strftime("%A, %B %-d, %Y")
    print("Fetching ETF data...")
    etfs = fetch_etfs()
    print("Fetching FX data...")
    fx = fetch_fx()
    print("Fetching stock movers...")
    gainers, losers = fetch_movers()
    print("Sending email...")
    html = build_html(etfs, fx, gainers, losers, date_str)
    send_email(html, date_str)


if __name__ == "__main__":
    main()
