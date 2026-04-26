import datetime
import pickle
import os.path
import yfinance as yf
from googleapiclient.discovery import build

# --- CONFIGURATION ---
# Use .NS for Indian stocks (e.g., RELIANCE.NS)
WATCHLIST = ["AAPL", "NVDA", "RELIANCE.NS", "HDFCBANK.NS", "TCS.NS"]

def get_calendar_service():
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
    return build('calendar', 'v3', credentials=creds)

def add_to_calendar(ticker, date, projection):
    service = get_calendar_service()
    event = {
        'summary': f"💰 Earnings: {ticker}",
        'description': f"Expected EPS/Results today: {projection}. Analyzing sentiment soon...",
        'start': {'date': date.strftime('%Y-%m-%d')},
        'end': {'date': (date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')},
        'reminders': {
            'useDefault': False,
            'overrides': [{'method': 'popup', 'minutes': 60}] # Alert 1 hour before day starts
        },
    }
    try:
        service.events().insert(calendarId='primary', body=event).execute()
        print(f"✅ Added {ticker} to calendar for {date}")
    except Exception as e:
        print(f"❌ Failed to add {ticker}: {e}")

def main():
    today = datetime.date.today()
    one_week_later = today + datetime.timedelta(days=7)
    
    print(f"Scanning watchlist for dates between {today} and {one_week_later}...")

    for ticker in WATCHLIST:
        print(f"Checking {ticker}...", end=" ", flush=True)
        stock = yf.Ticker(ticker)
        
        try:
            cal = stock.calendar
            # If calendar is empty, try the new 2026 'get_earnings_dates' method
            if not cal:
                earnings_df = stock.get_earnings_dates(limit=5)
                if earnings_df is not None:
                    # Convert index to a list of dates
                    dates_list = earnings_df.index.to_list()
                    # We only care about the most recent one
                    raw_date = dates_list[0]
                else:
                    print("❌ No data available.")
                    continue
            else:
                # Use dictionary data from .calendar
                raw_date = cal.get('Earnings Date', [None])[0]

            # CONVERSION LOGIC: Handle both Timestamps and Strings
            if raw_date is None:
                print("❓ Date not found.")
                continue
                
            if hasattr(raw_date, 'date'):
                e_date = raw_date.date()
            else:
                # If it's a string like "2026-05-01", parse it
                e_date = datetime.datetime.strptime(str(raw_date)[:10], '%Y-%m-%d').date()

            # Final Check & Calendar Sync
            if today <= e_date <= one_week_later:
                print(f"🎯 MATCH: {e_date}")
                projection = cal.get('Earnings Average', 'N/A') if isinstance(cal, dict) else "N/A"
                add_to_calendar(ticker, e_date, projection)
            else:
                print(f" (Future: {e_date})")

        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == '__main__':
    main()