import datetime
import pickle
import os
import json
import requests
import sys
import time
from google import genai
from google.genai import types
from googleapiclient.discovery import build

# ==========================================
# 1. YOUR CONFIGURATION (FILL THESE IN)
# ==========================================
GEMINI_API_KEY = "AIzaSyBNMW9tBdq_ibiypvaBM_WUAbn2j_dYpqQ"
TELEGRAM_TOKEN = "8670487384:AAFWRunc5zmWcCv9VWW90OH603vN73dcGZA"
TELEGRAM_CHAT_ID = "@StockSentimentPrediction_bot"

# The 2026 model string you confirmed works
MODEL_NAME = "gemini-3.1-flash-lite-preview"

# Use .NS for Indian stocks (NSE)
WATCHLIST = ["AAPL", "NVDA", "RELIANCE.NS", "HDFCBANK.NS", "TCS.NS"]

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def call_gemini_with_retry(prompt, model=MODEL_NAME, retries=3):
    """Handles 429 Rate Limits with exponential backoff."""
    for i in range(retries):
        try:
            return client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search_retrieval=types.GoogleSearchRetrieval())]
                )
            )
        except Exception as e:
            if "429" in str(e):
                wait_time = (i + 1) * 30  # Wait 30, 60, then 90 seconds
                print(f"🚦 Rate limit hit. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                print(f"❌ Gemini Error: {e}")
                return None
    return None

def get_calendar_service():
    if not os.path.exists('token.pickle'):
        print("❌ Error: token.pickle not found. Run auth_calendar.py first.")
        sys.exit(1)
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
    return build('calendar', 'v3', credentials=creds)

def add_to_calendar(ticker, date_str, projection):
    service = get_calendar_service()
    event = {
        'summary': f"💰 Earnings: {ticker}",
        'description': f"Projected/Expected Results: {projection}",
        'start': {'date': date_str},
        'end': {'date': date_str},
        'reminders': {'useDefault': True}
    }
    try:
        service.events().insert(calendarId='primary', body=event).execute()
        print(f"📅 Added {ticker} to Calendar for {date_str}")
    except Exception as e:
        print(f"❌ Calendar Error for {ticker}: {e}")

def send_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

# ==========================================
# 3. CORE WORKFLOWS
# ==========================================

def sync_weekly_calendar():
    """Step 1 & 2: Identifies upcoming results and puts them in iPhone Calendar."""
    print(f"🚀 Starting Weekly Scan for {datetime.date.today()}...")
    today = datetime.date.today()
    one_week_later = today + datetime.timedelta(days=7)

    for ticker in WATCHLIST:
        print(f"🔍 AI searching for {ticker}...")
        prompt = f"""
        Find the next quarterly earnings date and analyst EPS/Revenue projections for {ticker}.
        Today's date is {today}.
        Return ONLY a JSON object: 
        {{"date": "YYYY-MM-DD", "projection": "Summary of expected EPS/Revenue", "in_window": true/false}}
        Set 'in_window' to true ONLY if the date is between {today} and {one_week_later}.
        """
        
        response = call_gemini_with_retry(prompt)
        
        if response and response.text:
            try:
                # Clean and Parse JSON
                clean_txt = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(clean_txt)
                
                if data.get('in_window'):
                    add_to_calendar(ticker, data['date'], data['projection'])
                else:
                    print(f"ℹ️ {ticker} reports on {data['date']} (Not this week).")
            except Exception as e:
                print(f"⚠️ Data parsing failed for {ticker}: {e}")
        
        # Mandatory gap to stay under free-tier search limits
        print("⏳ Throttling for 20s...")
        time.sleep(20)

def run_daily_analysis():
    """Step 3, 4 & 5: Scans today's results and notifies via Telegram."""
    print(f"🕒 Running Daily Sentiment Analysis for {datetime.date.today()}...")
    
    for ticker in WATCHLIST:
        print(f"🧐 Checking results for {ticker}...")
        prompt = f"""
        Search for {ticker} quarterly earnings released today ({datetime.date.today()}).
        If released:
        1. Compare actual vs expectations.
        2. Analyze guidance and market sentiment.
        3. Decision: 'BUY' (very positive) or 'FLAG' (negative/neutral).
        Return ONLY JSON: 
        {{"released": true/false, "decision": "BUY/FLAG", "reason": "...", "confidence": 0-100}}
        """
        
        response = call_gemini_with_retry(prompt)
        
        if response and response.text:
            try:
                clean_txt = response.text.replace('```json', '').replace('```', '').strip()
                res = json.loads(clean_txt)

                if res.get('released'):
                    if res['decision'] == "BUY":
                        msg = f"🚀 *BUY ALERT: {ticker}*\n\nReason: {res['reason']}\nConfidence: {res['confidence']}%"
                        send_alert(msg)
                        print(f"✅ Telegram alert sent for {ticker}")
                    else:
                        with open("flagged_stocks.txt", "a") as f:
                            f.write(f"{datetime.date.today()} | {ticker} | {res['reason']}\n")
                        print(f"🚩 {ticker} flagged (Weak results).")
                else:
                    print(f"😴 No results found today for {ticker}.")
            except Exception as e:
                print(f"⚠️ Analysis parsing failed for {ticker}: {e}")
        
        time.sleep(20)

# ==========================================
# 4. EXECUTION
# ==========================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n❌ MISSING ARGUMENT!")
        print("Usage:")
        print(" python3 trade_bot.py --sync     (Weekly: Update iPhone Calendar)")
        print(" python3 trade_bot.py --analyze  (Daily: Get Buy Alerts)")
    elif sys.argv[1] == "--sync":
        sync_weekly_calendar()
    elif sys.argv[1] == "--analyze":
        run_daily_analysis()