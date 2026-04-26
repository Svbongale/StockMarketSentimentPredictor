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
# 1. CONFIGURATION (USING SECRETS)
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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
                wait_time = (i + 1) * 30 
                print(f"🚦 Rate limit hit. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                print(f"❌ Gemini Error: {e}")
                return None
    return None

def get_calendar_service():
    if not os.path.exists('token.pickle'):
        print("❌ Error: token.pickle not found. Ensure GitHub Secrets are correct.")
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
    print(f"🚀 Starting Weekly Scan for {datetime.date.today()}...")
    today = datetime.date.today()
    one_week_later = today + datetime.timedelta(days=7)

    for ticker in WATCHLIST:
        print(f"🔍 AI searching for {ticker}...")
        prompt = f"""
        Find the next quarterly earnings date and analyst EPS/Revenue projections for {ticker}.
        Today is {today}.
        Return ONLY a JSON object: 
        {{"date": "YYYY-MM-DD", "projection": "Summary of expected EPS/Revenue", "in_window": true/false}}
        """
        
        response = call_gemini_with_retry(prompt)
        
        if response and response.text:
            try:
                clean_txt = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(clean_txt)
                
                # Check if it's in our 7-day window
                e_date = datetime.datetime.strptime(data['date'], "%Y-%m-%d").date()
                if today <= e_date <= one_week_later:
                    add_to_calendar(ticker, data['date'], data['projection'])
                else:
                    print(f"ℹ️ {ticker} reports on {data['date']} (Not this week).")
            except Exception as e:
                print(f"⚠️ Parsing failed for {ticker}: {e}")
        
        time.sleep(20)

def run_daily_analysis():
    print(f"🕒 Running Daily Sentiment Analysis...")
    
    for ticker in WATCHLIST:
        print(f"🧐 Checking {ticker}...")
        prompt = f"""
        Search for {ticker} quarterly earnings released today ({datetime.date.today()}).
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
                    else:
                        # EASY FIX: Send a notification for 'Bad' results too
                        msg = f"🚩 *FLAGGED: {ticker}*\n\nReason: {res['reason']}\nConfidence: {res['confidence']}%"
                    
                    send_alert(msg)
                    print(f"✅ Notification sent for {ticker}")
                else:
                    print(f"😴 No results found today for {ticker}.")
            except Exception as e:
                print(f"⚠️ Analysis failed for {ticker}: {e}")
        
        time.sleep(20)

# ==========================================
# 4. EXECUTION
# ==========================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 trade_bot.py --sync OR --analyze")
    elif sys.argv[1] == "--sync":
        sync_weekly_calendar()
    elif sys.argv[1] == "--analyze":
        run_daily_analysis()