import yfinance as yf

try:
    ticker = yf.Ticker("VOO")
    if ticker.news:
        print("--- NEWS KEYS ---")
        print(list(ticker.news[0].keys()))
        print(f"Title: {ticker.news[0].get('title')}")
    else:
        print("No news found.")
except Exception as e:
    print(f"Error: {e}")
