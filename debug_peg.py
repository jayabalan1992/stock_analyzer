import yfinance as yf

tickers = ["NVDA", "AAPL", "TSLA"]

for t in tickers:
    print(f"\n--- {t} ---")
    try:
        stock = yf.Ticker(t)
        info = stock.info
        print(f"pegRatio: {info.get('pegRatio')}")
        # Search for other potential keys
        keys = [k for k in info.keys() if 'peg' in k.lower()]
        print(f"PEG-related keys: {keys}")
        for k in keys:
            print(f"{k}: {info[k]}")
    except Exception as e:
        print(f"Error: {e}")
